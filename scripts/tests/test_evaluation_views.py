"""Vistas `evaluation.config_changes` y `evaluation.comparable_runs` (JUP-121, tarea 3.2, Red).

Las dos vistas alimentan al dashboard (`design.md` D5 y D6, y la spec «Evolución entre ejecuciones comparables»):

* `evaluation.config_changes` da una fila por cada par de ejecuciones CONSECUTIVAS de la MISMA `source` (ordenadas por
  `run_at` y, a igualdad, por `run_id`) en el que cambió algo. Solo cuentan las ejecuciones con `run_at` no nulo.
  Columnas, en orden: `run_id` (la posterior), `previous_run_id`, `source`, `run_at` (el de la posterior), `changes`
  (`text[]`, no vacío, subconjunto de `{bateria, modelo, prompt, corpus}` y siempre en ESE orden) y `annotation`
  (`'Cambia: '` + los cambios unidos con `', '`).
* `evaluation.comparable_runs` da una fila por ejecución con fecha cuya `comparability_key` aparece en al menos dos
  ejecuciones con fecha. Columnas: `comparability_key`, `run_id`, `source`, `run_at`, `is_real`, `milestone` y
  `series_runs`. Las claves con una sola ejecución con fecha no salen: ahí el panel muestra «Sin datos: no hay con
  qué comparar» (escenario «Una sola ejecución comparable»).

Estas pruebas son de dos clases:

* SIN base de datos: la constante `VIEWS_DDL`, su contenido, su lugar en `DDL_BLOCKS` y su posición en el script de
  `build_sql` (después de las tablas y antes del `TRUNCATE`).
* CON PostgreSQL real (contenedor desechable de `evaluation_pg_helper`, con la imagen exacta de `postgres-pgvector`):
  el SQL de una vista solo se puede probar ejecutándolo. Cada test carga SU conjunto de datos (que vacía lo anterior)
  y compara las filas de la vista con lo esperado, calculado a mano en cada caso. Los conjuntos se construyen con
  documentos `rows-v1` escritos en un directorio temporal y `tool.build_dataset`, el mismo camino que el manifiesto
  real, de modo que `is_real`, `comparability_key` y el resto de columnas son los que produce la herramienta.

Decisiones donde el contrato admite más de una lectura (fijadas aquí; el coder debe respetarlas):

* El contenedor se crea de forma PEREZOSA (al primer test con base, y uno por módulo) y no en `setUpModule`: si no hay
  Docker, un `SkipTest` en `setUpModule` saltaría también las pruebas sin base de datos, que no lo necesitan.
* La ordenación de «consecutivas» es por `run_at` (instante, no texto: `...T12:00:00+02:00` es ANTERIOR a
  `...T11:00:00Z`) y después por `run_id`. Las ejecuciones sin fecha no existen para la vista: ni aparecen ni
  interrumpen la cadena de las demás.
* `prompt` solo se afirma si AMBAS huellas están registradas y son distintas; `bateria`, `modelo` y `corpus` usan
  `IS DISTINCT FROM`, de modo que NULL frente a un valor SÍ es un cambio (la ausencia de dato no es «igual»).
* En los datos versionados el par JUP-070 run-1/run-2 solo cambia `embedding_provider` (y `retrieval`): eso NO es
  batería, modelo, prompt ni corpus, así que la vista queda VACÍA con los cinco informes reales. La prueba lo deriva
  de las propias filas de `runs` y no lo escribe a mano.
* `series_runs` puede ser `integer` o `bigint` (`count(*)` da `bigint`): el contrato dice «entero».

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para apuntar
estas pruebas a una copia mutada.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (ayudante compartido con las pruebas de 3.3 y 5.x)

TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_views", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

FORBIDDEN_RE = re.compile(r"PASSWORD|CREATE\s+ROLE|GRANT|DROP", re.IGNORECASE)
VIEW_RE = re.compile(r"CREATE\s+OR\s+REPLACE\s+VIEW\s+evaluation\.(\w+)\s+AS\b", re.IGNORECASE)
CHANGE_ORDER = ("bateria", "modelo", "prompt", "corpus")


# --- Servidor: uno por módulo, perezoso y siempre limpiado ---------------------------------------------------------

_SERVER: dict = {}


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo; se crea en la primera petición. Si no hay Docker, cada test con base se salta."""
    if "failure" in _SERVER:
        raise unittest.SkipTest(_SERVER["failure"])
    if "instance" not in _SERVER:
        try:
            _SERVER["instance"] = evaluation_pg_helper.PostgresServer()
        except unittest.SkipTest as skip:
            _SERVER["failure"] = str(skip)
            raise
    return _SERVER["instance"]


def tearDownModule() -> None:
    # Además de `atexit` del ayudante: el contenedor desaparece al acabar el módulo aunque algún test falle.
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


# --- Construcción de conjuntos de datos con `rows-v1` ---------------------------------------------------------------

# Ejecución base: todo registrado y nada «no real» (ni `mock` ni plantilla ni sintética). Cada test cambia SOLO lo
# que quiere comparar, así que cualquier fila de `config_changes` se explica por el campo tocado.
BASE_RUN = {
    "commit": "abc1234", "suite": "JUP-069", "suite_version": "1.0.0", "suite_sha256": "aa" * 32,
    "corpus_sha256": "bb" * 32, "embedding_provider": "proveedor-1", "embedding_alias": "alias-1",
    "retrieval": {"top_k": 4}, "generation_model": "modelo-1", "prompt_sha256": "cc" * 32, "synthetic": False,
}
# Una fila de resultado válida: toda ejecución necesita al menos una (un informe sin filas se rechaza).
BASE_ROW = {
    "measure_type": "A", "grp": "g", "metric_id": "M-1", "behavior": "b", "status": "measured",
    "value": 0.5, "unit": "ms", "judgment": "automatic",
}


def at(minute: int) -> str:
    """Instante UTC del 14-10-2026 a las 10:MM:00; los minutos ordenan las ejecuciones de un test."""
    return f"2026-10-14T10:{minute:02d}:00Z"


def utc(minute: int) -> str:
    """Mismo instante con el formato con el que las consultas de las pruebas lo leen de la base."""
    return at(minute)


def R(run_id: str, source: str, minute: int | None = 0, *, milestone: bool = False, **fields) -> tuple[dict, bool]:
    """Ejecución `rows-v1`: `minute=None` la deja SIN fecha; `fields` sustituye cualquier campo (también `run_at`)."""
    run = {**BASE_RUN, "run_id": run_id, "source": source, "run_at": None if minute is None else at(minute)}
    run.update(fields)
    return run, milestone


