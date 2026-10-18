import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('aggregate', Path(__file__).with_name('chat-eval-aggregate.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'commit': 'candidate', 'bank_sha256': 'bank', 'repetitions': 3,
                     'samples': [{'case_id': f'JUP-069-{i:03}', 'repetition': n}
                                 for n in range(1, 4) for i in range(1, 29)]}
        self.receipts = []
        for i, sample in enumerate(self.plan['samples']):
            row = {'id': sample['case_id'], 'repetition': sample['repetition'],
                   'operation': {'operation_id': str(i)}, 'conversation_id': str(i),
                   'state': 'failed' if i == 0 else 'completed',
                   'resources': {}, 'resources_sha256': a.digest({})}
            self.receipts.append({'plan_sha256': a.digest(self.plan), 'bank_sha256': 'bank',
                                  'repetitions': 3, 'results': [row]})

    def test_full_campaign_keeps_failure_without_claiming_acceptance(self):
        result = a.aggregate(self.plan, self.receipts)
        self.assertEqual(result['state'], 'COLLECTED')
        self.assertEqual(len(result['results']), 84)
        self.assertEqual(result['results'][0]['state'], 'failed')
        self.assertEqual(result['acceptance'], 'NOT_ASSESSED')

    def test_partial_exposes_absent_repetition(self):
        result = a.aggregate(self.plan, self.receipts[:-1])
        self.assertEqual(result['state'], 'PARTIAL')
        self.assertEqual(result['missing_samples'], [{'case_id': 'JUP-069-028', 'repetition': 3}])

    def test_best_of_duplicate_is_rejected(self):
        retry = copy.deepcopy(self.receipts[0])
        retry['results'][0]['state'] = 'completed'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            a.aggregate(self.plan, self.receipts + [retry])

    def test_mixed_plan_or_reused_conversation_is_rejected(self):
        self.receipts[0]['plan_sha256'] = 'another'
        with self.assertRaisesRegex(ValueError, 'another plan'):
            a.aggregate(self.plan, self.receipts)
        self.receipts[0]['plan_sha256'] = a.digest(self.plan)
        self.receipts[1]['results'][0]['conversation_id'] = '0'
        with self.assertRaisesRegex(ValueError, 'fresh conversation'):
            a.aggregate(self.plan, self.receipts)

    def test_changed_resource_is_rejected(self):
        self.receipts[0]['results'][0]['resources']['answer'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            a.aggregate(self.plan, self.receipts)


if __name__ == '__main__':
    unittest.main()
