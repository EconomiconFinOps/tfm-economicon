"""Sección C del dashboard de evaluación: tasa de error y latencia p95 del backend (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisitos de la spec que fija este módulo (decisiones D1 y D2 del diseño):

* «Tasa de error distingue ausencia de errores de ausencia de tráfico»: con peticiones y ninguna 5xx el panel vale 0 %
  (un cero MEDIDO); sin peticiones sigue diciendo «Sin datos: no hubo peticiones». El fallo actual es que el numerador
  `sum(rate(...{status_code=~"5.."}))` no tiene series cuando nunca hubo un 5xx, y la división de un vector vacío da un
  vector vacío: el panel dice «sin datos» aunque haya tráfico. La corrección es `(numerador or vector(0))` y SOLO en el
  numerador: si el denominador también llevara `or vector(0)`, sin tráfico saldría `0/0 = NaN`, o un 0 inventado.
* «Latencia del backend rotulada con su alcance»: `backend_http_request_duration_seconds` agrega TODAS las rutas del
  backend; el título lo dice («todas las rutas») y la descripción aclara que no es la latencia de las consultas al asistente.

Dos niveles de prueba:

1. Estático: se lee la expresión del dashboard y se comprueba su forma (numerador con `or vector(0)`, denominador sin él).
2. Semántico: la expresión del dashboard se ejecuta con `promtool test rules` (imagen `prom/prometheus` de
   `docker-compose.yml`, sin descargarla: si no está o no hay Docker, la prueba se salta con motivo) sobre series de
   entrada fabricadas: tráfico sin 5xx -> 0; con 5xx -> el porcentaje; solo 5xx -> 100; sin tráfico -> vacío. Es lo que
   evita que una expresión de «forma correcta» se comporte mal (p. ej. `or vector(0)` en el sitio equivocado).

Los paneles se localizan por la métrica que consultan, no por su `id` ni su posición. Ruta del dashboard:
`EVALUATION_DASHBOARD_JSON`.

Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_section_c.py`
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

COMPOSE = R.ROOT / "docker-compose.yml"
SIN_PETICIONES = "Sin datos: no hubo peticiones"
DENOMINADOR = "sum(rate(backend_http_requests_total[5m]))"


def panel_de_error():
    """Panel de la sección C cuya expresión divide los 5xx entre las peticiones del backend."""
    candidatos = [p for p in R.de_seccion("C")
                  if any('status_code=~"5.."' in t.get("expr", "") for t in p.get("targets", []))]
    if len(candidatos) != 1:
        raise AssertionError(f"se esperaba un único panel de tasa de error en la sección C y hay {len(candidatos)}")
    return candidatos[0]


def panel_de_latencia():
    """Panel de la sección C que consulta el histograma de duración de las peticiones HTTP del backend."""
    candidatos = [p for p in R.de_seccion("C")
                  if any("backend_http_request_duration_seconds" in t.get("expr", "") for t in p.get("targets", []))]
    if len(candidatos) != 1:
        raise AssertionError(f"se esperaba un único panel de latencia p95 en la sección C y hay {len(candidatos)}")
    return candidatos[0]


def expresion(panel) -> str:
    objetivos = panel["targets"]
    assert len(objetivos) == 1, "el panel debe tener una sola serie"
    return objetivos[0]["expr"]


def dividir_en_la_raiz(expr: str) -> list:
    """Parte `expr` por las barras `/` que no están dentro de paréntesis, llaves, corchetes ni comillas."""
    partes, actual, profundidad, comilla = [], [], 0, None
    for caracter in expr:
        if comilla:
            actual.append(caracter)
            if caracter == comilla:
                comilla = None
            continue
        if caracter in "\"'":
            comilla = caracter
        elif caracter in "([{":
            profundidad += 1
        elif caracter in ")]}":
            profundidad -= 1
        elif caracter == "/" and profundidad == 0:
            partes.append("".join(actual).strip())
            actual = []
            continue
        actual.append(caracter)
    partes.append("".join(actual).strip())
    return partes


class TasaDeErrorEstaticaTests(unittest.TestCase):
    def test_el_numerador_usa_or_vector_0_y_el_denominador_no(self):
        # Numerador: `or vector(0)` convierte «ninguna serie 5xx» en un 0 medido. Denominador: sin `vector(`, para que
        # sin peticiones el cociente siga vacío (y el panel diga «Sin datos») en vez de 0/0 o de un 0 inventado.
        partes = dividir_en_la_raiz(expresion(panel_de_error()))
        self.assertEqual(len(partes), 2, f"se esperaba `numerador / denominador` y hay {partes}")
        numerador, denominador = partes
        self.assertRegex(numerador, r'status_code=~"5\.\."')
        self.assertRegex(numerador, r"\bor\s+vector\(\s*0\s*\)", "el numerador debe llevar `or vector(0)`")
        self.assertNotIn("vector(", denominador, "el denominador NO puede llevar `or vector`: inventaría un 0 sin tráfico")
        self.assertEqual(R.plano(denominador), DENOMINADOR)
        self.assertNotIn("5..", denominador)

    def test_or_vector_0_solo_cubre_los_5xx_y_no_toda_la_expresion(self):
        # `or vector(0)` debe quedar DENTRO de un paréntesis que contiene únicamente la suma de 5xx: si cubriera todo el
        # cociente (`a / b or vector(0)`), sin tráfico saldría 0 en lugar de «sin datos».
        numerador = dividir_en_la_raiz(expresion(panel_de_error()))[0]
        agrupado = re.search(r"\(\s*(sum\(rate\(backend_http_requests_total\{status_code=~\"5\.\.\"\}\[\w+\]\)\))"
                             r"\s+or\s+vector\(\s*0\s*\)\s*\)", numerador)
        self.assertIsNotNone(agrupado, numerador)

    def test_sigue_diciendo_sin_datos_cuando_no_hubo_peticiones(self):
        # El `noValue` del panel es lo que ve quien abre el panel sin tráfico en la última hora.
        self.assertEqual(R.defaults(panel_de_error()).get("noValue"), SIN_PETICIONES)

    def test_la_serie_se_mide_en_porcentaje_con_100_por_delante(self):
        self.assertTrue(expresion(panel_de_error()).lstrip().startswith("100 *"))
        self.assertEqual(R.defaults(panel_de_error()).get("unit"), "percent")


class LatenciaP95Tests(unittest.TestCase):
    def test_el_titulo_dice_que_son_todas_las_rutas(self):
        panel = panel_de_latencia()
        titulo = panel["title"]
        self.assertIn("todas las rutas", titulo)
        # D6 (`jup-121-anotaciones-y-fuente`): el título es el exacto de <= 40 caracteres y ya no dice «backend» ni
        # «tráfico real»; ese alcance (el backend, con tráfico real) pasa a la línea «Mide:» de la descripción.
        self.assertEqual(titulo, "Latencia p95, todas las rutas")
        self.assertLessEqual(len(titulo), 40)
        mide = panel["description"].split("\n")[1].lower()
        self.assertIn("backend", mide)
        self.assertIn("tráfico real", mide)
        # El rótulo de «tráfico real» ya no basta: la sección C cuenta síntomas del backend, no del asistente.

    def test_la_descripcion_aclara_que_no_es_la_latencia_de_las_consultas_al_asistente(self):
        descripcion = panel_de_latencia()["description"]
        self.assertRegex(descripcion, r"(?is)\bno es\b[^\n]*\basistente\b",
                         "la descripción debe decir que NO es la latencia de las consultas al asistente")
        self.assertRegex(descripcion, r"(?i)todas las rutas")

    def test_la_descripcion_conserva_sus_tres_lineas(self):
        # El rótulo nuevo no puede romper el formato «Tipo / Mide / No demuestra» que exige el resto de paneles.
        lineas = panel_de_latencia()["description"].split("\n")
        self.assertEqual(len(lineas), 3, lineas)
        self.assertTrue(lineas[0].startswith("Tipo: C"))
        self.assertTrue(lineas[1].startswith("Mide: "))
        self.assertTrue(lineas[2].startswith("No demuestra: "))

    def test_la_expresion_sigue_agregando_todas_las_rutas(self):
        # El diseño rotula, no filtra (D2): la expresión no se restringe a una ruta del asistente.
        expr = expresion(panel_de_latencia())
        self.assertIn("histogram_quantile(0.95", expr)
        self.assertNotRegex(expr, r"\b(route|path|handler)\s*=~?")


# --- Semántica con promtool ---------------------------------------------------------------------------------------------


def imagen_de_prometheus() -> str:
    """Imagen del servicio de Prometheus tal como está escrita en `docker-compose.yml`."""
    coincidencia = re.search(r"^\s*image:\s*(prom/prometheus:\S+)\s*$", COMPOSE.read_text(encoding="utf-8"), re.M)
    if not coincidencia:
        raise AssertionError(f"no se encontró la imagen de Prometheus en {COMPOSE}")
    return coincidencia.group(1)


def requerir_promtool() -> str:
    """Imagen de Prometheus disponible en local o `SkipTest` (sin descargar nada: la prueba no depende de la red)."""
    if shutil.which("docker") is None:
        raise unittest.SkipTest("Docker no disponible")
    imagen = imagen_de_prometheus()
    try:
        info = subprocess.run(["docker", "image", "inspect", imagen], capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError):
        raise unittest.SkipTest("Docker no disponible") from None
    if info.returncode != 0:
        raise unittest.SkipTest(f"Docker no disponible o imagen {imagen} no descargada (la prueba no usa la red)")
    return imagen


def caso(expr: str, series: dict, esperado: list) -> str:
    """Un caso de `promtool test rules`: series de entrada (`{selector: valores}`) y muestras esperadas a los 10 min."""
    entrada = "".join(f"      - series: '{selector}'\n        values: '{valores}'\n" for selector, valores in series.items())
    if esperado:
        muestras = "        exp_samples:\n" + "".join(
            f"          - labels: '{{}}'\n            value: {valor}\n" for valor in esperado)
    else:
        muestras = "        exp_samples: []\n"
    return (
        "  - interval: 1m\n"
        f"    input_series:\n{entrada}"
        "    promql_expr_test:\n"
        f"      - expr: '{expr}'\n"
        "        eval_time: 10m\n"
        f"{muestras}"
    )


class TasaDeErrorConPromtoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Imagen y expresión se resuelven antes de crear nada: sin dashboard o sin panel de error la prueba falla (Red)
        # sin arrancar Docker.
        cls.expr = expresion(panel_de_error())
        cls.imagen = requerir_promtool()

    def ejecutar(self, casos: list) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="promtool-readability-") as carpeta:
            base = Path(carpeta)
            (base / "rules.yml").write_text("groups:\n  - name: g\n    rules:\n      - record: x\n        expr: vector(1)\n",
                                            encoding="utf-8")
            (base / "test.yml").write_text(
                "rule_files: [rules.yml]\nevaluation_interval: 1m\ntests:\n" + "".join(casos), encoding="utf-8")
            # Prometheus ejecuta promtool como usuario sin privilegios, distinto
            # del propietario del temporal. Sólo estos YAML sintéticos son legibles.
            base.chmod(0o755)
            for fichero in (base / "rules.yml", base / "test.yml"):
                fichero.chmod(0o644)
            return subprocess.run(
                ["docker", "run", "--rm", "--entrypoint", "promtool", "-v", f"{base}:/t:ro", self.imagen,
                 "test", "rules", "/t/test.yml"],
                capture_output=True, timeout=180, check=False)

    def comprobar(self, casos: list):
        proceso = self.ejecutar(casos)
        salida = (proceso.stdout + proceso.stderr).decode("utf-8", "replace")
        self.assertEqual(proceso.returncode, 0, f"promtool rechazó la expresión del dashboard:\n{salida}")

    def test_con_trafico_y_sin_5xx_vale_cero(self):
        # Caso central del defecto: solo hay series 200 y NINGUNA 5xx. Debe dar un 0 medido, no un vector vacío.
        self.comprobar([caso(self.expr, {'backend_http_requests_total{status_code="200"}': "0+10x10"}, [0])])

    def test_con_5xx_da_el_porcentaje_sobre_todas_las_peticiones(self):
        # 10 peticiones/s con 5xx de 30 totales: el 25 % de las peticiones. Comprueba que el denominador cuenta
        # TODAS las peticiones (también las 5xx) y que `or vector(0)` no altera el cálculo cuando sí hay 5xx.
        self.comprobar([caso(self.expr, {
            'backend_http_requests_total{status_code="200"}': "0+30x10",
            'backend_http_requests_total{status_code="500"}': "0+10x10",
        }, [25])])

    def test_solo_5xx_es_el_cien_por_cien(self):
        self.comprobar([caso(self.expr, {'backend_http_requests_total{status_code="503"}': "0+5x10"}, [100])])

    def test_sin_trafico_no_hay_valor(self):
        # Sin ninguna serie de peticiones el denominador no tiene series: el resultado es vacío y el panel enseña su
        # `noValue` «Sin datos: no hubo peticiones». Un `or vector(0)` también en el denominador fallaría aquí (NaN).
        self.comprobar([caso(self.expr, {"backend_assistant_queries_total": "0+1x10"}, [])])


if __name__ == "__main__":
    unittest.main()
