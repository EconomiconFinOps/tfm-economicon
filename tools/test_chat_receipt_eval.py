"""Regression checks for false acceptance and paired evidence handling."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('receipt_eval', Path(__file__).with_name('chat-receipt-eval.py'))
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


class ReceiptEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.bank = ev.read(ev.BANK)
        self.bank_hash = ev.file_hash(ev.BANK)
        self.manifest = ev.partition(self.bank, self.bank_hash)
        self.receipt = ev.read(ev.ROOT / 'docs/evidence/jup-035-pr121-full28-20261012.json')
        self.samples = ev.normalize(self.receipt, self.bank, self.bank_hash, 'receipt-a', 'results')

    def test_completed_and_old_positive_labels_never_become_pass(self):
        report = ev.score(self.samples, self.bank, {}, self.manifest)
        self.assertEqual(report['summary']['verdicts'], {'pending': 23, 'technical_failure': 5})
        self.assertEqual(report['summary']['requirements'], {'unreviewed': 165})

    def test_bank_and_duplicate_case_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'bank hash'):
            ev.normalize(self.receipt, self.bank, 'wrong', 'a', 'results')
        self.receipt['results'].append(self.receipt['results'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            ev.normalize(self.receipt, self.bank, self.bank_hash, 'a', 'results')

    def test_recorded_true_does_not_hide_wrong_input(self):
        self.receipt['results'][0]['question'] = 'Otra pregunta'
        samples = ev.normalize(self.receipt, self.bank, self.bank_hash, 'a', 'results')
        self.assertEqual(ev.score(samples, self.bank, {}, self.manifest)['samples'][0]['verdict'], 'input_unverified')

    def labels(self, sample, status='pass'):
        return {key: {'status': status, 'reviewer': 'test', 'reason': 'fixture',
                      'evidence_sha256': sample['evidence_sha256'],
                      'criterion_sha256': requirement['criterion_sha256'],
                      **({'failure_cluster': 'single-cause'} if status == 'fail' else {})}
                for key, requirement in sample['requirements'].items()}

    def test_stale_label_and_unknown_sample_are_rejected(self):
        row = self.samples[0]
        labels = self.labels(row)
        labels['required-1']['evidence_sha256'] = 'old-response'
        with self.assertRaisesRegex(ValueError, 'stale'):
            ev.score(self.samples, self.bank, {row['sample_id']: labels}, self.manifest)
        with self.assertRaisesRegex(ValueError, 'outside'):
            ev.score(self.samples, self.bank, {'unknown': {}}, self.manifest)

    def test_forbidden_unreviewed_prevents_pass(self):
        row = self.samples[0]
        labels = self.labels(row)
        del labels['forbidden-1']
        report = ev.score(self.samples, self.bank, {row['sample_id']: labels}, self.manifest)
        self.assertEqual(report['samples'][0]['verdict'], 'pending')

    def test_technical_failure_cannot_be_overridden_by_manual_pass(self):
        row = self.samples[4]
        report = ev.score(self.samples, self.bank, {row['sample_id']: self.labels(row)}, self.manifest)
        self.assertEqual(report['samples'][4]['verdict'], 'technical_failure')

    def test_correlated_requirements_count_as_one_response_cluster(self):
        row = self.samples[0]
        report = ev.score(self.samples, self.bank, {row['sample_id']: self.labels(row, 'fail')}, self.manifest)
        self.assertGreater(report['summary']['requirements']['fail'], 1)
        self.assertEqual(report['summary']['response_failure_clusters'], 1)

    def test_partition_keeps_complete_families_together(self):
        families = {}
        for case in self.bank['cases']:
            families.setdefault(case['category'], set()).add(self.manifest['cases'][case['id']])
        self.assertTrue(all(len(parts) == 1 for parts in families.values()))
        self.assertEqual(sum(v == 'reserve' for v in self.manifest['cases'].values()), 6)

    def test_second_receipt_uses_original_history_and_structured_response(self):
        receipt = ev.read(ev.ROOT / 'docs/evidence/jup-035-pr121-review-fixes-20261012.json')
        samples = ev.normalize(receipt, self.bank, self.bank_hash, 'b', 'full28')
        self.assertTrue(samples[0]['input_matches_bank'])
        self.assertEqual(samples[0]['answer'], receipt['full28'][0]['result']['metadata']['response']['answer'])
        self.assertEqual(len(samples), 28)

    def test_paired_comparison_groups_regressions_by_response(self):
        row = self.samples[0]
        a = ev.score(self.samples, self.bank, {row['sample_id']: self.labels(row)}, self.manifest)
        b = ev.score(self.samples, self.bank, {row['sample_id']: self.labels(row, 'fail')}, self.manifest)
        for report in (a, b):
            report.update(scorer_sha256='same', rules_sha256='same', heuristic_sha256='same')
        comparison = ev.compare(a, b)
        self.assertEqual(comparison['regressed_responses'], [('JUP-069-001', 1)])
        self.assertGreater(comparison['counts']['pass->fail'], 1)
        b['rules_sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            ev.compare(a, b)

    def test_existing_numeric_heuristics_are_not_semantic_verdicts(self):
        legacy, rules = ev.legacy(), ev.read(ev.RULES)
        case = self.bank['cases'][0]
        for answer, expected in [('El total es 1000 USD.', False),
                                 ('El total es 1000 EUR.', True),
                                 ('El total no es 1000 EUR.', True)]:
            # Last case documents an actual heuristic limitation: never promote
            # a numeric match directly into semantic PASS.
            result = ev.diagnostics(case, answer, rules, legacy)['numbers-1']
            self.assertEqual(result['heuristic_match'], expected)
            self.assertEqual(result['semantic_status'], 'unreviewed')

    def repeated_receipt(self):
        receipt = copy.deepcopy(self.receipt)
        receipt['repetitions'] = 3
        receipt['results'] = [dict(copy.deepcopy(row), repetition=repeat)
                              for repeat in range(1, 4)
                              for row in self.receipt['results']]
        return receipt

    def test_all_repetitions_preserve_failures_without_best_of_selection(self):
        samples = ev.normalize(self.repeated_receipt(), self.bank, self.bank_hash, 'n3', 'results')
        report = ev.score(samples, self.bank, {}, self.manifest)
        self.assertEqual(len({s['sample_id'] for s in samples}), 84)
        self.assertEqual(report['summary']['samples_expected'], 84)
        self.assertEqual(report['summary']['missing_samples'], [])
        self.assertEqual(report['summary']['verdicts'], {'pending': 69, 'technical_failure': 15})

    def test_missing_repetition_is_visible_even_when_all_cases_present(self):
        receipt = self.repeated_receipt()
        receipt['results'].pop()
        samples = ev.normalize(receipt, self.bank, self.bank_hash, 'n3', 'results')
        summary = ev.score(samples, self.bank, {}, self.manifest)['summary']
        self.assertEqual(summary['missing_cases'], [])
        self.assertEqual(summary['missing_samples'], [{'case_id': 'JUP-069-028', 'repetition': 3}])

    def test_repeated_receipts_reject_ambiguous_or_duplicate_slots(self):
        empty = dict(self.repeated_receipt(), results=[])
        with self.assertRaisesRegex(ValueError, 'empty'):
            ev.normalize(empty, self.bank, self.bank_hash, 'n3', 'results')
        for value in (None, True, 0, 4, '2'):
            receipt = self.repeated_receipt()
            receipt['results'][0]['repetition'] = value
            with self.assertRaisesRegex(ValueError, 'repetition'):
                ev.normalize(receipt, self.bank, self.bank_hash, 'n3', 'results')
        receipt = self.repeated_receipt()
        receipt['results'].append(copy.deepcopy(receipt['results'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            ev.normalize(receipt, self.bank, self.bank_hash, 'n3', 'results')

    def test_regression_is_paired_to_exact_repetition(self):
        samples = ev.normalize(self.repeated_receipt(), self.bank, self.bank_hash, 'n3', 'results')
        target = samples[28]
        before = ev.score(samples, self.bank, {target['sample_id']: self.labels(target)}, self.manifest)
        after = ev.score(samples, self.bank, {target['sample_id']: self.labels(target, 'fail')}, self.manifest)
        for report in (before, after):
            report.update(scorer_sha256='same', rules_sha256='same', heuristic_sha256='same')
        self.assertEqual(ev.compare(before, after)['regressed_responses'], [('JUP-069-001', 2)])


if __name__ == '__main__':
    unittest.main()
