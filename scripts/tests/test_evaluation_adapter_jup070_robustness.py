"""Robustez del adaptador del informe de JUP-070 de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.2, mutación).

Fichero NUEVO de la remediación de mutación: no sustituye ni modifica los tests ya commiteados de
`test_evaluation_adapter_jup070.py`; los complementa con dos bloques.

1. Defecto real (Red). El requisito del spec «Informe no soportado o mal formado» exige que un informe
   con la forma interna rota de una métrica CONOCIDA falle con `AdapterError` cuyo mensaje EMPIECE por
   `metrics.<ID>: `. Hoy el adaptador deja escapar `KeyError`, `TypeError`, `AttributeError` o
   `ValueError` crudos (por ejemplo `data["groups"]` sin `groups`), que el cargador no sabe tratar
   como un error de datos con el campo nombrado.
2. Endurecimiento (pasa ya). Fija comportamientos que los tests anteriores no distinguían y que dejaban
   mutantes supervivientes: catálogo ilegible, prefijo exacto de los campos mal tipados, versión real del
   catálogo en el mensaje, GRD-2 no disponible con desglose por caso y formatos de fecha admitidos.

Todas las variantes salen de `copy.deepcopy` del informe real de la ejecución 2, de modo que solo cambia
el dato que se quiere probar. La ruta de la herramienta se puede sustituir con la variable de entorno
`EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup070_robustness", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REPORT_2 = json.loads((ROOT / "docs" / "evidence" / "JUP-070-run-2-report.json").read_text(encoding="utf8"))
CATALOGUE = json.loads((ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json").read_text(encoding="utf8"))

RUN_ID = "mi-ejecucion-7"
# Filas del informe real de la ejecución 2 (ver test_numero_total_de_filas del fichero principal).
TOTAL_ROWS = 48


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup070(report, run_id)


def variant(mutate) -> dict:
    """Copia profunda del informe real con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(REPORT_2)
    mutate(report)
    return report


def rows_of(results: list[dict], metric_id: str) -> list[dict]:
    return [row for row in results if row["metric_id"] == metric_id]


