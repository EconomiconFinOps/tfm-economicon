from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event, text

from app.core.runtime_secrets import StartupError
from app.db.migration_runner import MigrationRunner


def test_verify_reads_complete_ledger_and_rejects_incomplete_schema(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'schema.db'))
    source = tmp_path / 'migrations'
    source.mkdir()
    (source / '001_initial.py').write_text('')
    (source / '002_next.py').write_text('')
    runner = MigrationRunner(engine, 'unused', source, 'processor_schema_migrations')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE processor_schema_migrations(version TEXT PRIMARY KEY)'))
        connection.execute(text("INSERT INTO processor_schema_migrations VALUES('001')"))
        connection.execute(text('CREATE TABLE example(id TEXT)'))
    observed = []
    event.listen(engine, 'before_cursor_execute', lambda c, cursor, statement, parameters, context, many: observed.append(statement))
    try:
        with pytest.raises(StartupError):
            runner.verify({'example': {'id'}})
        assert not any(statement.lstrip().upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE')) for statement in observed)
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO processor_schema_migrations VALUES('002')"))
        observed.clear()
        runner.verify({'example': {'id'}})
        with pytest.raises(StartupError):
            runner.verify({'example': {'id', 'missing'}})
        with pytest.raises(StartupError):
            runner.verify({'missing_table': {'id'}})
        assert not any(statement.lstrip().upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE')) for statement in observed)
    finally:
        engine.dispose()


@pytest.mark.parametrize('component', ['operational', 'vectors'])
def test_verify_mode_never_calls_migration_runner(monkeypatch, component):
    if component == 'operational':
        from app.db import database as module
        value = module.Database('sqlite://')
    else:
        from app.vector_store import pgvector_store as module
        value = module.PgVectorStore('sqlite://', 1024)
        # The existing dimension check still runs after verification.
        connection = Mock()
        connection.execute.return_value.scalar_one.return_value = 1024
        value.engine = Mock()
        value.engine.connect.return_value.__enter__ = Mock(return_value=connection)
        value.engine.connect.return_value.__exit__ = Mock(return_value=False)
    fake = Mock()
    monkeypatch.setattr(module, 'MigrationRunner', Mock(return_value=fake))
    monkeypatch.setenv('PROCESSOR_SCHEMA_MODE', 'verify')
    value.initialize()
    fake.verify.assert_called_once()
    fake.run.assert_not_called()


def test_unknown_schema_mode_fails_closed(monkeypatch):
    from app.db.database import Database
    value = Database('sqlite://')
    monkeypatch.setenv('PROCESSOR_SCHEMA_MODE', 'typo')
    try:
        with pytest.raises(StartupError):
            value.initialize()
    finally:
        value.dispose()
