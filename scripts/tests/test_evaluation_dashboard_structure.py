"""Estructura estática del dashboard de evaluación del asistente (JUP-121, tarea 4.2, Red).

La tarea 4.3 crea `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (Grafana 11.3.0, provisionado desde
ficheros). Este módulo fija su contrato SIN base de datos y SIN cargar la herramienta: lee el JSON con la biblioteca
estándar y comprueba forma, secciones, descripciones, datasources, consultas y anotaciones. El comportamiento de las
consultas SQL contra un PostgreSQL real vive en `test_evaluation_dashboard_queries.py`, que reutiliza de aquí el
localizador de paneles (`buscar`) para que las dos pruebas hablen de los mismos paneles.

Ruta: por defecto el fichero real; `EVALUATION_DASHBOARD_JSON` permite apuntar a una copia (sirve para comprobar que
los esperados son alcanzables y que cada mutación se detecta).

Contrato que se valida (resumen; el detalle está en cada test):

* Cabecera: uid, título, schemaVersion 39, version 1, zona `browser`, sin refresco, rango `now-1y`..`now`, etiquetas,
  no editable, enlace al dashboard técnico, sin variables, `id` nulo. Formato: UTF-8, LF, sangría de 2 espacios,
  salto de línea final, sin claves repetidas.
* Paneles: ids enteros únicos y `gridPos` válido, sin solapes y en orden de lectura.
* Tres filas (`A · `, `B · `, `C · `, sin plegar) y cada panel pertenece a la sección de la última fila anterior.
* Todo panel que no es fila lleva `description` con tres líneas: `Tipo: X`, `Mide: ...`, `No demuestra: ...`, y su
  «No demuestra» nombra la limitación propia de la sección (A: usuarios reales o preguntas fuera de la batería; B:
  piloto; C: acierto o corrección).
* Datasources: A y B solo PostgreSQL (`evaluation-postgres`), C solo Prometheus; ningún panel mezcla los dos.
* Sección A: diez piezas identificadas por lo que consultan (`a0`..`a9`, ver `CLASIFICADORES`). Sección B: texto y tabla
  de negocio. Sección C: texto y las cinco señales en vivo con las expresiones de `technical-metrics.json` y las
  guardas `> 0`.
* Lo no medido: todo panel de valor de A y B muestra «No medido» para un NULL y ninguna consulta inventa un 0.
* Ejecuciones no reales: override `.*no real.*` con estilo propio en los paneles de evolución.
* Anotación de cambios de configuración con `array_to_string(changes, ',') AS tags`.
* Consultas: solo lectura, solo el esquema `evaluation`, `rawQuery`/`editorMode`/`format`/`refId` correctos y sin
  columnas que puedan llevar texto de preguntas o respuestas.
* Sin secretos.

Decisiones donde el enunciado admitía más de una lectura (fijadas aquí; el coder debe respetarlas):

* La robustez de JUP-071 (a9) se identifica por `source = 'JUP-071'` (no por `grp = 'robustness'`): ese grupo ya
  lo usan las filas STR de JUP-070 en la campaña (a4) y el panel de robustez debe quedar vacío con los datos reales.
* Los paneles de evolución (a5 y a6) llevan cada uno el override `no real`, no basta con uno en el dashboard.
* `spanNulls: false` en los dos paneles de evolución (D6 del diseño: ningún hueco se une con una línea ni se rellena).
* Todo panel `table`/`stat`/`gauge` de A y B cuya consulta usa `value` define `noValue` «No medido» o un mapeo de
  `null` a «No medido». El panel de robustez (a9) tiene su propio `noValue` «Sin datos...» y por tanto necesita el mapeo.
* `format` de cada target SQL: `time_series` en los `timeseries` y `table` en el resto.
* Dentro de una consulta, el único `COALESCE` prohibido es el que termina en un literal `0`; `IFNULL`, `NVL` y
  `NULLIF(..., 0)` se prohíben siempre (ocultan un nulo o un cero medido).
"""

import json
import os
import re
import unittest
from pathlib import Path

# Raíz del repositorio deducida de este fichero (scripts/tests/ -> raíz).
REPO_ROOT = Path(__file__).resolve().parents[2]
GRAFANA_DIR = REPO_ROOT / "apps" / "monitoring" / "grafana"
DASHBOARD = Path(os.environ.get("EVALUATION_DASHBOARD_JSON") or GRAFANA_DIR / "dashboards" / "assistant-evaluation.json")
TECHNICAL_DASHBOARD = GRAFANA_DIR / "dashboards" / "technical-metrics.json"

UID = "economicon-assistant-evaluation"
TITLE = "Economicon — Evaluación del asistente"
NO_COMPARABLE = "Sin datos: no hay con qué comparar"
NO_MEDIDO = "No medido"

DS_POSTGRES = {"type": "grafana-postgresql-datasource", "uid": "evaluation-postgres"}
DS_PROMETHEUS = {"type": "prometheus", "uid": "prometheus"}
DATASOURCE_POR_SECCION = {"A": DS_POSTGRES, "B": DS_POSTGRES, "C": DS_PROMETHEUS}

# Texto que cada sección debe nombrar en su línea «No demuestra».
LIMITACION_POR_SECCION = {
    "A": re.compile(r"usuarios reales|fuera de la bater", re.IGNORECASE),
    "B": re.compile(r"piloto", re.IGNORECASE),
    "C": re.compile(r"acierto|correct", re.IGNORECASE),
}

TABLAS_PERMITIDAS = {"evaluation.runs", "evaluation.results", "evaluation.config_changes", "evaluation.comparable_runs"}
PALABRAS_PROHIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|CALL|VACUUM|REINDEX|ANALYZE|REFRESH|INTO)\b",
    re.IGNORECASE,
)
# Identificadores que podrían contener el texto de una pregunta o de una respuesta (fuera de comillas).
COLUMNAS_DE_TEXTO = re.compile(r"(?<![\w'])(question|answer|prompt|response)s?(?![\w'])", re.IGNORECASE)
SECRETOS = re.compile(r"password|token|secret|api[_-]?key|bearer", re.IGNORECASE)


# --- Lectura del JSON -------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _sin_duplicados(pares):
    """Un objeto JSON con la misma clave dos veces se rechaza: `json.loads` se quedaría con la última en silencio."""
    claves = [clave for clave, _ in pares]
    repetidas = sorted({clave for clave in claves if claves.count(clave) > 1})
    if repetidas:
        raise AssertionError(f"claves JSON repetidas en el mismo objeto: {repetidas}")
    return dict(pares)


def crudo() -> bytes:
    """Bytes del dashboard; si no existe falla con una aserción legible (Red claro, no un error de E/S)."""
    if not DASHBOARD.is_file():
        raise AssertionError(f"no existe el dashboard esperado: {DASHBOARD}")
    if "crudo" not in _CACHE:
        _CACHE["crudo"] = DASHBOARD.read_bytes()
    return _CACHE["crudo"]


def dashboard() -> dict:
    if "dashboard" not in _CACHE:
        _CACHE["dashboard"] = json.loads(crudo().decode("utf-8"), object_pairs_hook=_sin_duplicados)
    return _CACHE["dashboard"]


