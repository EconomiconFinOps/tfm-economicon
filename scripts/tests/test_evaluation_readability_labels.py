"""Etiquetas de las tablas y unidades de la sección B (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisitos de la spec que fija este módulo (decisiones D5 y D6 del diseño):

* «Etiquetas con un solo sentido»: hoy «Estado» designa a la vez el tipo de ejecución (real / no real) y el estado de los
  casos, «Resultado» es la columna `status` (que solo repite «Medido») y «Conducta» es el `behavior` en inglés. Se corrige así:
  - la clasificación real o no real (columna `estado` de la consulta) se muestra como «Tipo de ejecución» en TODAS las
    tablas que la llevan; «Estado» no es el rótulo de ninguna columna;
  - en las tablas de detalle por fila (exactitud/relevancia/fundamento, latencia/formato/disponibilidad y robustez) la
    columna `status` está OCULTA (todo está medido; lo no medido sigue leyéndose «No medido» por el valor nulo);
  - `behavior` pasa a «Variante» con el texto traducido en una columna nueva `variante` de la consulta; `behavior` queda
    SIN CAMBIAR en la consulta (la conciliación con los informes originales lo usa) y oculta;
  - ninguna columna visible se llama «Conducta» ni «Resultado» en esas tablas.
* «Unidades legibles en la sección B»: la tabla de negocio añade `numerador_texto` y `denominador_texto` con la unidad del
  valor (milisegundos -> minutos con « min», céntimos -> euros con « €»); `numerator` y `denominator` en bruto siguen en
  la consulta (la conciliación los lee) pero ocultos. Con el manifiesto versionado ninguna celda visible de numerador o
  denominador contiene `360000` ni `70000` y el tiempo ahorrado se ve como «6.0 min».

Los paneles se localizan por título, no por `id` ni posición. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_labels.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

TIPO_DE_EJECUCION = "Tipo de ejecución"
TABLA_DE_ESTADOS = "Estado de los casos por ejecución"
DETALLES = {
    "calidad": "Exactitud, relevancia y fundamento",
    "campaña": "Latencia, formato y disponibilidad de la campaña",
    "robustez": "Robustez (JUP-071)",
}
TABLA_B = "Tiempo, asignación y ahorro"
PROHIBIDAS_VISIBLES = {"Conducta", "Resultado"}

# Traducciones fijadas por la spec (sin tildes y en minúsculas: se compara normalizando acentos).
VARIANTES = {
    "all": "todas", "judged": "con juicio humano", "clarify": "aclarar", "abstain": "abstenerse", "answer": "responder",
    "median": "mediana", "q1": "primer cuartil", "q3": "tercer cuartil", "embedding": "embedding",
    "retrieval": "recuperacion", "generation": "generacion", "total": "total",
}
CATEGORIAS_STR2 = ("timeout", "connection", "transport", "authentication", "request", "redirect", "rate_limit",
                   "upstream", "invalid_response", "schema_validation")


def detalle(clave: str) -> dict:
    return R.por_titulo(DETALLES[clave], "A")


def tablas_de_a_y_b() -> list:
    return [p for letra in "AB" for p in R.de_seccion(letra) if p["type"] == "table"]


def muestra_no_medido(panel) -> bool:
    """El nulo se lee «No medido»: `noValue` «No medido» o mapeo de `null` a «No medido» en los valores por defecto."""
    por_defecto = R.defaults(panel)
    if por_defecto.get("noValue") == "No medido":
        return True
    return any(m.get("type") == "special" and m.get("options", {}).get("match") == "null"
               and m.get("options", {}).get("result", {}).get("text") == "No medido"
               for m in por_defecto.get("mappings", []))


class TipoDeEjecucionTests(unittest.TestCase):
    def test_la_columna_estado_se_muestra_como_tipo_de_ejecucion_en_todas_las_tablas_que_la_llevan(self):
        con_estado = [p for p in tablas_de_a_y_b() if re.search(r"(?i)\bAS\s+estado\b", R.sql_de(p))]
        # Ejecuciones, estados de casos, calidad, campaña, calibración, benchmark, robustez y negocio: ocho como mínimo.
        self.assertGreaterEqual(len(con_estado), 8, [p["title"] for p in con_estado])
        for panel in con_estado:
            with self.subTest(panel=panel["title"]):
                self.assertEqual(R.nombre_visible(panel, "estado"), TIPO_DE_EJECUCION)
                self.assertFalse(R.oculta(panel, "estado"), "el tipo de ejecución debe verse")

    def test_ninguna_columna_se_llama_estado_salvo_en_la_tabla_de_estados_de_los_casos(self):
        # «Estado» designa SOLO el estado de los casos. Se revisan todos los rótulos (`displayName`) de todas las tablas.
        for panel in tablas_de_a_y_b():
            for override in panel.get("fieldConfig", {}).get("overrides", []):
                for propiedad in override.get("properties", []):
                    if propiedad["id"] == "displayName" and propiedad["value"] == "Estado":
                        with self.subTest(panel=panel["title"]):
                            self.assertTrue(panel["title"].startswith(TABLA_DE_ESTADOS), panel["title"])
                            self.assertNotEqual(override["matcher"]["options"], "estado",
                                                "la clasificación real / no real no puede llamarse «Estado»")

    def test_el_color_de_las_ejecuciones_no_reales_se_conserva_en_la_columna(self):
        # El cambio es de rótulo: la regla que colorea «no real…» en la columna sigue donde estaba.
        for panel in tablas_de_a_y_b():
            if re.search(r"(?i)\bAS\s+estado\b", R.sql_de(panel)):
                with self.subTest(panel=panel["title"]):
                    props = R.propiedades(panel, "estado")
                    self.assertIn("mappings", props)
                    self.assertEqual(props.get("custom.cellOptions", {}).get("type"), "color-text")


class DetalleDeLasTablasPorFilaTests(unittest.TestCase):
    def test_la_columna_status_esta_oculta_y_nada_visible_se_llama_conducta_ni_resultado(self):
        for clave in DETALLES:
            panel = detalle(clave)
            with self.subTest(panel=panel["title"]):
                self.assertTrue(R.oculta(panel, "status"), "`status` solo repetía «Medido»: se oculta")
                # Rótulos explícitos: ninguna columna VISIBLE se llama «Conducta» ni «Resultado».
                for override in panel["fieldConfig"]["overrides"]:
                    columna = override["matcher"]["options"]
                    if not R.oculta(panel, columna):
                        self.assertNotIn(R.nombre_visible(panel, columna), PROHIBIDAS_VISIBLES, columna)

    def test_lo_no_medido_se_sigue_leyendo_no_medido(self):
        # Sin la columna `status`, el nulo del valor es lo único que dice que no se midió: debe mapearse a «No medido».
        for clave in DETALLES:
            with self.subTest(panel=DETALLES[clave]):
                self.assertTrue(muestra_no_medido(detalle(clave)))

    def test_behavior_se_muestra_como_variante_con_el_texto_traducido(self):
        for clave in ("calidad", "campaña"):
            panel = detalle(clave)
            with self.subTest(panel=panel["title"]):
                self.assertRegex(R.sql_de(panel), r"(?i)\bAS\s+variante\b")
                self.assertEqual(R.nombre_visible(panel, "variante"), "Variante")
                self.assertFalse(R.oculta(panel, "variante"))
                # `behavior` sigue en la consulta (la conciliación lo lee; se comprueba contra la base más abajo) y oculto.
                self.assertTrue(R.oculta(panel, "behavior"))


class VarianteContraPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        detalle("calidad")  # sin el panel falla antes de arrancar Docker
        cls.calidad = R.ejecutar(R.consulta_unica(detalle("calidad")))
        cls.campana = R.ejecutar(R.consulta_unica(detalle("campaña")))
        cls.conducta_de_la_base = {
            (f["run_id"], f["metric_id"], f["behavior"]) for f in R.administrar(
                "SELECT run_id, metric_id, behavior FROM evaluation.results WHERE grp IN"
                " ('accuracy','relevance','grounding','latency','robustness','availability')")}

    def comprobar(self, datos):
        self.exigir(datos)
        self.assertTrue(datos["filas"])
        # `behavior` no cambia: el conjunto de (ejecución, métrica, behavior) de la tabla es el de la base.
        devueltas = {(f["run_id"], f["metric_id"], f["behavior"]) for f in datos["filas"]}
        self.assertTrue(devueltas <= self.conducta_de_la_base)
        for fila in datos["filas"]:
            crudo, variante = fila["behavior"], fila["variante"]
            with self.subTest(metrica=fila["metric_id"], behavior=crudo):
                self.assertIsInstance(variante, str)
                self.assertTrue(variante.strip())
                if crudo in VARIANTES:
                    self.assertEqual(R.sin_acentos(variante).lower(), VARIANTES[crudo])
                else:
                    # Categorías de fallo de STR-2: nombre en español, distinto del identificador en inglés.
                    self.assertIn(crudo, CATEGORIAS_STR2)
                    self.assertNotEqual(variante.lower(), crudo)
                    self.assertNotIn("_", variante)

    def exigir(self, datos):
        faltan = {"variante", "behavior", "status", "metric_id", "run_id"} - set(R.nombres(datos))
        self.assertFalse(faltan, f"la consulta no devuelve las columnas {sorted(faltan)}")

    def test_calidad_traduce_todas_las_variantes_de_exactitud_relevancia_y_fundamento(self):
        self.comprobar(self.calidad)
        vistas = {f["behavior"] for f in self.calidad["filas"]}
        self.assertLessEqual({"all", "judged", "clarify", "abstain", "answer", "median", "q1", "q3"}, vistas)

    def test_campana_traduce_etapas_y_categorias_de_fallo(self):
        self.comprobar(self.campana)
        vistas = {f["behavior"] for f in self.campana["filas"]}
        self.assertLessEqual({"embedding", "retrieval", "generation", "total", *CATEGORIAS_STR2}, vistas)

    def test_las_diez_categorias_de_fallo_tienen_un_nombre_distinto(self):
        self.exigir(self.campana)
        nombres = {f["behavior"]: f["variante"] for f in self.campana["filas"] if f["behavior"] in CATEGORIAS_STR2}
        self.assertEqual(len(nombres), 10)
        self.assertEqual(len({v.lower() for v in nombres.values()}), 10, nombres)


class LoNoMedidoSigueSiendoNuloTests(unittest.TestCase):
    """Con `status` oculta, el nulo del valor es lo que se lee «No medido»: la consulta no puede rellenarlo con 0 ni con texto."""

    @classmethod
    def setUpClass(cls):
        detalle("calidad")
        cls.preparacion = (
            R.insertar_ejecucion("rl-1", "JUP-070", "2026-10-14T09:00:00Z", real=True)
            + R.insertar_resultado("rl-1", "accuracy", "ACC-1", estado="not_measured", denominador=20, juicio="human")
            + R.insertar_resultado("rl-1", "latency", "LAT-3", "total", estado="not_measured", unidad="ms", denominador=28)
            + R.insertar_ejecucion("rl-2", "JUP-071", "2026-10-14T10:00:00Z", real=True)
            + R.insertar_resultado("rl-2", "robustness", "ROB-1", "categoria=a,perturbacion=b", estado="not_measured",
                                   denominador=10))

    def fila_no_medida(self, clave, run_id):
        datos = R.ejecutar(R.consulta_unica(detalle(clave)), self.preparacion)
        filas = [f for f in datos["filas"] if f["run_id"] == run_id and f["status"] == "not_measured"]
        self.assertEqual(len(filas), 1, filas)
        return filas[0]

    def test_calidad(self):
        fila = self.fila_no_medida("calidad", "rl-1")
        self.assertIsNone(fila["valor_texto"])
        self.assertIsNone(fila["value"])

    def test_campana(self):
        fila = self.fila_no_medida("campaña", "rl-1")
        self.assertIsNone(fila["valor_texto"])
        self.assertIsNone(fila["value"])

    def test_robustez(self):
        fila = self.fila_no_medida("robustez", "rl-2")
        self.assertIsNone(fila["valor_texto"])
        self.assertIsNone(fila["value"])


# --- Sección B: numerador y denominador con unidad -------------------------------------------------------------------------


def panel_b():
    return R.por_titulo(TABLA_B, "B")


NULOS = (None, "", "—")


class UnidadesDeLaSeccionBEstaticoTests(unittest.TestCase):
    def test_el_numerador_y_el_denominador_con_unidad_se_ven_y_los_brutos_se_ocultan(self):
        panel = panel_b()
        self.assertRegex(R.sql_de(panel), r"(?i)\bAS\s+numerador_texto\b")
        self.assertRegex(R.sql_de(panel), r"(?i)\bAS\s+denominador_texto\b")
        for texto, bruto in (("numerador_texto", "numerator"), ("denominador_texto", "denominator")):
            with self.subTest(columna=texto):
                self.assertFalse(R.oculta(panel, texto), "el texto con unidad debe verse")
                self.assertTrue(R.oculta(panel, bruto), "el valor en bruto queda en la consulta pero oculto")
                self.assertNotIn("_texto", R.nombre_visible(panel, texto))
                self.assertTrue(R.nombre_visible(panel, texto).strip())


class UnidadesDeLaSeccionBContraPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel_b()
        cls.datos = R.ejecutar(R.consulta_unica(panel_b()))
        cls.por_clave = {(f["metric_id"], f["behavior"], f["status"]): f for f in cls.datos["filas"]}

    @property
    def filas(self):
        """Filas por (medida, detalle, estado); falla con un mensaje claro si faltan las columnas nuevas (Red legible)."""
        faltan = {"numerador_texto", "denominador_texto"} - set(R.nombres(self.datos))
        self.assertFalse(faltan, f"la consulta de la tabla de negocio no devuelve las columnas {sorted(faltan)}")
        return self.por_clave

    def test_las_columnas_nuevas_existen_y_las_brutas_no_cambian(self):
        columnas = R.nombres(self.datos)
        self.assertLessEqual({"numerador_texto", "denominador_texto", "numerator", "denominator"}, set(columnas))
        # Siguen siendo numéricas: el texto con unidad es una columna APARTE.
        tipos = dict(self.datos["columnas"])
        self.assertIn(tipos["numerator"], ("double precision", "numeric"))
        self.assertIn(tipos["denominator"], ("bigint", "numeric", "integer"))
        self.assertEqual(self.filas[("time_saved_percent", "all", "measured")]["numerator"], 360000)
        self.assertEqual(self.filas[("assigned_percent", "all", "measured")]["numerator"], 70000)

    def test_ninguna_celda_visible_de_numerador_o_denominador_lleva_la_cifra_en_bruto(self):
        # 360000 (ms) y 70000 (céntimos) eran el defecto; se amplía a toda cifra en bruto de cuatro o más dígitos.
        self.assertTrue(self.filas)
        visibles = ("numerador_texto", "denominador_texto")
        for fila in self.datos["filas"]:
            for columna, bruto in (("numerador_texto", "numerator"), ("denominador_texto", "denominator")):
                crudo = fila[bruto]
                if crudo is not None and crudo >= 1000:
                    with self.subTest(metrica=fila["metric_id"], columna=columna):
                        self.assertNotIn(str(int(crudo)), str(fila[columna] or ""))
        for fila in self.datos["filas"]:
            for columna in visibles:
                self.assertNotRegex(str(fila[columna] or ""), r"360000|70000")

    def test_el_tiempo_ahorrado_muestra_su_numerador_y_su_denominador_en_minutos(self):
        fila = self.filas[("time_saved_percent", "all", "measured")]
        self.assertRegex(fila["numerador_texto"], r"^6([.,]0+)? ?min$")
        self.assertRegex(fila["denominador_texto"], r"^15([.,]0+)? ?min$")
        # El porcentaje en sí no se toca.
        self.assertRegex(fila["valor_texto"], r"^40([.,]0)? ?%$")

    def test_los_importes_en_centimos_se_muestran_en_euros(self):
        esperados = {  # métrica: (numerador en euros, denominador en euros)
            "assigned_percent": (r"700", r"1[.,  ]?000"),
            "governed_percent": (r"900", r"1[.,  ]?000"),
            "unallocated_percent": (r"100", r"1[.,  ]?000"),
            "potential_savings_percent": (r"140", r"1[.,  ]?000"),
        }
        for metrica, (numerador, denominador) in esperados.items():
            fila = self.filas[(metrica, "all", "measured")]
            with self.subTest(metrica=metrica):
                self.assertRegex(fila["numerador_texto"], rf"^{numerador}([.,]00?)?[  ]€$")
                self.assertRegex(fila["denominador_texto"], rf"^{denominador}([.,]00?)?[  ]€$")

    def test_un_recuento_de_parejas_no_se_convierte_en_minutos(self):
        # El denominador de `manual_time` o `time_trials` son PAREJAS (2 o 3), aunque el valor esté en milisegundos:
        # formatear por la unidad del valor lo volvería «0.0 min», que sería una cifra falsa.
        for clave, esperado in ((("manual_time", "all", "measured"), "2"), (("assisted_time", "all", "measured"), "2"),
                                (("time_saved", "all", "measured"), "2"), (("time_trials", "all", "pass"), "3")):
            with self.subTest(medida=clave):
                self.assertEqual(self.filas[clave]["denominador_texto"], esperado)

    def test_lo_que_no_tiene_numerador_ni_denominador_no_inventa_ninguno(self):
        for clave in (("allocated", "all", "measured"), ("realized_savings", "all", "not_measured"),
                      ("opportunities", "estimated", "measured")):
            fila = self.filas[clave]
            with self.subTest(medida=clave):
                self.assertIn(fila["numerador_texto"], NULOS)
                self.assertIn(fila["denominador_texto"], NULOS)

    def test_el_valor_y_el_resto_de_columnas_de_la_tabla_siguen_igual(self):
        # El cambio es de numerador y denominador: `valor_texto` conserva sus minutos y euros.
        self.assertRegex(self.filas[("time_saved", "all", "measured")]["valor_texto"], r"^6([.,]0)? ?min$")
        self.assertRegex(self.filas[("allocated", "all", "measured")]["valor_texto"], r"^700([.,]00)?[  ]€$")
        self.assertIsNone(self.filas[("realized_savings", "all", "not_measured")]["valor_texto"])


if __name__ == "__main__":
    unittest.main()
