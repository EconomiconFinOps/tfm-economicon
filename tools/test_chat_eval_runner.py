from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('runner', Path(__file__).with_name('chat-eval-runner.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
ledger_module = r.module('chat-eval-ledger')


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = ledger_module.Ledger(Path(self.temp.name) / 'spend.sqlite')
        bank = json.loads(r.planning.BANK.read_text(encoding='utf-8'))
        self.plan = {'bank_sha256': r.planning.EXPECTED_BANK, 'repetitions': 3,
                     'samples': r.planning.campaign(bank, 3), 'commit': 'synthetic-candidate',
                     'file_hashes': {'synthetic': 'hash'}, 'provider_constraint': {'model': 'synthetic'}}
        self.verified = {'commit': self.plan['commit'], 'file_hashes': self.plan['file_hashes'],
                         'provider_constraint': self.plan['provider_constraint'], 'screen_context': {},
                         'operation_bound': Decimal('0.1'),
                         'accounting': {'observed_at': 100, 'cumulative_usd': '1',
                                        'scope': 'jup035-cumulative-all-providers', 'evidence_sha256': 'synthetic'}}
        self.api = FakeAPI()

    def runner(self):
        return r.Runner(self.plan, self.api, self.ledger, Path(self.temp.name) / 'receipts',
                        lambda plan: self.verified, clock=lambda: 100)

    def test_start_then_restart_observes_and_collects_same_operation(self):
        self.assertEqual(self.runner().step()['state'], 'OBSERVING')
        self.assertEqual(self.runner().step()['state'], 'COLLECTED_ONE')
        self.assertEqual(self.api.posts, 1)
        receipts = list((Path(self.temp.name) / 'receipts').glob('*.json'))
        row = json.loads(receipts[0].read_text())['results'][0]
        self.assertEqual(row['state'], 'failed')
        self.assertEqual(row['repetition'], 1)
        self.assertEqual(self.runner().step()['state'], 'NEEDS_ACCOUNTING')
        self.assertEqual(self.api.posts, 1)

    def test_verified_failed_sample_advances_without_retry_or_releasing_bound(self):
        self.runner().step(); self.runner().step()
        path = next((Path(self.temp.name) / 'receipts').glob('*.json'))
        receipt = json.loads(path.read_text(encoding='utf-8')); saved = receipt['results'][0]
        saved['verification']['input_matches_bank'] = True
        saved['collection_state'] = 'VERIFIED_PUBLIC_SNAPSHOT'
        saved['durable_input_supplement'] = {'state': 'failed'}
        path.write_text(json.dumps(receipt), encoding='utf-8')
        self.ledger.retain_failed_cost(self.ledger.pending()[0]['request_id'], saved)
        self.assertEqual(saved['resources_sha256'], r.collect.digest(saved['resources']))
        self.assertEqual(self.runner().step()['state'], 'OBSERVING')
        self.assertEqual(self.api.posts, 2)
        self.assertEqual(json.loads(self.ledger.pending()[0]['reservation'])['reserved_usd'], '0.1')
        self.assertEqual(len(self.ledger.pending()), 2)

    def test_lost_response_recovers_handle_without_new_post(self):
        self.api.lose_response = True
        with self.assertRaises(TimeoutError):
            self.runner().step()
        self.assertEqual(self.runner().step()['state'], 'COLLECTED_ONE')
        self.assertEqual(self.api.posts, 1)

    def test_runtime_mismatch_blocks_before_conversation_or_reservation(self):
        self.verified['commit'] = 'other'
        with self.assertRaisesRegex(ValueError, 'Runtime'):
            self.runner().step()
        self.assertEqual(self.ledger.pending(), [])
        self.assertEqual(self.api.created, 0)

    def test_active_operation_is_not_restarted(self):
        self.runner().step()
        self.api.state = 'waiting'
        result = self.runner().step()
        self.assertEqual(result['operation_state'], 'waiting')
        self.assertEqual(self.api.posts, 1)

    def test_generated_runtime_proof_is_required_before_reserving_or_posting(self):
        runtime=r.module('chat-eval-runtime')
        self.plan['file_hashes'][runtime.TOKENIZER_BUILDER]='builder'
        pins={runtime.TOKENIZER:{'sha256':'a'*64,'revision':'b'*40,'bytes':17}}
        self.plan['generated_artifacts']=pins
        with self.assertRaisesRegex(ValueError,'Runtime'):
            self.runner().step()
        self.assertEqual(self.ledger.pending(),[])
        self.assertEqual(self.api.created,0)
        self.verified['generated_artifacts']=pins
        self.assertEqual(self.runner().step()['state'],'OBSERVING')
        self.assertEqual(self.api.posts,1)


class FakeAPI:
    def __init__(self):
        self.posts = self.created = 0
        self.state = 'failed'
        self.lose_response = False
    def create_conversation(self, title):
        self.created += 1
        return 'conversation'
    def generate(self, cid, rid, content, screen):
        self.posts += 1
        self.content, self.request_id = content, rid
        if self.lose_response:
            raise TimeoutError('synthetic lost response')
        return 'operation'
    def recover_handle(self, cid, rid):
        return 'operation' if rid == self.request_id else None
    def get(self, path):
        if path.endswith('/context'):
            return {'manifest': {}}
        if path.endswith('/evidence'):
            return {'items': []}
        if path.endswith('/conversation'):
            return {'messages': [{'id': 'question', 'role': 'user', 'content': self.content}]}
        return {'operation_id': 'operation', 'request_id': self.request_id,
                'question_id': 'question', 'state': self.state}


if __name__ == '__main__':
    unittest.main()