def paneles() -> list:
    lista = dashboard().get("panels")
    if not isinstance(lista, list) or not lista:
        raise AssertionError("`panels` debe ser una lista no vacía")
    return lista


def filas() -> list:
    return [p for p in paneles() if p.get("type") == "row"]


def _y(panel) -> int:
    return panel["gridPos"]["y"]


def seccion_de(panel) -> str:
    """Letra de la sección: la de la última fila anterior por `gridPos.y` (las filas no están plegadas)."""
    anteriores = [f for f in filas() if _y(f) < _y(panel)]
    if not anteriores:
        raise AssertionError(f"el panel {panel.get('title')!r} no está debajo de ninguna fila")
    return max(anteriores, key=_y)["title"][:1]


def contenido() -> list:
    """Paneles que no son fila, con su sección: lista de `(letra, panel)`."""
    return [(seccion_de(p), p) for p in paneles() if p.get("type") != "row"]


def de_seccion(letra) -> list:
    return [p for s, p in contenido() if s == letra]


def sql_de(panel) -> str:
    return "\n".join(t.get("rawSql", "") for t in panel.get("targets", []))


def _plano(texto) -> str:
    return re.sub(r"\s+", " ", texto)


def expresiones(panel) -> list:
    return [t.get("expr", "") for t in panel.get("targets", [])]


def todas_las_consultas() -> list:
    """`(etiqueta, objetivo, panel o None)` de cada target SQL de los paneles y de la anotación (sin `datasource`)."""
    resultado = []
    for letra, panel in contenido():
        for indice, objetivo in enumerate(panel.get("targets", [])):
            if "rawSql" in objetivo:
                resultado.append((f"{letra}/{panel.get('title')}/target {indice}", objetivo, panel))
    for entrada in anotaciones_propias():
        resultado.append((f"anotación {entrada.get('name')!r}", entrada.get("target", {}), None))
    return resultado


def anotaciones_propias() -> list:
    lista = dashboard().get("annotations", {}).get("list", [])
    return [a for a in lista if not a.get("builtIn")]


# --- Clasificador de paneles de la sección A -------------------------------------------------------------------------


def _nombra(sql, *nombres) -> bool:
    return all(re.search(rf"'{n}'", sql) for n in nombres)


def clasificar(panel):
    """Clave `a1`..`a9` (o de lectura: `a_matriz`, `a_resumen`, `a_evolucion_latencia`) del panel de la sección A según
    lo que consulta, o `None` (el texto es `a0` aparte).

    Las reglas se evalúan en orden y son excluyentes: así un panel solo cuenta para una pieza y un panel de más (o uno
    de menos) se nota. Es la fuente única que usa también `test_evaluation_dashboard_queries.py`.
    """
    sql = _plano(sql_de(panel))
    tipo = panel.get("type")
    # Piezas de lectura de `jup-121-lectura-dashboard`. Van ANTES de las originales porque comparten con ellas lo que
    # las originales miran: la matriz nombra las seis familias entre comillas (como el detalle de latencia, `a4`, y los
    # de calidad, `a3`), el resumen consulta `evaluation.runs` y la evolución de la latencia lee `comparable_runs`
    # como `a5`/`a6`. Se reconocen por lo que las distingue: su transformación, su alias y su familia.
    if tipo == "table" and "groupingToMatrix" in {t.get("id") for t in panel.get("transformations", [])}:
        return "a_matriz"
    if tipo == "table" and re.search(r"(?i)\bAS\s+resumen\b", sql):
        return "a_resumen"
    if tipo == "table" and re.search(r"left\(\s*x\.grp\s*,\s*4\s*\)\s*=\s*'rob_'", sql):
        return "a_indicadores_robustez"
    if (
        tipo == "timeseries"
        and re.search(r"evaluation\.comparable_runs\b", sql)
        and re.search(r"grp\s*=\s*'latency'", sql)
    ):
        return "a_evolucion_latencia"
    if tipo == "timeseries" and re.search(r"evaluation\.comparable_runs\b", sql):
        if re.search(r"judgment\s*=\s*'automatic'", sql):
            return "a5"
        if re.search(r"judgment\s*=\s*'human'", sql):
            return "a6"
        return None
    if tipo != "table":
        return None
    if re.search(r"source\s*=\s*'JUP-071'|source\s+IN\s*\([^)]*'JUP-071'", sql):
        return "a9"
    if re.search(r"grp\s*=\s*'calibration'", sql):
        return "a7"
    if re.search(r"grp\s*=\s*'benchmark'", sql):
        return "a8"
    if _nombra(sql, "latency", "robustness", "availability"):
        return "a4"
    if _nombra(sql, "accuracy", "relevance", "grounding"):
        return "a3"
    if re.search(r"metric_id\s*=\s*'cases'", sql):
        return "a2"
    if re.search(r"evaluation\.runs\b", sql) and not re.search(r"evaluation\.results\b", sql):
        return "a1"
    return None


CLAVES_A = ("a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9")
# Piezas añadidas por `jup-121-lectura-dashboard`: no se mezclan con las nueve originales para que las pruebas que
# recorren `CLAVES_A` sigan midiendo exactamente lo mismo.
CLAVES_LECTURA = ("a_matriz", "a_resumen", "a_evolucion_latencia", "a_indicadores_robustez")


def buscar(clave) -> list:
    """Paneles que cumplen la pieza `clave` (`a0`..`a9`, de lectura, `b_texto`, `b_tabla`) del contrato."""
    if clave == "a0":
        return [p for p in de_seccion("A") if p.get("type") == "text"]
    if clave in CLAVES_A + CLAVES_LECTURA:
        return [p for p in de_seccion("A") if clasificar(p) == clave]
    if clave == "b_texto":
        return [p for p in de_seccion("B") if p.get("type") == "text"]
    if clave == "b_tabla":
        return [
            p
            for p in de_seccion("B")
            if p.get("type") == "table"
            and re.search(r"measure_type\s*=\s*'B'|source\s*=\s*'JUP-068'", _plano(sql_de(p)))
        ]
    raise KeyError(clave)


def _unico(clave) -> dict:
    encontrados = buscar(clave)
    if len(encontrados) != 1:
        raise AssertionError(f"se esperaba exactamente un panel `{clave}` y hay {len(encontrados)}")
    return encontrados[0]


def _hay(clave) -> list:
    encontrados = buscar(clave)
    if not encontrados:
        raise AssertionError(f"falta el panel `{clave}` del contrato")
    return encontrados


def _defaults(panel) -> dict:
    return panel.get("fieldConfig", {}).get("defaults", {})


def muestra_no_medido(panel) -> bool:
    """`noValue` «No medido» o mapeo de `null` a «No medido» en los valores por defecto del panel."""
    por_defecto = _defaults(panel)
    if por_defecto.get("noValue") == NO_MEDIDO:
        return True
    for mapeo in por_defecto.get("mappings", []):
        opciones = mapeo.get("options", {})
        if (
            mapeo.get("type") == "special"
            and opciones.get("match") == "null"
            and opciones.get("result", {}).get("text") == NO_MEDIDO
        ):
            return True
    return False


