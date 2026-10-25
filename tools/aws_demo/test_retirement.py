"""Tag inventory can retain deleted resources; authoritative reads decide."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import runner
from test_control import config


class RetirementTests(unittest.TestCase):
    def inspect(self, service, resource, operation, response=None, error=None, account='123456789012'):
        instance = object.__new__(runner.Runner)
        instance.config = config()
        arn = f'arn:aws:{service}:eu-west-1:{account}:{resource}'
        calls = []
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'WORK', Path(directory)):
            def aws(*args, **kwargs):
                self.assertEqual(kwargs, {'deploy': True})
                if args[0] == 'resourcegroupstaggingapi':
                    return {'ResourceTagMappingList': [{'ResourceARN': arn}]} if args[3] == 'eu-west-1' else {}
                calls.append(args)
                self.assertEqual(args[0:2], (service, operation))
                self.assertEqual(args[-2:], ('--region', 'eu-west-1'))
                if error:
                    (Path(directory) / 'last-error.private.txt').write_text(error)
                    raise RuntimeError('aws failed')
                return response
            instance.aws = aws
            result = instance.inspect_residuals()
            return result, calls, arn

    def test_deleted_nat_and_endpoint_are_retired_metadata(self):
        cases = [('natgateway/nat-test', 'describe-nat-gateways', 'NatGateways', 'NatGatewayId', 'nat-test'),
                 ('vpc-endpoint/vpce-test', 'describe-vpc-endpoints', 'VpcEndpoints', 'VpcEndpointId', 'vpce-test')]
        for resource, operation, key, id_key, identity in cases:
            with self.subTest(resource=resource):
                result, calls, arn = self.inspect('ec2', resource, operation, {key: [{id_key: identity, 'State': 'deleted'}]})
                self.assertEqual(result['active'], [])
                self.assertEqual(result['retired_metadata'], [arn])
                self.assertEqual(len(calls), 1)

    def test_exact_not_found_codes_confirm_absence(self):
        cases = [('ec2', 'natgateway/nat-test', 'describe-nat-gateways', 'NatGatewayNotFound', 'DescribeNatGateways'),
                 ('ec2', 'natgateway/nat-test', 'describe-nat-gateways', 'InvalidNatGatewayID.NotFound', 'DescribeNatGateways'),
                 ('ec2', 'security-group-rule/sgr-test', 'describe-security-group-rules', 'InvalidSecurityGroupRuleId.NotFound', 'DescribeSecurityGroupRules'),
                 ('ec2', 'subnet/subnet-test', 'describe-subnets', 'InvalidSubnetID.NotFound', 'DescribeSubnets'),
                 ('ec2', 'vpc-endpoint/vpce-test', 'describe-vpc-endpoints', 'InvalidVpcEndpointId.NotFound', 'DescribeVpcEndpoints'),
                 ('cognito-idp', 'userpool/pool-test', 'describe-user-pool', 'ResourceNotFoundException', 'DescribeUserPool')]
        for service, resource, operation, code, api in cases:
            with self.subTest(resource=resource):
                result, _, arn = self.inspect(service, resource, operation,
                    error=f'An error occurred ({code}) when calling the {api} operation: absent\n')
                self.assertEqual(result['active'], [])
                self.assertEqual(result['retired_metadata'], [arn])

    def test_aws_cli_error_prefix_preserves_exact_absence_classification(self):
        result, _, arn = self.inspect('ec2', 'security-group-rule/sgr-test',
            'describe-security-group-rules', error=(
                'aws: [ERROR]: An error occurred (InvalidSecurityGroupRuleId.NotFound) '
                'when calling the DescribeSecurityGroupRules operation: absent\n'))
        self.assertEqual(result['active'], [])
        self.assertEqual(result['retired_metadata'], [arn])

    def test_prefixed_denials_wrong_operations_and_embedded_errors_abort(self):
        errors = (
            'aws: [ERROR]: An error occurred (AccessDenied) when calling the DescribeSubnets operation: denied',
            'aws: [ERROR]: An error occurred (InvalidSubnetID.NotFound) when calling the OtherOperation operation: wrong',
            'request text aws: [ERROR]: An error occurred (InvalidSubnetID.NotFound) when calling the DescribeSubnets operation: quoted',
            'aws: [WARNING]: An error occurred (InvalidSubnetID.NotFound) when calling the DescribeSubnets operation: wrong level',
        )
        for error in errors:
            with self.subTest(error=error), self.assertRaises(RuntimeError):
                self.inspect('ec2', 'subnet/subnet-test', 'describe-subnets', error=error)

    def test_inactive_cluster_requires_no_tasks_or_services(self):
        arn = 'arn:aws:ecs:eu-west-1:123456789012:cluster/economicon-ensayo1'
        for count in (0, 1):
            with self.subTest(running=count):
                result, _, _ = self.inspect('ecs', 'cluster/economicon-ensayo1', 'describe-clusters', {'clusters': [{
                    'clusterArn': arn, 'status': 'INACTIVE', 'runningTasksCount': count,
                    'pendingTasksCount': 0, 'activeServicesCount': 0}]})
                self.assertEqual(result['active'], [] if count == 0 else [arn])

    def test_missing_cluster_requires_exact_missing_failure(self):
        arn = 'arn:aws:ecs:eu-west-1:123456789012:cluster/economicon-ensayo1'
        result, _, _ = self.inspect('ecs', 'cluster/economicon-ensayo1', 'describe-clusters',
            {'clusters': [], 'failures': [{'arn': arn, 'reason': 'MISSING'}]})
        self.assertEqual(result['retired_metadata'], [arn])
        for response in ({'clusters': []}, {'clusters': [], 'failures': [{'arn': arn, 'reason': 'ACCESS_DENIED'}]}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                self.inspect('ecs', 'cluster/economicon-ensayo1', 'describe-clusters', response)

    def test_retired_ecs_services_and_tasks_require_exact_cycle_and_terminal_state(self):
        cluster = 'arn:aws:ecs:eu-west-1:123456789012:cluster/economicon-ensayo1'
        cases = [
            ('service', 'backend', 'describe-services', 'services', 'serviceArn',
             {'status':'INACTIVE', 'desiredCount':0, 'runningCount':0, 'pendingCount':0}),
            ('task', 'task-id', 'describe-tasks', 'tasks', 'taskArn',
             {'lastStatus':'STOPPED', 'desiredStatus':'STOPPED'}),
        ]
        for kind, name, operation, key, id_key, terminal in cases:
            resource = f'{kind}/economicon-ensayo1/{name}'
            arn = 'arn:aws:ecs:eu-west-1:123456789012:' + resource
            with self.subTest(kind=kind):
                obj = dict(terminal, clusterArn=cluster, **{id_key:arn})
                result, calls, _ = self.inspect('ecs', resource, operation, {key:[obj]})
                self.assertEqual(result['retired_metadata'], [arn])
                self.assertEqual(result['active'], [])
                self.assertEqual(calls[0][-4:-2], ('--cluster', cluster))
                result, _, _ = self.inspect('ecs', resource, operation,
                    {key:[], 'failures':[{'arn':arn, 'reason':'MISSING'}]})
                self.assertEqual(result['retired_metadata'], [arn])
                with self.assertRaises(ValueError):
                    self.inspect('ecs', resource, operation, {key:[dict(obj, clusterArn=cluster+'-foreign')]})
                for response in ({key:[]}, {key:[], 'failures':[{'arn':arn, 'reason':'ACCESS_DENIED'}]}):
                    with self.assertRaises(ValueError):
                        self.inspect('ecs', resource, operation, response)
        with self.assertRaises(ValueError):
            self.inspect('ecs', 'service/economicon-other/backend', 'describe-services', {'services':[]})

    def test_live_ecs_service_and_task_states_remain_active(self):
        cluster = 'arn:aws:ecs:eu-west-1:123456789012:cluster/economicon-ensayo1'
        resource = 'service/economicon-ensayo1/backend'
        arn = 'arn:aws:ecs:eu-west-1:123456789012:' + resource
        for state, desired, running, pending in [('ACTIVE',0,0,0),('DRAINING',0,0,0),('INACTIVE',1,0,0),('INACTIVE',0,1,0),('INACTIVE',0,0,1)]:
            with self.subTest(state=state, counts=(desired,running,pending)):
                result, _, _ = self.inspect('ecs', resource, 'describe-services', {'services':[{'serviceArn':arn,'clusterArn':cluster,'status':state,'desiredCount':desired,'runningCount':running,'pendingCount':pending}]})
                self.assertEqual(result['active'], [arn])
        resource = 'task/economicon-ensayo1/task-id'
        arn = 'arn:aws:ecs:eu-west-1:123456789012:' + resource
        for actual, desired in [('RUNNING','RUNNING'),('STOPPING','STOPPED'),('STOPPED','RUNNING')]:
            with self.subTest(actual=actual, desired=desired):
                result, _, _ = self.inspect('ecs', resource, 'describe-tasks', {'tasks':[{'taskArn':arn,'clusterArn':cluster,'lastStatus':actual,'desiredStatus':desired}]})
                self.assertEqual(result['active'], [arn])

    def test_present_and_deleting_resources_remain_active(self):
        for status in ('available', 'deleting', 'pending'):
            with self.subTest(status=status):
                result, _, arn = self.inspect('ec2', 'natgateway/nat-test', 'describe-nat-gateways',
                    {'NatGateways': [{'NatGatewayId': 'nat-test', 'State': status}]})
                self.assertEqual(result['active'], [arn])
        result, _, arn = self.inspect('cognito-idp', 'userpool/pool-test', 'describe-user-pool', {'UserPool': {'Id': 'pool-test'}})
        self.assertEqual(result['active'], [arn])

    def test_denials_and_unrelated_error_codes_abort(self):
        for error in ('An error occurred (AccessDenied) when calling the DescribeSubnets operation: denied',
                      'An error occurred (InvalidSubnetID.NotFound) when calling the OtherOperation operation: wrong',
                      'request text InvalidSubnetID.NotFound is not an AWS error'):
            with self.subTest(error=error), self.assertRaises(RuntimeError):
                self.inspect('ec2', 'subnet/subnet-test', 'describe-subnets', error=error)

    def test_malformed_or_wrong_identity_responses_fail_closed(self):
        for response in ({}, {'NatGateways': [{'NatGatewayId': 'nat-foreign', 'State': 'deleted'}]},
                         {'NatGateways': [{'NatGatewayId': 'nat-test'}]}):
            with self.subTest(response=response), self.assertRaises((KeyError, ValueError)):
                self.inspect('ec2', 'natgateway/nat-test', 'describe-nat-gateways', response)
        with self.assertRaises(ValueError):
            self.inspect('ec2', 'natgateway/nat-test', 'describe-nat-gateways', {'NatGateways': []}, account='999999999999')

    def test_unknown_types_remain_active_without_a_guessed_api(self):
        result, calls, arn = self.inspect('ec2', 'unknown-resource/unknown-test', 'unused')
        self.assertEqual(result['active'], [arn])
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
