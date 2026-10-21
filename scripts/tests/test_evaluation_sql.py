"""Generación del script SQL y subcomando `sql` de `tools/evaluation-dashboard.py` (JUP-121, tarea 3.1, Red).

El script carga el conjunto de datos normalizado (`build_dataset`) en el esquema `evaluation` de PostgreSQL 17 sin
base de datos ni credenciales: solo produce texto. Contrato que se valida (ADR-0022, `design.md` D1, D2 y D4 y
`docs/validation/evaluation-dashboard.md`):

* Constantes: `SCHEMA_NAME`, `RUN_COLUMNS` y `RESULT_COLUMNS` (dict ordenados clave del contrato -> columna),
  `INSERT_CHUNK` (500 tuplas por `INSERT` de resultados) y `SqlError(ValueError)`.
* `sql_literal(valor)`: único camino por el que un valor entra en el SQL. Cada rama (None, bool, int, float, str,
  lista de str, dict como `jsonb`) y cada rechazo (NaN, infinito, NUL, tipos ajenos) se prueba aislada, y una batería
  de cadenas hostiles se comprueba con un «desescapador» escrito en esta prueba (no con la herramienta).
* `build_sql(dataset)`: función pura y determinista. Valida el conjunto de datos (`dataset: `, `runs[i]: ` o la ruta
  de `validate_rows` precedida de `runs[i].`) y devuelve el script en este orden: `BEGIN;`, `SET LOCAL
  standard_conforming_strings = on;`, `CREATE SCHEMA IF NOT EXISTS`, las dos `CREATE TABLE IF NOT EXISTS`, el
  `TRUNCATE`, los `INSERT` de ejecuciones y de resultados (en bloques de 500) y `COMMIT;`.
* Subcomando `sql` de `main`, con las opciones de `rows` y la misma salida byte a byte por stdout y por `--output`.

Las tareas 3.2 (vista) y 3.3 (rol de lectura) añadirán sentencias DDL al script, por eso NUNCA se compara el script
completo con una cadena literal: se trocea en sentencias (con un separador que respeta las comillas) y se comprueba
la estructura, el orden y el contenido por secciones. Los valores de cada tupla se leen con un analizador escrito
aquí y se comparan con lo esperado calculado a partir del conjunto de datos, no con la salida de la herramienta.

Decisiones donde el contrato admite más de una lectura (fijadas aquí; el coder debe respetarlas):

* Los bloques de resultados se parten sobre la lista GLOBAL de filas (todas las ejecuciones, en orden), no por
  ejecución: con 6 ejecuciones y 405 filas hay un único `INSERT` de resultados.
* Una ejecución sin filas es válida para `build_sql` (solo la inserta en `evaluation.runs`) y si NINGUNA ejecución
  trae filas no se emite ningún `INSERT` de resultados (un `INSERT ... VALUES` sin tuplas no es SQL válido).
* Las columnas que `validate_rows` no cubre (`report_path`, `format`, `comparability_key`, `report_sha256`...) se
  escapan con `sql_literal` y NO se rechazan: un texto hostil sale como literal, nunca como sentencia.
* Un `NUL` en un texto llega a `build_sql` como `SqlError` (o `AdapterError`): ambas son `ValueError`.
* Dentro de un `dict` los NaN/infinitos, los tipos no serializables y las cadenas con NUL (PostgreSQL no admite
  `\\u0000` en `jsonb`) son `SqlError`.
* El orden de las claves de `run` y de cada fila del conjunto de datos no altera el script: manda el orden de
  `RUN_COLUMNS` y `RESULT_COLUMNS`.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para apuntar
estas pruebas a una copia mutada. Las pruebas con PostgreSQL real son la tarea 5.1: aquí no hay base de datos.
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
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_sql", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

# Valores literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
    "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)
RUN_OUTPUT_KEYS = RUN_KEYS + ("is_real", "non_real_reasons", "comparability_key") + (
    "format", "milestone", "report_path", "report_sha256")
# Columnas de la base: las mismas que las claves salvo `commit` -> `commit_sha` y `count` -> `case_count`.
RUN_COLUMN_LIST = [
    "run_id", "source", "run_at", "commit_sha", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
    "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
    "is_real", "non_real_reasons", "comparability_key", "format", "milestone", "report_path", "report_sha256",
]
RESULT_COLUMN_LIST = [
    "measure_type", "grp", "metric_id", "behavior", "status", "case_count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
]

# Actualizado tras integrar develop: el informe de calibración de JUP-022 lo regenera JUP-120 (no es evidencia
# congelada), así que su fecha y su `run_id` se derivan del propio informe con json/hashlib/datetime (sin la
# herramienta): sha256 del JSON canónico y `jup-022-<aaaammddThhmmssZ en UTC>-<8 primeros hex>`. Los otros cuatro
# `run_id` siguen siendo literales de evidencia fija.
JUP_022_DOCUMENT = json.loads(
    (ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json").read_text(encoding="utf-8-sig"))
JUP_022_RUN_AT = JUP_022_DOCUMENT["generated_at"]
JUP_022_RUN_ID = "jup-022-{}-{}".format(
    datetime.fromisoformat(JUP_022_RUN_AT).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    hashlib.sha256(json.dumps(JUP_022_DOCUMENT, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True).encode("utf-8")).hexdigest()[:8])

REAL_RUN_IDS = [
    "jup-070-20261008T201354Z-37175957", "jup-070-20261008T210144Z-b64cca76", "jup-078-undated-7ea00edf",
    JUP_022_RUN_ID, "JUP-068-synthetic-example-v1",
    "jup130-anomalies-2026-10-30", "jup130-data-2026-10-30", "jup130-ai-cost-2026-10-09-to-2026-10-21",
    "JUP-071-a543144c9a55", "JUP-071-864a0d6dc666",
    "jup130-ai-cost-2026-10-21-to-2026-10-22", "jup-070-20261022T000000Z-2c5c6500",
]
REAL_ROW_COUNTS = [48, 48, 10, 140, 23, 16, 10, 13, 136, 136, 15, 52]

# Documento `rows-v1` mínimo y válido para las pruebas de la línea de comandos.
ROWS_DOCUMENT = {
    "contract_version": 1,
    "run": {
        "run_id": "JUP-071-demo-1", "source": "JUP-071", "run_at": "2026-10-10T09:00:00Z", "commit": "abc1234",
        "suite": "JUP-069", "suite_version": "JUP-069-v1", "retrieval": {"top_k": 4},
    },
    "results": [
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "pass",
         "count": 3, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "fail",
         "count": 1, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
    ],
}

# Dataset real (ocho informes versionados; el de JUP-068 ejecuta Node) fijado por `setUpModule`.
DATASET: dict = {}
_REAL_SCRIPT: dict = {}


def setUpModule() -> None:
    DATASET.update(tool.build_dataset([tool.DEFAULT_MANIFEST]))


def real_script() -> str:
    # Se calcula a la primera petición y no en `setUpModule`: así cada prueba falla por sí sola si `build_sql` no
    # existe, en lugar de caer todo el módulo en un único error de preparación.
    if "text" not in _REAL_SCRIPT:
        _REAL_SCRIPT["text"] = tool.build_sql(DATASET)
    return _REAL_SCRIPT["text"]


# --- Ayudantes de lectura del SQL (escritos aquí, independientes de la herramienta) -----------------------------


def unescape_literal(literal: str) -> str:
    """Invierte un literal de cadena SQL: comillas exteriores y cada comilla interior duplicada."""
    assert len(literal) >= 2 and literal[0] == "'" and literal[-1] == "'", f"no es un literal entre comillas: {literal[:40]!r}"
    inner = literal[1:-1]
    out, i = [], 0
    while i < len(inner):
        if inner[i] == "'":
            # Una comilla interior sin pareja cerraría la cadena antes de tiempo: ahí empezaría una inyección.
            assert inner[i + 1:i + 2] == "'", f"comilla interior sin duplicar en la posición {i}"
            out.append("'")
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


def split_statements(script: str) -> list[str]:
    """Trocea el script por `;` fuera de cadenas; descarta los comentarios `--` fuera de cadenas."""
    statements, current, i, in_string = [], [], 0, False
    while i < len(script):
        char = script[i]
        if in_string:
            current.append(char)
            if char == "'":
                # Una comilla duplicada cierra y reabre: el estado final es el correcto.
                in_string = False
        elif char == "'":
            in_string = True
            current.append(char)
        elif char == "-" and script.startswith("--", i):
            end = script.find("\n", i)
            i = len(script) if end < 0 else end
            continue
        elif char == ";":
            statements.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    assert not in_string, "cadena sin cerrar al final del script"
    assert "".join(current).strip() == "", "texto tras la última sentencia: falta el `;` final"
    return statements


def split_lines(text: str) -> list[str]:
    """Separa por salto de línea fuera de cadenas (una cadena hostil puede contener saltos)."""
    lines, current, in_string = [], [], False
    for char in text:
        if char == "'":
            in_string = not in_string
        if char == "\n" and not in_string:
            lines.append("".join(current))
            current = []
        else:
            current.append(char)
    lines.append("".join(current))
    return lines


NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def parse_string(text: str, pos: int) -> tuple[str, int]:
    assert text[pos] == "'", f"se esperaba una cadena en {text[pos:pos + 30]!r}"
    out, i = [], pos + 1
    while True:
        char = text[i]
        if char == "'":
            if text[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
                continue
            return "".join(out), i + 1
        out.append(char)
        i += 1


def parse_value(text: str, pos: int):
    """Un valor de tupla: None, bool, str, ("num", texto), ("jsonb", texto), ("timestamptz", texto), ("array", [...])."""
    while text[pos] == " ":
        pos += 1
    for word, value in (("NULL", None), ("TRUE", True), ("FALSE", False)):
        if text.startswith(word, pos) and not text[pos + len(word):pos + len(word) + 1].isalnum():
            return value, pos + len(word)
    if text[pos] == "'":
        value, pos = parse_string(text, pos)
        for cast in ("jsonb", "timestamptz"):
            if text.startswith(f"::{cast}", pos):
                return (cast, value), pos + len(cast) + 2
        return value, pos
    if text.startswith("ARRAY[", pos):
        pos += len("ARRAY[")
        items = []
        while text[pos] == " ":
            pos += 1
        while text[pos] != "]":
            item, pos = parse_string(text, pos)
            items.append(item)
            while text[pos] == " ":
                pos += 1
            if text[pos] == ",":
                pos += 1
                while text[pos] == " ":
                    pos += 1
        assert text.startswith("]::text[]", pos), f"el array no acaba en ::text[]: {text[pos:pos + 20]!r}"
        return ("array", items), pos + len("]::text[]")
    match = NUMBER_RE.match(text, pos)
    assert match, f"valor no reconocido: {text[pos:pos + 30]!r}"
    return ("num", match.group()), match.end()


def parse_tuple(line: str) -> list:
    assert line.startswith("  ("), f"la tupla no empieza por dos espacios y un paréntesis: {line[:40]!r}"
    pos, values = 3, []
    while True:
        value, pos = parse_value(line, pos)
        values.append(value)
        while line[pos] == " ":
            pos += 1
        if line[pos] == ",":
            pos += 1
            continue
        assert line[pos] == ")", f"se esperaba ) en {line[pos:pos + 20]!r}"
        pos += 1
        break
    assert line[pos:] in ("", ",", ";"), f"resto inesperado tras la tupla: {line[pos:pos + 20]!r}"
    return values


INSERT_RE = re.compile(r"INSERT INTO evaluation\.(runs|results)\s*\(([^)]*)\)\s*VALUES\s*\n(.*)\Z", re.DOTALL)


class Script:
    """Script SQL troceado: sentencias, bloques `INSERT` y sus tuplas ya leídas."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.statements = split_statements(text)

    def first_words(self) -> list[str]:
        return [statement.split(None, 1)[0].upper() if statement else "" for statement in self.statements]

    def inserts(self, table: str) -> list[tuple[list[str], list[list]]]:
        found = []
        for statement in self.statements:
            if not statement.startswith("INSERT"):
                continue
            match = INSERT_RE.match(statement)
            assert match, f"INSERT con forma inesperada: {statement[:80]!r}"
            if match.group(1) != table:
                continue
            columns = [column.strip() for column in match.group(2).split(",")]
            lines = split_lines(match.group(3))
            found.append((columns, [parse_tuple(line) for line in lines]))
        return found

    def rows(self, table: str) -> list[list]:
        return [row for _, rows in self.inserts(table) for row in rows]


