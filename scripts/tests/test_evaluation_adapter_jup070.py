"""Adaptador del informe JSON de JUP-070 de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.2, fase Red).

Contrato que se valida (`adapt_jup070(report, run_id) -> (run, results)`):

* Es una función PURA sobre el dict ya parseado: no lee el informe, no lo muta y no comparte
  estructuras con él. El catálogo de JUP-067 sí se lee del repositorio.
* `run` y cada fila de `results` tienen EXACTAMENTE las claves de `RUN_KEYS` / `RESULT_KEYS`.
* Los adaptadores COPIAN, no recalculan: los valores medidos salen idénticos al informe.
* Lo no medido es `None` con estado `not_measured`, nunca 0 (spec «Lo no medido nunca es cero»).
* No se copia texto libre: solo identificadores, hashes, alias y unidades.

Los valores esperados se escriben a mano a partir de los informes reales
(`docs/evidence/JUP-070-run-{1,2}-report.json`) o se leen de esos JSON con accesos directos;
en ningún caso se calculan llamando al adaptador. Las variantes «no medido» se construyen con
`copy.deepcopy` del informe real para que solo cambie el dato que se quiere probar.

La ruta de la herramienta se puede sustituir con la variable de entorno
`EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una copia mutada.
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
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup070", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REPORT_1 = json.loads((ROOT / "docs" / "evidence" / "JUP-070-run-1-report.json").read_text(encoding="utf8"))
REPORT_2 = json.loads((ROOT / "docs" / "evidence" / "JUP-070-run-2-report.json").read_text(encoding="utf8"))
CATALOGUE = json.loads((ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json").read_text(encoding="utf8"))
CATALOGUE_BY_ID = {item["id"]: item for item in CATALOGUE["metrics"]}

RUN_ID = "mi-ejecucion-7"

# Claves literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)
CASE_STATUSES = ("pass", "fail", "blocked", "not_run")
VALUE_STATUSES = ("measured", "not_measured")

# Juicio por métrica según «Juicio humano o automático» de docs/validation/evaluation-dashboard.md.
HUMAN_METRICS = {"ACC-1", "ACC-3"}


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup070(report, run_id)


def expected_row(**fields) -> dict:
    """Fila esperada completa: todo lo no indicado es None salvo measure_type A y selected False."""
    row = {key: None for key in RESULT_KEYS}
    row["measure_type"] = "A"
    row["selected"] = False
    row.update(fields)
    return row


def proportion(metric_id: str, behavior: str, k, n, rate, low, high, judgment: str, **extra) -> dict:
    """Fila esperada de una proporción medida del catálogo (grp y unit salen del catálogo)."""
    item = CATALOGUE_BY_ID[metric_id]
    return expected_row(
        grp=item["family"], metric_id=metric_id, behavior=behavior, status="measured",
        value=rate, unit=item["unit"], numerator=k, denominator=n, ci_low=low, ci_high=high,
        judgment=judgment, **extra,
    )


def find(results: list[dict], metric_id: str, behavior: str) -> dict:
    """Devuelve la única fila (metric_id, behavior); falla si no hay exactamente una."""
    matches = [row for row in results if row["metric_id"] == metric_id and row["behavior"] == behavior]
    assert len(matches) == 1, f"se esperaba 1 fila {metric_id}/{behavior} y hay {len(matches)}"
    return matches[0]


def rows_of(results: list[dict], metric_id: str) -> list[dict]:
    return [row for row in results if row["metric_id"] == metric_id]


def variant(mutate, base: dict = REPORT_2) -> dict:
    """Copia profunda del informe con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(base)
    mutate(report)
    return report


