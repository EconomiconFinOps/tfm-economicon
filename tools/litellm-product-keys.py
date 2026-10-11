"""Issue bounded Economicon service keys without invoking models or printing secrets."""
import argparse
from datetime import datetime, timezone, timedelta
import math
import json
import os
from pathlib import Path
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request

POLICIES = {
    'LITELLM_API_KEY': {'models': ['economicon-chat', 'economicon-embedding'], 'max_budget': 9.0},
    'BACKEND_LITELLM_API_KEY': {'models': ['economicon-embedding'], 'max_budget': 1.0},
}
COMMON = {'duration': '30d', 'budget_duration': '30d', 'rpm_limit': 10,
          'tpm_limit': 20000, 'max_parallel_requests': 1}


class ProvisionError(Exception):
    """Content-free operational error safe for terminal output."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProvisionError('Gateway redirect refused')


class Gateway:
    def __init__(self, url, master):
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')
                or (parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'))):
            raise ProvisionError('Use an HTTPS gateway origin or loopback HTTP')
        if not master or '\n' in master or '\r' in master:
            raise ProvisionError('Missing or invalid administrator credential')
        self.url, self.master = url.rstrip('/'), master
        self.opener = urllib.request.build_opener(NoRedirect)

    def api(self, route, body=None):
        request = urllib.request.Request(self.url + route,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Authorization': 'Bearer ' + self.master, 'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except ProvisionError:
            raise
        except Exception:
            raise ProvisionError('Gateway administration request failed') from None

    def revoke(self, keys):
        if keys:
            self.api('/key/delete', {'keys': list(keys.values())})


def private_json(path):
    path = Path(path)
    if path.is_symlink():
        raise ProvisionError('Secret path must not be a symbolic link')
    if os.name != 'nt' and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ProvisionError('Secret file must have owner-only permissions')
    return json.loads(path.read_text(encoding='utf-8'))


def atomic_private(path, data):
    path = Path(path)
    if path.is_symlink():
        raise ProvisionError('Secret path must not be a symbolic link')
    fd, temporary = tempfile.mkstemp(prefix='.product-keys-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600) if hasattr(os, 'fchmod') else os.chmod(temporary, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect(gateway, keys):
    if set(keys) != set(POLICIES) or len(set(keys.values())) != len(keys):
        raise ProvisionError('Stored service credentials are incomplete or reused')
    receipt = {}
    for name, policy in POLICIES.items():
        info = gateway.api('/key/info?key=' + urllib.parse.quote(keys[name], safe='')).get('info', {})
        expected = {**policy, **{k: v for k, v in COMMON.items() if k != 'duration'}}
        if any((set(info.get(k, [])) != set(value) if k == 'models' else info.get(k) != value)
               for k, value in expected.items()) or not info.get('expires'):
            raise ProvisionError('Effective key policy does not match approved limits')
        try:
            expiry = datetime.fromisoformat(info['expires'].replace('Z', '+00:00'))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if not now < expiry <= now + timedelta(days=30, minutes=1):
                raise ValueError()
            spend = float(info['spend'])
            if not math.isfinite(spend) or spend < 0:
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise ProvisionError('Key expiry or spend counter is invalid') from None
        receipt[name] = {**expected, 'expires': info['expires'], 'spend': spend}
    return {'period': '30d', 'aggregate_max_budget_usd': 10, 'services': receipt,
            'model_calls': 0, 'accounting_limit': 'Counters are asynchronous; individual calls may overshoot.'}


def provision(gateway, destination, rotate=False):
    destination = Path(destination)
    old = private_json(destination) if destination.exists() else None
    if old and not rotate:
        return inspect(gateway, old)
    if rotate:
        raise ProvisionError('Automatic rotation is disabled to preserve the current budget window')
    new = {}
    try:
        for name, policy in POLICIES.items():
            result = gateway.api('/key/generate', {**policy, **COMMON})
            key = result.get('key')
            if not isinstance(key, str) or not key or key == gateway.master or '\n' in key or '\r' in key:
                raise ProvisionError('Gateway returned an invalid service credential')
            new[name] = key
        receipt = inspect(gateway, new)
        atomic_private(destination, new)
    except Exception:
        try:
            gateway.revoke(new)
        except Exception:
            # Keep retrievable credentials for explicit cleanup if rollback fails.
            atomic_private(str(destination) + '.rollback-pending', new)
            raise ProvisionError('Issuance failed; rollback keys retained in private rollback-pending file') from None
        raise ProvisionError('Issuance failed; generated keys revoked') from None
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['issue', 'inspect', 'revoke', 'rollback-pending'])
    parser.add_argument('--url', required=True)
    parser.add_argument('--keys-file', required=True)
    parser.add_argument('--master-env-file', help='Private JSON file containing LITELLM_MASTER_KEY')
    args = parser.parse_args()
    try:
        if os.name == 'nt':
            raise ProvisionError('Run on POSIX to enforce owner-only secret-file permissions')
        master = (private_json(args.master_env_file).get('LITELLM_MASTER_KEY')
                  if args.master_env_file else os.environ.get('LITELLM_MASTER_KEY'))
        gateway = Gateway(args.url, master)
        if args.action in ('revoke', 'rollback-pending'):
            path = Path(args.keys_file if args.action == 'revoke' else args.keys_file + '.rollback-pending')
            gateway.revoke(private_json(path))
            path.unlink()
            receipt = {'previous_keys_revoked': True, 'model_calls': 0}
        elif args.action == 'inspect':
            receipt = inspect(gateway, private_json(args.keys_file))
        else:
            if Path(args.keys_file + '.revoke-pending').exists() or Path(args.keys_file + '.rollback-pending').exists():
                raise ProvisionError('Resolve pending revocation before issuing more keys')
            receipt = provision(gateway, args.keys_file)
        print(json.dumps(receipt, indent=2))
        return 0
    except Exception as exc:
        print(str(exc) if isinstance(exc, ProvisionError) else 'Key administration failed; no secrets displayed')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
