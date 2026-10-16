"""Tablas de detalle (A y B): casos añadidos tras la fase de mutación (JUP-121, change `jup-121-lectura-dashboard`).

Complementa a `test_evaluation_readability_labels.py` (commiteado, no se toca). Las pruebas originales fijan qué columnas se
OCULTAN (`status`, `behavior`...) y que las columnas nuevas de la sección B existen, pero no la lista COMPLETA de columnas que
ve una persona ni el orden de las filas. Los mutantes supervivientes lo demostraron: dejar visible `value`, `unit`,
`run_id` o `commit_sha`, ocultar la columna «Categoría y perturbación» de robustez o quitar el nombre de «Numerador» no
hacía fallar nada. Casos añadidos:

* Lista exacta de columnas VISIBLES (con su rótulo) de las cuatro tablas de detalle, sobre la consulta real: lo que
  quien lee ve es el contrato de la spec «Etiquetas con un solo sentido» y «Unidades legibles en la sección B».
* Anchos mínimos legibles: una columna visible con ancho fijo menor que 60 px recorta su contenido.
* Lo nulo de numerador y denominador se ve como «—», y el resultado de la sección B se traduce («Medido», «No medido»).
* Orden de las filas: las tablas por fila van por fecha y métrica; la sección B por bloque (tiempo, asignación, ahorro).
* Formato de `valor_texto` por unidad en las tres tablas de calidad/campaña/robustez, incluidas las unidades que sus
  grupos no usan hoy (`ms` en calidad, `porcentaje`, `eur_minor_2`, una desconocida): la consulta debe formatear igual
  en las tres, aunque mañana llegue un grupo distinto.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_labels.py`
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

CALIDAD = ("Exactitud, relevancia y fundamento", "A")
CAMPANA = ("Latencia, formato y disponibilidad de la campaña", "A")
ROBUSTEZ = ("Robustez", "A")
NEGOCIO = ("Tiempo, asignación y ahorro", "B")
COMUNES = ["Fecha", "Versión de la batería", "Commit", "Modelo de generación", "Tipo de ejecución"]
VISIBLES_ESPERADAS = {
    CALIDAD: COMUNES + ["Métrica", "Variante", "Valor", "Numerador", "Denominador"],
    CAMPANA: COMUNES + ["Métrica", "Variante", "Valor", "Numerador", "Denominador"],
    ROBUSTEZ: COMUNES + ["Métrica", "Categoría y perturbación", "Valor", "Numerador", "Denominador"],
    NEGOCIO: COMUNES + ["Medida", "Variante", "Resultado", "Valor", "Numerador", "Denominador"],
}
TABLAS = list(VISIBLES_ESPERADAS)


def panel_de(clave):
    return R.por_titulo(*clave)


def datos_de(clave, preparacion: str = "") -> dict:
    return R.ejecutar(R.consulta_unica(panel_de(clave)), preparacion)


class ColumnasVisiblesTests(unittest.TestCase):
    def test_la_lista_exacta_de_columnas_visibles_de_cada_tabla_de_detalle(self):
        # Caso: se calcula con la consulta REAL (sus columnas y su orden) y los overrides del panel (rótulo y `hidden`).
        # Por qué: es la única forma de que `run_id`, `source`, `value`, `unit`, `commit_sha`, `status`, `behavior`... no
        # reaparezcan a la vista, y de que ningún rótulo se pierda (el nombre de una columna visible es parte de la spec).
        for clave in TABLAS:
            with self.subTest(tabla=clave[0]):
                panel = panel_de(clave)
                columnas = R.nombres(datos_de(clave))
                self.assertEqual(R.columnas_visibles(panel, columnas), VISIBLES_ESPERADAS[clave])

    def test_ninguna_columna_visible_con_ancho_fijo_es_mas_estrecha_que_60_pixeles(self):
        # Edge: un ancho minúsculo (p. ej. 10 px) deja la columna ilegible aunque exista. 60 px es el mínimo para un
        # rótulo corto como «Hito»; las tablas de detalle usan 80 px o más.
        for clave in TABLAS:
            panel = panel_de(clave)
            for columna in R.nombres(datos_de(clave)):
                if R.oculta(panel, columna):
                    continue
                ancho = R.propiedades(panel, columna).get("custom.width")
                with self.subTest(tabla=clave[0], columna=columna):
                    if ancho is not None:
                        self.assertGreaterEqual(ancho, 60)


class MapeosDeLoNuloYDelResultadoTests(unittest.TestCase):
    def test_numerador_y_denominador_vacios_se_ven_como_raya(self):
        # La consulta devuelve NULL (no un texto) y el panel lo traduce a «—»: sin ese mapeo la celda quedaría en
        # blanco y no se distinguiría de un fallo de carga. Las columnas visibles de numerador/denominador son
        # `numerator`/`denominator` en calidad, campaña y robustez y `numerador_texto`/`denominador_texto` en negocio.
        pares = {CALIDAD: ("numerator", "denominator"), CAMPANA: ("numerator", "denominator"),
                 ROBUSTEZ: ("numerator", "denominator"), NEGOCIO: ("numerador_texto", "denominador_texto")}
        for clave, columnas in pares.items():
            for columna in columnas:
                with self.subTest(tabla=clave[0], columna=columna):
                    mapeos = R.propiedades(panel_de(clave), columna).get("mappings")
                    self.assertTrue(mapeos, "la columna no traduce lo nulo")
                    nulo = [m for m in mapeos if m.get("type") == "special" and m["options"].get("match") == "null"]
                    self.assertEqual([m["options"]["result"]["text"] for m in nulo], ["—"])

    def test_el_resultado_de_negocio_se_traduce(self):
        panel = panel_de(NEGOCIO)
        propiedades = R.propiedades(panel, "status")
        self.assertEqual(propiedades.get("displayName"), "Resultado")
        mapeos = propiedades.get("mappings")
        self.assertTrue(mapeos, "la columna «Resultado» no traduce measured/not_measured")
        textos = {clave: valor["text"] for clave, valor in mapeos[0]["options"].items()}
        self.assertEqual(textos.get("measured"), "Medido")
        self.assertEqual(textos.get("not_measured"), "No medido")


class OrdenDeLasFilasTests(unittest.TestCase):
    def test_calidad_y_campana_van_por_fecha_y_luego_por_metrica(self):
        for clave in (CALIDAD, CAMPANA):
            filas = datos_de(clave)["filas"]
            with self.subTest(tabla=clave[0]):
                self.assertGreater(len(filas), 10)
                claves = [(datetime.fromisoformat(f["run_at"]), f["metric_id"]) for f in filas]
                self.assertEqual(claves, sorted(claves), "las filas deben ir por (fecha, métrica)")

    def test_negocio_va_por_bloque_tiempo_asignacion_ahorro(self):
        rango = {"time": 1, "allocation": 2, "savings": 3}
        bloques = [rango[f["grp"]] for f in datos_de(NEGOCIO)["filas"]]
        self.assertGreater(len(bloques), 10)
        self.assertEqual(bloques, sorted(bloques), f"el orden de los bloques no es tiempo, asignación, ahorro: {bloques}")
        self.assertEqual(set(bloques), {1, 2, 3})


FAMILIAS_POR_TABLA = {
    CALIDAD: {"accuracy", "relevance", "grounding"},
    CAMPANA: {"latency", "robustness", "availability"},
}


class CadaFamiliaVaALaTablaDeSuDetalleTests(unittest.TestCase):
    def test_exactitud_relevancia_y_fundamento_van_a_calidad_y_el_resto_a_campana(self):
        # Una fila por familia con un identificador propio; cada tabla de detalle debe mostrar exactamente las suyas
        # (las seis familias de la matriz se reparten entre las dos tablas, sin solaparse ni dejar ninguna fuera).
        todas = ["accuracy", "relevance", "grounding", "latency", "robustness", "availability"]
        preparacion = R.insertar_ejecucion("rl-f", "JUP-070", "2026-10-14T09:00:00Z", real=True)
        for familia in todas:
            preparacion += R.insertar_resultado("rl-f", familia, f"ZF-{familia}", valor=0.5)
        for clave, esperadas in FAMILIAS_POR_TABLA.items():
            vistas = {f["metric_id"] for f in datos_de(clave, preparacion)["filas"] if f["metric_id"].startswith("ZF-")}
            with self.subTest(tabla=clave[0]):
                self.assertEqual(vistas, {f"ZF-{familia}" for familia in esperadas})


UNIDADES = (
    # (unidad, valor insertado, texto esperado en `valor_texto`)
    ("tasa", 0.5, "50.0 %"),
    ("porcentaje", 12.5, "12.5 %"),
    ("ms", 1234.5, "1234.5 ms"),
    ("similitud", 0.617, "0.617"),
    ("recuento", 7, "7"),
    ("parejas", 4, "4"),
    ("eur_minor_2", 12345, "123.45 €"),
    ("zzz", 0.12345678, "0.1235 zzz"),
)


def preparacion_de_unidades() -> str:
    """Una ejecución de JUP-071 con una fila por unidad en tres grupos, para que la vean calidad, campaña y robustez."""
    sql = R.insertar_ejecucion("rl-u", "JUP-071", "2026-10-14T09:00:00Z", real=False, motivos=("sintetica",))
    for grupo, prefijo in (("accuracy", "QA"), ("latency", "QL"), ("robustness", "QR")):
        for i, (unidad, valor, _) in enumerate(UNIDADES):
            sql += R.insertar_resultado("rl-u", grupo, f"{prefijo}-{i}", valor=valor, unidad=unidad)
    return sql


class FormatoDelValorPorUnidadTests(unittest.TestCase):
    def test_las_tres_tablas_formatean_cada_unidad_igual(self):
        preparacion = preparacion_de_unidades()
        for clave, prefijo in ((CALIDAD, "QA"), (CAMPANA, "QL"), (ROBUSTEZ, "QR")):
            filas = {f["metric_id"]: f["valor_texto"].replace(",", ".")
                     for f in datos_de(clave, preparacion)["filas"] if f["metric_id"].startswith(prefijo + "-")}
            with self.subTest(tabla=clave[0]):
                self.assertEqual(filas, {f"{prefijo}-{i}": esperado for i, (_, _, esperado) in enumerate(UNIDADES)})


if __name__ == "__main__":
    unittest.main()
