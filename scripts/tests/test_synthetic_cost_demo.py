from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs" / "demo" / "JUP-107"
SCRIPT_PATH = ROOT / "scripts" / "synthetic_costs.py"
SPEC = importlib.util.spec_from_file_location("economicon_synthetic_costs_for_demo", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
costs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = costs
SPEC.loader.exec_module(costs)

TENANT = "tenant-growth"
TOOL_TESTS_PATH = ROOT / "scripts" / "tests" / "test_synthetic_costs.py"
TOOL_SPEC = importlib.util.spec_from_file_location("economicon_synthetic_costs_tests_for_demo", TOOL_TESTS_PATH)
assert TOOL_SPEC is not None and TOOL_SPEC.loader is not None
TOOL_TESTS = importlib.util.module_from_spec(TOOL_SPEC)
sys.modules[TOOL_SPEC.name] = TOOL_TESTS
TOOL_SPEC.loader.exec_module(TOOL_TESTS)
MAX_SECONDS = 240
BIG_MONTH = "2026-07"
ALLOWED_SCREENS = {"none", "billing-dashboard", "anomalies-panel"}
FIGURE_SCREENS = {"billing-dashboard", "anomalies-panel"}
FIXED_DATA_ROUTES = ("/recommendations", "/cuts", "/operational")
TOPICS = ("moneda", "hueco", "cero", "crédito", "grande", "cliente", "etiqueta", "anomalía")
ANOMALY_EXPECTED = PACKAGE / "esperados-anomalias.json"


def month_of(day) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def dated(records, currency, start, end):
    return [r for r in records if r["currency"] == currency and r["usage_date"] is not None
            and start <= month_of(r["usage_date"]) <= end]


def total(rows):
    return sum((r["pretax_cost"] for r in rows), Decimal("0"))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01")))


def group_key(record, group_by):
    if group_by == "service":
        return record["service_name"]
    if group_by == "cost_center":
        return record["tags"].get("cost_center")
    raise AssertionError(f"grouping not supported by the demo: {group_by}")


def compare(month_totals: dict[str, Decimal]):
    # Same endpoint rule as the JUP-106 guide: first and last month with a non-zero cost.
    months = sorted(m for m, value in month_totals.items() if value != 0)
    if len(months) < 2:
        return None
    first, last = months[0], months[-1]
    difference = month_totals[last] - month_totals[first]
    percent = (difference / month_totals[first] * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return first, last, difference, percent


def computed(records, figure):
    kind, currency = figure["kind"], figure.get("currency")
    if kind == "month_total":
        rows = dated(records, currency, figure["month"], figure["month"])
        return (money(total(rows)), len(rows)) if rows else (None, 0)
    if kind == "period_total":
        rows = dated(records, currency, figure["from"], figure["to"])
        return money(total(rows)), len(rows)
    if kind == "group_total":
        rows = [r for r in dated(records, currency, figure["from"], figure["to"])
                if group_key(r, figure["group_by"]) == figure["key"]]
        return money(total(rows)), len(rows)
    if kind == "comparison":
        rows = dated(records, currency, figure["from"], figure["to"])
        months: dict[str, Decimal] = {}
        for r in rows:
            months[month_of(r["usage_date"])] = months.get(month_of(r["usage_date"]), Decimal("0")) + r["pretax_cost"]
        result = compare(months)
        return None if result is None else (result[0], result[1], money(result[2]), str(result[3]))
    if kind == "undated":
        rows = [r for r in records if r["currency"] == currency and r["usage_date"] is None]
        return money(total(rows)), len(rows)
    if kind == "anomaly_episode":
        # Verified independently by test_synthetic_anomalies.py against the JUP-107 anomaly dataset.
        episodes = json.loads(ANOMALY_EXPECTED.read_text(encoding="utf-8"))["episodes"]
        found = [e for e in episodes if e["service"] == figure["service"] and e["severity"] == figure["severity"]]
        return (found[0]["accumulated_impact"], found[0]["impact_day_count"]) if len(found) == 1 else None
    raise AssertionError(f"unknown figure kind: {kind}")


def stated(figure):
    kind = figure["kind"]
    if kind == "comparison":
        return figure["first_month"], figure["last_month"], figure["difference"], figure["percent"]
    return figure["expected"], figure["records"]


def mismatches(records, figures):
    found = []
    for figure in figures:
        if computed(records, figure) != stated(figure):
            found.append(figure["id"])
    return found


# Any decimal number, and an integer only when it carries a unit.
QUANTITY = re.compile(r"(?<![\w.])(\d+[.,]\d+|\d+(?=\s*(?:euros|dólares|por ciento|EUR|USD|%)))")
SECRET_PROSE = re.compile(r"(?i)(contraseña|password)\s+(es|is)\s+\S{4,}|(contraseña|password)\s*[:=]\s*(?!process\.env)[^<\s'\"]\S{3,}")
REHEARSAL_CLAIM = re.compile(r"(?i)\b(se ensayó|ensayó|ensayaron|hemos ensayado|fue ensayada|ha sido ensayada)\b")
STEP_CLAIMS = {
    "D4": r"[Ff]ebrero tiene un cero registrado y marzo no tiene ningún dato",
    "D5": r"[Mm]ayo es un crédito",
    "D9": r"al cambiar a Core Finance no aparece ninguno",
    "D12": r"candidata para investigar, no una causa confirmada",
}
ANSWER_CLAIMS = {
    "moneda": ("EUR", "USD"), "cero": ("cero",), "crédito": ("-50.00",), "cliente": ("No:", "no aparece"),
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


def dataset():
    return costs.build_dataset(TENANT)[1]


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
        records = dataset()
        eur = {m: total(dated(records, "EUR", m, m)) for m in ("2026-01", "2026-02", "2026-04", "2026-05")}
        self.assertEqual(eur, {"2026-01": Decimal("100.00"), "2026-02": Decimal("0.00"),
                               "2026-04": Decimal("40.00"), "2026-05": Decimal("-50.00")})
        self.assertEqual(computed(records, {"kind": "comparison", "currency": "EUR", "from": "2026-01", "to": "2026-06"}),
                         ("2026-01", "2026-05", "-150.00", "-150.00"))
        self.assertEqual(computed(records, {"kind": "comparison", "currency": "USD", "from": "2026-01", "to": "2026-06"}),
                         ("2026-02", "2026-06", "14.75", "140.48"))

    def test_july_changes_the_usd_period_but_not_the_eur_one(self):
        records = dataset()
        self.assertEqual(computed(records, {"kind": "period_total", "currency": "USD", "from": "2026-01", "to": "2026-06"}),
                         ("35.75", 2))
        self.assertEqual(computed(records, {"kind": "period_total", "currency": "USD", "from": "2026-01", "to": BIG_MONTH}),
                         ("9007199254741028.76", 3))
        self.assertEqual(computed(records, {"kind": "period_total", "currency": "EUR", "from": "2026-01", "to": BIG_MONTH}),
                         computed(records, {"kind": "period_total", "currency": "EUR", "from": "2026-01", "to": "2026-06"}))

    def test_the_undated_record_is_outside_every_period_and_counted_once(self):
        records = dataset()
        self.assertEqual(computed(records, {"kind": "undated", "currency": "EUR"}), ("7.77", 1))
        self.assertEqual(computed(records, {"kind": "undated", "currency": "USD"}), ("0.00", 0))
        self.assertEqual(computed(records, {"kind": "period_total", "currency": "EUR", "from": "2026-01", "to": "2026-12"}),
                         ("90.00", 6))

    def test_grouping_keeps_the_rows_without_a_value_in_their_own_group(self):
        records = dataset()
        for group_by, keys in (("service", {"Compute": "100.00", "Storage": "30.00", "Credits": "-50.00", None: "10.00"}),
                               ("cost_center", {"finance": "100.00", "ops": "-20.00", None: "10.00"})):
            for key, expected in keys.items():
                figure = {"kind": "group_total", "currency": "EUR", "from": "2026-01", "to": "2026-06",
                          "group_by": group_by, "key": key}
                self.assertEqual(computed(records, figure)[0], expected, (group_by, key))

    def test_a_changed_amount_month_or_currency_is_reported_with_the_figure_id(self):
        figures = [{"id": "F1", "kind": "month_total", "currency": "EUR", "month": "2026-01", "expected": "100.00", "records": 2}]
        self.assertEqual(mismatches(dataset(), figures), [])
        for change in ({"expected": "100.01"}, {"month": "2026-02"}, {"currency": "USD"}, {"records": 3}):
            self.assertEqual(mismatches(dataset(), [{**figures[0], **change}]), ["F1"], change)

    def test_a_gap_month_is_reported_as_no_data_and_not_as_zero(self):
        gap = {"id": "F2", "kind": "month_total", "currency": "EUR", "month": "2026-03", "expected": None, "records": 0}
        self.assertEqual(mismatches(dataset(), [gap]), [])
        self.assertEqual(mismatches(dataset(), [{**gap, "expected": "0.00"}]), ["F2"])


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

    def test_every_step_is_complete_and_identifiers_are_unique(self):
        ids = [s["id"] for s in self.steps]
        self.assertEqual(len(ids), len(set(ids)))
        for step in self.steps:
            for field in ("id", "title", "seconds", "screen", "action", "say", "expect"):
                self.assertTrue(step.get(field) not in (None, ""), (step.get("id"), field))
            self.assertIsInstance(step["seconds"], int)
            self.assertGreater(step["seconds"], 0)
            self.assertRegex(step["id"], r"^D\d+$")

    def test_declared_total_matches_the_main_steps_and_the_cap_holds_with_the_optional_one(self):
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
        guion = self.read("guion.md")
        for name in ("guion.md", "preparacion.md", "preguntas.md", "README.md"):
            self.assertRegex(self.read(name).lower(), "sintétic", name)
        first = self.steps[min(declared)]["id"]
        self.assertRegex(guion.split(f"### {first}")[1].split("### D")[0].lower(), "sintétic")

    def test_only_the_billing_screen_shows_figures_and_fixed_data_screens_are_only_named_as_limits(self):
        for step in self.steps:
            self.assertIn(step["screen"], ALLOWED_SCREENS, step["id"])
            if step.get("shows_amounts"):
                self.assertIn(step["screen"], FIGURE_SCREENS, step["id"])
                if step["screen"] == "anomalies-panel":
                    self.assertEqual(step["id"], "D12")
        limits = [s["id"] for s in self.steps if s.get("limits")]
        self.assertEqual(len(limits), 1)
        sections = re.split(r"(?m)^### ", self.read("guion.md"))[1:]
        for section in sections:
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
        self.assertEqual(mismatches(dataset(), figures), [])
        covered = {f["kind"] for f in figures}
        self.assertEqual(covered, {"month_total", "period_total", "group_total", "comparison", "undated", "anomaly_episode"})

    def test_the_route_covers_the_cases_the_dataset_exists_for(self):
        figures = self.package["figures"]
        month_totals = {(f["currency"], f["month"]): f["expected"] for f in figures if f["kind"] == "month_total"}
        self.assertEqual(month_totals[("EUR", "2026-03")], None)
        self.assertEqual(month_totals[("EUR", "2026-02")], "0.00")
        self.assertEqual(month_totals[("EUR", "2026-05")], "-50.00")
        self.assertEqual(month_totals[("USD", BIG_MONTH)], "9007199254740993.01")
        comparisons = {f["currency"]: (f["difference"], f["percent"]) for f in figures if f["kind"] == "comparison"}
        self.assertEqual(comparisons, {"EUR": ("-150.00", "-150.00"), "USD": ("14.75", "140.48")})

    def test_questions_point_to_existing_steps_and_cover_the_topics(self):
        text = self.read("preguntas.md")
        rows = [line for line in text.splitlines() if line.startswith("|") and re.search(r"\bD\d+\b", line)]
        ids = {s["id"] for s in self.steps}
        self.assertGreaterEqual(len(rows), len(TOPICS))
        for row in rows:
            cited = set(re.findall(r"\bD\d+\b", row))
            self.assertTrue(cited <= ids, row)
        questions = " ".join(row.split("|")[1].lower() for row in rows)
        for topic in TOPICS:
            self.assertIn(topic, questions, topic)

    def test_preparation_loads_checks_removes_twice_and_does_not_share_a_stack(self):
        text = self.read("preparacion.md")
        for needle in ("python - apply < scripts/synthetic_costs.py", "python - status < scripts/synthetic_costs.py",
                       "python - apply < scripts/synthetic_anomalies.py", "python - remove < scripts/synthetic_anomalies.py",
                       "No pulsar «Detectar ahora» antes de la demo", "-p jup107", "down -v", "JUP-065"):
            self.assertIn(needle, text, needle)
        self.assertGreaterEqual(text.count("python - remove < scripts/synthetic_costs.py"), 2)
        self.assertLess(text.index("python - apply <"), text.index("python - remove <"))

    def test_the_rehearsal_record_asks_for_who_what_and_how_it_went(self):
        text = self.read("registro-ensayo.md").lower()
        for field in ("persona", "commit", "modo", "duración", "observaciones"):
            self.assertIn(field, text, field)
        for result in ("pass", "fail", "blocked", "not_run"):
            self.assertIn(result, text, result)
        self.assertIn("automatizada", text)

    def test_the_package_has_only_text_files_and_the_recipe_never_fakes_requests(self):
        suffixes = {p.suffix.lower() for p in PACKAGE.rglob("*") if p.is_file()}
        self.assertLessEqual(suffixes, {".md", ".json"})
        blocks = re.findall(r"(?s)```[a-z]*\n(.*?)```", self.read("receta-navegador.md"))
        code = "\n".join(blocks)
        self.assertTrue(code.strip())
        self.assertNotRegex(code, r"\.route\(|\.fulfill\(|setRequestInterception")


    def sections(self):
        parts = re.split(r"(?m)^### ", self.read("guion.md"))[1:]
        return {part.split()[0]: part for part in parts}

    def allowed_values(self, step_ids):
        wanted = set(step_ids)
        for step in self.steps:
            if step["id"] in step_ids:
                wanted |= set(step.get("reuses", []))
        return figure_values([f for f in self.package["figures"] if f["step"] in wanted])

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
        for needle in ("puertos", "5173", "CORS", "start_date=2026-01-01&end_date=2026-07-01", "X-Tenant-Id",
                       "data_status: partial", "EUR 90.00 6", "USD 35.75 2", "data_status: empty"):
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
        preparation = self.read("preparacion.md")
        self.assertRegex(preparation, r"Core Finance[^\n]*sin cifras|sin cifras[^\n]*Core Finance")
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
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        self.assertIn("chart_gap", code)

    def test_the_preparation_checks_the_other_client_and_gives_the_powershell_variant(self):
        text = self.read("preparacion.md")
        self.assertIn("tenant-core", text)
        self.assertIn('os.environ.get("TENANT"', text)
        self.assertRegex(text, r"Get-Content -Raw resumen\.py \| docker compose")

    def test_the_tool_messages_quoted_by_the_preparation_are_what_the_tool_prints(self):
        text = self.read("preparacion.md")
        store = TOOL_TESTS.FakeStore()
        env = {"DATABASE_URL": "cockroachdb://u:pw@host/db"}

        def run(command):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = costs.main([command], env=env, store_factory=lambda url: store)
            return code, out.getvalue().strip()

        self.assertEqual(run("status")[1].split(":")[1].split(",")[0].strip(), "estado absent")
        applied = run("apply")
        self.assertEqual(applied, (0, "loaded: 2 ingestas y 10 registros en tenant-growth."))
        first, second = run("remove"), run("remove")
        self.assertEqual(first, (0, "Retiradas 2 ingestas y 10 registros sinteticos."))
        self.assertEqual(second, (0, "Retiradas 0 ingestas y 0 registros sinteticos."))
        for quoted in (applied[1].rstrip("."), first[1], second[1], "absent"):
            self.assertIn(quoted, text, quoted)

    def test_the_literals_the_recipe_looks_for_are_tied_to_the_figures_and_periods(self):
        steps = {s["id"]: s for s in self.steps}
        figures = self.package["figures"]
        undated = next(f for f in figures if f["kind"] == "undated")
        self.assertIn(f"{undated['records']} registros sin fecha excluidos", steps["D8"]["ui_contains"])
        keys = {f["group_by"] for f in figures if f["step"] == "D7"}
        self.assertEqual(keys, {"cost_center"})
        self.assertIn("Etiqueta consultada: cost_center", steps["D7"]["ui_contains"])
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio"]
        period = steps["D2"]["period"]
        label = lambda ym: f"{months[int(ym[5:7]) - 1]} de {ym[:4]}"
        self.assertIn(f"{label(period['from'])} – {label(period['to'])} (UTC)", steps["D2"]["ui_contains"])

    def test_the_azure_labels_on_the_screen_are_announced_and_answered(self):
        step = next(s for s in self.steps if s.get("declares_synthetic"))
        self.assertRegex(step["say"], r"rótulos[^.]*Azure")
        rows = [l for l in self.read("preguntas.md").splitlines()
                if l.startswith("|") and len(l.split("|")) > 3 and "azure" in l.split("|")[1].lower()]
        self.assertTrue(rows, "falta la pregunta sobre los rótulos de Azure")
        self.assertIn("sintétic", rows[0].split("|")[3].lower())

    def test_the_first_step_checks_the_active_client_and_not_only_the_absence_of_amounts(self):
        code = "\n".join(re.findall(r"(?s)```js\n(.*?)```", self.read("receta-navegador.md")))
        block = code.split("if (step.no_amounts)")[1].split("if (step.chart_gap)")[0]
        self.assertIn("inputValue()", block)
        self.assertIn("tenant-core", block)

    def test_the_cautions_that_keep_the_demo_honest_are_pinned_in_the_documents(self):
        questions = self.read("preguntas.md")
        self.assertIn("Es una demostración visual; el aislamiento está cubierto por sus propias pruebas", questions)
        self.assertNotRegex(questions, r"(?i)prueba de autorización completa")
        preparation = self.read("preparacion.md")
        self.assertIn("Parar antes cualquier otro stack", preparation)
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
        detection = json.loads(ANOMALY_EXPECTED.read_text(encoding="utf-8"))["detection"]["last_evaluated_date"]
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
        fixed = self.read("README.md").split("usan datos fijos")[0].splitlines()[-1]
        self.assertNotIn("Anomalías", fixed.split("Las pantallas de")[-1])

    def test_the_first_step_is_taken_on_the_anomalies_panel_before_any_detection(self):
        first = self.steps[0]
        self.assertEqual(first["screen"], "anomalies-panel")
        self.assertIn("Todavía no se han buscado anomalías en este cliente", first["ui_contains"])

    def test_the_undated_amount_is_not_spoken_because_the_screen_only_shows_the_count(self):
        step = next(s for s in self.steps if s["id"] == "D8")
        self.assertNotIn("7,77", step["say"])
        self.assertIn("no se muestra en pantalla", step["expect"])


if __name__ == "__main__":
    unittest.main()
