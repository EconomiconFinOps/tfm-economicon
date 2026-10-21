"""Adaptador de las métricas de negocio de JUP-068 de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.5, fase Red).

Contrato que se valida (dos funciones):

* `adapt_jup068(report, run_id) -> (run, results)`: PURA sobre el dict del informe que produce
  `node tools/business-metrics.mjs report` (no lee ficheros, no lo muta y no comparte estructuras con él).
  - `run` tiene EXACTAMENTE las claves de `RUN_KEYS`: `source` y `suite` son `JUP-068`, `commit` el del
    informe, `suite_version` la `dataset_version`, `suite_sha256` la `input_sha256`, `run_at` None (el
    informe no trae marca de ejecución), `synthetic` es `provenance == "synthetic"`. Todo lo demás (corpus,
    embeddings, recuperación, modelo, prompt) es None. No se publica ningún texto libre (`scope`,
    `configuration`, `reviewer`, `evidence`, `period`, identificadores de parejas o estimaciones).
  - `results` son 23 filas de tipo B en este orden: 8 de tiempo (cuatro estados de las parejas, tiempo manual,
    asistido, ahorrado y su porcentaje), 9 de asignación (seis importes y tres porcentajes) y 6 de ahorro
    (tres recuentos de oportunidades, ahorro potencial, su porcentaje y ahorro realizado).
  - Regla 1 del contrato: lo no medido (`null` en el informe, o una suma de nada) es None con estado
    `not_measured`, nunca un cero; conserva el denominador donde el contrato lo indica. Un 0 medido sigue
    siendo `measured`. `realized_minor` es SIEMPRE null en el informe: sale no medido («beneficio realizado
    no medido»). Los valores se copian exactos y con su tipo (sin redondear).
* `read_business_report(path) -> dict`: ejecuta `node tools/business-metrics.mjs report <ruta>` con
  `subprocess.run` y devuelve el JSON de la salida. Cualquier fallo es un `AdapterError` cuyo mensaje EMPIEZA
  por `business-metrics: ` y nombra el fichero.

Los esperados se escriben a mano a partir del informe real del ejemplo (`docs/validation/JUP-068-example.json`),
nunca llamando al adaptador. Las variantes se construyen con `copy.deepcopy` del informe real, de modo que solo
cambia el dato que se quiere probar. El informe real se obtiene de verdad ejecutando Node (sin skip).

Endurecimiento desde el principio (lección de la mutación de 2.1 a 2.4): bool frente a entero, NaN e infinito,
cero medido frente a no medido, denominadores distintos por fila para detectar cruces, `governed` con valores
asimétricos, moneda y escala distintas de las del ejemplo, prefijo EXACTO del mensaje de error.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para
apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup068", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EXAMPLE_PATH = ROOT / "docs" / "validation" / "JUP-068-example.json"
CLI_PATH = ROOT / "tools" / "business-metrics.mjs"

RUN_ID = "JUP-068-synthetic-example-v1"

# Claves literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
    "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)

MARKER = "Texto libre con espacios que no debe aparecer en la salida"

# Datos del informe real, escritos a mano desde la salida del CLI (se contrastan con el informe en una guarda).
REAL_COMMIT = "6410950315b0e3c22057d09015e11e38c5e455ab"
REAL_DATASET_VERSION = "JUP-068-example-v1"
REAL_INPUT_SHA256 = "b3c9469a2c6af966092b3fb353116b7566d63b05fa2c935574c887b403c1155b"

# Orden contractual de las 23 filas, con una etiqueta corta por fila para construir variantes.
LABELS = (
    "trials_pass", "trials_fail", "trials_blocked", "trials_not_run", "manual", "assisted", "saved", "saved_pct",
    "allocated", "shared", "unallocated", "excluded", "total", "eligible", "assigned_pct", "governed_pct",
    "unallocated_pct",
    "estimated", "candidate", "not_evaluable", "potential", "potential_pct", "realized",
)

# Informe del CLI y su salida cruda; los fija `setUpModule` ejecutando Node de verdad.
REPORT: dict = {}
CLI_STDOUT = ""


def run_node(path) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(CLI_PATH), "report", str(path)], capture_output=True, text=True,
                          encoding="utf-8", timeout=60, cwd=ROOT)


def setUpModule() -> None:
    # El informe de entrada es la salida REAL del generador sobre el ejemplo versionado: si el generador o el
    # ejemplo cambian, estas pruebas lo notan en vez de quedarse con una copia a mano que envejece.
    global REPORT, CLI_STDOUT
    completed = run_node(EXAMPLE_PATH)
    assert completed.returncode == 0, completed.stderr
    CLI_STDOUT = completed.stdout
    REPORT = json.loads(CLI_STDOUT)
    # Guarda de la propia prueba (no es un test del adaptador): las constantes escritas a mano deben seguir al
    # informe real. Si el ejemplo o el generador cambian, el fallo apunta aquí y no a un adaptador correcto.
    assert REPORT["commit"] == REAL_COMMIT, "constante REAL_COMMIT desfasada"
    assert REPORT["dataset_version"] == REAL_DATASET_VERSION, "constante REAL_DATASET_VERSION desfasada"
    assert REPORT["input_sha256"] == REAL_INPUT_SHA256, "constante REAL_INPUT_SHA256 desfasada"
    assert REPORT["currency"] == "EUR" and REPORT["minor_unit_digits"] == 2, "moneda del ejemplo desfasada"
    assert REPORT["savings"]["realized_minor"] is None, "el ahorro realizado ya no es null en el informe"


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup068(report, run_id)


def expected_run(**fields) -> dict:
    """`run` esperado del informe real; cada prueba puede sobrescribir lo que cambie."""
    run = {
        "run_id": RUN_ID, "source": "JUP-068", "run_at": None, "commit": REAL_COMMIT, "suite": "JUP-068",
        "suite_version": REAL_DATASET_VERSION, "suite_sha256": REAL_INPUT_SHA256, "corpus_sha256": None,
        "embedding_provider": None, "embedding_alias": None, "retrieval": None, "generation_model": None,
        "prompt_sha256": None, "synthetic": True, "generation_model_id": None, "generation_provider": None, "generation_quantization": None, "gateway_config_sha256": None,
    }
    run.update(fields)
    return run


def make_row(grp: str, metric_id: str, unit: str, status: str = "measured", behavior: str = "all", count=None,
             value=None, numerator=None, denominator=None) -> dict:
    """Fila esperada completa: todo lo no indicado es None salvo los valores fijos del tipo B."""
    row = {key: None for key in RESULT_KEYS}
    row.update(measure_type="B", grp=grp, metric_id=metric_id, behavior=behavior, status=status, count=count,
               value=value, unit=unit, numerator=numerator, denominator=denominator, judgment=None,
               selected=False)
    return row


def no_data(grp: str, metric_id: str, unit: str, denominator=None, behavior: str = "all") -> dict:
    """Fila no medida: value, numerator y count None (assertEqual distingue None de 0), denominador conservado."""
    return make_row(grp, metric_id, unit, "not_measured", behavior, denominator=denominator)


def real_rows() -> list[dict]:
    """Las 23 filas esperadas del ejemplo real, escritas a mano en el orden del contrato."""
    eur = "eur_minor_2"
    return [
        # Tiempo: estados de las parejas (denominador = 3 intentos) y tiempos.
        make_row("time", "time_trials", "parejas", "pass", count=2, denominator=3),
        make_row("time", "time_trials", "parejas", "fail", count=1, denominator=3),
        make_row("time", "time_trials", "parejas", "blocked", count=0, denominator=3),
        make_row("time", "time_trials", "parejas", "not_run", count=0, denominator=3),
        make_row("time", "manual_time", "ms", value=900000, denominator=2),
        make_row("time", "assisted_time", "ms", value=540000, denominator=2),
        make_row("time", "time_saved", "ms", value=360000, denominator=2),
        make_row("time", "time_saved_percent", "porcentaje", value=40, numerator=360000, denominator=900000),
        # Asignación: importes en unidad menor y porcentajes sobre el gasto elegible (100000).
        make_row("allocation", "allocated", eur, value=70000),
        make_row("allocation", "shared", eur, value=20000),
        make_row("allocation", "unallocated", eur, value=10000),
        make_row("allocation", "excluded", eur, value=5000),
        make_row("allocation", "total", eur, value=105000),
        make_row("allocation", "eligible", eur, value=100000),
        make_row("allocation", "assigned_percent", "porcentaje", value=70, numerator=70000, denominator=100000),
        make_row("allocation", "governed_percent", "porcentaje", value=90, numerator=90000, denominator=100000),
        make_row("allocation", "unallocated_percent", "porcentaje", value=10, numerator=10000,
                 denominator=100000),
        # Ahorro: recuentos de oportunidades, ahorro potencial y ahorro realizado (no medido).
        make_row("savings", "opportunities", "recuento", behavior="estimated", value=1),
        make_row("savings", "opportunities", "recuento", behavior="candidate", value=1),
        make_row("savings", "opportunities", "recuento", behavior="not_evaluable", value=0),
        make_row("savings", "potential_savings", eur, value=14000),
        make_row("savings", "potential_savings_percent", "porcentaje", value=14.000000000000002, numerator=14000,
                 denominator=100000),
        no_data("savings", "realized_savings", eur),
    ]


def expected_with(**changes) -> list[dict]:
    """Las filas reales con algunas sustituidas por etiqueta (`LABELS`); el resto debe quedar intacto."""
    rows = real_rows()
    for label, row in changes.items():
        rows[LABELS.index(label)] = row
    return rows


def variant(mutate, base: dict | None = None) -> dict:
    """Copia profunda del informe con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(REPORT if base is None else base)
    mutate(report)
    return report


