"""Private Atlas import. No database/network calls on import; no model execution."""
import hashlib
from pathlib import Path
import re

from psycopg import sql
from sqlalchemy import text

from app.aws_bootstrap_common import require

SQL_PATH = Path(__file__).parent / 'aws_atlas_data/evaluations.sql'
SQL_SHA256 = 'b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09'
READER = 'grafana_evaluation_reader'
METADATA_ROLE = 'economicon_grafana'


def import_evaluations(engine):
    raw = SQL_PATH.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SQL_SHA256)
    # The artifact is preserved byte-for-byte. psycopg supplies ON_ERROR_STOP
    # and the transaction, so remove only psql's one directive and BEGIN/COMMIT.
    script = raw.decode('utf-8').removeprefix('\\set ON_ERROR_STOP on').strip()
    require(script.startswith('BEGIN;') and script.endswith('COMMIT;'))
    script = script[len('BEGIN;'):-len('COMMIT;')]
    with engine.begin() as connection:
        with connection.connection.driver_connection.cursor() as cursor:
            cursor.execute(script, prepare=False)
            while cursor.nextset():
                pass


def _login(connection, name, password, *, reader=False):
    require(name in {READER, METADATA_ROLE} and isinstance(password, str)
            and re.fullmatch('[a-f0-9]{64}', password))
    raw = connection.connection.driver_connection
    def execute(statement):
        connection.exec_driver_sql(statement.as_string(raw))
    existing = connection.execute(text('SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=:name'), {'name': name}).first()
    if existing:
        require(not any(existing))
        require(not connection.execute(text('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': name}).scalar_one())
        if reader:
            require(not connection.execute(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': name}).scalar_one())
            require(not connection.execute(text('SELECT count(*) FROM pg_namespace WHERE nspowner=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': name}).scalar_one())
            require(not connection.execute(text('SELECT count(*) FROM pg_database WHERE datdba=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': name}).scalar_one())
    else:
        execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS').format(sql.Identifier(name)))
    verifier = raw.pgconn.encrypt_password(password.encode(), name.encode(), b'scram-sha-256').decode()
    execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(name), sql.Literal(verifier)))
    return execute


def configure_reader(engine, password):
    with engine.begin() as c:
        execute = _login(c, READER, password, reader=True)
        database = c.execute(text('SELECT current_database()')).scalar_one()
        execute(sql.SQL('REVOKE CREATE,TEMPORARY ON DATABASE {} FROM PUBLIC').format(sql.Identifier(database)))
        execute(sql.SQL('REVOKE CREATE ON SCHEMA public FROM PUBLIC'))
        for schema in ('public', 'evaluation'):
            execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM {}').format(sql.Identifier(schema), sql.Identifier(READER)))
            execute(sql.SQL('REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM {}').format(sql.Identifier(schema), sql.Identifier(READER)))
            execute(sql.SQL('REVOKE ALL ON ALL SEQUENCES IN SCHEMA {} FROM {}').format(sql.Identifier(schema), sql.Identifier(READER)))
        execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM {}').format(sql.Identifier(database), sql.Identifier(READER)))
        execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(database), sql.Identifier(READER)))
        execute(sql.SQL('GRANT USAGE ON SCHEMA evaluation TO {}').format(sql.Identifier(READER)))
        execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA evaluation TO {}').format(sql.Identifier(READER)))
        execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA evaluation GRANT SELECT ON TABLES TO {}').format(sql.Identifier(READER)))


def configure_metadata(engine, password):
    """Dedicated DB on the existing RDS instance; no additional AWS database."""
    with engine.begin() as c:
        _login(c, METADATA_ROLE, password)
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
        admin = c.execute(text('SELECT current_user')).scalar_one()
        c.exec_driver_sql(sql.SQL('GRANT {} TO {}').format(sql.Identifier(METADATA_ROLE), sql.Identifier(admin)).as_string(c.connection.driver_connection))
        owner = c.execute(text("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='grafana'")).scalar_one_or_none()
        if owner is None:
            c.exec_driver_sql('CREATE DATABASE grafana OWNER economicon_grafana')
        else:
            require(owner == METADATA_ROLE)
        c.exec_driver_sql('REVOKE ALL ON DATABASE grafana FROM PUBLIC')


def prepare_monitoring(context):
    values = context.secret(context.inputs['runtime_secret_arns']['grafana'])
    engine = context.admin_engine('vectors')
    try:
        import_evaluations(engine)
        configure_reader(engine, values['GRAFANA_EVALUATION_DB_PASSWORD'])
        configure_metadata(engine, values['GF_DATABASE_PASSWORD'])
    finally:
        engine.dispose()
