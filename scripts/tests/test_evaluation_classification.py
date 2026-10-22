"""Clasificación, comparabilidad y completitud del juicio de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.7, Red).

Contrato que se valida (cuatro piezas; `docs/validation/evaluation-dashboard.md`, secciones «Ejecuciones no
reales», «Evolución y comparabilidad» y «Juicio humano o automático»):

* (A) `classify_run(run) -> tuple[str, ...]`: los MOTIVOS por los que una ejecución no es real, como tupla en el
  orden fijo de `NON_REAL_REASONS = ("plantilla", "doble", "sintetica", "sin_modelo_verificado")`, sin repetidos;
  `()` si es real. Reglas: `plantilla` si `generation_model == "plantilla-sin-modelo"` (igualdad exacta, distingue
  mayúsculas); `doble` si `embedding_provider` o `embedding_alias` valen exactamente `mock`; `sintetica` si
  `synthetic is True`; `sin_modelo_verificado` si `source` es `JUP-070` o `JUP-071` y `generation_model` es None.
  Primero valida `run` con `validate_rows(run, [])` y deja propagar su `AdapterError`. No muta.
* (B) `comparability_key(run, reasons) -> str`: el sha256 (64 caracteres hexadecimales) del JSON canónico
  (`sort_keys`, separadores compactos, `ensure_ascii`, UTF-8) de la lista `[source, suite_version, suite_sha256,
  corpus_sha256, embedding_provider, embedding_alias, retrieval, generation_model, prompt_sha256, list(reasons)]`.
  No entran `run_id`, `run_at`, `commit`, `suite` ni `synthetic`. `reasons` inválido -> `AdapterError` `reasons: `.
* (C) `AUTOMATIC_METRICS` y `unclassified_metrics(catalogue=None) -> list[str]`: los identificadores del catálogo
  de JUP-067 que no están ni en `HUMAN_METRICS` ni en `AUTOMATIC_METRICS` (ordenados). Con el catálogo real, `[]`:
  es la prueba que avisa cuando el catálogo incorpora una métrica sin clasificar como humana o automática.
* (D) `classify_run_row(run) -> dict`: copia de `run` con `is_real`, `non_real_reasons` y `comparability_key`
  (`CLASSIFICATION_KEYS`) añadidas al final.

Decisiones donde la especificación admite más de una lectura (fijadas aquí; el coder debe respetarlas):

* `AUTOMATIC_METRICS` incluye `ACC-2` aunque `HUMAN_ROWS` declare humana su fila `judged`: la disjunción que se
  exige es solo entre `HUMAN_METRICS` y `AUTOMATIC_METRICS` (métricas enteras); la fila `judged` es una excepción
  por fila, no por métrica.
* `comparability_key` solo valida `reasons`; no vuelve a validar `run` (eso lo hace `classify_run`).
* `reasons` admite tupla o lista; una cadena, un conjunto o un diccionario (iterables sin orden o que se
  confunden con una secuencia de letras) se rechazan.
* `unclassified_metrics` lee los identificadores de `catalogue["metrics"][i]["id"]` y devuelve una lista nueva.

Los valores esperados se escriben a mano. Los informes reales son los mismos que en
`test_evaluation_rows_contract.py` (JUP-070, JUP-078, JUP-022 y la salida REAL de
`node tools/business-metrics.mjs report docs/validation/JUP-068-example.json`, en `setUpModule`, sin skip).

Endurecimiento desde el principio (lección de la mutación de 2.1 a 2.6): una prueba por regla y por frontera de
la igualdad exacta (mayúsculas, sufijos, prefijos), `bool`/`None`/tipos, cada campo de la clave por separado,
valores `null` frente a la cadena `"null"`, intercambio de valores entre campos (que una concatenación no
distinguiría), el digest esperado calculado por la prueba con `hashlib` y `json` y un literal escrito a mano, y
determinismo entre procesos con semillas de hash distintas.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para
apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_classification", TOOL_PATH)
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
CATALOGUE_FILE = ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json"

# Valores literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
    "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
)
EXPECTED_REASONS = ("plantilla", "doble", "sintetica", "sin_modelo_verificado")
CLASSIFICATION_KEYS = ("is_real", "non_real_reasons", "comparability_key")
# Los nueve campos de la ejecución que entran en la clave, en el orden del contrato.
KEY_FIELDS = (
    "source", "suite_version", "suite_sha256", "corpus_sha256", "embedding_provider", "embedding_alias",
    "retrieval", "generation_model", "prompt_sha256",
)
# Los que admiten None en `rows-v1` (todos salvo `source`, que es obligatorio).
NULLABLE_KEY_FIELDS = tuple(field for field in KEY_FIELDS if field != "source")
# Campos que NO forman parte de la clave: identifican o describen la ejecución, no su comparabilidad.
OUT_OF_KEY_CHANGES = (
    ("run_id", "otro-identificador"), ("run_at", "2030-01-01T00:00:00Z"), ("commit", "0" * 40),
    ("suite", "JUP-999"), ("synthetic", True),
)
AUTOMATIC_IDS = (
    "ACC-2", "REL-1", "REL-2", "REL-3", "REL-4", "GRD-1", "GRD-2", "GRD-3", "LAT-1", "LAT-2", "LAT-3", "LAT-4",
    "STR-1", "STR-2", "AVL-1",
)
HUMAN_IDS = ("ACC-1", "ACC-3")

# Informes reales y salida real de Node; los fija `setUpModule`.
REPORTS: dict = {}
RUNS: dict = {}


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
    # Las ejecuciones se obtienen con los adaptadores ya validados en tareas anteriores (2.2 a 2.5).
    RUNS["070-1"] = tool.adapt_jup070(REPORTS["070-1"], "id-070-1")[0]
    RUNS["070-2"] = tool.adapt_jup070(REPORTS["070-2"], "id-070-2")[0]
    RUNS["078"] = tool.adapt_jup078(REPORTS["078"], "id-078")[0]
    RUNS["022"] = tool.adapt_jup022(REPORTS["022"], "id-022")[0]
    RUNS["068"] = tool.adapt_jup068(REPORTS["068"], "id-068")[0]


# --- Auxiliares de datos ------------------------------------------------------------------------------------

def good_run(**changes) -> dict:
    """Ejecución mínima válida: solo `run_id`, `source` y `synthetic`; lo demás es None."""
    run = {key: None for key in RUN_KEYS}
    run.update(run_id="clasif-1", source="JUP-070", synthetic=False)
    run.update(changes)
    return run


def real_run(**changes) -> dict:
    """Ejecución REAL con todos los campos rellenos: modelo verificado, embeddings reales y no sintética."""
    run = good_run(
        run_at="2026-10-08T20:13:54Z", commit="b12b3c80d0954a1f1a7bd12fae31456f269cff52", suite="JUP-069",
        suite_version="1.0.0", suite_sha256="e1" * 32, corpus_sha256="cf" * 32, embedding_provider="litellm",
        embedding_alias="economicon-embedding",
        retrieval={"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
        generation_model="modelo-verificado", prompt_sha256="f" * 64, synthetic=False,
    )
    run.update(changes)
    return run


def expected_key(run: dict, reasons) -> str:
    """Clave esperada: el sha256 del JSON canónico de la lista del contrato, calculado aquí con la biblioteca."""
    payload = [run[field] for field in KEY_FIELDS] + [list(reasons)]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ClassificationTestCase(unittest.TestCase):
    def assert_rejected(self, call, *paths: str) -> None:
        # `AdapterError` (y no cualquier excepción) con el mensaje `<ruta>: <problema>`.
        with self.assertRaises(tool.AdapterError) as caught:
            call()
        message = str(caught.exception)
        self.assertTrue(any(message.startswith(f"{path}: ") and len(message) > len(path) + 2 for path in paths),
                        f"el mensaje {message!r} debe empezar por alguna de {paths!r} seguida de ': ' y un motivo")


# --- (A) Clasificación: constantes y casos reales ------------------------------------------------------------

class ReasonsConstantTest(ClassificationTestCase):
    def test_motivos_y_orden_fijo(self) -> None:
        # El orden de la tupla es el que ordena los motivos de cada ejecución y entra en la clave.
        self.assertEqual(tool.NON_REAL_REASONS, EXPECTED_REASONS)
        self.assertIsInstance(tool.NON_REAL_REASONS, tuple)

    def test_claves_de_clasificacion(self) -> None:
        self.assertEqual(tool.CLASSIFICATION_KEYS, CLASSIFICATION_KEYS)
        self.assertIsInstance(tool.CLASSIFICATION_KEYS, tuple)


class ClassifyRealReportsTest(ClassificationTestCase):
    """Los cinco informes reales dan los motivos que documenta «Ejecuciones no reales»."""

    def test_jup070_run_1_es_plantilla_y_doble(self) -> None:
        self.assertEqual(tool.classify_run(RUNS["070-1"]), ("plantilla", "doble"))

    def test_jup070_run_2_es_solo_plantilla(self) -> None:
        self.assertEqual(tool.classify_run(RUNS["070-2"]), ("plantilla",))

    def test_jup078_es_real(self) -> None:
        # El benchmark llama de verdad al gateway: no es sintético aunque sus casos sean preguntas públicas.
        self.assertEqual(tool.classify_run(RUNS["078"]), ())

    def test_jup022_es_real(self) -> None:
        self.assertEqual(tool.classify_run(RUNS["022"]), ())

    def test_jup068_ejemplo_es_sintetico(self) -> None:
        self.assertEqual(tool.classify_run(RUNS["068"]), ("sintetica",))

    def test_el_resultado_es_una_tupla(self) -> None:
        # Tupla (hashable e inmutable) también cuando está vacía: `()` y no `[]` ni None.
        for name in RUNS:
            with self.subTest(report=name):
                self.assertIs(type(tool.classify_run(RUNS[name])), tuple)


# --- (A) Clasificación: una regla cada vez -------------------------------------------------------------------

class ClassifyRulesTest(ClassificationTestCase):
    def test_ejecucion_real_sin_motivos(self) -> None:
        self.assertEqual(tool.classify_run(real_run()), ())
        self.assertEqual(tool.classify_run(real_run(source="JUP-071")), ())

    def test_plantilla_solo_con_el_nombre_exacto(self) -> None:
        self.assertEqual(tool.classify_run(real_run(generation_model="plantilla-sin-modelo")), ("plantilla",))
        # Igualdad exacta: mayúsculas, prefijo, sufijo y otra palabra NO son la plantilla.
        for value in ("Plantilla-Sin-Modelo", "PLANTILLA-SIN-MODELO", "plantilla-sin-modelo-2",
                      "x-plantilla-sin-modelo", "plantilla", "sin-modelo", "plantilla_sin_modelo"):
            with self.subTest(generation_model=value):
                self.assertEqual(tool.classify_run(real_run(generation_model=value)), ())

    def test_plantilla_no_depende_de_la_fuente(self) -> None:
        for source in ("JUP-070", "JUP-071", "JUP-078", "JUP-022", "JUP-068", "otra-fuente"):
            with self.subTest(source=source):
                run = real_run(source=source, generation_model="plantilla-sin-modelo")
                self.assertEqual(tool.classify_run(run), ("plantilla",))

    def test_doble_por_el_proveedor(self) -> None:
        self.assertEqual(tool.classify_run(real_run(embedding_provider="mock")), ("doble",))

    def test_doble_por_el_alias(self) -> None:
        self.assertEqual(tool.classify_run(real_run(embedding_alias="mock")), ("doble",))

    def test_doble_por_proveedor_y_alias_no_repite_el_motivo(self) -> None:
        self.assertEqual(tool.classify_run(real_run(embedding_provider="mock", embedding_alias="mock")), ("doble",))

    def test_doble_solo_con_el_nombre_exacto(self) -> None:
        # Igualdad exacta en ambos campos: ni mayúsculas, ni prefijo, ni sufijo.
        for value in ("Mock", "MOCK", "mock2", "mocks", "litellm-mock", "mock-embedding", "mo", "mockk"):
            for field in ("embedding_provider", "embedding_alias"):
                with self.subTest(field=field, value=value):
                    self.assertEqual(tool.classify_run(real_run(**{field: value})), ())

    def test_doble_con_un_campo_mock_y_el_otro_real(self) -> None:
        run = real_run(embedding_provider="mock", embedding_alias="economicon-embedding")
        self.assertEqual(tool.classify_run(run), ("doble",))
        run = real_run(embedding_provider="litellm", embedding_alias="mock")
        self.assertEqual(tool.classify_run(run), ("doble",))

    def test_sintetica_solo_con_true(self) -> None:
        self.assertEqual(tool.classify_run(real_run(synthetic=True)), ("sintetica",))
        self.assertEqual(tool.classify_run(real_run(synthetic=False)), ())

    def test_sin_modelo_verificado_en_las_fuentes_del_chat(self) -> None:
        for source in ("JUP-070", "JUP-071"):
            with self.subTest(source=source):
                run = real_run(source=source, generation_model=None)
                self.assertEqual(tool.classify_run(run), ("sin_modelo_verificado",))

    def test_sin_modelo_verificado_no_aplica_a_otras_fuentes(self) -> None:
        # JUP-078 trae varios modelos y no registra ninguno en `run`; JUP-022 y JUP-068 no son campañas sobre el
        # chat. El prefijo, el sufijo y las minúsculas tampoco son la fuente.
        for source in ("JUP-078", "JUP-022", "JUP-068", "jup-070", "JUP-0700", "JUP-07", "JUP-072", "x-JUP-070"):
            with self.subTest(source=source):
                run = real_run(source=source, generation_model=None)
                self.assertEqual(tool.classify_run(run), ())

    def test_sin_modelo_verificado_con_un_modelo_registrado_no_aplica(self) -> None:
        for source in ("JUP-070", "JUP-071"):
            with self.subTest(source=source):
                self.assertEqual(tool.classify_run(real_run(source=source, generation_model="modelo-verificado")),
                                 ())

    def test_fila_rows_v1_de_jup071_sin_modelo(self) -> None:
        # Una ejecución que llega por `rows-v1` (futuro informe de robustez) con el mínimo de campos.
        run, _ = tool.adapt_rows_v1({"contract_version": 1,
                                     "run": {"run_id": "robustez-1", "source": "JUP-071"},
                                     "results": []})
        self.assertEqual(tool.classify_run(run), ("sin_modelo_verificado",))

    def test_fila_rows_v1_de_jup071_con_modelo(self) -> None:
        run, _ = tool.adapt_rows_v1({"contract_version": 1,
                                     "run": {"run_id": "robustez-2", "source": "JUP-071",
                                             "generation_model": "modelo-verificado"},
                                     "results": []})
        self.assertEqual(tool.classify_run(run), ())


# --- (A) Clasificación: combinaciones y orden ----------------------------------------------------------------

class ClassifyCombinationsTest(ClassificationTestCase):
    def test_plantilla_doble_y_sintetica_en_el_orden_fijo(self) -> None:
        # Las claves se insertan AL REVÉS: el orden de la tupla es el del contrato, no el del dict.
        run = dict(reversed(list(real_run(generation_model="plantilla-sin-modelo", embedding_provider="mock",
                                          synthetic=True).items())))
        self.assertEqual(tool.classify_run(run), ("plantilla", "doble", "sintetica"))

    def test_doble_sintetica_y_sin_modelo_verificado(self) -> None:
        run = real_run(source="JUP-071", generation_model=None, embedding_alias="mock", synthetic=True)
        self.assertEqual(tool.classify_run(run), ("doble", "sintetica", "sin_modelo_verificado"))

    def test_pares(self) -> None:
        cases = (
            (dict(generation_model="plantilla-sin-modelo", synthetic=True), ("plantilla", "sintetica")),
            (dict(generation_model="plantilla-sin-modelo", embedding_provider="mock"), ("plantilla", "doble")),
            (dict(embedding_provider="mock", synthetic=True), ("doble", "sintetica")),
            (dict(generation_model=None, synthetic=True), ("sintetica", "sin_modelo_verificado")),
            (dict(generation_model=None, embedding_alias="mock"), ("doble", "sin_modelo_verificado")),
        )
        for changes, expected in cases:
            with self.subTest(changes=changes):
                self.assertEqual(tool.classify_run(real_run(**changes)), expected)

    def test_tabla_exhaustiva_de_combinaciones(self) -> None:
        # Todas las combinaciones de modelo (plantilla, verificado, ninguno), embeddings (reales, proveedor mock,
        # alias mock, ambos), síntesis y fuente. El esperado se obtiene con una tabla de reglas independiente de la
        # herramienta y se filtra siempre por el orden fijo de los motivos.
        models = {"plantilla": "plantilla-sin-modelo", "verificado": "modelo-verificado", "ninguno": None}
        embeddings = {"reales": ("litellm", "alias"), "proveedor": ("mock", "alias"), "alias": ("litellm", "mock"),
                      "ambos": ("mock", "mock")}
        for model_name, embedding_name, synthetic, source in itertools.product(
                models, embeddings, (False, True), ("JUP-070", "JUP-071", "JUP-078")):
            model = models[model_name]
            provider, alias = embeddings[embedding_name]
            present = {
                "plantilla": model_name == "plantilla",
                "doble": embedding_name != "reales",
                "sintetica": synthetic,
                "sin_modelo_verificado": model_name == "ninguno" and source in ("JUP-070", "JUP-071"),
            }
            expected = tuple(reason for reason in EXPECTED_REASONS if present[reason])
            with self.subTest(model=model_name, embeddings=embedding_name, synthetic=synthetic, source=source):
                run = real_run(source=source, generation_model=model, embedding_provider=provider,
                               embedding_alias=alias, synthetic=synthetic)
                self.assertEqual(tool.classify_run(run), expected)

    def test_sin_repetidos(self) -> None:
        run = real_run(generation_model="plantilla-sin-modelo", embedding_provider="mock", embedding_alias="mock",
                       synthetic=True)
        reasons = tool.classify_run(run)
        self.assertEqual(len(reasons), len(set(reasons)))
        self.assertEqual(reasons, ("plantilla", "doble", "sintetica"))


# --- (A) Clasificación: validación previa y pureza -----------------------------------------------------------

class ClassifyValidationTest(ClassificationTestCase):
    def test_run_que_no_es_un_objeto(self) -> None:
        for value in (None, [], "run", 1, True, ()):
            with self.subTest(run=value):
                self.assert_rejected(lambda: tool.classify_run(value), "run")

    def test_campo_invalido_se_propaga_con_la_ruta_de_validate_rows(self) -> None:
        # Un `commit` con espacios es un defecto de la ejecución: se informa con la ruta de la validación común,
        # aunque la ejecución sea por lo demás una plantilla.
        run = real_run(commit="con espacios", generation_model="plantilla-sin-modelo")
        self.assert_rejected(lambda: tool.classify_run(run), "run.commit")

    def test_clave_ausente_y_clave_desconocida(self) -> None:
        run = real_run()
        del run["prompt_sha256"]
        self.assert_rejected(lambda: tool.classify_run(run), "run.prompt_sha256")
        run = real_run()
        run["milestone"] = "x"
        self.assert_rejected(lambda: tool.classify_run(run), "run.milestone")

    def test_synthetic_no_booleano_se_rechaza_y_no_cuenta_como_true(self) -> None:
        # `1` y `"true"` son truthy: sin validar, un `if run["synthetic"]` los clasificaría como sintéticos.
        for value in (1, "true", None):
            with self.subTest(synthetic=value):
                self.assert_rejected(lambda: tool.classify_run(real_run(synthetic=value)), "run.synthetic")

    def test_retrieval_invalido(self) -> None:
        self.assert_rejected(lambda: tool.classify_run(real_run(retrieval=[])), "run.retrieval")

    def test_no_muta_la_ejecucion(self) -> None:
        run = real_run(generation_model="plantilla-sin-modelo", embedding_provider="mock", synthetic=True)
        before = copy.deepcopy(run)
        tool.classify_run(run)
        self.assertEqual(run, before)

    def test_no_muta_cuando_rechaza(self) -> None:
        run = real_run(commit="con espacios")
        before = copy.deepcopy(run)
        self.assert_rejected(lambda: tool.classify_run(run), "run.commit")
        self.assertEqual(run, before)


# --- (B) Clave de comparabilidad -----------------------------------------------------------------------------

HEX64 = re.compile(r"[0-9a-f]{64}")


class ComparabilityKeyShapeTest(ClassificationTestCase):
    def test_es_un_hexadecimal_de_64_caracteres(self) -> None:
        key = tool.comparability_key(real_run(), ())
        self.assertIs(type(key), str)
        self.assertRegex(key, HEX64)
        self.assertIsNotNone(HEX64.fullmatch(key))

    def test_digest_esperado_calculado_con_hashlib_y_json(self) -> None:
        run = real_run()
        for reasons in ((), ("plantilla",), ("plantilla", "doble", "sintetica"), EXPECTED_REASONS):
            with self.subTest(reasons=reasons):
                self.assertEqual(tool.comparability_key(run, reasons), expected_key(run, reasons))

    def test_digest_de_un_json_escrito_a_mano(self) -> None:
        # Fija el formato exacto del JSON canónico (orden de la lista, claves de `retrieval` ordenadas, separadores
        # compactos y `null`) con un texto literal independiente de `json.dumps` del test.
        run = good_run(suite_version="1.0.0", retrieval={"top_k": 4, "max_distance": 0.6})
        text = ('["JUP-070","1.0.0",null,null,null,null,{"max_distance":0.6,"top_k":4},null,null,'
                '["plantilla","doble"]]')
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(tool.comparability_key(run, ("plantilla", "doble")), expected)

    def test_literal_de_referencia(self) -> None:
        # Valor fijado a mano para una ejecución concreta: avisa de cualquier cambio en el formato de la clave,
        # que invalidaría la comparabilidad de las ejecuciones ya guardadas.
        text = ('["JUP-070","1.0.0","' + "e1" * 32 + '","' + "cf" * 32 + '","litellm","economicon-embedding",'
                '{"chunk_overlap":50,"chunk_size":500,"max_distance":0.6,"top_k":4},"modelo-verificado","'
                + "f" * 64 + '",[]]')
        self.assertEqual(tool.comparability_key(real_run(), ()), hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_none_se_serializa_como_null(self) -> None:
        run = good_run()
        text = '["JUP-070",null,null,null,null,null,null,null,null,[]]'
        self.assertEqual(tool.comparability_key(run, ()), hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_acepta_tupla_y_lista_de_motivos_con_la_misma_clave(self) -> None:
        run = real_run()
        self.assertEqual(tool.comparability_key(run, ("plantilla", "doble")),
                         tool.comparability_key(run, ["plantilla", "doble"]))


class ComparabilityKeyDeterminismTest(ClassificationTestCase):
    def test_misma_ejecucion_dos_veces(self) -> None:
        run = real_run()
        self.assertEqual(tool.comparability_key(run, ()), tool.comparability_key(run, ()))
        self.assertEqual(tool.comparability_key(run, ()), tool.comparability_key(copy.deepcopy(run), ()))

    def test_determinista_entre_procesos_con_semillas_de_hash_distintas(self) -> None:
        # `hash()` de una cadena cambia entre procesos (PYTHONHASHSEED): la clave que se guarda en la base y se
        # compara en otra ejecución no puede depender de él.
        code = (
            "import importlib.util, json, sys\n"
            "spec = importlib.util.spec_from_file_location('dashboard_tool_key', sys.argv[1])\n"
            "tool = importlib.util.module_from_spec(spec)\n"
            "sys.modules[spec.name] = tool\n"
            "spec.loader.exec_module(tool)\n"
            "run = json.loads(sys.argv[2])\n"
            "print(tool.comparability_key(run, ('plantilla', 'doble')))\n"
        )
        run = real_run()
        keys = set()
        for seed in ("1", "2", "12345"):
            env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"}
            completed = subprocess.run([sys.executable, "-c", code, str(TOOL_PATH), json.dumps(run)],
                                       capture_output=True, text=True, encoding="utf-8", timeout=60, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            keys.add(completed.stdout.strip())
        self.assertEqual(keys, {expected_key(run, ("plantilla", "doble"))})

    def test_no_muta_la_ejecucion_ni_los_motivos(self) -> None:
        run, reasons = real_run(), ["plantilla", "doble"]
        before = copy.deepcopy((run, reasons))
        tool.comparability_key(run, reasons)
        self.assertEqual((run, reasons), before)


class ComparabilityKeyFieldsTest(ClassificationTestCase):
    # Un valor alternativo válido por campo: cambia solo ese campo respecto de `real_run()`.
    ALTERNATIVES = {
        "source": "JUP-071",
        "suite_version": "2.0.0",
        "suite_sha256": "a2" * 32,
        "corpus_sha256": "b3" * 32,
        "embedding_provider": "otro-proveedor",
        "embedding_alias": "otro-alias",
        "retrieval": {"top_k": 5, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
        "generation_model": "otro-modelo",
        "prompt_sha256": "a" * 64,
    }

    def test_cada_campo_de_la_clave_la_cambia(self) -> None:
        base = tool.comparability_key(real_run(), ())
        self.assertEqual(set(self.ALTERNATIVES), set(KEY_FIELDS))
        for field in KEY_FIELDS:
            with self.subTest(field=field):
                self.assertNotEqual(tool.comparability_key(real_run(**{field: self.ALTERNATIVES[field]}), ()), base)

    def test_los_campos_fuera_de_la_clave_no_la_cambian(self) -> None:
        base = tool.comparability_key(real_run(), ())
        for field, value in OUT_OF_KEY_CHANGES:
            with self.subTest(field=field):
                self.assertNotEqual(real_run()[field], value)  # guarda: el cambio es real
                self.assertEqual(tool.comparability_key(real_run(**{field: value}), ()), base)

    def test_los_campos_fuera_de_la_clave_no_la_cambian_con_motivos(self) -> None:
        reasons = ("plantilla", "doble")
        base = tool.comparability_key(real_run(), reasons)
        for field, value in OUT_OF_KEY_CHANGES:
            with self.subTest(field=field):
                self.assertEqual(tool.comparability_key(real_run(**{field: value}), reasons), base)

    def test_none_frente_a_un_valor_cambia_la_clave(self) -> None:
        base = tool.comparability_key(real_run(), ())
        for field in NULLABLE_KEY_FIELDS:
            with self.subTest(field=field):
                self.assertNotEqual(tool.comparability_key(real_run(**{field: None}), ()), base)

    def test_none_solo_es_igual_a_none(self) -> None:
        # Un campo null solo es igual a otro null: dos ejecuciones sin modelo comparten clave y una con modelo no.
        without_a = real_run(generation_model=None, prompt_sha256=None)
        without_b = real_run(generation_model=None, prompt_sha256=None, run_id="otra", commit="1" * 40)
        self.assertEqual(tool.comparability_key(without_a, ()), tool.comparability_key(without_b, ()))
        self.assertNotEqual(tool.comparability_key(without_a, ()),
                            tool.comparability_key(real_run(prompt_sha256=None), ()))

    def test_null_no_es_la_cadena_null(self) -> None:
        # «null», «None» y la cadena vacía no pueden confundirse con el valor ausente: `str(None)` o `or ""`.
        for field in NULLABLE_KEY_FIELDS:
            if field == "retrieval":
                continue
            none_key = tool.comparability_key(real_run(**{field: None}), ())
            for text in ("null", "None", "none"):
                with self.subTest(field=field, text=text):
                    self.assertNotEqual(tool.comparability_key(real_run(**{field: text}), ()), none_key)

    def test_los_valores_no_se_confunden_al_concatenarse(self) -> None:
        # `a` + `bc` frente a `ab` + `c`: la clave es una lista, no una concatenación de campos.
        first = real_run(suite_version="a", suite_sha256="bc")
        second = real_run(suite_version="ab", suite_sha256="c")
        self.assertNotEqual(tool.comparability_key(first, ()), tool.comparability_key(second, ()))
        first = real_run(embedding_provider="x", embedding_alias="yz")
        second = real_run(embedding_provider="xy", embedding_alias="z")
        self.assertNotEqual(tool.comparability_key(first, ()), tool.comparability_key(second, ()))

    def test_intercambiar_valores_entre_campos_cambia_la_clave(self) -> None:
        # La posición importa: el mismo valor en otro campo no es la misma ejecución.
        swaps = (("suite_sha256", "corpus_sha256", "a" * 64, "b" * 64),
                 ("embedding_provider", "embedding_alias", "uno", "dos"),
                 ("suite_sha256", "prompt_sha256", "a" * 64, "b" * 64),
                 ("suite_version", "generation_model", "1.0.0", "modelo-x"))
        for left, right, left_value, right_value in swaps:
            with self.subTest(fields=(left, right)):
                original = real_run(**{left: left_value, right: right_value})
                swapped = real_run(**{left: right_value, right: left_value})
                self.assertNotEqual(tool.comparability_key(original, ()), tool.comparability_key(swapped, ()))

    def test_el_orden_de_las_claves_de_retrieval_no_importa(self) -> None:
        ordered = {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50}
        reversed_ = dict(reversed(list(ordered.items())))
        self.assertEqual(list(reversed_), list(reversed(list(ordered))))  # guarda: el orden sí difiere
        self.assertEqual(tool.comparability_key(real_run(retrieval=ordered), ()),
                         tool.comparability_key(real_run(retrieval=reversed_), ()))

    def test_cada_valor_de_retrieval_cuenta(self) -> None:
        base = tool.comparability_key(real_run(), ())
        for key, value in (("top_k", 5), ("max_distance", 0.7), ("max_distance", None), ("chunk_size", 501),
                           ("chunk_overlap", 51), ("max_distance", 0)):
            with self.subTest(key=key, value=value):
                retrieval = {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50, key: value}
                self.assertNotEqual(tool.comparability_key(real_run(retrieval=retrieval), ()), base)

    def test_retrieval_ausente_vacio_o_con_nulos_son_distintos(self) -> None:
        keys = {
            tool.comparability_key(real_run(retrieval=None), ()),
            tool.comparability_key(real_run(retrieval={}), ()),
            tool.comparability_key(real_run(retrieval={"top_k": None}), ()),
            tool.comparability_key(real_run(retrieval={"top_k": 4}), ()),
        }
        self.assertEqual(len(keys), 4)


class ComparabilityKeyReasonsTest(ClassificationTestCase):
    def test_los_motivos_entran_en_la_clave(self) -> None:
        run = real_run()
        self.assertNotEqual(tool.comparability_key(run, ()), tool.comparability_key(run, ("plantilla",)))

    def test_cada_conjunto_de_motivos_da_una_clave_distinta(self) -> None:
        # Los 16 subconjuntos de los cuatro motivos, en el orden fijo, dan 16 claves distintas.
        subsets = [tuple(reason for reason, keep in zip(EXPECTED_REASONS, mask) if keep)
                   for mask in itertools.product((False, True), repeat=4)]
        keys = {tool.comparability_key(real_run(), subset) for subset in subsets}
        self.assertEqual(len(subsets), 16)
        self.assertEqual(len(keys), 16)

    def test_motivos_vacios_en_tupla_y_lista(self) -> None:
        self.assertEqual(tool.comparability_key(real_run(), ()), tool.comparability_key(real_run(), []))

    def test_motivos_invalidos(self) -> None:
        invalid = {
            "cadena": "plantilla",
            "cadena-vacia": "",
            "none": None,
            "numero": 1,
            "conjunto": {"plantilla"},
            "diccionario": {"plantilla": 1},
            "desconocido": ("desconocido",),
            "mayusculas": ("Plantilla",),
            "uno-valido-y-uno-desconocido": ("plantilla", "otro"),
            "duplicado": ("plantilla", "plantilla"),
            "duplicado-no-contiguo": ("plantilla", "doble", "plantilla"),
            "fuera-de-orden": ("doble", "plantilla"),
            "fuera-de-orden-al-final": ("plantilla", "sin_modelo_verificado", "sintetica"),
            "no-cadena": ("plantilla", 3),
            "none-dentro": (None,),
            "lista-anidada": (["plantilla"],),
        }
        for name, reasons in invalid.items():
            with self.subTest(case=name):
                self.assert_rejected(lambda: tool.comparability_key(real_run(), reasons), "reasons")

    def test_todos_los_motivos_en_orden_son_validos(self) -> None:
        self.assertEqual(tool.comparability_key(real_run(), EXPECTED_REASONS), expected_key(real_run(),
                                                                                              EXPECTED_REASONS))

    def test_el_error_de_motivos_no_muta_nada(self) -> None:
        run, reasons = real_run(), ["doble", "plantilla"]
        before = copy.deepcopy((run, reasons))
        self.assert_rejected(lambda: tool.comparability_key(run, reasons), "reasons")
        self.assertEqual((run, reasons), before)


class ComparabilityKeyRealReportsTest(ClassificationTestCase):
    def key(self, name: str) -> str:
        return tool.comparability_key(RUNS[name], tool.classify_run(RUNS[name]))

    def test_las_dos_ejecuciones_de_jup070_no_son_comparables(self) -> None:
        # Cambian el proveedor de embeddings (mock -> litellm), `max_distance` y los motivos (doble desaparece).
        self.assertNotEqual(self.key("070-1"), self.key("070-2"))

    def test_cada_diferencia_de_jup070_basta_por_si_sola(self) -> None:
        # Con los mismos motivos pasados a mano, el cambio de embeddings y de recuperación ya las distingue; con
        # los mismos campos pero motivos distintos, también.
        reasons = ("plantilla",)
        self.assertNotEqual(tool.comparability_key(RUNS["070-1"], reasons),
                            tool.comparability_key(RUNS["070-2"], reasons))
        aligned = {**RUNS["070-1"], "embedding_provider": RUNS["070-2"]["embedding_provider"],
                   "embedding_alias": RUNS["070-2"]["embedding_alias"], "retrieval": RUNS["070-2"]["retrieval"]}
        self.assertNotEqual(tool.comparability_key(aligned, ("plantilla", "doble")),
                            tool.comparability_key(RUNS["070-2"], ("plantilla",)))

    def test_la_misma_ejecucion_dos_veces(self) -> None:
        again = tool.adapt_jup070(copy.deepcopy(REPORTS["070-2"]), "otro-run-id")[0]
        self.assertEqual(self.key("070-2"), tool.comparability_key(again, tool.classify_run(again)))

    def test_las_cinco_ejecuciones_reales_tienen_claves_distintas(self) -> None:
        keys = {name: self.key(name) for name in RUNS}
        self.assertEqual(len(set(keys.values())), len(keys), keys)

    def test_jup022_con_otra_suite_version_no_es_comparable(self) -> None:
        # Hallazgo M1 de 2.4: la `suite_version` del informe de calibración es la de la batería de su `bank`;
        # un informe con otra versión de la batería no se puede comparar con el actual.
        report = copy.deepcopy(REPORTS["022"])
        report["bank"]["suite_version"] = report["bank"]["suite_version"] + ".1"
        other = tool.adapt_jup022(report, "otro-id")[0]
        self.assertNotEqual(other["suite_version"], RUNS["022"]["suite_version"])
        self.assertNotEqual(tool.comparability_key(other, tool.classify_run(other)), self.key("022"))

    def test_jup022_con_la_misma_batería_y_otro_identificador_es_comparable(self) -> None:
        other = tool.adapt_jup022(copy.deepcopy(REPORTS["022"]), "otro-id")[0]
        self.assertEqual(tool.comparability_key(other, tool.classify_run(other)), self.key("022"))


# --- (C) Completitud de la tabla de juicio humano frente al catálogo ----------------------------------------

def real_catalogue() -> dict:
    return json.loads(CATALOGUE_FILE.read_text(encoding="utf-8"))


def catalogue_with(*extra_ids: str, drop: tuple[str, ...] = ()) -> dict:
    """Copia del catálogo real con métricas añadidas (con los campos mínimos) y otras quitadas."""
    catalogue = copy.deepcopy(real_catalogue())
    catalogue["metrics"] = [metric for metric in catalogue["metrics"] if metric["id"] not in drop]
    for metric_id in extra_ids:
        catalogue["metrics"].append({"id": metric_id, "family": "accuracy", "name": "Métrica nueva", "unit": "tasa"})
    return catalogue


class JudgmentCompletenessTest(ClassificationTestCase):
    def test_conjuntos_declarados(self) -> None:
        self.assertIsInstance(tool.AUTOMATIC_METRICS, frozenset)
        self.assertEqual(tool.AUTOMATIC_METRICS, frozenset(AUTOMATIC_IDS))
        self.assertEqual(tool.HUMAN_METRICS, frozenset(HUMAN_IDS))

    def test_humanas_y_automaticas_son_disjuntas(self) -> None:
        self.assertEqual(tool.HUMAN_METRICS & tool.AUTOMATIC_METRICS, frozenset())

    def test_la_union_es_exactamente_el_catalogo(self) -> None:
        # Ni falta ninguna métrica del catálogo ni sobra una que el catálogo no tenga.
        ids = {metric["id"] for metric in real_catalogue()["metrics"]}
        self.assertEqual(tool.HUMAN_METRICS | tool.AUTOMATIC_METRICS, ids)
        self.assertEqual(len(ids), len(HUMAN_IDS) + len(AUTOMATIC_IDS))

    def test_con_el_catalogo_real_no_queda_nada_sin_clasificar(self) -> None:
        self.assertEqual(tool.unclassified_metrics(), [])
        self.assertEqual(tool.unclassified_metrics(real_catalogue()), [])

    def test_devuelve_una_lista(self) -> None:
        self.assertIs(type(tool.unclassified_metrics()), list)

    def test_una_metrica_nueva_se_reporta(self) -> None:
        self.assertEqual(tool.unclassified_metrics(catalogue_with("XYZ-1")), ["XYZ-1"])

    def test_varias_metricas_nuevas_salen_ordenadas(self) -> None:
        # Se añaden en desorden: la salida está ordenada por identificador, no en el orden del catálogo.
        self.assertEqual(tool.unclassified_metrics(catalogue_with("ZZZ-9", "AAA-1", "XYZ-1")),
                         ["AAA-1", "XYZ-1", "ZZZ-9"])

    def test_una_metrica_con_prefijo_de_una_clasificada_se_reporta(self) -> None:
        # `ACC-10` no es `ACC-1`: la clasificación es por identificador exacto, no por prefijo.
        self.assertEqual(tool.unclassified_metrics(catalogue_with("ACC-10", "REL-5", "acc-1")),
                         ["ACC-10", "REL-5", "acc-1"])

    def test_un_catalogo_reducido_no_falla_aunque_falten_metricas_clasificadas(self) -> None:
        # `ACC-1` (humana) y `REL-1` (automática) están clasificadas pero no en el catálogo: no se reportan.
        self.assertEqual(tool.unclassified_metrics(catalogue_with(drop=("ACC-1", "REL-1"))), [])
        self.assertEqual(tool.unclassified_metrics(catalogue_with("XYZ-1", drop=("ACC-1", "REL-1"))), ["XYZ-1"])

    def test_catalogo_sin_metricas(self) -> None:
        catalogue = real_catalogue()
        catalogue["metrics"] = []
        self.assertEqual(tool.unclassified_metrics(catalogue), [])

    def test_no_muta_el_catalogo(self) -> None:
        catalogue = catalogue_with("ZZZ-9", "AAA-1")
        before = copy.deepcopy(catalogue)
        tool.unclassified_metrics(catalogue)
        self.assertEqual(catalogue, before)

    def test_el_catalogo_por_defecto_es_el_de_jup067(self) -> None:
        # Sin argumento, la herramienta lee el fichero de JUP-067 (`_load_catalogue`): si se sustituye la lectura
        # por un catálogo con una métrica nueva, se reporta. Se restaura siempre la función original.
        original = tool._load_catalogue
        tool._load_catalogue = lambda: catalogue_with("XYZ-1")
        try:
            self.assertEqual(tool.unclassified_metrics(), ["XYZ-1"])
        finally:
            tool._load_catalogue = original
        self.assertEqual(tool.unclassified_metrics(), [])


# --- (D) Columnas de clasificación de la tabla de ejecuciones -----------------------------------------------

class ClassifyRunRowTest(ClassificationTestCase):
    EXPECTED = {
        "070-1": (False, ["plantilla", "doble"]),
        "070-2": (False, ["plantilla"]),
        "078": (True, []),
        "022": (True, []),
        "068": (False, ["sintetica"]),
    }

    def test_los_cinco_informes_reales(self) -> None:
        for name, (is_real, reasons) in self.EXPECTED.items():
            with self.subTest(report=name):
                row = tool.classify_run_row(RUNS[name])
                self.assertIs(row["is_real"], is_real)
                self.assertEqual(row["non_real_reasons"], reasons)
                self.assertIs(type(row["non_real_reasons"]), list)
                self.assertEqual(row["comparability_key"], tool.comparability_key(RUNS[name], tuple(reasons)))

    def test_las_claves_son_las_de_la_ejecucion_mas_las_tres_nuevas_al_final(self) -> None:
        row = tool.classify_run_row(RUNS["070-2"])
        self.assertEqual(tuple(row), RUN_KEYS + CLASSIFICATION_KEYS)
        self.assertEqual(tuple(row)[-3:], CLASSIFICATION_KEYS)

    def test_conserva_los_valores_de_la_ejecucion(self) -> None:
        for name in RUNS:
            with self.subTest(report=name):
                row = tool.classify_run_row(RUNS[name])
                self.assertEqual({key: row[key] for key in RUN_KEYS}, RUNS[name])

    def test_is_real_es_booleano_estricto(self) -> None:
        self.assertIs(tool.classify_run_row(real_run())["is_real"], True)
        self.assertIs(tool.classify_run_row(real_run(synthetic=True))["is_real"], False)

    def test_ejecucion_real_con_motivos_vacios(self) -> None:
        row = tool.classify_run_row(real_run())
        self.assertEqual(row["non_real_reasons"], [])
        self.assertEqual(row["comparability_key"], expected_key(real_run(), ()))

    def test_ejecucion_con_los_tres_motivos(self) -> None:
        run = real_run(generation_model="plantilla-sin-modelo", embedding_provider="mock", synthetic=True)
        row = tool.classify_run_row(run)
        self.assertEqual(row["non_real_reasons"], ["plantilla", "doble", "sintetica"])
        self.assertEqual(row["comparability_key"], expected_key(run, ("plantilla", "doble", "sintetica")))
        self.assertIs(row["is_real"], False)

    def test_no_muta_ni_comparte_retrieval(self) -> None:
        run = real_run()
        before = copy.deepcopy(run)
        row = tool.classify_run_row(run)
        self.assertEqual(run, before)
        self.assertNotIn("is_real", run)
        self.assertIsNot(row, run)
        # Modificar `retrieval` de la salida no puede alterar la ejecución de entrada.
        self.assertIsNot(row["retrieval"], run["retrieval"])
        row["retrieval"]["top_k"] = 99
        self.assertEqual(run["retrieval"]["top_k"], 4)

    def test_no_comparte_los_motivos_entre_llamadas(self) -> None:
        first = tool.classify_run_row(real_run(synthetic=True))
        first["non_real_reasons"].append("otro")
        self.assertEqual(tool.classify_run_row(real_run(synthetic=True))["non_real_reasons"], ["sintetica"])

    def test_la_ejecucion_original_sigue_siendo_valida(self) -> None:
        # La fila clasificada es una copia ampliada: `run` no se contamina con las columnas nuevas y la validación
        # común la sigue aceptando (que `rows-v1` rechaza claves desconocidas es lo que obliga a la copia).
        for name in RUNS:
            with self.subTest(report=name):
                tool.classify_run_row(RUNS[name])
                self.assertIsNone(tool.validate_rows(RUNS[name], []))

    def test_ejecucion_invalida_se_rechaza_con_la_ruta(self) -> None:
        self.assert_rejected(lambda: tool.classify_run_row(real_run(commit="con espacios")), "run.commit")
        self.assert_rejected(lambda: tool.classify_run_row(None), "run")


if __name__ == "__main__":
    unittest.main()