def with_section(section: str, **fields) -> dict:
    return variant(lambda r: r[section].update(fields))


def with_time(**fields) -> dict:
    return with_section("time", **fields)


def with_results(**fields) -> dict:
    return variant(lambda r: r["time"]["results"].update(fields))


def with_allocation(**fields) -> dict:
    return with_section("allocation", **fields)


def with_savings(**fields) -> dict:
    return with_section("savings", **fields)


def set_path(report: dict, path: tuple, value) -> dict:
    """Copia del informe con el campo anidado `path` sustituido por `value`."""
    copied = copy.deepcopy(report)
    target = copied
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return copied


def drop_path(report: dict, path: tuple) -> dict:
    copied = copy.deepcopy(report)
    target = copied
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return copied


def dotted(path: tuple) -> str:
    return ".".join(path)


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


def containers(value):
    """Todos los dict y list (no escalares) de una estructura anidada, incluida ella misma."""
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from containers(item)
    elif isinstance(value, (list, tuple)):
        yield value
        for item in value:
            yield from containers(item)


# Campos que deben ser enteros >= 0 (no bool, no float), y los que pueden ser null además.
COUNT_PATHS = (
    ("time", "results", "pass"), ("time", "results", "fail"), ("time", "results", "blocked"),
    ("time", "results", "not_run"), ("time", "eligible_pairs"), ("time", "manual_ms"), ("time", "assisted_ms"),
    ("allocation", "allocated"), ("allocation", "shared"), ("allocation", "unallocated"),
    ("allocation", "excluded"), ("allocation", "total_minor"), ("allocation", "eligible_minor"),
    ("savings", "estimated_count"), ("savings", "candidate_count"), ("savings", "not_evaluable_count"),
)
NULLABLE_INT_PATHS = (("time", "saved_ms"), ("savings", "potential_minor"), ("savings", "realized_minor"))
NULLABLE_NUMBER_PATHS = (
    ("time", "saved_percent"), ("allocation", "assigned_percent"), ("allocation", "governed_percent"),
    ("allocation", "unallocated_percent"), ("savings", "potential_percent"),
)
TOP_STRING_FIELDS = ("commit", "dataset_version", "input_sha256")


class RunBlockTest(unittest.TestCase):
    """El bloque `run`: procedencia y huellas del informe, sin nada de lo que el informe no registra."""

    def test_run_completo_del_informe_real(self) -> None:
        run, _ = adapt(REPORT)
        self.assertEqual(tuple(run), RUN_KEYS)
        self.assertEqual(run, {
            "run_id": "JUP-068-synthetic-example-v1",
            "source": "JUP-068",
            "run_at": None,
            "commit": "6410950315b0e3c22057d09015e11e38c5e455ab",
            "suite": "JUP-068",
            "suite_version": "JUP-068-example-v1",
            "suite_sha256": "b3c9469a2c6af966092b3fb353116b7566d63b05fa2c935574c887b403c1155b",
            "corpus_sha256": None,
            "embedding_provider": None,
            "embedding_alias": None,
            "retrieval": None,
            "generation_model": None,
            "prompt_sha256": None,
            "synthetic": True,
            "generation_model_id": None,
            "generation_provider": None,
            "generation_quantization": None,
            "gateway_config_sha256": None,
        })

    def test_run_id_es_el_argumento_y_no_el_del_informe(self) -> None:
        run, _ = adapt(REPORT, "otro-id.v2")
        self.assertEqual(run, expected_run(run_id="otro-id.v2"))
        self.assertNotEqual(run["run_id"], REPORT["run_id"])

    def test_commit_version_y_huella_siguen_al_informe(self) -> None:
        # Valores distintos entre sí y de los reales: commit, versión y huella no se intercambian.
        def change(report: dict) -> None:
            report["commit"] = "a" * 40
            report["dataset_version"] = "dataset-v9"
            report["input_sha256"] = "b" * 64

        run, _ = adapt(variant(change))
        self.assertEqual(run, expected_run(commit="a" * 40, suite_version="dataset-v9", suite_sha256="b" * 64))

    def test_provenance_synthetic_es_synthetic_true(self) -> None:
        run, _ = adapt(variant(lambda r: r.update(provenance="synthetic")))
        self.assertIs(run["synthetic"], True)

    def test_provenance_measured_es_synthetic_false(self) -> None:
        # Una ejecución medida no se marca como sintética (sería esconderla de las series reales).
        run, _ = adapt(variant(lambda r: r.update(provenance="measured")))
        self.assertIs(run["synthetic"], False)
        self.assertEqual(run, expected_run(synthetic=False))

    def test_campos_no_registrados_son_none(self) -> None:
        run, _ = adapt(REPORT)
        for key in ("run_at", "corpus_sha256", "embedding_provider", "embedding_alias", "retrieval",
                    "generation_model", "prompt_sha256"):
            with self.subTest(campo=key):
                self.assertIsNone(run[key])

    def test_el_informe_no_publica_nada_de_su_procedencia_libre(self) -> None:
        # `scope`, `configuration`, `reviewer`, `evidence` y `period` son texto libre o fechas: no entran.
        run, results = adapt(REPORT)
        dumped = json.dumps([run, results], ensure_ascii=False)
        for forbidden in (REPORT["scope"], REPORT["configuration"], REPORT["reviewer"], "2026-09-01",
                          "docs/validation", "synthetic:pair"):
            with self.subTest(texto=forbidden[:30]):
                self.assertNotIn(forbidden, dumped)

    def test_el_run_no_depende_de_los_resultados_no_medidos(self) -> None:
        run, _ = adapt(with_savings(potential_minor=None, potential_percent=None, estimated_count=0))
        self.assertEqual(run, expected_run())


