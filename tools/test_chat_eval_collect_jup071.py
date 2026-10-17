import copy
import importlib.util
import io
import json
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).with_name('chat-eval-jup071.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def plan():
    return {'version': 2, 'suite_commit': 'a' * 40, 'bank_sha256': 'a' * 64, 'repetitions': 3,
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
            self.assertEqual(converted['failure_category'], 'invalid_response')
            self.assertEqual(converted['answer'], '')
            self.assertEqual(converted['citations'], [])
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
        self.assertIsNone(row['failure_category'])
        self.assertEqual(row['citations'], ['source'])
        self.assertEqual(row['answer'], 'Please supply the denominator.')

    def test_corpus_without_measured_distance_blocks_legacy_scoring(self):
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        original = rows[handle()['sample_id']]
        before = copy.deepcopy(original)
        self.assertEqual(original['collection_state'], 'VERIFIED_PUBLIC_SNAPSHOT')
        converted = b.public_row(plan()['samples'][0], original)
        self.assertEqual(converted['failure_category'], 'invalid_response')
        self.assertEqual(converted['answer'], '')
        self.assertEqual(converted['citations'], [])
        self.assertEqual(converted['retrieved'], [])
        self.assertEqual(converted['public_evidence'], original['authorized_evidence'])
        self.assertNotIn('distance', converted['public_evidence'][0])
        self.assertEqual(original, before)

    def test_capability_keeps_unmeasured_corpus_and_citations_without_changing_receipts(self):
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        original = rows[handle()['sample_id']]
        before = copy.deepcopy(original)
        for capability in (False, None, 1, 'True', True):
            converted = b.public_row(plan()['samples'][0], original, accepts_unmeasured_distance=capability)
            with self.subTest(capability=capability):
                if capability is True:
                    self.assertIsNone(converted['failure_category'])
                    self.assertEqual(converted['citations'], ['source'])
                    self.assertEqual(converted['retrieved'], [{'chunk_id': 'source', 'source': 'policy.md',
                                                               'content': 'Never divide by zero.', 'distance': None}])
                else:
                    self.assertEqual(converted['failure_category'], 'invalid_response')
        self.assertEqual(original, before)

    def test_capability_never_accepts_malformed_distance(self):
        sample = plan()['samples'][0]
        for distance in (None, 0, 0.2, True, '0.2', float('nan'), float('inf')):
            data = resources()
            data['/assistant/conversations/c1/generations/o1/evidence']['items'][0]['distance'] = distance
            row = b.collector.collect(lambda path: copy.deepcopy(data[path]), sample, 'c1', 'o1')
            converted = b.public_row(sample, row, accepts_unmeasured_distance=True)
            with self.subTest(distance=distance):
                self.assertEqual(converted['failure_category'],
                                 None if distance is None or b.measured_distance(distance) else 'invalid_response')

    def test_structured_summary_uses_verified_response_without_action_text(self):
        sample = plan()['samples'][0]
        for status, actions, expected in [('partial', ['SECRET_ACTION'], True), ('no_data', [], False),
                                           ('SECRET_STATUS', 'SECRET_ACTION', None)]:
            data = resources()
            data['/assistant/conversations/c1/generations/o1/result']['metadata']['response'].update(
                status=status, next_actions=actions)
            row = b.collector.collect(lambda path: copy.deepcopy(data[path]), sample, 'c1', 'o1')
            summary = b.public_row(sample, row)['structured']
            self.assertEqual(summary, {'status': None if status == 'SECRET_STATUS' else status,
                                       'has_next_actions': expected})
            self.assertNotIn('SECRET', json.dumps(summary))
            row['resources']['history']['messages'][0]['content'] = 'Other prompt'
            self.assertEqual(b.public_row(sample, row)['structured'], {'status': None, 'has_next_actions': None})

    def test_provenance_is_per_sample_server_reported_and_not_attested(self):
        op = '/assistant/conversations/c1/generations/o1'
        manifest = {'prompt_version': 'jup-035.chat.v3:' + 'b' * 64,
                    'response_schema_sha256': 'c' * 64, 'assembler_sha256': 'd' * 64,
                    'tokenizer_sha256': 'e' * 64, 'private_text': 'DO_NOT_EXPORT'}
        self.data[op + '/context']['manifest'] = {**manifest, 'tokenizer_sha256': 'f' * 64}
        self.data[op + '/result']['metadata']['generation'] = {
            'context_manifest': manifest, 'usage': {'prompt_tokens': 10, 'completion_tokens': 2, 'total_tokens': 12}}
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        reported = b.server_reported(plan()['samples'][0], rows[handle()['sample_id']])
        for key in ('prompt_version', 'response_schema_sha256', 'assembler_sha256', 'tokenizer_sha256'):
            self.assertEqual(reported[key], manifest[key])
        self.assertNotIn('prompt_sha256', reported)  # Version suffix is a bundle hash, not a prompt hash.
        self.assertNotIn('DO_NOT_EXPORT', json.dumps(reported))
        self.assertFalse(reported['attested'])
        self.assertTrue(reported['snapshot_verified'])
        self.assertEqual(reported['usage']['total_tokens'], 12)
        self.assertEqual(b.server_reported(plan()['samples'][1], {'resources': {}, 'conversation_id': 'c2',
                         'operation': {'operation_id': 'o2'}, 'collection_state': 'INCOMPLETE'}),
                         {'sample_id': 'JUP-071-001:r2', 'snapshot_verified': False, 'attested': False,
                          'prompt_version': None})

    def test_capability_keeps_supplement_but_never_bypasses_hash_validation(self):
        snapshot = self.retrieval_snapshot()
        b.collect_all(plan(), [handle()], self.get, self.output, [snapshot])
        rows, _ = b.rows_from(plan(), self.output)
        row = rows[handle()['sample_id']]
        self.assertIsNone(b.public_row(plan()['samples'][0], row, accepts_unmeasured_distance=True)['failure_category'])
        row['retrieval_supplement']['evidence'][0]['content'] = 'Forged'
        self.assertEqual(b.public_row(plan()['samples'][0], row, accepts_unmeasured_distance=True)['failure_category'],
                         'invalid_response')

    def test_answer_without_corpus_does_not_require_a_distance(self):
        op = '/assistant/conversations/c1/generations/o1'
        self.data[op + '/evidence']['items'] = []
        self.data[op + '/result']['metadata']['response']['evidence'] = []
        self.collect()
        rows, _ = b.rows_from(plan(), self.output)
        converted = b.public_row(plan()['samples'][0], rows[handle()['sample_id']])
        self.assertIsNone(converted['failure_category'])
        self.assertEqual(converted['answer'], 'Please supply the denominator.')
        self.assertEqual(converted['retrieved'], [])

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

    def test_v2_plan_ignores_commit_but_detects_changed_content_and_prompts(self):
        frozen = {**plan(), 'suite_files': {'tools/assistant-eval.py': 'a' * 64}}
        current = {**frozen, 'suite_commit': 'b' * 40}
        with patch.object(b, 'plan_for', side_effect=lambda *args: copy.deepcopy(current)):
            b.validate_plan(frozen, object())
            current['suite_files'] = {'tools/assistant-eval.py': 'c' * 64}
            with self.assertRaisesRegex(ValueError, 'frozen sources'):
                b.validate_plan(frozen, object())

    def test_legacy_plan_still_requires_original_commit(self):
        current = {**plan(), 'suite_files': {'tools/assistant-eval.py': 'a' * 64,
                                            'tools/assistant-metrics.py': 'b' * 64,
                                            'tools/retrieval-calibration.py': 'c' * 64}}
        frozen = {**current, 'version': 1, 'suite_files': {'tools/assistant-eval.py': 'a' * 64}}
        with patch.object(b, 'plan_for', side_effect=lambda *args: copy.deepcopy(current)):
            b.validate_plan(frozen, object())
            current['suite_commit'] = 'b' * 40
            with self.assertRaisesRegex(ValueError, 'frozen sources'):
                b.validate_plan(frozen, object())

    def test_plan_hashes_transitive_tools_and_detects_their_content_changes(self):
        files = ['tools/assistant-robustness.py', 'tools/assistant-eval.py', 'tools/assistant-metrics.py',
                 'tools/retrieval-calibration.py', 'suite.json', 'baseline.json', 'service.py',
                 'rules.json', 'methodology.md', 'corpus/policy.md']
        for name in files:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture\n', encoding='utf-8')
        cases = [{'id': f'JUP-071-{n:03}', 'content': f'Prompt {n}'} for n in range(29)]
        tool = SimpleNamespace(__file__=self.root / files[0], ROOT=self.root, SUITE=self.root / 'suite.json',
            BASELINE=self.root / 'baseline.json', SERVICE=self.root / 'service.py',
            evaluation=SimpleNamespace(RULES_PATH=self.root / 'rules.json', prompt_text=lambda c: c['content']),
            load_suite=lambda: ({'methodology': {'path': 'methodology.md'},
                                'sources': {'policy': {'path': 'corpus/policy.md'}}}, {}),
            campaign=lambda *args: cases, code_commit=lambda: 'a' * 40,
            file_digest=lambda p: hashlib.sha256(p.read_text(encoding='utf-8').encode()).hexdigest(),
            digest=b.collector.digest)
        frozen = b.plan_for(tool, 3)
        self.assertEqual(len(frozen['samples']), 87)
        self.assertEqual(set(frozen['suite_files']), set(files))
        tool.code_commit = lambda: 'b' * 40
        b.validate_plan(frozen, tool)
        (self.root / 'tools/assistant-metrics.py').write_text('changed\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'frozen sources'):
            b.validate_plan(frozen, tool)

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
        self.assertEqual(converted['failure_category'], 'invalid_response')
        self.assertEqual(converted['answer'], '')
        self.assertEqual(converted['citations'], [])
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

    def export_tool(self, capability=False):
        return SimpleNamespace(ACCEPTS_UNMEASURED_DISTANCE=capability,
                               load_suite=lambda: ({}, {}), campaign=lambda *args: [],
                               provenance=lambda suite, kind, cfg: {'configuration': cfg, 'kind': kind,
                                                                   'model_execution_verified': False},
                               validate_raw=lambda *args: None)

    def cli_files(self):
        for name, value in [('plan.json', plan()), ('handles.json', [handle()]),
                            ('run-info.json', {key: 'synthetic declaration' for key in
                                               ('commit', 'corpus', 'provider', 'alias', 'retrieval', 'generation')})]:
            b.write_new(self.root / name, value)

    def invoke(self, *args, tool=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(b, 'suite_tool', return_value=tool or self.export_tool()), \
             patch.object(b, 'validate_plan'), patch('sys.stdout', stdout), patch('sys.stderr', stderr):
            code = b.main(['--suite-root', str(self.root / 'suite'), *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_export_negotiates_capability_from_loaded_tool_only(self):
        self.collect()
        config = {key: 'declaration' for key in ('commit', 'corpus', 'provider', 'alias', 'retrieval', 'generation')}
        for flag in (False, 1, 'True', True):
            with patch.object(b, 'validate_plan'):
                raw = b.export_raw(self.export_tool(flag), plan(), self.output, 1, config)
            self.assertEqual(raw['execution']['collection']['accepts_unmeasured_distance'], flag is True)
            self.assertEqual(raw['cases'][0]['failure_category'], None if flag is True else 'invalid_response')

    def test_unrelated_suite_commit_does_not_change_reexport_or_pairing_identity(self):
        self.collect()
        tool = self.export_tool()
        config = {key: 'declaration' for key in ('commit', 'corpus', 'provider', 'alias', 'retrieval', 'generation')}
        tool.provenance = lambda *args: {'harness_commit': 'b' * 40, 'model_execution_verified': False}
        with patch.object(b, 'validate_plan'):
            before = b.export_raw(tool, plan(), self.output, 1, config)
            tool.provenance = lambda *args: {'harness_commit': 'c' * 40, 'model_execution_verified': False}
            after = b.export_raw(tool, plan(), self.output, 1, config)
        self.assertEqual(before, after)
        self.assertEqual(before['execution']['harness_commit'], plan()['suite_commit'])

    def test_collect_summary_and_strict_exit_preserve_incomplete_receipts(self):
        self.cli_files()
        for strict in (False, True):
            output = self.root / f'collected-{strict}'
            with patch.object(b.collector, 'reader', return_value=self.get), \
                 patch.dict(b.os.environ, {'CHAT_EVAL_TOKEN': 'SYNTHETIC', 'CHAT_EVAL_TENANT': 'test'}):
                code, stdout, _ = self.invoke('collect', '--plan', self.root / 'plan.json',
                    '--handles', self.root / 'handles.json', '--base-url', 'http://localhost',
                    '--output-dir', output, *(['--strict'] if strict else []))
            self.assertEqual(code, 3 if strict else 0)
            result = json.loads(stdout)
            self.assertEqual(result['summary']['missing'], 2)
            self.assertEqual(result['summary']['collection_states'], {'VERIFIED_PUBLIC_SNAPSHOT': 1})
            self.assertTrue((output / 'manifest.json').exists())

    def test_collection_strict_checks_failed_states_even_if_snapshot_verified(self):
        self.collect([handle(r) for r in (1, 2, 3)])
        rows, _ = b.rows_from(plan(), self.output)
        self.assertTrue(b.collection_complete(b.collection_summary(plan(), rows)))
        rows[handle()['sample_id']]['state'] = 'failed'
        self.assertFalse(b.collection_complete(b.collection_summary(plan(), rows)))

    def test_export_all_strict_and_single_are_identical_and_never_overwrite(self):
        self.cli_files()
        self.collect([handle(r) for r in (1, 2, 3)])
        common = ['export', '--plan', self.root / 'plan.json', '--receipts', self.output,
                  '--run-info', self.root / 'run-info.json']
        output = self.root / 'exports'
        code, stdout, _ = self.invoke(*common, '--all-repetitions', '--output-dir', output, '--strict')
        self.assertEqual(code, 3)  # Legacy consumer blocks all unmeasured corpus rows.
        self.assertEqual(json.loads(stdout)['summary'], {'exported': 3, 'blocked': 3, 'missing': 0,
                                                         'structured_statuses': {'unknown': 3}})
        first = (output / 'raw-r1.json').read_bytes()
        code, _, _ = self.invoke(*common, '--repetition', 1, '--output', self.root / 'single.json')
        self.assertEqual(code, 0)
        self.assertEqual(first, (self.root / 'single.json').read_bytes())
        code, _, error = self.invoke(*common, '--all-repetitions', '--output-dir', output)
        self.assertEqual(code, 2)
        self.assertIn('Output already exists', error)
        self.assertEqual(first, (output / 'raw-r1.json').read_bytes())
        code, stdout, _ = self.invoke(*common, '--all-repetitions', '--output-dir', self.root / 'capable',
                                     '--strict', tool=self.export_tool(True))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)['summary']['blocked'], 0)

    def test_cli_reports_safe_actionable_errors_without_external_exception_text(self):
        self.cli_files()
        self.collect()
        common = ['export', '--plan', self.root / 'plan.json', '--receipts', self.output,
                  '--run-info', self.root / 'run-info.json', '--repetition', 1, '--output', self.root / 'raw.json']
        (self.root / 'run-info.json').write_text('{"token":"SUPER_SECRET"}', encoding='utf-8')
        code, _, error = self.invoke(*common)
        self.assertEqual(code, 2)
        self.assertIn('exactly six nonempty descriptive strings', error)
        self.assertNotIn('SUPER_SECRET', error)
        with patch.object(b, 'export_raw', side_effect=ValueError('SUPER_SECRET')):
            code, _, error = self.invoke(*common)
        self.assertEqual(code, 2)
        self.assertNotIn('SUPER_SECRET', error)
        self.assertFalse((self.root / 'raw.json').exists())

    def test_export_all_validates_every_repetition_before_creating_output(self):
        self.cli_files()
        self.collect([handle(r) for r in (1, 2, 3)])
        tool = self.export_tool()
        tool.validate_raw = unittest.mock.Mock(side_effect=[None, None, ValueError('SECRET_VALIDATOR_TEXT')])
        output = self.root / 'exports'
        code, _, error = self.invoke('export', '--plan', self.root / 'plan.json', '--receipts', self.output,
            '--run-info', self.root / 'run-info.json', '--all-repetitions', '--output-dir', output, tool=tool)
        self.assertEqual(code, 2)
        self.assertEqual(tool.validate_raw.call_count, 3)
        self.assertNotIn('SECRET_VALIDATOR_TEXT', error)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
