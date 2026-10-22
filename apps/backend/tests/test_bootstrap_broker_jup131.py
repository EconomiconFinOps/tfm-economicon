from unittest.mock import Mock

import pytest


class MemoryBroker:
    def __init__(self):
        self.values = {}
        self.writes = []
    def request(self, method, path, body=None):
        if method == 'GET':
            return self.values.get(path)
        self.writes.append((path, body))
        self.values[path] = dict(body)
        return {}


def context():
    value = Mock()
    value.inputs = dict(cycle_id='ensayo1', source_sha='a' * 40,
                        rabbitmq_console_url='https://b-01234567.mq.eu-south-2.amazonaws.com',
                        rehearsal_secret_arn='bundle', mq_admin_secret_arn='admin')
    bundle = {'_cycle_id': 'ensayo1', '_source_sha': 'a' * 40,
              'mq_passwords': {'backend': 'a' * 64, 'processor': 'b' * 64}}
    value.secret.side_effect = lambda arn: bundle if arn == 'bundle' else {'password': 'synthetic-admin-password'}
    return value


def test_broker_retries_keep_owned_vhost_and_nonadmin_users(monkeypatch):
    from app import aws_bootstrap_broker as module
    api = MemoryBroker()
    monkeypatch.setattr(module, 'BrokerAPI', lambda *args: api)
    module.configure_broker(context())
    module.configure_broker(context())
    assert api.values['/api/users/economicon_backend']['tags'] == ''
    assert api.values['/api/users/economicon_processor']['tags'] == ''
    permissions = api.values['/api/permissions/economicon-ensayo1/economicon_backend']
    assert permissions['configure'] == '^processor:jobs$'
    assert all(path.startswith(('/api/vhosts/economicon-ensayo1', '/api/users/economicon_', '/api/permissions/economicon-ensayo1/')) for path, body in api.writes)


def test_foreign_vhost_or_privileged_user_is_not_overwritten(monkeypatch):
    from app import aws_bootstrap_broker as module
    for path, body in [('/api/vhosts/economicon-ensayo1', {'description': 'foreign'}),
                       ('/api/users/economicon_backend', {'tags': ['administrator']})]:
        api = MemoryBroker()
        api.values[path] = body
        monkeypatch.setattr(module, 'BrokerAPI', lambda *args: api)
        with pytest.raises(RuntimeError):
            module.configure_broker(context())
        assert path not in [path for path, body in api.writes]


@pytest.mark.parametrize('url', ['http://b-01234567.mq.eu-south-2.amazonaws.com',
                               'https://credential-sink.invalid',
                               'https://b-01234567.mq.eu-south-2.amazonaws.com?x=1'])
def test_broker_admin_endpoint_is_exact_tls_and_never_redirected(url):
    from app.aws_bootstrap_broker import BrokerAPI
    with pytest.raises(RuntimeError):
        BrokerAPI(url, 'economicon_admin', 'synthetic-password')


def test_http_response_is_bounded_and_errors_are_sanitized(monkeypatch):
    from app import aws_bootstrap_broker as module
    connection = Mock()
    response = connection.getresponse.return_value
    response.status = 302
    response.read.return_value = b'synthetic-sensitive-upstream-body'
    monkeypatch.setattr(module.http.client, 'HTTPSConnection', Mock(return_value=connection))
    api = module.BrokerAPI('https://b-01234567.mq.eu-south-2.amazonaws.com', 'economicon_admin', 'synthetic-password')
    with pytest.raises(RuntimeError) as error:
        api.request('GET', '/api/vhosts/owned')
    assert 'sensitive' not in str(error.value)
    response.read.assert_called_once_with(65537)
    connection.close.assert_called_once()