def build(items) -> dict:
    """Escribe un documento `rows-v1` por ejecución y un manifiesto en un tmpdir y devuelve `build_dataset`."""
    with tempfile.TemporaryDirectory(prefix="evaluation-views-") as directory:
        base = Path(directory)
        entries = []
        for run, milestone in items:
            document = {"contract_version": 1, "run": run, "results": [dict(BASE_ROW)]}
            path = base / f"{run['run_id']}.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            entries.append({"path": str(path), "format": "rows-v1", "milestone": milestone})
        manifest = base / "manifest.json"
        manifest.write_text(json.dumps({"manifest_version": 1, "runs": entries}), encoding="utf-8")
        return tool.build_dataset([manifest], root=base)


def load(items) -> dict:
    """Construye el conjunto, lo carga en la base (vaciando lo anterior) y lo devuelve."""
    dataset = build(items)
    server().load_dataset(dataset, tool)
    return dataset


# --- Consultas de las vistas -----------------------------------------------------------------------------------------

# El orden se pide con la ordenación `C` (por código de carácter): la de la base depende de la configuración regional
# del contenedor y colocaría `SC-a-b` y `SC-a` de otra forma que las listas esperadas de Python.
STAMP = "to_char(run_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"
CHANGES_SQL = (f"SELECT run_id, previous_run_id, source, {STAMP}, changes::text, annotation "
               "FROM evaluation.config_changes ORDER BY source COLLATE \"C\", run_at, run_id COLLATE \"C\"")
COMPARABLE_SQL = (f"SELECT comparability_key, run_id, source, {STAMP}, is_real::text, milestone::text, series_runs::text "
                  "FROM evaluation.comparable_runs ORDER BY source COLLATE \"C\", run_at, run_id COLLATE \"C\"")


def change_rows(time_zone: str | None = None) -> list[tuple]:
    # `time_zone` cambia la zona horaria de la SESIÓN que lee la vista: el resultado no puede depender de ella.
    prefix = f"SET TIME ZONE '{time_zone}'; " if time_zone else ""
    return [tuple(row) for row in server().query(prefix + CHANGES_SQL)]


def comparable_rows() -> list[tuple]:
    return [tuple(row) for row in server().query(COMPARABLE_SQL)]


def changes_text(changes) -> str:
    """Forma de texto de un `text[]` de PostgreSQL sin comillas (los cuatro valores no las necesitan)."""
    return "{" + ",".join(changes) + "}"


def annotation_of(changes) -> str:
    return "Cambia: " + ", ".join(changes)


def expected_change_row(run_id: str, previous: str, source: str, minute: int, changes) -> tuple:
    return (run_id, previous, source, utc(minute), changes_text(changes), annotation_of(changes))


def view_columns(view: str) -> list[tuple[str, str, str]]:
    rows = server().query(
        "SELECT column_name, data_type, udt_name FROM information_schema.columns "
        f"WHERE table_schema = 'evaluation' AND table_name = '{view}' ORDER BY ordinal_position")
    return [tuple(row) for row in rows]


def pair_scenarios(scenarios) -> tuple[list, list]:
    """Cada escenario `(nombre, antes, despues, cambios)` es una fuente con dos ejecuciones en los minutos 0 y 1.

    Devuelve las ejecuciones y las filas esperadas de `config_changes`. Una fuente por escenario: así un solo conjunto
    y una sola carga cubren decenas de casos, y cada uno se comprueba aparte con `subTest`.
    """
    items, expected = [], []
    for name, before, after, changes in scenarios:
        source = f"SC-{name}"
        items.append(R(f"{source}-1", source, 0, **before))
        items.append(R(f"{source}-2", source, 1, **after))
        if changes:
            expected.append(expected_change_row(f"{source}-2", f"{source}-1", source, 1, changes))
    return items, expected


class ViewsTestCase(unittest.TestCase):
    """Base de las pruebas con base de datos: arranca (o reutiliza) el servidor del módulo."""

    @classmethod
    def setUpClass(cls) -> None:
        server()

    def assert_changes_equal(self, items, expected) -> None:
        """Carga `items` y exige que la vista devuelva EXACTAMENTE `expected` (ni más ni menos filas)."""
        load(items)
        self.assertEqual(change_rows(), sorted(expected, key=lambda row: (row[2], row[3], row[0])))


# --- Sin base de datos: el DDL y su sitio en el script --------------------------------------------------------------


def split_plain(text: str) -> list[str]:
    """Trocea por `;` fuera de cadenas (el DDL de las vistas no lleva comentarios ni comillas dobles)."""
    statements, current, in_string = [], [], False
    for char in text:
        if char == "'":
            in_string = not in_string
        if char == ";" and not in_string:
            statements.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    assert not in_string, "cadena sin cerrar"
    assert "".join(current).strip() == "", "texto tras la última sentencia: falta el `;` final"
    return statements


def squash(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())


_DATASET: dict = {}


def real_script() -> str:
    # Se calcula a la primera petición (no en `setUpModule`): cada test falla por sí solo si `build_sql` falla.
    if "script" not in _DATASET:
        _DATASET["script"] = tool.build_sql(tool.build_dataset([tool.DEFAULT_MANIFEST]))
    return _DATASET["script"]


