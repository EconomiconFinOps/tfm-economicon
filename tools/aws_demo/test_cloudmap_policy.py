"""Opt-in, read-only IAM evaluation of a rendered bootstrap deploy policy.

Set AWS_CLOUDMAP_POLICY_TEST_FILE to its JSON policy document. This calls only
SimulateCustomPolicy: it does not attach policies or create DNS resources.
"""
import json
import os
from pathlib import Path
import unittest

import boto3


@unittest.skipUnless(os.environ.get('AWS_CLOUDMAP_POLICY_TEST_FILE'),
                     'requires an explicitly supplied policy and IAM simulator access')
class CloudMapPolicyTests(unittest.TestCase):
    def test_private_zone_dependencies_preserve_direct_dns_boundaries(self):
        policy = json.dumps(json.loads(Path(
            os.environ['AWS_CLOUDMAP_POLICY_TEST_FILE']).read_text(encoding='utf-8-sig')))
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


if __name__ == '__main__':
    unittest.main()
