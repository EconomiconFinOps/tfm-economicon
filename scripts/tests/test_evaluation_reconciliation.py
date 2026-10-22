"""Conciliación del dashboard de evaluación con los informes ORIGINALES (JUP-121, tarea 5.1).

Es la prueba que exige la tarjeta: «los recuentos del dashboard coinciden con los de cada informe original». Cierra el
círculo entero con un PostgreSQL real (el contenedor desechable de `evaluation_pg_helper`, la imagen exacta de
`postgres-pgvector`):

    informe original (JSON)  ->  adaptadores  ->  `build_sql`  ->  PostgreSQL  ->  SQL de los PANELES  ->  lo que se ve

Los valores ESPERADOS no salen de ningún adaptador ni de `build_dataset`: este módulo lee los JSON originales
(`docs/evidence/JUP-070-run-{1,2}-report.json`, `docs/evidence/JUP-078-benchmark-results.json`,
`docs/spikes/JUP-022-retrieval-calibration.json`) y el informe de negocio que genera `tools/business-metrics.mjs report`
sobre `docs/validation/JUP-068-example.json`, y calcula aquí mismo los recuentos y proporciones que deben verse. Solo
usa de la herramienta lo que hay que probar de punta a punta: el manifiesto versionado y `build_sql`/`build_role_sql`
para cargar. Si un adaptador copiara mal un numerador, si `build_sql` perdiera una fila o si una consulta del dashboard
rellenara un nulo con 0, aquí se vería con el número original al lado.

Las consultas son LAS DEL DASHBOARD: se leen de `rawSql` del JSON (ruta sustituible con `EVALUATION_DASHBOARD_JSON`),
se localizan con el mismo localizador que `test_evaluation_dashboard_structure.py`, se sustituyen las macros de
Grafana como en `test_evaluation_dashboard_queries.py` y se ejecutan con `SET ROLE grafana_evaluation_reader`, el
rol con el que lee Grafana. Lo que no es un panel (los censos de filas y de estados) se consulta también con ese rol.

Convenciones del contrato que el oráculo da por buenas (están en `docs/validation/evaluation-dashboard.md`): el
`behavior` de una métrica por grupo, etapa o categoría es el nombre del informe (`clarify`, `generation`, `timeout`...),
`ACC-2` lleva además la fila `judged`, `REL-4` se publica como `median`, `q1` y `q3`, JUP-078 usa el alias del modelo
como `behavior`, JUP-022 usa `top_k=K,max_distance=D` (`none` sin umbral) y JUP-068 llama `total` y `eligible` a
`total_minor` y `eligible_minor`. Los valores y las proporciones se comparan con igualdad exacta salvo la tolerancia de
formato (`1e-9` relativa: PostgreSQL devuelve el `double precision` en su forma más corta).

La ejecución de estas pruebas tarda unos segundos: un contenedor por módulo y consultas en caché.
"""
from __future__ import annotations

import json
import math
import re
import secrets
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (contenedor desechable y herramienta, compartidos con 3.2, 3.3 y 5.x)
import test_evaluation_dashboard_structure as S  # noqa: E402  (localizador de paneles del contrato)
from test_evaluation_dashboard_queries import sustituir_macros  # noqa: E402  (macros de Grafana, una sola fuente)

# Valores literales del contrato (no se leen de la herramienta para poder compararlos con ella).
READER = "grafana_evaluation_reader"
TOLERANCIA_FORMATO = 1e-9

RUTAS = {
    "jup070-1": "docs/evidence/JUP-070-run-1-report.json",
    "jup070-2": "docs/evidence/JUP-070-run-2-report.json",
    "jup078": "docs/evidence/JUP-078-benchmark-results.json",
    "jup022": "docs/spikes/JUP-022-retrieval-calibration.json",
    "jup068-entrada": "docs/validation/JUP-068-example.json",
    "jup130-anomalies": "docs/evidence/JUP-130/JUP-130-anomalies.rows.json",
    "jup130-data": "docs/evidence/JUP-130/JUP-130-data.rows.json",
    "jup130-ai-cost": "docs/evidence/JUP-130/JUP-130-ai-cost.rows.json",
    "jup071": "docs/evidence/JUP-071-live-r1-rows.json",
    "jup070-3": "docs/evidence/JUP-133/JUP-133-bank28-report.json",
    "jup071-flash": "docs/evidence/JUP-071-live-flash-r1-rows.json",
    "jup133-ai-cost": "docs/evidence/JUP-133/JUP-133-ai-cost.rows.json",
}
JUP130 = ("jup130-anomalies", "jup130-data", "jup130-ai-cost", "jup071", "jup071-flash", "jup133-ai-cost")
# Campañas de JUP-070 (las dos de octubre y la del banco con el modelo nuevo de JUP-133) y las filas de cada una.
JUP070 = ("jup070-1", "jup070-2", "jup070-3")
FILAS_DE = {"jup070-1": 48, "jup070-2": 48, "jup070-3": 52}
# Resultados que deben existir: lo que se deduce de los informes (2 x 48 + 10 + 140 + 23 + 16 + 10 + 13 + 136). Se escribe en el test para
# que un cambio de los datos obligue a mirar este número y no se acepte «lo que haya».
FILAS_JUP070 = 48
FILAS_JUP078 = 10
FILAS_JUP022 = 140
FILAS_JUP068 = 23
FILAS_JUP130 = (16, 10, 13, 136, 136, 15)
TOTAL_ESPERADO = sum(FILAS_DE.values()) + FILAS_JUP078 + FILAS_JUP022 + FILAS_JUP068 + sum(FILAS_JUP130)
ESTADOS_DE_CASO = ("pass", "fail", "blocked", "not_run")


# --- Servidor y carga: un contenedor por módulo ---------------------------------------------------------------------

