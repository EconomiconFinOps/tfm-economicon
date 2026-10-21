"""Configuración y textos de los paneles nuevos o corregidos: casos añadidos tras la fase de mutación (JUP-121, change
`jup-121-lectura-dashboard`).

Complementa a las demás pruebas `test_evaluation_readability_*.py` (commiteadas, no se tocan). Es un módulo ESTÁTICO (sin
Docker): lee el JSON y fija lo que la lectura del dashboard promete y que los mutantes supervivientes demostraron sin
protección. Lo que se fija y por qué importa:

* Los TEXTOS de «Cómo leer la sección A / B / C»: las pruebas originales solo comprobaban el número de viñetas, la tabla y la
  altura máxima, así que se podía borrar la viñeta de «No medido no es 0 %», la de ejecuciones «no real», la de la
  evolución, la de unidades de la sección B o el aviso de que la proporción de búsquedas sin contexto es un límite inferior
  y nadie lo notaba. Aquí se exigen las frases clave de cada texto (comparadas sin tildes, en minúsculas y con los espacios
  colapsados) y una altura mínima: un panel de tres filas corta el texto.
* Las DESCRIPCIONES (ⓘ) que contienen lo que cada panel no demuestra: qué significan «No medido» y «—» en la matriz, que el
  resumen mira si ya hay una campaña con modelo real, que la latencia de campaña no es la del tráfico real, que la
  latencia p95 de la sección C no es la del asistente, que no hay informe de robustez...
* El aviso `noValue` de cada panel: es lo único que ve quien abre el dashboard cuando no hay datos.
* La CONFIGURACIÓN de la matriz y del resumen: tabla alineada a la izquierda con cabecera, texto que envuelve, ancho de la
  columna «Métrica»; el resumen es una línea sin cabecera. Y la unidad de la latencia p95 (milisegundos, porque la
  expresión multiplica por 1000).

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_config.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

MATRIZ = ("Resultados por métrica y ejecución", "A")
RESUMEN = ("Resumen de la última campaña", "A")
LATENCIA = ("Evolución de la latencia de la campaña", "A")
CALIDAD = ("Exactitud, relevancia y fundamento", "A")
CAMPANA = ("Latencia, formato y disponibilidad de la campaña", "A")
ROBUSTEZ = ("Robustez", "A")
NEGOCIO = ("Tiempo, asignación y ahorro", "B")
# D6 (`jup-121-anotaciones-y-fuente`): los títulos de C miden <= 40 caracteres; «tráfico real» pasó a la descripción.
P95 = ("Latencia p95, todas las rutas", "C")
ERROR = ("Tasa de error del backend", "C")


def norm(texto: str) -> str:
    """Sin tildes, en minúsculas y con los espacios colapsados: las frases se buscan sin depender de la tipografía."""
    return R.plano(R.sin_acentos(texto).lower())


def panel_de(clave):
    return R.por_titulo(*clave)


def descripcion(clave) -> dict:
    tipo, mide, no_demuestra = panel_de(clave)["description"].split("\n")
    return {"tipo": tipo, "mide": norm(mide), "no_demuestra": norm(no_demuestra)}


class AvisosSinDatosTests(unittest.TestCase):
    def test_el_aviso_de_cada_panel_es_el_acordado(self):
        # Es lo único que ve quien abre el dashboard sin datos; cada uno dice qué falta y, cuando procede, cómo cargarlo.
        esperados = {
            MATRIZ: "Sin datos: todavía no se han cargado ejecuciones (evaluation-dashboard:load)",
            RESUMEN: "Sin datos: todavía no hay campañas de JUP-070",
            LATENCIA: "Sin datos: no hay con qué comparar",
            CALIDAD: "Sin datos: todavía no se han cargado ejecuciones (evaluation-dashboard:load)",
            CAMPANA: "Sin datos: todavía no se han cargado ejecuciones (evaluation-dashboard:load)",
            ROBUSTEZ: "Sin datos: todavía no hay informe de robustez de JUP-071",
            NEGOCIO: "Sin datos: todavía no hay registros de negocio de JUP-068",
            P95: "Sin datos: no hubo peticiones",
            ERROR: "Sin datos: no hubo peticiones",
        }
        for clave, aviso in esperados.items():
            with self.subTest(panel=clave[0]):
                self.assertEqual(R.defaults(panel_de(clave))["noValue"], aviso)


class ConfiguracionDeLaMatrizYDelResumenTests(unittest.TestCase):
    def test_la_matriz_es_una_tabla_con_cabecera_alineada_a_la_izquierda_y_texto_que_envuelve(self):
        panel = panel_de(MATRIZ)
        custom = R.defaults(panel)["custom"]
        self.assertTrue(panel["options"]["showHeader"], "sin cabecera no se sabe a qué ejecución pertenece cada columna")
        self.assertEqual(custom["align"], "left")
        self.assertEqual(custom["minWidth"], 280)
        self.assertTrue(custom["cellOptions"]["wrapText"])

    def test_la_primera_columna_de_la_matriz_es_ancha_para_nombres_largos(self):
        # «ACC-3 · Casos clarify y abstain con resultado pass · aclarar» no cabe en una columna estándar.
        propiedades = R.propiedades(panel_de(MATRIZ), "Métrica")
        self.assertEqual(propiedades.get("custom.width"), 380)
        self.assertEqual(propiedades.get("custom.minWidth"), 300)

    def test_el_resumen_es_una_linea_de_texto_sin_cabecera_que_envuelve(self):
        panel = panel_de(RESUMEN)
        self.assertFalse(panel["options"]["showHeader"], "una sola celda: la cabecera «resumen» sobra")
        self.assertTrue(R.defaults(panel)["custom"]["cellOptions"]["wrapText"])

    def test_la_latencia_p95_de_la_seccion_c_esta_en_milisegundos(self):
        # La expresión multiplica por 1000 (segundos -> ms): la unidad del eje debe decirlo.
        self.assertEqual(R.defaults(panel_de(P95))["unit"], "ms")


class DescripcionesTests(unittest.TestCase):
    def test_la_matriz_explica_que_no_medido_y_raya_no_son_cero(self):
        d = descripcion(MATRIZ)
        self.assertIn("una fila por metrica y variante", d["mide"])
        self.assertIn("una columna por ejecucion", d["mide"])
        self.assertIn("intervalo de confianza del 95 %", d["mide"])
        self.assertIn("«no medido» es que no se pudo medir", d["no_demuestra"])
        self.assertIn("«—» que esa ejecucion no trae la metrica", d["no_demuestra"])
        self.assertIn("ninguno de los dos es 0 %", d["no_demuestra"])

    def test_el_resumen_dice_que_mira_si_ya_hay_modelo_real(self):
        d = descripcion(RESUMEN)
        self.assertIn("casos aprobados sobre el total", d["mide"])
        self.assertIn("si ya existe alguna ejecucion de jup-070 con modelo real", d["mide"])

    def test_la_latencia_de_campana_dice_sus_series_y_que_no_es_trafico_real(self):
        d = descripcion(LATENCIA)
        for frase in ("lat-1", "lat-2", "milisegundos", "ejecuciones comparables"):
            self.assertIn(frase, d["mide"])
        self.assertIn("no la del trafico real", d["no_demuestra"])
        self.assertIn("una serie solo une ejecuciones comparables", d["no_demuestra"])

    def test_el_detalle_de_calidad_remite_a_la_matriz(self):
        self.assertIn("la lectura principal es la tabla «resultados por metrica y ejecucion»", descripcion(CALIDAD)["mide"])

    def test_la_robustez_dice_que_sin_informe_cargado_sale_vacia(self):
        self.assertIn("sin un informe de robustez cargado el panel sale vacio", descripcion(ROBUSTEZ)["no_demuestra"])

    def test_la_latencia_p95_dice_que_no_es_la_del_asistente_y_donde_esta_esa(self):
        mide = descripcion(P95)["mide"]
        self.assertIn("no es la latencia de las consultas al asistente", mide)
        self.assertIn("la de una campana esta en la seccion a", mide)


class AjusteDeTextoDeLaVarianteTests(unittest.TestCase):
    def test_la_columna_de_variante_envuelve_sus_nombres_largos(self):
        # «fallo del servicio externo», «límite de peticiones»... y las categorías y perturbaciones de robustez no caben
        # en una línea de 170 o 270 px: sin `wrapText` la celda queda cortada con puntos suspensivos.
        for clave, columna in ((CALIDAD, "variante"), (CAMPANA, "variante"), (ROBUSTEZ, "behavior")):
            with self.subTest(panel=clave[0], columna=columna):
                opciones = R.propiedades(panel_de(clave), columna).get("custom.cellOptions")
                self.assertEqual(opciones, {"type": "auto", "wrapText": True})


class UbicacionYAnchoTests(unittest.TestCase):
    """Los mutantes de posición solo los mataban las pruebas congeladas, que el diseño (D9) parchea: se repite aquí lo
    esencial de la lectura (qué va antes de qué y qué ocupa todo el ancho)."""

    def test_orden_de_lectura_de_la_seccion_a(self):
        # Resumen -> ejecuciones -> estado de casos -> matriz -> detalles: lo principal antes que el detalle por fila.
        ys = [panel_de(c)["gridPos"]["y"] for c in (RESUMEN, ("Ejecuciones cargadas", "A"), ("Estado de los casos", "A"),
                                                       MATRIZ, CALIDAD, CAMPANA)]
        self.assertEqual(ys, sorted(set(ys)), f"las tablas de A no siguen el orden de lectura esperado: {ys}")

    def test_las_tablas_anchas_ocupan_todo_el_ancho(self):
        for clave in (RESUMEN, MATRIZ, CALIDAD, CAMPANA):
            with self.subTest(panel=clave[0]):
                self.assertEqual((panel_de(clave)["gridPos"]["x"], panel_de(clave)["gridPos"]["w"]), (0, 24))

    def test_la_latencia_de_campana_comparte_fila_con_las_proporciones_y_cada_una_ocupa_media_pantalla(self):
        hermano = panel_de(("Evolución de las métricas automáticas", "A"))["gridPos"]
        propia = panel_de(LATENCIA)["gridPos"]
        self.assertEqual((hermano["x"], hermano["w"]), (0, 12))
        self.assertEqual((propia["x"], propia["w"], propia["y"], propia["h"]), (12, 12, hermano["y"], hermano["h"]))

    def test_la_matriz_traduce_un_nulo_a_no_medido(self):
        mapeos = R.defaults(panel_de(MATRIZ))["mappings"]
        nulos = [m["options"]["result"]["text"] for m in mapeos if m.get("type") == "special" and m["options"].get("match") == "null"]
        self.assertEqual(nulos, ["No medido"])


class SeccionCTests(unittest.TestCase):
    def test_la_latencia_p95_agrega_todas_las_rutas_en_milisegundos_sobre_cinco_minutos(self):
        expresion = R.plano(panel_de(P95)["targets"][0]["expr"])
        self.assertEqual(expresion, "1000 * histogram_quantile(0.95, sum(rate(backend_http_request_duration_seconds_bucket[5m])) by (le))")

    def test_los_dos_paneles_miran_la_ultima_hora_y_nombran_el_trafico_real(self):
        # Antes el título terminaba en «(tráfico real)»; con los títulos de 40 caracteres ese alcance vive en la línea
        # «Mide:» de la descripción (el ⓘ) y en el texto «Cómo leer la sección C». Se exige ahí, y que el título sea el
        # exacto, quepa en un tercio de ancho y ya no arrastre el rótulo.
        texto_c = norm(R.por_titulo("Cómo leer la sección C", "C")["options"]["content"])
        self.assertIn("trafico real", texto_c)
        for clave in (P95, ERROR):
            with self.subTest(panel=clave[0]):
                titulo = panel_de(clave)["title"]
                self.assertEqual(panel_de(clave).get("timeFrom"), "1h")
                self.assertEqual(titulo, clave[0])
                self.assertLessEqual(len(titulo), 40)
                self.assertNotIn("trafico real", norm(titulo))
                self.assertIn("trafico real", descripcion(clave)["mide"])

    def test_la_tasa_de_error_dice_que_solo_detecta_sintomas(self):
        self.assertIn("solo detecta sintomas", descripcion(ERROR)["no_demuestra"])


FRASES = {
    "A": (
        # Viñeta de ejecuciones «no real».
        "ejecuciones «no real»", "se rotulan `no real` con su motivo", "series se dibujan discontinuas",
        # Viñeta de «No medido».
        "«no medido» no es 0 %", "«—» indica que esa ejecucion no la tiene", "un 0 % que se ve es un cero medido",
        # Viñeta de la evolución.
        "al menos dos puntos medidos de ejecuciones comparables", "«sin datos: no hay con que comparar»",
        # Tabla: de dónde salen los datos.
        "jup-070", "jup-069", "jup-067", "jup-022", "jup-078", "jup-071",
    ),
    "B": (
        "hoy el registro es un ejemplo sintetico", "`sintetica`", "no real",
        "ahorro realizado: «no medido»", "no es 0 €", "no se mide",
        "los tiempos se muestran en minutos y los importes en euros", "milisegundos y centimos",
        "un denominador de parejas es un recuento, no un tiempo", "jup-068",
    ),
    "C": (
        "son sintomas, no calidad", "la calidad esta en la seccion a", "proporciones sobre consultas terminadas",
        "es un limite inferior", "«sin datos» en vez de 0 %", "estos paneles muestran siempre la ultima hora",
        "[dashboard de metricas tecnicas](/d/economicon-technical-metrics)",
    ),
}


class TextosDeLasSeccionesTests(unittest.TestCase):
    def test_cada_texto_conserva_sus_frases_clave(self):
        for seccion, frases in FRASES.items():
            contenido = norm(R.por_titulo(f"Cómo leer la sección {seccion}", seccion)["options"]["content"])
            for frase in frases:
                with self.subTest(seccion=seccion, frase=frase):
                    self.assertIn(frase, contenido)

    def test_cada_texto_tiene_al_menos_cinco_filas_de_alto(self):
        # Una tabla de tres líneas (cabecera, separador y fila) más una viñeta no caben en menos de cinco filas de la
        # cuadrícula: con tres, Grafana corta el texto y hay que hacer scroll dentro del panel.
        for seccion in "ABC":
            with self.subTest(seccion=seccion):
                self.assertGreaterEqual(R.por_titulo(f"Cómo leer la sección {seccion}", seccion)["gridPos"]["h"], 5)


if __name__ == "__main__":
    unittest.main()