class BrokenMetricShapeTest(unittest.TestCase):
    """Defecto: la forma interna rota de una métrica conocida debe salir como `AdapterError`."""

    def assert_metric_error(self, report: dict, metric_id: str) -> None:
        # `assertRaises(AdapterError)` hace que un KeyError/TypeError/AttributeError/ValueError que escape
        # rompa el test: el contrato es un único tipo de error de datos con el campo nombrado.
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        self.assertTrue(message.startswith(f"metrics.{metric_id}: "), message)

    def test_acc_3_sin_groups(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["ACC-3"].pop("groups")), "ACC-3")

    def test_acc_3_groups_no_objeto(self) -> None:
        # `.items()` sobre algo que no es un dict daría AttributeError; None, lista y entero son los típicos.
        for bad in (None, [], 5, "clarify"):
            with self.subTest(groups=repr(bad)):
                self.assert_metric_error(variant(lambda r, bad=bad: r["metrics"]["ACC-3"].update(groups=bad)), "ACC-3")

    def test_acc_3_grupo_no_objeto(self) -> None:
        # Un grupo concreto roto no puede tratarse como un dict de proporción.
        for bad in (5, None, [0, 6], "x"):
            with self.subTest(group=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["ACC-3"]["groups"].update(clarify=bad)), "ACC-3")

    def test_rel_3_sin_groups(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["REL-3"].pop("groups")), "REL-3")

    def test_lat_1_sin_stages(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["LAT-1"].pop("stages")), "LAT-1")

    def test_lat_1_stages_no_objeto(self) -> None:
        for bad in (None, [], 5):
            with self.subTest(stages=repr(bad)):
                self.assert_metric_error(variant(lambda r, bad=bad: r["metrics"]["LAT-1"].update(stages=bad)), "LAT-1")

    def test_lat_1_etapa_no_objeto(self) -> None:
        # `entry.get(...)` sobre un entero o None lanza AttributeError.
        for bad in (5, None, "x", [1]):
            with self.subTest(stage=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["LAT-1"]["stages"].update(generation=bad)), "LAT-1")

    def test_lat_4_etapa_no_objeto(self) -> None:
        for bad in (5, None, "x", [1]):
            with self.subTest(stage=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["LAT-4"]["stages"].update(retrieval=bad)), "LAT-4")

    def test_str_2_sin_by_category(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["STR-2"].pop("by_category")), "STR-2")

    def test_str_2_by_category_no_objeto(self) -> None:
        for bad in (None, [], 5):
            with self.subTest(by_category=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["STR-2"].update(by_category=bad)), "STR-2")

    def test_grd_2_disponible_con_by_case_no_objeto(self) -> None:
        for bad in (None, [], 5, "JUP-069-005"):
            with self.subTest(by_case=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["GRD-2"].update(available=True, by_case=bad)), "GRD-2")

    def test_grd_2_disponible_sin_by_case(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["GRD-2"].pop("by_case")), "GRD-2")

    def test_acc_1_medido_sin_k(self) -> None:
        # Con `rate` presente y disponible hay que copiar `k`; sin él no se puede inventar un 0.
        self.assert_metric_error(variant(lambda r: r["metrics"]["ACC-1"].pop("k")), "ACC-1")

    def test_acc_1_medido_sin_n(self) -> None:
        self.assert_metric_error(variant(lambda r: r["metrics"]["ACC-1"].pop("n")), "ACC-1")

    def test_acc_2_judged_no_objeto(self) -> None:
        for bad in (5, None, [0, 30], "x"):
            with self.subTest(judged=repr(bad)):
                self.assert_metric_error(
                    variant(lambda r, bad=bad: r["metrics"]["ACC-2"].update(judged=bad)), "ACC-2")

    def test_acc_1_ci95_con_forma_invalida(self) -> None:
        # Debe ser una lista de exactamente dos límites; desempaquetar otra cosa da ValueError/TypeError crudos.
        for bad in ([0.1], "x", 5, [0.1, 0.2, 0.3], {"low": 0.1, "high": 0.2}):
            with self.subTest(ci95=repr(bad)):
                self.assert_metric_error(variant(lambda r, bad=bad: r["metrics"]["ACC-1"].update(ci95=bad)), "ACC-1")

    def test_acc_1_no_medido_no_necesita_k(self) -> None:
        # Excepción al bloque anterior: lo no medido no copia `k`, así que su ausencia NO es un error.
        # Se comprueba con available False y con rate None; el denominador se conserva y lo demás es None.
        def not_available(report: dict) -> None:
            report["metrics"]["ACC-1"].pop("k")
            report["metrics"]["ACC-1"].update(available=False)

        def rate_none(report: dict) -> None:
            report["metrics"]["ACC-1"].pop("k")
            report["metrics"]["ACC-1"].update(rate=None, ci95=None)

        for name, mutate in (("available False", not_available), ("rate None", rate_none)):
            with self.subTest(case=name):
                _, results = adapt(variant(mutate))
                row = rows_of(results, "ACC-1")[0]
                self.assertEqual(row["status"], "not_measured")
                self.assertIsNone(row["numerator"])
                self.assertIsNone(row["value"])
                self.assertEqual(row["denominator"], 20)


