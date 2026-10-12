from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "synthetic_anomalies.py"
COSTS_PATH = ROOT / "scripts" / "synthetic_costs.py"
EXPECTED_PATH = ROOT / "docs" / "demo" / "JUP-107" / "esperados-anomalias.json"
GUIDE_PATH = ROOT / "docs" / "demo" / "JUP-107" / "anomalias.md"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


anomalies = load("economicon_synthetic_anomalies", SCRIPT_PATH)
costs = load("economicon_synthetic_costs_for_anomalies", COSTS_PATH)

D = Decimal
TENANT = "tenant-core"


def cents(value: Decimal) -> Decimal:
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def independent_rules(current: Decimal, baseline, threshold: Decimal, percent: Decimal, minimum: Decimal) -> dict:
    """The rules of docs/api/cost-anomalies.md written again from the contract, not from the backend."""
    reasons = []
    absolute = "triggered" if current >= threshold else "below"
    if absolute == "triggered":
        reasons.append("absolute_threshold")
    if baseline is None:
        deviation = "baseline_missing"
    elif baseline <= 0:
        deviation = "baseline_nonpositive"
    elif current - baseline >= minimum and (current - baseline) * 100 >= baseline * percent:
        deviation = "triggered"
        reasons.append("period_increase")
    else:
        deviation = "below"
    delta = None if baseline is None else cents(current - baseline)
    shown = None if baseline is None or baseline <= 0 else cents((current - baseline) * 100 / baseline)
    return {"threshold_status": absolute, "deviation_status": deviation, "trigger_reasons": reasons,
            "delta_amount": delta, "deviation_percent": shown}


def check_expected(records, expected) -> list[str]:
    """Return one message per figure of the expected file that the records do not reproduce."""
    problems: list[str] = []
    periods = {name: (date.fromisoformat(p["start"]), date.fromisoformat(p["end"])) for name, p in expected["periods"].items()}
    rules = expected["rules"]
    threshold, percent, minimum = D(rules["absolute_threshold"]), D(rules["deviation_threshold_percent"]), D(rules["min_absolute_increase"])
    by_group: dict[tuple[str, str], list[Decimal]] = {}
    for record in records:
        if record["currency"] != expected["currency"]:
            continue
        for name, (start, end) in periods.items():
            if start <= record["usage_date"] < end:
                by_group.setdefault((record["service_name"], name), []).append(record["pretax_cost"])
    alerts = []
    for group in expected["groups"]:
        service = group["service"]
        sums = {}
        for name in ("baseline", "current"):
            amounts = by_group.get((service, name))
            sums[name] = None if amounts is None else sum(amounts, D("0"))
            expected_total = group[f"{name}_cost"]
            expected_count = group[f"{name}_record_count"]
            if (None if expected_total is None else D(expected_total)) != sums[name]:
                problems.append(f"{service} {name}: total {sums[name]} differs from expected {expected_total}")
            count = None if amounts is None else len(amounts)
            if count != expected_count:
                problems.append(f"{service} {name}: {count} records differ from expected {expected_count}")
        if sums["current"] is None:
            problems.append(f"{service} current: no records")
            continue
        outcome = independent_rules(sums["current"], sums["baseline"], threshold, percent, minimum)
        for key, value in outcome.items():
            wanted = group[key]
            if key in ("delta_amount", "deviation_percent"):
                wanted = None if wanted is None else D(wanted)
            if wanted != value:
                problems.append(f"{service}: {key} is {value} but the file says {wanted}")
        if outcome["trigger_reasons"]:
            alerts.append(service)
    if sorted(alerts) != sorted(expected["alerts"]):
        problems.append(f"alerts {sorted(alerts)} differ from expected {sorted(expected['alerts'])}")
    return problems


