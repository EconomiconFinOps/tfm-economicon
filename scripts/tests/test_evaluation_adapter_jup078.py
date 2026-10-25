"""Adaptador del benchmark de modelos de JUP-078 de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.3, fase Red).

Contrato que se valida (`adapt_jup078(report, run_id) -> (run, results)`):

* Es una función PURA sobre el dict ya parseado: no lee ficheros, no lo muta y no comparte estructuras
  con él.
* `run` tiene EXACTAMENTE las claves de `RUN_KEYS`: solo `run_id`, `source="JUP-078"` y
  `synthetic=False` llevan valor. El benchmark no registra commit, fecha, batería, corpus, embeddings
  ni prompt, y cada informe trae varios modelos, así que `generation_model` tampoco se rellena.
* Por cada modelo, en el orden del informe, cinco filas con `behavior` = alias: casos `pass`, casos
  `fail`, puntuación de palabras clave, latencia p95 y coste. El resto de claves de cada fila es None.
* Los valores medidos se COPIAN sin redondear ni convertir tipos. Lo no medido es `None` con estado
  `not_measured`, nunca 0 (spec «Lo no medido nunca es cero»). Caso sutil: el generador del benchmark
  escribe `mean_keyword_score = 0` cuando no hubo ninguna llamada correcta, y ese 0 significa «sin
  datos», no «puntuación nula»; por eso con `successful == 0` la puntuación (y la latencia y el coste)
  son no medidos aunque el informe traiga un número. Con `successful > 0` un 0 SÍ es una medición.
* Un informe que retiene texto (`content_retained` distinto de `False`), de otra versión o con la forma
  rota se rechaza con `AdapterError` cuyo mensaje EMPIEZA por `<campo>: `.
* No se copia texto libre: ni `error_type`, ni `notes`, ni los `results` por caso; solo identificadores.

Los valores esperados se escriben a mano a partir del informe real
(`docs/evidence/JUP-078-benchmark-results.json`) o se leen de ese JSON con accesos directos; en ningún
caso se calculan llamando al adaptador. Las variantes se construyen con `copy.deepcopy` del informe real
para que solo cambie el dato que se quiere probar.

Endurecimiento desde el principio (lección de la mutación de 2.1 y 2.2): alias de un solo carácter,
varios modelos con valores distintos para detectar mezclas, denominador `successful` frente a `cases`,
`fail = cases - successful` con `successful` distinto de `cases / 2`, bool frente a entero y prefijo
EXACTO del mensaje de error.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL`
para apuntar estas pruebas a una copia mutada.
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
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup078", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REPORT = json.loads((ROOT / "docs" / "evidence" / "JUP-078-benchmark-results.json").read_text(encoding="utf8"))

RUN_ID = "benchmark-modelos-1"

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

CHAT = "economicon-chat"
DEEPSEEK = "economicon-chat-deepseek"

MODEL_REQUIRED = ("alias", "cases", "successful", "mean_keyword_score", "p95_latency_ms", "cost_usd")
MEASURE_FIELDS = ("mean_keyword_score", "p95_latency_ms", "cost_usd")

MARKER = "Texto libre con espacios que no debe aparecer en la salida"


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup078(report, run_id)


def expected_run(run_id: str = RUN_ID) -> dict:
    """`run` esperado: todo None salvo run_id, la fuente y synthetic False."""
    run = {key: None for key in RUN_KEYS}
    run.update(run_id=run_id, source="JUP-078", synthetic=False)
    return run


def expected_row(metric_id: str, alias: str, status: str, unit: str, **fields) -> dict:
    """Fila esperada completa: todo lo no indicado es None salvo los valores fijos del benchmark."""
    row = {key: None for key in RESULT_KEYS}
    row.update(measure_type="A", grp="benchmark", metric_id=metric_id, behavior=alias, status=status,
               unit=unit, judgment="automatic", selected=False)
    row.update(fields)
    return row


def case_rows(alias: str, cases: int, successful: int) -> list[dict]:
    """Filas 1 y 2 de un modelo: `pass` = successful, `fail` = cases - successful, `cases` de denominador."""
    return [
        expected_row("cases", alias, "pass", "casos", count=successful, denominator=cases),
        expected_row("cases", alias, "fail", "casos", count=cases - successful, denominator=cases),
    ]


def measured(metric_id: str, unit: str, alias: str, value, denominator) -> dict:
    return expected_row(metric_id, alias, "measured", unit, value=value, denominator=denominator)


def not_measured(metric_id: str, unit: str, alias: str, denominator) -> dict:
    # `value` y `count` None: assertEqual con None distingue None de 0 y de 0.0.
    return expected_row(metric_id, alias, "not_measured", unit, denominator=denominator)


def model_rows(alias: str, cases: int, successful: int, score, p95, cost) -> list[dict]:
    """Las cinco filas esperadas de un modelo con TODAS las métricas medidas."""
    return case_rows(alias, cases, successful) + [
        measured("keyword_score", "puntuacion", alias, score, successful),
        measured("latency_p95", "ms", alias, p95, successful),
        measured("cost", "usd", alias, cost, None),
    ]


# Filas esperadas del informe real, escritas a mano desde el JSON.
REAL_ROWS = (
    model_rows(CHAT, 5, 5, 0.9, 11728.5, 0.0005395524)
    + model_rows(DEEPSEEK, 5, 4, 0.75, 10875.63, 0.0003567)
)


def variant(mutate, base: dict = REPORT) -> dict:
    """Copia profunda del informe con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(base)
    mutate(report)
    return report


