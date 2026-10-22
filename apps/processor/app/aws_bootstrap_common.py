"""Guarded private bootstrap primitives, kept identical in both app images."""
from dataclasses import dataclass, field
import json
import os
import re
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url


class BootstrapError(RuntimeError):
    pass


def require(value):
    if not value:
        raise BootstrapError('Private bootstrap configuration or dependency is invalid.')


def load_inputs(environment=None):
    env = os.environ if environment is None else environment
    try:
        require(env.get('ECONOMICON_BOOTSTRAP') == 'ecs' and env.get('AWS_EXECUTION_ENV') == 'AWS_ECS_FARGATE')
        raw = env['DEMO_BOOTSTRAP_INPUTS']
        require(len(raw.encode('utf-8')) <= 16384)
        value = json.loads(raw)
        require(value['region'] == 'eu-south-2' and re.fullmatch(r'[0-9]{12}', value['account_id']))
        require(re.fullmatch(r'(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})', value['cycle_id']))
        require(re.fullmatch(r'[0-9a-f]{40}', value['source_sha']))
        cluster = 'economicon-' + value['cycle_id']
        for key, name in [('operational', 'economicon'), ('vectors', 'embeddings')]:
            endpoint = value['database_endpoints'][key]
            require(endpoint['database'] == name and endpoint['port'] == 5432)
            require(re.fullmatch(re.escape(cluster + '-' + key) + r'\.[a-z0-9]+\.eu-south-2\.rds\.amazonaws\.com', endpoint['host']))
        prefix = f"arn:aws:secretsmanager:eu-south-2:{value['account_id']}:secret:"
        for key in ['operational', 'vectors']:
            require(re.fullmatch(re.escape(prefix) + r'rds!db-[A-Za-z0-9-]+', value['database_admin_secret_arns'][key]))
        for key in ['backend', 'processor', 'azure-cost-api']:
            require(re.fullmatch(re.escape(prefix + cluster + '/' + key + '/runtime-') + r'[A-Za-z0-9]{6}', value['runtime_secret_arns'][key]))
        return value
    except Exception:
        raise BootstrapError('Explicit ECS bootstrap and owned resource references are required.') from None


@dataclass(frozen=True)
class DatabaseRole:
    name: str
    password: str = field(repr=False)


class BootstrapContext:
    def __init__(self, inputs, client_factory):
        self.inputs, self.client = inputs, client_factory

    def verify_identity(self):
        value = self.client('sts', 'eu-south-2').get_caller_identity()
        account, cycle = self.inputs['account_id'], self.inputs['cycle_id']
        require(value['Account'] == account and re.fullmatch(
            f'arn:aws:sts::{account}:assumed-role/economicon-{cycle}-bootstrap/[A-Za-z0-9+=,.@_-]+', value['Arn']))

    def secret(self, arn):
        allowed = set(self.inputs['database_admin_secret_arns'].values()) | set(self.inputs['runtime_secret_arns'].values())
        if self.inputs.get('mq_admin_secret_arn'):
            allowed.add(self.inputs['mq_admin_secret_arn'])
        if self.inputs.get('rehearsal_secret_arn'):
            allowed.add(self.inputs['rehearsal_secret_arn'])
        require(arn in allowed)
        try:
            region = arn.split(':')[3]
            require(region in {'eu-south-2', 'eu-west-3'} and arn.split(':')[4] == self.inputs['account_id'])
            raw = self.client('secretsmanager', region).get_secret_value(SecretId=arn)['SecretString']
            require(len(raw.encode('utf-8')) <= 16384)
            value = json.loads(raw)
            require(isinstance(value, dict))
            return value
        except Exception:
            raise BootstrapError('Private bootstrap secret is unavailable or invalid.') from None

    def admin_engine(self, database):
        from app.aws_runtime import rds_root_certificate
        endpoint = self.inputs['database_endpoints'][database]
        secret = self.secret(self.inputs['database_admin_secret_arns'][database])
        require(secret['username'] == 'economicon_admin' and isinstance(secret['password'], str) and len(secret['password']) >= 12)
        url = URL.create('postgresql+psycopg', username=secret['username'], password=secret['password'],
                         host=endpoint['host'], port=5432, database=endpoint['database'],
                         query={'sslmode': 'verify-full', 'connect_timeout': '5'})
        return create_engine(url, pool_pre_ping=True, connect_args={'sslrootcert': rds_root_certificate()})

    def application_roles(self, database):
        key = 'DATABASE_URL' if database == 'operational' else 'VECTOR_DATABASE_URL'
        expected = self.inputs['database_endpoints'][database]
        roles = []
        for component in ['backend', 'processor']:
            url = make_url(self.secret(self.inputs['runtime_secret_arns'][component])[key])
            name = 'economicon_' + component
            require(url.drivername == 'postgresql+psycopg' and url.host == expected['host']
                    and url.port == expected['port'] and url.database == expected['database']
                    and url.username == name and isinstance(url.password, str)
                    and re.fullmatch(r'[a-f0-9]{64}', url.password)
                    and dict(url.query) == {'sslmode': 'verify-full'})
            roles.append(DatabaseRole(name, url.password))
        return roles