def independent_episodes(records) -> list[dict]:
    """The JUP-019 daily rule of docs/api/anomaly-episodes.md written again with fractions, not from the backend."""
    from fractions import Fraction

    daily: dict[str, dict[date, Fraction]] = {}
    observed = set()
    for record in records:
        if record["currency"] != "EUR":
            continue
        day = record["usage_date"]
        observed.add(day)
        service = daily.setdefault(record["service_name"], {})
        service[day] = service.get(day, Fraction(0)) + Fraction(record["pretax_cost"])
    last_complete = max(observed) - timedelta(days=1)
    tracking, episodes = {}, []
    day = min(observed)
    while day <= last_complete:
        previous = [day - timedelta(days=offset) for offset in range(1, 8)]
        if day in observed and all(item in observed for item in previous):
            for service in sorted(daily):
                values = daily[service]
                observed_cost = values.get(day, Fraction(0))
                episode = tracking.get(service)
                reference = episode["reference"] if episode else sum((values.get(item, Fraction(0)) for item in previous), Fraction(0)) / 7
                hit = reference > 0 and observed_cost - reference > 100 and (observed_cost - reference) * 100 > reference * 20
                if episode:
                    if not hit and (day - episode["last_seen_date"]).days > 3:
                        episode["observation"], episode["no_longer_observed_on"] = "no_longer_observed", day
                        del tracking[service]
                    else:
                        if hit:
                            episode["last_seen_date"] = day
                        episode["impact"] += max(Fraction(0), observed_cost - reference)
                        episode["impact_day_count"] += 1
                elif hit:
                    episode = {"service": service, "start_date": day, "last_seen_date": day, "observation": "observed",
                               "no_longer_observed_on": None, "reference": reference,
                               "impact": observed_cost - reference, "impact_day_count": 1}
                    tracking[service] = episode
                    episodes.append(episode)
        day += timedelta(days=1)

    def shown(value):
        return format(cents(D(value.numerator) / D(value.denominator)), "f")

    result = []
    for episode in episodes:
        impact = episode["impact"]
        severity = "P1" if impact > 2000 else "P2" if impact >= 500 else "P3"
        result.append({
            "service": episode["service"], "start_date": episode["start_date"].isoformat(),
            "last_seen_date": episode["last_seen_date"].isoformat(), "observation": episode["observation"],
            "no_longer_observed_on": episode["no_longer_observed_on"].isoformat() if episode["no_longer_observed_on"] else None,
            "reference_daily_cost": shown(episode["reference"]), "accumulated_impact": shown(impact),
            "impact_day_count": episode["impact_day_count"], "severity": severity,
        })
    order = {"P1": 0, "P2": 1, "P3": 2}
    return sorted(result, key=lambda item: (order[item["severity"]], -D(item["accumulated_impact"])))


