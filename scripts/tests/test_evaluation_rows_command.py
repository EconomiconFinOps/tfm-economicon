"""Normalización de una entrada del manifiesto y subcomando `rows` de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.8, Red).

Esta capa une todo lo anterior (manifiestos, adaptadores, validación común y clasificación) sin base de datos.
Contrato que se valida (`docs/validation/evaluation-dashboard.md`, secciones «Regenerar los datos», «Manifiesto» y
«Qué toma cada adaptador»):

* `DEFAULT_MANIFEST`, `DATASET_VERSION` y `RUN_OUTPUT_KEYS` (claves de la ejecución, las tres de clasificación y
  `format`, `milestone`, `report_path`, `report_sha256`, en ese orden).
* `derive_run_id(source, run_at, report_sha256)`: `<fuente en minúsculas>-<AAAAMMDDThhmmssZ en UTC o undated>-<8
  primeros hex>`.
* `report_digest(documento)`: sha256 del JSON canónico del documento YA PARSEADO, para que el `run_id` derivado
  sea igual en todas las máquinas (el fin de línea de un informe cambia con `autocrlf`).
* `normalize_entry(entry, root)`: `{"run": {...}, "results": [...]}` con el `run_id` explícito, el del informe o el
  derivado; una entrada sin filas es un error; `report_path` solo si el informe está dentro de `root` y su ruta es
  un identificador de ruta seguro; todo error sale como `AdapterError` prefijado por el fichero.
* `build_dataset(manifest_paths, root)`: `{"dataset_version": 1, "runs": [...]}` en el orden de los manifiestos,
  sin `run_id` repetidos y sin resultados parciales.
* `main(argv)` y la línea de comandos `rows [--manifest R]... [--no-versioned] [--output F] [--root D]`.

Decisiones donde la especificación admite más de una lectura (fijadas aquí; el coder debe respetarlas):

* Un `run_id` explícito repetido en dos manifiestos lo detecta ya `merge_manifests` con `ManifestError`, antes de
  normalizar nada. El error `run_id: ` de `build_dataset` (AdapterError) cubre las colisiones que `merge_manifests`
  no ve: la misma ejecución copiada a otro nombre (mismo contenido, mismo `run_id` derivado), dos `rows-v1` con el
  mismo `run_id` en el documento, o un `run_id` explícito que coincide con el de otra entrada. Para el caso
  explícito-en-dos-manifiestos solo se exige un `ValueError` que nombre el `run_id`.
* El mensaje de «ninguna fila» contiene la expresión `ninguna fila`.
* Los nombres con caracteres de control (`\\n`, ESC) dentro de un mensaje se escapan: el mensaje sale en una sola
  línea y sin secuencias de terminal. Las claves largas se truncan (como mucho 80 caracteres seguidos de la clave).
* La salida estándar es el JSON de `json.dumps(indent=2, ensure_ascii=True)` más un salto de línea; el fichero de
  `--output` lleva el mismo texto en UTF-8 sin BOM (el fin de línea de la plataforma no se exige: se normaliza).
* `main` devuelve 0 o 1; el código 2 de error de uso lo da `argparse` (se prueba por proceso real).
* La clasificación se calcula sobre el `run` crudo del adaptador (la clave de comparabilidad no usa `run_id`).

Los valores esperados se calculan en la prueba (hashlib, json y literales escritos a mano), no con la herramienta.
Se usan los ocho informes reales del manifiesto versionado (el de JUP-068 con Node real, en `setUpModule`) y
tmpdirs para todo lo demás: ninguna prueba toca el repositorio.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para
apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_command", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EVIDENCE = ROOT / "docs" / "evidence"
MANIFEST_FILE = ROOT / "docs" / "validation" / "evaluation-runs.json"
JUP_070_RUN_1 = EVIDENCE / "JUP-070-run-1-report.json"
JUP_070_RUN_2 = EVIDENCE / "JUP-070-run-2-report.json"
JUP_078_REPORT = EVIDENCE / "JUP-078-benchmark-results.json"
JUP_022_REPORT = ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json"
JUP_068_EXAMPLE = ROOT / "docs" / "validation" / "JUP-068-example.json"
JUP_130_DIR = EVIDENCE / "JUP-130"
JUP_130_REPORTS = tuple(JUP_130_DIR / f"JUP-130-{name}.rows.json" for name in ("anomalies", "data", "ai-cost"))

# Valores literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)
CLASSIFICATION_KEYS = ("is_real", "non_real_reasons", "comparability_key")
RUN_OUTPUT_KEYS = RUN_KEYS + CLASSIFICATION_KEYS + ("format", "milestone", "report_path", "report_sha256")

# Actualizado tras integrar develop: el informe de calibración de JUP-022 NO es evidencia congelada, lo regenera
# JUP-120 (nueva fecha, nuevo banco, nuevas tasas), así que su fecha, su huella y su `run_id` se derivan aquí del
# propio informe real, con json/hashlib/datetime y sin la herramienta: la huella es el sha256 del JSON canónico
# (ordenado, separadores compactos, ASCII) y el `run_id` es `jup-022-<aaaammddThhmmssZ en UTC>-<8 primeros hex>`.
# Los otros cuatro informes sí son evidencia fija y conservan sus literales, que siguen anclando el algoritmo de
# huella y el formato del `run_id`.
JUP_022_DOCUMENT = json.loads(JUP_022_REPORT.read_text(encoding="utf-8-sig"))
JUP_022_RUN_AT = JUP_022_DOCUMENT["generated_at"]
JUP_022_SHA = hashlib.sha256(json.dumps(JUP_022_DOCUMENT, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True).encode("utf-8")).hexdigest()
JUP_022_RUN_ID = "jup-022-{}-{}".format(
    datetime.fromisoformat(JUP_022_RUN_AT).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), JUP_022_SHA[:8])

def _canonical_sha(report_path):
    document = json.loads(report_path.read_text(encoding="utf-8-sig"))
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _jup130_case(report_path, source, run_id, rows, reasons):
    # Evidencia regenerable de JUP-130: la huella se calcula del propio fichero y el `run_id` es el del informe.
    return {
        "path": report_path, "format": "rows-v1", "source": source,
        "report_path": "docs/evidence/JUP-130/" + report_path.name,
        "run_id": run_id, "sha": _canonical_sha(report_path), "rows": rows, "reasons": reasons,
    }


# Ocho ejecuciones del manifiesto versionado, con lo esperado escrito a mano. Los `run_id` derivados y las huellas
# se fijaron a partir del JSON canónico de cada informe; no cambian mientras el informe (evidencia) no cambie.
# (La de JUP-022 es la excepción descrita arriba y se deriva del informe vigente.)
REAL_CASES = (
    {
        "path": JUP_070_RUN_1, "format": "jup-070-report-v1", "source": "JUP-070",
        "report_path": "docs/evidence/JUP-070-run-1-report.json",
        "run_id": "jup-070-20261008T201354Z-37175957",
        "sha": "371759579532d4789475da74317d3d18aa7bfa3b6b6a64760cc0a93f8f89e495",
        "rows": 48, "reasons": ["plantilla", "doble"],
    },
    {
        "path": JUP_070_RUN_2, "format": "jup-070-report-v1", "source": "JUP-070",
        "report_path": "docs/evidence/JUP-070-run-2-report.json",
        "run_id": "jup-070-20261008T210144Z-b64cca76",
        "sha": "b64cca76a96b62d518675b71209febfa28b96ed17a97f8334573830806fb1c53",
        "rows": 48, "reasons": ["plantilla"],
    },
    {
        "path": JUP_078_REPORT, "format": "jup-078-benchmark-v1", "source": "JUP-078",
        "report_path": "docs/evidence/JUP-078-benchmark-results.json",
        "run_id": "jup-078-undated-7ea00edf",
        "sha": "7ea00edf37c3266ab8d87c860488a4028a3200a60ab966db3feea0dd953c26a5",
        "rows": 10, "reasons": [],
    },
    {
        "path": JUP_022_REPORT, "format": "jup-022-calibration-v1", "source": "JUP-022",
        "report_path": "docs/spikes/JUP-022-retrieval-calibration.json",
        "run_id": JUP_022_RUN_ID,
        "sha": JUP_022_SHA,
        "rows": 140, "reasons": [],
    },
    {
        "path": JUP_068_EXAMPLE, "format": "jup-068-input-v1", "source": "JUP-068",
        "report_path": "docs/validation/JUP-068-example.json",
        "run_id": "JUP-068-synthetic-example-v1",
        "sha": "0d8641661c5b0f5df9b20c6a05c7ce104c1cd82f45821b159f4a77333dfd7834",
        "rows": 23, "reasons": ["sintetica"],
    },
    _jup130_case(JUP_130_REPORTS[0], "JUP-130-anomalies", "jup130-anomalies-2026-10-30", 16, ["sintetica"]),
    _jup130_case(JUP_130_REPORTS[1], "JUP-130-data", "jup130-data-2026-10-30", 10, ["sintetica"]),
    _jup130_case(JUP_130_REPORTS[2], "JUP-130-ai-cost", "jup130-ai-cost-2026-10-09-to-2026-10-21", 13, []),
)
REAL_RUN_IDS = [case["run_id"] for case in REAL_CASES]

# Informe de negocio de JUP-068 (salida de Node real sobre el ejemplo), fijado por `setUpModule`.
REPORT_068: dict = {}

# Documento `rows-v1` válido y mínimo (la robustez de JUP-071): una ejecución sin modelo de generación, así que la
# clasificación lo marca como no real por `sin_modelo_verificado`. Tres filas de tipo A, con `unit` y `judgment`.
ROWS_RUN = {
    "run_id": "JUP-071-demo-1", "source": "JUP-071", "run_at": "2026-10-10T09:00:00Z", "commit": "abc1234",
    "suite": "JUP-069", "suite_version": "JUP-069-v1", "retrieval": {"top_k": 4},
}
ROWS_DOCUMENT = {
    "contract_version": 1,
    "run": ROWS_RUN,
    "results": [
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "pass",
         "count": 3, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "fail",
         "count": 1, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-2", "behavior": "typo", "status": "measured",
         "value": 0.75, "unit": "tasa", "numerator": 3, "denominator": 4, "judgment": "automatic"},
    ],
}


def full_row(**fields) -> dict:
    # Fila con las 14 claves del contrato en orden: lo no declarado es None y `selected` es False.
    row = dict.fromkeys(RESULT_KEYS)
    row["selected"] = False
    row.update(fields)
    return row


EXPECTED_ROWS_RESULTS = [
    full_row(measure_type="A", grp="robustness", metric_id="ROB-1", behavior="typo", status="pass", count=3,
             unit="recuento", denominator=4, judgment="automatic"),
    full_row(measure_type="A", grp="robustness", metric_id="ROB-1", behavior="typo", status="fail", count=1,
             unit="recuento", denominator=4, judgment="automatic"),
    full_row(measure_type="A", grp="robustness", metric_id="ROB-2", behavior="typo", status="measured", value=0.75,
             unit="tasa", numerator=3, denominator=4, judgment="automatic"),
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_sha(document) -> str:
    # Huella esperada: sha256 del JSON canónico del documento parseado (implementada aparte de la herramienta).
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_key(run: dict, reasons: list) -> str:
    # Clave de comparabilidad según el contrato de 2.7: los nueve campos de configuración y los motivos.
    payload = [run[field] for field in (
        "source", "suite_version", "suite_sha256", "corpus_sha256", "embedding_provider", "embedding_alias",
        "retrieval", "generation_model", "prompt_sha256",
    )] + [list(reasons)]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_entry(path, fmt, milestone=True, run_id=None) -> dict:
    # Misma forma que devuelve `read_manifest`: `path` ya es un Path.
    path = Path(path)
    return {"path": path, "format": fmt, "milestone": milestone, "run_id": run_id,
            "manifest": path.parent / "manifiesto.json"}


def setUpModule() -> None:
    REPORT_068.update(tool.read_business_report(JUP_068_EXAMPLE))


class TmpCase(unittest.TestCase):
    """Base con un directorio temporal resuelto (en Windows el temporal puede traer nombres cortos 8.3)."""

    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name).resolve()

    def write(self, relative: str, document, *, indent=2, newline="\n", bom=False) -> Path:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(document, indent=indent, ensure_ascii=False).replace("\n", newline)
        path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        return path

    def write_manifest(self, relative: str, entries: list) -> Path:
        # Las rutas de `entries` se escriben tal cual (absolutas o relativas, según el caso).
        return self.write(relative, {"manifest_version": 1, "runs": entries})

    def normalize(self, path, fmt, *, root=None, milestone=True, run_id=None) -> dict:
        return tool.normalize_entry(make_entry(path, fmt, milestone, run_id), root=self.tmp if root is None else root)

    def normalize_error(self, path, fmt, *, root=None, run_id=None) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            self.normalize(path, fmt, root=root, run_id=run_id)
        return str(caught.exception)


# --- Constantes -------------------------------------------------------------------------------------------


class ConstantsTest(unittest.TestCase):
    def test_constantes_del_contrato(self) -> None:
        self.assertEqual(tool.DEFAULT_MANIFEST, tool.ROOT / "docs" / "validation" / "evaluation-runs.json")
        self.assertIsInstance(tool.DEFAULT_MANIFEST, Path)
        self.assertEqual(tool.DATASET_VERSION, 1)
        self.assertIs(type(tool.DATASET_VERSION), int)
        # Tupla (el orden es contrato), no lista ni conjunto.
        self.assertIsInstance(tool.RUN_OUTPUT_KEYS, tuple)
        self.assertEqual(tool.RUN_OUTPUT_KEYS, RUN_OUTPUT_KEYS)
        self.assertEqual(len(tool.RUN_OUTPUT_KEYS), 21)

    def test_la_raiz_por_defecto_es_root_en_las_dos_funciones(self) -> None:
        # Una raíz por defecto distinta (por ejemplo el directorio de trabajo) haría que el resultado dependiese
        # de desde dónde se ejecuta la herramienta.
        for function in (tool.normalize_entry, tool.build_dataset):
            with self.subTest(function=function.__name__):
                self.assertEqual(inspect.signature(function).parameters["root"].default, tool.ROOT)

    def test_main_acepta_argv_opcional(self) -> None:
        self.assertIsNone(inspect.signature(tool.main).parameters["argv"].default)


# --- derive_run_id ----------------------------------------------------------------------------------------


class DeriveRunIdTest(unittest.TestCase):
    def test_ejemplo_del_contrato(self) -> None:
        self.assertEqual(
            tool.derive_run_id("JUP-070", "2026-10-08T21:01:44Z", "ab" * 32), "jup-070-20261008T210144Z-abababab")

    def test_sin_fecha_es_undated(self) -> None:
        self.assertEqual(tool.derive_run_id("JUP-078", None, "cd" * 32), "jup-078-undated-cdcdcdcd")

    def test_fecha_con_fracciones_se_descarta_sin_redondear(self) -> None:
        # Las fracciones se truncan: .999999 NO sube al segundo siguiente.
        self.assertEqual(tool.derive_run_id("JUP-022", "2026-10-03T07:15:32.826486+00:00", "0123456789abcdef" * 4),
                         "jup-022-20261003T071532Z-01234567")
        self.assertEqual(tool.derive_run_id("JUP-022", "2026-10-03T07:15:32.999999Z", "0123456789abcdef" * 4),
                         "jup-022-20261003T071532Z-01234567")
        self.assertEqual(tool.derive_run_id("JUP-022", "2026-10-03T07:15:32.5Z", "0123456789abcdef" * 4),
                         "jup-022-20261003T071532Z-01234567")

    def test_el_desfase_se_convierte_a_utc(self) -> None:
        sha = "fedcba98" + "0" * 56
        cases = (
            ("2026-10-14T10:00:00-05:30", "20261014T153000Z"),   # desfase negativo: se suma
            ("2026-03-01T02:00:00+05:30", "20260228T203000Z"),   # positivo: se resta y cambia de día y de mes
            ("2026-12-31T23:30:00-01:00", "20270101T003000Z"),   # cruza el año
            ("2028-03-01T00:30:00+01:00", "20280229T233000Z"),   # año bisiesto
            ("2026-10-14T10:00:00+00:00", "20261014T100000Z"),
            ("2026-10-14T10:00:00Z", "20261014T100000Z"),
        )
        for run_at, stamp in cases:
            with self.subTest(run_at=run_at):
                self.assertEqual(tool.derive_run_id("JUP-070", run_at, sha), f"jup-070-{stamp}-fedcba98")

    def test_relleno_con_ceros_y_formato_compacto(self) -> None:
        self.assertEqual(tool.derive_run_id("JUP-070", "2026-01-02T03:04:05Z", "1" * 64), "jup-070-20260102T030405Z-11111111")
        self.assertEqual(tool.derive_run_id("JUP-070", "2026-10-08T00:00:00Z", "1" * 64), "jup-070-20261008T000000Z-11111111")

    def test_la_fuente_va_en_minusculas_y_se_conserva_el_resto(self) -> None:
        sha = "9" * 64
        self.assertEqual(tool.derive_run_id("JUP-071", None, sha), "jup-071-undated-99999999")
        self.assertEqual(tool.derive_run_id("Jup-071", None, sha), "jup-071-undated-99999999")
        self.assertEqual(tool.derive_run_id("jup-071", None, sha), "jup-071-undated-99999999")

    def test_toma_exactamente_los_ocho_primeros_caracteres_de_la_huella(self) -> None:
        sha = "12345678" + "9abcdef0" * 7
        result = tool.derive_run_id("JUP-070", None, sha)
        self.assertEqual(result, "jup-070-undated-12345678")
        self.assertIsInstance(result, str)

    def test_el_resultado_es_un_identificador_valido(self) -> None:
        result = tool.derive_run_id("JUP-070", "2026-10-08T21:01:44Z", "ab" * 32)
        self.assertRegex(result, r"^[A-Za-z0-9][A-Za-z0-9._:=,/+@-]{0,79}$")


# --- report_digest ----------------------------------------------------------------------------------------


class ReportDigestTest(unittest.TestCase):
    def test_literales_escritos_a_mano(self) -> None:
        # sha256 de los bytes `{"a":1,"b":[1,2]}` (separadores compactos, claves ordenadas) y del texto con las
        # no ASCII escapadas: calculados fuera de la herramienta.
        self.assertEqual(tool.report_digest({"b": [1, 2], "a": 1}),
                         "8baa73198470c7bb4c3ce142a8fd651affc0310d878bb9bd159e37a573fb4874")
        self.assertEqual(tool.report_digest({"é": "ñ"}),
                         "ddd2a360d6d915036a9c57fb80d90828faf2c23c553ff5901a3bb6a242f7cef3")
        self.assertEqual(tool.report_digest([]), "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945")

    def test_el_mismo_json_con_otro_formato_da_la_misma_huella(self) -> None:
        # CRLF frente a LF (autocrlf de Windows), otra sangría y otro orden de claves: el contenido es el mismo.
        document = {"z": {"y": [1, 2.5, None, True], "x": "ñ"}, "a": 1}
        variants = (
            json.dumps(document),
            json.dumps(document, indent=2),
            json.dumps(document, indent=4).replace("\n", "\r\n"),
            json.dumps(document, sort_keys=True, ensure_ascii=False),
            json.dumps(dict(reversed(list(document.items())))),
        )
        digests = {tool.report_digest(json.loads(text)) for text in variants}
        self.assertEqual(len(digests), 1, digests)
        self.assertEqual(digests, {canonical_sha(document)})

    def test_contenido_distinto_da_otra_huella(self) -> None:
        base = {"a": 1, "b": [1, 2]}
        seen = {tool.report_digest(base)}
        for other in ({"a": 2, "b": [1, 2]}, {"a": 1, "b": [2, 1]}, {"a": 1, "b": [1, 2], "c": 0},
                      {"a": 1.0, "b": [1, 2]}, {"a": True, "b": [1, 2]}, {"a": 1}, {"a": "1", "b": [1, 2]}):
            with self.subTest(other=other):
                digest = tool.report_digest(other)
                self.assertNotIn(digest, seen)
                seen.add(digest)

    def test_forma_de_la_huella_y_no_muta(self) -> None:
        document = {"b": {"d": [3, 1]}, "a": 1}
        snapshot = copy.deepcopy(document)
        digest = tool.report_digest(document)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(document, snapshot)
        self.assertEqual(list(document), ["b", "a"])


# --- normalize_entry con los ocho informes reales -----------------------------------------------------------


class NormalizeRealReportsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Una sola normalización por informe (la de JUP-068 ejecuta Node), compartida de solo lectura.
        cls.entries = tool.read_manifest(MANIFEST_FILE, root=ROOT)
        cls.normalized = [tool.normalize_entry(entry, root=ROOT) for entry in cls.entries]

    def test_el_manifiesto_versionado_lista_los_ocho_informes_en_orden(self) -> None:
        self.assertEqual([entry["path"] for entry in self.entries], [case["path"].resolve() for case in REAL_CASES])

    def test_forma_de_la_salida_y_orden_exacto_de_las_claves_de_run(self) -> None:
        for case, output in zip(REAL_CASES, self.normalized):
            with self.subTest(source=case["run_id"]):
                self.assertEqual(list(output), ["run", "results"])
                self.assertEqual(list(output["run"]), list(RUN_OUTPUT_KEYS))
                self.assertIsInstance(output["results"], list)

    def test_run_id_derivado_y_del_informe(self) -> None:
        self.assertEqual([output["run"]["run_id"] for output in self.normalized], REAL_RUN_IDS)
        # Todos distintos entre sí.
        self.assertEqual(len(set(REAL_RUN_IDS)), len(REAL_CASES))

    def test_huella_del_informe_parseado_y_report_path_relativo(self) -> None:
        for case, output in zip(REAL_CASES, self.normalized):
            with self.subTest(source=case["run_id"]):
                run = output["run"]
                self.assertEqual(run["report_sha256"], case["sha"])
                self.assertEqual(run["report_sha256"], canonical_sha(load_json(case["path"])))
                self.assertEqual(run["report_path"], case["report_path"])
                self.assertNotIn("\\", run["report_path"])

    def test_la_huella_de_jup_068_es_la_de_la_entrada_no_la_del_informe_de_node(self) -> None:
        run = self.normalized[4]["run"]
        self.assertEqual(run["report_sha256"], canonical_sha(load_json(JUP_068_EXAMPLE)))
        self.assertNotEqual(run["report_sha256"], canonical_sha(REPORT_068))

    def test_formato_y_hito_son_los_de_la_entrada(self) -> None:
        for case, output in zip(REAL_CASES, self.normalized):
            with self.subTest(source=case["run_id"]):
                self.assertEqual(output["run"]["format"], case["format"])
                self.assertIs(output["run"]["milestone"], True)

    def test_clasificacion_coherente_con_el_run_crudo(self) -> None:
        for case, output in zip(REAL_CASES, self.normalized):
            with self.subTest(source=case["run_id"]):
                run = output["run"]
                self.assertEqual(run["non_real_reasons"], case["reasons"])
                self.assertIsInstance(run["non_real_reasons"], list)
                self.assertIs(run["is_real"], not case["reasons"])
                self.assertEqual(run["comparability_key"], expected_key(run, case["reasons"]))
                self.assertRegex(run["comparability_key"], r"^[0-9a-f]{64}$")

    def test_las_ejecuciones_de_jup_070_tienen_claves_de_comparabilidad_distintas(self) -> None:
        # La documentación lo exige: cambian el proveedor de embeddings, `max_distance` y los motivos.
        self.assertNotEqual(self.normalized[0]["run"]["comparability_key"], self.normalized[1]["run"]["comparability_key"])

    def test_numero_de_filas(self) -> None:
        self.assertEqual([len(output["results"]) for output in self.normalized], [case["rows"] for case in REAL_CASES])

    def test_las_filas_son_las_del_adaptador_y_el_resto_del_run_tambien(self) -> None:
        raws = (
            tool.adapt_jup070(load_json(JUP_070_RUN_1), "x"),
            tool.adapt_jup070(load_json(JUP_070_RUN_2), "x"),
            tool.adapt_jup078(load_json(JUP_078_REPORT), "x"),
            tool.adapt_jup022(load_json(JUP_022_REPORT), "x"),
            tool.adapt_jup068(REPORT_068, "x"),
            *(tool.adapt_rows_v1(load_json(report), "x") for report in JUP_130_REPORTS),
        )
        for case, output, (raw_run, raw_results) in zip(REAL_CASES, self.normalized, raws):
            with self.subTest(source=case["run_id"]):
                self.assertEqual(output["results"], raw_results)
                for key in RUN_KEYS:
                    if key != "run_id":
                        self.assertEqual(output["run"][key], raw_run[key], key)

    def test_valores_de_fecha_y_modelo_de_los_informes_reales(self) -> None:
        runs = [output["run"] for output in self.normalized]
        self.assertEqual([run["run_at"] for run in runs], [
            "2026-10-08T20:13:54Z", "2026-10-08T21:01:44Z", None, JUP_022_RUN_AT, None,
            *(load_json(report)["run"]["run_at"] for report in JUP_130_REPORTS)])
        # Actualizado tras integrar develop: la fecha de la calibración (antes el literal
        # 2026-10-03T07:15:32.826486+00:00) es la `generated_at` del informe regenerado, copiada sin normalizar.
        self.assertEqual([run["generation_model"] for run in runs],
                         ["plantilla-sin-modelo", "plantilla-sin-modelo", None, None, None, None, None, None])

    def test_cada_salida_pasa_la_validacion_comun_y_serializa_a_json(self) -> None:
        for case, output in zip(REAL_CASES, self.normalized):
            with self.subTest(source=case["run_id"]):
                raw_run = {key: output["run"][key] for key in RUN_KEYS}
                tool.validate_rows(raw_run, output["results"])
                json.dumps(output, allow_nan=False)

    def test_dos_llamadas_no_comparten_estructuras_y_no_mutan_la_entrada(self) -> None:
        entry = self.entries[3]
        snapshot = copy.deepcopy(entry)
        first = tool.normalize_entry(entry, root=ROOT)
        second = tool.normalize_entry(entry, root=ROOT)
        self.assertEqual(entry, snapshot)
        self.assertEqual(first, second)
        self.assertIsNot(first["run"], second["run"])
        self.assertIsNot(first["results"], second["results"])
        self.assertIsNot(first["run"]["non_real_reasons"], second["run"]["non_real_reasons"])
        first["run"]["retrieval"]["chunk_size"] = -1
        first["results"][0]["count"] = -1
        first["run"]["non_real_reasons"].append("x")
        self.assertEqual(second, self.normalized[3])


# --- normalize_entry: opciones del manifiesto, rutas y formatos -------------------------------------------------


class NormalizeEntryOptionsTest(TmpCase):
    def test_un_run_id_explicito_sustituye_al_derivado(self) -> None:
        output = self.normalize(JUP_070_RUN_2, "jup-070-report-v1", root=ROOT, run_id="mi-ejecucion-1")
        reference = tool.normalize_entry(make_entry(JUP_070_RUN_2, "jup-070-report-v1"), root=ROOT)
        self.assertEqual(output["run"]["run_id"], "mi-ejecucion-1")
        # Solo cambia el identificador: huella, clasificación y filas son las mismas.
        self.assertEqual({k: v for k, v in output["run"].items() if k != "run_id"},
                         {k: v for k, v in reference["run"].items() if k != "run_id"})
        self.assertEqual(output["results"], reference["results"])
        self.assertEqual(list(output["run"]), list(RUN_OUTPUT_KEYS))

    def test_run_id_explicito_en_jup_078_y_jup_022(self) -> None:
        for case in (REAL_CASES[2], REAL_CASES[3]):
            with self.subTest(source=case["source"]):
                output = self.normalize(case["path"], case["format"], root=ROOT, run_id="explicito-9")
                self.assertEqual(output["run"]["run_id"], "explicito-9")

    def test_run_id_explicito_gana_al_del_informe_de_negocio(self) -> None:
        output = self.normalize(JUP_068_EXAMPLE, "jup-068-input-v1", root=ROOT, run_id="negocio-explicito")
        self.assertEqual(output["run"]["run_id"], "negocio-explicito")
        self.assertEqual(len(output["results"]), 23)

    def test_hito_falso_se_conserva_como_booleano(self) -> None:
        output = self.normalize(JUP_070_RUN_2, "jup-070-report-v1", root=ROOT, milestone=False)
        self.assertIs(output["run"]["milestone"], False)
        self.assertEqual(output["run"]["run_id"], "jup-070-20261008T210144Z-b64cca76")

    def test_fecha_con_desfase_deriva_el_run_id_en_utc(self) -> None:
        # Cableado de `derive_run_id`: la fecha del informe (con -05:30) pasa a UTC en el identificador, y la
        # huella entra completa: es la del informe modificado, no la del original.
        document = load_json(JUP_070_RUN_2)
        document["run"]["date"] = "2026-10-14T10:00:00-05:30"
        path = self.write("informe.json", document)
        output = self.normalize(path, "jup-070-report-v1")
        digest = canonical_sha(document)
        self.assertEqual(output["run"]["run_id"], f"jup-070-20261014T153000Z-{digest[:8]}")
        self.assertEqual(output["run"]["report_sha256"], digest)
        # `run_at` se copia tal cual del informe: no se normaliza a UTC.
        self.assertEqual(output["run"]["run_at"], "2026-10-14T10:00:00-05:30")

    def test_el_run_id_derivado_no_depende_del_formato_del_fichero(self) -> None:
        # Mismo contenido guardado con CRLF, sangría de 4 y las claves en otro orden: mismo run_id y misma huella.
        document = load_json(JUP_070_RUN_2)
        reordered = dict(reversed(list(document.items())))
        path = self.write("otro/formato.json", reordered, indent=4, newline="\r\n")
        output = self.normalize(path, "jup-070-report-v1")
        self.assertEqual(output["run"]["run_id"], "jup-070-20261008T210144Z-b64cca76")
        self.assertEqual(output["run"]["report_sha256"], REAL_CASES[1]["sha"])

    def test_un_contenido_distinto_cambia_el_run_id_derivado(self) -> None:
        document = load_json(JUP_078_REPORT)
        same = self.normalize(self.write("a.json", document), "jup-078-benchmark-v1")
        self.assertEqual(same["run"]["run_id"], "jup-078-undated-7ea00edf")
        document["models"][0]["p95_latency_ms"] = document["models"][0]["p95_latency_ms"] + 1
        other = self.normalize(self.write("b.json", document), "jup-078-benchmark-v1")
        self.assertNotEqual(other["run"]["run_id"], "jup-078-undated-7ea00edf")
        self.assertEqual(other["run"]["run_id"], f"jup-078-undated-{canonical_sha(document)[:8]}")

    def test_informe_fuera_de_la_raiz_no_registra_la_ruta_y_solo_deja_la_huella(self) -> None:
        path = self.write("sub/informe.json", load_json(JUP_070_RUN_2))
        output = self.normalize(path, "jup-070-report-v1", root=ROOT)
        self.assertIsNone(output["run"]["report_path"])
        self.assertEqual(output["run"]["report_sha256"], REAL_CASES[1]["sha"])
        self.assertNotIn(str(self.tmp), json.dumps(output))

    def test_informe_dentro_de_la_raiz_usa_ruta_relativa_con_barras(self) -> None:
        path = self.write("sub/Dir_1/Informe-2.v3.json", load_json(JUP_070_RUN_2))
        output = self.normalize(path, "jup-070-report-v1")
        self.assertEqual(output["run"]["report_path"], "sub/Dir_1/Informe-2.v3.json")
        # En la propia raíz.
        top = self.write("informe.json", load_json(JUP_070_RUN_2))
        self.assertEqual(self.normalize(top, "jup-070-report-v1")["run"]["report_path"], "informe.json")

    def test_la_ruta_se_compara_resuelta(self) -> None:
        # Una ruta con `..` que sale y vuelve a entrar sigue estando dentro de la raíz.
        self.write("sub/informe.json", load_json(JUP_070_RUN_2))
        (self.tmp / "otra").mkdir()
        tortuosa = self.tmp / "otra" / ".." / "sub" / "informe.json"
        output = self.normalize(tortuosa, "jup-070-report-v1")
        self.assertEqual(output["run"]["report_path"], "sub/informe.json")

    def test_un_directorio_hermano_con_el_mismo_prefijo_no_esta_dentro_de_la_raiz(self) -> None:
        # `raiz-otra` empieza igual que `raiz` pero NO cuelga de ella: una comparación de cadenas por prefijo lo
        # confundiría y registraría una ruta relativa inexistente.
        (self.tmp / "raiz").mkdir()
        path = self.write("raiz-otra/informe.json", load_json(JUP_070_RUN_2))
        output = self.normalize(path, "jup-070-report-v1", root=self.tmp / "raiz")
        self.assertIsNone(output["run"]["report_path"])
        dentro = self.write("raiz/informe.json", load_json(JUP_070_RUN_2))
        self.assertEqual(self.normalize(dentro, "jup-070-report-v1", root=self.tmp / "raiz")["run"]["report_path"],
                         "informe.json")

    def test_nombre_con_caracteres_no_permitidos_no_registra_la_ruta(self) -> None:
        # Espacios, tildes y otros caracteres fuera de `[A-Za-z0-9._/-]`: la ruta no se registra (None).
        document = load_json(JUP_070_RUN_2)
        for relative in ("con espacios/informe.json", "dir/mi informe.json", "dir/informé.json", "dir/a+b.json",
                         "dir/a@b.json", "dir/a=b.json", "dir/a,b.json"):
            with self.subTest(ruta=relative):
                try:
                    path = self.write(relative, document)
                except OSError:
                    continue
                output = self.normalize(path, "jup-070-report-v1")
                self.assertIsNone(output["run"]["report_path"])
                # La ejecución, en cambio, se normaliza igual.
                self.assertEqual(output["run"]["run_id"], "jup-070-20261008T210144Z-b64cca76")

    def test_nombre_con_espacios_dentro_de_la_raiz_mantiene_la_ruta_en_los_errores(self) -> None:
        document = load_json(JUP_070_RUN_2)
        document["report_version"] = 2
        path = self.write("dir con espacios/roto.json", document)
        message = self.normalize_error(path, "jup-070-report-v1")
        self.assertTrue(message.startswith("dir con espacios/roto.json: report_version: "), message)

    # --- rows-v1 -------------------------------------------------------------------------------------------

    def test_rows_v1_valido_usa_el_run_id_del_documento(self) -> None:
        path = self.write("robustez.json", ROWS_DOCUMENT)
        output = self.normalize(path, "rows-v1")
        run = output["run"]
        self.assertEqual(list(run), list(RUN_OUTPUT_KEYS))
        self.assertEqual(run["run_id"], "JUP-071-demo-1")
        self.assertEqual(output["results"], EXPECTED_ROWS_RESULTS)
        expected_run = dict.fromkeys(RUN_KEYS)
        expected_run.update(ROWS_RUN)
        expected_run["synthetic"] = False
        for key in RUN_KEYS:
            self.assertEqual(run[key], expected_run[key], key)
        self.assertEqual(run["non_real_reasons"], ["sin_modelo_verificado"])
        self.assertIs(run["is_real"], False)
        self.assertEqual(run["comparability_key"], expected_key(expected_run, ["sin_modelo_verificado"]))
        self.assertEqual(run["format"], "rows-v1")
        self.assertIs(run["milestone"], True)
        self.assertEqual(run["report_path"], "robustez.json")
        self.assertEqual(run["report_sha256"], canonical_sha(ROWS_DOCUMENT))

    def test_rows_v1_con_run_id_en_la_entrada_sustituye_al_del_documento(self) -> None:
        path = self.write("robustez.json", ROWS_DOCUMENT)
        output = self.normalize(path, "rows-v1", run_id="JUP-071-hito-2")
        self.assertEqual(output["run"]["run_id"], "JUP-071-hito-2")
        self.assertEqual(output["results"], EXPECTED_ROWS_RESULTS)
        self.assertEqual(output["run"]["report_sha256"], canonical_sha(ROWS_DOCUMENT))

    def test_rows_v1_sin_run_id_en_el_documento_exige_uno_en_la_entrada(self) -> None:
        document = copy.deepcopy(ROWS_DOCUMENT)
        del document["run"]["run_id"]
        path = self.write("sin-id.json", document)
        message = self.normalize_error(path, "rows-v1")
        self.assertTrue(message.startswith("sin-id.json: run.run_id: "), message)
        output = self.normalize(path, "rows-v1", run_id="desde-la-entrada")
        self.assertEqual(output["run"]["run_id"], "desde-la-entrada")

    def test_rows_v1_ejecucion_real_con_modelo_y_sin_sintetica(self) -> None:
        document = copy.deepcopy(ROWS_DOCUMENT)
        document["run"]["generation_model"] = "chat-modelo-1"
        output = self.normalize(self.write("real.json", document), "rows-v1")
        self.assertIs(output["run"]["is_real"], True)
        self.assertEqual(output["run"]["non_real_reasons"], [])
        document["run"]["synthetic"] = True
        output = self.normalize(self.write("sintetica.json", document), "rows-v1")
        self.assertIs(output["run"]["is_real"], False)
        self.assertEqual(output["run"]["non_real_reasons"], ["sintetica"])

    def test_rows_v1_con_una_sola_fila_es_valido(self) -> None:
        document = copy.deepcopy(ROWS_DOCUMENT)
        document["results"] = document["results"][:1]
        output = self.normalize(self.write("una.json", document), "rows-v1")
        self.assertEqual(output["results"], EXPECTED_ROWS_RESULTS[:1])

    def test_bom_al_principio_se_tolera_y_no_cambia_la_huella(self) -> None:
        plain = self.normalize(self.write("sin-bom.json", ROWS_DOCUMENT), "rows-v1")
        with_bom = self.normalize(self.write("con-bom.json", ROWS_DOCUMENT, bom=True), "rows-v1")
        self.assertEqual(with_bom["run"]["report_sha256"], plain["run"]["report_sha256"])
        self.assertEqual(with_bom["results"], plain["results"])

    def test_el_bom_tambien_se_tolera_en_un_informe_de_jup_070(self) -> None:
        path = self.write("070-bom.json", load_json(JUP_070_RUN_2), bom=True)
        output = self.normalize(path, "jup-070-report-v1")
        self.assertEqual(output["run"]["run_id"], "jup-070-20261008T210144Z-b64cca76")


# --- normalize_entry: errores ---------------------------------------------------------------------------


class NormalizeEntryErrorsTest(TmpCase):
    # --- Informe sin filas ---

    def assert_no_rows(self, message: str, label: str) -> None:
        self.assertTrue(message.startswith(f"{label}: "), message)
        self.assertIn("ninguna fila", message)

    def test_rows_v1_sin_resultados_es_un_error(self) -> None:
        document = copy.deepcopy(ROWS_DOCUMENT)
        document["results"] = []
        message = self.normalize_error(self.write("vacio.json", document), "rows-v1")
        self.assert_no_rows(message, "vacio.json")

    def test_jup_022_sin_puntos_ni_candidatos_es_un_error(self) -> None:
        document = load_json(JUP_022_REPORT)
        document["points"] = []
        document["selection"]["candidates"] = []
        message = self.normalize_error(self.write("cal-vacia.json", document), "jup-022-calibration-v1")
        self.assert_no_rows(message, "cal-vacia.json")

    def test_jup_078_sin_modelos_es_un_error(self) -> None:
        document = load_json(JUP_078_REPORT)
        document["models"] = []
        message = self.normalize_error(self.write("bench-vacio.json", document), "jup-078-benchmark-v1")
        self.assert_no_rows(message, "bench-vacio.json")

    # --- Lectura y JSON ---

    def test_json_invalido(self) -> None:
        for name, content in (("roto.json", b"{no es json"), ("vacio.json", b""), ("truncado.json", b'{"a": [1, 2')):
            with self.subTest(fichero=name):
                path = self.tmp / name
                path.write_bytes(content)
                message = self.normalize_error(path, "rows-v1")
                self.assertTrue(message.startswith(f"{name}: "), message)

    def test_json_anidado_hasta_desbordar_el_parser_es_adapter_error(self) -> None:
        path = self.tmp / "profundo.json"
        path.write_text("[" * 200000, encoding="utf-8")
        message = self.normalize_error(path, "rows-v1")
        self.assertTrue(message.startswith("profundo.json: "), message)

    def test_fichero_inexistente_o_ilegible(self) -> None:
        self.assertTrue(self.normalize_error(self.tmp / "no-existe.json", "rows-v1").startswith("no-existe.json: "))
        (self.tmp / "carpeta.json").mkdir()
        self.assertTrue(self.normalize_error(self.tmp / "carpeta.json", "rows-v1").startswith("carpeta.json: "))

    def test_utf8_invalido(self) -> None:
        path = self.tmp / "binario.json"
        path.write_bytes(b"\xff\xfe{\"a\": 1}")
        self.assertTrue(self.normalize_error(path, "rows-v1").startswith("binario.json: "))

    # --- Cada adaptador con un informe roto: el mensaje empieza por el fichero y conserva el campo ---

    def broken_cases(self):
        document_070 = load_json(JUP_070_RUN_2)
        document_070["report_version"] = 2
        document_078 = load_json(JUP_078_REPORT)
        document_078["schema_version"] = 2
        document_022 = load_json(JUP_022_REPORT)
        document_022["schema_version"] = 2
        document_rows = copy.deepcopy(ROWS_DOCUMENT)
        document_rows["contract_version"] = 2
        return (
            ("jup-070-report-v1", document_070, tool.adapt_jup070, "report_version: "),
            ("jup-078-benchmark-v1", document_078, tool.adapt_jup078, "schema_version: "),
            ("jup-022-calibration-v1", document_022, tool.adapt_jup022, "schema_version: "),
            ("rows-v1", document_rows, tool.adapt_rows_v1, "contract_version: "),
        )

    def test_cada_adaptador_con_un_informe_roto_conserva_su_mensaje_tras_el_fichero(self) -> None:
        for fmt, document, adapter, field in self.broken_cases():
            with self.subTest(formato=fmt):
                with self.assertRaises(tool.AdapterError) as raw:
                    # `adapt_rows_v1` toma solo el documento; los demás, el documento y un run_id provisional.
                    args = (document,) if fmt == "rows-v1" else (document, "x")
                    adapter(*args)
                path = self.write(f"roto-{fmt}.json", document)
                message = self.normalize_error(path, fmt)
                # Mensaje original TAL CUAL tras `<fichero>: `.
                self.assertEqual(message, f"roto-{fmt}.json: {raw.exception}")
                self.assertIn(field, message)

    def test_documento_que_no_es_un_objeto_en_cada_formato(self) -> None:
        for fmt in ("jup-070-report-v1", "jup-078-benchmark-v1", "jup-022-calibration-v1", "rows-v1"):
            with self.subTest(formato=fmt):
                path = self.write(f"lista-{fmt}.json", [1, 2, 3])
                message = self.normalize_error(path, fmt)
                self.assertTrue(message.startswith(f"lista-{fmt}.json: "), message)
                self.assertIn("debe ser un objeto", message)

    def test_jup_068_con_una_entrada_rota_nombra_el_fichero_y_el_generador(self) -> None:
        path = self.write("negocio-roto.json", {})
        message = self.normalize_error(path, "jup-068-input-v1")
        self.assertTrue(message.startswith("negocio-roto.json: business-metrics: "), message)

    def test_la_ruta_dentro_de_la_raiz_es_el_prefijo_del_mensaje(self) -> None:
        document = load_json(JUP_070_RUN_2)
        document["run"]["date"] = "no es una fecha"
        path = self.write("docs/evidence/x.json", document)
        message = self.normalize_error(path, "jup-070-report-v1")
        self.assertTrue(message.startswith("docs/evidence/x.json: run.date: debe ser una fecha ISO 8601"), message)

    def test_fuera_de_la_raiz_el_prefijo_es_solo_el_nombre_del_fichero(self) -> None:
        document = load_json(JUP_070_RUN_2)
        document["run"]["date"] = "no es una fecha"
        path = self.write("carpeta-con-usuario/x.json", document)
        message = self.normalize_error(path, "jup-070-report-v1", root=ROOT)
        self.assertTrue(message.startswith("x.json: run.date: debe ser una fecha ISO 8601"), message)
        # Ni el directorio temporal ni ninguna parte de la ruta absoluta.
        self.assertNotIn("carpeta-con-usuario", message)
        self.assertNotIn(str(self.tmp), message)
        self.assertNotIn(self.tmp.name, message)

    def test_los_errores_de_lectura_fuera_de_la_raiz_tampoco_vuelcan_la_ruta_en_el_prefijo(self) -> None:
        message = self.normalize_error(self.tmp / "dir-privado" / "falta.json", "rows-v1", root=ROOT)
        self.assertTrue(message.startswith("falta.json: "), message)

    def test_la_validacion_comun_se_aplica_a_la_salida_cruda_del_adaptador(self) -> None:
        # El adaptador de JUP-070 copia el commit sin comprobar el alfabeto; es `validate_rows` quien lo rechaza.
        document = load_json(JUP_070_RUN_2)
        document["run"]["commit"] = "texto libre con espacios"
        message = self.normalize_error(self.write("commit.json", document), "jup-070-report-v1")
        self.assertTrue(message.startswith("commit.json: run.commit: "), message)

    def adapter_cases(self):
        # (formato, nombre del adaptador, informe crudo con el que se obtiene una salida cruda válida)
        return (
            ("jup-070-report-v1", "adapt_jup070", load_json(JUP_070_RUN_2)),
            ("jup-078-benchmark-v1", "adapt_jup078", load_json(JUP_078_REPORT)),
            ("jup-022-calibration-v1", "adapt_jup022", load_json(JUP_022_REPORT)),
            ("jup-068-input-v1", "adapt_jup068", REPORT_068),
        )

    def patched_normalize(self, fmt, adapter_name, report, mutate):
        # Sustituye SOLO el adaptador (y la lectura de Node en JUP-068) por una salida cruda alterada: es la única
        # forma de comprobar que la validación común y la regla de «ninguna fila» se aplican en cada formato.
        raw_run, raw_results = getattr(tool, adapter_name)(report, "x")
        run, results = mutate(copy.deepcopy(raw_run), copy.deepcopy(raw_results))
        path = self.write(f"{fmt}.json", load_json(JUP_070_RUN_2) if fmt != "jup-068-input-v1" else load_json(JUP_068_EXAMPLE))
        with mock.patch.object(tool, adapter_name, return_value=(run, results)),                 mock.patch.object(tool, "read_business_report", return_value=REPORT_068):
            return self.normalize_error(path, fmt)

    def test_la_validacion_comun_se_aplica_a_la_salida_de_cada_adaptador(self) -> None:
        def bad_commit(run, results):
            run["commit"] = "texto libre con espacios"
            return run, results
        for fmt, adapter_name, report in self.adapter_cases():
            with self.subTest(formato=fmt):
                message = self.patched_normalize(fmt, adapter_name, report, bad_commit)
                self.assertTrue(message.startswith(f"{fmt}.json: run.commit: "), message)

    def test_la_validacion_comun_tambien_revisa_las_filas_de_cada_adaptador(self) -> None:
        # La clasificación valida solo la ejecución; las filas dependen de `validate_rows(run, results)`.
        def bad_row(run, results):
            results[0]["texto_libre"] = "no permitido"
            return run, results
        for fmt, adapter_name, report in self.adapter_cases():
            with self.subTest(formato=fmt):
                message = self.patched_normalize(fmt, adapter_name, report, bad_row)
                self.assertTrue(message.startswith(f"{fmt}.json: results[0].texto_libre: "), message)

    def test_la_regla_de_ninguna_fila_se_aplica_a_cada_formato(self) -> None:
        def no_rows(run, results):
            return run, []
        for fmt, adapter_name, report in self.adapter_cases():
            with self.subTest(formato=fmt):
                message = self.patched_normalize(fmt, adapter_name, report, no_rows)
                self.assert_no_rows(message, f"{fmt}.json")

    def test_una_fecha_que_no_es_el_formato_del_contrato_es_error_y_no_se_deriva(self) -> None:
        # `fromisoformat` acepta el separador espacio; el contrato no. Debe salir como error de validación y no
        # como un `run_id` derivado de una fecha inadmisible.
        document = load_json(JUP_070_RUN_2)
        document["run"]["date"] = "2026-10-08 21:01:44"
        message = self.normalize_error(self.write("fecha.json", document), "jup-070-report-v1")
        self.assertTrue(message.startswith("fecha.json: run.run_at: "), message)

    def test_un_manifest_error_interno_se_relanza_como_adapter_error_con_prefijo(self) -> None:
        path = self.write("origen.json", ROWS_DOCUMENT)
        with mock.patch.object(tool, "adapt_rows_v1", side_effect=tool.ManifestError("m.json: runs[0].path: algo")):
            message = self.normalize_error(path, "rows-v1")
        self.assertEqual(message, "origen.json: m.json: runs[0].path: algo")

    # --- Nombres de clave desconocidos dentro de un mensaje ---

    def test_una_clave_corta_desconocida_sigue_apareciendo_en_el_mensaje(self) -> None:
        document = load_json(JUP_070_RUN_2)
        document["metrics"]["ZZZ-9"] = {}
        message = self.normalize_error(self.write("corta.json", document), "jup-070-report-v1")
        self.assertTrue(message.startswith("corta.json: metrics."), message)
        self.assertIn("ZZZ-9", message)
        self.assertIn("métrica desconocida", message)

    def test_una_clave_larga_en_las_metricas_no_se_vuelca_entera(self) -> None:
        document = load_json(JUP_070_RUN_2)
        document["metrics"]["X" * 500] = {}
        message = self.normalize_error(self.write("larga.json", document), "jup-070-report-v1")
        self.assertTrue(message.startswith("larga.json: metrics."), message)
        self.assertNotIn("X" * 81, message)
        self.assertLess(len(message), 400)
        self.assertIn("métrica desconocida", message)

    def test_una_clave_larga_en_rows_v1_no_se_vuelca_entera(self) -> None:
        for where in ("run", "result", "document"):
            with self.subTest(donde=where):
                document = copy.deepcopy(ROWS_DOCUMENT)
                if where == "run":
                    document["run"]["k" * 500] = 1
                elif where == "result":
                    document["results"][0]["k" * 500] = 1
                else:
                    document["k" * 500] = 1
                message = self.normalize_error(self.write(f"larga-{where}.json", document), "rows-v1")
                self.assertTrue(message.startswith(f"larga-{where}.json: "), message)
                self.assertNotIn("k" * 81, message)
                self.assertLess(len(message), 400)
                self.assertIn("clave desconocida", message)

    def test_las_claves_con_caracteres_de_control_se_escapan(self) -> None:
        # Una clave con salto de línea o ESC no puede partir el mensaje ni inyectar secuencias de terminal.
        for key in ("mala\nclave", "mala\x1b[31mclave", "mala\rclave"):
            with self.subTest(clave=repr(key)):
                document = copy.deepcopy(ROWS_DOCUMENT)
                document["run"][key] = 1
                message = self.normalize_error(self.write("control.json", document), "rows-v1")
                self.assertTrue(message.startswith("control.json: "), message)
                for forbidden in ("\n", "\r", "\x1b"):
                    self.assertNotIn(forbidden, message)
                self.assertIn("clave desconocida", message)


# --- Mocks de la frontera de Node (run_id del informe de negocio) -------------------------------------------


class NormalizeBusinessRunIdTest(TmpCase):
    def normalized_with_report(self, report: dict, run_id=None):
        path = self.write("negocio.json", load_json(JUP_068_EXAMPLE))
        with mock.patch.object(tool, "read_business_report", return_value=report) as reader:
            output = self.normalize(path, "jup-068-input-v1", run_id=run_id)
        return output, reader, path

    def test_el_run_id_por_defecto_es_el_del_informe_de_negocio_y_se_lee_la_entrada_indicada(self) -> None:
        report = copy.deepcopy(REPORT_068)
        report["run_id"] = "JUP-068-otro-v7"
        output, reader, path = self.normalized_with_report(report)
        self.assertEqual(output["run"]["run_id"], "JUP-068-otro-v7")
        reader.assert_called_once()
        self.assertEqual(Path(reader.call_args.args[0]), path)

    def test_un_informe_de_negocio_sin_run_id_es_un_error_con_prefijo(self) -> None:
        report = copy.deepcopy(REPORT_068)
        del report["run_id"]
        path = self.write("negocio.json", load_json(JUP_068_EXAMPLE))
        with mock.patch.object(tool, "read_business_report", return_value=report):
            message = self.normalize_error(path, "jup-068-input-v1")
        self.assertTrue(message.startswith("negocio.json: "), message)

    def test_un_run_id_del_informe_que_no_es_identificador_es_un_error_con_prefijo(self) -> None:
        report = copy.deepcopy(REPORT_068)
        report["run_id"] = "texto libre con espacios"
        path = self.write("negocio.json", load_json(JUP_068_EXAMPLE))
        with mock.patch.object(tool, "read_business_report", return_value=report):
            message = self.normalize_error(path, "jup-068-input-v1")
        self.assertTrue(message.startswith("negocio.json: run.run_id: "), message)

    def test_con_run_id_explicito_el_del_informe_no_importa(self) -> None:
        report = copy.deepcopy(REPORT_068)
        report["run_id"] = "texto libre con espacios"
        output, _, _ = self.normalized_with_report(report, run_id="explicito-68")
        self.assertEqual(output["run"]["run_id"], "explicito-68")


# --- build_dataset ------------------------------------------------------------------------------------------


class BuildDatasetTest(TmpCase):
    def rows_manifest(self, name: str, *documents, milestone=False, run_ids=None) -> Path:
        # Manifiesto local con un informe `rows-v1` por documento (rutas absolutas, en el tmpdir).
        entries = []
        for index, document in enumerate(documents):
            report = self.write(f"{name}-informe-{index}.json", document)
            entry = {"path": str(report), "format": "rows-v1", "milestone": milestone}
            if run_ids and run_ids[index] is not None:
                entry["run_id"] = run_ids[index]
            entries.append(entry)
        return self.write_manifest(f"{name}.json", entries)

    def document_with_id(self, run_id: str) -> dict:
        document = copy.deepcopy(ROWS_DOCUMENT)
        document["run"]["run_id"] = run_id
        return document

    def test_el_manifiesto_versionado_da_ocho_ejecuciones_distintas_en_orden(self) -> None:
        dataset = tool.build_dataset([MANIFEST_FILE], root=ROOT)
        self.assertEqual(list(dataset), ["dataset_version", "runs"])
        self.assertEqual(dataset["dataset_version"], 1)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], REAL_RUN_IDS)
        self.assertEqual([len(item["results"]) for item in dataset["runs"]], [case["rows"] for case in REAL_CASES])
        for item, entry in zip(dataset["runs"], tool.read_manifest(MANIFEST_FILE, root=ROOT)):
            self.assertEqual(item, tool.normalize_entry(entry, root=ROOT))
        json.dumps(dataset, allow_nan=False)

    def test_dos_manifiestos_versionado_y_local_con_un_hito_falso(self) -> None:
        local = self.rows_manifest("local", ROWS_DOCUMENT)
        dataset = tool.build_dataset([MANIFEST_FILE, local], root=ROOT)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], REAL_RUN_IDS + ["JUP-071-demo-1"])
        extra = dataset["runs"][len(REAL_CASES)]
        self.assertIs(extra["run"]["milestone"], False)
        self.assertEqual(extra["run"]["format"], "rows-v1")
        self.assertIsNone(extra["run"]["report_path"])
        self.assertEqual(extra["results"], EXPECTED_ROWS_RESULTS)
        self.assertTrue(all(item["run"]["milestone"] is True for item in dataset["runs"][:len(REAL_CASES)]))

    def test_el_orden_es_el_de_los_manifiestos_dados(self) -> None:
        local = self.rows_manifest("local", ROWS_DOCUMENT)
        dataset = tool.build_dataset([local, MANIFEST_FILE], root=ROOT)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], ["JUP-071-demo-1"] + REAL_RUN_IDS)

    def test_una_tupla_de_manifiestos_tambien_vale_y_no_se_muta_la_lista(self) -> None:
        local = self.rows_manifest("local", ROWS_DOCUMENT)
        paths = [local]
        dataset = tool.build_dataset(tuple(paths), root=self.tmp)
        self.assertEqual(len(dataset["runs"]), 1)
        self.assertEqual(paths, [local])

    def test_la_raiz_se_usa_para_las_rutas_relativas_y_para_report_path(self) -> None:
        self.write("informes/robustez.json", ROWS_DOCUMENT)
        manifest = self.write_manifest("otras/local.json", [
            {"path": "informes/robustez.json", "format": "rows-v1", "milestone": False}])
        dataset = tool.build_dataset([manifest], root=self.tmp)
        self.assertEqual(dataset["runs"][0]["run"]["report_path"], "informes/robustez.json")

    def test_sin_manifiestos_el_conjunto_esta_vacio(self) -> None:
        self.assertEqual(tool.build_dataset([]), {"dataset_version": 1, "runs": []})
        self.assertEqual(list(tool.build_dataset([])), ["dataset_version", "runs"])
        self.assertEqual(tool.build_dataset(()), {"dataset_version": 1, "runs": []})

    def test_un_manifiesto_sin_ejecuciones_aporta_cero_filas(self) -> None:
        manifest = self.write_manifest("vacio.json", [])
        self.assertEqual(tool.build_dataset([manifest], root=self.tmp), {"dataset_version": 1, "runs": []})

    # --- run_id repetido ---

    def assert_duplicate(self, caught, *names: str) -> str:
        message = str(caught.exception)
        self.assertTrue(message.startswith("run_id: "), message)
        for name in names:
            self.assertIn(name, message)
        return message

    def test_la_misma_ejecucion_copiada_a_otro_nombre_repite_el_run_id_derivado(self) -> None:
        document = load_json(JUP_070_RUN_2)
        first = self.write("copias/original-a.json", document)
        second = self.write("copias/copia-b.json", document)
        manifest = self.write_manifest("copias.json", [
            {"path": str(first), "format": "jup-070-report-v1", "milestone": False},
            {"path": str(second), "format": "jup-070-report-v1", "milestone": False}])
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([manifest], root=self.tmp)
        message = self.assert_duplicate(caught, "original-a.json", "copia-b.json")
        self.assertIn("jup-070-20261008T210144Z-b64cca76", message)

    def test_dos_rows_v1_con_el_mismo_run_id_en_el_documento(self) -> None:
        first = self.rows_manifest("uno", ROWS_DOCUMENT)
        second = self.rows_manifest("dos", ROWS_DOCUMENT)
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([first, second], root=self.tmp)
        self.assert_duplicate(caught, "uno-informe-0.json", "dos-informe-0.json")

    def test_un_run_id_explicito_que_coincide_con_el_de_otra_entrada(self) -> None:
        # `merge_manifests` solo compara los `run_id` explícitos entre sí; este choque (explícito frente al del
        # documento de otra entrada) lo detecta `build_dataset`.
        other = self.document_with_id("otro-documento-1")
        first = self.rows_manifest("uno", other, run_ids=["JUP-071-demo-1"])
        second = self.rows_manifest("dos", ROWS_DOCUMENT)
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([first, second], root=self.tmp)
        self.assert_duplicate(caught, "uno-informe-0.json", "dos-informe-0.json")

    def test_el_hito_repetido_con_otro_run_id_explicito_si_se_admite(self) -> None:
        # El caso de uso del `run_id` explícito: dos copias del mismo informe, cada una con su identificador.
        first = self.rows_manifest("uno", ROWS_DOCUMENT, run_ids=["hito-1"])
        second = self.rows_manifest("dos", ROWS_DOCUMENT, run_ids=["hito-2"])
        dataset = tool.build_dataset([first, second], root=self.tmp)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], ["hito-1", "hito-2"])

    def test_run_id_explicito_repetido_en_dos_manifiestos_es_un_error_que_lo_nombra(self) -> None:
        # Aquí actúa `merge_manifests` (ManifestError); solo se exige un error de datos que nombre el identificador.
        first = self.rows_manifest("uno", self.document_with_id("a-1"), run_ids=["dup-1"])
        second = self.rows_manifest("dos", self.document_with_id("b-1"), run_ids=["dup-1"])
        with self.assertRaises(ValueError) as caught:
            tool.build_dataset([first, second], root=self.tmp)
        self.assertIn("dup-1", str(caught.exception))

    # --- Sin resultados parciales ---

    def test_si_falla_la_ultima_entrada_no_se_devuelve_nada(self) -> None:
        good = self.write("bien.json", ROWS_DOCUMENT)
        broken_document = copy.deepcopy(ROWS_DOCUMENT)
        broken_document["contract_version"] = 2
        broken = self.write("mal.json", broken_document)
        manifest = self.write_manifest("m.json", [
            {"path": str(good), "format": "rows-v1", "milestone": False},
            {"path": str(broken), "format": "rows-v1", "milestone": False}])
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([manifest], root=self.tmp)
        self.assertTrue(str(caught.exception).startswith("mal.json: contract_version: "), str(caught.exception))

    def test_un_manifiesto_inexistente_lanza_manifest_error(self) -> None:
        with self.assertRaises(tool.ManifestError):
            tool.build_dataset([self.tmp / "no-existe.json"], root=self.tmp)

    def test_un_informe_roto_en_el_manifiesto_versionado_mas_local_no_deja_nada(self) -> None:
        broken_document = copy.deepcopy(ROWS_DOCUMENT)
        broken_document["results"] = []
        manifest = self.rows_manifest("local", broken_document)
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([MANIFEST_FILE, manifest], root=ROOT)
        self.assertIn("ninguna fila", str(caught.exception))

    # --- Sin efectos ---

    def test_no_muta_los_ficheros_y_es_repetible(self) -> None:
        manifest = self.rows_manifest("local", ROWS_DOCUMENT)
        report = self.tmp / "local-informe-0.json"
        before = (manifest.read_bytes(), report.read_bytes(), sorted(path.name for path in self.tmp.iterdir()))
        first = tool.build_dataset([manifest], root=self.tmp)
        second = tool.build_dataset([manifest], root=self.tmp)
        after = (manifest.read_bytes(), report.read_bytes(), sorted(path.name for path in self.tmp.iterdir()))
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first["runs"], second["runs"])
        self.assertIsNot(first["runs"][0]["run"], second["runs"][0]["run"])


# --- Línea de comandos ---------------------------------------------------------------------------------------


def run_cli(*args, cwd=None, env_extra=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]],
        capture_output=True, text=True, encoding="utf-8", cwd=cwd, env=env, timeout=240, check=False,
    )


def dumps_text(dataset) -> str:
    return json.dumps(dataset, indent=2, ensure_ascii=True)


class CliTest(TmpCase):
    expected_versioned = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.expected_versioned = tool.build_dataset([MANIFEST_FILE], root=ROOT)

    def local_manifest(self, name="local", document=None, *, milestone=False, run_id=None) -> Path:
        report = self.write(f"{name}-informe.json", ROWS_DOCUMENT if document is None else document)
        entry = {"path": str(report), "format": "rows-v1", "milestone": milestone}
        if run_id is not None:
            entry["run_id"] = run_id
        return self.write_manifest(f"{name}.json", [entry])

    def assert_ok(self, completed) -> None:
        self.assertEqual(completed.returncode, 0, completed.stderr)

    # --- Salida correcta ---

    def test_rows_con_el_versionado_escribe_el_dataset_en_stdout(self) -> None:
        completed = run_cli("rows", "--root", ROOT, cwd=self.tmp)
        self.assert_ok(completed)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(completed.stdout, dumps_text(self.expected_versioned) + "\n")
        self.assertTrue(completed.stdout.isascii())
        dataset = json.loads(completed.stdout)
        self.assertEqual(dataset["dataset_version"], 1)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], REAL_RUN_IDS)
        self.assertEqual([len(item["results"]) for item in dataset["runs"]], [case["rows"] for case in REAL_CASES])
        self.assertEqual([item["run"]["report_path"] for item in dataset["runs"]],
                         [case["report_path"] for case in REAL_CASES])

    def test_output_escribe_el_fichero_y_deja_stdout_vacio(self) -> None:
        target = self.tmp / "salida" / "filas.json"
        target.parent.mkdir()
        completed = run_cli("rows", "--root", ROOT, "--output", target)
        self.assert_ok(completed)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")
        raw = target.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "el fichero no debe llevar BOM")
        text = raw.decode("utf-8").replace("\r\n", "\n")
        self.assertTrue(text.endswith("\n"))
        self.assertFalse(text.endswith("\n\n"))
        self.assertEqual(text, dumps_text(self.expected_versioned) + "\n")
        self.assertEqual(json.loads(text), self.expected_versioned)

    def test_output_reemplaza_el_contenido_anterior_por_completo(self) -> None:
        target = self.tmp / "filas.json"
        target.write_text("x" * 100000, encoding="utf-8")
        manifest = self.local_manifest()
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", target)
        self.assert_ok(completed)
        text = target.read_bytes().decode("utf-8").replace("\r\n", "\n")
        self.assertEqual(json.loads(text)["runs"][0]["run"]["run_id"], "JUP-071-demo-1")
        self.assertNotIn("xxxx", text)

    def test_manifest_extra_se_anade_despues_del_versionado(self) -> None:
        manifest = self.local_manifest()
        completed = run_cli("rows", "--root", ROOT, "--manifest", manifest)
        self.assert_ok(completed)
        dataset = json.loads(completed.stdout)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], REAL_RUN_IDS + ["JUP-071-demo-1"])
        self.assertIs(dataset["runs"][len(REAL_CASES)]["run"]["milestone"], False)
        self.assertIsNone(dataset["runs"][len(REAL_CASES)]["run"]["report_path"])

    def test_varios_manifest_conservan_el_orden_de_la_linea_de_comandos(self) -> None:
        second = self.local_manifest("segundo", self.document_with_id("JUP-071-segundo"))
        first = self.local_manifest("primero", self.document_with_id("JUP-071-primero"))
        completed = run_cli("rows", "--no-versioned", "--manifest", second, "--manifest", first, "--root", self.tmp)
        self.assert_ok(completed)
        ids = [item["run"]["run_id"] for item in json.loads(completed.stdout)["runs"]]
        self.assertEqual(ids, ["JUP-071-segundo", "JUP-071-primero"])

    def document_with_id(self, run_id: str) -> dict:
        document = copy.deepcopy(ROWS_DOCUMENT)
        document["run"]["run_id"] = run_id
        return document

    def test_no_versioned_con_solo_un_manifiesto_local(self) -> None:
        manifest = self.local_manifest()
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp)
        self.assert_ok(completed)
        dataset = json.loads(completed.stdout)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], ["JUP-071-demo-1"])
        self.assertEqual(dataset["runs"][0]["results"], EXPECTED_ROWS_RESULTS)
        self.assertEqual(dataset["runs"][0]["run"]["report_path"], "local-informe.json")

    def test_no_versioned_sin_manifiestos_da_el_conjunto_vacio(self) -> None:
        completed = run_cli("rows", "--no-versioned", "--root", self.tmp)
        self.assert_ok(completed)
        self.assertEqual(completed.stdout, '{\n  "dataset_version": 1,\n  "runs": []\n}\n')
        self.assertEqual(completed.stderr, "")

    def test_root_resuelve_las_rutas_relativas_y_el_report_path(self) -> None:
        # El informe vive bajo `--root`; el manifiesto, en otra carpeta; el directorio de trabajo, en una tercera.
        self.write("informes/robustez.json", ROWS_DOCUMENT)
        manifest = self.write_manifest("otras/local.json", [
            {"path": "informes/robustez.json", "format": "rows-v1", "milestone": False}])
        elsewhere = self.tmp / "cwd"
        elsewhere.mkdir()
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp, cwd=elsewhere)
        self.assert_ok(completed)
        self.assertEqual(json.loads(completed.stdout)["runs"][0]["run"]["report_path"], "informes/robustez.json")

    def test_sin_root_las_rutas_relativas_se_resuelven_desde_la_raiz_de_la_herramienta_y_no_desde_el_cwd(self) -> None:
        # El informe no existe: el error nombra la ruta resuelta, que debe colgar de `ROOT` y no del cwd.
        manifest = self.write_manifest("m.json", [
            {"path": "no-existe-jup121.json", "format": "rows-v1", "milestone": False}])
        cwd = self.tmp / "cwd"
        cwd.mkdir()
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, cwd=cwd)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn(str((Path(tool.ROOT) / "no-existe-jup121.json").resolve()), completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_la_salida_de_dos_ejecuciones_es_identica_byte_a_byte(self) -> None:
        manifest = self.write_manifest("m.json", [
            {"path": str(self.write("a.json", load_json(JUP_070_RUN_2))), "format": "jup-070-report-v1", "milestone": True},
            {"path": str(self.write("b.json", ROWS_DOCUMENT)), "format": "rows-v1", "milestone": False}])
        outputs = []
        for seed in ("0", "1", "4242"):
            completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp,
                                env_extra={"PYTHONHASHSEED": seed})
            self.assert_ok(completed)
            outputs.append(completed.stdout.encode("utf-8"))
        # Comprobación positiva: no basta con que dos salidas vacías coincidan.
        self.assertGreater(len(outputs[0]), 1000)
        self.assertEqual(len({output for output in outputs}), 1)
        self.assertEqual(len(json.loads(outputs[0])["runs"]), 2)

    # --- Fallos ---

    def test_manifiesto_inexistente_termina_con_1_y_conserva_el_output(self) -> None:
        target = self.tmp / "previo.json"
        target.write_bytes(b"contenido previo\n")
        completed = run_cli("rows", "--no-versioned", "--manifest", self.tmp / "no-existe.json", "--root", self.tmp,
                            "--output", target)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("error: "), completed.stderr)
        self.assertIn("no-existe.json", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(target.read_bytes(), b"contenido previo\n")

    def test_un_fallo_no_crea_el_fichero_de_salida(self) -> None:
        target = self.tmp / "nuevo.json"
        completed = run_cli("rows", "--no-versioned", "--manifest", self.tmp / "no-existe.json", "--root", self.tmp,
                            "--output", target)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertFalse(target.exists())

    def test_informe_roto_termina_con_1_y_nombra_el_fichero(self) -> None:
        broken = copy.deepcopy(ROWS_DOCUMENT)
        broken["contract_version"] = 2
        manifest = self.local_manifest("roto", broken)
        target = self.tmp / "salida.json"
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", target)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("error: roto-informe.json: contract_version: "), completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertFalse(target.exists())

    def test_un_fallo_en_la_ultima_entrada_no_deja_ninguna_salida_parcial(self) -> None:
        broken = copy.deepcopy(ROWS_DOCUMENT)
        broken["results"] = []
        manifest = self.local_manifest("sinfilas", broken)
        completed = run_cli("rows", "--root", ROOT, "--manifest", manifest)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("ninguna fila", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_run_id_duplicado_termina_con_1(self) -> None:
        first = self.local_manifest("uno")
        second = self.local_manifest("dos")
        completed = run_cli("rows", "--no-versioned", "--manifest", first, "--manifest", second, "--root", self.tmp)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("error: run_id: "), completed.stderr)
        self.assertEqual(completed.stdout, "")

    # --- Uso ---

    def test_sin_subcomando_es_un_error_de_uso(self) -> None:
        completed = run_cli()
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertIn("usage", completed.stderr.lower())

    def test_subcomando_desconocido_es_un_error_de_uso(self) -> None:
        completed = run_cli("cargar")
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertNotEqual(completed.stderr, "")

    def test_opcion_desconocida_o_sin_valor_es_un_error_de_uso(self) -> None:
        for args in (("rows", "--no-existe"), ("rows", "--manifest"), ("rows", "--output"), ("rows", "--root")):
            with self.subTest(args=args):
                completed = run_cli(*args)
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                self.assertEqual(completed.stdout, "")

    def test_ayuda_termina_con_0_y_documenta_las_opciones(self) -> None:
        general = run_cli("--help")
        self.assertEqual(general.returncode, 0, general.stderr)
        self.assertIn("rows", general.stdout)
        detailed = run_cli("rows", "--help")
        self.assertEqual(detailed.returncode, 0, detailed.stderr)
        for option in ("--manifest", "--no-versioned", "--output", "--root"):
            self.assertIn(option, detailed.stdout)


# --- main en el propio proceso -------------------------------------------------------------------------------


class MainInProcessTest(TmpCase):
    def call(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = tool.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_correcto_devuelve_0_y_solo_imprime_el_json(self) -> None:
        report = self.write("informe.json", ROWS_DOCUMENT)
        manifest = self.write_manifest("m.json", [{"path": str(report), "format": "rows-v1", "milestone": False}])
        code, out, err = self.call(["rows", "--no-versioned", "--manifest", str(manifest), "--root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIs(type(code), int)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out)["runs"][0]["run"]["run_id"], "JUP-071-demo-1")
        self.assertEqual(out, dumps_text(json.loads(out)) + "\n")

    def test_error_de_datos_devuelve_1_con_el_mensaje_en_stderr(self) -> None:
        code, out, err = self.call(["rows", "--no-versioned", "--manifest", str(self.tmp / "falta.json"),
                                    "--root", str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertIs(type(code), int)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn("falta.json", err)

    def test_error_de_adaptador_devuelve_1(self) -> None:
        broken = copy.deepcopy(ROWS_DOCUMENT)
        broken["contract_version"] = 2
        report = self.write("roto.json", broken)
        manifest = self.write_manifest("m.json", [{"path": str(report), "format": "rows-v1", "milestone": False}])
        code, out, err = self.call(["rows", "--no-versioned", "--manifest", str(manifest), "--root", str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: roto.json: contract_version: "), err)

    def test_sin_argv_toma_los_argumentos_del_proceso(self) -> None:
        with mock.patch.object(sys, "argv", ["evaluation-dashboard.py", "rows", "--no-versioned", "--root", str(self.tmp)]):
            code, out, _ = self.call(None)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"dataset_version": 1, "runs": []})


if __name__ == "__main__":
    unittest.main()