def with_model(index: int = 0, **fields) -> dict:
    """Informe real en el que el modelo `index` cambia los campos indicados."""
    return variant(lambda r: r["models"][index].update(fields))


def only_model(index: int = 0, **fields) -> dict:
    """Informe real con un único modelo (el `index`) y los campos cambiados."""

    def make(report: dict) -> None:
        report["models"] = [report["models"][index]]
        report["models"][0].update(fields)

    return variant(make)


def rows_for(results: list[dict], alias: str) -> list[dict]:
    return [row for row in results if row["behavior"] == alias]


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


class RunBlockTest(unittest.TestCase):
    """El bloque `run`: el benchmark solo aporta la fuente; lo demás es «no registrado»."""

    def test_run_completo_del_informe_real(self) -> None:
        # Sin commit, fecha, batería, corpus, embeddings ni prompt, y con varios modelos por informe:
        # nada se deduce ni se inventa, todo queda None salvo run_id, source y synthetic False.
        run, _ = adapt(REPORT)
        self.assertEqual(tuple(run), RUN_KEYS)
        self.assertEqual(run, {
            "run_id": RUN_ID,
            "source": "JUP-078",
            "run_at": None,
            "commit": None,
            "suite": None,
            "suite_version": None,
            "suite_sha256": None,
            "corpus_sha256": None,
            "embedding_provider": None,
            "embedding_alias": None,
            "retrieval": None,
            "generation_model": None,
            "prompt_sha256": None,
            "synthetic": False,
            "generation_model_id": None,
            "generation_provider": None,
            "generation_quantization": None,
            "gateway_config_sha256": None,
        })

    def test_run_id_es_el_argumento(self) -> None:
        # El identificador lo decide el manifiesto/herramienta: el informe no trae uno.
        run, _ = adapt(REPORT, "otro-id.v2")
        self.assertEqual(run["run_id"], "otro-id.v2")
        self.assertEqual(run, expected_run("otro-id.v2"))

    def test_solo_run_id_source_y_synthetic_tienen_valor(self) -> None:
        run, _ = adapt(REPORT)
        with_value = {key for key, value in run.items() if value is not None}
        self.assertEqual(with_value, {"run_id", "source", "synthetic"})
        self.assertIs(run["synthetic"], False)

    def test_generation_model_none_aunque_haya_un_solo_modelo(self) -> None:
        # Aunque el informe tenga un único modelo no se promociona su alias a generation_model: la
        # regla es la misma para todos los informes del benchmark (el alias va en `behavior`).
        run, _ = adapt(only_model(0))
        self.assertIsNone(run["generation_model"])
        self.assertEqual(run, expected_run())


class RealReportRowsTest(unittest.TestCase):
    """Normalización completa del informe real (dos modelos)."""

    def setUp(self) -> None:
        _, self.results = adapt(REPORT)

    def test_numero_de_filas(self) -> None:
        # 2 modelos x 5 filas.
        self.assertEqual(len(self.results), 10)

    def test_filas_completas_y_en_orden(self) -> None:
        # Igualdad de lista completa: orden por modelo (como en el informe) y dentro de cada modelo
        # pass, fail, keyword_score, latency_p95, cost.
        self.assertEqual(self.results, REAL_ROWS)

    def test_orden_exacto_por_modelo(self) -> None:
        order = [(row["behavior"], row["metric_id"], row["status"]) for row in self.results]
        expected = []
        for alias in (CHAT, DEEPSEEK):
            expected += [(alias, "cases", "pass"), (alias, "cases", "fail"),
                         (alias, "keyword_score", "measured"), (alias, "latency_p95", "measured"),
                         (alias, "cost", "measured")]
        self.assertEqual(order, expected)

    def test_economicon_chat(self) -> None:
        # 5 de 5 correctas: ningún fallo; los tres valores del JSON.
        rows = rows_for(self.results, CHAT)
        self.assertEqual([(r["metric_id"], r["status"], r["count"], r["value"], r["denominator"])
                          for r in rows], [
            ("cases", "pass", 5, None, 5),
            ("cases", "fail", 0, None, 5),
            ("keyword_score", "measured", None, 0.9, 5),
            ("latency_p95", "measured", None, 11728.5, 5),
            ("cost", "measured", None, 0.0005395524, None),
        ])

    def test_economicon_chat_deepseek(self) -> None:
        # 4 de 5: un fallo (el timeout), y los denominadores de puntuación y latencia son los 4 correctos.
        rows = rows_for(self.results, DEEPSEEK)
        self.assertEqual([(r["metric_id"], r["status"], r["count"], r["value"], r["denominator"])
                          for r in rows], [
            ("cases", "pass", 4, None, 5),
            ("cases", "fail", 1, None, 5),
            ("keyword_score", "measured", None, 0.75, 4),
            ("latency_p95", "measured", None, 10875.63, 4),
            ("cost", "measured", None, 0.0003567, None),
        ])

    def test_claves_unidades_grp_juicio_y_selected(self) -> None:
        for row in self.results:
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                self.assertEqual(tuple(row), RESULT_KEYS)
                self.assertEqual(row["measure_type"], "A")
                self.assertEqual(row["grp"], "benchmark")
                self.assertEqual(row["judgment"], "automatic")
                self.assertIs(row["selected"], False)
        units = {row["metric_id"]: row["unit"] for row in self.results}
        self.assertEqual(units, {"cases": "casos", "keyword_score": "puntuacion",
                                 "latency_p95": "ms", "cost": "usd"})

    def test_campos_sin_uso_son_none(self) -> None:
        # Numerador, intervalos: el benchmark no los tiene. `count` solo en las filas de casos y `value`
        # solo en las de valor.
        for row in self.results:
            with self.subTest(metric=row["metric_id"], behavior=row["behavior"]):
                for key in ("numerator", "ci_low", "ci_high"):
                    self.assertIsNone(row[key])
                if row["metric_id"] == "cases":
                    self.assertIsNone(row["value"])
                else:
                    self.assertIsNone(row["count"])

    def test_valores_leidos_del_json_en_disco(self) -> None:
        # Se compara con el JSON leído de nuevo del disco, no con el objeto ya cargado en el módulo.
        raw = json.loads((ROOT / "docs" / "evidence" / "JUP-078-benchmark-results.json").read_text(encoding="utf8"))
        _, results = adapt(raw)
        for model in raw["models"]:
            rows = rows_for(results, model["alias"])
            with self.subTest(alias=model["alias"]):
                self.assertEqual(rows[0]["count"], model["successful"])
                self.assertEqual(rows[1]["count"], model["cases"] - model["successful"])
                self.assertEqual(rows[2]["value"], model["mean_keyword_score"])
                self.assertEqual(rows[3]["value"], model["p95_latency_ms"])
                self.assertEqual(rows[4]["value"], model["cost_usd"])