class ViewsDdlTest(unittest.TestCase):
    def test_views_ddl_es_una_cadena_con_exactamente_las_dos_vistas(self) -> None:
        ddl = tool.VIEWS_DDL
        self.assertIs(type(ddl), str)
        statements = split_plain(ddl)
        # Dos sentencias, cada una un `CREATE OR REPLACE VIEW evaluation.<vista> AS`, sin repetir ni añadir otras.
        self.assertEqual(len(statements), 2, statements)
        names = []
        for statement in statements:
            match = VIEW_RE.match(statement)
            self.assertIsNotNone(match, statement[:80])
            names.append(match.group(1))
        self.assertEqual(sorted(names), ["comparable_runs", "config_changes"])

    def test_el_bloque_acaba_en_punto_y_coma_y_no_usa_palabras_prohibidas(self) -> None:
        # `build_sql` pega los bloques con una línea en blanco: sin `;` final la última vista se uniría al `TRUNCATE`.
        self.assertTrue(tool.VIEWS_DDL.rstrip().endswith(";"), tool.VIEWS_DDL[-40:])
        # `build_sql` no puede llevar credenciales ni permisos (van en otro script, tarea 3.3) ni `DROP`: `CREATE OR
        # REPLACE` es lo que mantiene el script idempotente sin destruir nada.
        self.assertIsNone(FORBIDDEN_RE.search(tool.VIEWS_DDL), FORBIDDEN_RE.search(tool.VIEWS_DDL))
        # Los nombres de las vistas y las tablas van siempre cualificados con el esquema.
        self.assertIn("evaluation.runs", tool.VIEWS_DDL)
        self.assertNotRegex(tool.VIEWS_DDL, r"(?i)\bFROM\s+runs\b")

    def test_ddl_blocks_compone_esquema_y_vistas_en_ese_orden(self) -> None:
        self.assertEqual(tool.DDL_BLOCKS, (tool.SCHEMA_DDL, tool.VIEWS_DDL))
        self.assertIs(type(tool.DDL_BLOCKS), tuple)

    def test_las_vistas_van_en_el_script_despues_de_las_tablas_y_antes_del_truncate(self) -> None:
        script = real_script()
        statements = split_plain(script)
        squashed = [squash(statement) for statement in statements]
        table_positions = [index for index, text in enumerate(squashed)
                           if text.startswith("CREATE TABLE IF NOT EXISTS evaluation.")]
        view_positions = {VIEW_RE.match(text).group(1): index for index, text in enumerate(squashed)
                          if VIEW_RE.match(text)}
        truncates = [index for index, text in enumerate(squashed) if text.startswith("TRUNCATE")]
        self.assertEqual(len(table_positions), 2)
        self.assertEqual(sorted(view_positions), ["comparable_runs", "config_changes"])
        self.assertEqual(len(truncates), 1)
        # esquema -> tablas -> vistas -> vaciado: una vista que se crea antes de sus tablas no se puede crear.
        self.assertTrue(max(table_positions) < min(view_positions.values()), (table_positions, view_positions))
        self.assertTrue(max(view_positions.values()) < truncates[0], (view_positions, truncates))
        # Entre el esquema y el vaciado solo hay DDL `CREATE`: las pruebas de 3.1 siguen permitiéndolo.
        for index in range(3, truncates[0]):
            self.assertTrue(squashed[index].startswith("CREATE "), squashed[index][:60])
        # El bloque entra tal cual y una sola vez (fuente única: `DDL_BLOCKS`).
        self.assertEqual(script.count(tool.VIEWS_DDL), 1)
        self.assertGreater(script.index(tool.VIEWS_DDL), script.index(tool.SCHEMA_DDL) + len(tool.SCHEMA_DDL) - 1)
        self.assertLess(script.index(tool.VIEWS_DDL), script.index(tool.TRUNCATE_SQL))

    def test_el_script_sigue_sin_credenciales_ni_permisos_ni_drop(self) -> None:
        # Regresión del contrato de 3.1 al añadir DDL: las vistas no deben colar `GRANT`, `PASSWORD`... en el script.
        # La búsqueda se hace sobre el DDL y no sobre los datos reales (que podrían contener la palabra en un texto).
        script = real_script()
        ddl_part = script[:script.index(tool.TRUNCATE_SQL)]
        # Se exige que las vistas YA estén en esa parte: sin ellas la comprobación pasaría sin examinar nada nuevo.
        self.assertIn(tool.VIEWS_DDL, ddl_part)
        self.assertIsNone(FORBIDDEN_RE.search(ddl_part), FORBIDDEN_RE.search(ddl_part))


# --- Con PostgreSQL real: estructura de las vistas ------------------------------------------------------------------


class ViewsStructureTest(ViewsTestCase):
    def test_las_dos_vistas_existen_en_el_esquema_y_no_son_materializadas(self) -> None:
        load([R("estructura-1", "SC-estructura", 0)])
        kinds = server().query(
            "SELECT c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'evaluation' AND c.relkind IN ('v', 'm') ORDER BY c.relname")
        # Vistas normales (`v`): una materializada (`m`) quedaría vieja hasta el siguiente `REFRESH`.
        self.assertEqual(kinds, [["comparable_runs", "v"], ["config_changes", "v"]])

    def test_columnas_de_config_changes_en_el_orden_y_con_los_tipos_del_contrato(self) -> None:
        load([R("estructura-1", "SC-estructura", 0)])
        self.assertEqual(view_columns("config_changes"), [
            ("run_id", "text", "text"), ("previous_run_id", "text", "text"), ("source", "text", "text"),
            ("run_at", "timestamp with time zone", "timestamptz"), ("changes", "ARRAY", "_text"),
            ("annotation", "text", "text"),
        ])

    def test_columnas_de_comparable_runs_en_el_orden_y_con_los_tipos_del_contrato(self) -> None:
        load([R("estructura-1", "SC-estructura", 0)])
        columns = view_columns("comparable_runs")
        self.assertEqual([column[0] for column in columns], [
            "comparability_key", "run_id", "source", "run_at", "is_real", "milestone", "series_runs"])
        self.assertEqual([column[1] for column in columns[:6]], [
            "text", "text", "text", "timestamp with time zone", "boolean", "boolean"])
        # `series_runs` es un entero: `count(*)` da `bigint` y también vale `integer`; nunca texto ni numérico.
        self.assertIn(columns[6][1], ("integer", "bigint"))

    def test_vistas_vacias_con_una_base_sin_ejecuciones(self) -> None:
        # Un conjunto sin ejecuciones es válido para `build_sql`: las vistas existen y no devuelven nada.
        server().load_dataset({"dataset_version": 1, "runs": []}, tool)
        self.assertEqual(change_rows(), [])
        self.assertEqual(comparable_rows(), [])


# --- Con PostgreSQL real: config_changes ----------------------------------------------------------------------------


