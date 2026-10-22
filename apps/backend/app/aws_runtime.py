"""Explicit ECS startup adapter, shared by the independently packaged services.

No network access on import or outside ECS mode. Only the processor needs its
own ENI address, obtained from the fixed link-local Fargate metadata endpoint.
"""
import http.client
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import parse_qsl, urlsplit


RDS_CA_PATH = Path(__file__).parent / 'resources/rds-eu-south-2.pem'
RDS_CA_SHA256 = '6e4db6870d865a83140270728f62fbdb73202a3a017dc500ae2605e3d17344c0'


class AwsRuntimeError(RuntimeError):
    pass


def rds_root_certificate():
    if hashlib.sha256(RDS_CA_PATH.read_bytes()).hexdigest() != RDS_CA_SHA256:
        raise AwsRuntimeError('Packaged RDS certificate differs from the reviewed bundle.')
    return str(RDS_CA_PATH.resolve())


def configure_database_tls(env):
    for name in ('DATABASE_URL', 'VECTOR_DATABASE_URL'):
        modes = [value for key, value in parse_qsl(urlsplit(env[name]).query, keep_blank_values=True)
                 if key == 'sslmode']
        if modes != ['verify-full']:
            raise ValueError()
    env['PGSSLROOTCERT'] = rds_root_certificate()


def fetch_metadata(uri):
    try:
        parsed = urlsplit(uri)
        if (parsed.scheme != 'http' or parsed.netloc != '169.254.170.2'
                or not re.fullmatch(r'/v4/[A-Za-z0-9_-]+', parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError()
        connection = http.client.HTTPConnection('169.254.170.2', timeout=2)
        try:
            connection.request('GET', parsed.path, headers={'Accept': 'application/json'})
            response = connection.getresponse()
            raw = response.read(65537)
            if response.status != 200 or len(raw) > 65536:
                raise ValueError()
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError()
            return value
        finally:
            connection.close()
    except Exception:
        raise AwsRuntimeError('Private ECS metadata is unavailable or invalid.') from None


def private_address(value):
    addresses = set()
    for network in value['Networks']:
        if network['NetworkMode'] != 'awsvpc':
            raise ValueError()
        for raw in network['IPv4Addresses']:
            address = ipaddress.IPv4Address(raw)
            if str(address) != raw or not any(address in ipaddress.IPv4Network(cidr)
                    for cidr in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
                raise ValueError()
            addresses.add(raw)
    if len(addresses) != 1:
        raise ValueError()
    return addresses.pop()


def prepare_runtime(component, *, environment=None, runtime_parent='/tmp', metadata_fetcher=None):
    env = os.environ if environment is None else environment
    if env.get('ECONOMICON_AWS_RUNTIME') != 'ecs':
        return
    # Remove the injected value before any validation or application child process.
    key = env.pop('CHAT_HMAC_KEY', None)
    directory = None
    path = None
    try:
        if component not in {'backend', 'processor'} or env.get('AWS_EXECUTION_ENV') != 'AWS_ECS_FARGATE':
            raise ValueError()
        configure_database_tls(env)
        if env.get('CHAT_ENABLED', 'false').lower() != 'true':
            return
        if not isinstance(key, str) or not re.fullmatch(r'[0-9a-f]{64}', key):
            raise ValueError()
        address = None
        if component == 'processor':
            metadata = (metadata_fetcher or fetch_metadata)(env['ECS_CONTAINER_METADATA_URI_V4'])
            address = private_address(metadata)
        directory = Path(tempfile.mkdtemp(prefix='economicon-runtime-', dir=runtime_parent))
        path = directory / 'chat.hmac'
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(key.encode('ascii'))
        name = 'CHAT_SERVICE_HMAC_KEY_FILE' if component == 'backend' else 'CHAT_SIGNING_KEY_FILE'
        env[name] = str(path)
        if address is not None:
            env['PROCESSOR_CHAT_BIND_HOST'] = address
    except Exception:
        if path is not None:
            path.unlink(missing_ok=True)
        if directory is not None:
            directory.rmdir()
        raise AwsRuntimeError('Private ECS runtime configuration is invalid.') from None
