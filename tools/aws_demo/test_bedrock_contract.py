import copy
import unittest

from tools.aws_demo.bedrock_contract import validate_profile, expected_profile


class BedrockProfileTests(unittest.TestCase):
    def test_ireland_has_four_pinned_destinations_and_rejects_spain(self):
        profile, value = self.fixture()
        expected = expected_profile('123456789012', profile)
        self.assertEqual(expected['arn'], 'arn:aws:bedrock:eu-west-1:123456789012:inference-profile/' + profile)
        self.assertEqual({arn.split(':')[3] for arn in expected['models']},
                         {'eu-central-1', 'eu-north-1', 'eu-west-1', 'eu-west-3'})
        value['models'].append({'modelArn': 'arn:aws:bedrock:eu-south-2::foundation-model/amazon.nova-micro-v1:0'})
        with self.assertRaises(ValueError):
            validate_profile(value, '123456789012', profile)

    def fixture(self):
        profile='eu.amazon.nova-micro-v1:0'
        expected=expected_profile('123456789012',profile)
        return profile, dict(inferenceProfileArn=expected['arn'],inferenceProfileId=profile,
            status='ACTIVE',type='SYSTEM_DEFINED',models=[{'modelArn':x} for x in expected['models']])

    def test_accepts_only_the_pinned_system_profile_and_destinations(self):
        profile,value=self.fixture()
        self.assertEqual(validate_profile(value,'123456789012',profile),expected_profile('123456789012',profile))

    def test_rejects_foreign_account_region_model_status_and_destination_drift(self):
        profile,value=self.fixture()
        changes=[('inferenceProfileArn',value['inferenceProfileArn'].replace('123456789012','999999999999')),
            ('status','INACTIVE'),('type','APPLICATION'),('inferenceProfileId','global.amazon.nova-micro-v1:0'),
            ('models',value['models'][:-1]),('models',value['models']+[{'modelArn':'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0'}])]
        for field,changed in changes:
            bad=copy.deepcopy(value);bad[field]=changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_profile(bad,'123456789012',profile)

    def test_rejects_unknown_profile_ids_before_any_external_access(self):
        for profile in ('global.amazon.nova-micro-v1:0','us.amazon.nova-micro-v1:0','other'):
            with self.assertRaises(ValueError): expected_profile('123456789012',profile)
