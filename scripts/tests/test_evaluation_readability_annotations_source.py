"""Anotaciones en todas las evoluciones, estado de casos solo de JUP-070 y contrato de clasificación (JUP-121, change
`jup-121-anotaciones-y-fuente`, Red).

Cubre los tres requisitos que añade el change (segunda validación de Paris y comentario de Lucia sobre JUP-071, PR #132):

1. «Anotaciones de cambio de configuración en todas las evoluciones». La capa «Cambios de configuración» es una anotación
   de Grafana con filtro por paneles (`filter.ids`, modo inclusión). Hoy cubre solo las evoluciones de métricas automáticas y
   de juicio humano y OMITE la evolución de la latencia de la campaña: la marca vertical no aparece en esa gráfica. Se fija:
   `filter.exclude` es `false` y `filter.ids` son EXACTAMENTE los ids de las tres evoluciones (localizadas por título, no por
   número: la numeración no es contrato) y ningún otro panel. Además se ejecuta la consulta de la capa contra PostgreSQL real,
   con el rol de lectura, en el escenario de Paris (dos pares de ejecuciones comparables de JUP-070 con un cambio de batería
   entre los pares) y se enlaza con las gráficas: la marca solo tiene sentido si cada una de las tres devuelve puntos a
   ambos lados del instante del cambio, así que se comprueba que los devuelven.
2. «Estado de los casos solo de las campañas de JUP-070». La consulta de «Estado de los casos por ejecución» filtra por
   `r.source = 'JUP-070'` (como ya hace el resumen de la última campaña). Una ejecución de otra fuente (JUP-071) con filas
   `cases/cases/all` no debe aparecer. La prueba lo demuestra con el escenario Y demuestra que el escenario discrimina:
   quitando el filtro por sustitución de texto en memoria, la ejecución de JUP-071 sí aparecería.
3. «Contrato de clasificación para nuevas fuentes». La guía, bajo «Robustez (JUP-071)», dice qué filas marcar `human` y
   cuáles `automatic` y que no se reutilicen los grupos de JUP-070. Se comprueba con palabras clave por frase o bloque, no
   con una redacción exacta.

Los paneles se localizan por título. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`; ruta de la guía:
`EVALUATION_DASHBOARD_GUIDE` (sirven para comprobar un borrador o una copia mutada).
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_annotations_source.py`
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

GUIA = Path(os.environ.get("EVALUATION_DASHBOARD_GUIDE") or R.ROOT / "docs" / "validation" / "evaluation-dashboard.md")

# Las tres gráficas de evolución de la sección A (se localizan por título).
EVOLUCIONES = (
    "Evolución de las métricas automáticas",
    "Evolución con juicio humano (solo hitos)",
    "Evolución de la latencia de la campaña",
)
TITULO_ESTADO = "Estado de los casos por ejecución"
FAMILIAS_JUP070 = ("accuracy", "relevance", "grounding", "latency", "robustness", "availability")


def capa_de_anotaciones() -> dict:
    """La única capa propia (no integrada de Grafana) «Cambios de configuración» del dashboard."""
    lista = R.dashboard().get("annotations", {}).get("list")
    if not isinstance(lista, list):
        raise AssertionError("`annotations.list` debe ser una lista")
    propias = [a for a in lista if not a.get("builtIn")
               and R.sin_acentos(str(a.get("name", ""))).startswith("Cambios de configuracion")]
    if len(propias) != 1:
        raise AssertionError(f"se esperaba exactamente una capa «Cambios de configuración» y hay {len(propias)}")
    return propias[0]


def ids_de_evoluciones() -> set:
    return {R.por_titulo(titulo, "A")["id"] for titulo in EVOLUCIONES}


def instante(texto: str) -> datetime:
    return datetime.fromisoformat(texto).astimezone(timezone.utc)


# --- Anotaciones: filtro de paneles ------------------------------------------------------------------------------------


class FiltroDeLaCapaDeAnotacionesTests(unittest.TestCase):
    def test_la_capa_es_de_inclusion_no_de_exclusion(self):
        # Caso: con `exclude: true` el filtro significaría «todos MENOS estos paneles» y la lista de ids dejaría de decir
        # dónde se ve la marca. La spec habla de los paneles donde SÍ aparece, así que debe ser inclusión explícita.
        filtro = capa_de_anotaciones().get("filter")
        self.assertIsInstance(filtro, dict, "la capa debe llevar un filtro por paneles")
        self.assertIs(filtro.get("exclude"), False)

    def test_el_filtro_incluye_exactamente_las_tres_evoluciones_y_ningun_otro_panel(self):
        # Caso (defecto de Paris): el filtro tenía los paneles de proporciones y de juicio humano, pero no la latencia, y la
        # marca del cambio de batería no salía en esa gráfica. Los ids esperados se calculan por TÍTULO, no copiados:
        # si el coder renumera paneles, la prueba sigue siendo verdadera. «Ningún otro» = igualdad de conjuntos (ni la tabla
        # de ejecuciones ni la sección C llevan marcas: no son series en el tiempo de las campañas).
        ids = capa_de_anotaciones().get("filter", {}).get("ids")
        self.assertIsInstance(ids, list)
        self.assertEqual(len(ids), len(set(ids)), f"ids repetidos en el filtro: {ids}")
        esperados = ids_de_evoluciones()
        self.assertEqual(len(esperados), 3, "las tres evoluciones deben ser paneles distintos")
        self.assertEqual(set(ids), esperados)

    def test_la_evolucion_de_la_latencia_esta_en_el_filtro(self):
        # Caso específico del defecto, con mensaje propio: la latencia de la campaña DEBE recibir la marca.
        latencia = R.por_titulo("Evolución de la latencia de la campaña", "A")["id"]
        self.assertIn(latencia, capa_de_anotaciones().get("filter", {}).get("ids", []))


# --- Anotaciones: el escenario de Paris contra PostgreSQL real ---------------------------------------------------------


def serie_del_escenario() -> str:
    """Dos pares de ejecuciones comparables de JUP-070 (días 10-11 y 12-13) con otra batería entre los pares.

    Cada ejecución lleva una proporción automática (ACC-2), una de juicio humano (ACC-1, ejecución de hito) y la latencia
    mediana de la etapa `total` (LAT-1, ms), para que las tres evoluciones tengan datos. Las claves de comparabilidad
    son distintas entre pares (cambia la batería) e iguales dentro de cada par; `modelo`, `prompt` y `corpus` no cambian,
    así que la ÚNICA anotación es `bateria`. Se vacían antes las campañas versionadas: son también de JUP-070 y
    añadirían cambios propios (y un cambio entre la última versionada y la primera sintética) que no son el escenario.
    """
    sql = "DELETE FROM evaluation.runs;\n"
    for indice, (dia, clave) in enumerate(((10, "k-an-a"), (11, "k-an-a"), (12, "k-an-b"), (13, "k-an-b")), start=1):
        run_id = f"an-{indice}"
        sql += R.insertar_ejecucion(run_id, "JUP-070", f"2026-10-{dia:02d}T10:00:00Z", clave=clave, hito=True)
        version, huella = ("1.0.0", "aa" * 32) if indice <= 2 else ("2.0.0", "bb" * 32)
        sql += (f"UPDATE evaluation.runs SET suite_version = {R.literal(version)}, suite_sha256 = {R.literal(huella)}"
                f" WHERE run_id = {R.literal(run_id)};\n")
        sql += R.insertar_resultado(run_id, "accuracy", "ACC-2", valor=0.5 + indice / 100, numerador=5, denominador=10,
                                    juicio="automatic")
        sql += R.insertar_resultado(run_id, "accuracy", "ACC-1", valor=0.4 + indice / 100, numerador=4, denominador=10,
                                    juicio="human")
        sql += R.insertar_resultado(run_id, "latency", "LAT-1", "total", valor=3000.0 + indice, unidad="ms",
                                    denominador=28, juicio="automatic")
    return sql


ESCENARIO = serie_del_escenario()
CAMBIO = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)


class AnotacionesEnElEscenarioDeParisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capa = capa_de_anotaciones()
        cls.marcas = R.ejecutar(cls.capa["target"]["rawSql"], ESCENARIO)

    def test_la_consulta_de_la_capa_devuelve_una_unica_marca_cambia_bateria_el_12_de_octubre(self):
        # Caso: un cambio de batería entre dos pares comparables de la misma fuente = UNA fila con el texto
        # «Cambia: bateria» (así lo redacta `config_changes`) en la fecha de la primera ejecución del segundo par. Dentro de
        # cada par no hay cambios, así que no hay más filas.
        self.assertTrue({"time", "text", "tags"} <= set(R.nombres(self.marcas)), R.nombres(self.marcas))
        self.assertEqual(len(self.marcas["filas"]), 1, self.marcas["filas"])
        fila = self.marcas["filas"][0]
        self.assertEqual(fila["text"], "Cambia: bateria")
        self.assertEqual(fila["tags"], "bateria")
        self.assertEqual(instante(fila["time"]), CAMBIO)

    def test_las_tres_evoluciones_devuelven_puntos_a_ambos_lados_de_la_marca(self):
        # Caso: la marca es útil solo si hay algo que anotar. Cada evolución devuelve, en el escenario, 4 puntos (una
        # serie por par de ejecuciones comparables, 2 puntos cada una): dos antes y dos después del cambio. Se ejecuta la
        # consulta REAL de cada panel con el rol de lectura. Si alguna no dibujara dos puntos, la prueba del filtro
        # protegería una gráfica vacía.
        for titulo in EVOLUCIONES:
            panel = R.por_titulo(titulo, "A")
            with self.subTest(panel=titulo):
                datos = R.ejecutar(R.consulta_unica(panel), ESCENARIO)
                tiempos = [instante(f["time"]) for f in datos["filas"]]
                self.assertEqual(len(tiempos), 4, datos["filas"])
                self.assertGreaterEqual(len(tiempos), 2)
                self.assertTrue([t for t in tiempos if t < CAMBIO], "sin puntos antes del cambio")
                self.assertTrue([t for t in tiempos if t >= CAMBIO], "sin puntos después del cambio")

    def test_las_graficas_anotadas_son_las_que_devuelven_datos_en_el_escenario(self):
        # Enlace entre los dos bloques: las gráficas con datos a ambos lados de la marca son exactamente las del filtro.
        # (Si el filtro se quedara con las dos antiguas, la tercera tendría datos y no marca: es el defecto de Paris.)
        con_datos = {R.por_titulo(t, "A")["id"] for t in EVOLUCIONES
                     if len(R.ejecutar(R.consulta_unica(R.por_titulo(t, "A")), ESCENARIO)["filas"]) >= 2}
        self.assertEqual(set(self.capa.get("filter", {}).get("ids", [])), con_datos)


# --- Estado de los casos solo de JUP-070 --------------------------------------------------------------------------------


def panel_estado() -> dict:
    return R.por_titulo(TITULO_ESTADO, "A")


def consulta_estado() -> str:
    return R.consulta_unica(panel_estado())


def sin_filtro_de_fuente(sql: str) -> str:
    """La consulta con el filtro `<alias>.source = 'JUP-070'` quitado (sustitución en memoria, solo para la prueba)."""
    condicion = r"[\w.]*\bsource\s*=\s*'JUP-070'"
    nueva = re.sub(rf"(?i)\bAND\s+{condicion}", "", sql)
    return re.sub(rf"(?i){condicion}\s+AND\b", "", nueva)


def where_principal(sql: str) -> str:
    """Texto del `WHERE` de la consulta principal (profundidad de paréntesis 0) hasta `GROUP BY`/`ORDER BY`.

    Los `FILTER (WHERE ...)` de las columnas de recuento también son `WHERE`, pero no son el filtro de filas.
    """
    profundidad, inicio = 0, None
    for m in re.finditer(r"\(|\)|\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b", sql, re.I):
        token = m.group(0)
        if token == "(":
            profundidad += 1
        elif token == ")":
            profundidad -= 1
        elif profundidad == 0 and token.upper() == "WHERE" and inicio is None:
            inicio = m.end()
        elif profundidad == 0 and inicio is not None:
            return sql[inicio:m.start()]
    if inicio is None:
        raise AssertionError("la consulta no tiene WHERE")
    return sql[inicio:]


# Una ejecución de robustez de JUP-071 con filas de estados de casos, con los mismos grupo, métrica y variante que las
# campañas de JUP-070 (`cases/cases/all`) y recuentos propios para reconocerla (6, 2, 1, 1 sobre 10).
ROBUSTEZ = R.insertar_ejecucion("rob-071", "JUP-071", "2026-10-14T10:00:00Z") + "".join(
    R.insertar_resultado("rob-071", "cases", "cases", "all", estado=estado, unidad="casos", denominador=10,
                         recuento=cuenta, juicio=None)
    for estado, cuenta in (("pass", 6), ("fail", 2), ("blocked", 1), ("not_run", 1)))
CON_ROBUSTEZ = ROBUSTEZ
SOLO_ROBUSTEZ = "DELETE FROM evaluation.runs;\n" + ROBUSTEZ


class FiltroPorFuenteEstaticoTests(unittest.TestCase):
    def test_el_where_filtra_por_la_fuente_jup_070(self):
        # Caso: la descripción del panel promete las campañas de JUP-070 pero la consulta tomaba cualquier ejecución con
        # `cases/cases`. Se exige la condición en el WHERE (tolerando espacios, saltos de línea y alias), igual que el resumen
        # de la última campaña.
        donde = where_principal(R.plano(consulta_estado()))
        self.assertRegex(donde, r"(?i)\bsource\s*=\s*'JUP-070'")
        # Y conserva las condiciones de los casos: el filtro de fuente se AÑADE, no sustituye al de grupo y métrica.
        self.assertRegex(donde, r"(?i)\bgrp\s*=\s*'cases'")
        self.assertRegex(donde, r"(?i)\bmetric_id\s*=\s*'cases'")

    def test_la_descripcion_sigue_hablando_de_jup_070(self):
        # La spec no cambia el texto del panel: el filtro hace cierta la promesa que ya contenía.
        self.assertIn("JUP-070", panel_estado().get("description", "") + panel_estado()["title"])


class EstadoDeLosCasosContraPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel_estado()  # sin el panel falla antes de arrancar Docker
        cls.sql = consulta_estado()

    def test_con_el_manifiesto_versionado_siguen_las_dos_campanas_de_jup_070_con_sus_recuentos(self):
        # Caso de no regresión: el filtro no quita lo que debe verse. Las dos campañas versionadas tienen 28 casos, todos
        # `fail` (como en la conciliación existente); `blocked` y `not_run` son ceros medidos, no nulos.
        datos = R.ejecutar(self.sql)
        esperadas = {f["run_id"] for f in R.administrar("SELECT run_id FROM evaluation.runs WHERE source = 'JUP-070'")}
        self.assertEqual(len(esperadas), 3)
        self.assertEqual(len(datos["filas"]), 3)
        self.assertEqual({f["run_id"] for f in datos["filas"]}, esperadas)
        for fila in datos["filas"]:
            with self.subTest(run_id=fila["run_id"]):
                # La tercera campaña es el banco con el chat real de JUP-133: 10 aprobados y 18 fallidos.
                esperado = (10, 18, 0, 0, 28) if fila["run_id"].startswith("jup-070-20261022") else (0, 28, 0, 0, 28)
                self.assertEqual((fila["pass"], fila["fail"], fila["blocked"], fila["not_run"], fila["denominator"]), esperado)

    def test_una_ejecucion_de_jup_071_con_recuentos_de_casos_no_aparece(self):
        # Caso (hallazgo de Lucia): una ejecución de robustez con filas `cases/cases/all` no es una campaña de JUP-070. El
        # panel sigue con exactamente las 2 campañas y ninguna fila es la de JUP-071.
        datos = R.ejecutar(self.sql, CON_ROBUSTEZ)
        runs = [f["run_id"] for f in datos["filas"]]
        self.assertNotIn("rob-071", runs)
        self.assertEqual(len(runs), 3, runs)
        self.assertEqual(set(runs), {f["run_id"] for f in R.administrar(
            "SELECT run_id FROM evaluation.runs WHERE source = 'JUP-070'", CON_ROBUSTEZ)})

    def test_sin_el_filtro_la_ejecucion_de_jup_071_si_se_mostraria(self):
        # Valida el PROPIO escenario: si quitando el filtro (sustitución de texto en memoria) la ejecución de JUP-071 también
        # desapareciera, la prueba anterior no discriminaría nada. Con el filtro quitado salen 6 filas (las dos campañas de robustez
        # versionadas también cuentan como JUP-071), y la de este escenario trae
        # sus recuentos (6, 2, 1, 1 sobre 10): se lee como una campaña más, que es el defecto.
        sin_filtro = sin_filtro_de_fuente(self.sql)
        self.assertNotEqual(sin_filtro, self.sql, "no se pudo quitar el filtro de fuente de la consulta: no está o es raro")
        datos = R.ejecutar(sin_filtro, CON_ROBUSTEZ)
        por_run = {f["run_id"]: f for f in datos["filas"]}
        self.assertEqual(len(por_run), 6, sorted(por_run))
        fila = por_run["rob-071"]
        self.assertEqual((fila["pass"], fila["fail"], fila["blocked"], fila["not_run"], fila["denominator"]),
                         (6, 2, 1, 1, 10))

    def test_con_solo_una_ejecucion_de_jup_071_el_panel_no_devuelve_filas(self):
        # Edge: sin campañas de JUP-070 (aquí se vacían las versionadas) y con una sola ejecución de otra fuente, el panel
        # queda vacío: no se rellena con lo que haya.
        datos = R.ejecutar(self.sql, SOLO_ROBUSTEZ)
        self.assertEqual(datos["filas"], [])
        # El escenario discrimina también aquí: sin filtro, esa ejecución sí saldría.
        self.assertEqual([f["run_id"] for f in R.ejecutar(sin_filtro_de_fuente(self.sql), SOLO_ROBUSTEZ)["filas"]],
                         ["rob-071"])


# --- Guía: contrato de clasificación para nuevas fuentes -----------------------------------------------------------------


ENCABEZADO = re.compile(r"^(#{1,6})\s+Robustez \(JUP-071\)\s*$", re.M)
PROHIBIR_REUTILIZAR = re.compile(
    r"no (?:se )?(?:deb\w+ )?(?:reutiliz|reutilic|reus|usar|use|usen|emple)|"
    r"(?:evit|prohib)\w+ (?:reutiliz|reus|usar|emple)|"
    r"no (?:los |las )?(?:comparta|compartan|repit)|"
    r"distint|propi[oa]s? (?:grupo|famil)|(?:grupo|famil)\w* (?:propi|distint|nuev)")


def apartado() -> str:
    """Texto bajo «Robustez (JUP-071)» hasta el siguiente encabezado de su mismo nivel o superior."""
    if not GUIA.is_file():
        raise AssertionError(f"no existe la guía {GUIA}")
    texto = GUIA.read_text(encoding="utf-8")
    encabezado = ENCABEZADO.search(texto)
    if not encabezado:
        raise AssertionError("la guía no tiene un encabezado «Robustez (JUP-071)»")
    nivel = len(encabezado.group(1))
    resto = texto[encabezado.end():]
    cierre = re.search(rf"^#{{1,{nivel}}}\s", resto, re.M)
    return resto[:cierre.start()] if cierre else resto


def bloques(markdown: str) -> list:
    """Unidades de texto: cada viñeta (con sus líneas de continuación), cada fila de tabla y cada párrafo."""
    resultado, actual = [], []

    def cerrar():
        if actual:
            resultado.append(" ".join(actual))
            actual.clear()

    for linea in markdown.split("\n"):
        if not linea.strip():
            cerrar()
        elif re.match(r"^\s*([-*+]|\d+[.)])\s+", linea) or linea.lstrip().startswith("|"):
            cerrar()
            actual.append(linea.strip())
            if linea.lstrip().startswith("|"):
                cerrar()
        elif linea.startswith("#"):
            cerrar()
        else:
            actual.append(linea.strip())
    cerrar()
    return resultado


def frases() -> list:
    """Frases (sin tildes, en minúsculas) de los bloques del apartado; se parten por `. ` y `; `, no por `:`."""
    salida = []
    for bloque in bloques(apartado()):
        plano = R.sin_acentos(bloque).lower()
        salida.extend(f for f in re.split(r"(?<=[.;])\s+", plano) if f.strip())
    return salida


def en_alguna_frase(*patrones: str) -> bool:
    return any(all(re.search(p, frase) for p in patrones) for frase in frases())


class ContratoDeClasificacionEnLaGuiaTests(unittest.TestCase):
    def test_el_apartado_existe_y_no_esta_vacio(self):
        self.assertTrue(apartado().strip(), "el apartado «Robustez (JUP-071)» está vacío")

    def test_las_proporciones_que_salen_del_resultado_de_un_caso_se_marcan_human(self):
        # Caso (D3): `pass_over_total` y `pass_over_evaluated` salen del resultado de un caso, que mezcla reglas y puntos
        # juzgados por personas; si se marcaran `automatic` entrarían en «Evolución de las métricas automáticas», que no
        # filtra por fuente. Cada una debe aparecer, en una frase propia, junto a `human`.
        for nombre in ("pass_over_total", "pass_over_evaluated"):
            with self.subTest(nombre=nombre):
                self.assertTrue(en_alguna_frase(nombre, r"\bhuman\b"),
                                f"la guía no dice que `{nombre}` se marca `human`")

    def test_las_comprobaciones_por_regla_se_marcan_automatic(self):
        # Caso (D3): lo que decide una regla (`numeric_checks`) es la contraparte `automatic`.
        self.assertTrue(en_alguna_frase("numeric_checks", r"\bautomatic\b"),
                        "la guía no dice que `numeric_checks` se marca `automatic`")

    def test_los_marcados_de_revision_se_marcan_human(self):
        # Caso (D3): `reduced_coverage` (revisión) lo marca una persona.
        self.assertTrue(en_alguna_frase("reduced_coverage", r"\bhuman\b"),
                        "la guía no dice que `reduced_coverage` se marca `human`")

    def test_pide_no_reutilizar_los_grupos_de_jup_070_y_los_nombra(self):
        # Caso (D3): varios paneles toman estos grupos sin filtrar por fuente; reutilizarlos mezclaría las series de JUP-071
        # con las campañas. Deben estar los seis nombres y una petición de no reutilizarlos en el mismo bloque.
        unidades = [R.sin_acentos(b).lower() for b in bloques(apartado())]
        candidatas = [b for b in unidades if all(re.search(rf"\b{f}\b", b) for f in FAMILIAS_JUP070)]
        self.assertTrue(candidatas, f"ningún bloque de la guía nombra los seis grupos de JUP-070: {FAMILIAS_JUP070}")
        self.assertTrue([b for b in candidatas if PROHIBIR_REUTILIZAR.search(b)],
                        "el bloque con los grupos no pide no reutilizarlos")
        self.assertTrue([b for b in candidatas if "jup-070" in b], "el bloque no dice que son los grupos de JUP-070")


if __name__ == "__main__":
    unittest.main()
