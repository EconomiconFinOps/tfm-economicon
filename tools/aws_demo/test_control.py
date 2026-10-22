import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("control", Path(__file__).with_name("control.py"))
control = importlib.util.module_from_spec(SPEC)
if SPEC.loader and Path(SPEC.origin).exists():
    SPEC.loader.exec_module(control)


def config():
    return {
        "cycle_id": "ensayo1", "account_id": "123456789012", "source_sha": "a" * 40,
        "region": "eu-south-2", "control_region": "eu-west-3",
        "frontend_domain": "economicon.danteinferno.es",
        "origin_domain": "origin.economicon.danteinferno.es", "route53_zone_id": "Z123456789",
        "availability_zones": ["eu-south-2a", "eu-south-2b", "eu-south-2c"],
        "postgres_version": "16.9", "rabbitmq_version": "3.13",
        "expires_at": "2026-10-23T18:00:00Z", "budget_eur": 60,
        "estimated_cycle_eur": 9, "available_credit_eur": 60,
        "ci_run_id": "12345", "release_recipe": "infra/aws-cicd/release.json",
    }


class ConfigTests(unittest.TestCase):
    def test_valid_config_uses_selected_regions_and_cycle_state(self):
        result = control.validate_config(config(), "a" * 40)
        self.assertEqual(control.state_key(result), "economicon/defensa/ensayo1/terraform.tfstate")

    def test_rejects_wrong_sha_account_region_zone_budget_and_expiry(self):
        for key, value in [("source_sha", "main"), ("account_id", "REPLACE"),
                           ("region", "eu-west-1"), ("availability_zones", ["eu-west-1a"]),
                           ("estimated_cycle_eur", 61), ("expires_at", "tomorrow"),
                           ("cycle_id", "../../other"), ("release_recipe", "../secrets.json")]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                control.validate_config(dict(config(), **{key: value}), "a" * 40)

    def test_rejects_stale_source_even_for_valid_configuration(self):
        with self.assertRaises(ValueError):
            control.validate_config(config(), "b" * 40)

    def test_fixture_is_deliberately_not_launchable(self):
        example = json.loads((Path(__file__).parents[2] / "infra/aws-cicd/ensayo1.example.json").read_text())
        with self.assertRaises(ValueError):
            control.validate_config(example, "a" * 40)


class PlanTests(unittest.TestCase):
    def test_unlock_cannot_create_resources_during_partial_failure_cleanup(self):
        plan = {"resource_changes": [{"address": 'aws_db_instance.main["operational"]',
                "change": {"actions": ["create"], "before": None, "after": {}}}]}
        with self.assertRaises(ValueError):
            control.check_unlock_plan(plan)

    def test_unlock_cannot_change_engine_or_network(self):
        plan = {"resource_changes": [{"address": 'aws_db_instance.main["operational"]',
                "change": {"actions": ["update"], "before": {"engine_version": "16.9"},
                           "after": {"engine_version": "17.1"}}}]}
        with self.assertRaises(ValueError):
            control.check_unlock_plan(plan)

    def test_unlock_accepts_only_protection_updates(self):
        plan = {"resource_changes": [{"address": "aws_lb.api", "change": {"actions": ["update"],
                "before": {"enable_deletion_protection": True}, "after": {"enable_deletion_protection": False}}}]}
        control.check_unlock_plan(plan)

    def test_destroy_requires_all_resources_to_belong_to_demo(self):
        good = {"resource_changes": [{"address": "aws_vpc.main", "mode": "managed",
                 "type": "aws_vpc", "change": {"actions": ["delete"],
                 "before": {"id": "vpc-1", "tags_all": {"Project": "economicon", "Environment": "ensayo1"}}}}]}
        self.assertEqual(control.check_destroy_plan(good, "ensayo1"), ["aws_vpc.main"])
        for key, value in [("Environment", "bootstrap"), ("Project", "other")]:
            bad = copy.deepcopy(good)
            bad["resource_changes"][0]["change"]["before"]["tags_all"][key] = value
            with self.assertRaises(ValueError):
                control.check_destroy_plan(bad, "ensayo1")

    def test_destroy_rejects_unknown_resource_type(self):
        with self.assertRaises(ValueError):
            control.check_destroy_plan({"resource_changes": [{"address": "aws_organizations_account.other",
                "type": "aws_organizations_account", "mode": "managed",
                "change": {"actions": ["delete"], "before": {}}}]}, "ensayo1")

    def test_inventory_only_selects_exact_state_addresses(self):
        state = {"values": {"root_module": {"resources": [
            {"address": 'aws_s3_bucket.main["frontend"]', "type": "aws_s3_bucket", "values": {"id": "demo-bucket"}},
            {"address": "aws_s3_bucket.state", "type": "aws_s3_bucket", "values": {"id": "bootstrap"}}]}}}
        self.assertEqual(control.cleanup_inventory(state)["buckets"], ["demo-bucket"])

    def test_plan_binding_detects_modified_binary_and_other_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "infra.tfplan"
            plan.write_bytes(b"saved-plan")
            binding = control.bind_plan(plan, config())
            control.verify_binding(plan, binding, config())
            plan.write_bytes(b"replaced-plan")
            with self.assertRaises(ValueError):
                control.verify_binding(plan, binding, config())


