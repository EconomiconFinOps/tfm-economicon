import asyncio
import ipaddress
import math
import time

import structlog
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.runtime_secrets import StartupError
from app.services.citations import DocumentCitations, structured_location

MAX_TOP_K = 20
logger = structlog.get_logger("vector_store")
MAX_COSINE_DISTANCE = 2.0
UNDEFINED_COLUMN = "42703"


class EmbeddingDimensionMismatch(StartupError):
    """The stored vectors cannot be compared with the vectors of the configured provider."""

    def __init__(self):
        super().__init__(
            "The stored embeddings have a different dimension than the configured provider; "
            "re-index the corpus into a new collection before starting the backend."
        )


class PgVectorQueryStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self._resolved_peer=None

    def _capture_peer(self, connection):
        """Read only the peer of an already authenticated ordinary connection."""
        try:
            info=connection.connection.driver_connection.info
            address=str(ipaddress.ip_address(info.hostaddr))
            host,port=info.host,str(info.port)
            if not isinstance(host,str) or not host or ',' in host: return
            self._resolved_peer=(host,port,address)
        except (AttributeError,TypeError,ValueError):
            return

    def search_chunks(
        self, tenant_id: str, query_embedding: list[float], top_k: int = 4, max_distance: float | None = None,
        provider: str | None = None, *, deadline: float | None = None, cancelled=None,
    ) -> list[dict]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
            raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")
        if max_distance is not None and (
            isinstance(max_distance, bool) or not isinstance(max_distance, (int, float))
            or not math.isfinite(max_distance) or not 0 < max_distance <= MAX_COSINE_DISTANCE
        ):
            raise ValueError("max_distance must be greater than 0 and at most 2")
        vector = "[" + ",".join(f"{value:.6f}" for value in query_embedding) + "]"
        threshold = "WHERE distance <= :max_distance" if max_distance is not None else ""
        provider_filter = "AND ce.provider = :provider" if provider is not None else ""
        parameters = {"tenant_id": tenant_id, "query_embedding": vector, "top_k": top_k}
        if provider is not None:
            parameters["provider"] = provider
        if max_distance is not None:
            parameters["max_distance"] = float(max_distance)
        def query(connection, structured=True):
            def timeout():
                if deadline is None: return
                remaining=deadline-time.time()
                if remaining<=0 or cancelled.is_set(): raise TimeoutError('Retrieval deadline.')
                milliseconds=max(1,int(remaining*1000))
                connection.execute(text("SELECT set_config('statement_timeout', :timeout, true), "
                    "set_config('lock_timeout', :timeout, true)"),{'timeout':str(milliseconds)})
            timeout()
            chunk_metadata = "dc.metadata" if structured else "NULL"
            document_metadata = "metadata" if structured else "CAST('{}' AS jsonb)"
            rows = connection.execute(
                text(
                    f"""
                    SELECT chunk_id, document_id, tenant_id, chunk_index, source, content, distance, metadata
                    FROM (
                        SELECT
                            dc.id AS chunk_id,
                            kd.id AS document_id,
                            kd.tenant_id AS tenant_id,
                            dc.chunk_index AS chunk_index,
                            kd.source AS source,
                            dc.content AS content,
                            {chunk_metadata} AS metadata,
                            (ce.embedding <=> CAST(:query_embedding AS vector)) AS distance
                        FROM knowledge_documents kd
                        JOIN document_chunks dc ON dc.document_id = kd.id
                        JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                        WHERE kd.tenant_id = :tenant_id
                        {provider_filter}
                    ) ranked
                    {threshold}
                    ORDER BY distance, chunk_id
                    LIMIT :top_k
                    """
                ),
                parameters,
            ).all()
            if not rows:
                return []
            # Fetch each source document once, scoped to the same tenant and
            # transaction snapshot as retrieval (including concurrent reingestion).
            timeout()
            documents = connection.execute(
                text(f"""
                    SELECT id, text_content, {document_metadata} AS metadata FROM knowledge_documents
                    WHERE tenant_id = :tenant_id AND id IN :document_ids
                """).bindparams(bindparam("document_ids", expanding=True)),
                {"tenant_id": tenant_id, "document_ids": list({row.document_id for row in rows})},
            )
            documents = {row.id:row for row in documents}
            locations = {key:DocumentCitations(row.text_content) for key,row in documents.items()}
            def manual(row):
                return documents[row.document_id].metadata.get('original_format') == 'manual-text'
            def location(row):
                if row.metadata:
                    value = structured_location(row.metadata, documents[row.document_id].metadata,
                                                documents[row.document_id].text_content)
                    if manual(row):
                        # Manual text has no structured blocks: keep the Markdown reading it had before.
                        value['section'] = locations[row.document_id].section(row.content)
                    return value
                return {'section':locations[row.document_id].section(row.content)}
            return [
                {
                    "chunk_id": row.chunk_id,
                    "document_id": row.document_id,
                    "tenant_id": row.tenant_id,
                    "title": documents[row.document_id].metadata.get("title") or (
                        None if documents[row.document_id].metadata.get('chunking') and not manual(row) else locations[row.document_id].title
                    ) or row.source.strip(),
                    "chunk_index": row.chunk_index,
                    **location(row),
                    **({'chunk_metadata':row.metadata} if row.metadata else {}),
                    "source": row.source,
                    "content": row.content,
                    "distance": float(row.distance),
                }
                for row in rows
            ]

        def tolerant(connection):
            # Vector migration 003 is applied by the processor, which starts after the
            # backend: until its columns exist, retrieve as before 003 instead of failing.
            try:
                return query(connection)
            except ProgrammingError as exc:
                # PostgreSQL identifies undefined columns by a 1-based character position;
                # column_name is not supplied for 42703. Fail closed for unrelated columns.
                position = getattr(getattr(exc.orig, 'diag', None), 'statement_position', None)
                missing = (exc.statement or '')[int(position)-1:].split(maxsplit=1) if position and position.isdecimal() else []
                if (getattr(exc.orig, 'sqlstate', None) != UNDEFINED_COLUMN
                        or not missing or missing[0] not in {'dc.metadata', 'metadata'}):
                    raise
                connection.rollback()
                logger.warning("vector_metadata_unavailable", reason="vector_migration_003_pending")
                return query(connection, structured=False)

        if deadline is not None:
            if not isinstance(deadline,(int,float)) or not math.isfinite(deadline) or cancelled is None:
                raise ValueError('Invalid retrieval deadline.')
            return self._bounded_query(tolerant,deadline,cancelled)
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            self._capture_peer(connection)
            return tolerant(connection)

    def _bounded_query(self, query, deadline, cancelled):
        """Request-owned async IO: no shared pool checkout or synchronous read."""
        import psycopg
        args,parameters=self.engine.dialect.create_connect_args(self.engine.url)
        peer=getattr(self,'_resolved_peer',None)
        # SQLAlchemy's adapters context is a Python driver option, not libpq
        # conninfo. Preserve it for connect, exclude only from address checking.
        libpq_parameters={key:value for key,value in parameters.items() if key!='context'}
        configured=psycopg.conninfo.conninfo_to_dict(psycopg.conninfo.make_conninfo(*args,**libpq_parameters))
        if (peer is None or configured.get('host')!=peer[0]
                or str(configured.get('port','5432'))!=peer[1]):
            raise ValueError('Retrieval address unavailable.')
        # Keep the original hostname (including TLS verify-full), supply only
        # the peer observed during startup/ordinary work. Never resolve here.
        parameters={**parameters,'hostaddr':peer[2]}
        async def run():
            driver=None
            async def connect():
                nonlocal driver
                remaining=deadline-time.time()
                if remaining<=0 or cancelled.is_set(): raise TimeoutError('Retrieval deadline.')
                kwargs={**parameters,'connect_timeout':max(1,math.ceil(remaining))}
                options=kwargs.get('options','')
                milliseconds=max(1,int(remaining*1000))
                kwargs['options']=options+f' -c statement_timeout={milliseconds} -c lock_timeout={milliseconds}'
                driver=await psycopg.AsyncConnection.connect(*args,**kwargs)
                return driver
            engine=create_async_engine(self.engine.url,poolclass=NullPool,async_creator=connect,
                isolation_level='REPEATABLE READ')
            async def read():
                async with engine.connect() as connection:
                    return await connection.run_sync(query)
            task=asyncio.create_task(read())
            try:
                while not task.done():
                    remaining=deadline-time.time()
                    if remaining<=0 or cancelled.is_set():
                        # Closing before task.cancel avoids psycopg's extra 5s+5s
                        # cancellation/read fallback outside the common deadline.
                        if driver is not None:
                            if remaining>0:
                                allowance=min(.05,remaining)
                                try:
                                    await asyncio.wait_for(driver.cancel_safe(timeout=allowance),allowance)
                                except Exception: pass
                            driver.pgconn.finish()
                        task.cancel()
                        await asyncio.gather(task,return_exceptions=True)
                        raise TimeoutError('Retrieval deadline.')
                    await asyncio.wait({task},timeout=min(.01,remaining))
                if cancelled.is_set() or time.time()>=deadline:
                    raise TimeoutError('Retrieval deadline.')
                try:
                    return task.result()
                except Exception as failure:
                    if getattr(getattr(failure,'orig',failure),'sqlstate',None)=='57014':
                        raise TimeoutError('Retrieval deadline.') from None
                    raise
            finally:
                if not task.done():
                    if driver is not None: driver.pgconn.finish()
                    task.cancel()
                    await asyncio.gather(task,return_exceptions=True)
                await engine.dispose()
        return asyncio.run(run())

    def embedding_column_dimension(self) -> int | None:
        """Dimension declared by chunk_embeddings.embedding, or None while the table does not exist yet."""
        with self.engine.connect() as connection:
            self._capture_peer(connection)
            value = connection.execute(text(
                "SELECT atttypmod FROM pg_attribute "
                "WHERE attrelid = to_regclass('chunk_embeddings') AND attname = 'embedding'"
            )).scalar()
        return value if isinstance(value, int) and value > 0 else None

    def verify_dimension(self, expected: int) -> None:
        try:
            column = self.embedding_column_dimension()
        except Exception:
            logger.warning("embedding_dimension_check_skipped", reason="query_failed")
            return
        if column is None:
            logger.info("embedding_dimension_check_skipped", reason="table_missing")
            return
        if column != expected:
            raise EmbeddingDimensionMismatch()

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                self._capture_peer(connection)
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()
