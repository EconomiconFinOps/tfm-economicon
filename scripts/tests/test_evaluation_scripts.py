"""Scripts de `package.json` y paso de CI del dashboard de evaluación (JUP-121, tarea 3.4, Red).

La tarea 3.4 expone los subcomandos de `tools/evaluation-dashboard.py` como scripts de pnpm y mete sus pruebas en
la CI. Este fichero no carga la herramienta: lee `package.json`, `.github/workflows/ci.yml` y la guía
`docs/validation/evaluation-dashboard.md` con la biblioteca estándar (sin YAML externo) y, en dos casos, lanza pnpm
de verdad para comprobar que los scripts funcionan de extremo a extremo.

Contrato que se valida:

* Cuatro scripts nuevos con valor EXACTO: `evaluation-dashboard:rows|sql|load` (invocan la herramienta con el
  subcomando) y `evaluation-dashboard:test` (descubre todos los `test_evaluation_*.py`). El patrón de descubrimiento
  va entre comillas dobles: el intérprete de comandos de pnpm en Windows no entiende las simples y, sin comillas,
  `*` se expandiría. El patrón cubre todos los ficheros `test_evaluation_*.py` y deja fuera el módulo auxiliar
  `evaluation_pg_helper.py` (no es un test).
* Los cuatro scripts son contiguos y van entre `chat-collector:test` y `synthetic-demo:test`; el resto de scripts
  no se toca (se fijan siete representativos con su valor de hoy como literales).
* La CI ejecuta `corepack pnpm evaluation-dashboard:test` UNA sola vez, en el paso «Validate governance tooling»,
  después de colector y robustez y antes de `synthetic-demo:test`, con la misma sangría; el resto del
  bloque no cambia.
* La guía nombra los cuatro scripts.

Rutas: por defecto los ficheros reales del repositorio. Las variables de entorno `EVALUATION_PACKAGE_JSON`,
`EVALUATION_CI_YML` y `EVALUATION_DOC` permiten apuntar a copias (se usan para comprobar que los esperados son
alcanzables y que las mutaciones se detectan). Los tests de ejecución real usan como directorio de trabajo la
carpeta de `package.json`, que es la raíz del espacio de trabajo de pnpm.

Decisiones donde el enunciado admitía más de una lectura:

* pnpm 9 reenvía el `--` literal al script, y entonces el analizador de argumentos de la herramienta tomaría
  `--no-versioned` como posicional. Por eso los tests de ejecución pasan la opción sin `--`:
  `corepack pnpm evaluation-dashboard:rows --no-versioned`.
* `pnpm run` escribe una cabecera (`> paquete@ script ruta`, `> comando`) en la salida estándar. Los tests de
  ejecución exigen que todo lo anterior a la salida de la herramienta sean líneas de esa cabecera (empiezan por
  `>` o están vacías) y comprueban lo que viene después.
* Los cuatro scripts nuevos deben ser contiguos en cualquier orden entre sí, pero ocupar exactamente el hueco
  entre `chat-collector:test` y `synthetic-demo:test`.
"""

import fnmatch
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

# Raíz del repositorio deducida de este fichero (scripts/tests/ -> raíz).
REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_JSON = Path(os.environ.get("EVALUATION_PACKAGE_JSON") or REPO_ROOT / "package.json")
CI_YML = Path(os.environ.get("EVALUATION_CI_YML") or REPO_ROOT / ".github" / "workflows" / "ci.yml")
DOC = Path(os.environ.get("EVALUATION_DOC") or REPO_ROOT / "docs" / "validation" / "evaluation-dashboard.md")
TESTS_DIR = REPO_ROOT / "scripts" / "tests"

NEW_SCRIPTS = {
    "evaluation-dashboard:rows": "python tools/evaluation-dashboard.py rows",
    "evaluation-dashboard:sql": "python tools/evaluation-dashboard.py sql",
    "evaluation-dashboard:load": "python tools/evaluation-dashboard.py load",
    "evaluation-dashboard:test": 'python -m unittest discover -s scripts/tests -p "test_evaluation_*.py"',
}

