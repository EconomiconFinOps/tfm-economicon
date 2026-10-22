import copy
import unittest
from unittest.mock import Mock

from tools.aws_demo.private_tasks import PrivateTasks, PrivateTaskError


ACCOUNT = '123456789012'
PREFIX = 'arn:aws:ecs:eu-west-1:' + ACCOUNT + ':'


def fixture():
    config = {'account_id': ACCOUNT, 'cycle_id': 'ensayo1', 'source_sha': 'a' * 40, 'region': 'eu-west-1'}
    image = ACCOUNT + '.dkr.ecr.eu-west-1.amazonaws.com/economicon-ensayo1/backend@sha256:' + 'b' * 64
    outputs = {'ecs_cluster_name': 'economicon-ensayo1', 'ecr_repositories': {'backend': image.split('@')[0]},
               'bootstrap_network': {'subnets': ['subnet-11111111', 'subnet-22222222', 'subnet-33333333'],
                    'security_group_id': 'sg-11111111',
                    'bootstrap_role_arn': 'arn:aws:iam::' + ACCOUNT + ':role/economicon-ensayo1-bootstrap',
                    'execution_roles': {'backend': 'arn:aws:iam::' + ACCOUNT + ':role/economicon-ensayo1-backend-exec'},
                    'log_groups': {'backend': '/ecs/economicon-ensayo1/backend'}}}
    ecs = Mock()
    definition = PREFIX + 'task-definition/economicon-ensayo1-bootstrap-backend-database:1'
    task = PREFIX + 'task/economicon-ensayo1/0123456789abcdef0123456789abcdef'
    ecs.register_task_definition.return_value = {'taskDefinition': {'taskDefinitionArn': definition}}
    ecs.run_task.return_value = {'tasks': [{'taskArn': task}], 'failures': []}
    ecs.describe_tasks.return_value = {'tasks': [{'taskArn': task, 'lastStatus': 'STOPPED',
                                                'containers': [{'name': 'backend', 'exitCode': 0}]}], 'failures': []}
    events = []
    runner = PrivateTasks(ecs, config, outputs, {'backend': image}, lambda value: events.append(copy.deepcopy(value)))
    return runner, ecs, events


class PrivateTaskTests(unittest.TestCase):
    def test_rds_service_managed_secret_reference_is_public_metadata(self):
        item, ecs, events = fixture()
        item.run('backend', 'database', {'database_admin_secret_arns': {
            'operational': 'arn:aws:secretsmanager:eu-west-1:123456789012:secret:rds!db-synthetic-ABC123'}})
        ecs.run_task.assert_called_once()

    def test_private_immutable_task_waits_for_zero_and_retires_definition(self):
        item, ecs, events = fixture()
        item.run('backend', 'database', {'cycle_id': 'ensayo1'})
        definition = ecs.register_task_definition.call_args.kwargs
        self.assertEqual(definition['networkMode'], 'awsvpc')
        self.assertTrue(definition['containerDefinitions'][0]['readonlyRootFilesystem'])
        self.assertIn('@sha256:', definition['containerDefinitions'][0]['image'])
        self.assertEqual(definition['containerDefinitions'][0]['command'], ['python', '-m', 'app.aws_bootstrap', 'database'])
        network = ecs.run_task.call_args.kwargs['networkConfiguration']['awsvpcConfiguration']
        self.assertEqual(network['assignPublicIp'], 'DISABLED')
        self.assertEqual(network['securityGroups'], ['sg-11111111'])
        ecs.get_waiter.return_value.wait.assert_called_once()
        ecs.deregister_task_definition.assert_called_once()
        self.assertEqual(events[-1]['status'], 'SUCCEEDED')

    def test_nonzero_and_missing_exit_never_count_as_success(self):
        for container in ({'name': 'backend', 'exitCode': 1}, {'name': 'backend'}):
            item, ecs, events = fixture()
            ecs.describe_tasks.return_value['tasks'][0]['containers'] = [container]
            with self.assertRaises(PrivateTaskError):
                item.run('backend', 'database', {})
            ecs.deregister_task_definition.assert_called_once()
            self.assertNotEqual(events[-1]['status'], 'SUCCEEDED')

    def test_timeout_stops_task_then_retires_definition_and_keeps_manifest(self):
        item, ecs, events = fixture()
        ecs.get_waiter.return_value.wait.side_effect = [TimeoutError('synthetic-sensitive-diagnostic'), None]
        with self.assertRaises(PrivateTaskError) as error:
            item.run('backend', 'database', {})
        self.assertNotIn('sensitive', str(error.exception))
        ecs.stop_task.assert_called_once()
        ecs.deregister_task_definition.assert_called_once()
        self.assertEqual(events[-1]['status'], 'FAILED')
        self.assertIn('task_arn', events[-1])

    def test_rejected_launch_still_retires_definition(self):
        item, ecs, events = fixture()
        ecs.run_task.return_value = {'tasks': [], 'failures': [{'reason': 'capacity'}]}
        with self.assertRaises(PrivateTaskError):
            item.run('backend', 'database', {})
        ecs.deregister_task_definition.assert_called_once()
        ecs.stop_task.assert_not_called()

    def test_foreign_response_arns_are_never_cleanup_targets(self):
        item, ecs, events = fixture()
        ecs.register_task_definition.return_value['taskDefinition']['taskDefinitionArn'] = PREFIX + 'task-definition/foreign:1'
        with self.assertRaises(PrivateTaskError):
            item.run('backend', 'database', {})
        ecs.deregister_task_definition.assert_not_called()
        ecs.run_task.assert_not_called()
        item, ecs, events = fixture()
        ecs.run_task.return_value['tasks'][0]['taskArn'] = PREFIX + 'task/foreign/' + 'f' * 32
        with self.assertRaises(PrivateTaskError):
            item.run('backend', 'database', {})
        ecs.stop_task.assert_not_called()
        ecs.deregister_task_definition.assert_called_once()

    def test_unpinned_foreign_images_and_secret_payload_are_rejected_before_aws(self):
        for image in ('foreign/image:latest', 'other@sha256:' + 'b' * 64):
            item, ecs, events = fixture()
            item.images['backend'] = image
            with self.assertRaises(PrivateTaskError):
                item.run('backend', 'database', {})
            ecs.register_task_definition.assert_not_called()
        item, ecs, events = fixture()
        with self.assertRaises(PrivateTaskError):
            item.run('backend', 'database', {'password': 'never-inline'})
        ecs.register_task_definition.assert_not_called()
