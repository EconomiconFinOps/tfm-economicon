import json
import hashlib
import io
import os
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import unittest

from tools.aws_demo import bootstrap


class MissingVersion(Exception):
    response = {'Error': {'Code': 'ResourceNotFoundException'}}


class Secrets:
    def __init__(self):
        self.values = {}
        self.writes = []
    def describe_secret(self, SecretId):
        return {'ARN': SecretId, 'Tags': [{'Key': 'Project', 'Value': 'economicon'}, {'Key': 'Environment', 'Value': 'ensayo1'}]}
    def get_secret_value(self, SecretId):
        if SecretId not in self.values: raise MissingVersion()
        return {'SecretString': self.values[SecretId]}
    def put_secret_value(self, **request):
        self.values[request['SecretId']] = request['SecretString']
        self.writes.append(request)
        return {'ARN': request['SecretId']}


def inputs():
    prefix = 'arn:aws:secretsmanager:eu-west-1:123456789012:secret:economicon-ensayo1/'
    outputs = {'runtime_secret_arns': {key: prefix + key + '/runtime-ABC123' for key in ['backend', 'processor', 'azure-cost-api', 'grafana']},
               'rehearsal_secret_arn': prefix + 'rehearsal/credentials-ABC123',
               'database_endpoints': {key: {'host': f'economicon-ensayo1-{key}.synthetic.eu-west-1.rds.amazonaws.com', 'port': 5432, 'database': database}
                    for key, database in [('operational', 'economicon'), ('vectors', 'embeddings')]},
               'rabbitmq_endpoints': ['amqps://b-01234567.mq.eu-west-1.amazonaws.com:5671']}
    return {'account_id': '123456789012', 'cycle_id': 'ensayo1', 'source_sha': 'a' * 40}, outputs


