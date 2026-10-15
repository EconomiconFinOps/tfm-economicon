"""Huecos del QA de la tarea 3.3 de JUP-121 (subcomando `load` de `tools/evaluation-dashboard.py`).

Fichero NUEVO que complementa a `test_evaluation_load.py` sin tocarlo.

Huecos sin test que el QA detectó con mutantes supervivientes (pasan contra el código real y mueren contra su
mutante): `--psql-command` vacío o mal citado, `load_command` vacío, la contraseña dentro del nombre del ejecutable,
el escape de caracteres de control del detalle, el encadenamiento de excepciones, el orden de redacción de las dos
formas de la contraseña, una subclase hostil de `str`, el límite exacto de 300 caracteres y el orden de validación de
`run_load` y de `main`. Excepción: el test de `main` con contraseña inválida y manifiesto inexistente nace en ROJO
(Red): `main` debe validar la contraseña (`build_role_sql`) antes de leer los manifiestos.

Sin base de datos: `subprocess.run` se sustituye por un doble o, para la CLI, se lanza el proceso real de la
herramienta (sin llegar nunca a ejecutar `psql`). La ruta de la herramienta se puede sustituir con
`EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.

Ejecución: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s scripts/tests -p test_evaluation_load_gaps.py -v`
"""
from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_load_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

# Valores literales del contrato (no se leen de la herramienta para poder comparar contra ella).
PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
# Contraseña distintiva: ninguna ventana de cuatro caracteres suya aparece en un texto de error normal.
PW = "ZQ7#kP!wV9&xJ2"
# Conjunto de datos válido y vacío: basta para llegar a `psql` sin leer ningún manifiesto (ni ejecutar Node).
EMPTY_DATASET = {"dataset_version": 1, "runs": []}


def fragments(secret: str, size: int = 4) -> list[str]:
    """Todas las ventanas de `size` caracteres de `secret`: un trozo de la contraseña que sobreviva es una fuga."""
    return [secret[start:start + size] for start in range(len(secret) - size + 1)]