class RealReportRowsTest(unittest.TestCase):
    """Normalización completa del informe real: 23 filas de tipo B."""

    def setUp(self) -> None:
        _, self.results = adapt(REPORT)

    def test_numero_de_filas(self) -> None:
        self.assertEqual(len(self.results), 23)
        self.assertEqual(len(LABELS), 23)

    def test_filas_completas_y_en_orden(self) -> None:
        # Igualdad de lista completa contra la tabla escrita a mano: orden, claves, valores, tipos de fila.
        self.assertEqual(self.results, real_rows())

    def test_forma_comun_de_todas_las_filas(self) -> None:
        for row in self.results:
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"], status=row["status"]):
                self.assertEqual(tuple(row), RESULT_KEYS)
                self.assertEqual(row["measure_type"], "B")
                self.assertIsNone(row["judgment"])
                self.assertIs(row["selected"], False)
                for key in ("ci_low", "ci_high"):
                    self.assertIsNone(row[key])

    def test_grupos_por_bloque(self) -> None:
        self.assertEqual([row["grp"] for row in self.results], ["time"] * 8 + ["allocation"] * 9 + ["savings"] * 6)

    def test_estados_de_las_parejas(self) -> None:
        # pass 2 / fail 1 / blocked 0 / not_run 0, con la suma de los cuatro (3) como denominador y el
        # recuento en `count` (no en `value`).
        rows = self.results[:4]
        self.assertEqual([row["status"] for row in rows], ["pass", "fail", "blocked", "not_run"])
        self.assertEqual([row["count"] for row in rows], [2, 1, 0, 0])
        self.assertEqual([row["denominator"] for row in rows], [3, 3, 3, 3])
        for row in rows:
            self.assertEqual((row["metric_id"], row["unit"], row["behavior"]), ("time_trials", "parejas", "all"))
            self.assertIsNone(row["value"])
            self.assertIsNone(row["numerator"])

    def test_tiempos(self) -> None:
        manual, assisted, saved, percent = self.results[4:8]
        self.assertEqual((manual["metric_id"], manual["value"], manual["denominator"]), ("manual_time", 900000, 2))
        self.assertEqual((assisted["metric_id"], assisted["value"], assisted["denominator"]),
                         ("assisted_time", 540000, 2))
        self.assertEqual((saved["metric_id"], saved["value"], saved["denominator"]), ("time_saved", 360000, 2))
        for row in (manual, assisted, saved):
            self.assertEqual(row["unit"], "ms")
            self.assertEqual(row["status"], "measured")
            self.assertIsNone(row["numerator"])
        self.assertEqual((percent["metric_id"], percent["unit"], percent["value"], percent["numerator"],
                          percent["denominator"]), ("time_saved_percent", "porcentaje", 40, 360000, 900000))

    def test_importes_de_asignacion_en_unidad_menor(self) -> None:
        amounts = self.results[8:14]
        self.assertEqual([row["metric_id"] for row in amounts],
                         ["allocated", "shared", "unallocated", "excluded", "total", "eligible"])
        self.assertEqual([row["value"] for row in amounts], [70000, 20000, 10000, 5000, 105000, 100000])
        for row in amounts:
            self.assertEqual(row["unit"], "eur_minor_2")
            self.assertIsNone(row["denominator"])
            self.assertIsNone(row["numerator"])

    def test_porcentajes_de_asignacion_con_numerador_y_denominador(self) -> None:
        rows = self.results[14:17]
        self.assertEqual([row["metric_id"] for row in rows],
                         ["assigned_percent", "governed_percent", "unallocated_percent"])
        self.assertEqual([row["value"] for row in rows], [70, 90, 10])
        # governed = allocated + shared = 70000 + 20000.
        self.assertEqual([row["numerator"] for row in rows], [70000, 90000, 10000])
        self.assertEqual([row["denominator"] for row in rows], [100000, 100000, 100000])
        for row in rows:
            self.assertEqual(row["unit"], "porcentaje")

    def test_recuentos_de_oportunidades_van_en_el_comportamiento(self) -> None:
        rows = self.results[17:20]
        self.assertEqual([(row["metric_id"], row["behavior"], row["value"], row["unit"]) for row in rows],
                         [("opportunities", "estimated", 1, "recuento"),
                          ("opportunities", "candidate", 1, "recuento"),
                          ("opportunities", "not_evaluable", 0, "recuento")])
        for row in rows:
            self.assertEqual(row["status"], "measured")
            self.assertIsNone(row["count"])

    def test_ahorro_potencial_y_su_porcentaje_sin_redondear(self) -> None:
        potential, percent = self.results[20:22]
        self.assertEqual(potential, make_row("savings", "potential_savings", "eur_minor_2", value=14000))
        self.assertEqual(percent["value"], 14.000000000000002)
        # El flotante del informe se copia tal cual: redondearlo a 14 perdería la huella de la división.
        self.assertEqual(repr(percent["value"]), "14.000000000000002")
        self.assertEqual((percent["numerator"], percent["denominator"]), (14000, 100000))

    def test_ahorro_realizado_es_no_medido(self) -> None:
        # Es la fila que dice «beneficio realizado no medido»: nunca un 0.
        realized = self.results[22]
        self.assertEqual(realized, no_data("savings", "realized_savings", "eur_minor_2"))
        self.assertEqual(realized["status"], "not_measured")
        for key in ("value", "numerator", "denominator", "count"):
            self.assertIsNone(realized[key])

    def test_los_valores_conservan_el_tipo_del_informe(self) -> None:
        # 40 y 70 llegan como enteros del JSON y 14.000000000000002 como float: no se convierten.
        self.assertIs(type(self.results[7]["value"]), int)
        self.assertIs(type(self.results[14]["value"]), int)
        self.assertIs(type(self.results[21]["value"]), float)
        for index in (4, 5, 6, 8, 13, 20):
            self.assertIs(type(self.results[index]["value"]), int)

    def test_valores_leidos_del_informe_de_nuevo_desde_el_cli(self) -> None:
        # Se compara con la salida del CLI parseada de nuevo, no con el objeto ya cargado en el módulo.
        raw = json.loads(CLI_STDOUT)
        _, results = adapt(raw)
        time, allocation, savings = raw["time"], raw["allocation"], raw["savings"]
        self.assertEqual([row["count"] for row in results[:4]],
                         [time["results"][key] for key in ("pass", "fail", "blocked", "not_run")])
        self.assertEqual([row["value"] for row in results[4:8]],
                         [time["manual_ms"], time["assisted_ms"], time["saved_ms"], time["saved_percent"]])
        self.assertEqual([row["value"] for row in results[8:17]],
                         [allocation["allocated"], allocation["shared"], allocation["unallocated"],
                          allocation["excluded"], allocation["total_minor"], allocation["eligible_minor"],
                          allocation["assigned_percent"], allocation["governed_percent"],
                          allocation["unallocated_percent"]])
        self.assertEqual([row["value"] for row in results[17:22]],
                         [savings["estimated_count"], savings["candidate_count"], savings["not_evaluable_count"],
                          savings["potential_minor"], savings["potential_percent"]])