# --- Formato y cabecera ----------------------------------------------------------------------------------------------


class FormatoTests(unittest.TestCase):
    def test_el_fichero_existe_y_es_json_valido_sin_claves_repetidas(self):
        self.assertIsInstance(dashboard(), dict)

    def test_utf8_sin_bom_lf_sangria_de_dos_espacios_y_un_unico_salto_final(self):
        # Mismo formato que el resto del repositorio: UTF-8 sin BOM (el título lleva raya y tilde), LF, sin
        # tabuladores ni espacios finales, sangría en múltiplos de 2 y exactamente un salto de línea final.
        datos = crudo()
        self.assertFalse(datos.startswith(b"\xef\xbb\xbf"), "BOM")
        texto = datos.decode("utf-8")
        self.assertNotIn("\r", texto)
        self.assertNotIn("\t", texto)
        self.assertTrue(texto.endswith("}\n") and not texto.endswith("\n\n"))
        lineas = texto.split("\n")[:-1]
        self.assertEqual(lineas[0], "{")
        self.assertRegex(lineas[1], r"^  \S")  # el primer nivel va a 2 espacios, no a 4 ni a un tabulador
        for linea in lineas:
            with self.subTest(linea=linea[:60]):
                self.assertEqual(linea, linea.rstrip())
                self.assertEqual((len(linea) - len(linea.lstrip(" "))) % 2, 0)

    def test_los_caracteres_no_ascii_se_escriben_literales_sin_escapes_unicode(self):
        # Mismo estilo que `technical-metrics.json`: la raya y las tildes van tal cual (`ensure_ascii=False`), no como
        # `\u2014`. Un volcado con escapes sería JSON equivalente pero ilegible en la revisión y en los diffs.
        texto = crudo().decode("utf-8")
        self.assertNotRegex(texto, r"\\u[0-9a-fA-F]{4}")
        self.assertIn(TITLE, texto)


class CabeceraTests(unittest.TestCase):
    def test_identidad(self):
        d = dashboard()
        self.assertEqual(d.get("uid"), UID)
        self.assertEqual(d.get("title"), TITLE)

    def test_id_nulo_presente(self):
        # `"id": null` explícito: Grafana asigna el id al provisionar, el fichero no lo fija.
        d = dashboard()
        self.assertIn("id", d)
        self.assertIsNone(d["id"])

    def test_versiones_y_tiempo(self):
        d = dashboard()
        self.assertIs(type(d.get("schemaVersion")), int)
        self.assertEqual(d["schemaVersion"], 39)
        self.assertIs(type(d.get("version")), int)
        self.assertEqual(d["version"], 1)
        self.assertEqual(d.get("timezone"), "utc")  # JUP-121: las ejecuciones se registran en UTC
        # Sin refresco automático: los resultados son históricos, no cambian cada 10 s.
        self.assertEqual(d.get("refresh"), "")
        # Rango amplio: las ejecuciones son de octubre de 2026 y las series no usan `$__timeFilter`.
        self.assertEqual(d.get("time"), {"from": "now-1y", "to": "now"})

    def test_etiquetas(self):
        etiquetas = dashboard().get("tags")
        self.assertIsInstance(etiquetas, list)
        self.assertIn("evaluacion", etiquetas)
        self.assertIn("asistente", etiquetas)
        self.assertEqual(len(etiquetas), len(set(etiquetas)))

    def test_no_editable(self):
        self.assertIs(dashboard().get("editable"), False)

    def test_enlace_al_dashboard_tecnico(self):
        enlaces = dashboard().get("links")
        self.assertIsInstance(enlaces, list)
        urls = [e.get("url", "") for e in enlaces if isinstance(e, dict)]
        self.assertTrue(any("/d/economicon-technical-metrics" in url for url in urls), urls)
        for enlace in enlaces:
            self.assertTrue(enlace.get("title"), enlace)

    def test_sin_variables(self):
        # Sin `templating`: las consultas no dependen de variables de dashboard (ni hay nada que el usuario cambie).
        plantilla = dashboard().get("templating", {"list": []})
        self.assertEqual(plantilla.get("list", []), [])

    def test_el_dashboard_tecnico_sigue_siendo_otro_y_existe(self):
        # El enlace apunta a un uid que existe de verdad.
        tecnico = json.loads(TECHNICAL_DASHBOARD.read_text(encoding="utf-8"))
        self.assertEqual(tecnico["uid"], "economicon-technical-metrics")
        self.assertNotEqual(tecnico["uid"], dashboard().get("uid"))


# --- Paneles y rejilla -----------------------------------------------------------------------------------------------


class PanelesTests(unittest.TestCase):
    def test_ids_enteros_y_unicos(self):
        ids = [p.get("id") for p in paneles()]
        for valor in ids:
            self.assertIs(type(valor), int, valor)  # `bool` no cuenta como entero
        self.assertEqual(len(ids), len(set(ids)), ids)

    def test_todo_panel_tiene_titulo_y_tipo(self):
        for panel in paneles():
            with self.subTest(id=panel.get("id")):
                self.assertTrue(isinstance(panel.get("title"), str) and panel["title"].strip())
                self.assertTrue(isinstance(panel.get("type"), str) and panel["type"])

    def test_gridpos_valido(self):
        for panel in paneles():
            with self.subTest(titulo=panel.get("title")):
                pos = panel.get("gridPos")
                self.assertIsInstance(pos, dict)
                for clave in ("x", "y", "w", "h"):
                    self.assertIs(type(pos.get(clave)), int, f"{clave} debe ser entero")
                self.assertTrue(1 <= pos["w"] <= 24, pos)
                self.assertGreaterEqual(pos["h"], 1)
                self.assertGreaterEqual(pos["x"], 0)
                self.assertGreaterEqual(pos["y"], 0)
                self.assertLessEqual(pos["x"] + pos["w"], 24, pos)

    def test_sin_solapamientos(self):
        # Dos rectángulos se solapan si lo hacen en horizontal y en vertical a la vez.
        lista = paneles()
        for i, a in enumerate(lista):
            for b in lista[i + 1 :]:
                pa, pb = a["gridPos"], b["gridPos"]
                solapan = (
                    pa["x"] < pb["x"] + pb["w"]
                    and pb["x"] < pa["x"] + pa["w"]
                    and pa["y"] < pb["y"] + pb["h"]
                    and pb["y"] < pa["y"] + pa["h"]
                )
                with self.subTest(a=a["title"], b=b["title"]):
                    self.assertFalse(solapan, (pa, pb))

    def test_orden_de_lectura_por_y_y_luego_x(self):
        # El orden de la lista es el de lectura: Grafana recoloca según `gridPos`, pero la revisión del JSON no.
        claves = [(p["gridPos"]["y"], p["gridPos"]["x"]) for p in paneles()]
        self.assertEqual(claves, sorted(claves))
        self.assertEqual(len(claves), len(set(claves)))

    def test_los_paneles_no_declaran_hijos(self):
        # Las filas no están plegadas: ninguna lleva paneles anidados ni la lista oculta nada.
        for fila in filas():
            self.assertEqual(fila.get("panels", []), [], fila["title"])