class ConfigChangesPairsTest(ViewsTestCase):
    """Un par de ejecuciones de la misma fuente: qué campos cuentan y cuáles no."""

    def test_sin_cambios_relevantes_no_hay_fila(self) -> None:
        # Dos ejecuciones iguales en batería, modelo, prompt y corpus. Lo demás SÍ cambia (commit, suite, proveedor y
        # alias de embeddings, recuperación, `synthetic`, fecha, identificador): nada de eso es un cambio de
        # configuración que anotar, y un comparador que mire de más (la clave de comparabilidad, por ejemplo) falla aquí.
        otros = {"commit": "zzz9999", "suite": "JUP-999", "embedding_provider": "proveedor-2",
                 "embedding_alias": "alias-2", "retrieval": {"top_k": 9, "max_distance": 0.3}, "synthetic": True}
        items, expected = pair_scenarios([
            ("identicas", {}, {}, []),
            ("solo-lo-irrelevante", {}, otros, []),
            ("todo-nulo", {"suite_version": None, "suite_sha256": None, "generation_model": None,
                           "corpus_sha256": None, "prompt_sha256": None},
             {"suite_version": None, "suite_sha256": None, "generation_model": None, "corpus_sha256": None,
              "prompt_sha256": None}, []),
        ])
        self.assertEqual(expected, [])
        self.assert_changes_equal(items, expected)

    def test_bateria_por_version_por_huella_o_por_ambas(self) -> None:
        sha = {"suite_sha256": "dd" * 32}
        version = {"suite_version": "2.0.0"}
        items, expected = pair_scenarios([
            # La versión cambia y la huella de la batería NO: sigue siendo un cambio de batería.
            ("bateria-version", {}, version, ["bateria"]),
            # La huella cambia y la versión no.
            ("bateria-huella", {}, sha, ["bateria"]),
            # Las dos a la vez dan UN solo `bateria`, no dos.
            ("bateria-ambas", {}, {**version, **sha}, ["bateria"]),
            # Ausencia de dato frente a un valor es un cambio (`IS DISTINCT FROM`, no `<>`, que daría NULL).
            ("bateria-version-nulo-a-valor", {"suite_version": None}, {}, ["bateria"]),
            ("bateria-version-valor-a-nulo", {}, {"suite_version": None}, ["bateria"]),
            ("bateria-huella-nulo-a-valor", {"suite_sha256": None}, {}, ["bateria"]),
            ("bateria-huella-valor-a-nulo", {}, {"suite_sha256": None}, ["bateria"]),
            # Dos nulos no son un cambio.
            ("bateria-nulo-nulo", {"suite_version": None, "suite_sha256": None},
             {"suite_version": None, "suite_sha256": None}, []),
            # Un campo nulo en ambas y el otro igual: tampoco.
            ("bateria-version-nula-igual-huella", {"suite_version": None}, {"suite_version": None}, []),
        ])
        self.assert_changes_equal(items, expected)

    def test_modelo_con_valor_nulo_a_valor_y_valor_a_nulo(self) -> None:
        items, expected = pair_scenarios([
            ("modelo-valores", {}, {"generation_model": "modelo-2"}, ["modelo"]),
            ("modelo-nulo-a-valor", {"generation_model": None}, {}, ["modelo"]),
            ("modelo-valor-a-nulo", {}, {"generation_model": None}, ["modelo"]),
            ("modelo-nulo-nulo", {"generation_model": None}, {"generation_model": None}, []),
        ])
        self.assert_changes_equal(items, expected)

    def test_corpus_con_valor_nulo_a_valor_y_valor_a_nulo(self) -> None:
        items, expected = pair_scenarios([
            ("corpus-valores", {}, {"corpus_sha256": "ee" * 32}, ["corpus"]),
            ("corpus-nulo-a-valor", {"corpus_sha256": None}, {}, ["corpus"]),
            ("corpus-valor-a-nulo", {}, {"corpus_sha256": None}, ["corpus"]),
            ("corpus-nulo-nulo", {"corpus_sha256": None}, {"corpus_sha256": None}, []),
        ])
        self.assert_changes_equal(items, expected)

    def test_prompt_solo_si_ambas_huellas_estan_registradas_y_son_distintas(self) -> None:
        # Escenario «Prompt no registrado»: si falta la huella en alguna de las dos ejecuciones no se puede afirmar
        # que el prompt cambió, y anotarlo sería inventar un dato. Una sola condición (`<>` o `IS DISTINCT FROM`
        # sin exigir las dos) generaría falsos positivos en los tres casos con nulo.
        items, expected = pair_scenarios([
            ("prompt-valores-distintos", {}, {"prompt_sha256": "ee" * 32}, ["prompt"]),
            ("prompt-iguales", {}, {}, []),
            ("prompt-nulo-a-valor", {"prompt_sha256": None}, {}, []),
            ("prompt-valor-a-nulo", {}, {"prompt_sha256": None}, []),
            ("prompt-nulo-nulo", {"prompt_sha256": None}, {"prompt_sha256": None}, []),
        ])
        self.assert_changes_equal(items, expected)

    def test_prompt_no_registrado_no_oculta_los_demas_cambios(self) -> None:
        # Con el prompt sin registrar en la anterior, el resto de cambios se anota igual y sin `prompt`.
        items, expected = pair_scenarios([
            ("prompt-ausente-con-modelo", {"prompt_sha256": None}, {"generation_model": "modelo-2"}, ["modelo"]),
            ("prompt-ausente-con-todo",
             {"prompt_sha256": None},
             {"suite_version": "2.0.0", "generation_model": "modelo-2", "corpus_sha256": "ee" * 32},
             ["bateria", "modelo", "corpus"]),
            ("prompt-ausente-despues-con-corpus", {"corpus_sha256": None}, {"prompt_sha256": None, "corpus_sha256": "ee" * 32},
             ["corpus"]),
        ])
        self.assert_changes_equal(items, expected)

    def test_las_dieciseis_combinaciones_salen_en_orden_fijo_y_con_la_anotacion_del_contrato(self) -> None:
        # Todos los subconjuntos de {bateria, modelo, prompt, corpus}: el orden de `changes` y de `annotation` es SIEMPRE
        # el de `CHANGE_ORDER` (no el alfabético, que pondría `corpus` antes que `modelo`) y el vacío no genera fila.
        effects = {
            "bateria": {"suite_version": "2.0.0"}, "modelo": {"generation_model": "modelo-2"},
            "prompt": {"prompt_sha256": "ee" * 32}, "corpus": {"corpus_sha256": "ee" * 32},
        }
        scenarios = []
        for size in range(len(CHANGE_ORDER) + 1):
            for subset in itertools.combinations(CHANGE_ORDER, size):
                after: dict = {}
                for change in subset:
                    after.update(effects[change])
                scenarios.append(("combo-" + ("-".join(subset) or "ninguno"), {}, after, list(subset)))
        items, expected = pair_scenarios(scenarios)
        self.assertEqual(len(expected), 15)
        self.assert_changes_equal(items, expected)
        by_source = {row[2]: row for row in change_rows()}
        # Anotaciones literales del contrato, escritas a mano (no derivadas de la misma función que arriba).
        self.assertEqual(by_source["SC-combo-bateria-modelo"][5], "Cambia: bateria, modelo")
        self.assertEqual(by_source["SC-combo-bateria-modelo-prompt-corpus"][5], "Cambia: bateria, modelo, prompt, corpus")
        self.assertEqual(by_source["SC-combo-modelo-corpus"][4:], ("{modelo,corpus}", "Cambia: modelo, corpus"))
        self.assertEqual(by_source["SC-combo-corpus"][5], "Cambia: corpus")

    def test_las_ocho_combinaciones_con_prompt_sin_registrar_nunca_llevan_prompt(self) -> None:
        # Mismos subconjuntos sin `prompt` pero con la huella del prompt NULL antes y registrada después: la
        # anotación contiene solo los otros tres cambios y la vista no devuelve fila cuando no hay ninguno.
        effects = {
            "bateria": {"suite_version": "2.0.0"}, "modelo": {"generation_model": "modelo-2"},
            "corpus": {"corpus_sha256": "ee" * 32},
        }
        scenarios = []
        for size in range(4):
            for subset in itertools.combinations(("bateria", "modelo", "corpus"), size):
                after: dict = {}
                for change in subset:
                    after.update(effects[change])
                scenarios.append(("sinprompt-" + ("-".join(subset) or "ninguno"), {"prompt_sha256": None}, after,
                                  list(subset)))
        items, expected = pair_scenarios(scenarios)
        self.assertEqual(len(expected), 7)
        self.assert_changes_equal(items, expected)
        for row in change_rows():
            self.assertNotIn("prompt", row[4])
            self.assertNotIn("prompt", row[5])

    def test_changes_es_un_array_de_texto_no_vacio_y_no_una_cadena(self) -> None:
        load([R("arr-1", "SC-arr", 0), R("arr-2", "SC-arr", 1, suite_version="2.0.0", generation_model="modelo-2")])
        self.assertEqual(server().scalar("SELECT pg_typeof(changes)::text FROM evaluation.config_changes"), "text[]")
        self.assertEqual(server().scalar("SELECT cardinality(changes) FROM evaluation.config_changes"), "2")
        self.assertEqual(server().scalar("SELECT changes[1] || '/' || changes[2] FROM evaluation.config_changes"),
                         "bateria/modelo")
        # El array permite buscar un cambio concreto, como hará el panel.
        self.assertEqual(server().scalar("SELECT count(*) FROM evaluation.config_changes WHERE 'modelo' = ANY(changes)"), "1")
        self.assertEqual(server().scalar("SELECT count(*) FROM evaluation.config_changes WHERE 'corpus' = ANY(changes)"), "0")

    def test_se_comparan_ejecuciones_reales_y_no_reales_sin_distinguir(self) -> None:
        # Los motivos de ejecución no real ya van en la clave de comparabilidad, no en las anotaciones: un par con una
        # ejecución de plantilla y otra con modelo real sí anota el cambio de modelo, y un par de dobles también.
        items, expected = pair_scenarios([
            ("mixta-real-a-plantilla", {}, {"generation_model": "plantilla-sin-modelo"}, ["modelo"]),
            ("mixta-doble-a-real", {"embedding_provider": "mock"}, {"generation_model": "modelo-2"}, ["modelo"]),
            ("mixta-dobles", {"embedding_provider": "mock"}, {"embedding_provider": "mock", "corpus_sha256": "ee" * 32},
             ["corpus"]),
        ])
        self.assert_changes_equal(items, expected)

    def test_una_sola_ejecucion_no_genera_filas(self) -> None:
        self.assert_changes_equal([R("sola-1", "SC-sola", 0)], [])

    def test_otra_fuente_con_una_sola_ejecucion_no_altera_el_resultado(self) -> None:
        # Una ejecución de otra fuente (con otro modelo y con la misma fecha) no es «anterior» de nadie: el par se evalúa
        # SOLO entre ejecuciones con la misma `source`.
        items, expected = pair_scenarios([("una-fuente", {}, {"generation_model": "modelo-2"}, ["modelo"])])
        items.append(R("OTRA-1", "OTRA", 0, generation_model="otro-modelo"))
        self.assert_changes_equal(items, expected)


