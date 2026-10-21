"""Consultas SQL del dashboard de evaluación contra un PostgreSQL real (JUP-121, tarea 4.2, Red).

El SQL de un panel solo se puede probar ejecutándolo. Este módulo lee el dashboard (`assistant-evaluation.json`, ruta
sustituible con `EVALUATION_DASHBOARD_JSON`), localiza cada pieza de la sección A y de la B con el mismo localizador que
`test_evaluation_dashboard_structure.py` y ejecuta SUS consultas, tal como están en el JSON, sobre dos conjuntos de
datos cargados con la herramienta (`tool.build_sql`, el mismo camino que la carga real):

* el conjunto VERSIONADO (cinco ejecuciones reales del manifiesto): lo que se verá en octubre de 2026;
* un conjunto SINTÉTICO (documentos `rows-v1` en un directorio temporal) que fuerza lo que los datos reales no
  ejercitan: series comparables, cambios de configuración, juicio humano, ejecuciones sin fecha y no reales,
  nulos y ceros medidos, y filas de robustez de JUP-071.

Las consultas corren con el rol de solo lectura de Grafana (`SET ROLE grafana_evaluation_reader`, tarea 3.3): si un
panel necesitara algo más que `SELECT` sobre el esquema `evaluation`, fallaría aquí y no en Grafana.

Macros de Grafana (el test las sustituye antes de ejecutar; otra macro hace fallar con un mensaje claro):
`$__timeFilter(col)` -> `TRUE`, `$__timeFrom()` -> `now() - interval '5 years'`, `$__timeTo()` -> `now()`,
`$__timeGroup(col,'1d')` -> `date_trunc('day', col)`, `$__interval` -> `'1h'`.

Contrato de columnas (decisiones donde el enunciado admitía más de una lectura; el coder debe respetarlas). Los
nombres son los de la salida de la consulta (alias), en minúsculas:

* a1 ejecuciones: `run_id`, `source`, `run_at`, `suite_version`, `commit_sha`, `generation_model`, `milestone` y una o
  más columnas más con el estado (`real` o `no real` más los motivos `plantilla`, `doble`, `sintetica`...). Lista las
  cuatro ejecuciones de la sección A o las cinco (con la de negocio); nunca menos. Un metadato ausente llega como NULL o
  como el texto `no registrado`.
* a2 estados: UNA fila por ejecución de JUP-070 (`grp = 'cases'`; no incluye el benchmark) con `run_id`, `run_at`,
  `suite`, `suite_version`, `commit_sha`, `generation_model`, `pass`, `fail`, `blocked`, `not_run` y `denominator`
  (un recuento de cero llega como 0, nunca NULL).
* a3 y a4: una fila por fila de `evaluation.results` de sus grupos, con `run_id`, `metric_id`, `behavior`, `status`,
  `value`, `numerator` y `denominator` (a4 añade `unit`: mezcla milisegundos y tasas). Los valores son los de la base,
  sin convertir ni rellenar (tolerancia relativa de 1e-3 por si se redondean).
* a5 y a6: columnas exactas `time` (timestamptz), `metric` (texto) y `value` (número), solo `status = 'measured'`.
  El texto de `metric` contiene el identificador de la métrica y la fuente, termina distinguiendo las no reales con
  `no real` y NUNCA comparte texto entre dos claves de comparabilidad distintas (si no, dos ejecuciones no comparables
  se unirían con una línea). La de juicio humano solo usa ejecuciones de hito; con una sola ejecución de hito en la
  serie se admite que aparezca o no.
* a7 calibración: `run_id`, `metric_id`, `behavior`, `value`, `numerator`, `denominator`, `selected` (booleano).
* a8 benchmark: una fila por modelo con `run_id`, `behavior` (alias), `successful`, `cases`, `keyword_score`,
  `latency_p95` y `cost`; sin llamadas correctas, las tres últimas son NULL.
* a9 robustez: `source = 'JUP-071'`; `run_id`, `source`, `metric_id`, `behavior`, `status`, `value`, `numerator`,
  `denominator`; vacía con los datos reales.
* B: cada tabla devuelve `run_id`, `metric_id`, `behavior`, `status` y `value` (más `numerator`, `denominator`).
* Anotación: `time`, `text` y `tags` (texto: `modelo` o `bateria,corpus`).
* Tablas con resultados (a1, a2, a3, a4, a7, a8, B): para cada fila de una ejecución no real, alguna celda dice
  `no real` y contiene cada uno de sus motivos; en las reales ninguna celda dice `no real`.

Se crea UN contenedor desechable por módulo, de forma perezosa (la primera consulta); mientras el dashboard no exista
las pruebas fallan antes de arrancar Docker.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import secrets
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (ayudante compartido con las pruebas de 3.2, 3.3 y 5.x)
import test_evaluation_dashboard_structure as S  # noqa: E402  (localizador de paneles del contrato)

TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_queries", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

NUMERICOS = ("double precision", "numeric", "real", "bigint", "integer", "smallint")
TIMESTAMPTZ = "timestamp with time zone"
COLUMNAS_PROHIBIDAS = {"question", "answer", "prompt", "response", "questions", "answers", "prompts", "responses"}


class ConsultaFallida(AssertionError):
    """La consulta del panel no se ejecuta (error de SQL, macro desconocida, permiso denegado...)."""


# --- Servidor: uno por módulo, perezoso y siempre limpiado ---------------------------------------------------------

_SERVER: dict = {}
_ESTADO: dict = {"conjunto": None, "rol": False}
_RESULTADOS: dict = {}


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


# --- Conjuntos de datos ------------------------------------------------------------------------------------------------


class Conjunto:
    """Un conjunto de datos con nombre; `cargar()` lo deja cargado (vacía lo anterior) y crea el rol de lectura."""

    def __init__(self, clave, fabrica):
        self.clave = clave
        self.fabrica = fabrica

    def cargar(self) -> None:
        servidor = server()
        if _ESTADO["conjunto"] == self.clave:
            return
        servidor.load_dataset(self.fabrica(), tool)
        _ESTADO["conjunto"] = self.clave
        if not _ESTADO["rol"]:
            # La contraseña es aleatoria y solo vive en esta sesión; el rol se crea tras la primera carga (los
            # privilegios por defecto necesitan que el esquema exista) y los permisos sobreviven a las recargas.
            resultado = servidor.psql(stdin=tool.build_role_sql(secrets.token_urlsafe(18)))
            if resultado.returncode != 0:
                raise RuntimeError(f"no se pudo crear el rol de lectura: {resultado.stderr.strip()}")
            _ESTADO["rol"] = True


def _construir_real() -> dict:
    return tool.build_dataset([tool.DEFAULT_MANIFEST])


BASE_RUN = {
    "commit": "abc1234", "suite": "JUP-069", "suite_version": "1.0.0", "suite_sha256": "aa" * 32,
    "corpus_sha256": "bb" * 32, "embedding_provider": "proveedor-1", "embedding_alias": "alias-1",
    "retrieval": {"top_k": 4}, "generation_model": "modelo-1", "prompt_sha256": "cc" * 32, "synthetic": False,
}


def dia(numero):
    """Instante UTC del `numero`-ésimo día de septiembre de 2026 a las 10:00: cada ejecución tiene el suyo."""
    return f"2026-09-{numero:02d}T10:00:00Z"


def fila_tasa(metric_id, grp, juicio, valor):
    """Fila de proporción `valor` sobre 100 casos; `None` es una métrica NO medida (sin valor ni numerador)."""
    base = {"measure_type": "A", "grp": grp, "metric_id": metric_id, "behavior": "all", "unit": "tasa",
            "judgment": juicio}
    if valor is None:
        return {**base, "status": "not_measured", "value": None, "denominator": 0}
    return {**base, "status": "measured", "value": valor, "numerator": round(valor * 100), "denominator": 100}


def fila_otra(grp, metric_id, behavior, status, unit, **campos):
    return {"measure_type": "A", "grp": grp, "metric_id": metric_id, "behavior": behavior, "status": status,
            "unit": unit, "judgment": "automatic", **campos}


# id, fuente, día (None = sin fecha), hito, (ACC-2 automática, ACC-1 humana, REL-1 automática), campos que cambian.
# `None` en una tasa es «no medida». Cada ejecución tiene un día distinto, así que `time` identifica a la ejecución.
ESPECIFICACION = [
    ("SC-A-1", "SC-A", 1, True, (0.80, 0.50, None), {}),
    ("SC-A-2", "SC-A", 2, False, (0.00, 0.60, 0.90), {}),  # ACC-2 = 0.0 MEDIDO: debe dibujarse, no desaparecer
    ("SC-A-3", "SC-A", 3, True, (0.30, 0.31, 0.32), {"retrieval": {"top_k": 6}}),  # otra clave de la MISMA fuente
    ("SC-A-4", "SC-A", 4, True, (0.35, 0.36, 0.37), {"retrieval": {"top_k": 6}}),
    ("SC-A-sin-fecha", "SC-A", None, True, (0.99, 0.98, 0.97), {}),  # misma clave que SC-A-1/2, sin fecha: no sale
    ("SC-N-1", "SC-N", 5, True, (0.40, 0.20, 0.10), {"generation_model": "plantilla-sin-modelo"}),  # no real
    ("SC-N-2", "SC-N", 6, True, (0.45, 0.25, 0.15), {"generation_model": "plantilla-sin-modelo"}),
    ("SC-M-1", "SC-M", 7, False, (0.70, 0.71, 0.72), {}),  # el modelo cambia: sola en su clave
    ("SC-M-2", "SC-M", 8, False, (0.73, 0.74, 0.75), {"generation_model": "modelo-2"}),  # anotación `modelo`
    ("SC-M-3", "SC-M", 9, False, (0.76, 0.77, 0.78), {"generation_model": "modelo-2"}),
    ("SC-B-1", "SC-B", 10, True, (0.60, 0.61, 0.62), {}),
    ("SC-B-2", "SC-B", 11, True, (0.65, 0.66, 0.67), {"suite_version": "2.0.0", "corpus_sha256": "dd" * 32}),
]

# Ejecuciones comparables (clave con al menos dos ejecuciones con fecha) de ese conjunto.
COMPARABLES = {"SC-A-1", "SC-A-2", "SC-A-3", "SC-A-4", "SC-N-1", "SC-N-2", "SC-M-2", "SC-M-3"}
NO_REALES = {"SC-N-1", "SC-N-2"}
ID_BENCHMARK = "SC-BM-1"
ID_CALIBRACION = "SC-CAL-1"
ID_ROBUSTEZ = "SC-ROB-1"


def _documentos_sinteticos() -> list:
    documentos = []
    for run_id, fuente, numero, hito, valores, campos in ESPECIFICACION:
        ejecucion = {**BASE_RUN, "run_id": run_id, "source": fuente,
                     "run_at": None if numero is None else dia(numero), **campos}
        filas = [fila_tasa("ACC-2", "accuracy", "automatic", valores[0]),
                 fila_tasa("ACC-1", "accuracy", "human", valores[1]),
                 fila_tasa("REL-1", "relevance", "automatic", valores[2])]
        documentos.append((ejecucion, filas, hito))
    # Benchmark sintético (no real): un modelo sin llamadas correctas (todo lo derivado es NO medido) y otro con ellas.
    benchmark = [
        fila_otra("benchmark", "cases", "m-cero", "pass", "casos", count=0, denominator=3),
        fila_otra("benchmark", "cases", "m-cero", "fail", "casos", count=3, denominator=3),
        fila_otra("benchmark", "keyword_score", "m-cero", "not_measured", "puntuacion", denominator=0),
        fila_otra("benchmark", "latency_p95", "m-cero", "not_measured", "ms", denominator=0),
        fila_otra("benchmark", "cost", "m-cero", "not_measured", "usd"),
        fila_otra("benchmark", "cases", "m-ok", "pass", "casos", count=2, denominator=3),
        fila_otra("benchmark", "cases", "m-ok", "fail", "casos", count=1, denominator=3),
        fila_otra("benchmark", "keyword_score", "m-ok", "measured", "puntuacion", value=0.8, denominator=2),
        fila_otra("benchmark", "latency_p95", "m-ok", "measured", "ms", value=1000.0, denominator=2),
        fila_otra("benchmark", "cost", "m-ok", "measured", "usd", value=0.01),
    ]
    documentos.append(({**BASE_RUN, "run_id": ID_BENCHMARK, "source": "JUP-078", "run_at": dia(20), "synthetic": True},
                       benchmark, True))
    # Calibración sintética: el candidato elegido, otro punto y un valor no medido.
    calibracion = [
        fila_otra("calibration", "document_hit_answer", "top_k=4,max_distance=0.6", "measured", "tasa",
                  value=0.5, numerator=5, denominator=10, selected=True),
        fila_otra("calibration", "document_hit_answer", "top_k=8,max_distance=0.6", "measured", "tasa",
                  value=0.6, numerator=6, denominator=10, selected=False),
        fila_otra("calibration", "empty_answer", "top_k=4,max_distance=0.6", "not_measured", "tasa", denominator=0),
    ]
    documentos.append(({**BASE_RUN, "run_id": ID_CALIBRACION, "source": "JUP-022", "run_at": dia(21), "synthetic": True},
                       calibracion, True))
    # Informe de robustez futuro (JUP-071), real, que sigue el contrato `rows-v1` sin tocar el dashboard.
    robustez = [
        fila_otra("robustness", "ROB-1", "categoria=a,perturbacion=b", "measured", "tasa",
                  value=0.5, numerator=5, denominator=10),
        fila_otra("robustness", "ROB-1", "categoria=a,perturbacion=c", "not_measured", "tasa", denominator=0),
    ]
    documentos.append(({**BASE_RUN, "run_id": ID_ROBUSTEZ, "source": "JUP-071", "run_at": dia(22)}, robustez, True))
    return documentos


def _construir_sintetico() -> dict:
    """Escribe un `rows-v1` por ejecución y un manifiesto en un tmpdir y devuelve `build_dataset`."""
    with tempfile.TemporaryDirectory(prefix="evaluation-dashboard-") as directorio:
        base = Path(directorio)
        entradas = []
        for ejecucion, filas, hito in _documentos_sinteticos():
            ruta = base / f"{ejecucion['run_id']}.json"
            ruta.write_text(json.dumps({"contract_version": 1, "run": ejecucion, "results": filas}), encoding="utf-8")
            entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": hito})
        manifiesto = base / "manifest.json"
        manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
        return tool.build_dataset([manifiesto], root=base)


REAL = Conjunto("real", _construir_real)
SINTETICO = Conjunto("sintetico", _construir_sintetico)


# --- Ejecución de consultas --------------------------------------------------------------------------------------------


def sustituir_macros(sql: str) -> str:
    """Sustituye las macros de Grafana que usa el dashboard; cualquier otra hace fallar con un mensaje claro."""
    sql = re.sub(r"\$__timeFilter\s*\([^()]*\)", "TRUE", sql)
    sql = re.sub(r"\$__timeFrom\s*\(\s*\)", "now() - interval '5 years'", sql)
    sql = re.sub(r"\$__timeTo\s*\(\s*\)", "now()", sql)
    sql = re.sub(r"\$__timeGroup\s*\(\s*([^,()]+?)\s*,\s*'1d'\s*\)", r"date_trunc('day', \1)", sql)
    sql = re.sub(r"\$__interval\b", "'1h'", sql)
    restos = re.findall(r"\$\{?\w+[^\s,;)]*", sql)
    if restos:
        raise ConsultaFallida(f"macro o variable de Grafana que este test no sabe sustituir: {sorted(set(restos))}")
    return sql


def ejecutar(sql: str, conjunto: Conjunto) -> dict:
    """Ejecuta `sql` (tal cual está en el dashboard) con el rol de lectura y devuelve columnas y filas tipadas.

    `columnas` es una lista `[(nombre, tipo)]` en orden y `filas` una lista de diccionarios. Se materializa en una tabla
    temporal para conocer los tipos de las columnas incluso con cero filas; un alias repetido falla ahí.
    """
    clave = (conjunto.clave, sql)
    if clave in _RESULTADOS:
        return _RESULTADOS[clave]
    cuerpo = sustituir_macros(sql).strip()
    cuerpo = cuerpo[:-1] if cuerpo.endswith(";") else cuerpo
    conjunto.cargar()
    guion = (
        f"SET ROLE {tool.READER_ROLE};\n"
        f"CREATE TEMP TABLE q AS\n{cuerpo}\n;\n"
        "SELECT jsonb_build_object("
        "'cols', (SELECT jsonb_agg(jsonb_build_array(a.attname::text, format_type(a.atttypid, a.atttypmod)) "
        "ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid = 'pg_temp.q'::regclass "
        "AND a.attnum > 0 AND NOT a.attisdropped), "
        "'rows', (SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM q));\n"
    )
    resultado = server().psql(stdin=guion)
    if resultado.returncode != 0:
        raise ConsultaFallida(f"la consulta falló: {resultado.stderr.strip()}\n--- SQL ---\n{cuerpo}")
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip()]
    datos = json.loads(lineas[-1])
    salida = {"columnas": [tuple(c) for c in datos["cols"]], "filas": datos["rows"]}
    _RESULTADOS[clave] = salida
    return salida


def consulta_panel(panel) -> str:
    objetivos = panel.get("targets", [])
    if len(objetivos) != 1:
        raise AssertionError(f"el panel {panel.get('title')!r} debe tener exactamente una consulta SQL")
    return objetivos[0]["rawSql"]


def de_panel(clave: str, conjunto: Conjunto) -> dict:
    """Resultado de la consulta del único panel `clave`."""
    return ejecutar(consulta_panel(S._unico(clave)), conjunto)


def nombres(resultado) -> list:
    return [nombre for nombre, _ in resultado["columnas"]]


def tipo_de(resultado, columna) -> str:
    return dict(resultado["columnas"])[columna]


def base_de_datos(sql: str) -> list:
    """Filas de una consulta del propio test (rol administrador), tipadas, para comparar con el panel."""
    resultado = server().psql(
        f"SELECT COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb) FROM ({sql}) t;")
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip())
    return json.loads([l for l in resultado.stdout.split("\n") if l.strip()][-1])


def instante(texto):
    """Texto ISO 8601 de PostgreSQL a `datetime` UTC."""
    return datetime.fromisoformat(texto).astimezone(timezone.utc)


def casi(obtenido, esperado) -> bool:
    """Igualdad con tolerancia relativa de 1e-3 y SIN confundir NULL con 0 (`None` solo es igual a `None`)."""
    if obtenido is None or esperado is None:
        return obtenido is None and esperado is None
    return abs(obtenido - esperado) <= 1e-3 * abs(esperado) + 1e-12


def celdas(fila) -> list:
    """Celdas de texto de una fila (para buscar el rótulo `no real` y sus motivos)."""
    return [str(valor) for valor in fila.values() if isinstance(valor, str)]


def comprobar_rotulo_real(caso, filas, run_id_de, runs_db):
    """Cada fila de una ejecución no real muestra `no real` y sus motivos; la de una real no dice `no real`."""
    for fila in filas:
        run = runs_db[run_id_de(fila)]
        textos = celdas(fila)
        if run["is_real"]:
            caso.assertFalse([t for t in textos if re.search(r"(?i)no real", t)], (run["run_id"], textos))
            caso.assertTrue([t for t in textos if re.search(r"(?i)\breal\b", t)], (run["run_id"], textos))
        else:
            caso.assertTrue([t for t in textos if re.search(r"(?i)\bno real\b", t)], (run["run_id"], textos))
            for motivo in run["non_real_reasons"]:
                caso.assertTrue([t for t in textos if motivo in t], (run["run_id"], motivo, textos))


def runs_de_la_base() -> dict:
    filas = base_de_datos(
        "SELECT run_id, source, run_at, is_real, non_real_reasons, comparability_key, milestone, commit_sha, "
        "suite, suite_version, generation_model FROM evaluation.runs")
    return {fila["run_id"]: fila for fila in filas}


def comprobar_texto_o_nulo(caso, obtenido, esperado, etiqueta):
    """Un metadato ausente llega como NULL o como `no registrado`; nunca como otro valor inventado."""
    if esperado is None:
        caso.assertTrue(obtenido is None or str(obtenido).strip().lower() == "no registrado", (etiqueta, obtenido))
    else:
        caso.assertEqual(obtenido, esperado, etiqueta)


# --- Conjunto versionado (cinco ejecuciones reales del manifiesto) -------------------------------------------------------


class ConjuntoVersionadoTests(unittest.TestCase):
    def test_todas_las_consultas_de_a_y_b_y_la_anotacion_se_ejecutan_con_el_rol_de_lectura(self):
        # Si una consulta tiene un error de SQL, usa una columna que no existe o necesita más permisos que `SELECT`
        # sobre `evaluation`, el panel de Grafana mostraría un error: aquí falla con el SQL y el mensaje de PostgreSQL.
        consultas = S.todas_las_consultas()
        self.assertGreaterEqual(len(consultas), 11)
        for etiqueta, objetivo, panel in consultas:
            with self.subTest(consulta=etiqueta):
                ejecutar(objetivo["rawSql"], REAL)

    def test_cada_consulta_devuelve_las_columnas_que_su_formato_exige(self):
        # `time_series` exige una columna de tiempo llamada `time` (Grafana no pinta una serie sin ella); la
        # anotación exige `time`, `text` y `tags`; ninguna consulta nombra columnas de texto de preguntas o respuestas.
        for etiqueta, objetivo, panel in S.todas_las_consultas():
            resultado = ejecutar(objetivo["rawSql"], REAL)
            with self.subTest(consulta=etiqueta):
                columnas = nombres(resultado)
                self.assertEqual(len(columnas), len(set(columnas)), columnas)
                self.assertFalse(COLUMNAS_PROHIBIDAS & {c.lower() for c in columnas}, columnas)
                formato = objetivo.get("format")
                self.assertIn(formato, ("table", "time_series"))
                if formato == "time_series":
                    self.assertIn("time", columnas)
                    self.assertEqual(tipo_de(resultado, "time"), TIMESTAMPTZ)
                    self.assertGreaterEqual(len(columnas), 2)
                if panel is None:
                    self.assertTrue({"time", "text", "tags"} <= set(columnas), columnas)

    def test_a1_tabla_de_ejecuciones_con_metadatos_y_estado_real_o_no(self):
        resultado = de_panel("a1", REAL)
        self.assertTrue(
            {"run_id", "source", "run_at", "suite_version", "commit_sha", "generation_model", "milestone"}
            <= set(nombres(resultado)), nombres(resultado))
        runs = runs_de_la_base()
        reales_a = {r for r, f in runs.items() if f["source"] != "JUP-068"}
        devueltas = [fila["run_id"] for fila in resultado["filas"]]
        # Las cuatro ejecuciones de la sección A (JUP-070 x2, JUP-078 sin fecha, JUP-022) o las cinco con la de negocio.
        self.assertEqual(len(devueltas), len(set(devueltas)), devueltas)
        self.assertIn(set(devueltas), (reales_a, set(runs)), devueltas)
        for fila in resultado["filas"]:
            run = runs[fila["run_id"]]
            with self.subTest(run_id=fila["run_id"]):
                self.assertEqual(fila["source"], run["source"])
                self.assertEqual(fila["milestone"], run["milestone"])
                if run["run_at"] is None:
                    # La ejecución sin fecha (JUP-078) sigue en la tabla y su fecha no se inventa.
                    self.assertIsNone(fila["run_at"])
                else:
                    self.assertEqual(instante(fila["run_at"]), instante(run["run_at"]))
                for columna in ("suite_version", "commit_sha", "generation_model"):
                    comprobar_texto_o_nulo(self, fila[columna], run[columna], columna)
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs)
        # Las dos de JUP-070 son de plantilla (no reales) y la de JUP-078 es real: la tabla las distingue.
        por_fuente = {runs[f["run_id"]]["source"]: f for f in resultado["filas"]}
        self.assertNotIn("no real", " ".join(celdas(por_fuente["JUP-078"])).lower())
        self.assertEqual(sum(1 for f in resultado["filas"] if runs[f["run_id"]]["source"] == "JUP-070"), 2)

    def test_a2_estados_de_los_casos_de_las_dos_ejecuciones_de_jup_070(self):
        resultado = de_panel("a2", REAL)
        self.assertTrue(
            {"run_id", "run_at", "suite", "suite_version", "commit_sha", "generation_model", "pass", "fail",
             "blocked", "not_run", "denominator"} <= set(nombres(resultado)), nombres(resultado))
        runs = runs_de_la_base()
        jup070 = {r for r, f in runs.items() if f["source"] == "JUP-070"}
        self.assertEqual(len(jup070), 2)
        self.assertEqual({f["run_id"] for f in resultado["filas"]}, jup070)
        self.assertEqual(len(resultado["filas"]), 2)
        for fila in resultado["filas"]:
            with self.subTest(run_id=fila["run_id"]):
                # Los cuatro estados con su total: 28 casos, todos `fail`; `blocked` y `not_run` son 0 MEDIDOS
                # (un recuento cero llega como 0, no como NULL ni como otro número) y no se suman a `fail`.
                self.assertEqual(
                    (fila["pass"], fila["fail"], fila["blocked"], fila["not_run"], fila["denominator"]),
                    (0, 28, 0, 0, 28))
                for estado in ("pass", "fail", "blocked", "not_run", "denominator"):
                    self.assertIsNotNone(fila[estado], estado)
                self.assertEqual(fila["generation_model"], "plantilla-sin-modelo")
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs)

    def _comparar_con_la_base(self, clave, grupos, columnas_extra=()):
        """a3 y a4: cada fila de resultados de los grupos llega tal cual (sin 0 inventados) y ninguna falta."""
        resultado = de_panel(clave, REAL)
        self.assertTrue(
            {"run_id", "metric_id", "behavior", "status", "value", "numerator", "denominator", *columnas_extra}
            <= set(nombres(resultado)), nombres(resultado))
        lista = ", ".join(f"'{g}'" for g in grupos)
        esperado = base_de_datos(
            "SELECT run_id, metric_id, behavior, status, value, numerator, denominator FROM evaluation.results "
            f"WHERE grp IN ({lista})")
        self.assertGreater(len(esperado), 0)
        clave_fila = lambda f: (f["run_id"], f["metric_id"], f["behavior"], f["status"])  # noqa: E731
        self.assertEqual(sorted(map(clave_fila, resultado["filas"])), sorted(map(clave_fila, esperado)))
        por_clave = {clave_fila(f): f for f in esperado}
        for fila in resultado["filas"]:
            origen = por_clave[clave_fila(fila)]
            with self.subTest(fila=clave_fila(fila)):
                for columna in ("value", "numerator", "denominator"):
                    self.assertTrue(casi(fila[columna], origen[columna]), (columna, fila[columna], origen[columna]))
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs_de_la_base())
        return resultado

    def test_a3_proporciones_de_calidad_con_numerador_denominador_y_estado(self):
        resultado = self._comparar_con_la_base("a3", ("accuracy", "relevance", "grounding"))
        # Las 16 métricas de calidad de cada ejecución de JUP-070 están medidas: ninguna fila se pierde ni cambia de
        # estado. Los nulos (métricas no medidas) se ejercitan con el conjunto sintético, porque los datos versionados
        # no los tienen en estos grupos.
        self.assertEqual(len(resultado["filas"]), 32)
        self.assertEqual({f["status"] for f in resultado["filas"]}, {"measured"})
        for fila in resultado["filas"]:
            self.assertIsNotNone(fila["value"])

    def test_a4_latencia_formato_y_disponibilidad_de_la_campana(self):
        resultado = self._comparar_con_la_base("a4", ("latency", "robustness", "availability"), ("unit",))
        self.assertTrue({"ms", "tasa"} <= {f["unit"] for f in resultado["filas"]})

    def test_a5_y_a6_no_dibujan_nada_con_los_datos_versionados(self):
        # Las cinco ejecuciones tienen claves de comparabilidad distintas: ninguna serie tiene con qué compararse y el
        # panel enseña su `noValue` («Sin datos: no hay con qué comparar») en vez de una línea o un punto en 0 %.
        for clave in ("a5", "a6"):
            resultado = de_panel(clave, REAL)
            with self.subTest(pieza=clave):
                self.assertEqual(nombres(resultado), ["time", "metric", "value"])
                self.assertEqual(resultado["filas"], [])

    def test_a7_calibracion_con_140_filas_y_20_candidatos_elegidos(self):
        resultado = de_panel("a7", REAL)
        self.assertTrue(
            {"run_id", "metric_id", "behavior", "value", "numerator", "denominator", "selected"}
            <= set(nombres(resultado)), nombres(resultado))
        self.assertEqual(len(resultado["filas"]), 140)
        self.assertEqual(sum(1 for f in resultado["filas"] if f["selected"] is True), 20)
        self.assertTrue(all(isinstance(f["selected"], bool) for f in resultado["filas"]))
        esperado = {(f["run_id"], f["metric_id"], f["behavior"]): f for f in base_de_datos(
            "SELECT run_id, metric_id, behavior, value, numerator, denominator, selected FROM evaluation.results "
            "WHERE grp = 'calibration'")}
        for fila in resultado["filas"]:
            origen = esperado[(fila["run_id"], fila["metric_id"], fila["behavior"])]
            with self.subTest(fila=(fila["metric_id"], fila["behavior"])):
                self.assertEqual(fila["selected"], origen["selected"])
                for columna in ("value", "numerator", "denominator"):
                    self.assertTrue(casi(fila[columna], origen[columna]), (columna, fila[columna], origen[columna]))
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs_de_la_base())

    def test_a8_benchmark_de_los_dos_modelos(self):
        resultado = de_panel("a8", REAL)
        self.assertTrue(
            {"run_id", "behavior", "successful", "cases", "keyword_score", "latency_p95", "cost"}
            <= set(nombres(resultado)), nombres(resultado))
        self.assertEqual(len(resultado["filas"]), 2)
        por_modelo = {f["behavior"]: f for f in resultado["filas"]}
        self.assertEqual(sorted(por_modelo), ["economicon-chat", "economicon-chat-deepseek"])
        # Valores del informe de JUP-078 (copiados, no recalculados): llamadas correctas sobre casos, puntuación
        # media por palabras clave, latencia p95 y coste.
        esperado = {
            "economicon-chat": (5, 5, 0.9, 11728.5, 0.0005395524),
            "economicon-chat-deepseek": (4, 5, 0.75, 10875.63, 0.0003567),
        }
        for modelo, (correctas, casos, puntuacion, latencia, coste) in esperado.items():
            fila = por_modelo[modelo]
            with self.subTest(modelo=modelo):
                self.assertEqual((fila["successful"], fila["cases"]), (correctas, casos))
                self.assertTrue(casi(fila["keyword_score"], puntuacion), fila["keyword_score"])
                self.assertTrue(casi(fila["latency_p95"], latencia), fila["latency_p95"])
                self.assertTrue(casi(fila["cost"], coste), fila["cost"])
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs_de_la_base())

    def test_a9_robustez_vacia_sin_informes_de_jup_071(self):
        # Sin informe de robustez no hay filas: el panel muestra «Sin datos» (su `noValue`) y no un 0 %. Las filas STR
        # de JUP-070 son de la campaña (a4), no de robustez futura: no aparecen aquí.
        resultado = de_panel("a9", REAL)
        self.assertEqual(resultado["filas"], [])
        self.assertIn("run_id", nombres(resultado))

    def test_b_la_tabla_de_negocio_muestra_tiempo_asignacion_y_ahorro_con_lo_no_medido_como_nulo(self):
        paneles_b = S._hay("b_tabla")  # primero el dashboard: sin él no hay nada que consultar (ni se arranca Docker)
        runs = runs_de_la_base()
        filas = []
        for panel in paneles_b:
            resultado = ejecutar(consulta_panel(panel), REAL)
            self.assertTrue(
                {"run_id", "metric_id", "behavior", "status", "value"} <= set(nombres(resultado)), nombres(resultado))
            filas.extend(resultado["filas"])
            comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs)
            # La ejecución de negocio es sintética: el estado dice `no real` y `sintetica`.
            for fila in resultado["filas"]:
                self.assertTrue(re.search(r"(?i)sint[eé]tic", " ".join(celdas(fila))), celdas(fila))
        esperado = {(f["run_id"], f["metric_id"], f["behavior"], f["status"]): f for f in base_de_datos(
            "SELECT run_id, metric_id, behavior, status, value, numerator, denominator FROM evaluation.results "
            "WHERE measure_type = 'B' AND run_id IN (SELECT run_id FROM evaluation.runs WHERE source = 'JUP-068')")}
        self.assertEqual(len(esperado), 23)
        for fila in filas:
            origen = esperado[(fila["run_id"], fila["metric_id"], fila["behavior"], fila["status"])]
            with self.subTest(fila=(fila["metric_id"], fila["behavior"], fila["status"])):
                self.assertTrue(casi(fila["value"], origen["value"]), (fila["value"], origen["value"]))
                for columna in ("numerator", "denominator"):
                    if columna in fila:
                        self.assertTrue(casi(fila[columna], origen[columna]), (columna, fila[columna]))
        # Todas las medidas pedidas aparecen en alguna tabla de B.
        for metrica in ("time_trials", "time_saved", "assigned_percent", "governed_percent",
                        "potential_savings", "realized_savings"):
            with self.subTest(metrica=metrica):
                self.assertTrue([f for f in filas if f["metric_id"] == metrica])
        # El beneficio realizado no se midió: `value` es NULL y NINGÚN cero ocupa su lugar.
        realizados = [f for f in filas if f["metric_id"] == "realized_savings"]
        self.assertEqual(len(realizados), len(S._hay("b_tabla")))
        for fila in realizados:
            self.assertEqual(fila["status"], "not_measured")
            self.assertIsNone(fila["value"])
            self.assertIsNone(fila.get("numerator"))
        # Los cuatro estados de las parejas de tiempo se ven como filas propias.
        self.assertEqual(
            {f["status"] for f in filas if f["metric_id"] == "time_trials"}, {"pass", "fail", "blocked", "not_run"})

    def test_la_anotacion_no_devuelve_nada_con_los_datos_versionados(self):
        # Las dos ejecuciones de JUP-070 solo difieren en el proveedor de embeddings: no es batería, modelo, prompt
        # ni corpus, así que no hay anotaciones.
        anotacion = S.anotaciones_propias()[0]["target"]
        resultado = ejecutar(anotacion["rawSql"], REAL)
        self.assertEqual(resultado["filas"], [])
        self.assertTrue({"time", "text", "tags"} <= set(nombres(resultado)))


# --- Conjunto sintético ------------------------------------------------------------------------------------------------


class ConjuntoSinteticoTests(unittest.TestCase):
    def test_el_conjunto_sintetico_es_el_que_las_pruebas_suponen(self):
        # Valida el propio montaje (las vistas ya tienen sus pruebas en `test_evaluation_views.py`): las ejecuciones
        # comparables y los cambios de configuración que usan los demás tests no dependen de una suposición.
        # Primero exige que el dashboard exista y sea válido: este test no lee ninguna consulta suya, pero no debe
        # pasar (ni arrancar Docker) mientras el dashboard no exista, para que el Red sea completo.
        S.dashboard()
        SINTETICO.cargar()
        comparables = base_de_datos("SELECT run_id FROM evaluation.comparable_runs")
        self.assertEqual({f["run_id"] for f in comparables}, COMPARABLES)
        cambios = base_de_datos("SELECT run_id, changes FROM evaluation.config_changes")
        self.assertEqual({f["run_id"]: f["changes"] for f in cambios},
                         {"SC-M-2": ["modelo"], "SC-B-2": ["bateria", "corpus"]})
        runs = runs_de_la_base()
        self.assertEqual({r for r, f in runs.items() if not f["is_real"] and r.startswith("SC-N")}, NO_REALES)

    def test_todas_las_consultas_se_ejecutan_tambien_con_el_conjunto_sintetico(self):
        for etiqueta, objetivo, panel in S.todas_las_consultas():
            with self.subTest(consulta=etiqueta):
                ejecutar(objetivo["rawSql"], SINTETICO)

    # -- a5 y a6: evolución ------------------------------------------------------------------------------------------

    def _puntos(self, clave):
        """Filas de la serie `clave` como `(run_id, metric_id, valor, etiqueta)`, identificando la ejecución por su día."""
        resultado = de_panel(clave, SINTETICO)
        self.assertEqual(nombres(resultado), ["time", "metric", "value"])
        self.assertEqual(tipo_de(resultado, "time"), TIMESTAMPTZ)
        self.assertIn(tipo_de(resultado, "metric"), ("text", "character varying"))
        self.assertIn(tipo_de(resultado, "value"), NUMERICOS)
        runs = runs_de_la_base()
        por_instante = {instante(f["run_at"]): r for r, f in runs.items() if f["run_at"] is not None}
        puntos = []
        for fila in resultado["filas"]:
            # Ningún punto sin valor: lo no medido no se dibuja ni se convierte en 0.
            self.assertIsNotNone(fila["value"], fila)
            self.assertIsNotNone(fila["time"], fila)
            self.assertIn(instante(fila["time"]), por_instante, fila)
            etiqueta = fila["metric"]
            ids = [m for m in ("ACC-1", "ACC-2", "REL-1") if re.search(rf"(?<![\w-]){m}(?![\w-])", etiqueta)]
            self.assertEqual(len(ids), 1, etiqueta)
            puntos.append((por_instante[instante(fila["time"])], ids[0], fila["value"], etiqueta))
        self._comprobar_etiquetas(puntos, runs)
        return puntos

    def _comprobar_etiquetas(self, puntos, runs):
        fuentes = {r: f["source"] for r, f in runs.items()}
        claves_por_etiqueta = {}
        for run_id, _, _, etiqueta in puntos:
            # La serie nombra su fuente, distingue las no reales y nunca une claves de comparabilidad distintas.
            self.assertIn(fuentes[run_id], etiqueta)
            if run_id in NO_REALES:
                self.assertIn("no real", etiqueta.lower(), etiqueta)
            else:
                self.assertNotIn("no real", etiqueta.lower(), etiqueta)
            claves_por_etiqueta.setdefault(etiqueta, set()).add(runs[run_id]["comparability_key"])
        for etiqueta, claves in claves_por_etiqueta.items():
            self.assertEqual(len(claves), 1, f"la serie {etiqueta!r} mezcla ejecuciones no comparables")
        # Dos series comparables de una misma fuente no comparten etiqueta (SC-A tiene dos claves).
        etiquetas_por_clave = {}
        for run_id, metrica, _, etiqueta in puntos:
            etiquetas_por_clave.setdefault((runs[run_id]["comparability_key"], metrica), set()).add(etiqueta)
        for clave, etiquetas in etiquetas_por_clave.items():
            self.assertEqual(len(etiquetas), 1, (clave, etiquetas))

    def test_a5_evolucion_automatica_solo_de_ejecuciones_comparables_y_medidas(self):
        puntos = self._puntos("a5")
        obtenido = sorted((r, m, round(v, 9)) for r, m, v, _ in puntos)
        esperado = []
        for run_id, _, numero, _, (acc2, _, rel1), _ in ESPECIFICACION:
            if run_id not in COMPARABLES:
                continue
            esperado.append((run_id, "ACC-2", acc2))
            if rel1 is not None and run_id!= "SC-A-2": # REL-1 de SC-A-1 no se midió: la serie SC-A-REL-1 solo tiene un punto medido y no se dibuja 
                esperado.append((run_id, "REL-1", rel1))
        self.assertEqual(obtenido, sorted((r, m, round(v, 9)) for r, m, v in esperado))
        # El 0.0 medido de SC-A-2 sí se dibuja (un cero medido no es un nulo).
        self.assertIn(("SC-A-2", "ACC-2", 0.0), [(r, m, v) for r, m, v, _ in puntos])
        # Ni la ejecución sin fecha, ni las que no tienen con qué compararse, ni las métricas humanas.
        run_ids = {r for r, _, _, _ in puntos}
        self.assertFalse(run_ids & {"SC-A-sin-fecha", "SC-M-1", "SC-B-1", "SC-B-2", ID_BENCHMARK, ID_CALIBRACION})
        self.assertNotIn("ACC-1", {m for _, m, _, _ in puntos})

    def test_a5_las_no_reales_se_distinguen_por_el_nombre_de_la_serie(self):
        puntos = self._puntos("a5")
        no_reales = {e for r, _, _, e in puntos if r in NO_REALES}
        reales = {e for r, _, _, e in puntos if r not in NO_REALES}
        self.assertTrue(no_reales and reales)
        self.assertFalse(no_reales & reales)
        # El motivo de no real es visible en el panel o en su leyenda (spec «Panel con ejecuciones mezcladas»).
        self.assertTrue(all("plantilla" in e.lower() for e in no_reales), no_reales)

    def test_a6_juicio_humano_solo_con_ejecuciones_de_hito(self):
        puntos = self._puntos("a6")
        obtenido = {(r, m): round(v, 9) for r, m, v, _ in puntos}
        self.assertEqual(len(obtenido), len(puntos))
        self.assertEqual({m for _, m in obtenido}, {"ACC-1"})
        obligatorios = {("SC-A-3", "ACC-1"): 0.31, ("SC-A-4", "ACC-1"): 0.36,
                        ("SC-N-1", "ACC-1"): 0.20, ("SC-N-2", "ACC-1"): 0.25}
        # SC-A-1 es la única ejecución de hito de su serie (SC-A-2 no lo es): que aparezca o no queda abierto.
        opcionales = {("SC-A-1", "ACC-1"): 0.50}
        for clave, valor in obligatorios.items():
            with self.subTest(punto=clave):
                self.assertEqual(obtenido.get(clave), valor)
        for clave, valor in obtenido.items():
            self.assertIn(clave, {**obligatorios, **opcionales})
            self.assertEqual(valor, {**obligatorios, **opcionales}[clave])
        # Las ejecuciones que no son de hito no salen: sus métricas humanas no se mezclan con las de hito.
        self.assertFalse({r for r, _ in obtenido} & {"SC-A-2", "SC-M-2", "SC-M-3", "SC-A-sin-fecha"})
        self.assertTrue([e for r, _, _, e in puntos if r in NO_REALES and "no real" in e.lower()])

    # -- anotación ------------------------------------------------------------------------------------------------------

    def test_la_anotacion_nombra_lo_que_cambio_en_la_fecha_de_la_segunda_ejecucion(self):
        anotacion = S.anotaciones_propias()[0]["target"]
        resultado = ejecutar(anotacion["rawSql"], SINTETICO)
        self.assertEqual(tipo_de(resultado, "time"), TIMESTAMPTZ)
        self.assertIn(tipo_de(resultado, "text"), ("text", "character varying"))
        self.assertIn(tipo_de(resultado, "tags"), ("text", "character varying"))
        obtenido = {(instante(f["time"]), f["text"], f["tags"]) for f in resultado["filas"]}
        self.assertEqual(len(obtenido), len(resultado["filas"]))
        # `modelo` entre SC-M-1 y SC-M-2 (día 8) y `bateria` + `corpus` entre SC-B-1 y SC-B-2 (día 11). Las etiquetas
        # van separadas por comas y sin llaves (`array_to_string`): un `text[]` crudo llegaría como `{modelo}`.
        self.assertEqual(obtenido, {
            (instante(dia(8)), "Cambia: modelo", "modelo"),
            (instante(dia(11)), "Cambia: bateria, corpus", "bateria,corpus"),
        })

    # -- las demás piezas con filas que los datos reales no tienen -------------------------------------------------------

    def test_a3_una_metrica_no_medida_llega_como_nulo_y_un_cero_medido_como_cero(self):
        # Regla central del dashboard: lo no medido es NULL y no 0 %. REL-1 de SC-A-1 no se midió (valor y numerador
        # NULL, denominador 0 conservado) y ACC-2 de SC-A-2 es un 0.0 MEDIDO que debe seguir siendo 0.
        resultado = de_panel("a3", SINTETICO)
        filas = {(f["run_id"], f["metric_id"]): f for f in resultado["filas"]}
        self.assertEqual(len(resultado["filas"]), 3 * len(ESPECIFICACION))
        self.assertEqual(len(filas), len(resultado["filas"]))
        no_medidas = [clave for clave, f in filas.items() if f["status"] == "not_measured"]
        self.assertEqual(no_medidas, [("SC-A-1", "REL-1")])
        vacia = filas[("SC-A-1", "REL-1")]
        self.assertIsNone(vacia["value"])
        self.assertIsNone(vacia["numerator"])
        self.assertEqual(vacia["denominator"], 0)
        cero = filas[("SC-A-2", "ACC-2")]
        self.assertEqual((cero["status"], cero["value"], cero["numerator"], cero["denominator"]),
                         ("measured", 0.0, 0, 100))
        # El resto conserva su valor, su numerador y su denominador.
        self.assertEqual(filas[("SC-A-1", "ACC-2")]["value"], 0.8)
        self.assertEqual(filas[("SC-A-1", "ACC-2")]["numerator"], 80)
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs_de_la_base())

    def test_a7_la_calibracion_sintetica_marca_el_candidato_y_conserva_el_nulo(self):
        resultado = de_panel("a7", SINTETICO)
        filas = resultado["filas"]
        self.assertEqual(len(filas), 3)
        self.assertEqual({f["run_id"] for f in filas}, {ID_CALIBRACION})
        por_clave = {(f["metric_id"], f["behavior"]): f for f in filas}
        elegido = por_clave[("document_hit_answer", "top_k=4,max_distance=0.6")]
        self.assertIs(elegido["selected"], True)
        self.assertEqual((elegido["value"], elegido["numerator"], elegido["denominator"]), (0.5, 5, 10))
        self.assertIs(por_clave[("document_hit_answer", "top_k=8,max_distance=0.6")]["selected"], False)
        vacio = por_clave[("empty_answer", "top_k=4,max_distance=0.6")]
        # No medido: el valor y el numerador siguen siendo NULL y el denominador conserva su 0.
        self.assertIsNone(vacio["value"])
        self.assertIsNone(vacio["numerator"])
        # Ejecución sintética: no real, con su motivo visible.
        comprobar_rotulo_real(self, filas, lambda f: f["run_id"], runs_de_la_base())
        self.assertTrue(all("sintetica" in " ".join(celdas(f)) for f in filas))

    def test_a8_el_benchmark_sin_llamadas_correctas_no_inventa_ceros(self):
        resultado = de_panel("a8", SINTETICO)
        por_modelo = {f["behavior"]: f for f in resultado["filas"]}
        self.assertEqual(sorted(por_modelo), ["m-cero", "m-ok"])
        cero, bueno = por_modelo["m-cero"], por_modelo["m-ok"]
        # Cero llamadas correctas sobre tres casos: el 0 de `successful` es medido; lo derivado (puntuación,
        # latencia p95, coste) NO se midió y llega NULL, nunca 0.
        self.assertEqual((cero["successful"], cero["cases"]), (0, 3))
        for columna in ("keyword_score", "latency_p95", "cost"):
            self.assertIsNone(cero[columna], columna)
        self.assertEqual((bueno["successful"], bueno["cases"]), (2, 3))
        self.assertEqual((bueno["keyword_score"], bueno["latency_p95"], bueno["cost"]), (0.8, 1000.0, 0.01))
        comprobar_rotulo_real(self, resultado["filas"], lambda f: f["run_id"], runs_de_la_base())

    def test_a9_las_filas_de_robustez_de_jup_071_aparecen_sin_cambiar_el_dashboard(self):
        resultado = de_panel("a9", SINTETICO)
        self.assertTrue(
            {"run_id", "source", "metric_id", "behavior", "status", "value", "numerator", "denominator"}
            <= set(nombres(resultado)), nombres(resultado))
        filas = resultado["filas"]
        self.assertEqual(len(filas), 2)
        self.assertEqual({(f["run_id"], f["source"]) for f in filas}, {(ID_ROBUSTEZ, "JUP-071")})
        por_comportamiento = {f["behavior"]: f for f in filas}
        medida = por_comportamiento["categoria=a,perturbacion=b"]
        self.assertEqual((medida["status"], medida["value"], medida["numerator"], medida["denominator"]),
                         ("measured", 0.5, 5, 10))
        no_medida = por_comportamiento["categoria=a,perturbacion=c"]
        self.assertEqual(no_medida["status"], "not_measured")
        self.assertIsNone(no_medida["value"])
        self.assertIsNone(no_medida["numerator"])

    def test_las_series_no_incluyen_el_benchmark_ni_la_calibracion_ni_la_robustez(self):
        # Esos informes tienen una sola ejecución (sin otra comparable): no forman serie.
        for clave in ("a5", "a6"):
            run_ids = {r for r, _, _, _ in self._puntos(clave)}
            with self.subTest(pieza=clave):
                self.assertFalse(run_ids & {ID_BENCHMARK, ID_CALIBRACION, ID_ROBUSTEZ})


if __name__ == "__main__":
    unittest.main()