class CatalogueUnreadableTest(unittest.TestCase):
    """El catálogo de JUP-067 ilegible es un error de contrato que nombra `catalogue`."""

    def assert_catalogue_error(self, path: Path) -> None:
        with mock.patch.object(tool, "CATALOGUE_PATH", path):
            with self.assertRaises(tool.AdapterError) as caught:
                adapt(REPORT_2)
        self.assertTrue(str(caught.exception).startswith("catalogue: "), str(caught.exception))

    def test_catalogo_inexistente(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self.assert_catalogue_error(Path(folder) / "no-existe.json")

    def test_catalogo_con_json_invalido(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "roto.json"
            path.write_text("{ esto no es json", encoding="utf-8")
            self.assert_catalogue_error(path)


class FieldPrefixTest(unittest.TestCase):
    """El mensaje empieza por el campo EXACTO (no basta con que lo contenga)."""

    def assert_prefix(self, report: dict, prefix: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        self.assertTrue(str(caught.exception).startswith(prefix), str(caught.exception))

    def test_objetos_de_run_mal_tipados(self) -> None:
        for field in ("corpus", "generation", "retrieval"):
            for bad in ([], 5):
                with self.subTest(field=field, bad=repr(bad)):
                    self.assert_prefix(variant(lambda r, field=field, bad=bad: r["run"].update({field: bad})),
                                       f"run.{field}: ")

    def test_metrica_conocida_con_valor_no_objeto(self) -> None:
        for bad in (5, [], None, "x"):
            with self.subTest(metric=repr(bad)):
                self.assert_prefix(variant(lambda r, bad=bad: r["metrics"].update({"ACC-1": bad})), "metrics.ACC-1: ")

    def test_corpus_sin_sha256(self) -> None:
        self.assert_prefix(variant(lambda r: r["run"]["corpus"].pop("sha256")), "run.corpus.sha256: ")

    def test_generation_sin_model_alias(self) -> None:
        self.assert_prefix(variant(lambda r: r["run"]["generation"].pop("model_alias")),
                           "run.generation.model_alias: ")

    def test_catalogue_version_distinta_cita_la_version_real(self) -> None:
        # El mensaje debe decir qué versión se esperaba, leída del catálogo y no escrita a mano en la herramienta.
        real = CATALOGUE["catalogue_version"]
        for bad in ("9.9.9", None):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(tool.AdapterError) as caught:
                    adapt(variant(lambda r, bad=bad: r.update(catalogue_version=bad)))
                message = str(caught.exception)
                self.assertTrue(message.startswith("catalogue_version: "), message)
                self.assertIn(real, message)


class Grd2NotAvailableTest(unittest.TestCase):
    """GRD-2 no disponible: una única fila `all` no medida aunque el informe traiga desglose por caso."""

    def test_una_fila_all_no_medida_con_by_case_no_vacio(self) -> None:
        def make(report: dict) -> None:
            report["metrics"]["GRD-2"].update(total=3, by_case={"JUP-069-005": 2, "JUP-069-006": 1}, available=False)

        _, results = adapt(variant(make))
        rows = rows_of(results, "GRD-2")
        # Exactamente una fila: el desglose por caso de una métrica no medida no se publica de ningún modo.
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["behavior"], "all")
        self.assertEqual(rows[0]["status"], "not_measured")
        self.assertIsNone(rows[0]["value"])
        # Mismo número de filas que con GRD-2 sin desglose (48): no aparecen filas por caso.
        self.assertEqual(len(results), TOTAL_ROWS)


class RunDateTest(unittest.TestCase):
    """Formatos de fecha ISO 8601 admitidos y rechazados en `run.date`."""

    def test_fechas_validas_y_conservadas_tal_cual(self) -> None:
        for raw in ("2026-10-08T21:01:44Z", "2026-10-08T21:01:44+00:00", "2026-10-08T21:01:44.123Z"):
            with self.subTest(date=raw):
                run, _ = adapt(variant(lambda r, raw=raw: r["run"].update(date=raw)))
                self.assertEqual(run["run_at"], raw)

    def test_fechas_invalidas(self) -> None:
        # No se incluye `20261008`: Python 3.13 lo acepta como ISO 8601 básico.
        for bad in ("", "ayer", None, "2026-13-45T00:00:00Z", "Z"):
            with self.subTest(date=repr(bad)):
                with self.assertRaises(tool.AdapterError) as caught:
                    adapt(variant(lambda r, bad=bad: r["run"].update(date=bad)))
                self.assertTrue(str(caught.exception).startswith("run.date: "), str(caught.exception))


if __name__ == "__main__":
    unittest.main()
