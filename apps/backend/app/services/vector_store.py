import asyncio
import ipaddress
import math
import re
import time
import hashlib
import json
import copy

import structlog
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.runtime_secrets import StartupError
from app.services.citations import DocumentCitations, structured_location

MAX_TOP_K = 20
logger = structlog.get_logger("vector_store")
MAX_COSINE_DISTANCE = 2.0
UNDEFINED_COLUMN = '42703'
MAX_POLICY_CHUNKS = 6


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
        plan=None, question=None,
        neighbor_seed_count: int = 0, policy_section: str | None = None,
    ) -> list[dict]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
            raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")
        if max_distance is not None and (
            isinstance(max_distance, bool) or not isinstance(max_distance, (int, float))
            or not math.isfinite(max_distance) or not 0 < max_distance <= MAX_COSINE_DISTANCE
        ):
            raise ValueError("max_distance must be greater than 0 and at most 2")
        if type(neighbor_seed_count) is not int or not 0 <= neighbor_seed_count <= top_k:
            raise ValueError('Invalid neighbor seed count.')
        if policy_section is not None:
            from app.core.chat_policy_sections import SECTIONS
            if policy_section not in SECTIONS.values() or not isinstance(provider, str) or not provider:
                raise ValueError('Invalid policy section lookup.')
        if plan is not None:
            return self._search_generation(tenant_id, query_embedding, top_k, max_distance, provider,
                                           plan, question, deadline, cancelled, neighbor_seed_count, policy_section)
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
            chunk_metadata = 'dc.metadata' if structured else 'NULL'
            document_metadata = 'metadata' if structured else "CAST('{}' AS jsonb)"
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
            if not rows and policy_section is None:
                return []
            neighbor_ids = set()
            if neighbor_seed_count and rows:
                # One semantic retrieval, followed by bounded positional expansion
                # in this same tenant/provider/snapshot; never another embedding.
                seeds = rows[:neighbor_seed_count]
                pairs = list(dict.fromkeys((row.document_id, index) for row in seeds
                    for index in (row.chunk_index - 1, row.chunk_index + 1) if index >= 0))
                if pairs:
                    timeout()
                    neighbor_params = {'tenant_id': tenant_id, 'neighbor_limit': 2 * neighbor_seed_count, 'query_embedding': vector}
                    predicates = []
                    for index, (document, chunk_index) in enumerate(pairs):
                        predicates.append(f'(dc.document_id = :document_{index} AND dc.chunk_index = :index_{index})')
                        neighbor_params[f'document_{index}'] = document
                        neighbor_params[f'index_{index}'] = chunk_index
                    neighbor_provider = ''
                    if provider is not None:
                        neighbor_params['provider'] = provider
                        neighbor_provider = 'AND ce.provider = :provider'
                    neighbors = connection.execute(text(f"""
                        SELECT DISTINCT dc.id AS chunk_id, kd.id AS document_id,
                            kd.tenant_id AS tenant_id, dc.chunk_index AS chunk_index,
                            kd.source AS source, dc.content AS content,
                            {chunk_metadata} AS metadata,
                            (ce.embedding <=> CAST(:query_embedding AS vector)) AS distance
                        FROM knowledge_documents kd
                        JOIN document_chunks dc ON dc.document_id = kd.id
                        JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                        WHERE kd.tenant_id = :tenant_id {neighbor_provider}
                            AND ({' OR '.join(predicates)})
                        ORDER BY document_id, chunk_index, chunk_id
                        LIMIT :neighbor_limit
                    """), neighbor_params).all()
                    by_location = {(row.document_id, row.chunk_index): row for row in neighbors}
                    expanded, selected = list(seeds), {row.chunk_id for row in seeds}
                    for location in pairs:
                        row = by_location.get(location)
                        if row is not None and row.chunk_id not in selected:
                            expanded.append(row); selected.add(row.chunk_id)
                            neighbor_ids.add(row.chunk_id)
                    expanded.extend(row for row in rows if row.chunk_id not in selected)
                    rows = expanded[:top_k]
            policy_ids = set()
            if policy_section is not None:
                from app.core.chat_policy_sections import COMPANION_SECTIONS
                policy_rows = self._policy_rows(connection, tenant_id, provider, vector, policy_section, timeout, structured)
                for companion in COMPANION_SECTIONS.get(policy_section, ()):
                    policy_rows += self._policy_rows(connection, tenant_id, provider, vector, companion, timeout, structured)
                policy_rows = list({row.chunk_id: row for row in policy_rows}.values())
                policy_ids = {row.chunk_id for row in policy_rows}
                rows = (policy_rows + [row for row in rows if row.chunk_id not in policy_ids])[:top_k]
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
                    "section_spans": locations[row.document_id].section_spans(row.content,
                        original=bool(documents[row.document_id].metadata.get("chunking"))),
                    "source": row.source,
                    "content": row.content,
                    "distance": float(row.distance),
                    **({'policy_priority': True} if row.chunk_id in policy_ids else {}),
                    **({'retrieval': {'mode': 'dense', 'generation_id': None, 'space_id': None,
                        'admission': 'policy' if row.chunk_id in policy_ids else 'neighbor'}}
                       if row.chunk_id in policy_ids or row.chunk_id in neighbor_ids else {}),
                }
                for row in rows
            ]

        def tolerant(connection):
            # Backend may serve legacy rows before the processor applies migration 003.
            try:
                return query(connection)
            except ProgrammingError as error:
                # 42703 supplies a 1-based query character position, not column_name.
                position = getattr(getattr(error.orig, 'diag', None), 'statement_position', None)
                missing = (error.statement or '')[int(position)-1:].split(maxsplit=1) if position and position.isdecimal() else []
                if (getattr(error.orig, 'sqlstate', None) != UNDEFINED_COLUMN
                        or not missing or missing[0] not in {'dc.metadata', 'metadata'}):
                    raise
                connection.rollback()
                logger.warning('vector_metadata_unavailable', reason='vector_migration_003_pending')
                return query(connection, structured=False)

        if deadline is not None:
            if not isinstance(deadline,(int,float)) or not math.isfinite(deadline) or cancelled is None:
                raise ValueError('Invalid retrieval deadline.')
            return self._bounded_query(tolerant,deadline,cancelled)
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            self._capture_peer(connection)
            return tolerant(connection)

    def _execute_query(self, query, deadline=None, cancelled=None):
        if deadline is not None:
            if not isinstance(deadline, (int, float)) or not math.isfinite(deadline) or cancelled is None:
                raise ValueError('Invalid retrieval deadline.')
            return self._bounded_query(query, deadline, cancelled)
        with self.engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            self._capture_peer(connection)
            return query(connection)

    def _policy_rows(self, connection, tenant_id, provider, vector, section, timeout, structured=True):
        """Exact section expansion in the caller's tenant/provider snapshot.

        Two document candidates or seven chunk candidates are ambiguity/budget
        sentinels, not samples from which a favorable policy is selected. Source
        text is bounded before transport; a large candidate is never truncated
        into an apparently complete policy. No second embedding is requested.
        """
        from app.core.chat_policy_sections import complete_sections, normalized
        timeout()
        document_metadata = "metadata" if structured else "CAST('{}' AS jsonb)"
        heading = (r'(?m)^[ ]{0,3}#{1,6}[ \t]+' + r'[ \t]+'.join(re.escape(w) for w in section.split())
                   + r'[ \t]*(#+[ \t]*)?\r?$')
        documents = connection.execute(text(f"""
            SELECT kd.id, CASE WHEN octet_length(kd.text_content) <= 65536
                THEN kd.text_content ELSE NULL END AS text_content, {document_metadata} AS metadata
            FROM knowledge_documents kd
            WHERE kd.tenant_id = :tenant_id AND kd.text_content ~* :policy_heading
                AND EXISTS (SELECT 1 FROM document_chunks dc
                    JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                    WHERE dc.document_id = kd.id AND ce.provider = :provider)
            ORDER BY kd.id LIMIT 2
        """), {'tenant_id': tenant_id, 'provider': provider, 'policy_heading': heading}).all()
        if len(documents) != 1 or documents[0].text_content is None:
            return []
        document = documents[0]
        locations = DocumentCitations(document.text_content)
        indices = [i for i, title in enumerate(locations.sections) if normalized(title) == normalized(section)]
        if len(indices) != 1 or indices[0]+1 >= len(locations.offsets):
            return []
        original = bool(document.metadata.get("chunking"))
        offsets = locations.original_offsets if original else locations.offsets
        start, end = offsets[indices[0]:indices[0]+2]
        if not 0 < end-start <= 4096:
            return []
        timeout()
        chunk_metadata = "dc.metadata" if structured else "NULL"
        rows = connection.execute(text(f"""
            SELECT chunk_id, document_id, tenant_id, chunk_index, source, content, distance, metadata
            FROM (
                SELECT dc.id AS chunk_id, kd.id AS document_id, kd.tenant_id,
                    dc.chunk_index, kd.source, dc.content, {chunk_metadata} AS metadata,
                    (ce.embedding <=> CAST(:query_embedding AS vector)) AS distance,
                    position(dc.content in :policy_normalized)-1 AS section_offset
                FROM knowledge_documents kd
                JOIN document_chunks dc ON dc.document_id = kd.id
                JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                WHERE kd.tenant_id = :tenant_id AND kd.id = :policy_document
                    AND ce.provider = :provider
            ) scoped
            WHERE section_offset >= 0 AND section_offset <= :policy_end
                AND section_offset + char_length(content) > :policy_start
            ORDER BY chunk_index, chunk_id LIMIT :policy_chunk_limit
        """), {'tenant_id': tenant_id, 'provider': provider, 'query_embedding': vector,
               'policy_document': document.id, 'policy_normalized': document.text_content if original else locations.normalized,
               'policy_start': start, 'policy_end': end,
               'policy_chunk_limit': MAX_POLICY_CHUNKS+1}).all()
        if (not rows or len(rows) > MAX_POLICY_CHUNKS
                or any(row.document_id != document.id or row.tenant_id != tenant_id for row in rows)):
            return []
        sources = [{'id': row.chunk_id, 'kind': 'corpus', 'content': row.content,
                    'provenance': {'document_id': document.id, 'chunk_index': row.chunk_index,
                                   'sections': locations.section_spans(row.content, original=original)}} for row in rows]
        if len(complete_sections(sources, section)) != 1:
            return []
        return list(rows)

    def resolve_retrieval_plan(self, tenant_id, *, enabled=False, contextual=False, hybrid=False,
                               deadline=None, cancelled=None):
        if not enabled:
            return None
        def query(connection):
            row = connection.execute(text('''SELECT h.generation_id,h.version,g.space_id,g.retrieval_config,s.descriptor
                FROM tenant_rag_head h JOIN rag_generations g ON g.tenant_id=h.tenant_id AND g.id=h.generation_id
                JOIN embedding_spaces s ON s.id=g.space_id WHERE h.tenant_id=:tenant AND g.state='ready' '''),
                {'tenant': tenant_id}).mappings().first()
            if row is None:
                raise ValueError('No verified active index; legacy identity is unknown')
            plan = {**dict(row), 'tenant_id': tenant_id}
            descriptor = plan['descriptor']
            fingerprint = hashlib.sha256(json.dumps(descriptor, ensure_ascii=False, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            fields = {'provider', 'model_id', 'mapping_sha256', 'tokenizer_id', 'preparation', 'dimension', 'distance',
                      'config_version', 'query_preparation', 'context_tokens', 'max_input_tokens', 'max_input_bytes', 'storage_format'}
            dimensions = {256,512,1024} if descriptor.get('provider') == 'bedrock' else {1536}
            if (set(descriptor) != fields or fingerprint != plan['space_id'] or type(descriptor.get('dimension')) is not int or descriptor.get('dimension') not in dimensions
                    or descriptor.get('distance') != 'cosine' or descriptor.get('query_preparation') != 'plain_query_v1'
                    or descriptor.get('storage_format') != 'decimal6_v1'
                    or descriptor.get('preparation') not in {'plain_v1', 'contextual_embedding_v1'}
                    or descriptor.get('config_version') != 'embedding_config_v1'):
                raise ValueError('Unsupported index identity')
            expected_model = {'mock': 'mock/sha256_v1', 'litellm': 'openai/text-embedding-3-small',
                              'bedrock': 'amazon.titan-embed-text-v2:0'}.get(descriptor['provider'])
            tokenizer = 'tiktoken/0.14.0:cl100k_base:223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7'
            if (expected_model is None or descriptor['model_id'] != expected_model or descriptor['tokenizer_id'] != tokenizer
                    or not isinstance(descriptor['mapping_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', descriptor['mapping_sha256'])
                    or type(descriptor['context_tokens']) is not int or not 0 <= descriptor['context_tokens'] <= 512
                    or type(descriptor['max_input_tokens']) is not int or not 800 <= descriptor['max_input_tokens'] <= 8192
                    or type(descriptor['max_input_bytes']) is not int or not 4096 <= descriptor['max_input_bytes'] <= 1048576):
                raise ValueError('Unsupported embedding space identity')
            config = plan['retrieval_config']
            if (config.get('mode') not in {'dense', 'hybrid'} or type(config.get('rrf_k')) is not int or not 1 <= config['rrf_k'] <= 1000
                    or config.get('candidate_limit') != 20 or config.get('lexical_policy') != 'literal_context_v1'):
                raise ValueError('Unsupported retrieval recipe')
            if descriptor['preparation'] == 'contextual_embedding_v1' and not contextual:
                raise ValueError('Contextual retrieval is disabled')
            if config['mode'] == 'hybrid' and not hybrid:
                raise ValueError('Hybrid retrieval is disabled')
            return plan
        return self._execute_query(query, deadline, cancelled)

    def embed_query(self, tenant_id, question, provider, plan, *, deadline=None, cancelled=None):
        if plan is None:
            return provider.embed(question)
        descriptor = plan['descriptor']
        if (plan['tenant_id'] != tenant_id or provider.name != descriptor.get('provider')
                or provider.dimension != descriptor.get('dimension')
                or (provider.name in {'litellm','bedrock'} and getattr(provider, 'mapping_sha256', None) != descriptor.get('mapping_sha256'))):
            raise ValueError('Question provider and index space are incompatible')
        if (not isinstance(question, str) or not question.strip() or len(question.encode('utf-8')) > 8192):
            # UTF-8 bytes conservatively bound cl100k tokens, without approximating
            # an exact token count or adding a second runtime tokenizer dependency.
            raise ValueError('Question exceeds verified embedding limits')
        text_hash = hashlib.sha256(question.encode('utf-8')).hexdigest()
        params = {'tenant': tenant_id, 'space': plan['space_id'], 'hash': text_hash}
        statement = text('SELECT embedding::text FROM embedding_cache WHERE tenant_id=:tenant AND space_id=:space AND text_hash=:hash')
        def check_deadline():
            if cancelled is not None and cancelled.is_set():
                raise TimeoutError('Retrieval deadline.')
            if deadline is not None and time.time() >= deadline:
                raise TimeoutError('Retrieval deadline.')
        cached = None
        def lookup(connection):
            nonlocal cached
            value = connection.execute(statement, params).scalar()
            if value is not None:
                cached = self._verified_vector(json.loads(value), dimension=provider.dimension)
                # A busy maintenance row must not delay a valid immutable hit.
                connection.execute(text('''UPDATE embedding_cache SET last_used_at=clock_timestamp()
                    WHERE ctid IN (SELECT ctid FROM embedding_cache
                        WHERE tenant_id=:tenant AND space_id=:space AND text_hash=:hash
                        FOR UPDATE SKIP LOCKED)'''), params)
                connection.commit()
            return cached
        try:
            self._execute_query(lookup, deadline, cancelled)
        except DBAPIError as failure:
            # REPEATABLE READ can still see a row updated after its snapshot.
            # _execute_query has rolled back/closed that transaction. Only the
            # auxiliary touch is disposable; invalid vectors and other errors fail.
            if cached is None or getattr(failure.orig, 'sqlstate', None) != '40001':
                raise
        check_deadline()
        if cached is not None:
            return cached
        verified = copy.copy(provider)
        verified.expected_model = descriptor['model_id']
        vector = self._verified_vector(verified.embed(question), dimension=provider.dimension)
        def insert(connection):
            connection.execute(text('''INSERT INTO embedding_cache(tenant_id,space_id,text_hash,embedding,token_count)
                VALUES(:tenant,:space,:hash,CAST(:vector AS vector),NULL) ON CONFLICT DO NOTHING'''),
                {**params, 'vector': '[' + ','.join(f'{value:.6f}' for value in vector) + ']'})
            value = connection.execute(statement, params).scalar_one()
            connection.commit()
            return self._verified_vector(json.loads(value), dimension=provider.dimension)
        # Retry only the SQL transaction, retaining this one inference result.
        # A concurrent winner is read in a fresh snapshot and remains canonical.
        for attempt in range(3):
            check_deadline()
            try:
                return self._execute_query(insert, deadline, cancelled)
            except DBAPIError as failure:
                if getattr(failure.orig, 'sqlstate', None) != '40001' or attempt == 2:
                    raise

    @staticmethod
    def _verified_vector(vector, dimension=1536):
        if (type(dimension) is not int or dimension not in {256,512,1024,1536}
                or not isinstance(vector, list) or len(vector) != dimension
                or not all(type(value) in {int, float} and math.isfinite(value) for value in vector)
                or not any(float(f'{value:.6f}') != 0 for value in vector)):
            raise ValueError('Invalid verified query vector')
        return [float(f'{value:.6f}') for value in vector]

    def _generation_policy_rows(self, connection, params, base, section, timeout):
        """Apply the existing policy bounds to immutable members, never legacy rows."""
        from app.core.chat_policy_sections import complete_sections, normalized
        timeout()
        heading = (r'(?m)^[ ]{0,3}#{1,6}[ \t]+' + r'[ \t]+'.join(re.escape(w) for w in section.split())
                   + r'[ \t]*(#+[ \t]*)?\r?$')
        documents = connection.execute(text("""SELECT r.id, m.document_id, r.metadata,
            CASE WHEN octet_length(r.content)<=65536 THEN r.content ELSE NULL END AS content
            FROM rag_generation_members m
            JOIN rag_document_revisions r ON r.tenant_id=m.tenant_id AND r.id=m.revision_id
            WHERE m.tenant_id=:tenant AND m.generation_id=:generation AND r.content ~* :policy_heading
                AND EXISTS (SELECT 1 FROM rag_chunk_vectors v
                    JOIN embedding_cache e ON e.tenant_id=v.tenant_id AND e.space_id=v.space_id AND e.text_hash=v.text_hash
                    WHERE v.tenant_id=m.tenant_id AND v.revision_id=m.revision_id AND v.space_id=:space)
            ORDER BY r.id LIMIT 2"""), {**params, 'policy_heading': heading}).mappings().all()
        if len(documents) != 1 or documents[0]['content'] is None:
            return []
        document = documents[0]
        locations = DocumentCitations(document['content'])
        indices = [index for index, title in enumerate(locations.sections)
                   if normalized(title) == normalized(section)]
        if len(indices) != 1 or indices[0] + 1 >= len(locations.offsets):
            return []
        original = bool(document['metadata'].get('chunking'))
        offsets = locations.original_offsets if original else locations.offsets
        start, end = offsets[indices[0]:indices[0] + 2]
        if not 0 < end - start <= 4096:
            return []
        timeout()
        scoped = base.replace('(e.embedding <=> CAST(:vector AS vector)) AS distance',
            '(e.embedding <=> CAST(:vector AS vector)) AS distance,'
            'position(c.content in :policy_content)-1 AS section_offset')
        rows = [dict(row) for row in connection.execute(text('SELECT * FROM (' + scoped
            + ' AND c.revision_id=:policy_revision) scoped WHERE section_offset>=0'
            + ' AND section_offset<=:policy_end AND section_offset+char_length(content)>:policy_start'
            + ' ORDER BY chunk_index,chunk_id LIMIT :policy_chunk_limit'),
            {**params, 'policy_revision': document['id'],
             'policy_content': document['content'] if original else locations.normalized,
             'policy_start': start, 'policy_end': end, 'policy_chunk_limit': MAX_POLICY_CHUNKS + 1}).mappings()]
        if (not rows or len(rows) > MAX_POLICY_CHUNKS
                or any(row['revision_id'] != document['id'] or row['document_id'] != document['document_id'] for row in rows)):
            return []
        sources = [{'id': row['chunk_id'], 'kind': 'corpus', 'content': row['content'],
                    'provenance': {'document_id': row['document_id'], 'chunk_index': row['chunk_index'],
                                   'sections': locations.section_spans(row['content'], original=original)}}
                   for row in rows]
        return rows if len(complete_sections(sources, section)) == 1 else []

    def _search_generation(self, tenant, vector, limit, threshold, provider, plan, question, deadline, cancelled,
                           neighbor_seed_count=0, policy_section=None):
        from app.services.retrieval_policy import fuse, lexical_eligible, query_policy
        self._verified_vector(vector, dimension=plan['descriptor']['dimension'])
        if plan['tenant_id'] != tenant or provider != plan['descriptor']['provider']:
            raise ValueError('Retrieval plan scope mismatch')
        policy = query_policy(question or '')
        params = {'tenant': tenant, 'generation': plan['generation_id'], 'space': plan['space_id'],
                  'vector': '[' + ','.join(f'{value:.6f}' for value in vector) + ']',
                  'question': ' '.join(policy['anchors'] + policy['terms'])}
        base = '''SELECT c.chunk_id,c.revision_id,c.chunk_index,c.content,c.metadata,m.document_id,r.source,
            (e.embedding <=> CAST(:vector AS vector)) AS distance
            FROM rag_generation_members m
            JOIN rag_document_revisions r ON r.tenant_id=m.tenant_id AND r.id=m.revision_id
            JOIN rag_revision_chunks c ON c.tenant_id=m.tenant_id AND c.revision_id=m.revision_id
            JOIN rag_chunk_vectors v ON v.tenant_id=c.tenant_id AND v.revision_id=c.revision_id AND v.chunk_id=c.chunk_id AND v.space_id=:space
            JOIN embedding_cache e ON e.tenant_id=v.tenant_id AND e.space_id=v.space_id AND e.text_hash=v.text_hash
            WHERE m.tenant_id=:tenant AND m.generation_id=:generation'''
        def query(connection):
            def timeout():
                if deadline is not None:
                    remaining = deadline - time.time()
                    if remaining <= 0 or cancelled.is_set(): raise TimeoutError('Retrieval deadline.')
                    connection.execute(text("SELECT set_config('statement_timeout',:ms,true),set_config('lock_timeout',:ms,true)"),
                                       {'ms': str(max(1, int(remaining * 1000)))})
            timeout()
            generation = connection.execute(text('SELECT space_id,state FROM rag_generations WHERE tenant_id=:tenant AND id=:generation'), params).mappings().first()
            if not generation or generation['state'] not in {'ready', 'retired'} or generation['space_id'] != plan['space_id']:
                raise ValueError('Captured retrieval generation is unavailable')
            timeout()
            dense = [dict(row) for row in connection.execute(text('SELECT * FROM (' + base + ') candidates '
                + ('WHERE distance<=:threshold ' if threshold is not None else '')
                + 'ORDER BY distance,chunk_id LIMIT 20'), {**params, 'threshold': threshold}).mappings()]
            mode = plan['retrieval_config']['mode']
            if mode == 'hybrid':
                # Anchors only gate lexical rescue. Dense remains inclusive of
                # every captured candidate inside the declared distance bound.
                timeout()
                lexical_sql = base.replace('(e.embedding <=> CAST(:vector AS vector)) AS distance',
                    '(e.embedding <=> CAST(:vector AS vector)) AS distance,ts_rank_cd(c.search_vector,plainto_tsquery(\'pg_catalog.simple\',:question)) AS lexical_score')
                phrases = ''
                for index, phrase in enumerate(policy['phrases']):
                    params['phrase' + str(index)] = phrase
                    phrases += " AND c.search_vector @@ phraseto_tsquery('pg_catalog.simple',:phrase" + str(index) + ')'
                lexical = [dict(row) for row in connection.execute(text(lexical_sql
                    + " AND c.search_vector @@ plainto_tsquery('pg_catalog.simple',:question)" + phrases
                    + ' ORDER BY lexical_score DESC,c.chunk_id LIMIT 20'), params).mappings()]
                dense_ids = {(item['revision_id'], item['chunk_id']) for item in dense}
                lexical = [item for item in lexical if (item['revision_id'], item['chunk_id']) in dense_ids or lexical_eligible(item['content'], policy)]
                rows = fuse(dense, lexical, limit=limit, k=plan['retrieval_config']['rrf_k'])
            else:
                rows = dense[:limit]
            if neighbor_seed_count and rows:
                seeds = rows[:neighbor_seed_count]
                pairs = list(dict.fromkeys((row['revision_id'], index) for row in seeds
                    for index in (row['chunk_index'] - 1, row['chunk_index'] + 1) if index >= 0))
                if pairs:
                    timeout()
                    neighbor_params = {**params, 'neighbor_limit': 2 * neighbor_seed_count}
                    predicates = []
                    for index, (revision, chunk_index) in enumerate(pairs):
                        predicates.append(f'(c.revision_id=:revision_{index} AND c.chunk_index=:index_{index})')
                        neighbor_params[f'revision_{index}'] = revision
                        neighbor_params[f'index_{index}'] = chunk_index
                    neighbors = [dict(row) for row in connection.execute(text(base
                        + ' AND (' + ' OR '.join(predicates) + ')'
                        + ' ORDER BY m.document_id,c.chunk_index,c.chunk_id LIMIT :neighbor_limit'),
                        neighbor_params).mappings()]
                    by_location = {(row['revision_id'], row['chunk_index']): row for row in neighbors}
                    expanded = list(seeds)
                    selected = {(row['revision_id'], row['chunk_id']) for row in seeds}
                    for location in pairs:
                        row = by_location.get(location)
                        if row is not None and (row['revision_id'], row['chunk_id']) not in selected:
                            row['admission'] = 'neighbor'
                            expanded.append(row)
                            selected.add((row['revision_id'], row['chunk_id']))
                    expanded.extend(row for row in rows if (row['revision_id'], row['chunk_id']) not in selected)
                    rows = expanded[:limit]
            policy_ids = set()
            if policy_section is not None:
                from app.core.chat_policy_sections import COMPANION_SECTIONS
                sections = (policy_section, *COMPANION_SECTIONS.get(policy_section, ()))
                policy_rows = [row for section in sections
                    for row in self._generation_policy_rows(connection, params, base, section, timeout)]
                policy_rows = list({(row['revision_id'], row['chunk_id']): row for row in policy_rows}.values())
                for row in policy_rows:
                    row['admission'] = 'policy'
                policy_ids = {(row['revision_id'], row['chunk_id']) for row in policy_rows}
                rows = (policy_rows + [row for row in rows
                    if (row['revision_id'], row['chunk_id']) not in policy_ids])[:limit]
            timeout()
            parents = {}
            locations = {}
            if rows:
                parents = {row['id']: row for row in connection.execute(text('''SELECT id,content,metadata FROM rag_document_revisions
                    WHERE tenant_id=:tenant AND id IN :revisions''').bindparams(bindparam('revisions', expanding=True)),
                    {'tenant': tenant, 'revisions': sorted({row['revision_id'] for row in rows})}).mappings()}
                locations = {key: DocumentCitations(row['content']) for key, row in parents.items()}
            result = []
            for row in rows:
                document = parents[row['revision_id']]
                parent = document['metadata']
                citation = locations[row['revision_id']]
                manual = parent.get('original_format') == 'manual-text'
                location = (structured_location(row['metadata'], parent, document['content']) if row['metadata']
                            else {'section': citation.section(row['content'])})
                if manual and row['metadata']:
                    location['section'] = citation.section(row['content'])
                result.append({'chunk_id': row['chunk_id'], 'document_id': row['document_id'], 'tenant_id': tenant,
                    'chunk_index': row['chunk_index'], 'title': parent.get('title') or (None if parent.get('chunking') and not manual else citation.title) or row['source'].strip(),
                    'source': row['source'], 'content': row['content'], 'distance': float(row['distance']), **location,
                    **({'chunk_metadata': row['metadata']} if row['metadata'] else {}),
                    'section_spans': citation.section_spans(row['content'], original=bool(parent.get('chunking'))),
                    **({'policy_priority': True} if (row['revision_id'], row['chunk_id']) in policy_ids else {}),
                    'retrieval': {'generation_id': plan['generation_id'], 'space_id': plan['space_id'], 'mode': mode,
                        'rrf_k': plan['retrieval_config']['rrf_k'],
                        **({'admission': row['admission']} if 'admission' in row else {}),
                        **{key: row[key] for key in ('dense_rank', 'lexical_rank', 'lexical_score', 'rrf_score') if key in row}}})
            return result
        return self._execute_query(query, deadline, cancelled)

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