# --- Secciones -------------------------------------------------------------------------------------------------------


class SeccionesTests(unittest.TestCase):
    def test_exactamente_tres_filas_a_b_c_en_orden_y_desplegadas(self):
        lista = filas()
        self.assertEqual(len(lista), 3, [f["title"] for f in lista])
        self.assertEqual([f["title"][:4] for f in lista], ["A · ", "B · ", "C · "])
        for fila in lista:
            self.assertIs(fila.get("collapsed"), False, fila["title"])
            self.assertTrue(fila["title"][4:].strip(), "la fila debe llevar un rótulo tras la letra")
        self.assertEqual([f["gridPos"]["y"] for f in lista], sorted(f["gridPos"]["y"] for f in lista))

    def test_las_filas_ocupan_todo_el_ancho_y_una_unidad_de_alto(self):
        for fila in filas():
            with self.subTest(fila=fila["title"]):
                self.assertEqual(fila["gridPos"]["x"], 0)
                self.assertEqual(fila["gridPos"]["w"], 24)
                self.assertEqual(fila["gridPos"]["h"], 1)

    def test_la_primera_entrada_es_la_fila_a(self):
        self.assertEqual(paneles()[0].get("type"), "row")
        self.assertTrue(paneles()[0]["title"].startswith("A · "))

    def test_cada_panel_cae_en_una_seccion_y_cada_seccion_tiene_paneles(self):
        secciones = {}
        for letra, panel in contenido():
            secciones.setdefault(letra, []).append(panel)
        self.assertEqual(sorted(secciones), ["A", "B", "C"])
        # Orden de lectura: la lista de paneles recorre A, luego B, luego C, sin intercalar.
        orden = [letra for letra, _ in contenido()]
        self.assertEqual(orden, sorted(orden))


# --- Descripción obligatoria -----------------------------------------------------------------------------------------


class DescripcionTests(unittest.TestCase):
    def test_tres_lineas_tipo_mide_no_demuestra_en_todo_panel_que_no_es_fila(self):
        # Cada panel (también los de texto) declara su tipo de medida, qué mide y qué NO demuestra, en este orden y en
        # exactamente tres líneas: es lo que el escenario «Descripción de cada panel» pide revisar.
        self.assertTrue(contenido())
        for letra, panel in contenido():
            with self.subTest(seccion=letra, panel=panel["title"]):
                descripcion = panel.get("description")
                self.assertIsInstance(descripcion, str)
                self.assertNotIn("\r", descripcion)
                lineas = descripcion.split("\n")
                self.assertEqual(len(lineas), 3, lineas)
                self.assertRegex(lineas[0], rf"^Tipo: {letra}(?![A-Za-z0-9])")
                self.assertRegex(lineas[1], r"^Mide: \S")
                self.assertRegex(lineas[2], r"^No demuestra: \S")

    def test_la_limitacion_de_cada_seccion_esta_nombrada(self):
        # «No demuestra» no es un relleno: A nombra que no cubre usuarios reales ni preguntas fuera de la batería,
        # B que no hay piloto real y C que los síntomas no prueban que las respuestas sean correctas.
        for letra, panel in contenido():
            with self.subTest(seccion=letra, panel=panel["title"]):
                linea = panel["description"].split("\n")[2]
                self.assertRegex(linea, LIMITACION_POR_SECCION[letra])


# --- Datasources -----------------------------------------------------------------------------------------------------


def _datasources_anidados(valor, ruta=""):
    """Todos los valores bajo una clave `datasource`, en cualquier nivel del panel."""
    if isinstance(valor, dict):
        for clave, hijo in valor.items():
            if clave == "datasource":
                yield f"{ruta}/{clave}", hijo
            else:
                yield from _datasources_anidados(hijo, f"{ruta}/{clave}")
    elif isinstance(valor, list):
        for indice, hijo in enumerate(valor):
            yield from _datasources_anidados(hijo, f"{ruta}[{indice}]")


class DatasourcesTests(unittest.TestCase):
    def test_paneles_de_datos_declaran_el_datasource_de_su_seccion_y_sus_targets_el_mismo(self):
        # Referencia con tipo y uid (hallazgo del QA de 4.1 con un Grafana 11.3.0 real). A y B solo PostgreSQL, C solo
        # Prometheus: ningún panel mezcla los dos y ningún target hereda el predeterminado por omisión.
        hay_datos = False
        for letra, panel in contenido():
            if panel["type"] == "text":
                continue
            hay_datos = True
            esperado = DATASOURCE_POR_SECCION[letra]
            with self.subTest(seccion=letra, panel=panel["title"]):
                self.assertEqual(panel.get("datasource"), esperado)
                objetivos = panel.get("targets")
                self.assertTrue(isinstance(objetivos, list) and objetivos, "un panel de datos necesita targets")
                for objetivo in objetivos:
                    self.assertEqual(objetivo.get("datasource"), esperado)
        self.assertTrue(hay_datos)

    def test_ningun_datasource_anidado_distinto_del_de_la_seccion(self):
        # Cualquier `datasource` en cualquier nivel del panel (opciones, overrides, transformaciones) es el de su
        # sección: una referencia al otro datasource dentro del panel lo convertiría en un panel mixto.
        for letra, panel in contenido():
            with self.subTest(seccion=letra, panel=panel["title"]):
                for ruta, valor in _datasources_anidados(panel):
                    self.assertEqual(valor, DATASOURCE_POR_SECCION[letra], ruta)

    def test_los_paneles_de_texto_no_llevan_targets(self):
        textos = [p for _, p in contenido() if p["type"] == "text"]
        self.assertGreaterEqual(len(textos), 3)
        for panel in textos:
            with self.subTest(panel=panel["title"]):
                self.assertNotIn("targets", panel)

    def test_secciones_a_y_b_solo_sql_y_c_solo_promql(self):
        for letra, panel in contenido():
            for objetivo in panel.get("targets", []):
                with self.subTest(seccion=letra, panel=panel["title"]):
                    if letra == "C":
                        self.assertIn("expr", objetivo)
                        self.assertNotIn("rawSql", objetivo)
                    else:
                        self.assertIn("rawSql", objetivo)
                        self.assertNotIn("expr", objetivo)

    def test_los_unicos_datasources_del_dashboard_son_los_dos_esperados(self):
        # Revisa todo el fichero (también `annotations`), con la salvedad de la anotación integrada de Grafana.
        validos = [DS_POSTGRES, DS_PROMETHEUS, {"type": "grafana", "uid": "-- Grafana --"}]
        for ruta, valor in _datasources_anidados(dashboard()):
            with self.subTest(ruta=ruta):
                self.assertIn(valor, validos)


# --- Sección A -------------------------------------------------------------------------------------------------------


