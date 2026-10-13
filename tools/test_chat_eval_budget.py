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


if __name__ == '__main__':
    unittest.main()
