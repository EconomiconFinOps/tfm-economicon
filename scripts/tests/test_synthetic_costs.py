from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "synthetic_costs.py"
SPEC = importlib.util.spec_from_file_location("economicon_synthetic_costs", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
costs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = costs
SPEC.loader.exec_module(costs)

TENANT = "tenant-growth"
D = Decimal

# Expected values written by hand from docs/validation/JUP-106-synthetic-costs.md, never from the loader.
MONTHLY = {
    ("EUR", "2026-01"): D("100.00"),
    ("EUR", "2026-02"): D("0.00"),
    ("EUR", "2026-04"): D("40.00"),
    ("EUR", "2026-05"): D("-50.00"),
    ("USD", "2026-02"): D("10.50"),
    ("USD", "2026-06"): D("25.25"),
    ("USD", "2026-07"): D("9007199254740993.01"),
}
UNDATED_EUR = D("7.77")
BY_SERVICE = {
    ("EUR", "Compute"): D("100.00"),
    ("EUR", "Storage"): D("30.00"),
    ("EUR", "Credits"): D("-50.00"),
    ("EUR", None): D("10.00"),
    ("USD", "Compute"): D("10.50"),
    ("USD", "Storage"): D("9007199254741018.26"),
}
BY_SUBSCRIPTION = {
    ("EUR", "synthetic-jup106-sub-a"): D("90.00"),
    ("USD", "synthetic-jup106-sub-b"): D("9007199254741028.76"),
}


class FakeStore:
    """In-memory stand-in with the same contract as SqlStore."""

    def __init__(self, real_runs=(), real_records=()):
        self.runs = {}
        self.records = {}
        self.writes = 0
        for tenant in real_runs:
            self.runs[f"real-run-{tenant}-{len(self.runs)}"] = {"tenant": tenant, "synthetic": False}
        for tenant in real_records:
            self.records[f"real-rec-{tenant}-{len(self.records)}"] = {"tenant": tenant, "synthetic": False}

    def list_synthetic(self):
        return {
            "runs": {key: row["tenant"] for key, row in self.runs.items() if row["synthetic"]},
            "records": {key: row["tenant"] for key, row in self.records.items() if row["synthetic"]},
        }

    def count_real(self, tenant):
        return {
            "runs": sum(1 for row in self.runs.values() if not row["synthetic"] and row["tenant"] == tenant),
            "records": sum(1 for row in self.records.values() if not row["synthetic"] and row["tenant"] == tenant),
        }

    def insert(self, runs, records):
        self.writes += 1
        for run in runs:
            self.runs[run["id"]] = {"tenant": run["tenant_id"], "synthetic": True}
        for record in records:
            self.records[record["id"]] = {"tenant": record["tenant_id"], "synthetic": True}

    def delete_synthetic(self):
        self.writes += 1
        before = (len(self.runs), len(self.records))
        self.records = {k: v for k, v in self.records.items() if not v["synthetic"]}
        self.runs = {k: v for k, v in self.runs.items() if not v["synthetic"]}
        return {"runs": before[0] - len(self.runs), "records": before[1] - len(self.records)}


def month(record):
    return record["usage_date"].strftime("%Y-%m") if record["usage_date"] else None


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.runs, self.records = costs.build_dataset(TENANT)

    def test_dataset_is_identical_on_every_call_and_independent_of_the_clock(self):
        self.assertEqual(costs.build_dataset(TENANT), costs.build_dataset(TENANT))
        other_runs, other_records = costs.build_dataset("tenant-core")
        self.assertEqual({r["id"] for r in other_records}, {r["id"] for r in self.records})
        self.assertTrue(all(r["tenant_id"] == "tenant-core" for r in other_records))
        self.assertEqual({r["created_at"] for r in self.records}, {datetime(2026, 7, 31, tzinfo=timezone.utc)})
        self.assertEqual({r["started_at"] for r in self.runs}, {datetime(2026, 7, 31, tzinfo=timezone.utc)})

    def test_every_identifier_carries_the_reserved_prefix_and_runs_are_marked_synthetic(self):
        self.assertEqual(len({r["id"] for r in self.records}), len(self.records))
        self.assertTrue(all(r["id"].startswith(costs.PREFIX) for r in self.records))
        self.assertTrue(all(r["ingestion_id"].startswith(costs.PREFIX) for r in self.records))
        self.assertTrue(all(r["subscription_id"].startswith(costs.PREFIX) for r in self.records))
        for run in self.runs:
            self.assertTrue(run["id"].startswith(costs.PREFIX))
            self.assertTrue(run["subscription_id"].startswith(costs.PREFIX))
            self.assertIs(run["request"]["synthetic"], True)
            self.assertEqual(run["status"], "completed")
            self.assertEqual(run["row_count"], sum(1 for r in self.records if r["ingestion_id"] == run["id"]))
        self.assertEqual({r["ingestion_id"] for r in self.records}, {run["id"] for run in self.runs})

    def test_required_cases_are_present_in_the_documented_months(self):
        dated = [r for r in self.records if r["usage_date"]]
        zero = [r for r in dated if r["pretax_cost"] == 0]
        self.assertEqual([(r["currency"], month(r)) for r in zero], [("EUR", "2026-02")])
        self.assertEqual({month(r) for r in dated if r["currency"] == "EUR"}, {"2026-01", "2026-02", "2026-04", "2026-05"})
        self.assertEqual({month(r) for r in dated if r["currency"] == "USD"}, {"2026-02", "2026-06", "2026-07"})
        self.assertNotIn("2026-03", {month(r) for r in dated})
        self.assertEqual([r["pretax_cost"] for r in dated if r["pretax_cost"] < 0], [D("-50.00")])
        self.assertEqual({r["currency"] for r in self.records}, {"EUR", "USD"})
        self.assertTrue(any(r["pretax_cost"] > D(2**53) for r in dated))
        self.assertEqual(len([r for r in self.records if r["usage_date"] is None]), 1)

    def test_missing_dimensions_and_resource_group_case_variants(self):
        missing = [r for r in self.records if r["service_name"] is None and r["resource_group"] is None]
        self.assertEqual([(r["currency"], month(r), r["tags"]) for r in missing], [("EUR", "2026-04", {})])
        groups = {r["resource_group"] for r in self.records if r["resource_group"]}
        self.assertIn("Web", groups)
        self.assertIn("web", groups)
        self.assertEqual(len({g.casefold() for g in groups if g.casefold() == "web"}), 1)

    def test_tag_keys_are_canonical_and_every_grouping_has_more_than_one_group(self):
        keys = {key for r in self.records for key in r["tags"]}
        self.assertTrue(keys <= {"cost_center", "environment", "project", "organization"})
        for field in ("service_name", "project", "subscription_id"):
            self.assertGreater(len({r[field] for r in self.records if r[field]}), 1, field)
        self.assertGreater(len({r["tags"].get("cost_center") for r in self.records if r["tags"]}), 1)

    def test_monthly_totals_match_the_hand_written_reference(self):
        totals = defaultdict(lambda: D(0))
        for record in self.records:
            if record["usage_date"]:
                totals[(record["currency"], month(record))] += record["pretax_cost"]
        self.assertEqual(dict(totals), MONTHLY)

    def test_undated_row_is_excluded_from_dated_totals_and_counted_once(self):
        undated = [r for r in self.records if r["usage_date"] is None]
        self.assertEqual([(r["currency"], r["pretax_cost"]) for r in undated], [("EUR", UNDATED_EUR)])

    def test_grouped_totals_match_the_hand_written_reference(self):
        by_service = defaultdict(lambda: D(0))
        by_subscription = defaultdict(lambda: D(0))
        for record in self.records:
            if record["usage_date"]:
                by_service[(record["currency"], record["service_name"])] += record["pretax_cost"]
                by_subscription[(record["currency"], record["subscription_id"])] += record["pretax_cost"]
        self.assertEqual(dict(by_service), BY_SERVICE)
        self.assertEqual(dict(by_subscription), BY_SUBSCRIPTION)

    def test_reference_comparisons_are_the_documented_ones(self):
        def eligible(currency, first, last):
            months = sorted(m for (c, m), v in MONTHLY.items() if c == currency and v != 0 and first <= m <= last)
            return MONTHLY[(currency, months[0])], MONTHLY[(currency, months[-1])], months[0], months[-1]

        first, last, a, b = eligible("EUR", "2026-01", "2026-05")
        self.assertEqual((a, b, last - first, ((last - first) / first * 100).quantize(D("0.01"))), ("2026-01", "2026-05", D("-150.00"), D("-150.00")))
        first, last, a, b = eligible("USD", "2026-01", "2026-06")
        self.assertEqual((a, b, last - first, ((last - first) / first * 100).quantize(D("0.01"))), ("2026-02", "2026-06", D("14.75"), D("140.48")))

    def test_costs_are_exact_decimals_never_floats(self):
        self.assertTrue(all(isinstance(r["pretax_cost"], Decimal) for r in self.records))
        self.assertEqual(max(r["pretax_cost"] for r in self.records), D("9007199254740993.01"))


class ApplyTests(unittest.TestCase):
    def test_load_on_an_empty_database_inserts_the_whole_dataset(self):
        store = FakeStore()
        runs, records = costs.build_dataset(TENANT)
        result = costs.apply(store, TENANT)
        self.assertEqual((result["outcome"], result["runs"], result["records"]), ("loaded", len(runs), len(records)))
        self.assertEqual(set(store.runs), {r["id"] for r in runs})
        self.assertEqual(set(store.records), {r["id"] for r in records})
        self.assertEqual({v["tenant"] for v in store.runs.values()}, {TENANT})

    def test_second_load_changes_nothing_and_reports_already_present(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        writes, snapshot = store.writes, (dict(store.runs), dict(store.records))
        result = costs.apply(store, TENANT)
        self.assertEqual(result["outcome"], "already-present")
        self.assertEqual(store.writes, writes)
        self.assertEqual((store.runs, store.records), snapshot)

    def test_load_is_refused_when_the_tenant_has_real_records(self):
        for kwargs in ({"real_records": [TENANT]}, {"real_runs": [TENANT]}):
            store = FakeStore(**kwargs)
            result = costs.apply(store, TENANT)
            self.assertEqual(result["outcome"], "refused", kwargs)
            self.assertIn("real", result["reason"])
            self.assertEqual(store.writes, 0)
            self.assertFalse(store.list_synthetic()["records"])

    def test_real_data_of_another_tenant_does_not_block_the_load(self):
        store = FakeStore(real_records=["tenant-core", "tenant-core"], real_runs=["tenant-core"])
        self.assertEqual(costs.apply(store, TENANT)["outcome"], "loaded")
        self.assertEqual(store.count_real("tenant-core"), {"runs": 1, "records": 2})

    def test_partial_state_is_reported_and_not_completed_silently(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        victim = sorted(store.records)[0]
        del store.records[victim]
        writes = store.writes
        result = costs.apply(store, TENANT)
        self.assertEqual(result["outcome"], "refused")
        self.assertEqual(result["state"], "partial")
        self.assertIn("remove", result["reason"])
        self.assertEqual(store.writes, writes)
        self.assertNotIn(victim, store.records)

    def test_extra_synthetic_row_in_the_same_tenant_is_partial_too(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        store.records[costs.PREFIX + "extra"] = {"tenant": TENANT, "synthetic": True}
        self.assertEqual(costs.status(store, TENANT)["state"], "partial")

    def test_runs_without_records_or_records_without_runs_are_partial(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        store.records.clear()
        self.assertEqual(costs.status(store, TENANT)["state"], "partial")
        self.assertEqual(costs.apply(store, TENANT)["outcome"], "refused")
        store = FakeStore()
        costs.apply(store, TENANT)
        store.runs.clear()
        self.assertEqual(costs.status(store, TENANT)["state"], "partial")
        self.assertEqual(costs.apply(store, TENANT)["outcome"], "refused")

    def test_records_of_another_tenant_are_detected_even_when_the_runs_match(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        victim = sorted(store.records)[0]
        store.records[victim]["tenant"] = "tenant-core"
        self.assertEqual(costs.status(store, TENANT)["state"], "other-tenant")

    def test_synthetic_rows_of_another_tenant_block_the_load(self):
        store = FakeStore()
        costs.apply(store, "tenant-core")
        writes = store.writes
        result = costs.apply(store, TENANT)
        self.assertEqual((result["outcome"], result["state"]), ("refused", "other-tenant"))
        self.assertEqual(store.writes, writes)

    def test_invalid_tenant_names_are_rejected_before_touching_the_store(self):
        for tenant in ("", " ", "Tenant", "a b", "x'; DROP TABLE azure_cost_records;--", "t" * 80):
            store = FakeStore()
            with self.assertRaises(ValueError, msg=repr(tenant)):
                costs.apply(store, tenant)
            self.assertEqual(store.writes, 0)


class StatusAndRemoveTests(unittest.TestCase):
    def test_status_states(self):
        store = FakeStore()
        self.assertEqual(costs.status(store, TENANT)["state"], "absent")
        costs.apply(store, TENANT)
        report = costs.status(store, TENANT)
        runs, records = costs.build_dataset(TENANT)
        self.assertEqual((report["state"], report["runs"], report["records"]), ("present", len(runs), len(records)))
        self.assertEqual(report["real_runs"] + report["real_records"], 0)

    def test_status_reports_real_rows_of_the_tenant(self):
        store = FakeStore(real_records=[TENANT, "tenant-core"], real_runs=[TENANT])
        report = costs.status(store, TENANT)
        self.assertEqual((report["real_runs"], report["real_records"]), (1, 1))

    def test_remove_deletes_only_synthetic_rows(self):
        store = FakeStore(real_records=[TENANT, "tenant-core"], real_runs=["tenant-core"])
        self.assertEqual(costs.apply(store, "tenant-other")["outcome"], "loaded")
        real_before = ({k for k, v in store.runs.items() if not v["synthetic"]}, {k for k, v in store.records.items() if not v["synthetic"]})
        result = costs.remove(store)
        runs, records = costs.build_dataset("tenant-other")
        self.assertEqual((result["runs"], result["records"]), (len(runs), len(records)))
        self.assertEqual((set(store.runs), set(store.records)), real_before)

    def test_load_then_remove_restores_the_previous_state(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        costs.remove(store)
        self.assertEqual((store.runs, store.records), ({}, {}))
        self.assertEqual(costs.status(store, TENANT)["state"], "absent")

    def test_remove_with_nothing_to_remove_succeeds(self):
        store = FakeStore(real_records=[TENANT])
        result = costs.remove(store)
        self.assertEqual((result["runs"], result["records"]), (0, 0))
        self.assertEqual(len(store.records), 1)

    def test_remove_works_even_when_the_tenant_has_real_data(self):
        store = FakeStore()
        costs.apply(store, TENANT)
        store.records["real-late"] = {"tenant": TENANT, "synthetic": False}
        costs.remove(store)
        self.assertEqual(set(store.records), {"real-late"})


class CommandLineTests(unittest.TestCase):
    def run_cli(self, argv, env, store=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = costs.main(argv, env=env, store_factory=lambda url: store if store is not None else FakeStore())
        return code, out.getvalue()

    def test_apply_status_remove_exit_codes(self):
        store = FakeStore()
        env = {"DATABASE_URL": "cockroachdb://u:pw@host/db"}
        self.assertEqual(self.run_cli(["apply"], env, store)[0], 0)
        self.assertEqual(self.run_cli(["apply"], env, store)[0], 0)
        self.assertEqual(self.run_cli(["status"], env, store)[0], 0)
        self.assertEqual(self.run_cli(["remove"], env, store)[0], 0)
        self.assertEqual(self.run_cli(["remove"], env, store)[0], 0)

    def test_refusals_exit_with_a_non_zero_code_and_write_nothing(self):
        store = FakeStore(real_records=[TENANT])
        code, text = self.run_cli(["apply"], {"DATABASE_URL": "cockroachdb://u:pw@host/db"}, store)
        self.assertEqual(code, 2)
        self.assertIn("real", text)
        self.assertEqual(store.writes, 0)

    def test_missing_database_url_fails_cleanly(self):
        code, text = self.run_cli(["apply"], {})
        self.assertEqual(code, 2)
        self.assertIn("DATABASE_URL", text)

    def test_the_connection_string_is_never_printed(self):
        secret = "cockroachdb://user:S3cr3tPassw0rd@host/db"
        for argv in (["apply"], ["status"], ["remove"], ["apply", "--tenant", "Bad Tenant"]):
            code, text = self.run_cli(argv, {"DATABASE_URL": secret})
            self.assertNotIn("S3cr3tPassw0rd", text, argv)

        def exploding(url):
            raise RuntimeError("could not connect to " + url)

        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = costs.main(["status"], env={"DATABASE_URL": secret}, store_factory=exploding)
        self.assertEqual(code, 2)
        self.assertNotIn("S3cr3tPassw0rd", out.getvalue())

    def test_tenant_argument_and_default(self):
        store = FakeStore()
        env = {"DATABASE_URL": "x://y"}
        self.run_cli(["apply", "--tenant", "tenant-core"], env, store)
        self.assertEqual({v["tenant"] for v in store.runs.values()}, {"tenant-core"})
        store = FakeStore()
        self.run_cli(["apply"], env, store)
        self.assertEqual({v["tenant"] for v in store.runs.values()}, {TENANT})

    def test_unknown_command_is_rejected(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                costs.main(["drop"], env={"DATABASE_URL": "x://y"}, store_factory=lambda url: FakeStore())


class RecordingEngine:
    def __init__(self):
        self.statements = []
        self.params = []

    def begin(self):
        engine = self

        class Connection:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, statement, params=None):
                engine.statements.append(str(statement))
                engine.params.append(params)

                class Result:
                    def mappings(self_inner):
                        return self_inner

                    def all(self_inner):
                        return []

                    def one(self_inner):
                        return {"runs": 0, "records": 0}

                    rowcount = 0

                return Result()

        return Connection()

    connect = begin


class SqlStoreTests(unittest.TestCase):
    def test_statements_use_bound_parameters_for_every_value(self):
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            self.skipTest("sqlalchemy is not installed")
        engine = RecordingEngine()
        store = costs.SqlStore(engine=engine)
        runs, records = costs.build_dataset("tenant-x")
        store.insert(runs, records)
        store.count_real("tenant-x'; DROP TABLE azure_cost_records;--")
        store.list_synthetic()
        store.delete_synthetic()
        joined = "\n".join(engine.statements)
        self.assertNotIn("DROP TABLE", joined)
        self.assertNotIn("tenant-x", joined)
        self.assertNotIn("9007199254740993", joined)
        self.assertNotIn(costs.PREFIX + "run", joined.replace(":prefix", ""))
        self.assertIn("azure_cost_records", joined)


@unittest.skipUnless(os.environ.get("JUP086_COCKROACH_TEST_URL"), "JUP086_COCKROACH_TEST_URL is not set")
class CockroachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, text

        cls.text = staticmethod(text)
        cls.url = os.environ["JUP086_COCKROACH_TEST_URL"]
        env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; from app.db.database import Database; db = Database(sys.argv[1]); db.initialize(); db.dispose()", cls.url],
            cwd=ROOT / "apps" / "processor", env=env, check=True, capture_output=True, text=True, timeout=120,
        )
        cls.engine = create_engine(cls.url, future=True)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        with self.engine.begin() as connection:
            connection.execute(self.text("DELETE FROM azure_cost_records"))
            connection.execute(self.text("DELETE FROM azure_cost_ingestion_runs"))
        self.store = costs.SqlStore(engine=self.engine)

    def sums(self, tenant):
        with self.engine.connect() as connection:
            rows = connection.execute(self.text(
                "SELECT currency, to_char(usage_date, 'YYYY-MM') AS month, SUM(pretax_cost)::STRING AS total "
                "FROM azure_cost_records WHERE tenant_id = :tenant AND usage_date IS NOT NULL GROUP BY 1, 2"
            ), {"tenant": tenant}).mappings().all()
        return {(row["currency"], row["month"]): D(row["total"]) for row in rows}

    def test_load_matches_the_reference_and_remove_restores_the_empty_state(self):
        result = costs.apply(self.store, TENANT)
        runs, records = costs.build_dataset(TENANT)
        self.assertEqual((result["outcome"], result["runs"], result["records"]), ("loaded", len(runs), len(records)))
        self.assertEqual(self.sums(TENANT), MONTHLY)
        with self.engine.connect() as connection:
            undated = connection.execute(self.text(
                "SELECT count(*) AS n, SUM(pretax_cost)::STRING AS total FROM azure_cost_records "
                "WHERE tenant_id = :tenant AND usage_date IS NULL"), {"tenant": TENANT}).mappings().one()
            statuses = connection.execute(self.text(
                "SELECT DISTINCT status FROM azure_cost_ingestion_runs WHERE tenant_id = :tenant"), {"tenant": TENANT}).all()
            flagged = connection.execute(self.text(
                "SELECT count(*) FROM azure_cost_ingestion_runs WHERE request->>'synthetic' = 'true'")).scalar()
        self.assertEqual((undated["n"], D(undated["total"])), (1, UNDATED_EUR))
        self.assertEqual([row[0] for row in statuses], ["completed"])
        self.assertEqual(flagged, len(runs))
        self.assertEqual(costs.apply(self.store, TENANT)["outcome"], "already-present")
        self.assertEqual(costs.status(self.store, TENANT)["state"], "present")
        costs.remove(self.store)
        self.assertEqual(self.sums(TENANT), {})
        self.assertEqual(costs.status(self.store, TENANT)["state"], "absent")

    def test_real_rows_are_protected_on_load_and_survive_removal(self):
        real = uuid.uuid4().hex
        with self.engine.begin() as connection:
            connection.execute(self.text(
                "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
                "VALUES (:id, :tenant, 'real-sub', '{}'::JSONB, 'completed', now())"), {"id": "run-" + real, "tenant": TENANT})
            connection.execute(self.text(
                "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, currency, "
                "dimensions, source_row_hash, created_at) VALUES (:id, :run, :tenant, 'real-sub', '2026-03-01', 5, 'EUR', "
                "'{}'::JSONB, :id, now())"), {"id": "rec-" + real, "run": "run-" + real, "tenant": TENANT})
        self.assertEqual(costs.apply(self.store, TENANT)["outcome"], "refused")
        self.assertEqual(costs.status(self.store, TENANT)["state"], "absent")
        costs.apply(self.store, "tenant-core")
        costs.remove(self.store)
        with self.engine.connect() as connection:
            left = connection.execute(self.text("SELECT count(*) FROM azure_cost_records")).scalar()
        self.assertEqual(left, 1)

    def test_rows_that_only_look_synthetic_are_real_and_survive_removal(self):
        with self.engine.begin() as connection:
            connection.execute(self.text(
                "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
                "VALUES (:id, :tenant, 'real-sub', '{}'::JSONB, 'completed', now())"), {"id": costs.PREFIX + "imposter", "tenant": TENANT})
            connection.execute(self.text(
                "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, currency, "
                "dimensions, source_row_hash, created_at) VALUES (:id, :run, :tenant, 'real-sub', '2026-03-01', 5, 'EUR', "
                "'{}'::JSONB, :id, now())"), {"id": costs.PREFIX + "imposter-rec", "run": costs.PREFIX + "imposter", "tenant": TENANT})
            connection.execute(self.text(
                "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
                "VALUES ('flagged-without-prefix', :tenant, 'real-sub', '{\"synthetic\": true}'::JSONB, 'completed', now())"), {"tenant": TENANT})
        report = costs.status(self.store, TENANT)
        self.assertEqual((report["state"], report["real_runs"], report["real_records"]), ("absent", 2, 1))
        self.assertEqual(costs.apply(self.store, TENANT)["outcome"], "refused")
        costs.remove(self.store)
        with self.engine.connect() as connection:
            left = connection.execute(self.text(
                "SELECT (SELECT count(*) FROM azure_cost_ingestion_runs), (SELECT count(*) FROM azure_cost_records)")).one()
        self.assertEqual(tuple(left), (2, 1))

    def test_every_loaded_record_is_marked_synthetic_in_its_dimensions(self):
        costs.apply(self.store, TENANT)
        with self.engine.connect() as connection:
            marked = connection.execute(self.text(
                "SELECT count(*) FROM azure_cost_records WHERE dimensions->>'synthetic' = 'true'")).scalar()
        self.assertEqual(marked, len(costs.build_dataset(TENANT)[1]))

    def test_partial_state_is_detected_in_the_database(self):
        costs.apply(self.store, TENANT)
        with self.engine.begin() as connection:
            connection.execute(self.text("DELETE FROM azure_cost_records WHERE id = (SELECT min(id) FROM azure_cost_records)"))
        self.assertEqual(costs.apply(self.store, TENANT)["state"], "partial")


if __name__ == "__main__":
    unittest.main()
