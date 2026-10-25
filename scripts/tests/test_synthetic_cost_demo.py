from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import re
import sys
import unittest
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs" / "demo" / "JUP-107"
sys.path.insert(0, str(ROOT / "scripts"))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dataset = load("economicon_demo_dataset_for_route", ROOT / "scripts" / "demo_dataset.py")
loader = load("economicon_demo_data_for_route", ROOT / "scripts" / "demo_data.py")
loader_tests = load("economicon_demo_data_tests_for_route", ROOT / "scripts" / "tests" / "test_demo_data.py")
MANIFEST = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))

TENANT = "tenant-growth"
REFERENCE = "2026-10-30"
MAX_SECONDS = 240
BIG_MONTH = "2026-10"
ALLOWED_SCREENS = {"none", "billing-dashboard", "anomalies-panel"}
FIGURE_SCREENS = {"billing-dashboard", "anomalies-panel"}
FIXED_DATA_ROUTES = ("/recommendations", "/cuts", "/operational")
TOPICS = ("moneda", "hueco", "cero", "crédito", "grande", "cliente", "etiqueta", "anomalía")
ANOMALY_EXPECTED = PACKAGE / "esperados-anomalias.json"


def month_of(day) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def dated(records, currency, start, end, tenant=TENANT):
    return [r for r in records if r["tenant"] == tenant and r["currency"] == currency
            and start <= month_of(r["usage_date"]) <= end]


def total(rows):
    return sum((r["pretax_cost"] for r in rows), Decimal("0"))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def group_key(record, group_by):
    if group_by == "service":
        return record["service_name"]
    if group_by == "project":
        return record["project"]
    raise AssertionError(f"grouping not supported by the demo: {group_by}")