class ConfigChangesChainsTest(ViewsTestCase):
    """Cadenas de varias ejecuciones: con quién se compara cada una, en qué orden y qué se ignora."""

    def test_tres_ejecuciones_encadenadas_comparan_cada_una_con_la_anterior_y_no_con_la_primera(self) -> None:
        # Cadena A -> B -> C con un cambio distinto en cada tramo, con los `run_id` en orden contrario al de las
        # fechas e insertados desordenados: el orden sale de `run_at`, no del identificador ni de la inserción. Si C se
        # comparase con A, su fila diría `modelo, corpus` y no solo `corpus`.
        items = [
            R("a-tercera", "SC-cadena", 2, generation_model="modelo-2", corpus_sha256="ee" * 32),
            R("z-primera", "SC-cadena", 0),
            R("m-segunda", "SC-cadena", 1, generation_model="modelo-2"),
        ]
        self.assert_changes_equal(items, [
            expected_change_row("m-segunda", "z-primera", "SC-cadena", 1, ["modelo"]),
            expected_change_row("a-tercera", "m-segunda", "SC-cadena", 2, ["corpus"]),
        ])

    def test_un_tramo_sin_cambios_no_rompe_la_cadena(self) -> None:
        # A -> B (cambia el modelo), B -> C (igual: sin fila), C -> D (cambia el corpus): D se compara con C, no con B.
        items = [
            R("cad-a", "SC-tramos", 0),
            R("cad-b", "SC-tramos", 1, generation_model="modelo-2"),
            R("cad-c", "SC-tramos", 2, generation_model="modelo-2", commit="otro1234"),
            R("cad-d", "SC-tramos", 3, generation_model="modelo-2", corpus_sha256="ee" * 32),
        ]
        self.assert_changes_equal(items, [
            expected_change_row("cad-b", "cad-a", "SC-tramos", 1, ["modelo"]),
            expected_change_row("cad-d", "cad-c", "SC-tramos", 3, ["corpus"]),
        ])

    def test_volver_a_la_configuracion_anterior_es_otro_cambio(self) -> None:
        # A (modelo-1) -> B (modelo-2) -> C (modelo-1): C es igual que A pero distinta de B, que es con quien se compara.
        items = [
            R("pp-a", "SC-pingpong", 0),
            R("pp-b", "SC-pingpong", 1, generation_model="modelo-2"),
            R("pp-c", "SC-pingpong", 2),
        ]
        self.assert_changes_equal(items, [
            expected_change_row("pp-b", "pp-a", "SC-pingpong", 1, ["modelo"]),
            expected_change_row("pp-c", "pp-b", "SC-pingpong", 2, ["modelo"]),
        ])

    def test_fuentes_distintas_intercaladas_por_fecha_no_se_mezclan(self) -> None:
        # X en los minutos 0 y 2 e Y en el 1 y el 3: ordenadas todas juntas serían x1, y1, x2, y2 y x2 se compararía con
        # y1. Cada fuente solo se compara con ella misma: una fila por fuente, con su propio cambio.
        items = [
            R("x-1", "SC-X", 0, generation_model="modelo-1"),
            R("y-1", "SC-Y", 1, corpus_sha256="ee" * 32),
            R("x-2", "SC-X", 2, generation_model="modelo-2"),
            R("y-2", "SC-Y", 3, corpus_sha256="ff" * 32),
        ]
        self.assert_changes_equal(items, [
            expected_change_row("x-2", "x-1", "SC-X", 2, ["modelo"]),
            expected_change_row("y-2", "y-1", "SC-Y", 3, ["corpus"]),
        ])

    def test_fuentes_intercaladas_con_la_misma_configuracion_no_inventan_cambios(self) -> None:
        # Mismo caso con fuentes que SÍ difieren entre sí en modelo: dentro de cada fuente no cambia nada.
        items = [
            R("p-1", "SC-P", 0, generation_model="modelo-p"),
            R("q-1", "SC-Q", 1, generation_model="modelo-q"),
            R("p-2", "SC-P", 2, generation_model="modelo-p"),
            R("q-2", "SC-Q", 3, generation_model="modelo-q"),
        ]
        self.assert_changes_equal(items, [])

    def test_una_ejecucion_sin_fecha_entre_dos_con_fecha_no_aparece_ni_interrumpe_la_comparacion(self) -> None:
        # Las dos con fecha difieren en el modelo; la intermedia SIN fecha difiere de ambas en el corpus. Debe salir la fila
        # de las dos con fecha comparadas entre sí (solo `modelo`) y ninguna con la ejecución sin fecha, ni como
        # posterior ni como anterior. Ordenar con NULL daría `corpus` (NULLS LAST: sin fecha después de la última).
        items = [
            R("nd-1", "SC-sinfecha", 0),
            R("nd-sin-fecha", "SC-sinfecha", None, corpus_sha256="ee" * 32, generation_model="modelo-9"),
            R("nd-2", "SC-sinfecha", 2, generation_model="modelo-2"),
        ]
        self.assert_changes_equal(items, [expected_change_row("nd-2", "nd-1", "SC-sinfecha", 2, ["modelo"])])

    def test_ejecuciones_sin_fecha_nunca_aparecen_aunque_difieran_entre_si(self) -> None:
        # Dos sin fecha y distintas: no hay orden, no hay par. Y una sola con fecha junto a una sin fecha: tampoco.
        items = [
            R("sf-1", "SC-nada", None), R("sf-2", "SC-nada", None, generation_model="modelo-2"),
            R("un-1", "SC-una", 0), R("un-sin", "SC-una", None, generation_model="modelo-2"),
        ]
        self.assert_changes_equal(items, [])

    def test_el_empate_de_fecha_se_desempata_por_run_id(self) -> None:
        # Tres ejecuciones con EL MISMO instante, insertadas en orden c, a, b: el orden es a, b, c (por `run_id`). Sin
        # desempate dependería del orden físico (c, a, b) y las filas serían otras.
        items = [
            R("t-c", "SC-empate", 5, corpus_sha256="ee" * 32, generation_model="modelo-2"),
            R("t-a", "SC-empate", 5),
            R("t-b", "SC-empate", 5, generation_model="modelo-2"),
        ]
        self.assert_changes_equal(items, [
            expected_change_row("t-b", "t-a", "SC-empate", 5, ["modelo"]),
            expected_change_row("t-c", "t-b", "SC-empate", 5, ["corpus"]),
        ])

    def test_el_empate_se_desempata_en_orden_ascendente_con_solo_dos_ejecuciones(self) -> None:
        # Insertadas primero la mayor: un orden descendente o físico daría la fila al revés (`t2-a` posterior a `t2-b`).
        items = [R("t2-b", "SC-empate2", 5, generation_model="modelo-2"), R("t2-a", "SC-empate2", 5)]
        self.assert_changes_equal(items, [expected_change_row("t2-b", "t2-a", "SC-empate2", 5, ["modelo"])])

    def test_el_orden_es_por_instante_y_no_por_el_texto_de_la_fecha(self) -> None:
        # `12:00+02:00` es las 10:00Z y `11:00Z` es POSTERIOR; el texto de la primera ordena después de la segunda y su
        # `run_id` también. Si se ordenara por texto o por identificador la fila saldría al revés.
        items = [
            R("zz-despues-en-texto", "SC-zona", None, run_at="2026-10-14T12:00:00+02:00"),
            R("aa-despues-en-tiempo", "SC-zona", None, run_at="2026-10-14T11:00:00Z", generation_model="modelo-2"),
        ]
        load(items)
        self.assertEqual(change_rows(), [(
            "aa-despues-en-tiempo", "zz-despues-en-texto", "SC-zona", "2026-10-14T11:00:00Z", "{modelo}",
            "Cambia: modelo")])

    def test_el_orden_es_cronologico_aunque_la_zona_de_la_sesion_repita_horas(self) -> None:
        # El 25-10-2026 en Madrid la hora 02:xx ocurre dos veces (fin del horario de verano). `02:30+02:00` son las 00:30Z
        # y `02:10+01:00` las 01:10Z: la primera es ANTERIOR aunque en el texto de una sesión `Europe/Madrid` (`... 02:30:00+02`
        # frente a `... 02:10:00+01`) vaya después. Ordenar por el texto de la fecha daría la fila al revés.
        load([
            R("dst-a", "SC-dst", None, run_at="2026-10-25T02:30:00+02:00"),
            R("dst-b", "SC-dst", None, run_at="2026-10-25T02:10:00+01:00", generation_model="modelo-2"),
        ])
        expected = [("dst-b", "dst-a", "SC-dst", "2026-10-25T01:10:00Z", "{modelo}", "Cambia: modelo")]
        self.assertEqual(change_rows(), expected)
        self.assertEqual(change_rows("Europe/Madrid"), expected)

    def test_run_at_de_la_fila_es_el_de_la_ejecucion_posterior(self) -> None:
        load([R("ra-1", "SC-fecha", 7), R("ra-2", "SC-fecha", 31, generation_model="modelo-2")])
        self.assertEqual(change_rows(), [expected_change_row("ra-2", "ra-1", "SC-fecha", 31, ["modelo"])])


