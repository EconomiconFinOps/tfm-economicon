"""Las tres categorías de operación del banco de JUP-133 salen traducidas, no con su identificador (hueco de JUP-133)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

TRADUCCIONES = {"operation_failed": "operación fallida", "operation_cancelled": "operación cancelada",
                "operation_paused": "operación en pausa"}
TITULOS = ("Exactitud, relevancia y fundamento (detalle)", "Latencia, formato y disponibilidad de la campaña (detalle)",
           "Resultados por métrica y ejecución")


def textos(titulo: str) -> list[str]:
    """Valores de las columnas que el panel traduce (`variante` en los detalles, `metrica` en la matriz)."""
    datos = R.ejecutar(R.consulta_unica(R.por_titulo(titulo)), completo=True)
    return [str(fila[columna]) for fila in datos["filas"] for columna in ("variante", "metrica") if columna in fila]


class CategoriasDeOperacionTraducidasTests(unittest.TestCase):
    def test_ningun_panel_ensena_el_identificador_crudo(self) -> None:
        for titulo in TITULOS:
            valores = textos(titulo)
            for crudo in TRADUCCIONES:
                with self.subTest(panel=titulo, categoria=crudo):
                    self.assertFalse([v for v in valores if crudo in v], crudo)

    def test_los_paneles_con_filas_de_fallos_por_categoria_ensenan_la_traduccion(self) -> None:
        for titulo in TITULOS[1:]:
            valores = textos(titulo)
            for traduccion in TRADUCCIONES.values():
                with self.subTest(panel=titulo, traduccion=traduccion):
                    self.assertTrue([v for v in valores if traduccion in v], traduccion)


if __name__ == "__main__":
    unittest.main()
