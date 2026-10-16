"""Remediación del QA de la tarea 2.5 de JUP-121: huecos de `read_business_report` (frontera con Node).

Las pruebas de `test_evaluation_adapter_jup068.py` cubren el camino feliz y los fallos más evidentes de la
ejecución del generador de Node. Este fichero cierra cinco huecos que dejaban vivos mutantes del código de la
frontera del proceso. Todas pasan con el producto actual (el código es correcto; faltaban las pruebas):

1. Sin shell. La ruta viaja como UN argumento propio de una lista; si alguien añade `shell=True` (o pasa una
   cadena) una ruta con espacios o metacaracteres se reinterpreta e incluso permite inyectar órdenes. Se prueba
   con un mock (forma de la llamada) y con Node REAL sobre rutas hostiles (comportamiento observable).
2. Primera línea NO VACÍA de stderr: el motivo del generador es la primera línea con contenido; las líneas en
   blanco iniciales no cuentan y la segunda línea no se incluye. Con stderr vacío no debe haber IndexError.
3. `ValueError` al ejecutar (byte nulo en la ruta): es una frontera del proceso y debe salir como AdapterError,
   igual que `OSError` y `SubprocessError`.
4. `RecursionError` al parsear: un stdout anidado hasta desbordar el parser no debe escapar como excepción cruda.
5. Ruta relativa: se resuelve desde la raíz del repositorio (`cwd=ROOT`), no desde el directorio de trabajo.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una
copia mutada.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_adapter_jup068_cli", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EXAMPLE_PATH = ROOT / "docs" / "validation" / "JUP-068-example.json"
RELATIVE_EXAMPLE = "docs/validation/JUP-068-example.json"
PREFIX = "business-metrics: "

# Informe de referencia (ejecutando Node real sobre el ejemplo); lo fija `setUpModule`.
REPORT: dict = {}


def setUpModule() -> None:
    REPORT.update(tool.read_business_report(EXAMPLE_PATH))


def completed(returncode=0, stdout="{}", stderr=""):
    return subprocess.CompletedProcess(["node"], returncode, stdout=stdout, stderr=stderr)


class ReadBusinessReportCliGapsTest(unittest.TestCase):
    def assert_error(self, path) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            tool.read_business_report(path)
        message = str(caught.exception)
        self.assertTrue(message.startswith(PREFIX), message)
        return message

    # --- 1. Sin shell ---

    def test_la_llamada_es_una_lista_sin_shell_y_la_ruta_va_intacta(self) -> None:
        # Una cadena o `shell=True` harían que el sistema reinterprete la ruta. La ruta debe ser el último
        # elemento de una lista, tal cual (`str(path)`), sin comillas añadidas ni escapes.
        path = Path("dir con espacios") / "a & b; $(echo hola) it's.json"
        with mock.patch.object(tool.subprocess, "run", return_value=completed(0, "{}")) as run:
            tool.read_business_report(path)
        run.assert_called_once()
        args, kwargs = run.call_args
        command = args[0] if args else kwargs["args"]
        self.assertIsInstance(command, list)
        self.assertNotIsInstance(command, str)
        self.assertIsInstance(command[-1], str)
        self.assertEqual(command[-1], str(path))
        self.assertFalse(kwargs.get("shell"), "no debe usarse shell=True")

    def test_rutas_con_metacaracteres_de_shell_se_leen_sin_inyeccion_con_node_real(self) -> None:
        # Pares (directorio, fichero) hostiles. Se intentan crear todos; los que el sistema de ficheros
        # no permita se descartan (sin skip) y se exige que al menos 3 se hayan podido probar.
        candidates = [
            ("dir con espacios", "informe.json"),
            ("a & b", "informe.json"),
            ("x;y", "informe.json"),
            ("$(echo hola)", "informe.json"),
            ("normal", "it's.json"),
            ("normal2", "a & b ; $(echo hola) 'x'.json"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            created: list[Path] = []
            for folder, name in candidates:
                try:
                    target = base / folder / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(EXAMPLE_PATH, target)
                except OSError:
                    continue
                created.append(target)
            self.assertGreaterEqual(len(created), 3, created)
            before = {p.relative_to(base).as_posix() for p in base.rglob("*")}
            for target in created:
                with self.subTest(ruta=str(target.relative_to(base))):
                    self.assertEqual(tool.read_business_report(target), REPORT)
            # Si la ruta se interpretara como orden, `echo`/`;` podrían crear o redirigir ficheros: el árbol
            # del tmpdir debe quedar exactamente como estaba.
            after = {p.relative_to(base).as_posix() for p in base.rglob("*")}
            self.assertEqual(after, before)

    # --- 2. Primera línea no vacía de stderr ---

    def test_el_motivo_es_la_primera_linea_no_vacia_del_stderr(self) -> None:
        stderr = "\n\n  \nprimera linea real\nsegunda linea\n"
        with mock.patch.object(tool.subprocess, "run", return_value=completed(1, "", stderr)):
            message = self.assert_error("informe.json")
        self.assertIn("primera linea real", message)
        self.assertNotIn("segunda linea", message)

    def test_stderr_vacio_o_en_blanco_no_lanza_indexerror(self) -> None:
        for stderr in ("", "\n", "  \n \n"):
            with self.subTest(stderr=repr(stderr)):
                with mock.patch.object(tool.subprocess, "run", return_value=completed(1, "", stderr)):
                    self.assert_error("informe.json")

    # --- 3. Excepciones al ejecutar ---

    def test_ruta_con_byte_nulo_con_subprocess_real(self) -> None:
        # Python lanza `ValueError: embedded null ...` al construir el proceso; es un fallo de frontera.
        self.assert_error("a\x00b.json")

    def test_value_error_simulado_al_ejecutar(self) -> None:
        with mock.patch.object(tool.subprocess, "run", side_effect=ValueError("x")):
            self.assert_error("informe.json")

    def test_oserror_y_subprocesserror_genericos(self) -> None:
        for error in (PermissionError("denegado"), subprocess.SubprocessError("fallo")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(tool.subprocess, "run", side_effect=error):
                    self.assert_error("informe.json")

    # --- 4. RecursionError al parsear ---

    def test_stdout_anidado_hasta_desbordar_el_parser_es_adapter_error(self) -> None:
        # `json.loads` lanza RecursionError con anidación extrema; no debe salir como excepción cruda.
        with mock.patch.object(tool.subprocess, "run", return_value=completed(0, "[" * 200000)):
            self.assert_error("informe.json")

    # --- 5. Ruta relativa ---

    def test_la_ruta_relativa_se_resuelve_desde_la_raiz_del_repositorio(self) -> None:
        # Con `cwd=ROOT` el resultado no depende del directorio de trabajo del llamante.
        original = os.getcwd()
        scratch = tempfile.TemporaryDirectory()
        # Los cleanups van en orden inverso: primero se restaura el cwd y después se borra el tmpdir
        # (Windows no permite borrar el directorio de trabajo actual).
        self.addCleanup(scratch.cleanup)
        self.addCleanup(os.chdir, original)
        os.chdir(scratch.name)
        self.assertFalse((Path(scratch.name) / "docs").exists())
        self.assertEqual(tool.read_business_report(RELATIVE_EXAMPLE), REPORT)


if __name__ == "__main__":
    unittest.main()
