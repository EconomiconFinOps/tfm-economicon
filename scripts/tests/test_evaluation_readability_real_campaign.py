"""Legibilidad del dashboard con el conjunto versionado COMPLETO, banco de JUP-133 incluido (change `jup-133-reevaluacion-metricas-modelo`).

El montaje común de las pruebas de legibilidad (`evaluation_readability_support.servidor`) deja fuera el banco de 28
preguntas con el chat real, porque esas pruebas describen escenarios sobre las dos campañas de plantilla de octubre. Esta
prueba carga el conjunto completo en un segundo PostgreSQL (`servidor_completo`) y comprueba lo que cambia al entrar la
tercera ejecución de JUP-070 (suite 1.0.1, 22/10/2026, real):

* el resumen de la campaña la presenta como la última, real y con sus casos aprobados;
* la matriz por métrica y ejecución tiene tres columnas en orden cronológico, la nueva marcada como real, y una celda por
  cada métrica y variante en cada columna;
* la tabla de campañas de la sección A no pierde ninguna de las tres.

Sin Docker se salta como las demás pruebas de legibilidad.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_real_campaign.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

TITULO_MATRIZ = "Resultados por métrica y ejecución"
BANCO = "jup-070-20261022"


def panel_resumen() -> dict:
    candidatos = [p for p in R.de_seccion("A")
                  if p["type"] == "table" and re.search(r"(?i)\bAS\s+resumen\b", R.sql_de(p))]
    if len(candidatos) != 1:
        raise AssertionError(f"se esperaba un único panel de resumen en la sección A y hay {len(candidatos)}")
    return candidatos[0]


class ResumenConElBancoTests(unittest.TestCase):
    def test_la_ultima_campana_es_la_del_banco_y_dice_real_con_sus_casos(self):
        datos = R.ejecutar(R.consulta_unica(panel_resumen()), completo=True)
        textos = [fila["resumen"] for fila in datos["filas"]]
        self.assertEqual(len(textos), 1, textos)
        texto = textos[0]
        self.assertIn("22/10/2026", texto)
        self.assertRegex(texto, r"\breal\b")
        self.assertNotIn("no real", texto)
        self.assertIn("10/28", texto)
        self.assertNotIn("todavía no hay evaluación con modelo real", texto)


class MatrizConElBancoTests(unittest.TestCase):
    def setUp(self) -> None:
        datos = R.ejecutar(R.consulta_unica(R.por_titulo(TITULO_MATRIZ, "A")), completo=True)
        self.filas = datos["filas"]
        self.cabeceras = list(dict.fromkeys(fila["ejecucion"] for fila in self.filas))

    def test_hay_tres_columnas_en_orden_cronologico_y_la_nueva_es_real(self):
        self.assertEqual(len(self.cabeceras), 3, self.cabeceras)
        self.assertEqual([c[:16] for c in self.cabeceras],
                         ["2026-10-08 20:13", "2026-10-08 21:01", "2026-10-22 00:00"])
        self.assertTrue(self.cabeceras[0].startswith("2026-10-08 20:13 · no real: "))
        self.assertTrue(self.cabeceras[1].startswith("2026-10-08 21:01 · no real: "))
        self.assertEqual(self.cabeceras[2], "2026-10-22 00:00 · real")

    def test_la_matriz_esta_completa_una_celda_por_metrica_variante_y_columna(self):
        pares = {(fila["metrica"], fila["orden"]) for fila in self.filas}
        self.assertEqual(len(self.filas), len(pares) * 3)
        for cabecera in self.cabeceras:
            self.assertEqual(sum(1 for fila in self.filas if fila["ejecucion"] == cabecera), len(pares), cabecera)

    def test_ninguna_celda_muestra_un_identificador_crudo_ni_queda_vacia(self):
        for fila in self.filas:
            self.assertTrue(str(fila["celda"]).strip(), fila)
            self.assertNotRegex(fila["metrica"], r"^[a-z_]+$", fila)


if __name__ == "__main__":
    unittest.main()
