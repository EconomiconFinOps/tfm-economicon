"""IAM uses the task credential chain and cannot redirect signed S3 requests."""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(params=['backend', 'processor'])
def storage_module(request):
    folder = 'services' if request.param == 'backend' else 'documents'
    path = ROOT / 'apps' / request.param / 'app' / folder / 'document_storage.py'
    name = 'document_iam_' + request.param
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def iam_env(monkeypatch):
    for name in ('DOCUMENT_S3_ACCESS_KEY', 'DOCUMENT_S3_SECRET_KEY', 'DOCUMENT_S3_PUBLIC_ENDPOINT'):
        monkeypatch.delenv(name, raising=False)
    for name, value in {
        'DOCUMENT_S3_AUTH_MODE': 'iam', 'DOCUMENT_S3_REGION': 'eu-west-1',
        'DOCUMENT_S3_ENDPOINT': 'https://s3.eu-west-1.amazonaws.com',
        'DOCUMENT_S3_BUCKET': 'economicon-synthetic-documents',
        'RUNTIME_ENVIRONMENT': 'production',
    }.items():
        monkeypatch.setenv(name, value)


def test_role_credentials_sign_upload_without_static_keys(storage_module, iam_env, monkeypatch):
    import boto3
    clients = []
    def client(service, **options):
        assert service == 's3'
        assert not any(key.startswith('aws_') for key in options)
        assert options['region_name'] == 'eu-west-1'
        assert options['config'].ignore_configured_endpoint_urls is True
        assert options['config'].proxies == {}
        value = Mock()
        clients.append(value)
        return value
    monkeypatch.setattr(boto3, 'client', client)
    store = storage_module.S3Storage()
    store.presign('staging/tenant/user/upload', 42)
    args = clients[1].generate_presigned_url.call_args
    assert args.args == ('put_object',)
    assert args.kwargs['Params']['ContentLength'] == 42
    assert args.kwargs['ExpiresIn'] == 180
    store.close()
    assert all(value.close.call_count == 1 for value in clients)


def test_real_presigner_keeps_temporary_session_token(storage_module, iam_env, monkeypatch):
    import boto3
    session = boto3.Session(aws_access_key_id='ASIASYNTHETICFIXTURE',
                            aws_secret_access_key='synthetic-secret-never-accepted-by-aws',
                            aws_session_token='synthetic-temporary-session')
    monkeypatch.setattr(boto3, 'client', session.client)
    store = storage_module.S3Storage()
    try:
        parsed = urlsplit(store.presign('staging/tenant/user/upload', 42))
        query = parse_qs(parsed.query)
        assert parsed.scheme == 'https'
        assert parsed.netloc == 's3.eu-west-1.amazonaws.com'
        assert parsed.path == '/economicon-synthetic-documents/staging/tenant/user/upload'
        assert query['X-Amz-Security-Token'] == ['synthetic-temporary-session']
        assert query['X-Amz-Expires'] == ['180']
        assert 'content-length' in query['X-Amz-SignedHeaders'][0]
    finally:
        store.close()


@pytest.mark.parametrize('name,value', [
    ('DOCUMENT_S3_ENDPOINT', 'https://signed-requests.attacker.invalid'),
    ('DOCUMENT_S3_PUBLIC_ENDPOINT', 'https://signed-requests.attacker.invalid'),
    ('DOCUMENT_S3_ENDPOINT', 'http://s3.eu-west-1.amazonaws.com'),
    ('DOCUMENT_S3_REGION', 'us-east-1'),
    ('DOCUMENT_S3_ACCESS_KEY', 'synthetic-static-key'),
    ('DOCUMENT_S3_SECRET_KEY', 'synthetic-static-secret'),
    ('DOCUMENT_S3_AUTH_MODE', 'guess'),
])
def test_rejects_ambiguous_credentials_or_unreviewed_endpoint(storage_module, iam_env, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        storage_module.StorageConfig.from_env()


def test_legacy_static_storage_remains_explicit(storage_module, monkeypatch):
    monkeypatch.delenv('DOCUMENT_S3_AUTH_MODE', raising=False)
    for name, value in {
        'DOCUMENT_S3_ENDPOINT': 'http://minio:9000',
        'DOCUMENT_S3_PUBLIC_ENDPOINT': 'http://localhost:9000',
        'DOCUMENT_S3_BUCKET': 'local-documents', 'DOCUMENT_S3_ACCESS_KEY': 'synthetic-access',
        'DOCUMENT_S3_SECRET_KEY': 'synthetic-secret', 'RUNTIME_ENVIRONMENT': 'development',
    }.items():
        monkeypatch.setenv(name, value)
    value = storage_module.StorageConfig.from_env()
    assert value.auth_mode == 'static'
    assert value.access_key == 'synthetic-access'
    assert 'synthetic-secret' not in repr(value)
