from __future__ import annotations

import importlib.util
import io
import contextlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dataset = load("economicon_demo_dataset_for_loader", ROOT / "scripts" / "demo_dataset.py")
sys.path.insert(0, str(ROOT / "scripts"))
demo = load("economicon_demo_data", ROOT / "scripts" / "demo_data.py")
MANIFEST = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
PAIRS = MANIFEST["pairs"]


class FakeStore:
    """In-memory stand-in with the contract of SqlStore."""

    def __init__(self):
        self.runs: dict[tuple[str, str], int] = {}
        self.records: dict[tuple[str, str], int] = {}
        self.episodes: dict[str, int] = {}
        self.writes = 0

    def add(self, tenant, subscription, records, runs=1):
        self.runs[(tenant, subscription)] = runs
        self.records[(tenant, subscription)] = records

    def subscription_counts(self, tenant):
        keys = {k[1] for k in list(self.runs) + list(self.records) if k[0] == tenant}
        return {sub: {"runs": self.runs.get((tenant, sub), 0), "records": self.records.get((tenant, sub), 0)} for sub in keys}

    def remove_subscriptions(self, tenant, subscriptions):
        self.writes += 1
        removed = {"runs": 0, "records": 0}
        for sub in subscriptions:
            removed["runs"] += self.runs.pop((tenant, sub), 0)
            removed["records"] += self.records.pop((tenant, sub), 0)
        return removed

    def tenant_cost_records(self, tenant):
        return sum(count for (t, _), count in self.records.items() if t == tenant)

    def drop_derived_state(self, tenant):
        self.writes += 1
        return self.episodes.pop(tenant, 0)


class FakeIngest:
    def __init__(self, store, fail_on=None):
        self.store, self.fail_on, self.calls = store, fail_on, []

    def __call__(self, tenant, subscription):
        self.calls.append((tenant, subscription))
        if len(self.calls) == self.fail_on:
            return False
        pair = next(p for p in PAIRS if p["subscription"] == subscription)
        self.store.add(tenant, subscription, pair["stored_rows"])
        return True


def run(command, store, ingest=None, env=None, extra=()):
    output = io.StringIO()
    environment = {"DATABASE_URL": "cockroachdb://x/y", "RUNTIME_ENVIRONMENT": "development", **(env or {})}
    with contextlib.redirect_stdout(output):
        code = demo.main([command, *extra], env=environment, store_factory=lambda url: store, ingest=ingest or FakeIngest(store))
    return code, output.getvalue()


class ApplyTests(unittest.TestCase):
    def test_loads_every_pair_once_in_manifest_order_and_reports_loaded(self):
        store, ingest = FakeStore(), None
        ingest = FakeIngest(store)
        code, out = run("apply", store, ingest)
        self.assertEqual(code, 0, out)
        self.assertEqual(ingest.calls, [(p["tenant"], p["subscription"]) for p in PAIRS])
        self.assertIn("loaded", out)
        self.assertIn("sinteticos", out)

    def test_second_apply_writes_nothing_and_reports_already_present(self):
        store = FakeStore()
        run("apply", store)
        ingest = FakeIngest(store)
        code, out = run("apply", store, ingest)
        self.assertEqual(code, 0)
        self.assertEqual(ingest.calls, [])
        self.assertIn("already-present", out)

    def test_refuses_a_tenant_with_data_of_a_foreign_subscription_and_loads_nothing_anywhere(self):
        store = FakeStore()
        store.add("tenant-growth", "someone-elses-subscription", 3)
        ingest = FakeIngest(store)
        code, out = run("apply", store, ingest)
        self.assertEqual(code, 2)
        self.assertEqual(ingest.calls, [])
        self.assertIn("tenant-growth", out)
        self.assertIn("other-data", out)

    def test_a_partial_state_is_refused_with_the_advice_to_remove_first(self):
        store = FakeStore()
        first = PAIRS[0]
        store.add(first["tenant"], first["subscription"], first["stored_rows"])
        ingest = FakeIngest(store)
        code, out = run("apply", store, ingest)
        self.assertEqual(code, 2)
        self.assertEqual(ingest.calls, [])
        self.assertIn("partial", out)
        self.assertIn("remove", out)

    def test_a_failure_in_the_middle_leaves_a_partial_state_that_apply_then_refuses(self):
        store = FakeStore()
        code, out = run("apply", store, FakeIngest(store, fail_on=3))
        self.assertEqual(code, 1, out)
        self.assertEqual(len(store.runs), 2)
        again, message = run("apply", store)
        self.assertEqual(again, 2)
        self.assertIn("partial", message)

    def test_a_subscription_with_fewer_records_than_expected_counts_as_partial(self):
        store = FakeStore()
        run("apply", store)
        key = next(iter(store.records))
        store.records[key] -= 1
        code, out = run("apply", store)
        self.assertEqual(code, 2)
        self.assertIn("partial", out)


