import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
import threading

spec = importlib.util.spec_from_file_location('ledger', Path(__file__).with_name('chat-eval-ledger.py'))
l = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'ledger.sqlite'
        self.ledger = l.Ledger(self.path)
        self.snapshot = {'observed_at': 100, 'scope': 'jup035-cumulative-all-providers',
                         'evidence_sha256': 'synthetic', 'cumulative_usd': str(l.budget.CAP - Decimal('1.00'))}

    def reserve(self, sample='case:r1', bound='0.60'):
        return self.ledger.reserve('plan', sample, self.snapshot, Decimal(bound), 100)

    def test_restart_keeps_reservation_and_duplicate_sample_is_rejected(self):
        request_id = self.reserve()
        reopened = l.Ledger(self.path)
        self.assertEqual(reopened.pending()[0]['request_id'], request_id)
        with self.assertRaisesRegex(ValueError, 'already reserved'):
            self.reserve()
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            reopened.reserve('another-plan', 'case:r1', self.snapshot, Decimal('0.5'), 100)

    def test_terminal_failure_keeps_entire_bound_across_restart(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        receipt = {'operation': {'operation_id': 'operation', 'state': 'failed'},
                   'conversation_id': 'conversation', 'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT',
                   'verification': {'input_matches_bank': True, 'stable_snapshot': True},
                   'durable_input_supplement': {'state': 'failed'}}
        self.ledger.retain_failed_cost(request_id, receipt)
        reservation = json.loads(l.Ledger(self.path).pending()[0]['reservation'])
        self.assertEqual(reservation['reserved_usd'], '0.60')
        l.budget.retained_failure(reservation, 'operation', receipt)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.reserve('next', '.41')
        changed = {**receipt, 'conversation_id': 'different'}
        with self.assertRaisesRegex(ValueError, 'receipt mismatch'):
            l.budget.retained_failure(reservation, 'operation', changed)

    def test_active_or_unverified_failure_cannot_be_skipped(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        for state in ('active', 'completed', 'failed'):
            receipt = {'operation': {'operation_id': 'operation', 'state': state},
                       'conversation_id': 'conversation', 'collection_state': 'INCOMPLETE'}
            with self.assertRaisesRegex(ValueError, 'Verified durable terminal failure'):
                self.ledger.retain_failed_cost(request_id, receipt)
        self.assertEqual(json.loads(self.ledger.pending()[0]['reservation'])['state'], 'RESERVED')

    def completed_receipt(self):
        import hashlib
        operation = {'operation_id': 'operation', 'state': 'completed', 'attempt_count': 2}
        result = {'id': 'answer', 'content': 'Synthetic completed answer'}
        history = {'messages': [{'id': 'answer', 'role': 'assistant', **result}]}
        resources = {'operation': operation, 'operation_after': dict(operation),
                     'result': result, 'history': history}
        digest = hashlib.sha256(json.dumps(resources, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        return {'operation': operation, 'conversation_id': 'conversation', 'result': result,
                'history': history, 'resources': resources, 'resources_sha256': digest,
                'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT',
                'verification': {k: True for k in ('input_matches_bank', 'stable_snapshot',
                                                 'public_history_parity', 'citation_ids_known')}}

    def test_completed_unknown_cost_keeps_full_bound_and_true_state_across_restart(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        receipt = self.completed_receipt()
        self.ledger.retain_completed_cost(request_id, receipt)
        reservation = json.loads(l.Ledger(self.path).pending()[0]['reservation'])
        self.assertEqual(reservation['state'], 'COST_UNKNOWN_RESERVED')
        self.assertEqual(reservation['reserved_usd'], '0.60')
        self.assertEqual(reservation['maximum_reserved_usd'], '0.60')
        self.assertEqual(reservation['terminal_completed']['state'], 'completed')
        self.assertNotIn('terminal_failure', reservation)
        l.budget.retained_cost(reservation, 'operation', receipt)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.reserve('next', '.41')
        with self.assertRaisesRegex(ValueError, 'untouched full reservation'):
            self.ledger.retain_completed_cost(request_id, receipt)

    def test_completed_retention_rejects_unverified_or_inconsistent_public_resources(self):
        import copy
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        original = self.completed_receipt()
        for patch in ('state', 'parity', 'resource_hash', 'resource_operation', 'result', 'conversation'):
            with self.subTest(patch=patch):
                receipt = copy.deepcopy(original)
                if patch == 'state': receipt['operation']['state'] = 'active'
                elif patch == 'parity': receipt['verification']['public_history_parity'] = False
                elif patch == 'resource_hash': receipt['resources_sha256'] = '0'*64
                elif patch == 'resource_operation': receipt['resources']['operation_after']['operation_id'] = 'different'
                elif patch == 'result': receipt['result'] = {'content': 'Changed after verification'}
                else: receipt['conversation_id'] = 'different'
                with self.assertRaises(ValueError):
                    self.ledger.retain_completed_cost(request_id, receipt)
                self.assertEqual(json.loads(self.ledger.pending()[0]['reservation'])['state'], 'RESERVED')

    def test_retention_cannot_reinflate_or_relabel_an_already_settled_success(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        operation = {'operation_id': 'operation', 'state': 'completed', 'attempt_count': 1,
                     'current_attempt_id': 'attempt'}
        report = {'event': 'chat_review_usage', 'operation_id': 'operation', 'attempt_id': 'attempt',
                  'complete': True, 'attempted_legs': 1, 'reported_legs': 1,
                  'requests': [{}], 'observed': {'cost_usd': '0.1'}}
        self.ledger.reconcile_cost(request_id, operation, [report], '0')
        with self.assertRaisesRegex(ValueError, 'untouched full reservation'):
            self.ledger.retain_completed_cost(request_id, self.completed_receipt())
        self.assertEqual(json.loads(self.ledger.pending()[0]['reservation'])['reserved_usd'], '0.1')

    def test_reservation_is_durable_before_post(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        def send(conversation, identifier):
            self.assertEqual((conversation, identifier), ('conversation', request_id))
            self.assertEqual(l.Ledger(self.path).pending()[0]['state'], 'DISPATCHING')
            return 'operation'
        self.ledger.dispatch(request_id, send)
        self.assertEqual(self.ledger.pending()[0]['operation_id'], 'operation')

    def test_timeout_after_post_does_not_retry_or_release_money(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        calls = []
        def send(*args):
            calls.append(args)
            raise TimeoutError('synthetic lost response')
        with self.assertRaises(TimeoutError):
            self.ledger.dispatch(request_id, send)
        with self.assertRaisesRegex(ValueError, 'Do not resend'):
            l.Ledger(self.path).dispatch(request_id, send)
        self.assertEqual(len(calls), 1)
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.reserve('case:r2', '0.50')
        self.ledger.observe_handle(request_id, 'found-by-request-id')
        self.assertEqual(self.ledger.pending()[0]['state'], 'OBSERVING')

    def test_observed_operation_cannot_change(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.ledger.observe_handle(request_id, 'another')

    def test_concurrent_reservations_cannot_both_spend_same_balance(self):
        barrier = threading.Barrier(2)
        def reserve(sample):
            ledger = l.Ledger(self.path)
            barrier.wait(timeout=5)
            try:
                return ledger.reserve('plan', sample, self.snapshot, Decimal('0.60'), 100)
            except ValueError as exc:
                self.assertIn('Insufficient budget', str(exc))
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(reserve, ['case:r1', 'case:r2']))
        self.assertEqual(sum(value is not None for value in result), 1)
        self.assertEqual(len(self.ledger.pending()), 1)

    def test_complete_cost_reduces_reserve_but_never_releases_actual_spend(self):
        request_id = self.reserve()
        self.ledger.attach_conversation(request_id, 'conversation')
        self.ledger.dispatch(request_id, lambda *args: 'operation')
        operation = {'operation_id': 'operation', 'state': 'completed', 'attempt_count': 1,
                     'current_attempt_id': 'attempt'}
        report = {'event': 'chat_review_usage', 'operation_id': 'operation', 'attempt_id': 'attempt',
                  'complete': True, 'attempted_legs': 2, 'reported_legs': 2,
                  'requests': [{}, {}], 'observed': {'cost_usd': '0.10'}}
        self.ledger.reconcile_cost(request_id, operation, [report], '0.02')
        self.assertIsNotNone(self.reserve('case:r2', '0.80'))
        with self.assertRaisesRegex(ValueError, 'Insufficient budget'):
            self.reserve('case:r3', '0.09')


if __name__ == '__main__':
    unittest.main()
