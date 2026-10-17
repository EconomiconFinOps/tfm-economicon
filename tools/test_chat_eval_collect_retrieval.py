import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


r = load('chat-eval-retrieval')
fixtures = load('test_chat_eval_collect')


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.CollectionTests()
        f.setUp()
        self.sample = f.sample
        evidence = [{'id': 'used', 'kind': 'corpus', 'content': '<literal> ñ'},
                    {'id': 'unused', 'kind': 'corpus', 'content': 'Other'}]
        content = json.dumps({'evidence': evidence, 'omissions': []}, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        digest = hashlib.sha256(content.replace('<', '\\u003c').replace('>', '\\u003e').encode()).hexdigest()
        self.snapshot = {'operation_id': 'o', 'evidence': evidence, 'omissions': [], 'content_sha256': digest}
        f.result['metadata']['generation'] = {'context_manifest': {'evidence_ids': ['used', 'unused'], 'tool_result': {'content_sha256': digest}}}
        f.data[f.base]['messages'][1] = copy.deepcopy(f.result)
        f.data[f.op + '/evidence']['items'] = []
        self.row = f.collect()

    def test_exact_supplement_recovers_citations_without_changing_api_resources(self):
        before = copy.deepcopy(self.row)
        result = r.reconcile(self.row, self.snapshot, self.sample)
        self.assertEqual(result['collection_state'], 'VERIFIED_PUBLIC_SNAPSHOT')
        self.assertEqual([x['id'] for x in result['cited_chunks']], ['used'])
        self.assertEqual(result['resources'], before['resources'])
        self.assertEqual(self.row, before)
        self.assertEqual(result['derivation']['original_collection_state'], 'INCOMPLETE')

    def test_altered_fragment_or_omissions_rejected(self):
        for field in ('evidence', 'omissions'):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot[field].append({'injected': True})
            with self.assertRaises(ValueError):
                r.reconcile(self.row, snapshot, self.sample)

    def test_other_operation_rejected(self):
        with self.assertRaises(ValueError):
            r.reconcile(self.row, {**self.snapshot, 'operation_id': 'other'}, self.sample)

    def test_unknown_citation_remains_incomplete(self):
        row = copy.deepcopy(self.row)
        row['resources']['result']['metadata']['response']['evidence'] = [{'id': 'unknown'}]
        row['resources']['history']['messages'][1] = copy.deepcopy(row['resources']['result'])
        row['resources_sha256'] = r.collect.digest(row['resources'])
        result = r.reconcile(row, self.snapshot, self.sample)
        self.assertEqual(result['collection_state'], 'INCOMPLETE')

    def test_supplement_cannot_repair_history_or_wrong_question(self):
        result = r.reconcile(self.row, self.snapshot, {**self.sample, 'content': 'Wrong input'})
        self.assertEqual(result['collection_state'], 'INCOMPLETE')
        row = copy.deepcopy(self.row)
        row['resources']['history']['messages'][1]['content'] = 'Changed answer'
        row['resources_sha256'] = r.collect.digest(row['resources'])
        self.assertEqual(r.reconcile(row, self.snapshot, self.sample)['collection_state'], 'INCOMPLETE')

    def test_changed_raw_resources_rejected(self):
        row = copy.deepcopy(self.row)
        row['resources']['context'] = {}
        with self.assertRaises(ValueError):
            r.reconcile(row, self.snapshot, self.sample)


if __name__ == '__main__':
    unittest.main()
