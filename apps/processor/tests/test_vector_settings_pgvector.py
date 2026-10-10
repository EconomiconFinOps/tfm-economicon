"""Opt-in JUP-102 acceptance against a disposable PostgreSQL + pgvector server.

Set JUP102_VECTOR_TEST_URL to an authenticated postgresql+psycopg URL whose
database is postgres, on localhost and a non-default port. The server must have
no user databases or public tables. Each test creates and drops only its own
UUID-named database; the caller owns the container/volume lifecycle. Never point
this fixture at an application server, and do not run it in parallel processes.
"""
import importlib.util
import os
from pathlib import Path
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings
from app.core.runtime_secrets import StartupError
from app.embeddings.providers import MockEmbeddingProvider
from app.vector_store.pgvector_store import PgVectorStore


@pytest.fixture
def vector_database():
    raw = os.environ.get("JUP102_VECTOR_TEST_URL")
    if not raw:
        pytest.skip("JUP102_VECTOR_TEST_URL absent: real PostgreSQL acceptance not exercised")
    url = make_url(raw)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.port is None or not 1024 <= url.port <= 65535
        or url.port in {5432, 26257}
        or url.database != "postgres" or url.query
        or not url.username or not url.password
    ):
        raise RuntimeError("Unsafe test URL: use a disposable authenticated loopback server")
    admin = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    name = "jup102_vector_" + uuid4().hex
    created = False
    try:
        with admin.connect() as connection:
            databases = set(connection.execute(text(
                "SELECT datname FROM pg_database WHERE NOT datistemplate"
            )).scalars())
            if databases != {"postgres"}:
                raise RuntimeError("Refusing a server with pre-existing user databases")
            if connection.execute(text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            )).scalar_one():
                raise RuntimeError("Refusing an administration database with public tables")
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        yield url.set(database=name)
    finally:
        try:
            if created:
                with admin.connect() as connection:
                    connection.execute(text(f'DROP DATABASE "{name}"'))
        finally:
            admin.dispose()


@pytest.fixture
def backend_query_store(monkeypatch):
    """Import the actual backend implementation and its actual local dependencies.

    Processor and backend both use the top-level package app. Temporary module
    entries let the backend query implementation run without replacing the
    processor package or introducing a query/citation test double.
    """
    backend = Path(__file__).resolve().parents[2] / "backend" / "app"

    def load(name, relative):
        spec = importlib.util.spec_from_file_location(name, backend / relative)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module

    load("app.schemas.assistant", "schemas/assistant.py")
    load("app.services.citations", "services/citations.py")
    return load("jup102_backend_vector_store", "services/vector_store.py").PgVectorQueryStore


def snapshot(store):
    queries = {
        "columns": """
            SELECT c.oid, c.relname, a.attname, a.atttypid::regtype::text,
                   a.atttypmod, a.attnotnull
            FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND c.relkind='r'
              AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY c.relname, a.attnum
        """,
        "indexes": "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY indexname",
        "ledger": "SELECT version, applied_at FROM vector_schema_migrations ORDER BY version",
        "documents": "SELECT * FROM knowledge_documents ORDER BY id",
        "chunks": "SELECT * FROM document_chunks ORDER BY id",
        "embeddings": "SELECT id, chunk_id, embedding::text, dimension, provider, created_at FROM chunk_embeddings ORDER BY id",
    }
    with store.engine.connect() as connection:
        return {name: [tuple(row) for row in connection.execute(text(query))] for name, query in queries.items()}


def seed(store):
    embed = MockEmbeddingProvider(store.embedding_dimension).embed
    for tenant, content in (("jup102-a", "synthetic compute rightsizing"),
                            ("jup102-b", "synthetic private storage costs")):
        store.store_document(
            job_id=tenant, tenant_id=tenant, source="jup102-synthetic", artifact_uri=None,
            text_content=content, chunks=[content], embeddings=[embed(content)], provider_name="mock",
        )
    return embed


@pytest.mark.parametrize("source,expected", [
    ("default", 8),
    ("environment", 16),
    ("dotenv", 16),
    ("environment-over-dotenv", 24),
    ("settings-constructor", 32),
])
def test_new_schema_settings_sources_and_real_retrieval(
    vector_database, backend_query_store, monkeypatch, tmp_path, source, expected,
):
    monkeypatch.setenv("VECTOR_DATABASE_URL", vector_database.render_as_string(hide_password=False))
    dotenv = tmp_path / "jup102.env"
    dotenv.write_text("EMBEDDING_DIMENSION=16\n", encoding="utf-8")
    if source in {"dotenv", "environment-over-dotenv", "settings-constructor"}:
        monkeypatch.setenv("ECONOMICON_ENV_FILE", str(dotenv))
    if source == "environment":
        monkeypatch.setenv("EMBEDDING_DIMENSION", "16")
    elif source in {"environment-over-dotenv", "settings-constructor"}:
        monkeypatch.setenv("EMBEDDING_DIMENSION", "24")
    settings = (
        Settings(_env_file=dotenv, embedding_dimension=32)
        if source == "settings-constructor" else get_settings()
    )
    assert settings.embedding_dimension == expected
    store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)
    query = backend_query_store(vector_database)
    try:
        store.initialize()
        assert query.embedding_column_dimension() == expected
        query.verify_dimension(expected)
        embed = seed(store)
        before = snapshot(store)
        store.initialize()
        assert snapshot(store) == before
        assert [version for version, _ in before["ledger"]] == ["001", "002"]
        assert {row[3] for row in before["embeddings"]} == {expected}
        assert len(before["embeddings"]) == 2
        assert any(name == "knowledge_documents_tenant_id_idx" for name, _ in before["indexes"])
        own = query.search_chunks("jup102-a", embed("synthetic compute rightsizing"), provider="mock")
        assert len(own) == 1 and own[0]["tenant_id"] == "jup102-a"
        assert own[0]["content"] == "synthetic compute rightsizing"
        assert own[0]["distance"] == pytest.approx(0.0, abs=1e-6)
        foreign_nearest = query.search_chunks("jup102-a", embed("synthetic private storage costs"), provider="mock")
        assert [row["document_id"] for row in foreign_nearest] == ["jup102-a"]
        assert query.search_chunks("jup102-empty", embed("synthetic compute rightsizing")) == []
    finally:
        query.close()
        store.close()


@pytest.mark.parametrize("stored_dimension,incompatible_dimension", [
    (16, 8), (16, 32), (8, 16),
], ids=["smaller-16-to-8", "larger-16-to-32", "legacy-8-to-16"])
def test_existing_vectors_schema_and_ledger_survive_incompatible_restart(
    vector_database, monkeypatch, tmp_path, stored_dimension, incompatible_dimension,
):
    monkeypatch.setenv("VECTOR_DATABASE_URL", vector_database.render_as_string(hide_password=False))
    dotenv = tmp_path / "jup102.env"
    dotenv.write_text(f"EMBEDDING_DIMENSION={stored_dimension}\n", encoding="utf-8")
    monkeypatch.setenv("ECONOMICON_ENV_FILE", str(dotenv))
    settings = get_settings()
    store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)
    mismatch = PgVectorStore(vector_database, incompatible_dimension)
    try:
        store.initialize()
        seed(store)
        before = snapshot(store)

        with pytest.raises(StartupError, match="restore the matching configuration or reindex"):
            mismatch.initialize()

        assert snapshot(store) == before
        store.initialize()
        assert snapshot(store) == before
    finally:
        mismatch.close()
        store.close()
