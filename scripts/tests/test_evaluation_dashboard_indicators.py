"""Panel «Indicadores de robustez (JUP-071)» del dashboard de evaluación: lo que MUESTRA (JUP-071, grupo 7).

La consulta del panel se ejecuta TAL CUAL está en el dashboard contra el servidor PostgreSQL desechable de
`test_evaluation_dashboard_visible.py` (que se reutiliza: contenedor, rol de lectura y caché de resultados) con datos
fabricados para forzar cada caso:

* sale la última ejecución de JUP-071 QUE TIENE indicadores, aunque haya otra posterior sin ellos;
* solo salen filas de los grupos `rob_*` (los recuentos de casos son del detalle por fila);
* el orden es el de las cuatro familias y, dentro de cada una, el de lectura;
* el texto del valor lleva su unidad y los tamaños se redondean; lo no medido llega NULL (el panel lo muestra «No medido»)
  y nunca un cero, y conserva su base;
* sin ninguna ejecución con indicadores, como pasa con el manifiesto versionado solo, el panel no devuelve filas.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`. Ejecución: `python -m unittest scripts/tests/test_evaluation_dashboard_indicators.py`
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_evaluation_dashboard_queries as Q  # noqa: E402
import test_evaluation_dashboard_structure as S  # noqa: E402
import test_evaluation_dashboard_visible as V  # noqa: E402

TITULO = "Indicadores de robustez (JUP-071)"
COLUMNAS = ["run_at", "estado", "familia", "indicador", "valor_texto", "base", "decide"]
FAMILIAS = ["Calidad del core", "Recuperación", "Rendimiento del sistema", "Conversación y usuario"]


def tasa(grp, metric_id, valor, numerador, denominador, juicio="human"):
    return Q.fila_otra(grp, metric_id, "all", "measured", "tasa", judgment=juicio, value=valor, numerator=numerador,
                       denominator=denominador)


def sin_medir(grp, metric_id, unidad="tasa", juicio="human"):
    return Q.fila_otra(grp, metric_id, "all", "not_measured", unidad, judgment=juicio, denominator=0)


def media(grp, metric_id, unidad, valor, denominador):
    return Q.fila_otra(grp, metric_id, "all", "measured", unidad, value=valor, denominator=denominador)


VIEJOS = [tasa("rob_core", "invention_rate", 0.5, 1, 2)]
ULTIMOS = [
    media("rob_retrieval", "fragments_per_query", "fragmentos", 10.5417, 24),
    tasa("rob_core", "invention_rate", 0.0, 0, 55),
    media("rob_system", "prompt_size_per_query", "unidades", 17410.6667, 27),
    Q.fila_otra("rob_system", "unmeasured_by_cause", "operation_failed", "measured", "casos", value=2, denominator=29),
    Q.fila_otra("rob_system", "unmeasured_by_cause", "evidence_unverified", "measured", "casos", value=3, denominator=29),
    media("rob_system", "cost_per_query", "usd", 0.0065268, 27),
    sin_medir("rob_conversation", "request_rate"),
    tasa("rob_core", "required_coverage", 0.652173913, 30, 46),
    # Un recuento de casos de la misma ejecución: es del detalle por fila, no un indicador.
    Q.fila_otra("cases", "cases", "all", "pass", "casos", count=7, denominator=29),
]
SIN_INDICADORES = [Q.fila_otra("cases", "cases", "all", "pass", "casos", count=7, denominator=29)]


def _construir(ejecuciones) -> dict:
    with tempfile.TemporaryDirectory(prefix="evaluation-indicators-") as directorio:
        base = Path(directorio)
        entradas = []
        for run_id, dia, filas in ejecuciones:
            ejecucion = {**Q.BASE_RUN, "run_id": run_id, "source": "JUP-071", "suite": "JUP-071", "run_at": V._dia(dia),
                         "generation_model": None}
            ruta = base / f"{run_id}.json"
            ruta.write_text(json.dumps({"contract_version": 1, "run": ejecucion, "results": filas}), encoding="utf-8")
            entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": False})
        manifiesto = base / "manifest.json"
        manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
        return V.tool.build_dataset([manifiesto], root=base)


CON_INDICADORES = V.Conjunto("indicadores", lambda: _construir([("IND-1", 20, VIEJOS), ("IND-2", 21, ULTIMOS), ("IND-3", 22, SIN_INDICADORES)]))
SOLO_DETALLE = V.Conjunto("sin-indicadores", lambda: _construir([("IND-3", 22, SIN_INDICADORES)]))


def tearDownModule() -> None:
    # El servidor y su estado son los del módulo de las pruebas visibles: al pararlo se olvida también qué conjunto y qué rol
    # tenía cargados, o el módulo siguiente creería tenerlos en un contenedor nuevo y vacío.
    V.tearDownModule()
    V._ESTADO.update(conjunto=None, rol=False)
    V._RESULTADOS.clear()


def consulta() -> str:
    panel = [p for p in S.de_seccion("A") if p["title"] == TITULO]
    if len(panel) != 1:
        raise AssertionError(f"se esperaba un único panel «{TITULO}» y hay {len(panel)}")
    return Q.consulta_panel(panel[0])


def filas(conjunto) -> list:
    return V.ejecutar(consulta(), conjunto)["filas"]


class PanelDeIndicadoresTests(unittest.TestCase):
    def test_sale_la_ultima_ejecucion_con_indicadores_aunque_haya_otra_posterior_sin_ellos(self):
        datos = filas(CON_INDICADORES)
        self.assertEqual(len(datos), len(ULTIMOS) - 1)
        self.assertEqual({fila["run_at"] for fila in datos}, {"2026-10-21T10:00:00+00:00"})
        self.assertNotIn("1 de 2", {fila["base"] for fila in datos})

    def test_las_columnas_son_las_del_panel(self):
        columnas = [nombre for nombre, _ in V.ejecutar(consulta(), CON_INDICADORES)["columnas"]]
        self.assertEqual(columnas, COLUMNAS)

    def test_solo_salen_filas_de_los_grupos_de_indicadores(self):
        indicadores = {fila["indicador"] for fila in filas(CON_INDICADORES)}
        self.assertFalse([i for i in indicadores if "cases" in i or "caso" == i.lower()], indicadores)
        self.assertEqual(len(indicadores), len(ULTIMOS) - 1)

    def test_el_orden_es_el_de_las_familias_y_el_de_lectura(self):
        datos = filas(CON_INDICADORES)
        orden = [FAMILIAS.index(fila["familia"]) for fila in datos]
        self.assertEqual(orden, sorted(orden))
        self.assertEqual([fila["indicador"] for fila in datos if fila["familia"] == "Calidad del core"],
                         ["Invenciones: prohibiciones incumplidas", "Cobertura de lo requerido"])
        self.assertEqual([fila["indicador"] for fila in datos if fila["familia"] == "Rendimiento del sistema"],
                         ["Casos sin medir · operación fallida", "Casos sin medir · evidencia sin verificar",
                          "Coste por consulta (informado por el servidor)", "Tamaño de la entrada por consulta"])

    def test_el_texto_del_valor_lleva_su_unidad_y_los_tamanos_se_redondean(self):
        por_indicador = {fila["indicador"]: fila for fila in filas(CON_INDICADORES)}
        esperado = {
            "Invenciones: prohibiciones incumplidas": ("0.0 %", "0 de 55"),
            "Cobertura de lo requerido": ("65.2 %", "30 de 46"),
            "Fragmentos recuperados por consulta": ("10.5 fragmentos", "sobre 24"),
            "Casos sin medir · operación fallida": ("2 casos", "sobre 29"),
            "Casos sin medir · evidencia sin verificar": ("3 casos", "sobre 29"),
            "Coste por consulta (informado por el servidor)": ("0.0065 USD", "sobre 27"),
            "Tamaño de la entrada por consulta": ("17411 unidades", "sobre 27"),
        }
        for indicador, (valor, base) in esperado.items():
            with self.subTest(indicador=indicador):
                self.assertEqual((por_indicador[indicador]["valor_texto"], por_indicador[indicador]["base"]), (valor, base))

    def test_lo_no_medido_llega_nulo_y_conserva_su_base_nunca_un_cero(self):
        fila = next(f for f in filas(CON_INDICADORES) if f["indicador"] == "Casos de aclaración que piden el dato")
        self.assertIsNone(fila["valor_texto"])
        self.assertEqual(fila["base"], "sobre 0")
        self.assertEqual(fila["decide"], "Juicio humano")

    def test_quien_decide_distingue_el_juicio_humano_de_la_regla(self):
        por_indicador = {fila["indicador"]: fila["decide"] for fila in filas(CON_INDICADORES)}
        self.assertEqual(por_indicador["Invenciones: prohibiciones incumplidas"], "Juicio humano")
        self.assertEqual(por_indicador["Fragmentos recuperados por consulta"], "Automático")

    def test_el_tipo_de_ejecucion_dice_que_no_hay_modelo_verificado(self):
        estados = {fila["estado"] for fila in filas(CON_INDICADORES)}
        self.assertEqual(len(estados), 1)
        self.assertTrue(next(iter(estados)).startswith("no real"), estados)

    def test_sin_ninguna_ejecucion_con_indicadores_el_panel_no_devuelve_filas(self):
        self.assertEqual(filas(SOLO_DETALLE), [])


if __name__ == "__main__":
    unittest.main()
