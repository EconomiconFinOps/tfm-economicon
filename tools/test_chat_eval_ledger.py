import importlib.util
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