class BootstrapTests(unittest.TestCase):
    def test_guarded_controller_sequences_private_tasks_and_records_failure(self):
        from tools.aws_demo.test_control import config as valid_config
        from tools.aws_demo.test_private_tasks import fixture, PREFIX
        for fail_broker in (False, True):
            with self.subTest(fail_broker=fail_broker), tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                config = valid_config()
                config['expires_at'] = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                item, ecs, _ = fixture()
                _, outputs = inputs()
                outputs.update(item.outputs)
                outputs.update(database_admin_secret_arns={key: 'arn:aws:secretsmanager:eu-west-1:123456789012:secret:rds!db-synthetic-' + key for key in ['operational', 'vectors']},
                    mq_admin_secret_arn='arn:aws:secretsmanager:eu-west-3:123456789012:secret:synthetic-mq-ABC123',
                    rabbitmq_console_url='https://b-01234567.mq.eu-west-1.amazonaws.com',
                    cognito={'user_pool_id': 'eu-west-1_Synthetic131'})
                outputs['ecr_repositories']['processor'] = outputs['ecr_repositories']['backend'].replace('/backend', '/processor')
                network = outputs['bootstrap_network']
                network['execution_roles']['processor'] = network['execution_roles']['backend'].replace('-backend-', '-processor-')
                network['log_groups']['processor'] = network['log_groups']['backend'].replace('/backend', '/processor')
                images = {key: value + '@sha256:' + 'b' * 64 for key, value in outputs['ecr_repositories'].items()}
                raw = json.dumps(config).encode()
                (work / 'config.json').write_bytes(raw)
                (work / 'outputs.json').write_text(json.dumps(outputs))
                (work / 'images.json').write_text(json.dumps(images))
                current = {}
                def register(**request):
                    current.update(component=request['containerDefinitions'][0]['name'], family=request['family'])
                    return {'taskDefinition': {'taskDefinitionArn': PREFIX + 'task-definition/' + request['family'] + ':1'}}
                ecs.register_task_definition.side_effect = register
                task_arn = PREFIX + 'task/economicon-ensayo1/' + '1' * 32
                ecs.run_task.return_value = {'tasks': [{'taskArn': task_arn}]}
                ecs.describe_tasks.side_effect = lambda **kwargs: {'tasks': [{'taskArn': task_arn, 'lastStatus': 'STOPPED',
                    'containers': [{'name': current['component'], 'exitCode': 1 if fail_broker and current['family'].endswith('-broker') else 0}]}]}
                sts, secret_client = Mock(), Secrets()
                sts.get_caller_identity.return_value = {'Account': config['account_id'], 'Arn':
                    'arn:aws:sts::123456789012:assumed-role/economicon-defensa-deploy/test'}
                clients = {'sts': sts, 'ecs': ecs, 'secretsmanager': secret_client}
                env = {'CODEBUILD_BUILD_ID': 'synthetic:131', 'DEMO_CONFIG': str(work / 'config.json'),
                       'DEMO_OUTPUTS': str(work / 'outputs.json'), 'DEMO_IMAGES': str(work / 'images.json'),
                       'SOURCE_SHA': config['source_sha'], 'CONFIG_KEY': 'configs/' + hashlib.sha256(raw).hexdigest() + '.json',
                       'DEPLOY_ROLE_ARN': 'arn:aws:iam::123456789012:role/economicon-defensa-deploy'}
                output, errors = io.StringIO(), io.StringIO()
                with patch.dict(os.environ, env, clear=True), patch.object(bootstrap, 'WORK', work), \
                     patch.object(bootstrap, 'sdk_client', side_effect=lambda name, region: clients[name]), \
                     redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(bootstrap.main(), 1 if fail_broker else 0)
                phases = [call.kwargs['family'].rsplit('-', 1)[-1] for call in ecs.register_task_definition.call_args_list]
                self.assertEqual(phases, ['database', 'database', 'broker'] + ([] if fail_broker else ['fixtures', 'fixtures', 'monitoring']))
                manifest = json.loads((work / 'bootstrap-tasks.json').read_text())
                self.assertEqual(manifest['events'][-1]['status'], 'FAILED' if fail_broker else 'SUCCEEDED')
                self.assertEqual(ecs.deregister_task_definition.call_count, len(phases))
                self.assertNotIn('Ec1!', output.getvalue() + errors.getvalue() + json.dumps(manifest))
                if not fail_broker:
                    self.assertFalse(json.loads(output.getvalue())['application_ready'])

    def test_invalid_database_snapshot_does_not_write_credentials(self):
        config, outputs = inputs()
        outputs['database_endpoints']['vectors']['host'] = 'credential-sink.invalid'
        client = Secrets()
        with self.assertRaises(RuntimeError):
            bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertEqual(len(client.writes), 0)

    def test_seed_bundle_makes_partial_retries_reuse_all_credentials(self):
        config, outputs = inputs()
        client = Secrets()
        bundle = bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertEqual(len(client.writes), 5)
        again = bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertEqual(bundle, again)
        self.assertEqual(len(client.writes), 5)
        backend = json.loads(client.values[outputs['runtime_secret_arns']['backend']])
        processor = json.loads(client.values[outputs['runtime_secret_arns']['processor']])
        self.assertEqual(backend['CHAT_HMAC_KEY'], processor['CHAT_HMAC_KEY'])
        self.assertIn('sslmode=verify-full', backend['DATABASE_URL'])
        self.assertNotEqual(backend['DATABASE_URL'], processor['DATABASE_URL'])
        del client.values[outputs['runtime_secret_arns']['processor']]
        bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertEqual(json.loads(client.values[outputs['runtime_secret_arns']['processor']]), processor)

    def test_existing_foreign_metadata_or_mismatching_values_are_not_overwritten(self):
        config, outputs = inputs()
        client = Secrets()
        bootstrap.ensure_runtime_secrets(client, config, outputs)
        client.values[outputs['runtime_secret_arns']['backend']] = '{"unexpected":"private-value"}'
        previous = len(client.writes)
        with self.assertRaises(RuntimeError):
            bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertEqual(len(client.writes), previous)
        client = Secrets()
        client.describe_secret = Mock(return_value={'ARN': outputs['rehearsal_secret_arn'], 'Tags': []})
        with self.assertRaises(RuntimeError):
            bootstrap.ensure_runtime_secrets(client, config, outputs)
        self.assertFalse(client.writes)

    def test_local_main_never_constructs_sdk_clients(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(bootstrap, 'sdk_client', side_effect=AssertionError('AWS forbidden')) as sdk:
            self.assertEqual(bootstrap.main(), 1)
            sdk.assert_not_called()
