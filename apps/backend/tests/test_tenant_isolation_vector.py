"""Real nearest-neighbor isolation, including final assistant context/citations."""
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.services.assistant import AssistantService
from app.services.vector_store import PgVectorQueryStore


@pytest.fixture
def retrieval(monkeypatch):
    raw = os.environ.get("JUP086_VECTOR_TEST_URL")
    if not raw:
        pytest.skip("JUP086_VECTOR_TEST_URL absent: disposable real pgvector not exercised")
    url = make_url(raw)
    assert url.drivername == "postgresql+psycopg"
    assert url.host in {"127.0.0.1", "localhost"} and url.port not in {None, 5432, 26257}
    assert url.database in {"postgres", "jup086_vectors"} and not url.query
    admin = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    name, created, store = "jup086_retrieval_" + uuid4().hex, False, None
    try:
        with admin.connect() as connection:
            assert set(connection.execute(text("SELECT datname FROM pg_database WHERE NOT datistemplate")).scalars()) <= {"postgres", "jup086_vectors"}
            assert connection.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")).scalar_one() == 0
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        store = PgVectorQueryStore(url.set(database=name))
        path = Path(__file__).resolve().parents[2] / "processor/app/vector_store/migrations/001_initial.py"
        spec = importlib.util.spec_from_file_location("jup086_vector_schema", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        monkeypatch.setenv("EMBEDDING_DIMENSION", "8")
        with store.engine.begin() as connection:
            module.upgrade(connection)
            for identifier, tenant, content, vector in (("own", "tenant-a", "own-source-content", "[0,1,0,0,0,0,0,0]"), ("foreign", "tenant-b", "foreign-secret-marker", "[1,0,0,0,0,0,0,0]")):
                params = {"id": identifier, "tenant": tenant, "content": content, "vector": vector, "now": datetime.now(timezone.utc)}
                connection.execute(text("INSERT INTO knowledge_documents VALUES (:id, :id, :tenant, :content, NULL, :content, 1, :now, :now)"), params)
                connection.execute(text("INSERT INTO document_chunks VALUES (:id, :id, 0, :content, 20, :now)"), params)
                connection.execute(text("INSERT INTO chunk_embeddings VALUES (:id, :id, CAST(:vector AS vector), 8, 'mock', :now)"), params)
        yield store
    finally:
        if store is not None:
            store.close()
        try:
            if created:
                with admin.connect() as connection:
                    connection.execute(text(f'DROP DATABASE "{name}"'))
        finally:
            admin.dispose()


@pytest.mark.parametrize(
    'tenant,expected',
    [
        pytest.param('tenant-a', ['own'], id='tenant-a-expected0'),
    ],
)
def test_filter_precedes_nearest_limit_and_excludes_foreign_context(retrieval, tenant, expected):
    result = retrieval.search_chunks(tenant, [1.0] + [0.0] * 7, top_k=1)
    assert [row["chunk_id"] for row in result] == expected
    answer = AssistantService().answer("query", result)
    if tenant != "tenant-b":
        assert "foreign" not in str(result) + str(answer)
    if tenant == "tenant-a":
        assert "own-source-content" in answer["content"]
        assert answer["citations"]
