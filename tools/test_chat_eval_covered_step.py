import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('covered', Path(__file__).with_name('chat-eval-covered-step.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def plan(commit):
    return {'commit': commit, 'samples': [{'sample_id': '001:r1'}, {'sample_id': '001:r2'}]}


def row(p, sample, operation):
    return {'plan_hash': hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False,
        separators=(',', ':')).encode()).hexdigest(), 'sample_id': sample, 'operation_id': operation,
        'reservation': json.dumps({'state': 'COST_OBSERVED', 'reserved_usd': '0.01'})}


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b = plan('baseline'), plan('candidate')
        self.rows = [row(self.a, '001:r1', 'old1'), row(self.a, '001:r2', 'old2'),
                     row(self.b, '001:r1', 'new1')]

    def test_reused_sample_names_keep_both_campaigns(self):
        self.assertEqual(c.campaign_prefix(self.rows, [self.a, self.b]), self.rows)

    def test_cannot_omit_historical_plan(self):
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.b])

    def test_missing_first_sample_rejected(self):
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows[1:], [self.a, self.b])

    def test_plan_content_change_rejected(self):
        self.b['commit'] = 'different'
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.b])

    def test_unsettled_previous_operation_rejected(self):
        self.rows[0]['reservation'] = json.dumps({'state': 'RESERVED'})
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.b])

    def test_retained_failure_requires_identity_and_full_bound(self):
        reservation = {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '.32',
            'maximum_reserved_usd': '.32', 'terminal_failure': {
                'operation_id': 'new1', 'state': 'failed', 'receipt_sha256': 'a'*64}}
        self.rows[-1]['reservation'] = json.dumps(reservation)
        self.assertEqual(c.campaign_prefix(self.rows, [self.a, self.b]), self.rows)
        for change in ({'reserved_usd': '0'}, {'reserved_usd': '.01'},
                       {'terminal_failure': {'operation_id': 'different', 'state': 'failed', 'receipt_sha256': 'a'*64}}):
            self.rows[-1]['reservation'] = json.dumps({**reservation, **change})
            with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.b])

    def test_duplicate_operation_rejected(self):
        self.rows[-1]['operation_id'] = 'old1'
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.b])

    def test_completed_unknown_cost_is_an_ordered_prefix_only_with_full_maximum(self):
        reservation = {'state': 'COST_UNKNOWN_RESERVED', 'reserved_usd': '.32',
            'maximum_reserved_usd': '.32', 'terminal_completed': {
                'operation_id': 'new1', 'state': 'completed', 'receipt_sha256': 'a'*64}}
        self.rows[-1]['reservation'] = json.dumps(reservation)
        self.assertEqual(c.campaign_prefix(self.rows, [self.a, self.b]), self.rows)
        for patch in ({'reserved_usd': '0'}, {'reserved_usd': '.01'},
                      {'terminal_completed': {'operation_id': 'new1', 'state': 'failed', 'receipt_sha256': 'a'*64}}):
            self.rows[-1]['reservation'] = json.dumps({**reservation, **patch})
            with self.assertRaises(ValueError):
                c.campaign_prefix(self.rows, [self.a, self.b])

    def test_duplicate_sample_rejected(self):
        self.rows.append(row(self.b, '001:r1', 'new2'))
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.b])

    def test_duplicate_plan_rejected(self):
        with self.assertRaises(ValueError): c.campaign_prefix(self.rows, [self.a, self.a, self.b])


if __name__ == '__main__': unittest.main()
