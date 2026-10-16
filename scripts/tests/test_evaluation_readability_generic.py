"""Reglas que TODO panel del dashboard de evaluación debe cumplir, viejo o nuevo (JUP-121, change `jup-121-lectura-dashboard`, Red).

Los módulos congelados (`test_evaluation_dashboard_structure.py`...) ya exigen estas reglas a los paneles que conocen, pero
algunas de sus comprobaciones localizan los paneles por lo que consultan (`clasificar`) y el parche que acompaña a este change
las tiene que tocar. Este módulo recorre TODOS los paneles que no son fila, sin clasificar nada, para que un panel nuevo (la
tabla por métrica y ejecución, el resumen de la campaña, la evolución de la latencia) al que le falte una de ellas se detecte
aunque las pruebas congeladas cambien:

* descripción de exactamente tres líneas: `Tipo: <sección>`, `Mide: ...` y `No demuestra: ...` (la letra es la de la sección
  donde está el panel);
* UN solo datasource, el de su sección (A y B: PostgreSQL de evaluación; C: Prometheus), en el panel, en cada target y en
  cualquier otro lugar del panel donde se declare uno (opciones, overrides, transformaciones);
* `noValue` definido en todo panel con datos (lo que se ve cuando la consulta no devuelve nada);
* nada de semáforos: ni la palabra en títulos, descripciones o consultas ni umbrales con varios tramos de color;
* en A y B, cada target SQL con `rawQuery`, `editorMode: code` y el `format` que corresponde al tipo de panel.

Un test aparte comprueba que el recorrido incluye de verdad los tres paneles nuevos (si el recorrido no los viera, estas
reglas no protegerían nada).

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`. Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_generic.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

PANELES_NUEVOS = (
    "Resultados por métrica y ejecución",
    "Resumen de la última campaña",
    "Evolución de la latencia de la campaña",
)


def datasources_anidados(valor, ruta=""):
    """Todos los valores bajo una clave `datasource`, en cualquier nivel del panel."""
    if isinstance(valor, dict):
        for clave, hijo in valor.items():
            if clave == "datasource":
                yield f"{ruta}/{clave}", hijo
            else:
                yield from datasources_anidados(hijo, f"{ruta}/{clave}")
    elif isinstance(valor, list):
        for indice, hijo in enumerate(valor):
            yield from datasources_anidados(hijo, f"{ruta}[{indice}]")


def con_datos():
    return [(letra, p) for letra, p in R.contenido() if p["type"] != "text"]


class RecorridoTests(unittest.TestCase):
    def test_el_recorrido_incluye_los_paneles_nuevos(self):
        titulos = [p["title"] for _, p in R.contenido()]
        for prefijo in PANELES_NUEVOS:
            with self.subTest(panel=prefijo):
                self.assertEqual(len([t for t in titulos if t.startswith(prefijo)]), 1, titulos)

    def test_hay_paneles_en_las_tres_secciones(self):
        self.assertEqual({letra for letra, _ in R.contenido()}, {"A", "B", "C"})
        self.assertGreaterEqual(len(R.contenido()), 21)


class DescripcionDeTodosLosPanelesTests(unittest.TestCase):
    def test_tres_lineas_tipo_mide_no_demuestra(self):
        for letra, panel in R.contenido():
            with self.subTest(seccion=letra, panel=panel["title"]):
                descripcion = panel.get("description")
                self.assertIsInstance(descripcion, str)
                self.assertNotIn("\r", descripcion)
                lineas = descripcion.split("\n")
                self.assertEqual(len(lineas), 3, lineas)
                self.assertRegex(lineas[0], rf"^Tipo: {letra}(?![A-Za-z0-9])")
                self.assertRegex(lineas[1], r"^Mide: \S")
                self.assertRegex(lineas[2], r"^No demuestra: \S")


class UnSoloDatasourceTests(unittest.TestCase):
    def test_cada_panel_con_datos_declara_el_datasource_de_su_seccion_en_el_panel_y_en_sus_targets(self):
        for letra, panel in con_datos():
            esperado = R.DATASOURCE_POR_SECCION[letra]
            with self.subTest(seccion=letra, panel=panel["title"]):
                self.assertEqual(panel.get("datasource"), esperado)
                self.assertTrue(panel.get("targets"), "un panel de datos necesita targets")
                for objetivo in panel["targets"]:
                    self.assertEqual(objetivo.get("datasource"), esperado)

    def test_ningun_datasource_anidado_es_distinto_del_de_la_seccion(self):
        for letra, panel in R.contenido():
            with self.subTest(seccion=letra, panel=panel["title"]):
                for ruta, valor in datasources_anidados(panel):
                    self.assertEqual(valor, R.DATASOURCE_POR_SECCION[letra], ruta)

    def test_los_paneles_de_texto_no_llevan_targets(self):
        for _, panel in R.contenido():
            if panel["type"] == "text":
                with self.subTest(panel=panel["title"]):
                    self.assertNotIn("targets", panel)

    def test_a_y_b_solo_consultan_sql_y_c_solo_promql(self):
        for letra, panel in con_datos():
            for objetivo in panel["targets"]:
                with self.subTest(seccion=letra, panel=panel["title"]):
                    if letra == "C":
                        self.assertIn("expr", objetivo)
                        self.assertNotIn("rawSql", objetivo)
                    else:
                        self.assertIn("rawSql", objetivo)
                        self.assertNotIn("expr", objetivo)


class AvisoSinDatosTests(unittest.TestCase):
    def test_todo_panel_con_datos_define_no_value(self):
        for letra, panel in con_datos():
            with self.subTest(seccion=letra, panel=panel["title"]):
                aviso = R.defaults(panel).get("noValue")
                self.assertTrue(isinstance(aviso, str) and aviso.strip(), "sin `noValue` Grafana pinta un hueco o un cero")


class SinSemaforosTests(unittest.TestCase):
    def test_la_palabra_semaforo_no_aparece_en_titulos_descripciones_ni_consultas(self):
        for letra, panel in R.contenido():
            textos = [panel["title"], panel.get("description", ""), R.sql_de(panel)]
            textos += [t.get("expr", "") for t in panel.get("targets", [])]
            with self.subTest(seccion=letra, panel=panel["title"]):
                self.assertNotRegex(R.sin_acentos(" ".join(textos)), r"(?i)semaforo")

    def test_ningun_panel_define_umbrales_con_varios_tramos_de_color(self):
        # Los umbrales de JUP-067 son provisionales: nada se colorea como bueno o malo.
        for letra, panel in R.contenido():
            umbrales = R.defaults(panel).get("thresholds", {}).get("steps", [])
            with self.subTest(seccion=letra, panel=panel["title"]):
                self.assertLessEqual(len(umbrales), 1, umbrales)
                for tramo in umbrales:
                    self.assertNotRegex(str(tramo.get("color", "")), r"(?i)red|green|yellow|orange")


class ConsultasSqlTests(unittest.TestCase):
    def test_cada_target_sql_de_a_y_b_tiene_modo_codigo_y_el_formato_de_su_tipo(self):
        for letra, panel in con_datos():
            if letra == "C":
                continue
            esperado = "time_series" if panel["type"] == "timeseries" else "table"
            refs = []
            for objetivo in panel["targets"]:
                with self.subTest(panel=panel["title"], refId=objetivo.get("refId")):
                    self.assertIs(objetivo.get("rawQuery"), True)
                    self.assertEqual(objetivo.get("editorMode"), "code")
                    self.assertEqual(objetivo.get("format"), esperado)
                    self.assertRegex(objetivo.get("rawSql", "").strip(), r"(?i)^(SELECT|WITH)\b")
                    refs.append(objetivo.get("refId"))
            self.assertEqual(len(refs), len(set(refs)), refs)


if __name__ == "__main__":
    unittest.main()
