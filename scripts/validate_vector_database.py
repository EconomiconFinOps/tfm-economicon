"""JUP-021 real PostgreSQL acceptance; synthetic fixtures in a dedicated database.

Run only with infra/vector/compose.yaml. No credentials are printed.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/processor"))
from app.core.runtime_secrets import StartupError
from app.vector_store.pgvector_store import PgVectorStore
from app.embeddings.providers import MockEmbeddingProvider


def load_backend(name):
    spec = importlib.util.spec_from_file_location(
        "backend_" + name, ROOT / "apps/backend/app/services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["seed", "verify"])
    parser.add_argument("--confirm-dedicated-database", action="store_true", required=True)
    args = parser.parse_args()
    url = os.environ["VECTOR_DATABASE_URL"]
    store = PgVectorStore(url, 8)
    query = load_backend("vector_store").PgVectorQueryStore(url)
    try:
        if args.phase == "seed":
            with store.engine.connect() as connection:
                assert connection.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")).scalar_one() == 0, "Seed requires an empty dedicated database"
        store.initialize()
        store.initialize()
        embed = MockEmbeddingProvider(8).embed
        assert embed("JUP-021 fixture") == load_backend("embedding_provider").MockEmbeddingProvider(8).embed("JUP-021 fixture")
        if args.phase == "seed":
            for tenant, content in [("jup021-a", "rightsizing compute"), ("jup021-b", "private storage costs")]:
                store.store_document(job_id=tenant, tenant_id=tenant, source="jup021-synthetic", artifact_uri=None, text_content=content, chunks=[content], embeddings=[embed(content)], provider_name="mock")
        own = query.search_chunks("jup021-a", embed("rightsizing compute"))
        foreign_nearest = query.search_chunks("jup021-a", embed("private storage costs"))
        assert len(own) == 1 and own[0]["content"] == "rightsizing compute"
        assert abs(own[0]["distance"]) < 1e-6
        assert len(foreign_nearest) == 1 and foreign_nearest[0]["content"] == "rightsizing compute"
        assert query.search_chunks("jup021-unknown", embed("rightsizing compute")) == []
        assert query.search_chunks("jup021-b", embed("private storage costs"))[0]["content"] == "private storage costs"
        try:
            store.store_document(job_id="jup021-a", tenant_id="jup021-b", source="attack", artifact_uri=None, text_content="attack", chunks=["attack"], embeddings=[embed("attack")], provider_name="mock")
        except PermissionError:
            pass
        else:
            raise AssertionError("Cross-tenant replacement accepted")
        try:
            store.store_document(job_id="jup021-a", tenant_id="jup021-a", source="bad", artifact_uri=None, text_content="bad", chunks=["bad"], embeddings=[[1.0]], provider_name="mock")
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong dimension accepted")
        for wrong_dimension in (7, 9):
            mismatch = PgVectorStore(url, wrong_dimension)
            try:
                try:
                    mismatch.initialize()
                except StartupError:
                    pass
                else:
                    raise AssertionError("Startup accepted incompatible schema")
            finally:
                mismatch.close()
        assert query.search_chunks("jup021-a", embed("rightsizing compute")) == own
        with store.engine.connect() as connection:
            versions = list(connection.execute(text("SELECT version FROM vector_schema_migrations ORDER BY version")).scalars())
            assert versions == ["001", "002"]
            indexes = list(connection.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")).scalars())
            assert "knowledge_documents_tenant_id_idx" in indexes
            index_definition = connection.execute(text("""
                SELECT indexdef FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'knowledge_documents'
                  AND indexname = 'knowledge_documents_tenant_id_idx'
            """)).scalar_one()
            assert "(tenant_id)" in index_definition
            assert "document_chunks_document_id_chunk_index_key" in indexes
            assert "chunk_embeddings_chunk_id_key" in indexes
            counts = {table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() for table in ("knowledge_documents", "document_chunks", "chunk_embeddings")}
            assert set(counts.values()) == {2}
            version = connection.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one()
        print(json.dumps({"result": "PASS", "phase": args.phase, "pgvector": version, "migrations": versions, "counts": counts, "checks": ["repeatable migrations", "matching embedding implementations", "cosine retrieval", "tenant isolation", "cross-tenant overwrite denied", "dimension rejection before replacement", "startup schema mismatch", "tenant and join indexes"]}, indent=2))
    finally:
        query.close()
        store.close()


if __name__ == "__main__":
    main()
