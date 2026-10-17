"""Orden de lectura de la sección A, títulos de la sección C y fecha de la matriz (JUP-121, change
`jup-121-anotaciones-y-fuente`, tareas 1.3, 1.4 y 1.5, Red).

Tres requisitos de la spec (decisiones D5, D6 y D7 del diseño), tras la segunda vuelta de Lucia sobre la PR #132:

1. «Orden de lectura de la sección A» (D5). Hoy las dos tablas «(detalle)» (exactitud y latencia por fila, 36 y 14 unidades
   de alto) están justo debajo de la matriz y empujan las gráficas de evolución al final de la sección. Se fija el orden
   de lectura (por `gridPos.y` y luego `x`, que es también el orden de la lista `panels`, porque una prueba congelada lo
   exige): rótulo de fila -> (resumen y «Cómo leer») -> ejecuciones -> estado de los casos -> matriz -> las tres
   evoluciones (SIN ninguna tabla entre la matriz y ellas) -> calibración -> benchmark -> robustez -> las dos tablas
   «(detalle)» al final, y todo antes de la fila de la sección B. Sin solapes ni huecos verticales: cada panel empieza
   donde termina el anterior (las dos evoluciones de proporciones y de latencia pueden compartir fila). Las tablas
   «(detalle)» siguen siendo las que usa la conciliación: no cambian de consulta, y se comprueba que devuelven las mismas
   filas (32 y 56 contra el manifiesto versionado, calculadas además desde la base y no solo copiadas).

   Nota sobre «Resumen» y «Cómo leer la sección A»: una prueba congelada (`test_evaluation_readability_summary`) exige que
   el resumen sea el panel con menor `y` de la sección. Aquí no se fija el orden relativo de ESOS DOS (ocupan, en el orden
   que sea, los dos primeros puestos tras el rótulo); así esta prueba no contradice a la congelada.

2. «Títulos de la sección C que no se cortan» (D6). Los paneles de Prometheus de un tercio de ancho (`w == 8`: consultas
   por minuto, p95 y tasa de error; localizados por la expresión que consultan, no por título ni `id`) llevan un título de
   40 caracteres como máximo; los títulos exactos son «Consultas al asistente por minuto», «Latencia p95, todas las rutas»
   y «Tasa de error del backend». El título del p95 conserva «todas las rutas». «Tráfico real» pasa a la descripción de
   cada panel (y el p95 sigue aclarando que no es la latencia de las consultas al asistente) y el texto de la sección C
   sigue diciendo que los paneles muestran tráfico real. Los dos paneles de proporciones (`w == 12`) no cambian de título.

3. «Fecha sin ambigüedad en la tabla por métrica y ejecución» (D7). La cabecera de columna de la matriz pasaba por
   `DD-MM HH24:MI`, que se lee como mes y día. Pasa a `YYYY-MM-DD HH24:MI` en UTC, como el resto de tablas. Se ejecuta la
   consulta REAL contra PostgreSQL con el rol de lectura: el manifiesto versionado da exactamente
   `2026-10-08 20:13 · no real: plantilla, doble` y `2026-10-08 21:01 · no real: plantilla`; con ejecuciones sintéticas de
   otro día, de fin de año y del año siguiente (mismo día y mes que otra: con `DD-MM` las dos columnas tendrían la misma
   cabecera y la matriz las fundiría) sale el año correcto; y las ejecuciones sin fecha siguen al final con su cabecera
   `sin fecha · <run_id> · ...`, que no cambia. La zona horaria de la sesión se fuerza a una que NO es UTC para que una
   consulta que formatee en hora local (sin `AT TIME ZONE 'UTC'`) no pase por casualidad.

Los paneles se localizan por título o por expresión, nunca por `id` ni posición. Ruta del dashboard:
`EVALUATION_DASHBOARD_JSON` (sirve para comprobar un JSON de referencia o una copia mutada).
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_order_titles_date.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

# --- Sección A: títulos (prefijos) en el orden de lectura esperado --------------------------------------------------------

RESUMEN = "Resumen de la última campaña"
COMO_LEER_A = "Cómo leer la sección A"
EJECUCIONES = "Ejecuciones cargadas"
ESTADO = "Estado de los casos por ejecución"
MATRIZ = "Resultados por métrica y ejecución"
EVOLUCIONES = ("Evolución de las métricas automáticas", "Evolución de la latencia de la campaña",
               "Evolución con juicio humano (solo hitos)")
CALIBRACION = "Calibración de la recuperación (JUP-022)"
BENCHMARK = "Benchmark de modelos (JUP-078)"
ROBUSTEZ = "Robustez (JUP-071)"
DETALLE_CALIDAD = "Exactitud, relevancia y fundamento (detalle)"
DETALLE_CAMPANA = "Latencia, formato y disponibilidad de la campaña (detalle)"

# Cada elemento es un tramo de la lectura: el conjunto de paneles que ocupan esos puestos, en el orden que sea cuando el
# tramo es un conjunto y en el orden dado cuando es de uno. Las dos evoluciones de proporciones y de latencia comparten fila
# (su orden horizontal lo fija otra prueba congelada), por eso las tres forman un único tramo.
TRAMOS = (
    {RESUMEN, COMO_LEER_A},
    {EJECUCIONES},
    {ESTADO},
    {MATRIZ},
    set(EVOLUCIONES),
    {CALIBRACION},
    {BENCHMARK},
    {ROBUSTEZ},
    {DETALLE_CALIDAD},
    {DETALLE_CAMPANA},
)


def seccion_a() -> list:
    """Paneles de la sección A (sin la fila) en el orden de lectura: `gridPos.y` y luego `x`."""
    return sorted(R.de_seccion("A"), key=lambda p: (p["gridPos"]["y"], p["gridPos"]["x"]))


def titulos_a() -> list:
    return [p["title"] for p in seccion_a()]


def fila_de(letra: str) -> dict:
    encontradas = [f for f in R.filas() if f["title"].startswith(letra + " ")]
    if len(encontradas) != 1:
        raise AssertionError(f"se esperaba una única fila de la sección {letra} y hay {len(encontradas)}")
    return encontradas[0]


def posicion(prefijo: str) -> int:
    """Índice del panel que empieza por `prefijo` en el orden de lectura de la sección A."""
    R.por_titulo(prefijo, "A")  # falla con un mensaje claro si falta o está repetido
    return [i for i, t in enumerate(titulos_a()) if t.startswith(prefijo)][0]


# --- D5: orden de lectura ---------------------------------------------------------------------------------------------


class OrdenDeLecturaDeLaSeccionATests(unittest.TestCase):
    def test_la_seccion_a_se_lee_en_el_orden_esperado(self):
        # Caso principal (spec «Orden de lectura de la sección A»): lo principal primero (resumen, ejecuciones, estado de
        # los casos, matriz y evoluciones), después calibración, benchmark y robustez, y al final el detalle por fila.
        # Se recorre la lectura por tramos: cada tramo exige exactamente los paneles de su conjunto en esos puestos.
        titulos = titulos_a()
        self.assertEqual(len(titulos), sum(len(t) for t in TRAMOS), f"la sección A debe tener solo estos paneles: {titulos}")
        inicio = 0
        for tramo in TRAMOS:
            reales = titulos[inicio:inicio + len(tramo)]
            with self.subTest(esperado=sorted(tramo)):
                for prefijo in tramo:
                    self.assertEqual(len([t for t in reales if t.startswith(prefijo)]), 1,
                                     f"en este puesto de la lectura se esperaba «{prefijo}»; hay {reales}")
            inicio += len(tramo)

    def test_las_evoluciones_estan_justo_detras_de_la_matriz_sin_ninguna_tabla_entre_medias(self):
        # Escenario «Evoluciones tras la matriz»: los tres paneles que siguen a la matriz son las tres evoluciones. Si una
        # tabla (p. ej. la calibración) se cuela entre la matriz y ellas, el puesto siguiente no es una evolución.
        siguientes = titulos_a()[posicion(MATRIZ) + 1:posicion(MATRIZ) + 4]
        self.assertEqual(len(siguientes), 3, siguientes)
        for prefijo in EVOLUCIONES:
            with self.subTest(evolucion=prefijo):
                self.assertEqual(len([t for t in siguientes if t.startswith(prefijo)]), 1, siguientes)
        # Y todas son gráficas, no tablas.
        for panel in seccion_a()[posicion(MATRIZ) + 1:posicion(MATRIZ) + 4]:
            self.assertEqual(panel["type"], "timeseries", panel["title"])

    def test_las_tablas_de_detalle_son_las_dos_ultimas_y_van_despues_de_la_robustez(self):
        # Escenario «Detalle al final»: exactitud primero y latencia después, ambas tras la robustez y sin nada detrás hasta
        # la fila de la sección B.
        titulos = titulos_a()
        self.assertTrue(titulos[-2].startswith(DETALLE_CALIDAD), titulos)
        self.assertTrue(titulos[-1].startswith(DETALLE_CAMPANA), titulos)
        self.assertGreater(posicion(DETALLE_CALIDAD), posicion(ROBUSTEZ))
        self.assertGreater(posicion(DETALLE_CAMPANA), posicion(ROBUSTEZ))

    def test_calibracion_benchmark_y_robustez_van_despues_de_las_evoluciones_y_antes_del_detalle(self):
        # El resto del orden por separado, para localizar el defecto con un mensaje propio.
        ultima_evolucion = max(posicion(t) for t in EVOLUCIONES)
        for prefijo in (CALIBRACION, BENCHMARK, ROBUSTEZ):
            with self.subTest(panel=prefijo):
                self.assertGreater(posicion(prefijo), ultima_evolucion)
                self.assertLess(posicion(prefijo), posicion(DETALLE_CALIDAD))
        self.assertLess(posicion(CALIBRACION), posicion(BENCHMARK))
        self.assertLess(posicion(BENCHMARK), posicion(ROBUSTEZ))

    def test_el_resumen_y_el_como_leer_abren_la_seccion_tras_el_rotulo(self):
        # Los dos primeros puestos de la sección (sin fijar cuál va antes: ver la nota del módulo).
        self.assertEqual({t for t in titulos_a()[:2]}, {R.por_titulo(RESUMEN, "A")["title"], R.por_titulo(COMO_LEER_A, "A")["title"]})

    def test_toda_la_seccion_a_queda_antes_de_la_fila_de_la_seccion_b(self):
        # Reordenar no puede sacar un panel de la sección A: el último acaba como mucho donde empieza la fila de B, y
        # ningún panel de A queda por debajo de ella.
        fila_b = fila_de("B")["gridPos"]["y"]
        for panel in seccion_a():
            with self.subTest(panel=panel["title"]):
                self.assertLessEqual(panel["gridPos"]["y"] + panel["gridPos"]["h"], fila_b)


class ColocacionSinHuecosNiSolapesTests(unittest.TestCase):
    def test_cada_panel_empieza_donde_termina_el_anterior_sin_huecos_ni_solapes(self):
        # Caso: al mover paneles hay que reflujar las `y`. Por líneas de lectura (mismo `y`): la primera empieza justo
        # debajo del rótulo de la sección, cada línea empieza donde acaba la más alta de la anterior (hueco 0) y la
        # sección termina donde empieza la fila de B.
        paneles = seccion_a()
        fila_a = fila_de("A")["gridPos"]
        lineas = sorted({p["gridPos"]["y"] for p in paneles})
        esperado = fila_a["y"] + fila_a["h"]
        for y in lineas:
            with self.subTest(linea=y):
                self.assertEqual(y, esperado, f"hueco o solape vertical: la línea empieza en {y} y debía empezar en {esperado}")
            esperado = max(p["gridPos"]["y"] + p["gridPos"]["h"] for p in paneles if p["gridPos"]["y"] == y)
        self.assertEqual(esperado, fila_de("B")["gridPos"]["y"], "entre el último panel de A y la fila de B no debe haber hueco")

    def test_los_paneles_de_una_misma_linea_tienen_el_mismo_alto(self):
        # Las dos evoluciones que comparten fila miden lo mismo: si no, la línea siguiente dejaría un hueco bajo la menor.
        por_linea = {}
        for p in seccion_a():
            por_linea.setdefault(p["gridPos"]["y"], set()).add(p["gridPos"]["h"])
        for y, altos in por_linea.items():
            with self.subTest(linea=y):
                self.assertEqual(len(altos), 1, f"alturas distintas en la línea {y}: {altos}")

    def test_ningun_panel_de_la_seccion_a_se_solapa_con_otro(self):
        # Mismo criterio que la prueba congelada de estructura (rectángulos que se cortan en horizontal y en vertical),
        # restringido a la sección A, que es la que se reordena.
        paneles = seccion_a()
        for i, a in enumerate(paneles):
            for b in paneles[i + 1:]:
                pa, pb = a["gridPos"], b["gridPos"]
                solapan = (pa["x"] < pb["x"] + pb["w"] and pb["x"] < pa["x"] + pa["w"]
                           and pa["y"] < pb["y"] + pb["h"] and pb["y"] < pa["y"] + pa["h"])
                with self.subTest(a=a["title"], b=b["title"]):
                    self.assertFalse(solapan, (pa, pb))

    def test_la_lista_de_paneles_sigue_el_mismo_orden_que_las_posiciones(self):
        # Caso: Grafana recoloca según `gridPos`, pero la revisión del JSON no, y una prueba congelada exige que la lista sea
        # el orden de lectura. Se comprueba para TODO el dashboard: la lista coincide con (y, x) ordenado, así que mover
        # un panel en `gridPos` sin moverlo en la lista (o al revés) rompe esto.
        lista = [p["title"] for p in R.paneles()]
        por_posicion = [p["title"] for p in sorted(R.paneles(), key=lambda p: (p["gridPos"]["y"], p["gridPos"]["x"]))]
        self.assertEqual(lista, por_posicion)

    def test_los_titulos_de_la_seccion_a_en_la_lista_siguen_el_orden_esperado(self):
        # La misma secuencia de tramos, leída ahora en el orden de la LISTA (no de `gridPos`): protege el JSON tal cual se
        # revisa en la PR. Dentro de un tramo con varios paneles el orden no se fija.
        en_lista = [p["title"] for p in R.paneles() if p.get("type") != "row" and R.seccion_de(p) == "A"]
        inicio = 0
        for tramo in TRAMOS:
            reales = en_lista[inicio:inicio + len(tramo)]
            with self.subTest(esperado=sorted(tramo)):
                for prefijo in tramo:
                    self.assertEqual(len([t for t in reales if t.startswith(prefijo)]), 1, reales)
            inicio += len(tramo)


class TablasDeDetalleSiguenSiendoLasDeLaConciliacionTests(unittest.TestCase):
    """Mover las tablas «(detalle)» no cambia sus consultas: devuelven las mismas filas que antes de reordenar."""

    @classmethod
    def setUpClass(cls):
        R.por_titulo(DETALLE_CALIDAD, "A")  # sin los paneles falla antes de arrancar Docker
        R.por_titulo(DETALLE_CAMPANA, "A")

    def filas_en_la_base(self, familias) -> list:
        lista = ", ".join(f"'{f}'" for f in familias)
        return R.administrar("SELECT run_id, metric_id, behavior, status FROM evaluation.results x"
                             f" JOIN evaluation.runs USING (run_id) WHERE x.grp IN ({lista})")

    def comprobar(self, titulo, familias, esperadas):
        datos = R.ejecutar(R.consulta_unica(R.por_titulo(titulo, "A")))
        # Las columnas que lee la conciliación con los informes siguen ahí.
        for columna in ("run_id", "metric_id", "behavior", "status", "value", "numerator", "denominator", "unit"):
            self.assertIn(columna, R.nombres(datos), f"{titulo}: falta la columna {columna}")
        en_la_base = self.filas_en_la_base(familias)
        # Una fila por resultado de sus familias: el recuento sale de la base, no de la consulta del panel.
        self.assertEqual(len(datos["filas"]), len(en_la_base), titulo)
        self.assertEqual(sorted((f["run_id"], f["metric_id"], f["behavior"], f["status"]) for f in datos["filas"]),
                         sorted((f["run_id"], f["metric_id"], f["behavior"], f["status"]) for f in en_la_base), titulo)
        # Y los recuentos conocidos del manifiesto versionado (dos campañas de JUP-070).
        self.assertEqual(len(datos["filas"]), esperadas, titulo)

    def test_exactitud_relevancia_y_fundamento_devuelve_32_filas(self):
        self.comprobar(DETALLE_CALIDAD, ("accuracy", "relevance", "grounding"), 32)

    def test_latencia_formato_y_disponibilidad_devuelve_56_filas(self):
        self.comprobar(DETALLE_CAMPANA, ("latency", "robustness", "availability"), 56)


# --- D6: títulos de la sección C ---------------------------------------------------------------------------------------

LIMITE_TITULO = 40
TITULO_CONSULTAS = "Consultas al asistente por minuto"
TITULO_P95 = "Latencia p95, todas las rutas"
TITULO_ERROR = "Tasa de error del backend"
TITULOS_PROPORCIONES = ("Búsquedas sin contexto sobre consultas terminadas", "Fallos de recuperación sobre consultas terminadas")


def un_tercio(fragmento_de_expresion: str) -> dict:
    """El ÚNICO panel de C de un tercio de ancho (`w == 8`) cuya expresión contiene `fragmento_de_expresion`.

    Se localiza por lo que consulta, no por el título (que es lo que cambia) ni por el `id`. Se exige `w == 8` porque las dos
    proporciones (`w == 12`) también leen `backend_assistant_queries_total` en su denominador.
    """
    candidatos = [p for p in R.de_seccion("C") if p["gridPos"]["w"] == 8
                  and any(fragmento_de_expresion in t.get("expr", "") for t in p.get("targets", []))]
    if len(candidatos) != 1:
        raise AssertionError(f"se esperaba un único panel de un tercio con {fragmento_de_expresion!r} y hay {len(candidatos)}")
    return candidatos[0]


def consultas():
    return un_tercio("backend_assistant_queries_total")


def p95():
    return un_tercio("backend_http_request_duration_seconds")


def error():
    return un_tercio('status_code=~"5.."')


def minusculas_sin_tildes(texto: str) -> str:
    return R.sin_acentos(texto).lower()


class TitulosDeLaSeccionCTests(unittest.TestCase):
    def test_la_seccion_c_tiene_exactamente_tres_paneles_de_un_tercio(self):
        # Base de las demás pruebas: los tres de Prometheus de `w == 8` (consultas, p95 y error), nada más con ese ancho.
        tercios = [p for p in R.de_seccion("C") if p["gridPos"]["w"] == 8]
        self.assertEqual(len(tercios), 3, [p["title"] for p in tercios])
        self.assertEqual({p["title"] for p in tercios}, {consultas()["title"], p95()["title"], error()["title"]})

    def test_los_titulos_de_un_tercio_no_pasan_de_40_caracteres(self):
        # Caso (hallazgo de Lucia): en un panel de 8 unidades de ancho un título más largo se corta con puntos suspensivos y
        # no se lee entero. Frontera: 40 caben, 41 no. Se mide el título completo, con espacios y signos.
        for panel in (consultas(), p95(), error()):
            with self.subTest(titulo=panel["title"]):
                self.assertLessEqual(len(panel["title"]), LIMITE_TITULO, f"{len(panel['title'])} caracteres: {panel['title']!r}")

    def test_los_titulos_exactos_de_los_tres_paneles(self):
        # Los títulos que fija la decisión D6 (cada uno por la expresión de su panel, así un título no puede ir a otro).
        self.assertEqual(consultas()["title"], TITULO_CONSULTAS)
        self.assertEqual(p95()["title"], TITULO_P95)
        self.assertEqual(error()["title"], TITULO_ERROR)

    def test_el_titulo_de_la_latencia_conserva_todas_las_rutas(self):
        # Escenario «Título de la latencia»: 40 caracteres o menos Y dice «todas las rutas» (aclara que es el agregado de
        # todo el backend y no la latencia del asistente). Acortar el título no debe perder ese alcance.
        titulo = p95()["title"]
        self.assertIn("todas las rutas", titulo)
        self.assertLessEqual(len(titulo), LIMITE_TITULO)

    def test_los_dos_paneles_de_proporciones_conservan_su_titulo(self):
        # No regresión: los de la mitad del ancho (`w == 12`) caben y no se tocan.
        anchos_12 = [p for p in R.de_seccion("C") if p["gridPos"]["w"] == 12]
        self.assertEqual(sorted(p["title"] for p in anchos_12), sorted(TITULOS_PROPORCIONES))


class AlcanceEnLaDescripcionDeLaSeccionCTests(unittest.TestCase):
    def test_cada_descripcion_conserva_trafico_real(self):
        # Caso: el título ya no puede llevar «(tráfico real)», pero los paneles siguen mostrando tráfico real del backend y
        # el lector debe poder saberlo: pasa a la descripción (el ⓘ de cada panel). Se compara sin tildes ni mayúsculas.
        for panel in (consultas(), p95(), error()):
            with self.subTest(panel=panel["title"]):
                self.assertIn("trafico real", minusculas_sin_tildes(panel.get("description", "")))

    def test_la_descripcion_de_la_latencia_dice_que_no_es_la_latencia_de_las_consultas_al_asistente(self):
        # El alcance que se saca del título: agrega todas las rutas y NO es la latencia de las consultas al asistente.
        descripcion = minusculas_sin_tildes(R.plano(p95().get("description", "")))
        self.assertIn("no es la latencia de las consultas al asistente", descripcion)

    def test_el_texto_de_la_seccion_c_sigue_diciendo_que_los_paneles_muestran_trafico_real(self):
        # La sección en conjunto lo dice en su texto «Cómo leer la sección C» o en el título de su fila (cualquiera de los
        # dos vale: no se fija dónde, sino que no se pierda al acortar los títulos).
        texto = R.por_titulo("Cómo leer la sección C", "C").get("options", {}).get("content", "")
        rotulo = fila_de("C")["title"]
        self.assertIn("trafico real", minusculas_sin_tildes(texto + "\n" + rotulo))


# --- D7: fecha de la cabecera de la matriz -----------------------------------------------------------------------------


def panel_matriz() -> dict:
    return R.por_titulo(MATRIZ, "A")


# Hora local de la sesión distinta de UTC (+12/+13 h): una consulta que formatee `run_at` sin `AT TIME ZONE 'UTC'` mostraría
# otra hora y, en las ejecuciones cerca de medianoche, otro día e incluso otro año.
SESION_NO_UTC = "SET LOCAL TIME ZONE 'Pacific/Auckland';\n"

CABECERAS_VERSIONADAS = ["2026-10-08 20:13 · no real: plantilla, doble", "2026-10-08 21:01 · no real: plantilla"]


def cabeceras(preparacion: str) -> list:
    """Cabeceras de columna (la columna `ejecucion` de la consulta), sin repetir y en el orden de columnas de la matriz.

    `groupingToMatrix` crea las columnas por primera aparición del valor de `ejecucion`; como la consulta cruza cada métrica
    con cada ejecución, el orden de primera aparición es el de las columnas.
    """
    datos = R.ejecutar(R.consulta_unica(panel_matriz()), preparacion)
    resultado = []
    for fila in datos["filas"]:
        if fila["ejecucion"] not in resultado:
            resultado.append(fila["ejecucion"])
    return resultado


class CabeceraDeLaMatrizEstaticaTests(unittest.TestCase):
    def test_el_sql_formatea_la_fecha_con_aaaa_mm_dd_en_utc(self):
        # La cabecera se formatea en la propia consulta: `to_char(<run_at> AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI')`. Sin
        # `AT TIME ZONE 'UTC'` la hora dependería de la zona de la sesión (las ejecuciones se registran en UTC).
        sql = R.plano(R.consulta_unica(panel_matriz()))
        self.assertRegex(sql, r"to_char\(\s*\w+\.run_at\s+AT\s+TIME\s+ZONE\s+'UTC'\s*,\s*'YYYY-MM-DD HH24:MI'\s*\)")

    def test_no_queda_ningun_dd_mm_hh24_mi_en_la_consulta(self):
        # El formato antiguo `DD-MM HH24:MI` es el defecto (se lee como mes y día). `YYYY-MM-DD HH24:MI` no lo contiene
        # (acaba en «MM-DD»), así que basta buscar el orden día-mes pegado a la hora.
        self.assertNotRegex(R.consulta_unica(panel_matriz()), r"(?<![A-Za-z])DD-MM\b")
        self.assertNotRegex(R.consulta_unica(panel_matriz()), r"(?<![A-Za-z])DD-MM HH24:MI")

    def test_las_ejecuciones_sin_fecha_conservan_su_formato_en_la_consulta(self):
        # No regresión: la cabecera de las ejecuciones sin fecha sigue siendo `sin fecha · <run_id>` (el formato no cambia).
        self.assertRegex(R.plano(R.consulta_unica(panel_matriz())), r"'sin fecha · ' \|\| \w+\.run_id")


class CabeceraDeLaMatrizContraPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel_matriz()  # sin el panel falla antes de arrancar Docker

    def test_las_dos_campanas_versionadas_llevan_la_fecha_iso_en_utc(self):
        # Caso principal del requisito: las dos campañas del manifiesto, del 8 de octubre de 2026 a las 20:13 y 21:01 UTC,
        # con su tipo («no real: plantilla, doble» / «no real: plantilla») tras el separador « · ».
        self.assertEqual(cabeceras(""), CABECERAS_VERSIONADAS)

    def test_la_hora_no_depende_de_la_zona_de_la_sesion(self):
        # Caso: la sesión de Grafana puede no estar en UTC. Con la zona forzada a Auckland (+13 h) las cabeceras siguen
        # siendo las UTC: mata la consulta que formatea en hora local.
        self.assertEqual(cabeceras(SESION_NO_UTC), CABECERAS_VERSIONADAS)

    def test_ejecuciones_de_otro_dia_de_fin_de_ano_y_del_ano_siguiente_salen_con_su_ano_y_su_hora_utc(self):
        # Edge cases de la fecha, insertadas a propósito en desorden y con la sesión fuera de UTC:
        #   fd-1  14-oct-2026 09:30 (otro día);
        #   fd-2  31-dic-2026 23:59 (en Auckland ya sería 2027-01-01: el año solo sale bien si se formatea en UTC);
        #   fd-3  14-oct-2027 09:30 (mismo día y mes que fd-1: con `DD-MM` las dos columnas tendrían LA MISMA cabecera);
        #   fd-5  03-feb-2027 04:05 (día, mes y hora de un dígito: se rellenan con cero);
        #   fd-4  sin fecha (al final, con su identificador).
        preparacion = SESION_NO_UTC
        for run_id, run_at, real, motivos in (
                ("fd-3", "2027-10-14T09:30:00Z", True, ()),
                ("fd-4", None, False, ("sintetica",)),
                ("fd-1", "2026-10-14T09:30:00Z", True, ()),
                ("fd-5", "2027-02-03T04:05:00Z", False, ("doble",)),
                ("fd-2", "2026-12-31T23:59:00Z", True, ())):
            preparacion += R.insertar_ejecucion(run_id, "JUP-070", run_at, real=real, motivos=motivos)
            preparacion += R.insertar_resultado(run_id, "accuracy", "ACC-1", valor=0.5)
        self.assertEqual(cabeceras(preparacion), CABECERAS_VERSIONADAS + [
            "2026-10-14 09:30 · real",
            "2026-12-31 23:59 · real",
            "2027-02-03 04:05 · no real: doble",
            "2027-10-14 09:30 · real",
            "sin fecha · fd-4 · no real: sintetica",
        ])
        # Ninguna cabecera se repite: con el formato antiguo fd-1 y fd-3 serían la misma columna y la matriz las fundiría.
        datos = R.ejecutar(R.consulta_unica(panel_matriz()), preparacion)
        una_metrica = [f for f in datos["filas"] if f["metrica"] == "ACC-1 · Casos con resultado pass · todas"]
        self.assertEqual(len(una_metrica), 7)
        self.assertEqual(len({f["ejecucion"] for f in una_metrica}), 7, "dos ejecuciones comparten cabecera")

    def test_las_ejecuciones_sin_fecha_siguen_al_final_con_su_cabecera(self):
        # Formato que NO cambia: `sin fecha · <run_id> · <tipo>`, al final y por identificador aunque se inserten al revés.
        preparacion = ""
        for run_id in ("sf-b", "sf-a"):
            preparacion += R.insertar_ejecucion(run_id, "JUP-070", None, real=False, motivos=("sintetica",))
            preparacion += R.insertar_resultado(run_id, "accuracy", "ACC-1", valor=0.5)
        self.assertEqual(cabeceras(preparacion), CABECERAS_VERSIONADAS + [
            "sin fecha · sf-a · no real: sintetica",
            "sin fecha · sf-b · no real: sintetica",
        ])


if __name__ == "__main__":
    unittest.main()
