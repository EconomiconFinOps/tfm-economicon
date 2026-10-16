"""Ayudante de las pruebas de lectura del dashboard de evaluación (JUP-121, change `jup-121-lectura-dashboard`).

NO es un módulo de pruebas (sin `unittest.TestCase`): lo importan los `test_evaluation_readability_*.py`.

Por qué existe en lugar de reutilizar los ayudantes de las pruebas congeladas (`test_evaluation_dashboard_*.py`):
el diseño de este change obliga a PARCHEAR esas pruebas (cambian títulos, columnas y textos). Si estas pruebas nuevas
dependieran de sus ayudantes, el parche podría romperlas sin que nadie lo note. Aquí hay un cargador del dashboard y un
ejecutor de consultas propios, y las pruebas nuevas no importan nada de los módulos congelados.

Qué ofrece:

* Lectura del dashboard (`EVALUATION_DASHBOARD_JSON` sustituye la ruta, igual que en los módulos congelados; sirve para
  comprobar un JSON de referencia) y localizadores de panel POR TÍTULO o por lo que consultan, nunca por `id` ni por
  posición, para que no dependan del orden en que el coder numere o coloque los paneles.
* UN PostgreSQL desechable por proceso (la imagen exacta del `docker-compose.yml`, vía `evaluation_pg_helper`), con el
  conjunto VERSIONADO cargado una sola vez y el rol de solo lectura de Grafana. Cada escenario con datos sintéticos
  se ejecuta dentro de una transacción que SIEMPRE termina en `ROLLBACK`: el conjunto versionado queda intacto y no hace
  falta recargarlo (cargarlo cuesta segundos; un `ROLLBACK`, milisegundos).
* Las consultas de los paneles se ejecutan TAL CUAL están en el JSON y con el rol de lectura (`SET LOCAL ROLE`): si un
  panel necesitara algo más que `SELECT` sobre el esquema `evaluation`, fallaría aquí y no en Grafana.

Sin Docker, `servidor()` lanza `unittest.SkipTest("Docker no disponible")`: es la única excepción a «sin skip» (como en
las demás pruebas del repositorio con servicios reales).
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (contenedor desechable compartido con los demás módulos)

DASHBOARD = Path(os.environ.get("EVALUATION_DASHBOARD_JSON")
                 or ROOT / "apps" / "monitoring" / "grafana" / "dashboards" / "assistant-evaluation.json")
CATALOGO = ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json"
READER = "grafana_evaluation_reader"

DS_POSTGRES = {"type": "grafana-postgresql-datasource", "uid": "evaluation-postgres"}
DS_PROMETHEUS = {"type": "prometheus", "uid": "prometheus"}
DATASOURCE_POR_SECCION = {"A": DS_POSTGRES, "B": DS_POSTGRES, "C": DS_PROMETHEUS}

# Seis familias del catálogo de JUP-067 que la tabla por métrica y ejecución recorre, en el orden del catálogo.
FAMILIAS = ("accuracy", "relevance", "grounding", "latency", "robustness", "availability")


# --- Lectura del dashboard --------------------------------------------------------------------------------------------

_CACHE: dict = {}


def dashboard() -> dict:
    """Dashboard como diccionario; si el fichero no existe falla con una aserción legible (Red claro, no un error de E/S)."""
    if "dashboard" not in _CACHE:
        if not DASHBOARD.is_file():
            raise AssertionError(f"no existe el dashboard esperado: {DASHBOARD}")
        _CACHE["dashboard"] = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    return _CACHE["dashboard"]


def paneles() -> list:
    lista = dashboard().get("panels")
    if not isinstance(lista, list) or not lista:
        raise AssertionError("`panels` debe ser una lista no vacía")
    return lista


def filas() -> list:
    return [p for p in paneles() if p.get("type") == "row"]


def seccion_de(panel) -> str:
    """Letra de la sección del panel: la de la última fila que queda por encima (las filas no están plegadas)."""
    anteriores = [f for f in filas() if f["gridPos"]["y"] < panel["gridPos"]["y"]]
    if not anteriores:
        raise AssertionError(f"el panel {panel.get('title')!r} no está debajo de ninguna fila")
    return max(anteriores, key=lambda f: f["gridPos"]["y"])["title"][:1]


def contenido() -> list:
    """`[(letra de sección, panel)]` de los paneles que no son fila."""
    return [(seccion_de(p), p) for p in paneles() if p.get("type") != "row"]


def de_seccion(letra: str) -> list:
    return [p for s, p in contenido() if s == letra]


def por_titulo(prefijo: str, seccion: str | None = None) -> dict:
    """El ÚNICO panel que no es fila cuyo título empieza por `prefijo` (opcionalmente de una sección).

    Falla con un mensaje claro si no hay ninguno o hay varios: así un panel que falta se ve como «falta el panel» y no
    como un error de tipo en otra parte de la prueba.
    """
    candidatos = [p for s, p in contenido() if p["title"].startswith(prefijo) and (seccion is None or s == seccion)]
    if len(candidatos) != 1:
        titulos = [p["title"] for _, p in contenido()]
        raise AssertionError(f"se esperaba exactamente un panel que empiece por {prefijo!r} y hay {len(candidatos)}; "
                             f"títulos: {titulos}")
    return candidatos[0]


def sql_de(panel) -> str:
    return "\n".join(t.get("rawSql", "") for t in panel.get("targets", []))


def consulta_unica(panel) -> str:
    objetivos = panel.get("targets", [])
    if len(objetivos) != 1:
        raise AssertionError(f"el panel {panel.get('title')!r} debe tener exactamente una consulta")
    return objetivos[0]["rawSql"]


def plano(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


def defaults(panel) -> dict:
    return panel.get("fieldConfig", {}).get("defaults", {})


# --- Columnas: nombre visible y visibilidad (overrides por nombre) ---------------------------------------------------


def propiedades(panel, columna: str) -> dict:
    """`{id de propiedad: valor}` de los overrides `byName` de `columna` (si hay varios, se fusionan en orden)."""
    resultado = {}
    for override in panel.get("fieldConfig", {}).get("overrides", []):
        if override.get("matcher") == {"id": "byName", "options": columna}:
            for propiedad in override.get("properties", []):
                resultado[propiedad["id"]] = propiedad.get("value")
    return resultado


def oculta(panel, columna: str) -> bool:
    return propiedades(panel, columna).get("custom.hidden") is True


def nombre_visible(panel, columna: str) -> str:
    """Rótulo con el que Grafana muestra la columna: su `displayName` o, si no hay, el nombre de la columna."""
    return propiedades(panel, columna).get("displayName") or columna


def columnas_visibles(panel, columnas) -> list:
    """Rótulos de las columnas no ocultas, en el orden de la consulta."""
    return [nombre_visible(panel, c) for c in columnas if not oculta(panel, c)]


def sin_acentos(texto: str) -> str:
    """Quita las tildes (el catálogo de JUP-067 está en ASCII y el dashboard puede llevar las tildes correctas)."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def catalogo() -> list:
    """Las 17 métricas del catálogo de JUP-067, en el orden del catálogo."""
    return json.loads(CATALOGO.read_text(encoding="utf-8"))["metrics"]