class SeccionATests(unittest.TestCase):
    def test_hay_un_texto_introductorio(self):
        textos = _hay("a0")
        for panel in textos:
            self.assertTrue(isinstance(panel.get("options", {}).get("content"), str) and panel["options"]["content"].strip())

    def test_cada_pieza_existe_y_hay_exactamente_una_de_cada_una(self):
        # Diez piezas: una por cada cosa que la sección A debe contar. «Exactamente una» evita que una pieza duplicada
        # tape a otra que falta.
        for clave in CLAVES_A:
            with self.subTest(pieza=clave):
                self.assertEqual(len(buscar(clave)), 1, [p["title"] for p in buscar(clave)])

    def test_las_piezas_de_lectura_existen_una_sola_vez_y_cada_una_con_su_tipo(self):
        # El clasificador distingue la matriz, el resumen y la evolución de la latencia del detalle (`a4`) y de las
        # evoluciones `a5`/`a6`, con las que comparten palabras. Si una regla se pierde, el panel se cuela en otra
        # pieza (`a4` pasa a tener dos) o queda sin clasificar: aquí se exige exactamente uno de cada y su tipo.
        esperados = {"a_matriz": "table", "a_resumen": "table", "a_evolucion_latencia": "timeseries",
                     "a_indicadores_robustez": "table"}
        self.assertEqual(set(esperados), set(CLAVES_LECTURA))
        for clave, tipo in esperados.items():
            with self.subTest(pieza=clave):
                self.assertEqual(len(buscar(clave)), 1, [p["title"] for p in buscar(clave)])
                self.assertEqual(_unico(clave)["type"], tipo)

    def test_ningun_panel_de_datos_de_a_queda_sin_clasificar(self):
        # Un panel de A que ninguna pieza reclama es un panel que el contrato no conoce (y que las pruebas no ven).
        for panel in de_seccion("A"):
            if panel["type"] == "text":
                continue
            with self.subTest(panel=panel["title"]):
                self.assertIsNotNone(clasificar(panel))

    def test_tipos_de_panel(self):
        for clave in CLAVES_A:
            esperado = "timeseries" if clave in ("a5", "a6") else "table"
            for panel in buscar(clave):
                with self.subTest(pieza=clave):
                    self.assertEqual(panel["type"], esperado)

    def test_a1_tabla_de_ejecuciones(self):
        sql = _plano(sql_de(_unico("a1")))
        self.assertRegex(sql, r"(?i)^(SELECT|WITH)\b")
        self.assertRegex(sql, r"evaluation\.runs\b")
        for columna in ("run_id", "source", "run_at", "suite_version", "commit_sha", "generation_model", "milestone"):
            with self.subTest(columna=columna):
                self.assertRegex(sql, rf"\b{columna}\b")
        # El estado real / no real se calcula a partir de `is_real` y de los motivos de ejecución no real.
        self.assertRegex(sql, r"\bis_real\b")
        self.assertRegex(sql, r"\bnon_real_reasons\b")

    def test_a2_estados_de_los_casos_con_denominador(self):
        sql = _plano(sql_de(_unico("a2")))
        self.assertRegex(sql, r"evaluation\.results\b")
        self.assertRegex(sql, r"evaluation\.runs\b")
        self.assertRegex(sql, r"metric_id\s*=\s*'cases'")
        for palabra in ("pass", "fail", "blocked", "not_run", "denominator"):
            with self.subTest(palabra=palabra):
                self.assertRegex(sql, rf"\b{palabra}\b")

    def test_a3_proporciones_de_calidad_con_numerador_denominador_valor_y_estado(self):
        sql = _plano(sql_de(_unico("a3")))
        self.assertRegex(sql, r"evaluation\.results\b")
        for palabra in ("numerator", "denominator", "value", "status"):
            with self.subTest(palabra=palabra):
                self.assertRegex(sql, rf"\b{palabra}\b")

    def test_a4_latencia_formato_y_disponibilidad_de_la_campana(self):
        panel = _unico("a4")
        self.assertIn("campaña", panel["title"].lower())
        self.assertNotIn("tráfico real", panel["title"].lower())
        self.assertRegex(_plano(sql_de(panel)), r"evaluation\.results\b")

    def test_a5_evolucion_automatica(self):
        self._evolucion(_unico("a5"), "automatic")

    def test_a6_evolucion_con_juicio_humano_solo_de_hito(self):
        panel = _unico("a6")
        self._evolucion(panel, "human")
        # Las series de juicio humano solo incluyen ejecuciones de hito (D5 del diseño).
        self.assertRegex(_plano(sql_de(panel)), r"\bmilestone\b")

    def _evolucion(self, panel, juicio):
        sql = _plano(sql_de(panel))
        self.assertEqual(panel["type"], "timeseries")
        self.assertRegex(sql, r"evaluation\.comparable_runs\b")
        self.assertRegex(sql, r"evaluation\.results\b")
        self.assertRegex(sql, rf"judgment\s*=\s*'{juicio}'")
        self.assertRegex(sql, r"status\s*=\s*'measured'")
        # Las series filtran las ejecuciones sin fecha aunque la vista ya lo haga: la consulta no depende de ella.
        self.assertRegex(sql, r"run_at\s+IS\s+NOT\s+NULL")
        for alias in (r"\btime\b", r"\bmetric\b", r"\bvalue\b"):
            self.assertRegex(sql, rf"(?i)\bAS\s+{alias[2:-2]}\b")
        for objetivo in panel["targets"]:
            self.assertEqual(objetivo.get("format"), "time_series")
        # Una serie sin otra comparable no se dibuja: el panel dice por qué (nunca un 0 %), y nunca une un hueco.
        self.assertEqual(_defaults(panel).get("noValue"), NO_COMPARABLE)
        self.assertIs(_defaults(panel).get("custom", {}).get("spanNulls"), False)

    def test_a7_calibracion_muestra_el_candidato_elegido(self):
        sql = _plano(sql_de(_unico("a7")))
        self.assertRegex(sql, r"grp\s*=\s*'calibration'")
        self.assertRegex(sql, r"\bselected\b")

    def test_a8_benchmark_de_modelos(self):
        sql = _plano(sql_de(_unico("a8")))
        for palabra in ("keyword_score", "latency_p95", "cost"):
            with self.subTest(palabra=palabra):
                self.assertRegex(sql, rf"\b{palabra}\b")

    def test_a9_robustez_vacia_con_aviso_que_nombra_jup_071(self):
        panel = _unico("a9")
        aviso = _defaults(panel).get("noValue", "")
        self.assertIn("Sin datos", aviso)
        self.assertIn("JUP-071", aviso)
        # Es una tabla con `value`: el aviso de «sin filas» no sustituye al «No medido» de los nulos.
        self.assertTrue(muestra_no_medido(panel))


# --- Sección B -------------------------------------------------------------------------------------------------------


