"""Pruebas del inventario de medidas por dependencia del modelo (JUP-133, grupo 1).

El inventario `docs/validation/model-dependence-inventory.json` clasifica cada medida del
asistente como `dependiente`, `independiente` o `historica`. Aquí se valida su forma y se
contrasta con el manifiesto versionado de `tools/evaluation-dashboard.py`, para que una
fuente nueva no entre al dashboard sin que alguien decida si depende del modelo.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_inventory", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

INVENTORY = ROOT / "docs" / "validation" / "model-dependence-inventory.json"
CLASSES = ("dependiente", "independiente", "historica")
CHECK_KINDS = ("code", "report", "not_done")
ENTRY_KEYS = {"id", "name", "cards", "class", "justification", "check", "sources", "evidence", "rerun"}
CHECK_KEYS = {"kind", "ref", "finding"}
ROOT_KEYS = {"inventory_version", "entries"}


class InventoryError(ValueError):
    """Problema del inventario, con la entrada y el campo para localizarlo."""


def _text(entry: dict, key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InventoryError(f"{where}.{key}: debe ser una cadena no vacía")
    return value


def validate_inventory(data: object, manifest_sources: set[str], root: Path = ROOT) -> None:
    """Lanza `InventoryError` con la entrada y el campo si el inventario no cumple la spec."""
    if not isinstance(data, dict) or set(data) != ROOT_KEYS:
        raise InventoryError(f"la raíz debe ser un objeto con exactamente las claves {sorted(ROOT_KEYS)}")
    if data["inventory_version"] != 1:
        raise InventoryError("inventory_version: debe ser 1")
    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        raise InventoryError("entries: debe ser una lista no vacía")
    seen_ids: set[str] = set()
    owners: dict[str, str] = {}
    for index, entry in enumerate(entries):
        where = f"entries[{index}]"
        if not isinstance(entry, dict):
            raise InventoryError(f"{where}: debe ser un objeto")
        unknown = set(entry) - ENTRY_KEYS
        missing = ENTRY_KEYS - set(entry)
        if unknown or missing:
            raise InventoryError(f"{where}: claves desconocidas {sorted(unknown)} o ausentes {sorted(missing)}")
        entry_id = _text(entry, "id", where)
        where = f"entries[{entry_id}]"
        if entry_id in seen_ids:
            raise InventoryError(f"{where}: id repetido")
        seen_ids.add(entry_id)
        _text(entry, "name", where)
        _text(entry, "justification", where)
        _text(entry, "rerun", where)
        if entry["class"] not in CLASSES:
            raise InventoryError(f"{where}.class: {entry['class']!r} no es una de {list(CLASSES)}")
        cards = entry["cards"]
        if not isinstance(cards, list) or not cards or not all(isinstance(c, str) and c.startswith("JUP-") for c in cards):
            raise InventoryError(f"{where}.cards: debe ser una lista no vacía de identificadores JUP-XXX")
        check = entry["check"]
        if not isinstance(check, dict) or set(check) != CHECK_KEYS or check["kind"] not in CHECK_KINDS:
            raise InventoryError(f"{where}.check: debe tener exactamente {sorted(CHECK_KEYS)} y un kind de {list(CHECK_KINDS)}")
        _text(check, "finding", f"{where}.check")
        if check["kind"] != "not_done":
            ref = _text(check, "ref", f"{where}.check")
            if not (root / ref).exists():
                raise InventoryError(f"{where}.check.ref: {ref!r} no existe en el repositorio")
        if entry["class"] == "independiente" and check["kind"] == "not_done":
            raise InventoryError(f"{where}: una medida independiente necesita una comprobación hecha (code o report)")
        sources = entry["sources"]
        if not isinstance(sources, list) or not all(isinstance(s, str) and s for s in sources):
            raise InventoryError(f"{where}.sources: debe ser una lista de fuentes del manifiesto")
        for source in sources:
            if source in owners:
                raise InventoryError(f"{where}.sources: {source!r} ya está clasificada en {owners[source]} (dos clases para una medida)")
            owners[source] = entry_id
        evidence = entry["evidence"]
        if not isinstance(evidence, list) or not evidence or not all(isinstance(p, str) for p in evidence):
            raise InventoryError(f"{where}.evidence: debe ser una lista no vacía de rutas")
        for path in evidence:
            if not (root / path).exists():
                raise InventoryError(f"{where}.evidence: {path!r} no existe en el repositorio")
    unclassified = sorted(manifest_sources - set(owners))
    if unclassified:
        raise InventoryError(f"el manifiesto lista fuentes sin clasificar: {unclassified}")
    stale = sorted(set(owners) - manifest_sources)
    if stale:
        raise InventoryError(f"el inventario cita fuentes que no están en el manifiesto: {stale}")


def manifest_sources() -> set[str]:
    dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])
    return {item["run"]["source"] for item in dataset["runs"]}


def load_inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


class InventoryContractTests(unittest.TestCase):
    def test_real_inventory_is_valid(self) -> None:
        validate_inventory(load_inventory(), manifest_sources())

    def test_every_manifest_source_has_exactly_one_class(self) -> None:
        owners: dict[str, str] = {}
        for entry in load_inventory()["entries"]:
            for source in entry["sources"]:
                self.assertNotIn(source, owners, source)
                owners[source] = entry["class"]
        self.assertEqual(set(owners), manifest_sources())

    def test_unclassified_manifest_source_fails_and_names_it(self) -> None:
        with self.assertRaisesRegex(InventoryError, "sin clasificar.*JUP-999"):
            validate_inventory(load_inventory(), manifest_sources() | {"JUP-999"})

    def test_source_in_two_classes_fails(self) -> None:
        data = load_inventory()
        with_sources = [e for e in data["entries"] if e["sources"]]
        with_sources[1]["sources"].append(with_sources[0]["sources"][0])
        with self.assertRaisesRegex(InventoryError, "dos clases"):
            validate_inventory(data, manifest_sources())

    def test_independent_without_a_done_check_fails(self) -> None:
        data = load_inventory()
        entry = next(e for e in data["entries"] if e["class"] == "independiente")
        entry["check"] = {"kind": "not_done", "ref": "", "finding": "pendiente"}
        with self.assertRaisesRegex(InventoryError, "independiente necesita una comprobación"):
            validate_inventory(data, manifest_sources())

    def test_unknown_class_fails(self) -> None:
        data = load_inventory()
        data["entries"][0]["class"] = "mixta"
        with self.assertRaisesRegex(InventoryError, "no es una de"):
            validate_inventory(data, manifest_sources())

    def test_empty_justification_fails(self) -> None:
        for blank in ("", "   "):
            data = load_inventory()
            data["entries"][0]["justification"] = blank
            with self.assertRaisesRegex(InventoryError, "justification"):
                validate_inventory(data, manifest_sources())

    def test_missing_reference_file_fails(self) -> None:
        data = load_inventory()
        data["entries"][0]["evidence"] = ["docs/validation/no-existe.json"]
        with self.assertRaisesRegex(InventoryError, "no existe"):
            validate_inventory(data, manifest_sources())

    def test_unknown_key_fails(self) -> None:
        data = load_inventory()
        data["entries"][0]["extra"] = 1
        with self.assertRaisesRegex(InventoryError, "claves desconocidas"):
            validate_inventory(data, manifest_sources())

    def test_duplicate_id_fails(self) -> None:
        data = load_inventory()
        data["entries"][1]["id"] = data["entries"][0]["id"]
        with self.assertRaisesRegex(InventoryError, "id repetido"):
            validate_inventory(data, manifest_sources())

    def test_validation_does_not_mutate_its_input(self) -> None:
        data = load_inventory()
        before = copy.deepcopy(data)
        validate_inventory(data, manifest_sources())
        self.assertEqual(data, before)


class InventoryContentTests(unittest.TestCase):
    """Decisiones de clasificación que la tarjeta nombra y que no deben cambiar sin pensarlo."""

    def setUp(self) -> None:
        self.by_id = {entry["id"]: entry for entry in load_inventory()["entries"]}

    def _class_of(self, source: str) -> str:
        return next(e["class"] for e in self.by_id.values() if source in e["sources"])

    def test_anomalies_and_data_freshness_are_independent(self) -> None:
        self.assertEqual(self._class_of("JUP-130-anomalies"), "independiente")
        self.assertEqual(self._class_of("JUP-130-data"), "independiente")

    def test_ai_cost_and_live_robustness_depend_on_the_model(self) -> None:
        self.assertEqual(self._class_of("JUP-130-ai-cost"), "dependiente")
        self.assertEqual(self._class_of("JUP-071"), "dependiente")

    def test_glm_deepseek_comparison_is_historical(self) -> None:
        entry = next(e for e in self.by_id.values() if "JUP-063" in e["cards"])
        self.assertEqual(entry["class"], "historica")

    def test_independent_code_checks_point_at_real_files_without_model_calls(self) -> None:
        """La comprobación de código de una medida independiente no debe citar el cliente del modelo."""
        for entry in self.by_id.values():
            if entry["class"] != "independiente" or entry["check"]["kind"] != "code":
                continue
            text = (ROOT / entry["check"]["ref"]).read_text(encoding="utf-8")
            for forbidden in ("chat_gateway", "litellm", "openrouter", "summary_gateway"):
                self.assertNotIn(forbidden, text.lower(), f"{entry['id']}: {entry['check']['ref']} cita {forbidden}")


if __name__ == "__main__":
    unittest.main()
