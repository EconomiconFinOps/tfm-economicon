"""Read-only startup on a dedicated disposable PostgreSQL server, never AWS."""
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.core.runtime_secrets import StartupError
from app.vector_store.pgvector_store import PgVectorStore
from app.aws_bootstrap_common import DatabaseRole, grant_application_roles
from test_vector_settings_pgvector import vector_database


def test_vector_startup_as_role_without_ddl_or_write_permissions(vector_database, monkeypatch):
    owner = PgVectorStore(vector_database.render_as_string(hide_password=False), 1536)
    role = 'jup131_readonly_' + uuid4().hex
    password = 'Synthetic-disposable-test-pass-131!'
    reader = None
    created = False
    try:
        owner.initialize()
        with owner.engine.begin() as connection:
            connection.execute(text(f'''CREATE ROLE "{role}" LOGIN PASSWORD 'Synthetic-disposable-test-pass-131!' '''))
            created = True
            connection.execute(text('REVOKE CREATE ON SCHEMA public FROM PUBLIC'))
            connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role}"'))
            connection.execute(text(f'GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{role}"'))
        reader = PgVectorStore(vector_database.set(username=role, password=password).render_as_string(hide_password=False), 1536)
        monkeypatch.setenv('PROCESSOR_SCHEMA_MODE', 'verify')
        reader.initialize()
        reader.initialize()
        with reader.engine.connect() as connection:
            assert connection.execute(text('SELECT current_user')).scalar_one() == role
            assert not connection.execute(text("SELECT has_schema_privilege(current_user,'public','CREATE')")).scalar_one()
        with pytest.raises(DBAPIError), reader.engine.begin() as connection:
            connection.execute(text('CREATE TABLE forbidden_startup_ddl(id INTEGER)'))
        with owner.engine.begin() as connection:
            connection.execute(text("DELETE FROM vector_schema_migrations WHERE version='005'"))
        with pytest.raises(StartupError):
            reader.initialize()
    finally:
        if reader is not None:
            reader.close()
        if created:
            with owner.engine.begin() as connection:
                connection.execute(text(f'DROP OWNED BY "{role}"'))
                connection.execute(text(f'DROP ROLE "{role}"'))
        owner.close()


def test_bootstrap_grants_are_restartable_without_application_ddl(vector_database):
    owner = create_engine(vector_database)
    roles = [DatabaseRole('economicon_backend', 'a' * 64), DatabaseRole('economicon_processor', 'b' * 64)]
    created = False
    app = None
    try:
        with owner.begin() as connection:
            assert connection.execute(text("SELECT count(*) FROM pg_roles WHERE rolname IN ('economicon_backend','economicon_processor')")).scalar_one() == 0
            connection.execute(text('CREATE TABLE bootstrap_role_probe(id INTEGER PRIMARY KEY)'))
        created = True
        grant_application_roles(owner, roles)
        grant_application_roles(owner, roles)
        assert 'a' * 64 not in repr(roles)
        app = create_engine(vector_database.set(username=roles[0].name, password=roles[0].password))
        with app.begin() as connection:
            connection.execute(text('INSERT INTO bootstrap_role_probe VALUES(1)'))
            assert connection.execute(text('SELECT id FROM bootstrap_role_probe')).scalar_one() == 1
            assert not connection.execute(text("SELECT has_schema_privilege(current_user,'public','CREATE')")).scalar_one()
        with pytest.raises(DBAPIError), app.begin() as connection:
            connection.execute(text('CREATE TABLE forbidden_bootstrap_runtime(id INTEGER)'))
        with pytest.raises(DBAPIError), app.begin() as connection:
            connection.execute(text('CREATE TEMPORARY TABLE forbidden_bootstrap_temp(id INTEGER)'))
        with pytest.raises(DBAPIError), app.begin() as connection:
            connection.execute(text('CREATE SCHEMA forbidden_bootstrap_schema'))
        with owner.connect() as connection:
            values = connection.execute(text("SELECT rolpassword FROM pg_authid WHERE rolname IN ('economicon_backend','economicon_processor')")).scalars().all()
            assert len(values) == 2 and all(value.startswith('SCRAM-SHA-256$') for value in values)
    finally:
        if app is not None:
            app.dispose()
        if created:
            with owner.begin() as connection:
                for role in roles:
                    exists = connection.execute(text('SELECT count(*) FROM pg_roles WHERE rolname=:name'), {'name': role.name}).scalar_one()
                    if exists:
                        connection.execute(text(f'DROP OWNED BY "{role.name}"'))
                        connection.execute(text(f'DROP ROLE "{role.name}"'))
        owner.dispose()