class ReleaseTests(unittest.TestCase):
    def test_recipe_rejects_unreviewed_models_and_inline_task_keys(self):
        recipe = dict(application_sha256="a" * 64,
                      evidence={name: {"path": "docs/evidence/synthetic.md", "sha256": "b" * 64}
                                for name in ("postgresql", "cognito", "bedrock", "demo_data")},
                      bootstrap=[["python", "tools/aws_demo/bootstrap.py"]],
                      checks=[["python", "tools/aws_demo/checks.py"]])
        for field, value in [
            ("bedrock_model_arns", ["arn:aws:bedrock:eu-south-2::foundation-model/*"]),
            ("bedrock_model_arns", ["arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"]),
            ("bedrock_chat_profile_id", "global.amazon.nova-micro-v1:0"),
            ("application_environment", {"backend": {"CHAT_HMAC_KEY": "synthetic-secret"}}),
            ("application_environment", {"processor": {"AWS_ACCESS_KEY_ID": "synthetic-key"}}),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                control.validate_recipe(dict(recipe, **{field: value}))

    def test_text_digest_is_portable_between_windows_and_linux(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.md"
            path.write_bytes(b"first\r\nsecond\r\n")
            windows = control.source_sha256(path)
            path.write_bytes(b"first\nsecond\n")
            self.assertEqual(windows, control.source_sha256(path))

    def test_expiry_source_keeps_dependency_locks_but_excludes_state_secrets_and_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = ["infra/aws-reference/.terraform.lock.hcl", "apps/backend/.dockerignore", ".github/workflows/ci.yml",
                     ".env", "infra/aws-reference/cycle.tfstate", ".work/plan.tfplan", "node_modules/a.js", "tools/aws_demo/runner.py"]
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            included = {p.relative_to(root).as_posix() for p in control.source_files(root)}
            self.assertEqual(included, set(names[:3] + [names[-1]]))

    def test_recipe_rejects_shell_and_missing_acceptance(self):
        for recipe in [{"bootstrap": [["sh", "-c", "true"]]},
                       {"bootstrap": [], "checks": []}]:
            with self.assertRaises(ValueError):
                control.validate_recipe(recipe)

    def test_fake_acceptance_does_not_enable_applications(self):
        with self.assertRaises(ValueError):
            control.validate_recipe({"source_sha": "a" * 40, "evidence": {}, "bootstrap": [], "checks": []})

    def test_scope_lock_is_shared_by_up_and_down_not_by_pipeline_name(self):
        self.assertEqual(control.lock_key(config()), "economicon.danteinferno.es")


if __name__ == "__main__":
    unittest.main()
