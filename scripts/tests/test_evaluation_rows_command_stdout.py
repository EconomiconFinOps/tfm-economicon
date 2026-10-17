"""Salida estándar, raíz y errores de lectura de `rows` en `tools/evaluation-dashboard.py` (JUP-121, tarea 2.8, QA).

Complementa `test_evaluation_rows_command.py` y `test_evaluation_rows_command_gaps.py` (no se importan ni se
modifican). Cubre tres hallazgos del QA:

1. L2 (Red en Windows): la salida estándar de `rows` debe ser BYTE A BYTE la del fichero de `--output`
   (UTF-8, `\\n`, sin BOM, un único `\\n` final). Escribir con `sys.stdout.write` en modo texto convierte `\\n` en
   `\\r\\n` en Windows y los bytes difieren, así que el JSON versionado cambiaría de una máquina a otra si se
   redirige la salida. Se comprueba con un proceso real leyendo los BYTES (sin `text=True`).
2. M1: `report_path` se calcula comparando rutas RESUELTAS, también la de la raíz: una raíz relativa (`.`) o con
   `..` no debe hacer que `report_path` quede en `None` para un informe que sí está dentro.
3. L1: un `OSError` al leer el informe se cita por su `strerror` (o, si no lo tiene, por el nombre de su clase) y
   nunca con la ruta absoluta, que puede llevar nombres de usuario y acaba en registros de CI.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_command_stdout", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

# Documento `rows-v1` válido y mínimo (mismo que el de las pruebas principales).
ROWS_DOCUMENT = {
    "contract_version": 1,
    "run": {
        "run_id": "JUP-071-demo-1", "source": "JUP-071", "run_at": "2026-10-10T09:00:00Z", "commit": "abc1234",
        "suite": "JUP-069", "suite_version": "JUP-069-v1", "retrieval": {"top_k": 4},
    },
    "results": [
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "pass",
         "count": 3, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
    ],
}

REPORT_RELATIVE = "dentro/informe.json"


def run_cli_bytes(*args, cwd=None):
    # Proceso real y SIN `text=True`: la traducción de saltos de línea ocurre al escribir en la salida estándar y
    # solo se ve si se leen los bytes tal cual salen.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]],
        capture_output=True, env=env, timeout=240, check=False, cwd=None if cwd is None else str(cwd),
    )


class TmpCase(unittest.TestCase):
    """Base con un directorio temporal resuelto (en Windows el temporal puede traer nombres cortos 8.3)."""

    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name).resolve()

    def write(self, relative: str, document) -> Path:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def entry(self, path: Path) -> dict:
        return {"path": Path(path), "format": "rows-v1", "milestone": False, "run_id": None,
                "manifest": self.tmp / "manifiesto.json"}

    def local_manifest(self, report: Path) -> Path:
        # Manifiesto local con la ruta ABSOLUTA del informe: así la raíz solo influye en `report_path`.
        return self.write("local.json", {"manifest_version": 1, "runs": [
            {"path": str(report), "format": "rows-v1", "milestone": False}]})


# --- 1. L2: la salida estándar es byte a byte la del fichero --------------------------------------------------


class StdoutBytesTest(TmpCase):
    def assert_stdout_equals_output_file(self, *args) -> bytes:
        output = self.tmp / "salida.json"
        via_file = run_cli_bytes(*args, "--output", output)
        self.assertEqual(via_file.returncode, 0, via_file.stderr)
        self.assertEqual(via_file.stdout, b"")
        via_stdout = run_cli_bytes(*args)
        self.assertEqual(via_stdout.returncode, 0, via_stdout.stderr)
        expected = output.read_bytes()
        # Mismos bytes, no solo el mismo texto: el fichero versionado no puede depender de la plataforma.
        self.assertEqual(via_stdout.stdout, expected)
        return via_stdout.stdout

    def test_salida_estandar_local_es_identica_byte_a_byte_al_fichero_de_output(self) -> None:
        report = self.write("informe.json", ROWS_DOCUMENT)
        manifest = self.local_manifest(report)
        stdout = self.assert_stdout_equals_output_file(
            "rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp)
        # Sin traducción de saltos de línea (en Windows `sys.stdout.write` daría `\r\n`), con un único `\n` final.
        self.assertNotIn(b"\r\n", stdout)
        self.assertNotIn(b"\r", stdout)
        self.assertTrue(stdout.endswith(b"\n"), stdout[-10:])
        self.assertFalse(stdout.endswith(b"\n\n"), stdout[-10:])
        # UTF-8 sin BOM y JSON válido con la versión del conjunto de datos.
        self.assertFalse(stdout.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(json.loads(stdout.decode("utf-8"))["dataset_version"], 1)

    def test_salida_estandar_del_manifiesto_versionado_no_lleva_retornos_de_carro(self) -> None:
        # Caso real: el manifiesto versionado (informes de JUP-068, 070, 078...). Es lo que se versionaría
        # redirigiendo la salida, así que no puede llevar `\r` en ningún sitio.
        stdout = self.assert_stdout_equals_output_file("rows")
        self.assertNotIn(b"\r", stdout)
        self.assertTrue(stdout.endswith(b"\n"))
        self.assertFalse(stdout.endswith(b"\n\n"))
        self.assertEqual(json.loads(stdout.decode("utf-8"))["dataset_version"], 1)


# --- 2. M1: la raíz también se resuelve -----------------------------------------------------------------------


class RootResolutionTest(TmpCase):
    def inside_report(self) -> Path:
        return self.write(REPORT_RELATIVE, ROWS_DOCUMENT)

    def test_raiz_con_punto_punto_resuelve_el_report_path(self) -> None:
        # `<tmp>/sub/..` es `<tmp>`: una comparación léxica con la raíz sin resolver daría `None`.
        report = self.inside_report()
        (self.tmp / "sub").mkdir()
        item = tool.normalize_entry(self.entry(report), root=self.tmp / "sub" / "..")
        self.assertEqual(item["run"]["report_path"], REPORT_RELATIVE)

    def test_raiz_relativa_resuelve_el_report_path(self) -> None:
        # Raíz `.` con el directorio de trabajo en `<tmp>` y el informe por ruta absoluta.
        report = self.inside_report()
        previous = os.getcwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(self.tmp)
        item = tool.normalize_entry(self.entry(report), root=Path("."))
        self.assertEqual(item["run"]["report_path"], REPORT_RELATIVE)

    def test_cli_con_raiz_punto_y_cwd_en_el_tmp_resuelve_el_report_path(self) -> None:
        report = self.inside_report()
        manifest = self.local_manifest(report)
        output = self.tmp / "salida.json"
        completed = run_cli_bytes("rows", "--no-versioned", "--manifest", manifest, "--root", ".",
                                  "--output", output, cwd=self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        dataset = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual([run["run"]["report_path"] for run in dataset["runs"]], [REPORT_RELATIVE])

    def test_informe_fuera_de_la_raiz_deja_el_report_path_en_none(self) -> None:
        # Contraste: resolver la raíz no debe dar por dentro un informe que cuelga de otro directorio.
        report = self.write("otro/informe.json", ROWS_DOCUMENT)
        (self.tmp / "dentro").mkdir(exist_ok=True)
        item = tool.normalize_entry(self.entry(report), root=self.tmp / "dentro")
        self.assertIsNone(item["run"]["report_path"])


# --- 3. L1: errores de lectura del informe sin ruta absoluta --------------------------------------------------


class ReadErrorMessageTest(TmpCase):
    def read_error(self, error: OSError) -> str:
        report = self.write(REPORT_RELATIVE, ROWS_DOCUMENT)
        # Frontera: el fallo de lectura (permisos, disco) se simula en `Path.read_text`, que usa `_read_report`.
        with mock.patch.object(Path, "read_text", side_effect=error):
            with self.assertRaises(tool.AdapterError) as caught:
                tool.normalize_entry(self.entry(report), root=self.tmp)
        return str(caught.exception)

    def test_oserror_con_strerror_cita_el_texto_y_no_la_ruta_absoluta(self) -> None:
        # Se pasa la ruta como `filename`: `str(error)` la repetiría ("[Errno 13] denegado: '<ruta>'").
        absolute = str(self.tmp / REPORT_RELATIVE)
        message = self.read_error(PermissionError(13, "denegado", absolute))
        self.assertTrue(message.startswith(f"{REPORT_RELATIVE}: report: "), message)
        self.assertIn("denegado", message)
        self.assertNotIn(str(self.tmp), message)
        self.assertNotIn(absolute, message)
        # `str(error)` usa el `repr` de la ruta (barras invertidas duplicadas en Windows): se busca también el
        # nombre propio del directorio temporal, que aparece igual en cualquier plataforma.
        self.assertNotIn(self.tmp.name, message)

    def test_oserror_sin_strerror_cita_el_nombre_de_la_clase_y_no_una_ruta(self) -> None:
        # `str(OSError())` es vacío: sin el nombre de la clase el mensaje no diría qué falló.
        message = self.read_error(OSError())
        self.assertTrue(message.startswith(f"{REPORT_RELATIVE}: report: "), message)
        self.assertIn("OSError", message)
        self.assertNotIn(str(self.tmp), message)

    def test_oserror_sin_strerror_pero_con_ruta_no_filtra_la_ruta(self) -> None:
        # Subclase sin `strerror` y con `filename`: se cita la clase, no la ruta que `str(error)` incluiría.
        absolute = str(self.tmp / REPORT_RELATIVE)
        message = self.read_error(PermissionError(None, None, absolute))
        self.assertIn("PermissionError", message)
        self.assertNotIn(str(self.tmp), message)
        self.assertNotIn(self.tmp.name, message)


if __name__ == "__main__":
    unittest.main()