def squash(sql: str) -> str:
    # Normaliza el espaciado: un solo espacio entre palabras y ninguno junto a `(`, `)` y `,`.
    text = re.sub(r"\s+", " ", sql.strip())
    return re.sub(r"\s*([(),])\s*", r"\1", text)


def split_top_level(body: str) -> list[str]:
    parts, depth, in_string, current = [], 0, False, []
    for char in body:
        if char == "'":
            in_string = not in_string
        if not in_string:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append("".join(current))
                current = []
                continue
        current.append(char)
    parts.append("".join(current))
    return parts


RUNS_ITEMS = [squash(item) for item in (
    "run_id text PRIMARY KEY", "source text NOT NULL", "run_at timestamptz", "commit_sha text", "suite text",
    "suite_version text", "suite_sha256 text", "corpus_sha256 text", "embedding_provider text",
    "embedding_alias text", "retrieval jsonb", "generation_model text", "prompt_sha256 text",
    "synthetic boolean NOT NULL", "generation_model_id text", "generation_provider text",
    "generation_quantization text", "gateway_config_sha256 text", "is_real boolean NOT NULL",
    "non_real_reasons text[] NOT NULL",
    "comparability_key text NOT NULL", "format text NOT NULL", "milestone boolean NOT NULL", "report_path text",
    "report_sha256 text NOT NULL",
)]
RESULTS_COLUMN_ITEMS = [squash(item) for item in (
    "run_id text NOT NULL REFERENCES evaluation.runs (run_id) ON DELETE CASCADE",
    "measure_type text NOT NULL CHECK (measure_type IN ('A','B'))",
    "grp text NOT NULL", "metric_id text NOT NULL", "behavior text NOT NULL",
    "status text NOT NULL CHECK (status IN ('pass','fail','blocked','not_run','measured','not_measured'))",
    "case_count bigint", "value double precision", "unit text NOT NULL", "numerator double precision",
    "denominator bigint", "ci_low double precision", "ci_high double precision",
    "judgment text CHECK (judgment IS NULL OR judgment IN ('automatic','human'))",
    "selected boolean NOT NULL DEFAULT false",
)]
RESULTS_CONSTRAINTS = sorted(squash(item) for item in (
    "PRIMARY KEY (run_id, grp, metric_id, behavior, status)",
    "CHECK (status <> 'not_measured' OR (value IS NULL AND numerator IS NULL AND case_count IS NULL "
    "AND ci_low IS NULL AND ci_high IS NULL))",
    "CHECK (status <> 'measured' OR value IS NOT NULL)",
))
CREATE_TABLE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS evaluation\.(runs|results)\((.*)\)\Z", re.DOTALL)
ALLOWED_FIRST_WORDS = {"BEGIN", "SET", "CREATE", "ALTER", "COMMENT", "TRUNCATE", "INSERT", "COMMIT"}
FORBIDDEN_RE = re.compile(r"PASSWORD|CREATE\s+ROLE|GRANT|DROP", re.IGNORECASE)