# --- PostgreSQL desechable compartido por el proceso -----------------------------------------------------------------

_PG: dict = {}


def servidor() -> evaluation_pg_helper.PostgresServer:
    """Servidor del proceso con el conjunto versionado y el rol de lectura; se crea en el primer uso.

    Si no hay Docker lanza `SkipTest` (y recuerda el motivo); si el montaje falla, repite el error en cada uso en lugar
    de levantar otro contenedor. El contenedor lo borra el `atexit` del ayudante aunque ningún `tearDownModule` llegue
    a ejecutarse.
    """
    if "failure" in _PG:
        raise unittest.SkipTest(_PG["failure"])
    if "error" in _PG:
        raise RuntimeError(_PG["error"])
    if "instance" not in _PG:
        try:
            _PG["instance"] = evaluation_pg_helper.PostgresServer()
        except unittest.SkipTest as skip:
            _PG["failure"] = str(skip)
            raise
        try:
            herramienta = evaluation_pg_helper.load_tool()
            _PG["instance"].load_dataset(herramienta.build_dataset([herramienta.DEFAULT_MANIFEST]), herramienta)
            resultado = _PG["instance"].psql(stdin=herramienta.build_role_sql(secrets.token_urlsafe(18)))
            if resultado.returncode != 0:
                raise RuntimeError(f"no se pudo crear el rol de lectura: {resultado.stderr.strip()}")
        except BaseException as error:
            _PG["error"] = f"no se pudo montar la prueba: {error}"
            _PG["instance"].stop()
            raise
    return _PG["instance"]


def sustituir_macros(sql: str) -> str:
    """Macros de Grafana que usa el dashboard; cualquier otra hace fallar con un mensaje claro."""
    sql = re.sub(r"\$__timeFilter\s*\([^()]*\)", "TRUE", sql)
    sql = re.sub(r"\$__timeFrom\s*\(\s*\)", "now() - interval '5 years'", sql)
    sql = re.sub(r"\$__timeTo\s*\(\s*\)", "now()", sql)
    sql = re.sub(r"\$__interval\b", "'1h'", sql)
    restos = re.findall(r"\$\{?\w+[^\s,;)]*", sql)
    if restos:
        raise AssertionError(f"macro o variable de Grafana que esta prueba no sabe sustituir: {sorted(set(restos))}")
    return sql


_RESULTADOS: dict = {}