# Scripts representativos que deben conservarse al reconciliar JUP-121 y JUP-123.
UNTOUCHED_SCRIPTS = {
    "jup:check": "node tools/jup-check.mjs",
    "assistant-metrics:test": "python -m unittest discover -s scripts/tests -p test_assistant_metrics.py",
    "assistant-eval:test": "python -m unittest discover -s scripts/tests -p test_assistant_eval.py",
    "chat-collector:test": "python -m unittest discover -s tools -p test_chat_eval_collect*.py -v",
    "retrieval-calibration:test": "python -m unittest discover -s scripts/tests -p test_retrieval_calibration.py",
    "docker:validate": "node --test tools/docker-topology.test.mjs",
    "business-metrics:test": "node --test tools/business-metrics.test.mjs",
}

CI_LINE = "corepack pnpm evaluation-dashboard:test"
CI_INDENT = " " * 10
CI_STEP_NAME = "Validate governance tooling"

# Líneas del bloque `run: |` del paso de gobernanza tal como están hoy, sin la línea nueva.
CI_BLOCK_TODAY = [
    "corepack pnpm jup:check:test",
    "corepack pnpm pr:check:test",
    "corepack pnpm ci:check:test",
    "corepack pnpm roadmap:test",
    "corepack pnpm repository:governance:test",
    "corepack pnpm jup:check:all",
    "corepack pnpm jup:cleanup:test",
    "corepack pnpm jup:cleanup:check",
    "corepack pnpm assistant-corpus:test",
    "corepack pnpm assistant-corpus:validate",
    "corepack pnpm validation-questions:validate",
    "corepack pnpm validation-questions:test",
    "corepack pnpm business-metrics:validate",
    "corepack pnpm business-metrics:test",
    "corepack pnpm retrieval-labels:validate",
    "corepack pnpm retrieval-labels:test",
    "corepack pnpm retrieval-calibration:test",
    "corepack pnpm assistant-metrics:test",
    "corepack pnpm assistant-eval:test",
    "corepack pnpm chat-collector:test",
    "corepack pnpm assistant-robustness:validate",
    "corepack pnpm assistant-robustness:test",
    "corepack pnpm synthetic-demo:test",
    "corepack pnpm demo-dataset:test",
    "corepack pnpm demo-data:test",
    "corepack pnpm llm-gateway:test",
    "python -m unittest discover -s tools -p test_litellm_product_keys.py -v",
    "corepack pnpm docker:validate",
    "corepack pnpm local:test",
    "corepack pnpm cd:test",
    "corepack pnpm tokenizer:test",
    "corepack pnpm collaboration:test",
    "corepack pnpm contributions:test",
    "corepack pnpm openspec:validate",
]


def _pares_sin_duplicados(pares):
    """Hook de `json.loads`: conserva el orden y rechaza claves repetidas (JSON válido pero ambiguo)."""
    resultado = {}
    for clave, valor in pares:
        if clave in resultado:
            raise ValueError(f"clave duplicada en package.json: {clave}")
        resultado[clave] = valor
    return resultado


def _cargar_package():
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"), object_pairs_hook=_pares_sin_duplicados)


def _scripts():
    return _cargar_package()["scripts"]


def _lineas_ci():
    return CI_YML.read_text(encoding="utf-8").splitlines()


def _bloque_gobernanza():
    """Devuelve (índice de la primera línea del bloque, líneas crudas del bloque) del paso de gobernanza.

    Recorre líneas en lugar de usar un analizador YAML: localiza `- name: Validate governance tooling`, la
    línea `run: |` siguiente y las líneas con más sangría que `run:` (el contenido del bloque literal).
    """
    lineas = _lineas_ci()
    paso = next(
        (i for i, linea in enumerate(lineas) if re.fullmatch(rf"\s*- name: {re.escape(CI_STEP_NAME)}\s*", linea)),
        None,
    )
    if paso is None:
        raise AssertionError(f"no se encuentra el paso «{CI_STEP_NAME}» en {CI_YML}")
    run = next(i for i in range(paso + 1, len(lineas)) if re.fullmatch(r"\s*run: \|\s*", lineas[i]))
    sangria_run = len(lineas[run]) - len(lineas[run].lstrip())
    inicio = run + 1
    fin = inicio
    while fin < len(lineas):
        linea = lineas[fin]
        if linea.strip() == "":
            # Una línea en blanco cierra el bloque en este fichero (separa del siguiente job).
            break
        if len(linea) - len(linea.lstrip()) <= sangria_run:
            break
        fin += 1
    return inicio, lineas[inicio:fin]


