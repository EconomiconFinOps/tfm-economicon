import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('usage', Path(__file__).with_name('chat-eval-usage.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


class UsageTests(unittest.TestCase):
    def report(self, attempt='a'):
        return {'event': 'chat_review_usage', 'operation_id': 'o', 'attempt_id': attempt,
                'complete': True, 'attempted_legs': 1, 'reported_legs': 1,
                'observed': {'cost_usd': '0.01', 'unwanted': 'not-retained'},
                'requests': [{'phase': 'draft', 'request_sha256': 'a' * 64,
                              'output_token_limit': 1000, 'prompt': 'not-retained'}]}

    def test_nested_structlog_format_excludes_unrelated_content(self):
        raw = '\n'.join([json.dumps({'event': 'unrelated not-retained'}),
                         json.dumps({'event': 'chat_review_usage ' + json.dumps(self.report())})]).encode()
        result = u.reports(raw, 'o')
        self.assertEqual(len(result['reports']), 1)
        self.assertNotIn('not-retained', json.dumps(result))

    def test_distinct_attempts_preserved_identical_duplicates_counted(self):
        raw = '\n'.join(json.dumps(x) for x in [self.report(), self.report(), self.report('b')]).encode()
        result = u.reports(raw, 'o')
        self.assertEqual(result['identical_duplicates'], 1)
        self.assertEqual(len(result['reports']), 2)

    def test_other_operation_is_not_attributed(self):
        self.assertEqual(u.reports(json.dumps(self.report()).encode(), 'other')['reports'], [])

    def test_missing_request_hash_blocks_settlement_evidence(self):
        event = self.report(); event['requests'][0]['request_sha256'] = ''
        with self.assertRaisesRegex(ValueError, 'provenance'):
            u.reports(json.dumps(event).encode(), 'o')


if __name__ == '__main__':
    unittest.main()
