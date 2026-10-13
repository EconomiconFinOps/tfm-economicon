from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('budget', Path(__file__).with_name('chat-eval-budget.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'observed_at': 100, 'scope': 'jup035-cumulative-all-providers',
                         'evidence_sha256': 'observed', 'cumulative_usd': '1.00'}

    def test_four_attempts_and_both_generation_legs_are_reserved(self):
        bound = b.operation_bound(input_tokens_per_attempt=10000,
                                  input_price_per_million='1', output_price_per_million='2',
                                  auxiliary_bound_usd='0.01')
        self.assertEqual(bound, Decimal('0.0756'))

    def test_unknown_attempt_keeps_reservation_and_prevents_overspend(self):
        reserved = b.admit(self.snapshot, {}, 'unknown-outcome', Decimal('0.80'), 100)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            b.admit(self.snapshot, reserved, 'next', Decimal('0.21'), 100)
        self.assertEqual(reserved['unknown-outcome']['reserved_usd'], '0.80')

    def test_exact_cap_allowed_but_duplicate_is_rejected(self):
        reserved = b.admit(self.snapshot, {}, 'operation', Decimal('1.00'), 100)
        with self.assertRaisesRegex(ValueError, 'already reserved'):
            b.admit(self.snapshot, reserved, 'operation', Decimal('0.01'), 100)

    def test_historical_or_stale_accounting_cannot_admit_spend(self):
        for patch in ({'observed_at': 60}, {'observed_at': 101}, {'cumulative_usd': '0.1'},
                      {'cumulative_usd': 'NaN'}, {'scope': 'gateway-only'}, {'evidence_sha256': ''}):
            with self.assertRaises(ValueError):
                b.admit({**self.snapshot, **patch}, {}, 'operation', Decimal('0.1'), 100)

    def test_live_snapshot_uses_upper_bound_without_double_counting(self):
        keys = {name: {'spend': '0.1', 'max_budget': '1', 'expires': '2030-01-01T00:00:00+00:00'}
                for name in ('backend', 'processor')}
        snapshot = b.accounting_snapshot({'usage': '1.092818129', 'secret': 'not-retained'}, keys, 100)
        self.assertEqual(snapshot['cumulative_usd'], '1.092818129')
        self.assertNotIn('not-retained', str(snapshot))
        self.assertIn('not exact task', snapshot['accounting_basis'])

    def test_expired_or_missing_key_blocks_snapshot(self):
        keys = {name: {'spend': '0.1', 'max_budget': '1', 'expires': '1970-01-01T00:01:00+00:00'}
                for name in ('backend', 'processor')}
        with self.assertRaisesRegex(ValueError, 'expired'):
            b.accounting_snapshot({'usage': '1'}, keys, 100)
        with self.assertRaisesRegex(ValueError, 'Both'):
            b.accounting_snapshot({'usage': '1'}, {'processor': keys['processor']}, 100)

    def test_settlement_requires_failed_attempts_too(self):
        operation = {'operation_id': 'o', 'current_attempt_id': 'second', 'state': 'completed', 'attempt_count': 2}
        def report(attempt):
            return {'event': 'chat_review_usage', 'operation_id': 'o', 'attempt_id': attempt,
                    'complete': True, 'attempted_legs': 2, 'reported_legs': 2,
                    'requests': [{}, {}], 'observed': {'cost_usd': '0.01'}}
        with self.assertRaises(ValueError):
            b.completed_attempt_cost(operation, [report('second')])
        self.assertEqual(b.completed_attempt_cost(operation, [report('first'), report('second')]), Decimal('0.02'))
        incomplete = report('first'); incomplete['complete'] = False
        with self.assertRaises(ValueError):
            b.completed_attempt_cost(operation, [incomplete, report('second')])


if __name__ == '__main__':
    unittest.main()
