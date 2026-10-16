"""Evolución de la latencia de la campaña (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisito de la spec «Latencia de la campaña en la evolución automática» (decisión D8 del diseño). La tarjeta pide ver la
latencia de la campaña evolucionar entre ejecuciones; el panel «Evolución de las métricas automáticas» solo dibuja
proporciones (`unit = 'tasa'`, en porcentaje) y la latencia está en milisegundos, así que va en un panel APARTE con las
mismas reglas:

* serie por clave de comparabilidad (`evaluation.comparable_runs`), solo la etapa `total` (`behavior = 'total'`), solo
  LAT-1 (mediana) y LAT-2 (percentil 95), solo puntos medidos en milisegundos, solo ejecuciones con fecha;
* una serie con menos de dos puntos medidos NO se dibuja (`medidos >= 2`, misma lógica que el panel de proporciones) y el panel
  dice «Sin datos: no hay con qué comparar»;
* la cadena de transformaciones es LA MISMA que la del panel de proporciones (reconstruye un marco por serie para que
  `spanNulls: false` no deje solo puntos sueltos), la unidad es `ms` y las ejecuciones no reales se dibujan discontinuas;
* con los datos versionados (dos campañas de JUP-070 con claves de comparabilidad distintas) devuelve 0 filas.

Fuera de la evolución, documentado en la guía: LAT-3 (máximo), LAT-4 (tasa de fallo), las demás etapas y GRD-2 / REL-4.

Escenario sintético (siempre con ROLLBACK sobre PostgreSQL real, con el rol de lectura): una serie real con LAT-1 y LAT-2, otra
no real, una donde LAT-2 solo se midió una vez, una ejecución sola, otra sin fecha, y filas que NO deben aparecer (otra
etapa, LAT-3, proporciones).

El panel se localiza por título, no por `id` ni posición. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_latency.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

TITULO = "Evolución de la latencia de la campaña"
TITULO_PROPORCIONES = "Evolución de las métricas automáticas"
SIN_COMPARAR = "Sin datos: no hay con qué comparar"


def panel():
    return R.por_titulo(TITULO, "A")


def consulta() -> str:
    return R.consulta_unica(panel())


def puntos(preparacion: str = "") -> dict:
    return R.ejecutar(consulta(), preparacion)


class EstructuraTests(unittest.TestCase):
    def test_es_una_serie_temporal_tipo_a_de_postgres_en_formato_time_series(self):
        p = panel()
        self.assertEqual(p["type"], "timeseries")
        self.assertEqual(p["datasource"], R.DS_POSTGRES)
        self.assertTrue(p["description"].startswith("Tipo: A"))
        self.assertEqual(len(p["targets"]), 1)
        objetivo = p["targets"][0]
        self.assertEqual(objetivo["datasource"], R.DS_POSTGRES)
        self.assertEqual(objetivo["format"], "time_series")
        self.assertIs(objetivo["rawQuery"], True)
        self.assertEqual(objetivo["editorMode"], "code")

    def test_aviso_unidad_y_huecos(self):
        por_defecto = R.defaults(panel())
        self.assertEqual(por_defecto.get("noValue"), SIN_COMPARAR)
        self.assertEqual(por_defecto.get("unit"), "ms")
        self.assertIs(por_defecto.get("custom", {}).get("spanNulls"), False, "ningún hueco se une con una línea")

    def test_las_no_reales_se_dibujan_con_linea_discontinua_como_en_las_proporciones(self):
        referencia = R.por_titulo(TITULO_PROPORCIONES, "A")
        # Misma convención que la gráfica de proporciones: override por regex `.*no real.*` con línea discontinua.
        esperado = [o for o in referencia["fieldConfig"]["overrides"]
                    if o["matcher"] == {"id": "byRegexp", "options": ".*no real.*"}]
        self.assertEqual(len(esperado), 1)
        obtenido = [o for o in panel()["fieldConfig"]["overrides"]
                    if o["matcher"] == {"id": "byRegexp", "options": ".*no real.*"}]
        self.assertEqual(obtenido, esperado)
        estilo = [p["value"] for p in obtenido[0]["properties"] if p["id"] == "custom.lineStyle"][0]
        self.assertEqual(estilo["fill"], "dash")
        self.assertTrue(estilo["dash"])

    def test_misma_cadena_de_transformaciones_que_el_panel_de_proporciones(self):
        # prepareTimeSeries(multi) -> seriesToRows -> filterByValue(Value no nulo) -> partitionByValues(Metric): lo que
        # se verificó con un Grafana real para que cada serie sea un marco sin nulos intercalados.
        referencia = R.por_titulo(TITULO_PROPORCIONES, "A")
        self.assertEqual([t["id"] for t in referencia["transformations"]],
                         ["prepareTimeSeries", "seriesToRows", "filterByValue", "partitionByValues"])
        self.assertEqual(panel().get("transformations"), referencia["transformations"])

    def test_la_consulta_filtra_latencia_total_en_ms_solo_medida_y_solo_ejecuciones_comparables(self):
        sql = R.plano(consulta())
        self.assertRegex(sql, r"evaluation\.comparable_runs\b")
        self.assertRegex(sql, r"grp\s*=\s*'latency'")
        self.assertRegex(sql, r"metric_id\s+IN\s*\(\s*'LAT-1'\s*,\s*'LAT-2'\s*\)|metric_id\s+IN\s*\(\s*'LAT-2'\s*,\s*'LAT-1'\s*\)")
        self.assertRegex(sql, r"behavior\s*=\s*'total'")
        self.assertRegex(sql, r"unit\s*=\s*'ms'")
        self.assertRegex(sql, r"status\s*=\s*'measured'")
        self.assertRegex(sql, r"run_at\s+IS\s+NOT\s+NULL")
        self.assertRegex(sql, r"\bmedidos\s*>=\s*2\b")
        self.assertNotRegex(sql, r"LAT-3|LAT-4")
        for alias in ("time", "metric", "value"):
            self.assertRegex(sql, rf"(?i)\bAS\s+{alias}\b")

    def test_las_series_no_dependen_del_selector_de_tiempo(self):
        self.assertNotIn("$__", consulta())


class ConDatosVersionadosTests(unittest.TestCase):
    def test_devuelve_cero_filas_porque_las_dos_campanas_no_son_comparables(self):
        # Las dos campañas de JUP-070 tienen claves de comparabilidad distintas (cambia el proveedor de embeddings):
        # ninguna serie llega a dos puntos y el panel enseña «Sin datos: no hay con qué comparar».
        panel()
        datos = puntos()
        self.assertEqual(R.nombres(datos), ["time", "metric", "value"])
        self.assertEqual(datos["filas"], [])


# --- Escenario sintético --------------------------------------------------------------------------------------------------


def serie(prefijo, clave, dias, *, real=True, motivos=(), lat1=(), lat2=(), lat2_no_medida=False):
    """Ejecuciones `prefijo-1..n` de la clave `clave` en `dias` (octubre de 2026, 10:00 UTC) con latencias de la etapa `total`."""
    sql = ""
    for indice, dia in enumerate(dias, start=1):
        run_id = f"{prefijo}-{indice}"
        fecha = None if dia is None else f"2026-10-{dia:02d}T10:00:00Z"
        sql += R.insertar_ejecucion(run_id, "JUP-070", fecha, real=real, motivos=motivos, clave=clave)
        if indice <= len(lat1):
            sql += R.insertar_resultado(run_id, "latency", "LAT-1", "total", valor=lat1[indice - 1], unidad="ms",
                                        denominador=28)
        if indice <= len(lat2):
            if lat2_no_medida and indice == len(lat2):
                sql += R.insertar_resultado(run_id, "latency", "LAT-2", "total", estado="not_measured", unidad="ms",
                                            denominador=28)
            else:
                sql += R.insertar_resultado(run_id, "latency", "LAT-2", "total", valor=lat2[indice - 1], unidad="ms",
                                            denominador=28)
    return sql


PREPARACION = (
    # K1 real: LAT-1 y LAT-2 con dos puntos medidos, más filas que NO deben salir (otra etapa, LAT-3, una proporción).
    serie("ll-a", "k-lat-a", (10, 12), lat1=(3000.0, 3100.0), lat2=(4000.0, 4200.0))
    + "".join(R.insertar_resultado(f"ll-a-{i}", "latency", "LAT-1", "generation", valor=v, unidad="ms", denominador=28)
              + R.insertar_resultado(f"ll-a-{i}", "latency", "LAT-3", "total", valor=v + 3444, unidad="ms", denominador=28)
              + R.insertar_resultado(f"ll-a-{i}", "accuracy", "ACC-2", valor=0.5, numerador=5, denominador=10)
              for i, v in ((1, 2111.0), (2, 2222.0)))
    # K2 no real (plantilla): las dos series se dibujan, con «no real» en su nombre.
    + serie("ll-b", "k-lat-b", (11, 13), real=False, motivos=("plantilla",), lat1=(100.0, 110.0), lat2=(150.0, 160.0))
    # K3 real: LAT-1 con dos puntos; LAT-2 medida solo en la primera -> la serie LAT-2 no llega a dos y no sale.
    + serie("ll-c", "k-lat-c", (14, 15), lat1=(7000.0, 7100.0), lat2=(8000.0, 8100.0), lat2_no_medida=True)
    # K4: una ejecución sola en su clave (no comparable). K5: una con fecha y otra sin fecha (solo cuenta la fechada).
    + serie("ll-d", "k-lat-d", (16,), lat1=(9000.0,), lat2=(9500.0,))
    + serie("ll-e", "k-lat-e", (17, None), lat1=(6000.0, 6100.0), lat2=(6500.0, 6600.0))
)

ESPERADOS = {
    ("ll-a-1", "LAT-1", 3000.0), ("ll-a-2", "LAT-1", 3100.0), ("ll-a-1", "LAT-2", 4000.0), ("ll-a-2", "LAT-2", 4200.0),
    ("ll-b-1", "LAT-1", 100.0), ("ll-b-2", "LAT-1", 110.0), ("ll-b-1", "LAT-2", 150.0), ("ll-b-2", "LAT-2", 160.0),
    ("ll-c-1", "LAT-1", 7000.0), ("ll-c-2", "LAT-1", 7100.0),
}


class ConEjecucionesComparablesSinteticasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel()
        cls.datos = puntos(PREPARACION)
        fechas = {datetime.fromisoformat(f["run_at"]).astimezone(timezone.utc): f["run_id"]
                  for f in R.administrar("SELECT run_id, run_at FROM evaluation.runs WHERE run_at IS NOT NULL",
                                         PREPARACION)}
        cls.puntos = []
        for fila in cls.datos["filas"]:
            instante = datetime.fromisoformat(fila["time"]).astimezone(timezone.utc)
            cls.puntos.append((fechas[instante], fila["metric"], fila["value"]))

    def metrica_de(self, etiqueta):
        ids = [m for m in ("LAT-1", "LAT-2") if re.search(rf"(?<![\w-]){m}(?![\w-])", etiqueta)]
        self.assertEqual(len(ids), 1, etiqueta)
        return ids[0]

    def test_columnas_y_tipos_de_una_serie_temporal(self):
        self.assertEqual(R.nombres(self.datos), ["time", "metric", "value"])
        tipos = dict(self.datos["columnas"])
        self.assertEqual(tipos["time"], "timestamp with time zone")
        self.assertIn(tipos["metric"], ("text", "character varying"))
        self.assertIn(tipos["value"], ("double precision", "numeric"))

    def test_devuelve_exactamente_los_puntos_de_lat_1_y_lat_2_de_la_etapa_total_en_ms(self):
        obtenidos = {(run, self.metrica_de(etiqueta), valor) for run, etiqueta, valor in self.puntos}
        self.assertEqual(len(obtenidos), len(self.puntos), "punto repetido")
        self.assertEqual(obtenidos, ESPERADOS)

    def test_no_se_mezclan_etapas_percentiles_ni_proporciones(self):
        # Valores que NO pueden aparecer: LAT-1 de otra etapa (2111, 2222), LAT-3 total (5555, 5666) y el 0.5 de ACC-2.
        valores = {valor for _, _, valor in self.puntos}
        self.assertFalse(valores & {2111.0, 2222.0, 5555.0, 5666.0, 0.5})
        runs = {run for run, _, _ in self.puntos}
        self.assertFalse(runs & {"ll-d-1", "ll-e-1", "ll-e-2"}, "una ejecución sola o sin fecha no forma serie")

    def test_una_serie_con_un_solo_punto_medido_no_se_dibuja(self):
        # LAT-2 de la serie K3 solo se midió en la primera ejecución: ni un punto suelto (regla `medidos >= 2`).
        runs_lat2_c = {run for run, etiqueta, _ in self.puntos if run.startswith("ll-c") and self.metrica_de(etiqueta) == "LAT-2"}
        self.assertEqual(runs_lat2_c, set())
        # Y LAT-1 de esa misma clave sí se dibuja: la regla es por serie, no por ejecución.
        self.assertEqual({run for run, etiqueta, _ in self.puntos
                          if run.startswith("ll-c") and self.metrica_de(etiqueta) == "LAT-1"}, {"ll-c-1", "ll-c-2"})

    def test_cada_serie_tiene_su_propia_etiqueta_con_fuente_y_metrica(self):
        series = {}
        for run, etiqueta, _ in self.puntos:
            series.setdefault(etiqueta, set()).add(run.rsplit("-", 1)[0])
        # Una etiqueta = una clave de comparabilidad: las series de claves distintas jamás se unen con una línea.
        for etiqueta, claves in series.items():
            with self.subTest(etiqueta=etiqueta):
                self.assertEqual(len(claves), 1, f"la serie {etiqueta!r} mezcla ejecuciones no comparables")
                self.assertIn("JUP-070", etiqueta)
        self.assertEqual(len(series), 5, "K1 x2, K2 x2 y K3 x1")

    def test_las_no_reales_llevan_no_real_y_su_motivo_y_las_reales_no(self):
        for run, etiqueta, _ in self.puntos:
            with self.subTest(run=run):
                if run.startswith("ll-b"):
                    self.assertIn("no real", etiqueta)
                    self.assertIn("plantilla", etiqueta)
                else:
                    self.assertNotIn("no real", etiqueta)

    def test_una_ejecucion_sin_fecha_no_interrumpe_ni_aporta_puntos(self):
        # K5 tiene una ejecución fechada y otra sin fecha: `comparable_runs` solo cuenta las fechadas, así que no hay serie.
        self.assertFalse([p for p in self.puntos if p[0].startswith("ll-e")])


if __name__ == "__main__":
    unittest.main()
