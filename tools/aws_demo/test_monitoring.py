import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from tools.aws_demo import bootstrap, control, runner
from tools.aws_demo.test_bootstrap import inputs, Secrets
from tools.aws_demo.test_control import config
from tools.aws_demo.test_private_tasks import fixture


class MonitoringControlTests(unittest.TestCase):
    def test_acceptance_rejects_open_access_broken_sources_and_changed_history(self):
        from tools.aws_demo.monitoring_checks import check_monitoring
        manifest = {'entries': [{'run_id': 'known', 'report_sha256': 'a'*64, 'results': 20}]}
        for failure in (None, 'anonymous', 'datasource', 'identity', 'dashboard'):
            def exchange(method, path, body, headers):
                if path.endswith('/search'):
                    return (200 if failure == 'anonymous' else 401), {}
                if path.endswith('/api/health'):
                    return 200, {'database': 'ok'}
                if '/dashboards/' in path:
                    return 200, {'dashboard': {'uid': 'wrong' if failure == 'dashboard' else 'expected', 'panels': [1]}}
                if '/datasources/' in path:
                    return 200, {'status': 'ERROR' if failure == 'datasource' else 'OK'}
                return 200, {'results': {'A': {'frames': [{'data': {'values': [['known'], ['b'*64 if failure == 'identity' else 'a'*64], [20]]}}]}}}
            with self.subTest(failure=failure):
                if failure:
                    with self.assertRaises(ValueError):
                        check_monitoring(exchange, 'localhost', 'synthetic', manifest, ['expected'])
                else:
                    self.assertEqual(check_monitoring(exchange, 'localhost', 'synthetic', manifest, ['expected'])['anonymous_access'], 'denied')

    def test_project_cap_is_thirty_even_when_remaining_funds_are_higher(self):
        for amount in (30.01, 60):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                control.validate_config(dict(config(), budget_eur=amount, available_credit_eur=60), 'a' * 40)
        control.validate_config(dict(config(), budget_eur=30, available_credit_eur=29, estimated_cycle_eur=9), 'a' * 40)
        with self.assertRaises(ValueError):
            control.validate_config(dict(config(), budget_eur=30, available_credit_eur=8, estimated_cycle_eur=9), 'a' * 40)

    def test_monitoring_secrets_are_distinct_and_retries_preserve_them(self):
        conf, output = inputs()
        output['runtime_secret_arns']['grafana'] = output['runtime_secret_arns']['backend'].replace('/backend/', '/grafana/')
        client = Secrets()
        bootstrap.ensure_runtime_secrets(client, conf, output)
        secret = json.loads(client.values[output['runtime_secret_arns']['grafana']])
        keys = ['GF_DATABASE_PASSWORD', 'GF_SECURITY_ADMIN_PASSWORD', 'GF_SECURITY_SECRET_KEY', 'GRAFANA_EVALUATION_DB_PASSWORD']
        self.assertEqual(len({secret[k] for k in keys}), 4)
        before = copy.deepcopy(client.values)
        bootstrap.ensure_runtime_secrets(client, conf, output)
        self.assertEqual(client.values, before)

    def test_private_monitoring_phase_uses_backend_image_and_no_secret_values(self):
        task, _, _ = fixture()
        definition = task.definition('backend', 'monitoring', {})
        self.assertEqual(definition['containerDefinitions'][0]['command'], ['python', '-m', 'app.aws_bootstrap', 'monitoring'])
        self.assertEqual(definition['taskRoleArn'], task.outputs['bootstrap_network']['bootstrap_role_arn'])

    def test_monitoring_images_share_only_the_owned_repository(self):
        self.assertEqual(runner.IMAGES['grafana']['repository'], 'grafana')
        self.assertEqual(runner.IMAGES['prometheus']['repository'], 'grafana')
        self.assertEqual(len(runner.IMAGES), 5)

    def test_monitoring_release_and_cleanup_are_explicitly_allowed(self):
        changes = [{'address': f'{kind}.monitoring[0]', 'change': {'actions': ['create']}}
                   for kind in ('aws_ecs_task_definition', 'aws_ecs_service')]
        control.check_applications_plan({'resource_changes': changes})
        with self.assertRaises(ValueError):
            control.check_applications_plan({'resource_changes': [{'address': 'aws_iam_role.monitoring', 'change': {'actions': ['create']}}]})
        state = {'values': {'root_module': {'resources': [{'address': 'aws_ecr_repository.application["grafana"]', 'values': {'name': 'economicon-ensayo1/grafana'}}]}}}
        self.assertEqual(control.cleanup_inventory(state)['repositories'], ['economicon-ensayo1/grafana'])


if __name__ == '__main__':
    unittest.main()
