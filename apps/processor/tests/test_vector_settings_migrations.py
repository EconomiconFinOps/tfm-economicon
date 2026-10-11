"""Exercise Settings -> store -> real migrations with an explicit SQL recorder.

The recorder replaces PostgreSQL only; these tests do not claim database
compatibility. test_vector_settings_pgvector.py verifies that separately.
"""
from contextlib import contextmanager
import importlib
import os
import re
from types import SimpleNamespace

import pytest

from app.core.config import Settings, get_settings
from app.vector_store.pgvector_store import PgVectorStore


class RecordingEngine:
    def __init__(self):
        self.statements = []
        self.versions = set()
        self.dimension = None

    @contextmanager
    def begin(self):
        yield self

    connect = begin

    def execute(self, statement, parameters=None):
        sql = str(statement).strip()
        self.statements.append(sql)
        if sql.startswith("SELECT version"):
            return [SimpleNamespace(version=version) for version in self.versions]
        if sql.startswith("INSERT INTO vector_schema_migrations"):
            self.versions.add(parameters["version"])
        if sql.startswith("CREATE TABLE chunk_embeddings"):
            self.dimension = int(re.search(r"embedding VECTOR\((\d+)\)", sql).group(1))
        if "SELECT atttypmod" in sql:
            return SimpleNamespace(scalar_one=lambda: self.dimension)
        return []


@pytest.mark.parametrize("source,expected", [
    ("default", 8),
    ("environment", 16),
    ("dotenv", 16),
    ("environment-over-dotenv", 24),
    ("settings-constructor", 32),
])
def test_initial_schema_uses_the_effective_settings_dimension(monkeypatch, tmp_path, source, expected):
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
    environment_before = dict(os.environ)
    engine = RecordingEngine()
    monkeypatch.setattr("app.vector_store.pgvector_store.create_engine", lambda *args, **kwargs: engine)
    store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)

    store.initialize()
    store.initialize()

    assert engine.dimension == expected
    assert engine.versions == {"001", "002"}
    assert sum(sql.startswith("CREATE TABLE chunk_embeddings") for sql in engine.statements) == 1
    assert sum(sql.startswith("CREATE INDEX knowledge_documents_tenant_id_idx") for sql in engine.statements) == 1
    assert dict(os.environ) == environment_before


def test_changing_environment_after_settings_and_module_import_does_not_change_schema(monkeypatch, tmp_path):
    dotenv = tmp_path / "jup102.env"
    dotenv.write_text("EMBEDDING_DIMENSION=16\n", encoding="utf-8")
    monkeypatch.setenv("ECONOMICON_ENV_FILE", str(dotenv))
    settings = get_settings()
    importlib.import_module("app.vector_store.migrations.001_initial")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "64")
    engine = RecordingEngine()
    monkeypatch.setattr("app.vector_store.pgvector_store.create_engine", lambda *args, **kwargs: engine)

    PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension).initialize()

    assert engine.dimension == settings.embedding_dimension == 16
    assert os.environ["EMBEDDING_DIMENSION"] == "64"


def test_initial_migration_requires_an_explicit_dimension_before_executing_sql():
    initial = importlib.import_module("app.vector_store.migrations.001_initial")
    connection = RecordingEngine()

    with pytest.raises(TypeError, match="embedding_dimension"):
        initial.upgrade(connection)

    assert connection.statements == []
