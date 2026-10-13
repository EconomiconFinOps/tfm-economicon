from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = Decimal


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dataset = load("economicon_demo_dataset", ROOT / "scripts" / "demo_dataset.py")
EXPECTED_COSTS_PATH = ROOT / "docs" / "demo" / "JUP-119" / "esperados-costes.json"
JUP107_PATH = ROOT / "docs" / "demo" / "JUP-107" / "esperados-anomalias.json"
EXPECTED_ANOMALIES_PATH = JUP107_PATH
ORIGINAL_MANIFEST = ROOT / "fixtures" / "azure-cost" / "manifest.json"


def cents(value: Decimal) -> Decimal:
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def parse_day(text: str) -> date:
    return datetime.strptime(text, dataset.DATE_FORMAT).date()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def tenant_of(manifest: dict) -> dict[str, str]:
    return {pair["subscription"]: pair["tenant"] for pair in manifest["pairs"]}


def records_of(rows: list[dict[str, str]], manifest: dict) -> list[dict]:
    tenants = tenant_of(manifest)
    return [{
        "tenant": tenants[row["SubscriptionId"]], "subscription": row["SubscriptionId"], "usage_date": parse_day(row["Date"]),
        "pretax_cost": D(row["CostInBillingCurrency"]), "currency": row["BillingCurrencyCode"],
        "service_name": row["MeterCategory"] or None,
        "project": next((v for k, v in json.loads("{" + row["Tags"] + "}").items() if k.lower() == "project"), None) if row["Tags"] else None,
    } for row in rows]


def expected_costs(records: list[dict]) -> dict:
    """Totals and record counts from the CSV records with exact decimal arithmetic, never from the backend."""
    figures: dict[str, dict] = {"month_currency": {}, "month_currency_service": {}, "month_currency_project": {}}
    for record in records:
        month = record["usage_date"].strftime("%Y-%m")
        keys = {
            "month_currency": (record["tenant"], month, record["currency"]),
            "month_currency_service": (record["tenant"], month, record["currency"], record["service_name"] or "(sin servicio)"),
            "month_currency_project": (record["tenant"], month, record["currency"], record["project"] or "(sin proyecto)"),
        }
        for name, key in keys.items():
            slot = figures[name].setdefault("|".join(key), [D(0), 0])
            slot[0] += record["pretax_cost"]
            slot[1] += 1
    return {name: {key: {"total": format(total, "f"), "records": count} for key, (total, count) in sorted(items.items())}
            for name, items in figures.items()}


def check_costs(records: list[dict], expected: dict) -> list[str]:
    problems = []
    actual = expected_costs(records)
    for name, items in expected["figures"].items():
        for key in sorted(set(items) | set(actual[name])):
            wanted, found = items.get(key), actual[name].get(key)
            if wanted is None or found is None or D(wanted["total"]) != D(found["total"]) or wanted["records"] != found["records"]:
                problems.append(f"{name} {key}: file says {wanted} but the records give {found}")
    return problems


