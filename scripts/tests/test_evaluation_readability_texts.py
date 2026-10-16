"""Textos introductorios de las secciones del dashboard de evaluación (JUP-121, change `jup-121-lectura-dashboard`, Red).

Decisión D7 del diseño: el texto «Cómo leer la sección A» obligaba a hacer scroll (siete viñetas, un panel de 11 filas de
alto) antes de ver un solo resultado. Se acorta a TRES viñetas como máximo y a un panel de a lo sumo 8 filas, y el resto de
la explicación va a la guía (`docs/validation/evaluation-dashboard.md`). Lo que NO puede perderse es lo que cada sección
dice a la vista sobre lo que no demuestra: la tabla de tres columnas «Qué mide / De dónde salen los datos / Qué no
demuestra» se conserva en A, B y C.

Este módulo es estático (sin Docker): lee el JSON y comprueba el panel de texto de cada sección por su título.
Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`. Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_texts.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

# Cabecera de la tabla de tres columnas (tolerante con los espacios alrededor de las barras).
CABECERA = re.compile(r"\|\s*Qué mide\s*\|\s*De dónde salen los datos\s*\|\s*Qué no demuestra\s*\|")
SEPARADOR = re.compile(r"^\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*$", re.M)


def texto(seccion: str) -> dict:
    return R.por_titulo(f"Cómo leer la sección {seccion}", seccion)


def contenido(panel) -> str:
    return panel["options"]["content"]


def viñetas(markdown: str) -> list:
    """Líneas que son viñeta de primer nivel de Markdown (`- ...`)."""
    return [linea for linea in markdown.split("\n") if linea.startswith("- ")]


class ComoLeerLaSeccionATests(unittest.TestCase):
    def test_tiene_como_maximo_tres_vinetas(self):
        # Siete viñetas largas obligaban a hacer scroll: el resto de la explicación vive en la guía.
        lineas = viñetas(contenido(texto("A")))
        self.assertLessEqual(len(lineas), 3, f"hay {len(lineas)} viñetas: {[l[:50] for l in lineas]}")

    def test_conserva_la_tabla_que_mide_de_donde_salen_y_que_no_demuestra(self):
        markdown = contenido(texto("A"))
        self.assertRegex(markdown, CABECERA)
        self.assertRegex(markdown, SEPARADOR)
        # La fila de datos de la tabla existe y dice qué no demuestra la sección (no es solo la cabecera).
        filas = [l for l in markdown.split("\n") if l.startswith("|")]
        self.assertGreaterEqual(len(filas), 3, filas)
        self.assertRegex(filas[2], r"(?i)usuarios reales|fuera de la bater")

    def test_el_panel_cabe_sin_scroll_en_ocho_filas_o_menos(self):
        self.assertLessEqual(texto("A")["gridPos"]["h"], 8)

    def test_sigue_siendo_markdown_y_con_descripcion_de_tres_lineas(self):
        panel = texto("A")
        self.assertEqual(panel["type"], "text")
        self.assertEqual(panel["options"]["mode"], "markdown")
        lineas = panel["description"].split("\n")
        self.assertEqual(len(lineas), 3, lineas)
        self.assertTrue(lineas[0].startswith("Tipo: A"))
        self.assertRegex(lineas[2], r"^No demuestra: .*(usuarios reales|fuera de la bater)")


class ComoLeerLasSeccionesByCTests(unittest.TestCase):
    def test_b_y_c_conservan_su_tabla_con_que_no_demuestra(self):
        for seccion, limitacion in (("B", r"(?i)piloto"), ("C", r"(?i)acierto|correct")):
            with self.subTest(seccion=seccion):
                markdown = contenido(texto(seccion))
                self.assertRegex(markdown, CABECERA)
                self.assertRegex(markdown, SEPARADOR)
                filas = [l for l in markdown.split("\n") if l.startswith("|")]
                self.assertGreaterEqual(len(filas), 3, filas)
                self.assertRegex(filas[2], limitacion)


if __name__ == "__main__":
    unittest.main()