class SeccionBTests(unittest.TestCase):
    def test_hay_texto_y_al_menos_una_tabla_de_negocio(self):
        self.assertTrue(_hay("b_texto"))
        self.assertTrue(_hay("b_tabla"))

    def test_todos_los_paneles_de_datos_de_b_son_tablas_de_negocio(self):
        for panel in de_seccion("B"):
            if panel["type"] == "text":
                continue
            with self.subTest(panel=panel["title"]):
                self.assertIn(panel, buscar("b_tabla"))

    def test_la_tabla_nombra_tiempo_asignacion_y_ahorro_y_el_estado_real_o_sintetico(self):
        # Entre todas las tablas de B se ven las filas de tiempo, de asignación y de ahorro. Los nombres no tienen
        # que estar en el SQL (una consulta general con `measure_type = 'B'` los devuelve): lo comprueba el módulo de
        # consultas con la base real. Aquí solo se exige que el estado real/sintético salga de `is_real`.
        sql = " ".join(_plano(sql_de(p)) for p in _hay("b_tabla"))
        self.assertRegex(sql, r"evaluation\.results\b")
        self.assertRegex(sql, r"\bis_real\b")


# --- Sección C -------------------------------------------------------------------------------------------------------

# Las tres expresiones de `technical-metrics.json` que la sección C reutiliza idénticas (solo las del backend).
def _expresiones_tecnicas():
    tecnico = json.loads(TECHNICAL_DASHBOARD.read_text(encoding="utf-8"))
    por_titulo = {p["title"]: p for p in tecnico["panels"]}
    p95 = por_titulo["Latencia p95 por servicio (ms)"]["targets"][0]["expr"]
    error = por_titulo["Tasa de error por servicio (%)"]["targets"][0]["expr"]
    consultas = por_titulo["Volumen de consultas al asistente (consultas/min)"]["targets"][0]["expr"]
    return p95, error, consultas


# Denominador de las proporciones: consultas que terminaron (respondidas + fallidas por la recuperación), con la
# guarda `> 0` DENTRO del paréntesis para que sin tráfico no haya resultado ni NaN ni 0 (ver `design.md` D7).
def _proporcion(numerador):
    return re.compile(
        r"^\s*(?:100\s*\*\s*)?sum\(rate\(" + numerador + r"\[\w+\]\)\)\s*/\s*"
        r"\(\s*sum\(rate\(backend_assistant_queries_total\[\w+\]\)\)\s*\+\s*"
        r"sum\(rate\(backend_retrieval_failures_total\[\w+\]\)\)\s*>\s*0\s*\)\s*$"
    )


# Tasa de error de `jup-121-lectura-dashboard` (D1): el numerador lleva `or vector(0)` para valer 0 cuando hay peticiones
# y ninguna acaba en 5xx; sin peticiones el denominador no tiene series y sigue diciendo «Sin datos».
ERROR_CON_NUMERADOR_A_CERO = (
    '100 * (sum(rate(backend_http_requests_total{status_code=~"5.."}[5m])) or vector(0)) '
    "/ sum(rate(backend_http_requests_total[5m]))"
)


class SeccionCTests(unittest.TestCase):
    def _exprs(self):
        return [(p, e) for p in de_seccion("C") for e in expresiones(p)]

    def test_texto_de_sintomas_que_enlaza_al_dashboard_tecnico(self):
        textos = [p for p in de_seccion("C") if p["type"] == "text"]
        self.assertTrue(textos)
        junto = " ".join(p["title"] + " " + p.get("options", {}).get("content", "") + " " + p["description"] for p in textos)
        self.assertRegex(junto, r"(?i)s[ií]ntomas")
        self.assertIn("economicon-technical-metrics", junto)
        for panel in textos:
            self.assertTrue(panel.get("options", {}).get("content", "").strip())

    def test_latencia_y_consultas_se_reutilizan_identicas_y_el_error_solo_difiere_en_el_numerador_a_cero(self):
        p95, error, consultas = _expresiones_tecnicas()
        todas = [e for _, e in self._exprs()]
        # La latencia y las consultas por minuto siguen siendo idénticas a las del dashboard técnico (JUP-043).
        for nombre, expr in (("p95", p95), ("consultas/min", consultas)):
            with self.subTest(expresion=nombre):
                self.assertEqual(todas.count(expr), 1, expr)
        # La tasa de error ya no lo es (D1 de `jup-121-lectura-dashboard`): vale 0 con tráfico y sin 5xx. Se exige la
        # expresión nueva exacta, una sola vez, y que la del dashboard técnico (que no se toca) ya no aparezca tal cual.
        with self.subTest(expresion="error"):
            self.assertEqual(todas.count(ERROR_CON_NUMERADOR_A_CERO), 1, todas)
            self.assertEqual(todas.count(error), 0, error)
            # Y que difiere de la del dashboard técnico SOLO en el `or vector(0)` del numerador: quitado ese
            # fragmento (con su paréntesis) y normalizados los espacios, queda la expresión técnica tal cual.
            sin_el_cero = re.sub(
                r"\(\s*(sum\(rate\([^()]*\[5m\]\)\))\s+or\s+vector\(0\)\s*\)", r"\1", ERROR_CON_NUMERADOR_A_CERO
            )
            self.assertNotEqual(sin_el_cero, ERROR_CON_NUMERADOR_A_CERO)
            self.assertEqual(re.sub(r"\s+", " ", sin_el_cero).strip(), re.sub(r"\s+", " ", error).strip())

    def test_los_paneles_de_latencia_y_error_se_rotulan_como_trafico_real_en_la_descripcion(self):
        p95, _, consultas = _expresiones_tecnicas()
        # La latencia conserva su expresión; el error se localiza ya por la expresión nueva (D1).
        for expr in (p95, ERROR_CON_NUMERADOR_A_CERO):
            paneles_con = [p for p, e in self._exprs() if e == expr]
            self.assertEqual(len(paneles_con), 1)
            # D6 (`jup-121-anotaciones-y-fuente`): el título ya no lleva «(tráfico real)» (cabe en <= 40 caracteres, el
            # ancho de un tercio); el rótulo vive en la línea «Mide:» de la descripción (el ⓘ del panel).
            self.assertNotIn("tráfico real", paneles_con[0]["title"].lower())
            self.assertLessEqual(len(paneles_con[0]["title"]), 40)
            mide = [l for l in paneles_con[0]["description"].split("\n") if l.startswith("Mide:")]
            self.assertEqual(len(mide), 1, paneles_con[0]["description"])
            self.assertIn("tráfico real", mide[0].lower())
            # La latencia y la tasa de error se leen solos: ninguna otra serie comparte su panel.
            self.assertEqual(expresiones(paneles_con[0]), [expr])
        # D2: la latencia agrega todas las rutas del backend y el título lo dice (no es la del asistente).
        panel_p95 = [p for p, e in self._exprs() if e == p95][0]
        self.assertEqual(panel_p95["title"], "Latencia p95, todas las rutas")
        panel_error = [p for p, e in self._exprs() if e == ERROR_CON_NUMERADOR_A_CERO][0]
        self.assertEqual(panel_error["title"], "Tasa de error del backend")
        paneles_consultas = [p for p, e in self._exprs() if e == consultas]
        self.assertEqual(len(paneles_consultas), 1)
        # Las consultas por minuto también se rotulan como tráfico real, en su descripción y no en su título.
        self.assertEqual(paneles_consultas[0]["title"], "Consultas al asistente por minuto")
        self.assertIn("tráfico real", paneles_consultas[0]["description"].lower())

    def test_proporcion_de_busquedas_sin_contexto_con_la_guarda(self):
        self._proporcion("backend_retrieval_empty_total")

    def test_proporcion_de_fallos_de_recuperacion_con_la_guarda(self):
        self._proporcion("backend_retrieval_failures_total")

    def _proporcion(self, numerador):
        patron = _proporcion(numerador)
        encontrados = [(p, e) for p, e in self._exprs() if patron.match(e)]
        self.assertEqual(len(encontrados), 1, [e for _, e in self._exprs()])
        panel, expr = encontrados[0]
        self.assertEqual(expresiones(panel), [expr])
        # Sin consultas en la ventana la guarda deja la serie vacía: el panel debe decirlo («Sin datos»), no 0 %.
        self.assertIn("Sin datos", _defaults(panel).get("noValue", ""))
        # Nada de `or vector(0)` ni de sumar un cero: eso convertiría «sin datos» en 0 %.
        self.assertNotRegex(expr, r"(?i)vector\(|\bor\b|\+\s*0\b")

    def test_los_titulos_no_mezclan_campana_con_trafico_real(self):
        # La latencia y la disponibilidad de una campaña (A) nunca comparten panel con las del tráfico real (C):
        # los rótulos lo hacen visible. Se revisa también el texto de los títulos de las filas.
        for panel in de_seccion("A"):
            with self.subTest(seccion="A", panel=panel["title"]):
                self.assertNotIn("tráfico real", panel["title"].lower())
        for panel in de_seccion("C"):
            with self.subTest(seccion="C", panel=panel["title"]):
                self.assertNotIn("campaña", panel["title"].lower())

    def test_ningun_panel_de_c_consulta_sql_ni_ningun_a_o_b_consulta_prometheus(self):
        for letra, panel in contenido():
            for objetivo in panel.get("targets", []):
                with self.subTest(seccion=letra, panel=panel["title"]):
                    if letra == "C":
                        self.assertNotIn("evaluation.", json.dumps(objetivo))
                    else:
                        self.assertNotRegex(objetivo.get("rawSql", ""), r"backend_|processor_")

    def test_todos_los_targets_de_c_tienen_refid_unico_y_expresion(self):
        for panel in de_seccion("C"):
            if panel["type"] == "text":
                continue
            with self.subTest(panel=panel["title"]):
                refs = [t.get("refId") for t in panel["targets"]]
                self.assertTrue(all(isinstance(r, str) and r for r in refs), refs)
                self.assertEqual(len(refs), len(set(refs)))
                for objetivo in panel["targets"]:
                    self.assertTrue(isinstance(objetivo.get("expr"), str) and objetivo["expr"].strip())


