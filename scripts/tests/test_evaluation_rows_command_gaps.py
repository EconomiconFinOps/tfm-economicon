"""Ramas defensivas de `rows` en `tools/evaluation-dashboard.py` (JUP-121, tarea 2.8, remediación de mutación).

Complementa `test_evaluation_rows_command.py` (no se importa ni se modifica): cada prueba fija una rama de error
que ninguna prueba anterior distinguía de su mutante. Todas PASAN con el producto real; su valor es que un
mutante de la rama defensiva las hace fallar.

Ramas cubiertas:

1. Error al escribir `--output` (`_write_atomically` y el `except OSError` de `main`): código 1, mensaje en
   stderr, sin dejar temporales `.tmp` ni pisar el fichero anterior.
2. Fecha que desborda al pasar a UTC (`derive_run_id`): error de datos `run.run_at`, no una traza.
3. JSON anidado hasta desbordar el parser o los pasos posteriores: `AdapterError`, no `RecursionError` crudo.
4. JSON inválido (truncado): `AdapterError` con el prefijo `<fichero>: report: `.
5. Informe de negocio (JUP-068) sin `run_id` ni en el informe ni en la entrada.
6. Etiqueta del fichero en el error de `run_id` repetido (ruta relativa dentro de `root`, solo nombre fuera).

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_command_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

JUP_070_RUN_2 = ROOT / "docs" / "evidence" / "JUP-070-run-2-report.json"
JUP_068_EXAMPLE = ROOT / "docs" / "validation" / "JUP-068-example.json"

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

# Informe de negocio de JUP-068 (salida de Node real sobre el ejemplo), fijado por `setUpModule`.
REPORT_068: dict = {}


def setUpModule() -> None:
    REPORT_068.update(tool.read_business_report(JUP_068_EXAMPLE))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_cli(*args):
    # Proceso real: es la única forma de comprobar el código de salida y qué sale por stdout y stderr.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]],
        capture_output=True, text=True, encoding="utf-8", env=env, timeout=240, check=False,
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

    def write_manifest(self, relative: str, entries: list) -> Path:
        return self.write(relative, {"manifest_version": 1, "runs": entries})

    def normalize_error(self, path, fmt, *, root=None, run_id=None) -> str:
        entry = {"path": Path(path), "format": fmt, "milestone": True, "run_id": run_id,
                 "manifest": Path(path).parent / "manifiesto.json"}
        with self.assertRaises(tool.AdapterError) as caught:
            tool.normalize_entry(entry, root=self.tmp if root is None else root)
        return str(caught.exception)

    def local_manifest(self) -> Path:
        report = self.write("local-informe.json", ROWS_DOCUMENT)
        return self.write_manifest("local.json", [{"path": str(report), "format": "rows-v1", "milestone": False}])

    def temporaries(self, directory: Path) -> list:
        # Temporales de `_write_atomically`: `.<nombre>.<aleatorio>.tmp`.
        return sorted(path.name for path in directory.iterdir() if path.name.startswith(".") and path.name.endswith(".tmp"))


# --- 1. Error al escribir --output ---------------------------------------------------------------------------


class OutputWriteErrorTest(TmpCase):
    def test_directorio_de_salida_inexistente_da_codigo_1_y_no_crea_nada(self) -> None:
        # `mkstemp` falla antes del `try` de `_write_atomically`: lo captura el `except OSError` de `main`. Debe
        # ser un error de uso del entorno (código 1 y mensaje), no una traza ni el 2 de `argparse`.
        manifest = self.local_manifest()
        before = sorted(path.name for path in self.tmp.iterdir())
        target = self.tmp / "no" / "existe" / "salida.json"
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", target)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("error: "), completed.stderr)
        self.assertIn("no se puede escribir la salida", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(completed.stdout, "")
        # No se crea el directorio ausente ni ningún fichero.
        self.assertFalse((self.tmp / "no").exists())
        self.assertEqual(sorted(path.name for path in self.tmp.iterdir()), before)

    def test_destino_que_es_un_directorio_existente_da_codigo_1_y_no_deja_temporales(self) -> None:
        # El temporal se crea bien (el directorio padre existe) y `os.replace` falla al renombrarlo sobre un
        # directorio: el `except` de `_write_atomically` debe borrar el temporal Y relanzar. Sin el `raise`, el
        # error se tragaría y la herramienta saldría con 0 sin haber escrito nada.
        manifest = self.local_manifest()
        work = self.tmp / "trabajo"
        work.mkdir()
        destination = work / "destino"
        destination.mkdir()
        completed = run_cli("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--output", destination)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("error: "), completed.stderr)
        self.assertIn("no se puede escribir la salida", completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertTrue(destination.is_dir())
        self.assertEqual(self.temporaries(work), [])
        self.assertEqual(sorted(path.name for path in work.iterdir()), ["destino"])

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = tool.main([str(arg) for arg in argv])
        return code, out.getvalue(), err.getvalue()

    def test_fallo_de_os_replace_conserva_el_fichero_anterior_y_borra_el_temporal(self) -> None:
        # Frontera simulada: el renombrado final falla (permisos, disco). El fichero previo no se toca y el
        # temporal no queda huérfano en el directorio.
        manifest = self.local_manifest()
        work = self.tmp / "trabajo"
        work.mkdir()
        target = work / "filas.json"
        target.write_text("contenido previo", encoding="utf-8")
        with mock.patch.object(tool.os, "replace", side_effect=PermissionError(13, "denegado")):
            code, out, err = self.run_main("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp,
                                           "--output", target)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn("denegado", err)
        self.assertEqual(target.read_text(encoding="utf-8"), "contenido previo")
        self.assertEqual(self.temporaries(work), [])
        self.assertEqual(sorted(path.name for path in work.iterdir()), ["filas.json"])

    def test_la_escritura_correcta_no_deja_temporales(self) -> None:
        manifest = self.local_manifest()
        work = self.tmp / "trabajo"
        work.mkdir()
        target = work / "filas.json"
        code, out, err = self.run_main("rows", "--no-versioned", "--manifest", manifest, "--root", self.tmp,
                                       "--output", target)
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertEqual(self.temporaries(work), [])
        self.assertEqual(sorted(path.name for path in work.iterdir()), ["filas.json"])
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["runs"][0]["run"]["run_id"], "JUP-071-demo-1")


# --- 2. Fecha que desborda al pasar a UTC --------------------------------------------------------------------


class UtcOverflowTest(TmpCase):
    def report_with_date(self, name: str, date: str) -> Path:
        document = load_json(JUP_070_RUN_2)
        document["run"]["date"] = date
        return self.write(name, document)

    def test_fecha_que_desborda_en_utc_es_un_error_de_datos_con_prefijo_de_fichero(self) -> None:
        # 0001-01-01 con desfase positivo y 9999-12-31 con desfase negativo no caben en UTC (`OverflowError`).
        # Sin el `raise` de `derive_run_id` el fallo sería un `UnboundLocalError` en vez de un error de `run.run_at`.
        for date in ("0001-01-01T00:00:00+05:00", "9999-12-31T23:59:59-05:00"):
            with self.subTest(fecha=date):
                path = self.report_with_date("dentro/informe.json", date)
                message = self.normalize_error(path, "jup-070-report-v1")
                self.assertTrue(message.startswith("dentro/informe.json: run.run_at: "), message)
                self.assertIn("UTC", message)
                # Fuera de `root` solo se cita el nombre del fichero.
                message = self.normalize_error(path, "jup-070-report-v1", root=ROOT)
                self.assertTrue(message.startswith("informe.json: run.run_at: "), message)
                self.assertNotIn(str(self.tmp), message)

    def test_fechas_cerca_del_limite_que_si_caben_siguen_derivando_el_run_id(self) -> None:
        # Contraste del caso anterior: el desbordamiento solo se declara cuando de verdad no cabe en UTC.
        cases = (
            ("0001-01-02T00:00:00+00:00", "00010102T000000Z"),
            ("9999-12-30T23:59:59Z", "99991230T235959Z"),
        )
        for date, stamp in cases:
            with self.subTest(fecha=date):
                path = self.report_with_date("limite.json", date)
                entry = {"path": path, "format": "jup-070-report-v1", "milestone": True, "run_id": None,
                         "manifest": self.tmp / "m.json"}
                run_id = tool.normalize_entry(entry, root=self.tmp)["run"]["run_id"]
                self.assertRegex(run_id, rf"^jup-070-{stamp}-[0-9a-f]{{8}}$")


# --- 3 y 4. JSON anidado e inválido --------------------------------------------------------------------------


class ReportJsonErrorsTest(TmpCase):
    def test_json_anidado_hasta_desbordar_el_parser_es_adapter_error_y_no_recursion_error(self) -> None:
        # Miles de niveles: `json.loads` lanza `RecursionError`; debe salir como error de datos prefijado.
        for name, text in (("lista.json", "[" * 100000), ("objeto.json", '{"a":' * 100000)):
            with self.subTest(fichero=name):
                path = self.tmp / name
                path.write_text(text, encoding="utf-8")
                message = self.normalize_error(path, "rows-v1")
                self.assertTrue(message.startswith(f"{name}: report: "), message)
                self.assertIn("JSON inválido", message)
                self.assertNotIn("\n", message)

    def test_recursion_en_un_paso_posterior_al_parseo_dice_demasiado_anidado(self) -> None:
        # Un documento que el parser acepta pero que desborda la pila al procesarlo (huella, adaptador) cae en la
        # rama `except RecursionError` de `normalize_entry`. Se simula el desbordamiento en la huella (frontera
        # estrecha) porque provocarlo de verdad depende del límite de recursión de cada intérprete.
        path = self.write("anidado.json", ROWS_DOCUMENT)
        with mock.patch.object(tool, "report_digest", side_effect=RecursionError("maximum recursion depth exceeded")):
            message = self.normalize_error(path, "rows-v1")
        self.assertEqual(message, "anidado.json: el documento está demasiado anidado")

    def test_json_invalido_truncado_es_error_de_report_con_prefijo(self) -> None:
        path = self.tmp / "truncado.json"
        path.write_text('{"a": ', encoding="utf-8")
        message = self.normalize_error(path, "rows-v1")
        self.assertTrue(message.startswith("truncado.json: report: "), message)
        self.assertIn("JSON", message)
        self.assertIn("inválido", message)


# --- 5. Informe de negocio sin run_id ------------------------------------------------------------------------


class BusinessReportWithoutRunIdTest(TmpCase):
    def test_sin_run_id_en_el_informe_ni_en_la_entrada_es_un_error_de_run_id(self) -> None:
        # El informe de Node (simulado en la frontera) no trae `run_id` y la entrada tampoco. Si no se rechazara
        # aquí, el fallo saldría después con otro mensaje (el del adaptador con `run_id=None`).
        report = copy.deepcopy(REPORT_068)
        report.pop("run_id", None)
        path = self.write("negocio.json", load_json(JUP_068_EXAMPLE))
        with mock.patch.object(tool, "read_business_report", return_value=report):
            message = self.normalize_error(path, "jup-068-input-v1")
        self.assertTrue(message.startswith("negocio.json: run_id: "), message)
        self.assertIn("no trae run_id", message)
        self.assertIn("la entrada del manifiesto tampoco", message)

    def test_con_run_id_explicito_en_la_entrada_el_informe_sin_run_id_si_vale(self) -> None:
        # Contraste: el identificador de la entrada suple al ausente del informe.
        report = copy.deepcopy(REPORT_068)
        report.pop("run_id", None)
        path = self.write("negocio.json", load_json(JUP_068_EXAMPLE))
        entry = {"path": path, "format": "jup-068-input-v1", "milestone": True, "run_id": "desde-la-entrada",
                 "manifest": self.tmp / "m.json"}
        with mock.patch.object(tool, "read_business_report", return_value=report):
            output = tool.normalize_entry(entry, root=self.tmp)
        self.assertEqual(output["run"]["run_id"], "desde-la-entrada")


# --- 6. Etiqueta de fichero en el run_id repetido ------------------------------------------------------------


class DuplicateRunIdLabelTest(TmpCase):
    def duplicate_manifest(self, folder: str) -> Path:
        # Dos copias del mismo `rows-v1` (mismo `run_id` en el documento) en `folder`, referidas por ruta absoluta.
        first = self.write(f"{folder}/informe-a.json", ROWS_DOCUMENT)
        second = self.write(f"{folder}/informe-b.json", ROWS_DOCUMENT)
        return self.write_manifest("manifiesto.json", [
            {"path": str(first), "format": "rows-v1", "milestone": False},
            {"path": str(second), "format": "rows-v1", "milestone": False}])

    def duplicate_message(self, manifest: Path, root: Path) -> str:
        with self.assertRaises(tool.AdapterError) as caught:
            tool.build_dataset([manifest], root=root)
        return str(caught.exception)

    def test_dentro_de_la_raiz_las_dos_rutas_son_relativas_y_con_barras(self) -> None:
        manifest = self.duplicate_manifest("sub")
        message = self.duplicate_message(manifest, self.tmp)
        self.assertTrue(message.startswith("run_id: "), message)
        self.assertIn("sub/informe-a.json", message)
        self.assertIn("sub/informe-b.json", message)
        self.assertNotIn(str(self.tmp), message)
        self.assertNotIn("\\", message)

    def test_fuera_de_la_raiz_solo_aparecen_los_nombres_de_fichero(self) -> None:
        # Con el informe fuera de `root` la etiqueta es solo el nombre (no la ruta absoluta ni `None`, que es lo
        # que daría usar la ruta relativa inexistente).
        manifest = self.duplicate_manifest("fuera")
        root = self.tmp / "raiz"
        root.mkdir()
        message = self.duplicate_message(manifest, root)
        self.assertTrue(message.startswith("run_id: "), message)
        self.assertIn("repetido en informe-b.json; ya lo usa informe-a.json", message)
        self.assertNotIn("None", message)
        self.assertNotIn(str(self.tmp), message)
        self.assertNotIn("fuera/", message)
        self.assertNotIn("fuera\\", message)


if __name__ == "__main__":
    unittest.main()