class ConfigChangesRealDataTest(ViewsTestCase):
    def test_con_los_cinco_informes_versionados_la_vista_coincide_con_la_comparacion_calculada_en_python(self) -> None:
        # Se carga el manifiesto REAL (ocho ejecuciones, entre ellas JUP-068 vía Node) y se calcula el resultado esperado
        # leyendo `evaluation.runs` con una consulta y comparando campo a campo en Python, con un algoritmo escrito aquí
        # (agrupar por fuente, ordenar por fecha e identificador, comparar con la anterior). Solo las dos ejecuciones de
        # JUP-070 tienen fecha y comparten fuente; el resto no forma par.
        dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])
        server().load_dataset(dataset, tool)
        absent = "~"  # no pertenece al alfabeto de identificadores: distingue NULL de cualquier valor real
        columns = ["suite_version", "suite_sha256", "generation_model", "prompt_sha256", "corpus_sha256"]
        select = ", ".join(f"coalesce({column}, '{absent}')" for column in columns)
        rows = server().query(
            "SELECT run_id, source, coalesce(to_char(run_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS.US'), ''), "
            f"embedding_provider, {select} FROM evaluation.runs")
        runs = []
        for run_id, source, moment, provider, *values in rows:
            fields = dict(zip(columns, (None if value == absent else value for value in values)))
            runs.append({"run_id": run_id, "source": source, "run_at": moment or None, "provider": provider, **fields})
        self.assertEqual(len(runs), 9)

        expected = []
        for source in sorted({run["source"] for run in runs}):
            series = sorted((run for run in runs if run["source"] == source and run["run_at"] is not None),
                            key=lambda run: (run["run_at"], run["run_id"]))
            for previous, current in zip(series, series[1:]):
                changes = []
                if (previous["suite_version"], previous["suite_sha256"]) != (current["suite_version"], current["suite_sha256"]):
                    changes.append("bateria")
                if previous["generation_model"] != current["generation_model"]:
                    changes.append("modelo")
                if None not in (previous["prompt_sha256"], current["prompt_sha256"]) \
                        and previous["prompt_sha256"] != current["prompt_sha256"]:
                    changes.append("prompt")
                if previous["corpus_sha256"] != current["corpus_sha256"]:
                    changes.append("corpus")
                if changes:
                    expected.append((current["run_id"], previous["run_id"], source, changes_text(changes),
                                     annotation_of(changes)))
        actual = [(row[0], row[1], row[2], row[4], row[5]) for row in change_rows()]
        self.assertEqual(sorted(actual, key=lambda row: (row[2], row[0])), sorted(expected, key=lambda row: (row[2], row[0])))

        # Guardas de que la prueba mide lo que dice: las dos ejecuciones de JUP-070 son el único par, difieren en el
        # proveedor de embeddings (y en la recuperación) y aun así eso NO es un cambio de batería, modelo, prompt ni corpus.
        jup_070 = [run for run in runs if run["source"] == "JUP-070"]
        self.assertEqual(len(jup_070), 2)
        self.assertNotEqual(jup_070[0]["provider"], jup_070[1]["provider"])
        self.assertEqual(int(server().scalar("SELECT count(*) FROM evaluation.config_changes")), len(expected))


