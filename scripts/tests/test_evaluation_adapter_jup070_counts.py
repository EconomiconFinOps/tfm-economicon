"""Recuentos `k`/`n` y ruta de los errores de forma del adaptador de JUP-070 (JUP-121, tarea 2.2, mutación M1).

Fichero NUEVO de la remediación de mutación del hallazgo M1 del QA: no modifica los tests ya commiteados
de `test_evaluation_adapter_jup070.py` ni de `test_evaluation_adapter_jup070_robustness.py`. El producto
ya es correcto; estos tests cierran dos huecos que dejaban mutantes supervivientes en
`tools/evaluation-dashboard.py`:

1. Lógica. Hasta ahora solo se probaba que `k`/`n` FALTEN en una proporción medida, nunca que tengan un
   tipo inválido. Una proporción medida copia `k` y `n` tal cual a la fila, así que un `"x"`, un `1.5`,
   un `True` (bool es subclase de int) o un `None` colarían en `numerator`/`denominator` un dato que no es
   un recuento. Se comprueba en cada forma de proporción que existe en el informe.
2. Composición del mensaje. El spec exige que el mensaje EMPIECE por `metrics.<ID>: ` y el elemento anidado
   concreto (`groups.clarify`, `stages.generation`, `judged`) va después, sin dobles espacios.

Decisión de diseño explícita: NO se prueban recuentos negativos ni `k > n`; el adaptador los copia tal cual
(no recalcula ni valida semántica estadística, regla 4 del contrato), así que no hay comportamiento que fijar.

Todas las variantes salen de `copy.deepcopy` del informe real de la ejecución 2. La ruta de la herramienta se
puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una copia mutada.
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
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup070_counts", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REPORT_2 = json.loads((ROOT / "docs" / "evidence" / "JUP-070-run-2-report.json").read_text(encoding="utf8"))

RUN_ID = "mi-ejecucion-7"

# Valores que NO son un recuento entero. `True` se incluye a propósito: bool es subclase de int y un
# `isinstance(value, int)` ingenuo lo aceptaría como 1.
INVALID_COUNTS = ("x", 1.5, True, None)


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup070(report, run_id)


def variant(mutate) -> dict:
    """Copia profunda del informe real con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(REPORT_2)
    mutate(report)
    return report


def rows_of(results: list[dict], metric_id: str) -> list[dict]:
    return [row for row in results if row["metric_id"] == metric_id]


# Posiciones de proporción medida del informe real: (metrica, descripción, función que devuelve el dict).
# Cubren las cinco formas: métrica que es la proporción, sub-objeto `judged`, grupo y etapa.
POSITIONS = (
    ("ACC-1", "fila all", lambda m: m["ACC-1"]),
    ("ACC-2", "fila all", lambda m: m["ACC-2"]),
    ("ACC-2", "sub-objeto judged", lambda m: m["ACC-2"]["judged"]),
    ("ACC-3", "grupo clarify", lambda m: m["ACC-3"]["groups"]["clarify"]),
    ("REL-3", "grupo answer", lambda m: m["REL-3"]["groups"]["answer"]),
    ("LAT-4", "etapa generation", lambda m: m["LAT-4"]["stages"]["generation"]),
)