def ejecutar(sql: str, preparacion: str = "") -> dict:
    """Ejecuta `sql` (tal cual está en el dashboard) con el rol de lectura y devuelve columnas y filas tipadas.

    `preparacion` es SQL de administrador (inserciones o borrados sintéticos) que se aplica ANTES de cambiar de rol y
    dentro de la misma transacción; la transacción termina siempre en `ROLLBACK`, así que ningún escenario contamina
    al siguiente. Devuelve `{"columnas": [(nombre, tipo)], "filas": [dict]}`; se materializa en una tabla temporal para
    conocer los tipos incluso con cero filas. Con caché por (preparación, consulta).
    """
    clave = (preparacion, sql)
    if clave in _RESULTADOS:
        return _RESULTADOS[clave]
    cuerpo = sustituir_macros(sql).strip()
    cuerpo = cuerpo[:-1] if cuerpo.endswith(";") else cuerpo
    guion = (
        "BEGIN;\n"
        f"{preparacion}\n"
        f"SET LOCAL ROLE {READER};\n"
        f"CREATE TEMP TABLE q ON COMMIT DROP AS\n{cuerpo}\n;\n"
        "SELECT jsonb_build_object("
        "'cols', (SELECT jsonb_agg(jsonb_build_array(a.attname::text, format_type(a.atttypid, a.atttypmod)) "
        "ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid = 'pg_temp.q'::regclass "
        "AND a.attnum > 0 AND NOT a.attisdropped), "
        "'rows', (SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM q));\n"
        "ROLLBACK;\n"
    )
    resultado = servidor().psql(stdin=guion)
    if resultado.returncode != 0:
        raise AssertionError(f"la consulta falló: {resultado.stderr.strip()}\n--- SQL ---\n{cuerpo}")
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip().startswith("{")]
    datos = json.loads(lineas[-1])
    salida = {"columnas": [tuple(c) for c in datos["cols"]], "filas": datos["rows"]}
    _RESULTADOS[clave] = salida
    return salida


def administrar(sql: str, preparacion: str = "") -> list:
    """Filas (diccionarios) de una consulta del PROPIO test, con rol de administrador, sobre el mismo escenario."""
    guion = (
        "BEGIN;\n"
        f"{preparacion}\n"
        f"SELECT COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb) FROM ({sql}) t;\n"
        "ROLLBACK;\n"
    )
    resultado = servidor().psql(stdin=guion)
    if resultado.returncode != 0:
        raise AssertionError(resultado.stderr.strip())
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip().startswith("[")]
    return json.loads(lineas[-1])


def nombres(resultado: dict) -> list:
    return [nombre for nombre, _ in resultado["columnas"]]


# --- Datos sintéticos (INSERT directos, siempre dentro de un escenario con ROLLBACK) -----------------------------------


def literal(valor) -> str:
    """Literal SQL de un valor de prueba (cadena, número, booleano, lista de textos o `None`)."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float)):
        return repr(valor)
    if isinstance(valor, (list, tuple)):
        return "ARRAY[" + ", ".join(literal(v) for v in valor) + "]::text[]" if valor else "'{}'::text[]"
    return "'" + str(valor).replace("'", "''") + "'"


def insertar_ejecucion(run_id, fuente, run_at, *, real=True, motivos=(), clave=None, hito=False) -> str:
    """`INSERT` de una fila de `evaluation.runs` (columnas obligatorias rellenas; `run_at` `None` = sin fecha)."""
    return (
        "INSERT INTO evaluation.runs (run_id, source, run_at, synthetic, is_real, non_real_reasons, comparability_key,"
        " format, milestone, report_sha256) VALUES ("
        f"{literal(run_id)}, {literal(fuente)}, {literal(run_at)}, false, {literal(real)}, {literal(list(motivos))},"
        f" {literal(clave or 'k-' + run_id)}, 'rows-v1', {literal(hito)}, {literal('h-' + run_id)});\n"
    )


def insertar_resultado(run_id, grp, metric_id, behavior="all", *, estado="measured", valor=None, unidad="tasa",
                       numerador=None, denominador=None, ci_bajo=None, ci_alto=None, juicio="automatic",
                       recuento=None, tipo="A") -> str:
    """`INSERT` de una fila de `evaluation.results`. Un `not_measured` no puede traer valor, numerador ni intervalo."""
    return (
        "INSERT INTO evaluation.results (run_id, measure_type, grp, metric_id, behavior, status, case_count, value,"
        " unit, numerator, denominator, ci_low, ci_high, judgment) VALUES ("
        f"{literal(run_id)}, {literal(tipo)}, {literal(grp)}, {literal(metric_id)}, {literal(behavior)},"
        f" {literal(estado)}, {literal(recuento)}, {literal(valor)}, {literal(unidad)}, {literal(numerador)},"
        f" {literal(denominador)}, {literal(ci_bajo)}, {literal(ci_alto)}, {literal(juicio)});\n"
    )


def insertar_casos(run_id, aprobados, total, fallidos=None) -> str:
    """Las cuatro filas de estados de casos (`grp = 'cases'`) de una ejecución de JUP-070, como las deja la herramienta."""
    fallidos = total - aprobados if fallidos is None else fallidos
    contadores = {"pass": aprobados, "fail": fallidos, "blocked": 0, "not_run": 0}
    return "".join(
        insertar_resultado(run_id, "cases", "cases", "all", estado=estado, unidad="casos", denominador=total,
                           recuento=cuenta, juicio=None)
        for estado, cuenta in contadores.items())
