"""Cifras de la memoria afectadas, plan de reejecución y plantilla del informe de JUP-133 (grupo 3).

La lista de cifras (`docs/validation/model-change-memory-figures.json`) enlaza cada cifra con una medida del
inventario o la declara «sin origen verificable». El plan y la plantilla se comprueban en lo que la spec exige:
presupuesto máximo escrito, autorización sin conceder el gasto, «No medido» en lugar de 0 % y reglas de lectura.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "validation" / "model-change-memory-figures.json"
INVENTORY = ROOT / "docs" / "validation" / "model-dependence-inventory.json"
PLAN = ROOT / "docs" / "validation" / "model-reevaluation-plan.md"
TEMPLATE = ROOT / "docs" / "validation" / "model-reevaluation-report-template.md"

STATUSES = ("cambia", "obsoleta_sin_sustituto", "se_mantiene", "sin_origen_verificable")
SECTIONS = set("abcdefghi")
NO_EVIDENCE = "no consta en el repositorio"
FIGURE_KEYS = {"id", "sections", "figure", "previous_value", "new_value", "status", "inventory_id", "evidence", "note"}


class FiguresError(ValueError):
    pass


def validate_figures(data: dict, inventory_ids: set[str], root: Path = ROOT) -> None:
    if set(data) != {"figures_version", "source_note", "figures"} or data["figures_version"] != 1:
        raise FiguresError("la raíz debe tener figures_version 1, source_note y figures")
    seen: set[str] = set()
    for index, item in enumerate(data["figures"]):
        where = f"figures[{index}]"
        if set(item) != FIGURE_KEYS:
            raise FiguresError(f"{where}: claves {sorted(set(item) ^ FIGURE_KEYS)} desconocidas o ausentes")
        if item["id"] in seen:
            raise FiguresError(f"{where}: id repetido {item['id']!r}")
        seen.add(item["id"])
        if item["status"] not in STATUSES:
            raise FiguresError(f"{where}.status: {item['status']!r} no es uno de {list(STATUSES)}")
        if not item["sections"] or not set(item["sections"]) <= SECTIONS:
            raise FiguresError(f"{where}.sections: deben ser apartados de a a i")
        for key in ("figure", "previous_value", "new_value", "note", "evidence"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise FiguresError(f"{where}.{key}: debe ser una cadena no vacía")
        missing_ok = item["evidence"] == NO_EVIDENCE and item["status"] == "sin_origen_verificable"
        if not missing_ok and not (root / item["evidence"]).exists():
            raise FiguresError(f"{where}.evidence: {item['evidence']!r} no existe")
        linked = item["inventory_id"]
        if linked is None:
            if item["status"] != "sin_origen_verificable":
                raise FiguresError(f"{where}: una cifra sin medida del inventario debe constar «sin_origen_verificable»")
        elif linked not in inventory_ids:
            raise FiguresError(f"{where}.inventory_id: {linked!r} no está en el inventario")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FiguresTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load(FIGURES)
        self.inventory = {entry["id"]: entry for entry in load(INVENTORY)["entries"]}

    def test_real_list_is_valid(self) -> None:
        validate_figures(self.data, set(self.inventory))

    def test_every_figure_links_to_the_inventory_or_says_it_has_no_origin(self) -> None:
        for item in self.data["figures"]:
            if item["inventory_id"] is None:
                self.assertEqual(item["status"], "sin_origen_verificable", item["id"])

    def test_figure_without_an_inventory_measure_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["figures"][0]["inventory_id"] = None
        with self.assertRaisesRegex(FiguresError, "sin_origen_verificable"):
            validate_figures(data, set(self.inventory))

    def test_unknown_inventory_id_fails(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["figures"][0]["inventory_id"] = "no-existe"
        with self.assertRaisesRegex(FiguresError, "no está en el inventario"):
            validate_figures(data, set(self.inventory))

    def test_unmeasured_new_values_are_never_a_number_or_zero(self) -> None:
        for item in self.data["figures"]:
            if item["status"] == "cambia":
                # O no se ha reejecutado («No medido»), o lleva el valor medido con su fecha; nunca un cero ni un número suelto.
                if item["new_value"] != "No medido":
                    self.assertRegex(item["new_value"], r"\d{1,2}/\d{2}/2026", item["id"])
                    self.assertNotRegex(item["new_value"], r"^\s*0(?:[,.]0+)?\s*(?:%|USD)?\s*$", item["id"])

    def test_independent_measures_are_kept_and_dependent_ones_change(self) -> None:
        for item in self.data["figures"]:
            linked = self.inventory.get(item["inventory_id"] or "")
            if linked is None or item["status"] == "sin_origen_verificable":
                continue
            expected = {"dependiente": "cambia", "independiente": "se_mantiene", "historica": "se_mantiene"}
            self.assertEqual(item["status"], expected[linked["class"]], item["id"])

    def test_the_list_does_not_copy_the_memory_or_its_hashes(self) -> None:
        text = FIGURES.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\b[0-9a-f]{40}\b")
        self.assertNotRegex(text, r"\b[0-9a-f]{64}\b")
        for item in self.data["figures"]:
            self.assertLessEqual(len(item["figure"]), 160, item["id"])

    def test_dependent_measures_all_have_a_figure_or_an_explanation(self) -> None:
        covered = {item["inventory_id"] for item in self.data["figures"]}
        for entry_id, entry in self.inventory.items():
            if entry["class"] == "dependiente" and entry_id != "chat-battery-n3-n5":
                self.assertIn(entry_id, covered, entry_id)
        self.assertIn("chat-battery-n3-n5", PLAN.read_text(encoding="utf-8"))


class FiguresReadingTests(unittest.TestCase):
    def test_the_markdown_reading_lists_every_figure_of_the_json(self) -> None:
        reading = (ROOT / "docs" / "validation" / "model-change-memory-figures.md").read_text(encoding="utf-8")
        for item in load(FIGURES)["figures"]:
            self.assertIn(item["figure"], reading, item["id"])
            self.assertIn(item["previous_value"], reading, item["id"])


class PlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = PLAN.read_text(encoding="utf-8")

    def test_the_budget_cap_is_written_and_not_a_blank(self) -> None:
        self.assertIn("1,5 USD", self.text)
        self.assertNotRegex(self.text, r"(?i)presupuesto[^\n]*:\s*(?:\[?pendiente|_+|\.\.\.)")

    def test_spending_requires_a_fresh_confirmation_and_stops_at_the_cap(self) -> None:
        lowered = self.text.lower()
        self.assertIn("confirmación", lowered)
        self.assertIn("parar", lowered)
        self.assertIn("sin autorizar", lowered)

    def test_every_dependent_measure_has_a_rerun_decision(self) -> None:
        for entry in load(INVENTORY)["entries"]:
            if entry["class"] == "dependiente":
                self.assertIn(entry["id"], self.text, entry["id"])

    def test_infrastructure_sensitive_metrics_exist_in_the_catalogue(self) -> None:
        self.assertIn("Sensibilidad a la infraestructura local", self.text)
        catalogue = {m["id"] for m in load(ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json")["metrics"]}
        section = self.text.split("## Sensibilidad a la infraestructura local")[1].split("## Qué queda fuera")[0]
        mentioned = set(re.findall(r"(?:LAT|AVL|STR)-[0-9]", section))
        self.assertTrue({"LAT-1", "LAT-2", "LAT-4", "AVL-1", "STR-2"} <= mentioned)
        self.assertLessEqual(mentioned, catalogue)

    def test_no_secret_or_key_value_appears(self) -> None:
        self.assertNotRegex(self.text, r"sk-[A-Za-z0-9_-]{8,}")


class TemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = TEMPLATE.read_text(encoding="utf-8")

    def test_after_column_starts_unmeasured(self) -> None:
        self.assertIn("No medido", self.text)
        self.assertNotRegex(self.text, r"\|\s*0\s?%\s*\|")

    def test_reading_rules_forbid_unsupported_conclusions(self) -> None:
        for phrase in ("diferencia no distinguible", "sin comparación", "No medido", "límite de la comparación"):
            self.assertIn(phrase, self.text)

    def test_it_asks_for_the_model_identity_spend_and_what_was_not_reevaluated(self) -> None:
        for phrase in ("gateway_config_sha256", "Gasto real", "Presupuesto autorizado", "No se reevaluó"):
            self.assertIn(phrase, self.text)


if __name__ == "__main__":
    unittest.main()