class NotMeasuredTest(unittest.TestCase):
    """Lo no medido es None con `not_measured` y conserva el denominador donde el contrato lo indica."""

    def test_sin_parejas_elegibles_los_tiempos_no_estan_medidos(self) -> None:
        # Ninguna pareja `pass`: manual y asistido son sumas de nada (0 que no es una medición) y el ahorro es
        # null. Las cuatro filas de estados siguen siendo mediciones (hubo 3 intentos, todos `fail`).
        report = variant(lambda r: r["time"].update(
            results={"pass": 0, "fail": 3, "blocked": 0, "not_run": 0}, eligible_pairs=0, manual_ms=0,
            assisted_ms=0, saved_ms=None, saved_percent=None))
        _, results = adapt(report)
        self.assertEqual(results, expected_with(
            trials_pass=make_row("time", "time_trials", "parejas", "pass", count=0, denominator=3),
            trials_fail=make_row("time", "time_trials", "parejas", "fail", count=3, denominator=3),
            manual=no_data("time", "manual_time", "ms", denominator=0),
            assisted=no_data("time", "assisted_time", "ms", denominator=0),
            saved=no_data("time", "time_saved", "ms", denominator=0),
            saved_pct=no_data("time", "time_saved_percent", "porcentaje", denominator=0),
        ))
        for index in (4, 5, 6, 7):
            for key in ("value", "numerator", "count"):
                self.assertIsNone(results[index][key])

    def test_manual_y_asistido_cero_con_parejas_elegibles_son_mediciones(self) -> None:
        # Contraste con el caso anterior: con 2 parejas elegibles un 0 es un valor medido, no «sin datos»; lo
        # que decide es `eligible_pairs`, no que la suma sea cero.
        report = with_time(manual_ms=0, assisted_ms=0, saved_ms=0, saved_percent=None)
        _, results = adapt(report)
        self.assertEqual(results[4], make_row("time", "manual_time", "ms", value=0, denominator=2))
        self.assertEqual(results[5], make_row("time", "assisted_time", "ms", value=0, denominator=2))
        self.assertEqual(results[6], make_row("time", "time_saved", "ms", value=0, denominator=2))
        # Con manual 0 el informe deja el porcentaje en null: no medido, conservando el denominador 0.
        self.assertEqual(results[7], no_data("time", "time_saved_percent", "porcentaje", denominator=0))

    def test_tiempo_asistido_cero_es_medicion(self) -> None:
        _, results = adapt(with_time(assisted_ms=0, saved_ms=900000, saved_percent=100))
        self.assertEqual(results[5], make_row("time", "assisted_time", "ms", value=0, denominator=2))
        self.assertIs(results[5]["status"] == "measured", True)

    def test_ahorro_de_tiempo_cero_es_medido(self) -> None:
        # Manual y asistido iguales: ahorro 0 y 0 % son mediciones reales («no hubo mejora»), no huecos.
        report = with_time(manual_ms=500000, assisted_ms=500000, saved_ms=0, saved_percent=0)
        _, results = adapt(report)
        self.assertEqual(results, expected_with(
            manual=make_row("time", "manual_time", "ms", value=500000, denominator=2),
            assisted=make_row("time", "assisted_time", "ms", value=500000, denominator=2),
            saved=make_row("time", "time_saved", "ms", value=0, denominator=2),
            saved_pct=make_row("time", "time_saved_percent", "porcentaje", value=0, numerator=0,
                               denominator=500000),
        ))
        self.assertEqual(results[6]["status"], "measured")
        self.assertEqual(results[7]["status"], "measured")

    def test_saved_ms_none_con_parejas_es_no_medido_con_su_porcentaje_sin_numerador(self) -> None:
        # Informe coherente con ahorro nulo: tanto el ahorro como su porcentaje son null. Manual y asistido
        # siguen medidos (hay parejas elegibles); el porcentaje conserva el denominador manual.
        _, results = adapt(with_time(saved_ms=None, saved_percent=None))
        self.assertEqual(results, expected_with(
            saved=no_data("time", "time_saved", "ms", denominator=2),
            saved_pct=no_data("time", "time_saved_percent", "porcentaje", denominator=900000)))

    def test_saved_percent_none_es_no_medido_con_el_denominador_manual(self) -> None:
        _, results = adapt(with_time(saved_percent=None))
        self.assertEqual(results, expected_with(
            saved_pct=no_data("time", "time_saved_percent", "porcentaje", denominator=900000)))

    def test_sin_gasto_elegible_los_porcentajes_no_estan_medidos(self) -> None:
        # Solo hay gasto excluido: el informe deja los tres porcentajes en null (división por cero) y el
        # ahorro potencial no existe. Los importes en cero SÍ son mediciones.
        report = variant(lambda r: (
            r["allocation"].update(allocated=0, shared=0, unallocated=0, excluded=5000, total_minor=5000,
                                   eligible_minor=0, assigned_percent=None, governed_percent=None,
                                   unallocated_percent=None),
            r["savings"].update(estimated_count=0, potential_minor=None, potential_percent=None)))
        _, results = adapt(report)
        eur = "eur_minor_2"
        self.assertEqual(results, expected_with(
            allocated=make_row("allocation", "allocated", eur, value=0),
            shared=make_row("allocation", "shared", eur, value=0),
            unallocated=make_row("allocation", "unallocated", eur, value=0),
            excluded=make_row("allocation", "excluded", eur, value=5000),
            total=make_row("allocation", "total", eur, value=5000),
            eligible=make_row("allocation", "eligible", eur, value=0),
            assigned_pct=no_data("allocation", "assigned_percent", "porcentaje", denominator=0),
            governed_pct=no_data("allocation", "governed_percent", "porcentaje", denominator=0),
            unallocated_pct=no_data("allocation", "unallocated_percent", "porcentaje", denominator=0),
            estimated=make_row("savings", "opportunities", "recuento", behavior="estimated", value=0),
            potential=no_data("savings", "potential_savings", eur),
            potential_pct=no_data("savings", "potential_savings_percent", "porcentaje", denominator=0),
        ))

    def test_cada_porcentaje_de_asignacion_none_es_no_medido_con_el_denominador_conservado(self) -> None:
        # Con gasto elegible 100000, un porcentaje null se conserva con su denominador pero sin numerador.
        cases = (("assigned_percent", "assigned_pct", "assigned_percent"),
                 ("governed_percent", "governed_pct", "governed_percent"),
                 ("unallocated_percent", "unallocated_pct", "unallocated_percent"))
        for field, label, metric in cases:
            with self.subTest(campo=field):
                _, results = adapt(with_allocation(**{field: None}))
                self.assertEqual(results, expected_with(
                    **{label: no_data("allocation", metric, "porcentaje", denominator=100000)}))

    def test_porcentaje_cero_medido_con_gasto_elegible(self) -> None:
        # 0 % asignado con gasto elegible es una medición: todo el gasto está sin asignar.
        report = with_allocation(allocated=0, shared=0, unallocated=100000, total_minor=105000,
                                 assigned_percent=0.0, governed_percent=0.0, unallocated_percent=100.0)
        _, results = adapt(report)
        self.assertEqual(results[14], make_row("allocation", "assigned_percent", "porcentaje", value=0.0,
                                               numerator=0, denominator=100000))
        self.assertEqual(results[15], make_row("allocation", "governed_percent", "porcentaje", value=0.0,
                                               numerator=0, denominator=100000))
        self.assertEqual(results[16], make_row("allocation", "unallocated_percent", "porcentaje", value=100.0,
                                               numerator=100000, denominator=100000))
        self.assertIs(type(results[14]["value"]), float)
        self.assertEqual(results[14]["status"], "measured")

    def test_importe_excluido_cero_es_medido(self) -> None:
        _, results = adapt(with_allocation(excluded=0, total_minor=100000))
        self.assertEqual(results, expected_with(
            excluded=make_row("allocation", "excluded", "eur_minor_2", value=0),
            total=make_row("allocation", "total", "eur_minor_2", value=100000)))
        self.assertEqual(results[11]["status"], "measured")

    def test_sin_ahorro_estimado_el_potencial_es_no_medido_y_los_recuentos_siguen(self) -> None:
        # potential_minor None (no hay estimaciones): no medido, sin denominador; su porcentaje también,
        # conservando el gasto elegible como denominador. Los recuentos (0 estimadas) siguen medidos.
        report = with_savings(estimated_count=0, potential_minor=None, potential_percent=None)
        _, results = adapt(report)
        self.assertEqual(results, expected_with(
            estimated=make_row("savings", "opportunities", "recuento", behavior="estimated", value=0),
            potential=no_data("savings", "potential_savings", "eur_minor_2"),
            potential_pct=no_data("savings", "potential_savings_percent", "porcentaje", denominator=100000)))

    def test_ahorro_potencial_cero_es_medido(self) -> None:
        # Un ahorro potencial de 0 con estimaciones es una medición («estimado y nulo»), no un hueco.
        _, results = adapt(with_savings(potential_minor=0, potential_percent=0.0))
        self.assertEqual(results[20], make_row("savings", "potential_savings", "eur_minor_2", value=0))
        self.assertEqual(results[21], make_row("savings", "potential_savings_percent", "porcentaje", value=0.0,
                                               numerator=0, denominator=100000))

    def test_ahorro_realizado_con_un_entero_futuro_es_medido(self) -> None:
        # Hoy el informe lo deja siempre en null; si un informe futuro trae un entero, sale medido, con su
        # unidad monetaria y sin numerador ni denominador.
        _, results = adapt(with_savings(realized_minor=5000))
        self.assertEqual(results, expected_with(
            realized=make_row("savings", "realized_savings", "eur_minor_2", value=5000)))

    def test_ahorro_realizado_cero_es_medido(self) -> None:
        _, results = adapt(with_savings(realized_minor=0))
        self.assertEqual(results[22], make_row("savings", "realized_savings", "eur_minor_2", value=0))
        self.assertEqual(results[22]["status"], "measured")

    def test_lo_no_medido_no_contagia_a_las_demas_filas(self) -> None:
        _, results = adapt(with_savings(potential_minor=None, potential_percent=None))
        changed = {LABELS.index("potential"), LABELS.index("potential_pct")}
        expected = real_rows()
        for index, (got, want) in enumerate(zip(results, expected)):
            if index not in changed:
                with self.subTest(fila=LABELS[index]):
                    self.assertEqual(got, want)


