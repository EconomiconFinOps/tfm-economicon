from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest
import copy
import hashlib
import json

spec = importlib.util.spec_from_file_location('budget', Path(__file__).with_name('chat-eval-budget.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class AuthorizedBudgetTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / 'fixtures/chat-eval/currency-n5-budget.json'
        self.fixture = json.loads(path.read_text(encoding='utf-8'))
        self.reservations = copy.deepcopy(self.fixture['reservations'])
        self.snapshot = b.accounting_snapshot(self.fixture['upstream'], self.fixture['keys'], 100)
        self.coverage(self.snapshot, self.reservations)

    def coverage(self, snapshot, reservations):
        snapshot['complete_ledger_history'] = {
            'historical_floor_usd': str(b.HISTORICAL_FLOOR),
            'request_ids_sha256': hashlib.sha256(json.dumps(sorted(reservations)).encode()).hexdigest()}
        return snapshot

    def admit(self, *, snapshot=None, reservations=None, operation_id='synthetic-next',
              bound=Decimal('0.01'), now=100, cap='30.00'):
        return b.admit(self.snapshot if snapshot is None else snapshot,
                       self.reservations if reservations is None else reservations,
                       operation_id, bound, now, authorized_cap_usd=cap)

    def test_final_aggregate_retains_every_prior_amount_and_needs_explicit_cap(self):
        self.assertEqual(b.CAP, Decimal('20.00'))
        before = copy.deepcopy((self.snapshot, self.reservations))
        self.assertEqual(Decimal(self.snapshot['cumulative_usd']) +
                         Decimal(self.reservations['synthetic-pending']['reserved_usd']),
                         Decimal(self.fixture['covered_upper_usd']))
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(cap=None)
        result = self.admit()
        self.assertEqual({key: result[key] for key in self.reservations}, self.reservations)
        self.assertEqual(result['synthetic-next']['reserved_usd'], '0.01')
        self.assertEqual((self.snapshot, self.reservations), before)
        self.assertEqual(b.CAP, Decimal('20.00'))

    def test_reviewer_cumulative_example_with_complete_synthetic_pending_ledger(self):
        reservations = {'synthetic-prior': {'state': 'RESERVED', 'reserved_usd': '1.00'}}
        snapshot = self.coverage({**self.snapshot, 'cumulative_usd': '23.117520366'}, reservations)
        result = self.admit(snapshot=snapshot, reservations=reservations)
        self.assertEqual(result['synthetic-prior'], reservations['synthetic-prior'])
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(snapshot=snapshot, reservations=reservations, cap=None)

    def test_covered_upper_is_not_upstream_usage_and_cannot_remove_holds(self):
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(snapshot={**self.snapshot, 'cumulative_usd': self.fixture['covered_upper_usd']})
        self.assertEqual(self.reservations['synthetic-pending']['reserved_usd'], '15.04040862')

    def test_unknown_terminal_cost_keeps_its_full_maximum_under_30(self):
        reservations = copy.deepcopy(self.reservations)
        receipt = {'operation': {'operation_id': 'synthetic-done', 'state': 'completed'},
                   'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT'}
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        reservations['synthetic-pending'].update({
            'state': 'COST_UNKNOWN_RESERVED', 'maximum_reserved_usd': '15.04040862',
            'terminal_completed': {'operation_id': 'synthetic-done', 'state': 'completed', 'receipt_sha256': digest}})
        b.retained_cost(reservations['synthetic-pending'], 'synthetic-done', receipt)
        admitted = self.admit(reservations=reservations)
        self.assertEqual(admitted['synthetic-pending'], reservations['synthetic-pending'])
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(reservations=reservations, bound=Decimal('6.882479635'))

    def test_explicit_admission_matches_historical_cap_override(self):
        from unittest.mock import patch
        with patch.object(b, 'CAP', Decimal('30.00')):
            historical = self.admit(cap=None)
        self.assertEqual(self.admit(), historical)
        self.assertEqual(b.CAP, Decimal('20.00'))

    def test_exact_cap_and_one_billionth_over_boundary(self):
        remaining = Decimal('30.00') - Decimal(self.fixture['covered_upper_usd'])
        self.admit(bound=remaining)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(bound=remaining + Decimal('0.000000001'))

    def test_explicit_cap_is_a_valid_bounded_decimal_string(self):
        for cap in (True, 30, 30.0, Decimal('30'), {}, '', 'NaN', 'Infinity', '-1', '0', '30.000000001'):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                self.admit(cap=cap)
        for cap in ('20.00', '19.00'):
            with self.subTest(cap=cap), self.assertRaisesRegex(ValueError, 'Insufficient budget'):
                self.admit(cap=cap)

    def test_stale_future_and_unverified_accounting_still_fail_under_30(self):
        for patch in ({'observed_at': 69}, {'observed_at': 101}, {'observed_at': float('nan')},
                      {'scope': 'gateway-only'}, {'evidence_sha256': ''}, {'cumulative_usd': '0.1'}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.admit(snapshot={**self.snapshot, **patch})

    def test_freshness_boundary_is_not_widened_by_authorization(self):
        self.admit(now=130)
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.admit(now=130.000001)

    def test_invalid_operation_and_bound_still_fail_under_30(self):
        for operation in (None, '', '  ', False, 7, [], 'synthetic-pending'):
            with self.subTest(operation=operation), self.assertRaisesRegex(ValueError, 'unidentified'):
                self.admit(operation_id=operation)
        for bound in (Decimal('0'), Decimal('-1'), Decimal('NaN'), Decimal('Infinity'), '0.01', 0.01):
            with self.subTest(bound=bound), self.assertRaisesRegex(ValueError, 'positive bounded'):
                self.admit(bound=bound)

    def test_history_identity_and_floor_still_fail_under_30(self):
        for patch in ({'request_ids_sha256': 'different-ledger'}, {'historical_floor_usd': '0'}):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot['complete_ledger_history'].update(patch)
            with self.subTest(patch=patch), self.assertRaisesRegex(ValueError, 'ledger history'):
                self.admit(snapshot=snapshot)

    def test_lagging_upstream_cannot_hide_prior_settled_or_unknown_cost(self):
        reservations = copy.deepcopy(self.reservations)
        reservations['synthetic-observed']['reserved_usd'] = '29'
        snapshot = self.coverage({**self.snapshot, 'cumulative_usd': '1.00'}, reservations)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(snapshot=snapshot, reservations=reservations)

    def test_another_admission_consumes_the_same_30_cap_without_reset(self):
        result = self.admit(bound=Decimal('6.88'))
        snapshot = self.coverage(copy.deepcopy(self.snapshot), result)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.admit(snapshot=snapshot, reservations=result, operation_id='synthetic-third')


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'observed_at': 100, 'scope': 'jup035-cumulative-all-providers',
                         'evidence_sha256': 'observed', 'cumulative_usd': str(b.CAP - Decimal('1.00'))}

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

    def covered(self, reservations, spent=None):
        import hashlib, json
        if spent is None: spent = str(b.CAP - Decimal('.613889585'))
        return {**self.snapshot, 'cumulative_usd': spent, 'complete_ledger_history': {
            'historical_floor_usd': str(b.HISTORICAL_FLOOR),
            'request_ids_sha256': hashlib.sha256(json.dumps(sorted(reservations)).encode()).hexdigest()}}

    def test_audited_settled_cost_is_preserved_without_counting_twice(self):
        reservations = {'charged': {'state': 'COST_OBSERVED', 'reserved_usd': '.296203837'},
                        'seed': {'state': 'RESERVED', 'reserved_usd': '.002'}}
        result = b.admit(self.covered(reservations), reservations, 'next', Decimal('.319952'), 100)
        self.assertEqual(result['charged'], reservations['charged'])
        self.assertEqual(result['seed'], reservations['seed'])
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            b.admit(self.covered(reservations), reservations, 'next', Decimal('.62'), 100)

    def test_lagging_counter_cannot_hide_settled_cost(self):
        reservations = {'charged': {'state': 'COST_OBSERVED', 'reserved_usd': str(b.CAP - b.HISTORICAL_FLOOR - Decimal('.02'))}}
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            b.admit(self.covered(reservations, '1.00'), reservations, 'next', Decimal('.05'), 100)

    def test_history_identity_and_floor_must_match(self):
        reservations = {'charged': {'state': 'COST_OBSERVED', 'reserved_usd': '.2'}}
        snapshot = self.covered(reservations)
        for patch in ({'request_ids_sha256': 'wrong'}, {'historical_floor_usd': '0'}):
            with self.assertRaisesRegex(ValueError, 'ledger history'):
                b.admit({**snapshot, 'complete_ledger_history': {**snapshot['complete_ledger_history'], **patch}},
                        reservations, 'next', Decimal('.1'), 100)

    def test_unknown_outcome_still_reserves_its_entire_bound(self):
        reservations = {'unknown': {'state': 'RESERVED', 'reserved_usd': '.7'}}
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            b.admit(self.covered(reservations), reservations, 'next', Decimal('.01'), 100)

    def test_completed_unknown_reservation_requires_full_amount_identity_and_receipt(self):
        import copy, hashlib, json
        receipt = {'operation': {'operation_id': 'done', 'state': 'completed'},
                   'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT'}
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        reservation = {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '.319952',
            'maximum_reserved_usd': '.319952', 'terminal_completed': {
                'operation_id': 'done', 'state': 'completed', 'receipt_sha256': digest}}
        self.assertTrue(b.retained_cost(reservation, 'done', receipt))
        for patch in ({'reserved_usd': '0'}, {'reserved_usd': '.01'},
                      {'state': 'COST_OBSERVED'}, {'terminal_failure': {}}):
            with self.assertRaises(ValueError):
                b.retained_cost({**reservation, **patch}, 'done', receipt)
        for state in ('failed', 'cancelled', 'active'):
            changed = copy.deepcopy(receipt); changed['operation']['state'] = state
            with self.assertRaisesRegex(ValueError, 'receipt mismatch'):
                b.retained_cost(reservation, 'done', changed)
        with self.assertRaises(ValueError):
            b.retained_cost(reservation, 'another', receipt)

    def test_real_partial_campaign_preserves_all_reserves_under_raised_cap(self):
        from unittest.mock import patch
        reservations = {'prior': {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '1.921712'},
                        'completed_eof': {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '.319952'}}
        snapshot = self.covered(reservations, '2.548894402')
        with patch.object(b, 'CAP', Decimal('5.00')):
            with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
                b.admit(snapshot, reservations, 'ninth', Decimal('.319952'), 100)
        self.assertEqual(b.CAP, Decimal('20.00'))
        admitted = b.admit(snapshot, reservations, 'ninth', Decimal('.319952'), 100)
        self.assertEqual({k: admitted[k] for k in reservations}, reservations)
        self.assertEqual(admitted['ninth']['reserved_usd'], '0.319952')
        self.assertEqual(reservations['completed_eof']['reserved_usd'], '.319952')

    def test_cap20_extension_preserves_the_partial51_accounting(self):
        from unittest.mock import patch
        reservations = {'all_settled': {'state': 'COST_OBSERVED', 'reserved_usd': '2.813385973'},
                        'all_unknown': {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '6.081088'}}
        snapshot = self.covered(reservations, '3.81381063')
        with patch.object(b, 'CAP', Decimal('10.00')):
            with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
                b.admit(snapshot, reservations, '024r2', Decimal('.319952'), 100)
        admitted = b.admit(snapshot, reservations, '024r2', Decimal('.319952'), 100)
        self.assertEqual({key: admitted[key] for key in reservations}, reservations)
        self.assertEqual(admitted['024r2']['reserved_usd'], '0.319952')
        self.assertEqual(reservations['all_unknown']['reserved_usd'], '6.081088')


if __name__ == '__main__':
    unittest.main()