def assert_same(test: unittest.TestCase, actual, expected, what: str = "valor") -> None:
    """Igualdad con un mensaje corto: `assertEqual` sobre listas o textos largos calcula un diff muy lento al fallar."""
    if actual == expected:
        return
    size = min(len(actual), len(expected))
    index = next((i for i in range(size) if actual[i] != expected[i]), size)
    window = slice(max(index - 30, 0), index + 60)
    test.fail(f"{what}: difieren en el índice {index} (longitudes {len(actual)} y {len(expected)}): "
              f"{actual[window]!r} != {expected[window]!r}")


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def expected_cell(key: str, value):
    """Valor leído que debe tener una celda, calculado a partir del dato (no de la herramienta)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if key == "run_at":
        return ("timestamptz", value)
    if key == "retrieval":
        return ("jsonb", canonical(value))
    if key == "non_real_reasons":
        return ("array", list(value))
    if isinstance(value, int):
        return ("num", str(value))
    if isinstance(value, float):
        return ("num", repr(value))
    return value


def expected_run_cells(run: dict) -> list:
    return [expected_cell(key, run[key]) for key in RUN_OUTPUT_KEYS]


def expected_result_cells(run_id: str, row: dict) -> list:
    return [run_id] + [expected_cell(key, row[key]) for key in RESULT_KEYS]


# --- Conjuntos de datos sintéticos ----------------------------------------------------------------------------------


def make_run(run_id: str = "run-1", **fields) -> dict:
    run = {
        "run_id": run_id, "source": "SRC-1", "run_at": "2026-10-14T10:00:00Z", "commit": "abc1234",
        "suite": "JUP-069", "suite_version": "1.0.0", "suite_sha256": "ab" * 32, "corpus_sha256": "cd" * 32,
        "embedding_provider": "mock", "embedding_alias": "mock-alias",
        "retrieval": {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
        "generation_model": "modelo-1", "prompt_sha256": None, "synthetic": False,
        "generation_model_id": None, "generation_provider": None, "generation_quantization": None,
        "gateway_config_sha256": None,
        "is_real": True, "non_real_reasons": [], "comparability_key": "ef" * 32, "format": "rows-v1",
        "milestone": False, "report_path": "docs/evidence/informe.json", "report_sha256": "01" * 32,
    }
    run.update(fields)
    return run


def make_row(index: int, **fields) -> dict:
    row = {
        "measure_type": "A", "grp": "g", "metric_id": "M-1", "behavior": f"b{index}", "status": "measured",
        "count": None, "value": 0.5, "unit": "ms", "numerator": None, "denominator": None,
        "ci_low": None, "ci_high": None, "judgment": "automatic", "selected": False,
    }
    row.update(fields)
    return row


def make_dataset(*runs) -> dict:
    # Cada elemento es `(run, results)`.
    return {"dataset_version": 1, "runs": [{"run": run, "results": results} for run, results in runs]}


def reduced(run: dict) -> dict:
    return {key: run[key] for key in RUN_KEYS}


def chunk_sizes(script: Script) -> list[int]:
    return [len(rows) for _, rows in script.inserts("results")]


# --- Constantes -----------------------------------------------------------------------------------------------


class ConstantsTest(unittest.TestCase):
    def test_nombre_del_esquema_y_tamano_de_bloque(self) -> None:
        self.assertEqual(tool.SCHEMA_NAME, "evaluation")
        self.assertEqual(tool.INSERT_CHUNK, 500)
        self.assertIs(type(tool.INSERT_CHUNK), int)

    def test_columnas_de_ejecuciones_en_el_orden_del_contrato(self) -> None:
        # dict ordenado: clave del contrato -> columna; solo `commit` cambia de nombre.
        self.assertIsInstance(tool.RUN_COLUMNS, dict)
        self.assertEqual(list(tool.RUN_COLUMNS), list(RUN_OUTPUT_KEYS))
        self.assertEqual(list(tool.RUN_COLUMNS.values()), RUN_COLUMN_LIST)
        self.assertEqual(len(tool.RUN_COLUMNS), 25)
        self.assertEqual(tool.RUN_COLUMNS["commit"], "commit_sha")

    def test_columnas_de_resultados_en_el_orden_del_contrato(self) -> None:
        self.assertIsInstance(tool.RESULT_COLUMNS, dict)
        self.assertEqual(list(tool.RESULT_COLUMNS), list(RESULT_KEYS))
        self.assertEqual(list(tool.RESULT_COLUMNS.values()), RESULT_COLUMN_LIST)
        self.assertEqual(len(tool.RESULT_COLUMNS), 14)
        self.assertEqual(tool.RESULT_COLUMNS["count"], "case_count")

    def test_las_columnas_siguen_a_las_claves_de_la_herramienta(self) -> None:
        # Si el contrato `rows-v1` cambia, las columnas deben cambiar con él: la herramienta no puede divergir.
        self.assertEqual(tuple(tool.RUN_COLUMNS), tool.RUN_OUTPUT_KEYS)
        self.assertEqual(tuple(tool.RESULT_COLUMNS), tool.RESULT_KEYS)

    def test_sql_error_es_un_value_error(self) -> None:
        self.assertTrue(issubclass(tool.SqlError, ValueError))
        self.assertIsNot(tool.SqlError, ValueError)

    def test_firma_de_build_sql_y_sql_literal(self) -> None:
        self.assertEqual(list(inspect.signature(tool.build_sql).parameters), ["dataset"])
        self.assertEqual(list(inspect.signature(tool.sql_literal).parameters), ["value"])


# --- sql_literal ------------------------------------------------------------------------------------------------

# Cadenas hostiles (sin NUL, que se rechaza aparte): comillas, barras, cierre de esquema, dólares, comentarios,
# saltos, tabuladores, unicode, vacía y larga.
HOSTILE = [
    "'", "''", "'''", "\\", "\\\\", "\\'", "'\\", "';DROP SCHEMA evaluation;--", "x'); DROP SCHEMA evaluation; --",
    "$$", "$tag$ ' $tag$", "--", "/*", "*/", "a\nb", "a\r\nb", "\n", "\t", "é", "日本語", "😀",
    "mezcla ' \\ \n \t é 😀 ''", "", "a" * 10000, "'" * 1000, "%s", "{}", ":nombre", chr(0x2028), "\x1a", "\x7f", " ",
]


class SqlLiteralScalarsTest(unittest.TestCase):
    def test_none_es_null(self) -> None:
        self.assertEqual(tool.sql_literal(None), "NULL")

    def test_booleanos_antes_que_enteros(self) -> None:
        # bool es subclase de int: sin el orden correcto `True` saldría como `1`.
        self.assertEqual(tool.sql_literal(True), "TRUE")
        self.assertEqual(tool.sql_literal(False), "FALSE")

    def test_enteros_en_decimal_y_cero_no_es_falso_ni_nulo(self) -> None:
        for value, expected in ((0, "0"), (1, "1"), (-5, "-5"), (42, "42"), (9007199254740991, "9007199254740991"),
                                (-9007199254740991, "-9007199254740991"), (9007199254740993, "9007199254740993"),
                                (10 ** 30, "1" + "0" * 30)):
            with self.subTest(value=value):
                result = tool.sql_literal(value)
                self.assertEqual(result, expected)
                self.assertIs(type(result), str)

    def test_floats_con_repr(self) -> None:
        # `repr` es la forma más corta que reconstruye el mismo float: ni pierde precisión ni añade ruido.
        for value, expected in ((0.1, "0.1"), (1e308, "1e+308"), (-0.0, "-0.0"), (0.0, "0.0"), (1.0, "1.0"),
                                (-1.5, "-1.5"), (5e-324, "5e-324"), (1e16, "1e+16"), (1e-7, "1e-07"),
                                (123456789.123, "123456789.123"), (0.30000000000000004, "0.30000000000000004"),
                                (1.7976931348623157e308, "1.7976931348623157e+308")):
            with self.subTest(value=value):
                self.assertEqual(tool.sql_literal(value), expected)
                self.assertEqual(float(tool.sql_literal(value)), value)

    def test_el_float_entero_conserva_el_punto(self) -> None:
        # 4.0 no es 4: el tipo del dato se conserva en el texto.
        self.assertEqual(tool.sql_literal(4.0), "4.0")
        self.assertEqual(tool.sql_literal(4), "4")

    def test_nan_e_infinitos_son_error(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal(value)

    def test_tipos_ajenos_son_error(self) -> None:
        for value in ((1, 2), (), {1, 2}, frozenset(), b"abc", bytearray(b"x"), object(), 1 + 2j,
                      (char for char in "ab"), Path("x"), range(3)):
            with self.subTest(tipo=type(value).__name__):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal(value)


class SqlLiteralStringsTest(unittest.TestCase):
    def test_cadenas_simples(self) -> None:
        self.assertEqual(tool.sql_literal("abc"), "'abc'")
        self.assertEqual(tool.sql_literal(""), "''")
        self.assertEqual(tool.sql_literal(" "), "' '")

    def test_la_comilla_simple_se_duplica(self) -> None:
        self.assertEqual(tool.sql_literal("it's"), "'it''s'")
        self.assertEqual(tool.sql_literal("'"), "''''")
        self.assertEqual(tool.sql_literal("''"), "''''''")
        self.assertEqual(tool.sql_literal("'a'"), "'''a'''")

    def test_la_barra_invertida_no_se_toca(self) -> None:
        # El script fija `standard_conforming_strings = on`: la barra no es un escape y duplicarla cambiaría el dato.
        self.assertEqual(tool.sql_literal("\\"), "'\\'")
        self.assertEqual(tool.sql_literal("\\\\"), "'\\\\'")
        self.assertEqual(tool.sql_literal("a\\'b"), "'a\\''b'")

    def test_saltos_tabuladores_y_unicode_se_conservan_tal_cual(self) -> None:
        self.assertEqual(tool.sql_literal("a\nb"), "'a\nb'")
        self.assertEqual(tool.sql_literal("a\tb"), "'a\tb'")
        self.assertEqual(tool.sql_literal("é😀"), "'é😀'")

    def test_nul_es_error_en_cualquier_posicion(self) -> None:
        # PostgreSQL no admite NUL en un texto: se rechaza en lugar de truncar en silencio.
        for text in ("\x00", "a\x00", "\x00a", "ab\x00cd", "'\x00'"):
            with self.subTest(text=repr(text)):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal(text)

    def test_bateria_hostil_el_literal_es_una_sola_cadena_y_se_desescapa_al_original(self) -> None:
        for text in HOSTILE:
            with self.subTest(text=text[:30]):
                literal = tool.sql_literal(text)
                self.assertTrue(literal.startswith("'") and literal.endswith("'"))
                # Cada comilla del dato aparece duplicada y solo hay dos comillas más: las exteriores.
                self.assertEqual(literal.count("'"), 2 + 2 * text.count("'"))
                # El desescapador falla si queda una comilla suelta (cadena cerrada antes de tiempo).
                self.assertEqual(unescape_literal(literal), text)

    def test_una_inyeccion_clasica_queda_dentro_del_literal(self) -> None:
        literal = tool.sql_literal("x'); DROP SCHEMA evaluation; --")
        self.assertEqual(literal, "'x''); DROP SCHEMA evaluation; --'")
        # Troceado con el separador que respeta comillas: una sola sentencia, sin `DROP` fuera de la cadena.
        self.assertEqual(split_statements(f"SELECT {literal};"), [f"SELECT {literal}"])


class SqlLiteralListsTest(unittest.TestCase):
    def test_lista_de_cadenas(self) -> None:
        self.assertEqual(tool.sql_literal(["a", "b"]), "ARRAY['a','b']::text[]")
        self.assertEqual(tool.sql_literal(["plantilla", "doble"]), "ARRAY['plantilla','doble']::text[]")
        self.assertEqual(tool.sql_literal(["solo"]), "ARRAY['solo']::text[]")

    def test_lista_vacia_lleva_el_cast(self) -> None:
        # `ARRAY[]` sin tipo no es válido en PostgreSQL: el cast es obligatorio.
        self.assertEqual(tool.sql_literal([]), "ARRAY[]::text[]")

    def test_los_elementos_se_escapan(self) -> None:
        self.assertEqual(tool.sql_literal(["it's", ""]), "ARRAY['it''s','']::text[]")

    def test_elementos_hostiles_se_leen_de_vuelta(self) -> None:
        literal = tool.sql_literal(HOSTILE)
        value, end = parse_value(literal, 0)
        self.assertEqual(end, len(literal))
        self.assertEqual(value, ("array", HOSTILE))

    def test_un_elemento_que_no_es_cadena_es_error(self) -> None:
        for bad in ([1], ["a", 2], [None], ["a", None], [True], [["a"]], [{"a": 1}], ["a", b"b"], [1.5]):
            with self.subTest(lista=bad):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal(bad)

    def test_un_elemento_con_nul_es_error(self) -> None:
        with self.assertRaises(tool.SqlError):
            tool.sql_literal(["a", "b\x00"])


class SqlLiteralJsonTest(unittest.TestCase):
    def test_ejemplo_del_contrato_con_claves_ordenadas(self) -> None:
        self.assertEqual(tool.sql_literal({"top_k": 4, "chunk_size": 500}), "'{\"chunk_size\":500,\"top_k\":4}'::jsonb")
        self.assertEqual(tool.sql_literal({"chunk_size": 500, "top_k": 4}), "'{\"chunk_size\":500,\"top_k\":4}'::jsonb")

    def test_diccionario_vacio(self) -> None:
        self.assertEqual(tool.sql_literal({}), "'{}'::jsonb")

    def test_anidado_con_todos_los_tipos_json(self) -> None:
        value = {"z": [1, None, True, False, {"b": 1.5, "a": "x"}], "a": {"k": -0.0}}
        self.assertEqual(tool.sql_literal(value),
                         "'" + '{"a":{"k":-0.0},"z":[1,null,true,false,{"a":"x","b":1.5}]}' + "'::jsonb")

    def test_numeros_extremos(self) -> None:
        value = {"a": 1e308, "b": -0.0, "c": 2 ** 53 - 1, "d": 2 ** 53 + 1, "e": 10 ** 30, "f": 5e-324}
        self.assertEqual(
            tool.sql_literal(value),
            "'" + '{"a":1e+308,"b":-0.0,"c":9007199254740991,"d":9007199254740993,"e":' + "1" + "0" * 30
            + ',"f":5e-324}' + "'::jsonb")

    def test_las_no_ascii_se_escapan_en_el_json(self) -> None:
        # ensure_ascii=True: el script entero es ASCII y no depende de la codificación del terminal.
        bar = chr(92)
        expected = '{"%su00e9":"%su00f1%sud83d%sude00"}' % (bar, bar, bar, bar)
        self.assertEqual(tool.sql_literal({"é": "ñ😀"}), "'" + expected + "'::jsonb")
        self.assertTrue(tool.sql_literal({"é": "ñ"}).isascii())

    def test_la_comilla_dentro_del_json_se_duplica_en_el_literal(self) -> None:
        # La duplicación se aplica al texto JSON ya serializado: si no, `it's` cerraría la cadena.
        self.assertEqual(tool.sql_literal({"a": "it's"}), "'" + '{"a":"it\'\'s"}' + "'::jsonb")
        self.assertEqual(tool.sql_literal({"it's": 1}), "'" + '{"it\'\'s":1}' + "'::jsonb")

    def test_bateria_hostil_como_valor_y_como_clave(self) -> None:
        for text in HOSTILE:
            with self.subTest(text=text[:30]):
                for value in ({"k": text}, {text: 1}):
                    literal = tool.sql_literal(value)
                    self.assertTrue(literal.endswith("'::jsonb"))
                    body = unescape_literal(literal[:-len("::jsonb")])
                    self.assertEqual(body, canonical(value))
                    self.assertEqual(json.loads(body), value)

    def test_nan_e_infinito_dentro_del_diccionario_son_error(self) -> None:
        # `NaN` no es JSON: jsonb lo rechazaría. Se detecta aquí y no al ejecutar el script.
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                for container in ({"a": value}, {"a": [value]}, {"a": {"b": value}}):
                    with self.assertRaises(tool.SqlError):
                        tool.sql_literal(container)

    def test_tipos_no_serializables_dentro_del_diccionario_son_error(self) -> None:
        for inner in ({1, 2}, b"x", object(), Path("x")):
            with self.subTest(tipo=type(inner).__name__):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal({"a": inner})

    def test_nul_dentro_del_diccionario_es_error(self) -> None:
        # json.dumps lo escribe como `\u0000`, que jsonb no admite: sin esta comprobación el fallo llegaría a la base.
        for value in ({"a": "x\x00y"}, {"x\x00y": 1}, {"a": ["\x00"]}, {"a": {"b": "\x00"}}):
            with self.subTest(valor=value):
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal(value)

    def test_el_diccionario_no_se_muta(self) -> None:
        value = {"b": [1, {"d": 1, "c": 2}], "a": None}
        snapshot = copy.deepcopy(value)
        tool.sql_literal(value)
        self.assertEqual(value, snapshot)
        self.assertEqual(list(value), ["b", "a"])


# --- build_sql: estructura del script real ------------------------------------------------------------------------


class BuildSqlStructureTest(unittest.TestCase):
    def test_forma_general_del_script(self) -> None:
        script = real_script()
        self.assertIs(type(script), str)
        self.assertTrue(script.startswith("BEGIN;"), script[:40])
        self.assertTrue(script.endswith("COMMIT;\n"), script[-40:])
        self.assertFalse(script.endswith("\n\n"))
        # UTF-8, `\n` y sin traducción de saltos de línea; el JSON escapa lo no ASCII, así que el dato real es ASCII.
        self.assertNotIn("\r", script)
        self.assertTrue(script.isascii())

    def test_primera_y_ultima_sentencia(self) -> None:
        statements = Script(real_script()).statements
        self.assertEqual(statements[0], "BEGIN")
        self.assertEqual(statements[-1], "COMMIT")
        # Una sola transacción: ni otro BEGIN ni otro COMMIT en medio.
        self.assertEqual(statements.count("BEGIN"), 1)
        self.assertEqual(statements.count("COMMIT"), 1)
        self.assertNotIn("ROLLBACK", statements)

    def test_sentencias_permitidas_y_orden_de_las_secciones(self) -> None:
        script = Script(real_script())
        words = script.first_words()
        self.assertTrue(set(words) <= ALLOWED_FIRST_WORDS, sorted(set(words) - ALLOWED_FIRST_WORDS))
        squashed = [squash(statement) for statement in script.statements]
        self.assertEqual(squashed[1], "SET LOCAL standard_conforming_strings = on")
        self.assertEqual(squashed[2], "CREATE SCHEMA IF NOT EXISTS evaluation")
        truncates = [index for index, statement in enumerate(squashed) if statement.startswith("TRUNCATE")]
        self.assertEqual(len(truncates), 1)
        truncate = truncates[0]
        self.assertEqual(squashed[truncate], "TRUNCATE evaluation.results,evaluation.runs")
        tables = {match.group(1): index for index, statement in enumerate(squashed)
                  if (match := CREATE_TABLE_RE.match(statement))}
        self.assertEqual(set(tables), {"runs", "results"})
        # esquema -> tablas (runs antes que results, que la referencia) -> vaciado.
        self.assertTrue(2 < tables["runs"] < tables["results"] < truncate, (tables, truncate))
        # Entre el esquema y el vaciado solo puede haber DDL (3.2 y 3.3 añadirán la vista y el rol).
        for statement_words in words[3:truncate]:
            self.assertIn(statement_words, {"CREATE", "ALTER", "COMMENT"})
        # Tras el vaciado solo hay inserciones y el cierre; ejecuciones primero y resultados después.
        tail = words[truncate + 1:-1]
        self.assertEqual(tail, ["INSERT", "INSERT", "INSERT"])
        self.assertTrue(squashed[truncate + 1].startswith("INSERT INTO evaluation.runs("))
        self.assertTrue(squashed[truncate + 2].startswith("INSERT INTO evaluation.results("))
        self.assertTrue(squashed[truncate + 3].startswith("INSERT INTO evaluation.results("))

    def test_las_tablas_tienen_las_columnas_y_restricciones_del_contrato(self) -> None:
        by_table = {}
        for statement in Script(real_script()).statements:
            match = CREATE_TABLE_RE.match(squash(statement))
            if match:
                by_table[match.group(1)] = split_top_level(match.group(2))
        # Columnas en orden exacto; las restricciones de tabla, como conjunto (su orden no es contrato).
        self.assertEqual(by_table["runs"], RUNS_ITEMS)
        self.assertEqual(len(by_table["runs"]), 25)
        results = by_table["results"]
        self.assertEqual(results[:15], RESULTS_COLUMN_ITEMS)
        self.assertEqual(sorted(results[15:]), RESULTS_CONSTRAINTS)

    def test_lo_no_medido_no_puede_ser_cero_ni_en_la_base(self) -> None:
        # Las dos restricciones de coherencia (regla 1 del contrato) se repiten como CHECK de la tabla.
        text = squash(real_script())
        self.assertIn(squash("CHECK (status <> 'not_measured' OR (value IS NULL AND numerator IS NULL AND "
                             "case_count IS NULL AND ci_low IS NULL AND ci_high IS NULL))"), text)
        self.assertIn(squash("CHECK (status <> 'measured' OR value IS NOT NULL)"), text)

    def test_las_columnas_de_los_insert_son_las_del_contrato(self) -> None:
        script = Script(real_script())
        (runs_columns, _), = script.inserts("runs")
        results_inserts = script.inserts("results")
        self.assertEqual(runs_columns, RUN_COLUMN_LIST)
        # Con más de 500 filas los resultados salen en dos bloques; todos con las mismas columnas.
        self.assertEqual([columns for columns, _ in results_inserts], [["run_id"] + RESULT_COLUMN_LIST] * len(results_inserts))

    def test_numero_de_tuplas_y_un_unico_bloque_de_resultados(self) -> None:
        script = Script(real_script())
        self.assertEqual(len(script.rows("runs")), 12)
        self.assertEqual(len(script.rows("results")), 647)
        self.assertEqual(sum(REAL_ROW_COUNTS), 647)
        self.assertEqual(len(script.inserts("runs")), 1)
        # Con 647 filas (> 500) hay dos bloques: el corte es sobre la lista global, no por ejecución.
        self.assertEqual(chunk_sizes(script), [500, 147])
        self.assertTrue(all(size <= 500 for size in chunk_sizes(script)))

    def test_cada_insert_lleva_una_tupla_por_linea_separadas_por_coma_y_acaba_en_punto_y_coma(self) -> None:
        text = real_script()
        pattern = re.compile(
            r"^INSERT INTO evaluation\.(runs|results)\s*\([^)]*\)\s*VALUES\n((?:  \(.*\),\n)*  \(.*\);\n)", re.MULTILINE)
        matches = list(pattern.finditer(text))
        self.assertEqual([match.group(1) for match in matches], ["runs", "results", "results"])
        self.assertEqual([match.group(2).count("\n") for match in matches], [12, 500, 147])
        # Todas las sentencias INSERT del script están cubiertas por el patrón (ninguna con otra forma).
        self.assertEqual(len(re.findall(r"^INSERT INTO", text, re.MULTILINE)), 3)


class BuildSqlValuesTest(unittest.TestCase):
    def test_cada_tupla_de_ejecucion_tiene_los_valores_esperados_y_en_orden(self) -> None:
        rows = Script(real_script()).rows("runs")
        self.assertEqual(len(rows), len(DATASET["runs"]))
        for index, (cells, item) in enumerate(zip(rows, DATASET["runs"])):
            with self.subTest(run=REAL_RUN_IDS[index]):
                self.assertEqual(len(cells), 25)
                self.assertEqual(cells, expected_run_cells(item["run"]))
        self.assertEqual([cells[0] for cells in rows], REAL_RUN_IDS)

    def test_cada_tupla_de_resultado_tiene_los_valores_esperados_el_run_id_de_su_ejecucion_y_el_orden(self) -> None:
        rows = Script(real_script()).rows("results")
        expected = [expected_result_cells(item["run"]["run_id"], row)
                    for item in DATASET["runs"] for row in item["results"]]
        self.assertEqual(len(rows), len(expected))
        for index, (cells, wanted) in enumerate(zip(rows, expected)):
            self.assertEqual(cells, wanted, f"tupla {index}")
        # El run_id de cada tupla es el de su ejecución, en bloques contiguos del tamaño de cada informe.
        wanted_ids = [run_id for run_id, count in zip(REAL_RUN_IDS, REAL_ROW_COUNTS) for _ in range(count)]
        assert_same(self, [cells[0] for cells in rows], wanted_ids, "run_id de cada tupla")

    def test_la_fila_no_medida_de_ahorro_realizado_de_jup_068_lleva_null_y_no_ceros(self) -> None:
        text = real_script()
        lines = [line for line in text.split("\n") if "'realized_savings'" in line]
        self.assertEqual(len(lines), 1)
        cells = parse_tuple(lines[0])
        self.assertEqual(cells, ["JUP-068-synthetic-example-v1", "B", "savings", "realized_savings", "all",
                                 "not_measured", None, None, "eur_minor_2", None, None, None, None, None, False])
        # En el texto: NULL (sin comillas ni cero) en case_count y value, y en numerador, denominador, intervalo y juicio.
        self.assertRegex(lines[0], r"'not_measured',\s*NULL,\s*NULL,\s*'eur_minor_2',\s*NULL,\s*NULL,\s*NULL,\s*NULL,\s*NULL,\s*FALSE\)")

    def test_los_metadatos_nulos_de_las_ejecuciones_reales_salen_como_null(self) -> None:
        # Las tuplas de ejecución son las de 25 celdas; las de resultado tienen 15.
        by_id = {parse_tuple(line)[0]: line for line in real_script().split("\n")
                 if line.startswith("  (") and len(parse_tuple(line)) == 25}
        self.assertEqual(sorted(by_id), sorted(REAL_RUN_IDS))
        # JUP-022 no registra la huella de la batería ni el commit; JUP-070 no registra el prompt.
        jup_022 = parse_tuple(by_id[JUP_022_RUN_ID])
        self.assertEqual((jup_022[3], jup_022[6], jup_022[11], jup_022[12]), (None, None, None, None))
        for run_id in ("jup-070-20261008T201354Z-37175957", "jup-070-20261008T210144Z-b64cca76"):
            self.assertIsNone(parse_tuple(by_id[run_id])[12])
        # JUP-078 no registra nada salvo la fuente, el formato y la huella: 11 NULL (run_at ... prompt_sha256) y los
        # cuatro campos de identidad del modelo, que ningún informe antiguo trae.
        self.assertEqual(by_id["jup-078-undated-7ea00edf"].count("NULL"), 15)

    def test_ningun_nulo_se_escribe_como_cadena_vacia_ni_como_cero(self) -> None:
        # El dato real no contiene cadenas vacías: cualquier `''` del script sería un NULL mal escrito.
        script = Script(real_script())
        inserts = "\n".join(statement for statement in script.statements if statement.startswith("INSERT"))
        self.assertNotIn("''", inserts)
        self.assertNotIn("'NULL'", inserts)
        self.assertNotIn("'None'", inserts)
        self.assertNotIn("None", inserts)

    def test_retrieval_como_jsonb_con_las_claves_ordenadas(self) -> None:
        text = real_script()
        self.assertIn('\'{"chunk_overlap":50,"chunk_size":500,"max_distance":0.6,"top_k":4}\'::jsonb', text)
        self.assertIn('\'{"chunk_overlap":50,"chunk_size":500,"max_distance":null,"top_k":4}\'::jsonb', text)
        self.assertIn('\'{"chunk_overlap":50,"chunk_size":500}\'::jsonb', text)
        # Campaña del banco con el modelo nuevo (JUP-133): top_k 12 por los vecinos que añade el producto.
        self.assertIn('\'{"chunk_overlap":50,"chunk_size":500,"max_distance":null,"top_k":12}\'::jsonb', text)
        self.assertEqual(text.count("::jsonb"), 4)

    def test_retrieval_none_es_null_y_no_un_jsonb(self) -> None:
        # JUP-078 y JUP-068 no traen `retrieval`: columna 11 a NULL (no la cadena 'null'::jsonb ni '{}').
        rows = Script(real_script()).rows("runs")
        self.assertEqual(rows[2][10], None)
        self.assertEqual(rows[4][10], None)
        self.assertNotIn("'null'", real_script())
        self.assertNotIn("'{}'", real_script())

    def test_run_at_con_cast_o_null(self) -> None:
        text = real_script()
        self.assertIn("'2026-10-08T20:13:54Z'::timestamptz", text)
        self.assertIn("'2026-10-08T21:01:44Z'::timestamptz", text)
        # Actualizado tras integrar develop: la fecha de la calibración es la `generated_at` del informe regenerado
        # (antes el literal 2026-10-03T07:15:32.826486+00:00), escrita tal cual con su cast.
        self.assertIn(f"'{JUP_022_RUN_AT}'::timestamptz", text)
        self.assertEqual(text.count("::timestamptz"), 10)
        rows = Script(real_script()).rows("runs")
        self.assertEqual([cells[2] is None for cells in rows], [False, False, True, False, True, False, False, False, False, False, False, False])

    def test_non_real_reasons_como_array_de_texto(self) -> None:
        text = real_script()
        self.assertIn("ARRAY['plantilla','doble']::text[]", text)
        self.assertEqual(text.count("ARRAY['plantilla']::text[]"), 1)
        self.assertEqual(text.count("ARRAY['sintetica']::text[]"), 3)
        self.assertEqual(text.count("ARRAY['sin_modelo_verificado']::text[]"), 2)
        # JUP-078, JUP-022 y el coste de IA de JUP-130 son reales: array vacío con su cast (no NULL, la columna es NOT NULL).
        self.assertEqual(text.count("ARRAY[]::text[]"), 5)
        rows = Script(real_script()).rows("runs")
        self.assertEqual([cells[19] for cells in rows], [
            ("array", ["plantilla", "doble"]), ("array", ["plantilla"]), ("array", []), ("array", []),
            ("array", ["sintetica"]), ("array", ["sintetica"]), ("array", ["sintetica"]), ("array", []),
            ("array", ["sin_modelo_verificado"]), ("array", ["sin_modelo_verificado"]), ("array", []), ("array", [])])

    def test_booleanos_en_mayusculas(self) -> None:
        rows = Script(real_script()).rows("runs")
        # synthetic (13), is_real (14) y milestone (18).
        self.assertEqual([cells[13] for cells in rows], [False, False, False, False, True, True, True, False, False, False, False, False])
        self.assertEqual([cells[18] for cells in rows], [False, False, True, True, False, False, False, True, False, False, True, True])
        self.assertEqual([cells[22] for cells in rows], [True] * 12)
        selected = [cells[14] for cells in Script(real_script()).rows("results")]
        self.assertIn(True, selected)
        self.assertIn(False, selected)
        inserts = "\n".join(s for s in Script(real_script()).statements if s.startswith("INSERT"))
        self.assertNotRegex(inserts, r"\b(true|false)\b")

    def test_hay_filas_seleccionadas_de_la_calibracion(self) -> None:
        # `selected` TRUE viene del barrido de JUP-022: el literal booleano debe salir sin comillas.
        rows = Script(real_script()).rows("results")
        self.assertEqual(sum(1 for cells in rows if cells[14] is True),
                         sum(1 for item in DATASET["runs"] for row in item["results"] if row["selected"] is True))
        self.assertGreater(sum(1 for cells in rows if cells[14] is True), 0)

    def test_las_rutas_de_los_informes_son_literales(self) -> None:
        text = real_script()
        for path in ("docs/evidence/JUP-070-run-1-report.json", "docs/spikes/JUP-022-retrieval-calibration.json"):
            self.assertIn(f"'{path}'", text)


# --- build_sql: conjuntos sintéticos -----------------------------------------------------------------------------


class BuildSqlSyntheticTest(unittest.TestCase):
    def test_bloques_de_500_con_el_orden_de_las_filas_conservado(self) -> None:
        # 1201 filas: 500 + 500 + 201.
        rows = [make_row(index) for index in range(1201)]
        # Guarda de las propias pruebas: si el apoyo fuera inválido, los errores de abajo serían ruido.
        tool.validate_rows(reduced(make_run()), rows)
        self.assertEqual(list(make_run()), list(RUN_OUTPUT_KEYS))
        script = Script(tool.build_sql(make_dataset((make_run(), rows))))
        self.assertEqual(chunk_sizes(script), [500, 500, 201])
        behaviors = [cells[4] for cells in script.rows("results")]
        assert_same(self, behaviors, [f"b{index}" for index in range(1201)], "orden de las filas")
        self.assertEqual(len(script.inserts("runs")), 1)

    def test_fronteras_del_tamano_de_bloque(self) -> None:
        for total in (1, 499, 500, 501, 999, 1000, 1001):
            with self.subTest(filas=total):
                expected = [500] * (total // 500) + ([total % 500] if total % 500 else [])
                script = Script(tool.build_sql(make_dataset((make_run(), [make_row(i) for i in range(total)]))))
                self.assertEqual(chunk_sizes(script), expected)
                self.assertEqual(len(script.rows("results")), total)

    def test_el_corte_en_bloques_es_sobre_la_lista_global_de_varias_ejecuciones(self) -> None:
        # Tres ejecuciones de 300 filas: 900 filas -> 500 + 400, con un bloque que mezcla dos ejecuciones.
        runs = [(make_run(f"run-{n}"), [make_row(i, grp=f"g{n}") for i in range(300)]) for n in range(3)]
        script = Script(tool.build_sql(make_dataset(*runs)))
        self.assertEqual(chunk_sizes(script), [500, 400])
        results = script.rows("results")
        assert_same(self, [cells[0] for cells in results], [f"run-{n}" for n in range(3) for _ in range(300)], "run_id")
        assert_same(self, [cells[2] for cells in results], [f"g{n}" for n in range(3) for _ in range(300)], "grp")
        self.assertEqual([cells[0] for cells in script.rows("runs")], ["run-0", "run-1", "run-2"])

    def test_conjunto_vacio_crea_esquema_y_tablas_y_vacia_sin_insert(self) -> None:
        text = tool.build_sql({"dataset_version": 1, "runs": []})
        script = Script(text)
        squashed = [squash(statement) for statement in script.statements]
        self.assertEqual(squashed[:3], ["BEGIN", "SET LOCAL standard_conforming_strings = on",
                                        "CREATE SCHEMA IF NOT EXISTS evaluation"])
        self.assertEqual(squashed[-2:], ["TRUNCATE evaluation.results,evaluation.runs", "COMMIT"])
        tables = [match.group(1) for statement in squashed if (match := CREATE_TABLE_RE.match(statement))]
        self.assertEqual(tables, ["runs", "results"])
        self.assertNotIn("INSERT", text.upper())
        self.assertTrue(text.startswith("BEGIN;") and text.endswith("COMMIT;\n"))

    def test_una_ejecucion_sin_filas_se_inserta_sin_bloque_de_resultados(self) -> None:
        # `INSERT ... VALUES` sin tuplas no es SQL válido: no debe emitirse.
        script = Script(tool.build_sql(make_dataset((make_run(), []))))
        self.assertEqual(len(script.rows("runs")), 1)
        self.assertEqual(script.inserts("results"), [])
        self.assertEqual(script.first_words().count("INSERT"), 1)

    def test_una_ejecucion_sin_filas_entre_otras_no_altera_las_demas(self) -> None:
        dataset = make_dataset((make_run("a"), [make_row(0)]), (make_run("b"), []), (make_run("c"), [make_row(1)]))
        script = Script(tool.build_sql(dataset))
        self.assertEqual([cells[0] for cells in script.rows("runs")], ["a", "b", "c"])
        self.assertEqual([cells[0] for cells in script.rows("results")], ["a", "c"])

    def test_numeros_extremos_en_filas_y_en_retrieval(self) -> None:
        retrieval = {"top_k": 2 ** 53 - 1, "max_distance": 1e308, "chunk_size": -0.0, "chunk_overlap": 0}
        rows = [
            make_row(0, value=1e308, numerator=-0.0, denominator=2 ** 53 - 1, ci_low=-1e308, ci_high=1e308),
            make_row(1, status="pass", value=None, count=2 ** 53 - 1, unit="casos", denominator=2 ** 53 - 1),
            make_row(2, status="not_measured", value=None, unit="tasa", denominator=0),
            make_row(3, value=0.0, unit="tasa", numerator=0, denominator=5),
            make_row(4, value=5e-324),
        ]
        dataset = make_dataset((make_run(retrieval=retrieval), rows))
        tool.validate_rows(reduced(dataset["runs"][0]["run"]), rows)
        text = tool.build_sql(dataset)
        self.assertIn('\'{"chunk_overlap":0,"chunk_size":-0.0,"max_distance":1e+308,"top_k":9007199254740991}\'::jsonb', text)
        script = Script(text)
        for cells, row in zip(script.rows("results"), rows):
            self.assertEqual(cells, expected_result_cells("run-1", row))
        first = script.rows("results")[0]
        # value, numerator, denominator, ci_low y ci_high (celdas 7 y 9 a 12 de la tupla de resultado).
        self.assertEqual([first[7]] + first[9:13], [("num", "1e+308"), ("num", "-0.0"), ("num", "9007199254740991"),
                                                    ("num", "-1e+308"), ("num", "1e+308")])
        # El cero medido es 0 y 0.0 (una medición), nunca NULL; el no medido conserva el denominador 0.
        zero = script.rows("results")[3]
        self.assertEqual((zero[7], zero[9], zero[10]), (("num", "0.0"), ("num", "0"), ("num", "5")))
        not_measured = script.rows("results")[2]
        self.assertEqual((not_measured[7], not_measured[9], not_measured[10]), (None, None, ("num", "0")))

    def test_run_at_con_desfase_y_fracciones_se_copia_tal_cual(self) -> None:
        for run_at in ("2026-10-14T10:00:00Z", "2026-10-14T10:00:00.5-05:30", "2026-10-14T10:00:00.123456+00:00", None):
            with self.subTest(run_at=run_at):
                text = tool.build_sql(make_dataset((make_run(run_at=run_at), [make_row(0)])))
                cells = Script(text).rows("runs")[0]
                self.assertEqual(cells[2], expected_cell("run_at", run_at))
                if run_at is not None:
                    self.assertIn(f"'{run_at}'::timestamptz", text)
                else:
                    self.assertNotIn("::timestamptz", text)

    def test_el_orden_de_las_claves_no_altera_el_script(self) -> None:
        # Manda el orden de RUN_COLUMNS y RESULT_COLUMNS, no el de los diccionarios del conjunto de datos.
        base = make_dataset((make_run(), [make_row(0), make_row(1, status="pass", value=None, count=2, unit="casos")]))
        shuffled = copy.deepcopy(base)
        entry = shuffled["runs"][0]
        entry["run"] = {key: entry["run"][key] for key in reversed(list(entry["run"]))}
        entry["run"]["retrieval"] = {key: entry["run"]["retrieval"][key] for key in reversed(list(entry["run"]["retrieval"]))}
        entry["results"] = [{key: row[key] for key in reversed(list(row))} for row in entry["results"]]
        shuffled["runs"] = [{"results": entry["results"], "run": entry["run"]}]
        self.assertEqual(tool.build_sql(shuffled), tool.build_sql(base))

    def test_textos_hostiles_en_columnas_sin_validacion_comun_quedan_dentro_del_literal(self) -> None:
        # `validate_rows` no mira report_path, format, comparability_key ni report_sha256: solo el escapado de
        # `sql_literal` impide que un texto como `x'); DROP SCHEMA evaluation; --` sea una sentencia.
        for field in ("report_path", "format", "comparability_key", "report_sha256"):
            for text in HOSTILE:
                with self.subTest(campo=field, texto=text[:25]):
                    dataset = make_dataset((make_run(**{field: text}), [make_row(0)]))
                    script = Script(tool.build_sql(dataset))
                    # Mismas sentencias que sin ataque: ninguna extra (un DROP suelto sería una sentencia más).
                    self.assertEqual(script.first_words().count("DROP"), 0)
                    self.assertTrue(set(script.first_words()) <= ALLOWED_FIRST_WORDS)
                    self.assertEqual(script.first_words().count("INSERT"), 2)
                    self.assertEqual(script.statements[-1], "COMMIT")
                    cells = script.rows("runs")[0]
                    self.assertEqual(cells[RUN_OUTPUT_KEYS.index(field)], text)
                    self.assertEqual(cells, expected_run_cells(dataset["runs"][0]["run"]))

    def test_texto_hostil_en_report_path_con_la_inyeccion_clasica(self) -> None:
        attack = "x'); DROP SCHEMA evaluation; --"
        text = tool.build_sql(make_dataset((make_run(report_path=attack), [make_row(0)])))
        self.assertIn("'x''); DROP SCHEMA evaluation; --'", text)
        script = Script(text)
        self.assertEqual(script.rows("runs")[0][23], attack)
        self.assertNotIn("DROP", [word for word in script.first_words()])

    def test_nul_en_una_columna_de_texto_es_error(self) -> None:
        for field in ("report_path", "format", "comparability_key"):
            with self.subTest(campo=field):
                with self.assertRaises((tool.SqlError, tool.AdapterError)):
                    tool.build_sql(make_dataset((make_run(**{field: "a\x00b"}), [make_row(0)])))

    def test_un_run_id_hostil_lo_rechaza_la_validacion_comun_con_la_ruta(self) -> None:
        attack = "x'); DROP SCHEMA evaluation; --"
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_sql(make_dataset((make_run(run_id=attack), [make_row(0)])))
        self.assertTrue(str(caught.exception).startswith("runs[0].run.run_id: "), str(caught.exception))

    def test_un_behavior_hostil_en_una_fila_lo_rechaza_la_validacion_comun_con_la_ruta(self) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_sql(make_dataset((make_run(), [make_row(0), make_row(1, behavior="x'); DROP TABLE t; --")])))
        self.assertTrue(str(caught.exception).startswith("runs[0].results[1].behavior: "), str(caught.exception))

    def test_run_ids_que_difieren_solo_en_mayusculas_son_distintos(self) -> None:
        # La clave primaria distingue mayúsculas: no es un duplicado.
        script = Script(tool.build_sql(make_dataset((make_run("Run-1"), []), (make_run("run-1"), []))))
        self.assertEqual([cells[0] for cells in script.rows("runs")], ["Run-1", "run-1"])


# --- build_sql: errores del conjunto de datos --------------------------------------------------------------------


class BuildSqlValidationTest(unittest.TestCase):
    def fail(self, dataset) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_sql(dataset)
        return str(caught.exception)

    def valid_entry(self, run_id: str = "run-1") -> dict:
        return {"run": make_run(run_id), "results": [make_row(0), make_row(1)]}

    def test_el_conjunto_no_es_un_diccionario(self) -> None:
        for dataset in ([], None, "x", 1, [self.valid_entry()], ("a",), 1.5, True):
            with self.subTest(dataset=repr(dataset)[:20]):
                self.assertTrue(self.fail(dataset).startswith("dataset: "))

    def test_dataset_version_distinta_de_uno_entero(self) -> None:
        # 2 es otra versión; True y 1.0 son «iguales» a 1 en Python pero no son el entero 1 del contrato.
        for version in (2, 0, -1, True, False, 1.0, "1", None, [1]):
            with self.subTest(version=repr(version)):
                message = self.fail({"dataset_version": version, "runs": []})
                self.assertTrue(message.startswith("dataset: "), message)
                self.assertIn("dataset_version", message)

    def test_dataset_version_ausente(self) -> None:
        message = self.fail({"runs": []})
        self.assertTrue(message.startswith("dataset: "), message)
        self.assertIn("dataset_version", message)

    def test_runs_ausente_o_no_es_lista(self) -> None:
        for dataset in ({"dataset_version": 1}, {"dataset_version": 1, "runs": None}, {"dataset_version": 1, "runs": {}},
                        {"dataset_version": 1, "runs": "x"}, {"dataset_version": 1, "runs": ()},
                        {"dataset_version": 1, "runs": 3}):
            with self.subTest(dataset=repr(dataset)):
                message = self.fail(dataset)
                self.assertTrue(message.startswith("dataset: "), message)
                self.assertIn("runs", message)

    def test_la_ejecucion_no_es_un_diccionario(self) -> None:
        for entry in (None, [], "x", 3, (self.valid_entry()["run"], [])):
            with self.subTest(entry=repr(entry)[:20]):
                message = self.fail({"dataset_version": 1, "runs": [self.valid_entry("a"), entry]})
                self.assertTrue(message.startswith("runs[1]: "), message)

    def test_la_ejecucion_sin_run_o_sin_results(self) -> None:
        for key in ("run", "results"):
            with self.subTest(falta=key):
                entry = self.valid_entry()
                del entry[key]
                message = self.fail({"dataset_version": 1, "runs": [entry]})
                self.assertTrue(message.startswith("runs[0]: "), message)
                self.assertIn(key, message)

    def test_la_ejecucion_con_clave_desconocida(self) -> None:
        entry = self.valid_entry()
        entry["extra"] = []
        message = self.fail({"dataset_version": 1, "runs": [entry]})
        self.assertTrue(message.startswith("runs[0]: "), message)
        self.assertIn("extra", message)

    def test_run_no_es_diccionario_o_results_no_es_lista(self) -> None:
        for broken, field in (({"run": None, "results": []}, "run"), ({"run": [], "results": []}, "run"),
                              ({"run": make_run(), "results": None}, "results"),
                              ({"run": make_run(), "results": {}}, "results"),
                              ({"run": make_run(), "results": ()}, "results")):
            with self.subTest(roto=repr(broken)[:40]):
                message = self.fail({"dataset_version": 1, "runs": [self.valid_entry("a"), broken]})
                self.assertTrue(message.startswith("runs[1]"), message)
                self.assertIn(field, message)

    def test_run_con_una_clave_de_clasificacion_ausente(self) -> None:
        for key in ("is_real", "non_real_reasons", "comparability_key", "format", "milestone", "report_path",
                    "report_sha256"):
            with self.subTest(falta=key):
                run = make_run()
                del run[key]
                message = self.fail(make_dataset((run, [make_row(0)])))
                self.assertTrue(message.startswith("runs[0]"), message)
                self.assertIn(key, message)

    def test_run_con_una_clave_del_contrato_ausente(self) -> None:
        run = make_run()
        del run["suite"]
        message = self.fail(make_dataset((make_run("a"), []), (run, [])))
        self.assertTrue(message.startswith("runs[1]"), message)
        self.assertIn("suite", message)

    def test_run_con_una_clave_desconocida(self) -> None:
        for extra in ("desconocida", "milestone2", "Run_id"):
            with self.subTest(clave=extra):
                run = make_run()
                run[extra] = 1
                message = self.fail(make_dataset((run, [make_row(0)])))
                self.assertTrue(message.startswith("runs[0]"), message)
                self.assertIn(extra, message)

    def test_los_errores_de_la_validacion_comun_llevan_la_ruta_de_la_ejecucion(self) -> None:
        # Mensaje = `runs[i].` + el de `validate_rows` (que ya trae `run.campo` o `results[j].campo`).
        cases = {
            "commit": (make_run(commit="texto libre con espacios"), [make_row(0)]),
            "retrieval": (make_run(retrieval={"top_k": "4"}), [make_row(0)]),
            "synthetic": (make_run(synthetic=1), [make_row(0)]),
            "run_at": (make_run(run_at="2026-13-45T00:00:00Z"), [make_row(0)]),
            "valor": (make_run(), [make_row(0), make_row(1), make_row(2, status="pass", value=0.5, count=1)]),
            "estado": (make_run(), [make_row(0), make_row(1, status="desconocido")]),
            "duplicada": (make_run(), [make_row(0), make_row(1), make_row(0)]),
            "no es fila": (make_run(), [make_row(0), 7]),
            "tasa": (make_run(), [make_row(0, unit="tasa", numerator=5, denominator=2)]),
        }
        for name, (run, rows) in cases.items():
            with self.subTest(caso=name):
                with self.assertRaises(tool.AdapterError) as inner:
                    tool.validate_rows(reduced(run), rows)
                # Se coloca en la posición 1 para comprobar que el índice es el de la ejecución y no el 0.
                message = self.fail(make_dataset((make_run("otra"), [make_row(0)]), (run, rows)))
                self.assertEqual(message, f"runs[1].{inner.exception}")

    def test_rutas_concretas(self) -> None:
        message = self.fail(make_dataset((make_run(commit="a b"), [make_row(0)])))
        self.assertTrue(message.startswith("runs[0].run.commit: "), message)
        message = self.fail(make_dataset((make_run(), [make_row(0), make_row(1), make_row(2, status="pass", value=0.5, count=1)])))
        self.assertTrue(message.startswith("runs[0].results[2].value: "), message)

    def test_el_primer_error_es_el_de_la_primera_ejecucion_defectuosa(self) -> None:
        dataset = make_dataset((make_run("a"), [make_row(0)]), (make_run("b", commit="a b"), []),
                               (make_run("c", source="x y"), []))
        self.assertTrue(self.fail(dataset).startswith("runs[1].run.commit: "))

    def test_run_id_duplicado(self) -> None:
        dataset = make_dataset((make_run("a"), [make_row(0)]), (make_run("b"), [make_row(0)]),
                               (make_run("a"), [make_row(1)]))
        message = self.fail(dataset)
        self.assertTrue(message.startswith("runs[2]"), message)
        self.assertIn("run_id", message)

    def test_los_errores_no_devuelven_script_parcial(self) -> None:
        # Atómico: o hay script completo o excepción; nunca una cadena con las ejecuciones válidas.
        dataset = make_dataset((make_run("a"), [make_row(0)]), (make_run("b", commit="a b"), []))
        with self.assertRaises(tool.AdapterError):
            tool.build_sql(dataset)


# --- Determinismo y pureza ------------------------------------------------------------------------------------


DRIVER = """\
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_sql_driver", sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
with open(sys.argv[2], encoding="utf-8") as stream:
    dataset = json.load(stream)