_SERVER: dict = {}
_CONSULTAS: dict = {}


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo, creado de forma perezosa en el primer uso (como en las demás pruebas con PostgreSQL).

    Sin Docker lanza `SkipTest` (y recuerda el motivo); si la carga falla, el error se repite en cada uso en lugar de
    levantar otro contenedor. Si algo falla después, el contenedor lo borra el `atexit` del ayudante aunque
    `tearDownModule` no llegue a ejecutarse."""
    if "failure" in _SERVER:
        raise unittest.SkipTest(_SERVER["failure"])
    if "error" in _SERVER:
        raise RuntimeError(_SERVER["error"])
    if "instance" not in _SERVER:
        try:
            _SERVER["instance"] = evaluation_pg_helper.PostgresServer()
        except unittest.SkipTest as skip:
            _SERVER["failure"] = str(skip)
            raise
        try:
            _cargar_versionado(_SERVER["instance"])
        except BaseException as error:
            _SERVER["error"] = f"no se pudo montar la prueba: {error}"
            raise
    return _SERVER["instance"]


def _cargar_versionado(instance) -> None:
    tool = evaluation_pg_helper.load_tool()
    # Conjunto VERSIONADO tal cual lo carga `corepack pnpm evaluation-dashboard:load`: las ocho ejecuciones del manifiesto.
    dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])
    guion = tool.build_sql(dataset) + "\n" + tool.build_role_sql(secrets.token_urlsafe(18))
    resultado = instance.psql(stdin=guion)
    if resultado.returncode != 0:
        raise RuntimeError(f"no se pudo cargar el conjunto versionado: {resultado.stderr.strip()}")


def tearDownModule() -> None:
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


# --- Consultas con el rol de Grafana --------------------------------------------------------------------------------


def con_el_rol(sql: str) -> list:
    """Filas (diccionarios) de `sql` ejecutado con `SET ROLE grafana_evaluation_reader`, tal cual está escrito.

    Se envuelve en una subconsulta para recoger las filas como JSON sin tocar la consulta; una macro de Grafana se
    sustituye antes, y una desconocida hace fallar la prueba con un mensaje claro. Con caché: cada texto SQL se ejecuta
    una sola vez en el módulo.
    """
    if sql in _CONSULTAS:
        return _CONSULTAS[sql]
    cuerpo = sustituir_macros(sql).strip()
    cuerpo = cuerpo[:-1] if cuerpo.endswith(";") else cuerpo
    guion = (f"SET ROLE {READER};\n"
             f"SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM (\n{cuerpo}\n) q;\n")
    resultado = server().psql(stdin=guion)
    if resultado.returncode != 0:
        raise AssertionError(f"la consulta falló con el rol de lectura: {resultado.stderr.strip()}\n--- SQL ---\n{cuerpo}")
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip()]
    filas = json.loads(lineas[-1])
    _CONSULTAS[sql] = filas
    return filas


def del_panel(clave: str) -> list:
    """Filas de la consulta del único panel `clave` (a1..a9) del dashboard."""
    objetivos = S._unico(clave).get("targets", [])
    assert len(objetivos) == 1, f"el panel {clave} debe tener una sola consulta"
    return con_el_rol(objetivos[0]["rawSql"])


def de_los_paneles_de_negocio() -> list:
    filas = []
    for panel in S._hay("b_tabla"):
        objetivos = panel.get("targets", [])
        assert len(objetivos) == 1, f"el panel {panel.get('title')!r} debe tener una sola consulta"
        filas += con_el_rol(objetivos[0]["rawSql"])
    return filas


# --- Lectura de los informes originales (sin adaptadores) -----------------------------------------------------------


def leer(clave: str) -> dict:
    return json.loads((ROOT / RUTAS[clave]).read_text(encoding="utf-8"))


def filas_de_los_indicadores() -> list:
    """Filas de los paneles de la sección B de JUP-130 (coste de IA y datos), una consulta por panel."""
    filas = []
    for panel in S._hay("b_indicadores"):
        objetivos = panel.get("targets", [])
        assert len(objetivos) == 1, f"el panel {panel.get('title')!r} debe tener una sola consulta"
        filas += con_el_rol(objetivos[0]["rawSql"])
    return filas


def informe_de_negocio() -> dict:
    """Informe de JUP-068 tal como lo genera su CLI (la misma orden que la documentación del proyecto)."""
    ruta = RUTAS["jup068-entrada"]
    proceso = subprocess.run(["node", "tools/business-metrics.mjs", "report", ruta], cwd=ROOT, capture_output=True,
                             timeout=60, check=False)
    if proceso.returncode != 0:
        raise AssertionError(f"`business-metrics.mjs report` falló: {proceso.stderr.decode('utf-8', 'replace')}")
    return json.loads(proceso.stdout.decode("utf-8"))


def instante(texto: str) -> datetime:
    """Texto ISO 8601 (con `Z` o con desfase) a `datetime` UTC; el `Z` se normaliza para no depender de la versión de Python."""
    return datetime.fromisoformat(texto.replace("Z", "+00:00")).astimezone(timezone.utc)


# --- Oráculo: filas esperadas de cada informe -----------------------------------------------------------------------
# Una fila esperada es `{(metric_id, behavior, status): {"value", "numerator", "denominator", "unit", "count"}}`.


def fila(value=None, numerator=None, denominator=None, unit="", count=None) -> dict:
    return {"value": value, "numerator": numerator, "denominator": denominator, "unit": unit, "count": count}


def proporcion(datos: dict, medida: bool = True) -> dict:
    """Métrica `{k, n, rate}` del informe. Con `available: false` queda no medida con su denominador (regla 6 del contrato)."""
    if datos.get("available") is False:
        return fila(None, None, datos["n"], "tasa")
    return fila(datos["rate"], datos["k"], datos["n"], "tasa")


def esperado_jup070(informe: dict) -> dict:
    """48 filas de una campaña de JUP-070, calculadas de su informe original (sin pasar por el adaptador)."""
    esperado = {}
    contadores = informe["counts"]
    for estado in ESTADOS_DE_CASO:
        esperado[("cases", "all", estado)] = fila(denominator=contadores["cases"], unit="casos", count=contadores[estado])
    metricas = informe["metrics"]
    esperado[("ACC-1", "all", "measured")] = proporcion(metricas["ACC-1"])
    esperado[("ACC-2", "all", "measured")] = proporcion(metricas["ACC-2"])
    esperado[("ACC-2", "judged", "measured")] = proporcion(metricas["ACC-2"]["judged"])
    for grupo, datos in metricas["ACC-3"]["groups"].items():
        esperado[("ACC-3", grupo, "measured")] = proporcion(datos)
    for metrica in ("REL-1", "REL-2", "GRD-1", "GRD-3", "STR-1", "AVL-1"):
        esperado[(metrica, "all", "measured")] = proporcion(metricas[metrica])
    for grupo, datos in metricas["REL-3"]["groups"].items():
        esperado[("REL-3", grupo, "measured")] = proporcion(datos)
    rel4 = metricas["REL-4"]
    for clave in ("median", "q1", "q3"):
        esperado[("REL-4", clave, "measured")] = fila(rel4[clave], None, rel4["n"], "similitud")
    esperado[("GRD-2", "all", "measured")] = fila(metricas["GRD-2"]["total"], unit="recuento")
    for caso, total in metricas["GRD-2"].get("by_case", {}).items():
        esperado[("GRD-2", caso, "measured")] = fila(total, unit="recuento")
    for metrica in ("LAT-1", "LAT-2", "LAT-3"):
        for etapa, datos in metricas[metrica]["stages"].items():
            esperado[(metrica, etapa, "measured")] = fila(datos["value"], None, datos["n"], "ms")
    for etapa, datos in metricas["LAT-4"]["stages"].items():
        esperado[("LAT-4", etapa, "measured")] = proporcion(datos)
    for categoria, total in metricas["STR-2"]["by_category"].items():
        esperado[("STR-2", categoria, "measured")] = fila(total, unit="recuento")
    esperado[("STR-2", "all", "measured")] = fila(metricas["STR-2"]["total"], unit="recuento")
    return esperado


def esperado_jup078(informe: dict) -> dict:
    """Por modelo: `{alias: {successful, cases, keyword_score, latency_p95, cost}}` del informe original.

    Sin llamadas correctas el informe escribe un 0 de «nada que promediar»: lo que se debe ver es NULL, no ese 0.
    """
    modelos = {}
    for modelo in informe["models"]:
        con_datos = modelo["successful"] > 0
        modelos[modelo["alias"]] = {
            "successful": modelo["successful"], "cases": modelo["cases"],
            "keyword_score": modelo["mean_keyword_score"] if con_datos else None,
            "latency_p95": modelo["p95_latency_ms"] if con_datos else None,
            "cost": modelo["cost_usd"] if con_datos else None,
        }
    return modelos


def esperado_jup022(informe: dict) -> dict:
    """Cinco filas por punto del barrido y la marca `selected` de los candidatos de `selection`."""
    elegidos = {(c["top_k"], c["max_distance"]) for c in informe["selection"]["candidates"]}
    esperado = {}
    for punto in informe["points"]:
        umbral = "none" if punto["max_distance"] is None else str(punto["max_distance"])
        comportamiento = f"top_k={punto['top_k']},max_distance={umbral}"
        for metrica, grupo, tasa, casos in (
            ("document_hit_answer", "answer", "document_hit_rate", "cases"),
            ("section_hit_answer", "answer", "section_hit_rate", "section_cases"),
            ("empty_answer", "answer", "empty_rate", "cases"),
            ("document_hit_non_answer", "non_answer", "document_hit_rate", "cases"),
            ("empty_non_answer", "non_answer", "empty_rate", "cases"),
        ):
            valor, n = punto[grupo][tasa], punto[grupo][casos]
            if n == 0:
                fila_esperada = {"value": None, "numerator": None, "denominator": 0}
            else:
                # El informe redondea la tasa a 4 decimales: el numerador es el único `k` que la reproduce.
                k = round(valor * n)
                assert round(k / n, 4) == valor, ("la tasa de JUP-022 no es una fracción k/n", comportamiento, metrica)
                fila_esperada = {"value": valor, "numerator": k, "denominator": n}
            fila_esperada["selected"] = (punto["top_k"], punto["max_distance"]) in elegidos
            esperado[(metrica, comportamiento)] = fila_esperada
    return esperado


def esperado_jup068(informe: dict) -> dict:
    """23 filas de negocio de JUP-068, del informe que genera `business-metrics.mjs`."""
    tiempo, asignacion, ahorro = informe["time"], informe["allocation"], informe["savings"]
    moneda = f"{informe['currency'].lower()}_minor_{informe['minor_unit_digits']}"
    parejas = tiempo["eligible_pairs"]
    intentos = sum(tiempo["results"][estado] for estado in ESTADOS_DE_CASO)
    elegible = asignacion["eligible_minor"]
    esperado = {}
    for estado in ESTADOS_DE_CASO:
        esperado[("time_trials", "all", estado)] = fila(denominator=intentos, unit="parejas", count=tiempo["results"][estado])
    esperado[("manual_time", "all", "measured")] = fila(tiempo["manual_ms"], None, parejas, "ms")
    esperado[("assisted_time", "all", "measured")] = fila(tiempo["assisted_ms"], None, parejas, "ms")
    esperado[("time_saved", "all", "measured")] = fila(tiempo["saved_ms"], None, parejas, "ms")
    esperado[("time_saved_percent", "all", "measured")] = fila(
        tiempo["saved_percent"], tiempo["saved_ms"], tiempo["manual_ms"], "porcentaje")
    for metrica, clave in (("allocated", "allocated"), ("shared", "shared"), ("unallocated", "unallocated"),
                           ("excluded", "excluded"), ("total", "total_minor"), ("eligible", "eligible_minor")):
        esperado[(metrica, "all", "measured")] = fila(asignacion[clave], unit=moneda)
    for metrica, numerador in (("assigned_percent", asignacion["allocated"]),
                               ("governed_percent", asignacion["allocated"] + asignacion["shared"]),
                               ("unallocated_percent", asignacion["unallocated"])):
        esperado[(metrica, "all", "measured")] = fila(asignacion[metrica], numerador, elegible, "porcentaje")
    for comportamiento, clave in (("estimated", "estimated_count"), ("candidate", "candidate_count"),
                                  ("not_evaluable", "not_evaluable_count")):
        esperado[("opportunities", comportamiento, "measured")] = fila(ahorro[clave], unit="recuento")
    esperado[("potential_savings", "all", "measured")] = fila(ahorro["potential_minor"], unit=moneda)
    esperado[("potential_savings_percent", "all", "measured")] = fila(
        ahorro["potential_percent"], ahorro["potential_minor"], elegible, "porcentaje")
    # El ahorro realizado es `null` en el informe por diseño: debe verse NO MEDIDO (NULL), nunca un 0.
    realizado = ahorro["realized_minor"]
    if realizado is None:
        esperado[("realized_savings", "all", "not_measured")] = fila(unit=moneda)
    else:
        esperado[("realized_savings", "all", "measured")] = fila(realizado, unit=moneda)
    return esperado


# --- Comparaciones --------------------------------------------------------------------------------------------------


def numero_igual(obtenido, esperado) -> bool:
    """Igualdad numérica con tolerancia de FORMATO y sin confundir NULL con 0 (`None` solo es igual a `None`)."""
    if obtenido is None or esperado is None:
        return obtenido is None and esperado is None
    return math.isclose(obtenido, esperado, rel_tol=TOLERANCIA_FORMATO, abs_tol=0.0)


def redondeo(valor, decimales: str) -> str:
    """Redondeo de «mitad hacia arriba» sobre la forma decimal más corta del número (el que muestra PostgreSQL)."""
    return str(Decimal(repr(float(valor))).quantize(Decimal(decimales), rounding=ROUND_HALF_UP))


def texto_visible(unidad: str, valor, conteo=None, minutos: bool = False):
    """Texto de la columna `valor_texto` que el panel enseña, calculado aquí a partir del valor ORIGINAL.

    `None` es «No medido» (la celda llega vacía y Grafana escribe «No medido»). Los formatos son los del dashboard:
    tasa y porcentaje con un decimal y `%`, milisegundos con un decimal (o minutos en la tabla de negocio), similitud con
    tres decimales, recuentos enteros e importes en céntimos mostrados en euros con dos decimales.
    """
    if conteo is not None:
        return str(conteo)
    if valor is None:
        return None
    if unidad == "tasa":
        return f"{redondeo(valor * 100, '0.1')} %"
    if unidad == "porcentaje":
        return f"{redondeo(valor, '0.1')} %"
    if unidad == "ms":
        return f"{redondeo(valor / 60000, '0.1')} min" if minutos else f"{redondeo(valor, '0.1')} ms"
    if unidad == "similitud":
        return redondeo(valor, "0.001")
    if unidad in ("recuento", "parejas"):
        return str(int(valor))
    if unidad == "eur_minor_2":
        return f"{redondeo(valor / 100, '0.01')} €"
    raise AssertionError(f"unidad sin formato conocido en la prueba: {unidad}")


class ConciliacionCase(unittest.TestCase):
    """Utilidades de comparación fila a fila con mensajes que dicen QUÉ fila y QUÉ columna difieren."""

    def comparar_filas(self, obtenidas: dict, esperadas: dict, columnas: tuple, etiqueta: str) -> None:
        """Mismas claves en los dos lados y, por clave, las `columnas` numéricas iguales (NULL solo con NULL)."""
        self.assertEqual(sorted(obtenidas), sorted(esperadas), f"{etiqueta}: las filas no son las mismas")
        for clave, esperada in esperadas.items():
            for columna in columnas:
                with self.subTest(informe=etiqueta, fila=clave, columna=columna):
                    self.assertTrue(
                        numero_igual(obtenidas[clave][columna], esperada[columna]),
                        f"{etiqueta} {clave} {columna}: dashboard={obtenidas[clave][columna]!r} informe={esperada[columna]!r}")


def ejecuciones() -> list:
    """Ejecuciones cargadas, leídas con el rol de Grafana."""
    return con_el_rol("SELECT run_id, source, run_at, commit_sha, milestone FROM evaluation.runs ORDER BY run_id")


def run_de(fuente: str, run_at: str | None = None, run_id: str | None = None) -> str:
    """Identificador de la ejecución cargada que corresponde a un informe, hallada por sus datos propios (no por el adaptador)."""
    candidatas = [e for e in ejecuciones() if e["source"] == fuente]
    if run_at is not None:
        candidatas = [e for e in candidatas if e["run_at"] is not None and instante(e["run_at"]) == instante(run_at)]
    if run_id is not None:
        candidatas = [e for e in candidatas if e["run_id"] == run_id]
    assert len(candidatas) == 1, f"no hay una única ejecución {fuente} {run_at or run_id}: {candidatas}"
    return candidatas[0]["run_id"]


# --- Que ningún informe desaparezca y que el total sea el que se deduce de ellos ----------------------------------------


class InformesPresentesTests(ConciliacionCase):
    def test_las_doce_ejecuciones_estan_cargadas_y_cada_una_corresponde_a_su_informe(self):
        # «Que ningún informe desaparezca»: dos campañas de JUP-070 (halladas por su fecha y su commit originales), el
        # benchmark, la calibración (por su `generated_at`) y la ejecución de negocio (por su `run_id` propio).
        cargadas = ejecuciones()
        self.assertEqual(len(cargadas), 12, [e["run_id"] for e in cargadas])
        self.assertEqual(sorted(e["source"] for e in cargadas), [
            "JUP-022", "JUP-068", "JUP-070", "JUP-070", "JUP-070", "JUP-071", "JUP-071", "JUP-078", "JUP-130-ai-cost", "JUP-130-ai-cost", "JUP-130-anomalies", "JUP-130-data"])
        for clave in JUP070:
            informe = leer(clave)
            run_id = run_de("JUP-070", run_at=informe["run"]["date"])
            commit = next(e["commit_sha"] for e in cargadas if e["run_id"] == run_id)
            self.assertEqual(commit, informe["run"]["commit"], clave)
        run_de("JUP-078")
        run_de("JUP-022", run_at=leer("jup022")["generated_at"])
        run_de("JUP-068", run_id=informe_de_negocio()["run_id"])
        for clave in JUP130:
            run_de(leer(clave)["run"]["source"], run_id=leer(clave)["run"]["run_id"])

    def test_la_tabla_de_ejecuciones_del_dashboard_las_lista_con_su_fecha_y_commit_originales(self):
        # El panel a1 es lo primero que ve quien abre el dashboard: no puede perder una ejecución ni inventar su fecha.
        filas = {f["run_id"]: f for f in del_panel("a1")}
        for clave in JUP070:
            informe = leer(clave)
            run_id = run_de("JUP-070", run_at=informe["run"]["date"])
            self.assertIn(run_id, filas, f"la tabla de ejecuciones no lista la campaña {clave}")
            fila_panel = filas[run_id]
            self.assertEqual(instante(fila_panel["run_at"]), instante(informe["run"]["date"]), clave)
            self.assertEqual(fila_panel["commit_sha"], informe["run"]["commit"], clave)
            self.assertEqual(fila_panel["suite_version"], informe["run"]["suite_version"], clave)
        run_calibracion = run_de("JUP-022", run_at=leer("jup022")["generated_at"])
        self.assertIn(run_calibracion, filas, "la tabla de ejecuciones no lista la calibración de JUP-022")
        calibracion = filas[run_calibracion]
        self.assertEqual(instante(calibracion["run_at"]), instante(leer("jup022")["generated_at"]))
        # JUP-078 no trae fecha: la tabla no se la inventa.
        self.assertIn(run_de("JUP-078"), filas, "la tabla de ejecuciones no lista el benchmark de JUP-078")
        self.assertIsNone(filas[run_de("JUP-078")]["run_at"])
        # La sección A lista sus cuatro ejecuciones; la de negocio puede estar o no.
        self.assertGreaterEqual(len(filas), 4)

    def test_el_total_de_resultados_es_la_suma_que_se_deduce_de_los_informes(self):
        esperado = (
            sum(len(esperado_jup070(leer(clave))) for clave in JUP070)
            + 5 * len(leer("jup078")["models"]) + 5 * len(leer("jup022")["points"])
            + len(esperado_jup068(informe_de_negocio()))
            + sum(len(leer(clave)["results"]) for clave in JUP130))
        # El número no se acepta «porque sí»: 96 + 10 + 140 + 23 + 16 + 10 + 13 + 136.
        self.assertEqual(esperado, TOTAL_ESPERADO)
        self.assertEqual(TOTAL_ESPERADO, 647)
        filas = con_el_rol("SELECT count(*) AS n FROM evaluation.results")
        self.assertEqual(filas[0]["n"], TOTAL_ESPERADO)
        por_ejecucion = {f["run_id"]: f["n"] for f in con_el_rol(
            "SELECT run_id, count(*) AS n FROM evaluation.results GROUP BY run_id")}
        self.assertEqual(sorted(por_ejecucion.values()), sorted([*FILAS_DE.values(), FILAS_JUP078, FILAS_JUP022, FILAS_JUP068, *FILAS_JUP130]))

    def test_ninguna_fila_medida_es_nula_ni_ninguna_no_medida_lleva_valor(self):
        # Regla 1 del contrato comprobada sobre los datos reales cargados: lo no medido es NULL y lo medido tiene valor.
        mal = con_el_rol(
            "SELECT run_id, grp, metric_id, behavior, status FROM evaluation.results "
            "WHERE (status = 'measured' AND value IS NULL) "
            "OR (status = 'not_measured' AND (value IS NOT NULL OR numerator IS NOT NULL OR case_count IS NOT NULL "
            "OR ci_low IS NOT NULL OR ci_high IS NOT NULL))")
        self.assertEqual(mal, [])

    def test_el_reparto_por_estado_coincide_con_el_de_los_informes(self):
        # Guarda anti-vacío del punto anterior: hay filas de cada estado y en la cantidad que dicen los informes. La única
        # fila no medida es el ahorro realizado de JUP-068 (el informe lo deja en `null`).
        esperado = {}
        for informe in (*(esperado_jup070(leer(clave)) for clave in JUP070), esperado_jup068(informe_de_negocio())):
            for (_, _, estado) in informe:
                esperado[estado] = esperado.get(estado, 0) + 1
        for modelo in leer("jup078")["models"]:
            esperado["pass"] = esperado.get("pass", 0) + 1
            esperado["fail"] = esperado.get("fail", 0) + 1
            medidas = 3 if modelo["successful"] > 0 else 0
            esperado["measured"] = esperado.get("measured", 0) + medidas
            esperado["not_measured"] = esperado.get("not_measured", 0) + 3 - medidas
        esperado["measured"] += 5 * len(leer("jup022")["points"])
        for clave in JUP130:
            for fila in leer(clave)["results"]:
                esperado[fila["status"]] = esperado.get(fila["status"], 0) + 1
        obtenido = {f["status"]: f["n"] for f in con_el_rol(
            "SELECT status, count(*) AS n FROM evaluation.results GROUP BY status")}
        self.assertEqual(obtenido, esperado)
        self.assertEqual(obtenido["not_measured"], 1 + sum(
            1 for clave in JUP130 for fila in leer(clave)["results"] if fila["status"] == "not_measured"))
        self.assertEqual(sum(obtenido.values()), TOTAL_ESPERADO)


# --- (a) JUP-070 ---------------------------------------------------------------------------------------------------


class Jup070Tests(ConciliacionCase):
    def test_los_recuentos_de_estado_de_cada_ejecucion_son_los_counts_del_informe(self):
        filas = {f["run_id"]: f for f in del_panel("a2")}
        self.assertEqual(len(filas), 3, "el panel de estados lista una fila por ejecución de JUP-070")
        for clave in JUP070:
            informe = leer(clave)
            contadores = informe["counts"]
            # Precondición del propio informe: los cuatro estados suman el total de casos.
            self.assertEqual(sum(contadores[e] for e in ESTADOS_DE_CASO), contadores["cases"], clave)
            fila_panel = filas[run_de("JUP-070", run_at=informe["run"]["date"])]
            with self.subTest(informe=clave):
                self.assertEqual(
                    (fila_panel["pass"], fila_panel["fail"], fila_panel["blocked"], fila_panel["not_run"],
                     fila_panel["denominator"]),
                    (contadores["pass"], contadores["fail"], contadores["blocked"], contadores["not_run"],
                     contadores["cases"]))

    def _filas_de_campana(self, clave: str) -> dict:
        """Filas de los paneles de calidad (a3) y de campaña (a4) de una ejecución, por `(metric_id, behavior, status)`."""
        run_id = run_de("JUP-070", run_at=leer(clave)["run"]["date"])
        obtenidas = {}
        for panel in ("a3", "a4"):
            for f in del_panel(panel):
                if f["run_id"] == run_id:
                    clave_fila = (f["metric_id"], f["behavior"], f["status"])
                    self.assertNotIn(clave_fila, obtenidas, f"fila repetida en los paneles: {clave_fila}")
                    obtenidas[clave_fila] = f
        return obtenidas

    def test_cada_metrica_de_calidad_y_de_campana_coincide_con_el_informe(self):
        for clave in JUP070:
            esperado = esperado_jup070(leer(clave))
            # Los 4 estados de casos van en el panel de estados; las otras 44 filas, en las dos tablas de resultados.
            sin_casos = {k: v for k, v in esperado.items() if k[0] != "cases"}
            self.assertEqual(len(esperado), FILAS_DE[clave], clave)
            self.assertEqual(len(sin_casos), FILAS_DE[clave] - 4, clave)
            obtenidas = self._filas_de_campana(clave)
            self.comparar_filas(obtenidas, sin_casos, ("value", "numerator", "denominator"), clave)

    def test_los_numeradores_denominadores_y_tasas_de_las_proporciones_son_los_k_n_rate_del_informe(self):
        # Foco en las proporciones (ACC-1/2/3, REL-1/2/3, GRD-1/3, STR-1, LAT-4 por etapa, AVL-1): `k`, `n` y `rate`.
        for clave in JUP070:
            informe = leer(clave)
            obtenidas = self._filas_de_campana(clave)
            metricas = informe["metrics"]
            propias = {
                ("ACC-1", "all"): metricas["ACC-1"], ("ACC-2", "all"): metricas["ACC-2"],
                ("ACC-2", "judged"): metricas["ACC-2"]["judged"], ("REL-1", "all"): metricas["REL-1"],
                ("REL-2", "all"): metricas["REL-2"], ("GRD-1", "all"): metricas["GRD-1"],
                ("GRD-3", "all"): metricas["GRD-3"], ("STR-1", "all"): metricas["STR-1"],
                ("AVL-1", "all"): metricas["AVL-1"],
            }
            for metrica in ("ACC-3", "REL-3"):
                for grupo, datos in metricas[metrica]["groups"].items():
                    propias[(metrica, grupo)] = datos
            for etapa, datos in metricas["LAT-4"]["stages"].items():
                propias[("LAT-4", etapa)] = datos
            self.assertEqual(len(propias), 9 + 2 + 3 + 3, "faltan proporciones en el oráculo")
            for (metrica, comportamiento), datos in propias.items():
                with self.subTest(informe=clave, metrica=metrica, behavior=comportamiento):
                    obtenida = obtenidas[(metrica, comportamiento, "measured")]
                    self.assertEqual(obtenida["numerator"], datos["k"])
                    self.assertEqual(obtenida["denominator"], datos["n"])
                    self.assertTrue(numero_igual(obtenida["value"], datos["rate"]), (obtenida["value"], datos["rate"]))
                    # Coherencia interna del informe: la tasa es k/n (una conciliación con un informe roto no probaría nada).
                    self.assertAlmostEqual(datos["k"] / datos["n"], datos["rate"], places=5)

    def test_latencias_similitudes_y_recuentos_de_formato_coinciden_con_el_informe(self):
        for clave in JUP070:
            informe = leer(clave)["metrics"]
            obtenidas = self._filas_de_campana(clave)
            with self.subTest(informe=clave):
                for metrica in ("LAT-1", "LAT-2", "LAT-3"):
                    for etapa, datos in informe[metrica]["stages"].items():
                        obtenida = obtenidas[(metrica, etapa, "measured")]
                        self.assertTrue(numero_igual(obtenida["value"], datos["value"]), (metrica, etapa))
                        self.assertEqual(obtenida["denominator"], datos["n"], (metrica, etapa))
                        self.assertEqual(obtenida["unit"], "ms")
                for estadistico in ("median", "q1", "q3"):
                    obtenida = obtenidas[("REL-4", estadistico, "measured")]
                    self.assertTrue(numero_igual(obtenida["value"], informe["REL-4"][estadistico]), estadistico)
                    self.assertEqual(obtenida["denominator"], informe["REL-4"]["n"], estadistico)
                self.assertTrue(numero_igual(obtenidas[("GRD-2", "all", "measured")]["value"], informe["GRD-2"]["total"]))
                for categoria, total in informe["STR-2"]["by_category"].items():
                    self.assertTrue(numero_igual(obtenidas[("STR-2", categoria, "measured")]["value"], total), categoria)
                self.assertTrue(numero_igual(obtenidas[("STR-2", "all", "measured")]["value"], informe["STR-2"]["total"]))

    def test_las_dos_campanas_se_distinguen_por_sus_valores(self):
        # Guarda anti-confusión: si la carga o un filtro mezclara las dos ejecuciones (o repitiera una), las dos
        # conciliaciones anteriores podrían pasar con la misma fila vista dos veces. Los informes difieren de verdad.
        uno, dos = leer("jup070-1")["metrics"], leer("jup070-2")["metrics"]
        self.assertNotEqual(uno["ACC-2"]["k"], dos["ACC-2"]["k"])
        a = self._filas_de_campana("jup070-1")[("ACC-2", "all", "measured")]
        b = self._filas_de_campana("jup070-2")[("ACC-2", "all", "measured")]
        self.assertEqual((a["numerator"], b["numerator"]), (uno["ACC-2"]["k"], dos["ACC-2"]["k"]))
        self.assertNotEqual(a["run_id"], b["run_id"])


# --- (b) JUP-078 ---------------------------------------------------------------------------------------------------


class Jup078Tests(ConciliacionCase):
    def test_cada_modelo_coincide_con_models_del_informe(self):
        informe = leer("jup078")
        esperado = esperado_jup078(informe)
        self.assertEqual(len(esperado), 2)
        run_id = run_de("JUP-078")
        filas = {f["behavior"]: f for f in del_panel("a8") if f["run_id"] == run_id}
        self.assertEqual(sorted(filas), sorted(esperado))
        for alias, datos in esperado.items():
            for columna, valor in datos.items():
                with self.subTest(modelo=alias, columna=columna):
                    if columna in ("successful", "cases"):
                        self.assertEqual(filas[alias][columna], valor)
                    else:
                        self.assertTrue(numero_igual(filas[alias][columna], valor), (filas[alias][columna], valor))

    def test_el_benchmark_tiene_las_cinco_filas_por_modelo_en_la_base(self):
        # El panel pivota las filas del modelo: aquí se cuentan las filas de la base de la ejecución del benchmark.
        run_id = run_de("JUP-078")
        filas = con_el_rol(f"SELECT metric_id, behavior, status FROM evaluation.results WHERE run_id = '{run_id}'")
        modelos = leer("jup078")["models"]
        self.assertEqual(len(filas), 5 * len(modelos))
        self.assertEqual(sorted({f["behavior"] for f in filas}), sorted(m["alias"] for m in modelos))


# --- (c) JUP-022 ---------------------------------------------------------------------------------------------------


class Jup022Tests(ConciliacionCase):
    def test_los_28_puntos_por_5_tasas_con_sus_denominadores_coinciden_con_points(self):
        informe = leer("jup022")
        esperado = esperado_jup022(informe)
        self.assertEqual(len(informe["points"]), 28)
        self.assertEqual(len(esperado), FILAS_JUP022)
        run_id = run_de("JUP-022", run_at=informe["generated_at"])
        obtenidas = {(f["metric_id"], f["behavior"]): f for f in del_panel("a7") if f["run_id"] == run_id}
        self.comparar_filas(obtenidas, esperado, ("value", "numerator", "denominator"), "JUP-022")

    def test_exactamente_20_filas_selected_son_las_de_los_candidatos_de_selection(self):
        informe = leer("jup022")
        esperado = esperado_jup022(informe)
        marcadas_esperadas = {clave for clave, datos in esperado.items() if datos["selected"]}
        self.assertEqual(len(informe["selection"]["candidates"]), 4)
        self.assertEqual(len(marcadas_esperadas), 20)
        run_id = run_de("JUP-022", run_at=informe["generated_at"])
        filas = [f for f in del_panel("a7") if f["run_id"] == run_id]
        marcadas = {(f["metric_id"], f["behavior"]) for f in filas if f["selected"] is True}
        self.assertEqual(len(marcadas), 20)
        self.assertEqual(marcadas, marcadas_esperadas)
        # El resto no está marcado: `selected` es booleano en todas las filas y falso en las demás.
        self.assertTrue(all(isinstance(f["selected"], bool) for f in filas))
        self.assertEqual(sum(1 for f in filas if not f["selected"]), FILAS_JUP022 - 20)


# --- (d) JUP-068 ---------------------------------------------------------------------------------------------------


class Jup068Tests(ConciliacionCase):
    def _filas(self) -> dict:
        informe = informe_de_negocio()
        run_id = run_de("JUP-068", run_id=informe["run_id"])
        obtenidas = {}
        for f in de_los_paneles_de_negocio():
            if f["run_id"] == run_id:
                clave = (f["metric_id"], f["behavior"], f["status"])
                self.assertNotIn(clave, obtenidas, f"fila repetida en la tabla de negocio: {clave}")
                obtenidas[clave] = f
        return obtenidas

    def test_la_tabla_de_negocio_coincide_con_el_informe_de_negocio(self):
        esperado = esperado_jup068(informe_de_negocio())
        self.assertEqual(len(esperado), FILAS_JUP068)
        self.comparar_filas(self._filas(), esperado, ("value", "numerator", "denominator"), "JUP-068")

    def test_time_trials_tiene_los_cuatro_estados_con_su_total(self):
        informe = informe_de_negocio()["time"]
        obtenidas = self._filas()
        total = sum(informe["results"][e] for e in ESTADOS_DE_CASO)
        for estado in ESTADOS_DE_CASO:
            with self.subTest(estado=estado):
                fila_panel = obtenidas[("time_trials", "all", estado)]
                # La tabla enseña el recuento en la columna de texto; el total es el denominador.
                self.assertEqual(fila_panel["valor_texto"], str(informe["results"][estado]))
                self.assertEqual(fila_panel["denominator"], total)
                self.assertIsNone(fila_panel["value"], "un recuento de parejas no es un valor medido")

    def test_tiempo_manual_asistido_y_ahorrado_con_su_porcentaje(self):
        tiempo = informe_de_negocio()["time"]
        obtenidas = self._filas()
        for metrica, clave in (("manual_time", "manual_ms"), ("assisted_time", "assisted_ms"), ("time_saved", "saved_ms")):
            with self.subTest(metrica=metrica):
                self.assertTrue(numero_igual(obtenidas[(metrica, "all", "measured")]["value"], tiempo[clave]))
                self.assertEqual(obtenidas[(metrica, "all", "measured")]["denominator"], tiempo["eligible_pairs"])
        porcentaje = obtenidas[("time_saved_percent", "all", "measured")]
        self.assertTrue(numero_igual(porcentaje["value"], tiempo["saved_percent"]))
        self.assertEqual((porcentaje["numerator"], porcentaje["denominator"]), (tiempo["saved_ms"], tiempo["manual_ms"]))

    def test_importes_y_porcentajes_de_asignacion(self):
        asignacion = informe_de_negocio()["allocation"]
        obtenidas = self._filas()
        for metrica, clave in (("allocated", "allocated"), ("shared", "shared"), ("unallocated", "unallocated"),
                               ("excluded", "excluded"), ("total", "total_minor"), ("eligible", "eligible_minor")):
            with self.subTest(importe=metrica):
                self.assertTrue(numero_igual(obtenidas[(metrica, "all", "measured")]["value"], asignacion[clave]))
        for metrica, numerador in (("assigned_percent", asignacion["allocated"]),
                                   ("governed_percent", asignacion["allocated"] + asignacion["shared"]),
                                   ("unallocated_percent", asignacion["unallocated"])):
            with self.subTest(porcentaje=metrica):
                fila_panel = obtenidas[(metrica, "all", "measured")]
                self.assertTrue(numero_igual(fila_panel["value"], asignacion[metrica]))
                self.assertEqual((fila_panel["numerator"], fila_panel["denominator"]), (numerador, asignacion["eligible_minor"]))

    def test_oportunidades_y_ahorro_potencial_coinciden_y_el_realizado_es_nulo(self):
        ahorro = informe_de_negocio()["savings"]
        obtenidas = self._filas()
        for comportamiento, clave in (("estimated", "estimated_count"), ("candidate", "candidate_count"),
                                      ("not_evaluable", "not_evaluable_count")):
            with self.subTest(oportunidades=comportamiento):
                self.assertTrue(numero_igual(obtenidas[("opportunities", comportamiento, "measured")]["value"], ahorro[clave]))
        self.assertTrue(numero_igual(obtenidas[("potential_savings", "all", "measured")]["value"], ahorro["potential_minor"]))
        porcentaje = obtenidas[("potential_savings_percent", "all", "measured")]
        self.assertTrue(numero_igual(porcentaje["value"], ahorro["potential_percent"]))
        self.assertEqual(porcentaje["numerator"], ahorro["potential_minor"])
        # El informe deja el ahorro realizado en `null` por diseño: NO MEDIDO. Ni un 0 ni un valor de relleno.
        self.assertIsNone(ahorro["realized_minor"])
        realizado = obtenidas[("realized_savings", "all", "not_measured")]
        self.assertIsNone(realizado["value"])
        self.assertIsNone(realizado["numerator"])
        self.assertIsNone(realizado["valor_texto"])
        self.assertNotIn(("realized_savings", "all", "measured"), obtenidas)


# --- Lo que se ve: el texto de cada celda y la cobertura de los paneles -----------------------------------------------


class LoQueSeVeTests(ConciliacionCase):
    def test_el_texto_visible_de_las_tablas_de_calidad_y_campana_se_calcula_del_valor_original(self):
        # `valor_texto` es lo que lee una persona. Se recalcula del valor del informe original con el formato documentado:
        # un porcentaje sin multiplicar por 100, una unidad equivocada o un cero de relleno dejarían de coincidir.
        for clave in JUP070:
            esperado = esperado_jup070(leer(clave))
            run_id = run_de("JUP-070", run_at=leer(clave)["run"]["date"])
            comprobadas = 0
            for panel in ("a3", "a4"):
                for f in del_panel(panel):
                    if f["run_id"] != run_id:
                        continue
                    origen = esperado[(f["metric_id"], f["behavior"], f["status"])]
                    with self.subTest(informe=clave, fila=(f["metric_id"], f["behavior"])):
                        self.assertEqual(f["valor_texto"], texto_visible(origen["unit"], origen["value"]))
                    comprobadas += 1
            self.assertEqual(comprobadas, FILAS_DE[clave] - 4)

    def test_el_texto_visible_de_la_tabla_de_negocio_se_calcula_del_valor_original(self):
        esperado = esperado_jup068(informe_de_negocio())
        run_id = run_de("JUP-068", run_id=informe_de_negocio()["run_id"])
        filas = [f for f in de_los_paneles_de_negocio() if f["run_id"] == run_id]
        self.assertEqual(len(filas), FILAS_JUP068)
        for f in filas:
            origen = esperado[(f["metric_id"], f["behavior"], f["status"])]
            with self.subTest(fila=(f["metric_id"], f["behavior"], f["status"])):
                self.assertEqual(f["valor_texto"], texto_visible(origen["unit"], origen["value"], origen["count"], minutos=True))

    def test_los_paneles_juntos_muestran_cada_una_de_las_647_filas_de_la_base(self):
        # Cobertura: si una consulta de panel perdiera filas (un filtro de más, un grupo que falta) la suma no llegaría a 647.
        # Estados de casos (4 filas de la base por fila del panel) y benchmark (5 por modelo) vienen pivotados.
        visibles = (
            4 * len(del_panel("a2")) + len(del_panel("a3")) + len(del_panel("a4")) + len(del_panel("a7"))
            + 5 * len(del_panel("a8")) + len(de_los_paneles_de_negocio())
            + len(del_panel("a_anomalias")) + len(filas_de_los_indicadores()) + len(del_panel("a9")))
        self.assertEqual(visibles, TOTAL_ESPERADO)
        self.assertEqual(con_el_rol("SELECT count(*) AS n FROM evaluation.results")[0]["n"], visibles)


if __name__ == "__main__":
    unittest.main()
