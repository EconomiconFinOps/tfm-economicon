"""Frescura y reconciliación de los datos de coste de `tools/memory-indicators.py` (JUP-130, grupo 3)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "memory-indicators.py"
SPEC = importlib.util.spec_from_file_location("economicon_memory_indicators_data", TOOL_PATH)
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

DASHBOARD = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_for_jup130_data", ROOT / "tools" / "evaluation-dashboard.py")
dashboard = importlib.util.module_from_spec(DASHBOARD)
sys.modules[DASHBOARD.name] = dashboard
DASHBOARD.loader.exec_module(dashboard)


def rows(report, metric_id, behavior=None):
    return [r for r in report["results"] if r["metric_id"] == metric_id and (behavior is None or r["behavior"] == behavior)]


def one(report, metric_id, behavior):
    found = rows(report, metric_id, behavior)
    assert len(found) == 1, (metric_id, behavior, found)
    return found[0]


class Source:
    """Fuente sintética: coste por (inquilino, día, divisa) como `Decimal`."""

    def __init__(self, records):
        self.records = records


def fake_api(records, reference="2026-10-30", reachable=True):
    """Imita GET /billing/summary: solo devuelve registros hasta la fecha de referencia, por inquilino."""
    def fetch(tenant, start, end):
        if not reachable:
            raise tool.ApiUnavailable("conexión")
        totals = {}
        for (owner, day, currency), cost in records.items():
            if owner == tenant and start <= day < end and day <= date.fromisoformat(reference):
                total, count = totals.get(currency, (Decimal(0), 0))
                totals[currency] = (total + cost, count + 1)
        return [{"currency": c, "cost": format(t, "f"), "record_count": n} for c, (t, n) in sorted(totals.items())]
    return fetch


def records(tenant="tenant-core", first="2026-10-01", last="2026-10-05", currency="EUR", cost="10.00", skip=()):
    out, day = {}, date.fromisoformat(first)
    while day <= date.fromisoformat(last):
        if day.isoformat() not in skip:
            out[(tenant, day, currency)] = Decimal(cost)
        day += timedelta(days=1)
    return out


class Freshness(unittest.TestCase):
    def freshness(self, data, reference="2026-10-30", api=None):
        api = api or fake_api(data, reference)
        return tool.freshness_days(api, "tenant-core", date.fromisoformat(reference), date(2026, 7, 1))

    def test_data_up_to_the_reference_day_is_zero_days_old(self):
        self.assertEqual(self.freshness(records(last="2026-10-30")), 0)

    def test_data_ending_the_day_before_is_one_day_old(self):
        self.assertEqual(self.freshness(records(last="2026-10-29")), 1)

    def test_data_ending_five_days_before_is_five_days_old(self):
        self.assertEqual(self.freshness(records(last="2026-10-25")), 5)

    def test_a_gap_before_the_last_day_does_not_change_the_age(self):
        self.assertEqual(self.freshness(records(first="2026-10-01", last="2026-10-28", skip=("2026-10-10", "2026-10-11"))), 2)

    def test_a_tenant_without_records_has_no_freshness(self):
        self.assertIsNone(self.freshness({}))

    def test_a_single_record_on_the_window_start_is_found(self):
        self.assertEqual(self.freshness({("tenant-core", date(2026, 7, 1), "EUR"): Decimal(1)}), 121)

    def test_data_after_the_reference_day_is_not_visible_so_it_does_not_make_the_data_fresher(self):
        data = records(first="2026-10-20", last="2026-11-10")
        self.assertEqual(self.freshness(data, reference="2026-10-25"), 0)

    def test_the_search_uses_few_requests(self):
        calls = []
        inner = fake_api(records(last="2026-09-01"))

        def counting(tenant, start, end):
            calls.append((start, end))
            return inner(tenant, start, end)
        tool.freshness_days(counting, "tenant-core", date(2026, 10, 30), date(2026, 7, 1))
        self.assertLessEqual(len(calls), 9)


class SourceSums(unittest.TestCase):
    def test_the_demo_sums_exactly_per_tenant_and_currency(self):
        totals = tool.source_totals(date(2026, 10, 30))
        self.assertEqual(sorted(totals), ["tenant-core", "tenant-growth"])
        self.assertEqual(set(totals["tenant-core"]), {"EUR"})
        self.assertEqual(set(totals["tenant-growth"]), {"EUR", "USD"})
        self.assertIsInstance(totals["tenant-core"]["EUR"], Decimal)

    def test_a_later_reference_date_excludes_later_rows_like_the_api(self):
        early = tool.source_totals(date(2026, 9, 1))["tenant-core"]["EUR"]
        late = tool.source_totals(date(2026, 10, 30))["tenant-core"]["EUR"]
        self.assertLess(early, late)

    def test_the_big_integer_of_the_demo_does_not_lose_a_cent(self):
        usd = tool.source_totals(date(2026, 10, 30))["tenant-growth"]["USD"]
        self.assertGreater(usd, Decimal("9007199254740993.00"))
        self.assertEqual(tool.round_money(usd), Decimal("9007199254741838.37"))

    def test_the_public_rows_carry_sub_cent_costs_so_the_exact_sum_is_not_in_minor_units(self):
        usd = tool.source_totals(date(2026, 10, 30))["tenant-growth"]["USD"]
        self.assertNotEqual(usd, usd.quantize(Decimal("0.01")))


class MoneyRounding(unittest.TestCase):
    def test_it_rounds_half_up_once_to_two_places(self):
        for exact, wanted in (("50.005", "50.01"), ("50.004", "50.00"), ("0.015", "0.02"), ("-0.005", "-0.01"),
                              ("-0.015", "-0.02"), ("9007199254740993.004", "9007199254740993.00")):
            self.assertEqual(tool.round_money(Decimal(exact)), Decimal(wanted), exact)

    def test_negative_zero_is_zero(self):
        self.assertEqual(str(tool.round_money(Decimal("-0.001"))), "0.00")


class Reconciliation(unittest.TestCase):
    def reconcile(self, source, api_records, reference="2026-10-30"):
        return tool.reconcile(source, fake_api(api_records, reference), "tenant-core", date(2026, 7, 1), date.fromisoformat(reference))

    def test_equal_totals_reconcile_with_zero_delta(self):
        data = records()
        result = self.reconcile({"EUR": Decimal("50.00")}, data)
        self.assertEqual(result, {"EUR": 0})

    def test_a_one_cent_difference_is_not_reconciled(self):
        data = records()
        self.assertEqual(self.reconcile({"EUR": Decimal("50.01")}, data), {"EUR": 1})

    def test_a_negative_difference_keeps_its_sign(self):
        self.assertEqual(self.reconcile({"EUR": Decimal("49.99")}, records()), {"EUR": -1})

    def test_two_currencies_are_reconciled_separately_and_never_offset(self):
        data = {**records(currency="EUR"), **records(currency="USD")}
        result = self.reconcile({"EUR": Decimal("50.01"), "USD": Decimal("49.99")}, data)
        self.assertEqual(result, {"EUR": 1, "USD": -1})

    def test_a_currency_missing_from_the_api_shows_the_whole_source_as_difference(self):
        self.assertEqual(self.reconcile({"USD": Decimal("12.34")}, records(currency="EUR"))["USD"], 1234)

    def test_a_currency_only_in_the_api_is_compared_with_zero(self):
        self.assertEqual(self.reconcile({}, records(currency="EUR")), {"EUR": -5000})

    def test_sub_cent_costs_are_summed_exactly_and_rounded_once_like_the_api(self):
        self.assertEqual(self.reconcile({"EUR": Decimal("50.005")}, records()), {"EUR": 1})
        self.assertEqual(self.reconcile({"EUR": Decimal("50.004")}, records()), {"EUR": 0})

    def test_rounding_each_row_would_give_another_answer_than_rounding_the_sum(self):
        self.assertEqual(sum(tool.round_money(Decimal("0.004")) for _ in range(3)), Decimal("0.00"))
        self.assertEqual(tool.round_money(Decimal("0.004") * 3), Decimal("0.01"))

    def test_the_api_total_is_read_as_an_exact_decimal_string(self):
        big = {("tenant-core", date(2026, 10, 1), "USD"): Decimal("9007199254740993.01")}
        result = tool.reconcile({"USD": Decimal("9007199254740993.01")}, fake_api(big), "tenant-core", date(2026, 7, 1), date(2026, 10, 30))
        self.assertEqual(result, {"USD": 0})

    def test_a_difference_beyond_the_safe_integer_is_an_error(self):
        with self.assertRaises(tool.IndicatorError):
            self.reconcile({"USD": Decimal("90071992547409.93")}, {})

    def test_an_unreachable_api_raises_instead_of_declaring_a_reconciliation(self):
        with self.assertRaises(tool.ApiUnavailable):
            self.reconcile({"EUR": Decimal("50.00")}, records(), reference="2026-10-30") if False else tool.reconcile(
                {"EUR": Decimal("50.00")}, fake_api({}, reachable=False), "tenant-core", date(2026, 7, 1), date(2026, 10, 30))


class DataReport(unittest.TestCase):
    def report(self, **kwargs):
        defaults = {"reference": date(2026, 10, 30), "commit": None, "run_at": None}
        return tool.data_report(**{**defaults, **kwargs})

    def test_a_reachable_api_that_matches_the_source_reconciles_every_tenant_and_currency(self):
        source = tool.source_totals(date(2026, 10, 30))
        api = self.full_api(source)
        report, _ = self.report(fetch=api, reference_date_from_api=date(2026, 10, 30))
        for tenant, totals in source.items():
            for currency in totals:
                behavior = f"{tenant}/{currency}"
                self.assertEqual(one(report, "reconciliation_delta_minor", behavior)["value"], 0)
                self.assertEqual(one(report, "reconciled", behavior)["value"], 1)

    def full_api(self, source):
        def fetch(tenant, start, end):
            return [{"currency": c, "cost": format(t, "f"), "record_count": 1} for c, t in sorted(source[tenant].items())]
        return fetch

    def test_a_one_cent_gap_makes_reconciled_zero_for_that_currency_only(self):
        source = tool.source_totals(date(2026, 10, 30))

        def fetch(tenant, start, end):
            items = self.full_api(source)(tenant, start, end)
            if tenant == "tenant-core":
                items[0]["cost"] = format(Decimal(items[0]["cost"]) - Decimal("0.01"), "f")
            return items
        report, _ = self.report(fetch=fetch, reference_date_from_api=date(2026, 10, 30))
        self.assertEqual(one(report, "reconciled", "tenant-core/EUR")["value"], 0)
        self.assertEqual(one(report, "reconciliation_delta_minor", "tenant-core/EUR")["value"], 1)
        self.assertEqual(one(report, "reconciled", "tenant-growth/EUR")["value"], 1)

    def test_without_api_the_reconciliation_is_not_measured_and_never_true(self):
        report, table = self.report(fetch=None, reference_date_from_api=None)
        for metric in ("reconciliation_delta_minor", "reconciled", "freshness_days"):
            for row in rows(report, metric):
                self.assertEqual(row["status"], "not_measured", metric)
        self.assertEqual([r for r in rows(report, "reconciled") if r["status"] == "measured"], [])
        self.assertIn("no medido", table)

    def test_missing_days_come_from_the_source_and_are_never_counted_as_zero_cost(self):
        report, _ = self.report(fetch=None, reference_date_from_api=None)
        core = one(report, "source_missing_days", "tenant-core")
        self.assertEqual(core["status"], "measured")
        self.assertEqual(core["unit"], "dias")

    def test_the_report_passes_the_common_contract_with_type_b_and_the_data_group(self):
        report, _ = self.report(fetch=None, reference_date_from_api=None)
        run, results = dashboard.adapt_rows_v1(report)
        self.assertEqual(run["source"], "JUP-130")
        self.assertTrue(all(r["measure_type"] == "B" and r["grp"] == "data_quality" and r["judgment"] is None for r in results))

    def test_the_table_declares_the_source_and_what_it_does_not_prove(self):
        _, table = self.report(fetch=None, reference_date_from_api=None)
        for phrase in ("sintético", "no demuestra", "datos reales de Azure",
                       "python tools/memory-indicators.py data --reference 2026-10-30"):
            self.assertIn(phrase, table)

    def test_two_runs_are_identical_byte_for_byte(self):
        first = self.report(fetch=None, reference_date_from_api=None)
        second = self.report(fetch=None, reference_date_from_api=None)
        self.assertEqual(json.dumps(first[0]), json.dumps(second[0]))
        self.assertEqual(first[1], second[1])


class Command(unittest.TestCase):
    def run_tool(self, *args, env=None):
        import os
        environment = {**os.environ, **(env or {})}
        environment.pop("DEMO_PASSWORD", None) if not env or "DEMO_PASSWORD" not in env else None
        return subprocess.run([sys.executable, str(TOOL_PATH), *args], capture_output=True, text=True, encoding="utf-8",
                              cwd=ROOT, env=environment)

    def test_without_a_base_url_it_writes_a_not_measured_report(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("data", "--reference", "2026-10-30", "--out", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-data.rows.json").read_text("utf-8"))
            self.assertTrue(all(r["status"] != "measured" or r["metric_id"] == "source_missing_days" for r in report["results"]))

    def test_an_unreachable_api_gives_not_measured_and_no_password_in_the_output(self):
        secret = "contraseña-de-prueba-JUP130"
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("data", "--reference", "2026-10-30", "--out", directory, "--base-url",
                                   "http://127.0.0.1:9", "--email", "operator@example.com", env={"DEMO_PASSWORD": secret})
            self.assertEqual(result.returncode, 0, result.stderr)
            written = (Path(directory) / "JUP-130-data.rows.json").read_text("utf-8") + (Path(directory) / "JUP-130-data.md").read_text("utf-8")
            for text in (result.stdout, result.stderr, written):
                self.assertNotIn(secret, text)
            report = json.loads((Path(directory) / "JUP-130-data.rows.json").read_text("utf-8"))
            self.assertEqual([r for r in report["results"] if r["metric_id"] == "reconciled" and r["status"] == "measured"], [])

    def test_a_base_url_without_http_is_a_usage_error(self):
        result = self.run_tool("data", "--reference", "2026-10-30", "--base-url", "ftp://x")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
