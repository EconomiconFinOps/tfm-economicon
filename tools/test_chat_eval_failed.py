import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('failed', Path(__file__).with_name('chat-eval-failed.py'))
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class FailedTests(unittest.TestCase):
    def setUp(self):
        self.sample = {'case_id': 'case', 'repetition': 2, 'content': 'Exact question'}
        op = {'operation_id': 'op', 'question_id': 'q', 'request_id': 'r',
              'state': 'failed', 'attempt_count': 1, 'current_attempt_id': None}
        raw = {'operation': op, 'operation_after': copy.deepcopy(op),
               'context': {}, 'evidence': {'items': []}, 'history': {'messages': []}}
        self.row = {'id': 'case', 'repetition': 2, 'conversation_id': 'c',
                    'operation': op, 'resources': raw, 'resources_sha256': f.collect.digest(raw),
                    'collection_state': 'INCOMPLETE'}
        self.snapshot = {'tenant_id': 't', 'operation_id': 'op', 'conversation_id': 'c',
                         'client_request_id': 'r', 'question_message_id': 'q',
                         'question_content': 'Exact question', 'state': 'failed',
                         'attempt_count': 1, 'attempt_ids': ['a']}

    def run_reconcile(self):
        return f.reconcile(self.row, self.snapshot, self.sample, 't')

    def test_failure_and_raw_resources_remain_unchanged(self):
        before = copy.deepcopy(self.row)
        result = self.run_reconcile()
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(result['collection_state'], 'VERIFIED_PUBLIC_SNAPSHOT')
        self.assertIsNone(result['result'].get('content'))
        self.assertEqual(result['resources'], before['resources'])
        self.assertEqual(self.row, before)
        self.assertIsNone(result['operation']['current_attempt_id'])

    def test_cross_tenant_identity_and_input_rejected(self):
        for key in ('tenant_id', 'operation_id', 'conversation_id', 'client_request_id', 'question_message_id', 'question_content', 'state'):
            with self.subTest(key=key):
                changed = {**self.snapshot, key: 'other'}
                with self.assertRaises(ValueError):
                    f.reconcile(self.row, changed, self.sample, 't')

    def test_missing_or_duplicate_attempts_rejected(self):
        for ids in ([], ['a', 'a'], [None]):
            self.snapshot['attempt_ids'] = ids
            with self.assertRaises(ValueError): self.run_reconcile()

    def test_resource_tampering_rejected(self):
        self.row['resources']['history']['messages'].append({'content': 'tampered'})
        with self.assertRaises(ValueError): self.run_reconcile()

    def test_unstable_snapshot_not_repaired(self):
        self.row['resources']['operation_after']['attempt_count'] = 2
        self.row['resources_sha256'] = f.collect.digest(self.row['resources'])
        self.assertEqual(self.run_reconcile()['collection_state'], 'INCOMPLETE')

    def test_missing_public_resource_not_repaired(self):
        del self.row['resources']['context']
        self.row['resources_sha256'] = f.collect.digest(self.row['resources'])
        self.assertEqual(self.run_reconcile()['collection_state'], 'INCOMPLETE')


if __name__ == '__main__': unittest.main()
