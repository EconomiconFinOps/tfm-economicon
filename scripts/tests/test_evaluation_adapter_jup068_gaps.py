"""Remediación de mutación de la tarea 2.5 de JUP-121: huecos que dejaron las pruebas de los adaptadores.

Dos huecos independientes:

1. Frontera de `eligible_pairs` en el adaptador de JUP-068 (mutante superviviente `pairs > 0` -> `pairs > 1`).
   Ninguna prueba usaba exactamente UNA pareja elegible, así que un umbral desplazado pasaba inadvertido. Aquí
   se fijan las tres posiciones de la frontera: 0 (no medido), 1 (medido, el caso que mata al mutante) y 2
   (control, ya cubierto en otra parte).

2. DEFECTO (Red): `_is_number` llama a `math.isfinite` sobre un `int` de Python. Con un entero mayor que ~1e308
   (p. ej. `10**400`, que `json.loads` SÍ produce) `math.isfinite` lanza `OverflowError` crudo en lugar de
   que el adaptador lo rechace con `AdapterError`. Cada adaptador que valida con `_is_number` debe rechazar
   ese valor con un `AdapterError` cuyo mensaje EMPIECE por el campo habitual. Un float grande pero finito
   (`1e300`) sigue siendo un número válido, y `inf`/`nan` siguen rechazándose.

Nota sobre JUP-070: su adaptador copia los valores de las métricas sin validarlos con `_is_number` (no hay
comprobación numérica que falle), así que no tiene caso de entero gigante; solo se prueban los adaptadores que
sí validan con `_is_number`.

Todas las variantes se construyen con `copy.deepcopy` del informe real, para que solo cambie el dato probado.
Los informes reales se leen de disco (JUP-078, JUP-022) o se obtienen ejecutando Node (JUP-068), sin skip.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una
copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup068_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EXAMPLE_PATH = ROOT / "docs" / "validation" / "JUP-068-example.json"
CLI_PATH = ROOT / "tools" / "business-metrics.mjs"
BENCHMARK_PATH = ROOT / "docs" / "evidence" / "JUP-078-benchmark-results.json"
CALIBRATION_PATH = ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json"

RUN_ID = "JUP-121-gaps"

# Entero de Python que no cabe en un float: `json.loads("1" + "0" * 400)` lo produce tal cual.
HUGE = 10**400

# Informes reales; los fija `setUpModule`.
BUSINESS_REPORT: dict = {}
BENCHMARK_REPORT: dict = {}
CALIBRATION_REPORT: dict = {}


def setUpModule() -> None:
    global BUSINESS_REPORT, BENCHMARK_REPORT, CALIBRATION_REPORT
    # El informe de JUP-068 es la salida REAL del generador de Node sobre el ejemplo versionado.
    completed = subprocess.run(["node", str(CLI_PATH), "report", str(EXAMPLE_PATH)], capture_output=True,
                               text=True, encoding="utf-8", timeout=60, cwd=ROOT)
    assert completed.returncode == 0, completed.stderr
    BUSINESS_REPORT = json.loads(completed.stdout)
    BENCHMARK_REPORT = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    CALIBRATION_REPORT = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    # Guardas de la propia prueba: si los informes cambian de forma, el fallo debe apuntar aquí.
    assert BUSINESS_REPORT["time"]["eligible_pairs"] == 2, "el ejemplo de JUP-068 ya no tiene 2 parejas"
    assert BENCHMARK_REPORT["models"][0]["successful"] > 0, "el primer modelo de JUP-078 ya no tiene éxitos"
    assert CALIBRATION_REPORT["points"][0]["answer"]["document_hit_rate"] is not None


def row(results: list[dict], metric_id: str) -> dict:
    """La única fila con ese `metric_id` (en JUP-068 y en el benchmark de un modelo es única)."""
    found = [item for item in results if item["metric_id"] == metric_id]
    assert len(found) == 1, f"se esperaba una sola fila {metric_id}, hay {len(found)}"
    return found[0]


def business_with_time(eligible_pairs: int, manual_ms: int, assisted_ms: int, saved_ms, saved_percent) -> dict:
    report = copy.deepcopy(BUSINESS_REPORT)
    report["time"].update(eligible_pairs=eligible_pairs, manual_ms=manual_ms, assisted_ms=assisted_ms,
                          saved_ms=saved_ms, saved_percent=saved_percent)
    return report


class BusinessEligiblePairsBoundaryTests(unittest.TestCase):
    """Frontera `eligible_pairs > 0`: decide si manual y asistido son una medición o una suma de nada."""

    def test_one_eligible_pair_is_measured(self) -> None:
        # Caso que mata el mutante `pairs > 1`: con UNA pareja elegible los tiempos son mediciones reales (el
        # generador sumó un par) y deben publicarse medidos con denominador 1, no descartarse como «sin datos».
        report = business_with_time(1, 600000, 300000, 300000, 50)
        _, results = tool.adapt_jup068(report, RUN_ID)
        manual, assisted = row(results, "manual_time"), row(results, "assisted_time")
        self.assertEqual(manual["status"], "measured")
        self.assertEqual(manual["value"], 600000)
        self.assertEqual(manual["denominator"], 1)
        self.assertEqual(assisted["status"], "measured")
        self.assertEqual(assisted["value"], 300000)
        self.assertEqual(assisted["denominator"], 1)

    def test_one_eligible_pair_keeps_saved_rows_measured_too(self) -> None:
        # El ahorro y su porcentaje comparten el criterio de las parejas: con una también salen medidos.
        report = business_with_time(1, 600000, 300000, 300000, 50)
        _, results = tool.adapt_jup068(report, RUN_ID)
        saved, percent = row(results, "time_saved"), row(results, "time_saved_percent")
        self.assertEqual((saved["status"], saved["value"], saved["denominator"]), ("measured", 300000, 1))
        self.assertEqual((percent["status"], percent["value"]), ("measured", 50))

    def test_zero_eligible_pairs_is_not_measured(self) -> None:
        # Sin parejas elegibles el 0 del generador significa «sin datos»: no medido, valor None y denominador 0.
        report = business_with_time(0, 0, 0, None, None)
        _, results = tool.adapt_jup068(report, RUN_ID)
        for metric_id in ("manual_time", "assisted_time"):
            with self.subTest(metric_id=metric_id):
                found = row(results, metric_id)
                self.assertEqual(found["status"], "not_measured")
                self.assertIsNone(found["value"])
                self.assertEqual(found["denominator"], 0)

    def test_two_eligible_pairs_is_measured_control(self) -> None:
        # Control (ya cubierto con el ejemplo real): con dos parejas siguen medidos, denominador 2.
        report = business_with_time(2, 900000, 540000, 360000, 40)
        _, results = tool.adapt_jup068(report, RUN_ID)
        for metric_id, value in (("manual_time", 900000), ("assisted_time", 540000)):
            with self.subTest(metric_id=metric_id):
                found = row(results, metric_id)
                self.assertEqual((found["status"], found["value"], found["denominator"]),
                                 ("measured", value, 2))


class HugeIntegerRejectionTests(unittest.TestCase):
    """DEFECTO: un `int` mayor que ~1e308 debe ser un `AdapterError` con el campo, no un `OverflowError`."""

    def assert_rejected(self, adapter, report: dict, prefix: str) -> None:
        # `assertRaises(AdapterError)` falla con OverflowError si el defecto sigue (la excepción cruda sale).
        with self.assertRaises(tool.AdapterError) as caught:
            adapter(report, RUN_ID)
        self.assertTrue(str(caught.exception).startswith(prefix),
                        f"el mensaje {str(caught.exception)!r} debe empezar por {prefix!r}")

    def test_jup078_huge_integers_are_rejected(self) -> None:
        for field in ("mean_keyword_score", "cost_usd"):
            for value in (HUGE, -HUGE):
                with self.subTest(field=field, positive=value > 0):
                    report = copy.deepcopy(BENCHMARK_REPORT)
                    report["models"][0][field] = value
                    self.assert_rejected(tool.adapt_jup078, report, f"models[0].{field}: ")

    def test_jup022_huge_integers_are_rejected(self) -> None:
        # La tasa se valida con `_is_number` ANTES de comprobar el rango [0, 1]; el umbral, antes de `> 0`.
        cases = (
            ("answer.document_hit_rate", lambda report, value: report["points"][0]["answer"]
             .__setitem__("document_hit_rate", value)),
            ("max_distance", lambda report, value: report["points"][0].__setitem__("max_distance", value)),
        )
        for field, setter in cases:
            for value in (HUGE, -HUGE):
                with self.subTest(field=field, positive=value > 0):
                    report = copy.deepcopy(CALIBRATION_REPORT)
                    setter(report, value)
                    self.assert_rejected(tool.adapt_jup022, report, f"points[0].{field}: ")

    def test_jup068_huge_integers_are_rejected(self) -> None:
        for block, field in (("time", "saved_percent"), ("allocation", "assigned_percent")):
            for value in (HUGE, -HUGE):
                with self.subTest(field=f"{block}.{field}", positive=value > 0):
                    report = copy.deepcopy(BUSINESS_REPORT)
                    report[block][field] = value
                    self.assert_rejected(tool.adapt_jup068, report, f"{block}.{field}: ")

    def test_large_finite_float_is_still_a_valid_number(self) -> None:
        # Un float grande pero finito (1e300) es un número válido: no debe rechazarse por el arreglo del defecto.
        report = copy.deepcopy(BENCHMARK_REPORT)
        report["models"][0]["mean_keyword_score"] = 1e300
        _, results = tool.adapt_jup078(report, RUN_ID)
        found = [item for item in results if item["metric_id"] == "keyword_score"
                 and item["behavior"] == report["models"][0]["alias"]]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["status"], "measured")
        self.assertEqual(found[0]["value"], 1e300)

    def test_infinite_and_nan_floats_are_still_rejected(self) -> None:
        # Regresión del comportamiento previo: inf y nan siguen siendo `AdapterError` con el prefijo del campo.
        for value in (float("inf"), float("-inf"), float("nan")):
            with self.subTest(value=repr(value)):
                report = copy.deepcopy(BENCHMARK_REPORT)
                report["models"][0]["cost_usd"] = value
                self.assert_rejected(tool.adapt_jup078, report, "models[0].cost_usd: ")


if __name__ == "__main__":
    unittest.main()
