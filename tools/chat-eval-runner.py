"""One recoverable campaign step; runtime/accounting adapters are explicit inputs.

No CLI for paid execution is exposed until the verified deployment/accounting
adapter exists. step() never renews keys, resumes an operation or retries a POST.
"""
import importlib.util
import json
from pathlib import Path
import time


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


collect = module('chat-eval-collect')
planning = module('chat-eval-plan')


def validate_plan(plan):
    module('chat-eval-runtime').generated_hashes(plan)
    bank = json.loads(planning.BANK.read_text(encoding='utf-8'))
    if (planning.sha(planning.BANK) != planning.EXPECTED_BANK
            or plan.get('bank_sha256') != planning.EXPECTED_BANK
            or plan.get('samples') != planning.campaign(bank, plan['repetitions'])):
        raise ValueError('Campaign must match the full immutable bank and repetitions')


class Runner:
    def __init__(self, plan, api, ledger, output, preflight, clock=time.time, accounting=None):
        validate_plan(plan)
        self.plan, self.api, self.ledger = plan, api, ledger
        self.plan_hash = collect.digest(plan)
        self.output = Path(output).resolve()
        root = Path(__file__).resolve().parents[1]
        if self.output == root or root in self.output.parents:
            raise ValueError('Receipts must be outside the checkout')
        self.output.mkdir(parents=True, exist_ok=True)
        self.preflight, self.clock = preflight, clock
        self.accounting = accounting

    def step(self):
        """Perform one dispatch OR one observation; caller schedules next step."""
        rows = {r['sample_id']: r for r in self.ledger.pending() if r['plan_hash'] == self.plan_hash}
        for sample in self.plan['samples']:
            path = self.output / (sample['sample_id'].replace(':', '-') + '.json')
            if path.exists():
                receipt = json.loads(path.read_text(encoding='utf-8'))
                if (receipt.get('plan_sha256') != self.plan_hash or len(receipt.get('results', [])) != 1
                        or receipt['results'][0].get('id') != sample['case_id']
                        or receipt['results'][0].get('repetition') != sample['repetition']):
                    raise ValueError('Existing receipt identity mismatch')
                saved = receipt['results'][0]
                if (sample['sample_id'] not in rows
                        or saved.get('resources_sha256') != collect.digest(saved.get('resources'))
                        or saved.get('operation', {}).get('operation_id') != rows[sample['sample_id']]['operation_id']):
                    raise ValueError('Existing receipt lacks matching durable operation evidence')
                if receipt['results'][0].get('collection_state') != 'VERIFIED_PUBLIC_SNAPSHOT':
                    return {'state': 'NEEDS_EVIDENCE_RECONCILIATION', 'sample_id': sample['sample_id']}
                row = rows[sample['sample_id']]
                reservation = json.loads(row['reservation'])
                if reservation['state'] == 'COST_UNKNOWN_RESERVED':
                    module('chat-eval-budget').retained_cost(reservation, row['operation_id'], saved)
                    continue
                if reservation['state'] != 'COST_OBSERVED':
                    if self.accounting is None:
                        return {'state': 'NEEDS_ACCOUNTING', 'operation_id': row['operation_id']}
                    costs = self.accounting(saved['operation'])
                    self.ledger.reconcile_cost(row['request_id'], saved['operation'],
                                               costs['reports'], costs['auxiliary_cost_usd'])
                    return {'state': 'COST_RECONCILED', 'operation_id': row['operation_id']}
                continue
            row = rows.get(sample['sample_id'])
            if row is None:
                # Adapter must freshly read trusted runtime state and provider
                # accounting; booleans in a user-edited file are not verification.
                verified = self.preflight(self.plan)
                if (verified['commit'] != self.plan['commit']
                        or verified['file_hashes'] != self.plan['file_hashes']
                        or verified.get('generated_artifacts', {}) != self.plan.get('generated_artifacts', {})
                        or verified['provider_constraint'] != self.plan['provider_constraint']):
                    raise ValueError('Runtime does not match the frozen plan')
                request_id = self.ledger.reserve(self.plan_hash, sample['sample_id'],
                                                 verified['accounting'], verified['operation_bound'], self.clock())
                conversation = self.api.create_conversation('JUP-123 ' + sample['sample_id'])
                self.ledger.attach_conversation(request_id, conversation)
                if not 0 <= self.clock() - verified['accounting']['observed_at'] <= 30:
                    raise ValueError('Accounting became stale before dispatch; reservation retained')
                operation = self.ledger.dispatch(request_id, lambda cid, rid:
                    self.api.generate(cid, rid, sample['content'], verified['screen_context']))
                return {'state': 'OBSERVING', 'sample_id': sample['sample_id'], 'operation_id': operation}
            request_id, conversation = row['request_id'], row['conversation_id']
            if row['state'] == 'RESERVED':
                # A crash before dispatch still requires explicit reconciliation;
                # do not create another conversation or assume money is free.
                return {'state': 'NEEDS_RESERVATION_RECONCILIATION', 'request_id': request_id}
            operation = row['operation_id'] or self.api.recover_handle(conversation, request_id)
            if not operation:
                return {'state': 'UNKNOWN_DISPATCH', 'request_id': request_id}
            self.ledger.observe_handle(request_id, operation)
            status = self.api.get('/assistant/conversations/' + collect.identifier(conversation)
                                  + '/generations/' + collect.identifier(operation))
            if status.get('state') not in ('completed', 'failed', 'cancelled'):
                return {'state': 'OBSERVING', 'operation_id': operation,
                        'operation_state': status.get('state')}
            result = collect.collect(self.api.get, sample, conversation, operation)
            receipt = {'version': 1, 'plan_sha256': self.plan_hash,
                       'bank_sha256': self.plan['bank_sha256'], 'repetitions': self.plan['repetitions'],
                       'results': [result]}
            with path.open('x', encoding='utf-8') as handle:
                json.dump(receipt, handle, ensure_ascii=False, indent=2)
                handle.write('\n')
            return {'state': 'COLLECTED_ONE', 'sample_id': sample['sample_id'],
                    'collection_state': result['collection_state'], 'receipt': str(path)}
        return {'state': 'COLLECTED', 'acceptance': 'NOT_ASSESSED'}
