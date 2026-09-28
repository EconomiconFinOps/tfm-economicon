"""Opt-in real pgvector replacement, collisions, rollback and concurrent writes."""
from concurrent.futures import ThreadPoolExecutor
import importlib
import os
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.vector_store.pgvector_store import PgVectorStore
from tenant_isolation_support import snapshot


@pytest.fixture
def vector_store(monkeypatch):
    raw = os.environ.get("JUP086_VECTOR_TEST_URL")
    if not raw:
        pytest.skip("JUP086_VECTOR_TEST_URL absent: disposable real pgvector not exercised")
    url = make_url(raw)
    assert url.drivername == "postgresql+psycopg"
    assert url.host in {"127.0.0.1", "localhost"} and url.port not in {None, 5432, 26257}
    assert url.database in {"postgres", "jup086_vectors"} and not url.query
    admin = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    name = "jup086_vector_" + uuid4().hex
    created = False
    store = None
    try:
        with admin.connect() as connection:
            assert set(connection.execute(text("SELECT datname FROM pg_database WHERE NOT datistemplate")).scalars()) <= {"postgres", "jup086_vectors"}
            assert connection.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")).scalar_one() == 0
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        monkeypatch.setenv("EMBEDDING_DIMENSION", "8")
        store = PgVectorStore(url.set(database=name), 8)
        with store.engine.begin() as connection:
            importlib.import_module("app.vector_store.migrations.001_initial").upgrade(connection)
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


def document(store, job="shared-id", tenant="tenant-b", content="foreign-content-marker", embedding=None):
    return store.store_document(job_id=job, tenant_id=tenant, source="synthetic-report", artifact_uri=None, text_content=content, chunks=[content], embeddings=[embedding or [1.0] + [0.0] * 7], provider_name="mock")


def vector_snapshot(store):
    return snapshot(store, "knowledge_documents", "document_chunks", "chunk_embeddings")


def attempt(store, **kwargs):
    try:
        return document(store, **kwargs)
    except (PermissionError, LookupError, ValueError, RuntimeError, DBAPIError):
        return None


def test_foreign_global_document_id_cannot_reparent_or_delete_children(vector_store):
    document(vector_store)
    before = vector_snapshot(vector_store)
    with pytest.raises(PermissionError):
        document(vector_store, tenant="tenant-a", content="attacker-replacement")
    assert vector_snapshot(vector_store) == before


def test_foreign_global_job_id_collision_preserves_every_row(vector_store):
    document(vector_store, job="other-document")
    with vector_store.engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET job_id='shared-id' WHERE id='other-document'"))
    before = vector_snapshot(vector_store)
    attempt(vector_store, tenant="tenant-a", content="attacker-replacement")
    assert vector_snapshot(vector_store) == before






def test_failed_same_tenant_replacement_rolls_back_deletion_and_children(vector_store):
    document(vector_store, tenant="tenant-a", content="original")
    before = vector_snapshot(vector_store)
    with pytest.raises((ValueError, DBAPIError)):
        document(vector_store, tenant="tenant-a", content="replacement", embedding=[1.0, 0.0])
    assert vector_snapshot(vector_store) == before




def test_concurrent_foreign_replacements_preserve_existing_owner(vector_store):
    document(vector_store)
    before = vector_snapshot(vector_store)
    barrier = Barrier(2)

    def write(tenant):
        barrier.wait(timeout=10)
        return attempt(vector_store, tenant=tenant, content="attacker-" + tenant)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(write, tenant) for tenant in ("tenant-a", "tenant-c")]
        for future in futures:
            future.result(timeout=20)
    assert vector_snapshot(vector_store) == before
