import copy
import importlib.util
from pathlib import Path
import unittest
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location('collect', Path(__file__).with_name('chat-eval-collect.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.sample = {'case_id': 'JUP-069-001', 'repetition': 2, 'content': 'Synthetic question'}
        self.base = '/assistant/conversations/c'
        self.op = self.base + '/generations/o'
        self.result = {'id': 'a', 'role': 'assistant', 'content': '1000 EUR',
                       'metadata': {'response': {'answer': '1000 EUR', 'evidence': [{'id': 'used'}]}}}
        self.data = {self.op: {'operation_id': 'o', 'state': 'completed', 'question_id': 'q'},
                     self.op + '/result': self.result,
                     self.op + '/context': {'manifest': {'sha': 'observed'}},
                     self.op + '/evidence': {'items': [{'id': 'used', 'content': 'Source'},
                                                      {'id': 'unused', 'content': 'Other'}]},
                     self.base: {'messages': [{'id': 'q', 'role': 'user', 'content': 'Synthetic question'},
                                               copy.deepcopy(self.result)]}}
        self.paths = []

    def get(self, path):
        self.paths.append(path)
        return copy.deepcopy(self.data[path])

    def collect(self, get=None):
        return c.collect(get or self.get, self.sample, 'c', 'o')

    def test_terminal_snapshot_has_parity_and_only_used_citations(self):
        row = self.collect()
        self.assertEqual(row['collection_state'], 'VERIFIED_PUBLIC_SNAPSHOT')
        self.assertEqual(row['repetition'], 2)
        self.assertEqual([x['id'] for x in row['cited_chunks']], ['used'])
        self.assertEqual(len(row['authorized_evidence']), 2)
        self.assertEqual(self.paths.count(self.op), 2)
        self.assertEqual(row['resources_sha256'], c.digest(row['resources']))

    def test_omitted_evidence_keeps_error_without_leaking_exception_text(self):
        def get(path):
            if path.endswith('/evidence'):
                raise HTTPError('https://secret.invalid', 503, 'SECRET_TOKEN', {}, None)
            return self.get(path)
        row = self.collect(get)
        self.assertEqual(row['collection_state'], 'INCOMPLETE')
        self.assertEqual(row['collection_errors']['evidence']['http_status'], 503)
        self.assertNotIn('SECRET_TOKEN', str(row))

    def test_mismatched_history_and_extra_questions_cannot_be_verified(self):
        self.data[self.base]['messages'][-1]['content'] = 'Other answer'
        self.data[self.base]['messages'].append({'id': 'q2', 'role': 'user', 'content': 'Another'})
        row = self.collect()
        self.assertFalse(row['verification']['public_history_parity'])
        self.assertFalse(row['verification']['input_matches_bank'])
        self.assertEqual(row['collection_state'], 'INCOMPLETE')

    def test_unknown_citation_is_not_silently_dropped(self):
        self.data[self.op + '/result']['metadata']['response']['evidence'].append({'id': 'unknown'})
        row = self.collect()
        self.assertFalse(row['verification']['citation_ids_known'])
        self.assertEqual(row['collection_state'], 'INCOMPLETE')

    def test_nonterminal_is_observed_not_restarted(self):
        self.data[self.op]['state'] = 'waiting'
        with self.assertRaisesRegex(ValueError, 'not terminal'):
            self.collect()
        self.assertEqual(self.paths, [self.op])

    def test_failure_preserved_without_fetching_nonexistent_result(self):
        self.data[self.op]['state'] = 'failed'
        self.data[self.base]['messages'].pop()
        row = self.collect()
        self.assertEqual(row['state'], 'failed')
        self.assertIsNone(row['verification']['public_history_parity'])
        self.assertNotIn(self.op + '/result', self.paths)

    def test_unstable_snapshot_is_incomplete(self):
        def get(path):
            value = self.get(path)
            if path == self.op and self.paths.count(path) == 2:
                value['current_attempt_id'] = 'changed'
            return value
        self.assertFalse(self.collect(get)['verification']['stable_snapshot'])

    def test_untrusted_identifiers_and_origins_are_rejected(self):
        for value in ('../other', 'a?token=x', 'a/b', ''):
            with self.assertRaises(ValueError):
                c.identifier(value)
        for origin in ('http://remote.test', 'https://user:pass@host', 'https://host/path', 'https://host?x=1'):
            with self.assertRaises(ValueError):
                c.reader(origin, 'token', 'tenant')


if __name__ == '__main__':
    unittest.main()
