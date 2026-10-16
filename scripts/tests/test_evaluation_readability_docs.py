"""Guía del dashboard: apartado «Calculado y no mostrado» (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisito de la spec «Cifras calculadas y no mostradas documentadas»: `docs/validation/evaluation-dashboard.md` lista las
cifras que se calculan (o que no se cargan) y que el dashboard NO enseña, con el MOTIVO de cada una. Quien lee el dashboard
y echa en falta, por ejemplo, el tamaño del corpus o la calibración por categoría debe poder ver ahí por qué no está, en
lugar de suponer un olvido.

Qué fija este módulo (es rojo hasta que el humano escriba el apartado):

* Existe un encabezado Markdown «Calculado y no mostrado».
* BAJO ese encabezado (hasta el siguiente encabezado de su mismo nivel o superior) cada una de estas cifras aparece en una
  viñeta, fila de tabla o párrafo propio que además lleva su motivo (una explicación con conector causal o de límite, no
  solo el nombre): intervalo de confianza (si ya se muestra, el apartado lo dice), GRD-2, REL-4, LAT-3, tamaño del corpus,
  casos críticos, casos juzgados por una sola persona, calibración por categoría y fallos de recuperación por categoría.

Que el motivo sea cierto lo revisa una persona; aquí solo se evita que una cifra aparezca sin ninguna razón al lado.
Ruta de la guía: `EVALUATION_DASHBOARD_GUIDE` la sustituye (sirve para comprobar un borrador o una copia mutada).
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_docs.py`
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

GUIA = Path(os.environ.get("EVALUATION_DASHBOARD_GUIDE") or R.ROOT / "docs" / "validation" / "evaluation-dashboard.md")
ENCABEZADO = re.compile(r"^(#{1,6})\s+Calculado y no mostrado\s*$", re.M)

# (nombre legible, regex sobre el texto SIN tildes y en minúsculas)
CIFRAS = (
    ("intervalo de confianza", r"intervalo de confianza|ic ?95"),
    ("GRD-2", r"grd-2"),
    ("REL-4", r"rel-4"),
    ("LAT-3", r"lat-3"),
    ("tamaño del corpus", r"tamano del corpus"),
    ("casos críticos", r"casos criticos"),
    ("casos juzgados por una sola persona", r"una sola persona"),
    ("calibración por categoría", r"calibracion por categoria"),
    ("fallos de recuperación por categoría", r"fallos de recuperacion por categoria"),
)
# Conectores que introducen una razón o un límite (sin tildes). Admite «porque», «motivo», «ya que», «solo»...
RAZON = re.compile(r"\b(porque|motivo|razon|ya que|dado que|puesto que|debido|pues|por eso|al no|aun no|todavia no|"
                   r"solo|unicamente|no se|no hay|no es|no son|sin|queda|se muestra|ya se)\b")
PALABRAS_MINIMAS = 10


def sin_tildes(texto: str) -> str:
    return R.sin_acentos(texto).lower()


def apartado() -> str:
    """Texto del apartado «Calculado y no mostrado» hasta el siguiente encabezado del mismo nivel o superior."""
    if not GUIA.is_file():
        raise AssertionError(f"no existe la guía {GUIA}")
    texto = GUIA.read_text(encoding="utf-8")
    encabezado = ENCABEZADO.search(texto)
    if not encabezado:
        raise AssertionError("la guía no tiene un encabezado «Calculado y no mostrado»")
    nivel = len(encabezado.group(1))
    resto = texto[encabezado.end():]
    cierre = re.search(rf"^#{{1,{nivel}}}\s", resto, re.M)
    return resto[:cierre.start()] if cierre else resto


def bloques(markdown: str) -> list:
    """Unidades de texto del apartado: cada viñeta (con sus líneas de continuación), cada fila de tabla y cada párrafo."""
    resultado, actual = [], []

    def cerrar():
        if actual:
            resultado.append(" ".join(actual))
            actual.clear()

    for linea in markdown.split("\n"):
        if not linea.strip():
            cerrar()
        elif re.match(r"^\s*([-*+]|\d+[.)])\s+", linea) or linea.lstrip().startswith("|"):
            cerrar()
            actual.append(linea.strip())
            if linea.lstrip().startswith("|"):
                cerrar()
        elif linea.startswith("#"):
            cerrar()
        else:
            actual.append(linea.strip())
    cerrar()
    return resultado


class CalculadoYNoMostradoTests(unittest.TestCase):
    def test_existe_el_encabezado(self):
        self.assertTrue(apartado().strip(), "el apartado «Calculado y no mostrado» está vacío")

    def test_cada_cifra_aparece_con_su_motivo_en_el_mismo_bloque(self):
        unidades = bloques(apartado())
        self.assertTrue(unidades)
        for nombre, patron in CIFRAS:
            with self.subTest(cifra=nombre):
                candidatas = [b for b in unidades if re.search(patron, sin_tildes(b))]
                self.assertTrue(candidatas, f"«{nombre}» no aparece bajo «Calculado y no mostrado»")
                # Alguna de las apariciones lleva una explicación: un conector de razón y texto suficiente (no solo el nombre).
                con_motivo = [b for b in candidatas
                              if RAZON.search(sin_tildes(b)) and len(re.findall(r"\w+", b)) >= PALABRAS_MINIMAS]
                self.assertTrue(con_motivo, f"«{nombre}» aparece sin motivo: {candidatas}")

    def test_el_intervalo_de_confianza_dice_si_se_muestra_o_no(self):
        # El intervalo se carga en la base y el dashboard nuevo lo muestra junto al valor: el apartado debe decirlo
        # (o explicar por qué no) en lugar de callar. Basta con que un verbo de visibilidad esté en su bloque.
        for bloque in bloques(apartado()):
            texto = sin_tildes(bloque)
            if re.search(r"intervalo de confianza|ic ?95", texto):
                self.assertRegex(texto, r"mostr|muestr|aparec|se ve|no se ve|figura|visible|ensen")
                return
        self.fail("el apartado no menciona el intervalo de confianza")


if __name__ == "__main__":
    unittest.main()