def string_values(value):
    """Todas las cadenas (no claves) de una estructura anidada."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from string_values(item)


class ConstantsTest(unittest.TestCase):
    """Las constantes públicas del contrato y la clase de error."""

    def test_constantes_del_contrato(self) -> None:
        # Los consumidores (cargador, validador de rows-v1) dependen de estas tuplas exactas y de su orden.
        self.assertEqual(tuple(tool.RUN_KEYS), RUN_KEYS)
        self.assertEqual(tuple(tool.RESULT_KEYS), RESULT_KEYS)
        self.assertEqual(tuple(tool.CASE_STATUSES), CASE_STATUSES)
        self.assertEqual(tuple(tool.VALUE_STATUSES), VALUE_STATUSES)

    def test_adapter_error_es_value_error(self) -> None:
        # Los errores de un informe se tratan como errores de validación de datos, como ManifestError.
        self.assertTrue(issubclass(tool.AdapterError, ValueError))


class RunBlockTest(unittest.TestCase):
    """El bloque `run`: copia de metadatos del informe, sin deducir nada."""

    def test_run_1_mock(self) -> None:
        # Run-1 usa embeddings `mock` y no fija max_distance (None): se conserva None, no se deduce un valor.
        run, _ = adapt(REPORT_1)
        self.assertEqual(tuple(run), RUN_KEYS)
        self.assertEqual(run, {
            "run_id": RUN_ID,
            "source": "JUP-070",
            "run_at": "2026-10-08T20:13:54Z",
            "commit": "b12b3c80d0954a1f1a7bd12fae31456f269cff52",
            "suite": "JUP-069",
            "suite_version": "1.0.0",
            "suite_sha256": "e15349564edfa5ce6cef94ff90ee2bfd15ef17656a2c4b201ac37bcd6d44571c",
            "corpus_sha256": "cf2633b96ca30a63f70952c6cb23ca8139dcb665e9a51a0d52dbcc144b00c8dc",
            "embedding_provider": "mock",
            "embedding_alias": "mock",
            "retrieval": {"top_k": 4, "max_distance": None, "chunk_size": 500, "chunk_overlap": 50},
            "generation_model": "plantilla-sin-modelo",
            "prompt_sha256": None,
            "synthetic": False,
        })

    def test_run_2_litellm(self) -> None:
        run, _ = adapt(REPORT_2)
        self.assertEqual(set(run), set(RUN_KEYS))
        self.assertEqual(run, {
            "run_id": RUN_ID,
            "source": "JUP-070",
            "run_at": "2026-10-08T21:01:44Z",
            "commit": "8a116df28472a30b21b996ab6fa02377dde7b2c1",
            "suite": "JUP-069",
            "suite_version": "1.0.0",
            "suite_sha256": "e15349564edfa5ce6cef94ff90ee2bfd15ef17656a2c4b201ac37bcd6d44571c",
            "corpus_sha256": "cf2633b96ca30a63f70952c6cb23ca8139dcb665e9a51a0d52dbcc144b00c8dc",
            "embedding_provider": "litellm",
            "embedding_alias": "economicon-embedding",
            "retrieval": {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
            "generation_model": "plantilla-sin-modelo",
            "prompt_sha256": None,
            "synthetic": False,
        })

    def test_run_id_es_el_argumento(self) -> None:
        # El identificador lo decide el manifiesto/herramienta, no el informe (JUP-070 no trae uno).
        run, _ = adapt(REPORT_2, "otro-id.v2")
        self.assertEqual(run["run_id"], "otro-id.v2")

    def test_retrieval_es_una_copia(self) -> None:
        # Si la salida compartiese el dict con el informe, mutar la fila alteraría la fuente de verdad.
        report = copy.deepcopy(REPORT_2)
        run, _ = adapt(report)
        self.assertEqual(run["retrieval"], report["run"]["retrieval"])
        self.assertIsNot(run["retrieval"], report["run"]["retrieval"])
        run["retrieval"]["top_k"] = 999
        self.assertEqual(report["run"]["retrieval"]["top_k"], 4)

    def test_run_at_se_copia_tal_cual(self) -> None:
        # No se normaliza la fecha: la `Z` final y los offsets del informe se conservan literalmente.
        for raw in ("2026-10-08T21:01:44Z", "2026-10-08T21:01:44+00:00", "2026-10-08T21:01:44.250Z"):
            with self.subTest(date=raw):
                report = variant(lambda r, raw=raw: r["run"].update(date=raw))
                run, _ = adapt(report)
                self.assertEqual(run["run_at"], raw)

    def test_valores_nulos_del_informe_se_copian_como_none(self) -> None:
        # «Metadato ausente»: un null del informe queda null en la ejecución (se muestra «no registrado»).
        def blank(report: dict) -> None:
            run = report["run"]
            for key in ("commit", "provider", "alias", "suite_version", "suite_sha256"):
                run[key] = None
            run["corpus"]["sha256"] = None
            run["generation"]["model_alias"] = None

        run, _ = adapt(variant(blank))
        for key in ("commit", "suite_version", "suite_sha256", "corpus_sha256",
                    "embedding_provider", "embedding_alias", "generation_model"):
            with self.subTest(key=key):
                self.assertIsNone(run[key])
        # La batería sigue siendo JUP-069 y la fuente JUP-070 aunque falten los metadatos.
        self.assertEqual(run["suite"], "JUP-069")
        self.assertEqual(run["source"], "JUP-070")

    def test_synthetic_true_se_conserva(self) -> None:
        # Alimenta el motivo de ejecución no real `sintetica`.
        run, _ = adapt(variant(lambda r: r["run"].update(synthetic=True)))
        self.assertIs(run["synthetic"], True)


class Run2RowsTest(unittest.TestCase):
    """Normalización completa del informe real de la ejecución 2."""

    def setUp(self) -> None:
        _, self.results = adapt(REPORT_2)

    def test_numero_total_de_filas(self) -> None:
        # 4 recuentos + 1 ACC-1 + 2 ACC-2 + 2 ACC-3 + 1 REL-1 + 1 REL-2 + 3 REL-3 + 3 REL-4 + 1 GRD-1
        # + 1 GRD-2 + 1 GRD-3 + 12 LAT-1..3 + 3 LAT-4 + 1 STR-1 + 11 STR-2 + 1 AVL-1 = 48.
        self.assertEqual(len(self.results), 48)

    def test_claves_exactas_y_estados_validos(self) -> None:
        for row in self.results:
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                self.assertEqual(set(row), set(RESULT_KEYS))
                self.assertEqual(row["measure_type"], "A")
                self.assertIn(row["status"], CASE_STATUSES + VALUE_STATUSES)
                self.assertIs(row["selected"], False)

    def test_estados_de_recuento_solo_en_las_filas_de_casos(self) -> None:
        # pass/fail/blocked/not_run son estados de la métrica `cases`; el resto usa measured/not_measured.
        for row in self.results:
            expected = CASE_STATUSES if row["metric_id"] == "cases" else VALUE_STATUSES
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                self.assertIn(row["status"], expected)

    def test_orden_de_las_filas(self) -> None:
        # Primero los recuentos en el orden de CASE_STATUSES y luego las métricas en el orden del informe.
        expected = [("cases", "all")] * 4
        expected += [("ACC-1", "all"), ("ACC-2", "all"), ("ACC-2", "judged"),
                     ("ACC-3", "clarify"), ("ACC-3", "abstain"),
                     ("REL-1", "all"), ("REL-2", "all"),
                     ("REL-3", "answer"), ("REL-3", "clarify"), ("REL-3", "abstain"),
                     ("REL-4", "median"), ("REL-4", "q1"), ("REL-4", "q3"),
                     ("GRD-1", "all"), ("GRD-2", "all"), ("GRD-3", "all")]
        for metric in ("LAT-1", "LAT-2", "LAT-3"):
            expected += [(metric, stage) for stage in ("embedding", "retrieval", "generation", "total")]
        expected += [("LAT-4", stage) for stage in ("embedding", "retrieval", "generation")]
        expected += [("STR-1", "all")]
        expected += [("STR-2", name) for name in (
            "timeout", "connection", "transport", "authentication", "request", "redirect",
            "rate_limit", "upstream", "invalid_response", "schema_validation")]
        expected += [("STR-2", "all"), ("AVL-1", "all")]
        self.assertEqual([(r["metric_id"], r["behavior"]) for r in self.results], expected)
        self.assertEqual([r["status"] for r in self.results[:4]], list(CASE_STATUSES))

    def test_filas_de_recuento(self) -> None:
        # `cases` es el denominador de las cuatro filas; blocked y not_run son estados propios.
        def count_row(status: str, count: int, judgment: str) -> dict:
            return expected_row(grp="cases", metric_id="cases", behavior="all", status=status, count=count,
                                unit="casos", denominator=28, judgment=judgment)

        self.assertEqual(self.results[:4], [
            count_row("pass", 0, "human"),
            count_row("fail", 28, "human"),
            count_row("blocked", 0, "automatic"),
            count_row("not_run", 0, "automatic"),
        ])

    def test_acc_1(self) -> None:
        self.assertEqual(find(self.results, "ACC-1", "all"),
                         proportion("ACC-1", "all", 0, 20, 0.0, 0.0, 0.161125, "human"))

    def test_acc_2_all_y_judged(self) -> None:
        # ACC-2 es la única métrica con un sub-objeto `judged` (puntos juzgados por personas).
        self.assertEqual(find(self.results, "ACC-2", "all"),
                         proportion("ACC-2", "all", 25, 51, 0.490196, 0.358575, 0.623191, "automatic"))
        self.assertEqual(find(self.results, "ACC-2", "judged"),
                         proportion("ACC-2", "judged", 0, 30, 0.0, 0.0, 0.113513, "human"))

    def test_acc_3_grupo(self) -> None:
        self.assertEqual(find(self.results, "ACC-3", "clarify"),
                         proportion("ACC-3", "clarify", 0, 6, 0.0, 0.0, 0.390334, "human"))
        self.assertEqual(find(self.results, "ACC-3", "abstain"),
                         proportion("ACC-3", "abstain", 0, 2, 0.0, 0.0, 0.65762, "human"))

    def test_rel_1_y_rel_2(self) -> None:
        self.assertEqual(find(self.results, "REL-1", "all"),
                         proportion("REL-1", "all", 20, 20, 1.0, 0.838875, 1.0, "automatic"))
        self.assertEqual(find(self.results, "REL-2", "all"),
                         proportion("REL-2", "all", 16, 20, 0.8, 0.583983, 0.919342, "automatic"))

    def test_rel_3_grupo_answer(self) -> None:
        self.assertEqual(find(self.results, "REL-3", "answer"),
                         proportion("REL-3", "answer", 0, 20, 0.0, 0.0, 0.161125, "automatic"))

    def test_rel_4_mediana_y_cuartiles(self) -> None:
        # REL-4 no es una proporción: tres filas con el estadístico como `value` y `n` como denominador.
        for behavior, value in (("median", 0.6166171504041825), ("q1", 0.5578881845513168),
                                ("q3", 0.635971726018935)):
            with self.subTest(behavior=behavior):
                self.assertEqual(find(self.results, "REL-4", behavior), expected_row(
                    grp="relevance", metric_id="REL-4", behavior=behavior, status="measured",
                    value=value, unit="similitud", denominator=20, judgment="automatic"))

    def test_grd(self) -> None:
        self.assertEqual(find(self.results, "GRD-1", "all"),
                         proportion("GRD-1", "all", 60, 60, 1.0, 0.939828, 1.0, "automatic"))
        self.assertEqual(find(self.results, "GRD-3", "all"),
                         proportion("GRD-3", "all", 60, 60, 1.0, 0.939828, 1.0, "automatic"))

    def test_grd_2_total_cero_es_medido(self) -> None:
        # total 0 con available true es una medición real (cero fallos de fundamentación), no «no medido».
        self.assertEqual(find(self.results, "GRD-2", "all"), expected_row(
            grp="grounding", metric_id="GRD-2", behavior="all", status="measured",
            value=0, unit="recuento", judgment="automatic"))
        self.assertEqual(len(rows_of(self.results, "GRD-2")), 1)  # by_case vacío: ninguna fila por caso

    def test_latencia_por_etapa(self) -> None:
        self.assertEqual(find(self.results, "LAT-2", "total"), expected_row(
            grp="latency", metric_id="LAT-2", behavior="total", status="measured",
            value=4561.659, unit="ms", denominator=28, judgment="automatic"))
        self.assertEqual(find(self.results, "LAT-1", "generation")["value"], 3213.097)
        self.assertEqual(find(self.results, "LAT-3", "total")["value"], 5679.037)

    def test_latencia_cero_ms_es_medida(self) -> None:
        # Etapas con value 0 (embedding/retrieval de la plantilla) son medidas, no ausentes.
        row = find(self.results, "LAT-1", "embedding")
        self.assertEqual(row["status"], "measured")
        self.assertEqual(row["value"], 0)
        self.assertIsNotNone(row["value"])

    def test_lat_4_tasa_por_etapa(self) -> None:
        self.assertEqual(find(self.results, "LAT-4", "generation"),
                         proportion("LAT-4", "generation", 0, 28, 0.0, 0.0, 0.120643, "automatic"))
        self.assertEqual(find(self.results, "LAT-4", "generation")["unit"], "tasa")

    def test_str_1(self) -> None:
        self.assertEqual(find(self.results, "STR-1", "all"),
                         proportion("STR-1", "all", 28, 28, 1.0, 0.879357, 1.0, "automatic"))

    def test_str_2_categorias_y_total(self) -> None:
        self.assertEqual(find(self.results, "STR-2", "all"), expected_row(
            grp="robustness", metric_id="STR-2", behavior="all", status="measured",
            value=0, unit="recuento", judgment="automatic"))
        self.assertEqual(find(self.results, "STR-2", "timeout"), expected_row(
            grp="robustness", metric_id="STR-2", behavior="timeout", status="measured",
            value=0, unit="recuento", judgment="automatic"))

    def test_avl_1(self) -> None:
        self.assertEqual(find(self.results, "AVL-1", "all"),
                         proportion("AVL-1", "all", 56, 56, 1.0, 0.935806, 1.0, "automatic"))


class Run1RowsTest(unittest.TestCase):
    """El informe de la ejecución 1 difiere en ACC-2, REL-1, REL-2, REL-4 y LAT-*: se leen del JSON."""

    def setUp(self) -> None:
        _, self.results = adapt(REPORT_1)

    def test_mismo_numero_de_filas_y_claves(self) -> None:
        self.assertEqual(len(self.results), 48)
        for row in self.results:
            self.assertEqual(set(row), set(RESULT_KEYS))

    def test_valores_copiados_del_informe(self) -> None:
        # Los esperados se leen del JSON con accesos directos, sin pasar por el adaptador.
        metrics = REPORT_1["metrics"]
        for metric_id in ("ACC-2", "REL-1", "REL-2"):
            data = metrics[metric_id]
            with self.subTest(metric=metric_id):
                row = find(self.results, metric_id, "all")
                self.assertEqual(row["numerator"], data["k"])
                self.assertEqual(row["denominator"], data["n"])
                self.assertEqual(row["value"], data["rate"])
                self.assertEqual((row["ci_low"], row["ci_high"]), tuple(data["ci95"]))
        for behavior, field in (("median", "median"), ("q1", "q1"), ("q3", "q3")):
            with self.subTest(behavior=behavior):
                self.assertEqual(find(self.results, "REL-4", behavior)["value"], metrics["REL-4"][field])
        for metric_id in ("LAT-1", "LAT-2", "LAT-3"):
            for stage, data in metrics[metric_id]["stages"].items():
                with self.subTest(metric=metric_id, stage=stage):
                    row = find(self.results, metric_id, stage)
                    self.assertEqual(row["value"], data["value"])
                    self.assertEqual(row["denominator"], data["n"])
        judged = metrics["ACC-2"]["judged"]
        judged_row = find(self.results, "ACC-2", "judged")
        self.assertEqual((judged_row["numerator"], judged_row["denominator"], judged_row["value"]),
                         (judged["k"], judged["n"], judged["rate"]))

    def test_run_1_y_run_2_no_comparten_filas_distintas_de_las_del_informe(self) -> None:
        # Las dos ejecuciones difieren en sus valores: una adaptación que ignorase el informe lo delataría.
        _, results_2 = adapt(REPORT_2)
        self.assertNotEqual(self.results, results_2)


class CatalogueMappingTest(unittest.TestCase):
    """`grp` y `unit` de cada fila de métrica salen del catálogo de JUP-067."""

    def test_grp_y_unit_contra_el_catalogo(self) -> None:
        _, results = adapt(REPORT_2)
        seen = set()
        for row in results:
            if row["metric_id"] == "cases":
                continue
            item = CATALOGUE_BY_ID[row["metric_id"]]
            seen.add(row["metric_id"])
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                self.assertEqual(row["grp"], item["family"])
                self.assertEqual(row["unit"], item["unit"])
        self.assertEqual(seen, set(REPORT_2["metrics"]))

    def test_familias_y_unidades_literales(self) -> None:
        # Tabla literal para que un cambio del catálogo no arrastre al adaptador sin que nadie lo vea.
        expected = {
            "ACC-1": ("accuracy", "tasa"), "ACC-2": ("accuracy", "tasa"), "ACC-3": ("accuracy", "tasa"),
            "REL-1": ("relevance", "tasa"), "REL-2": ("relevance", "tasa"), "REL-3": ("relevance", "tasa"),
            "REL-4": ("relevance", "similitud"),
            "GRD-1": ("grounding", "tasa"), "GRD-2": ("grounding", "recuento"), "GRD-3": ("grounding", "tasa"),
            "LAT-1": ("latency", "ms"), "LAT-2": ("latency", "ms"), "LAT-3": ("latency", "ms"),
            "LAT-4": ("latency", "tasa"),
            "STR-1": ("robustness", "tasa"), "STR-2": ("robustness", "recuento"),
            "AVL-1": ("availability", "tasa"),
        }
        _, results = adapt(REPORT_2)
        for metric_id, (grp, unit) in expected.items():
            for row in rows_of(results, metric_id):
                with self.subTest(metric=metric_id, behavior=row["behavior"]):
                    self.assertEqual((row["grp"], row["unit"]), (grp, unit))

    def test_filas_de_recuento_grp_y_unit(self) -> None:
        _, results = adapt(REPORT_2)
        for row in results[:4]:
            self.assertEqual((row["grp"], row["metric_id"], row["behavior"], row["unit"]),
                             ("cases", "cases", "all", "casos"))


class JudgmentTest(unittest.TestCase):
    """Tabla de «Juicio humano o automático»."""

    def test_tabla_de_juicio(self) -> None:
        _, results = adapt(REPORT_2)
        by_status = {row["status"]: row["judgment"] for row in results[:4]}
        self.assertEqual(by_status, {"pass": "human", "fail": "human",
                                     "blocked": "automatic", "not_run": "automatic"})
        for row in results[4:]:
            if row["metric_id"] in HUMAN_METRICS or (row["metric_id"], row["behavior"]) == ("ACC-2", "judged"):
                expected = "human"
            else:
                expected = "automatic"
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                self.assertEqual(row["judgment"], expected)

    def test_acc_2_separa_comprobaciones_objetivas_y_juzgadas(self) -> None:
        # `all` agrupa comprobaciones por regla (automatic); `judged` son puntos juzgados por personas.
        _, results = adapt(REPORT_2)
        self.assertEqual(find(results, "ACC-2", "all")["judgment"], "automatic")
        self.assertEqual(find(results, "ACC-2", "judged")["judgment"], "human")

    def test_juicio_no_nulo_en_tipo_a(self) -> None:
        # En el tipo A el juicio siempre es automatic o human (null solo existe en el tipo B).
        _, results = adapt(REPORT_2)
        for row in results:
            self.assertIn(row["judgment"], ("automatic", "human"))


class NotMeasuredTest(unittest.TestCase):
    """Lo no medido es None con estado not_measured y nunca 0."""

    def assert_not_measured(self, row: dict, denominator=None) -> None:
        self.assertEqual(row["status"], "not_measured")
        for key in ("value", "numerator", "count", "ci_low", "ci_high"):
            with self.subTest(field=key):
                self.assertIsNone(row[key])  # assertIsNone distingue None de 0 y de 0.0
        self.assertEqual(row["denominator"], denominator)

    def assert_rest_intact(self, results: list[dict], touched: set) -> None:
        # Las demás filas deben ser idénticas a las del informe sin alterar.
        _, baseline = adapt(REPORT_2)
        self.assertEqual(len(results), len(baseline))
        for got, want in zip(results, baseline):
            if (got["metric_id"], got["behavior"]) not in touched:
                self.assertEqual(got, want)

    def test_acc_1_available_false(self) -> None:
        # Se deja rate=0.0 y k=0 a propósito: `available` False manda y el 0.0 no puede filtrarse como medido.
        report = variant(lambda r: r["metrics"]["ACC-1"].update(available=False))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "ACC-1", "all"), denominator=20)
        self.assert_rest_intact(results, {("ACC-1", "all")})

    def test_acc_1_rate_none(self) -> None:
        report = variant(lambda r: r["metrics"]["ACC-1"].update(rate=None, ci95=None, available=True))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "ACC-1", "all"), denominator=20)
        self.assert_rest_intact(results, {("ACC-1", "all")})

    def test_acc_1_sin_casos(self) -> None:
        # Sin casos aplicables (n=0) la tasa no está definida: no se convierte en 0 %.
        report = variant(lambda r: r["metrics"]["ACC-1"].update(k=0, n=0, rate=None, ci95=None, available=False))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "ACC-1", "all"), denominator=0)
        self.assert_rest_intact(results, {("ACC-1", "all")})

    def test_rate_con_ci95_ausente_deja_ci_none(self) -> None:
        # Una proporción medida sin ci95 conserva el valor y deja los límites en None.
        report = variant(lambda r: r["metrics"]["ACC-1"].pop("ci95"))
        _, results = adapt(report)
        row = find(results, "ACC-1", "all")
        self.assertEqual(row["status"], "measured")
        self.assertEqual(row["value"], 0.0)
        self.assertIsNone(row["ci_low"])
        self.assertIsNone(row["ci_high"])

    def test_available_false_manda_sobre_un_rate_presente(self) -> None:
        # Un informe incoherente (available False con rate 0.5) no debe publicar el 0.5 como medido.
        report = variant(lambda r: r["metrics"]["REL-2"].update(available=False))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "REL-2", "all"), denominator=20)

    def test_acc_2_judged_no_disponible(self) -> None:
        # Solo la fila `judged` pasa a no medida; `all` sigue medida.
        report = variant(lambda r: r["metrics"]["ACC-2"]["judged"].update(rate=None, ci95=None, available=False))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "ACC-2", "judged"), denominator=30)
        self.assertEqual(find(results, "ACC-2", "judged")["judgment"], "human")
        self.assertEqual(find(results, "ACC-2", "all")["status"], "measured")
        self.assert_rest_intact(results, {("ACC-2", "judged")})

    def test_grupo_de_acc_3(self) -> None:
        report = variant(lambda r: r["metrics"]["ACC-3"]["groups"]["abstain"].update(
            rate=None, ci95=None, available=False))
        _, results = adapt(report)
        self.assert_not_measured(find(results, "ACC-3", "abstain"), denominator=2)
        self.assertEqual(find(results, "ACC-3", "clarify")["status"], "measured")
        self.assert_rest_intact(results, {("ACC-3", "abstain")})

    def test_etapa_de_lat_4(self) -> None:
        report = variant(lambda r: r["metrics"]["LAT-4"]["stages"]["retrieval"].update(
            rate=None, ci95=None, available=False))
        _, results = adapt(report)
        row = find(results, "LAT-4", "retrieval")
        self.assert_not_measured(row, denominator=28)
        self.assertEqual(row["unit"], "tasa")
        self.assertEqual(find(results, "LAT-4", "generation")["status"], "measured")
        self.assert_rest_intact(results, {("LAT-4", "retrieval")})

    def test_rel_4_no_disponible(self) -> None:
        # Las tres filas (median, q1, q3) pasan a no medidas; sus cuantiles no se rellenan con 0.
        def make(report: dict) -> None:
            report["metrics"]["REL-4"].update(available=False, median=None, q1=None, q3=None)

        _, results = adapt(variant(make))
        rows = rows_of(results, "REL-4")
        self.assertEqual([r["behavior"] for r in rows], ["median", "q1", "q3"])
        for row in rows:
            with self.subTest(behavior=row["behavior"]):
                self.assert_not_measured(row, denominator=20)
        self.assert_rest_intact(results, {("REL-4", "median"), ("REL-4", "q1"), ("REL-4", "q3")})

    def test_rel_4_available_false_aunque_traiga_valores(self) -> None:
        report = variant(lambda r: r["metrics"]["REL-4"].update(available=False))
        _, results = adapt(report)
        for row in rows_of(results, "REL-4"):
            with self.subTest(behavior=row["behavior"]):
                self.assertEqual(row["status"], "not_measured")
                self.assertIsNone(row["value"])

    def test_grd_2_no_disponible(self) -> None:
        # Con available False tampoco se publican los recuentos por caso como medidos.
        def make(report: dict) -> None:
            report["metrics"]["GRD-2"].update(
                total=2, by_case={"JUP-069-005": 2}, available=False)

        _, results = adapt(variant(make))
        rows = rows_of(results, "GRD-2")
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(behavior=row["behavior"]):
                self.assertEqual(row["status"], "not_measured")
                self.assertIsNone(row["value"])
                self.assertIsNone(row["count"])
        self.assert_rest_intact(results, {(r["metric_id"], r["behavior"]) for r in rows})

    def test_grd_2_disponible_con_fallos_por_caso(self) -> None:
        # Una fila `all` con el total y una fila por caso (identificador de caso como `behavior`).
        def make(report: dict) -> None:
            report["metrics"]["GRD-2"].update(
                total=3, by_case={"JUP-069-005": 2, "JUP-069-006": 1}, available=True)

        _, results = adapt(variant(make))
        self.assertEqual([r["behavior"] for r in rows_of(results, "GRD-2")], ["all", "JUP-069-005", "JUP-069-006"])
        self.assertEqual(find(results, "GRD-2", "all")["value"], 3)
        self.assertEqual(find(results, "GRD-2", "JUP-069-005")["value"], 2)
        self.assertEqual(find(results, "GRD-2", "JUP-069-006")["value"], 1)
        for row in rows_of(results, "GRD-2"):
            self.assertEqual((row["status"], row["unit"], row["grp"]), ("measured", "recuento", "grounding"))

    def test_etapa_de_lat_1_sin_valor(self) -> None:
        report = variant(lambda r: r["metrics"]["LAT-1"]["stages"]["generation"].update(value=None))
        _, results = adapt(report)
        row = find(results, "LAT-1", "generation")
        self.assert_not_measured(row, denominator=28)
        self.assertEqual(row["unit"], "ms")
        # `total` conserva su propio valor medido: la ausencia de una etapa no contamina a las demás.
        self.assertEqual(find(results, "LAT-1", "total")["status"], "measured")
        self.assert_rest_intact(results, {("LAT-1", "generation")})

    def test_cero_medido_no_se_confunde_con_no_medido(self) -> None:
        # Contraste: value 0 y rate 0.0 con available True son mediciones y no pueden pasar a not_measured.
        _, results = adapt(REPORT_2)
        for metric_id, behavior in (("LAT-2", "embedding"), ("ACC-1", "all"), ("STR-2", "timeout")):
            with self.subTest(metric=metric_id):
                row = find(results, metric_id, behavior)
                self.assertEqual(row["status"], "measured")
                self.assertIsNotNone(row["value"])

    def test_no_medido_con_run_dentro_del_informe_no_cambia_el_run(self) -> None:
        # Que una métrica no se mida no altera el bloque `run`.
        report = variant(lambda r: r["metrics"]["ACC-1"].update(available=False))
        run, _ = adapt(report)
        self.assertEqual(run, adapt(REPORT_2)[0])


class CountsTest(unittest.TestCase):
    """blocked y not_run son estados propios y nunca se suman a fail."""

    @staticmethod
    def with_counts(**counts) -> dict:
        def make(report: dict) -> None:
            report["counts"].update(counts)

        return variant(make)

    def test_blocked_y_not_run_no_se_suman_a_fail(self) -> None:
        report = self.with_counts(**{"pass": 10, "fail": 8, "blocked": 6, "not_run": 4})
        _, results = adapt(report)
        by_status = {row["status"]: row for row in results[:4]}
        self.assertEqual({k: v["count"] for k, v in by_status.items()},
                         {"pass": 10, "fail": 8, "blocked": 6, "not_run": 4})
        self.assertEqual(sum(row["count"] for row in results[:4]), 28)
        for row in results[:4]:
            self.assertEqual(row["denominator"], 28)
            self.assertEqual(row["metric_id"], "cases")
            self.assertIsNone(row["value"])
            self.assertEqual(row["status"] in CASE_STATUSES, True)

    def test_blocked_y_not_run_son_filas_propias(self) -> None:
        report = self.with_counts(**{"pass": 0, "fail": 20, "blocked": 5, "not_run": 3})
        _, results = adapt(report)
        self.assertEqual([r["status"] for r in rows_of(results, "cases")], list(CASE_STATUSES))
        self.assertEqual(find_status(results, "fail")["count"], 20)
        self.assertEqual(find_status(results, "blocked")["count"], 5)
        self.assertEqual(find_status(results, "not_run")["count"], 3)
        self.assertEqual(find_status(results, "blocked")["judgment"], "automatic")
        self.assertEqual(find_status(results, "not_run")["judgment"], "automatic")

    def test_coherencia_con_los_informes_reales(self) -> None:
        for name, report in (("run-1", REPORT_1), ("run-2", REPORT_2)):
            _, results = adapt(report)
            counts = report["counts"]
            with self.subTest(report=name):
                total = sum(row["count"] for row in results[:4])
                self.assertEqual(total, counts["cases"])
                for row in results[:4]:
                    self.assertEqual(row["count"], counts[row["status"]])
                    self.assertEqual(row["denominator"], counts["cases"])


def find_status(results: list[dict], status: str) -> dict:
    matches = [row for row in results if row["metric_id"] == "cases" and row["status"] == status]
    assert len(matches) == 1
    return matches[0]


class ErrorsTest(unittest.TestCase):
    """AdapterError con «<campo>: <problema>»."""

    def assert_error(self, report, field: str, *, prefix: bool = True) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        self.assertIn(field, message)
        if prefix:
            # Formato del contrato: el mensaje empieza por el campo y un separador.
            self.assertTrue(message.startswith(f"{field}: "), message)

    def test_report_no_es_dict(self) -> None:
        for bad in ([], None, "informe", 3, [REPORT_2]):
            with self.subTest(bad=repr(bad)[:20]):
                self.assert_error(bad, "report")

    def test_report_version(self) -> None:
        # Solo el entero 1 vale: True (que es 1 en Python), "1" o la ausencia se rechazan.
        for bad in (2, 0, True, "1", None):
            with self.subTest(version=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(report_version=bad)), "report_version")
        self.assert_error(variant(lambda r: r.pop("report_version")), "report_version")

    def test_catalogue_version_distinta(self) -> None:
        self.assert_error(variant(lambda r: r.update(catalogue_version="9.9.9")), "catalogue_version")
        self.assert_error(variant(lambda r: r.update(catalogue_version=None)), "catalogue_version")
        self.assert_error(variant(lambda r: r.pop("catalogue_version")), "catalogue_version")

    def test_counts_inconsistente(self) -> None:
        # pass+fail+blocked+not_run debe ser igual a cases.
        self.assert_error(variant(lambda r: r["counts"].update(**{"pass": 1})), "counts")
        self.assert_error(variant(lambda r: r["counts"].update(fail=27)), "counts")
        self.assert_error(variant(lambda r: r["counts"].update(cases=29)), "counts")

    def test_counts_ausente_o_no_dict(self) -> None:
        self.assert_error(variant(lambda r: r.pop("counts")), "counts")
        self.assert_error(variant(lambda r: r.update(counts=None)), "counts")
        self.assert_error(variant(lambda r: r.update(counts=[28, 0, 28, 0, 0])), "counts")

    def test_counts_con_valores_no_validos(self) -> None:
        cases = {
            "negativo": {"pass": -1, "fail": 29},        # suma coherente, pero un recuento negativo
            "bool": {"pass": True, "fail": 27},          # True sumaría 1 pero no es un recuento
            "cadena": {"pass": "0", "fail": 28},
            "decimal": {"pass": 0.5, "fail": 27.5},
            "nulo": {"pass": None},
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                self.assert_error(variant(lambda r, change=change: r["counts"].update(change)), "counts")

    def test_counts_con_clave_ausente(self) -> None:
        for key in ("cases", "pass", "fail", "blocked", "not_run"):
            with self.subTest(key=key):
                self.assert_error(variant(lambda r, key=key: r["counts"].pop(key)), "counts")

    def test_cases_bool_o_cadena(self) -> None:
        self.assert_error(variant(lambda r: r["counts"].update(cases="28")), "counts")
        self.assert_error(variant(lambda r: r["counts"].update(cases=True, **{"pass": 0, "fail": 1,
                                                                              "blocked": 0, "not_run": 0})), "counts")

    def test_run_ausente_o_no_objeto(self) -> None:
        self.assert_error(variant(lambda r: r.pop("run")), "run")
        self.assert_error(variant(lambda r: r.update(run=None)), "run")
        self.assert_error(variant(lambda r: r.update(run=[])), "run")

    def test_campos_obligatorios_de_run(self) -> None:
        # Cada uno de los diez campos obligatorios ausente: el mensaje nombra `run.<campo>`.
        for field in ("commit", "date", "provider", "alias", "suite_version", "suite_sha256",
                      "corpus", "generation", "retrieval", "synthetic"):
            with self.subTest(field=field):
                self.assert_error(variant(lambda r, field=field: r["run"].pop(field)), f"run.{field}")

    def test_campos_anidados_obligatorios(self) -> None:
        self.assert_error(variant(lambda r: r["run"]["corpus"].pop("sha256")), "run.corpus.sha256")
        self.assert_error(variant(lambda r: r["run"]["generation"].pop("model_alias")),
                          "run.generation.model_alias")

    def test_objetos_de_run_no_objeto(self) -> None:
        for field in ("corpus", "generation", "retrieval"):
            with self.subTest(field=field):
                self.assert_error(variant(lambda r, field=field: r["run"].update({field: None})),
                                  f"run.{field}", prefix=False)
                self.assert_error(variant(lambda r, field=field: r["run"].update({field: "texto"})),
                                  f"run.{field}", prefix=False)

    def test_date_no_iso(self) -> None:
        # `date` no admite null (una ejecución sin fecha no se puede ordenar en las series).
        for bad in ("ayer", "", "08/10/2026", "2026-13-45T00:00:00Z", 20261008, None):
            with self.subTest(date=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["run"].update(date=bad)), "run.date")

    def test_synthetic_no_bool(self) -> None:
        # Bool estricto: 1/0 o cadenas no sirven (decide el motivo de ejecución no real `sintetica`).
        for bad in ("true", "yes", 1, 0, None):
            with self.subTest(synthetic=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["run"].update(synthetic=bad)), "run.synthetic")

    def test_metrics_no_dict(self) -> None:
        for bad in ([], None, "x", 3):
            with self.subTest(metrics=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(metrics=bad)), "metrics")
        self.assert_error(variant(lambda r: r.pop("metrics")), "metrics")

    def test_metrica_desconocida(self) -> None:
        # Una métrica fuera del catálogo indica un informe de otra versión: se rechaza con su identificador.
        self.assert_error(variant(lambda r: r["metrics"].update({"XYZ-9": {"k": 1, "n": 2}})), "metrics.XYZ-9")

    def test_metrica_desconocida_entre_conocidas(self) -> None:
        report = variant(lambda r: r["metrics"].update({"ACC-9": {}}))
        self.assert_error(report, "metrics.ACC-9")


class PurityTest(unittest.TestCase):
    """La función no muta la entrada, es determinista y tolera lo que no usa."""

    def test_no_muta_el_informe(self) -> None:
        for name, report in (("run-1", REPORT_1), ("run-2", REPORT_2)):
            candidate = copy.deepcopy(report)
            adapt(candidate)
            with self.subTest(report=name):
                self.assertEqual(candidate, report)

    def test_no_muta_el_informe_con_no_medidos(self) -> None:
        report = variant(lambda r: r["metrics"]["ACC-1"].update(available=False, rate=None))
        before = copy.deepcopy(report)
        adapt(report)
        self.assertEqual(report, before)

    def test_dos_llamadas_dan_lo_mismo(self) -> None:
        first = adapt(REPORT_2)
        second = adapt(REPORT_2)
        self.assertEqual(first, second)
        # Y las salidas son independientes: mutar una no altera la otra.
        first[1][0]["count"] = 999
        self.assertNotEqual(adapt(REPORT_2)[1][0]["count"], 999)

    def test_claves_de_nivel_superior_desconocidas_se_ignoran(self) -> None:
        # `gaps`, `critical`, `notes` y `generated_at` ya existen; se añaden otras sin efecto.
        def extend(report: dict) -> None:
            report["notes"] = ["nota del informe"]
            report["extra_futuro"] = {"cualquier": "cosa"}
            report["generated_at"] = "2030-01-01T00:00:00Z"

        self.assertEqual(adapt(variant(extend)), adapt(REPORT_2))

    def test_sin_claves_opcionales_del_informe(self) -> None:
        # Quitar gaps, critical, notes y generated_at no cambia nada: no se usan.
        def strip(report: dict) -> None:
            for key in ("gaps", "critical", "notes", "generated_at"):
                report.pop(key)

        self.assertEqual(adapt(variant(strip)), adapt(REPORT_2))

    def test_metrica_del_catalogo_ausente_no_es_error(self) -> None:
        # Una métrica ausente no genera filas ni error: lo que no está no se inventa.
        report = variant(lambda r: (r["metrics"].pop("ACC-1"), r["metrics"].pop("LAT-4")))
        _, results = adapt(report)
        self.assertEqual(len(results), 48 - 1 - 3)
        self.assertEqual(rows_of(results, "ACC-1"), [])
        self.assertEqual(rows_of(results, "LAT-4"), [])
        self.assertEqual(find(results, "ACC-2", "all")["status"], "measured")

    def test_metrics_vacio_solo_deja_los_recuentos(self) -> None:
        _, results = adapt(variant(lambda r: r.update(metrics={})))
        self.assertEqual([row["status"] for row in results], list(CASE_STATUSES))

    def test_el_orden_de_las_metricas_es_el_del_informe(self) -> None:
        # Las filas siguen el orden de `report["metrics"]` y no el del catálogo.
        def reverse(report: dict) -> None:
            report["metrics"] = dict(reversed(list(report["metrics"].items())))

        _, results = adapt(variant(reverse))
        order: list[str] = []
        for row in results[4:]:
            if not order or order[-1] != row["metric_id"]:
                order.append(row["metric_id"])
        self.assertEqual(order, list(reversed(list(REPORT_2["metrics"]))))
        self.assertEqual([r["status"] for r in results[:4]], list(CASE_STATUSES))


class NoFreeTextTest(unittest.TestCase):
    """Ninguna cadena de la salida es texto libre."""

    def assert_identifiers(self, run: dict, results: list[dict]) -> None:
        for text in list(string_values(run)) + list(string_values(results)):
            with self.subTest(text=text[:40]):
                self.assertLessEqual(len(text), 80)
                self.assertNotIn(" ", text)
                self.assertTrue(tool.IDENTIFIER_RE.match(text), text)

    def test_run_y_filas_reales_solo_llevan_identificadores(self) -> None:
        # `covers` ("successful calls only") y `scope` ("casos criticos") del informe tienen espacios y no se copian.
        for report in (REPORT_1, REPORT_2):
            run, results = adapt(report)
            self.assert_identifiers(run, results)

    def test_notes_y_gaps_no_se_copian(self) -> None:
        marker = "Texto libre con espacios que no debe aparecer en la salida"

        def inject(report: dict) -> None:
            report["notes"] = [marker]
            report["gaps"] = [marker, "JUP-069-024"]
            report["critical"] = {"cases": [marker]}
            report["metrics"]["ACC-2"]["target"]["origin"] = marker
            report["metrics"]["LAT-1"]["stages"]["total"]["covers"] = marker

        run, results = adapt(variant(inject))
        dumped = json.dumps([run, results], ensure_ascii=False)
        self.assertNotIn("Texto libre", dumped)
        self.assertNotIn(marker, dumped)
        self.assert_identifiers(run, results)

    def test_sin_gaps_ni_critical_en_la_salida(self) -> None:
        # Los identificadores de caso de `gaps`/`critical` no son filas: la salida no los trae en `behavior`.
        _, results = adapt(REPORT_2)
        behaviors = {row["behavior"] for row in results}
        for case_id in REPORT_2["gaps"] + REPORT_2["critical"]["cases"]:
            self.assertNotIn(case_id, behaviors)


class ExactCopyTest(unittest.TestCase):
    """Los valores medidos se copian sin redondear ni convertir."""

    def test_flotante_con_muchos_decimales_identico(self) -> None:
        _, results = adapt(REPORT_2)
        median = find(results, "REL-4", "median")["value"]
        self.assertEqual(median, 0.6166171504041825)
        self.assertEqual(repr(median), "0.6166171504041825")
        self.assertIsInstance(median, float)

    def test_todos_los_valores_de_rel_4_identicos_al_json(self) -> None:
        # Se compara con el JSON leído de nuevo del disco, no con el objeto ya cargado en el módulo.
        raw = json.loads((ROOT / "docs" / "evidence" / "JUP-070-run-2-report.json").read_text(encoding="utf8"))
        _, results = adapt(raw)
        rel4 = raw["metrics"]["REL-4"]
        for behavior in ("median", "q1", "q3"):
            with self.subTest(behavior=behavior):
                self.assertEqual(find(results, "REL-4", behavior)["value"], rel4[behavior])

    def test_enteros_y_flotantes_conservan_su_tipo(self) -> None:
        # value 0 de la latencia es int y rate 0.0 es float: no se convierte uno en otro.
        _, results = adapt(REPORT_2)
        self.assertIs(type(find(results, "LAT-2", "embedding")["value"]), int)
        self.assertIs(type(find(results, "LAT-2", "total")["value"]), float)
        self.assertIs(type(find(results, "ACC-1", "all")["value"]), float)
        self.assertIs(type(find(results, "ACC-1", "all")["numerator"]), int)

    def test_intervalo_de_confianza_sin_redondeo(self) -> None:
        def make(report: dict) -> None:
            report["metrics"]["REL-2"].update(rate=0.8000000000000002, ci95=[0.5839830000000001, 0.9193419999999999])

        _, results = adapt(variant(make))
        row = find(results, "REL-2", "all")
        self.assertEqual(row["value"], 0.8000000000000002)
        self.assertEqual(row["ci_low"], 0.5839830000000001)
        self.assertEqual(row["ci_high"], 0.9193419999999999)


if __name__ == "__main__":
    unittest.main()