class NegativeAndHardeningTest(unittest.TestCase):
    """Valores negativos permitidos y casos que distinguen implementaciones incorrectas pero verosímiles."""

    def test_ahorro_de_tiempo_negativo_es_medido(self) -> None:
        # El asistente tardó más que el trabajo manual: el ahorro negativo es un resultado real y se publica.
        report = with_time(manual_ms=500000, assisted_ms=800000, saved_ms=-300000, saved_percent=-60)
        _, results = adapt(report)
        self.assertEqual(results[6], make_row("time", "time_saved", "ms", value=-300000, denominator=2))
        self.assertEqual(results[7], make_row("time", "time_saved_percent", "porcentaje", value=-60,
                                              numerator=-300000, denominator=500000))
        self.assertEqual(results[6]["status"], "measured")
        self.assertEqual(results[7]["status"], "measured")

    def test_porcentaje_negativo_con_decimales_se_copia_exacto(self) -> None:
        report = with_time(manual_ms=3, assisted_ms=4, saved_ms=-1, saved_percent=-33.33333333333333)
        _, results = adapt(report)
        self.assertEqual(repr(results[7]["value"]), "-33.33333333333333")
        self.assertEqual((results[7]["numerator"], results[7]["denominator"]), (-1, 3))

    def test_moneda_y_escala_forman_la_unidad(self) -> None:
        # usd con 0 decimales: la unidad sigue a la moneda en minúsculas y a la escala del informe.
        report = variant(lambda r: r.update(currency="USD", minor_unit_digits=0))
        _, results = adapt(report)
        money = ("allocated", "shared", "unallocated", "excluded", "total", "eligible", "potential", "realized")
        for label in money:
            with self.subTest(fila=label):
                self.assertEqual(results[LABELS.index(label)]["unit"], "usd_minor_0")
        self.assertEqual(results, [dict(row, unit="usd_minor_0") if LABELS[i] in money else row
                                   for i, row in enumerate(real_rows())])

    def test_escala_de_tres_decimales(self) -> None:
        _, results = adapt(variant(lambda r: r.update(currency="JPY", minor_unit_digits=3)))
        self.assertEqual(results[8]["unit"], "jpy_minor_3")
        self.assertEqual(results[22]["unit"], "jpy_minor_3")

    def test_los_porcentajes_y_recuentos_no_llevan_unidad_monetaria(self) -> None:
        _, results = adapt(variant(lambda r: r.update(currency="USD", minor_unit_digits=0)))
        for label, unit in (("saved_pct", "porcentaje"), ("assigned_pct", "porcentaje"),
                            ("governed_pct", "porcentaje"), ("unallocated_pct", "porcentaje"),
                            ("potential_pct", "porcentaje"), ("estimated", "recuento"), ("manual", "ms"),
                            ("trials_pass", "parejas")):
            with self.subTest(fila=label):
                self.assertEqual(results[LABELS.index(label)]["unit"], unit)

    def test_governed_suma_allocated_y_shared_con_valores_asimetricos(self) -> None:
        # allocated 11 y shared 22 distintos entre sí y de unallocated 35: un governed = solo shared (22),
        # solo allocated (11) o allocated + unallocated (46) daría otro numerador que 33.
        report = with_allocation(allocated=11, shared=22, unallocated=35, excluded=44, total_minor=112,
                                 eligible_minor=68, assigned_percent=17.5, governed_percent=50.5,
                                 unallocated_percent=33.25)
        _, results = adapt(report)
        self.assertEqual(results[14], make_row("allocation", "assigned_percent", "porcentaje", value=17.5,
                                               numerator=11, denominator=68))
        self.assertEqual(results[15], make_row("allocation", "governed_percent", "porcentaje", value=50.5,
                                               numerator=33, denominator=68))
        self.assertEqual(results[16], make_row("allocation", "unallocated_percent", "porcentaje", value=33.25,
                                               numerator=35, denominator=68))

    def test_informe_con_todos_los_valores_distintos_no_cruza_denominadores_ni_numeradores(self) -> None:
        # Cada dato lleva un número propio: cualquier cruce entre campos (pass/eligible_pairs, manual/total,
        # eligible/total, potential/eligible) cambia una fila y la delata.
        report = variant(lambda r: (
            r["time"].update(results={"pass": 5, "fail": 2, "blocked": 1, "not_run": 7}, eligible_pairs=5,
                             manual_ms=1000, assisted_ms=400, saved_ms=600, saved_percent=60),
            r["allocation"].update(allocated=11, shared=22, unallocated=35, excluded=44, total_minor=112,
                                   eligible_minor=68, assigned_percent=17.5, governed_percent=50.5,
                                   unallocated_percent=33.25),
            r["savings"].update(estimated_count=3, candidate_count=4, not_evaluable_count=6, potential_minor=8,
                                potential_percent=12.5, realized_minor=None)))
        _, results = adapt(report)
        eur = "eur_minor_2"
        self.assertEqual(results, [
            make_row("time", "time_trials", "parejas", "pass", count=5, denominator=15),
            make_row("time", "time_trials", "parejas", "fail", count=2, denominator=15),
            make_row("time", "time_trials", "parejas", "blocked", count=1, denominator=15),
            make_row("time", "time_trials", "parejas", "not_run", count=7, denominator=15),
            make_row("time", "manual_time", "ms", value=1000, denominator=5),
            make_row("time", "assisted_time", "ms", value=400, denominator=5),
            make_row("time", "time_saved", "ms", value=600, denominator=5),
            make_row("time", "time_saved_percent", "porcentaje", value=60, numerator=600, denominator=1000),
            make_row("allocation", "allocated", eur, value=11),
            make_row("allocation", "shared", eur, value=22),
            make_row("allocation", "unallocated", eur, value=35),
            make_row("allocation", "excluded", eur, value=44),
            make_row("allocation", "total", eur, value=112),
            make_row("allocation", "eligible", eur, value=68),
            make_row("allocation", "assigned_percent", "porcentaje", value=17.5, numerator=11, denominator=68),
            make_row("allocation", "governed_percent", "porcentaje", value=50.5, numerator=33, denominator=68),
            make_row("allocation", "unallocated_percent", "porcentaje", value=33.25, numerator=35,
                     denominator=68),
            make_row("savings", "opportunities", "recuento", behavior="estimated", value=3),
            make_row("savings", "opportunities", "recuento", behavior="candidate", value=4),
            make_row("savings", "opportunities", "recuento", behavior="not_evaluable", value=6),
            make_row("savings", "potential_savings", eur, value=8),
            make_row("savings", "potential_savings_percent", "porcentaje", value=12.5, numerator=8,
                     denominator=68),
            no_data("savings", "realized_savings", eur),
        ])

    def test_estados_de_parejas_todo_cero_conserva_denominador_cero(self) -> None:
        # Sin intentos registrados: los cuatro recuentos son 0 medidos sobre 0 intentos (el estado de una fila
        # de recuento es el nombre del caso, no «medido»).
        report = variant(lambda r: r["time"].update(
            results={"pass": 0, "fail": 0, "blocked": 0, "not_run": 0}, eligible_pairs=0, manual_ms=0,
            assisted_ms=0, saved_ms=None, saved_percent=None))
        _, results = adapt(report)
        for index, status in enumerate(("pass", "fail", "blocked", "not_run")):
            with self.subTest(estado=status):
                self.assertEqual(results[index],
                                 make_row("time", "time_trials", "parejas", status, count=0, denominator=0))

    def test_los_cuatro_estados_no_se_intercambian(self) -> None:
        _, results = adapt(with_results(**{"pass": 4, "fail": 3, "blocked": 2, "not_run": 1}))
        self.assertEqual([(row["status"], row["count"], row["denominator"]) for row in results[:4]],
                         [("pass", 4, 10), ("fail", 3, 10), ("blocked", 2, 10), ("not_run", 1, 10)])

    def test_recuentos_de_oportunidades_no_se_intercambian(self) -> None:
        _, results = adapt(with_savings(estimated_count=7, candidate_count=8, not_evaluable_count=9))
        self.assertEqual([(row["behavior"], row["value"]) for row in results[17:20]],
                         [("estimated", 7), ("candidate", 8), ("not_evaluable", 9)])

    def test_importes_con_cinco_valores_distintos_no_se_cruzan(self) -> None:
        _, results = adapt(with_allocation(allocated=1, shared=2, unallocated=3, excluded=4, total_minor=5,
                                           eligible_minor=6))
        self.assertEqual([(row["metric_id"], row["value"]) for row in results[8:14]],
                         [("allocated", 1), ("shared", 2), ("unallocated", 3), ("excluded", 4), ("total", 5),
                          ("eligible", 6)])

    def test_importes_grandes_se_copian_exactos(self) -> None:
        big = 2 ** 53 - 1
        _, results = adapt(with_allocation(allocated=big))
        self.assertEqual(results[8]["value"], big)
        self.assertIs(type(results[8]["value"]), int)

    def test_fila_de_ahorro_potencial_usa_eligible_como_denominador_del_porcentaje(self) -> None:
        # El denominador del porcentaje de ahorro es el gasto elegible, no el total ni el ahorro.
        _, results = adapt(with_allocation(eligible_minor=777, total_minor=888))
        self.assertEqual((results[21]["numerator"], results[21]["denominator"]), (14000, 777))
        self.assertEqual(results[13]["value"], 777)
        self.assertEqual(results[12]["value"], 888)


