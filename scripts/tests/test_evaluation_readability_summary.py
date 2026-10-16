"""Resumen de la última campaña, al principio de la sección A (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisito de la spec «Resumen de la última campaña» (decisión D4 del diseño). Quien entra al dashboard sin contexto ve
primero un texto de una sola línea con lo esencial de la última campaña de JUP-070: fecha, tipo de ejecución (real o no),
casos aprobados sobre el total y si TODAVÍA no hay una evaluación con modelo real. Es un panel de tipo tabla con una fila y
una columna de texto (`resumen`), por ejemplo:

    Última campaña: 08/10/2026 · no real (plantilla) · 0/28 casos aprobados · todavía no hay evaluación con modelo real

Reglas que fija este módulo (todas contra PostgreSQL real con el rol de lectura de Grafana):

* «Última» = la ejecución de JUP-070 con mayor `run_at`. Una ejecución sin fecha no puede ser la última (en PostgreSQL
  `ORDER BY run_at DESC` pondría los NULL primero: se prueba), ni cuentan otras fuentes (JUP-078 y JUP-022 son
  `is_real = true` en los datos versionados y no deben hacer desaparecer el aviso «todavía no hay evaluación con modelo real»).
* Con el manifiesto versionado (dos campañas de plantilla): una fila que dice «no real», «plantilla», «0/28» y «todavía no
  hay evaluación con modelo real». Es la segunda campaña (la de la fecha mayor), así que no menciona `doble`, motivo de la primera.
* Con una campaña real insertada (la última): dice «real», sus casos aprobados sobre el total y NO «todavía no hay
  evaluación con modelo real».
* Con una campaña real ANTIGUA y una no real posterior: el resumen es el de la posterior (no real), pero no afirma que
  todavía no haya evaluación real, porque la hay.
* Sin ejecuciones de JUP-070: cero filas (el `noValue` del panel dice «Sin datos: todavía no hay campañas de JUP-070»;
  nunca una campaña «0/0» inventada).
* Posición: es el PRIMER panel de la sección A tras su rótulo de fila (menor `gridPos.y` entre los paneles de la sección).

El panel se localiza por lo que consulta (una columna `resumen`), no por su `id` ni posición. Ruta del dashboard:
`EVALUATION_DASHBOARD_JSON`. Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_summary.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

SIN_CAMPANAS = "Sin datos: todavía no hay campañas de JUP-070"
SIN_REAL = "todavía no hay evaluación con modelo real"


def panel():
    candidatos = [p for p in R.de_seccion("A")
                  if p["type"] == "table" and re.search(r"(?i)\bAS\s+resumen\b", R.sql_de(p))]
    if len(candidatos) != 1:
        raise AssertionError(
            f"se esperaba un único panel de resumen (una columna `resumen`) en la sección A y hay {len(candidatos)}")
    return candidatos[0]


def resumenes(preparacion: str = "") -> list:
    """Textos de `resumen` que devuelve la consulta del panel sobre el escenario `preparacion`."""
    datos = R.ejecutar(R.consulta_unica(panel()), preparacion)
    return [fila["resumen"] for fila in datos["filas"]]


def campana(run_id, run_at, *, real, motivos=(), aprobados=0, total=28) -> str:
    """Una campaña de JUP-070 sintética con sus cuatro filas de estados de casos."""
    return (R.insertar_ejecucion(run_id, "JUP-070", run_at, real=real, motivos=motivos)
            + R.insertar_casos(run_id, aprobados, total))


class EstructuraTests(unittest.TestCase):
    def test_es_una_tabla_tipo_a_de_postgres_con_formato_tabla(self):
        p = panel()
        self.assertEqual(p["type"], "table")
        self.assertEqual(p["datasource"], R.DS_POSTGRES)
        self.assertTrue(p["description"].startswith("Tipo: A"))
        objetivo = p["targets"][0]
        self.assertEqual(len(p["targets"]), 1)
        self.assertEqual(objetivo["format"], "table")
        self.assertIs(objetivo["rawQuery"], True)
        self.assertEqual(objetivo["editorMode"], "code")

    def test_se_titula_resumen_de_la_ultima_campana(self):
        self.assertTrue(panel()["title"].startswith("Resumen de la última campaña"), panel()["title"])

    def test_sin_campanas_el_aviso_dice_sin_datos_de_jup_070(self):
        self.assertEqual(R.defaults(panel()).get("noValue"), SIN_CAMPANAS)

    def test_es_el_primer_panel_de_la_seccion_a_tras_el_rotulo(self):
        # El resumen va ARRIBA, antes del texto «Cómo leer»: menor `gridPos.y` de toda la sección y sin empate, para que
        # no dependa del orden de la lista ni de la posición horizontal.
        resumen = panel()
        otros = [p for p in R.de_seccion("A") if p is not resumen]
        self.assertTrue(otros)
        for otro in otros:
            with self.subTest(otro=otro["title"]):
                self.assertLess(resumen["gridPos"]["y"], otro["gridPos"]["y"])
        fila_a = [f for f in R.filas() if f["title"].startswith("A · ")][0]
        self.assertGreater(resumen["gridPos"]["y"], fila_a["gridPos"]["y"])

    def test_la_consulta_solo_mira_jup_070(self):
        self.assertRegex(R.sql_de(panel()), r"'JUP-070'")


class ConManifiestoVersionadoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel()  # sin el panel nuevo falla antes de arrancar Docker (Red)
        cls.datos = R.ejecutar(R.consulta_unica(panel()))

    def test_una_sola_fila_con_una_columna_de_texto_llamada_resumen(self):
        self.assertEqual(R.nombres(self.datos), ["resumen"])
        self.assertIn(dict(self.datos["columnas"])["resumen"], ("text", "character varying"))
        self.assertEqual(len(self.datos["filas"]), 1)

    def test_dice_no_real_plantilla_0_de_28_y_que_todavia_no_hay_modelo_real(self):
        texto = self.datos["filas"][0]["resumen"]
        self.assertRegex(texto, r"(?i)última campaña")
        self.assertIn("no real", texto)
        self.assertIn("plantilla", texto)
        self.assertIn("0/28", texto)
        self.assertIn(SIN_REAL, texto)

    def test_es_la_campana_mas_reciente_con_su_fecha(self):
        # La segunda campaña es del 08/10/2026 21:01 UTC y solo es de plantilla; la primera (20:13) añadía `doble`.
        texto = self.datos["filas"][0]["resumen"]
        self.assertRegex(texto, r"08/10/2026|08-10-2026|2026-10-08")
        self.assertNotRegex(texto, r"\bdoble\b")

    def test_una_sola_linea_legible(self):
        texto = self.datos["filas"][0]["resumen"]
        self.assertNotIn("\n", texto)
        self.assertLess(len(texto), 250)

    def test_los_benchmarks_y_la_calibracion_reales_no_apagan_el_aviso(self):
        # Los datos versionados traen JUP-078 y JUP-022 con `is_real = true`: no son campañas de JUP-070 y el aviso
        # «todavía no hay evaluación con modelo real» sigue valiendo.
        reales = R.administrar("SELECT source FROM evaluation.runs WHERE is_real ORDER BY source")
        self.assertTrue(reales, "el escenario supone ejecuciones reales de otras fuentes")
        self.assertNotIn("JUP-070", {f["source"] for f in reales})
        self.assertIn(SIN_REAL, self.datos["filas"][0]["resumen"])


class EscenariosSinteticosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel()

    def una_fila(self, preparacion: str) -> str:
        textos = resumenes(preparacion)
        self.assertEqual(len(textos), 1, textos)
        return textos[0]

    def test_con_una_campana_real_posterior_dice_real_y_no_el_aviso(self):
        texto = self.una_fila(campana("rs-real", "2026-10-14T09:00:00Z", real=True, aprobados=20, total=28))
        self.assertRegex(texto, r"\breal\b")
        self.assertNotIn("no real", texto)
        self.assertNotIn(SIN_REAL, texto)
        self.assertIn("20/28", texto)
        self.assertRegex(texto, r"14/10/2026|14-10-2026|2026-10-14")

    def test_una_campana_real_antigua_no_se_presenta_como_la_ultima_ni_apaga_la_realidad(self):
        # Real el 1/10 y no real (plantilla) el 8/10: la última es la no real y el resumen lo dice; pero ya existe una
        # evaluación real, así que no puede afirmar que «todavía no hay» una.
        texto = self.una_fila(campana("rs-vieja", "2026-10-01T09:00:00Z", real=True, aprobados=20, total=28))
        self.assertIn("no real", texto)
        self.assertIn("0/28", texto)
        self.assertNotIn("20/28", texto)
        self.assertNotIn(SIN_REAL, texto)

    def test_la_ultima_se_elige_por_fecha_y_no_por_el_orden_de_los_identificadores(self):
        # Identificador alfabéticamente POSTERIOR pero fecha ANTERIOR: debe ganar la de fecha mayor.
        texto = self.una_fila(campana("zzz-anterior", "2026-10-02T09:00:00Z", real=True, aprobados=7, total=28))
        self.assertNotIn("7/28", texto)
        texto = self.una_fila(campana("aaa-posterior", "2026-10-20T09:00:00Z", real=True, aprobados=9, total=28))
        self.assertIn("9/28", texto)

    def test_una_campana_sin_fecha_no_puede_ser_la_ultima(self):
        # `ORDER BY run_at DESC` pone los NULL primero en PostgreSQL: una consulta ingenua elegiría la ejecución sin fecha.
        texto = self.una_fila(campana("rs-sin-fecha", None, real=False, motivos=("sintetica",), aprobados=5, total=28))
        self.assertIn("0/28", texto)
        self.assertNotIn("5/28", texto)
        self.assertNotIn("sintetica", texto)

    def test_los_motivos_de_no_real_son_los_de_la_ultima_campana(self):
        texto = self.una_fila(campana("rs-doble", "2026-10-14T09:00:00Z", real=False, motivos=("doble", "plantilla"),
                                      aprobados=3, total=28))
        self.assertIn("no real", texto)
        self.assertIn("doble", texto)
        self.assertIn("plantilla", texto)
        self.assertIn("3/28", texto)

    def test_sin_campanas_de_jup_070_no_hay_filas(self):
        # Cero filas -> Grafana enseña el `noValue` del panel («Sin datos: ...»). Una fila «0/0» inventaría una campaña.
        self.assertEqual(resumenes("DELETE FROM evaluation.runs WHERE source = 'JUP-070';"), [])

    def test_sin_campanas_aunque_haya_otras_fuentes_reales(self):
        preparacion = ("DELETE FROM evaluation.runs WHERE source = 'JUP-070';"
                       + R.insertar_ejecucion("rs-otra", "JUP-071", "2026-10-14T09:00:00Z", real=True))
        self.assertEqual(resumenes(preparacion), [])


if __name__ == "__main__":
    unittest.main()
