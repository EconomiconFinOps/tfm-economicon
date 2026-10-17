"""Ajustes visuales del dashboard hallados con Grafana 11.3.0 real (JUP-121, change `jup-121-lectura-dashboard`, tarea 3.5, Red).

Requisito que fija este módulo (decisión D10 del diseño). Las capturas con Edge headless a 1440 y 1600 px mostraron:

* la matriz «Resultados por métrica y ejecución» (44 filas tras pivotar) ocupaba 36 unidades de alto y ocultaba 13 filas tras
  un scroll: su alto mínimo es «filas + 6 unidades» (cabecera y margen), calculado con la consulta REAL contra el manifiesto
  versionado y no copiado como un número;
* «Estado de los casos por ejecución» (5 unidades) cortaba la tercera ejecución y «Ejecuciones cargadas» (8) no llegaba a
  seis: se dimensionan para al menos 6 ejecuciones con su cabecera (h >= 10 y h >= 8 respectivamente);
* las horas de las tablas salían en la zona del navegador y las de la cabecera de la matriz en UTC: las ejecuciones se
  registran en UTC, así que el dashboard declara `"timezone": "utc"` y un texto visible lo dice;
* la cabecera «Tipo de ejecución» (17 caracteres) se truncaba en calibración y benchmark con 110 px: la columna `estado`
  de esas dos tablas fija al menos 170 px, y en las demás tablas donde se ve no queda por debajo de 140 px;
* la columna «Detalle» de la sección B mostraba `all`, `candidate`, `estimated`, `not_evaluable` en inglés: se traduce con
  una columna `variante` («Variante») igual que en las tablas de detalle, y `behavior` queda en la consulta (la
  conciliación con el informe de JUP-068 lo lee) pero oculto.

Los paneles se localizan por título, no por `id` ni posición. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_layout.py`
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

MATRIZ = ("Resultados por métrica y ejecución", "A")
EJECUCIONES = ("Ejecuciones cargadas", "A")
ESTADOS = ("Estado de los casos por ejecución", "A")
CALIBRACION = ("Calibración de la recuperación", "A")
BENCHMARK = ("Benchmark de modelos", "A")
NEGOCIO = ("Tiempo, asignación y ahorro", "B")
TEXTO_A = ("Cómo leer la sección A", "A")
INFORME_JUP068 = R.ROOT / "docs" / "validation" / "JUP-068-example.json"

# Márgenes de la decisión D10.
FILAS_EXTRA_DE_LA_MATRIZ = 6
ALTO_MINIMO_EJECUCIONES = 10
ALTO_MINIMO_ESTADOS = 8
ANCHO_MINIMO_TIPO_DE_EJECUCION = 170
ANCHO_MINIMO_RESTO = 140

# Traducción fijada por D10 (sin tildes y en minúsculas: se compara normalizando acentos).
VARIANTES_B = {"all": "todos", "candidate": "candidatas", "estimated": "estimadas", "not_evaluable": "no evaluables"}


def panel_de(clave):
    return R.por_titulo(*clave)


def tablas_con_estado() -> list:
    """Tablas de A y B cuya consulta devuelve la columna `estado` (tipo de ejecución) y que la muestran."""
    return [p for letra in "AB" for p in R.de_seccion(letra)
            if p["type"] == "table" and re.search(r"(?i)\bAS\s+estado\b", R.sql_de(p)) and not R.oculta(p, "estado")]


# --- Altura de las tablas ----------------------------------------------------------------------------------------------


class AlturaDeLasTablasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel_de(MATRIZ)  # sin el panel falla antes de arrancar Docker
        cls.datos = R.ejecutar(R.consulta_unica(panel_de(MATRIZ)))

    def test_la_matriz_muestra_todas_sus_filas_mas_seis_unidades(self):
        # Caso: a Grafana le llegan las filas de la consulta y `groupingToMatrix` las pivota a UNA fila por `metrica`
        # (el `rowField` de la transformación). Cada fila ocupa ~1 unidad de alto: con 36 unidades las últimas 13 de 44
        # quedaban tras un scroll y parecía que no existían. El mínimo se calcula con el manifiesto versionado para que
        # una métrica nueva en el catálogo vuelva a exigir más alto en lugar de dejarlo anticuado.
        filas = {fila["metrica"] for fila in self.datos["filas"]}
        self.assertGreaterEqual(len(filas), 44, "el manifiesto versionado debe dar al menos las 44 filas vistas en Grafana")
        alto = panel_de(MATRIZ)["gridPos"]["h"]
        self.assertGreaterEqual(alto, len(filas) + FILAS_EXTRA_DE_LA_MATRIZ,
                                f"la matriz tiene {len(filas)} filas y mide {alto} unidades: se ocultan tras un scroll")

    def test_la_tabla_de_ejecuciones_cabe_seis_ejecuciones_con_su_cabecera(self):
        alto = panel_de(EJECUCIONES)["gridPos"]["h"]
        self.assertGreaterEqual(alto, ALTO_MINIMO_EJECUCIONES, f"«Ejecuciones cargadas» mide {alto} unidades")

    def test_la_tabla_de_estado_de_los_casos_cabe_seis_ejecuciones_con_su_cabecera(self):
        # Caso: con 5 unidades Grafana cortaba la tercera ejecución. Una fila por ejecución de JUP-070 + cabecera.
        alto = panel_de(ESTADOS)["gridPos"]["h"]
        self.assertGreaterEqual(alto, ALTO_MINIMO_ESTADOS, f"«Estado de los casos por ejecución» mide {alto} unidades")

    def test_agrandar_las_tablas_no_solapa_ningun_panel_con_otro(self):
        # Mismo criterio que la prueba congelada de estructura (rectángulos que se cortan en horizontal y vertical a la
        # vez), repetido aquí por si el parche de las pruebas congeladas la cambia: crecer en alto empuja lo de debajo.
        lista = R.paneles()
        for i, a in enumerate(lista):
            for b in lista[i + 1:]:
                pa, pb = a["gridPos"], b["gridPos"]
                solapan = (pa["x"] < pb["x"] + pb["w"] and pb["x"] < pa["x"] + pa["w"]
                           and pa["y"] < pb["y"] + pb["h"] and pb["y"] < pa["y"] + pa["h"])
                with self.subTest(a=a["title"], b=b["title"]):
                    self.assertFalse(solapan, (pa, pb))


# --- Zona horaria -----------------------------------------------------------------------------------------------------


class ZonaHorariaTests(unittest.TestCase):
    def test_el_dashboard_declara_la_zona_utc(self):
        # Las ejecuciones se registran en UTC y la cabecera de la matriz ya va en UTC: con «browser» las tablas
        # enseñaban otra hora para la MISMA ejecución según quién mirara.
        self.assertEqual(R.dashboard().get("timezone"), "utc")

    def test_un_texto_visible_dice_que_las_horas_estan_en_utc(self):
        # Declarar la zona no basta: quien lee debe poder saberlo. Vale la descripción del dashboard o el texto
        # «Cómo leer la sección A» (el que se ve sin abrir ningún ⓘ).
        descripcion = R.dashboard().get("description") or ""
        leer_a = panel_de(TEXTO_A).get("options", {}).get("content", "")
        self.assertRegex(descripcion + "\n" + leer_a, r"\bUTC\b",
                         "ni la descripción del dashboard ni «Cómo leer la sección A» dicen que las horas están en UTC")


# --- Cabecera «Tipo de ejecución» -------------------------------------------------------------------------------------


class AnchoDelTipoDeEjecucionTests(unittest.TestCase):
    def test_calibracion_y_benchmark_fijan_un_ancho_que_cabe_la_cabecera(self):
        # Caso: con 110 px la cabecera de 17 caracteres salía truncada. Debe haber un ancho FIJADO (no «sin ancho», que en
        # estas dos tablas ya se vio truncado) de al menos 170.
        for clave in (CALIBRACION, BENCHMARK):
            panel = panel_de(clave)
            with self.subTest(panel=panel["title"]):
                self.assertEqual(R.nombre_visible(panel, "estado"), "Tipo de ejecución")
                ancho = R.propiedades(panel, "estado").get("custom.width")
                self.assertIsNotNone(ancho, "la columna estado debe fijar `custom.width`")
                self.assertGreaterEqual(ancho, ANCHO_MINIMO_TIPO_DE_EJECUCION)

    def test_en_el_resto_de_tablas_la_columna_no_se_queda_corta(self):
        # Caso: ninguna otra tabla puede haber quedado por debajo de 140 px (se midió que cabe en las demás); sin ancho
        # fijado Grafana reparte el espacio y tampoco trunca.
        resto = [p for p in tablas_con_estado() if not p["title"].startswith((CALIBRACION[0], BENCHMARK[0]))]
        self.assertGreaterEqual(len(resto), 6, [p["title"] for p in resto])
        for panel in resto:
            with self.subTest(panel=panel["title"]):
                ancho = R.propiedades(panel, "estado").get("custom.width")
                if ancho is not None:
                    self.assertGreaterEqual(ancho, ANCHO_MINIMO_RESTO)


# --- Sección B: variantes en español ----------------------------------------------------------------------------------


class VariantesDeLaSeccionBEstaticoTests(unittest.TestCase):
    def test_la_columna_variante_se_ve_y_behavior_queda_oculta_igual_que_en_los_detalles(self):
        panel = panel_de(NEGOCIO)
        self.assertRegex(R.sql_de(panel), r"(?i)\bAS\s+variante\b")
        self.assertEqual(R.nombre_visible(panel, "variante"), "Variante")
        self.assertFalse(R.oculta(panel, "variante"), "la variante traducida debe verse")
        # `behavior` sigue en la consulta (se comprueba contra la base más abajo) pero ya no se ve en bruto.
        self.assertTrue(R.oculta(panel, "behavior"), "`behavior` en inglés no debe verse")


def recuentos_de_oportunidades_del_informe() -> dict:
    """Recuento original por estado del informe de JUP-068 (lo que la conciliación compara); 0 si el estado no aparece."""
    informe = json.loads(INFORME_JUP068.read_text(encoding="utf-8"))
    cuenta = Counter(oportunidad["status"] for oportunidad in informe["opportunities"])
    return {estado: cuenta.get(estado, 0) for estado in ("estimated", "candidate", "not_evaluable")}


class VariantesDeLaSeccionBContraPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel_de(NEGOCIO)
        cls.datos = R.ejecutar(R.consulta_unica(panel_de(NEGOCIO)))
        cls.recuentos = recuentos_de_oportunidades_del_informe()

    @property
    def filas(self):
        """Filas de la consulta; falla con un mensaje claro si falta `variante` (Red legible, no un KeyError)."""
        faltan = {"variante", "behavior", "metric_id", "status", "valor_texto"} - set(R.nombres(self.datos))
        self.assertFalse(faltan, f"la consulta de la tabla de negocio no devuelve las columnas {sorted(faltan)}")
        return self.datos["filas"]

    def fila(self, metrica, comportamiento):
        coincidencias = [f for f in self.filas if f["metric_id"] == metrica and f["behavior"] == comportamiento]
        self.assertEqual(len(coincidencias), 1, coincidencias)
        return coincidencias[0]

    def test_ninguna_columna_visible_se_llama_detalle_y_variante_ocupa_su_sitio(self):
        # La columna traducida sustituye a la antigua «Detalle»: justo después de «Medida». Se calcula con las columnas
        # REALES de la consulta y los overrides del panel (rótulo y `hidden`), como hace Grafana.
        visibles = R.columnas_visibles(panel_de(NEGOCIO), R.nombres(self.datos))
        self.assertNotIn("Detalle", visibles, "«Detalle» (el `behavior` en bruto) no debe quedar visible")
        self.assertIn("Variante", visibles, visibles)
        self.assertEqual(visibles[visibles.index("Medida") + 1], "Variante", visibles)

    def test_ninguna_celda_visible_de_variante_esta_en_ingles(self):
        # Caso: los cuatro valores crudos eran el defecto. Se busca como palabra completa (`\b`) en TODAS las filas; el
        # guion bajo cuenta como carácter de palabra, así que `not_evaluable` también se detecta entero.
        self.assertTrue(self.filas)
        for fila in self.filas:
            with self.subTest(metrica=fila["metric_id"], behavior=fila["behavior"]):
                self.assertIsInstance(fila["variante"], str)
                self.assertTrue(fila["variante"].strip())
                self.assertNotRegex(fila["variante"].lower(), r"\b(all|candidate|estimated|not_evaluable)\b")

    def test_cada_variante_se_traduce_a_su_texto_en_espanol(self):
        # Caso: la traducción exacta por valor crudo (se comparan sin tildes y en minúsculas, así que el dashboard puede
        # escribirlas bien). `all` ocupa la mayoría de las filas; las tres de oportunidades, el resto.
        vistos = {f["behavior"] for f in self.filas}
        self.assertEqual(vistos, set(VARIANTES_B), "el manifiesto versionado debe ejercitar las cuatro variantes")
        for fila in self.filas:
            with self.subTest(metrica=fila["metric_id"], behavior=fila["behavior"]):
                self.assertEqual(R.sin_acentos(fila["variante"]).lower(), VARIANTES_B[fila["behavior"]])

    def test_las_oportunidades_muestran_estimadas_candidatas_y_no_evaluables_con_su_recuento_del_informe(self):
        # Caso: una fila concreta de cada estado, con el recuento del informe original de JUP-068 (1, 1 y 0): la
        # traducción no puede mover el valor de fila ni intercambiar etiquetas entre estados.
        esperadas = {"estimated": "estimadas", "candidate": "candidatas", "not_evaluable": "no evaluables"}
        for comportamiento, texto in esperadas.items():
            fila = self.fila("opportunities", comportamiento)
            with self.subTest(estado=comportamiento):
                self.assertEqual(R.sin_acentos(fila["variante"]).lower(), texto)
                self.assertEqual(fila["valor_texto"], str(self.recuentos[comportamiento]))

    def test_behavior_sigue_en_la_consulta_con_los_valores_originales(self):
        # La conciliación con el informe lee `behavior`: debe seguir presente, en inglés y con las mismas filas que la base.
        # (No usa `self.filas`: esta comprobación es independiente de que la columna `variante` ya exista.)
        self.assertIn("behavior", R.nombres(self.datos))
        en_la_base = Counter(
            (f["metric_id"], f["behavior"], f["status"]) for f in R.administrar(
                "SELECT metric_id, behavior, status FROM evaluation.results WHERE measure_type = 'B'"))
        devueltas = Counter((f["metric_id"], f["behavior"], f["status"]) for f in self.datos["filas"])
        self.assertEqual(devueltas, en_la_base)


if __name__ == "__main__":
    unittest.main()