class ErrorsTest(unittest.TestCase):
    """AdapterError con «<campo>: <problema>»; el mensaje EMPIEZA por el campo."""

    def assert_error(self, report, field: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        # Formato del contrato: el mensaje empieza por el campo exacto y un separador, no solo lo contiene.
        self.assertTrue(message.startswith(f"{field}: "), message)

    def test_error_es_value_error(self) -> None:
        with self.assertRaises(ValueError):
            adapt([])

    def test_report_no_es_objeto(self) -> None:
        for bad in ([], None, "informe", 3, [REPORT]):
            with self.subTest(bad=repr(bad)[:20]):
                self.assert_error(bad, "report")

    # --- Cabecera ---

    def test_schema_version_distinta_de_1(self) -> None:
        # Solo el entero 1 vale: True (que es 1 en Python), 1.0, "1" o None se rechazan.
        for bad in (2, 0, -1, True, "1", None, 1.0):
            with self.subTest(version=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(schema_version=bad)), "schema_version")

    def test_schema_version_ausente(self) -> None:
        self.assert_error(drop_path(REPORT, ("schema_version",)), "schema_version")

    def test_jup_distinto_de_jup_068(self) -> None:
        for bad in ("JUP-070", "jup-068", "JUP-068 ", None, 68, ""):
            with self.subTest(jup=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(jup=bad)), "jup")

    def test_jup_ausente(self) -> None:
        self.assert_error(drop_path(REPORT, ("jup",)), "jup")

    def test_provenance_no_valida(self) -> None:
        for bad in ("real", "Synthetic", "MEASURED", "", None, True, ["synthetic"], 1):
            with self.subTest(provenance=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(provenance=bad)), "provenance")

    def test_provenance_ausente(self) -> None:
        self.assert_error(drop_path(REPORT, ("provenance",)), "provenance")

    def test_cadenas_de_cabecera_no_validas(self) -> None:
        for field in TOP_STRING_FIELDS:
            for bad in ("", 5, 1.5, None, True, ["x"], {}):
                with self.subTest(campo=field, bad=repr(bad)):
                    self.assert_error(set_path(REPORT, (field,), bad), field)
            with self.subTest(campo=field, ausente=True):
                self.assert_error(drop_path(REPORT, (field,)), field)

    def test_currency_no_valida(self) -> None:
        # `^[A-Z]{3}$` completo: dos o cuatro letras, minúsculas, dígitos, espacios o un salto de línea final
        # (que un `$` de Python aceptaría) se rechazan.
        for bad in ("eu", "eur", "EURO", "EU", "", "EU1", " EUR", "EUR ", "EUR\n", "ÉUR", None, 5, True,
                    ["EUR"]):
            with self.subTest(currency=repr(bad)):
                self.assert_error(set_path(REPORT, ("currency",), bad), "currency")

    def test_currency_ausente(self) -> None:
        self.assert_error(drop_path(REPORT, ("currency",)), "currency")

    def test_currency_de_tres_letras_mayusculas_es_valida(self) -> None:
        for good in ("EUR", "USD", "JPY", "AAA", "ZZZ"):
            with self.subTest(currency=good):
                _, results = adapt(set_path(REPORT, ("currency",), good))
                self.assertEqual(results[8]["unit"], f"{good.lower()}_minor_2")

    def test_minor_unit_digits_no_valido(self) -> None:
        for bad in (-1, True, False, 2.0, 2.5, "2", None, [2]):
            with self.subTest(digits=repr(bad)):
                self.assert_error(set_path(REPORT, ("minor_unit_digits",), bad), "minor_unit_digits")
        self.assert_error(drop_path(REPORT, ("minor_unit_digits",)), "minor_unit_digits")

    def test_minor_unit_digits_cero_es_valido(self) -> None:
        _, results = adapt(set_path(REPORT, ("minor_unit_digits",), 0))
        self.assertEqual(results[8]["unit"], "eur_minor_0")

    # --- Bloques ---

    def test_bloques_que_no_son_objeto_o_faltan(self) -> None:
        for path in (("time",), ("time", "results"), ("allocation",), ("savings",)):
            for bad in (None, [], "x", 5, True):
                with self.subTest(campo=dotted(path), bad=repr(bad)):
                    self.assert_error(set_path(REPORT, path, bad), dotted(path))
            with self.subTest(campo=dotted(path), ausente=True):
                self.assert_error(drop_path(REPORT, path), dotted(path))

    def test_recuentos_e_importes_no_validos(self) -> None:
        # Enteros >= 0 estrictos: bool, float (incluso 1.0), cadenas, negativos, None y NaN fuera.
        for path in COUNT_PATHS:
            for bad in (True, False, 1.0, 2.5, "1", -1, None, [1], {}, float("nan")):
                with self.subTest(campo=dotted(path), bad=repr(bad)):
                    self.assert_error(set_path(REPORT, path, bad), dotted(path))

    def test_recuentos_e_importes_ausentes(self) -> None:
        for path in COUNT_PATHS + NULLABLE_INT_PATHS + NULLABLE_NUMBER_PATHS:
            with self.subTest(campo=dotted(path)):
                self.assert_error(drop_path(REPORT, path), dotted(path))

    def test_recuentos_e_importes_cero_son_validos(self) -> None:
        report = REPORT
        for path in COUNT_PATHS:
            report = set_path(report, path, 0)
        self.assertEqual(len(adapt(report)[1]), 23)

    def test_enteros_anulables_no_validos(self) -> None:
        for path in NULLABLE_INT_PATHS:
            for bad in (True, False, 1.0, 2.5, "1", [1], {}, float("nan"), float("inf")):
                with self.subTest(campo=dotted(path), bad=repr(bad)):
                    self.assert_error(set_path(REPORT, path, bad), dotted(path))

    def test_saved_ms_negativo_y_none_son_validos(self) -> None:
        for good in (-1, -999999, 0, None):
            with self.subTest(saved_ms=good):
                self.assertEqual(len(adapt(with_time(saved_ms=good))[1]), 23)

    def test_enteros_anulables_none_son_validos(self) -> None:
        for path in NULLABLE_INT_PATHS:
            with self.subTest(campo=dotted(path)):
                self.assertEqual(len(adapt(set_path(REPORT, path, None))[1]), 23)

    def test_porcentajes_no_validos(self) -> None:
        for path in NULLABLE_NUMBER_PATHS:
            for bad in (True, False, "40", [], {}, float("nan"), float("inf"), float("-inf")):
                with self.subTest(campo=dotted(path), bad=repr(bad)):
                    self.assert_error(set_path(REPORT, path, bad), dotted(path))

    def test_porcentajes_negativos_enteros_y_none_son_validos(self) -> None:
        for path in NULLABLE_NUMBER_PATHS:
            for good in (-12.5, -3, 0, 0.0, 100, 250.5, None):
                with self.subTest(campo=dotted(path), valor=good):
                    self.assertEqual(len(adapt(set_path(REPORT, path, good))[1]), 23)

    def test_se_informa_del_primer_campo_defectuoso_en_orden_de_contrato(self) -> None:
        # Dos defectos a la vez: el primero que el contrato valida (cabecera antes que los bloques) manda.
        report = variant(lambda r: (r.update(jup="JUP-070"), r["time"].update(manual_ms=-1)))
        self.assert_error(report, "jup")

    def test_error_no_devuelve_resultado_parcial(self) -> None:
        with self.assertRaises(tool.AdapterError):
            adapt(with_savings(realized_minor="mal"))


