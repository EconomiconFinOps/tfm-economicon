"""Backend runtime verifies completed schema without DDL, seeding or repair."""
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine,event,text

from app.core.runtime_secrets import StartupError
from app.db.database import Database
from test_chat_operations_jup035 import api


def writes(engine):
    observed=[]
    def before(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().split(None,1)[0].upper() in {'CREATE','ALTER','DROP','INSERT','UPDATE','DELETE','MERGE'}:
            observed.append(statement.lstrip().split(None,1)[0].upper())
    event.listen(engine,'before_cursor_execute',before)
    return observed


def test_verify_runtime_uses_existing_completed_schema_without_mutation(api,monkeypatch):
    monkeypatch.setenv('BACKEND_SCHEMA_MODE','verify')
    # SQLite's STRING affinity converts version'001' into integer1. Preserve
    # the fixture's original table and build the textual version table used by CR.
    with api[1].engine.begin() as connection:
        connection.execute(text('ALTER TABLE schema_migrations RENAME TO numeric_version_fixture_original'))
        connection.execute(text('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY,applied_at TIMESTAMPTZ)'))
        connection.execute(text("INSERT INTO schema_migrations SELECT printf('%03d',version),applied_at FROM numeric_version_fixture_original"))
    seed=[]
    monkeypatch.setattr(api[1],'_seed_defaults',lambda:seed.append('called'))
    observed=writes(api[1].engine)
    api[1].initialize()
    assert observed==[] and seed==[],{'writes':observed,'seed':seed}
    with api[1].engine.connect() as connection:
        assert connection.execute(text('SELECT COUNT(*) FROM conversations')).scalar_one()==5


@pytest.mark.parametrize('registered',['none','incomplete'])
def test_verify_missing_or_incomplete_schema_fails_closed_without_creating_it(tmp_path,monkeypatch,registered):
    monkeypatch.setenv('BACKEND_SCHEMA_MODE','verify')
    db=Database.__new__(Database)
    db.engine=create_engine('sqlite:///'+str(tmp_path/'verify-only.db'))
    # SQLite fixture adapter only for Cockroach's clock-default grammar.
    def sqlite_clock_default(connection,cursor,statement,parameters,context,many):
        return statement.replace('DEFAULT now()','DEFAULT CURRENT_TIMESTAMP').replace('version STRING PRIMARY KEY','version TEXT PRIMARY KEY'),parameters
    event.listen(db.engine,'before_cursor_execute',sqlite_clock_default,retval=True)
    seed=[]
    monkeypatch.setattr(db,'_seed_defaults',lambda:seed.append('called'))
    if registered=='incomplete':
        with db.engine.begin() as connection:
            connection.execute(text('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY,applied_at TIMESTAMPTZ)'))
            connection.execute(text("INSERT INTO schema_migrations VALUES ('001',NULL),('002',NULL)"))
    observed=writes(db.engine)
    try:
        with pytest.raises(StartupError):
            db.initialize()
        assert observed==[] and seed==[]
    finally:
        db.engine.dispose()


def textual_versions(database):
    with database.engine.begin() as connection:
        connection.execute(text('ALTER TABLE schema_migrations RENAME TO version_fixture_original'))
        connection.execute(text('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY,applied_at TIMESTAMPTZ)'))
        connection.execute(text("INSERT INTO schema_migrations SELECT printf('%03d',version),applied_at FROM version_fixture_original"))


def test_registered_version_cannot_hide_missing_chat_catalog(api,monkeypatch):
    monkeypatch.setenv('BACKEND_SCHEMA_MODE','verify')
    textual_versions(api[1])
    with api[1].engine.begin() as connection:
        connection.execute(text('ALTER TABLE chat_operations RENAME TO original_chat_fixture'))
    observed=writes(api[1].engine)
    with pytest.raises(StartupError):
        api[1].initialize()
    assert observed==[]


def test_complete_catalog_without_completed_marker_cannot_enable_chat(api,monkeypatch):
    monkeypatch.setenv('BACKEND_SCHEMA_MODE','verify')
    textual_versions(api[1])
    with api[1].engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_migrations WHERE version='002'"))
    observed=writes(api[1].engine)
    with pytest.raises(StartupError):
        api[1].initialize()
    assert observed==[]
