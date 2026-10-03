"""Real nearest-neighbor isolation, including final assistant context/citations."""
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url

from app.services.assistant import AssistantService
from app.services.citations import resolve_citations
from app.services.citations import DocumentCitations
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
        pytest.param('tenant-b', ['foreign'], id='tenant-b-own-citation'),
        pytest.param('tenant-empty', [], id='empty-tenant-no-citation'),
    ],
)
def test_filter_precedes_nearest_limit_and_excludes_foreign_context(retrieval, tenant, expected):
    result = retrieval.search_chunks(tenant, [1.0] + [0.0] * 7, top_k=1)
    assert [row["chunk_id"] for row in result] == expected
    answer = AssistantService().answer("query", result)
    citations = resolve_citations(answer["citations"], result, tenant)
    assert [item["evidence_id"] for item in citations] == expected
    for citation in citations:
        assert citation["document_id"] == expected[0]
        assert citation["reference"] == f"document:{expected[0]}/chunk:0"
        assert citation["excerpt"] == result[0]["content"]
        assert citation["page"] is None
    if tenant != "tenant-b":
        assert "foreign" not in str(result) + str(answer)
    if tenant == "tenant-a":
        assert "own-source-content" in answer["content"]
        assert answer["citations"]


def test_document_text_is_fetched_and_indexed_once_for_multiple_chunks(retrieval, monkeypatch):
    from unittest.mock import Mock
    from app.services import vector_store
    document = "## Guia de C#\n" + " ".join(f"fragmento-{i}" for i in range(4))
    with retrieval.engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET text_content=:body, source='guia.md ' WHERE id='own'"), {"body": document})
        connection.execute(text("UPDATE document_chunks SET content='fragmento-0' WHERE id='own'"))
        for i in range(1, 4):
            params = {"id": f"own-{i}", "index": i, "content": f"fragmento-{i}", "now": datetime.now(timezone.utc)}
            connection.execute(text("INSERT INTO document_chunks VALUES (:id, 'own', :index, :content, 11, :now)"), params)
            connection.execute(text("INSERT INTO chunk_embeddings VALUES (:id, :id, '[0,1,0,0,0,0,0,0]'::vector, 8, 'mock', :now)"), params)
    factory = Mock(wraps=DocumentCitations)
    monkeypatch.setattr(vector_store, "DocumentCitations", factory)
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(retrieval.engine, "before_cursor_execute", capture)
    try:
        result = retrieval.search_chunks("tenant-a", [0.0, 1.0] + [0.0] * 6)
    finally:
        event.remove(retrieval.engine, "before_cursor_execute", capture)
    assert len(result) == 4
    factory.assert_called_once_with(document)
    assert len(statements) == 2
    assert "text_content" not in statements[0]
    assert "tenant_id" in statements[1]
    assert all(row["title"] == row["section"] == "Guia de C#" for row in result)
    answer = AssistantService().answer("Consulta", result)
    for index, citation in enumerate(resolve_citations(answer["citations"], result, "tenant-a"), 1):
        assert f"- [{index}] {citation['source']}: {citation['excerpt']}" in answer["content"]


def test_reingestion_does_not_mix_document_versions_between_queries(retrieval):
    def replace_after_retrieval(conn, cursor, statement, parameters, context, executemany):
        if "dc.id AS chunk_id" in statement:
            with retrieval.engine.begin() as writer:
                writer.execute(text("UPDATE knowledge_documents SET text_content='# New title', source='new-source' WHERE id='own'"))
    event.listen(retrieval.engine, "after_cursor_execute", replace_after_retrieval)
    try:
        [result] = retrieval.search_chunks("tenant-a", [0.0, 1.0] + [0.0] * 6, top_k=1)
    finally:
        event.remove(retrieval.engine, "after_cursor_execute", replace_after_retrieval)
    assert result["title"] == result["source"] == result["content"] == "own-source-content"
