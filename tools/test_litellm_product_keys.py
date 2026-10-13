import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('keys', Path(__file__).with_name('litellm-product-keys.py'))
keys = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keys)


class FakeGateway:
    master = 'synthetic-master'
    def __init__(self):
        self.values = {}
        self.calls = []
        self.fail_generation = None
        self.fail_revoke = False
    def api(self, route, body=None):
        self.calls.append((route, body))
        if route == '/key/generate':
            number = len(self.values) + 1
            if number == self.fail_generation:
                raise RuntimeError('secret upstream error')
            key = 'synthetic-' + str(number)
            self.values[key] = {**body, 'expires': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(), 'spend': body.get('spend', 0)}
            return {'key': key}
        if route.startswith('/key/info'):
            return {'info': self.values[route.split('=', 1)[1]]}
        raise AssertionError(route)
    def revoke(self, values):
        if self.fail_revoke:
            raise RuntimeError('secret upstream error')
        for value in values.values():
            self.values.pop(value, None)


class ProductKeysTest(unittest.TestCase):
    def test_issue_and_idempotency(self):
        gateway = FakeGateway()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            receipt = keys.provision(gateway, path)
            self.assertEqual(receipt['aggregate_max_budget_usd'], 10)
            self.assertEqual(len(gateway.values), 2)
            self.assertEqual(keys.provision(gateway, path), receipt)
            self.assertEqual(sum(route == '/key/generate' for route, _ in gateway.calls), 2)
            self.assertNotIn('synthetic-', json.dumps(receipt))
            self.assertEqual(set(json.loads(path.read_text())), set(keys.POLICIES))
            self.assertTrue(all('/v1/' not in route for route, _ in gateway.calls))

    def test_partial_failure_revokes_and_does_not_persist(self):
        gateway = FakeGateway()
        gateway.fail_generation = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            with self.assertRaisesRegex(keys.ProvisionError, 'generated keys revoked'):
                keys.provision(gateway, path)
            self.assertFalse(path.exists())
            self.assertEqual(gateway.values, {})

    def test_policy_mismatch_rejected(self):
        gateway = FakeGateway()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            keys.provision(gateway, path)
            gateway.values['synthetic-1']['max_budget'] = 10
            with self.assertRaises(keys.ProvisionError):
                keys.provision(gateway, path)

    def test_failed_rollback_preserves_private_cleanup_keys(self):
        gateway = FakeGateway()
        gateway.fail_generation = 2
        gateway.fail_revoke = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            with self.assertRaisesRegex(keys.ProvisionError, 'rollback-pending'):
                keys.provision(gateway, path)
            self.assertTrue(Path(str(path) + '.rollback-pending').exists())

    def test_rotation_cannot_reset_budget(self):
        gateway = FakeGateway()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            keys.provision(gateway, path)
            old = set(gateway.values)
            with self.assertRaisesRegex(keys.ProvisionError, 'rotation is disabled'):
                keys.provision(gateway, path, rotate=True)
            self.assertEqual(old, set(gateway.values))

    def test_expired_or_unbounded_key_rejected(self):
        for days in [-1, 31]:
            gateway = FakeGateway()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'keys.json'
                keys.provision(gateway, path)
                gateway.values['synthetic-1']['expires'] = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
                with self.assertRaisesRegex(keys.ProvisionError, 'expiry'):
                    keys.provision(gateway, path)

    def test_unsafe_gateway_and_redirect(self):
        for url in ['http://example.com', 'https://user:pass@example.com', 'https://example.com?q=1', 'https://example.com/v1']:
            with self.assertRaises(keys.ProvisionError):
                keys.Gateway(url, 'synthetic')
        with self.assertRaises(keys.ProvisionError):
            keys.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example')


if __name__ == '__main__':
    unittest.main()
