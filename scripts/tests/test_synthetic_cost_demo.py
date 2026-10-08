from __future__ import annotations

import importlib.util
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
MAX_SECONDS = 240
BIG_MONTH = "2026-07"
ALLOWED_SCREENS = {"none", "billing-dashboard"}
FIXED_DATA_ROUTES = ("/anomalies", "/recommendations", "/cuts", "/operational")
TOPICS = ("moneda", "hueco", "cero", "crédito", "grande", "cliente", "etiqueta")


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
        self.assertEqual(self.package["total_seconds"], main)
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
                self.assertEqual(step["screen"], "billing-dashboard", step["id"])
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
        self.assertEqual(len(self.optional), 1)
        self.assertEqual(self.optional[0]["period"], {"from": BIG_MONTH, "to": BIG_MONTH})
        self.assertIn(BIG_MONTH, self.read("guion.md"))

    def test_every_figure_belongs_to_a_step_and_equals_the_independent_computation(self):
        figures = self.package["figures"]
        ids = {s["id"] for s in self.steps}
        self.assertEqual(len({f["id"] for f in figures}), len(figures))
        for figure in figures:
            self.assertIn(figure["step"], ids, figure["id"])
        self.assertEqual(mismatches(dataset(), figures), [])
        covered = {f["kind"] for f in figures}
        self.assertEqual(covered, {"month_total", "period_total", "group_total", "comparison", "undated"})

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
                       "-p jup107", "down -v", "JUP-065"):
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


if __name__ == "__main__":
    unittest.main()