class NotMeasuredTest(unittest.TestCase):
    """Lo no medido es None con `not_measured` y nunca 0."""

    def assert_second_model_intact(self, results: list[dict]) -> None:
        # Cambiar un dato del primer modelo no debe tocar las filas del segundo.
        self.assertEqual(rows_for(results, DEEPSEEK), model_rows(DEEPSEEK, 5, 4, 0.75, 10875.63, 0.0003567))

    def test_sin_llamadas_correctas_la_puntuacion_cero_es_sin_datos(self) -> None:
        # El caso real del generador: sin ninguna llamada correcta escribe mean_keyword_score = 0, que
        # significa «sin datos». No puede publicarse como una puntuación medida de 0.
        report = with_model(0, successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None)
        _, results = adapt(report)
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 5, 0) + [
            not_measured("keyword_score", "puntuacion", CHAT, 0),
            not_measured("latency_p95", "ms", CHAT, 0),
            not_measured("cost", "usd", CHAT, None),
        ])
        self.assert_second_model_intact(results)

    def test_sin_llamadas_correctas_con_valores_numericos_todo_no_medido(self) -> None:
        # Un informe incoherente (successful 0 pero con p95 y coste numéricos) tampoco publica esos
        # números como medidos: sin llamadas correctas no hay nada que haya podido medirse.
        report = with_model(0, successful=0, mean_keyword_score=0.5, p95_latency_ms=1234.5, cost_usd=0.002)
        _, results = adapt(report)
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 5, 0) + [
            not_measured("keyword_score", "puntuacion", CHAT, 0),
            not_measured("latency_p95", "ms", CHAT, 0),
            not_measured("cost", "usd", CHAT, None),
        ])
        self.assert_second_model_intact(results)

    def test_sin_llamadas_correctas_con_ceros_todo_no_medido(self) -> None:
        # Variante con 0 en las tres métricas (otro modo de «sin datos»): nunca medidas de 0.
        _, results = adapt(with_model(0, successful=0, mean_keyword_score=0, p95_latency_ms=0, cost_usd=0))
        for row in rows_for(results, CHAT)[2:]:
            with self.subTest(metric=row["metric_id"]):
                self.assertEqual(row["status"], "not_measured")
                self.assertIsNone(row["value"])
                self.assertIsNone(row["count"])

    def test_puntuacion_cero_con_llamadas_correctas_es_una_medicion(self) -> None:
        # Contraste del caso anterior: con successful > 0 un 0.0 es una puntuación real (todas fallaron
        # las palabras clave) y debe copiarse como medida, no esconderse como no medida.
        _, results = adapt(with_model(0, mean_keyword_score=0.0))
        row = rows_for(results, CHAT)[2]
        self.assertEqual(row, measured("keyword_score", "puntuacion", CHAT, 0.0, 5))
        self.assertIsNotNone(row["value"])
        self.assertIs(type(row["value"]), float)
        self.assert_second_model_intact(results)

    def test_puntuacion_cero_entera_con_llamadas_correctas_es_medida(self) -> None:
        _, results = adapt(with_model(1, mean_keyword_score=0))
        row = rows_for(results, DEEPSEEK)[2]
        self.assertEqual(row, measured("keyword_score", "puntuacion", DEEPSEEK, 0, 4))
        self.assertIs(type(row["value"]), int)

    def test_coste_cero_con_llamadas_correctas_es_medido(self) -> None:
        # Un modelo gratuito cuesta 0.0 USD: es una medición, no ausencia de coste.
        _, results = adapt(with_model(0, cost_usd=0.0))
        row = rows_for(results, CHAT)[4]
        self.assertEqual(row, measured("cost", "usd", CHAT, 0.0, None))
        self.assertEqual(row["status"], "measured")
        self.assertIsNotNone(row["value"])
        self.assert_second_model_intact(results)

    def test_latencia_cero_con_llamadas_correctas_es_medida(self) -> None:
        _, results = adapt(with_model(0, p95_latency_ms=0))
        self.assertEqual(rows_for(results, CHAT)[3], measured("latency_p95", "ms", CHAT, 0, 5))

    def test_puntuacion_none_es_no_medida(self) -> None:
        # Solo cambia la puntuación: latencia y coste del mismo modelo siguen medidos.
        _, results = adapt(with_model(0, mean_keyword_score=None))
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 5, 5) + [
            not_measured("keyword_score", "puntuacion", CHAT, 5),
            measured("latency_p95", "ms", CHAT, 11728.5, 5),
            measured("cost", "usd", CHAT, 0.0005395524, None),
        ])
        self.assert_second_model_intact(results)

    def test_latencia_none_es_no_medida(self) -> None:
        _, results = adapt(with_model(1, p95_latency_ms=None))
        self.assertEqual(rows_for(results, DEEPSEEK), case_rows(DEEPSEEK, 5, 4) + [
            measured("keyword_score", "puntuacion", DEEPSEEK, 0.75, 4),
            not_measured("latency_p95", "ms", DEEPSEEK, 4),
            measured("cost", "usd", DEEPSEEK, 0.0003567, None),
        ])
        self.assertEqual(rows_for(results, CHAT), model_rows(CHAT, 5, 5, 0.9, 11728.5, 0.0005395524))

    def test_coste_none_es_no_medido(self) -> None:
        # El coste no tiene denominador, ni siquiera cuando no se mide.
        _, results = adapt(with_model(0, cost_usd=None))
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 5, 5) + [
            measured("keyword_score", "puntuacion", CHAT, 0.9, 5),
            measured("latency_p95", "ms", CHAT, 11728.5, 5),
            not_measured("cost", "usd", CHAT, None),
        ])
        self.assert_second_model_intact(results)

    def test_las_tres_metricas_none_con_llamadas_correctas(self) -> None:
        _, results = adapt(with_model(0, mean_keyword_score=None, p95_latency_ms=None, cost_usd=None))
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 5, 5) + [
            not_measured("keyword_score", "puntuacion", CHAT, 5),
            not_measured("latency_p95", "ms", CHAT, 5),
            not_measured("cost", "usd", CHAT, None),
        ])

    def test_no_medidos_nunca_llevan_valor_ni_recuento(self) -> None:
        # Barrido de todas las combinaciones de None: lo no medido jamás lleva value, count, numerator ni CI.
        for score in (None, 0.9):
            for p95 in (None, 100.5):
                for cost in (None, 0.01):
                    report = with_model(0, mean_keyword_score=score, p95_latency_ms=p95, cost_usd=cost)
                    _, results = adapt(report)
                    for row in rows_for(results, CHAT)[2:]:
                        with self.subTest(score=score, p95=p95, cost=cost, metric=row["metric_id"]):
                            if row["status"] == "not_measured":
                                for key in ("value", "count", "numerator", "ci_low", "ci_high"):
                                    self.assertIsNone(row[key])
                            else:
                                self.assertEqual(row["status"], "measured")
                                self.assertIsNotNone(row["value"])

    def test_cero_casos(self) -> None:
        # Sin casos no se inventan estados: las dos filas de casos salen con recuento 0 y denominador 0,
        # y al no haber llamadas correctas las métricas son no medidas.
        report = with_model(0, cases=0, successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None)
        _, results = adapt(report)
        self.assertEqual(rows_for(results, CHAT), case_rows(CHAT, 0, 0) + [
            not_measured("keyword_score", "puntuacion", CHAT, 0),
            not_measured("latency_p95", "ms", CHAT, 0),
            not_measured("cost", "usd", CHAT, None),
        ])
        pass_row, fail_row = rows_for(results, CHAT)[:2]
        self.assertEqual((pass_row["count"], pass_row["denominator"]), (0, 0))
        self.assertEqual((fail_row["count"], fail_row["denominator"]), (0, 0))
        self.assert_second_model_intact(results)

    def test_todo_fallido_cuenta_todos_como_fail(self) -> None:
        # successful 0 con 5 casos: pass 0 y fail 5 (no 0 ni 2 ni 3); el denominador sigue siendo cases.
        _, results = adapt(with_model(0, successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None))
        pass_row, fail_row = rows_for(results, CHAT)[:2]
        self.assertEqual((pass_row["status"], pass_row["count"], pass_row["denominator"]), ("pass", 0, 5))
        self.assertEqual((fail_row["status"], fail_row["count"], fail_row["denominator"]), ("fail", 5, 5))

    def test_no_medido_no_altera_el_run(self) -> None:
        run, _ = adapt(with_model(0, mean_keyword_score=None, successful=0))
        self.assertEqual(run, expected_run())