# --- Con PostgreSQL real: comparable_runs ---------------------------------------------------------------------------


def comparable_scenarios():
    """Conjunto con un caso por fuente (la clave de comparabilidad incluye la fuente, así que no se mezclan)."""
    return [
        # Dos ejecuciones con la misma configuración y fecha: forman una serie de dos. Cambian `run_id`, `run_at`, `commit`
        # e hito, que NO entran en la clave.
        R("par-1", "CMP-par", 0, milestone=True, commit="aaa1111"),
        R("par-2", "CMP-par", 1, milestone=False, commit="bbb2222"),
        # Una sola ejecución: sin serie.
        R("unica-1", "CMP-unica", 0),
        # Tres con la misma clave y una sin fecha: aparecen las dos con fecha y la serie es de dos.
        R("tres-1", "CMP-tres", 0, milestone=True),
        R("tres-sin-fecha", "CMP-tres", None, milestone=True),
        R("tres-2", "CMP-tres", 2),
        # Dos con la misma clave y NINGUNA con fecha: no hay serie que dibujar.
        R("nada-1", "CMP-nada", None),
        R("nada-2", "CMP-nada", None),
        # Dos con la misma clave y una sola con fecha: la serie con fecha es de una, no aparece.
        R("una-con-fecha", "CMP-una-fecha", 0),
        R("una-sin-fecha", "CMP-una-fecha", None),
        # Tres con fecha: la serie es de tres y las tres filas lo dicen.
        R("trio-1", "CMP-trio", 0),
        R("trio-2", "CMP-trio", 1),
        R("trio-3", "CMP-trio", 2, milestone=True),
        # Dobles (`mock`): ejecuciones no reales con la misma clave; `is_real` y el hito se propagan.
        R("doble-1", "CMP-doble", 0, embedding_provider="mock", milestone=True),
        R("doble-2", "CMP-doble", 1, embedding_provider="mock", milestone=False),
        # Misma fuente y claves distintas (otro modelo): cada clave tiene una sola ejecución, no aparecen. Un recuento por
        # fuente en lugar de por clave daría una serie de dos.
        R("claves-1", "CMP-claves", 0),
        R("claves-2", "CMP-claves", 1, generation_model="modelo-2"),
        # Misma fuente con DOS series (claves A y B, de tres y de dos ejecuciones): cada fila lleva el tamaño de SU serie
        # (3 y 2), no el de la fuente (5).
        R("dos-a1", "CMP-dos", 0), R("dos-a2", "CMP-dos", 1), R("dos-a3", "CMP-dos", 2),
        R("dos-b1", "CMP-dos", 3, generation_model="modelo-2"), R("dos-b2", "CMP-dos", 4, generation_model="modelo-2"),
        # Misma fuente con una pareja (clave A) y una ejecución suelta (clave B): solo salen las dos de la pareja y la
        # serie vale dos, no tres.
        R("mixta-1", "CMP-mixta", 0),
        R("mixta-2", "CMP-mixta", 1),
        R("mixta-3", "CMP-mixta", 2, generation_model="modelo-2"),
    ]