class InvalidCountTypeTest(unittest.TestCase):
    """`k` y `n` de una proporción MEDIDA deben ser enteros; cualquier otro tipo es un error con campo."""

    def test_k_y_n_con_tipo_invalido_en_cada_posicion(self) -> None:
        for metric_id, label, get in POSITIONS:
            for key in ("k", "n"):
                for bad in INVALID_COUNTS:
                    with self.subTest(metric=metric_id, position=label, key=key, bad=repr(bad)):
                        report = variant(lambda r, get=get, key=key, bad=bad: get(r["metrics"]).update({key: bad}))
                        # Con `assertRaises(AdapterError)` un TypeError crudo o la ausencia de error (el dato
                        # inválido copiado a la fila) rompen el test.
                        with self.assertRaises(tool.AdapterError) as caught:
                            adapt(report)
                        message = str(caught.exception)
                        self.assertTrue(message.startswith(f"metrics.{metric_id}: "), message)
                        # El mensaje nombra la clave concreta que está mal.
                        self.assertIn(repr(key), message)

    def test_cero_entero_es_un_cero_medido(self) -> None:
        # Edge case positivo: `k=0` y `n=0` son enteros válidos. Con `rate` presente y `available` True
        # siguen siendo una medición (cero medido), no «no medido» ni un error por «falsy».
        for metric_id, label, get in POSITIONS:
            for key in ("k", "n"):
                with self.subTest(metric=metric_id, position=label, key=key):
                    report = variant(lambda r, get=get, key=key: get(r["metrics"]).update({key: 0}))
                    _, results = adapt(report)
                    measured = [row for row in rows_of(results, metric_id) if row["status"] == "measured"]
                    # El informe real tiene todas estas posiciones medidas; ninguna cambia de estado.
                    self.assertTrue(measured)
                    field = "numerator" if key == "k" else "denominator"
                    self.assertIn(0, [row[field] for row in measured])
                    self.assertTrue(all(row[field] is not None for row in measured), measured)

    def test_no_medido_no_valida_k_ni_n_invalidos(self) -> None:
        # Una proporción no medida no usa `k` (y el denominador se copia tal cual), así que un `k`
        # inválido allí NO es un error: la fila es `not_measured` con numerador None.
        def not_available(report: dict) -> None:
            report["metrics"]["ACC-1"].update(available=False, k="x")

        def rate_none(report: dict) -> None:
            report["metrics"]["ACC-1"].update(rate=None, ci95=None, k="x")

        for name, mutate in (("available False", not_available), ("rate None", rate_none)):
            with self.subTest(case=name):
                _, results = adapt(variant(mutate))
                row = rows_of(results, "ACC-1")[0]
                self.assertEqual(row["status"], "not_measured")
                self.assertIsNone(row["numerator"])
                self.assertIsNone(row["value"])


class NestedPathMessageTest(unittest.TestCase):
    """La ruta del elemento anidado va tras el prefijo `metrics.<ID>: ` y sin dobles espacios."""

    def error_message(self, report: dict) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        return str(caught.exception)

    def test_grupo_de_acc_3_no_objeto_incluye_groups_clarify(self) -> None:
        # Ruta de DOS elementos: comprueba el separador `.` entre `groups` y `clarify`.
        message = self.error_message(variant(lambda r: r["metrics"]["ACC-3"]["groups"].update(clarify=5)))
        self.assertTrue(message.startswith("metrics.ACC-3: "), message)
        self.assertIn("groups.clarify", message)
        self.assertNotIn("  ", message)

    def test_etapa_de_lat_4_no_objeto_incluye_stages_generation(self) -> None:
        message = self.error_message(variant(lambda r: r["metrics"]["LAT-4"]["stages"].update(generation=None)))
        self.assertTrue(message.startswith("metrics.LAT-4: "), message)
        self.assertIn("stages.generation", message)
        self.assertNotIn("  ", message)

    def test_judged_de_acc_2_no_objeto_incluye_judged(self) -> None:
        message = self.error_message(variant(lambda r: r["metrics"]["ACC-2"].update(judged=5)))
        self.assertTrue(message.startswith("metrics.ACC-2: "), message)
        self.assertIn("judged", message)
        self.assertNotIn("  ", message)

    def test_acc_3_sin_groups_nombra_groups_sin_doble_espacio(self) -> None:
        message = self.error_message(variant(lambda r: r["metrics"]["ACC-3"].pop("groups")))
        self.assertTrue(message.startswith("metrics.ACC-3: "), message)
        # `startswith` con DOS espacios descarta que el prefijo lleve un hueco de más.
        self.assertFalse(message.startswith("metrics.ACC-3:  "), message)
        self.assertIn("groups", message)
        self.assertNotIn("  ", message)

    def test_acc_1_sin_k_con_ruta_vacia_no_deja_espacio_sobrante(self) -> None:
        # Ruta VACÍA (la métrica es la proporción): el problema va solo, sin un `where` vacío delante que
        # produciría `metrics.ACC-1:  falta 'k'`.
        message = self.error_message(variant(lambda r: r["metrics"]["ACC-1"].pop("k")))
        self.assertTrue(message.startswith("metrics.ACC-1: "), message)
        self.assertFalse(message.startswith("metrics.ACC-1:  "), message)
        self.assertNotIn("  ", message)


if __name__ == "__main__":
    unittest.main()