def _salida_de_herramienta(stdout, primera_linea):
    """Separa la cabecera de pnpm de la salida de la herramienta a partir de `primera_linea`."""
    lineas = stdout.splitlines(keepends=True)
    inicio = next((i for i, linea in enumerate(lineas) if linea.rstrip("\r\n") == primera_linea), None)
    if inicio is None:
        raise AssertionError(f"la salida no contiene una línea `{primera_linea}`: {stdout!r}")
    cabecera = lineas[:inicio]
    ajenas = [linea for linea in cabecera if linea.strip() and not linea.startswith(">")]
    if ajenas:
        raise AssertionError(f"antes de la salida de la herramienta solo puede ir la cabecera de pnpm: {ajenas!r}")
    return "".join(lineas[inicio:])


def _ejecutar_pnpm(*args):
    """Lanza `corepack pnpm ...` en la raíz del espacio de trabajo, sin red y con tiempo máximo."""
    corepack = shutil.which("corepack")
    if corepack is None:
        raise AssertionError("corepack no está disponible en el PATH (Node/pnpm son requisito del repositorio)")
    return subprocess.run(
        [corepack, "pnpm", *args],
        cwd=PACKAGE_JSON.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",  # mensajes de error de Windows en otra página de códigos no deben romper el test
        timeout=180,
    )


class PackageJsonTests(unittest.TestCase):
    """Scripts de `package.json`."""

    def test_package_json_es_json_valido_con_scripts(self):
        # Base de todo lo demás: el fichero se parsea (sin claves repetidas) y tiene un objeto `scripts`.
        paquete = _cargar_package()
        self.assertIsInstance(paquete["scripts"], dict)

    def test_script_rows_con_valor_exacto(self):
        self.assertEqual(_scripts().get("evaluation-dashboard:rows"), NEW_SCRIPTS["evaluation-dashboard:rows"])

    def test_script_sql_con_valor_exacto(self):
        self.assertEqual(_scripts().get("evaluation-dashboard:sql"), NEW_SCRIPTS["evaluation-dashboard:sql"])

    def test_script_load_con_valor_exacto(self):
        self.assertEqual(_scripts().get("evaluation-dashboard:load"), NEW_SCRIPTS["evaluation-dashboard:load"])

    def test_script_test_con_valor_exacto(self):
        self.assertEqual(_scripts().get("evaluation-dashboard:test"), NEW_SCRIPTS["evaluation-dashboard:test"])

    def test_scripts_previos_siguen_con_el_mismo_valor(self):
        # Añadir scripts no debe alterar los existentes: se fijan seis representativos con su valor de hoy.
        scripts = _scripts()
        for nombre, valor in UNTOUCHED_SCRIPTS.items():
            with self.subTest(script=nombre):
                self.assertEqual(scripts.get(nombre), valor)

    def test_los_cuatro_scripts_son_contiguos_entre_chat_collector_y_synthetic_demo(self):
        # Van junto a los de assistant-* / retrieval-*: ocupan exactamente el hueco entre `chat-collector:test`
        # y `synthetic-demo:test` (en cualquier orden entre sí) y no hay otros scripts intercalados.
        claves = list(_scripts())
        self.assertIn("assistant-eval:test", claves)
        self.assertIn("synthetic-demo:test", claves)
        self.assertLess(claves.index("assistant-eval:test"), claves.index("chat-collector:test"))
        desde = claves.index("chat-collector:test") + 1
        hasta = claves.index("synthetic-demo:test")
        self.assertEqual(sorted(claves[desde:hasta]), sorted(NEW_SCRIPTS))

    def test_el_script_test_usa_comillas_dobles_y_ninguna_simple(self):
        # En Windows el intérprete de comandos de pnpm no interpreta las comillas simples; las dobles evitan además
        # que `*` se expanda antes de llegar a unittest.
        valor = _scripts().get("evaluation-dashboard:test", "")
        self.assertNotIn("'", valor)
        self.assertRegex(valor, r'-p "test_evaluation_\*\.py"')

    def test_el_patron_de_descubrimiento_cubre_todos_los_tests_de_evaluation(self):
        # El patrón de `-p` debe casar con cada `test_evaluation_*.py` que existe (también este fichero) y no con
        # el módulo auxiliar `evaluation_pg_helper.py`, que no es un test. Se usa `fnmatch`, igual que unittest.
        valor = _scripts().get("evaluation-dashboard:test", "")
        coincidencia = re.search(r'-p\s+"([^"]+)"', valor)
        self.assertIsNotNone(coincidencia, f"el script no lleva `-p` con el patrón entre comillas dobles: {valor!r}")
        patron = coincidencia.group(1)
        self.assertRegex(valor, r"-s\s+scripts/tests\b")
        ficheros = sorted(p.name for p in TESTS_DIR.glob("test_evaluation_*.py"))
        self.assertIn("test_evaluation_scripts.py", ficheros)
        self.assertGreater(len(ficheros), 20)
        for nombre in ficheros:
            with self.subTest(fichero=nombre):
                self.assertTrue(fnmatch.fnmatchcase(nombre, patron), f"{nombre} no casa con {patron}")
        self.assertTrue((TESTS_DIR / "evaluation_pg_helper.py").exists())
        self.assertFalse(fnmatch.fnmatchcase("evaluation_pg_helper.py", patron))


