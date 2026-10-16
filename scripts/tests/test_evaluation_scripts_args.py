"""Un `--` suelto de pnpm no debe romper la línea de comandos de `tools/evaluation-dashboard.py` (JUP-121, tarea 3.4, Red).

pnpm 9 reenvía al script el `--` literal que se escribe tras el nombre del script: `corepack pnpm
evaluation-dashboard:rows -- --no-versioned` ejecuta `python tools/evaluation-dashboard.py rows "--" "--no-versioned"`.
Hoy `argparse` rechaza ese `--` («unrecognized arguments») con el código 2. Como la herramienta no tiene argumentos
posicionales, el `--` no aporta nada y se puede ignorar sin perder información.

Contrato que se valida (decidido por el coordinador de la tarea):

* `main(argv)` ignora UN `--` suelto: la PRIMERA aparición exacta del argumento `--`. Con eso `rows -- --no-versioned`,
  `sql -- --no-versioned`, `load -- --manifest X` y `-- rows --no-versioned` se comportan como si no estuviera el `--`.
* Un SEGUNDO `--`, o un `--` pegado a otro texto (`--x`, `---`), no se toca: `argparse` lo rechaza con el código 2.
  Así `rows -- -- --no-versioned` sigue siendo un error de uso: tras quitar el primero queda `rows -- --no-versioned`,
  y `argparse` rechaza el sobrante.
* Un `--` que sigue a una opción que espera valor (`--manifest --`) no se elimina para «dárselo» como valor:
  `argparse` nunca toma `--` como valor y responde «expected one argument» con el código 2. Se fija ese resultado
  (también con una ruta detrás: `--manifest -- RUTA` sigue siendo el código 2, no se convierte en `--manifest RUTA`).
* Los scripts de pnpm `evaluation-dashboard:rows` y `:sql` imprimen lo mismo con y sin `--`.

Casos que PASAN HOY a propósito (guardas del contrato que ya se cumplen y que el cambio no debe romper): dos `--`,
`---`, `--x`, `-- rows --no-versioned --` (el segundo `--` sobrante), `--manifest --` y `--manifest -- RUTA`. Ojo con
`-- rows --no-versioned`: pasa hoy con Python 3.13 porque `argparse` ya tolera un `--` inicial, pero no es seguro que
pase con 3.12 (la versión de la CI), donde solo el cambio lo garantiza.

Valores esperados escritos a mano (nunca calculados con la herramienta). La ruta de la herramienta se puede sustituir
con `EVALUATION_DASHBOARD_TOOL` y la de `package.json` con `EVALUATION_PACKAGE_JSON` para apuntar a copias mutadas.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
PACKAGE_JSON = Path(os.environ.get("EVALUATION_PACKAGE_JSON") or ROOT / "package.json")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_scripts_args", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
# Conjunto de datos vacío (sin manifiesto versionado), formateado como lo escribe `rows`.
ROWS_EMPTY = json.dumps({"dataset_version": 1, "runs": []}, indent=2) + "\n"
MISSING_PASSWORD_ERROR = f"error: falta la variable de entorno {PASSWORD_ENV}\n"


def run_main(argv, *, without_password=False):
    """Ejecuta `main` en proceso con la salida capturada. Devuelve (código, stdout, stderr).

    `argparse` termina con `SystemExit`: se convierte en su código para poder comparar sin que el test explote.
    """
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ):
        if without_password:
            os.environ.pop(PASSWORD_ENV, None)
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = tool.main(list(argv))
            except SystemExit as exit_:
                code = exit_.code
    return code, out.getvalue(), err.getvalue()


def run_cli(*args):
    """Lanza la herramienta como proceso real (el código 2 de `argparse` solo se ve así), sin contraseña en el entorno."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop(PASSWORD_ENV, None)
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=240, check=False,
    )


