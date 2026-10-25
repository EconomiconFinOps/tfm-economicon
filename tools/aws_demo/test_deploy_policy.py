"""Opt-in, read-only IAM evaluation of a rendered bootstrap deploy policy.

Set AWS_DEPLOY_POLICY_TEST_FILE to its JSON policy document. This calls only
SimulateCustomPolicy: it does not attach policies or create DNS resources.
"""
import json
import os
from pathlib import Path
import re
import unittest

import boto3


@unittest.skipUnless(os.environ.get('AWS_DEPLOY_POLICY_TEST_FILE'),
                     'requires an explicitly supplied policy and IAM simulator access')
class DeployPolicyTests(unittest.TestCase):
    def test_private_zone_dependencies_preserve_direct_dns_boundaries(self):
        policy = json.dumps(json.loads(Path(
            os.environ['AWS_DEPLOY_POLICY_TEST_FILE']).read_text(encoding='utf-8-sig')))
        iam = boto3.client('iam')
        zone = 'arn:aws:route53:::hostedzone/ZCLOUDMAPREGRESSION'
        cloudmap = {'ContextKeyName': 'aws:CalledVia',
                    'ContextKeyValues': ['servicediscovery.amazonaws.com'],
                    'ContextKeyType': 'stringList'}
        ireland = {'ContextKeyName': 'route53:VPCs',
                   'ContextKeyValues': ['VPCId=vpc-0123456789abcdef0,VPCRegion=eu-west-1'],
                   'ContextKeyType': 'string'}
        paris = {**ireland, 'ContextKeyValues': [
            'VPCId=vpc-0123456789abcdef0,VPCRegion=eu-west-3']}
        other_service = {**cloudmap, 'ContextKeyValues': ['cloudformation.amazonaws.com']}
        cases = [
            ('private Ireland via Cloud Map', 'CreateHostedZone', '*', [cloudmap, ireland], 'allowed'),
            ('public zone via Cloud Map', 'CreateHostedZone', '*', [cloudmap], 'implicitDeny'),
            ('private Paris via Cloud Map', 'CreateHostedZone', '*', [cloudmap, paris], 'implicitDeny'),
            ('direct private creation', 'CreateHostedZone', '*', [ireland], 'implicitDeny'),
            ('other service private creation', 'CreateHostedZone', '*', [other_service, ireland], 'implicitDeny'),
            ('Cloud Map namespace lookup', 'ListHostedZonesByName', '*', [cloudmap], 'allowed'),
            ('direct namespace lookup', 'ListHostedZonesByName', '*', [], 'implicitDeny'),
            ('Cloud Map zone read', 'GetHostedZone', zone, [cloudmap], 'allowed'),
            ('direct unrelated zone read', 'GetHostedZone', zone, [], 'implicitDeny'),
            ('other service zone read', 'GetHostedZone', zone, [other_service], 'implicitDeny'),
            ('Cloud Map namespace deletion', 'DeleteHostedZone', zone, [cloudmap], 'allowed'),
            ('direct zone deletion', 'DeleteHostedZone', zone, [], 'implicitDeny'),
            ('other service zone deletion', 'DeleteHostedZone', zone, [other_service], 'implicitDeny'),
            ('direct unrelated record mutation', 'ChangeResourceRecordSets', zone, [], 'implicitDeny'),
        ]
        for label, action, resource, context, expected in cases:
            with self.subTest(label=label):
                result = iam.simulate_custom_policy(
                    PolicyInputList=[policy], ActionNames=[f'route53:{action}'],
                    ResourceArns=[resource], ContextEntries=context)
                decisions = [item['EvalDecision'] for item in result['EvaluationResults']]
                self.assertEqual(decisions, [expected])

    def test_terraform_bucket_and_role_dependencies_stay_in_project_scope(self):
        document = json.loads(Path(os.environ['AWS_DEPLOY_POLICY_TEST_FILE']).read_text(
            encoding='utf-8-sig'))
        policy = json.dumps(document)
        iam = boto3.client('iam')
        actions = ['s3:GetEncryptionConfiguration', 's3:PutEncryptionConfiguration',
                   's3:GetAccelerateConfiguration', 's3:GetLifecycleConfiguration',
                   's3:GetReplicationConfiguration']
        protected_bucket = next(s['Resource'][0] for s in document['Statement']
                                if s['Effect'] == 'Deny' and s['Action'] == 's3:*')
        for resource, expected in [
            ('arn:aws:s3:::economicon-ensayo1-regression', 'allowed'),
            ('arn:aws:s3:::unrelated-regression', 'implicitDeny'),
            (protected_bucket, 'explicitDeny'),
        ]:
            result = iam.simulate_custom_policy(
                PolicyInputList=[policy], ActionNames=actions, ResourceArns=[resource])
            decisions = {item['EvalActionName']: item['EvalDecision']
                         for item in result['EvaluationResults']}
            for action in actions:
                with self.subTest(resource=resource, action=action):
                    self.assertEqual(decisions[action], expected)
        account = re.search(r'arn:aws:iam::([0-9]{12}):role/economicon-\*', policy).group(1)
        protected_role = next(s['Resource'][0] for s in document['Statement']
                              if s['Effect'] == 'Deny' and 'iam:DeleteRole' in s['Action'])
        for action, resource, expected in [
            ('iam:ListInstanceProfilesForRole', f'arn:aws:iam::{account}:role/economicon-ensayo1-regression', 'allowed'),
            ('iam:ListInstanceProfilesForRole', f'arn:aws:iam::{account}:role/unrelated-regression', 'implicitDeny'),
            ('iam:DeleteRole', protected_role, 'explicitDeny'),
        ]:
            with self.subTest(resource=resource, action=action):
                result = iam.simulate_custom_policy(
                    PolicyInputList=[policy], ActionNames=[action], ResourceArns=[resource])
                self.assertEqual(result['EvaluationResults'][0]['EvalDecision'], expected)


if __name__ == '__main__':
    unittest.main()