class PurityTest(unittest.TestCase):
    """La función no muta la entrada, es determinista y tolera lo que no usa."""

    def test_no_muta_el_informe(self) -> None:
        candidate = copy.deepcopy(REPORT)
        adapt(candidate)
        self.assertEqual(candidate, REPORT)

    def test_no_muta_el_informe_con_no_medidos(self) -> None:
        report = with_savings(potential_minor=None, potential_percent=None, estimated_count=0)
        before = copy.deepcopy(report)
        adapt(report)
        self.assertEqual(report, before)

    def test_dos_llamadas_dan_lo_mismo_y_son_independientes(self) -> None:
        first = adapt(REPORT)
        second = adapt(REPORT)
        self.assertEqual(first, second)
        # Mutar una salida no altera la otra ni una llamada posterior.
        first[1][0]["count"] = 999
        first[0]["run_id"] = "mutado"
        third = adapt(REPORT)
        self.assertEqual(third[1][0]["count"], 2)
        self.assertEqual(third[0]["run_id"], RUN_ID)

    def test_la_salida_no_comparte_estructuras_con_la_entrada(self) -> None:
        report = copy.deepcopy(REPORT)
        input_ids = {id(item) for item in containers(report)}
        run, results = adapt(report)
        for item in list(containers(run)) + list(containers(results)):
            self.assertNotIn(id(item), input_ids)
        for row in results:
            row["value"] = -1
            row["behavior"] = "mutada"
        run["source"] = "mutada"
        self.assertEqual(report, REPORT)

    def test_las_filas_son_dicts_distintos(self) -> None:
        _, results = adapt(REPORT)
        self.assertEqual(len({id(row) for row in results}), len(results))

    def test_claves_desconocidas_y_listas_se_ignoran(self) -> None:
        # Texto libre, periodo, listas de parejas y estimaciones y campos futuros no se usan ni se copian: la
        # salida es idéntica a la del informe sin ellos.
        def extend(report: dict) -> None:
            report["scope"] = MARKER
            report["configuration"] = MARKER
            report["reviewer"] = MARKER
            report["evidence"] = [MARKER, "otra evidencia con espacios"]
            report["period"] = {"start": MARKER, "end": MARKER}
            report["cost_basis"] = MARKER
            report["run_id"] = MARKER
            report["extra_futuro"] = {"anidado": [1, 2, {"x": MARKER}]}
            report["time"]["pairs"] = [{"id": MARKER, "saved_ms": 1, "saved_percent": 1, "evidence": [MARKER]}]
            report["time"]["extra"] = MARKER
            report["time"]["results"]["extra"] = 99
            report["allocation"]["extra"] = MARKER
            report["savings"]["estimates"] = [{"id": MARKER, "resource_id": MARKER, "savings_minor": 1,
                                               "evidence": [MARKER]}]
            report["savings"]["extra"] = MARKER

        self.assertEqual(adapt(variant(extend)), adapt(REPORT))

    def test_sin_claves_opcionales_no_cambia_nada(self) -> None:
        # El adaptador solo exige los campos de su contrato: lo demás puede faltar sin efecto.
        def strip(report: dict) -> None:
            for key in ("run_id", "scope", "period", "cost_basis", "configuration", "reviewer", "evidence"):
                report.pop(key)
            report["time"].pop("pairs")
            report["savings"].pop("estimates")

        self.assertEqual(adapt(variant(strip)), adapt(REPORT))

    def test_las_listas_de_parejas_y_estimaciones_no_cambian_las_filas(self) -> None:
        # Vacías o con muchas entradas: las filas salen de los agregados, no de las listas.
        def change(report: dict) -> None:
            report["time"]["pairs"] = []
            report["savings"]["estimates"] = [{"id": f"e{i}"} for i in range(50)]

        self.assertEqual(adapt(variant(change)), adapt(REPORT))


