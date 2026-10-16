"""Guía del dashboard: casos añadidos tras la fase de mutación (JUP-121, change `jup-121-lectura-dashboard`).

NO sustituye a `test_evaluation_readability_docs.py` (ya commiteado, no se toca): lo complementa con lo que dejaron vivo
los mutantes de la guía.

Qué dejó vivo la primera ronda y por qué importa:

* Las pruebas originales buscan CADA cifra en CUALQUIER bloque del apartado «Calculado y no mostrado». Como unas viñetas
  citan a otras («por la misma razón que GRD-2 …») y el párrafo de apertura nombra el intervalo de confianza, borrar la
  viñeta propia de GRD-2 o del intervalo, o dejarla en el solo nombre, no hacía fallar nada. Pero la spec pide que la guía
  LISTE cada cifra CON SU MOTIVO: quien echa en falta GRD-2 debe encontrar una entrada que empiece por GRD-2 y se la
  explique, no una mención de pasada en la de otra cifra. Aquí se exige una entrada propia (viñeta cuyo rótulo en negrita
  es la cifra) con su motivo.
* El intervalo de confianza: las pruebas originales solo comprueban que «algún verbo de visibilidad» aparece en el primer
  bloque que lo nombra (el párrafo de apertura), no que la entrada del intervalo diga la verdad. Si la guía dijera «no se
  muestra» cuando la matriz SÍ lo muestra, la guía mentiría y nada fallaría. Aquí la afirmación se contrasta con la
  consulta real de la matriz.
* La descripción de la matriz en «Dashboard» nombra el formato `IC95 lo–hi %`: se contrasta con el rótulo que la consulta
  de la matriz escribe de verdad, para que la guía y el panel no se separen.

Ruta de la guía: `EVALUATION_DASHBOARD_GUIDE`; del dashboard: `EVALUATION_DASHBOARD_JSON` (como en el resto de módulos).
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_docs.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402
import test_evaluation_readability_docs as D  # noqa: E402  (solo sus ayudantes de lectura de la guía; no sus TestCase)

MATRIZ = "Resultados por métrica y ejecución"
VINETA = re.compile(r"^\s*[-*+]\s+\*\*(?P<rotulo>[^*]+)\*\*")


def vinetas_con_rotulo() -> list:
    """`[(rótulo en negrita sin tildes y en minúsculas, texto completo de la viñeta)]` del apartado."""
    resultado = []
    for bloque in D.bloques(D.apartado()):
        encontrado = VINETA.match(bloque)
        if encontrado:
            resultado.append((D.sin_tildes(encontrado.group("rotulo")), bloque))
    return resultado


class EntradaPropiaDeCadaCifraTests(unittest.TestCase):
    def test_cada_cifra_tiene_una_entrada_propia_con_su_motivo(self):
        # Caso: una mención de pasada en la viñeta de otra cifra (o en el párrafo de apertura) no cuenta como listarla.
        # Por qué: la spec dice que la guía lista cada cifra con su motivo. La entrada propia es la viñeta cuyo rótulo en
        # negrita ES la cifra; además debe traer una explicación (conector de razón y texto suficiente, no solo el nombre).
        entradas = vinetas_con_rotulo()
        self.assertTrue(entradas, "el apartado no tiene viñetas con rótulo en negrita")
        for nombre, patron in D.CIFRAS:
            with self.subTest(cifra=nombre):
                propias = [texto for rotulo, texto in entradas if re.search(patron, rotulo)]
                self.assertTrue(propias, f"«{nombre}» no tiene una entrada propia (viñeta con ese rótulo) bajo "
                                         f"«Calculado y no mostrado»; solo se la menciona de pasada")
                self.assertEqual(len(propias), 1, f"«{nombre}» tiene varias entradas propias: {propias}")
                texto = D.sin_tildes(propias[0])
                self.assertRegex(texto, D.RAZON, f"la entrada de «{nombre}» no da ninguna razón: {propias[0]}")
                self.assertGreaterEqual(len(re.findall(r"\w+", propias[0])), D.PALABRAS_MINIMAS,
                                        f"la entrada de «{nombre}» es demasiado corta para llevar un motivo: {propias[0]}")


class IntervaloDeConfianzaCoherenteConElDashboardTests(unittest.TestCase):
    def _entrada_del_intervalo(self) -> str:
        for rotulo, texto in vinetas_con_rotulo():
            if re.search(r"intervalo de confianza|ic ?95", rotulo):
                return D.sin_tildes(texto)
        self.fail("el apartado no tiene la entrada propia del intervalo de confianza")

    def _la_matriz_muestra_el_intervalo(self) -> bool:
        return "IC95" in R.consulta_unica(R.por_titulo(MATRIZ, "A"))

    def test_la_entrada_del_intervalo_dice_lo_mismo_que_hace_la_matriz(self):
        # Caso: la matriz escribe «IC95 …» en las celdas, así que la entrada debe afirmar que SÍ se muestra y decir dónde.
        # Por qué: las pruebas originales aceptan «no se muestra» o «se muestra» indistintamente (basta un verbo de
        # visibilidad); una guía que contradice al panel confunde más que una que calla.
        self.assertTrue(self._la_matriz_muestra_el_intervalo(), "la matriz ya no escribe el intervalo: revisar esta prueba")
        texto = self._entrada_del_intervalo()
        self.assertNotRegex(texto, r"\bno se (muestra|ve|ensena|presenta)\b",
                            "la entrada dice que el intervalo NO se muestra, pero la matriz sí lo muestra")
        self.assertRegex(texto, r"\b(si se muestra|se muestra|aparece|se ve)\b",
                         "la entrada del intervalo no dice que se muestra")
        self.assertRegex(texto, r"matriz|resultados por metrica y ejecucion",
                         "la entrada no dice dónde se ve el intervalo (la tabla de resultados por métrica y ejecución)")

    def test_la_guia_describe_el_formato_ic95_que_escribe_la_matriz(self):
        # Caso: el rótulo «IC95» que la consulta de la matriz escribe debe aparecer en la descripción de la matriz de
        # «Dashboard» (viñeta «Matriz.»). Por qué: es la única forma de que quien lee la celda «IC95 41.2–78.0 %» sepa
        # qué es sin abrir la consulta.
        texto = D.GUIA.read_text(encoding="utf-8")
        encontrado = re.search(r"^- \*\*Matriz\.\*\*.*$", texto, re.M)
        self.assertIsNotNone(encontrado, "la guía no tiene la viñeta «Matriz.» en «Dashboard»")
        self.assertTrue(self._la_matriz_muestra_el_intervalo())
        self.assertIn("IC95", encontrado.group(0), "la viñeta «Matriz.» no nombra el formato IC95 de las celdas")


if __name__ == "__main__":
    unittest.main()