class ComparableRunsTest(ViewsTestCase):
    def test_series_con_al_menos_dos_ejecuciones_con_fecha(self) -> None:
        dataset = load(comparable_scenarios())
        key = {item["run"]["run_id"]: item["run"]["comparability_key"] for item in dataset["runs"]}
        # Guardas: la clave de cada caso es la esperada (misma dentro de una serie y distinta entre series), para que
        # las filas de abajo se deban a la vista y no a un conjunto mal construido.
        for same in (("par-1", "par-2"), ("tres-1", "tres-sin-fecha", "tres-2"), ("trio-1", "trio-2", "trio-3"),
                     ("doble-1", "doble-2"), ("mixta-1", "mixta-2"), ("nada-1", "nada-2"),
                     ("dos-a1", "dos-a2", "dos-a3"), ("dos-b1", "dos-b2"),
                     ("una-con-fecha", "una-sin-fecha")):
            self.assertEqual(len({key[run_id] for run_id in same}), 1, same)
        self.assertNotEqual(key["claves-1"], key["claves-2"])
        self.assertNotEqual(key["mixta-1"], key["mixta-3"])
        self.assertNotEqual(key["dos-a1"], key["dos-b1"])
        self.assertEqual((len(key), len(set(key.values()))), (25, 13))

        def row(run_id, source, minute, is_real, milestone, series):
            return (key[run_id], run_id, source, utc(minute), is_real, milestone, str(series))

        expected = sorted([
            row("par-1", "CMP-par", 0, "true", "true", 2), row("par-2", "CMP-par", 1, "true", "false", 2),
            row("tres-1", "CMP-tres", 0, "true", "true", 2), row("tres-2", "CMP-tres", 2, "true", "false", 2),
            row("trio-1", "CMP-trio", 0, "true", "false", 3), row("trio-2", "CMP-trio", 1, "true", "false", 3),
            row("trio-3", "CMP-trio", 2, "true", "true", 3),
            row("doble-1", "CMP-doble", 0, "false", "true", 2), row("doble-2", "CMP-doble", 1, "false", "false", 2),
            row("mixta-1", "CMP-mixta", 0, "true", "false", 2), row("mixta-2", "CMP-mixta", 1, "true", "false", 2),
            row("dos-a1", "CMP-dos", 0, "true", "false", 3), row("dos-a2", "CMP-dos", 1, "true", "false", 3),
            row("dos-a3", "CMP-dos", 2, "true", "false", 3), row("dos-b1", "CMP-dos", 3, "true", "false", 2),
            row("dos-b2", "CMP-dos", 4, "true", "false", 2),
        ], key=lambda item: (item[2], item[3], item[1]))
        self.assertEqual(comparable_rows(), expected)

    def test_los_dos_informes_reales_de_jup_070_tienen_claves_distintas_y_no_aparecen(self) -> None:
        # Escenario «Una sola ejecución comparable» con los datos versionados: las ejecuciones 1 y 2 de JUP-070 cambian el
        # proveedor de embeddings y la recuperación, así que su clave difiere y el panel debe mostrar «Sin datos». Las
        # otras cuatro ejecuciones reales son claves únicas o no tienen fecha.
        dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])
        keys = [item["run"]["comparability_key"] for item in dataset["runs"]]
        self.assertEqual(len(set(keys)), 9)
        server().load_dataset(dataset, tool)
        self.assertEqual(server().scalar("SELECT count(*) FROM evaluation.runs"), "9")
        self.assertEqual(comparable_rows(), [])

    def test_is_real_y_milestone_se_propagan_desde_la_ejecucion(self) -> None:
        # Cuatro ejecuciones con la misma clave (misma fuente y configuración) y combinaciones de hito: el valor de cada
        # fila es el de SU ejecución (no el de la serie ni un valor fijo).
        load([
            R("prop-1", "CMP-prop", 0, milestone=True), R("prop-2", "CMP-prop", 1, milestone=False),
            R("prop-3", "CMP-prop", 2, milestone=True), R("prop-4", "CMP-prop", 3, milestone=False),
        ])
        self.assertEqual([(row[1], row[4], row[5], row[6]) for row in comparable_rows()], [
            ("prop-1", "true", "true", "4"), ("prop-2", "true", "false", "4"),
            ("prop-3", "true", "true", "4"), ("prop-4", "true", "false", "4"),
        ])
        # Y una serie de plantilla (no real) con hito: `is_real` falso y `milestone` verdadero se leen tal cual.
        load([
            R("tpl-1", "CMP-tpl", 0, milestone=True, generation_model="plantilla-sin-modelo"),
            R("tpl-2", "CMP-tpl", 1, milestone=True, generation_model="plantilla-sin-modelo"),
        ])
        self.assertEqual([(row[1], row[4], row[5]) for row in comparable_rows()],
                         [("tpl-1", "false", "true"), ("tpl-2", "false", "true")])

    def test_una_sola_ejecucion_no_aparece(self) -> None:
        load([R("solo-1", "CMP-solo", 0)])
        self.assertEqual(comparable_rows(), [])

    def test_la_clave_y_la_fecha_que_devuelve_la_vista_son_las_de_la_ejecucion(self) -> None:
        # Fechas con desfase horario: la vista devuelve el instante tal cual (timestamptz), sin tocarlo.
        dataset = load([
            R("fz-1", "CMP-fz", None, run_at="2026-10-14T12:30:00+02:00"),
            R("fz-2", "CMP-fz", None, run_at="2026-10-14T09:00:00Z"),
        ])
        keys = {item["run"]["run_id"]: item["run"]["comparability_key"] for item in dataset["runs"]}
        # Orden de la consulta: por instante, así que `fz-2` (09:00Z) va antes que `fz-1` (12:30+02:00 = 10:30Z).
        self.assertEqual(comparable_rows(), [
            (keys["fz-2"], "fz-2", "CMP-fz", "2026-10-14T09:00:00Z", "true", "false", "2"),
            (keys["fz-1"], "fz-1", "CMP-fz", "2026-10-14T10:30:00Z", "true", "false", "2"),
        ])


# --- Con PostgreSQL real: idempotencia y recarga --------------------------------------------------------------------


class ViewsReloadTest(ViewsTestCase):
    def test_cargar_dos_veces_el_mismo_conjunto_no_duplica_ni_cambia_las_vistas(self) -> None:
        items = [
            R("rel-1", "SC-rel", 0), R("rel-2", "SC-rel", 1, generation_model="modelo-2"),
            R("pc-1", "CMP-rel", 0), R("pc-2", "CMP-rel", 1),
        ]
        load(items)
        changes, comparable = change_rows(), comparable_rows()
        definitions = server().query(
            "SELECT pg_get_viewdef('evaluation.config_changes'::regclass), "
            "pg_get_viewdef('evaluation.comparable_runs'::regclass)")
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(comparable), 2)
        load(items)
        self.assertEqual(change_rows(), changes)
        self.assertEqual(comparable_rows(), comparable)
        self.assertEqual(server().query(
            "SELECT pg_get_viewdef('evaluation.config_changes'::regclass), "
            "pg_get_viewdef('evaluation.comparable_runs'::regclass)"), definitions)

    def test_create_or_replace_en_una_base_ya_cargada_sustituye_los_datos_de_las_vistas(self) -> None:
        # Carga A (con filas en las dos vistas) y después B, distinta, sobre la base ya cargada: el script vuelve a
        # ejecutar `CREATE OR REPLACE VIEW` con las vistas existentes y el resultado es solo el de B, sin restos de A.
        load([
            R("a-1", "SC-A", 0), R("a-2", "SC-A", 1, generation_model="modelo-2"),
            R("a-c1", "CMP-A", 0), R("a-c2", "CMP-A", 1),
        ])
        self.assertEqual(len(change_rows()), 1)
        self.assertEqual(len(comparable_rows()), 2)
        load([
            R("b-1", "SC-B", 0), R("b-2", "SC-B", 1, corpus_sha256="ee" * 32),
            R("b-solo", "CMP-B", 0),
        ])
        self.assertEqual(change_rows(), [expected_change_row("b-2", "b-1", "SC-B", 1, ["corpus"])])
        self.assertEqual(comparable_rows(), [])

    def test_recargar_deja_las_vistas_en_el_esquema_y_no_las_toca_el_truncate(self) -> None:
        load([R("v-1", "SC-v", 0)])
        load([R("v-2", "SC-v", 0)])
        names = server().query("SELECT viewname FROM pg_views WHERE schemaname = 'evaluation' ORDER BY viewname")
        self.assertEqual(names, [["comparable_runs"], ["config_changes"]])


if __name__ == "__main__":
    unittest.main()