# --- Lo no medido nunca es cero --------------------------------------------------------------------------------------


class NoMedidoTests(unittest.TestCase):
    def test_los_paneles_de_valor_de_a_y_b_muestran_no_medido_para_un_nulo(self):
        # Un NULL es «No medido»: con `noValue` o con un mapeo de valor `null`. Sin esto, Grafana pintaría un hueco
        # o un cero. Se aplica a toda tabla, `stat` o `gauge` cuya consulta usa `value` (los gráficos de evolución
        # tienen su propio aviso y nunca reciben nulos: filtran `status = 'measured'`).
        revisados = 0
        for letra in "AB":
            for panel in de_seccion(letra):
                if panel["type"] in ("table", "stat", "gauge") and re.search(r"\bvalue\b", sql_de(panel)):
                    revisados += 1
                    with self.subTest(seccion=letra, panel=panel["title"]):
                        self.assertTrue(muestra_no_medido(panel))
        self.assertGreaterEqual(revisados, 4)

    def test_hay_una_tabla_de_negocio_con_valor_que_muestra_no_medido(self):
        # «Beneficio realizado no medido» sale de aquí: la fila `realized_savings` tiene `value` nulo.
        for panel in _hay("b_tabla"):
            with self.subTest(panel=panel["title"]):
                self.assertTrue(muestra_no_medido(panel))

    def test_ninguna_consulta_de_a_o_b_fabrica_un_cero_ni_oculta_un_nulo(self):
        # Un NULL de la base debe llegar como NULL. Se prohíbe rellenar con 0 (`COALESCE(x, 0)`), `IFNULL`/`NVL` y
        # `NULLIF(x, 0)` (que esconde un cero medido, como un 0 % real). `COALESCE` con un texto («no registrado»)
        # sí se admite: no inventa una cifra.
        relleno = re.compile(r"(?is)\bCOALESCE\s*\((?:[^()]|\([^()]*\))*,\s*0+(?:\.0*)?\s*\)")
        for etiqueta, objetivo, panel in todas_las_consultas():
            if panel is not None and seccion_de(panel) == "C":
                continue
            sql = objetivo["rawSql"]
            with self.subTest(consulta=etiqueta):
                self.assertIsNone(relleno.search(sql), relleno.search(sql))
                self.assertNotRegex(sql, r"(?i)\b(IFNULL|NVL)\b")
                self.assertNotRegex(sql, r"(?is)\bNULLIF\s*\(")


# --- Ejecuciones no reales --------------------------------------------------------------------------------------------


class NoRealTests(unittest.TestCase):
    def _override_no_real(self, panel):
        for override in panel.get("fieldConfig", {}).get("overrides", []):
            if override.get("matcher") != {"id": "byRegexp", "options": ".*no real.*"}:
                continue
            for propiedad in override.get("properties", []):
                valor = propiedad.get("value")
                if propiedad.get("id") == "custom.lineStyle" and isinstance(valor, dict):
                    if valor.get("fill") == "dash" and valor.get("dash"):
                        return True
                if propiedad.get("id") == "color" and isinstance(valor, dict) and valor.get("fixedColor"):
                    return True
        return False

    def test_las_series_no_reales_se_dibujan_distintas(self):
        # Una serie cuyo nombre contiene `no real` (rótulo de la consulta) se dibuja discontinua o con otro color:
        # el rótulo y el estilo distinguen una ejecución de prueba de una real (D6 del diseño).
        for clave in ("a5", "a6"):
            for panel in _hay(clave):
                with self.subTest(pieza=clave):
                    self.assertTrue(self._override_no_real(panel), panel.get("fieldConfig", {}).get("overrides"))

    def test_las_consultas_de_evolucion_rotulan_la_serie_como_no_real(self):
        for clave in ("a5", "a6"):
            sql = _plano(sql_de(_unico(clave)))
            with self.subTest(pieza=clave):
                self.assertRegex(sql, r"\bis_real\b")
                self.assertIn("no real", sql)

    def test_las_tablas_de_resultados_rotulan_la_ejecucion_real_o_no(self):
        # Toda tabla con resultados de A y B incluye la distinción `real`/`no real` (calculada de `is_real`).
        for letra in "AB":
            for panel in de_seccion(letra):
                if panel["type"] != "table":
                    continue
                sql = _plano(sql_de(panel))
                clave = clasificar(panel) if letra == "A" else "b"
                if clave in ("a9",):
                    continue  # robustez: vacía por ahora; la distinción se comprueba con filas sintéticas
                with self.subTest(seccion=letra, panel=panel["title"]):
                    self.assertRegex(sql, r"\bis_real\b")
                    self.assertIn("no real", sql)


