"""PR146 regression cases. No AWS calls or credentials are needed."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runner
import control
import prepare
from test_control import config
from tools.aws_demo.private_tasks import _public, PrivateTaskError


def recipe():
    return json.loads((Path(__file__).parents[2] / 'infra/aws-cicd/release.json').read_text())


class ReviewFixTests(unittest.TestCase):
    def test_applications_guard_runs_before_upload_and_before_apply(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        bad = {'resource_changes': [{'address': 'aws_db_instance.main["vectors"]',
                                    'change': {'actions': ['delete', 'create']}}]}
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'WORK', Path(directory)):
            calls, uploads = [], []
            def tf(*args):
                calls.append(args)
                if args[0] == 'show':
                    return json.dumps(bad)
                (Path(directory) / 'applications.tfplan').write_bytes(b'synthetic')
                return ''
            item.tf, item.upload = tf, uploads.append
            with self.assertRaises(ValueError):
                item.make_plan('applications')
            self.assertEqual(uploads, [])
            path = Path(directory) / 'applications.tfplan'
            binding = Path(directory) / 'applications.binding.json'
            binding.write_text(json.dumps(control.bind_plan(path, item.config, 'applications')))
            item.download = lambda name: Path(directory) / name
            with self.assertRaises(ValueError):
                item.apply_saved('applications')
            self.assertFalse(any(args[0] == 'apply' for args in calls))

    def test_docker_build_receives_public_environment_at_actual_callsite(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        item.upload = lambda name: None
        calls = []
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'WORK', Path(directory)), \
                patch.object(runner, 'source_files', return_value=[]), \
                patch.object(runner, 'run', side_effect=lambda args, env: calls.append((args, env))), \
                patch.dict(os.environ, GITHUB_TOKEN='sensitive', MQ_ADMIN_PASSWORD='sensitive',
                           AWS_CONTAINER_CREDENTIALS_RELATIVE_URI='/sensitive'):
            item.build()
        self.assertEqual(len(calls), 6)
        for _, env in calls:
            self.assertNotIn('GITHUB_TOKEN', env)
            self.assertNotIn('MQ_ADMIN_PASSWORD', env)
            self.assertNotIn('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI', env)

    def test_invalid_recipe_path_preparation_stays_blocked_without_exception(self):
        for changes in ({'release_recipe': None}, {'cycle_id': 5}):
            with tempfile.TemporaryDirectory() as directory:
                result = prepare.prepare(dict(config(), **changes), directory, 'a' * 40)
                self.assertFalse(result['aws_deployable'])

    def test_approval_receipt_exposes_plan_hash_class_and_binding_location(self):
        item = object.__new__(runner.Runner)
        item.config, item.bucket, item.prefix = config(), 'control', 'cycles/synthetic'
        item.upload = lambda name: None
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'WORK', Path(directory)):
            def tf(*args):
                (Path(directory) / 'infra.tfplan').write_bytes(b'synthetic')
                return ''
            item.tf = tf
            item.make_plan('infra')
            receipt = json.loads((Path(directory) / 'approval.json').read_text())
            self.assertEqual(receipt['plan_kind'], 'infra')
            self.assertEqual(receipt['sha256'], control.bind_plan(Path(directory) / 'infra.tfplan', item.config)['sha256'])
            self.assertEqual(receipt['binding_uri'], 's3://control/cycles/synthetic/infra.binding.json')

    def test_applications_plan_rejects_database_drift_replacements_and_foreign_policies(self):
        def plan(address, actions):
            return {'resource_changes': [{'address': address, 'change': {'actions': actions}}]}
        control.check_applications_plan(plan('aws_ecs_service.application["backend"]', ['create']))
        control.check_applications_plan(plan('aws_iam_role_policy.bedrock_chat[0]', ['update']))
        for address, actions in [
            ('aws_db_instance.main["operational"]', ['delete', 'create']),
            ('aws_db_instance.main["vectors"]', ['update']),
            ('aws_mq_broker.main', ['delete']), ('aws_cognito_user_pool.main', ['update']),
            ('aws_ecs_service.application["backend"]', ['delete', 'create']),
            ('aws_iam_role_policy.foreign', ['create']),
            ('module.other.aws_ecs_service.application["backend"]', ['create']),
        ]:
            with self.subTest(address=address), self.assertRaises(ValueError):
                control.check_applications_plan(plan(address, actions))

    def test_saved_plan_cannot_be_relabelled_as_another_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.tfplan'
            path.write_bytes(b'synthetic')
            binding = control.bind_plan(path, config(), 'infra')
            with self.assertRaises(ValueError):
                control.verify_binding(path, binding, config(), 'applications')

    def test_source_requires_develop_push_ci_and_current_ancestry(self):
        ci = dict(head_sha='a' * 40, conclusion='success', status='completed', event='push',
                  head_branch='develop', path='.github/workflows/ci.yml',
                  repository={'full_name': 'EconomiconFinOps/tfm-economicon'})
        comparison = {'status': 'ahead', 'merge_base_commit': {'sha': 'a' * 40}}
        control.check_reviewed_source(ci, comparison, 'a' * 40)
        for changes in ({'event': 'workflow_dispatch'}, {'event': 'pull_request'},
                        {'head_branch': 'feat/unreviewed'}, {'head_sha': 'b' * 40},
                        {'repository': {'full_name': 'foreign/fork'}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                control.check_reviewed_source(dict(ci, **changes), comparison, 'a' * 40)
        for comparison in ({'status': 'diverged'}, {'status': 'behind'},
                           {'status': 'ahead', 'merge_base_commit': {'sha': 'b' * 40}}):
            with self.assertRaises(ValueError):
                control.check_reviewed_source(ci, comparison, 'a' * 40)

    def test_lease_update_has_atomic_expected_phase_and_config(self):
        item = object.__new__(runner.Runner)
        item.config, item.config_key, item.table = config(), 'configs/pinned.json', 'leases'
        calls = []
        current = {'cycle': {'S': 'ensayo1'}, 'sha': {'S': 'a' * 40},
                   'config_key': {'S': item.config_key}, 'phase': {'S': 'PLANNED'}}
        def aws(*args, payload):
            if args[1] == 'get-item':
                return {'Item': copy.deepcopy(current)}
            calls.append(payload)
            # A teardown wins after the read, before the writer's update.
            current['phase'] = {'S': 'TEARDOWN'}
            if 'phase = :expected' in payload['ConditionExpression']:
                raise RuntimeError('ConditionalCheckFailedException')
        item.aws = aws
        with self.assertRaises(RuntimeError):
            item.lease('APPLYING', expected='PLANNED')
        self.assertIn('config_key = :config', calls[0]['ConditionExpression'])
        self.assertEqual(calls[0]['ExpressionAttributeValues'][':expected'], {'S': 'PLANNED'})
        with self.assertRaises(ValueError):
            item.lease('APPLYING', expected='PLANNED')

    def test_build_test_environment_drops_all_credential_sources(self):
        unsafe = dict(PATH='/usr/bin', HOME='/root', GITHUB_TOKEN='synthetic',
                      MQ_ADMIN_PASSWORD='synthetic', AWS_ACCESS_KEY_ID='synthetic',
                      AWS_SECRET_ACCESS_KEY='synthetic', AWS_SESSION_TOKEN='synthetic',
                      AWS_CONTAINER_CREDENTIALS_RELATIVE_URI='/secret',
                      AWS_CONTAINER_CREDENTIALS_FULL_URI='http://localhost/secret',
                      AWS_CONTAINER_AUTHORIZATION_TOKEN='synthetic',
                      AWS_WEB_IDENTITY_TOKEN_FILE='/secret', AWS_PROFILE='admin',
                      NODE_OPTIONS='--require=/secret', PYTHONPATH='/secret',
                      DOCKER_CONFIG='/root/.docker', NPM_TOKEN='synthetic')
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, unsafe, clear=True), \
                patch.object(runner, 'WORK', Path(directory)):
            env = runner.public_process_env()
            for key in unsafe.keys() - {'PATH', 'HOME'}:
                self.assertNotIn(key, env)
            self.assertNotEqual(env['HOME'], unsafe['HOME'])
            self.assertEqual(env['AWS_EC2_METADATA_DISABLED'], 'true')
            self.assertEqual(Path(env['AWS_SHARED_CREDENTIALS_FILE']).read_bytes(), b'')

    def test_public_values_reject_nested_dsn_keys_and_private_keys(self):
        for value in ('postgresql://u:p@host/database', 'amqps://u:p@host/vhost',
                      'AKIA' + 'A' * 16, 'ASIA' + 'B' * 16,
                      '-----BEGIN RSA PRIVATE KEY-----', 'Bearer synthetic-credential'):
            with self.subTest(value=value), self.assertRaises(PrivateTaskError):
                _public({'nested': [{'DSN': value}]})
            v = recipe()
            v['application_environment']['backend']['DSN'] = value
            with self.assertRaises(ValueError):
                control.validate_recipe(v)
        _public({'resource': 'arn:aws:s3:::synthetic', 'path': '/opt/economicon/chat/v4'})

    def test_recipe_requires_native_consistent_provider_contract(self):
        for app, key, value in [('backend', 'EMBEDDING_PROVIDER', 'mock'),
                ('processor', 'LLM_PROVIDER', None), ('processor', 'BEDROCK_CHAT_MODEL_ID', 'other'),
                ('backend', 'BEDROCK_REGION', 'eu-west-3'),
                ('processor', 'EMBEDDING_DIMENSION', '1536')]:
            v = recipe()
            if value is None:
                del v['application_environment'][app][key]
            else:
                v['application_environment'][app][key] = value
            with self.subTest(app=app, key=key), self.assertRaises(ValueError):
                control.validate_recipe(v)
        for field in ('bedrock_model_arns', 'bedrock_chat_profile_id', 'application_environment'):
            v = recipe()
            del v[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                control.validate_recipe(v)

    def test_wrong_configuration_types_and_unicode_digits_are_value_errors(self):
        for key, value in [('cycle_id', 5), ('release_recipe', None), ('availability_zones', None),
                           ('ci_run_id', '١٢٣'), ('postgres_version', '١٦.٩')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                control.validate_config(dict(config(), **{key: value}), 'a' * 40)