def fake_run(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"", effect: BaseException | None = None):
    """Doble de `subprocess.run` que imita su semántica (con `check=True` lanza `CalledProcessError`)."""
    calls: list[tuple] = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        if effect is not None:
            raise effect
        if kwargs.get("check") and returncode != 0:
            raise subprocess.CalledProcessError(returncode, args, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(args, returncode, stdout, stderr)

    run.calls = calls  # type: ignore[attr-defined]
    return run


def patched_run(**kwargs):
    """Sustituye `subprocess.run` (y devuelve el doble): `tool.subprocess` es el módulo global, así que afecta a todo."""
    double = fake_run(**kwargs)
    return double, mock.patch.object(tool.subprocess, "run", new=double)


def run_cli(*args, env_extra=None, env_remove=()):
    """Lanza la herramienta como proceso real (sin llegar a ejecutar `psql` en ningún caso de este fichero)."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    for key in env_remove:
        env.pop(key, None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]], capture_output=True, env=env,
                          timeout=240, check=False)


class FailureCase(unittest.TestCase):
    """Base: ejecuta `run_load` con un `psql` que falla y devuelve el mensaje del `LoadError`."""

    def failure(self, stderr: bytes, password: str = PW, code: int = 3, **call) -> str:
        double, patch = patched_run(returncode=code, stderr=stderr)
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(EMPTY_DATASET, password, **call)
        self.assertEqual(len(double.calls), 1)
        message = str(caught.exception)
        # Invariantes de todo fallo de `psql`: prefijo, una sola línea y ni rastro de la contraseña.
        self.assertTrue(message.startswith(f"load: psql terminó con código {code}"), message)
        self.assertNotIn("\n", message)
        self.assertNotIn("\r", message)
        self.assertNotIn(password, message)
        return message


# --- Huecos con mutantes supervivientes ------------------------------------------------------------------------


class PsqlCommandOptionTest(unittest.TestCase):
    """`--psql-command` por la CLI como proceso real: los errores de uso salen con el código 2 de `argparse`."""

    def usage_error(self, value: str):
        completed = run_cli("load", "--no-versioned", "--psql-command", value, env_extra={PASSWORD_ENV: PW})
        self.assertEqual(completed.stdout, b"")
        return completed

    def test_un_comando_vacio_o_de_espacios_es_un_error_de_uso(self) -> None:
        # Si se aceptara el vacío, `load` ejecutaría las opciones de `psql` como si fueran el programa (o el comando
        # por defecto contra una base que quien lo escribe no eligió): debe ser un error de uso (código 2).
        for value in ("", "   ", "\t "):
            with self.subTest(value=value):
                completed = self.usage_error(value)
                stderr = completed.stderr.decode("utf-8")
                self.assertEqual(completed.returncode, 2, stderr)
                self.assertIn("--psql-command", stderr)
                self.assertIn("vacío", stderr)

    def test_comillas_sin_cerrar_son_un_error_de_uso_y_no_una_traza(self) -> None:
        # `shlex.split` lanza `ValueError` ante una comilla sin cerrar: sin capturarlo saldría una traza con código 1.
        for value in ("'a", "\"a", "psql -U 'x"):
            with self.subTest(value=value):
                completed = self.usage_error(value)
                stderr = completed.stderr.decode("utf-8")
                self.assertEqual(completed.returncode, 2, stderr)
                self.assertIn("--psql-command", stderr)
                self.assertNotIn("Traceback", stderr)


class LoadCommandEmptyTest(unittest.TestCase):
    def test_un_comando_vacio_es_un_load_error(self) -> None:
        # Una lista o tupla vacía dejaría solo las opciones de `psql` como «programa»: se rechaza con un error claro.
        for empty in ([], ()):
            with self.subTest(type=type(empty).__name__):
                with self.assertRaises(tool.LoadError) as caught:
                    tool.load_command(empty)
                self.assertTrue(str(caught.exception).startswith("load: "), str(caught.exception))

    def test_run_load_con_comando_vacio_no_lanza_nada(self) -> None:
        double, patch = patched_run()
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(EMPTY_DATASET, PW, psql_command=[])
        self.assertTrue(str(caught.exception).startswith("load: "))
        self.assertEqual(double.calls, [])


class ExecutableNameRedactionTest(unittest.TestCase):
    """La contraseña puede estar dentro del NOMBRE del ejecutable (p. ej. `--psql-command "psql-<contraseña>"`)."""

    def failure(self, effect: BaseException) -> str:
        double, patch = patched_run(effect=effect)
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(EMPTY_DATASET, PW, psql_command=[f"psql-{PW}", "-U", "x"])
        return str(caught.exception)

    def test_ejecutable_inexistente_con_la_contrasena_en_el_nombre_sale_tapado(self) -> None:
        message = self.failure(FileNotFoundError(2, "No such file", f"psql-{PW}"))
        self.assertTrue(message.startswith("load: "), message)
        self.assertIn("no se encuentra", message)
        self.assertIn("***", message)
        for piece in fragments(PW):
            self.assertNotIn(piece, message, piece)

    def test_oserror_con_la_contrasena_en_el_nombre_y_en_el_texto_sale_tapado(self) -> None:
        message = self.failure(OSError(13, f"Permission denied: psql-{PW}", f"psql-{PW}"))
        self.assertTrue(message.startswith("load: "), message)
        self.assertIn("***", message)
        for piece in fragments(PW):
            self.assertNotIn(piece, message, piece)


class ControlEscapeTest(FailureCase):
    def test_los_caracteres_de_control_del_detalle_no_llegan_crudos(self) -> None:
        # Un `stderr` con secuencias de terminal (ESC) o un pitido (BEL) no puede reescribir la terminal de quien lee
        # el error: se escapan, y el texto del mensaje sigue siendo legible.
        message = self.failure(b"\x1b[31mERROR: boom\x1b[0m\x07\n")
        self.assertIn("ERROR: boom", message)
        for raw in ("\x1b", "\x07"):
            self.assertNotIn(raw, message)
        # Quedan como texto visible (`\x1b`), no desaparecen sin rastro.
        self.assertIn("\\x1b", message)
        self.assertIn("\\x07", message)


class ExceptionChainTest(unittest.TestCase):
    """Un fallo no encadena la excepción original: su mensaje puede llevar la contraseña y saldría en la traza."""

    def assert_unchained(self, effect: BaseException, **call) -> None:
        double, patch = patched_run(effect=effect)
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(EMPTY_DATASET, PW, **call)
        error = caught.exception
        # `from None`: sin causa explícita y con el contexto implícito suprimido (no se imprime en la traza).
        self.assertIsNone(error.__cause__)
        self.assertIs(error.__suppress_context__, True)

    def test_timeout(self) -> None:
        self.assert_unchained(subprocess.TimeoutExpired(["docker"], 120, output=b"", stderr=f"ERROR: {PW}".encode()))

    def test_oserror(self) -> None:
        self.assert_unchained(OSError(5, f"fallo con {PW} dentro"))

    def test_archivo_no_encontrado(self) -> None:
        self.assert_unchained(FileNotFoundError(2, "No such file", f"psql-{PW}"), psql_command=[f"psql-{PW}"])


class RedactionOrderTest(FailureCase):
    """Con una contraseña que termina en comilla simple, la forma literal (`abc'`) es PREFIJO de la escapada (`abc''`)."""

    SECRET = "abc'"

    def test_las_dos_formas_se_tapan_enteras_y_no_queda_una_comilla_suelta(self) -> None:
        # Si se tapara primero la forma corta, `abc''` quedaría como `***'`: una comilla que, junto al texto de
        # alrededor, revela el final de la contraseña. La forma larga debe tapar primero.
        message = self.failure(b"ERROR:  x abc'' y abc' z\n", self.SECRET)
        self.assertTrue(message.endswith("ERROR:  x *** y *** z"), message)
        self.assertNotIn("abc", message)
        self.assertNotIn("***'", message)

    def test_la_sentencia_repetida_con_la_contrasena_entre_comillas_queda_con_asteriscos_entre_comillas(self) -> None:
        # En un `ALTER ROLE ... PASSWORD 'abc'''` el literal es `'abc'''`: tapado, debe quedar `'***'` exacto.
        message = self.failure(b"ERROR:  PASSWORD 'abc'''\n", self.SECRET)
        self.assertTrue(message.endswith("ERROR:  PASSWORD '***'"), message)
        self.assertNotIn("abc", message)

    def test_la_contrasena_que_empieza_por_la_comilla_tambien(self) -> None:
        # Simétrico por el otro extremo: `'ab` (forma literal) y `''ab` (escapada) no dejan `'` pegada a `***`.
        secret = "'ab"
        message = self.failure(b"ERROR:  p ''ab q 'ab r\n", secret)
        self.assertTrue(message.endswith("ERROR:  p *** q *** r"), message)


class HostileStrSubclassTest(unittest.TestCase):
    def test_una_subclase_de_str_hostil_es_un_load_error_de_contrasena(self) -> None:
        class Hostil(str):
            # Todo lo que una interpolación ingenua podría usar devuelve una inyección.
            def __str__(self) -> str:
                return "x'; DROP ROLE y; --"

            def __repr__(self) -> str:
                return "x'; DROP ROLE y; --"

            def __format__(self, spec: str) -> str:
                return "x'; DROP ROLE y; --"

        # Concretamente `LoadError` con prefijo `password: ` (y no `SqlError` de `sql_literal` ni un script): la
        # contraseña se rechaza ANTES de construir ningún SQL. El valor no aparece en el mensaje.
        with self.assertRaises(tool.LoadError) as caught:
            tool.build_role_sql(Hostil("clave"))
        message = str(caught.exception)
        self.assertTrue(message.startswith("password: "), message)
        self.assertNotIn("DROP ROLE", message)
        self.assertNotIn("clave", message)


class DetailLimitTest(FailureCase):
    PREFIX = "ERROR:  "

    def test_una_linea_de_exactamente_300_caracteres_no_se_recorta(self) -> None:
        line = self.PREFIX + "B" * (300 - len(self.PREFIX))
        self.assertEqual(len(line), 300)
        message = self.failure((line + "\n").encode("utf-8"))
        # Entera y sin marca de recorte.
        self.assertTrue(message.endswith(line), message)
        self.assertNotIn("...", message)
        self.assertLessEqual(len(message), 380)

    def test_una_linea_de_301_caracteres_se_recorta(self) -> None:
        line = self.PREFIX + "B" * (301 - len(self.PREFIX))
        self.assertEqual(len(line), 301)
        message = self.failure((line + "\n").encode("utf-8"))
        self.assertNotIn(line, message)
        # Se conservan los 300 primeros y el mensaje sigue acotado.
        self.assertIn(line[:300], message)
        self.assertLessEqual(len(message), 380)


class ValidationOrderTest(unittest.TestCase):
    def test_run_load_con_datos_y_contrasena_invalidos_da_el_error_de_los_datos(self) -> None:
        # Los datos se validan PRIMERO: quien tiene las dos cosas mal corrige antes lo que viene de los informes, y
        # el error de datos nunca se queda tapado por el de la contraseña. Ninguno de los dos llega a `psql`.
        double, patch = patched_run()
        bad_datasets = ({"dataset_version": 2, "runs": []}, "no es un objeto", {"dataset_version": 1, "runs": "x"})
        with patch:
            for dataset in bad_datasets:
                with self.subTest(dataset=str(dataset)[:30]):
                    with self.assertRaises(ValueError) as caught:
                        tool.run_load(dataset, "")
                    self.assertNotIsInstance(caught.exception, tool.LoadError)
                    self.assertFalse(str(caught.exception).startswith("password: "), str(caught.exception))
        self.assertEqual(double.calls, [])

    def test_main_con_contrasena_invalida_y_manifiesto_inexistente_da_el_error_de_la_contrasena(self) -> None:
        # Contrato de `main`: la contraseña se valida «ANTES de hacer nada», también antes de leer el manifiesto. Una
        # contraseña inválida no puede quedar oculta tras un error de datos ni llegar a leer ningún informe.
        double, patch = patched_run()
        out, err = io.StringIO(), io.StringIO()
        argv = ["load", "--no-versioned", "--manifest", str(ROOT / "no-existe-jup121-gaps.json")]
        with mock.patch.dict(os.environ, {PASSWORD_ENV: "Q" * 201 + "ZQXLEAK"}), patch, \
                redirect_stdout(out), redirect_stderr(err):
            code = tool.main(argv)
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertTrue(err.getvalue().startswith("error: password: "), err.getvalue())
        self.assertNotIn("ZQXLEAK", err.getvalue())
        self.assertNotIn("no-existe", err.getvalue())
        self.assertEqual(double.calls, [])


if __name__ == "__main__":
    unittest.main()
