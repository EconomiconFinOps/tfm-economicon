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