class CiWorkflowTests(unittest.TestCase):
    """Paso «Validate governance tooling» de `.github/workflows/ci.yml`."""

    def test_la_linea_aparece_una_sola_vez_en_todo_el_fichero(self):
        # Ni ausente (la CI no ejecutaría las pruebas) ni duplicada (se ejecutarían dos veces).
        apariciones = [linea for linea in _lineas_ci() if linea.strip() == CI_LINE]
        self.assertEqual(len(apariciones), 1)

    def test_la_linea_esta_en_el_paso_de_gobernanza_tras_assistant_eval_y_antes_de_synthetic_demo(self):
        _, bloque = _bloque_gobernanza()
        esperado = CI_BLOCK_TODAY.copy()
        esperado.insert(esperado.index("corepack pnpm synthetic-demo:test"), CI_LINE)
        self.assertEqual([linea.strip() for linea in bloque], esperado)

    def test_la_linea_nueva_tiene_la_misma_sangria_que_las_demas(self):
        # En un bloque literal de YAML una sangría distinta cambiaría el contenido o rompería el fichero.
        _, bloque = _bloque_gobernanza()
        self.assertIn(CI_INDENT + CI_LINE, bloque)
        for linea in bloque:
            with self.subTest(linea=linea):
                self.assertTrue(linea.startswith(CI_INDENT) and not linea.startswith(CI_INDENT + " "))

    def test_el_resto_del_bloque_no_cambia(self):
        # Con la línea nueva quitada, el bloque es idéntico al de hoy (mismo orden, sin líneas añadidas ni
        # borradas). Esta comprobación pasa hoy y debe seguir pasando.
        _, bloque = _bloque_gobernanza()
        resto = [linea.strip() for linea in bloque if linea.strip() != CI_LINE]
        self.assertEqual(resto, CI_BLOCK_TODAY)


class DocumentationTests(unittest.TestCase):
    def test_la_guia_nombra_los_cuatro_scripts(self):
        # La sección «Regenerar los datos» debe decir cómo lanzar rows, sql, load y las pruebas por su nombre
        # de script (hoy solo nombra `load` y `rows`).
        texto = DOC.read_text(encoding="utf-8")
        ausentes = [
            nombre
            for nombre in NEW_SCRIPTS
            if not re.search(rf"(?<![\w:-]){re.escape(nombre)}(?![\w-])", texto)
        ]
        self.assertEqual(ausentes, [])


class EjecucionRealTests(unittest.TestCase):
    """Los scripts funcionan de verdad con pnpm (necesitan Node/pnpm, que el repositorio ya exige)."""

    def test_rows_sin_versionado_imprime_el_conjunto_vacio_formateado(self):
        # `--no-versioned` evita leer manifiestos: la salida es el conjunto de datos vacío, formateado con sangría
        # de dos espacios y salto de línea final. El script debe reenviar el argumento extra a la herramienta.
        resultado = _ejecutar_pnpm("evaluation-dashboard:rows", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        salida = _salida_de_herramienta(resultado.stdout, "{")
        self.assertEqual(salida, json.dumps({"dataset_version": 1, "runs": []}, indent=2) + "\n")

    def test_sql_sin_versionado_empieza_por_begin(self):
        # El script `sql` imprime el script transaccional: la primera línea de la herramienta es `BEGIN;`.
        resultado = _ejecutar_pnpm("evaluation-dashboard:sql", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        salida = _salida_de_herramienta(resultado.stdout, "BEGIN;")
        self.assertTrue(salida.startswith("BEGIN;"))
        self.assertIn("COMMIT;", salida)


if __name__ == "__main__":
    unittest.main()