class RemoveTests(unittest.TestCase):
    def test_removes_only_the_manifest_subscriptions_and_is_repeatable(self):
        store = FakeStore()
        run("apply", store)
        store.add("tenant-growth", "foreign-subscription", 5)
        code, out = run("remove", store)
        self.assertEqual(code, 0, out)
        self.assertEqual(store.subscription_counts("tenant-growth"), {"foreign-subscription": {"runs": 1, "records": 5}})
        self.assertEqual(store.subscription_counts("tenant-core"), {})
        writes = store.writes
        again, message = run("remove", store)
        self.assertEqual(again, 0)
        self.assertIn("0", message)
        self.assertEqual(store.subscription_counts("tenant-growth"), {"foreign-subscription": {"runs": 1, "records": 5}})
        self.assertGreaterEqual(store.writes, writes)

    def test_drops_episodes_of_a_tenant_left_without_cost_data_and_keeps_those_of_a_tenant_that_still_has_some(self):
        store = FakeStore()
        run("apply", store)
        store.episodes.update({"tenant-core": 3, "tenant-growth": 2})
        store.add("tenant-growth", "foreign-subscription", 5)
        code, out = run("remove", store)
        self.assertEqual(code, 0)
        self.assertNotIn("tenant-core", store.episodes)
        self.assertEqual(store.episodes["tenant-growth"], 2)
        self.assertIn("tenant-growth", out)

    def test_remove_does_not_accept_a_tenant_option(self):
        store = FakeStore()
        code, out = run("remove", store, extra=("--tenant", "tenant-core"))
        self.assertEqual(code, 2)


class GuardTests(unittest.TestCase):
    def test_production_is_refused_for_apply_and_remove_without_touching_anything(self):
        for command in ("apply", "remove"):
            store, ingest = FakeStore(), None
            ingest = FakeIngest(store)
            code, out = run(command, store, ingest, env={"RUNTIME_ENVIRONMENT": "production"})
            self.assertEqual(code, 2, command)
            self.assertEqual((ingest.calls, store.writes), ([], 0))
            self.assertIn("production", out)

    def test_missing_database_url_is_reported_without_a_traceback(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = demo.main(["status"], env={"RUNTIME_ENVIRONMENT": "development"}, store_factory=lambda url: FakeStore())
        self.assertEqual(code, 2)
        self.assertIn("DATABASE_URL", output.getvalue())

    def test_an_unexpected_error_does_not_print_the_connection_string(self):
        class Broken(FakeStore):
            def subscription_counts(self, tenant):
                raise RuntimeError("cockroachdb://root:secret@host/db failed")
        code, out = run("status", Broken())
        self.assertEqual(code, 2)
        self.assertNotIn("secret", out)


class StatusTests(unittest.TestCase):
    def test_reports_each_tenant_state(self):
        store = FakeStore()
        code, out = run("status", store)
        self.assertEqual(code, 0)
        self.assertIn("tenant-core: absent", out)
        run("apply", store)
        code, out = run("status", store)
        self.assertIn("tenant-core: present", out)
        self.assertIn("tenant-growth: present", out)
        store.add("tenant-growth", "foreign-subscription", 1)
        self.assertIn("tenant-growth: other-data", run("status", store)[1])


class GenerateTests(unittest.TestCase):
    def test_generate_reproduces_the_versioned_files(self):
        before = {path: path.read_bytes() for path in dataset.generate()}
        code, out = run("generate", FakeStore(), env={"DATABASE_URL": ""})
        self.assertEqual(code, 0, out)
        self.assertEqual({path: path.read_bytes() for path in before}, before)


if __name__ == "__main__":
    unittest.main()