class HardeningTest(unittest.TestCase):
    """Casos que distinguen implementaciones incorrectas pero verosímiles (mutantes típicos)."""

    def test_alias_de_un_solo_caracter(self) -> None:
        # Un alias mínimo es válido y llega a `behavior`; evita validaciones de longitud mal puestas.
        _, results = adapt(only_model(0, alias="a"))
        self.assertEqual(results, model_rows("a", 5, 5, 0.9, 11728.5, 0.0005395524))

    def test_alias_de_un_solo_caracter_en_dos_modelos(self) -> None:
        def make(report: dict) -> None:
            report["models"][0]["alias"] = "a"
            report["models"][1]["alias"] = "b"

        _, results = adapt(variant(make))
        self.assertEqual([r["behavior"] for r in results], ["a"] * 5 + ["b"] * 5)

    def test_tres_modelos_con_valores_distintos_no_se_mezclan(self) -> None:
        # Todos los campos distintos entre modelos: un adaptador que reutilice un valor de otro modelo
        # (índice mal calculado, variable arrastrada del bucle) lo delata.
        def make(report: dict) -> None:
            report["models"] = [
                {"alias": "m1", "cases": 10, "successful": 9, "mean_keyword_score": 0.1,
                 "p95_latency_ms": 111.5, "cost_usd": 0.001},
                {"alias": "m2", "cases": 8, "successful": 3, "mean_keyword_score": 0.2,
                 "p95_latency_ms": 222.5, "cost_usd": 0.002},
                {"alias": "m3", "cases": 6, "successful": 6, "mean_keyword_score": 0.3,
                 "p95_latency_ms": 333.5, "cost_usd": 0.003},
            ]

        _, results = adapt(variant(make))
        self.assertEqual(results,
                         model_rows("m1", 10, 9, 0.1, 111.5, 0.001)
                         + model_rows("m2", 8, 3, 0.2, 222.5, 0.002)
                         + model_rows("m3", 6, 6, 0.3, 333.5, 0.003))

    def test_un_modelo_no_medido_no_contagia_al_siguiente(self) -> None:
        # El primero sin datos y el segundo con datos: el estado no medido no se arrastra entre iteraciones.
        def make(report: dict) -> None:
            report["models"][0].update(successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None)

        _, results = adapt(variant(make))
        self.assertEqual(rows_for(results, DEEPSEEK), model_rows(DEEPSEEK, 5, 4, 0.75, 10875.63, 0.0003567))
        # Y a la inversa: el primero medido y el segundo sin datos.

        def reverse(report: dict) -> None:
            report["models"][1].update(successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None)

        _, results = adapt(variant(reverse))
        self.assertEqual(rows_for(results, CHAT), model_rows(CHAT, 5, 5, 0.9, 11728.5, 0.0005395524))

    def test_denominador_de_puntuacion_y_latencia_es_successful_no_cases(self) -> None:
        # cases 7 y successful 2: el denominador de la puntuación y de la p95 es 2; el de pass/fail es 7.
        _, results = adapt(only_model(0, cases=7, successful=2))
        rows = rows_for(results, CHAT)
        self.assertEqual(rows[2]["denominator"], 2)
        self.assertEqual(rows[3]["denominator"], 2)
        self.assertIsNone(rows[4]["denominator"])
        self.assertEqual(rows[0]["denominator"], 7)
        self.assertEqual(rows[1]["denominator"], 7)

    def test_fail_es_cases_menos_successful_sin_confundir_el_signo(self) -> None:
        # successful 2 de 7: pass 2, fail 5. Con successful = cases/2 (p. ej. 4 de 8) un signo cambiado
        # o un intercambio pass/fail daría lo mismo; aquí 2 y 5 son distintos y no son la mitad.
        _, results = adapt(only_model(0, cases=7, successful=2))
        self.assertEqual(results[:2], case_rows(CHAT, 7, 2))
        self.assertEqual((results[0]["status"], results[0]["count"]), ("pass", 2))
        self.assertEqual((results[1]["status"], results[1]["count"]), ("fail", 5))

    def test_fail_con_otros_valores_asimetricos(self) -> None:
        for cases, successful in ((10, 1), (10, 9), (3, 0), (3, 3), (1, 0), (1, 1), (100, 37)):
            with self.subTest(cases=cases, successful=successful):
                _, results = adapt(only_model(0, cases=cases, successful=successful))
                self.assertEqual(results[:2], case_rows(CHAT, cases, successful))
                self.assertEqual(results[0]["count"] + results[1]["count"], cases)

    def test_bool_en_cases_se_rechaza_pero_el_entero_1_vale(self) -> None:
        # True es 1 en Python; solo el entero real es un recuento.
        with self.assertRaises(tool.AdapterError):
            adapt(only_model(0, cases=True, successful=1))
        _, results = adapt(only_model(0, cases=1, successful=1))
        self.assertEqual(results[:2], case_rows(CHAT, 1, 1))

    def test_bool_en_successful_se_rechaza_pero_el_entero_1_vale(self) -> None:
        with self.assertRaises(tool.AdapterError):
            adapt(only_model(0, cases=2, successful=True))
        _, results = adapt(only_model(0, cases=2, successful=1))
        self.assertEqual(results[:2], case_rows(CHAT, 2, 1))

    def test_successful_igual_a_cases_es_valido(self) -> None:
        # Frontera: successful == cases no es error (solo successful > cases lo es).
        _, results = adapt(only_model(0, cases=5, successful=5))
        self.assertEqual(results[1]["count"], 0)

    def test_successful_uno_por_debajo_y_uno_por_encima_de_cases(self) -> None:
        # Frontera exacta de la comparación successful <= cases.
        _, results = adapt(only_model(0, cases=5, successful=4))
        self.assertEqual(results[:2], case_rows(CHAT, 5, 4))
        with self.assertRaises(tool.AdapterError):
            adapt(only_model(0, cases=5, successful=6))

    def test_cero_casos_y_cero_correctos_es_valido(self) -> None:
        # Frontera inferior: 0 es un recuento válido para cases y successful.
        _, results = adapt(only_model(0, cases=0, successful=0))
        self.assertEqual(results[:2], case_rows(CHAT, 0, 0))

    def test_enteros_como_valores_medidos_conservan_su_tipo(self) -> None:
        # Un entero del informe no se convierte a float ni al revés.
        _, results = adapt(only_model(0, mean_keyword_score=1, p95_latency_ms=12000, cost_usd=1))
        rows = rows_for(results, CHAT)
        self.assertIs(type(rows[2]["value"]), int)
        self.assertIs(type(rows[3]["value"]), int)
        self.assertIs(type(rows[4]["value"]), int)
        self.assertEqual([r["value"] for r in rows[2:]], [1, 12000, 1])

    def test_flotantes_se_copian_sin_redondear(self) -> None:
        # Coste con 10 decimales y valores con la imprecisión binaria típica: se copian idénticos.
        report = only_model(0, mean_keyword_score=0.8000000000000002, p95_latency_ms=11728.500000000002,
                            cost_usd=0.0005395524000000001)
        _, results = adapt(report)
        rows = rows_for(results, CHAT)
        self.assertEqual(repr(rows[2]["value"]), "0.8000000000000002")
        self.assertEqual(repr(rows[3]["value"]), "11728.500000000002")
        self.assertEqual(repr(rows[4]["value"]), "0.0005395524000000001")

    def test_valores_reales_sin_redondear(self) -> None:
        _, results = adapt(REPORT)
        self.assertEqual(repr(results[4]["value"]), "0.0005395524")
        self.assertEqual(repr(results[9]["value"]), "0.0003567")
        self.assertIs(type(results[2]["value"]), float)


