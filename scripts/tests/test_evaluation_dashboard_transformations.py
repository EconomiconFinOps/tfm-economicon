"""Cadena de transformaciones de los paneles de evolución del dashboard de evaluación (JUP-121, hallazgo B1 del QA).

Problema que se corrige: las dos gráficas de evolución (A5 «automáticas» y A6 «juicio humano», que consultan
`evaluation.comparable_runs`) devuelven formato largo `time, metric, value`. Grafana lo pivota a formato ancho (una
columna por `metric`) y, con `spanNulls: false` (D6 del diseño: ningún hueco se une con una línea), cada fila que
pertenece a OTRA serie deja un `null` en la columna de esta. Si varias series se intercalan en el tiempo, no queda
ningún par de puntos consecutivos sin nulo entre ellos y la gráfica solo dibuja puntos sueltos, sin líneas.

La solución es una cadena de `transformations` de panel que reconstruye un marco por serie, comprobada en un Grafana
real con capturas:

  1. `prepareTimeSeries` con `format: "multi"`  -> un marco por serie (conserva `Metric` como campo).
  2. `seriesToRows`                              -> vuelve a un único marco largo `Time, Metric, Value`.
  3. `filterByValue` (incluye solo `Value` no nulo) -> descarta las filas vacías que dejó el pivotado.
  4. `partitionByValues` por `Metric`, `asLabels: false` -> un marco por serie, sin nulos intercalados.

Los tests congelados (`test_evaluation_dashboard_structure.py`) solo fijan `format: "time_series"` y
`spanNulls: false`; no dicen nada de esta cadena, de modo que un cambio accidental (quitar un paso, reordenarlos,
cambiar `multi` por `wide`) rompería las líneas sin que ningún test lo notara. Este módulo fija la cadena EXACTA y lo
que debe seguir intacto a su alrededor. Es estático (sin Docker ni base de datos): solo lee el JSON.

Los esperados se copian literalmente del dashboard actual (no se deducen de la documentación de Grafana): lo que se
protege es la combinación que se verificó con un Grafana real.

Ruta: por defecto el fichero real; `EVALUATION_DASHBOARD_JSON` permite apuntar a una copia (se usa para comprobar que
cada mutación se detecta). El localizador de paneles se reutiliza del módulo de estructura para que ambos hablen de
los mismos paneles `a5` y `a6`.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_evaluation_dashboard_structure as S  # noqa: E402  (localizador de paneles y ruta del dashboard)

# Cadena esperada, copiada literalmente del dashboard. El ORDEN importa: `partitionByValues` antes de filtrar no
# serviría y `filterByValue` antes de `seriesToRows` filtraría marcos distintos de los que hay que filtrar.
TRANSFORMACIONES_ESPERADAS = [
    {"id": "prepareTimeSeries", "options": {"format": "multi"}},
    {"id": "seriesToRows", "options": {}},
    {
        "id": "filterByValue",
        "options": {
            "type": "include",
            "match": "any",
            "filters": [{"fieldName": "Value", "config": {"id": "isNotNull", "options": {}}}],
        },
    },
    {
        "id": "partitionByValues",
        "options": {"fields": ["Metric"], "naming": {"asLabels": False}},
    },
]

IDS_ESPERADOS = ["prepareTimeSeries", "seriesToRows", "filterByValue", "partitionByValues"]
NO_COMPARABLE = "Sin datos: no hay con qué comparar"
OVERRIDE_NO_REAL = {"id": "byRegexp", "options": ".*no real.*"}

# Claves de las transformaciones que solo pertenecen a los paneles de evolución.
IDS_DE_LA_CADENA = {"prepareTimeSeries", "partitionByValues"}


def evolucion() -> list:
    """`[(clave, panel)]` de los dos paneles de evolución (`a5` automática y `a6` con juicio humano)."""
    return [("a5", S._unico("a5")), ("a6", S._unico("a6"))]


def evoluciones_con_cadena() -> list:
    """`[(clave, panel)]` de los tres paneles que llevan la cadena: las dos evoluciones de arriba y la de la latencia.

    `jup-121-lectura-dashboard` (D8) añade una tercera evolución, la de la latencia de la campaña, con la misma
    cadena. `evolucion()` se deja como estaba (las pruebas de la cadena exacta son de calidad: unidad `percentunit`);
    esta lista solo se usa para el ALCANCE de la cadena.
    """
    return evolucion() + [("a_evolucion_latencia", S._unico("a_evolucion_latencia"))]


def _ids(panel) -> list:
    return [t.get("id") for t in panel.get("transformations", [])]


def _declara_cadena(panel) -> bool:
    """El panel usa `prepareTimeSeries` o `partitionByValues` en su lista de transformaciones (no en otro sitio)."""
    return bool(IDS_DE_LA_CADENA & set(_ids(panel)))


class CadenaExactaTests(unittest.TestCase):
    def test_las_dos_evoluciones_llevan_exactamente_las_cuatro_transformaciones_en_orden(self):
        # Lista exacta: ni una más (una transformación extra podría reintroducir nulos) ni una menos ni reordenadas.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                transformaciones = panel.get("transformations")
                self.assertIsInstance(transformaciones, list)
                self.assertEqual(_ids(panel), IDS_ESPERADOS)
                self.assertEqual(transformaciones, TRANSFORMACIONES_ESPERADAS)

    def test_prepare_time_series_usa_formato_multi(self):
        # `multi` es lo que conserva `Metric` como campo de cada marco; `wide` reproduciría el pivotado con nulos y
        # `many` descartaría la columna de etiqueta que necesita el paso final.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                paso = panel["transformations"][0]
                self.assertEqual(paso["id"], "prepareTimeSeries")
                self.assertEqual(paso["options"], {"format": "multi"})

    def test_series_to_rows_va_segunda_y_sin_opciones(self):
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                paso = panel["transformations"][1]
                self.assertEqual(paso["id"], "seriesToRows")
                self.assertEqual(paso["options"], {})

    def test_filter_by_value_incluye_solo_los_valores_no_nulos(self):
        # Es el paso que quita los nulos del pivotado. Debe INCLUIR las filas con `Value` no nulo (`isNotNull`): con
        # `isNull` o con `exclude` se quedarían justo las filas equivocadas.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                paso = panel["transformations"][2]
                self.assertEqual(paso["id"], "filterByValue")
                opciones = paso["options"]
                self.assertEqual(opciones["type"], "include")
                self.assertEqual(opciones["match"], "any")
                self.assertEqual(
                    opciones["filters"],
                    [{"fieldName": "Value", "config": {"id": "isNotNull", "options": {}}}],
                )
                self.assertEqual(set(opciones), {"type", "match", "filters"})

    def test_partition_by_values_parte_por_metric_sin_etiquetas_en_el_nombre(self):
        # Una serie por valor de `Metric`; `asLabels: false` deja el nombre de la serie como el propio valor (el
        # override `.*no real.*` casa con ese nombre, así que con `true` el estilo discontinuo dejaría de aplicarse).
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                paso = panel["transformations"][3]
                self.assertEqual(paso["id"], "partitionByValues")
                self.assertEqual(paso["options"]["fields"], ["Metric"])
                self.assertIs(paso["options"]["naming"]["asLabels"], False)
                self.assertEqual(set(paso["options"]), {"fields", "naming"})
                self.assertEqual(paso["options"]["naming"], {"asLabels": False})

    def test_la_particion_es_el_ultimo_paso(self):
        # Cualquier transformación posterior volvería a unir las series en un marco ancho.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                self.assertEqual(panel["transformations"][-1]["id"], "partitionByValues")

    def test_las_dos_cadenas_son_identicas_entre_si(self):
        # Una divergencia entre A5 y A6 significaría que una se arregló y la otra no (o que se estropeó solo una).
        (_, automatica), (_, humano) = evolucion()
        self.assertEqual(automatica["transformations"], humano["transformations"])


class AjustesQueLaCadenaNecesitaTests(unittest.TestCase):
    """Lo que debe seguir como estaba: la cadena arregla las líneas SIN relajar el contrato de D6 ni los rótulos."""

    def test_el_target_sigue_en_formato_time_series(self):
        # `prepareTimeSeries` espera el formato largo de la consulta; con `table` no habría pivotado que reconstruir.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                self.assertTrue(panel["targets"])
                for objetivo in panel["targets"]:
                    self.assertEqual(objetivo.get("format"), "time_series")

    def test_span_nulls_sigue_a_false(self):
        # Las líneas se arreglan quitando los nulos ajenos, NO uniendo huecos: `true` taparía un hueco real (D6).
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                self.assertIs(panel["fieldConfig"]["defaults"]["custom"]["spanNulls"], False)

    def test_el_aviso_sin_datos_y_la_unidad_se_conservan(self):
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                defaults = panel["fieldConfig"]["defaults"]
                self.assertEqual(defaults.get("noValue"), NO_COMPARABLE)
                self.assertEqual(defaults.get("unit"), "percentunit")

    def test_el_override_de_ejecuciones_no_reales_sigue_discontinuo(self):
        # Exactamente un override con ese `matcher`, y con un estilo de línea discontinuo.
        for clave, panel in evolucion():
            with self.subTest(pieza=clave):
                overrides = panel["fieldConfig"].get("overrides", [])
                propios = [o for o in overrides if o.get("matcher") == OVERRIDE_NO_REAL]
                self.assertEqual(len(propios), 1, overrides)
                estilos = [p for p in propios[0].get("properties", []) if p.get("id") == "custom.lineStyle"]
                self.assertEqual(len(estilos), 1, propios[0])
                valor = estilos[0].get("value")
                self.assertIsInstance(valor, dict)
                self.assertEqual(valor.get("fill"), "dash")
                self.assertTrue(valor.get("dash"), valor)


class AlcanceDeLaCadenaTests(unittest.TestCase):
    """La cadena es solo de las tres evoluciones: las tablas y las señales en vivo no deben heredarla."""

    def _otros_paneles(self):
        propios = {id(p) for _, p in evoluciones_con_cadena()}
        return [p for p in S.paneles() if id(p) not in propios]

    def test_hay_otros_paneles_que_comprobar(self):
        # Salvaguarda: el resto de pruebas no puede pasar «por vacío».
        otros = self._otros_paneles()
        self.assertGreaterEqual(len(otros), 15)
        self.assertTrue([p for p in otros if p.get("type") == "table"])

    def test_ningun_otro_panel_declara_prepare_time_series_ni_partition_by_values(self):
        # Las tablas de A y B (y cualquier otro panel) no deben llevar la cadena: partirían una tabla en varias.
        for panel in self._otros_paneles():
            with self.subTest(panel=panel.get("title")):
                self.assertFalse(_declara_cadena(panel), _ids(panel))
                # Tampoco en ningún otro lugar del panel (p. ej. anidado), por si cambia la forma de declararlo.
                texto = json.dumps(panel)
                self.assertNotIn("partitionByValues", texto)
                self.assertNotIn("prepareTimeSeries", texto)

    def test_las_tablas_de_a_y_b_no_llevan_transformaciones_de_la_cadena(self):
        tablas = [(letra, p) for letra, p in S.contenido() if letra in "AB" and p.get("type") == "table"]
        self.assertGreaterEqual(len(tablas), 6)
        for letra, panel in tablas:
            with self.subTest(seccion=letra, panel=panel["title"]):
                self.assertFalse(_declara_cadena(panel), _ids(panel))

    def test_los_paneles_de_prometheus_de_c_no_llevan_partition_by_values(self):
        # Las series de C ya llegan como un marco por serie desde Prometheus: partirlas de nuevo las rompería.
        datos = [p for p in S.de_seccion("C") if p.get("type") != "text"]
        self.assertEqual(len(datos), 5)
        for panel in datos:
            with self.subTest(panel=panel["title"]):
                self.assertNotIn("partitionByValues", _ids(panel))
                self.assertNotIn("partitionByValues", json.dumps(panel))

    def test_la_anotacion_no_lleva_transformaciones(self):
        # Las anotaciones de Grafana no admiten esta cadena y la consulta ya devuelve `time, text, tags`.
        propias = S.anotaciones_propias()
        self.assertEqual(len(propias), 1)
        for entrada in S.dashboard().get("annotations", {}).get("list", []):
            with self.subTest(anotacion=entrada.get("name")):
                self.assertNotIn("transformations", entrada)
                self.assertNotIn("transformations", entrada.get("target", {}))
                texto = json.dumps(entrada)
                self.assertNotIn("partitionByValues", texto)
                self.assertNotIn("prepareTimeSeries", texto)

    def test_la_cadena_solo_aparece_en_los_tres_paneles_de_evolucion(self):
        # Vista global: en todo el fichero la cadena aparece exactamente tres veces cada paso (A5, A6 y la evolución
        # de la latencia de la campaña, D8 de `jup-121-lectura-dashboard`).
        texto = json.dumps(S.dashboard())
        self.assertEqual(texto.count("partitionByValues"), 3)
        self.assertEqual(texto.count("prepareTimeSeries"), 3)

    def test_los_paneles_con_transformaciones_son_las_tres_evoluciones_y_la_matriz(self):
        # La matriz de resultados por métrica y ejecución (`groupingToMatrix` + `organize`) es el único panel con
        # transformaciones que no es una evolución; ninguna otra tabla ni señal en vivo las lleva.
        con = [p["title"] for p in S.paneles() if p.get("transformations")]
        esperados = [p["title"] for _, p in evoluciones_con_cadena()] + [S._unico("a_matriz")["title"]]
        self.assertEqual(sorted(con), sorted(esperados))
        self.assertEqual(_ids(S._unico("a_matriz")), ["groupingToMatrix", "organize"])


if __name__ == "__main__":
    unittest.main()
