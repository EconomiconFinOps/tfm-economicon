import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[3]


def fixture_inputs():
    prefix = 'arn:aws:secretsmanager:eu-west-1:123456789012:secret:'
    return dict(account_id='123456789012', region='eu-west-1', cycle_id='ensayo1', source_sha='a' * 40,
        database_endpoints={key: {'host': f'economicon-ensayo1-{key}.synthetic.eu-west-1.rds.amazonaws.com',
                                 'port': 5432, 'database': database}
                            for key, database in [('operational', 'economicon'), ('vectors', 'embeddings')]},
        database_admin_secret_arns={key: prefix + 'rds!db-' + key + '-ABC123' for key in ['operational', 'vectors']},
        runtime_secret_arns={key: prefix + 'economicon-ensayo1/' + key + '/runtime-ABC123'
                             for key in ['backend', 'processor', 'azure-cost-api']},
        mq_admin_secret_arn='arn:aws:secretsmanager:eu-west-3:123456789012:secret:synthetic-mq-ABC123')


@pytest.fixture(params=['backend', 'processor'])
def bootstrap(request):
    name = 'bootstrap_common_' + request.param
    path = ROOT / 'apps' / request.param / 'app/aws_bootstrap_common.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_explicit_ecs_mode_and_owned_resources_required(bootstrap):
    value = fixture_inputs()
    env = {'ECONOMICON_BOOTSTRAP': 'ecs', 'AWS_EXECUTION_ENV': 'AWS_ECS_FARGATE',
           'DEMO_BOOTSTRAP_INPUTS': json.dumps(value)}
    assert bootstrap.load_inputs(env) == value
    for changed in [{}, dict(env, AWS_EXECUTION_ENV='local')]:
        with pytest.raises(RuntimeError):
            bootstrap.load_inputs(changed)
    value['database_endpoints']['operational']['host'] = 'credential-sink.invalid'
    with pytest.raises(RuntimeError):
        bootstrap.load_inputs(dict(env, DEMO_BOOTSTRAP_INPUTS=json.dumps(value)))


def test_secret_reads_are_exact_allowlist_bounded_and_not_printed(bootstrap):
    client = Mock()
    client.get_secret_value.return_value = {'SecretString': '{"password":"synthetic-private-value"}'}
    factory = Mock(return_value=client)
    context = bootstrap.BootstrapContext(fixture_inputs(), factory)
    arn = fixture_inputs()['database_admin_secret_arns']['operational']
    assert context.secret(arn)['password'] == 'synthetic-private-value'
    client.get_secret_value.assert_called_once_with(SecretId=arn)
    client.get_secret_value.reset_mock()
    with pytest.raises(RuntimeError):
        context.secret(arn.replace('123456789012', '999999999999'))
    client.get_secret_value.assert_not_called()
    client.get_secret_value.return_value = {'SecretString': 'sensitive invalid JSON'}
    with pytest.raises(RuntimeError) as caught:
        context.secret(arn)
    assert 'sensitive' not in str(caught.value)


def test_bootstrap_role_identity_must_match_cycle_and_account(bootstrap):
    client = Mock()
    client.get_caller_identity.return_value = {'Account': '123456789012',
        'Arn': 'arn:aws:sts::123456789012:assumed-role/economicon-ensayo1-bootstrap/synthetic'}
    context = bootstrap.BootstrapContext(fixture_inputs(), lambda service, region: client)
    context.verify_identity()
    client.get_caller_identity.return_value['Arn'] = 'arn:aws:sts::123456789012:assumed-role/economicon-ensayo1-backend-task/synthetic'
    with pytest.raises(RuntimeError):
        context.verify_identity()


def test_app_credentials_cannot_redirect_admin_grants(bootstrap):
    context = bootstrap.BootstrapContext(fixture_inputs(), Mock())
    context.secret = Mock(side_effect=lambda arn: {
        'DATABASE_URL': 'postgresql+psycopg://economicon_backend:' + 'a' * 64 +
        '@credential-sink.invalid:5432/economicon?sslmode=verify-full'})
    with pytest.raises(RuntimeError):
        context.application_roles('operational')
