"""Legibilidad del manifiesto completo: banco histórico y seis repeticiones JUP-133.

Las tres campañas nuevas del banco son provisionales y la última no hereda
la clasificación real del ensayo anterior. La matriz conserva las seis columnas
JUP-070, con fechas, estado y celdas completas. PostgreSQL desechable.
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
    def test_la_ultima_campana_es_provisional_y_no_hereda_la_aceptacion_del_banco(self):
        datos = R.ejecutar(R.consulta_unica(panel_resumen()), completo=True)
        textos = [fila["resumen"] for fila in datos["filas"]]
        self.assertEqual(len(textos), 1, textos)
        texto = textos[0]
        self.assertIn("23/10/2026", texto)
        self.assertIn("no real", texto)
        self.assertIn("sin_modelo_verificado", texto)
        self.assertIn("0/28", texto)
        self.assertNotIn("todavía no hay evaluación con modelo real", texto)


class MatrizConElBancoTests(unittest.TestCase):
    def setUp(self) -> None:
        datos = R.ejecutar(R.consulta_unica(R.por_titulo(TITULO_MATRIZ, "A")), completo=True)
        self.filas = datos["filas"]
        self.cabeceras = list(dict.fromkeys(fila["ejecucion"] for fila in self.filas))

    def test_hay_seis_columnas_y_las_tres_nuevas_conservan_su_estado_provisional(self):
        self.assertEqual(len(self.cabeceras), 6, self.cabeceras)
        self.assertEqual([c[:16] for c in self.cabeceras],
                         ["2026-10-08 20:13", "2026-10-08 21:01", "2026-10-22 00:00",
                          "2026-10-23 14:08", "2026-10-23 14:34", "2026-10-23 15:02"])
        self.assertTrue(self.cabeceras[0].startswith("2026-10-08 20:13 · no real: "))
        self.assertTrue(self.cabeceras[1].startswith("2026-10-08 21:01 · no real: "))
        self.assertEqual(self.cabeceras[2], "2026-10-22 00:00 · real")
        for header in self.cabeceras[3:]:
            self.assertTrue(header.endswith(" · no real: sin_modelo_verificado"), header)

    def test_la_matriz_esta_completa_una_celda_por_metrica_variante_y_columna(self):
        pares = {(fila["metrica"], fila["orden"]) for fila in self.filas}
        self.assertEqual(len(self.filas), len(pares) * 6)
        for cabecera in self.cabeceras:
            self.assertEqual(sum(1 for fila in self.filas if fila["ejecucion"] == cabecera), len(pares), cabecera)

    def test_ninguna_celda_queda_vacia(self):
        # Los identificadores crudos de las categorías de operación los vigila `test_evaluation_readability_operation_labels.py`.
        for fila in self.filas:
            self.assertTrue(str(fila["celda"]).strip(), fila)


if __name__ == "__main__":
    unittest.main()