def run_pnpm(*args):
    """Lanza `corepack pnpm ...` en la raíz del espacio de trabajo (la carpeta de `package.json`)."""
    corepack = shutil.which("corepack")
    if corepack is None:
        raise AssertionError("corepack no está disponible en el PATH (Node/pnpm son requisito del repositorio)")
    return subprocess.run(
        [corepack, "pnpm", *args], cwd=PACKAGE_JSON.parent,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, check=False,
    )


def tool_output(stdout, first_line):
    """Quita la cabecera de pnpm (líneas `>` o vacías) y devuelve lo que imprime la herramienta desde `first_line`."""
    lines = stdout.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.rstrip("\r\n") == first_line), None)
    if start is None:
        raise AssertionError(f"la salida no contiene una línea `{first_line}`: {stdout!r}")
    foreign = [line for line in lines[:start] if line.strip() and not line.startswith(">")]
    if foreign:
        raise AssertionError(f"antes de la salida de la herramienta solo puede ir la cabecera de pnpm: {foreign!r}")
    return "".join(lines[start:])


class DoubleDashInProcessTests(unittest.TestCase):
    """`main` en proceso: un `--` suelto no cambia nada."""

    def test_rows_con_doble_guion_da_la_misma_salida_que_sin_el(self):
        # Caso de pnpm: `rows -- --no-versioned`. Debe imprimir el conjunto vacío y devolver 0, igual que sin `--`.
        sin = run_main(["rows", "--no-versioned"])
        self.assertEqual(sin, (0, ROWS_EMPTY, ""))
        self.assertEqual(run_main(["rows", "--", "--no-versioned"]), sin)

    def test_sql_con_doble_guion_da_la_misma_salida_que_sin_el(self):
        # Igual para `sql`: la salida es el script transaccional completo, idéntico con y sin `--`.
        sin = run_main(["sql", "--no-versioned"])
        self.assertEqual(sin[0], 0)
        self.assertTrue(sin[1].startswith("BEGIN;"))
        self.assertEqual(run_main(["sql", "--", "--no-versioned"]), sin)

    def test_load_con_doble_guion_sin_contrasena_da_el_mismo_error_que_sin_el(self):
        # `load` mira la contraseña antes que nada: sin ella, el error y el código 1 deben ser los mismos con `--`.
        sin = run_main(["load", "--no-versioned"], without_password=True)
        self.assertEqual(sin, (1, "", MISSING_PASSWORD_ERROR))
        self.assertEqual(run_main(["load", "--", "--no-versioned"], without_password=True), sin)

    def test_load_con_doble_guion_y_manifest_sin_contrasena_da_el_error_de_la_contrasena(self):
        # El caso documentado de la guía: `load -- --manifest X`. Sin contraseña, el error es el de la variable (no
        # el de `argparse` ni el de un manifiesto inexistente, que ni se llega a leer).
        codigo, salida, error = run_main(["load", "--", "--manifest", "no-existe.json"], without_password=True)
        self.assertEqual((codigo, salida, error), (1, "", MISSING_PASSWORD_ERROR))

    def test_doble_guion_antes_del_subcomando_se_ignora(self):
        # `-- rows --no-versioned`: el `--` va delante del subcomando y tampoco cambia nada.
        self.assertEqual(run_main(["--", "rows", "--no-versioned"]), (0, ROWS_EMPTY, ""))

    def test_doble_guion_al_final_se_ignora(self):
        # `rows --no-versioned --`: hoy `argparse` lo rechaza como sobrante («unrecognized arguments: --»).
        self.assertEqual(run_main(["rows", "--no-versioned", "--"]), (0, ROWS_EMPTY, ""))

    def test_solo_se_ignora_el_primero_de_dos_dobles_guiones(self):
        # Se quita UNA aparición, la primera. En `-- rows --no-versioned --` queda el segundo, que `argparse` rechaza:
        # distingue «quitar el primero» de «quitar el último» (que dejaría `-- rows --no-versioned`, válido).
        codigo, salida, error = run_main(["--", "rows", "--no-versioned", "--"])
        self.assertEqual(codigo, 2)
        self.assertEqual(salida, "")
        self.assertIn("unrecognized arguments", error)

    def test_dos_dobles_guiones_seguidos_siguen_siendo_un_error_de_uso(self):
        # Quitar TODOS los `--` haría válido `rows -- -- --no-versioned`; con el contrato queda `rows -- --no-versioned`.
        codigo, salida, _ = run_main(["rows", "--", "--", "--no-versioned"])
        self.assertEqual((codigo, salida), (2, ""))

    def test_un_guion_pegado_a_otro_texto_no_se_toca(self):
        # `---` y `--x` no son el argumento exacto `--`: se dejan y `argparse` los rechaza (código 2). Un `--no-versioned`
        # válido delante demuestra que el rechazo viene del argumento raro y no de otra cosa.
        for rarisimo in ("---", "--x"):
            with self.subTest(argumento=rarisimo):
                codigo, salida, error = run_main(["rows", "--no-versioned", rarisimo])
                self.assertEqual((codigo, salida), (2, ""))
                self.assertIn(rarisimo, error)

    def test_doble_guion_como_valor_de_una_opcion_no_se_elimina(self):
        # `argparse` nunca toma `--` como valor: `--manifest --` es «expected one argument» (código 2) y debe seguir
        # siéndolo. Con una ruta detrás, quitar el `--` lo convertiría en `--manifest RUTA` (código 1, manifiesto
        # inexistente): eso es lo que se descarta.
        for argv in (["rows", "--no-versioned", "--manifest", "--"],
                     ["rows", "--no-versioned", "--manifest", "--", "no-existe.json"]):
            with self.subTest(argv=argv):
                codigo, salida, error = run_main(argv)
                self.assertEqual((codigo, salida), (2, ""))
                self.assertIn("expected one argument", error)


