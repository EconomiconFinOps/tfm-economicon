"""Private RabbitMQ management bootstrap; never follows redirects or logs bodies."""
import base64
import http.client
import json
import re
import ssl
from urllib.parse import quote, urlsplit

from app.aws_bootstrap_common import BootstrapError, require


class BrokerAPI:
    def __init__(self, url, username, password):
        parsed = urlsplit(url)
        require(parsed.scheme == 'https' and parsed.port in {None, 443} and not parsed.username
                and not parsed.password and not parsed.query and not parsed.fragment and parsed.path in {'', '/'}
                and re.fullmatch(r'b-[a-f0-9-]+\.mq\.eu-south-2\.(?:amazonaws\.com|on\.aws)', parsed.hostname or ''))
        require(username == 'economicon_admin' and isinstance(password, str) and 12 <= len(password) <= 250)
        self.host = parsed.hostname
        self.authorization = 'Basic ' + base64.b64encode((username + ':' + password).encode()).decode('ascii')

    def request(self, method, path, body=None):
        require(method in {'GET', 'PUT'} and path.startswith('/api/') and '?' not in path)
        connection = None
        try:
            payload = None if body is None else json.dumps(body, separators=(',', ':'), allow_nan=False).encode()
            require(payload is None or len(payload) <= 16384)
            connection = http.client.HTTPSConnection(self.host, 443, timeout=15, context=ssl.create_default_context())
            connection.request(method, path, body=payload,
                               headers={'Authorization': self.authorization, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            raw = response.read(65537)
            require(len(raw) <= 65536)
            if response.status == 404 and method == 'GET':
                return None
            require(response.status in {200, 201, 204})
            value = json.loads(raw) if raw else {}
            require(isinstance(value, dict))
            return value
        except Exception:
            raise BootstrapError('Private broker management request failed.') from None
        finally:
            if connection is not None:
                connection.close()


def configure_broker(context):
    config = context.inputs
    bundle = context.secret(config['rehearsal_secret_arn'])
    require(bundle['_cycle_id'] == config['cycle_id'] and bundle['_source_sha'] == config['source_sha'])
    passwords = bundle['mq_passwords']
    require(all(isinstance(passwords.get(name), str) and re.fullmatch(r'[a-f0-9]{64}', passwords[name])
                for name in ('backend', 'processor')))
    admin = context.secret(config['mq_admin_secret_arn'])
    api = BrokerAPI(config['rabbitmq_console_url'], 'economicon_admin', admin['password'])
    vhost = quote('economicon-' + config['cycle_id'], safe='')
    marker = 'JUP-131:' + config['cycle_id'] + ':' + config['source_sha']
    path = '/api/vhosts/' + vhost
    current = api.request('GET', path)
    if current is not None:
        require(current.get('description', current.get('metadata', {}).get('description')) == marker)
    # Inspect both accounts before modifying either one.
    for component in ('backend', 'processor'):
        current_user = api.request('GET', '/api/users/economicon_' + component)
        require(current_user is None or current_user.get('tags') in ('', []))
    if current is None:
        api.request('PUT', path, {'description': marker, 'tags': 'economicon,JUP-131'})
    for component in ('backend', 'processor'):
        user = 'economicon_' + component
        api.request('PUT', '/api/users/' + user, {'password': passwords[component], 'tags': ''})
        permissions = {'configure': '^processor:jobs$', 'write': '^(amq\\.default)?$', 'read': '^processor:jobs$'}
        target = '/api/permissions/' + vhost + '/' + user
        api.request('PUT', target, permissions)
        actual = api.request('GET', target)
        require(actual is not None and all(actual.get(key) == value for key, value in permissions.items()))