sys.stdout.buffer.write(module.build_sql(dataset).encode("utf-8"))
"""


class DeterminismAndPurityTest(unittest.TestCase):
    def test_dos_llamadas_iguales_dan_la_misma_cadena(self) -> None:
        assert_same(self, tool.build_sql(DATASET), tool.build_sql(DATASET), "dos llamadas")
        assert_same(self, tool.build_sql(DATASET), real_script(), "llamada y caché")
        assert_same(self, tool.build_sql(copy.deepcopy(DATASET)), real_script(), "copia profunda")

    def test_no_muta_el_conjunto_de_datos(self) -> None:
        snapshot = copy.deepcopy(DATASET)
        tool.build_sql(DATASET)
        self.assertEqual(DATASET, snapshot)
        self.assertEqual(list(DATASET["runs"][0]["run"]), list(RUN_OUTPUT_KEYS))
        small = make_dataset((make_run(non_real_reasons=["b", "a"]), [make_row(2), make_row(1)]))
        before = copy.deepcopy(small)
        tool.build_sql(small)
        self.assertEqual(small, before)
        self.assertEqual(small["runs"][0]["run"]["non_real_reasons"], ["b", "a"])
        self.assertEqual([row["behavior"] for row in small["runs"][0]["results"]], ["b2", "b1"])

    def test_no_reordena_las_ejecuciones_ni_las_filas(self) -> None:
        # El orden de entrada manda: ni ordena por run_id ni por la clave natural.
        dataset = make_dataset((make_run("z"), [make_row(9), make_row(1)]), (make_run("a"), [make_row(5)]))
        script = Script(tool.build_sql(dataset))
        self.assertEqual([cells[0] for cells in script.rows("runs")], ["z", "a"])
        self.assertEqual([cells[4] for cells in script.rows("results")], ["b9", "b1", "b5"])

    def test_el_orden_de_los_motivos_se_conserva(self) -> None:
        text = tool.build_sql(make_dataset((make_run(non_real_reasons=["doble", "plantilla"]), [])))
        self.assertIn("ARRAY['doble','plantilla']::text[]", text)

    def test_la_salida_es_identica_con_distintas_semillas_de_hash(self) -> None:
        # PYTHONHASHSEED cambia el orden de los conjuntos y de los hash de cadenas: un script que dependiera de ellos
        # (p. ej. al recorrer un `set`) saldría distinto entre procesos.
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        tmp = Path(holder.name).resolve()
        driver = tmp / "driver.py"
        driver.write_text(DRIVER, encoding="utf-8")
        data = tmp / "dataset.json"
        extra = make_dataset((make_run("extra-1", non_real_reasons=["sintetica", "plantilla", "doble"],
                                        retrieval={"top_k": 4, "chunk_size": 1, "max_distance": 0.5, "chunk_overlap": 0}),
                              [make_row(index) for index in range(7)]))
        dataset = {"dataset_version": 1, "runs": DATASET["runs"] + extra["runs"]}
        data.write_text(json.dumps(dataset), encoding="utf-8")
        outputs = []
        for seed in ("0", "1", "4242"):
            env = dict(os.environ)
            env["PYTHONHASHSEED"] = seed
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run([sys.executable, str(driver), str(TOOL_PATH), str(data)], capture_output=True,
                                       env=env, timeout=120, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            outputs.append(completed.stdout)
        # Comprobación positiva: no basta con que tres salidas vacías coincidan.
        self.assertGreater(len(outputs[0]), 10000)
        self.assertEqual(len(set(outputs)), 1)
        assert_same(self, outputs[0].decode("utf-8"), tool.build_sql(dataset), "subproceso y proceso actual")


class NoCredentialsTest(unittest.TestCase):
    def test_el_script_real_no_lleva_credenciales_roles_ni_borrados(self) -> None:
        # El rol de lectura y sus permisos son la tarea 3.3, y la contraseña nunca viaja en el script.
        self.assertIsNone(FORBIDDEN_RE.search(real_script()), FORBIDDEN_RE.search(real_script()))

    def test_el_script_vacio_y_el_sintetico_tampoco(self) -> None:
        for text in (tool.build_sql({"dataset_version": 1, "runs": []}),
                     tool.build_sql(make_dataset((make_run(), [make_row(0)])))):
            self.assertIsNone(FORBIDDEN_RE.search(text))

    def test_el_script_no_nombra_variables_de_entorno_ni_conexiones(self) -> None:
        text = real_script().upper()
        for word in ("GRAFANA_EVALUATION_DB", "POSTGRES://", "POSTGRESQL://", "HOST=", "SECRET", "TOKEN"):
            with self.subTest(palabra=word):
                self.assertNotIn(word, text)

    def test_ninguna_sentencia_borra_objetos(self) -> None:
        # El vaciado es TRUNCATE de las dos tablas del esquema, nunca DROP: la idempotencia no destruye el esquema.
        words = Script(real_script()).first_words()
        for forbidden in ("DROP", "DELETE", "UPDATE", "GRANT", "REVOKE", "SELECT"):
            self.assertNotIn(forbidden, words)


# --- Línea de comandos ---------------------------------------------------------------------------------------


def run_cli_bytes(*args, cwd=None):
    # Proceso real y SIN `text=True`: la traducción de saltos de línea ocurre al escribir en la salida estándar y solo
    # se ve si se leen los bytes tal cual salen.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]],
        capture_output=True, env=env, timeout=240, check=False, cwd=None if cwd is None else str(cwd),
    )


class TmpCase(unittest.TestCase):
    """Base con un directorio temporal resuelto (en Windows el temporal puede traer nombres cortos 8.3)."""

    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name).resolve()

    def write(self, relative: str, document) -> Path:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def local_manifest(self, name: str = "local", document=None, report_relative: str = "dentro/informe.json") -> Path:
        report = self.write(report_relative, ROWS_DOCUMENT if document is None else document)
        return self.write(f"{name}.json", {"manifest_version": 1, "runs": [
            {"path": str(report), "format": "rows-v1", "milestone": False}]})


class CliTest(TmpCase):
    def expected_local(self, manifest: Path) -> bytes:
        return tool.build_sql(tool.build_dataset([manifest], root=self.tmp)).encode("utf-8")

    def test_sql_con_el_versionado_imprime_el_script_en_bytes_utf8_sin_retornos_de_carro(self) -> None:
        completed = run_cli_bytes("sql")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, real_script().encode("utf-8"))
        self.assertNotIn(b"\r", completed.stdout)
        self.assertTrue(completed.stdout.startswith(b"BEGIN;"))
        self.assertTrue(completed.stdout.endswith(b"COMMIT;\n"))
        self.assertFalse(completed.stdout.endswith(b"\n\n"))
        self.assertFalse(completed.stdout.startswith(b"\xef\xbb\xbf"))

    def test_la_salida_estandar_es_identica_byte_a_byte_al_fichero_de_output_y_entre_ejecuciones(self) -> None:
        output = self.tmp / "carga.sql"
        via_file = run_cli_bytes("sql", "--output", output)
        self.assertEqual(via_file.returncode, 0, via_file.stderr)
        self.assertEqual(via_file.stdout, b"")
        self.assertEqual(via_file.stderr, b"")
        first = run_cli_bytes("sql")
        second = run_cli_bytes("sql")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, output.read_bytes())
        self.assertGreater(len(first.stdout), 10000)

    def test_output_se_escribe_de_forma_atomica_sin_dejar_temporales_y_reemplaza_lo_anterior(self) -> None:
        directory = self.tmp / "salida"
        directory.mkdir()
        target = directory / "carga.sql"
        target.write_text("x" * 100000, encoding="utf-8")
        manifest = self.local_manifest()
        completed = run_cli_bytes("sql", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(target.read_bytes(), self.expected_local(manifest))
        self.assertNotIn(b"xxxx", target.read_bytes())
        self.assertEqual(sorted(os.listdir(directory)), ["carga.sql"])

    def test_manifiesto_local_sin_versionado_y_report_path_relativo_a_root(self) -> None:
        manifest = self.local_manifest()
        completed = run_cli_bytes("sql", "--no-versioned", "--manifest", manifest, "--root", self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, self.expected_local(manifest))
        script = Script(completed.stdout.decode("utf-8"))
        runs = script.rows("runs")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0][0], "JUP-071-demo-1")
        self.assertEqual(runs[0][23], "dentro/informe.json")
        self.assertEqual(len(script.rows("results")), 2)

    def test_root_fuera_del_informe_deja_report_path_en_null(self) -> None:
        manifest = self.local_manifest()
        other = self.tmp / "otra-raiz"
        other.mkdir()
        completed = run_cli_bytes("sql", "--no-versioned", "--manifest", manifest, "--root", other)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIsNone(Script(completed.stdout.decode("utf-8")).rows("runs")[0][23])

    def test_varios_manifiestos_conservan_el_orden_de_la_linea_de_comandos(self) -> None:
        first_doc, second_doc = copy.deepcopy(ROWS_DOCUMENT), copy.deepcopy(ROWS_DOCUMENT)
        first_doc["run"]["run_id"], second_doc["run"]["run_id"] = "JUP-071-primero", "JUP-071-segundo"
        second = self.local_manifest("segundo", second_doc, "a/segundo.json")
        first = self.local_manifest("primero", first_doc, "a/primero.json")
        completed = run_cli_bytes("sql", "--no-versioned", "--manifest", second, "--manifest", first, "--root", self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ids = [cells[0] for cells in Script(completed.stdout.decode("utf-8")).rows("runs")]
        self.assertEqual(ids, ["JUP-071-segundo", "JUP-071-primero"])

    def test_no_versioned_sin_manifiestos_da_el_script_sin_inserciones(self) -> None:
        completed = run_cli_bytes("sql", "--no-versioned", "--root", self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, tool.build_sql({"dataset_version": 1, "runs": []}).encode("utf-8"))
        self.assertNotIn(b"INSERT", completed.stdout.upper())
        self.assertIn(b"TRUNCATE", completed.stdout)
        self.assertNotIn(b"\r", completed.stdout)

    def test_manifiesto_inexistente_termina_con_1_sin_salida_ni_fichero(self) -> None:
        target = self.tmp / "carga.sql"
        for extra in ((), ("--output", target)):
            with self.subTest(output=bool(extra)):
                completed = run_cli_bytes("sql", "--no-versioned", "--manifest", self.tmp / "no-existe.json",
                                          "--root", self.tmp, *extra)
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertEqual(completed.stdout, b"")
                self.assertTrue(completed.stderr.startswith(b"error: "), completed.stderr)
                self.assertIn(b"no-existe.json", completed.stderr)
                self.assertNotIn(b"Traceback", completed.stderr)
                self.assertFalse(target.exists())

    def test_un_error_conserva_el_output_anterior(self) -> None:
        target = self.tmp / "previo.sql"
        target.write_bytes(b"contenido previo\n")
        broken = copy.deepcopy(ROWS_DOCUMENT)
        broken["contract_version"] = 2
        manifest = self.local_manifest("roto", broken, "roto-informe.json")
        completed = run_cli_bytes("sql", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", target)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stdout, b"")
        self.assertTrue(completed.stderr.startswith(b"error: roto-informe.json: contract_version: "), completed.stderr)
        self.assertEqual(target.read_bytes(), b"contenido previo\n")

    def test_output_en_un_directorio_inexistente_termina_con_1(self) -> None:
        completed = run_cli_bytes("sql", "--no-versioned", "--root", self.tmp, "--output", self.tmp / "no" / "carga.sql")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stdout, b"")
        self.assertTrue(completed.stderr.startswith(b"error: "), completed.stderr)
        self.assertNotIn(b"Traceback", completed.stderr)

    def test_uso_incorrecto_termina_con_2(self) -> None:
        # Contraste: el subcomando existe y con opciones válidas termina bien; sin él, argparse daría 2 por «sql»
        # desconocido y las comprobaciones de abajo pasarían por el motivo equivocado.
        valid = run_cli_bytes("sql", "--no-versioned", "--root", self.tmp)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        for args in (("sql", "--no-existe"), ("sql", "--manifest"), ("sql", "--output"), ("sql", "--root"),
                     ("sql", "sobrante")):
            with self.subTest(args=args):
                completed = run_cli_bytes(*args)
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                self.assertEqual(completed.stdout, b"")
                self.assertNotEqual(completed.stderr, b"")
                # El rechazo es de la opción o del argumento, no del subcomando.
                self.assertNotIn(b"invalid choice", completed.stderr)

    def test_la_ayuda_del_subcomando_documenta_las_opciones(self) -> None:
        general = run_cli_bytes("--help")
        self.assertEqual(general.returncode, 0, general.stderr)
        self.assertIn(b"sql", general.stdout)
        self.assertIn(b"rows", general.stdout)
        detailed = run_cli_bytes("sql", "--help")
        self.assertEqual(detailed.returncode, 0, detailed.stderr)
        for option in (b"--manifest", b"--no-versioned", b"--output", b"--root"):
            self.assertIn(option, detailed.stdout)

    def test_rows_sigue_dando_su_json(self) -> None:
        manifest = self.local_manifest()
        completed = run_cli_bytes("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = completed.stdout.decode("utf-8")
        dataset = json.loads(text)
        self.assertEqual(dataset["dataset_version"], 1)
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], ["JUP-071-demo-1"])
        self.assertEqual(text, json.dumps(dataset, indent=2, ensure_ascii=True) + "\n")
        self.assertNotIn(b"BEGIN", completed.stdout)
        # Los dos subcomandos parten del mismo conjunto de datos: las ejecuciones del SQL son las del JSON.
        generated = run_cli_bytes("sql", "--no-versioned", "--manifest", manifest, "--root", self.tmp)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.assertEqual([cells[0] for cells in Script(generated.stdout.decode("utf-8")).rows("runs")],
                         [item["run"]["run_id"] for item in dataset["runs"]])


class MainInProcessTest(TmpCase):
    def call(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = tool.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_sql_correcto_devuelve_0_e_imprime_solo_el_script(self) -> None:
        manifest = self.local_manifest_path()
        code, out, err = self.call(["sql", "--no-versioned", "--manifest", str(manifest), "--root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIs(type(code), int)
        self.assertEqual(err, "")
        self.assertEqual(out, tool.build_sql(tool.build_dataset([manifest], root=self.tmp)))

    def local_manifest_path(self) -> Path:
        report = self.tmp / "informe.json"
        report.write_text(json.dumps(ROWS_DOCUMENT), encoding="utf-8")
        manifest = self.tmp / "m.json"
        manifest.write_text(json.dumps({"manifest_version": 1, "runs": [
            {"path": str(report), "format": "rows-v1", "milestone": False}]}), encoding="utf-8")
        return manifest

    def test_sql_usa_build_dataset_y_build_sql_de_la_herramienta(self) -> None:
        # Cableado: el subcomando pasa el conjunto de datos de `build_dataset` a `build_sql` y escribe lo que devuelve.
        marker = {"dataset_version": 1, "runs": []}
        with mock.patch.object(tool, "build_dataset", return_value=marker) as dataset_mock, \
                mock.patch.object(tool, "build_sql", return_value="SELECT 1;\n") as sql_mock:
            code, out, err = self.call(["sql", "--no-versioned", "--root", str(self.tmp)])
        self.assertEqual((code, out, err), (0, "SELECT 1;\n", ""))
        sql_mock.assert_called_once_with(marker)
        dataset_mock.assert_called_once()

    def test_un_sql_error_devuelve_1_con_el_mensaje_y_sin_salida(self) -> None:
        with mock.patch.object(tool, "build_sql", side_effect=tool.SqlError("literal no representable")):
            code, out, err = self.call(["sql", "--no-versioned", "--root", str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(err, "error: literal no representable\n")

    def test_un_adapter_error_de_build_sql_devuelve_1(self) -> None:
        with mock.patch.object(tool, "build_sql", side_effect=tool.AdapterError("runs[0]: algo")):
            code, out, err = self.call(["sql", "--no-versioned", "--root", str(self.tmp)])
        self.assertEqual((code, out, err), (1, "", "error: runs[0]: algo\n"))

    def test_un_error_de_build_sql_no_crea_el_fichero_de_output(self) -> None:
        target = self.tmp / "carga.sql"
        with mock.patch.object(tool, "build_sql", side_effect=tool.SqlError("x")):
            code, out, err = self.call(["sql", "--no-versioned", "--root", str(self.tmp), "--output", str(target)])
        self.assertEqual(code, 1)
        self.assertFalse(target.exists())

    def test_rows_no_llama_a_build_sql(self) -> None:
        manifest = self.local_manifest_path()
        with mock.patch.object(tool, "build_sql", side_effect=AssertionError("rows no genera SQL")):
            code, out, err = self.call(["rows", "--no-versioned", "--manifest", str(manifest), "--root", str(self.tmp)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["dataset_version"], 1)


class CalibrationDateWithFractionTest(TmpCase):
    """Añadido tras integrar develop: fecha de calibración con fracción de segundo >= 0.5 s.

    El informe de calibración regenerado por JUP-120 tiene `generated_at` con 0.046773 s; la anterior tenía
    0.826486 s, y esa fracción alta era la que detectaba un `run_id` que REDONDEARA el segundo en vez de
    truncarlo (y fijaba el literal `timestamptz` con seis decimales). Con la fecha nueva esas dos comprobaciones
    perdían filo, así que se reproducen aquí con una copia temporal del informe real con ESA fecha antigua
    (el repositorio no se toca). Los valores esperados se calculan con json/hashlib/datetime, no con la herramienta.
    """

    OLD_GENERATED_AT = "2026-10-03T07:15:32.826486+00:00"

    def test_el_run_id_trunca_los_segundos_y_el_script_conserva_la_fecha_exacta(self) -> None:
        report = json.loads(
            (ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json").read_text(encoding="utf-8-sig"))
        report["generated_at"] = self.OLD_GENERATED_AT
        path = self.write("calibracion/informe.json", report)
        manifest = self.write("calibracion.json", {"manifest_version": 1, "runs": [
            {"path": str(path), "format": "jup-022-calibration-v1", "milestone": False}]})
        dataset = tool.build_dataset([manifest], root=self.tmp)
        sha = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True).encode("utf-8")).hexdigest()
        # 32.826486 s se trunca a 32 (un redondeo daría 33) y el prefijo de la huella son sus ocho primeros hex.
        self.assertEqual([item["run"]["run_id"] for item in dataset["runs"]], [f"jup-022-20261003T071532Z-{sha[:8]}"])
        self.assertEqual(dataset["runs"][0]["run"]["run_at"], self.OLD_GENERATED_AT)
        text = tool.build_sql(dataset)
        # La fecha va tal cual con su cast (seis decimales y desplazamiento), una sola vez.
        self.assertIn(f"'{self.OLD_GENERATED_AT}'::timestamptz", text)
        self.assertEqual(text.count("::timestamptz"), 1)
        self.assertEqual(len(Script(text).rows("runs")), 1)


if __name__ == "__main__":
    unittest.main()