class DoubleDashCliTests(unittest.TestCase):
    """Línea de comandos real: códigos de salida de proceso."""

    def test_rows_con_doble_guion_sale_con_0(self):
        resultado = run_cli("rows", "--", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.replace("\r\n", "\n"), ROWS_EMPTY)

    def test_sql_con_doble_guion_sale_con_0(self):
        resultado = run_cli("sql", "--", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertTrue(resultado.stdout.startswith("BEGIN;"))

    def test_doble_guion_al_final_sale_con_0(self):
        resultado = run_cli("rows", "--no-versioned", "--")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.replace("\r\n", "\n"), ROWS_EMPTY)

    def test_dos_dobles_guiones_salen_con_2(self):
        # Segundo `--` sin tocar: `argparse` no reconoce el argumento sobrante.
        resultado = run_cli("rows", "--", "--", "--no-versioned")
        self.assertEqual(resultado.returncode, 2)
        self.assertEqual(resultado.stdout, "")
        self.assertIn("unrecognized arguments", resultado.stderr)

    def test_doble_guion_tras_manifest_sale_con_2_y_no_se_elimina(self):
        resultado = run_cli("rows", "--no-versioned", "--manifest", "--")
        self.assertEqual(resultado.returncode, 2)
        self.assertEqual(resultado.stdout, "")
        self.assertIn("expected one argument", resultado.stderr)


class DoubleDashPnpmTests(unittest.TestCase):
    """Los scripts de pnpm con el `--` que pnpm 9 reenvía literal (necesitan Node/pnpm y la tarea 3.4)."""

    def test_script_rows_con_doble_guion_imprime_lo_mismo_que_sin_el(self):
        resultado = run_pnpm("evaluation-dashboard:rows", "--", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(tool_output(resultado.stdout, "{").replace("\r\n", "\n"), ROWS_EMPTY)

    def test_script_sql_con_doble_guion_imprime_lo_mismo_que_sin_el(self):
        resultado = run_pnpm("evaluation-dashboard:sql", "--", "--no-versioned")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        salida = tool_output(resultado.stdout, "BEGIN;")
        self.assertTrue(salida.startswith("BEGIN;"))
        self.assertIn("COMMIT;", salida)


if __name__ == "__main__":
    unittest.main()
