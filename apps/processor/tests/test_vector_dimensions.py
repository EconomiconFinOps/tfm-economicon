"""Reject incompatible writes before opening a transaction or deleting chunks."""
import asyncio
from unittest.mock import MagicMock, Mock

import pytest

from app.vector_store.pgvector_store import PgVectorStore
from app.core.runtime_secrets import StartupError


@pytest.mark.parametrize("dimension", [0, -1])
def test_invalid_dimension_rejected_without_connecting(dimension):
    with pytest.raises(ValueError, match="greater than zero"):
        PgVectorStore("not-a-database-url", dimension)


@pytest.mark.parametrize("vectors", [[[1.0]], [[1.0] * 8, [1.0] * 9]])
def test_bad_batch_never_begins_replacement(vectors):
    store = PgVectorStore("sqlite://", 8)
    store.engine.dispose()
    store.engine = Mock()
    with pytest.raises(ValueError, match="configured dimension"):
        store.store_document(
            job_id="existing", tenant_id="tenant-a", source="test", artifact_uri=None,
            text_content="replacement", chunks=["chunk"] * len(vectors),
            embeddings=vectors, provider_name="mock",
        )
    store.engine.begin.assert_not_called()


@pytest.fixture
def schema_store(monkeypatch):
    monkeypatch.setattr("app.vector_store.pgvector_store.MigrationRunner.run", lambda self: None)
    store = PgVectorStore("sqlite://", 8)
    store.engine.dispose()
    store.engine = MagicMock()
    return store


def stored_dimension(store, dimension):
    store.engine.connect.return_value.__enter__.return_value.execute.return_value.scalar_one.return_value = dimension


@pytest.mark.parametrize("dimension", [7, 9, -1])
def test_startup_rejects_incompatible_schema(schema_store, dimension):
    stored_dimension(schema_store, dimension)
    with pytest.raises(StartupError, match="differs from the stored vector schema"):
        schema_store.initialize()


def test_startup_accepts_matching_schema(schema_store):
    stored_dimension(schema_store, 8)
    schema_store.initialize()


def test_combined_entrypoint_preserves_actionable_dimension_error(schema_store, monkeypatch):
    from app import run_all

    stored_dimension(schema_store, 9)
    monkeypatch.setattr(run_all, "ProcessorWorker", lambda settings: schema_store.initialize())
    with pytest.raises(StartupError, match="restore the matching configuration or reindex"):
        run_all.main()


def test_api_lifespan_preserves_actionable_dimension_error(schema_store, monkeypatch):
    from app import main

    stored_dimension(schema_store, 7)
    monkeypatch.setattr(main, "Database", Mock())
    monkeypatch.setattr(main, "RabbitMQQueue", Mock())
    monkeypatch.setattr(main, "PgVectorStore", lambda *args: schema_store)

    async def start():
        async with main.lifespan(main.app):
            pytest.fail("API started with an incompatible dimension")

    with pytest.raises(StartupError, match="restore the matching configuration or reindex"):
        asyncio.run(start())
