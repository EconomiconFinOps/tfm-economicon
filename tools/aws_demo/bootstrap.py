"""Guarded CodeBuild orchestration for private application database bootstrap.

No AWS calls on import or ordinary local execution. Secrets remain in Secrets
Manager; ECS definitions receive public references, never credential values.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
from urllib.parse import quote, urlsplit

try:
    from .control import validate_config
    from .private_tasks import PrivateTasks
except ImportError:
    from control import validate_config
    from private_tasks import PrivateTasks

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.work/aws-demo'
COMPONENTS = ('backend', 'processor', 'azure-cost-api', 'grafana')
MONITORING_KEYS = ('GF_DATABASE_PASSWORD', 'GF_SECURITY_ADMIN_PASSWORD',
                   'GF_SECURITY_SECRET_KEY', 'GRAFANA_EVALUATION_DB_PASSWORD')


class BootstrapControllerError(RuntimeError):
    pass


def check(value):
    if not value:
        raise BootstrapControllerError('Bootstrap inputs or existing credential state are invalid.')


def sdk_client(service, region):
    import boto3
    from botocore.config import Config
    return boto3.client(service, region_name=region, config=Config(
        signature_version='v4', ignore_configured_endpoint_urls=True, proxies={},
        connect_timeout=3, read_timeout=30, retries={'total_max_attempts': 1}))


def _read_secret(client, arn, config):
    metadata = client.describe_secret(SecretId=arn)
    tags = {tag['Key']: tag['Value'] for tag in metadata.get('Tags', [])}
    check(metadata['ARN'] == arn and tags.get('Project') == 'economicon'
          and tags.get('Environment') == config['cycle_id'] and not metadata.get('DeletedDate'))
    try:
        raw = client.get_secret_value(SecretId=arn)['SecretString']
    except Exception as error:
        if getattr(error, 'response', {}).get('Error', {}).get('Code') == 'ResourceNotFoundException':
            return None
        raise
    check(len(raw.encode('utf-8')) <= 16384)
    value = json.loads(raw)
    check(isinstance(value, dict))
    return value


def _write_secret(client, arn, value, config, label):
    token = hashlib.sha256((config['cycle_id'] + '/' + config['source_sha'] + '/' + label).encode()).hexdigest()
    client.put_secret_value(SecretId=arn, ClientRequestToken=token,
                            SecretString=json.dumps(value, sort_keys=True, separators=(',', ':')))


def ensure_runtime_secrets(client, config, outputs):
    cluster = 'economicon-' + config['cycle_id']
    prefix = f"arn:aws:secretsmanager:eu-west-1:{config['account_id']}:secret:{cluster}/"
    arns = outputs['runtime_secret_arns']
    check(set(arns) == set(COMPONENTS))
    for name in COMPONENTS:
        check(re.fullmatch(re.escape(prefix + name + '/runtime-') + r'[A-Za-z0-9]{6}', arns[name]))
    bundle_arn = outputs['rehearsal_secret_arn']
    check(re.fullmatch(re.escape(prefix + 'rehearsal/credentials-') + r'[A-Za-z0-9]{6}', bundle_arn))
    endpoint = urlsplit(outputs['rabbitmq_endpoints'][0])
    check(endpoint.scheme == 'amqps' and endpoint.port in {None, 5671} and not endpoint.username
          and not endpoint.password and not endpoint.query and not endpoint.fragment and endpoint.path in {'', '/'}
          and re.fullmatch(r'b-[a-f0-9-]+\.mq\.eu-west-1\.(?:amazonaws\.com|on\.aws)', endpoint.hostname or ''))
    for database, expected_name in [('operational', 'economicon'), ('vectors', 'embeddings')]:
        db = outputs['database_endpoints'][database]
        check(db['database'] == expected_name and db['port'] == 5432 and re.fullmatch(
            re.escape(cluster + '-' + database) + r'\.[a-z0-9]+\.eu-west-1\.rds\.amazonaws\.com', db['host']))
    identity = {'_schema': 1, '_cycle_id': config['cycle_id'], '_source_sha': config['source_sha']}
    bundle = _read_secret(client, bundle_arn, config)
    if bundle is None:
        bundle = dict(identity, database_passwords={name: secrets.token_hex(32) for name in ('backend', 'processor')},
                      mq_passwords={name: secrets.token_hex(32) for name in ('backend', 'processor')},
                      chat_hmac_key=secrets.token_hex(32), auth_secret_key=secrets.token_hex(32),
                      azure_token=secrets.token_hex(32), skiptoken_key=secrets.token_hex(32),
                      monitoring={key: secrets.token_hex(32) for key in MONITORING_KEYS},
                      smoke_user={'email': 'aws-defensa+' + config['cycle_id'] + '@example.com',
                                  'password': 'Ec1!' + secrets.token_hex(24)})
        _write_secret(client, bundle_arn, bundle, config, 'credentials-v1')
    check(all(bundle.get(key) == value for key, value in identity.items()))
    for field in ['chat_hmac_key', 'auth_secret_key', 'azure_token', 'skiptoken_key']:
        check(isinstance(bundle.get(field), str) and re.fullmatch(r'[0-9a-f]{64}', bundle[field]))
    for component in COMPONENTS:
        if component == 'grafana':
            check(set(bundle.get('monitoring', {})) == set(MONITORING_KEYS))
            check(all(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) for value in bundle['monitoring'].values()))
            value = dict(identity, **bundle['monitoring'])
        elif component == 'azure-cost-api':
            value = dict(identity, AZURE_COST_VALID_TOKENS=bundle['azure_token'], AZURE_COST_SKIPTOKEN_SECRET=bundle['skiptoken_key'])
        else:
            password = bundle['database_passwords'][component]
            mq_password = bundle['mq_passwords'][component]
            check(re.fullmatch(r'[0-9a-f]{64}', password) and re.fullmatch(r'[0-9a-f]{64}', mq_password))
            value = dict(identity, CHAT_HMAC_KEY=bundle['chat_hmac_key'])
            for database, key, expected_name in [('operational', 'DATABASE_URL', 'economicon'), ('vectors', 'VECTOR_DATABASE_URL', 'embeddings')]:
                db = outputs['database_endpoints'][database]
                value[key] = f"postgresql+psycopg://economicon_{component}:{password}@{db['host']}:5432/{db['database']}?sslmode=verify-full"
            value['RABBITMQ_URL'] = f"amqps://economicon_{component}:{mq_password}@{endpoint.hostname}:5671/" + quote(cluster, safe='')
            if component == 'backend':
                value['AUTH_SECRET_KEY'] = bundle['auth_secret_key']
            else:
                value['AZURE_COST_API_TOKEN'] = bundle['azure_token']
        existing = _read_secret(client, arns[component], config)
        if existing is None:
            _write_secret(client, arns[component], value, config, component + '-runtime-v1')
        else:
            check(existing == value)
    return bundle


def _load_file(name, maximum):
    path = Path(os.environ[name]).resolve()
    check(path.is_relative_to(WORK.resolve()) and path.is_file() and path.stat().st_size <= maximum)
    return path.read_bytes()


def load_control_context():
    """Shared admission before bootstrap or live acceptance may construct clients."""
    check(os.environ.get('CODEBUILD_BUILD_ID'))
    raw = _load_file('DEMO_CONFIG', 65536)
    check(os.environ['CONFIG_KEY'] == 'configs/' + hashlib.sha256(raw).hexdigest() + '.json')
    config = validate_config(json.loads(raw), os.environ['SOURCE_SHA'])
    check(datetime.now(timezone.utc) < datetime.fromisoformat(config['expires_at'].replace('Z', '+00:00')))
    outputs = json.loads(_load_file('DEMO_OUTPUTS', 65536))
    identity = sdk_client('sts', 'eu-west-1').get_caller_identity()
    role = os.environ['DEPLOY_ROLE_ARN']
    check(re.fullmatch(f"arn:aws:iam::{config['account_id']}:role/economicon-[a-z0-9-]+-deploy", role))
    check(identity['Account'] == config['account_id'] and re.fullmatch(
        f"arn:aws:sts::{config['account_id']}:assumed-role/{role.rsplit('/', 1)[-1]}/[A-Za-z0-9+=,.@_-]+", identity['Arn']))
    return config, outputs


def main():
    try:
        config, outputs = load_control_context()
        images = json.loads(_load_file('DEMO_IMAGES', 8192))
        payload = {key: config[key] for key in ('cycle_id', 'source_sha', 'account_id', 'region')}
        payload.update({key: outputs[key] for key in ('database_endpoints', 'database_admin_secret_arns',
                        'runtime_secret_arns', 'rehearsal_secret_arn', 'mq_admin_secret_arn', 'rabbitmq_console_url', 'cognito')})
        payload['embedding'] = {'dimension': 1024}
        events = []
        def record(value):
            events.append(value)
            path = WORK / 'bootstrap-tasks.json'
            temporary = WORK / 'bootstrap-tasks.tmp'
            temporary.write_text(json.dumps({'source_sha': config['source_sha'], 'cycle_id': config['cycle_id'], 'events': events}) + '\n')
            os.chmod(temporary, 0o600)
            temporary.replace(path)
        tasks = PrivateTasks(sdk_client('ecs', 'eu-west-1'), config, outputs, images, record)
        # Check every image/network/role before populating credentials.
        for component in ('backend', 'processor'):
            tasks.definition(component, 'database', payload)
        ensure_runtime_secrets(sdk_client('secretsmanager', 'eu-west-1'), config, outputs)
        for component in ('backend', 'processor'):
            tasks.run(component, 'database', payload)
        tasks.run('backend', 'broker', payload)
        tasks.run('backend', 'fixtures', payload)
        tasks.run('processor', 'fixtures', payload)
        tasks.run('backend', 'monitoring', payload)
        print(json.dumps({'phase': 'application-bootstrap', 'result': 'SUCCESS', 'application_ready': False}))
        return 0
    except Exception:
        print('Private database bootstrap failed; inspect restricted diagnostics and task manifest.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
