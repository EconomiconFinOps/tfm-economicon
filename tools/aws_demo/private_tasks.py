"""Private one-off task lifecycle. SDK clients are supplied by a guarded caller.

Importing this module does not construct clients or contact AWS. The manifest
callback must persist every registered definition and launched task for recovery.
"""
import json
import re
from uuid import uuid4


class PrivateTaskError(RuntimeError):
    pass


def _require(value):
    if not value:
        raise PrivateTaskError('Private bootstrap task configuration or result is invalid.')


def _public(value):
    if isinstance(value, dict):
        for name, child in value.items():
            if name.endswith(('_secret_arn', '_secret_arns')):
                arns = child.values() if isinstance(child, dict) else [child]
                _require(all(isinstance(arn, str) and re.fullmatch(
                    r'arn:aws:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:[A-Za-z0-9!/_+=.@-]+', arn)
                             for arn in arns))
            else:
                _require(not re.search(r'password|secret|token|credential|hmac|access_key', name, re.I))
                _public(child)
    elif isinstance(value, list):
        for child in value:
            _public(child)
    else:
        _require(value is None or type(value) in {str, int, float, bool})


class PrivateTasks:
    def __init__(self, ecs, config, outputs, images, record):
        self.ecs, self.config, self.outputs = ecs, config, outputs
        self.images, self.record = images, record

    def definition(self, component, phase, inputs):
        config = self.config
        _require(component in {'backend', 'processor'} and phase in {'database', 'fixtures', 'reindex', 'broker'})
        _require(config['region'] == 'eu-west-1' and re.fullmatch(r'[0-9]{12}', config['account_id']))
        _require(re.fullmatch(r'(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})', config['cycle_id']))
        _require(re.fullmatch(r'[a-f0-9]{40}', config['source_sha']))
        cluster = 'economicon-' + config['cycle_id']
        _require(self.outputs['ecs_cluster_name'] == cluster)
        repository = f"{config['account_id']}.dkr.ecr.eu-west-1.amazonaws.com/{cluster}/{component}"
        image = self.images[component]
        _require(self.outputs['ecr_repositories'][component] == repository
                 and re.fullmatch(re.escape(repository) + r'@sha256:[a-f0-9]{64}', image))
        network = self.outputs['bootstrap_network']
        role_prefix = f"arn:aws:iam::{config['account_id']}:role/{cluster}"
        _require(network['bootstrap_role_arn'] == role_prefix + '-bootstrap')
        _require(network['execution_roles'][component] == role_prefix + '-' + component + '-exec')
        _require(len(network['subnets']) == 3 and len(set(network['subnets'])) == 3
                 and all(re.fullmatch(r'subnet-(?:[a-f0-9]{8}|[a-f0-9]{17})', subnet) for subnet in network['subnets']))
        _require(re.fullmatch(r'sg-(?:[a-f0-9]{8}|[a-f0-9]{17})', network['security_group_id']))
        _require(network['log_groups'][component] == f'/ecs/{cluster}/{component}')
        _public(inputs)
        payload = json.dumps(inputs, sort_keys=True, separators=(',', ':'), allow_nan=False)
        _require(len(payload.encode('utf-8')) <= 16384)
        tags = [{'key': key, 'value': value} for key, value in {
            'Project': 'economicon', 'Environment': config['cycle_id'], 'Task': 'JUP-131',
            'Purpose': 'bootstrap', 'SourceSha': config['source_sha'],
        }.items()]
        return {
            'family': f'{cluster}-bootstrap-{component}-{phase}', 'requiresCompatibilities': ['FARGATE'],
            'networkMode': 'awsvpc', 'cpu': '512', 'memory': '1024',
            'executionRoleArn': network['execution_roles'][component], 'taskRoleArn': network['bootstrap_role_arn'],
            'runtimePlatform': {'cpuArchitecture': 'X86_64', 'operatingSystemFamily': 'LINUX'},
            'volumes': [{'name': 'tmp'}], 'tags': tags,
            'containerDefinitions': [{
                'name': component, 'image': image, 'essential': True,
                'command': ['python', '-m', 'app.aws_bootstrap', phase],
                'readonlyRootFilesystem': True, 'linuxParameters': {'initProcessEnabled': True},
                'mountPoints': [{'sourceVolume': 'tmp', 'containerPath': '/tmp', 'readOnly': False}],
                'environment': [{'name': 'ECONOMICON_BOOTSTRAP', 'value': 'ecs'},
                                {'name': 'DEMO_BOOTSTRAP_INPUTS', 'value': payload}],
                'logConfiguration': {'logDriver': 'awslogs', 'options': {
                    'awslogs-group': network['log_groups'][component], 'awslogs-region': 'eu-west-1',
                    'awslogs-stream-prefix': 'bootstrap'}}, 'stopTimeout': 60,
            }],
        }

    def run(self, component, phase, inputs):
        # Validate the complete request before the first mutation.
        try:
            definition = self.definition(component, phase, inputs)
        except Exception:
            raise PrivateTaskError('Private bootstrap task configuration is invalid.') from None
        state = {'component': component, 'phase': phase, 'status': 'REGISTERING'}
        task = None
        arn = None
        stopped = False
        success = False
        cleanup_failed = False
        cluster = self.outputs['ecs_cluster_name']
        try:
            response = self.ecs.register_task_definition(**definition)
            candidate = response['taskDefinition']['taskDefinitionArn']
            prefix = f"arn:aws:ecs:eu-west-1:{self.config['account_id']}:task-definition/{definition['family']}:"
            _require(re.fullmatch(re.escape(prefix) + r'[1-9][0-9]*', candidate))
            arn = candidate
            state.update(definition_arn=arn, status='REGISTERED')
            self.record(dict(state))
            response = self.ecs.run_task(cluster=cluster, taskDefinition=arn, launchType='FARGATE',
                platformVersion='1.4.0', count=1, enableExecuteCommand=False,
                startedBy='jup131-' + uuid4().hex[:28], clientToken=uuid4().hex,
                tags=definition['tags'], networkConfiguration={'awsvpcConfiguration': {
                    'subnets': self.outputs['bootstrap_network']['subnets'],
                    'securityGroups': [self.outputs['bootstrap_network']['security_group_id']],
                    'assignPublicIp': 'DISABLED'}})
            _require(not response.get('failures') and len(response.get('tasks', [])) == 1)
            candidate = response['tasks'][0]['taskArn']
            _require(re.fullmatch(f"arn:aws:ecs:eu-west-1:{self.config['account_id']}:task/{cluster}/[a-f0-9]{{32}}", candidate))
            task = candidate
            state.update(task_arn=task, status='RUNNING')
            self.record(dict(state))
            self.ecs.get_waiter('tasks_stopped').wait(cluster=cluster, tasks=[task],
                WaiterConfig={'Delay': 5, 'MaxAttempts': 120})
            response = self.ecs.describe_tasks(cluster=cluster, tasks=[task])
            _require(not response.get('failures') and len(response.get('tasks', [])) == 1)
            result = response['tasks'][0]
            _require(result.get('taskArn') == task and result.get('lastStatus') == 'STOPPED')
            stopped = True
            containers = result.get('containers', [])
            _require(len(containers) == 1 and containers[0].get('name') == component
                     and type(containers[0].get('exitCode')) is int and containers[0]['exitCode'] == 0)
            success = True
        except Exception:
            success = False
        finally:
            if task and not stopped:
                try:
                    self.ecs.stop_task(cluster=cluster, task=task, reason='Disposable bootstrap failed or timed out')
                    self.ecs.get_waiter('tasks_stopped').wait(cluster=cluster, tasks=[task],
                        WaiterConfig={'Delay': 5, 'MaxAttempts': 12})
                except Exception:
                    cleanup_failed = True
            if arn:
                try:
                    self.ecs.deregister_task_definition(taskDefinition=arn)
                except Exception:
                    cleanup_failed = True
            state['status'] = 'CLEANUP_FAILED' if cleanup_failed else ('SUCCEEDED' if success else 'FAILED')
            self.record(dict(state))
        if not success or cleanup_failed:
            raise PrivateTaskError('Private bootstrap task failed; inspect the restricted task manifest.')
        return state