def independent_episodes(records: list[dict], reference: date) -> tuple[list[dict], date | None]:
    """The JUP-019 daily rule of docs/api/anomaly-episodes.md written again with fractions, not from the backend."""
    daily: dict[str, dict[date, Fraction]] = {}
    observed = set()
    for record in records:
        if record["currency"] != "EUR" or record["usage_date"] > reference:
            continue
        day = record["usage_date"]
        observed.add(day)
        values = daily.setdefault(record["service_name"], {})
        values[day] = values.get(day, Fraction(0)) + Fraction(record["pretax_cost"])
    last_complete = min(max(observed), reference) - timedelta(days=1)
    tracking, episodes = {}, []
    day = min(observed)
    while day <= last_complete:
        previous = [day - timedelta(days=offset) for offset in range(1, 8)]
        if day in observed and all(item in observed for item in previous):
            for service in sorted(daily):
                values = daily[service]
                observed_cost = values.get(day, Fraction(0))
                episode = tracking.get(service)
                reference_cost = episode["reference"] if episode else sum((values.get(item, Fraction(0)) for item in previous), Fraction(0)) / 7
                hit = reference_cost > 0 and observed_cost - reference_cost > 100 and (observed_cost - reference_cost) * 100 > reference_cost * 20
                if episode:
                    if not hit and (day - episode["last_seen_date"]).days > 3:
                        episode["observation"], episode["no_longer_observed_on"] = "no_longer_observed", day
                        del tracking[service]
                    else:
                        if hit:
                            episode["last_seen_date"] = day
                        episode["impact"] += max(Fraction(0), observed_cost - reference_cost)
                        episode["impact_day_count"] += 1
                elif hit:
                    episode = {"service": service, "start_date": day, "last_seen_date": day, "observation": "observed",
                               "no_longer_observed_on": None, "reference": reference_cost,
                               "impact": observed_cost - reference_cost, "impact_day_count": 1}
                    tracking[service] = episode
                    episodes.append(episode)
        day += timedelta(days=1)

    def shown(value):
        return format(cents(D(value.numerator) / D(value.denominator)), "f")

    result = []
    for episode in episodes:
        impact = episode["impact"]
        result.append({
            "service": episode["service"], "start_date": episode["start_date"].isoformat(),
            "last_seen_date": episode["last_seen_date"].isoformat(), "observation": episode["observation"],
            "no_longer_observed_on": episode["no_longer_observed_on"].isoformat() if episode["no_longer_observed_on"] else None,
            "reference_daily_cost": shown(episode["reference"]), "accumulated_impact": shown(impact),
            "impact_day_count": episode["impact_day_count"],
            "severity": "P1" if impact > 2000 else "P2" if impact >= 500 else "P3",
        })
    order = {"P1": 0, "P2": 1, "P3": 2}
    return sorted(result, key=lambda item: (order[item["severity"]], -D(item["accumulated_impact"]))), last_complete


def weekly_totals(records: list[dict]) -> dict[str, dict[str, tuple[Decimal, int] | None]]:
    periods = {"baseline": (date(2026, 9, 1), date(2026, 9, 8)), "current": (date(2026, 9, 8), date(2026, 9, 15))}
    result: dict[str, dict] = defaultdict(lambda: {"baseline": None, "current": None})
    for record in records:
        if record["tenant"] != dataset.TENANT_CORE or record["currency"] != "EUR":
            continue
        for name, (start, end) in periods.items():
            if start <= record["usage_date"] < end:
                total, count = result[record["service_name"]][name] or (D(0), 0)
                result[record["service_name"]][name] = (total + record["pretax_cost"], count + 1)
    return result


def coverage_gaps(records: list[dict], manifest: dict) -> list[str]:
    """One message per tenant day without any record inside the window, naming the tenant, its subscriptions and the day."""
    first, last = date.fromisoformat(manifest["window"]["start"]), date.fromisoformat(manifest["window"]["end"])
    seen, subscriptions = defaultdict(set), defaultdict(set)
    for record in records:
        seen[record["tenant"]].add(record["usage_date"])
        subscriptions[record["tenant"]].add(record["subscription"])
    problems = []
    for tenant in sorted({pair["tenant"] for pair in manifest["pairs"]}):
        day = first
        while day <= last:
            if day not in seen[tenant]:
                problems.append(f"{tenant}: no record on {day.isoformat()} (subscriptions: {', '.join(sorted(subscriptions[tenant]))})")
                break
            day += timedelta(days=1)
    for record in records:
        if not first <= record["usage_date"] <= last:
            problems.append(f"{record['tenant']}: record of {record['subscription']} on {record['usage_date'].isoformat()} outside the window")
            break
    return problems


