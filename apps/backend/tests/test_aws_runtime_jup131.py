"""Private ECS chat startup; no AWS or metadata requests during these tests."""
import importlib.util
from pathlib import Path
import stat
import sys
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[3]
KEY = 'a1' * 32
METADATA = {'Networks': [{'NetworkMode': 'awsvpc', 'IPv4Addresses': ['10.0.10.42']}]}


@pytest.fixture(params=['backend', 'processor'])
def runtime(request):
    path = ROOT / 'apps' / request.param / 'app/aws_runtime.py'
    spec = importlib.util.spec_from_file_location('aws_runtime_' + request.param, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment():
    return {'ECONOMICON_AWS_RUNTIME': 'ecs', 'AWS_EXECUTION_ENV': 'AWS_ECS_FARGATE',
            'CHAT_ENABLED': 'true', 'CHAT_HMAC_KEY': KEY,
            'DATABASE_URL': 'postgresql+psycopg://synthetic:fixture@db.eu-south-2.rds.amazonaws.com/fixture?sslmode=verify-full',
            'VECTOR_DATABASE_URL': 'postgresql+psycopg://synthetic:fixture@vectors.eu-south-2.rds.amazonaws.com/fixture?sslmode=verify-full',
            'ECS_CONTAINER_METADATA_URI_V4': 'http://169.254.170.2/v4/synthetic-container'}


@pytest.mark.parametrize('component', ['backend', 'processor'])
def test_key_is_private_and_listener_uses_task_address(runtime, tmp_path, component):
    env = environment()
    fetch = Mock(return_value=METADATA)
    runtime.prepare_runtime(component, environment=env, runtime_parent=tmp_path, metadata_fetcher=fetch)
    assert 'CHAT_HMAC_KEY' not in env
    name = 'CHAT_SERVICE_HMAC_KEY_FILE' if component == 'backend' else 'CHAT_SIGNING_KEY_FILE'
    path = Path(env[name])
    assert path.read_bytes() == KEY.encode()
    assert path.parent.parent == tmp_path
    if sys.platform != 'win32':
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    if component == 'processor':
        assert env['PROCESSOR_CHAT_BIND_HOST'] == '10.0.10.42'
        fetch.assert_called_once_with(env['ECS_CONTAINER_METADATA_URI_V4'])
    else:
        fetch.assert_not_called()


def test_local_mode_preserves_existing_file_configuration(runtime, tmp_path):
    env = {'CHAT_ENABLED': 'true', 'CHAT_SIGNING_KEY_FILE': '/existing/secret'}
    fetch = Mock(side_effect=AssertionError('No metadata access outside explicit ECS mode'))
    runtime.prepare_runtime('processor', environment=env, runtime_parent=tmp_path, metadata_fetcher=fetch)
    assert env == {'CHAT_ENABLED': 'true', 'CHAT_SIGNING_KEY_FILE': '/existing/secret'}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('key', ['', 'short-secret', KEY + '\n', 'z' * 64])
def test_invalid_key_fails_safely_without_retaining_secret(runtime, tmp_path, key):
    env = environment()
    env['CHAT_HMAC_KEY'] = key
    with pytest.raises(RuntimeError) as caught:
        runtime.prepare_runtime('backend', environment=env, runtime_parent=tmp_path)
    assert key == '' or key not in str(caught.value)
    assert 'CHAT_HMAC_KEY' not in env
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('addresses', [[], ['127.0.0.1'], ['0.0.0.0'], ['169.254.170.2'],
                                    ['8.8.8.8'], ['10.0.0.1', '10.0.0.2']])
def test_processor_rejects_missing_public_or_ambiguous_address(runtime, tmp_path, addresses):
    env = environment()
    fetch = Mock(return_value={'Networks': [{'NetworkMode': 'awsvpc', 'IPv4Addresses': addresses}]})
    with pytest.raises(RuntimeError):
        runtime.prepare_runtime('processor', environment=env, runtime_parent=tmp_path, metadata_fetcher=fetch)
    assert 'CHAT_HMAC_KEY' not in env
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('uri', ['http://attacker.invalid/v4/x', 'http://169.254.169.254/v4/x',
                              'https://169.254.170.2/v4/x', 'http://169.254.170.2/v4/x?redirect=1'])
def test_metadata_endpoint_cannot_be_redirected(runtime, monkeypatch, uri):
    http = Mock(side_effect=AssertionError('Unreviewed metadata destination'))
    monkeypatch.setattr(runtime.http.client, 'HTTPConnection', http)
    with pytest.raises(RuntimeError):
        runtime.fetch_metadata(uri)
    http.assert_not_called()


@pytest.mark.parametrize('mode', ['disable', 'prefer', 'require', 'verify-ca', 'verify-full&sslmode=disable'])
def test_ecs_requires_server_identity_verification(runtime, tmp_path, mode):
    env = environment()
    env['DATABASE_URL'] = env['DATABASE_URL'].replace('verify-full', mode)
    with pytest.raises(RuntimeError):
        runtime.prepare_runtime('backend', environment=env, runtime_parent=tmp_path)
    assert 'CHAT_HMAC_KEY' not in env
    assert not list(tmp_path.iterdir())


def test_pinned_ca_is_used_even_when_chat_is_disabled(runtime, tmp_path):
    env = environment()
    env.update(CHAT_ENABLED='false', PGSSLROOTCERT='/untrusted/ca.pem')
    runtime.prepare_runtime('backend', environment=env, runtime_parent=tmp_path)
    assert Path(env['PGSSLROOTCERT']).name == 'rds-eu-south-2.pem'
    assert Path(env['PGSSLROOTCERT']).is_file()
    assert not list(tmp_path.iterdir())


def test_missing_or_modified_ca_fails_before_startup(runtime, tmp_path, monkeypatch):
    path = tmp_path / 'modified-ca.pem'
    path.write_text('untrusted synthetic certificate')
    monkeypatch.setattr(runtime, 'RDS_CA_PATH', path, raising=False)
    env = environment()
    with pytest.raises(RuntimeError):
        runtime.prepare_runtime('backend', environment=env, runtime_parent=tmp_path)
    assert 'CHAT_HMAC_KEY' not in env
