import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).with_name('chat-eval-jup071.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def plan():
    return {'version': 1, 'bank_sha256': 'a' * 64, 'repetitions': 3,
            'samples': [{'sample_id': f'JUP-071-001:r{r}', 'case_id': 'JUP-071-001',
                         'repetition': r, 'content': 'Missing denominator; clarify.'} for r in range(1, 4)]}


def handle(r=1):
    return {'sample_id': f'JUP-071-001:r{r}', 'conversation_id': f'c{r}', 'operation_id': f'o{r}'}


def resources(r=1):
    base = f'/assistant/conversations/c{r}'
    op = base + f'/generations/o{r}'
    result = {'id': f'a{r}', 'role': 'assistant', 'content': 'Please supply the denominator.',
              'metadata': {'response': {'answer': 'Please supply the denominator.',
                                       'evidence': [{'id': 'source'}]}}}
    return {op: {'operation_id': f'o{r}', 'state': 'completed', 'question_id': f'q{r}'},
            op + '/context': {'manifest': {}},
            op + '/evidence': {'items': [{'id': 'source', 'kind': 'corpus', 'source': 'policy.md',
                                          'content': 'Never divide by zero.'}]},
            op + '/result': result,
            base: {'messages': [{'id': f'q{r}', 'role': 'user', 'content': plan()['samples'][0]['content']}, result]}}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'receipts'
        self.data = {**resources(1), **resources(2), **resources(3)}
        self.seen = []

    def get(self, path):
        self.seen.append(path)
        return copy.deepcopy(self.data[path])

    def collect(self, handles=None, get=None):
        return b.collect_all(plan(), handles if handles is not None else [handle()], get or self.get, self.output)

    def test_three_repetitions_keep_independent_operations_and_exact_prompts(self):
        self.collect([handle(r) for r in (1, 2, 3)])
        rows, manifest = b.rows_from(plan(), self.output)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(manifest['receipts']), 3)
        for sample in plan()['samples']:
            converted = b.public_row(sample, rows[sample['sample_id']])
            self.assertEqual(converted['prompt'], sample['content'])
            self.assertIsNone(converted['failure_category'])
            self.assertEqual(converted['citations'], ['source'])
            self.assertEqual(converted['retrieved'], [])  # No fabricated distance.
        self.assertTrue(all(path.startswith('/assistant/conversations/') for path in self.seen))

    def test_missing_handles_remain_missing_not_fake_answers(self):
        self.collect([])
        rows, manifest = b.rows_from(plan(), self.output)
        self.assertEqual(rows, {})
        self.assertEqual(manifest['receipts'], [])

    def test_unknown_duplicate_and_reused_handles_fail_before_reads(self):
        invalid = [[{**handle(), 'sample_id': 'unknown'}], [handle(), handle()],
                   [handle(), {**handle(2), 'conversation_id': 'c1'}],
                   [handle(), {**handle(2), 'operation_id': 'o1'}],
                   [{**handle(), 'token': 'secret'}], [{**handle(), 'operation_id': '../escape'}]]
        for handles in invalid:
            with self.subTest(handles=handles), self.assertRaises(ValueError):
                self.collect(handles)
        self.assertEqual(self.seen, [])
        self.assertFalse(self.output.exists())

    def test_recollection_never_overwrites_failed_or_successful_run(self):
        self.collect()
        original = (self.output / 'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.collect()
        self.assertEqual((self.output / 'manifest.json').read_bytes(), original)

    def test_transport_error_is_preserved_redacted_and_blocked(self):
        def fail(path):
            raise TimeoutError('SECRET_PROVIDER_PAYLOAD')
        self.collect(get=fail)
        rows, _ = b.rows_from(plan(), self.output)
        row = rows[handle()['sample_id']]
        self.assertNotIn('SECRET_PROVIDER_PAYLOAD', json.dumps(row))
        self.assertEqual(row['collection_errors']['observation']['class'], 'TimeoutError')
        self.assertEqual(b.public_row(plan()['samples'][0], row)['failure_category'], 'invalid_response')

    def test_nonterminal_is_observed_once_never_resumed(self):
        self.data['/assistant/conversations/c1/generations/o1']['state'] = 'running'
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        self.assertEqual(len(self.seen), 1)
        self.assertEqual(rows[handle()['sample_id']]['collection_state'], 'INCOMPLETE')

    def test_failed_terminal_never_exported_as_success(self):
        self.data['/assistant/conversations/c1/generations/o1']['state'] = 'failed'
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        row = b.public_row(plan()['samples'][0], rows[handle()['sample_id']])
        self.assertEqual(row['failure_category'], 'invalid_response')
        self.assertEqual(row['answer'], '')
        self.assertNotIn('/assistant/conversations/c1/generations/o1/result', self.seen)

    def test_receipt_tampering_and_missing_file_are_rejected(self):
        self.collect()
        path = self.output / 'JUP-071-001-r1.json'
        row = b.read(path)
        row['results'][0]['result']['content'] = 'forged'
        path.write_text(json.dumps(row), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'changed'):
            b.rows_from(plan(), self.output)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            b.rows_from(plan(), self.output)

    def test_cross_sample_identity_rejected_even_with_updated_receipt_digest(self):
        self.collect()
        path = self.output / 'JUP-071-001-r1.json'
        receipt = b.read(path)
        receipt['results'][0]['operation']['operation_id'] = 'other'
        path.write_text(json.dumps(receipt), encoding='utf-8')
        manifest = b.read(self.output / 'manifest.json')
        manifest['receipts'][0]['sha256'] = b.collector.digest(receipt)
        (self.output / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'identity'):
            b.rows_from(plan(), self.output)

    def test_snapshot_flag_cannot_override_missing_evidence_or_wrong_prompt(self):
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        for mutate in ('evidence', 'prompt'):
            row = copy.deepcopy(rows[handle()['sample_id']])
            if mutate == 'evidence':
                del row['resources']['evidence']
            else:
                row['resources']['history']['messages'][0]['content'] = 'Other question'
            self.assertEqual(b.public_row(plan()['samples'][0], row)['failure_category'], 'invalid_response')

    def test_known_distance_retained_and_full_source_stays_in_sidecar(self):
        self.data['/assistant/conversations/c1/generations/o1/evidence']['items'][0]['distance'] = 0.2
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        row = b.public_row(plan()['samples'][0], rows[handle()['sample_id']])
        self.assertEqual(row['retrieved'][0]['distance'], 0.2)
        self.assertEqual(row['retrieved'][0]['content'], 'Never divide by zero.')

    def test_output_inside_checkout_or_existing_file_rejected(self):
        with self.assertRaises(ValueError):
            b.outside(b.ROOT / 'docs/private.json', self.root)
        suite = self.root / 'suite'
        with self.assertRaises(ValueError):
            b.outside(suite / 'outputs.json', suite)
        path = self.root / 'result.json'
        b.write_new(path, {'original': True})
        with self.assertRaises(FileExistsError):
            b.write_new(path, {})
        self.assertEqual(b.read(path), {'original': True})

    def test_changed_plan_or_suite_rejected(self):
        with patch.object(b, 'plan_for', return_value=plan()):
            b.validate_plan(plan(), object())
            changed = plan()
            changed['samples'][0]['content'] = 'Expected answer injected'
            with self.assertRaises(ValueError):
                b.validate_plan(changed, object())

    def retrieval_snapshot(self):
        op = '/assistant/conversations/c1/generations/o1'
        evidence = self.data[op + '/evidence']['items']
        content = json.dumps({'evidence': evidence, 'omissions': []}, sort_keys=True,
                             ensure_ascii=False, separators=(',', ':'))
        digest = b.retrieval.hashlib.sha256(content.replace('<', '\\u003c').replace('>', '\\u003e').encode()).hexdigest()
        self.data[op + '/result']['metadata']['generation'] = {
            'context_manifest': {'evidence_ids': ['source'], 'tool_result': {'content_sha256': digest}}}
        self.data[op + '/evidence']['items'] = []
        return {'operation_id': 'o1', 'evidence': evidence, 'omissions': [], 'content_sha256': digest}

    def test_rag_supplement_exports_full_evidence_and_preserves_initial_receipt(self):
        snapshot = self.retrieval_snapshot()
        b.collect_all(plan(), [handle()], self.get, self.output, [snapshot])
        rows, _ = b.rows_from(plan(), self.output)
        original = b.read(self.output / 'originals/JUP-071-001-r1.json')['results'][0]
        self.assertEqual(original['collection_state'], 'INCOMPLETE')
        row = rows[handle()['sample_id']]
        self.assertEqual(row['resources'], original['resources'])
        converted = b.public_row(plan()['samples'][0], row)
        self.assertIsNone(converted['failure_category'])
        self.assertEqual(converted['public_evidence'], snapshot['evidence'])
        self.assertEqual(converted['retrieved'], [])
        changed = copy.deepcopy(row)
        changed['retrieval_supplement']['evidence'][0]['content'] = 'Forged'
        self.assertEqual(b.public_row(plan()['samples'][0], changed)['failure_category'], 'invalid_response')

    def test_rejected_supplement_keeps_original_and_blocks_export(self):
        snapshot = self.retrieval_snapshot()
        snapshot['omissions'] = [{'unrecorded': True}]
        b.collect_all(plan(), [handle()], self.get, self.output, [snapshot])
        rows, _ = b.rows_from(plan(), self.output)
        row = rows[handle()['sample_id']]
        self.assertEqual(row['collection_errors']['retrieval_supplement']['class'], 'RejectedSnapshot')
        self.assertEqual(b.public_row(plan()['samples'][0], row)['failure_category'], 'invalid_response')
        self.assertTrue((self.output / 'originals/JUP-071-001-r1.json').is_file())

    def test_export_is_stable_and_config_comparable_across_repetitions(self):
        self.collect([handle(r) for r in (1, 2, 3)])
        config = {field: 'descriptive value' for field in ('commit', 'corpus', 'provider', 'alias', 'retrieval', 'generation')}
        validate = []
        tool = SimpleNamespace(load_suite=lambda: ({}, {}), campaign=lambda *args: [],
                               provenance=lambda suite, kind, cfg: {'configuration': cfg, 'collected_at': 'NOW',
                                                                   'kind': kind, 'model_execution_verified': False},
                               validate_raw=lambda raw, *args: validate.append(raw))
        with patch.object(b, 'validate_plan'):
            one = b.export_raw(tool, plan(), self.output, 1, config)
            same = b.export_raw(tool, plan(), self.output, 1, config)
            two = b.export_raw(tool, plan(), self.output, 2, config)
        self.assertEqual(one, same)
        self.assertEqual(one['execution']['configuration'], two['execution']['configuration'])
        self.assertNotEqual(b.collector.digest(one), b.collector.digest(two))
        self.assertFalse(one['execution']['model_execution_verified'])
        self.assertEqual(len(validate), 3)
        with patch.object(b, 'validate_plan'), self.assertRaises(ValueError):
            b.export_raw(tool, plan(), self.output, 1, {**config, 'token': 'SECRET'})


if __name__ == '__main__':
    unittest.main()
