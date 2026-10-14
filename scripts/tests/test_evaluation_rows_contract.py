"""Validación común y adaptador `rows-v1` de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.6, fase Red).

Contrato que se valida (dos funciones):

* `validate_rows(run, results) -> None`: la validación COMÚN del contrato de filas planas
  (`docs/validation/evaluation-dashboard.md`, «Contrato de filas planas rows-v1», reglas 1 a 6). Se aplica a la
  salida de todos los adaptadores y a la entrada `rows-v1`. No devuelve nada, no muta nada y, si algo incumple
  el contrato, lanza `AdapterError` cuyo mensaje EMPIEZA por `"<ruta>: "` con la ruta EXACTA del campo:
  `run.<campo>` para la ejecución (`run.retrieval.<clave>` dentro de `retrieval`), `results[<i>].<campo>` para
  una fila y `results` / `results[<i>]` / `run` para los errores de forma. Motivo (hallazgo M2 del QA de 2.2):
  los adaptadores COPIAN valores sin validar tipo ni alfabeto, así que `rate='alto'`, un grupo llamado
  `¿Cuál es el enunciado?` o un `commit` con espacios llegarían a la base; esta validación es la barrera final.
* `adapt_rows_v1(document, run_id=None) -> (run, results)`: adaptador del formato de entrada de futuros
  informes (JUP-071). Es PURO (no muta ni comparte estructuras), rellena con None lo opcional (`synthetic` y
  `selected` con False), devuelve `run` con exactamente `RUN_KEYS` y filas con exactamente `RESULT_KEYS` en ese
  orden, llama internamente a `validate_rows` y propaga su `AdapterError`.

Decisiones donde la especificación admite más de una lectura (el coder debe respetarlas; están fijadas aquí):

* Una clave desconocida o ausente en `run` o en una fila se informa en la ruta de ESA clave: `run.milestone`,
  `results[1].extra`, `run.commit` (ausente), `results[1].unit` (ausente). Las de nivel superior de `rows-v1`:
  `document.<clave>` para las desconocidas y `contract_version` / `run` / `results` para las ausentes.
* Orden de validación: primero `run` y después `results` en el orden de las filas; dentro de `run` o de una fila,
  primero las CLAVES (desconocidas, luego ausentes), después el tipo de cada campo en el orden de `RUN_KEYS` /
  `RESULT_KEYS` y solo al final la COHERENCIA entre campos; los duplicados se detectan fila a fila (el error
  sale en la segunda fila de la pareja, antes de mirar las siguientes).
* Rutas de coherencia: `count` / `value` / `numerator` / `ci_low` / `ci_high` sobrantes o faltantes según el
  estado se informan en el campo afectado; `0 <= numerator <= denominator` con unidad `tasa` se informa en
  `numerator`; un intervalo con un solo límite se informa en `ci_low` o `ci_high` (cualquiera de los dos);
  un duplicado se informa en `results[<j>]` (la fila entera, sin campo).
* Cuando `adapt_rows_v1` recibe `run_id` en `run` Y como argumento no se fija qué pasa si el `run` del documento
  NO trae `run_id` (la especificación lo marca obligatorio): no se prueba.

Los valores esperados se escriben a mano. Los informes reales son los versionados de JUP-070, JUP-078 y
JUP-022 y la salida REAL de `node tools/business-metrics.mjs report docs/validation/JUP-068-example.json`,
que se ejecuta en `setUpModule` (sin skip). Las variantes se construyen con `copy.deepcopy` para que solo
cambie el dato que se quiere probar, y los índices de fila de las variantes se localizan en la salida del
adaptador (por `metric_id` y `behavior`), nunca con el validador.

Endurecimiento desde el principio (lección de la mutación de 2.1 a 2.5): fronteras (80/81 caracteres, 0/-1,
numerador igual al denominador y denominador + 1, un solo límite de intervalo), bool frente a entero, NaN,
infinito y enteros gigantes (que no deben escapar como `OverflowError`), `"EUR\\n"` con salto de línea final
(se valida con `fullmatch`), un fallo por regla, falsos valores (`0`, `False`, `""`) que un `if value` dejaría
pasar, y pruebas que combinan dos defectos para fijar el orden de validación.

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
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_contract", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EVIDENCE = ROOT / "docs" / "evidence"
JUP_070_RUN_1 = EVIDENCE / "JUP-070-run-1-report.json"
JUP_070_RUN_2 = EVIDENCE / "JUP-070-run-2-report.json"
JUP_078_REPORT = EVIDENCE / "JUP-078-benchmark-results.json"
JUP_022_REPORT = ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json"
JUP_068_EXAMPLE = ROOT / "docs" / "validation" / "JUP-068-example.json"
JUP_068_CLI = ROOT / "tools" / "business-metrics.mjs"

# Claves literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)
RUN_NULLABLE_IDENTIFIERS = (
    "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256", "embedding_provider",
    "embedding_alias", "generation_model", "prompt_sha256",
)
RETRIEVAL_KEYS = ("top_k", "max_distance", "chunk_size", "chunk_overlap")
CASE_STATUSES = ("pass", "fail", "blocked", "not_run")

NAN = float("nan")
INF = float("inf")
HUGE = 10 ** 400  # no cabe en un float: `math.isfinite(HUGE)` lanzaría OverflowError

# Informes reales y salida real de Node; los fija `setUpModule`.
REPORTS: dict = {}


def run_node(path) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(JUP_068_CLI), "report", str(path)], capture_output=True, text=True,
                          encoding="utf-8", timeout=60, cwd=ROOT)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def setUpModule() -> None:
    # Los informes de entrada son los REALES: si un informe o el generador cambian, estas pruebas lo notan.
    completed = run_node(JUP_068_EXAMPLE)
    assert completed.returncode == 0, completed.stderr
    REPORTS["070-1"] = load_json(JUP_070_RUN_1)
    REPORTS["070-2"] = load_json(JUP_070_RUN_2)
    REPORTS["078"] = load_json(JUP_078_REPORT)
    REPORTS["022"] = load_json(JUP_022_REPORT)
    REPORTS["068"] = json.loads(completed.stdout)


# --- Auxiliares de datos ------------------------------------------------------------------------------------

def validate(run, results):
    return tool.validate_rows(run, results)


def adapt_070(report, run_id="id-070"):
    return tool.adapt_jup070(report, run_id)


def adapt_078(report, run_id="id-078"):
    return tool.adapt_jup078(report, run_id)


def adapt_022(report, run_id="id-022"):
    return tool.adapt_jup022(report, run_id)


def adapt_068(report, run_id="id-068"):
    return tool.adapt_jup068(report, run_id)


def good_run(**changes) -> dict:
    """Ejecución mínima válida: solo `run_id`, `source` y `synthetic`; lo demás es None."""
    run = {key: None for key in RUN_KEYS}
    run.update(run_id="robustez-1", source="JUP-071", synthetic=False)
    run.update(changes)
    return run


def full_run(**changes) -> dict:
    """Ejecución con TODOS los campos rellenos y válidos."""
    run = good_run(
        run_at="2026-10-08T20:13:54Z", commit="b12b3c80d0954a1f1a7bd12fae31456f269cff52", suite="JUP-069",
        suite_version="1.0.0", suite_sha256="e1" * 32, corpus_sha256="cf" * 32, embedding_provider="litellm",
        embedding_alias="economicon-embedding",
        retrieval={"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
        generation_model="plantilla-sin-modelo", prompt_sha256="f" * 64, synthetic=True,
    )
    run.update(changes)
    return run


def good_row(**changes) -> dict:
    """Fila de tipo A medida y válida: tasa 9/10 de robustez."""
    row = {key: None for key in RESULT_KEYS}
    row.update(measure_type="A", grp="robustness", metric_id="pass_rate", behavior="missing_field",
               status="measured", value=0.9, unit="tasa", numerator=9, denominator=10,
               judgment="automatic", selected=False)
    row.update(changes)
    return row


def case_row(status: str = "pass", **changes) -> dict:
    """Fila de recuento de casos válida (grupo distinto de `good_row` para no chocar como duplicado)."""
    row = {key: None for key in RESULT_KEYS}
    row.update(measure_type="A", grp="cases", metric_id="cases", behavior="all", status=status, count=3,
               unit="casos", denominator=10, judgment="automatic", selected=False)
    row.update(changes)
    return row


def filler(**changes) -> dict:
    """Fila válida de relleno (índice 0) con otra clave de duplicado que la fila que se prueba."""
    return good_row(grp="filler", **changes)


def reverse_keys(row: dict) -> dict:
    """Mismo contenido con las claves insertadas al revés: el orden de validación no puede ser el del dict."""
    return dict(reversed(list(row.items())))


IDENT_OK = ("a", "0", "a" * 80, "A-1", "JUP-069-024", "top_k=4,max_distance=none", "x@y+z:1/2_3.4", "1.0.0",
            "eur_minor_2", "Z9")
# Todo lo que NO es un identificador: texto libre, frontera de 81 caracteres, el salto de línea final que `$`
# dejaría pasar, inicio no alfanumérico, no ASCII, tipos que no son cadena y falsos valores.
IDENT_BAD = ("", "con espacios", "a" * 81, "¿Cuál es el enunciado?", "EUR\n", "abc\n\n", " abc", "abc ", "-abc",
             ".abc", "_abc", "ñandú", "a\tb", "a#b", "a(b)", 1, 0, 1.5, True, False, ["a"], {"a": 1})


class RowsTestCase(unittest.TestCase):
    """Aserciones comunes: la ruta exacta como prefijo del mensaje y la ausencia de efectos."""

    def assert_rejected(self, run, results, *paths: str) -> None:
        # `AdapterError` (y no cualquier excepción) con el mensaje `<ruta>: <problema>`: el prefijo lleva el
        # `": "` para que `results[1]` no se confunda con `results[10]` ni `run.commit` con `run.commit_x`.
        with self.assertRaises(tool.AdapterError) as caught:
            validate(run, results)
        self.assert_prefix(caught.exception, *paths)

    def assert_prefix(self, error: Exception, *paths: str) -> None:
        message = str(error)
        self.assertTrue(any(message.startswith(f"{path}: ") and len(message) > len(path) + 2 for path in paths),
                        f"el mensaje {message!r} debe empezar por alguna de {paths!r} seguida de ': ' y un motivo")

    def assert_accepted(self, run, results) -> None:
        self.assertIsNone(validate(run, results))


# --- (A) Casos válidos --------------------------------------------------------------------------------------

class ValidRowsAcceptTest(RowsTestCase):
    """Lo que el contrato permite expresamente no se rechaza (la validación no puede ser más estricta)."""

    def test_devuelve_none_con_una_fila_valida(self) -> None:
        self.assertIsNone(validate(good_run(), [good_row()]))

    def test_sin_filas_es_valido(self) -> None:
        # Un informe sin resultados (p. ej. robustez todavía sin datos) es un documento válido.
        self.assert_accepted(good_run(), [])

    def test_ejecucion_con_todos_los_campos(self) -> None:
        self.assert_accepted(full_run(), [good_row()])

    def test_las_claves_pueden_venir_en_cualquier_orden(self) -> None:
        # El orden de las claves lo fija la salida de los adaptadores, no la entrada de la validación.
        self.assert_accepted(reverse_keys(full_run()), [reverse_keys(good_row())])

    def test_retrieval_solo_con_chunk_size_y_chunk_overlap(self) -> None:
        # JUP-022 publica solo el troceado: `top_k` y `max_distance` van por fila y no se exigen las cuatro.
        self.assert_accepted(good_run(retrieval={"chunk_size": 500, "chunk_overlap": 50}), [])

    def test_retrieval_vacio_y_con_valores_nulos(self) -> None:
        self.assert_accepted(good_run(retrieval={}), [])
        self.assert_accepted(good_run(retrieval={"top_k": 4, "max_distance": None}), [])
        self.assert_accepted(good_run(retrieval={key: None for key in RETRIEVAL_KEYS}), [])

    def test_retrieval_admite_enteros_y_flotantes(self) -> None:
        for value in (0, 4, 0.6, 1e300, 10 ** 300, -1.5):
            with self.subTest(value=value):
                self.assert_accepted(good_run(retrieval={"max_distance": value}), [])

    def test_run_at_none_y_formatos_iso(self) -> None:
        for value in (None, "2026-10-08T20:13:54Z", "2026-10-08T20:13:54+00:00", "2026-10-08T20:13:54"):
            with self.subTest(run_at=value):
                self.assert_accepted(good_run(run_at=value), [])

    def test_identificadores_validos_en_cada_campo_de_la_ejecucion(self) -> None:
        # Incluye el límite de 80 caracteres y el alfabeto completo de la regla 3.
        for key in ("run_id", "source") + RUN_NULLABLE_IDENTIFIERS:
            for value in IDENT_OK:
                with self.subTest(field=key, value=value[:30]):
                    self.assert_accepted(good_run(**{key: value}), [])

    def test_identificadores_validos_en_cada_campo_de_la_fila(self) -> None:
        for key in ("grp", "metric_id", "behavior", "unit"):
            for value in IDENT_OK:
                with self.subTest(field=key, value=value[:30]):
                    self.assert_accepted(good_run(), [good_row(**{key: value})])

    def test_numero_negativo_y_cero_son_valores_medidos(self) -> None:
        # Un tiempo ahorrado negativo (el asistente tardó más) es un valor legítimo; el 0 medido también.
        for value in (-5000, -0.25, 0, 0.0, 1e300, 10 ** 300):
            with self.subTest(value=value):
                self.assert_accepted(good_run(), [good_row(unit="ms", value=value, numerator=None,
                                                           denominator=None)])

    def test_numerador_negativo_con_unidad_que_no_es_tasa(self) -> None:
        # `time_saved_percent` tiene como numerador el ahorro, que puede ser negativo.
        self.assert_accepted(good_run(), [good_row(unit="porcentaje", value=-12.5, numerator=-5000,
                                                   denominator=40000)])

    def test_numerador_mayor_que_el_denominador_con_unidad_que_no_es_tasa(self) -> None:
        # La regla 0 <= numerador <= denominador es solo de las tasas: ni `porcentaje` ni `ms` ni `tasas`
        # (la unidad se compara por igualdad exacta con `tasa`).
        for unit in ("porcentaje", "ms", "tasas", "TASA", "eur_minor_2"):
            with self.subTest(unit=unit):
                self.assert_accepted(good_run(), [good_row(unit=unit, numerator=11, denominator=10)])

    def test_denominador_cero(self) -> None:
        # `n` = 0 es un denominador real (lo no medido lo conserva, regla 5) y con tasa 0/0 es coherente.
        self.assert_accepted(good_run(), [good_row(numerator=0, denominator=0)])
        self.assert_accepted(good_run(), [good_row(status="not_measured", value=None, numerator=None,
                                                   denominator=0)])

    def test_frontera_de_la_tasa(self) -> None:
        # Tabla (numerador, denominador, válida): igual al denominador sí; denominador + 1 no; 0 sí; -1 no.
        table = (
            (0, 10, True), (10, 10, True), (5, 10, True), (0.5, 1, True), (0, 0, True),
            (11, 10, False), (-1, 10, False), (1, 0, False), (1.0000001, 1, False), (-0.5, 10, False),
        )
        for numerator, denominator, ok in table:
            with self.subTest(numerator=numerator, denominator=denominator):
                results = [filler(), good_row(numerator=numerator, denominator=denominator)]
                if ok:
                    self.assert_accepted(good_run(), results)
                else:
                    self.assert_rejected(good_run(), results, "results[1].numerator")

    def test_tasa_sin_numerador_o_sin_denominador_no_se_compara(self) -> None:
        # El numerador es exacto solo a veces (regla 5): sin uno de los dos no hay nada que comparar.
        self.assert_accepted(good_run(), [good_row(numerator=None, denominator=10)])
        self.assert_accepted(good_run(), [good_row(numerator=50, denominator=None)])
        self.assert_accepted(good_run(), [good_row(numerator=None, denominator=None)])

    def test_recuentos_de_casos_en_cada_estado(self) -> None:
        for status in CASE_STATUSES:
            with self.subTest(status=status):
                self.assert_accepted(good_run(), [case_row(status), filler()])

    def test_recuento_cero_es_un_recuento(self) -> None:
        for status in CASE_STATUSES:
            with self.subTest(status=status):
                self.assert_accepted(good_run(), [case_row(status, count=0)])

    def test_medido_con_intervalo_y_no_medido_con_denominador(self) -> None:
        self.assert_accepted(good_run(), [good_row(ci_low=0.5, ci_high=0.98)])
        self.assert_accepted(good_run(), [good_row(ci_low=0, ci_high=0)])
        self.assert_accepted(good_run(), [good_row(status="not_measured", value=None, numerator=None,
                                                   denominator=7)])

    def test_tipo_b_con_juicio_none_y_tipo_a_con_ambos_juicios(self) -> None:
        self.assert_accepted(good_run(), [good_row(measure_type="B", judgment=None)])
        for judgment in ("automatic", "human"):
            with self.subTest(judgment=judgment):
                self.assert_accepted(good_run(), [good_row(judgment=judgment)])

    def test_seleccionada_true(self) -> None:
        self.assert_accepted(good_run(), [good_row(selected=True)])

    def test_estados_de_valor_y_de_caso_con_cualquier_clave_distinta(self) -> None:
        # Mismo `grp`, `metric_id` y `behavior` con estados distintos NO son duplicados.
        self.assert_accepted(good_run(), [good_row(), good_row(status="not_measured", value=None, numerator=None)])
        self.assert_accepted(good_run(), [case_row(status) for status in CASE_STATUSES])

    def test_no_muta_lo_que_valida(self) -> None:
        run, results = full_run(), [good_row(), case_row("fail"), good_row(grp="otro", ci_low=0.1, ci_high=0.9)]
        before = copy.deepcopy((run, results))
        validate(run, results)
        self.assertEqual((run, results), before)

    def test_no_muta_cuando_rechaza(self) -> None:
        run, results = good_run(retrieval={"top_k": 4}), [good_row(), good_row(behavior="¿Cuál es el enunciado?")]
        before = copy.deepcopy((run, results))
        self.assert_rejected(run, results, "results[1].behavior")
        self.assertEqual((run, results), before)


# --- (A) Errores en la ejecución ----------------------------------------------------------------------------

class RunErrorsTest(RowsTestCase):
    """Cada regla de `run` rechaza con la ruta exacta del campo."""

    def test_run_no_es_un_objeto(self) -> None:
        for value in (None, [], "run", 1, True, (), [("run_id", "a")]):
            with self.subTest(run=value):
                self.assert_rejected(value, [], "run")

    def test_clave_desconocida_en_run(self) -> None:
        # `milestone` lo fija el manifiesto, no el informe: tampoco es una clave de la ejecución.
        for key in ("milestone", "extra", "Run_id", "retrieval_x", "notes"):
            with self.subTest(key=key):
                run = good_run()
                run[key] = "x"
                self.assert_rejected(run, [], f"run.{key}")

    def test_clave_ausente_en_run(self) -> None:
        for key in RUN_KEYS:
            with self.subTest(key=key):
                run = good_run()
                del run[key]
                self.assert_rejected(run, [], f"run.{key}")

    def test_identificadores_obligatorios_invalidos(self) -> None:
        for key in ("run_id", "source"):
            for value in IDENT_BAD + (None,):
                with self.subTest(field=key, value=repr(value)[:30]):
                    self.assert_rejected(good_run(**{key: value}), [], f"run.{key}")

    def test_identificadores_opcionales_invalidos(self) -> None:
        # None es «no registrado» y vale; cualquier otra cosa tiene que ser un identificador.
        for key in RUN_NULLABLE_IDENTIFIERS:
            for value in IDENT_BAD:
                with self.subTest(field=key, value=repr(value)[:30]):
                    self.assert_rejected(good_run(**{key: value}), [], f"run.{key}")

    def test_run_at_invalido(self) -> None:
        for value in ("ayer", "", "2026-13-45T00:00:00Z", 20261008, 1.5, True, False, 0, ["2026-10-08"]):
            with self.subTest(run_at=value):
                self.assert_rejected(good_run(run_at=value), [], "run.run_at")

    def test_retrieval_no_es_un_objeto(self) -> None:
        for value in ([], "top_k=4", 4, True, False, 0, [("top_k", 4)]):
            with self.subTest(retrieval=value):
                self.assert_rejected(good_run(retrieval=value), [], "run.retrieval")

    def test_clave_desconocida_en_retrieval(self) -> None:
        for key in ("notes", "k", "TOP_K", "milestone"):
            with self.subTest(key=key):
                self.assert_rejected(good_run(retrieval={"top_k": 4, key: 1}), [], f"run.retrieval.{key}")

    def test_valor_invalido_en_cada_clave_de_retrieval(self) -> None:
        # bool no es número (True == 1), una cadena tampoco, NaN e infinito no son mediciones y un entero que
        # no cabe en float no debe escapar como OverflowError.
        for key in RETRIEVAL_KEYS:
            for value in (True, False, "4", "alto", NAN, INF, -INF, HUGE, -HUGE, [4], {"n": 4}):
                with self.subTest(key=key, value=repr(value)[:20]):
                    self.assert_rejected(good_run(retrieval={key: value}), [], f"run.retrieval.{key}")

    def test_synthetic_exige_un_booleano(self) -> None:
        for value in (1, 0, "true", "false", None, 1.0, []):
            with self.subTest(synthetic=value):
                self.assert_rejected(good_run(synthetic=value), [], "run.synthetic")

    def test_results_no_se_valida_si_run_ya_fallo(self) -> None:
        # La forma de `results` es problema de `results`, pero `run` va primero.
        self.assert_rejected(good_run(commit="a b"), None, "run.commit")


# --- (A) Errores en las filas -------------------------------------------------------------------------------

def mutated_rows(field: str, value, base: dict | None = None) -> list[dict]:
    """`[relleno, fila con el campo cambiado]`: el defecto está en `results[1]` para vigilar el índice."""
    row = dict(base if base is not None else good_row())
    row[field] = value
    return [filler(), row]


class ResultsShapeTest(RowsTestCase):
    def test_results_no_es_una_lista(self) -> None:
        for value in (None, {}, "filas", 1, (), (good_row(),), {"0": good_row()}):
            with self.subTest(results=repr(value)[:30]):
                self.assert_rejected(good_run(), value, "results")

    def test_fila_que_no_es_un_objeto(self) -> None:
        for value in (None, [], "fila", 1, True, ()):
            with self.subTest(row=value):
                self.assert_rejected(good_run(), [filler(), value], "results[1]")

    def test_clave_desconocida_en_una_fila(self) -> None:
        for key in ("extra", "question", "answer", "notes", "Value"):
            with self.subTest(key=key):
                row = good_row()
                row[key] = "texto"
                self.assert_rejected(good_run(), [filler(), row], f"results[1].{key}")

    def test_clave_ausente_en_una_fila(self) -> None:
        for key in RESULT_KEYS:
            with self.subTest(key=key):
                row = good_row()
                del row[key]
                self.assert_rejected(good_run(), [filler(), row], f"results[1].{key}")

    def test_el_indice_de_la_fila_es_el_de_la_lista(self) -> None:
        # Con doce filas, el defecto de la última se informa como `results[11]`, no como `results[1]`.
        rows = [good_row(behavior=f"b{i}") for i in range(11)] + [good_row(behavior="b 11")]
        self.assert_rejected(good_run(), rows, "results[11].behavior")


class RowFieldErrorsTest(RowsTestCase):
    """Un fallo por regla de tipo o alfabeto de cada campo de la fila."""

    def check(self, field: str, values, base: dict | None = None) -> None:
        for value in values:
            with self.subTest(field=field, value=repr(value)[:25]):
                self.assert_rejected(good_run(), mutated_rows(field, value, base), f"results[1].{field}")

    def test_measure_type(self) -> None:
        self.check("measure_type", ("C", "a", "b", "", "AB", "A ", None, ["A"], 1, True))

    def test_identificadores_de_la_fila(self) -> None:
        # `unit` es obligatoria: None se rechaza (a diferencia de los campos opcionales de `run`).
        for field in ("grp", "metric_id", "behavior", "unit"):
            self.check(field, IDENT_BAD + (None,))

    def test_status(self) -> None:
        self.check("status", ("ok", "PASS", "Measured", "", "measured ", "not-measured", None, ["pass"], 1, True))

    def test_count(self) -> None:
        # En una fila de casos: negativo, bool (False == 0), flotante (incluso 3.0), cadena y NaN.
        self.check("count", (-1, True, False, 3.0, 2.5, "3", NAN, INF, [3]), case_row())

    def test_denominator(self) -> None:
        self.check("denominator", (-1, True, False, 10.0, 2.5, "10", NAN, INF, [10]))

    def test_value(self) -> None:
        self.check("value", (True, False, "0.5", "alto", NAN, INF, -INF, HUGE, -HUGE, [0.5], {}))

    def test_numerator(self) -> None:
        self.check("numerator", (True, False, "9", NAN, INF, -INF, HUGE, [9]))

    def test_intervalo(self) -> None:
        # Un límite inválido con el otro válido: el defecto es del límite, no de la pareja.
        for value in (True, False, "0.5", "alto", NAN, INF, -INF, HUGE, [0.5]):
            with self.subTest(limit="ci_low", value=repr(value)[:20]):
                row = good_row(ci_low=value, ci_high=0.9)
                self.assert_rejected(good_run(), [filler(), row], "results[1].ci_low")
            with self.subTest(limit="ci_high", value=repr(value)[:20]):
                row = good_row(ci_low=0.1, ci_high=value)
                self.assert_rejected(good_run(), [filler(), row], "results[1].ci_high")

    def test_juicio_del_tipo_a(self) -> None:
        # El tipo A es automatic o human: None, otra palabra, mayúsculas, vacío o un falso valor no valen.
        self.check("judgment", (None, "manual", "Automatic", "HUMAN", "", " human", True, False, 0, ["human"]))

    def test_juicio_del_tipo_b(self) -> None:
        # El tipo B no tiene juicio: null. Un `human`, un `automatic`, una cadena vacía o un falso valor no valen.
        base = good_row(measure_type="B", judgment=None)
        self.check("judgment", ("automatic", "human", "", "none", False, 0, True), base)

    def test_selected(self) -> None:
        self.check("selected", (1, 0, None, "true", "false", "", 1.0, [True]))


# --- (A) Coherencia entre campos ----------------------------------------------------------------------------

class CoherenceTest(RowsTestCase):
    def rejected_row(self, row: dict, *paths: str) -> None:
        # La fila defectuosa va en `results[1]`; la de relleno (índice 0) es válida.
        self.assert_rejected(good_run(), [filler(), row], *[f"results[1].{path}" for path in paths])

    def test_estado_de_caso_sin_recuento(self) -> None:
        for status in CASE_STATUSES:
            with self.subTest(status=status):
                self.rejected_row(case_row(status, count=None), "count")

    def test_estado_de_caso_con_valor_o_numerador(self) -> None:
        # 0 y 0.0 NO son None: un `if row["value"]` los dejaría pasar y publicaría un cero como si se hubiera medido.
        for status in CASE_STATUSES:
            for value in (0.5, 0, 0.0, 3):
                with self.subTest(status=status, field="value", value=value):
                    self.rejected_row(case_row(status, value=value), "value")
                with self.subTest(status=status, field="numerator", value=value):
                    self.rejected_row(case_row(status, numerator=value), "numerator")

    def test_no_medido_con_valor_numerador_o_recuento(self) -> None:
        base = good_row(status="not_measured", value=None, numerator=None, count=None, denominator=7)
        for field in ("value", "numerator", "count"):
            for value in (0, 0.0, 1, 0.5):
                with self.subTest(field=field, value=value):
                    self.rejected_row({**base, field: value}, field)

    def test_no_medido_con_intervalo(self) -> None:
        base = good_row(status="not_measured", value=None, numerator=None, count=None, denominator=7)
        # Ambos límites: el primer sobrante en el orden del contrato es `ci_low`.
        self.rejected_row({**base, "ci_low": 0.1, "ci_high": 0.9}, "ci_low", "ci_high")
        self.rejected_row({**base, "ci_low": 0, "ci_high": 0}, "ci_low", "ci_high")
        # Con un solo límite el defecto es el límite sobrante o la pareja incompleta; ambas rutas son del intervalo.
        self.rejected_row({**base, "ci_low": 0.1}, "ci_low", "ci_high")
        self.rejected_row({**base, "ci_high": 0.9}, "ci_low", "ci_high")

    def test_no_medido_conserva_el_denominador(self) -> None:
        # Regla 5: el denominador de lo no medido es válido (también 0 y grande); no es un campo prohibido.
        for denominator in (0, 7, 10 ** 12, None):
            with self.subTest(denominator=denominator):
                row = good_row(status="not_measured", value=None, numerator=None, denominator=denominator)
                self.assert_accepted(good_run(), [row])

    def test_medido_sin_valor(self) -> None:
        self.rejected_row(good_row(value=None), "value")

    def test_medido_con_recuento(self) -> None:
        # count=0 es un recuento (no None): una fila `measured` no lleva `count`.
        for count in (0, 3):
            with self.subTest(count=count):
                self.rejected_row(good_row(count=count), "count")

    def test_intervalo_con_un_solo_limite(self) -> None:
        for low, high in ((0.1, None), (None, 0.9), (0, None), (None, 0)):
            with self.subTest(ci_low=low, ci_high=high):
                self.rejected_row(good_row(ci_low=low, ci_high=high), "ci_low", "ci_high")

    def test_tasa_fuera_de_rango(self) -> None:
        self.rejected_row(good_row(numerator=11, denominator=10), "numerator")
        self.rejected_row(good_row(numerator=-1, denominator=10), "numerator")
        self.rejected_row(good_row(numerator=1, denominator=0), "numerator")

    def test_tasa_en_una_fila_no_medida_no_aplica(self) -> None:
        # Sin numerador (lo no medido lo tiene a None) no hay comparación posible.
        self.assert_accepted(good_run(), [good_row(status="not_measured", value=None, numerator=None,
                                                   denominator=0)])


# --- (A) Duplicados -----------------------------------------------------------------------------------------

class DuplicatesTest(RowsTestCase):
    def test_misma_clave_en_dos_filas(self) -> None:
        # Mismos grp, metric_id, behavior y status, aunque cambien los valores: la base no admite duplicados.
        self.assert_rejected(good_run(), [good_row(), good_row(value=0.5, numerator=5)], "results[1]")

    def test_el_error_sale_en_la_segunda_fila_y_no_en_la_primera(self) -> None:
        self.assert_rejected(good_run(), [filler(), good_row(), good_row(value=0.1, numerator=1)], "results[2]")

    def test_duplicado_no_contiguo(self) -> None:
        rows = [good_row(), filler(), filler(behavior="otro"), good_row()]
        self.assert_rejected(good_run(), rows, "results[3]")

    def test_duplicado_de_recuento_de_casos(self) -> None:
        self.assert_rejected(good_run(), [case_row("fail"), case_row("pass"), case_row("fail", count=0)],
                             "results[2]")

    def test_el_tipo_de_medida_no_forma_parte_de_la_clave(self) -> None:
        # La clave es (grp, metric_id, behavior, status): una fila A y una B con la misma clave chocan.
        self.assert_rejected(good_run(), [good_row(), good_row(measure_type="B", judgment=None)], "results[1]")

    def test_cada_componente_de_la_clave_distingue_filas(self) -> None:
        # Cambiar UNO solo de los cuatro componentes deja de ser duplicado.
        for field, value in (("grp", "otro"), ("metric_id", "otra"), ("behavior", "otro"),
                             ("status", "not_measured")):
            with self.subTest(field=field):
                other = good_row(**{field: value})
                if field == "status":
                    other.update(value=None, numerator=None)
                self.assert_accepted(good_run(), [good_row(), other])

    def test_clave_con_prefijo_comun_no_es_duplicado(self) -> None:
        # `a` + `bc` frente a `ab` + `c`: la clave son cuatro componentes, no una concatenación.
        self.assert_accepted(good_run(), [good_row(grp="a", metric_id="bc"), good_row(grp="ab", metric_id="c")])


# --- (A) Orden de validación --------------------------------------------------------------------------------

BAD_RUN_VALUE = {
    "run_id": "a b", "source": "a b", "run_at": "ayer", "commit": "a b", "suite": "a b", "suite_version": "a b",
    "suite_sha256": "a b", "corpus_sha256": "a b", "embedding_provider": "a b", "embedding_alias": "a b",
    "retrieval": [], "generation_model": "a b", "prompt_sha256": "a b", "synthetic": 1,
}
# Cada valor incumple SU propia regla de tipo con independencia de los demás campos de una fila de tipo A medida.
BAD_ROW_VALUE = {
    "measure_type": "C", "grp": "a b", "metric_id": "a b", "behavior": "a b", "status": "x", "count": -1,
    "value": NAN, "unit": "a b", "numerator": True, "denominator": -1, "ci_low": "x", "ci_high": "x",
    "judgment": "manual", "selected": 1,
}


class ValidationOrderTest(RowsTestCase):
    """Fija QUÉ error se informa cuando hay dos defectos a la vez."""

    def test_run_antes_que_results(self) -> None:
        self.assert_rejected(good_run(commit="a b"), [good_row(behavior="a b")], "run.commit")
        self.assert_rejected(good_run(commit="a b"), None, "run.commit")

    def test_filas_en_el_orden_de_la_lista(self) -> None:
        rows = [good_row(behavior="x1"), good_row(behavior="a b"), good_row(behavior="x3", selected=1)]
        self.assert_rejected(good_run(), rows, "results[1].behavior")
        self.assert_rejected(good_run(), [rows[0], rows[2], rows[1]], "results[1].selected")

    def test_primero_la_forma_de_results_y_despues_nada_mas(self) -> None:
        # Una fila que no es objeto se informa antes que las filas siguientes con defectos.
        self.assert_rejected(good_run(), [good_row(), "fila", good_row(behavior="a b")], "results[1]")

    def test_claves_de_run_antes_que_los_valores(self) -> None:
        run = good_run(run_id="a b")
        run["milestone"] = False
        self.assert_rejected(run, [], "run.milestone")
        run = good_run(run_id="a b")
        del run["synthetic"]
        self.assert_rejected(run, [], "run.synthetic")

    def test_claves_de_la_fila_antes_que_los_valores(self) -> None:
        row = good_row(measure_type="C")
        row["extra"] = "x"
        self.assert_rejected(good_run(), [row], "results[0].extra")
        row = good_row(measure_type="C")
        del row["selected"]
        self.assert_rejected(good_run(), [row], "results[0].selected")

    def test_campos_de_run_en_el_orden_de_run_keys(self) -> None:
        # Dos campos inválidos a la vez; el dict se inserta AL REVÉS para que el orden sea el del contrato y
        # no el de iteración del dict.
        for first, second in zip(RUN_KEYS, RUN_KEYS[1:]):
            with self.subTest(first=first, second=second):
                run = good_run()
                run[first], run[second] = BAD_RUN_VALUE[first], BAD_RUN_VALUE[second]
                self.assert_rejected(reverse_keys(run), [], f"run.{first}")

    def test_campos_de_la_fila_en_el_orden_de_result_keys(self) -> None:
        for first, second in zip(RESULT_KEYS, RESULT_KEYS[1:]):
            with self.subTest(first=first, second=second):
                row = good_row()
                row[first], row[second] = BAD_ROW_VALUE[first], BAD_ROW_VALUE[second]
                self.assert_rejected(good_run(), [reverse_keys(row)], f"results[0].{first}")

    def test_los_tipos_se_validan_antes_que_la_coherencia(self) -> None:
        # `count` falta en un `pass` (coherencia, campo 6.º) y `selected` es 1 (tipo, último campo): gana el tipo.
        self.assert_rejected(good_run(), [case_row("pass", count=None, selected=1)], "results[0].selected")
        # Un `measured` con `count` (coherencia, campo `count`) y `denominator` -1 (tipo): gana el tipo.
        self.assert_rejected(good_run(), [good_row(count=3, denominator=-1)], "results[0].denominator")

    def test_duplicado_antes_de_validar_las_filas_siguientes(self) -> None:
        # El duplicado de la fila 1 se informa antes que el defecto de la fila 2.
        rows = [good_row(), good_row(), good_row(behavior="a b")]
        self.assert_rejected(good_run(), rows, "results[1]")

    def test_el_defecto_de_una_fila_anterior_gana_al_duplicado_posterior(self) -> None:
        rows = [good_row(), good_row(behavior="a b"), good_row()]
        self.assert_rejected(good_run(), rows, "results[1].behavior")


# --- (A) Salida de los cuatro adaptadores -------------------------------------------------------------------

def index_of(results: list[dict], metric_id: str, behavior: str | None = None) -> int:
    """Posición de la primera fila de la métrica en la SALIDA del adaptador (nunca se consulta al validador)."""
    return next(i for i, row in enumerate(results)
                if row["metric_id"] == metric_id and (behavior is None or row["behavior"] == behavior))


def variant(report: dict, mutate) -> dict:
    """Copia profunda del informe real con una modificación; el informe real nunca se toca."""
    copy_ = copy.deepcopy(report)
    mutate(copy_)
    return copy_


class AdapterOutputsAreValidTest(RowsTestCase):
    """La validación común acepta lo que producen los adaptadores con los informes REALES."""

    def check(self, adapter, report, expected_rows: int) -> None:
        run, results = adapter(report)
        self.assertEqual(len(results), expected_rows)  # guarda: una salida vacía haría trivial la validación
        self.assert_accepted(run, results)

    def test_jup070_run_1(self) -> None:
        self.check(adapt_070, REPORTS["070-1"], 48)

    def test_jup070_run_2(self) -> None:
        self.check(adapt_070, REPORTS["070-2"], 48)

    def test_jup078(self) -> None:
        self.check(adapt_078, REPORTS["078"], 10)

    def test_jup022(self) -> None:
        self.check(adapt_022, REPORTS["022"], 140)

    def test_jup068(self) -> None:
        self.check(adapt_068, REPORTS["068"], 23)

    def test_jup070_con_proporcion_completa_k_igual_a_n(self) -> None:
        # Frontera de la tasa vista desde un adaptador real: k == n es válida (numerador == denominador).
        report = variant(REPORTS["070-2"], lambda r: r["metrics"]["ACC-1"].update(k=20, n=20, rate=1.0))
        run, results = adapt_070(report)
        self.assert_accepted(run, results)

    def test_jup068_tiempo_ahorrado_negativo(self) -> None:
        # El generador puede informar un ahorro negativo (el asistente tardó más): valor y numerador negativos
        # con unidad `ms` y `porcentaje`, que no son tasas.
        def mutate(report: dict) -> None:
            report["time"]["saved_ms"] = -5000
            report["time"]["saved_percent"] = -12.5

        run, results = adapt_068(variant(REPORTS["068"], mutate))
        self.assertLess(results[index_of(results, "time_saved")]["value"], 0)
        self.assert_accepted(run, results)

    def test_jup078_alias_de_80_caracteres(self) -> None:
        report = variant(REPORTS["078"], lambda r: r["models"][0].update(alias="m" * 80))
        run, results = adapt_078(report)
        self.assert_accepted(run, results)

    def test_jup078_varios_modelos_sin_duplicados(self) -> None:
        def mutate(report: dict) -> None:
            third = copy.deepcopy(report["models"][0])
            third["alias"] = "tercer-modelo"
            report["models"].append(third)

        run, results = adapt_078(variant(REPORTS["078"], mutate))
        self.assertEqual(len(results), 15)
        self.assert_accepted(run, results)


class AdapterFreeTextIsRejectedTest(RowsTestCase):
    """Texto libre o valores sin sentido que los adaptadores COPIAN: la validación común los detiene.

    Primero se comprueba que el adaptador DEVUELVE algo (los copia) y después que `validate_rows` lo rechaza con
    la ruta de la fila o del campo de `run`. Los casos que el adaptador ya rechaza por sí mismo (alias de JUP-078
    con espacios, `commit` de JUP-068 con espacios, `minor_unit_digits` negativo...) no se repiten aquí.
    """

    def assert_output_rejected(self, adapter, report, path) -> None:
        run, results = adapter(report)
        # `path` puede ser una cadena o una función de la salida (para localizar la fila por contenido).
        expected = path(results) if callable(path) else path
        paths = expected if isinstance(expected, tuple) else (expected,)
        self.assert_rejected(run, results, *paths)

    # --- JUP-070: campos de `run`

    def test_jup070_campos_de_run_con_texto_libre(self) -> None:
        cases = (
            ("commit", lambda r: r["run"].update(commit="texto libre con espacios"), "run.commit"),
            ("commit-81", lambda r: r["run"].update(commit="c" * 81), "run.commit"),
            ("commit-salto", lambda r: r["run"].update(commit="abc\n"), "run.commit"),
            ("provider", lambda r: r["run"].update(provider="con espacios"), "run.embedding_provider"),
            ("alias", lambda r: r["run"].update(alias="con espacios"), "run.embedding_alias"),
            ("suite_version", lambda r: r["run"].update(suite_version="con espacios"), "run.suite_version"),
            ("suite_sha256", lambda r: r["run"].update(suite_sha256="con espacios"), "run.suite_sha256"),
            ("corpus", lambda r: r["run"]["corpus"].update(sha256="con espacios"), "run.corpus_sha256"),
            ("model_alias", lambda r: r["run"]["generation"].update(model_alias="con espacios"),
             "run.generation_model"),
        )
        for name, mutate, path in cases:
            with self.subTest(case=name):
                self.assert_output_rejected(adapt_070, variant(REPORTS["070-2"], mutate), path)

    def test_jup070_retrieval_con_valores_o_claves_invalidos(self) -> None:
        cases = (
            ("top_k-texto", lambda r: r["run"]["retrieval"].update(top_k="alto"), "run.retrieval.top_k"),
            ("max_distance-bool", lambda r: r["run"]["retrieval"].update(max_distance=True),
             "run.retrieval.max_distance"),
            ("chunk_size-nan", lambda r: r["run"]["retrieval"].update(chunk_size=NAN), "run.retrieval.chunk_size"),
            ("clave-extra", lambda r: r["run"]["retrieval"].update(nota="texto"), "run.retrieval.nota"),
        )
        for name, mutate, path in cases:
            with self.subTest(case=name):
                self.assert_output_rejected(adapt_070, variant(REPORTS["070-2"], mutate), path)

    # --- JUP-070: filas

    def test_jup070_grupo_con_el_texto_de_una_pregunta(self) -> None:
        # Un nombre de grupo es el `behavior` de la fila: aquí cabría un enunciado de pregunta.
        name = "¿Cuál es el enunciado?"

        def mutate(report: dict) -> None:
            groups = report["metrics"]["ACC-3"]["groups"]
            groups[name] = copy.deepcopy(groups["clarify"])

        run, results = adapt_070(variant(REPORTS["070-2"], mutate))
        index = index_of(results, "ACC-3", name)
        self.assert_rejected(run, results, f"results[{index}].behavior")

    def test_jup070_nombres_de_grupo_etapa_caso_y_categoria_invalidos(self) -> None:
        # Cada sitio por el que un nombre del informe acaba en `behavior`, con espacios y con 81 caracteres.
        def acc3(name):
            return lambda r: r["metrics"]["ACC-3"]["groups"].update({name: dict(r["metrics"]["ACC-3"]["groups"]["clarify"])})

        def rel3(name):
            return lambda r: r["metrics"]["REL-3"]["groups"].update({name: dict(next(iter(r["metrics"]["REL-3"]["groups"].values())))})

        def grd2(name):
            return lambda r: r["metrics"]["GRD-2"]["by_case"].update({name: 2})

        def lat1(name):
            return lambda r: r["metrics"]["LAT-1"]["stages"].update({name: {"n": 3, "value": 5}})

        def str2(name):
            return lambda r: r["metrics"]["STR-2"]["by_category"].update({name: 1})

        for name in ("texto con espacios", "g" * 81, "caso\n"):
            for metric_id, build in (("ACC-3", acc3), ("REL-3", rel3), ("GRD-2", grd2), ("LAT-1", lat1),
                                     ("STR-2", str2)):
                with self.subTest(metric=metric_id, name=name[:20]):
                    run, results = adapt_070(variant(REPORTS["070-2"], build(name)))
                    index = index_of(results, metric_id, name)
                    self.assert_rejected(run, results, f"results[{index}].behavior")

    def test_jup070_nombre_de_80_caracteres_es_valido(self) -> None:
        # La frontera exacta del alfabeto vista desde un informe real.
        name = "g" * 80
        report = variant(REPORTS["070-2"], lambda r: r["metrics"]["GRD-2"]["by_case"].update({name: 2}))
        run, results = adapt_070(report)
        self.assertEqual(results[index_of(results, "GRD-2", name)]["behavior"], name)
        self.assert_accepted(run, results)

    def test_jup070_tasa_que_no_es_un_numero(self) -> None:
        def mutate(report: dict) -> None:
            report["metrics"]["ACC-1"]["rate"] = "alto"

        run, results = adapt_070(variant(REPORTS["070-2"], mutate))
        self.assert_rejected(run, results, f"results[{index_of(results, 'ACC-1')}].value")

    def test_jup070_k_mayor_que_n_y_k_negativo(self) -> None:
        # El adaptador solo exige enteros: una tasa con k > n o k < 0 llegaría a la base.
        for name, fields, field in (("k>n", {"k": 9, "n": 3}, "numerator"),
                                    ("k<0", {"k": -1}, "numerator"),
                                    ("n<0", {"n": -1}, "denominator"),
                                    ("n=k-1", {"k": 5, "n": 4}, "numerator")):
            with self.subTest(case=name):
                run, results = adapt_070(variant(REPORTS["070-2"], lambda r: r["metrics"]["ACC-1"].update(fields)))
                self.assert_rejected(run, results, f"results[{index_of(results, 'ACC-1')}].{field}")

    def test_jup070_intervalo_invalido(self) -> None:
        for name, ci, paths in (("texto", ["a", "b"], ("ci_low",)), ("un-limite", [0.1, None], ("ci_low", "ci_high")),
                                ("bool", [True, 0.5], ("ci_low",)), ("nan", [0.0, NAN], ("ci_high",))):
            with self.subTest(case=name):
                run, results = adapt_070(variant(REPORTS["070-2"], lambda r: r["metrics"]["ACC-1"].update(ci95=ci)))
                index = index_of(results, "ACC-1")
                self.assert_rejected(run, results, *[f"results[{index}].{path}" for path in paths])

    def test_jup070_valores_de_latencia_y_similitud_invalidos(self) -> None:
        def latency(report: dict) -> None:
            report["metrics"]["LAT-1"]["stages"]["generation"]["value"] = "rapido"

        def similarity(report: dict) -> None:
            report["metrics"]["REL-4"]["median"] = "alto"

        run, results = adapt_070(variant(REPORTS["070-2"], latency))
        self.assert_rejected(run, results, f"results[{index_of(results, 'LAT-1', 'generation')}].value")
        run, results = adapt_070(variant(REPORTS["070-2"], similarity))
        self.assert_rejected(run, results, f"results[{index_of(results, 'REL-4', 'median')}].value")

    def test_jup070_entero_gigante_no_escapa_como_overflow(self) -> None:
        # `json.loads` produce enteros de precisión arbitraria; `math.isfinite(10**400)` lanza OverflowError.
        # La validación debe convertirlo en `AdapterError`, no dejar escapar la excepción cruda.
        def total(report: dict) -> None:
            report["metrics"]["GRD-2"]["total"] = HUGE

        def rate(report: dict) -> None:
            report["metrics"]["ACC-1"]["rate"] = HUGE

        run, results = adapt_070(variant(REPORTS["070-2"], total))
        self.assert_rejected(run, results, f"results[{index_of(results, 'GRD-2', 'all')}].value")
        run, results = adapt_070(variant(REPORTS["070-2"], rate))
        self.assert_rejected(run, results, f"results[{index_of(results, 'ACC-1')}].value")

    # --- JUP-022

    def test_jup022_top_k_enorme_hace_un_behavior_de_mas_de_80_caracteres(self) -> None:
        # `behavior` es `top_k=<K>,max_distance=<D>`: con un `top_k` de 100 cifras supera el límite de la regla 3.
        report = variant(REPORTS["022"], lambda r: r["points"][0].update(top_k=10 ** 100))
        run, results = adapt_022(report)
        self.assertGreater(len(results[0]["behavior"]), 80)
        self.assert_rejected(run, results, "results[0].behavior")

    def test_jup022_troceado_gigante_no_escapa_como_overflow(self) -> None:
        report = variant(REPORTS["022"], lambda r: r["chunking"].update(size=HUGE))
        run, results = adapt_022(report)
        self.assert_rejected(run, results, "run.retrieval.chunk_size")
        report = variant(REPORTS["022"], lambda r: r["chunking"].update(overlap=HUGE))
        run, results = adapt_022(report)
        self.assert_rejected(run, results, "run.retrieval.chunk_overlap")

    # --- JUP-068

    def test_jup068_escala_de_moneda_enorme_hace_una_unidad_de_mas_de_80_caracteres(self) -> None:
        # La unidad de los importes es `eur_minor_<dígitos>`: con 81 dígitos supera el límite de la regla 3.
        run, results = adapt_068(variant(REPORTS["068"], lambda r: r.update(minor_unit_digits=10 ** 80)))
        index = index_of(results, "allocated")
        self.assertGreater(len(results[index]["unit"]), 80)
        self.assert_rejected(run, results, f"results[{index}].unit")

    def test_jup068_entero_gigante_no_escapa_como_overflow(self) -> None:
        run, results = adapt_068(variant(REPORTS["068"], lambda r: r["time"].update(saved_ms=HUGE)))
        self.assert_rejected(run, results, f"results[{index_of(results, 'time_saved')}].value")
        run, results = adapt_068(variant(REPORTS["068"], lambda r: r["savings"].update(potential_minor=HUGE)))
        self.assert_rejected(run, results, f"results[{index_of(results, 'potential_savings')}].value")


# --- (B) Adaptador rows-v1 ----------------------------------------------------------------------------------

def adapt_rows(document, *args, **kwargs):
    return tool.adapt_rows_v1(document, *args, **kwargs)


def robustness_input(**changes) -> dict:
    """Fila de entrada de ejemplo (informe de robustez de JUP-071) con solo las claves que declara el informe."""
    row = {
        "measure_type": "A", "grp": "robustness", "metric_id": "pass_rate", "behavior": "missing_field",
        "status": "measured", "value": 0.9, "numerator": 9, "denominator": 10, "unit": "tasa",
        "judgment": "automatic",
    }
    row.update(changes)
    return row


def document(run: dict | None = None, results: list | None = None, **top) -> dict:
    doc = {
        "contract_version": 1,
        "run": run if run is not None else {"run_id": "robustez-1", "source": "JUP-071"},
        "results": results if results is not None else [robustness_input()],
    }
    doc.update(top)
    return doc


def without(mapping: dict, key: str) -> dict:
    copy_ = dict(mapping)
    del copy_[key]
    return copy_


class RowsV1ExamplesTest(RowsTestCase):
    def test_documento_de_robustez_de_ejemplo(self) -> None:
        run, results = adapt_rows(document())
        # `run` completo: solo run_id, source y synthetic (False por defecto) llevan valor.
        self.assertEqual(run, good_run())
        self.assertEqual(list(run), list(RUN_KEYS))
        # La fila: lo no indicado es None y `selected` False.
        self.assertEqual(results, [good_row()])
        self.assertEqual(list(results[0]), list(RESULT_KEYS))

    def test_devuelve_una_tupla_valida_para_el_validador(self) -> None:
        out = adapt_rows(document())
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 2)
        self.assert_accepted(*out)

    def test_solo_run_id_y_source_con_results_vacio(self) -> None:
        run, results = adapt_rows(document(results=[]))
        self.assertEqual(run, good_run())
        self.assertEqual(results, [])
        self.assertIsInstance(results, list)

    def test_run_con_todos_los_campos_opcionales(self) -> None:
        expected = full_run()
        run, results = adapt_rows(document(run=copy.deepcopy(expected)))
        self.assertEqual(run, expected)
        self.assertEqual(list(run), list(RUN_KEYS))
        self.assertEqual(results, [good_row()])

    def test_cada_campo_opcional_de_run_ausente_es_none_y_synthetic_false(self) -> None:
        full = full_run()
        for key in RUN_KEYS[2:]:
            with self.subTest(missing=key):
                run, _ = adapt_rows(document(run=without(full, key)))
                self.assertEqual(run, {**full, key: False if key == "synthetic" else None})

    def test_synthetic_true_se_conserva(self) -> None:
        run, _ = adapt_rows(document(run={"run_id": "a", "source": "b", "synthetic": True}))
        self.assertIs(run["synthetic"], True)

    def test_fila_con_todos_los_campos(self) -> None:
        expected = good_row(ci_low=0.55, ci_high=0.99, selected=True)
        _, results = adapt_rows(document(results=[copy.deepcopy(expected)]))
        self.assertEqual(results, [expected])

    def test_cada_campo_opcional_de_la_fila_ausente_es_none_y_selected_false(self) -> None:
        # Fila de tipo A de recuento con todos los campos opcionales presentes; se quita uno cada vez.
        full = case_row("fail", count=2, unit="casos", denominator=10, selected=True)
        for key in RESULT_KEYS[5:]:
            with self.subTest(missing=key):
                row = without(full, key)
                if key in ("count", "unit", "judgment"):
                    # Son opcionales en el formato, pero la validación común las exige en esta fila (un `fail`
                    # sin recuento, una unidad obligatoria, un tipo A sin juicio): el error se propaga.
                    with self.assertRaises(tool.AdapterError) as caught:
                        adapt_rows(document(results=[row]))
                    self.assert_prefix(caught.exception, f"results[0].{key}")
                    continue
                _, results = adapt_rows(document(results=[row]))
                self.assertEqual(results, [{**full, key: False if key == "selected" else None}])

    def test_fila_de_tipo_b_minima(self) -> None:
        row = {"measure_type": "B", "grp": "time", "metric_id": "time_saved", "behavior": "all",
               "status": "not_measured", "unit": "ms"}
        _, results = adapt_rows(document(results=[row]))
        expected = {key: None for key in RESULT_KEYS}
        expected.update(row, selected=False)
        self.assertEqual(results, [expected])

    def test_filas_en_el_orden_de_entrada_y_claves_canonicas(self) -> None:
        # La entrada llega con las claves al revés; la salida las tiene en el orden de RESULT_KEYS y RUN_KEYS.
        rows = [reverse_keys(robustness_input(behavior=f"b{i}")) for i in range(3)]
        run, results = adapt_rows(document(run=reverse_keys(full_run()), results=rows))
        self.assertEqual(list(run), list(RUN_KEYS))
        self.assertEqual([row["behavior"] for row in results], ["b0", "b1", "b2"])
        for row in results:
            self.assertEqual(list(row), list(RESULT_KEYS))


class RowsV1RunIdTest(RowsTestCase):
    def test_run_id_del_argumento_sustituye_al_del_documento(self) -> None:
        for call in (lambda d: adapt_rows(d, "ejecucion-2"), lambda d: adapt_rows(d, run_id="ejecucion-2")):
            run, _ = call(document(run={"run_id": "ejecucion-1", "source": "JUP-071"}))
            self.assertEqual(run["run_id"], "ejecucion-2")

    def test_sin_argumento_se_usa_el_del_documento(self) -> None:
        run, _ = adapt_rows(document(run={"run_id": "ejecucion-1", "source": "JUP-071"}))
        self.assertEqual(run["run_id"], "ejecucion-1")
        run, _ = adapt_rows(document(run={"run_id": "ejecucion-1", "source": "JUP-071"}), None)
        self.assertEqual(run["run_id"], "ejecucion-1")

    def test_la_sustitucion_solo_cambia_run_id(self) -> None:
        run, results = adapt_rows(document(run=full_run()), "otro")
        self.assertEqual(run, full_run(run_id="otro"))
        self.assertEqual(results, [good_row()])

    def test_run_id_del_argumento_se_valida(self) -> None:
        # Cadena vacía NO es None: sustituye y se rechaza (un `if run_id:` la ignoraría y aceptaría el del documento).
        for value in ("", "con espacios", "a" * 81, "id\n", 5, True):
            with self.subTest(run_id=value):
                with self.assertRaises(tool.AdapterError) as caught:
                    adapt_rows(document(), value)
                self.assert_prefix(caught.exception, "run.run_id")

    def test_run_id_de_80_caracteres_en_el_argumento(self) -> None:
        run, _ = adapt_rows(document(), "r" * 80)
        self.assertEqual(run["run_id"], "r" * 80)


class RowsV1RoundTripTest(RowsTestCase):
    """Un documento que reproduce la salida normalizada de un adaptador vuelve a salir idéntico."""

    def check(self, adapter, report) -> None:
        run, results = adapter(report)
        doc = {"contract_version": 1, "run": run, "results": results}
        out = adapt_rows(copy.deepcopy(doc))
        self.assertEqual(out, (run, results))
        self.assertEqual(list(out[0]), list(RUN_KEYS))
        self.assertTrue(all(list(row) == list(RESULT_KEYS) for row in out[1]))
        # Y también tras pasar por JSON (así llegará de un fichero); ningún valor se altera (NaN no hay).
        self.assertEqual(adapt_rows(json.loads(json.dumps(doc))), (run, results))

    def test_jup078(self) -> None:
        self.check(adapt_078, REPORTS["078"])

    def test_jup022(self) -> None:
        self.check(adapt_022, REPORTS["022"])

    def test_jup068(self) -> None:
        self.check(adapt_068, REPORTS["068"])

    def test_jup070_run_2(self) -> None:
        self.check(adapt_070, REPORTS["070-2"])

    def test_jup070_run_1(self) -> None:
        self.check(adapt_070, REPORTS["070-1"])

    def test_el_run_id_del_documento_es_el_de_la_salida_original(self) -> None:
        run, results = adapt_078(REPORTS["078"], "benchmark-modelos-1")
        out_run, _ = adapt_rows({"contract_version": 1, "run": run, "results": results})
        self.assertEqual(out_run["run_id"], "benchmark-modelos-1")


class RowsV1PurityTest(RowsTestCase):
    def test_no_muta_el_documento(self) -> None:
        doc = document(run=full_run(), results=[robustness_input(), robustness_input(behavior="otro", ci_low=0.5,
                                                                                    ci_high=0.9)])
        before = copy.deepcopy(doc)
        adapt_rows(doc, "otro-id")
        self.assertEqual(doc, before)

    def test_no_muta_el_documento_cuando_rechaza(self) -> None:
        doc = document(run=full_run(), results=[robustness_input(), robustness_input(behavior="a b")])
        before = copy.deepcopy(doc)
        with self.assertRaises(tool.AdapterError):
            adapt_rows(doc)
        self.assertEqual(doc, before)

    def test_la_salida_no_comparte_estructuras_con_el_documento(self) -> None:
        doc = document(run=full_run(), results=[robustness_input()])
        before = copy.deepcopy(doc)
        run, results = adapt_rows(doc)
        # Se altera TODO lo mutable de la salida: el documento (fuente de verdad) no debe enterarse.
        run["retrieval"]["top_k"] = 99
        run["commit"] = "cambiado"
        results[0]["value"] = 0.0
        results.append({"x": 1})
        self.assertEqual(doc, before)

    def test_dos_llamadas_son_iguales_y_no_comparten_estructuras(self) -> None:
        doc = document(run=full_run())
        first, second = adapt_rows(doc), adapt_rows(doc)
        self.assertEqual(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertIsNot(first[0]["retrieval"], second[0]["retrieval"])
        self.assertIsNot(first[1], second[1])
        self.assertIsNot(first[1][0], second[1][0])


class RowsV1DocumentErrorsTest(RowsTestCase):
    def assert_adapt_rejected(self, doc, *paths: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt_rows(doc)
        self.assert_prefix(caught.exception, *paths)

    def test_documento_que_no_es_un_objeto(self) -> None:
        for value in (None, [], "documento", 1, True, [document()], ()):
            with self.subTest(document=repr(value)[:30]):
                self.assert_adapt_rejected(value, "document")

    def test_contract_version_invalida(self) -> None:
        # True == 1 y 1.0 == 1 en Python: solo el entero 1 exacto vale (mismo criterio que los manifiestos).
        for value in (True, 1.0, "1", 2, 0, -1, None, [1], 1.5):
            with self.subTest(contract_version=repr(value)):
                self.assert_adapt_rejected(document(contract_version=value), "contract_version")

    def test_contract_version_ausente(self) -> None:
        self.assert_adapt_rejected(without(document(), "contract_version"), "contract_version")

    def test_clave_desconocida_de_nivel_superior(self) -> None:
        for key in ("extra", "milestone", "notes", "Run", "version"):
            with self.subTest(key=key):
                self.assert_adapt_rejected(document(**{key: "x"}), f"document.{key}")

    def test_run_ausente_o_mal_tipado(self) -> None:
        self.assert_adapt_rejected(without(document(), "run"), "run")
        for value in (None, [], "run", 1, True, [("run_id", "a")]):
            with self.subTest(run=repr(value)):
                doc = document()
                doc["run"] = value
                self.assert_adapt_rejected(doc, "run")

    def test_results_ausente_o_mal_tipado(self) -> None:
        self.assert_adapt_rejected(without(document(), "results"), "results")
        for value in (None, {}, "filas", 1, (), (robustness_input(),), {"0": robustness_input()}):
            with self.subTest(results=repr(value)[:30]):
                doc = document()
                doc["results"] = value
                self.assert_adapt_rejected(doc, "results")

    def test_fila_que_no_es_un_objeto(self) -> None:
        for value in (None, [], "fila", 1, True, ()):
            with self.subTest(row=repr(value)):
                self.assert_adapt_rejected(document(results=[robustness_input(), value]), "results[1]")

    def test_run_con_clave_desconocida(self) -> None:
        # `milestone` es de RUN_KEYS en la documentación del contrato, pero la fija el manifiesto: se rechaza.
        for key in ("milestone", "extra", "notes", "Commit"):
            with self.subTest(key=key):
                run = {"run_id": "a", "source": "b", key: "x"}
                self.assert_adapt_rejected(document(run=run), f"run.{key}")

    def test_run_sin_campos_obligatorios(self) -> None:
        for key in ("run_id", "source"):
            with self.subTest(missing=key):
                self.assert_adapt_rejected(document(run=without({"run_id": "a", "source": "b"}, key)), f"run.{key}")

    def test_fila_con_clave_desconocida(self) -> None:
        for key in ("extra", "question", "answer", "notes"):
            with self.subTest(key=key):
                row = robustness_input()
                row[key] = "texto"
                self.assert_adapt_rejected(document(results=[robustness_input(behavior="otro"), row]),
                                           f"results[1].{key}")

    def test_fila_sin_campos_obligatorios(self) -> None:
        for key in ("measure_type", "grp", "metric_id", "behavior", "status"):
            with self.subTest(missing=key):
                row = without(robustness_input(), key)
                self.assert_adapt_rejected(document(results=[robustness_input(behavior="otro"), row]),
                                           f"results[1].{key}")


class RowsV1PropagatesValidationTest(RowsTestCase):
    """`adapt_rows_v1` valida lo que construye con la validación común y propaga su error con su ruta."""

    def assert_adapt_rejected(self, doc, *paths: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt_rows(doc)
        self.assert_prefix(caught.exception, *paths)

    def test_texto_libre_en_una_fila(self) -> None:
        for field in ("grp", "metric_id", "behavior", "unit"):
            with self.subTest(field=field):
                rows = [robustness_input(grp="filler"), robustness_input(**{field: "¿Cuál es el enunciado?"})]
                self.assert_adapt_rejected(document(results=rows), f"results[1].{field}")

    def test_texto_libre_en_la_ejecucion(self) -> None:
        bad = {"source": "a b", "commit": "texto libre", "embedding_alias": "a" * 81, "run_at": "ayer",
               "synthetic": 1, "retrieval": [4]}
        for key, value in bad.items():
            with self.subTest(field=key):
                run = {"run_id": "a", "source": "JUP-071"}
                run[key] = value
                self.assert_adapt_rejected(document(run=run), f"run.{key}")

    def test_retrieval_con_clave_desconocida(self) -> None:
        run = {"run_id": "a", "source": "JUP-071", "retrieval": {"top_k": 4, "notas": 1}}
        self.assert_adapt_rejected(document(run=run), "run.retrieval.notas")

    def test_campos_explicitamente_null_que_no_pueden_serlo(self) -> None:
        # Un `null` escrito no equivale a una clave ausente: `synthetic` y `selected` ausentes valen False, pero
        # `null` incumple el booleano estricto; `run_id` y `source` nulos no son identificadores.
        self.assert_adapt_rejected(document(run={"run_id": "a", "source": "b", "synthetic": None}), "run.synthetic")
        self.assert_adapt_rejected(document(results=[robustness_input(selected=None)]), "results[0].selected")
        self.assert_adapt_rejected(document(run={"run_id": None, "source": "b"}), "run.run_id")
        self.assert_adapt_rejected(document(run={"run_id": "a", "source": None}), "run.source")

    def test_run_at_null_explicito_es_valido(self) -> None:
        run, _ = adapt_rows(document(run={"run_id": "a", "source": "b", "run_at": None}))
        self.assertIsNone(run["run_at"])

    def test_estado_y_tipo_invalidos(self) -> None:
        self.assert_adapt_rejected(document(results=[robustness_input(status="ok")]), "results[0].status")
        self.assert_adapt_rejected(document(results=[robustness_input(measure_type="C")]), "results[0].measure_type")

    def test_juicio_cruzado_entre_tipos(self) -> None:
        self.assert_adapt_rejected(document(results=[robustness_input(measure_type="B")]), "results[0].judgment")
        self.assert_adapt_rejected(document(results=[robustness_input(judgment=None)]), "results[0].judgment")
        self.assert_adapt_rejected(document(results=[robustness_input(judgment="manual")]), "results[0].judgment")

    def test_coherencia_de_estado_y_valor(self) -> None:
        self.assert_adapt_rejected(document(results=[robustness_input(status="not_measured")]), "results[0].value")
        # Con varios campos sobrantes (valor y numerador) basta con que el error sea de uno de ellos.
        self.assert_adapt_rejected(document(results=[robustness_input(status="pass", count=2)]),
                                   "results[0].value", "results[0].numerator")
        self.assert_adapt_rejected(document(results=[robustness_input(value=None)]), "results[0].value")

    def test_tasa_fuera_de_rango(self) -> None:
        self.assert_adapt_rejected(document(results=[robustness_input(numerator=11)]), "results[0].numerator")
        self.assert_adapt_rejected(document(results=[robustness_input(numerator=-1)]), "results[0].numerator")

    def test_filas_duplicadas(self) -> None:
        rows = [robustness_input(), robustness_input(value=0.5, numerator=5)]
        self.assert_adapt_rejected(document(results=rows), "results[1]")

    def test_numeros_no_validos(self) -> None:
        for value in (NAN, INF, True, "0.9", HUGE):
            with self.subTest(value=repr(value)[:20]):
                self.assert_adapt_rejected(document(results=[robustness_input(value=value)]), "results[0].value")

    def test_recuento_invalido(self) -> None:
        row = {"measure_type": "A", "grp": "cases", "metric_id": "cases", "behavior": "all", "status": "pass",
               "unit": "casos", "judgment": "human"}
        self.assert_adapt_rejected(document(results=[row]), "results[0].count")
        for count in (-1, True, 2.0, "2"):
            with self.subTest(count=count):
                self.assert_adapt_rejected(document(results=[{**row, "count": count}]), "results[0].count")

    def test_validacion_de_la_ejecucion_antes_que_la_de_las_filas(self) -> None:
        doc = document(run={"run_id": "a", "source": "b", "commit": "a b"},
                       results=[robustness_input(behavior="a b")])
        self.assert_adapt_rejected(doc, "run.commit")


if __name__ == "__main__":
    unittest.main()