def grant_application_roles(engine, roles):
    """Owner migrates; application logins receive DML, never ownership or DDL."""
    from psycopg import sql
    require({role.name for role in roles} == {'economicon_backend', 'economicon_processor'})
    with engine.begin() as connection:
        raw = connection.connection.driver_connection
        def execute(statement):
            connection.exec_driver_sql(statement.as_string(raw))
        database = connection.execute(text('SELECT current_database()')).scalar_one()
        execute(sql.SQL('REVOKE CREATE ON SCHEMA public FROM PUBLIC'))
        execute(sql.SQL('REVOKE CREATE,TEMPORARY ON DATABASE {} FROM PUBLIC').format(sql.Identifier(database)))
        for role in roles:
            require(isinstance(role.password, str) and re.fullmatch(r'[a-f0-9]{64}', role.password))
            existing = connection.execute(text('''SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls
                FROM pg_roles WHERE rolname=:name'''), {'name': role.name}).first()
            if existing:
                require(not any(existing))
                require(connection.execute(text('SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()')).scalar_one() != role.name)
                require(not connection.execute(text('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': role.name}).scalar_one())
                require(not connection.execute(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=:name)'), {'name': role.name}).scalar_one())
            else:
                execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS').format(sql.Identifier(role.name)))
            verifier = raw.pgconn.encrypt_password(role.password.encode(), role.name.encode(), b'scram-sha-256').decode()
            execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role.name), sql.Literal(verifier)))
            execute(sql.SQL('REVOKE CREATE,TEMPORARY ON DATABASE {} FROM {}').format(sql.Identifier(database), sql.Identifier(role.name)))
            execute(sql.SQL('REVOKE CREATE ON SCHEMA public FROM {}').format(sql.Identifier(role.name)))
            execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(database), sql.Identifier(role.name)))
            execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role.name)))
            execute(sql.SQL('GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(role.name)))
            execute(sql.SQL('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(role.name)))
            execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO {}').format(sql.Identifier(role.name)))
            execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,SELECT ON SEQUENCES TO {}').format(sql.Identifier(role.name)))


def run_entrypoint(component, execute):
    try:
        inputs = load_inputs()
        require(len(sys.argv) == 2 and sys.argv[1] in {'database', 'fixtures', 'broker', 'reindex'})
        import boto3
        from botocore.config import Config
        config = Config(signature_version='v4', ignore_configured_endpoint_urls=True, proxies={},
                        connect_timeout=3, read_timeout=30, retries={'total_max_attempts': 1})
        context = BootstrapContext(inputs, lambda service, region: boto3.client(service, region_name=region, config=config))
        context.verify_identity()
        execute(context, sys.argv[1])
        print(json.dumps({'component': component, 'phase': sys.argv[1], 'result': 'SUCCESS'}))
        return 0
    except Exception:
        print('Private application bootstrap failed; configuration or dependency rejected.', file=sys.stderr)
        return 1
