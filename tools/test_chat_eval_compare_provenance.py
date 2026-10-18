"""Counterexamples for cross-provenance comparisons; never accept/relabel a campaign."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('provenance_compare', Path(__file__).with_name('chat-eval-compare-provenance.py'))
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)
ev = comparison.evaluator


class ProvenanceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.old = ev.read(ev.ROOT / 'tools/fixtures/chat-eval/JUP-069-questions-1.0.0.json')
        self.new = copy.deepcopy(self.old)
        self.new['suite_version'] = '1.0.1'
        self.new['sources']['rules']['sha256'] = 'new-corpus-not-old-measurement'
        self.rules_a = {'rules_version': 'fixture', 'bank': {'suite_version': '1.0.0'}, 'rules': ['unchanged']}
        self.rules_b = dict(copy.deepcopy(self.rules_a), bank={'suite_version': '1.0.1'})
        self.a = self.report(self.old, self.rules_a)
        self.b = self.report(self.new, self.rules_b)

    def report(self, bank, rules):
        case = bank['cases'][0]
        requirements = ev.requirements(case)
        rows = []
        for rep in (1, 2, 3):
            checks = {k: dict(v, status='pass', reason='Synthetic test judgment', reviewer='fixture',
                              evidence_sha256='response-evidence', semantic_identity_sha256='response-context')
                      for k, v in requirements.items()}
            rows.append({'case_id': case['id'], 'repetition': rep, 'repetitions_expected': 3,
                         'state': 'completed', 'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT',
                         'input_matches_bank': True, 'evidence_sha256': 'response-evidence',
                         'semantic_identity_sha256': 'response-context', 'checks': checks})
        bank_hash = ev.digest(bank)
        return {'version': 1, 'bank_sha256': bank_hash, 'rules_sha256': ev.digest(rules),
                'partition_sha256': ev.digest(ev.partition(bank, bank_hash)),
                'scorer_sha256': 'original-scorer', 'heuristic_sha256': 'original-heuristic',
                'summary': {'repetitions_expected': 3}, 'samples': rows}

    def compare(self):
        return comparison.compare_campaigns(self.a, self.b, self.old, self.new, self.rules_a, self.rules_b,
                                            ev.digest(self.old), ev.digest(self.new),
                                            ev.digest(self.rules_a), ev.digest(self.rules_b))

    def test_provenance_revision_preserves_distinct_banks_and_original_reports(self):
        original = copy.deepcopy((self.a, self.b, self.old, self.new))
        result = self.compare()
        self.assertNotEqual(result['before_bank_sha256'], result['after_bank_sha256'])
        self.assertEqual(result['paired_responses'], 3)
        self.assertTrue(result['missing_after'])  # Other bank cases were never executed.
        self.assertFalse(result['human_acceptance'])
        self.assertFalse(result['labels_transferred'])
        self.assertEqual(original, (self.a, self.b, self.old, self.new))

    def test_changed_question_context_expected_category_or_language_is_not_provenance(self):
        original_bank = copy.deepcopy(self.new)
        for field in ('question', 'context', 'category', 'expected'):
            with self.subTest(field=field):
                self.new = copy.deepcopy(original_bank)
                self.new['cases'][0][field] = 'different'
                with self.assertRaisesRegex(ValueError, 'non-provenance'):
                    self.compare()
        self.new = copy.deepcopy(original_bank)
        self.new['language'] = 'en'
        with self.assertRaisesRegex(ValueError, 'non-provenance'):
            self.compare()

    def test_bank_duplicates_and_empty_bank_are_rejected(self):
        for cases in ([], [self.new['cases'][0], self.new['cases'][0]]):
            self.new['cases'] = cases
            with self.assertRaises(ValueError):
                self.compare()

    def test_changed_heuristic_rules_or_scorer_cannot_be_ignored(self):
        self.rules_b['rules'].append('new forbidden heuristic')
        with self.assertRaisesRegex(ValueError, 'rules changed'):
            self.compare()
        self.rules_b['rules'].pop()
        for field in ('version', 'scorer_sha256', 'heuristic_sha256'):
            original = self.b[field]
            self.b[field] = 'different'
            with self.assertRaisesRegex(ValueError, 'implementation'):
                self.compare()
            self.b[field] = original

    def test_original_bank_rule_partition_and_version_bindings_are_required(self):
        for field in ('bank_sha256', 'rules_sha256', 'partition_sha256'):
            original = self.b[field]
            self.b[field] = 'forged'
            with self.assertRaises(ValueError):
                self.compare()
            self.b[field] = original
        self.rules_b['bank'] = {'suite_version': '1.0.0'}
        with self.assertRaisesRegex(ValueError, 'version'):
            self.compare()

    def test_omitted_extra_or_forged_criterion_is_rejected(self):
        original = copy.deepcopy(self.b['samples'][0]['checks'])
        self.b['samples'][0]['checks'].pop('forbidden-1')
        with self.assertRaisesRegex(ValueError, 'criterion'):
            self.compare()
        self.b['samples'][0]['checks'] = copy.deepcopy(original)
        self.b['samples'][0]['checks']['required-1']['criterion'] = 'A different requirement'
        with self.assertRaisesRegex(ValueError, 'criterion'):
            self.compare()
        self.b['samples'][0]['checks'] = copy.deepcopy(original)
        self.b['samples'][0]['checks']['forged'] = original['required-1']
        with self.assertRaisesRegex(ValueError, 'criterion'):
            self.compare()

    def test_stale_judgment_or_missing_reason_cannot_be_compared(self):
        check = self.b['samples'][0]['checks']['required-1']
        for field in ('evidence_sha256', 'semantic_identity_sha256', 'reason', 'reviewer'):
            original = check[field]
            check[field] = ''
            with self.assertRaises(ValueError):
                self.compare()
            check[field] = original

    def test_duplicates_and_boolean_repetitions_are_rejected(self):
        self.b['samples'].append(copy.deepcopy(self.b['samples'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.compare()
        self.b['samples'].pop()
        self.b['samples'][0]['repetition'] = True
        with self.assertRaisesRegex(ValueError, 'repetition'):
            self.compare()

    def test_technical_input_and_evidence_failures_are_excluded_even_with_pass_labels(self):
        for field, value, reason in [('state', 'failed', 'technical_failure'),
                                     ('input_matches_bank', None, 'input_unverified'),
                                     ('collection_state', 'INCOMPLETE', 'evidence_incomplete')]:
            original = self.b['samples'][0][field]
            self.b['samples'][0][field] = value
            result = self.compare()
            self.assertEqual(result['excluded_pairs'][0]['after'], reason)
            self.assertFalse(any(t['repetition'] == 1 for t in result['transitions']))
            self.b['samples'][0][field] = original

    def test_regressions_are_grouped_per_response_and_uncertainty_is_not_hidden(self):
        checks = self.b['samples'][1]['checks']
        for key in ('required-1', 'forbidden-1'):
            checks[key].update(status='fail', failure_cluster='one-unsupported-claim')
        checks['quality-grounding']['status'] = 'uncertain'
        result = self.compare()
        self.assertEqual(result['regressed_responses'], [('JUP-069-001', 2)])
        self.assertEqual(result['counts']['pass->fail'], 2)
        self.assertEqual(result['counts']['pass->uncertain'], 1)
        self.assertEqual(result['transitions'][0]['before'], 'pass')

    def test_missing_and_unpaired_samples_stay_visible(self):
        self.b['samples'].pop()
        result = self.compare()
        self.assertEqual(result['unpaired_before'], [('JUP-069-001', 3)])
        self.assertIn(('JUP-069-001', 3), result['missing_after'])

    def test_audit_must_bind_original_report_and_original_judgments(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = {key: root / (key + '.json') for key in ('report', 'bank', 'rules', 'audit')}
            self.a['notes_sha256'] = 'original-notes'
            for key, data in [('report', self.a), ('bank', self.old), ('rules', self.rules_a)]:
                paths[key].write_text(json.dumps(data), encoding='utf-8')
            audit = {'local_review': {'review_file': paths['report'].name,
                                      'review_sha256': ev.file_hash(paths['report']),
                                      'notes_sha256': 'original-notes'}}
            paths['audit'].write_text(json.dumps(audit), encoding='utf-8')
            self.assertEqual(comparison.load_side(paths['report'], paths['audit'], paths['bank'], paths['rules'])[0], self.a)
            self.a['samples'][0]['checks']['required-1']['status'] = 'fail'
            paths['report'].write_text(json.dumps(self.a), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'original report'):
                comparison.load_side(paths['report'], paths['audit'], paths['bank'], paths['rules'])


if __name__ == '__main__':
    unittest.main()