class NoFreeTextTest(unittest.TestCase):
    """Ninguna cadena de la salida es texto libre, una ruta ni una fecha."""

    def assert_identifiers(self, run: dict, results: list[dict]) -> None:
        for text in list(string_values(run)) + list(string_values(results)):
            with self.subTest(text=text[:40]):
                self.assertLessEqual(len(text), 80)
                self.assertNotIn(" ", text)
                self.assertTrue(tool.IDENTIFIER_RE.match(text), text)

    def test_informe_real_solo_lleva_identificadores(self) -> None:
        run, results = adapt(REPORT)
        self.assert_identifiers(run, results)

    def test_conjunto_exacto_de_cadenas_de_la_salida(self) -> None:
        # Lista cerrada: cualquier cadena nueva (un campo copiado de más) rompe esta igualdad.
        run, results = adapt(REPORT)
        self.assertEqual(set(string_values(run)), {
            RUN_ID, "JUP-068", REAL_COMMIT, REAL_DATASET_VERSION, REAL_INPUT_SHA256,
        })
        self.assertEqual(set(string_values(results)), {
            "B", "time", "allocation", "savings", "time_trials", "manual_time", "assisted_time", "time_saved",
            "time_saved_percent", "allocated", "shared", "unallocated", "excluded", "total", "eligible",
            "assigned_percent", "governed_percent", "unallocated_percent", "opportunities", "potential_savings",
            "potential_savings_percent", "realized_savings", "all", "estimated", "candidate", "not_evaluable",
            "pass", "fail", "blocked", "not_run", "measured", "not_measured", "parejas", "ms", "porcentaje",
            "recuento", "eur_minor_2",
        })

    def test_texto_libre_inyectado_no_aparece_en_la_salida(self) -> None:
        def inject(report: dict) -> None:
            report["scope"] = MARKER
            report["configuration"] = MARKER
            report["reviewer"] = MARKER
            report["evidence"] = [MARKER]
            report["period"] = {"start": MARKER, "end": MARKER}
            report["time"]["pairs"] = [{"id": f"{MARKER} 1"}, {"id": f"{MARKER} 2"}]
            report["savings"]["estimates"] = [{"id": MARKER, "resource_id": MARKER}]

        run, results = adapt(variant(inject))
        dumped = json.dumps([run, results], ensure_ascii=False)
        self.assertNotIn("Texto libre", dumped)
        self.assertNotIn(MARKER, dumped)
        self.assert_identifiers(run, results)

    def test_moneda_en_minusculas_en_la_unidad_cumple_el_patron_de_identificador(self) -> None:
        run, results = adapt(variant(lambda r: r.update(currency="USD", minor_unit_digits=0)))
        self.assert_identifiers(run, results)

    def test_ninguna_ruta_ni_fecha_del_informe_aparece_en_la_salida(self) -> None:
        run, results = adapt(REPORT)
        dumped = json.dumps([run, results], ensure_ascii=False)
        for forbidden in ("docs/", ".md", ".json", "2026-09", "subscription-demo", "synthetic:", "vm-demo"):
            with self.subTest(texto=forbidden):
                self.assertNotIn(forbidden, dumped)


class ReadBusinessReportTest(unittest.TestCase):
    """`read_business_report`: ejecuta el generador de Node y convierte cualquier fallo en AdapterError."""

    PREFIX = "business-metrics: "

    def assert_error(self, path) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            tool.read_business_report(path)
        message = str(caught.exception)
        self.assertTrue(message.startswith(self.PREFIX), message)
        self.assertIn(Path(path).name, message)
        return message

    def completed(self, returncode=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(["node"], returncode, stdout=stdout, stderr=stderr)

    # --- Con Node de verdad ---

    def test_con_el_ejemplo_real_devuelve_la_salida_del_cli(self) -> None:
        result = tool.read_business_report(EXAMPLE_PATH)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, json.loads(CLI_STDOUT))
        self.assertEqual(result, REPORT)

    def test_acepta_la_ruta_como_cadena(self) -> None:
        self.assertEqual(tool.read_business_report(str(EXAMPLE_PATH)), REPORT)

    def test_la_salida_se_puede_adaptar_de_extremo_a_extremo(self) -> None:
        run, results = adapt(tool.read_business_report(EXAMPLE_PATH))
        self.assertEqual(run, expected_run())
        self.assertEqual(results, real_rows())

    def test_fichero_inexistente(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "no-existe-jup068.json"
            message = self.assert_error(path)
            # Se incluye el motivo que da el generador (primera línea de su stderr).
            expected = run_node(path).stderr.splitlines()[0]
            self.assertIn(expected, message)

    def test_json_invalido(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roto-jup068.json"
            path.write_text("{esto no es json", encoding="utf-8")
            message = self.assert_error(path)
            self.assertIn(run_node(path).stderr.splitlines()[0], message)

    def test_registro_que_el_validador_de_node_rechaza(self) -> None:
        # schema_version 2: el generador termina con código 1 y su mensaje; el adaptador lo propaga.
        record = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        record["schema_version"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "version-2-jup068.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            completed = run_node(path)
            self.assertNotEqual(completed.returncode, 0)
            message = self.assert_error(path)
            self.assertIn(completed.stderr.splitlines()[0], message)

    # --- Fronteras simuladas (proceso, tiempo, formato de la salida) ---

    def test_invoca_node_con_el_generador_la_orden_report_y_la_ruta(self) -> None:
        with mock.patch.object(tool.subprocess, "run", return_value=self.completed(0, "{}")) as run:
            tool.read_business_report("informe-x.json")
        run.assert_called_once()
        args, kwargs = run.call_args
        command = args[0] if args else kwargs["args"]
        self.assertEqual(command[0], "node")
        self.assertEqual(Path(command[1]), CLI_PATH)
        self.assertEqual(command[2:], ["report", "informe-x.json"])
        self.assertIs(kwargs["capture_output"], True)
        self.assertIs(kwargs["text"], True)
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["timeout"], 60)
        self.assertEqual(Path(kwargs["cwd"]), ROOT)

    def test_devuelve_el_json_del_stdout_y_no_de_stderr(self) -> None:
        stdout = json.dumps({"schema_version": 1, "dato": [1, 2]}, indent=2)
        with mock.patch.object(tool.subprocess, "run",
                               return_value=self.completed(0, stdout, "aviso {\"otro\": 1}")):
            self.assertEqual(tool.read_business_report("x.json"), {"schema_version": 1, "dato": [1, 2]})

    def test_salida_distinta_de_cero_es_error_con_la_primera_linea_de_stderr(self) -> None:
        stderr = "línea uno del error\nlínea dos del error\n"
        with mock.patch.object(tool.subprocess, "run", return_value=self.completed(1, "", stderr)):
            message = self.assert_error("informe-roto.json")
        self.assertIn("línea uno del error", message)

    def test_salida_distinta_de_cero_es_error_aunque_el_stdout_sea_json_valido(self) -> None:
        # Un código de salida de fallo manda sobre cualquier stdout que parezca un informe.
        for code in (1, 2, 127, -9):
            with self.subTest(codigo=code):
                with mock.patch.object(tool.subprocess, "run", return_value=self.completed(code, "{}", "fallo")):
                    self.assert_error("informe.json")

    def test_salida_distinta_de_cero_sin_stderr_sigue_siendo_error(self) -> None:
        with mock.patch.object(tool.subprocess, "run", return_value=self.completed(2, "", "")):
            self.assert_error("informe.json")

    def test_node_ausente(self) -> None:
        with mock.patch.object(tool.subprocess, "run", side_effect=FileNotFoundError("node")):
            self.assert_error("informe.json")

    def test_otros_fallos_del_sistema_operativo(self) -> None:
        with mock.patch.object(tool.subprocess, "run", side_effect=PermissionError("denegado")):
            self.assert_error("informe.json")

    def test_tiempo_agotado(self) -> None:
        with mock.patch.object(tool.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 60)):
            self.assert_error("informe.json")

    def test_stdout_que_no_es_un_objeto_json(self) -> None:
        for stdout in ("", "   \n", "no es json", "{roto", "[]", "[{}]", "null", "3", '"texto"', "true"):
            with self.subTest(stdout=stdout[:12]):
                with mock.patch.object(tool.subprocess, "run", return_value=self.completed(0, stdout)):
                    self.assert_error("informe.json")

    def test_el_error_nombra_el_fichero_con_su_ruta_completa_o_su_nombre(self) -> None:
        with mock.patch.object(tool.subprocess, "run", return_value=self.completed(1, "", "x")):
            message = self.assert_error(Path("carpeta") / "negocio-especial.json")
        self.assertIn("negocio-especial.json", message)


if __name__ == "__main__":
    unittest.main()