# --- Anotaciones ------------------------------------------------------------------------------------------------------


class AnotacionesTests(unittest.TestCase):
    def test_una_anotacion_de_cambios_de_configuracion_sobre_postgres(self):
        lista = dashboard().get("annotations", {}).get("list")
        self.assertIsInstance(lista, list)
        propias = anotaciones_propias()
        self.assertEqual(len(propias), 1, propias)
        entrada = propias[0]
        self.assertEqual(entrada.get("datasource"), DS_POSTGRES)
        self.assertIs(entrada.get("enable"), True)
        self.assertTrue(isinstance(entrada.get("name"), str) and entrada["name"].strip())
        objetivo = entrada.get("target")
        self.assertIsInstance(objetivo, dict)
        self.assertIs(objetivo.get("rawQuery"), True)
        self.assertEqual(objetivo.get("editorMode"), "code")
        self.assertEqual(objetivo.get("format"), "table")
        self.assertTrue(isinstance(objetivo.get("refId"), str) and objetivo["refId"])

    def test_la_anotacion_devuelve_time_text_y_tags_desde_config_changes(self):
        # `changes` es un `text[]`: sin `array_to_string` llegaría como `{modelo}` y no como etiquetas.
        sql = _plano(anotaciones_propias()[0]["target"]["rawSql"])
        self.assertRegex(sql, r"evaluation\.config_changes\b")
        self.assertRegex(sql, r"(?i)\brun_at\s+AS\s+time\b")
        self.assertRegex(sql, r"(?i)\bannotation\s+AS\s+text\b")
        self.assertRegex(sql, r"(?i)\barray_to_string\s*\(\s*changes\s*,\s*','\s*\)\s+AS\s+tags\b")

    def test_la_anotacion_integrada_de_grafana_si_existe_no_se_toca(self):
        for entrada in dashboard().get("annotations", {}).get("list", []):
            if entrada.get("builtIn"):
                self.assertEqual(entrada.get("builtIn"), 1)
                self.assertEqual(entrada.get("name"), "Annotations & Alerts")


# --- Consultas SQL -----------------------------------------------------------------------------------------------------


class ConsultasTests(unittest.TestCase):
    def test_hay_consultas_en_todos_los_paneles_de_datos_de_a_y_b(self):
        consultas = todas_las_consultas()
        # nueve piezas de A (a1..a9) + tabla de B + anotación = al menos once
        self.assertGreaterEqual(len(consultas), 11)

    def test_cada_target_sql_tiene_modo_codigo_formato_y_refid_validos(self):
        for letra, panel in contenido():
            if letra == "C" or panel["type"] == "text":
                continue
            esperado = "time_series" if panel["type"] == "timeseries" else "table"
            refs = []
            for objetivo in panel["targets"]:
                with self.subTest(panel=panel["title"], refId=objetivo.get("refId")):
                    self.assertIs(objetivo.get("rawQuery"), True)
                    self.assertEqual(objetivo.get("editorMode"), "code")
                    self.assertEqual(objetivo.get("format"), esperado)
                    self.assertTrue(isinstance(objetivo.get("refId"), str) and objetivo["refId"])
                    self.assertTrue(isinstance(objetivo.get("rawSql"), str) and objetivo["rawSql"].strip())
                    refs.append(objetivo["refId"])
            with self.subTest(panel=panel["title"], comprobacion="refId únicos"):
                self.assertEqual(len(refs), len(set(refs)), refs)

    def test_solo_lectura_una_sola_sentencia(self):
        for etiqueta, objetivo, _ in todas_las_consultas():
            sql = objetivo["rawSql"].strip()
            with self.subTest(consulta=etiqueta):
                self.assertRegex(sql, r"(?i)^(SELECT|WITH)\b")
                sin_final = sql[:-1] if sql.endswith(";") else sql
                self.assertNotIn(";", sin_final)
                self.assertIsNone(PALABRAS_PROHIBIDAS.search(sql), PALABRAS_PROHIBIDAS.search(sql))

    def test_solo_tablas_y_vistas_del_esquema_evaluation(self):
        # Cada `FROM` / `JOIN` nombra una tabla o vista de `evaluation` (o una CTE de la propia consulta); ninguna
        # referencia a otro esquema ni a los catálogos. El rol de Grafana tampoco podría leerlos (tarea 3.3).
        for etiqueta, objetivo, _ in todas_las_consultas():
            sql = _plano(objetivo["rawSql"])
            ctes = set(re.findall(r"(?i)(?:\bWITH|,)\s*(\w+)\s+AS\s*\(", sql))
            with self.subTest(consulta=etiqueta):
                self.assertTrue(re.search(r"(?i)\b(FROM|JOIN)\b", sql))
                for nombre in re.findall(r"(?i)\b(?:FROM|JOIN)\s+([A-Za-z_][\w.\"]*)", sql):
                    if nombre in ctes:
                        continue
                    self.assertIn(nombre.lower(), TABLAS_PERMITIDAS, nombre)
                self.assertNotRegex(sql, r"(?i)\b(pg_\w+|information_schema|public)\b")
                self.assertTrue(re.search(r"\bevaluation\.(runs|results|config_changes|comparable_runs)\b", sql))

    def test_ninguna_columna_puede_llevar_texto_de_preguntas_o_respuestas(self):
        # La base solo guarda cifras, estados e identificadores (spec «Sin texto de preguntas ni de respuestas»);
        # aun así ninguna consulta nombra una columna de ese tipo, por si algún día existiera.
        for etiqueta, objetivo, _ in todas_las_consultas():
            with self.subTest(consulta=etiqueta):
                self.assertIsNone(COLUMNAS_DE_TEXTO.search(objetivo["rawSql"]), COLUMNAS_DE_TEXTO.search(objetivo["rawSql"]))

    def test_las_tablas_y_las_series_declaran_sus_columnas_por_alias(self):
        # Todas las columnas de las series tienen alias explícito (`time`, `metric`, `value`): Grafana pivota por esos
        # nombres, no por los de la base.
        for clave in ("a5", "a6"):
            sql = _plano(sql_de(_unico(clave)))
            with self.subTest(pieza=clave):
                self.assertRegex(sql, r"(?i)\bAS\s+time\b")


# --- Secretos ----------------------------------------------------------------------------------------------------------


class SecretosTests(unittest.TestCase):
    def test_el_dashboard_no_contiene_contrasenas_tokens_ni_claves(self):
        # Depende de que el fichero exista (lo lee): no puede pasar «por vacío».
        texto = crudo().decode("utf-8")
        self.assertTrue(texto.strip())
        self.assertIsNone(SECRETOS.search(texto), SECRETOS.search(texto))
        self.assertNotRegex(texto, r"://[^/\s\"]*:[^/\s\"]*@")


if __name__ == "__main__":
    unittest.main()