def compare(month_totals: dict[str, Decimal]):
    # Same endpoint rule as the dashboard: first and last month with a non-zero cost.
    months = sorted(m for m, value in month_totals.items() if value != 0)
    if len(months) < 2:
        return None
    first, last = months[0], months[-1]
    difference = month_totals[last] - month_totals[first]
    percent = (difference / month_totals[first] * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return first, last, difference, percent


def computed(records, figure):
    kind, currency = figure["kind"], figure.get("currency")
    tenant = figure.get("tenant", TENANT)
    if kind == "month_total":
        rows = dated(records, currency, figure["month"], figure["month"], tenant)
        return (money(total(rows)), len(rows)) if rows else (None, 0)
    if kind == "period_total":
        rows = dated(records, currency, figure["from"], figure["to"], tenant)
        return money(total(rows)), len(rows)
    if kind == "group_total":
        rows = [r for r in dated(records, currency, figure["from"], figure["to"], tenant)
                if group_key(r, figure["group_by"]) == figure["key"]]
        return money(total(rows)), len(rows)
    if kind == "comparison":
        months: dict[str, Decimal] = {}
        for r in dated(records, currency, figure["from"], figure["to"], tenant):
            months[month_of(r["usage_date"])] = months.get(month_of(r["usage_date"]), Decimal("0")) + r["pretax_cost"]
        result = compare(months)
        return None if result is None else (result[0], result[1], money(result[2]), str(result[3]))
    if kind == "anomaly_episode":
        # Verified independently by test_demo_dataset.py against the anomaly dataset.
        episodes = json.loads(ANOMALY_EXPECTED.read_text(encoding="utf-8"))["episodes_by_reference"][figure["reference"]]["episodes"]
        found = [e for e in episodes if e["service"] == figure["service"] and e["severity"] == figure["severity"]]
        return (found[0]["accumulated_impact"], found[0]["impact_day_count"]) if len(found) == 1 else None
    raise AssertionError(f"unknown figure kind: {kind}")


def stated(figure):
    if figure["kind"] == "comparison":
        if figure.get("unavailable"):
            return None
        return figure["first_month"], figure["last_month"], figure["difference"], figure["percent"]
    return figure["expected"], figure["records"]


def mismatches(records, figures):
    return [figure["id"] for figure in figures if computed(records, figure) != stated(figure)]


# Any decimal number, and an integer only when it carries a unit.
QUANTITY = re.compile(r"(?<![\w.])(\d+[.,]\d+|\d+(?=\s*(?:euros|dólares|por ciento|EUR|USD|%)))")
SECRET_PROSE = re.compile(r"(?i)(contraseña|password)\s+(es|is)\s+\S{4,}|(contraseña|password)\s*[:=]\s*(?!process\.env)[^<\s'\"]\S{3,}")
REHEARSAL_CLAIM = re.compile(r"(?i)\b(se ensayó|ensayó|ensayaron|hemos ensayado|fue ensayada|ha sido ensayada)\b")
STEP_CLAIMS = {
    "D4": r"julio no tiene ningún dato y agosto tiene un cero registrado",
    "D5": r"crédito de 250 euros negativos",
    "D9": r"al cambiar de cliente aparecen otras cifras",
    "D12": r"candidata para investigar, no una causa confirmada",
}
ANSWER_CLAIMS = {
    "moneda": ("EUR", "USD"), "cero": ("cero",), "crédito": ("-250.00",), "cliente": ("No:", "sus propias cifras"),
    "etiqueta": ("Etiqueta",), "grande": ("no se dibuja",),
}
NAV_NAMES = ("recomendaciones", "corte global", "coste detallado")
SECRET = re.compile(r"(?i)(DEMO_PASSWORD|TOKEN|SECRET|API[_-]?KEY)\s*[=:]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._\-]{5,}")
TOPIC_STEPS = {"moneda": {"D3", "D6"}, "hueco": {"D4"}, "cero": {"D4"}, "crédito": {"D5"}, "grande": {"D11"},
               "cliente": {"D9"}, "etiqueta": {"D7"}, "anomalía": {"D12"}}


def quantities(text):
    return {abs(Decimal(m.group(1).replace(",", "."))) for m in QUANTITY.finditer(text)}


def figure_values(figures):
    values = set()
    for figure in figures:
        for key in ("expected", "difference", "percent"):
            if figure.get(key) is not None:
                values.add(abs(Decimal(figure[key])))
    return values


def load_package():
    return json.loads((PACKAGE / "esperados.json").read_text(encoding="utf-8"))


def dataset_records():
    """The stored records of every demo tenant: the CSV rows summed by day, service, project and currency."""
    tenants = {pair["subscription"]: pair["tenant"] for pair in MANIFEST["pairs"]}
    daily = defaultdict(Decimal)
    with dataset.DEMO_PATH.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            day = datetime.strptime(row["Date"], dataset.DATE_FORMAT).date()
            key = (tenants[row["SubscriptionId"]], row["SubscriptionId"], day, row["MeterCategory"] or None,
                   dataset.project_of(row), row["BillingCurrencyCode"])
            daily[key] += Decimal(row["CostInBillingCurrency"])
    return [{"tenant": t, "subscription": s, "usage_date": d, "service_name": svc, "project": proj, "currency": cur,
             # The cost column keeps twelve decimals; the public rows carry fifteen.
             "pretax_cost": cost.quantize(Decimal("1E-12"), rounding=ROUND_HALF_EVEN)}
            for (t, s, d, svc, proj, cur), cost in daily.items()]


RECORDS = dataset_records()


class ComputationTests(unittest.TestCase):
    """The independent calculation itself, on constructed cases and on the dataset."""

    def test_a_recorded_zero_is_not_an_endpoint_and_a_gap_is_not_a_zero(self):
        totals = {"2026-02": Decimal("0.00"), "2026-04": Decimal("40.00"), "2026-05": Decimal("-50.00")}
        self.assertEqual(compare(totals), ("2026-04", "2026-05", Decimal("-90.00"), Decimal("-225.00")))
        self.assertIsNone(compare({"2026-02": Decimal("0.00"), "2026-04": Decimal("40.00")}))

    def test_comparison_percent_rounds_half_up_and_keeps_the_sign_of_the_difference(self):
        self.assertEqual(compare({"2026-01": Decimal("3"), "2026-02": Decimal("3.01")})[3], Decimal("0.33"))
        self.assertEqual(compare({"2026-01": Decimal("200"), "2026-02": Decimal("1")})[2], Decimal("-199"))

    def test_the_dataset_reproduces_the_documented_reference_values(self):
        months = {m: total(dated(RECORDS, "EUR", m, m)) for m in ("2026-07", "2026-08", "2026-09", "2026-10")}
        self.assertEqual({m: money(v) for m, v in months.items()},
                         {"2026-07": "19404.00", "2026-08": "20421.20", "2026-09": "21755.54", "2026-10": "23242.56"})
        self.assertEqual(computed(RECORDS, {"kind": "comparison", "currency": "EUR", "from": "2026-07", "to": "2026-09"}),
                         ("2026-07", "2026-09", "2351.54", "12.12"))
        self.assertIsNone(computed(RECORDS, {"kind": "comparison", "currency": "USD", "from": "2026-07", "to": "2026-09"}))

    def test_october_changes_the_usd_period_but_not_the_eur_one_before_it(self):
        self.assertEqual(computed(RECORDS, {"kind": "period_total", "currency": "USD", "from": "2026-07", "to": "2026-09"}), ("0.87", 70))
        self.assertEqual(computed(RECORDS, {"kind": "period_total", "currency": "USD", "from": "2026-07", "to": BIG_MONTH}),
                         ("9007199254741838.37", 101))
        self.assertEqual(computed(RECORDS, {"kind": "period_total", "currency": "EUR", "from": "2026-07", "to": "2026-09"}), ("61580.74", 370))

    def test_every_row_of_the_dataset_has_a_date_inside_the_window_and_the_reference_date(self):
        days = [r["usage_date"] for r in RECORDS if r["subscription"].startswith(dataset.PREFIX)]
        self.assertGreaterEqual(min(days).isoformat(), MANIFEST["window"]["start"])
        self.assertLessEqual(max(days).isoformat(), MANIFEST["window"]["end"])
        self.assertLessEqual(max(days).isoformat(), REFERENCE)

    def test_grouping_keeps_the_rows_without_a_value_in_their_own_group(self):
        for group_by, keys in (("service", {"Compute": "28099.20", "Credits": "-250.00", None: "12.50"}),
                               ("project", {"Alpha": "44971.22", "Beta": "15935.60", None: "673.92"})):
            for key, expected in keys.items():
                figure = {"kind": "group_total", "currency": "EUR", "from": "2026-07", "to": "2026-09",
                          "group_by": group_by, "key": key}
                self.assertEqual(computed(RECORDS, figure)[0], expected, (group_by, key))

    def test_a_changed_amount_month_or_currency_is_reported_with_the_figure_id(self):
        figures = [{"id": "F1", "kind": "month_total", "currency": "EUR", "month": "2026-07", "expected": "19404.00", "records": 124}]
        self.assertEqual(mismatches(RECORDS, figures), [])
        for change in ({"expected": "19404.01"}, {"month": "2026-08"}, {"currency": "USD"}, {"records": 125}):
            self.assertEqual(mismatches(RECORDS, [{**figures[0], **change}]), ["F1"], change)

    def test_a_gap_month_is_reported_as_no_data_and_not_as_zero(self):
        gap = {"id": "F2", "kind": "month_total", "currency": "USD", "month": "2026-07", "expected": None, "records": 0}
        self.assertEqual(mismatches(RECORDS, [gap]), [])
        self.assertEqual(mismatches(RECORDS, [{**gap, "expected": "0.00"}]), ["F2"])
        zero = {"id": "F3", "kind": "month_total", "currency": "USD", "month": "2026-08", "expected": "0.00", "records": 31}
        self.assertEqual(mismatches(RECORDS, [zero]), [])

    def test_a_comparison_that_cannot_be_made_is_stated_as_unavailable(self):
        figure = {"id": "F4", "kind": "comparison", "currency": "USD", "from": "2026-07", "to": "2026-09", "unavailable": True}
        self.assertEqual(mismatches(RECORDS, [figure]), [])
        self.assertIsNotNone(computed(RECORDS, {**figure, "from": "2026-09", "to": BIG_MONTH}))
        self.assertEqual(mismatches(RECORDS, [{"id": "F5", "kind": "comparison", "currency": "EUR", "from": "2026-07", "to": "2026-09",
                                               "unavailable": True}]), ["F5"])


class PackageTests(unittest.TestCase):
    """The demo package against the dataset, the spec and the neighbouring work."""

    @classmethod
    def setUpClass(cls):
        cls.package = load_package()
        cls.steps = cls.package["steps"]
        cls.main = [s for s in cls.steps if not s.get("optional")]
        cls.optional = [s for s in cls.steps if s.get("optional")]

    def read(self, name):
        return (PACKAGE / name).read_text(encoding="utf-8")

    def sections(self):
        parts = re.split(r"(?m)^### ", self.read("guion.md"))[1:]
        return {part.split()[0]: part for part in parts}

    def allowed_values(self, step_ids):
        wanted = set(step_ids)
        for step in self.steps:
            if step["id"] in step_ids:
                wanted |= set(step.get("reuses", []))
        return figure_values([f for f in self.package["figures"] if f["step"] in wanted])

    def test_every_step_is_complete_and_identifiers_are_unique(self):
        ids = [s["id"] for s in self.steps]
        self.assertEqual(len(ids), len(set(ids)))
        for step in self.steps:
            for field in ("id", "title", "seconds", "screen", "action", "say", "expect"):
                self.assertTrue(step.get(field) not in (None, ""), (step.get("id"), field))
            self.assertIsInstance(step["seconds"], int)
            self.assertGreater(step["seconds"], 0)
            self.assertRegex(step["id"], r"^D\d+$")

    def test_declared_total_matches_the_main_steps_and_the_cap_holds_with_the_optional_ones(self):
        main = sum(s["seconds"] for s in self.main)
        self.assertEqual(main, 180)
        self.assertEqual(self.package["total_seconds"], main)
        self.assertEqual(self.package["optional_seconds"], sum(s["seconds"] for s in self.optional))
        self.assertLessEqual(main + sum(s["seconds"] for s in self.optional), MAX_SECONDS)
        self.assertRegex(self.read("guion.md"), rf"Duración total:\s*{main} s")

    def test_the_synthetic_declaration_precedes_every_amount(self):
        declared = [i for i, s in enumerate(self.steps) if s.get("declares_synthetic")]
        showing = [i for i, s in enumerate(self.steps) if s.get("shows_amounts")]
        self.assertTrue(declared and showing)
        self.assertLess(min(declared), min(showing))
        for name in ("guion.md", "preparacion.md", "preguntas.md", "README.md"):
            self.assertRegex(self.read(name).lower(), "sintétic", name)
        first = self.steps[min(declared)]["id"]
        self.assertRegex(self.read("guion.md").split(f"### {first}")[1].split("### D")[0].lower(), "sintétic")

    def test_only_the_billing_screen_shows_figures_and_fixed_data_screens_are_only_named_as_limits(self):
        for step in self.steps:
            self.assertIn(step["screen"], ALLOWED_SCREENS, step["id"])
            if step.get("shows_amounts"):
                self.assertIn(step["screen"], FIGURE_SCREENS, step["id"])
                if step["screen"] == "anomalies-panel":
                    self.assertEqual(step["id"], "D12")
        limits = [s["id"] for s in self.steps if s.get("limits")]
        self.assertEqual(len(limits), 1)
        for section in re.split(r"(?m)^### ", self.read("guion.md"))[1:]:
            owner = section.split()[0]
            for route in FIXED_DATA_ROUTES:
                if route in section:
                    self.assertEqual(owner, limits[0], (owner, route))
        self.assertTrue(any(route in self.read("guion.md") for route in FIXED_DATA_ROUTES))

    def test_the_main_route_stops_before_the_very_large_month_and_the_optional_step_names_it(self):
        for step in self.main:
            if step.get("period"):
                self.assertLess(step["period"]["to"], BIG_MONTH, step["id"])
        self.assertEqual({s["id"] for s in self.optional}, {"D7", "D11"})
        big = [s for s in self.optional if s.get("period", {}).get("from") == BIG_MONTH]
        self.assertEqual(len(big), 1)
        self.assertEqual(big[0]["period"], {"from": BIG_MONTH, "to": BIG_MONTH})
        self.assertIn(BIG_MONTH, self.read("guion.md"))

    def test_every_figure_belongs_to_a_step_and_equals_the_independent_computation(self):
        figures = self.package["figures"]
        ids = {s["id"] for s in self.steps}
        self.assertEqual(len({f["id"] for f in figures}), len(figures))
        for figure in figures:
            self.assertIn(figure["step"], ids, figure["id"])
        self.assertEqual(mismatches(RECORDS, figures), [])
        self.assertEqual({f["kind"] for f in figures}, {"month_total", "period_total", "group_total", "comparison", "anomaly_episode"})

    def test_the_route_covers_the_cases_the_dataset_exists_for(self):
        figures = self.package["figures"]
        month_totals = {(f["currency"], f["month"]): f["expected"] for f in figures if f["kind"] == "month_total"}
        self.assertEqual(month_totals[("USD", "2026-07")], None)
        self.assertEqual(month_totals[("USD", "2026-08")], "0.00")
        self.assertEqual(month_totals[("EUR", "2026-07")], "19404.00")
        self.assertEqual(month_totals[("USD", BIG_MONTH)], "9007199254741837.50")
        groups = {(f["currency"], f["key"]): f["expected"] for f in figures if f["kind"] == "group_total" and f["group_by"] == "service"}
        self.assertEqual(groups[("EUR", "Credits")], "-250.00")
        self.assertEqual(groups[("USD", "Archive")], "9007199254740993.00")
        self.assertIsNone(groups.get(("EUR", None)) and None)
        comparisons = {f["currency"]: (f.get("difference"), f.get("percent"), f.get("unavailable")) for f in figures if f["kind"] == "comparison"}
        self.assertEqual(comparisons, {"EUR": ("2351.54", "12.12", None), "USD": (None, None, True)})

    def test_the_route_assumes_the_reference_date_the_data_end_on(self):
        self.assertEqual(self.package["reference_date"], REFERENCE)
        self.assertEqual(MANIFEST["window"]["end"], REFERENCE)
        for name in ("guion.md", "preparacion.md", "README.md"):
            self.assertIn("COST_REFERENCE_DATE=2026-10-30", self.read(name), name)
        self.assertIn("Fecha simulada: 30/10/2026", " ".join(self.steps[0]["ui_contains"]))

    def test_the_data_limits_are_declared_where_the_audience_reads_them(self):
        for name in ("guion.md", "README.md", "preparacion.md"):
            self.assertRegex(self.read(name), r"servicio y (la )?etiqueta `?Project`?", name)
        for field in ("grupo de recursos", "centro de coste"):
            self.assertIn(field, self.read("README.md"))
        limits = next(s for s in self.steps if s.get("limits"))
        for word in ("servicio y proyecto", "centro de coste", "propietario", "aplicación"):
            self.assertIn(word, limits["say"] + " " + limits["expect"], word)

    def test_questions_point_to_existing_steps_and_cover_the_topics(self):
        text = self.read("preguntas.md")
        rows = [line for line in text.splitlines() if line.startswith("|") and re.search(r"\bD\d+\b", line)]
        ids = {s["id"] for s in self.steps}
        self.assertGreaterEqual(len(rows), len(TOPICS))
        for row in rows:
            self.assertTrue(set(re.findall(r"\bD\d+\b", row)) <= ids, row)
        questions = " ".join(row.split("|")[1].lower() for row in rows)
        for topic in TOPICS:
            self.assertIn(topic, questions, topic)

    def test_preparation_loads_checks_removes_twice_and_does_not_share_a_stack(self):
        text = self.read("preparacion.md")
        for needle in ("demo_data.py apply", "demo_data.py status", "demo_data.py remove", "--profile demo",
                       "No pulsar «Detectar ahora» antes de la demo", "-p jup107", "down -v", "JUP-065",
                       "COST_REFERENCE_DATE=2026-10-30"):
            self.assertIn(needle, text, needle)
        self.assertGreaterEqual(text.count("demo_data.py remove"), 2)
        self.assertLess(text.index("demo_data.py apply"), text.index("demo_data.py remove"))
        self.assertNotRegex(text, r"synthetic_(costs|anomalies)\.py")

    def test_the_rehearsal_record_asks_for_who_what_and_how_it_went(self):
        text = self.read("registro-ensayo.md").lower()
        for field in ("persona", "commit", "modo", "duración", "observaciones", "fecha de referencia"):
            self.assertIn(field, text, field)
        for result in ("pass", "fail", "blocked", "not_run"):
            self.assertIn(result, text, result)
        self.assertIn("automatizada", text)
        for step in self.steps:
            self.assertIn(f"| {step['id']}", self.read("registro-ensayo.md"), step["id"])

    def test_the_package_has_only_text_files_and_the_recipe_never_fakes_requests(self):
        suffixes = {p.suffix.lower() for p in PACKAGE.rglob("*") if p.is_file()}
        self.assertLessEqual(suffixes, {".md", ".json"})
        code = "\n".join(re.findall(r"(?s)```[a-z]*\n(.*?)```", self.read("receta-navegador.md")))
        self.assertTrue(code.strip())
        self.assertNotRegex(code, r"\.route\(|\.fulfill\(|setRequestInterception")

    def test_each_guide_section_carries_the_exact_text_and_duration_of_its_step(self):
        sections = self.sections()
        self.assertEqual(list(sections), [s["id"] for s in self.steps])
        for step in self.steps:
            lines = sections[step["id"]].splitlines()
            for line in (f"- **Acción:** {step['action']}", f"- **Qué decir:** «{step['say']}»",
                         f"- **Resultado esperado:** {step['expect']}"):
                self.assertIn(line, lines, (step["id"], line[:40]))
            duration = f"- **Duración:** {step['seconds']} s" + (" (opcional, no cuenta en el total)" if step.get("optional") else "")
            self.assertIn(duration, lines, step["id"])
        declaring = [s for s in self.steps if s.get("declares_synthetic")]
        self.assertIn("sintétic", declaring[0]["say"].lower())

    def test_quantities_spoken_or_expected_belong_to_the_figures_of_their_step(self):
        for step in self.steps:
            spoken = quantities(step["say"] + " " + step["expect"])
            self.assertLessEqual(spoken, self.allowed_values([step["id"]]), step["id"])

    def test_question_rows_cite_a_step_cover_each_topic_and_quote_only_figures_of_that_step(self):
        rows = [l for l in self.read("preguntas.md").splitlines()
                if l.startswith("|") and "---" not in l and not l.startswith("| Pregunta")]
        ids = {s["id"] for s in self.steps}
        screens = {s["id"]: s["screen"] for s in self.steps}
        parsed = []
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            cited = set(re.findall(r"\bD\d+\b", cells[1]))
            self.assertTrue(cited, "pregunta sin paso: " + cells[0])
            self.assertLessEqual(cited, ids, row)
            for step_id in cited:
                self.assertIn(screens[step_id], ALLOWED_SCREENS, row)
            self.assertLessEqual(quantities(cells[2]), self.allowed_values(cited), row)
            parsed.append((cells[0].lower(), cited))
        for topic, expected in TOPIC_STEPS.items():
            matching = [cited for question, cited in parsed if topic in question]
            self.assertTrue(matching, topic)
            for cited in matching:
                self.assertTrue(cited & expected, (topic, cited))

    def test_menu_names_of_fixed_data_screens_appear_only_in_the_limits_step(self):
        limits = next(s["id"] for s in self.steps if s.get("limits"))
        for step in self.steps:
            if step["id"] == limits:
                continue
            text = " ".join(str(step.get(k, "")) for k in ("title", "action", "say", "expect")).lower()
            for name in NAV_NAMES:
                self.assertNotIn(name, text, (step["id"], name))
        for step_id, section in self.sections().items():
            if step_id != limits:
                for name in NAV_NAMES:
                    self.assertNotIn(name, section.lower(), (step_id, name))

    def test_the_readme_does_not_claim_a_single_screen_reads_the_costs(self):
        readme = self.read("README.md")
        self.assertIn("/overview-legacy", readme)
        self.assertNotIn("Solo el dashboard ejecutivo", readme)

    def test_preparation_warns_about_ports_and_checks_the_api_before_and_after(self):
        text = self.read("preparacion.md")
        for needle in ("puertos", "5173", "CORS", "start_date=2026-07-01&end_date=2026-10-01", "X-Tenant-Id",
                       "data_status: partial", "EUR 61580.74 370", "USD 0.87 70", "EUR 79337.00 569", "data_status: empty"):
            self.assertIn(needle, text, needle)
        snippet = text.split("```python")[1].split("```")[0]
        self.assertNotRegex(snippet, r"print\([^)]*(PASSWORD|password)")
        self.assertIn('os.environ["DEMO_PASSWORD"]', snippet)

    def test_the_recipe_watches_failed_requests_and_error_responses_and_scopes_the_tenant_by_label(self):
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        for needle in ("requestfailed", "page.on('response'", "status() >= 400", "getByLabel('Ámbito de cliente')"):
            self.assertIn(needle, code, needle)
        self.assertNotIn("locator('select')", code)
        self.assertNotRegex(code, r"addInitScript|routeFromHAR|unroute|console\.\w+\([^)]*\bPASSWORD\b")

    def test_the_recipe_uses_the_periods_clients_and_keys_of_the_new_route(self):
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        for needle in ("setPeriod('2026-07', '2026-09')", "setPeriod('2026-10', '2026-10')", "fill('project')",
                       "Comparación no disponible", "page.innerText('body')"):
            self.assertIn(needle, code, needle)
        for stale in ("2026-01", "cost_center", "undated", "synthetic_"):
            self.assertNotIn(stale, code, stale)

    def test_no_file_of_the_package_holds_a_secret_like_assignment(self):
        for path in PACKAGE.iterdir():
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(SECRET.search(text), path.name)
            self.assertIsNone(SECRET_PROSE.search(text), path.name)

    def test_no_default_period_claim_that_depends_on_todays_date(self):
        for step in self.steps:
            text = " ".join(str(step.get(k, "")) for k in ("action", "say", "expect"))
            self.assertNotRegex(text, r"(?i)\bhoy\b", step["id"])
        self.assertNotRegex(self.read("guion.md"), r"(?i)\bhoy\b")

    def test_the_first_step_is_taken_with_no_amount_on_screen_and_the_preparation_says_how(self):
        first = self.steps[0]
        self.assertTrue(first.get("no_amounts"))
        self.assertIn("Core Finance", first["action"])
        self.assertRegex(self.read("preparacion.md"), r"Core Finance[^\n]*sin cifras|sin cifras[^\n]*Core Finance")
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        self.assertIn("no_amounts", code)

    def test_no_document_claims_a_rehearsal_that_has_no_record(self):
        for path in PACKAGE.iterdir():
            if path.name == "registro-ensayo.md":
                continue
            self.assertIsNone(REHEARSAL_CLAIM.search(path.read_text(encoding="utf-8")), path.name)

    def test_the_qualitative_claims_of_the_key_steps_and_answers_are_pinned(self):
        say = {s["id"]: s["say"] for s in self.steps}
        for step_id, pattern in STEP_CLAIMS.items():
            self.assertRegex(say[step_id], pattern, step_id)
        rows = [l for l in self.read("preguntas.md").splitlines()
                if l.startswith("|") and "---" not in l and not l.startswith("| Pregunta")]
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            for topic, words in ANSWER_CLAIMS.items():
                if topic in cells[0].lower():
                    for word in words:
                        self.assertIn(word, cells[2], (topic, word))

    def test_the_gap_in_the_chart_is_checked_by_the_recipe_and_flagged_in_the_step(self):
        step = next(s for s in self.steps if s["id"] == "D4")
        self.assertTrue(step.get("chart_gap"))
        self.assertIn("USD", step["action"])
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        self.assertIn("chart_gap", code)

    def test_the_preparation_checks_the_other_client_and_gives_the_powershell_variant(self):
        text = self.read("preparacion.md")
        self.assertIn("tenant-core", text)
        self.assertIn('os.environ.get("TENANT"', text)
        self.assertRegex(text, r"Get-Content -Raw resumen\.py \| docker compose")

    def test_the_tool_messages_quoted_by_the_preparation_are_what_the_tool_prints(self):
        text = self.read("preparacion.md")
        store = loader_tests.FakeStore()
        env = {"DATABASE_URL": "cockroachdb://u:pw@host/db", "RUNTIME_ENVIRONMENT": "development"}

        def run(command):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = loader.main([command], env=env, store_factory=lambda url: store, ingest=loader_tests.FakeIngest(store))
            return code, out.getvalue().strip()

        absent = run("status")
        self.assertIn("tenant-core: absent", absent[1])
        applied = run("apply")
        self.assertEqual(applied[0], 0)
        records = sum(pair["stored_rows"] for pair in MANIFEST["pairs"])
        self.assertEqual(applied[1], "loaded: 7 parejas tenant/suscripcion con datos sinteticos o de fechas desplazadas, no son facturas de Azure.")
        self.assertIn("tenant-core: present", run("status")[1])
        first, second = run("remove"), run("remove")
        self.assertEqual(first, (0, f"Retirados 7 ingestas, {records} registros y 0 episodios de anomalia derivados de ellos."))
        self.assertEqual(second, (0, "Retirados 0 ingestas, 0 registros y 0 episodios de anomalia derivados de ellos."))
        for quoted in (applied[1], f"Retirados 7 ingestas, {records} registros y", second[1], "tenant-core: absent", "`present`"):
            self.assertIn(quoted, text, quoted)

    def test_the_literals_the_recipe_looks_for_are_tied_to_the_figures_and_periods(self):
        steps = {s["id"]: s for s in self.steps}
        figures = self.package["figures"]
        missing = next(f for f in figures if f["kind"] == "group_total" and f["group_by"] == "service" and f["key"] is None)
        self.assertIn(f"{missing['records']} registros sin dimensión; 0 registros sin fecha excluidos", " ".join(steps["D8"]["ui_contains"]))
        keys = {f["group_by"] for f in figures if f["step"] == "D7"}
        self.assertEqual(keys, {"project"})
        self.assertIn("Etiqueta consultada: project", steps["D7"]["ui_contains"])
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre"]
        period = steps["D2"]["period"]
        label = lambda ym: f"{months[int(ym[5:7]) - 1]} de {ym[:4]}"
        self.assertIn(f"{label(period['from'])} – {label(period['to'])} (UTC)", steps["D2"]["ui_contains"])
        comparison = next(f for f in figures if f["kind"] == "comparison" and not f.get("unavailable"))
        self.assertIn(f"Comparación: {label(comparison['last_month'])} frente a {label(comparison['first_month'])}", " ".join(steps["D5"]["ui_contains"]))

    def test_the_azure_labels_on_the_screen_are_announced_and_answered(self):
        step = next(s for s in self.steps if s.get("declares_synthetic"))
        self.assertRegex(step["say"], r"rótulos[^.]*Azure")
        rows = [l for l in self.read("preguntas.md").splitlines()
                if l.startswith("|") and len(l.split("|")) > 3 and "azure" in l.split("|")[1].lower()]
        self.assertTrue(rows, "falta la pregunta sobre los rótulos de Azure")
        self.assertIn("demostración", rows[0].split("|")[3].lower())

    def test_the_first_step_checks_the_active_client_and_not_only_the_absence_of_amounts(self):
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        block = code.split("if (step.no_amounts)")[1].split("if (step.chart_gap)")[0]
        self.assertIn("inputValue()", block)
        self.assertIn("tenant-core", block)

    def test_the_cautions_that_keep_the_demo_honest_are_pinned_in_the_documents(self):
        questions = self.read("preguntas.md")
        self.assertIn("Es una demostración visual; el aislamiento está cubierto por sus propias pruebas", questions)
        self.assertNotRegex(questions, r"(?i)prueba de autorización completa")
        self.assertIn("Parar antes cualquier otro stack", self.read("preparacion.md"))
        self.assertIn("no sustituye una prueba de autorización", self.read("guion.md"))

    def test_the_preparation_does_not_call_the_ports_fixed(self):
        self.assertNotIn("puertos fijos", self.read("preparacion.md"))

    def test_the_anomalies_step_follows_isolation_and_is_tied_to_the_anomaly_dataset(self):
        ids = [s["id"] for s in self.steps]
        self.assertEqual(ids[ids.index("D9") + 1], "D12")
        step = next(s for s in self.steps if s["id"] == "D12")
        self.assertEqual(step["screen"], "anomalies-panel")
        self.assertEqual(step["first_row"], "Compute")
        self.assertIn("Candidata: causa no establecida", step["dialog_contains"])
        detection = json.loads(ANOMALY_EXPECTED.read_text(encoding="utf-8"))["episodes_by_reference"][REFERENCE]["last_evaluated_date"]
        day, month, year = detection[8:10], detection[5:7], detection[:4]
        self.assertIn(f"Revisado hasta el {day}/{month}/{year}", step["ui_contains"])
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        for needle in ("first_row", "dialog_contains", "anomaly_episode", "Detectar ahora"):
            self.assertIn(needle, code, needle)

    def test_the_anomalies_panel_is_no_longer_presented_as_fixed_data(self):
        limits = next(s for s in self.steps if s.get("limits"))
        text = " ".join(str(limits.get(k, "")) for k in ("say", "expect"))
        self.assertNotIn("/anomalies", text)
        self.assertNotIn("anomal", text.lower())
        self.assertNotIn("/anomalies", self.sections()[limits["id"]])

    def test_the_first_step_is_taken_on_the_anomalies_panel_before_any_detection(self):
        first = self.steps[0]
        self.assertEqual(first["screen"], "anomalies-panel")
        self.assertIn("Todavía no se han buscado anomalías en este cliente", first["ui_contains"])

    def test_the_route_has_no_step_on_a_record_without_a_date_because_the_dataset_has_none(self):
        self.assertFalse(any("sin fecha" in s["say"] for s in self.steps))
        self.assertTrue(all(r["usage_date"] is not None for r in RECORDS))
        self.assertIn("0 registros sin fecha excluidos", " ".join(next(s for s in self.steps if s["id"] == "D8")["ui_contains"]))


if __name__ == "__main__":
    unittest.main()