class FakeStore:
    """In-memory stand-in with the contract of SqlStore, shared between the two tools through one dict."""

    def __init__(self, prefix: str, rows: dict | None = None, hanging: int = 0):
        self.prefix = prefix
        self.rows = {"runs": {}, "records": {}} if rows is None else rows
        self.rows.setdefault("episodes", {})
        self.hanging = hanging
        self.writes = 0

    def add_episodes(self, tenant: str, count: int = 2):
        self.rows["episodes"][tenant] = count

    def count_episodes(self, tenant):
        return self.rows["episodes"].get(tenant, 0)

    def add_foreign(self, kind: str, tenant: str, identifier: str = "foreign-1"):
        self.rows[kind][identifier] = {"tenant": tenant, "prefix_ok": False}

    def _mine(self, kind: str):
        return {k: v["tenant"] for k, v in self.rows[kind].items() if k.startswith(self.prefix)}

    def list_synthetic(self):
        return {"runs": self._mine("runs"), "records": self._mine("records")}

    def count_real(self, tenant):
        return {kind: sum(1 for k, v in self.rows[kind].items() if v["tenant"] == tenant and not k.startswith(self.prefix))
                for kind in ("runs", "records")}

    def insert(self, runs, records):
        for tenant in {run["tenant_id"] for run in runs}:
            if sum(self.count_real(tenant).values()):
                raise anomalies.RealDataError("real data appeared")
        self.writes += 1
        for run in runs:
            self.rows["runs"][run["id"]] = {"tenant": run["tenant_id"]}
        for record in records:
            self.rows["records"][record["id"]] = {"tenant": record["tenant_id"]}

    def count_attached(self):
        return self.hanging

    def delete_synthetic(self):
        self.writes += 1
        tenants = set(self._mine("runs").values())
        deleted = {}
        for kind in ("runs", "records"):
            keys = [k for k in self.rows[kind] if k.startswith(self.prefix)]
            for key in keys:
                del self.rows[kind][key]
            deleted[kind] = len(keys)
        deleted["episodes"], deleted["kept_episode_tenants"] = 0, []
        for tenant in sorted(tenants):
            if sum(self.count_real(tenant).values()):
                if self.rows["episodes"].get(tenant):
                    deleted["kept_episode_tenants"].append(tenant)
                continue
            deleted["episodes"] += self.rows["episodes"].pop(tenant, 0)
        return deleted


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        self.runs, self.records = anomalies.build_dataset(TENANT)

    def test_dataset_is_identical_on_every_call_and_independent_of_the_clock(self):
        self.assertEqual(anomalies.build_dataset(TENANT), anomalies.build_dataset(TENANT))
        self.assertEqual({r["created_at"] for r in self.records}, {datetime(2026, 9, 15, tzinfo=timezone.utc)})

    def test_one_completed_synthetic_run_with_reserved_prefix_everywhere(self):
        self.assertEqual(anomalies.PREFIX, "synthetic-jup107-")
        self.assertEqual(anomalies.DEFAULT_TENANT, "tenant-core")
        self.assertEqual(len(self.runs), 1)
        run = self.runs[0]
        self.assertTrue(run["id"].startswith(anomalies.PREFIX))
        self.assertTrue(run["subscription_id"].startswith(anomalies.PREFIX))
        self.assertIs(run["request"]["synthetic"], True)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["row_count"], len(self.records))
        self.assertEqual(len({r["id"] for r in self.records}), len(self.records))
        for record in self.records:
            self.assertTrue(record["id"].startswith(anomalies.PREFIX))
            self.assertEqual(record["ingestion_id"], run["id"])
            self.assertEqual(record["currency"], "EUR")
            self.assertTrue(record["service_name"])
            self.assertEqual(record["tenant_id"], TENANT)

    def test_periods_are_consecutive_equal_and_every_record_is_in_the_data_range(self):
        base, cur = (self.expected["periods"][n] for n in ("baseline", "current"))
        b0, b1, c0, c1 = (date.fromisoformat(x) for x in (base["start"], base["end"], cur["start"], cur["end"]))
        self.assertEqual(b1, c0)
        self.assertEqual(b1 - b0, c1 - c0)
        self.assertEqual((c1 - c0).days, 7)
        first, last = (date.fromisoformat(self.expected["data_range"][k]) for k in ("first_day", "last_day"))
        self.assertEqual(first, b0)
        for record in self.records:
            self.assertTrue(first <= record["usage_date"] <= last, record["id"])
        self.assertEqual(max(r["usage_date"] for r in self.records), last)

    def test_one_record_per_service_and_day_except_networking_before_it_appears(self):
        seen = {}
        for record in self.records:
            key = (record["service_name"], record["usage_date"])
            self.assertNotIn(key, seen, key)
            seen[key] = record
        days = [date(2026, 9, 1) + timedelta(days=n) for n in range(21)]
        for service in ("Compute", "Analytics", "Storage", "Database", "Tools", "Backup"):
            self.assertEqual([d for d in days if (service, d) in seen], days, service)
        self.assertEqual(min(d for (s, d) in seen if s == "Networking"), date(2026, 9, 14))
        self.assertEqual(len(self.records), 6 * 21 + 8)

    def test_one_detection_opens_exactly_the_expected_episodes(self):
        self.assertEqual(independent_episodes(self.records), self.expected["episodes"])
        services = {episode["service"] for episode in self.expected["episodes"]}
        self.assertEqual(services | set(self.expected["without_episode"]),
                         {g["service"] for g in self.expected["groups"]})
        self.assertFalse(services & set(self.expected["without_episode"]))
        last = max(r["usage_date"] for r in self.records) - timedelta(days=1)
        self.assertEqual(self.expected["detection"]["last_evaluated_date"], last.isoformat())

    def test_every_severity_and_both_observations_are_shown(self):
        episodes = self.expected["episodes"]
        self.assertEqual({e["severity"] for e in episodes}, {"P1", "P2", "P3"})
        self.assertEqual({e["observation"] for e in episodes}, {"observed", "no_longer_observed"})

    def test_altering_a_third_week_amount_changes_the_episodes(self):
        altered = copy.deepcopy(self.records)
        row = next(r for r in altered if r["service_name"] == "Database" and r["usage_date"] == date(2026, 9, 17))
        row["pretax_cost"] = D("171.00")
        self.assertNotEqual(independent_episodes(altered), self.expected["episodes"])
        self.assertEqual(check_expected(altered, self.expected), [])

    def test_current_period_is_closed_before_the_utc_day_of_the_run(self):
        end = date.fromisoformat(self.expected["periods"]["current"]["end"])
        today = datetime.now(timezone.utc).date()
        self.assertLessEqual(end, today, "El reloj del sistema es anterior al fin del periodo actual: la API rechazaria la peticion.")

    def test_every_figure_of_the_expected_file_is_reproduced_by_exact_sums(self):
        self.assertEqual(check_expected(self.records, self.expected), [])

    def test_the_file_states_the_reference_outcome(self):
        names = {g["service"]: g for g in self.expected["groups"]}
        self.assertEqual(set(names), {"Compute", "Analytics", "Storage", "Database", "Tools", "Backup", "Networking"})
        self.assertEqual(self.expected["alerts"], ["Analytics", "Compute"])
        self.assertEqual(names["Compute"]["trigger_reasons"], ["absolute_threshold", "period_increase"])
        self.assertEqual(names["Analytics"]["trigger_reasons"], ["absolute_threshold"])
        self.assertEqual(names["Tools"]["deviation_status"], "below")
        self.assertEqual(names["Tools"]["deviation_percent"], "300.00")
        self.assertEqual(names["Database"]["delta_amount"], "-300.00")
        self.assertEqual(names["Backup"]["deviation_status"], "baseline_nonpositive")
        self.assertEqual(names["Networking"]["deviation_status"], "baseline_missing")

    def test_boundary_group_is_decided_by_cross_multiplication_not_by_the_rounded_percentage(self):
        current, baseline = D("2300.00"), D("2200.00")
        shown = cents((current - baseline) * 100 / baseline)
        self.assertEqual(shown, D("4.55"))
        at_shown = independent_rules(current, baseline, D("2000.00"), D("4.55"), D("100.00"))
        below_shown = independent_rules(current, baseline, D("2000.00"), D("4.54"), D("100.00"))
        self.assertEqual(at_shown["deviation_status"], "below")
        self.assertEqual(below_shown["deviation_status"], "triggered")

    def test_the_file_freezes_no_identifier_computed_by_the_backend(self):
        text = EXPECTED_PATH.read_text(encoding="utf-8")
        self.assertNotIn("evidence_id", text)
        self.assertIsNone(re.search(r'"id"\s*:', text))

    def test_altering_an_amount_or_a_period_fails_naming_the_figure(self):
        altered = copy.deepcopy(self.records)
        target = next(r for r in altered if r["service_name"] == "Compute" and r["usage_date"] >= date(2026, 9, 8))
        target["pretax_cost"] += D("1.00")
        messages = check_expected(altered, self.expected)
        self.assertTrue(any("Compute current" in m and "2401.00" in m for m in messages), messages)
        moved = copy.deepcopy(self.records)
        row = next(r for r in moved if r["service_name"] == "Networking")
        row["usage_date"] = date(2026, 9, 3)
        messages = check_expected(moved, self.expected)
        self.assertTrue(any("Networking" in m for m in messages), messages)
        wrong_service = copy.deepcopy(self.records)
        next(r for r in wrong_service if r["service_name"] == "Tools")["service_name"] = "Compute"
        self.assertTrue(check_expected(wrong_service, self.expected))


