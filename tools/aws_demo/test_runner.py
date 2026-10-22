import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import runner
import prepare
from test_control import config


class RunnerTests(unittest.TestCase):
    def test_orphan_bootstrap_definitions_are_scoped_before_retirement(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        prefix = 'arn:aws:ecs:eu-south-2:123456789012:task-definition/economicon-ensayo1-bootstrap-'
        owned, foreign = prefix + 'backend-database:1', prefix + 'processor-database:2'
        calls = []
        def aws(*args, **kwargs):
            calls.append(args)
            if args[1] == 'list-task-definitions':
                return {'taskDefinitionArns': [owned, foreign, 'arn:aws:ecs:eu-south-2:999999999999:task-definition/foreign:1']}
            if args[1] == 'describe-task-definition':
                arn = args[3]
                tags = dict(Project='economicon', Environment='ensayo1', Purpose='bootstrap', SourceSha='a' * 40 if arn == owned else 'b' * 40)
                return {'taskDefinition': {'taskDefinitionArn': arn, 'status': 'ACTIVE'},
                        'tags': [{'key': key, 'value': value} for key, value in tags.items()]}
            return {}
        item.aws = aws
        self.assertEqual(item.retire_bootstrap_definitions('economicon-ensayo1'), [owned])
        retired = [args[3] for args in calls if args[1] == 'deregister-task-definition']
        self.assertEqual(retired, [owned])

    def test_inactive_definition_is_retired_metadata_not_active_inventory(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        arn = 'arn:aws:ecs:eu-south-2:123456789012:task-definition/economicon-ensayo1-bootstrap-backend-database:1'
        def aws(*args, **kwargs):
            if args[0] == 'resourcegroupstaggingapi':
                return {'ResourceTagMappingList': [{'ResourceARN': arn}]} if args[3] == 'eu-south-2' else {}
            return {'taskDefinition': {'status': 'INACTIVE'}}
        item.aws = aws
        result = item.inspect_residuals()
        self.assertEqual(result['active'], [])
        self.assertEqual(result['retired_metadata'], [arn])

    def test_base_plan_has_embedding_and_chat_permissions_before_bootstrap(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        recipe = {"application_environment": {"processor": {"BEDROCK_REGION": "eu-south-2"}},
                  "bedrock_model_arns": ["arn:aws:bedrock:eu-south-2::foundation-model/amazon.titan-embed-text-v2:0"],
                  "bedrock_chat_profile_id": "eu.amazon.nova-micro-v1:0"}
        item.recipe = lambda: recipe
        with patch.dict(os.environ, BOUNDARY_ARN="arn:aws:iam::123456789012:policy/synthetic"):
            values = item.base_vars()
        self.assertFalse(values["deploy_applications"])
        self.assertEqual(values["bedrock_model_arns"], recipe["bedrock_model_arns"])
        self.assertEqual(values["bedrock_chat_profile_id"], recipe["bedrock_chat_profile_id"])
        self.assertEqual(values["application_environment"], recipe["application_environment"])

    def test_bedrock_metadata_preflight_rejects_destination_drift(self):
        from bedrock_contract import expected_profile
        item = object.__new__(runner.Runner)
        item.config = config()
        profile = "eu.amazon.nova-micro-v1:0"
        contract = expected_profile(item.config["account_id"], profile)
        value = dict(inferenceProfileArn=contract["arn"], inferenceProfileId=profile,
                     status="ACTIVE", type="SYSTEM_DEFINED", models=[{"modelArn": x} for x in contract["models"]])
        calls = []
        item.aws = lambda *a, **kw: calls.append((a, kw)) or value
        item.validate_bedrock_profile({"bedrock_chat_profile_id": profile})
        self.assertEqual(calls[0], (("bedrock", "get-inference-profile", "--inference-profile-identifier", profile,
                                    "--region", "eu-south-2"), {"deploy": True}))
        value["models"] = value["models"][:-1]
        with self.assertRaises(ValueError):
            item.validate_bedrock_profile({"bedrock_chat_profile_id": profile})

    def test_inventory_reports_active_resources_separately_from_pending_deletion(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        def response(*args, **kwargs):
            if args[0] == "resourcegroupstaggingapi":
                return {"ResourceTagMappingList": [{"ResourceARN": "arn:aws:kms:eu-south-2:123456789012:key/pending"},
                    {"ResourceARN": "arn:aws:ecs:eu-south-2:123456789012:cluster/active"}]} if "eu-south-2" in args else {}
            return {"KeyMetadata": {"KeyState": "PendingDeletion"}}
        item.aws = response
        result = item.inspect_residuals()
        self.assertEqual(len(result["active"]), 1)
        self.assertEqual(len(result["pending_deletion"]), 1)

    def test_expired_approval_never_calls_terraform(self):
        item = object.__new__(runner.Runner)
        item.config = dict(config(), expires_at="2000-01-01T00:00:00Z")
        item.lease = lambda *a, **kw: "PLANNED"
        item.init = lambda: self.fail("expired plan must not initialize/apply")
        with self.assertRaises(ValueError):
            item.apply()

    def test_stop_writers_scales_state_services_before_storage_cleanup(self):
        item = object.__new__(runner.Runner)
        calls = []
        item.aws = lambda *a, **kw: calls.append(a) or {"taskArns": []}
        item.stop_writers({"values": {"root_module": {"resources": [
            {"type": "aws_ecs_service", "address": 'aws_ecs_service.application["processor"]',
             "values": {"cluster": "arn:cluster/demo", "name": "processor"}},
            {"type": "aws_ecs_cluster", "address": "aws_ecs_cluster.main", "values": {"id": "arn:cluster/demo"}}
        ]}}})
        self.assertEqual(calls[0][0:2], ("ecs", "update-service"))
        self.assertIn("0", calls[0])
        self.assertEqual(calls[1][0:3], ("ecs", "wait", "services-stable"))

    def test_import_and_local_preparation_never_invoke_aws(self):
        with tempfile.TemporaryDirectory() as directory, patch("subprocess.run", side_effect=AssertionError("Network/process forbidden")):
            result = prepare.prepare(config(), directory, "a" * 40)
            self.assertFalse(result["aws_deployable"])
            self.assertFalse(result["aws_resources_created"])
            up = json.loads((Path(directory) / "start-up.json").read_text())
            self.assertEqual(up["sourceRevisions"][0]["revisionValue"], "a" * 40)
            self.assertEqual(up["variables"][0]["name"], "ConfigKey")

    def test_stale_plan_never_calls_terraform(self):
        item = object.__new__(runner.Runner)
        item.config = dict(config(), expires_at="2099-01-01T00:00:00Z")
        item.lease = lambda *a, **kw: "TEARDOWN"
        item.init = lambda: self.fail("stale plan must not initialize/apply")
        with self.assertRaises(ValueError):
            item.apply()

    def test_partial_empty_state_cleanup_never_plans_creation(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        item.vars = {}
        item.lease = lambda *a, **kw: "TEARDOWN"
        item.init = lambda: None
        calls = []
        item.tf = lambda *args: calls.append(args) or '{"values":{"root_module":{}}}'
        item.make_plan = lambda *a, **kw: calls.append(("destroy-plan",))
        item.upload = lambda *a: None
        item.plan_down()
        self.assertFalse(any(c[0] in ("plan", "apply") for c in calls))
        self.assertIn(("destroy-plan",), calls)

    def test_failed_command_does_not_echo_passwords_or_dsn(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, "WORK", Path(directory)), \
             patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, "secret-password", "sensitive-dsn")):
            with self.assertRaises(RuntimeError) as error:
                runner.run(["terraform", "plan"])
            self.assertNotIn("secret-password", str(error.exception))
            self.assertNotIn("sensitive-dsn", str(error.exception))
            self.assertIn("secret-password", (Path(directory) / "last-error.private.txt").read_text())

    def test_cloud_entrypoint_rejects_local_execution(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            runner.Runner()


if __name__ == "__main__":
    unittest.main()
