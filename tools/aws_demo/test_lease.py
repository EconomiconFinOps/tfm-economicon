"""Lease expression contract: reserved names and conditional ownership guards."""
from contextlib import nullcontext
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import runner
from control import bind_plan, lock_key
from test_control import config


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.item = object.__new__(runner.Runner)
        self.item.config = config()
        self.item.config_key = 'configs/synthetic.json'
        self.item.table = 'synthetic-lease'
        self.record = {
            'domain': {'S': lock_key(self.item.config)},
            'cycle': {'S': self.item.config['cycle_id']},
            'sha': {'S': self.item.config['source_sha']},
            'config_key': {'S': self.item.config_key},
            'phase': {'S': 'PLANNED'},
        }
        self.after_read = None
        self.writes = []
        self.item.aws = self.aws

    def aws(self, service, operation, *args, payload=None, **kwargs):
        if service == 'scheduler':
            self.assertEqual(operation, 'delete-schedule')
            return {}
        self.assertEqual(service, 'dynamodb')
        self.assertEqual(payload['TableName'], self.item.table)
        self.assertEqual(payload['Key'], {'domain': {'S': lock_key(self.item.config)}})
        if operation == 'get-item':
            snapshot = copy.deepcopy(self.record)
            if self.after_read:
                self.record.update(self.after_read)
            return {'Item': snapshot}
        self.assertIn(operation, ('update-item', 'delete-item'))
        expression = payload['ConditionExpression']
        # DynamoDB rejects CYCLE when used as a bare attribute in an expression.
        # Any valid alias spelling is accepted; placeholders are not identifiers.
        bare_names = re.findall(r'(?<![\w#:\u00c0-\uffff])\b[A-Za-z_]\w*\b', expression)
        self.assertNotIn('cycle', [name.lower() for name in bare_names],
                         'DynamoDB rejects the reserved attribute cycle without an alias')
        names = payload.get('ExpressionAttributeNames', {})
        values = payload['ExpressionAttributeValues']
        conditions = {}
        for term in expression.split(' AND '):
            match = re.fullmatch(r'([#\w]+) = (:\w+)', term)
            self.assertIsNotNone(match)
            attribute, placeholder = match.groups()
            attribute = names[attribute] if attribute.startswith('#') else attribute
            conditions[attribute] = values[placeholder]
        self.assertEqual(set(conditions), {'cycle', 'sha', 'config_key', 'phase'})
        if any(self.record.get(name) != value for name, value in conditions.items()):
            raise RuntimeError('ConditionalCheckFailedException')
        self.writes.append(operation)
        if operation == 'delete-item':
            self.record = None
        else:
            match = re.fullmatch(r'SET ([#\w]+) = (:\w+)', payload['UpdateExpression'])
            self.assertIsNotNone(match)
            name, placeholder = match.groups()
            name = names[name] if name.startswith('#') else name
            self.record[name] = values[placeholder]
        return {}

    def test_all_lifecycle_transitions_accept_reserved_attribute_alias(self):
        for phase in ('APPLYING', 'INFRA_READY', 'RELEASING', 'READY', 'TEARDOWN'):
            with self.subTest(phase=phase):
                expected = self.record['phase']['S']
                self.item.lease(phase, expected=expected)
                self.assertEqual(self.record['phase']['S'], phase)

    def test_ownership_and_phase_changes_between_read_and_update_are_rejected(self):
        for attribute in ('cycle', 'sha', 'config_key', 'phase'):
            with self.subTest(attribute=attribute):
                self.setUp()
                self.after_read = {attribute: {'S': 'concurrent-change'}}
                with self.assertRaisesRegex(RuntimeError, 'ConditionalCheckFailedException'):
                    self.item.lease('APPLYING', expected='PLANNED')
                self.assertEqual(self.writes, [])
                self.assertEqual(self.record[attribute], {'S': 'concurrent-change'})

    def test_stale_expected_phase_is_rejected_before_write(self):
        self.record['phase'] = {'S': 'TEARDOWN'}
        with self.assertRaisesRegex(ValueError, 'stale writer rejected'):
            self.item.lease('APPLYING', expected='PLANNED')
        self.assertEqual(self.writes, [])

    def test_empty_destroy_releases_only_the_matching_teardown_lease(self):
        self.record['phase'] = {'S': 'TEARDOWN'}
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'WORK', Path(directory)):
            work = Path(directory)
            saved = work / 'destroy.tfplan'
            saved.write_bytes(b'synthetic empty destroy plan')
            (work / 'destroy.binding.json').write_text(json.dumps(bind_plan(saved, self.item.config, 'destroy')))
            self.item.init = lambda: None
            self.item.download = lambda name: work / name
            self.item.tf = lambda *args: '{}'
            self.item.resource_credentials = nullcontext
            self.item.apply_saved = lambda name: self.assertEqual(name, 'destroy')
            self.item.upload = lambda name: None
            self.item.inspect_residuals = lambda: {'active': [], 'pending_deletion': [], 'retired_metadata': []}
            self.item.destroy()
            self.assertIsNone(self.record)
            self.assertEqual(self.writes, ['delete-item'])


if __name__ == '__main__':
    unittest.main()