class ErrorsTest(unittest.TestCase):
    """AdapterError con «<campo>: <problema>»; el mensaje EMPIEZA por el campo."""

    def assert_error(self, report, field: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        # Formato del contrato: el mensaje empieza por el campo exacto y un separador, no solo lo contiene.
        self.assertTrue(message.startswith(f"{field}: "), message)

    def test_error_es_value_error(self) -> None:
        # Se comprueba junto a una llamada real: el error de datos hereda de ValueError (como ManifestError).
        with self.assertRaises(ValueError):
            adapt([])

    def test_report_no_es_objeto(self) -> None:
        for bad in ([], None, "informe", 3, [REPORT]):
            with self.subTest(bad=repr(bad)[:20]):
                self.assert_error(bad, "report")

    def test_schema_version_distinta_de_1(self) -> None:
        # Solo el entero 1 vale: True (que es 1 en Python), "1", 1.0 o la ausencia se rechazan.
        for bad in (2, 0, -1, True, "1", None, 1.0):
            with self.subTest(version=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(schema_version=bad)), "schema_version")

    def test_schema_version_ausente(self) -> None:
        self.assert_error(variant(lambda r: r.pop("schema_version")), "schema_version")

    def test_content_retained_ausente(self) -> None:
        # Un informe que no declara si retiene texto no se carga: no se supone nada.
        self.assert_error(variant(lambda r: r.pop("content_retained")), "content_retained")

    def test_content_retained_distinto_de_false(self) -> None:
        # Solo el booleano False vale; True (retiene texto) y los equivalentes falsos de otros tipos no.
        for bad in (True, 0, "false", "False", None, [], 0.0):
            with self.subTest(content_retained=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(content_retained=bad)), "content_retained")

    def test_models_no_es_lista(self) -> None:
        for bad in ({}, {"alias": "x"}, None, "modelos", 3):
            with self.subTest(models=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(models=bad)), "models")

    def test_models_ausente(self) -> None:
        self.assert_error(variant(lambda r: r.pop("models")), "models")

    def test_modelo_no_es_objeto(self) -> None:
        for bad in (None, [], 5, "economicon-chat"):
            with self.subTest(model=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["models"].__setitem__(1, bad)), "models[1]")
        # Y en la posición 0 el índice del mensaje es 0.
        self.assert_error(variant(lambda r: r["models"].__setitem__(0, None)), "models[0]")

    def test_campo_obligatorio_ausente_en_cada_modelo(self) -> None:
        for index in (0, 1):
            for field in MODEL_REQUIRED:
                with self.subTest(index=index, field=field):
                    self.assert_error(variant(lambda r, index=index, field=field: r["models"][index].pop(field)),
                                      f"models[{index}].{field}")

    def test_alias_no_valido(self) -> None:
        for bad in ("", 5, None, ["x"], True, {}):
            with self.subTest(alias=repr(bad)):
                self.assert_error(with_model(1, alias=bad), "models[1].alias")
        self.assert_error(with_model(0, alias=""), "models[0].alias")

    def test_alias_repetido(self) -> None:
        # El error apunta al SEGUNDO modelo con ese alias.
        self.assert_error(with_model(1, alias=CHAT), "models[1].alias")

    def test_alias_repetido_no_adyacente(self) -> None:
        def make(report: dict) -> None:
            third = copy.deepcopy(report["models"][0])
            third["alias"] = "otro"
            report["models"].insert(1, third)  # chat, otro, deepseek
            report["models"][2]["alias"] = CHAT  # el repetido es el de la posición 2

        self.assert_error(variant(make), "models[2].alias")

    def test_cases_no_valido(self) -> None:
        # bool, cadena, flotante (aunque sea entero 5.0), negativo y None.
        for bad in (True, False, "5", 5.0, 5.5, -1, None, [5]):
            with self.subTest(cases=repr(bad)):
                self.assert_error(with_model(1, cases=bad), "models[1].cases")
        self.assert_error(with_model(0, cases=-1), "models[0].cases")

    def test_successful_no_valido(self) -> None:
        for bad in (True, False, "4", 4.0, 4.5, -1, None, [4]):
            with self.subTest(successful=repr(bad)):
                self.assert_error(with_model(1, successful=bad), "models[1].successful")
        self.assert_error(with_model(0, successful=-1), "models[0].successful")

    def test_successful_mayor_que_cases(self) -> None:
        self.assert_error(with_model(1, successful=6), "models[1].successful")
        self.assert_error(with_model(0, cases=4, successful=5), "models[0].successful")
        self.assert_error(with_model(0, cases=0, successful=1), "models[0].successful")

    def test_metricas_con_tipo_no_valido(self) -> None:
        # Cada campo medido admite int/float finito o None; cadena, bool, lista y objeto se rechazan.
        for field in MEASURE_FIELDS:
            for bad in ("0.5", True, False, [1], {}, {"v": 1}):
                with self.subTest(field=field, bad=repr(bad)):
                    self.assert_error(with_model(1, **{field: bad}), f"models[1].{field}")

    def test_metricas_no_finitas(self) -> None:
        # NaN e infinito no son mediciones: se rechazan en lugar de publicarse.
        for field in MEASURE_FIELDS:
            for bad in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, bad=repr(bad)):
                    self.assert_error(with_model(0, **{field: bad}), f"models[0].{field}")

    def test_metricas_no_finitas_con_cero_llamadas_correctas_tambien_se_rechazan(self) -> None:
        # La validación va antes que la regla de «sin datos»: un NaN no se esconde como no medido.
        report = with_model(0, successful=0, p95_latency_ms=float("nan"))
        self.assert_error(report, "models[0].p95_latency_ms")

    def test_metricas_none_son_validas(self) -> None:
        # Contraste de los rechazos anteriores: None sí es un valor admitido en los tres campos.
        for field in MEASURE_FIELDS:
            with self.subTest(field=field):
                _, results = adapt(with_model(0, **{field: None}))
                self.assertEqual(len(results), 10)

    def test_se_informa_del_primer_modelo_defectuoso(self) -> None:
        # Con dos modelos rotos se informa del primero, de forma determinista.
        def make(report: dict) -> None:
            report["models"][0]["cases"] = "5"
            report["models"][1]["cases"] = "5"

        self.assert_error(variant(make), "models[0].cases")

    def test_error_de_nivel_superior_antes_que_el_de_modelo(self) -> None:
        # content_retained True y un modelo roto: manda el campo del nivel superior.
        def make(report: dict) -> None:
            report["content_retained"] = True
            report["models"][0]["cases"] = "x"

        self.assert_error(variant(make), "content_retained")

    def test_el_error_se_lanza_aunque_el_resto_sea_valido(self) -> None:
        # Con un modelo válido y otro roto no se devuelve un resultado parcial.
        with self.assertRaises(tool.AdapterError):
            adapt(with_model(1, cases="mal"))


