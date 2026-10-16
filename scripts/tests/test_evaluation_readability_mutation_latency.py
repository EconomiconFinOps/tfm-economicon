"""Evolución de la latencia de la campaña: casos añadidos tras la fase de mutación (JUP-121, change `jup-121-lectura-dashboard`).

Complementa a `test_evaluation_readability_latency.py` (commiteado, no se toca). Las pruebas originales comprueban QUÉ
puntos salen (LAT-1 y LAT-2, etapa total, mínimo de dos medidos...) pero no CÓMO se rotula ni en qué orden se entregan, y
tampoco que el panel tenga el mismo estilo que su hermano de proporciones. Los mutantes supervivientes señalaron:

* La etiqueta de cada serie: `LAT-1 · mediana total · JUP-070 · serie <8 primeros caracteres de la clave>` y, si no es
  real, ` · no real: <motivos>`. Permutar «mediana» y «percentil 95», quitar la etapa o alargar la clave a más de ocho
  caracteres cambiaba la leyenda sin que ninguna prueba lo notara; la guía documenta justo esa forma (métrica, fuente y
  «serie» con los 8 primeros caracteres de la clave).
* El orden de las filas: una serie temporal debe llegar ordenada por tiempo (y, a igual tiempo, por etiqueta). Las
  ejecuciones se insertan a propósito en orden cronológico inverso para que el orden físico no lo dé por casualidad.
* Paridad de estilo con «Evolución de las métricas automáticas»: mismos ejes, puntos siempre visibles, huecos sin unir,
  leyenda en tabla y tooltip; solo cambian la unidad (milisegundos), los decimales y que no hay máximo. Una gráfica de
  milisegundos que cambiara de estilo respecto a su hermana obligaría a reaprender la lectura.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_latency.py`
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402
import test_evaluation_readability_latency as L  # noqa: E402  (solo sus ayudantes: panel, puntos, serie)

HERMANO = "Evolución de las métricas automáticas"


class EtiquetasExactasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        L.panel()
        # Clave de más de ocho caracteres: la etiqueta solo lleva los ocho primeros. La no real usa dos motivos.
        preparacion = (L.serie("lm-a", "abcdefghij-resto", (10, 12), lat1=(3000.0, 3100.0), lat2=(4000.0, 4200.0))
                       + L.serie("lm-b", "12345678-zzz", (11, 13), real=False, motivos=("plantilla", "doble"),
                                 lat1=(100.0, 110.0), lat2=(150.0, 160.0)))
        cls.etiquetas = {fila["metric"] for fila in L.puntos(preparacion)["filas"]}

    def test_las_cuatro_etiquetas_exactas(self):
        self.assertEqual(self.etiquetas, {
            "LAT-1 · mediana total · JUP-070 · serie abcdefgh",
            "LAT-2 · percentil 95 total · JUP-070 · serie abcdefgh",
            "LAT-1 · mediana total · JUP-070 · serie 12345678 · no real: plantilla, doble",
            "LAT-2 · percentil 95 total · JUP-070 · serie 12345678 · no real: plantilla, doble",
        })


class OrdenDeLasFilasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        L.panel()
        # Días en orden DESCENDENTE (12 antes que 10) y dos series con las mismas fechas: ni el orden de inserción ni un
        # orden solo por etiqueta producen una serie temporal correcta.
        preparacion = (L.serie("lo-a", "k-orden-a", (12, 10), lat1=(3100.0, 3000.0), lat2=(4200.0, 4000.0))
                       + L.serie("lo-b", "k-orden-b", (12, 10), lat1=(110.0, 100.0), lat2=(160.0, 150.0)))
        cls.filas = L.puntos(preparacion)["filas"]

    def test_las_filas_llegan_ordenadas_por_tiempo_y_luego_por_etiqueta(self):
        claves = [(datetime.fromisoformat(f["time"]), f["metric"]) for f in self.filas]
        self.assertEqual(len(claves), 8, claves)
        self.assertEqual(claves, sorted(claves), "la serie temporal debe llegar ordenada por (tiempo, etiqueta)")


class MismoEstiloQueElPanelHermanoTests(unittest.TestCase):
    def setUp(self):
        self.latencia = L.panel()
        self.hermano = R.por_titulo(HERMANO, "A")

    def test_ejes_puntos_huecos_y_apilado_son_los_del_panel_de_proporciones(self):
        self.assertEqual(R.defaults(self.latencia)["custom"], R.defaults(self.hermano)["custom"])
        self.assertEqual(R.defaults(self.latencia)["color"], R.defaults(self.hermano)["color"])
        self.assertEqual(R.defaults(self.latencia)["thresholds"], R.defaults(self.hermano)["thresholds"])

    def test_leyenda_y_tooltip_son_los_del_panel_de_proporciones(self):
        self.assertEqual(self.latencia["options"], self.hermano["options"])

    def test_solo_cambian_unidad_decimales_y_maximo(self):
        d = R.defaults(self.latencia)
        self.assertEqual(d.get("unit"), "ms")
        self.assertEqual(d.get("decimals"), 0)
        self.assertEqual(d.get("min"), 0)
        self.assertNotIn("max", d, "una latencia en milisegundos no tiene máximo natural (la tasa sí: 1)")

    def test_el_aviso_sin_datos_es_el_mismo_que_el_del_panel_hermano(self):
        self.assertEqual(R.defaults(self.latencia)["noValue"], R.defaults(self.hermano)["noValue"])
        self.assertEqual(self.latencia["fieldConfig"]["overrides"], self.hermano["fieldConfig"]["overrides"])


if __name__ == "__main__":
    unittest.main()