class DerivedFixtureTests(unittest.TestCase):
    def setUp(self):
        self.original_header, self.original = dataset.read_rows(dataset.PUBLIC_SOURCE)
        self.derived = read_csv(dataset.DERIVED_PATH)
        self.manifest = json.loads(dataset.DERIVED_MANIFEST_PATH.read_text("utf-8"))

    def test_shift_moves_the_first_public_day_to_the_first_september_day(self):
        self.assertEqual(dataset.PUBLIC_FIRST_DAY + timedelta(days=dataset.SHIFT_DAYS), date(2026, 9, 1))
        self.assertEqual(self.manifest["shift_days"], dataset.SHIFT_DAYS)

    def test_only_the_three_date_columns_differ_by_exactly_the_shift(self):
        self.assertEqual(len(self.derived), len(self.original))
        self.assertEqual(len(self.derived), 50)
        for before, after in zip(self.original, self.derived):
            for column in before:
                if column in dataset.DATE_COLUMNS:
                    self.assertEqual(parse_day(after[column]) - parse_day(before[column]), timedelta(days=dataset.SHIFT_DAYS), column)
                else:
                    self.assertEqual(after[column], before[column], column)

    def test_headers_match_the_original(self):
        self.assertEqual(list(dataset.HEADER), self.original_header)

    def test_original_fixtures_and_manifest_are_untouched(self):
        manifest = json.loads(ORIGINAL_MANIFEST.read_text("utf-8"))
        self.assertEqual(len(manifest["files"]), 11)
        self.assertEqual(manifest["transformation"], "None; sampled rows retain the public values published by Microsoft.")
        self.assertTrue(all("derived" not in entry["path"] for entry in manifest["files"]))
        self.assertFalse(any("shifted" in entry["path"] for entry in manifest["files"]))

    def test_derivative_is_marked_as_derived_with_its_checksum(self):
        content = dataset.DERIVED_PATH.read_bytes()
        self.assertEqual(self.manifest["kind"], "derived")
        self.assertEqual(self.manifest["source_fixture"], "fixtures/azure-cost/EA-Cost-Actual.sample.csv")
        self.assertEqual(self.manifest["sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(self.manifest["rows"], 50)

    def test_regeneration_is_byte_identical_to_the_versioned_files(self):
        for path, content in dataset.generate().items():
            self.assertEqual(path.read_bytes(), content, f"{path.relative_to(ROOT).as_posix()} is out of date: run scripts/demo_dataset.py")


class DemoDatasetTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
        self.rows = read_csv(dataset.DEMO_PATH)
        self.records = records_of(self.rows, self.manifest)

    def test_generation_is_deterministic(self):
        self.assertEqual(dataset.generate(), dataset.generate())
        self.assertEqual(dataset.render_csv(dataset.demo_rows()), dataset.render_csv(list(reversed(dataset.demo_rows()))))

    def test_every_row_has_a_valid_date_and_the_original_columns(self):
        self.assertEqual(list(self.rows[0].keys()), list(dataset.HEADER))
        for row in self.rows:
            self.assertRegex(row["Date"], r"^\d{2}/\d{2}/\d{4}$")
            parse_day(row["Date"])

    def test_every_subscription_is_in_the_manifest_with_a_declared_origin(self):
        listed = {pair["subscription"]: pair["origin"] for pair in self.manifest["pairs"]}
        self.assertEqual({row["SubscriptionId"] for row in self.rows}, set(listed))
        for subscription, origin in listed.items():
            self.assertEqual(subscription.startswith(dataset.PREFIX), origin == dataset.ORIGIN_SYNTHETIC, subscription)
            self.assertIn(origin, (dataset.ORIGIN_PUBLIC, dataset.ORIGIN_SYNTHETIC))
        self.assertEqual(sum(pair["rows"] for pair in self.manifest["pairs"]), len(self.rows))
        self.assertEqual(self.manifest["sha256"], hashlib.sha256(dataset.DEMO_PATH.read_bytes()).hexdigest())

    def test_public_rows_are_exactly_the_shifted_derivative(self):
        public = {pair["subscription"] for pair in self.manifest["pairs"] if pair["origin"] == dataset.ORIGIN_PUBLIC}
        in_demo = sorted((r for r in self.rows if r["SubscriptionId"] in public), key=dataset.sort_key)
        self.assertEqual(in_demo, sorted(read_csv(dataset.DERIVED_PATH), key=dataset.sort_key))

    def test_each_demo_tenant_is_covered_every_day_of_the_common_window(self):
        self.assertEqual(self.manifest["window"], {"start": "2026-07-01", "end": "2026-10-30"})
        self.assertEqual(coverage_gaps(self.records, self.manifest), [])

    def test_a_removed_day_fails_naming_tenant_and_day(self):
        trimmed = [r for r in self.records if not (r["tenant"] == dataset.TENANT_CORE and r["usage_date"] == date(2026, 8, 15))]
        problems = coverage_gaps(trimmed, self.manifest)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("tenant-core: no record on 2026-08-15"), problems)
        self.assertIn("synthetic-anomalies", problems[0])

    def test_a_record_outside_the_window_fails(self):
        for day in (date(2026, 6, 30), date(2026, 10, 31)):
            extra = self.records + [{**self.records[0], "tenant": dataset.TENANT_CORE, "subscription": dataset.ANOMALIES_SUBSCRIPTION, "usage_date": day}]
            self.assertEqual(coverage_gaps(extra, self.manifest),
                             [f"tenant-core: record of {dataset.ANOMALIES_SUBSCRIPTION} on {day.isoformat()} outside the window"])

    def test_a_public_row_outside_the_window_fails_too(self):
        public = next(r for r in self.records if not r["subscription"].startswith(dataset.PREFIX))
        for day in (date(2026, 6, 1), date(2026, 11, 15)):
            extra = self.records + [{**public, "usage_date": day}]
            problems = coverage_gaps(extra, self.manifest)
            self.assertEqual(len(problems), 1, day)
            self.assertIn(public["subscription"], problems[0])
            self.assertIn(day.isoformat(), problems[0])

    def test_usd_series_tells_a_gap_from_a_recorded_zero(self):
        usd = [r for r in self.records if r["tenant"] == dataset.TENANT_GROWTH and r["currency"] == "USD"]
        by_month = defaultdict(list)
        for record in usd:
            by_month[record["usage_date"].month].append(record["pretax_cost"])
        self.assertNotIn(7, by_month, "July must have no USD record at all")
        self.assertTrue(by_month[8] and all(value == 0 for value in by_month[8]), "August must hold recorded zeros")
        self.assertTrue(any(value > 0 for value in by_month[9]) and any(value > 0 for value in by_month[10]))

    def test_euro_series_has_a_credit_and_unlabelled_rows(self):
        eur = [r for r in self.records if r["tenant"] == dataset.TENANT_GROWTH and r["currency"] == "EUR"]
        self.assertTrue(any(r["pretax_cost"] < 0 for r in eur))
        self.assertTrue(any(r["service_name"] is None for r in eur))
        self.assertTrue(any(r["project"] is None for r in eur))

    def test_the_big_integer_has_no_cents_and_exceeds_the_js_safe_range(self):
        big = [r for r in self.records if r["pretax_cost"] > 2 ** 53]
        self.assertEqual(len(big), 1)
        self.assertEqual(big[0]["pretax_cost"] % 1, 0)
        self.assertEqual(big[0]["usage_date"].month, 10)

    def test_every_pair_names_the_definition_that_ingests_it_and_it_groups_by_two_fields(self):
        for pair in self.manifest["pairs"]:
            self.assertIn("definition", pair, pair["subscription"])
            path = dataset.DEMO_DIR / pair["definition"]
            self.assertTrue(path.is_file(), pair["definition"])
            grouping = json.loads(path.read_text("utf-8"))["dataset"]["grouping"]
            self.assertEqual([(g["type"], g["name"]) for g in grouping], [("Dimension", "ServiceName"), ("Tag", "Project")])

    def test_grouping_uses_the_two_fields_the_api_allows(self):
        definition = json.loads((dataset.DEMO_DIR / "ingestion-definition.json").read_text("utf-8"))
        self.assertEqual([(g["type"], g["name"]) for g in definition["dataset"]["grouping"]], [("Dimension", "ServiceName"), ("Tag", "Project")])
        self.assertEqual(definition["timePeriod"], {"from": "2026-07-01T00:00:00Z", "to": "2026-10-31T00:00:00Z"})
        self.assertEqual(self.manifest["absent_fields"], list(dataset.ABSENT_FIELDS))

    def test_regeneration_is_byte_identical_to_the_versioned_files(self):
        for path, content in dataset.generate().items():
            self.assertEqual(path.read_bytes(), content, f"{path.relative_to(ROOT).as_posix()} is out of date: run scripts/demo_dataset.py")


class ExpectedFiguresTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
        self.records = records_of(read_csv(dataset.DEMO_PATH), self.manifest)

    def test_cost_totals_match_the_reference_document(self):
        expected = json.loads(EXPECTED_COSTS_PATH.read_text("utf-8"))
        self.assertEqual(check_costs(self.records, expected), [])

    def test_an_altered_amount_fails_naming_the_figure(self):
        expected = json.loads(EXPECTED_COSTS_PATH.read_text("utf-8"))
        altered = copy.deepcopy(self.records)
        target = next(r for r in altered if r["tenant"] == dataset.TENANT_GROWTH and r["currency"] == "EUR" and r["usage_date"].month == 9)
        target["pretax_cost"] += D("0.01")
        problems = check_costs(altered, expected)
        self.assertTrue(problems)
        self.assertTrue(any(p.startswith("month_currency tenant-growth|2026-09|EUR") for p in problems), problems)

    def test_weekly_totals_keep_the_figures_of_jup_107(self):
        reference = {group["service"]: group for group in json.loads(JUP107_PATH.read_text("utf-8"))["groups"]}
        found = weekly_totals(self.records)
        self.assertEqual(set(found), set(reference))
        for service, group in reference.items():
            for name in ("baseline", "current"):
                total = None if found[service][name] is None else found[service][name][0]
                count = None if found[service][name] is None else found[service][name][1]
                self.assertEqual(total, None if group[f"{name}_cost"] is None else D(group[f"{name}_cost"]), f"{service} {name}")
                self.assertEqual(count, group[f"{name}_record_count"], f"{service} {name}")

    def test_detection_at_the_original_reference_date_reproduces_jup_107(self):
        episodes, last = independent_episodes(self.records_of_core(), date(2026, 9, 21))
        wanted = json.loads(JUP107_PATH.read_text("utf-8"))["episodes_by_reference"]["2026-09-21"]
        self.assertEqual(last, date(2026, 9, 20))
        self.assertEqual(episodes, wanted["episodes"])

    def test_detection_figures_match_the_reference_document(self):
        expected = json.loads(EXPECTED_ANOMALIES_PATH.read_text("utf-8"))
        for reference, wanted in expected["episodes_by_reference"].items():
            episodes, last = independent_episodes(self.records_of_core(), date.fromisoformat(reference))
            self.assertEqual(last.isoformat(), wanted["last_evaluated_date"], reference)
            self.assertEqual(episodes, wanted["episodes"], reference)

    def test_every_case_not_in_the_csv_names_an_existing_test(self):
        expected = json.loads(EXPECTED_COSTS_PATH.read_text("utf-8"))
        self.assertGreaterEqual(len(expected["cases_not_in_the_csv"]), 5)
        for case, detail in expected["cases_not_in_the_csv"].items():
            path, _, name = detail["prueba"].partition("::")
            source = (ROOT / path).read_text("utf-8")
            self.assertIn(f"def {name}(", source, f"{case}: {detail['prueba']} does not exist")

    def test_the_calm_base_opens_no_episode_before_september(self):
        episodes, _ = independent_episodes(self.records_of_core(), date(2026, 8, 31))
        self.assertEqual(episodes, [])

    def test_the_end_of_the_window_opens_at_least_two_further_episodes(self):
        original = {e["service"] for e in json.loads(JUP107_PATH.read_text("utf-8"))["episodes_by_reference"]["2026-09-21"]["episodes"]}
        episodes, last = independent_episodes(self.records_of_core(), date(2026, 10, 30))
        self.assertEqual(last, date(2026, 10, 29))
        self.assertGreaterEqual(len({e["service"] for e in episodes} - original), 2)
        self.assertTrue(original <= {e["service"] for e in episodes})

    def records_of_core(self):
        return [r for r in self.records if r["tenant"] == dataset.TENANT_CORE]


def write_reference_documents() -> None:
    manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
    records = records_of(read_csv(dataset.DEMO_PATH), manifest)
    EXPECTED_COSTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    costs = {
        "version": 1,
        "descripcion": "Totales esperados del conjunto de demostracion de costes (scripts/demo_dataset.py): por tenant, mes y moneda, y por servicio y por proyecto. Una prueba los recalcula del CSV con aritmetica exacta sin usar el backend. Importes sinteticos y del dataset publico con fechas desplazadas; no son facturas de Azure.",
        "window": manifest["window"], "absent_fields": manifest["absent_fields"],
        "cases_not_in_the_csv": {
            "fila sin fecha de uso": {
                "motivo": "la API simulada la rechaza",
                "prueba": "apps/backend/tests/test_billing_summary.py::test_scoped_sql_reference_for_each_dimension"},
            "importe por encima de 2^53 con centimos": {
                "motivo": "la API lo devuelve en coma flotante y pierde precision",
                "prueba": "apps/backend/tests/test_billing_summary.py::test_scoped_sql_reference_for_each_dimension"},
            "grupos de recurso que solo difieren en mayusculas": {
                "motivo": "la demo no lleva el grupo de recurso: la API agrupa por dos campos",
                "prueba": "apps/backend/tests/test_billing_summary.py::test_scoped_sql_reference_for_each_dimension"},
            "registros con grupo de recurso, centro de coste y otras etiquetas": {
                "motivo": "la demo no los lleva por la misma razon",
                "prueba": "apps/backend/tests/test_billing_summary.py::test_scoped_sql_reference_for_each_dimension"},
            "registros sin grupo de recurso, servicio ni etiquetas": {
                "motivo": "la demo lleva servicio y proyecto, no el resto",
                "prueba": "apps/backend/tests/test_tag_coverage.py::test_positive_weighting_adjustments_currencies_and_isolation"},
        },
        "figures": expected_costs(records),
    }
    EXPECTED_COSTS_PATH.write_text(json.dumps(costs, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    core = [r for r in records if r["tenant"] == dataset.TENANT_CORE]
    by_reference = {}
    for reference in (date(2026, 9, 21), date(2026, 10, 30)):
        episodes, last = independent_episodes(core, reference)
        by_reference[reference.isoformat()] = {"last_evaluated_date": last.isoformat(), "episodes": episodes}
    anomalies = json.loads(EXPECTED_ANOMALIES_PATH.read_text("utf-8"))
    anomalies["data_range"] = {"first_day": "2026-07-01", "last_day": "2026-10-30"}
    anomalies["episodes_by_reference"] = by_reference
    EXPECTED_ANOMALIES_PATH.write_text(json.dumps(anomalies, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(EXPECTED_COSTS_PATH.relative_to(ROOT).as_posix())
    print(EXPECTED_ANOMALIES_PATH.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    if "--write" in sys.argv:
        write_reference_documents()
    else:
        unittest.main()