class PurityTest(unittest.TestCase):
    """La función no muta la entrada, es determinista y tolera lo que no usa."""

    def test_no_muta_el_informe(self) -> None:
        candidate = copy.deepcopy(REPORT)
        adapt(candidate)
        self.assertEqual(candidate, REPORT)

    def test_no_muta_el_informe_con_no_medidos(self) -> None:
        report = with_model(0, successful=0, mean_keyword_score=0, p95_latency_ms=None, cost_usd=None)
        before = copy.deepcopy(report)
        adapt(report)
        self.assertEqual(report, before)

    def test_dos_llamadas_dan_lo_mismo(self) -> None:
        first = adapt(REPORT)
        second = adapt(REPORT)
        self.assertEqual(first, second)
        # Y las salidas son independientes: mutar una no altera la otra ni una llamada posterior.
        first[1][0]["count"] = 999
        first[0]["run_id"] = "mutado"
        third = adapt(REPORT)
        self.assertEqual(third[1][0]["count"], 5)
        self.assertEqual(third[0]["run_id"], RUN_ID)

    def test_la_salida_no_comparte_estructuras_con_la_entrada(self) -> None:
        # Ningún dict/list de la salida es el mismo objeto que uno de la entrada: mutar la fila no puede
        # alterar el informe, que es la fuente de verdad.
        report = copy.deepcopy(REPORT)
        input_ids = {id(item) for item in containers(report)}
        run, results = adapt(report)
        for item in list(containers(run)) + list(containers(results)):
            self.assertNotIn(id(item), input_ids)
        for row in results:
            row["count"] = -1
            row["behavior"] = "mutada"
        run["source"] = "mutada"
        self.assertEqual(report, REPORT)

    def test_las_filas_son_dicts_distintos(self) -> None:
        # Cada fila es un dict propio: no se repite el mismo objeto en la lista.
        _, results = adapt(REPORT)
        self.assertEqual(len({id(row) for row in results}), len(results))

    def test_models_vacio_es_valido(self) -> None:
        run, results = adapt(variant(lambda r: r.update(models=[])))
        self.assertEqual(run, expected_run())
        self.assertEqual(results, [])
        self.assertIsInstance(results, list)

    def test_un_solo_modelo(self) -> None:
        _, results = adapt(only_model(1))
        self.assertEqual(results, model_rows(DEEPSEEK, 5, 4, 0.75, 10875.63, 0.0003567))

    def test_claves_desconocidas_del_nivel_superior_se_ignoran(self) -> None:
        def extend(report: dict) -> None:
            report["notes"] = [MARKER]
            report["results"] = {"cualquier": "cosa"}
            report["generated_at"] = "2030-01-01T00:00:00Z"
            report["extra_futuro"] = {"anidado": [1, 2, {"x": MARKER}]}

        self.assertEqual(adapt(variant(extend)), adapt(REPORT))

    def test_claves_desconocidas_del_modelo_se_ignoran(self) -> None:
        # `results`, `prompt_tokens`, `completion_tokens` y `notes` no se usan ni se copian.
        def extend(report: dict) -> None:
            for model in report["models"]:
                model["notes"] = MARKER
                model["prompt_tokens"] = 999999
                model["completion_tokens"] = 888888
                model["extra_futuro"] = {"x": [1, 2, 3]}

        self.assertEqual(adapt(variant(extend)), adapt(REPORT))

    def test_sin_results_ni_tokens_en_el_modelo(self) -> None:
        # Quitar lo que el adaptador no usa no cambia nada.
        def strip(report: dict) -> None:
            for model in report["models"]:
                for key in ("results", "prompt_tokens", "completion_tokens"):
                    model.pop(key)

        self.assertEqual(adapt(variant(strip)), adapt(REPORT))

    def test_el_orden_de_los_modelos_es_el_del_informe(self) -> None:
        # Las filas siguen el orden de `models`, no el alfabético ni el del alias.
        def reverse(report: dict) -> None:
            report["models"].reverse()

        _, results = adapt(variant(reverse))
        self.assertEqual(results, REAL_ROWS[5:] + REAL_ROWS[:5])
        self.assertEqual([r["behavior"] for r in results[::5]], [DEEPSEEK, CHAT])