class ToolTests(unittest.TestCase):
    def new_store(self, **kwargs):
        return FakeStore(anomalies.PREFIX, **kwargs)

    def test_apply_is_idempotent(self):
        store = self.new_store()
        first = anomalies.apply(store, TENANT)
        self.assertEqual(first["outcome"], "loaded")
        self.assertEqual((first["runs"], first["records"]), (1, len(anomalies.build_dataset(TENANT)[1])))
        writes = store.writes
        second = anomalies.apply(store, TENANT)
        self.assertEqual(second["outcome"], "already-present")
        self.assertEqual(store.writes, writes)

    def test_apply_refuses_a_tenant_with_foreign_cost_data(self):
        for kind in ("runs", "records"):
            store = self.new_store()
            store.add_foreign(kind, TENANT)
            result = anomalies.apply(store, TENANT)
            self.assertEqual(result["outcome"], "refused")
            self.assertIn("ya tiene datos de coste reales", result["reason"])
            self.assertEqual(store.writes, 0)

    def test_apply_refuses_partial_and_other_tenant_states(self):
        store = self.new_store()
        anomalies.apply(store, TENANT)
        del store.rows["records"][next(iter(store.rows["records"]))]
        self.assertEqual(anomalies.status(store, TENANT)["state"], "partial")
        self.assertEqual(anomalies.apply(store, TENANT)["outcome"], "refused")
        other = self.new_store()
        anomalies.apply(other, "tenant-growth")
        self.assertEqual(anomalies.status(other, TENANT)["state"], "other-tenant")
        self.assertEqual(anomalies.apply(other, TENANT)["outcome"], "refused")

    def test_remove_touches_only_its_own_rows_and_can_be_repeated(self):
        rows = {"runs": {}, "records": {}}
        mine, theirs = FakeStore(anomalies.PREFIX, rows), FakeStore(costs.PREFIX, rows)
        anomalies.apply(mine, TENANT)
        costs.apply(theirs, "tenant-growth")
        before_theirs = {k: dict(v) for k, v in theirs.list_synthetic().items()}
        removed = anomalies.remove(mine)
        self.assertFalse(removed["refused"])
        self.assertGreater(removed["records"], 0)
        self.assertEqual(theirs.list_synthetic(), before_theirs)
        self.assertEqual(mine.list_synthetic(), {"runs": {}, "records": {}})
        again = anomalies.remove(mine)
        self.assertEqual((again["runs"], again["records"], again["refused"]), (0, 0, False))

    def test_remove_deletes_episodes_only_of_tenants_left_without_other_cost_data(self):
        rows = {"runs": {}, "records": {}}
        store = FakeStore(anomalies.PREFIX, rows)
        anomalies.apply(store, TENANT)
        store.add_episodes(TENANT, 3)
        store.add_episodes("tenant-growth", 2)
        removed = anomalies.remove(store)
        self.assertEqual((removed["episodes"], removed["kept_episode_tenants"]), (3, []))
        self.assertEqual(store.count_episodes(TENANT), 0)
        self.assertEqual(store.count_episodes("tenant-growth"), 2)
        again = anomalies.remove(store)
        self.assertEqual(again["episodes"], 0)

    def test_remove_keeps_episodes_of_a_tenant_that_still_has_other_cost_data(self):
        store = self.new_store()
        anomalies.apply(store, TENANT)
        store.add_foreign("records", TENANT, "ingested-later")
        store.add_episodes(TENANT, 3)
        removed = anomalies.remove(store)
        self.assertFalse(removed["refused"])
        self.assertEqual((removed["episodes"], removed["kept_episode_tenants"]), (0, [TENANT]))
        self.assertEqual(store.count_episodes(TENANT), 3)
        code, text = self.run_cli(store, "status")
        self.assertIn("3 episodios", text)

    def test_remove_refuses_when_real_rows_hang_from_a_synthetic_run(self):
        store = self.new_store(hanging=2)
        anomalies.apply(store, TENANT)
        result = anomalies.remove(store)
        self.assertTrue(result["refused"])
        self.assertEqual(store.writes, 1)

    def test_each_tool_sees_the_other_ones_rows_as_real(self):
        rows = {"runs": {}, "records": {}}
        mine, theirs = FakeStore(anomalies.PREFIX, rows), FakeStore(costs.PREFIX, rows)
        anomalies.apply(mine, TENANT)
        costs_view = costs.status(theirs, TENANT)
        self.assertGreater(costs_view["real_records"], 0)
        self.assertEqual(costs_view["records"], 0)
        self.assertEqual(costs.apply(theirs, TENANT)["outcome"], "refused")
        anomalies.remove(mine)
        costs.apply(theirs, "tenant-growth")
        mine_view = anomalies.status(mine, "tenant-growth")
        self.assertGreater(mine_view["real_records"], 0)
        self.assertEqual(anomalies.apply(mine, "tenant-growth")["outcome"], "refused")

    def run_cli(self, store, *argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = anomalies.main(list(argv), env={"DATABASE_URL": "sqlite://"}, store_factory=lambda url: store)
        return code, output.getvalue()

    def test_every_command_declares_in_its_output_that_the_rows_are_synthetic(self):
        store = self.new_store()
        for argv in (("status",), ("apply",), ("apply",), ("status",), ("remove",), ("remove",)):
            code, text = self.run_cli(store, *argv)
            self.assertEqual(code, 0, argv)
            self.assertIn("sintetic", text, (argv, text))
        refused = self.new_store()
        refused.add_foreign("records", TENANT)
        code, text = self.run_cli(refused, "apply")
        self.assertEqual(code, 2)
        self.assertIn("sintetic", text)
        self.assertIn("ya tiene datos de coste reales", text)

    def test_refusals_exit_with_status_2_and_say_why(self):
        hanging = self.new_store(hanging=3)
        anomalies.apply(hanging, TENANT)
        code, text = self.run_cli(hanging, "remove")
        self.assertEqual(code, 2)
        self.assertIn("colgando", text)
        self.assertEqual(hanging.writes, 1)
        store = self.new_store()
        anomalies.apply(store, TENANT)
        writes = store.writes
        code, text = self.run_cli(store, "remove", "--tenant", "tenant-growth")
        self.assertEqual(code, 2)
        self.assertIn("no acepta --tenant", text)
        self.assertEqual(store.writes, writes)
        code, _ = self.run_cli(store, "status", "--tenant", "Tenant_Invalido")
        self.assertEqual(code, 2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(anomalies.main(["status"], env={}, store_factory=lambda url: store), 2)

    def test_the_script_is_ascii_and_depends_on_nothing_of_the_repository(self):
        source = SCRIPT_PATH.read_bytes()
        source.decode("ascii")
        text = source.decode("ascii")
        for line in text.splitlines():
            if re.match(r"\s*(from|import)\s+", line):
                module = re.match(r"\s*(?:from|import)\s+([A-Za-z_][\w.]*)", line).group(1).split(".")[0]
                self.assertIn(module, {"__future__", "argparse", "os", "re", "sys", "json", "datetime", "decimal", "typing", "sqlalchemy"}, line)


def comma(value: str) -> str:
    return value.replace(".", ",")


class GuideTests(unittest.TestCase):
    def setUp(self):
        self.text = GUIDE_PATH.read_text(encoding="utf-8")
        self.body = "\n".join(line for line in self.text.splitlines() if not line.lstrip().startswith("#"))
        self.expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        self.script = (ROOT / "scripts" / "call_anomalies_demo.py").read_text(encoding="utf-8")

    def test_the_synthetic_declaration_precedes_the_first_amount(self):
        first_amount = re.search(r"\d[\d.,]*\s?(EUR|\u20ac)|\b\d{3,}[.,]\d{2}\b", self.body)
        self.assertIsNotNone(first_amount)
        before = self.body[: first_amount.start()]
        opening = self.body.strip().split("\n\n")[0]
        self.assertLessEqual(len(opening), len(before))
        self.assertIn("Todos los importes de esta gu\u00eda son datos sint\u00e9ticos", opening)
        self.assertIn("Azure", opening)
        self.assertIn("dataset p\u00fablico", opening)
        self.assertIsNone(re.search(r"\d[\d.,]*\s?(EUR|\u20ac)|\b\d{3,}[.,]\d{2}\b", opening))

    def test_the_panel_limitation_is_explicit_and_negative(self):
        self.assertIn("/anomalies", self.body)
        self.assertRegex(self.body, r"(?is)panel `/anomalies`[^.]*datos de demostraci[o\u00f3]n fijos")
        self.assertRegex(self.body, r"(?is)panel `/anomalies`[^.]*no lee este endpoint")
        self.assertIn("no refleja estas alertas", self.body)

    def test_the_request_of_the_guide_and_of_the_script_equal_the_expected_file(self):
        blocks = re.findall(r"```json\n(.*?)```", self.text, re.S)
        self.assertEqual(len(blocks), 1)
        in_guide = json.loads(blocks[0])
        namespace = {}
        for line in self.script.splitlines():
            if line.startswith(("RULES =", "REQUEST =")):
                exec(line, namespace)
        wanted = {
            "start_date": self.expected["periods"]["current"]["start"],
            "end_date": self.expected["periods"]["current"]["end"],
            "group_by": self.expected["group_by"],
            "currency": self.expected["currency"],
            **self.expected["rules"],
        }
        self.assertEqual(in_guide, wanted)
        self.assertEqual(namespace["REQUEST"], wanted)
        self.assertIn(f'TENANT = "{self.expected["tenant"]}"', self.script)
        first = date.fromisoformat(self.expected["periods"]["baseline"]["start"])
        last = date.fromisoformat(self.expected["periods"]["baseline"]["end"]) - timedelta(days=1)
        self.assertIn(f"del {first.day} al {last.day} de septiembre de {first.year}, ambos incluidos", self.body)

    def test_every_figure_of_the_guide_table_comes_from_the_expected_file(self):
        rows = {}
        for line in self.text.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cells) == 6 and cells[0] != "Servicio" and not re.fullmatch(r"-+", cells[0]):
                self.assertNotIn(cells[0], rows, "fila duplicada")
                rows[cells[0]] = cells
            elif line.startswith("| Servicio"):
                self.assertEqual(cells, ["Servicio", "Actual", "Base", "Diferencia", "Alerta", "Por qué"])
        self.assertEqual(set(rows), {g["service"] for g in self.expected["groups"]})
        minimum = comma(self.expected["rules"]["min_absolute_increase"])
        self.assertIn(f"por debajo del incremento mínimo de {minimum}", rows["Tools"][5])
        alerts, ordinal = self.expected["alerts"], {2: "Dos", 3: "Tres", 1: "Una"}[len(self.expected["alerts"])]
        self.assertIn(f"{ordinal} alertas" if len(alerts) > 1 else "Una alerta", self.text)
        self.assertIn(f"({alerts[0]} antes que {alerts[1]})", self.text)
        for group in self.expected["groups"]:
            service, cells = group["service"], rows[group["service"]]
            self.assertEqual(cells[1], comma(group["current_cost"]), service)
            self.assertEqual(cells[2], "sin datos" if group["baseline_cost"] is None else comma(group["baseline_cost"]), service)
            alert = service in self.expected["alerts"]
            self.assertEqual(cells[4], "**S\u00ed**" if alert else "No", service)
            if group["delta_amount"] is None:
                self.assertEqual(cells[3], "\u2014", service)
            else:
                amount = comma(group["delta_amount"].lstrip("-"))
                sign = "\u2212" if group["delta_amount"].startswith("-") else "+"
                wanted = sign + amount
                if group["deviation_percent"] is not None:
                    shown_percent = comma(group["deviation_percent"].replace("-", "\u2212"))
                    wanted += " (" + shown_percent + " %)"
                self.assertEqual(cells[3], wanted, service)
            if group["deviation_status"] in ("baseline_missing", "baseline_nonpositive"):
                self.assertIn(f"`{group['deviation_status']}`", cells[5], service)
            if group["threshold_status"] == "triggered":
                self.assertIn("umbral", cells[5], service)

    def test_the_script_never_prints_the_password_or_the_token(self):
        self.assertIn("scripts/call_anomalies_demo.py", self.text)
        blocks = [self.script] + re.findall(r"```python\n(.*?)```", self.text, re.S)
        printed = 0
        for block in blocks:
            for line in block.splitlines():
                if "print" in line:
                    printed += 1
                    self.assertNotRegex(line, r"(?i)password|token|DEMO_PASSWORD|access_token")
        self.assertGreater(printed, 0)
        self.assertIn("os.environ", self.script)

    def test_the_guide_covers_preparation_and_return_to_the_initial_state(self):
        for needle in ("apply", "status", "remove", "tenant-core", "down -v", "esperados-anomalias.json"):
            self.assertIn(needle, self.text)
        self.assertLess(self.text.index("apply"), self.text.index("remove"))
        self.assertIn("no acepta `--tenant`", self.text)
        self.assertIn("PowerShell", self.text)
        self.assertIn("Get-Content -Raw scripts/synthetic_anomalies.py | docker compose -p jup107b exec -T processor python - apply", self.text)
        self.assertIn("Get-Content -Raw scripts/call_anomalies_demo.py | docker compose -p jup107b exec -T backend python -", self.text)


@unittest.skipUnless(os.environ.get("JUP086_COCKROACH_TEST_URL"), "JUP086_COCKROACH_TEST_URL is not set")
class CockroachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        cls.text = staticmethod(text)
        url = make_url(os.environ["JUP086_COCKROACH_TEST_URL"])
        if (url.drivername != "cockroachdb+psycopg" or url.host not in {"127.0.0.1", "localhost"}
                or url.port in {None, 5432, 26257} or url.database != "defaultdb" or url.username != "root"
                or url.password is not None or dict(url.query) != {"sslmode": "disable"}):
            raise RuntimeError("Unsafe integration URL: use a disposable loopback node")
        admin = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
        cls.addClassCleanup(admin.dispose)
        name = "jup107_test_" + uuid.uuid4().hex
        with admin.connect() as connection:
            if connection.execute(text("SHOW CLUSTER SETTING cluster.organization")).scalar_one() != "processor-integration-tests":
                raise RuntimeError("Refusing an unmarked server")
            connection.execute(text(f'CREATE DATABASE "{name}"'))

        def drop():
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{name}" CASCADE'))

        cls.addClassCleanup(drop)
        cls.url = url.set(database=name).render_as_string(hide_password=False)
        env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; from app.db.database import Database; db = Database(sys.argv[1]); db.initialize(); db.dispose()", cls.url],
            cwd=ROOT / "apps" / "processor", env=env, check=True, capture_output=True, text=True, timeout=400,
        )
        subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; from pathlib import Path; from sqlalchemy import create_engine; "
             "from app.db.migration_runner import MigrationRunner; e = create_engine(sys.argv[1]); "
             "MigrationRunner(e, 'app.db.migrations', Path('app/db/migrations')).run(); e.dispose()", cls.url],
            cwd=ROOT / "apps" / "backend", env=env, check=True, capture_output=True, text=True, timeout=400,
        )
        cls.engine = create_engine(cls.url, future=True)
        cls.addClassCleanup(cls.engine.dispose)

    def setUp(self):
        with self.engine.begin() as connection:
            for table in ("azure_cost_records", "azure_cost_ingestion_runs", "anomaly_episodes", "anomaly_detection_state"):
                connection.execute(self.text(f"DELETE FROM {table}"))
        self.store = anomalies.SqlStore(engine=self.engine)

    def add_episode(self, identifier, tenant):
        with self.engine.begin() as connection:
            connection.execute(self.text(
                "INSERT INTO anomaly_episodes (id, tenant_id, currency, service, service_key, start_date, last_seen_date, "
                "observation, reference_week_cost, opening_observed_cost, impact_numerator, impact_day_count, "
                "impact_through_date, severity, status, rules_version, rules, created_at, updated_at) VALUES "
                "(:id, :tenant, 'EUR', 'Compute', :id, '2026-09-09', '2026-09-09', 'observed', 1000, 377, 1639, 1, "
                "'2026-09-09', 'P3', 'new', 'jup019-daily-v1', '{}'::JSONB, now(), now())"), {"id": identifier, "tenant": tenant})
            connection.execute(self.text(
                "UPSERT INTO anomaly_detection_state (tenant_id, last_evaluated_date, rules_version, updated_at) "
                "VALUES (:tenant, '2026-09-20', 'jup019-daily-v1', now())"), {"tenant": tenant})

    def anomaly_counts(self, tenant):
        with self.engine.connect() as connection:
            return tuple(connection.execute(self.text(
                "SELECT (SELECT count(*) FROM anomaly_episodes WHERE tenant_id = :t), "
                "(SELECT count(*) FROM anomaly_detection_state WHERE tenant_id = :t)"), {"t": tenant}).one())

    def test_remove_clears_episodes_and_detection_state_of_its_tenant_only(self):
        anomalies.apply(self.store, TENANT)
        self.add_episode("ep-core", TENANT)
        self.add_episode("ep-growth", "tenant-growth")
        self.assertEqual(anomalies.status(self.store, TENANT)["episodes"], 1)
        removed = anomalies.remove(self.store)
        self.assertEqual((removed["episodes"], removed["kept_episode_tenants"]), (1, []))
        self.assertEqual(self.anomaly_counts(TENANT), (0, 0))
        self.assertEqual(self.anomaly_counts("tenant-growth"), (1, 1))
        self.assertEqual(anomalies.remove(self.store)["episodes"], 0)

    def test_remove_keeps_episodes_when_the_tenant_still_has_other_cost_data(self):
        anomalies.apply(self.store, TENANT)
        self.insert_real("run-later", "rec-later")
        self.add_episode("ep-core", TENANT)
        removed = anomalies.remove(self.store)
        self.assertEqual((removed["episodes"], removed["kept_episode_tenants"]), (0, [TENANT]))
        self.assertEqual(self.anomaly_counts(TENANT), (1, 1))

    def insert_real(self, run_id, record_id, tenant=TENANT, request="{}"):
        with self.engine.begin() as connection:
            connection.execute(self.text(
                "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
                "VALUES (:id, :tenant, 'real-sub', CAST(:request AS JSONB), 'completed', now())"),
                {"id": run_id, "tenant": tenant, "request": request})
            connection.execute(self.text(
                "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, currency, "
                "dimensions, source_row_hash, created_at) VALUES (:id, :run, :tenant, 'real-sub', '2026-03-01', 5, 'EUR', "
                "'{}'::JSONB, :id, now())"), {"id": record_id, "run": run_id, "tenant": tenant})

    def counts(self):
        with self.engine.connect() as connection:
            return tuple(connection.execute(self.text(
                "SELECT (SELECT count(*) FROM azure_cost_ingestion_runs), (SELECT count(*) FROM azure_cost_records)")).one())

    def test_load_matches_the_expected_sums_and_remove_restores_the_empty_state(self):
        expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        result = anomalies.apply(self.store, TENANT)
        runs, records = anomalies.build_dataset(TENANT)
        self.assertEqual((result["outcome"], result["runs"], result["records"]), ("loaded", len(runs), len(records)))
        with self.engine.connect() as connection:
            rows = connection.execute(self.text(
                "SELECT service_name, CASE WHEN usage_date < '2026-09-08' THEN 'baseline' ELSE 'current' END AS period, "
                "SUM(pretax_cost)::STRING AS total, count(*) AS n FROM azure_cost_records "
                "WHERE tenant_id = :tenant AND currency = 'EUR' AND usage_date < '2026-09-15' GROUP BY 1, 2"),
                {"tenant": TENANT}).mappings().all()
        stored = {(row["service_name"], row["period"]): (D(row["total"]), row["n"]) for row in rows}
        wanted = {}
        for group in expected["groups"]:
            for period in ("baseline", "current"):
                if group[f"{period}_cost"] is not None:
                    wanted[(group["service"], period)] = (D(group[f"{period}_cost"]), group[f"{period}_record_count"])
        self.assertEqual(stored, wanted)
        self.assertEqual(anomalies.apply(self.store, TENANT)["outcome"], "already-present")
        self.assertEqual(anomalies.status(self.store, TENANT)["state"], "present")
        anomalies.remove(self.store)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(anomalies.status(self.store, TENANT)["state"], "absent")

    def test_real_rows_are_protected_on_load_and_survive_removal(self):
        self.insert_real("run-real", "rec-real")
        self.assertEqual(anomalies.apply(self.store, TENANT)["outcome"], "refused")
        self.assertEqual(anomalies.status(self.store, TENANT)["state"], "absent")
        self.assertEqual(anomalies.apply(self.store, "tenant-growth")["outcome"], "loaded")
        anomalies.remove(self.store)
        self.assertEqual(self.counts(), (1, 1))

    def test_rows_that_only_look_synthetic_are_real_and_survive_removal(self):
        self.insert_real(anomalies.PREFIX + "imposter", anomalies.PREFIX + "imposter-rec")
        self.insert_real("flagged-without-prefix", "rec-flagged", request='{"synthetic": true}')
        self.insert_real(anomalies.PREFIX + "string-flag", "rec-string", request='{"synthetic": "true"}')
        report = anomalies.status(self.store, TENANT)
        self.assertEqual((report["state"], report["real_runs"]), ("absent", 3))
        self.assertEqual(anomalies.apply(self.store, TENANT)["outcome"], "refused")
        anomalies.remove(self.store)
        self.assertEqual(self.counts(), (3, 3))

    def test_remove_refuses_instead_of_failing_when_a_real_record_hangs_from_a_synthetic_run(self):
        anomalies.apply(self.store, TENANT)
        with self.engine.begin() as connection:
            connection.execute(self.text(
                "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, currency, "
                "dimensions, source_row_hash, created_at) VALUES ('real-1', :run, :tenant, 'real-sub', '2026-03-01', 5, 'EUR', "
                "'{}'::JSONB, 'real-1', now())"), {"run": anomalies.RUN, "tenant": TENANT})
        before = self.counts()
        self.assertTrue(anomalies.remove(self.store)["refused"])
        self.assertEqual(self.counts(), before)

    def test_the_jup_106_tool_sees_these_rows_as_real_and_never_removes_them(self):
        theirs = costs.SqlStore(engine=self.engine)
        anomalies.apply(self.store, TENANT)
        loaded = self.counts()
        report = costs.status(theirs, TENANT)
        self.assertEqual((report["state"], report["records"], report["real_records"]), ("absent", 0, loaded[1]))
        self.assertEqual(costs.apply(theirs, TENANT)["outcome"], "refused")
        costs.remove(theirs)
        self.assertEqual(self.counts(), loaded)

    def test_it_coexists_with_the_jup_106_dataset_and_never_touches_it(self):
        self.assertEqual(costs.apply(costs.SqlStore(engine=self.engine), "tenant-growth")["outcome"], "loaded")
        theirs = self.counts()
        self.assertEqual(anomalies.apply(self.store, TENANT)["outcome"], "loaded")
        self.assertEqual(anomalies.status(self.store, "tenant-growth")["state"], "other-tenant")
        anomalies.remove(self.store)
        self.assertEqual(self.counts(), theirs)
        self.assertEqual(costs.status(costs.SqlStore(engine=self.engine), "tenant-growth")["state"], "present")


if __name__ == "__main__":
    unittest.main()
