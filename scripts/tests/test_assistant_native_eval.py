"""Offline native transport and campaign safety; no provider or product fixtures changed."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluation = load('native_evaluation_under_test', 'tools/assistant-eval.py')
budget_module = load('campaign_budget_under_test', 'tools/evaluation_budget.py')


class Reply(io.BytesIO):
    status = 200
    def __init__(self, value, sse=False):
        super().__init__(('data: ' + json.dumps(value) + '\n\n' if sse else json.dumps(value)).encode())
        self.headers = {'Content-Type': 'text/event-stream' if sse else 'application/json'}


class Opener:
    def __init__(self, replies): self.replies, self.calls = list(replies), []
    def open(self, request, timeout):
        self.calls.append(request)
        value = self.replies.pop(0)
        return value if isinstance(value, Reply) else Reply(value)


class NativeCollectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ledger = budget_module.BudgetLedger(Path(self.directory.name) / 'budget.json', alert=lambda _: None)
        self.ledger.initialize(budget_id='synthetic-test-only', limit='20', alert_at='15', authorization='synthetic local test')
        self.operation = {'operation_id': 'op', 'state': 'completed', 'attempt_count': 2}
        self.metadata = {'generation': {'operation_id': 'op', 'attempt_id': 'attempt',
            'context_manifest': {'evidence_ids': ['cost:synthetic', 'doc:chunk:fingerprint:0']}, 'usage': {'cost_usd': '.01'}},
            'citations': ['doc:chunk:fingerprint:0'], 'source_citations': [], 'response': {'answer': 'Synthetic answer'}}
        self.inputs = {'cases': [{'id': 'case-a', 'prompt': 'Exact frozen prompt', 'screen_context': {'synthetic': True}},
                                 {'id': 'case-b', 'prompt': 'Second frozen prompt', 'screen_context': {'synthetic': True}}]}
        self.retrieved = [{'chunk_id': 'doc:chunk:fingerprint:0', 'document_id': 'doc', 'source': 'synthetic',
            'content': 'Actual returned evidence.', 'distance': .8, 'chunk_metadata': {'section_path': ['Real section']}}]

    def responses(self):
        return [{'id': 'conversation'}, Reply({'operation': self.operation}, sse=True),
                {'content': 'Synthetic answer', 'metadata': self.metadata}]

    def collect(self, opener, **kwargs):
        return evaluation.collect_native_cases('http://127.0.0.1:9999', 'synthetic@example.invalid', 'synthetic-password',
            'synthetic-tenant', self.inputs, opener=opener, budget=self.ledger,
            evidence_reader=kwargs.pop('evidence_reader', lambda *args: self.retrieved), sleep=lambda _: None, **kwargs)

    def test_native_uses_exact_prompt_effective_tool_evidence_and_retains_unknown_whole_cost(self):
        opener = Opener([{'access_token': 'synthetic'}] + self.responses())
        raw = self.collect(opener)
        self.assertEqual(len(raw['cases']), 1)  # No next paid case before cost reconciliation.
        entry = raw['cases'][0]
        self.assertIsNone(entry['failure_category'])
        self.assertEqual(entry['retrieved'], self.retrieved)
        self.assertIsNone(entry['cost_usd'])  # Final generator usage alone is not the whole operation bill.
        request = opener.calls[2]
        self.assertTrue(request.full_url.endswith('/generations'))
        self.assertEqual(json.loads(request.data)['content'], self.inputs['cases'][0]['prompt'])
        self.assertEqual(opener.calls[-1].get_method(), 'GET')
        state = self.ledger._read()
        self.assertEqual(next(iter(state['operations'].values()))['state'], 'unknown')
        self.assertEqual(self.ledger.committed(state), Decimal('6.50'))

    def test_all_request_receipts_allow_next_case_without_double_counting_backend_retries(self):
        opener = Opener([{'access_token': 'synthetic'}] + self.responses() + self.responses())
        def account(identifier, entry):
            return {'operation_id': identifier, 'cost_usd': '.04', 'all_requests_accounted': True,
                    'operation_finished': True, 'reference': 'synthetic gateway receipt'}
        raw = self.collect(opener, account=account)
        self.assertEqual(len(raw['cases']), 2)
        self.assertEqual(self.ledger.committed(self.ledger._read()), Decimal('.08'))
        self.assertEqual(sum(request.full_url.endswith('/generations') for request in opener.calls), 2)

    def test_missing_effective_evidence_is_an_observed_failure_with_no_automatic_retry(self):
        opener = Opener([{'access_token': 'synthetic'}] + self.responses())
        raw = self.collect(opener, evidence_reader=lambda *args: [])
        self.assertEqual(raw['cases'][0]['failure_category'], 'invalid_response')
        self.assertEqual(len(raw['cases']), 1)
        self.assertEqual(sum(request.full_url.endswith('/generations') for request in opener.calls), 1)

    def test_restarted_collector_cannot_submit_a_paid_operation_while_an_unknown_is_pending(self):
        self.ledger.reserve('previous-timeout', '6.50', kind='chat')
        self.ledger.finish('previous-timeout')
        opener = Opener([{'access_token': 'synthetic'}, {'id': 'conversation'}])
        with self.assertRaises(budget_module.BudgetError):
            self.collect(opener)
        self.assertFalse(any(request.full_url.endswith('/generations') for request in opener.calls))
        self.assertEqual(set(self.ledger._read()['operations']), {'previous-timeout'})
        self.assertEqual(self.ledger.committed(self.ledger._read()), Decimal('6.50'))

    def test_structural_labels_use_persisted_metadata_without_legacy_id_arithmetic(self):
        labelled = evaluation.label_fragments(self.retrieved, {'doc': 'docs/assistant-corpus/finops.md'}, 500, 50)
        self.assertEqual(labelled[0]['heading'], 'Real section')
        self.assertEqual(self.retrieved[0]['chunk_metadata']['section_path'], ['Real section'])

    def test_case_duplicates_and_expected_answers_are_rejected_before_login_or_spend(self):
        for mutate in [lambda: self.inputs['cases'].append(self.inputs['cases'][0]),
                       lambda: self.inputs['cases'][0].update(expected='Never send an answer reference')]:
            self.inputs['cases'] = self.inputs['cases'][:2]
            mutate()
            opener = Opener([])
            with self.assertRaises(evaluation.EvaluationError): self.collect(opener)
            self.assertEqual(opener.calls, [])
            self.inputs['cases'][0].pop('expected', None)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.alerts = []
        self.ledger = budget_module.BudgetLedger(Path(self.directory.name) / 'budget.json', alert=self.alerts.append)
        self.ledger.initialize(budget_id='synthetic-test-only', limit=20, alert_at=15, authorization='synthetic local test')

    def test_alert_precedes_boundary_and_limit_is_enforced_after_settlement(self):
        for identifier in ['a', 'b', 'c']:
            self.ledger.reserve(identifier, '6.50', kind='chat')
            self.ledger.finish(identifier, {'operation_id': identifier, 'cost_usd': '6.50',
                'all_requests_accounted': True, 'operation_finished': True, 'reference': 'synthetic receipt'})
        self.assertEqual(len(self.alerts), 1)
        self.assertEqual(self.ledger._read()['alerts'][0]['before_operation'], 'c')
        self.assertEqual(self.ledger.committed(self.ledger._read()), Decimal('19.50'))
        with self.assertRaises(budget_module.BudgetError): self.ledger.reserve('d', '6.50', kind='chat')

    def test_unknown_preserves_reservation_and_blocks_restarted_admission_until_cost_and_finish_are_proven(self):
        self.ledger.reserve('timed-out', '6.50', kind='chat')
        self.ledger.finish('timed-out')
        resumed = budget_module.BudgetLedger(self.ledger.path, alert=self.alerts.append)
        for kind in ['chat', 'index', 'auxiliary']:
            with self.assertRaises(budget_module.BudgetError):
                resumed.reserve('next-' + kind, '6.50', kind=kind)
        state = resumed._read()
        self.assertEqual(set(state['operations']), {'timed-out'})
        self.assertEqual(state['operations']['timed-out']['state'], 'unknown')
        self.assertEqual(resumed.committed(state), Decimal('6.50'))
        receipt = {'operation_id': 'timed-out', 'cost_usd': '.04',
                   'all_requests_accounted': True, 'reference': 'synthetic final receipt'}
        for finished in [None, False, 1]:
            with self.assertRaises(budget_module.BudgetError):
                resumed.finish('timed-out', {**receipt, 'operation_finished': finished})
            self.assertEqual(resumed._read(), state)
        resumed.finish('timed-out', {**receipt, 'operation_finished': True})
        resumed.reserve('next', '6.50', kind='chat')
        self.assertEqual(resumed.committed(resumed._read()), Decimal('6.54'))

    def test_no_parallel_index_chat_or_duplicate_operation_and_receipt_must_cover_all_requests(self):
        self.ledger.reserve('a', '6.50', kind='chat')
        with self.assertRaises(budget_module.BudgetError): self.ledger.reserve('index', '.01', kind='index')
        with self.assertRaises(budget_module.BudgetError): self.ledger.reserve('a', '6.50', kind='chat')
        with self.assertRaises(budget_module.BudgetError): self.ledger.finish('a', {'cost_usd': '.01'})
        self.ledger.finish('a')
        self.ledger.finish('a', {'operation_id': 'a', 'cost_usd': '.03', 'all_requests_accounted': True,
                               'operation_finished': True, 'reference': 'receipt'})
        with self.assertRaises(budget_module.BudgetError): self.ledger.finish('a')
        self.assertEqual(self.ledger.committed(self.ledger._read()), Decimal('.03'))

    def test_real_cost_overrun_is_preserved_and_blocks_further_calls(self):
        self.ledger.reserve('a', '6.50', kind='chat')
        with self.assertRaises(budget_module.BudgetError):
            self.ledger.finish('a', {'operation_id': 'a', 'cost_usd': '21', 'all_requests_accounted': True,
                                   'operation_finished': True, 'reference': 'adverse receipt'})
        self.assertEqual(self.ledger.committed(self.ledger._read()), Decimal('21'))
        with self.assertRaises(budget_module.BudgetError): self.ledger.reserve('b', '6.50', kind='chat')


class HybridMetricsCompatibilityTests(unittest.TestCase):
    def test_only_explicit_lexical_admission_can_exceed_dense_threshold_and_rubrics_stay_identical(self):
        from test_assistant_metrics import base_results, passing, metrics, BANK, LABELS, CATALOGUE
        result = base_results()
        case = passing(result, 'JUP-069-006')
        case['retrieved'] = [{'chunk_id': 'synthetic', 'source': 'rules', 'heading': '', 'distance': 1., 'admission': 'lexical'}]
        result['run']['retrieval'].update(mode='hybrid', chunking_unit='tokens', preparation='contextual_embedding_v1', space_id='a'*64,
                                          chunk_size=600, chunk_overlap=60)
        metrics.validate_results(result, BANK, LABELS, CATALOGUE)
        for admission in ['dense', 'both']:
            case['retrieved'][0]['admission'] = admission
            with self.assertRaises(metrics.ResultsError): metrics.validate_results(result, BANK, LABELS, CATALOGUE)
        case['retrieved'][0]['admission'] = 'lexical'
        result['run']['retrieval']['mode'] = 'dense'
        with self.assertRaises(metrics.ResultsError): metrics.validate_results(result, BANK, LABELS, CATALOGUE)


if __name__ == '__main__': unittest.main()