class NoFreeTextTest(unittest.TestCase):
    """Ninguna cadena de la salida es texto libre."""

    def assert_identifiers(self, run: dict, results: list[dict]) -> None:
        for text in list(string_values(run)) + list(string_values(results)):
            with self.subTest(text=text[:40]):
                self.assertLessEqual(len(text), 80)
                self.assertNotIn(" ", text)
                self.assertTrue(tool.IDENTIFIER_RE.match(text), text)

    def test_informe_real_solo_lleva_identificadores(self) -> None:
        # benchmark, cases, keyword_score, latency_p95, cost, alias, casos, puntuacion, ms, usd, estados,
        # automatic, A y JUP-078 cumplen IDENTIFIER_RE.
        run, results = adapt(REPORT)
        self.assert_identifiers(run, results)

    def test_conjunto_exacto_de_cadenas_de_la_salida(self) -> None:
        # Lista cerrada: cualquier cadena nueva (un campo copiado de más) rompe esta igualdad.
        run, results = adapt(REPORT)
        self.assertEqual(set(string_values(run)), {RUN_ID, "JUP-078"})
        self.assertEqual(set(string_values(results)), {
            "A", "benchmark", "cases", "keyword_score", "latency_p95", "cost", CHAT, DEEPSEEK,
            "pass", "fail", "measured", "casos", "puntuacion", "ms", "usd", "automatic",
        })

    def test_texto_libre_inyectado_no_aparece_en_la_salida(self) -> None:
        # `error_type` y `notes` con espacios en un resultado por caso, y cadenas con espacios en claves
        # desconocidas del nivel superior y del modelo: nada de ello se copia.
        def inject(report: dict) -> None:
            report["notes"] = [MARKER]
            report["extra"] = MARKER
            model = report["models"][0]
            model["notes"] = MARKER
            model["extra"] = {"detalle": MARKER}
            model["results"][0]["error_type"] = MARKER
            model["results"][0]["notes"] = MARKER
            report["models"][1]["results"][4]["error_type"] = MARKER

        run, results = adapt(variant(inject))
        dumped = json.dumps([run, results], ensure_ascii=False)
        self.assertNotIn("Texto libre", dumped)
        self.assertNotIn(MARKER, dumped)
        self.assert_identifiers(run, results)

    def test_ni_los_resultados_por_caso_ni_los_tipos_de_error_se_copian(self) -> None:
        # `error_type` real (TimeoutError), los case_id y resolved_model parecen identificadores válidos,
        # pero no son filas del contrato: la salida no los trae.
        run, results = adapt(REPORT)
        dumped = json.dumps([run, results], ensure_ascii=False)
        for forbidden in ("TimeoutError", "cost-total", "largest-service", "percentage-change",
                          "missing-context", "finops-actions", "resolved_model", "case_id"):
            with self.subTest(text=forbidden):
                self.assertNotIn(forbidden, dumped)
        behaviors = {row["behavior"] for row in results}
        self.assertEqual(behaviors, {CHAT, DEEPSEEK})


if __name__ == "__main__":
    unittest.main()
