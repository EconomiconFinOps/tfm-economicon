"""Resumen de la última campaña: casos añadidos tras la fase de mutación (JUP-121, change `jup-121-lectura-dashboard`).

Complementa a `test_evaluation_readability_summary.py` (commiteado, no se toca). Las pruebas originales comprueban el
CONTENIDO del resumen con expresiones tolerantes («0/28», «no real», una fecha en uno de tres formatos); aquí se fija el
TEXTO EXACTO que ve quien abre el dashboard y los bordes que la tolerancia dejaba vivos:

* El formato completo de la línea: `Última campaña: DD/MM/AAAA · <real | no real (motivos)> · k/n casos aprobados` más el
  aviso final solo cuando ninguna campaña de JUP-070 es real. Un cambio de separador, de formato de fecha o la pérdida de
  « casos aprobados» pasaba desapercibido.
* Una campaña sin filas de casos dice «sin recuento de casos» (no deja el hueco ni inventa «0/28»).
* Dos campañas con la MISMA fecha: gana siempre la de identificador menor (desempate determinista); sin él, la elección
  dependería del orden físico de las filas.
* La fecha se escribe en UTC: una campaña a las 23:30 UTC sigue siendo del mismo día (una zona con adelanto la movería).

Los escenarios son sintéticos y terminan en `ROLLBACK`. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_summary.py`
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402
import test_evaluation_readability_summary as S  # noqa: E402  (solo sus ayudantes: panel, resumenes, campana)

AVISO = " · todavía no hay evaluación con modelo real"


class TextoExactoDelResumenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        S.panel()  # sin el panel falla antes de arrancar Docker

    def una_fila(self, preparacion: str) -> str:
        textos = S.resumenes(preparacion)
        self.assertEqual(len(textos), 1, textos)
        return textos[0]

    def test_campana_real_texto_exacto_en_utc_y_sin_aviso(self):
        # 23:30 UTC: en una zona con adelanto (Asia/Tokio, Madrid en horario de verano...) ya sería el día siguiente.
        texto = self.una_fila(S.campana("rm-real", "2026-10-14T23:30:00Z", real=True, aprobados=20, total=28))
        self.assertEqual(texto, "Última campaña: 14/10/2026 · real · 20/28 casos aprobados")

    def test_campana_no_real_texto_exacto_con_motivos_y_aviso(self):
        # Los datos versionados no tienen ninguna campaña real de JUP-070, así que el aviso final aparece.
        texto = self.una_fila(S.campana("rm-nr", "2026-10-14T09:00:00Z", real=False, motivos=("plantilla", "doble"),
                                        aprobados=3, total=28))
        self.assertEqual(texto, "Última campaña: 14/10/2026 · no real (plantilla, doble) · 3/28 casos aprobados" + AVISO)

    def test_una_campana_sin_filas_de_casos_dice_sin_recuento(self):
        # Caso límite: la ejecución existe pero el informe no trajo el estado de sus casos. No se inventa «0/28» ni se
        # deja «casos aprobados» colgando sin cifras.
        texto = self.una_fila(R.insertar_ejecucion("rm-sin-casos", "JUP-070", "2026-10-14T09:00:00Z", real=True))
        self.assertEqual(texto, "Última campaña: 14/10/2026 · real · sin recuento de casos")

    def test_con_la_misma_fecha_gana_el_identificador_menor_aunque_se_inserte_despues(self):
        # Se inserta primero la «b»: el orden físico favorecería a «b»; el desempate por identificador elige «a».
        preparacion = (S.campana("rm-b", "2026-10-14T09:00:00Z", real=True, aprobados=22, total=28)
                       + S.campana("rm-a", "2026-10-14T09:00:00Z", real=True, aprobados=11, total=28))
        texto = self.una_fila(preparacion)
        self.assertEqual(texto, "Última campaña: 14/10/2026 · real · 11/28 casos aprobados")


if __name__ == "__main__":
    unittest.main()
