"""Adaptador de la calibración de la recuperación de JUP-022 de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.4, fase Red).

Contrato que se valida (`adapt_jup022(report, run_id) -> (run, results)`):

* Es una función PURA sobre el dict ya parseado: no lee ficheros, no lo muta y no comparte estructuras
  con él.
* `run` tiene EXACTAMENTE las claves de `RUN_KEYS`. `run_at` es `generated_at` copiado tal cual (debe
  parsear como ISO 8601); `suite` es `JUP-069` y `suite_version` la de `bank`; `corpus_sha256` es una
  huella DERIVADA (sha256 de las líneas `<clave>=<sha256>` ordenadas por clave y unidas con `\\n`, así que
  no depende del orden de las claves ni de las rutas); proveedor y alias salen de `provider`; `retrieval`
  lleva solo `chunk_size` y `chunk_overlap` (top_k y max_distance varían por punto y van en cada fila).
  `commit`, `suite_sha256`, `generation_model` y `prompt_sha256` quedan None; `synthetic` es False.
* Por cada punto del barrido, en el orden del informe, cinco filas: acierto de documento y de sección y
  resultado vacío de los casos `answer`, y acierto de documento y resultado vacío de los que no deben
  responder (`non_answer`). `behavior` = `top_k=<k>,max_distance=<md|none>`; `selected` es True si
  `(top_k, max_distance)` coincide con un candidato de `selection.candidates`.
* Reglas 1, 4 y 5 del contrato: las tasas se COPIAN; el numerador es `round(tasa * casos)` solo si
  reproduce la tasa del informe (que redondea a 4 decimales: tolerancia 5e-5), si no es None. Lo no
  medido es None con estado `not_measured` y conserva su denominador: tasa None, o denominador 0 (una
  tasa sobre cero casos es «sin datos», no un 0). Una tasa 0.0 con casos SÍ es una medición.
* Un informe de otra versión, de otra fuente o con la forma rota se rechaza con `AdapterError` cuyo
  mensaje EMPIEZA por `<campo>: `. No se copia texto libre ni rutas.

Los valores esperados salen del informe real (`docs/spikes/JUP-022-retrieval-calibration.json`) leído
con json/hashlib (actualizado tras integrar develop; antes eran literales), nunca llamando al adaptador. Las variantes se construyen con `copy.deepcopy` del
informe real o con constructores mínimos para que solo cambie el dato que se quiere probar.

Endurecimiento desde el principio (lección de la mutación de 2.1 a 2.3): bool frente a entero, NaN e
infinito, tolerancia del numerador con valores a ambos lados del límite, denominadores distintos por
fila para detectar mezclas, `max_distance` entero y None, prefijo EXACTO del mensaje de error.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL`
para apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup022", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REPORT_PATH = ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json"
REPORT = json.loads(REPORT_PATH.read_text(encoding="utf8"))

RUN_ID = "calibracion-recuperacion-1"

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
# Las cinco métricas de cada punto, en el orden del contrato.
METRICS = (
    "document_hit_answer", "section_hit_answer", "empty_answer",
    "document_hit_non_answer", "empty_non_answer",
)

MARKER = "Texto libre con espacios que no debe aparecer en la salida"

# Actualizado tras integrar develop: JUP-120 regeneró el informe de calibración (otra fecha, banco 1.0.1,
# otros hashes de corpus y otras tasas, que ahora también dependen de `top_k`). Los valores que vienen del
# informe real se LEEN de él (con json/hashlib, nunca con el adaptador) para que una nueva regeneración no
# obligue a reescribir las pruebas; lo que se mantiene fijo a mano son las anclas independientes del
# informe: la rejilla del barrido (28 puntos), los denominadores del banco (20, 20, 20, 8, 8), el
# troceado (500/50) y los formatos de huella de las pruebas con corpus construido a mano.
REAL_GENERATED_AT = REPORT["generated_at"]
REAL_SUITE_VERSION = REPORT["bank"]["suite_version"]


def _real_corpus_sha256() -> str:
    """Huella del corpus real calculada con hashlib de forma incremental (sin `corpus_hash` ni el adaptador)."""
    digest = hashlib.sha256()
    for position, key in enumerate(sorted(REPORT["corpus"])):
        if position:
            digest.update(b"\n")
        digest.update(f"{key}={REPORT['corpus'][key]['sha256']}".encode("utf-8"))
    return digest.hexdigest()


REAL_CORPUS_SHA256 = _real_corpus_sha256()

# Barrido real (28 puntos = top_k 3..6 x 7 distancias, en ese orden). Las tasas se leen de cada punto del
# informe (ver `real_point_spec`); los denominadores del banco son 20, 20, 20, 8 y 8 (casos `answer`,
# casos con sección, casos `answer`, casos `non_answer`, casos `non_answer`).
REAL_TOP_KS = (3, 4, 5, 6)
REAL_DISTANCES = (None, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75)
REAL_DENOMINATORS = (20, 20, 20, 8, 8)
# El candidato elegido por el informe real: la distancia 0.6 para cada top_k.
REAL_SELECTED = {(3, 0.6), (4, 0.6), (5, 0.6), (6, 0.6)}


def adapt(report, run_id: str = RUN_ID):
    return tool.adapt_jup022(report, run_id)


def behavior_of(top_k, max_distance) -> str:
    """Texto esperado de `behavior`, escrito a mano: `none` para None y el número tal cual si no."""
    return f"top_k={top_k},max_distance={'none' if max_distance is None else max_distance}"


def corpus_hash(corpus: dict) -> str:
    """Huella esperada del corpus, calculada con hashlib independientemente del adaptador."""
    lines = [f"{key}={corpus[key]['sha256']}" for key in sorted(corpus)]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def expected_run(**fields) -> dict:
    """`run` esperado del informe real; cada prueba puede sobrescribir lo que cambie."""
    run = {
        "run_id": RUN_ID, "source": "JUP-022", "run_at": REAL_GENERATED_AT, "commit": None,
        "suite": "JUP-069", "suite_version": REAL_SUITE_VERSION, "suite_sha256": None,
        "corpus_sha256": REAL_CORPUS_SHA256, "embedding_provider": "litellm",
        "embedding_alias": "economicon-embedding",
        "retrieval": {"chunk_size": 500, "chunk_overlap": 50},
        "generation_model": None, "prompt_sha256": None, "synthetic": False, "generation_model_id": None, "generation_provider": None, "generation_quantization": None, "gateway_config_sha256": None,
    }
    run.update(fields)
    return run


def expected_row(metric_id: str, behavior: str, value, denominator, numerator, selected: bool = False,
                 status: str = "measured") -> dict:
    """Fila esperada completa: todo lo no indicado es None salvo los valores fijos de la calibración."""
    row = {key: None for key in RESULT_KEYS}
    row.update(measure_type="A", grp="calibration", metric_id=metric_id, behavior=behavior,
               status=status, unit="tasa", judgment="automatic", selected=selected,
               value=value, denominator=denominator, numerator=numerator)
    return row


def no_data(metric_id: str, behavior: str, denominator, selected: bool = False) -> dict:
    """Fila no medida: value y numerator None (assertEqual distingue None de 0) y denominador conservado."""
    return expected_row(metric_id, behavior, None, denominator, None, selected, status="not_measured")


def point_rows(behavior: str, selected: bool, spec) -> list[dict]:
    """Cinco filas medidas desde `spec` = cinco tuplas (tasa, denominador, numerador)."""
    return [expected_row(metric, behavior, value, denominator, numerator, selected)
            for metric, (value, denominator, numerator) in zip(METRICS, spec)]


def real_point_spec(top_k, max_distance) -> list[tuple]:
    """Cinco tuplas `(tasa, denominador, numerador)` del punto real `(top_k, max_distance)`, en el orden de METRICS.

    Actualizado tras integrar develop: se leen las tasas del informe real (campo por campo, sin el
    adaptador) y el numerador es `round(tasa * casos)`; los denominadores se comparan con la ancla fija
    `REAL_DENOMINATORS` para que un cambio del banco no pase inadvertido.
    """
    matches = [p for p in REPORT["points"] if p["top_k"] == top_k and p["max_distance"] == max_distance]
    assert len(matches) == 1, (top_k, max_distance)
    answer, non_answer = matches[0]["answer"], matches[0]["non_answer"]
    values = (answer["document_hit_rate"], answer["section_hit_rate"], answer["empty_rate"],
              non_answer["document_hit_rate"], non_answer["empty_rate"])
    cases = (answer["cases"], answer["section_cases"], answer["cases"], non_answer["cases"], non_answer["cases"])
    assert cases == REAL_DENOMINATORS, (top_k, max_distance, cases)
    return [(value, denominator, round(value * denominator)) for value, denominator in zip(values, cases)]


def real_rows() -> list[dict]:
    rows = []
    for top_k in REAL_TOP_KS:
        for distance in REAL_DISTANCES:
            rows += point_rows(behavior_of(top_k, distance), (top_k, distance) in REAL_SELECTED,
                               real_point_spec(top_k, distance))
    return rows


def make_point(top_k=3, max_distance=0.6, a_cases=20, a_doc=0.9, a_empty=0.05, s_cases=20, a_sec=0.7,
               n_cases=8, n_doc=0.625, n_empty=0.0) -> dict:
    """Punto del barrido con la forma del informe real y valores personalizables."""
    return {
        "top_k": top_k, "max_distance": max_distance,
        "answer": {"cases": a_cases, "document_hit_rate": a_doc, "empty_rate": a_empty,
                   "section_cases": s_cases, "section_hit_rate": a_sec},
        "non_answer": {"cases": n_cases, "document_hit_rate": n_doc, "empty_rate": n_empty},
        "by_category": {"allocation": 1.0, "tagging": 0.6667},
    }


def make_candidate(top_k, max_distance) -> dict:
    return {"top_k": top_k, "max_distance": max_distance, "section_hit_rate": 0.7, "empty_rate": 0.05}


def make_report(points: list, candidates: list | None = None, **top_level) -> dict:
    """Informe real con otros puntos y candidatos (pares `(top_k, max_distance)`); lo demás intacto."""
    report = copy.deepcopy(REPORT)
    report["points"] = copy.deepcopy(points)
    report["selection"]["candidates"] = [make_candidate(k, d) for k, d in (candidates or [])]
    report.update(top_level)
    return report


def one_point(candidates: list | None = None, **fields) -> dict:
    """Informe con un único punto `(3, 0.6)` personalizado; por defecto ese punto es el seleccionado."""
    point = make_point(**fields)
    chosen = [(point["top_k"], point["max_distance"])] if candidates is None else candidates
    return make_report([point], chosen)


def variant(mutate, base: dict = REPORT) -> dict:
    """Copia profunda del informe con una modificación; el informe real nunca se toca."""
    report = copy.deepcopy(base)
    mutate(report)
    return report


def with_point(index: int, **fields) -> dict:
    """Informe real en el que el punto `index` cambia los campos de primer nivel indicados."""
    return variant(lambda r: r["points"][index].update(fields))


def with_answer(index: int, **fields) -> dict:
    return variant(lambda r: r["points"][index]["answer"].update(fields))


def with_non_answer(index: int, **fields) -> dict:
    return variant(lambda r: r["points"][index]["non_answer"].update(fields))


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
    """El bloque `run`, con huella de corpus derivada del informe."""

    def test_run_completo_del_informe_real(self) -> None:
        run, _ = adapt(REPORT)
        self.assertEqual(tuple(run), RUN_KEYS)
        self.assertEqual(run, {
            "run_id": RUN_ID,
            "source": "JUP-022",
            "run_at": REAL_GENERATED_AT,  # actualizado tras integrar develop: se lee del informe regenerado
            "commit": None,
            "suite": "JUP-069",
            "suite_version": REAL_SUITE_VERSION,  # actualizado tras integrar develop: banco 1.0.1
            "suite_sha256": None,
            "corpus_sha256": REAL_CORPUS_SHA256,
            "embedding_provider": "litellm",
            "embedding_alias": "economicon-embedding",
            "retrieval": {"chunk_size": 500, "chunk_overlap": 50},
            "generation_model": None,
            "prompt_sha256": None,
            "synthetic": False,
            "generation_model_id": None,
            "generation_provider": None,
            "generation_quantization": None,
            "gateway_config_sha256": None,
        })

    def test_run_id_es_el_argumento(self) -> None:
        run, _ = adapt(REPORT, "otro-id.v2")
        self.assertEqual(run, expected_run(run_id="otro-id.v2"))

    def test_run_at_es_generated_at_copiado_y_parsea_como_iso(self) -> None:
        run, _ = adapt(REPORT)
        self.assertIsInstance(run["run_at"], str)
        # Contrato con el resto de la carga: la cadena se puede parsear como fecha ISO 8601 con zona.
        self.assertIsNotNone(datetime.fromisoformat(run["run_at"]).tzinfo)

    def test_run_at_se_copia_sin_normalizar_la_zona(self) -> None:
        # Se copia tal cual: ni se convierte a UTC ni se reescribe el formato.
        run, _ = adapt(variant(lambda r: r.update(generated_at="2030-01-02T03:04:05+02:00")))
        self.assertEqual(run["run_at"], "2030-01-02T03:04:05+02:00")

    def test_corpus_sha256_calculado_con_hashlib_coincide_con_la_constante(self) -> None:
        # Doble comprobación de la constante del test: se recalcula aquí desde el JSON real con otra
        # construcción (`corpus_hash`, una sola llamada) distinta de la de la constante (incremental).
        # Actualizado tras integrar develop: la constante ya no es un literal del informe antiguo.
        self.assertEqual(corpus_hash(REPORT["corpus"]), REAL_CORPUS_SHA256)
        self.assertEqual(adapt(REPORT)[0]["corpus_sha256"], corpus_hash(REPORT["corpus"]))

    def test_corpus_sha256_no_depende_del_orden_de_las_claves(self) -> None:
        def reverse(report: dict) -> None:
            report["corpus"] = dict(reversed(list(report["corpus"].items())))

        shuffled = variant(reverse)
        self.assertNotEqual(list(shuffled["corpus"]), list(REPORT["corpus"]))
        self.assertEqual(adapt(shuffled)[0]["corpus_sha256"], REAL_CORPUS_SHA256)

    def test_corpus_sha256_cambia_si_cambia_el_sha_de_un_documento(self) -> None:
        # Cada uno de los cuatro documentos influye en la huella.
        for key in REPORT["corpus"]:
            with self.subTest(documento=key):
                changed = variant(lambda r, key=key: r["corpus"][key].update(sha256="0" * 64))
                value = adapt(changed)[0]["corpus_sha256"]
                self.assertEqual(value, corpus_hash(changed["corpus"]))
                self.assertNotEqual(value, REAL_CORPUS_SHA256)

    def test_corpus_sha256_no_depende_de_las_rutas(self) -> None:
        def repath(report: dict) -> None:
            for key, entry in report["corpus"].items():
                entry["path"] = f"otra/ruta/{key}.md"

        self.assertEqual(adapt(variant(repath))[0]["corpus_sha256"], REAL_CORPUS_SHA256)

    def test_corpus_sha256_formato_exacto_clave_igual_sha_sin_salto_final(self) -> None:
        # Un documento: una sola línea `<clave>=<sha>`, sin salto de línea final ni espacios.
        sha = "ab" * 32
        report = variant(lambda r: r.update(corpus={"rules": {"sha256": sha}}))
        self.assertEqual(adapt(report)[0]["corpus_sha256"],
                         hashlib.sha256(f"rules={sha}".encode("utf-8")).hexdigest())

    def test_corpus_sha256_ordena_por_clave_y_no_por_sha(self) -> None:
        # La clave `a` lleva el sha MAYOR y la `b` el menor: ordenar por sha o por valor daría otra huella.
        report = variant(lambda r: r.update(corpus={"b": {"sha256": "00" * 32}, "a": {"sha256": "ff" * 32}}))
        expected = hashlib.sha256(f"a={'ff' * 32}\nb={'00' * 32}".encode("utf-8")).hexdigest()
        self.assertEqual(adapt(report)[0]["corpus_sha256"], expected)

    def test_corpus_sha256_incluye_todas_las_entradas_no_solo_las_cuatro_conocidas(self) -> None:
        # Se deriva de TODAS las entradas del informe, sea cual sea su número.
        def extend(report: dict) -> None:
            report["corpus"]["zeta"] = {"path": "x.md", "sha256": "12" * 32}

        report = variant(extend)
        self.assertEqual(adapt(report)[0]["corpus_sha256"], corpus_hash(report["corpus"]))
        self.assertNotEqual(adapt(report)[0]["corpus_sha256"], REAL_CORPUS_SHA256)

    def test_corpus_sha256_es_hexadecimal_de_64_caracteres(self) -> None:
        value = adapt(REPORT)[0]["corpus_sha256"]
        self.assertEqual(len(value), 64)
        self.assertEqual(value, value.lower())
        int(value, 16)

    def test_retrieval_solo_trae_el_troceado_y_es_una_copia(self) -> None:
        run, _ = adapt(REPORT)
        self.assertEqual(run["retrieval"], {"chunk_size": 500, "chunk_overlap": 50})
        # `chunks` (52) y los parametros por punto no entran en el run.
        self.assertEqual(set(run["retrieval"]), {"chunk_size", "chunk_overlap"})

    def test_retrieval_sigue_los_valores_del_informe(self) -> None:
        # Valores distintos de los reales y distintos entre sí: tamaño y solape no se intercambian.
        report = variant(lambda r: r["chunking"].update(size=300, overlap=0))
        self.assertEqual(adapt(report)[0]["retrieval"], {"chunk_size": 300, "chunk_overlap": 0})

    def test_proveedor_alias_y_version_siguen_al_informe(self) -> None:
        def change(report: dict) -> None:
            report["provider"].update(name="mock", alias="alias-x")
            report["bank"]["suite_version"] = "2.3.1"

        run, _ = adapt(variant(change))
        self.assertEqual((run["embedding_provider"], run["embedding_alias"], run["suite_version"]),
                         ("mock", "alias-x", "2.3.1"))
        self.assertEqual(run["suite"], "JUP-069")

    def test_campos_no_registrados_son_none_y_synthetic_false(self) -> None:
        run, _ = adapt(REPORT)
        for key in ("commit", "suite_sha256", "generation_model", "prompt_sha256"):
            with self.subTest(campo=key):
                self.assertIsNone(run[key])
        self.assertIs(run["synthetic"], False)


class RealReportRowsTest(unittest.TestCase):
    """Normalización completa del informe real: 28 puntos x 5 filas."""

    def setUp(self) -> None:
        _, self.results = adapt(REPORT)

    def test_numero_de_filas(self) -> None:
        self.assertEqual(len(REPORT["points"]), 28)
        self.assertEqual(len(self.results), 140)

    def test_filas_completas_y_en_orden(self) -> None:
        # Igualdad de lista completa contra la tabla escrita a mano: orden de puntos, orden de las cinco
        # métricas, valores, denominadores, numeradores y `selected`.
        self.assertEqual(self.results, real_rows())

    def test_orden_exacto_de_puntos_y_metricas(self) -> None:
        order = [(row["behavior"], row["metric_id"]) for row in self.results]
        expected = [(behavior_of(k, d), metric) for k in REAL_TOP_KS for d in REAL_DISTANCES
                    for metric in METRICS]
        self.assertEqual(order, expected)

    def test_primer_punto_sin_umbral(self) -> None:
        # top_k=3 sin distancia máxima: las cinco filas del primer punto del informe, sin `selected`.
        # Actualizado tras integrar develop: las tasas (antes 0.95/0.75/0.0/0.75/0.0) se leen del informe
        # regenerado por JUP-120; se mantiene el orden de métricas, los denominadores 20/20/20/8/8 y que
        # el punto no es candidato.
        behavior = "top_k=3,max_distance=none"
        self.assertEqual(self.results[:5], [
            expected_row(metric, behavior, value, denominator, numerator)
            for metric, (value, denominator, numerator) in zip(METRICS, real_point_spec(3, None))
        ])
        self.assertEqual({row["selected"] for row in self.results[:5]}, {False})

    def test_punto_candidato_top_k_4_distancia_0_6(self) -> None:
        # Es el punto de índice 10 (top_k 4 empieza en el 7 y la distancia 0.6 es la cuarta): filas 50 a 54. Es candidato, así que `selected` es True.
        # Actualizado tras integrar develop: tasas leídas del informe regenerado (antes 0.9/0.7/0.05/0.625/0.0).
        behavior = "top_k=4,max_distance=0.6"
        rows = [row for row in self.results if row["behavior"] == behavior]
        self.assertEqual(rows, [
            expected_row(metric, behavior, value, denominator, numerator, selected=True)
            for metric, (value, denominator, numerator) in zip(METRICS, real_point_spec(4, 0.6))
        ])
        self.assertEqual(self.results[50:55], rows)

    def test_punto_con_umbral_estricto_top_k_5_distancia_0_5(self) -> None:
        # Umbral muy estricto: casi todo vacío (con 0.5 los vacíos de `answer` superan a los aciertos de
        # documento por sección y los de `non_answer` son la mayoría).
        # Actualizado tras integrar develop: tasas leídas del informe regenerado (antes 0.45/0.3/0.55/0.125/0.75).
        behavior = "top_k=5,max_distance=0.5"
        rows = [row for row in self.results if row["behavior"] == behavior]
        self.assertEqual(rows, [
            expected_row(metric, behavior, value, denominator, numerator)
            for metric, (value, denominator, numerator) in zip(METRICS, real_point_spec(5, 0.5))
        ])
        # El comentario original aludía a vacíos 11/20 y 6/8: se conserva la comprobación de que el
        # umbral estricto es el que más vacíos produce en `answer` de todo el barrido de ese top_k.
        empty_rates = [real_point_spec(5, d)[2][0] for d in REAL_DISTANCES]
        self.assertEqual(max(empty_rates), real_point_spec(5, 0.5)[2][0])

    def test_veinte_filas_seleccionadas_y_el_resto_no(self) -> None:
        # Cuatro candidatos x cinco filas. Se comprueba el conjunto exacto de comportamientos.
        selected = [row for row in self.results if row["selected"]]
        self.assertEqual(len(selected), 20)
        self.assertEqual({row["behavior"] for row in selected},
                         {"top_k=3,max_distance=0.6", "top_k=4,max_distance=0.6",
                          "top_k=5,max_distance=0.6", "top_k=6,max_distance=0.6"})
        for row in self.results:
            self.assertIs(type(row["selected"]), bool)
        self.assertEqual(sum(1 for row in self.results if row["selected"] is False), 120)

    def test_todas_medidas_con_numerador_reconstruido(self) -> None:
        # En el informe real todas las tasas reproducen un entero: numerador siempre presente.
        for row in self.results:
            with self.subTest(behavior=row["behavior"], metric=row["metric_id"]):
                self.assertEqual(row["status"], "measured")
                self.assertIsInstance(row["numerator"], int)
                self.assertIsNotNone(row["value"])
                self.assertEqual(row["numerator"], round(row["value"] * row["denominator"]))

    def test_claves_unidades_grp_juicio_y_campos_sin_uso(self) -> None:
        for row in self.results:
            with self.subTest(behavior=row["behavior"], metric=row["metric_id"]):
                self.assertEqual(tuple(row), RESULT_KEYS)
                self.assertEqual(row["measure_type"], "A")
                self.assertEqual(row["grp"], "calibration")
                self.assertEqual(row["judgment"], "automatic")
                self.assertEqual(row["unit"], "tasa")
                for key in ("count", "ci_low", "ci_high"):
                    self.assertIsNone(row[key])

    def test_valores_leidos_del_json_en_disco(self) -> None:
        # Se compara con el JSON leído de nuevo del disco, no con el objeto ya cargado en el módulo.
        raw = json.loads(REPORT_PATH.read_text(encoding="utf8"))
        _, results = adapt(raw)
        for index, point in enumerate(raw["points"]):
            rows = results[index * 5:index * 5 + 5]
            answer, non_answer = point["answer"], point["non_answer"]
            with self.subTest(punto=index):
                self.assertEqual([r["value"] for r in rows], [
                    answer["document_hit_rate"], answer["section_hit_rate"], answer["empty_rate"],
                    non_answer["document_hit_rate"], non_answer["empty_rate"]])
                self.assertEqual([r["denominator"] for r in rows], [
                    answer["cases"], answer["section_cases"], answer["cases"],
                    non_answer["cases"], non_answer["cases"]])

    def test_tabla_de_esperados_coincide_con_el_json_real(self) -> None:
        # Guarda de la propia prueba: si el informe real se regenera, esta tabla escrita a mano debe
        # revisarse y el fallo apunta aquí en vez de a un adaptador correcto.
        points = [(p["top_k"], p["max_distance"]) for p in REPORT["points"]]
        self.assertEqual(points, [(k, d) for k in REAL_TOP_KS for d in REAL_DISTANCES])
        candidates = {(c["top_k"], c["max_distance"]) for c in REPORT["selection"]["candidates"]}
        self.assertEqual(candidates, REAL_SELECTED)

    def test_by_category_no_se_publica(self) -> None:
        # Las tasas por categoría no llevan denominador en el informe: no hay filas con sus nombres.
        dumped = json.dumps(self.results)
        for category in ("allocation", "anomalies", "budgets", "costs", "recommendations", "tagging"):
            with self.subTest(categoria=category):
                self.assertNotIn(category, dumped)


class NotMeasuredTest(unittest.TestCase):
    """Lo no medido es None con `not_measured` y conserva el denominador."""

    BEHAVIOR = "top_k=3,max_distance=0.6"

    def rows(self, **fields) -> list[dict]:
        _, results = adapt(one_point(**fields))
        return results

    def intact(self, results: list[dict], only: tuple[str, ...]) -> None:
        # Las filas cuyo metric_id no está en `only` son las del punto base, sin cambios.
        base = point_rows(self.BEHAVIOR, True, [(0.9, 20, 18), (0.7, 20, 14), (0.05, 20, 1),
                                                (0.625, 8, 5), (0.0, 8, 0)])
        for row, expected in zip(results, base):
            if row["metric_id"] not in only:
                self.assertEqual(row, expected)

    def test_punto_base_todo_medido(self) -> None:
        # Línea base de las demás pruebas de la clase.
        self.assertEqual(self.rows(), point_rows(self.BEHAVIOR, True, [
            (0.9, 20, 18), (0.7, 20, 14), (0.05, 20, 1), (0.625, 8, 5), (0.0, 8, 0)]))

    def test_cada_tasa_none_es_no_medida_con_su_denominador(self) -> None:
        cases = [
            ("document_hit_answer", {"a_doc": None}, 20),
            ("section_hit_answer", {"a_sec": None}, 20),
            ("empty_answer", {"a_empty": None}, 20),
            ("document_hit_non_answer", {"n_doc": None}, 8),
            ("empty_non_answer", {"n_empty": None}, 8),
        ]
        for metric, fields, denominator in cases:
            with self.subTest(metric=metric):
                results = self.rows(**fields)
                index = METRICS.index(metric)
                self.assertEqual(results[index], no_data(metric, self.BEHAVIOR, denominator, True))
                for key in ("value", "numerator", "count", "ci_low", "ci_high"):
                    self.assertIsNone(results[index][key])
                self.intact(results, (metric,))

    def test_todas_las_tasas_none_son_no_medidas(self) -> None:
        results = self.rows(a_doc=None, a_sec=None, a_empty=None, n_doc=None, n_empty=None)
        self.assertEqual(results, [
            no_data("document_hit_answer", self.BEHAVIOR, 20, True),
            no_data("section_hit_answer", self.BEHAVIOR, 20, True),
            no_data("empty_answer", self.BEHAVIOR, 20, True),
            no_data("document_hit_non_answer", self.BEHAVIOR, 8, True),
            no_data("empty_non_answer", self.BEHAVIOR, 8, True),
        ])

    def test_tasa_cero_sobre_cero_casos_es_sin_datos_no_cero(self) -> None:
        # `answer.cases` = 0 con tasas presentes (incluso 0.0): sin casos no hay medición. Afecta a las
        # filas que usan `cases`; la de sección usa `section_cases` y sigue medida.
        results = self.rows(a_cases=0, a_doc=0.0, a_empty=0.0)
        self.assertEqual(results[0], no_data("document_hit_answer", self.BEHAVIOR, 0, True))
        self.assertEqual(results[2], no_data("empty_answer", self.BEHAVIOR, 0, True))
        self.assertEqual(results[1], expected_row("section_hit_answer", self.BEHAVIOR, 0.7, 20, 14, True))
        self.intact(results, ("document_hit_answer", "empty_answer"))

    def test_tasa_positiva_sobre_cero_casos_tambien_es_sin_datos(self) -> None:
        # Un informe incoherente (tasa 0.5 con 0 casos) no publica el valor: el denominador manda.
        results = self.rows(a_cases=0, a_doc=0.5, a_empty=0.5)
        self.assertEqual(results[0], no_data("document_hit_answer", self.BEHAVIOR, 0, True))
        self.assertEqual(results[2], no_data("empty_answer", self.BEHAVIOR, 0, True))

    def test_cero_section_cases_solo_afecta_a_la_fila_de_seccion(self) -> None:
        results = self.rows(s_cases=0, a_sec=0.0)
        self.assertEqual(results[1], no_data("section_hit_answer", self.BEHAVIOR, 0, True))
        self.intact(results, ("section_hit_answer",))

    def test_cero_casos_de_non_answer_afecta_a_sus_dos_filas(self) -> None:
        results = self.rows(n_cases=0, n_doc=0.0, n_empty=0.0)
        self.assertEqual(results[3], no_data("document_hit_non_answer", self.BEHAVIOR, 0, True))
        self.assertEqual(results[4], no_data("empty_non_answer", self.BEHAVIOR, 0, True))
        self.intact(results, ("document_hit_non_answer", "empty_non_answer"))

    def test_cero_en_todos_los_denominadores(self) -> None:
        results = self.rows(a_cases=0, s_cases=0, n_cases=0, a_doc=0.0, a_sec=0.0, a_empty=0.0,
                            n_doc=0.0, n_empty=0.0)
        self.assertEqual(results, [no_data(metric, self.BEHAVIOR, 0, True) for metric in METRICS])

    def test_tasa_cero_con_casos_es_una_medicion(self) -> None:
        # Contraste: 0.0 sobre 20 casos es una medición real (nada acertó) y no puede esconderse.
        results = self.rows(a_doc=0.0, a_sec=0.0, n_doc=0.0)
        for index in (0, 1, 3):
            with self.subTest(fila=METRICS[index]):
                self.assertEqual(results[index]["status"], "measured")
                self.assertEqual(results[index]["value"], 0.0)
                self.assertIs(type(results[index]["value"]), float)
                self.assertEqual(results[index]["numerator"], 0)
                self.assertIs(type(results[index]["numerator"]), int)
        self.assertEqual(results[0], expected_row("document_hit_answer", self.BEHAVIOR, 0.0, 20, 0, True))
        self.assertEqual(results[3], expected_row("document_hit_non_answer", self.BEHAVIOR, 0.0, 8, 0, True))

    def test_tasa_cero_entera_con_casos_es_medida_y_conserva_el_tipo(self) -> None:
        results = self.rows(a_empty=0, n_empty=0)
        self.assertEqual(results[2], expected_row("empty_answer", self.BEHAVIOR, 0, 20, 0, True))
        self.assertIs(type(results[2]["value"]), int)

    def test_tasa_uno_es_medida_con_todos_los_casos_de_numerador(self) -> None:
        results = self.rows(a_doc=1.0, a_sec=1, n_doc=1.0)
        self.assertEqual(results[0], expected_row("document_hit_answer", self.BEHAVIOR, 1.0, 20, 20, True))
        self.assertEqual(results[1], expected_row("section_hit_answer", self.BEHAVIOR, 1, 20, 20, True))
        self.assertEqual(results[3], expected_row("document_hit_non_answer", self.BEHAVIOR, 1.0, 8, 8, True))

    def test_no_medido_en_un_punto_no_contagia_a_los_demas(self) -> None:
        points = [make_point(3, 0.5, a_doc=None, a_cases=0), make_point(3, 0.6)]
        _, results = adapt(make_report(points, [(3, 0.6)]))
        self.assertEqual(results[0]["status"], "not_measured")
        self.assertEqual(results[5:], point_rows("top_k=3,max_distance=0.6", True, [
            (0.9, 20, 18), (0.7, 20, 14), (0.05, 20, 1), (0.625, 8, 5), (0.0, 8, 0)]))

    def test_tasa_que_no_reproduce_un_entero_es_medida_sin_numerador(self) -> None:
        # 0.5 sobre 3 casos no es ninguna fracción k/3: se copia la tasa y el numerador queda None.
        results = self.rows(a_doc=0.5, a_cases=3, a_empty=0.0, s_cases=3, a_sec=0.5)
        self.assertEqual(results[0], expected_row("document_hit_answer", self.BEHAVIOR, 0.5, 3, None, True))
        self.assertEqual(results[0]["status"], "measured")
        self.assertEqual(results[1], expected_row("section_hit_answer", self.BEHAVIOR, 0.5, 3, None, True))

    def test_tolerancia_de_redondeo_a_cuatro_decimales(self) -> None:
        # El informe redondea a 4 decimales: 1/3 se escribe 0.3333 (diferencia 3.3e-5, dentro de 5e-5) y
        # su numerador es 1; 0.3334 (diferencia 6.7e-5) ya no reproduce ningún entero.
        for rate, numerator in ((0.3333, 1), (0.6667, 2), (0.3334, None), (0.3332, None), (0.6666, None),
                                (0.6668, None)):
            with self.subTest(rate=rate):
                results = self.rows(a_doc=rate, a_cases=3)
                self.assertEqual(results[0],
                                 expected_row("document_hit_answer", self.BEHAVIOR, rate, 3, numerator, True))

    def test_numerador_se_redondea_al_entero_mas_cercano(self) -> None:
        # 0.3333 x 3 = 0.9999 -> 1 (un suelo daría 0) y 0.6667 x 3 = 2.0001 -> 2 (un techo daría 3).
        # 4/7 = 0.571428...: el informe escribe 0.5714 y el numerador es 4.
        self.assertEqual(self.rows(a_doc=0.5714, a_cases=7)[0]["numerator"], 4)
        self.assertEqual(self.rows(a_doc=0.2857, a_cases=7)[0]["numerator"], 2)
        self.assertEqual(self.rows(a_doc=0.1429, a_cases=7)[0]["numerator"], 1)

    def test_fraccion_cercana_a_un_entero_pero_fuera_de_tolerancia(self) -> None:
        # 0.1235 sobre 8 casos queda a 5e-4 de 1/8 = 0.125: no reproduce la tasa, sin numerador.
        results = self.rows(n_doc=0.1235)
        self.assertEqual(results[3], expected_row("document_hit_non_answer", self.BEHAVIOR, 0.1235, 8, None, True))

    def test_el_no_medido_no_altera_el_run(self) -> None:
        run, _ = adapt(one_point(a_doc=None))
        self.assertEqual(run, expected_run())


class HardeningTest(unittest.TestCase):
    """Casos que distinguen implementaciones incorrectas pero verosímiles (mutantes típicos)."""

    def test_max_distance_entero_se_escribe_sin_decimales(self) -> None:
        # `max_distance=1` (entero) es un número válido; `str(1)` es "1" y no "1.0".
        _, results = adapt(one_point(top_k=2, max_distance=1))
        self.assertEqual([row["behavior"] for row in results], ["top_k=2,max_distance=1"] * 5)
        self.assertTrue(all(row["selected"] for row in results))

    def test_max_distance_float_se_escribe_con_str(self) -> None:
        for distance, text in ((0.55, "0.55"), (0.5, "0.5"), (0.6, "0.6"), (1.0, "1.0"), (0.001, "0.001")):
            with self.subTest(distance=distance):
                _, results = adapt(one_point(max_distance=distance))
                self.assertEqual(results[0]["behavior"], f"top_k=3,max_distance={text}")

    def test_max_distance_none_se_escribe_none(self) -> None:
        _, results = adapt(one_point(max_distance=None))
        self.assertEqual({row["behavior"] for row in results}, {"top_k=3,max_distance=none"})
        self.assertTrue(all(row["selected"] for row in results))

    def test_dos_puntos_con_mismo_top_k_y_distinta_distancia_se_distinguen(self) -> None:
        points = [make_point(4, 0.5, a_doc=0.45, a_sec=0.3, a_empty=0.55),
                  make_point(4, 0.6, a_doc=0.9, a_sec=0.7, a_empty=0.05)]
        _, results = adapt(make_report(points, [(4, 0.6)]))
        self.assertEqual({row["behavior"] for row in results[:5]}, {"top_k=4,max_distance=0.5"})
        self.assertEqual({row["behavior"] for row in results[5:]}, {"top_k=4,max_distance=0.6"})
        self.assertEqual([row["selected"] for row in results], [False] * 5 + [True] * 5)
        self.assertEqual([row["value"] for row in results[:3]], [0.45, 0.3, 0.55])
        self.assertEqual([row["value"] for row in results[5:8]], [0.9, 0.7, 0.05])

    def test_dos_puntos_con_misma_distancia_y_distinto_top_k_se_distinguen(self) -> None:
        points = [make_point(3, 0.6), make_point(6, 0.6)]
        _, results = adapt(make_report(points, [(6, 0.6)]))
        self.assertEqual([row["selected"] for row in results], [False] * 5 + [True] * 5)

    def test_candidato_con_distancia_none_solo_selecciona_el_punto_sin_umbral(self) -> None:
        # (3, None) y (3, 0.6): el candidato (3, None) marca solo el primero, y a la inversa.
        points = [make_point(3, None), make_point(3, 0.6)]
        _, results = adapt(make_report(points, [(3, None)]))
        self.assertEqual([row["selected"] for row in results], [True] * 5 + [False] * 5)
        _, results = adapt(make_report(points, [(3, 0.6)]))
        self.assertEqual([row["selected"] for row in results], [False] * 5 + [True] * 5)

    def test_candidato_con_otro_top_k_no_marca_ningun_punto_con_el_mismo_umbral(self) -> None:
        # Mismo `max_distance` pero distinto `top_k`: no es el candidato.
        points = [make_point(3, 0.6), make_point(4, 0.6), make_point(5, 0.6)]
        _, results = adapt(make_report(points, [(4, 0.6)]))
        self.assertEqual([row["selected"] for row in results], [False] * 5 + [True] * 5 + [False] * 5)

    def test_varios_candidatos_marcan_varios_puntos(self) -> None:
        points = [make_point(3, 0.5), make_point(4, 0.6), make_point(5, None), make_point(6, 0.7)]
        _, results = adapt(make_report(points, [(3, 0.5), (5, None)]))
        self.assertEqual([row["selected"] for row in results],
                         [True] * 5 + [False] * 5 + [True] * 5 + [False] * 5)

    def test_sin_candidatos_no_hay_filas_seleccionadas(self) -> None:
        _, results = adapt(make_report([make_point(3, 0.6)], []))
        self.assertEqual([row["selected"] for row in results], [False] * 5)

    def test_denominadores_distintos_por_fila_no_se_mezclan(self) -> None:
        # cases 20, section_cases 17 y non_answer 9: cada fila usa su propio denominador.
        _, results = adapt(one_point(a_cases=20, s_cases=17, n_cases=9, a_doc=0.8, a_sec=0.4118,
                                     a_empty=0.15, n_doc=0.3333, n_empty=0.6667))
        self.assertEqual([row["denominator"] for row in results], [20, 17, 20, 9, 9])
        self.assertEqual([row["numerator"] for row in results], [16, 7, 3, 3, 6])
        self.assertEqual([row["value"] for row in results], [0.8, 0.4118, 0.15, 0.3333, 0.6667])

    def test_cada_fila_toma_su_propia_tasa_sin_cruces(self) -> None:
        # Cinco tasas distintas: un cruce entre documento/sección o answer/non_answer lo delata.
        _, results = adapt(one_point(a_doc=0.1, a_sec=0.2, a_empty=0.3, n_doc=0.4, n_empty=0.5,
                                     a_cases=10, s_cases=10, n_cases=10))
        self.assertEqual([(row["metric_id"], row["value"], row["numerator"]) for row in results], [
            ("document_hit_answer", 0.1, 1), ("section_hit_answer", 0.2, 2), ("empty_answer", 0.3, 3),
            ("document_hit_non_answer", 0.4, 4), ("empty_non_answer", 0.5, 5)])

    def test_puntos_con_valores_distintos_no_se_mezclan(self) -> None:
        points = [
            make_point(3, 0.5, a_cases=10, a_doc=0.1, s_cases=10, a_sec=0.2, a_empty=0.3, n_cases=10,
                       n_doc=0.4, n_empty=0.5),
            make_point(5, None, a_cases=4, a_doc=0.25, s_cases=2, a_sec=0.5, a_empty=0.75, n_cases=5,
                       n_doc=0.2, n_empty=0.6),
            make_point(4, 0.7, a_cases=8, a_doc=0.875, s_cases=6, a_sec=0.5, a_empty=0.0, n_cases=2,
                       n_doc=0.5, n_empty=1.0),
        ]
        _, results = adapt(make_report(points, [(5, None)]))
        self.assertEqual(results,
                         point_rows("top_k=3,max_distance=0.5", False,
                                    [(0.1, 10, 1), (0.2, 10, 2), (0.3, 10, 3), (0.4, 10, 4), (0.5, 10, 5)])
                         + point_rows("top_k=5,max_distance=none", True,
                                      [(0.25, 4, 1), (0.5, 2, 1), (0.75, 4, 3), (0.2, 5, 1), (0.6, 5, 3)])
                         + point_rows("top_k=4,max_distance=0.7", False,
                                      [(0.875, 8, 7), (0.5, 6, 3), (0.0, 8, 0), (0.5, 2, 1), (1.0, 2, 2)]))

    def test_el_orden_de_los_puntos_es_el_del_informe_no_el_numerico(self) -> None:
        points = [make_point(6, 0.7), make_point(3, None), make_point(4, 0.5)]
        _, results = adapt(make_report(points, []))
        self.assertEqual([row["behavior"] for row in results[::5]],
                         ["top_k=6,max_distance=0.7", "top_k=3,max_distance=none", "top_k=4,max_distance=0.5"])

    def test_orden_de_las_cinco_filas(self) -> None:
        _, results = adapt(one_point())
        self.assertEqual([row["metric_id"] for row in results], list(METRICS))

    def test_top_k_uno_y_distancia_minima_son_validos(self) -> None:
        # Fronteras inferiores válidas: top_k 1 y una distancia pequeña positiva.
        _, results = adapt(one_point(top_k=1, max_distance=0.0001))
        self.assertEqual(results[0]["behavior"], "top_k=1,max_distance=0.0001")

    def test_tasas_en_las_fronteras_0_y_1_son_validas(self) -> None:
        for rate in (0, 0.0, 1, 1.0):
            with self.subTest(rate=rate):
                _, results = adapt(one_point(a_doc=rate, a_sec=rate, a_empty=rate, n_doc=rate, n_empty=rate))
                self.assertEqual([row["value"] for row in results], [rate] * 5)

    def test_casos_cero_son_validos_en_los_tres_denominadores(self) -> None:
        _, results = adapt(one_point(a_cases=0, s_cases=0, n_cases=0))
        self.assertEqual(len(results), 5)

    def test_chunking_con_ceros_es_valido(self) -> None:
        run, _ = adapt(variant(lambda r: r["chunking"].update(size=0, overlap=0)))
        self.assertEqual(run["retrieval"], {"chunk_size": 0, "chunk_overlap": 0})

    def test_tasas_se_copian_sin_redondear(self) -> None:
        _, results = adapt(one_point(a_doc=0.8000000000000002, a_cases=10))
        self.assertEqual(repr(results[0]["value"]), "0.8000000000000002")


class ErrorsTest(unittest.TestCase):
    """AdapterError con «<campo>: <problema>»; el mensaje EMPIEZA por el campo."""

    def assert_error(self, report, field: str) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        # Formato del contrato: el mensaje empieza por el campo exacto y un separador, no solo lo contiene.
        self.assertTrue(message.startswith(f"{field}: "), message)

    def assert_error_any(self, report, *fields: str) -> None:
        # Para los subcampos de un candidato el contrato admite el prefijo del candidato o el del campo.
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        message = str(caught.exception)
        self.assertTrue(any(message.startswith(f"{field}: ") for field in fields), message)

    def test_error_es_value_error(self) -> None:
        with self.assertRaises(ValueError):
            adapt([])

    # --- Cabecera ---

    def test_report_no_es_objeto(self) -> None:
        for bad in ([], None, "informe", 3, [REPORT]):
            with self.subTest(bad=repr(bad)[:20]):
                self.assert_error(bad, "report")

    def test_schema_version_distinta_de_1(self) -> None:
        # Solo el entero 1 vale: True (que es 1 en Python), 1.0, "1" o None se rechazan.
        for bad in (2, 0, -1, True, "1", None, 1.0):
            with self.subTest(version=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(schema_version=bad)), "schema_version")

    def test_schema_version_ausente(self) -> None:
        self.assert_error(variant(lambda r: r.pop("schema_version")), "schema_version")

    def test_jup_distinto_de_jup_022(self) -> None:
        for bad in ("JUP-070", "jup-022", "JUP-022 ", None, 22, ""):
            with self.subTest(jup=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(jup=bad)), "jup")

    def test_jup_ausente(self) -> None:
        self.assert_error(variant(lambda r: r.pop("jup")), "jup")

    def test_generated_at_no_valido(self) -> None:
        for bad in (None, 5, "ayer", "", "2026-13-45T00:00:00+00:00", ["2026-10-03T07:15:32+00:00"], True):
            with self.subTest(generated_at=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(generated_at=bad)), "generated_at")

    def test_generated_at_ausente(self) -> None:
        self.assert_error(variant(lambda r: r.pop("generated_at")), "generated_at")

    # --- provider ---

    def test_provider_no_es_objeto_o_falta(self) -> None:
        for bad in (None, [], "litellm", 5):
            with self.subTest(provider=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(provider=bad)), "provider")
        self.assert_error(variant(lambda r: r.pop("provider")), "provider")

    def test_provider_name_no_valido(self) -> None:
        for bad in ("", 5, None, ["x"], True):
            with self.subTest(name=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["provider"].update(name=bad)), "provider.name")
        self.assert_error(variant(lambda r: r["provider"].pop("name")), "provider.name")

    def test_provider_alias_no_valido(self) -> None:
        for bad in ("", 5, None, ["x"], True):
            with self.subTest(alias=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["provider"].update(alias=bad)), "provider.alias")
        self.assert_error(variant(lambda r: r["provider"].pop("alias")), "provider.alias")

    # --- corpus ---

    def test_corpus_no_es_objeto_o_esta_vacio(self) -> None:
        for bad in (None, [], {}, "corpus", 5):
            with self.subTest(corpus=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(corpus=bad)), "corpus")
        self.assert_error(variant(lambda r: r.pop("corpus")), "corpus")

    def test_entrada_de_corpus_no_es_objeto(self) -> None:
        for bad in (None, [], "abc", 5):
            with self.subTest(entrada=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["corpus"].update(finops=bad)), "corpus.finops")

    def test_sha256_de_una_entrada_de_corpus_no_valido(self) -> None:
        for bad in ("", 5, None, ["x"], True):
            with self.subTest(sha256=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["corpus"]["finops"].update(sha256=bad)),
                                  "corpus.finops.sha256")
        for key in REPORT["corpus"]:
            with self.subTest(ausente=key):
                self.assert_error(variant(lambda r, key=key: r["corpus"][key].pop("sha256")),
                                  f"corpus.{key}.sha256")

    # --- bank y chunking ---

    def test_bank_no_es_objeto_o_falta(self) -> None:
        for bad in (None, [], "bank", 5):
            with self.subTest(bank=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(bank=bad)), "bank")
        self.assert_error(variant(lambda r: r.pop("bank")), "bank")

    def test_suite_version_no_valida(self) -> None:
        for bad in (None, 5, 1.0, True, ["1.0.0"]):
            with self.subTest(suite_version=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["bank"].update(suite_version=bad)),
                                  "bank.suite_version")
        self.assert_error(variant(lambda r: r["bank"].pop("suite_version")), "bank.suite_version")

    def test_chunking_no_es_objeto_o_falta(self) -> None:
        for bad in (None, [], "chunking", 5):
            with self.subTest(chunking=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(chunking=bad)), "chunking")
        self.assert_error(variant(lambda r: r.pop("chunking")), "chunking")

    def test_chunking_size_y_overlap_no_validos(self) -> None:
        for field in ("size", "overlap"):
            for bad in (True, False, 500.0, "500", -1, None, [5]):
                with self.subTest(field=field, bad=repr(bad)):
                    self.assert_error(variant(lambda r, f=field, b=bad: r["chunking"].update({f: b})),
                                      f"chunking.{field}")
            with self.subTest(field=field, ausente=True):
                self.assert_error(variant(lambda r, f=field: r["chunking"].pop(f)), f"chunking.{field}")

    # --- points ---

    def test_points_no_es_lista_o_falta(self) -> None:
        for bad in (None, {}, "puntos", 3, {"top_k": 3}):
            with self.subTest(points=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(points=bad)), "points")
        self.assert_error(variant(lambda r: r.pop("points")), "points")

    def test_punto_no_es_objeto(self) -> None:
        for bad in (None, [], 5, "punto"):
            with self.subTest(punto=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["points"].__setitem__(1, bad)), "points[1]")
        self.assert_error(variant(lambda r: r["points"].__setitem__(0, None)), "points[0]")

    def test_top_k_no_valido(self) -> None:
        for bad in (0, -1, True, False, 3.0, 3.5, "3", None, [3]):
            with self.subTest(top_k=repr(bad)):
                self.assert_error(with_point(1, top_k=bad), "points[1].top_k")
        self.assert_error(variant(lambda r: r["points"][1].pop("top_k")), "points[1].top_k")

    def test_max_distance_no_valida(self) -> None:
        for bad in (0, 0.0, -0.5, -1, "0.6", True, False, [], {}, float("nan"), float("inf"), float("-inf")):
            with self.subTest(max_distance=repr(bad)):
                self.assert_error(with_point(2, max_distance=bad), "points[2].max_distance")

    def test_max_distance_ausente_se_rechaza_pero_none_es_valida(self) -> None:
        # None significa «sin umbral» y es válido; la clave AUSENTE no (podría ser un informe incompleto).
        self.assert_error(variant(lambda r: r["points"][2].pop("max_distance")), "points[2].max_distance")
        _, results = adapt(make_report([make_point(3, 0.5), make_point(3, None)], []))
        self.assertEqual(results[5]["behavior"], "top_k=3,max_distance=none")

    def test_answer_y_non_answer_no_son_objetos(self) -> None:
        for key in ("answer", "non_answer"):
            for bad in (None, [], "x", 5):
                with self.subTest(key=key, bad=repr(bad)):
                    self.assert_error(with_point(1, **{key: bad}), f"points[1].{key}")
            with self.subTest(key=key, ausente=True):
                self.assert_error(variant(lambda r, k=key: r["points"][1].pop(k)), f"points[1].{key}")

    def test_casos_no_validos(self) -> None:
        for group, field in (("answer", "cases"), ("answer", "section_cases"), ("non_answer", "cases")):
            for bad in (True, False, 20.0, 5.5, "20", -1, None, [20]):
                with self.subTest(group=group, field=field, bad=repr(bad)):
                    report = variant(lambda r, g=group, f=field, b=bad: r["points"][2][g].update({f: b}))
                    self.assert_error(report, f"points[2].{group}.{field}")
            with self.subTest(group=group, field=field, ausente=True):
                report = variant(lambda r, g=group, f=field: r["points"][2][g].pop(f))
                self.assert_error(report, f"points[2].{group}.{field}")

    def test_tasas_no_validas(self) -> None:
        rates = (("answer", "document_hit_rate"), ("answer", "empty_rate"), ("answer", "section_hit_rate"),
                 ("non_answer", "document_hit_rate"), ("non_answer", "empty_rate"))
        bads = (-0.1, 1.5, 1.0000001, -1e-9, 2, -1, float("nan"), float("inf"), float("-inf"),
                True, False, "0.5", [], {})
        for group, field in rates:
            for bad in bads:
                with self.subTest(group=group, field=field, bad=repr(bad)):
                    report = variant(lambda r, g=group, f=field, b=bad: r["points"][0][g].update({f: b}))
                    self.assert_error(report, f"points[0].{group}.{field}")

    def test_tasa_ausente_se_rechaza_pero_none_es_valida(self) -> None:
        # Misma regla que max_distance: None es «no medido» y es válido; la clave ausente no.
        rates = (("answer", "document_hit_rate"), ("answer", "empty_rate"), ("answer", "section_hit_rate"),
                 ("non_answer", "document_hit_rate"), ("non_answer", "empty_rate"))
        for group, field in rates:
            with self.subTest(group=group, field=field):
                report = variant(lambda r, g=group, f=field: r["points"][0][g].pop(f))
                self.assert_error(report, f"points[0].{group}.{field}")
                valid = variant(lambda r, g=group, f=field: r["points"][0][g].update({f: None}))
                self.assertEqual(len(adapt(valid)[1]), 140)

    def test_non_answer_no_exige_campos_de_seccion(self) -> None:
        # El informe real no trae `section_cases` ni `section_hit_rate` en non_answer: no se piden.
        self.assertNotIn("section_cases", REPORT["points"][0]["non_answer"])
        self.assertEqual(len(adapt(REPORT)[1]), 140)

    def test_punto_repetido_apunta_al_segundo(self) -> None:
        def duplicate(report: dict) -> None:
            report["points"][2]["top_k"] = report["points"][0]["top_k"]
            report["points"][2]["max_distance"] = report["points"][0]["max_distance"]

        self.assert_error(variant(duplicate), "points[2]")

    def test_punto_repetido_sin_umbral(self) -> None:
        points = [make_point(3, None), make_point(4, 0.6), make_point(3, None)]
        self.assert_error(make_report(points, []), "points[2]")

    def test_mismo_top_k_con_distinta_distancia_no_es_repetido(self) -> None:
        _, results = adapt(make_report([make_point(3, 0.5), make_point(3, 0.6), make_point(3, None)], []))
        self.assertEqual(len(results), 15)

    def test_se_informa_del_primer_punto_defectuoso(self) -> None:
        def make(report: dict) -> None:
            report["points"][0]["top_k"] = 0
            report["points"][1]["top_k"] = 0

        self.assert_error(variant(make), "points[0].top_k")

    # --- selection ---

    def test_selection_no_es_objeto_o_falta(self) -> None:
        for bad in (None, [], "seleccion", 5):
            with self.subTest(selection=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r.update(selection=bad)), "selection")
        self.assert_error(variant(lambda r: r.pop("selection")), "selection")

    def test_selection_candidates_no_es_lista_o_falta(self) -> None:
        for bad in (None, {}, "candidatos", 5):
            with self.subTest(candidates=repr(bad)):
                self.assert_error(variant(lambda r, bad=bad: r["selection"].update(candidates=bad)),
                                  "selection.candidates")
        self.assert_error(variant(lambda r: r["selection"].pop("candidates")), "selection.candidates")

    def test_candidato_no_es_objeto(self) -> None:
        for bad in (None, [], 5, "candidato"):
            with self.subTest(candidato=repr(bad)):
                report = variant(lambda r, bad=bad: r["selection"]["candidates"].__setitem__(1, bad))
                self.assert_error(report, "selection.candidates[1]")

    def test_candidato_con_top_k_no_valido(self) -> None:
        for bad in (True, 3.0, "3", None, [3]):
            with self.subTest(top_k=repr(bad)):
                report = variant(lambda r, bad=bad: r["selection"]["candidates"][1].update(top_k=bad))
                self.assert_error_any(report, "selection.candidates[1]", "selection.candidates[1].top_k")
        report = variant(lambda r: r["selection"]["candidates"][1].pop("top_k"))
        self.assert_error_any(report, "selection.candidates[1]", "selection.candidates[1].top_k")

    def test_candidato_con_max_distance_no_valida(self) -> None:
        for bad in ("0.6", True, False, [], float("nan")):
            with self.subTest(max_distance=repr(bad)):
                report = variant(lambda r, bad=bad: r["selection"]["candidates"][2].update(max_distance=bad))
                self.assert_error_any(report, "selection.candidates[2]", "selection.candidates[2].max_distance")
        report = variant(lambda r: r["selection"]["candidates"][2].pop("max_distance"))
        self.assert_error_any(report, "selection.candidates[2]", "selection.candidates[2].max_distance")

    def test_candidato_sin_punto_correspondiente(self) -> None:
        # El candidato debe existir en el barrido; si no, el informe es incoherente.
        for top_k, distance in ((9, 0.6), (3, 0.6000001), (3, 0.99), (7, None)):
            with self.subTest(top_k=top_k, distance=distance):
                report = variant(lambda r, k=top_k, d=distance: r["selection"]["candidates"][1].update(
                    top_k=k, max_distance=d))
                self.assert_error(report, "selection.candidates[1]")

    def test_candidato_sin_punto_cuando_el_punto_existe_con_otra_distancia(self) -> None:
        # Un barrido sin punto sin umbral para top_k=3: el candidato (3, None) no corresponde a nada.
        points = [make_point(3, 0.5), make_point(3, 0.6)]
        self.assert_error(make_report(points, [(3, None)]), "selection.candidates[0]")

    def test_candidato_con_distancia_con_pero_punto_sin_umbral(self) -> None:
        points = [make_point(3, None)]
        self.assert_error(make_report(points, [(3, 0.6)]), "selection.candidates[0]")

    def test_error_no_devuelve_resultado_parcial(self) -> None:
        with self.assertRaises(tool.AdapterError):
            adapt(with_answer(27, cases="mal"))


class PurityTest(unittest.TestCase):
    """La función no muta la entrada, es determinista y tolera lo que no usa."""

    def test_no_muta_el_informe(self) -> None:
        candidate = copy.deepcopy(REPORT)
        adapt(candidate)
        self.assertEqual(candidate, REPORT)

    def test_no_muta_el_informe_con_no_medidos(self) -> None:
        report = one_point(a_doc=None, a_cases=0)
        before = copy.deepcopy(report)
        adapt(report)
        self.assertEqual(report, before)

    def test_dos_llamadas_dan_lo_mismo(self) -> None:
        first = adapt(REPORT)
        second = adapt(REPORT)
        self.assertEqual(first, second)
        # Y las salidas son independientes: mutar una no altera la otra ni una llamada posterior.
        first[1][0]["numerator"] = 999
        first[0]["run_id"] = "mutado"
        first[0]["retrieval"]["chunk_size"] = -1
        third = adapt(REPORT)
        # Actualizado tras integrar develop: el numerador de la primera fila ya no es el literal 19 de la
        # calibración antigua sino el que corresponde al informe real regenerado.
        self.assertEqual(third[1][0]["numerator"], real_point_spec(3, None)[0][2])
        self.assertNotEqual(third[1][0]["numerator"], 999)
        self.assertEqual(third[0]["run_id"], RUN_ID)
        self.assertEqual(third[0]["retrieval"], {"chunk_size": 500, "chunk_overlap": 50})

    def test_la_salida_no_comparte_estructuras_con_la_entrada(self) -> None:
        report = copy.deepcopy(REPORT)
        input_ids = {id(item) for item in containers(report)}
        run, results = adapt(report)
        for item in list(containers(run)) + list(containers(results)):
            self.assertNotIn(id(item), input_ids)
        for row in results:
            row["numerator"] = -1
            row["behavior"] = "mutada"
        run["retrieval"]["chunk_size"] = -1
        run["source"] = "mutada"
        self.assertEqual(report, REPORT)

    def test_las_filas_son_dicts_distintos(self) -> None:
        _, results = adapt(REPORT)
        self.assertEqual(len({id(row) for row in results}), len(results))

    def test_points_vacia_es_valida(self) -> None:
        # Sin puntos tampoco hay candidatos (un candidato sin punto es un error, probado aparte): el
        # resultado es el run y una lista vacía.
        run, results = adapt(make_report([], []))
        self.assertEqual(run, expected_run())
        self.assertEqual(results, [])
        self.assertIsInstance(results, list)

    def test_points_vacia_con_candidatos_es_error_por_candidato_sin_punto(self) -> None:
        # Sin barrido no puede haber candidato: el informe real con points vacía y 4 candidatos es incoherente.
        report = make_report([], [(3, 0.6)])
        with self.assertRaises(tool.AdapterError) as caught:
            adapt(report)
        self.assertTrue(str(caught.exception).startswith("selection.candidates[0]: "))

    def test_claves_desconocidas_se_ignoran(self) -> None:
        # labels, cases, gaps, limits, sweep, planned_calls, by_category, rutas y la regla de selección no
        # se usan ni se copian, y la salida es idéntica a la del informe sin ellas.
        def extend(report: dict) -> None:
            report["labels"] = [MARKER]
            report["cases"] = {"JUP-069-001": {"pregunta": MARKER}}
            report["gaps"] = [MARKER]
            report["limits"] = [MARKER]
            report["sweep"] = {"top_k": [99], "max_distance": [MARKER]}
            report["planned_calls"] = 123456
            report["extra_futuro"] = {"anidado": [1, 2, {"x": MARKER}]}
            report["corpus"]["rules"]["path"] = MARKER
            report["bank"]["path"] = MARKER
            report["provider"]["dimension"] = 99999
            report["chunking"]["chunks"] = 99999
            report["selection"]["rule"] = MARKER
            report["selection"]["min_hit_ratio"] = 0.123
            report["selection"]["candidates"][0]["section_hit_rate"] = 0.987
            for point in report["points"]:
                point["by_category"] = {"x": MARKER}
                point["extra"] = MARKER
                point["answer"]["extra"] = MARKER
                point["non_answer"]["extra"] = MARKER

        self.assertEqual(adapt(variant(extend)), adapt(REPORT))

    def test_sin_claves_opcionales_no_cambia_nada(self) -> None:
        def strip(report: dict) -> None:
            for key in ("labels", "cases", "gaps", "limits", "sweep", "planned_calls"):
                report.pop(key)
            for point in report["points"]:
                point.pop("by_category")
            report["selection"].pop("rule")
            report["bank"].pop("path")
            for entry in report["corpus"].values():
                entry.pop("path")

        self.assertEqual(adapt(variant(strip)), adapt(REPORT))


class NoFreeTextTest(unittest.TestCase):
    """Ninguna cadena de la salida es texto libre ni una ruta."""

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
            RUN_ID, "JUP-022", REAL_GENERATED_AT, "JUP-069", REAL_SUITE_VERSION, REAL_CORPUS_SHA256, "litellm",
            "economicon-embedding",
        })
        behaviors = {behavior_of(k, d) for k in REAL_TOP_KS for d in REAL_DISTANCES}
        self.assertEqual(set(string_values(results)), behaviors | {
            "A", "calibration", "measured", "tasa", "automatic", *METRICS,
        })

    def test_texto_libre_y_rutas_inyectados_no_aparecen_en_la_salida(self) -> None:
        def inject(report: dict) -> None:
            report["limits"] = [MARKER]
            report["gaps"] = [MARKER]
            report["labels"] = {"x": MARKER}
            report["corpus"]["rules"]["path"] = "docs/assistant-corpus/business-rules/" + MARKER
            report["bank"]["path"] = "docs/validation/" + MARKER
            report["selection"]["rule"] = MARKER

        run, results = adapt(variant(inject))
        dumped = json.dumps([run, results], ensure_ascii=False)
        self.assertNotIn("Texto libre", dumped)
        self.assertNotIn(MARKER, dumped)
        self.assert_identifiers(run, results)

    def test_ninguna_ruta_del_informe_aparece_en_la_salida(self) -> None:
        run, results = adapt(REPORT)
        dumped = json.dumps([run, results], ensure_ascii=False)
        for forbidden in ("docs/", ".md", ".json", "assistant-corpus", "JUP-069-questions"):
            with self.subTest(texto=forbidden):
                self.assertNotIn(forbidden, dumped)


if __name__ == "__main__":
    unittest.main()
