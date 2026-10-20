"""Subcomando `load` de `tools/evaluation-dashboard.py` (JUP-121, tarea 3.3, Red).

`load` carga el conjunto de datos en PostgreSQL y crea o actualiza el rol de solo lectura de Grafana. Contrato que se
valida (ADR-0022, `design.md` D1, D2 y D8 y las spec «Acceso de Grafana de solo lectura» y «Regeneración con un único
comando»):

* Constantes `READER_ROLE`, `PASSWORD_ENV`, `DEFAULT_PSQL_COMMAND`, `PSQL_FLAGS` y `LOAD_TIMEOUT`, y la clase
  `LoadError(ValueError)`.
* `build_role_sql(password)`: script SQL APARTE del de `build_sql` (que no puede llevar `GRANT`, `PASSWORD` ni `CREATE
  ROLE`). Puro y determinista. Dentro de una transacción y en este orden: `SET LOCAL standard_conforming_strings = on`,
  un `DO $$ ... $$` que crea el rol solo si no está en `pg_roles` (`CREATE ROLE` no tiene `IF NOT EXISTS`), `ALTER ROLE
  ... WITH LOGIN PASSWORD <literal>` (siempre, para rotar la contraseña), `GRANT CONNECT` en la base, `GRANT USAGE` en
  el esquema, `GRANT SELECT ON ALL TABLES` (tablas y vistas) y `ALTER DEFAULT PRIVILEGES ... GRANT SELECT`. Nada más.
  Valida la contraseña (`str` no vacía, sin caracteres de control, hasta 200 caracteres) con `LoadError` de prefijo
  `password: ` que nunca cita el valor.
* `load_command(psql_command=None)`: el comando de `psql` más `PSQL_FLAGS`.
* `run_load(dataset, password, psql_command=None, timeout=LOAD_TIMEOUT)`: concatena `build_sql` y `build_role_sql` y los
  pasa a `psql` por la entrada estándar (bytes UTF-8). La contraseña NUNCA va en los argumentos ni en el entorno. Los
  fallos son `LoadError` con prefijo `load: ` y, si hay `stderr`, su última línea no vacía (hasta 300 caracteres) con la
  contraseña redactada: `psql` repite la sentencia que falla y ahí iría.
* Subcomando `load` de `main`: lee la contraseña de `GRAFANA_EVALUATION_DB_PASSWORD` ANTES de hacer nada.

Las pruebas son de tres clases:

* SIN proceso externo: `build_role_sql`, `load_command`, `run_load` y `main` con `subprocess.run` sustituido por un doble
  que imita su semántica (incluido `check=True`), de modo que no dependen de cómo el coder gestione el código de salida.
  Los conjuntos de datos usan solo `rows-v1` locales (nunca el manifiesto versionado, que ejecuta Node con `subprocess`).
* Con un `psql` FALSO (un script de Python que registra argumentos, entrada, entorno y directorio y sale con el código
  pedido): procesos reales, sin Docker. Prueban lo que un doble no puede: que los bytes llegan intactos, que el entorno
  real no lleva la contraseña, el `cwd`, el timeout y la salida byte a byte de la CLI.
* Con PostgreSQL real (el contenedor desechable de `evaluation_pg_helper`, la imagen exacta de `postgres-pgvector`).
  `load` se ejecuta con `--psql-command "docker exec -i <contenedor> psql ..."`. Para iniciar sesión COMO el rol de
  Grafana se usa `docker exec` + `psql -h <IP del contenedor en el puente>`: la imagen oficial confía en las conexiones
  por socket y por `127.0.0.1` y exige `scram-sha-256` en el resto, así que solo una conexión a la IP propia comprueba
  de verdad la contraseña. La contraseña viaja por `PGPASSWORD` en el entorno del cliente de Docker (`-e PGPASSWORD` sin
  valor), no en la línea de comandos. Funciona en Windows sin tener `psql` en el equipo.

Decisiones donde el contrato admite más de una lectura (fijadas aquí; el coder debe respetarlas):

* «Carácter de control» es la categoría Unicode `Cc` que el contrato cita de forma explícita (`\\n`, `\\x00`) más `\\r`, `\\t`,
  `\\x1b` y `\\x7f`. La longitud se mide en caracteres, no en bytes (200 `ñ` son válidas). Una cadena con sustitutos
  sueltos (lo que produce `os.environ` en Linux con bytes inválidos, p. ej. `\\udcff`) tampoco se puede enviar en UTF-8:
  se rechaza con `LoadError` de prefijo `password: ` en lugar de dejar escapar un `UnicodeEncodeError` (endurecimiento
  que va más allá del texto literal del contrato).
* `LoadError` es la única excepción de `run_load` ante un fallo de ejecución. La redacción de la contraseña se aplica a
  TODO mensaje de error de `run_load` (también al de un `OSError`) y ANTES de truncar a 300 caracteres: truncar primero
  dejaría un trozo de la contraseña pegado al corte.
* La última línea no vacía se toma tras quitar los `\\r` y sin espacios en los extremos; el mensaje es una sola línea.
* Los textos de error de `run_load` que se fijan son los del contrato: `psql terminó con código N`, `no se encuentra`
  (con el nombre del ejecutable) y `timeout` (con los segundos); el resto del mensaje es libre.
* `run_load` pasa a `subprocess.run` `input` (bytes), `capture_output=True`, `timeout`, `cwd=ROOT` y `env` (`os.environ`
  sin `GRAFANA_EVALUATION_DB_PASSWORD` y con `PGCLIENTENCODING=UTF8`); sin `shell` ni modo texto.
* `--output` no es una opción de `load` y `--psql-command` no es una opción de `rows` ni de `sql`.
* El PRIMER fallo de la parte de datos detiene la carga (`ON_ERROR_STOP`): el rol y la contraseña anteriores quedan como
  estaban.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (ayudante compartido con las pruebas de 3.2 y 5.x)

TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_load", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

# Valores literales del contrato (no se leen de la herramienta para poder comparar contra ella).
READER = "grafana_evaluation_reader"
PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
EXPECTED_DEFAULT_COMMAND = ["docker", "compose", "exec", "-T", "-e", "PGCLIENTENCODING=UTF8", "postgres-pgvector",
                            "psql", "-U", "postgres", "-d", "embeddings"]
EXPECTED_FLAGS = ["-v", "ON_ERROR_STOP=1", "-X", "-q"]
MISSING_VARIABLE_ERROR = "error: falta la variable de entorno GRAFANA_EVALUATION_DB_PASSWORD\n"

# Contraseña distintiva: ninguna ventana de cuatro caracteres suya aparece en un texto de error normal.
PW = "ZQ7#kP!wV9&xJ2"
# Con comillas, barra invertida, comillas dobles, `$$`, un punto y coma y unicode: todo lo que rompe un escape ingenuo.
PW_HOSTILE = "n'ew\\pä\"ss日本 $$ ;-- Zq"

# Documento `rows-v1` mínimo y válido (mismo que el de las pruebas de `sql`): una ejecución y dos resultados.
ROWS_DOCUMENT = {
    "contract_version": 1,
    "run": {
        "run_id": "JUP-071-demo-1", "source": "JUP-071", "run_at": "2026-10-10T09:00:00Z", "commit": "abc1234",
        "suite": "JUP-069", "suite_version": "JUP-069-v1", "retrieval": {"top_k": 4},
    },
    "results": [
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "pass",
         "count": 3, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
        {"measure_type": "A", "grp": "robustness", "metric_id": "ROB-1", "behavior": "typo", "status": "fail",
         "count": 1, "unit": "recuento", "denominator": 4, "judgment": "automatic"},
    ],
}


# --- Ayudantes de lectura del SQL (escritos aquí, independientes de la herramienta) -----------------------------


def squash(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())


def unescape_literal(literal: str) -> str:
    """Invierte un literal de cadena SQL: comillas exteriores y cada comilla interior duplicada."""
    assert len(literal) >= 2 and literal[0] == "'" and literal[-1] == "'", f"no es un literal entre comillas: {literal[:40]!r}"
    inner = literal[1:-1]
    out, i = [], 0
    while i < len(inner):
        if inner[i] == "'":
            # Una comilla interior sin pareja cerraría la cadena antes de tiempo: ahí empezaría una inyección.
            assert inner[i + 1:i + 2] == "'", f"comilla interior sin duplicar en la posición {i}"
            out.append("'")
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


def split_statements(script: str) -> list[str]:
    """Trocea por `;` fuera de cadenas `'...'` y de bloques `$$...$$`; descarta los comentarios `--`.

    Un `DO $$ ... $$` lleva `;` dentro y una contraseña hostil lleva `'`, `$$`, `;` y `--`: ni lo uno ni lo otro puede
    partir una sentencia, y es justo lo que se quiere comprobar.
    """
    statements, current, i, n = [], [], 0, len(script)
    while i < n:
        char = script[i]
        if char == "'":
            j = i + 1
            while True:
                assert j < n, "cadena sin cerrar"
                if script[j] == "'":
                    if script[j + 1:j + 2] == "'":
                        j += 2
                        continue
                    break
                j += 1
            current.append(script[i:j + 1])
            i = j + 1
        elif script.startswith("$$", i):
            end = script.find("$$", i + 2)
            assert end >= 0, "bloque $$ sin cerrar"
            current.append(script[i:end + 2])
            i = end + 2
        elif script.startswith("--", i):
            end = script.find("\n", i)
            i = n if end < 0 else end
        elif char == ";":
            statements.append("".join(current).strip())
            current = []
            i += 1
        else:
            current.append(char)
            i += 1
    assert "".join(current).strip() == "", "texto tras la última sentencia: falta el `;` final"
    return statements


# Sentencias fijas del script del rol (sin el `;` final), por posición. La 2 (el `DO`) y la 3 (`ALTER ROLE`) se
# comprueban aparte: la primera por su contenido y la segunda porque lleva la contraseña.
FIXED_STATEMENTS = {
    0: "BEGIN",
    1: "SET LOCAL standard_conforming_strings = on",
    4: f"GRANT CONNECT ON DATABASE embeddings TO {READER}",
    5: f"GRANT USAGE ON SCHEMA evaluation TO {READER}",
    6: f"GRANT SELECT ON ALL TABLES IN SCHEMA evaluation TO {READER}",
    7: f"ALTER DEFAULT PRIVILEGES IN SCHEMA evaluation GRANT SELECT ON TABLES TO {READER}",
    8: "COMMIT",
}
ALTER_ROLE_RE = re.compile(rf"ALTER\s+ROLE\s+{READER}\s+WITH\s+LOGIN\s+PASSWORD\s+(?P<literal>'.*')", re.DOTALL)


def password_of(script: str) -> str:
    """Contraseña que el script fija: el literal del `ALTER ROLE`, desescapado con el lector de esta prueba."""
    statement = split_statements(script)[3]
    match = ALTER_ROLE_RE.fullmatch(statement)
    assert match is not None, statement[:80]
    return unescape_literal(match.group("literal"))


def fragments(secret: str, size: int = 4) -> list[str]:
    """Todas las ventanas de `size` caracteres de `secret`: un trozo de la contraseña que sobreviva es una fuga."""
    return [secret[start:start + size] for start in range(len(secret) - size + 1)]


# --- Dobles de `subprocess.run` -----------------------------------------------------------------------------------


def fake_run(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"", effect: BaseException | None = None):
    """Doble de `subprocess.run` que imita su semántica: con `check=True` lanza `CalledProcessError` si hay error.

    Registra las llamadas en `.calls` como `(args, kwargs)`. Si `effect` es una excepción, la lanza (fallo al ejecutar).
    """
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


def write_json(path: Path, document) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


class TmpCase(unittest.TestCase):
    """Base con un directorio temporal resuelto (en Windows el temporal puede traer nombres cortos 8.3)."""

    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name).resolve()

    def manifest(self, run_ids=("JUP-071-demo-1",), name: str = "m.json") -> Path:
        """Manifiesto local con un informe `rows-v1` por identificador (2 resultados cada uno)."""
        entries = []
        for run_id in run_ids:
            document = copy.deepcopy(ROWS_DOCUMENT)
            document["run"]["run_id"] = run_id
            report = write_json(self.tmp / f"{run_id}.json", document)
            entries.append({"path": str(report), "format": "rows-v1", "milestone": False})
        return write_json(self.tmp / name, {"manifest_version": 1, "runs": entries})

    def dataset(self, run_ids=("JUP-071-demo-1",)) -> dict:
        return tool.build_dataset([self.manifest(run_ids)], root=self.tmp)


# --- Constantes ------------------------------------------------------------------------------------------------


class ConstantsTest(unittest.TestCase):
    def test_constantes_del_contrato(self) -> None:
        self.assertEqual(tool.READER_ROLE, READER)
        self.assertEqual(tool.PASSWORD_ENV, PASSWORD_ENV)
        self.assertEqual(tool.LOAD_TIMEOUT, 120)
        self.assertIs(type(tool.LOAD_TIMEOUT), int)

    def test_comando_por_defecto_y_opciones_de_psql_son_tuplas_inmutables(self) -> None:
        # Tuplas, no listas: un llamador no puede alterar el comando por defecto de todo el proceso.
        self.assertIs(type(tool.DEFAULT_PSQL_COMMAND), tuple)
        self.assertEqual(list(tool.DEFAULT_PSQL_COMMAND), EXPECTED_DEFAULT_COMMAND)
        self.assertIs(type(tool.PSQL_FLAGS), tuple)
        self.assertEqual(list(tool.PSQL_FLAGS), EXPECTED_FLAGS)

    def test_load_error_es_un_value_error_propio(self) -> None:
        # Hereda de ValueError como `AdapterError`, `ManifestError` y `SqlError`: los errores de datos y de carga se tratan igual.
        self.assertTrue(issubclass(tool.LoadError, ValueError))
        self.assertIsNot(tool.LoadError, ValueError)
        for other in (tool.AdapterError, tool.ManifestError, tool.SqlError):
            self.assertFalse(issubclass(tool.LoadError, other), other)


# --- build_role_sql: estructura --------------------------------------------------------------------------------


class BuildRoleSqlStructureTest(unittest.TestCase):
    def script(self, password: str = "plana-sin-nada") -> str:
        return tool.build_role_sql(password)

    def test_son_nueve_sentencias_en_el_orden_del_contrato(self) -> None:
        statements = split_statements(self.script())
        self.assertEqual(len(statements), 9, statements)
        for position, expected in FIXED_STATEMENTS.items():
            self.assertEqual(squash(statements[position]), expected, position)
        # Las dos que se comprueban aparte están donde toca: el `DO` antes del `ALTER ROLE`, y este antes de los permisos.
        self.assertTrue(squash(statements[2]).startswith("DO $$"), statements[2][:40])
        self.assertTrue(squash(statements[3]).startswith(f"ALTER ROLE {READER} WITH LOGIN PASSWORD '"), statements[3][:70])

    def test_es_una_transaccion_con_el_ajuste_de_cadenas_primero(self) -> None:
        script = self.script()
        self.assertIs(type(script), str)
        self.assertTrue(script.startswith("BEGIN;"), script[:20])
        self.assertTrue(script.rstrip().endswith("COMMIT;"), script[-20:])
        statements = split_statements(script)
        # `standard_conforming_strings` ANTES de cualquier literal: la contraseña se escapa suponiendo que está activo.
        self.assertEqual(squash(statements[1]), "SET LOCAL standard_conforming_strings = on")
        self.assertEqual(sum(1 for text in statements if squash(text).upper().startswith("COMMIT")), 1)
        self.assertEqual(sum(1 for text in statements if squash(text).upper().startswith("BEGIN")), 1)

    def test_el_rol_se_crea_con_un_bloque_do_que_mira_pg_roles_y_no_con_if_not_exists(self) -> None:
        script = self.script()
        block = squash(split_statements(script)[2])
        self.assertTrue(block.startswith("DO $$") and block.endswith("$$"), block)
        # Mira el catálogo por el nombre exacto del rol y solo entonces lo crea, con `LOGIN` y nada más.
        self.assertIn("pg_roles", block)
        self.assertRegex(block, rf"rolname\s*=\s*'{READER}'")
        self.assertRegex(block, rf"CREATE ROLE {READER} LOGIN\s*;")
        # `CREATE ROLE IF NOT EXISTS` no existe en PostgreSQL: el script no podría ejecutarse.
        self.assertIsNone(re.search(r"CREATE\s+ROLE\s+IF\s+NOT\s+EXISTS", script, re.IGNORECASE))
        self.assertEqual(len(re.findall(r"CREATE\s+ROLE", script, re.IGNORECASE)), 1)
        # El bloque no lleva la contraseña ni atributos de privilegio.
        for forbidden in ("PASSWORD", "SUPERUSER", "CREATEDB", "CREATEROLE", "REPLICATION", "BYPASSRLS"):
            self.assertNotIn(forbidden, block.upper(), forbidden)

    def test_el_alter_role_va_siempre_y_despues_del_bloque_do(self) -> None:
        # Se ejecuta aunque el rol ya existiera: es lo que rota la contraseña en una segunda carga.
        statements = split_statements(self.script())
        match = ALTER_ROLE_RE.fullmatch(statements[3])
        self.assertIsNotNone(match, statements[3])
        self.assertEqual(unescape_literal(match.group("literal")), "plana-sin-nada")

    def test_no_concede_nada_mas_que_lectura_del_esquema_de_evaluacion(self) -> None:
        script = self.script()
        upper = script.upper()
        # La igualdad exacta de las sentencias ya lo impone; estas líneas dan el motivo cuando un permiso sobra.
        for forbidden in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER", "EXECUTE", "SUPERUSER",
                          "CREATEDB", "CREATEROLE", "REPLICATION", "BYPASSRLS", "GRANT OPTION", "PRIVILEGES ON",
                          "ALL PRIVILEGES", "TO PUBLIC", "PG_READ", "PG_WRITE", "PG_MONITOR", "DROP ", "ADMIN OPTION"):
            self.assertNotIn(forbidden, upper, forbidden)
        # Solo hay dos `GRANT` de privilegio sobre objetos y uno de conexión; ninguno toca otro esquema.
        self.assertEqual(len(re.findall(r"\bGRANT\b", script)), 4)
        self.assertEqual(len(re.findall(r"\bIN SCHEMA\b", script)), 2)
        self.assertNotIn("public", script.lower().replace("plana-sin-nada", ""))
        self.assertNotRegex(script, r"(?i)\bCREATE\b(?!\s+ROLE)")

    def test_cada_sentencia_nombra_exactamente_el_rol_del_contrato(self) -> None:
        statements = [squash(text) for text in split_statements(self.script())]
        for position in (3, 4, 5, 6, 7):
            self.assertIn(READER, statements[position], position)
            # Ni otro rol parecido ni el rol del superusuario.
            self.assertEqual(statements[position].count(READER), 1, position)
            self.assertNotIn("postgres", statements[position])

    def test_es_determinista_puro_y_no_depende_del_estado(self) -> None:
        first = tool.build_role_sql(PW)
        second = tool.build_role_sql(PW)
        self.assertEqual(first, second)
        self.assertNotEqual(tool.build_role_sql(PW), tool.build_role_sql(PW + "x"))
        # Distinta contraseña, mismas sentencias fijas: lo único que cambia es el literal del `ALTER ROLE`.
        statements_a = split_statements(first)
        statements_b = split_statements(tool.build_role_sql("otra-distinta"))
        self.assertEqual(statements_a[:3] + statements_a[4:], statements_b[:3] + statements_b[4:])
        self.assertNotEqual(statements_a[3], statements_b[3])

    def test_no_lee_el_entorno_ni_la_variable_de_la_contrasena(self) -> None:
        # La contraseña es el ARGUMENTO: leerla del entorno la haría depender de un estado global.
        with mock.patch.dict(os.environ, {PASSWORD_ENV: "del-entorno-no"}):
            script = tool.build_role_sql(PW)
        self.assertEqual(password_of(script), PW)
        self.assertNotIn("del-entorno-no", script)

    def test_no_comparte_ninguna_sentencia_con_el_script_de_datos(self) -> None:
        # Hallazgo del QA de 3.1: el script de `build_sql` no puede llevar permisos ni contraseñas; van en el del rol.
        data = tool.build_sql({"dataset_version": 1, "runs": []})
        role = tool.build_role_sql(PW)
        self.assertNotIn(READER, data)
        for forbidden in ("CREATE ROLE", "ALTER ROLE", "GRANT", "PASSWORD"):
            self.assertNotIn(forbidden, data.upper())
        self.assertNotIn("CREATE SCHEMA", role)
        self.assertNotIn("TRUNCATE", role)


# --- build_role_sql: contraseñas hostiles y validación ------------------------------------------------------------


HOSTILE_PASSWORDS = [
    "it's", "a'b'c", "'", "''", "'" * 100, '"', 'pa"ss', "\\", "a\\'b", "C:\\dir\\", "\\" * 200, "$$", "x$$y",
    "$a$b$", "$tag$ x $tag$", "';DROP ROLE x;--", "'; DROP ROLE x; --", "'); ALTER ROLE postgres PASSWORD 'hack'; --",
    "contraseña-ñ-日本-🔑", "ñ" * 200, "a" * 200, " con espacios  ", "E'\\x41'", "%s", "{0}", "${HOME}", "`id`", "--",
    "/*", "*/", "a;b", "a--b", "'||(SELECT 1)||'", "\\'; SELECT pg_sleep(9); --",
]


class BuildRoleSqlPasswordTest(unittest.TestCase):
    def test_el_literal_se_desescapa_a_la_contrasena_exacta_y_no_aparece_ninguna_otra_sentencia(self) -> None:
        baseline = split_statements(tool.build_role_sql("plana-sin-nada"))
        for password in HOSTILE_PASSWORDS:
            with self.subTest(password=password[:30]):
                script = tool.build_role_sql(password)
                statements = split_statements(script)
                # Un `'` sin duplicar abriría una sentencia nueva: habría más de nueve.
                self.assertEqual(len(statements), 9, [text[:60] for text in statements])
                self.assertEqual(password_of(script), password)
                # El resto del script es idéntico al de una contraseña inofensiva.
                self.assertEqual(statements[:3] + statements[4:], baseline[:3] + baseline[4:])

    def test_la_contrasena_aparece_una_sola_vez_y_solo_dentro_del_literal(self) -> None:
        for password in HOSTILE_PASSWORDS:
            if len(password) < 4:
                continue
            with self.subTest(password=password[:30]):
                statements = split_statements(tool.build_role_sql(password))
                outside = "\n".join(text for position, text in enumerate(statements) if position != 3)
                escaped = password.replace("'", "''")
                self.assertNotIn(password, outside)
                self.assertNotIn(escaped, outside)
                self.assertEqual(statements[3].count(escaped), 1, statements[3][:80])

    def test_contrasena_ordinaria_va_en_el_literal_tal_cual(self) -> None:
        script = tool.build_role_sql(PW)
        self.assertEqual(script.count(PW), 1)
        self.assertIn(f"PASSWORD '{PW}'", script)

    def test_la_comilla_se_duplica_y_la_barra_invertida_no_se_toca(self) -> None:
        # Con `standard_conforming_strings = on` la barra es un carácter normal: duplicarla cambiaría la contraseña.
        self.assertIn("PASSWORD 'it''s'", tool.build_role_sql("it's"))
        self.assertIn("PASSWORD 'a\\b'", tool.build_role_sql("a\\b"))
        self.assertNotIn("\\\\", tool.build_role_sql("a\\b"))
        self.assertNotIn("E'", tool.build_role_sql("a\\b"))

    def test_la_contrasena_unicode_es_ascii_o_utf8_sin_transformar(self) -> None:
        # El literal conserva los caracteres: la codificación a bytes UTF-8 es cosa de `run_load`.
        script = tool.build_role_sql("contraseña-ñ-日本")
        self.assertIn("'contraseña-ñ-日本'", script)

    def test_longitudes_limite_validas(self) -> None:
        for password in ("a", "a" * 200, "ñ" * 200, "日" * 200):
            with self.subTest(length=len(password)):
                self.assertEqual(password_of(tool.build_role_sql(password)), password)


class BuildRoleSqlValidationTest(unittest.TestCase):
    LEAK = "ZQXLEAK"

    def assert_rejected(self, value, secret: str | None = None) -> None:
        with self.assertRaises(tool.LoadError) as caught:
            tool.build_role_sql(value)
        message = str(caught.exception)
        self.assertTrue(message.startswith("password: "), message)
        self.assertEqual(message.count("\n"), 0, message)
        # El mensaje dice QUÉ regla incumple, nunca el valor: ni en el texto ni en `repr` ni en los argumentos.
        if secret is not None:
            for text in (message, repr(caught.exception), repr(caught.exception.args)):
                self.assertNotIn(secret, text)

    def test_vacia_y_tipos_que_no_son_cadena(self) -> None:
        self.assert_rejected("")
        for value in (None, 123456789, 1.5, True, b"ZQXLEAK", bytearray(b"ZQXLEAK"), ["ZQXLEAK"], ("ZQXLEAK",),
                      {"ZQXLEAK": 1}, object()):
            with self.subTest(value=type(value).__name__):
                self.assert_rejected(value, "ZQXLEAK" if isinstance(value, (bytes, bytearray, list, tuple, dict)) else "123456789")

    def test_caracteres_de_control(self) -> None:
        for name, char in (("salto de línea", "\n"), ("retorno de carro", "\r"), ("NUL", "\x00"), ("tabulador", "\t"),
                           ("escape", "\x1b"), ("DEL", "\x7f"), ("campana", "\x07")):
            for position, value in (("medio", f"{self.LEAK}{char}resto"), ("inicio", f"{char}{self.LEAK}"),
                                    ("final", f"{self.LEAK}{char}")):
                with self.subTest(char=name, position=position):
                    self.assert_rejected(value, self.LEAK)

    def test_longitud_maxima_de_200_caracteres(self) -> None:
        self.assert_rejected(self.LEAK + "Q" * 194, self.LEAK)
        self.assert_rejected("Q" * 201, "QQQQQ")
        # Se cuenta en caracteres y no en bytes: 201 `ñ` son 402 bytes, 200 `ñ` ya se aceptaron arriba.
        self.assert_rejected("ñ" * 201, "ññññ")
        self.assert_rejected("a" * 5000, "aaaaa")

    def test_cadena_que_no_se_puede_codificar_en_utf8(self) -> None:
        # `os.environ` en Linux devuelve bytes inválidos como sustitutos sueltos: sin esta barrera `run_load` lanzaría
        # un `UnicodeEncodeError` crudo (una traza) en lugar de un error accionable.
        self.assert_rejected("abc\udcff" + self.LEAK, self.LEAK)
        self.assert_rejected("\ud800", None)

    def test_una_subclase_de_str_no_se_cuela(self) -> None:
        class Hostil(str):
            def __repr__(self) -> str:
                return "'; DROP ROLE x; --"

        # Sea cual sea la excepción (la de la contraseña o la de `sql_literal`), es un `ValueError`: nunca un script.
        with self.assertRaises(ValueError):
            tool.build_role_sql(Hostil("clave"))

    def test_los_rechazos_no_producen_texto_parcial_ni_cambian_el_estado(self) -> None:
        with self.assertRaises(tool.LoadError):
            tool.build_role_sql("mala\ncontraseña")
        self.assertEqual(password_of(tool.build_role_sql("buena")), "buena")


# --- load_command ------------------------------------------------------------------------------------------------


class LoadCommandTest(unittest.TestCase):
    def test_por_defecto_es_docker_compose_exec_mas_las_opciones(self) -> None:
        command = tool.load_command()
        self.assertIs(type(command), list)
        self.assertEqual(command, EXPECTED_DEFAULT_COMMAND + EXPECTED_FLAGS)
        self.assertTrue(all(type(item) is str for item in command))

    def test_none_equivale_a_no_pasar_nada(self) -> None:
        self.assertEqual(tool.load_command(None), tool.load_command())
        self.assertEqual(tool.load_command(psql_command=None), EXPECTED_DEFAULT_COMMAND + EXPECTED_FLAGS)

    def test_un_comando_propio_se_conserva_entero_y_seguido_de_las_opciones(self) -> None:
        custom = ["docker", "exec", "-i", "mi-contenedor", "psql", "-U", "postgres", "-d", "embeddings"]
        self.assertEqual(tool.load_command(custom), custom + EXPECTED_FLAGS)
        # También una tupla: la forma de `DEFAULT_PSQL_COMMAND`.
        self.assertEqual(tool.load_command(tuple(custom)), custom + EXPECTED_FLAGS)
        # No sustituye el comando por el de por defecto ni añade el de por defecto.
        self.assertNotIn("compose", tool.load_command(custom))

    def test_devuelve_una_lista_nueva_y_no_muta_la_entrada(self) -> None:
        custom = ["psql", "-U", "x"]
        snapshot = list(custom)
        result = tool.load_command(custom)
        self.assertIsNot(result, custom)
        self.assertEqual(custom, snapshot)
        result.append("intruso")
        result.clear()
        # Ni el resultado ni la entrada comparten estado con el siguiente cálculo ni con las constantes.
        self.assertEqual(tool.load_command(custom), snapshot + EXPECTED_FLAGS)
        self.assertEqual(tool.load_command(), EXPECTED_DEFAULT_COMMAND + EXPECTED_FLAGS)
        self.assertEqual(list(tool.DEFAULT_PSQL_COMMAND), EXPECTED_DEFAULT_COMMAND)
        self.assertEqual(list(tool.PSQL_FLAGS), EXPECTED_FLAGS)

    def test_las_opciones_obligan_a_parar_en_el_primer_error_y_no_leen_psqlrc(self) -> None:
        # `ON_ERROR_STOP=1`: sin él `psql` seguiría tras un fallo y el rol se crearía con datos a medias.
        # `-X`: un `~/.psqlrc` del usuario no puede alterar la sesión. `-q`: sin ruido en la salida.
        command = tool.load_command(["psql"])
        self.assertEqual(command[1:], ["-v", "ON_ERROR_STOP=1", "-X", "-q"])


# --- run_load: llamada a subprocess ---------------------------------------------------------------------------------


class RunLoadCallTest(TmpCase):
    def run_load(self, *, dataset=None, password=PW, **kwargs):
        double, patch = patched_run()
        with patch:
            summary = tool.run_load(self.dataset() if dataset is None else dataset, password, **kwargs)
        self.assertEqual(len(double.calls), 1, "debe lanzar `psql` una sola vez")
        args, call_kwargs = double.calls[0]
        return summary, args, call_kwargs

    def test_argumentos_por_defecto_son_una_lista_sin_shell(self) -> None:
        _, args, kwargs = self.run_load()
        self.assertIs(type(args), list)
        self.assertEqual(args, EXPECTED_DEFAULT_COMMAND + EXPECTED_FLAGS)
        self.assertTrue(all(type(item) is str for item in args))
        # Sin shell: la línea de comandos no pasa por un intérprete que pueda expandir o ejecutar nada.
        self.assertIs(kwargs.get("shell", False), False)

    def test_comando_propio_en_lista_o_tupla(self) -> None:
        custom = ["docker", "exec", "-i", "mi-contenedor", "psql", "-U", "postgres", "-d", "embeddings"]
        for given in (custom, tuple(custom)):
            with self.subTest(type=type(given).__name__):
                _, args, _ = self.run_load(psql_command=given)
                self.assertEqual(args, custom + EXPECTED_FLAGS)

    def test_opciones_de_la_llamada(self) -> None:
        _, _, kwargs = self.run_load()
        self.assertIs(kwargs.get("capture_output"), True)
        self.assertEqual(kwargs.get("timeout"), 120)
        # `cwd` es la raíz del repositorio: `docker compose` busca ahí el `docker-compose.yml` del proyecto.
        self.assertIn("cwd", kwargs)
        self.assertEqual(Path(kwargs["cwd"]), tool.ROOT)
        # Sin modo texto en ninguna de sus formas: la entrada y la salida son bytes, la codificación es explícita.
        for forbidden in ("text", "universal_newlines", "encoding", "errors"):
            self.assertNotIn(forbidden, kwargs, forbidden)
        self.assertLessEqual(set(kwargs), {"input", "capture_output", "timeout", "cwd", "env", "check"})
        self.assertTrue({"input", "capture_output", "timeout", "cwd", "env"} <= set(kwargs))

    def test_el_timeout_se_puede_cambiar(self) -> None:
        _, _, kwargs = self.run_load(timeout=7)
        self.assertEqual(kwargs["timeout"], 7)
        _, _, kwargs = self.run_load(psql_command=["psql"], timeout=0.5)
        self.assertEqual(kwargs["timeout"], 0.5)

    def test_la_entrada_son_bytes_utf8_con_los_datos_antes_que_el_rol(self) -> None:
        dataset = self.dataset(("JUP-071-demo-1", "JUP-071-demo-2"))
        _, _, kwargs = self.run_load(dataset=dataset, password=PW_HOSTILE)
        payload = kwargs["input"]
        self.assertIs(type(payload), bytes)
        text = payload.decode("utf-8")
        expected = tool.build_sql(dataset) + "\n" + tool.build_role_sql(PW_HOSTILE)
        self.assertEqual(text, expected)
        self.assertEqual(payload, expected.encode("utf-8"))
        # Los datos van PRIMERO: el rol concede permisos sobre un esquema que el script de datos acaba de crear.
        self.assertLess(text.index("CREATE SCHEMA IF NOT EXISTS evaluation"), text.index("CREATE ROLE"))
        self.assertLess(text.index("TRUNCATE"), text.index("ALTER ROLE"))
        self.assertLess(text.rindex("COMMIT;", 0, text.index("DO $$")), text.index("DO $$"))
        self.assertEqual(text.count("BEGIN;"), 2)
        self.assertEqual(text.count("COMMIT;"), 2)
        # Dos transacciones separadas por una línea en blanco: el `COMMIT` de los datos queda firme aunque el rol falle.
        self.assertIn("COMMIT;\n\nBEGIN;", text)

    def test_la_contrasena_unicode_viaja_en_utf8_y_no_en_otra_codificacion(self) -> None:
        _, _, kwargs = self.run_load(password="ñ日本🔑-ü")
        self.assertIn("ñ日本🔑-ü".encode("utf-8"), kwargs["input"])
        self.assertNotIn("ñ".encode("latin-1"), kwargs["input"].replace("ñ".encode("utf-8"), b""))

    def test_la_contrasena_solo_aparece_en_la_entrada(self) -> None:
        with mock.patch.dict(os.environ, {PASSWORD_ENV: PW, "OTRA_VARIABLE_DE_PRUEBA": "valor"}):
            _, args, kwargs = self.run_load()
        self.assertEqual(kwargs["input"].count(PW.encode("utf-8")), 1)
        self.assertNotIn(PW, repr(args))
        for name, value in kwargs.items():
            if name != "input":
                self.assertNotIn(PW, repr(value), name)
        # Compara por valor: nada del entorno que se pasa contiene la contraseña, ni en una clave ni en un valor.
        for key, value in kwargs["env"].items():
            self.assertNotIn(PW, key)
            self.assertNotIn(PW, value, key)
        self.assertNotIn(PASSWORD_ENV, kwargs["env"])

    def test_la_contrasena_no_va_en_el_entorno_aunque_este_en_el_del_proceso(self) -> None:
        # Es el caso real: `main` la lee de `os.environ`, así que sigue ahí y hay que quitarla al lanzar `psql`.
        with mock.patch.dict(os.environ, {PASSWORD_ENV: PW_HOSTILE}):
            _, _, kwargs = self.run_load(password=PW_HOSTILE)
            self.assertNotIn(PASSWORD_ENV, kwargs["env"])
            self.assertNotIn(PW_HOSTILE, "\n".join(kwargs["env"].values()))
            # Pero el entorno del propio proceso no se toca: quitarla de ahí rompería una segunda llamada.
            self.assertEqual(os.environ[PASSWORD_ENV], PW_HOSTILE)

    def test_el_entorno_hereda_el_del_proceso_y_fuerza_utf8(self) -> None:
        with mock.patch.dict(os.environ, {"VARIABLE_DE_PRUEBA_3_3": "se-hereda", "PGCLIENTENCODING": "LATIN1"}):
            _, _, kwargs = self.run_load()
        env = kwargs["env"]
        self.assertEqual(env["VARIABLE_DE_PRUEBA_3_3"], "se-hereda")
        # Sin `PGCLIENTENCODING=UTF8` el cliente usaría la página de códigos del sistema y una contraseña con tildes llegaría corrupta.
        self.assertEqual(env["PGCLIENTENCODING"], "UTF8")
        for key in ("PATH", "SYSTEMROOT") if os.name == "nt" else ("PATH",):
            if key in os.environ:
                self.assertEqual(env[key], os.environ[key], key)

    def test_no_muta_el_conjunto_de_datos(self) -> None:
        dataset = self.dataset(("JUP-071-demo-1", "JUP-071-demo-2"))
        snapshot = copy.deepcopy(dataset)
        self.run_load(dataset=dataset)
        self.assertEqual(dataset, snapshot)

    def test_valida_antes_de_lanzar_nada(self) -> None:
        # Un conjunto inválido o una contraseña inválida no llegan a `psql`: no se envía ni un byte.
        double, patch = patched_run()
        with patch:
            with self.assertRaises(tool.AdapterError):
                tool.run_load({"dataset_version": 2, "runs": []}, PW)
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(self.dataset(), "mala\ncontraseña")
            with self.assertRaises(tool.LoadError):
                tool.run_load(self.dataset(), "")
        self.assertTrue(str(caught.exception).startswith("password: "))
        self.assertEqual(double.calls, [])

    def test_usa_el_build_sql_y_el_build_role_sql_de_la_herramienta(self) -> None:
        # Cableado: lo que se envía es lo que devuelven las dos funciones, buscadas por nombre en cada llamada.
        with mock.patch.object(tool, "build_sql", return_value="-- datos\n"), \
                mock.patch.object(tool, "build_role_sql", return_value="-- rol\n") as role_mock:
            _, _, kwargs = self.run_load(dataset={"dataset_version": 1, "runs": []})
        self.assertEqual(kwargs["input"], b"-- datos\n\n-- rol\n")
        role_mock.assert_called_once_with(PW)


# --- run_load: resultado y fallos ---------------------------------------------------------------------------------


class RunLoadSummaryTest(TmpCase):
    def summary(self, dataset, **kwargs) -> str:
        double, patch = patched_run(**kwargs)
        with patch:
            return tool.run_load(dataset, PW)

    def test_resumen_con_ejecuciones_y_resultados(self) -> None:
        # Las cuentas se leen del conjunto (2 ejecuciones, 4 resultados), no de lo que `psql` diga.
        text = self.summary(self.dataset(("JUP-071-demo-1", "JUP-071-demo-2")))
        self.assertEqual(text, "2 ejecuciones y 4 resultados cargados")
        self.assertIs(type(text), str)

    def test_resumen_con_una_ejecucion_no_cambia_el_plural(self) -> None:
        self.assertEqual(self.summary(self.dataset()), "1 ejecuciones y 2 resultados cargados")

    def test_resumen_con_tres_ejecuciones(self) -> None:
        text = self.summary(self.dataset(("JUP-071-a", "JUP-071-b", "JUP-071-c")))
        self.assertEqual(text, "3 ejecuciones y 6 resultados cargados")

    def test_resumen_de_un_conjunto_vacio(self) -> None:
        # Un conjunto vacío es válido: se crea el esquema y el rol igualmente.
        self.assertEqual(self.summary({"dataset_version": 1, "runs": []}), "0 ejecuciones y 0 resultados cargados")

    def test_resumen_con_una_ejecucion_sin_filas(self) -> None:
        dataset = self.dataset()
        dataset["runs"][0]["results"] = []
        self.assertEqual(self.summary(dataset), "1 ejecuciones y 0 resultados cargados")

    def test_la_salida_de_psql_no_entra_en_el_resumen(self) -> None:
        text = self.summary(self.dataset(), stdout=b"COMMIT\nINSERT 0 999\n", stderr=b"NOTICE:  schema exists, skipping\n")
        self.assertEqual(text, "1 ejecuciones y 2 resultados cargados")

    def test_los_avisos_en_stderr_con_codigo_cero_no_son_un_fallo(self) -> None:
        # `CREATE SCHEMA IF NOT EXISTS` avisa por `stderr` en la segunda carga: eso es un éxito.
        text = self.summary(self.dataset(), returncode=0, stderr=b"NOTICE:  relation already exists, skipping\n")
        self.assertEqual(text, "1 ejecuciones y 2 resultados cargados")


class RunLoadFailureTest(TmpCase):
    def expect_failure(self, *, password: str = PW, timeout=None, psql_command=None, **kwargs) -> str:
        double, patch = patched_run(**kwargs)
        call = {} if timeout is None else {"timeout": timeout}
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(self.dataset(), password, psql_command=psql_command, **call)
        message = str(caught.exception)
        self.assertTrue(message.startswith("load: "), message)
        self.assertEqual(len(double.calls), 1)
        # Una sola línea y sin citar la contraseña, el conjunto de datos ni nada de lo enviado por `stdin`.
        self.assertNotIn("\n", message)
        self.assertNotIn("\r", message)
        self.assertNotIn(password, message)
        for sent in ("JUP-071-demo-1", "CREATE ROLE", "INSERT INTO", "BEGIN;"):
            self.assertNotIn(sent, message)
        return message

    def test_codigo_distinto_de_cero_dice_el_codigo_y_la_ultima_linea(self) -> None:
        stderr = b"psql:<stdin>:12: ERROR:  primera linea\nLINE 1: SELECT mal\n\nERROR:  la relacion no existe\n\n"
        message = self.expect_failure(returncode=7, stderr=stderr)
        self.assertIn("psql terminó con código 7", message)
        self.assertIn("ERROR:  la relacion no existe", message)
        # Solo la ÚLTIMA línea no vacía: las anteriores no acompañan al mensaje.
        self.assertNotIn("primera linea", message)
        self.assertNotIn("LINE 1", message)

    def test_cada_codigo_se_cita_tal_cual(self) -> None:
        for code in (1, 2, 3, 127, 255):
            with self.subTest(code=code):
                self.assertIn(f"psql terminó con código {code}", self.expect_failure(returncode=code, stderr=b"ERROR:  x\n"))

    def test_los_saltos_de_linea_de_windows_no_dejan_retornos_de_carro(self) -> None:
        message = self.expect_failure(returncode=3, stderr=b"primera\r\nERROR:  fallo al insertar\r\n\r\n")
        self.assertIn("ERROR:  fallo al insertar", message)
        self.assertNotIn("primera", message)

    def test_stderr_vacio_o_ausente_no_rompe_y_sigue_dando_el_codigo(self) -> None:
        for stderr in (b"", b"\n", b"\n\n\n", b"\r\n"):
            with self.subTest(stderr=stderr):
                self.assertIn("psql terminó con código 9", self.expect_failure(returncode=9, stderr=stderr))

    def test_stderr_con_bytes_que_no_son_utf8_no_lanza(self) -> None:
        message = self.expect_failure(returncode=3, stderr=b"previa\n\xff\xfe error \xc3 final\n")
        self.assertIn("error", message)
        self.assertIn("final", message)
        # `errors="replace"`: el byte inválido sale como el carácter de sustitución y no como una excepción.
        self.assertIn("\ufffd", message)

    def test_el_ejecutable_no_se_encuentra(self) -> None:
        message = self.expect_failure(effect=FileNotFoundError(2, "El sistema no puede encontrar el archivo especificado"))
        self.assertIn("no se encuentra", message)
        self.assertIn("docker", message)
        custom = self.expect_failure(effect=FileNotFoundError(2, "no such file"), psql_command=["ejecutable-inexistente-xyz", "-U", "x"])
        self.assertIn("no se encuentra", custom)
        self.assertIn("ejecutable-inexistente-xyz", custom)

    def test_sin_permiso_para_ejecutarlo(self) -> None:
        message = self.expect_failure(effect=PermissionError(13, "Permission denied"))
        self.assertTrue(message.startswith("load: "))

    def test_error_de_sistema_generico(self) -> None:
        self.expect_failure(effect=OSError(5, "Input/output error"))
        # Una tubería rota al escribir la entrada es un `OSError` (`BrokenPipeError`): también un `LoadError`.
        self.expect_failure(effect=BrokenPipeError(32, "Broken pipe"))

    def test_timeout(self) -> None:
        message = self.expect_failure(effect=subprocess.TimeoutExpired(["docker"], 120), timeout=120)
        self.assertIn("timeout", message.lower())
        self.assertIn("120", message)
        # El plazo que se cita es el que se pidió, no una constante.
        self.assertIn("5", self.expect_failure(effect=subprocess.TimeoutExpired(["docker"], 5), timeout=5))

    def test_timeout_con_salida_parcial_que_contiene_la_contrasena(self) -> None:
        expired = subprocess.TimeoutExpired(["docker"], 120, output=b"", stderr=f"ERROR: {PW}".encode())
        message = self.expect_failure(effect=expired)
        self.assertIn("timeout", message.lower())

    def test_un_oserror_cuyo_mensaje_contiene_la_contrasena_se_redacta(self) -> None:
        # Redacción en TODA ruta de error y no solo en la de `stderr`.
        message = self.expect_failure(effect=OSError(5, f"fallo con {PW} dentro"))
        self.assertNotIn(PW, message)
        self.assertEqual(self.expect_failure(effect=OSError(f"fallo con {PW} dentro")).count(PW), 0)

    def test_un_fallo_no_conserva_la_cadena_de_excepciones_con_la_contrasena(self) -> None:
        double, patch = patched_run(effect=OSError(5, f"fallo con {PW} dentro"))
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(self.dataset(), PW)
        # Ligado como causa mostraría el mensaje original en la traza; como contexto solo vale si queda suprimido.
        error = caught.exception
        self.assertTrue(error.__cause__ is None or PW not in str(error.__cause__))
        self.assertTrue(error.__context__ is None or error.__suppress_context__ or PW not in str(error.__context__))

    def test_un_error_de_programacion_no_se_disfraza_de_error_de_carga(self) -> None:
        # Solo se capturan los fallos de ejecución: un `RuntimeError` inesperado debe verse tal cual.
        double, patch = patched_run(effect=RuntimeError("bug"))
        with patch:
            with self.assertRaises(RuntimeError):
                tool.run_load(self.dataset(), PW)

    def test_check_true_de_la_implementacion_tambien_queda_cubierto(self) -> None:
        # El doble lanza `CalledProcessError` si la implementación pide `check=True`: debe salir como `LoadError`.
        message = self.expect_failure(returncode=3, stderr=b"ERROR:  duplicado\n")
        self.assertIn("código 3", message)
        self.assertIn("duplicado", message)


class RunLoadRedactionTest(TmpCase):
    """`psql` repite en `stderr` la sentencia que falla, y la del rol lleva la contraseña: no puede salir en el error."""

    def message(self, stderr: bytes, password: str = PW, code: int = 3) -> str:
        double, patch = patched_run(returncode=code, stderr=stderr)
        with patch:
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(self.dataset(), password)
        return str(caught.exception)

    def assert_no_fragments(self, message: str, secret: str) -> None:
        for piece in fragments(secret):
            self.assertNotIn(piece, message, piece)

    def test_la_sentencia_repetida_sale_con_la_contrasena_tapada(self) -> None:
        stderr = (f"psql:<stdin>:40: ERROR:  syntax error\nLINE 1: ALTER ROLE {READER} WITH LOGIN PASSWORD '{PW}'\n").encode()
        message = self.message(stderr)
        self.assertNotIn(PW, message)
        self.assertIn("***", message)
        # Se sustituye el contenido y se conserva el contexto, comillas incluidas: el mensaje sigue siendo útil.
        self.assertIn(f"ALTER ROLE {READER} WITH LOGIN PASSWORD '***'", message)

    def test_la_contrasena_con_comilla_sale_tapada_en_su_forma_escapada_y_en_la_literal(self) -> None:
        secret = "Zq7'kP!w'V9"
        escaped = secret.replace("'", "''")
        for label, line in (("escapada", f"LINE 1: ... PASSWORD '{escaped}'"), ("literal", f"detalle: {secret} no vale")):
            with self.subTest(forma=label):
                message = self.message(f"previa\n{line}\n".encode(), secret)
                self.assertNotIn(secret, message)
                self.assertNotIn(escaped, message)
                self.assertNotIn("kP!w", message)
                self.assertIn("***", message)

    def test_las_dos_formas_en_la_misma_linea(self) -> None:
        secret = "a'b'c-Zq9"
        escaped = secret.replace("'", "''")
        message = self.message(f"x {escaped} y {secret} z {escaped}\n".encode(), secret)
        for text in (secret, escaped, "Zq9"):
            self.assertNotIn(text, message)
        self.assertEqual(message.count("***"), 3)

    def test_todas_las_apariciones_de_la_misma_linea(self) -> None:
        message = self.message(f"{PW} una {PW} dos {PW} tres\n".encode())
        self.assertNotIn(PW, message)
        self.assertEqual(message.count("***"), 3)
        self.assertIn("una", message)

    def test_solo_se_tapa_la_contrasena_y_no_el_resto_de_la_linea(self) -> None:
        message = self.message(f"ERROR: antes {PW} despues\n".encode())
        self.assertIn("ERROR: antes *** despues", message)

    def test_contrasena_con_unicode_en_utf8(self) -> None:
        secret = "contraseña-ñ-日本-🔑"
        message = self.message(f"fallo con {secret} dentro\n".encode("utf-8"), secret)
        self.assertNotIn(secret, message)
        self.assertNotIn("日本", message)
        self.assertIn("fallo con *** dentro", message)

    def test_los_caracteres_especiales_se_tapan_de_forma_literal_y_no_como_expresion_regular(self) -> None:
        secret = "a.c+(x"
        message = self.message(b"abc a.c+(x aXc\n", secret)
        self.assertNotIn(secret, message)
        # `a.c` como patrón casaría con `abc` y `aXc`; como texto, no.
        self.assertIn("abc", message)
        self.assertIn("aXc", message)
        message = self.message(b"antes \\1 despues\n", "\\1")
        self.assertIn("antes *** despues", message)

    def test_contrasena_de_un_solo_caracter(self) -> None:
        message = self.message(b"x Q y\n", "Q")
        self.assertEqual(message.split(": ", 2)[-1].count("Q"), 0)

    def test_la_contrasena_solo_en_lineas_anteriores_no_aparece(self) -> None:
        message = self.message(f"LINE 1: ... PASSWORD '{PW}'\nERROR:  fallo final\n".encode())
        self.assertNotIn(PW, message)
        self.assertIn("fallo final", message)

    def test_la_redaccion_es_anterior_al_truncado_por_la_izquierda(self) -> None:
        # La contraseña cruza el límite de 300: si se truncara antes, quedaría pegado el principio de la contraseña.
        message = self.message(("x" * 295 + PW + "\n").encode())
        self.assert_no_fragments(message, PW)
        self.assertIn("***", message)

    def test_la_redaccion_es_anterior_al_truncado_por_la_derecha(self) -> None:
        # Y si el truncado conservara el FINAL de la línea, quedaría el final de la contraseña.
        message = self.message((PW + "y" * 295 + "\n").encode())
        self.assert_no_fragments(message, PW)

    def test_la_redaccion_con_comillas_dobladas_es_anterior_al_truncado(self) -> None:
        secret = "Zq7'kP!w'V9&x"
        escaped = secret.replace("'", "''")
        message = self.message(("x" * 290 + escaped + "\n").encode(), secret)
        self.assertNotIn("kP!w", message)
        self.assertNotIn(escaped, message)

    def test_mensajes_largos_se_truncan_a_300_caracteres(self) -> None:
        message = self.message(("A" * 1000 + "\n").encode())
        self.assertNotIn("A" * 301, message)
        self.assertIn("A" * 100, message)
        # El mensaje entero es acotado: el prefijo fijo ocupa poco más de 40 caracteres.
        self.assertLessEqual(len(message), 300 + 80)

    def test_una_linea_de_exactamente_300_caracteres_no_se_recorta(self) -> None:
        line = "B" * 300
        message = self.message((line + "\n").encode())
        self.assertIn(line, message)

    def test_una_linea_de_301_caracteres_se_recorta(self) -> None:
        self.assertNotIn("B" * 301, self.message(("B" * 301 + "\n").encode()))

    def test_solo_cuenta_la_ultima_linea_para_el_limite(self) -> None:
        message = self.message(("C" * 1000 + "\nERROR:  corta\n").encode())
        self.assertIn("ERROR:  corta", message)
        self.assertNotIn("CCCC", message)

    def test_el_limite_se_mide_en_caracteres_y_no_en_bytes(self) -> None:
        # 300 `ñ` son 600 bytes: un recorte por bytes dejaría la mitad.
        line = "ñ" * 300
        self.assertIn(line, self.message((line + "\n").encode("utf-8")))


# --- main: subcomando load en proceso (con subprocess.run sustituido) ---------------------------------------------


class MainInProcessTest(TmpCase):
    def setUp(self) -> None:
        super().setUp()
        self.manifest_path = self.manifest()
        self.environment = self.enterContext(mock.patch.dict(os.environ, {PASSWORD_ENV: PW}))

    def argv(self, *extra) -> list[str]:
        return ["load", "--no-versioned", "--manifest", str(self.manifest_path), "--root", str(self.tmp), *extra]

    def call(self, argv, **double_kwargs):
        double, patch = patched_run(**double_kwargs)
        out, err = io.StringIO(), io.StringIO()
        with patch, redirect_stdout(out), redirect_stderr(err):
            try:
                code = tool.main(argv)
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue(), double

    # -- la contraseña manda antes que nada --

    def test_sin_la_variable_falla_con_su_nombre_y_no_ejecuta_nada(self) -> None:
        os.environ.pop(PASSWORD_ENV, None)
        # Un manifiesto que no existe y un `build_dataset` que falla si se llama: la variable se mira ANTES de leer nada.
        argv = ["load", "--no-versioned", "--manifest", str(self.tmp / "no-existe.json"), "--root", str(self.tmp)]
        with mock.patch.object(tool, "build_dataset", side_effect=AssertionError("no debe leerse ningún manifiesto")), \
                mock.patch.object(tool, "run_load", side_effect=AssertionError("no debe cargarse nada")):
            code, out, err, double = self.call(argv)
        self.assertEqual(code, 1)
        self.assertIs(type(code), int)
        self.assertEqual(out, "")
        self.assertEqual(err, MISSING_VARIABLE_ERROR)
        self.assertEqual(double.calls, [])

    def test_con_la_variable_vacia_es_lo_mismo_que_sin_ella(self) -> None:
        os.environ[PASSWORD_ENV] = ""
        code, out, err, double = self.call(self.argv())
        self.assertEqual((code, out, err), (1, "", MISSING_VARIABLE_ERROR))
        self.assertEqual(double.calls, [])

    def test_con_el_manifiesto_inexistente_y_sin_variable_gana_el_error_de_la_variable(self) -> None:
        os.environ.pop(PASSWORD_ENV, None)
        code, out, err, double = self.call(["load", "--manifest", str(self.tmp / "no-existe.json")])
        self.assertEqual((code, out, err), (1, "", MISSING_VARIABLE_ERROR))
        self.assertEqual(double.calls, [])

    def test_el_error_de_la_variable_nombra_la_variable_y_no_un_valor(self) -> None:
        os.environ.pop(PASSWORD_ENV, None)
        _, _, err, _ = self.call(self.argv())
        self.assertIn(PASSWORD_ENV, err)
        self.assertEqual(err.count("\n"), 1)

    def test_una_contrasena_invalida_se_rechaza_sin_citarla_ni_ejecutar_psql(self) -> None:
        for bad in ("Q" * 201 + "ZQXLEAK", "con\nsalto-ZQXLEAK"):
            with self.subTest(bad=bad[:12]):
                os.environ[PASSWORD_ENV] = bad
                code, out, err, double = self.call(self.argv())
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("error: password: "), err)
                self.assertNotIn("ZQXLEAK", err)
                self.assertNotIn("QQQQQ", err)
                self.assertEqual(double.calls, [])

    # -- éxito --

    def test_exito_imprime_solo_el_resumen_con_un_salto_de_linea(self) -> None:
        code, out, err, double = self.call(self.argv())
        self.assertEqual(code, 0)
        self.assertIs(type(code), int)
        self.assertEqual(out, "1 ejecuciones y 2 resultados cargados\n")
        self.assertEqual(err, "")
        self.assertEqual(len(double.calls), 1)

    def test_el_resumen_cuenta_ejecuciones_y_resultados_del_conjunto(self) -> None:
        self.manifest_path = self.manifest(("JUP-071-a", "JUP-071-b", "JUP-071-c"), name="tres.json")
        code, out, err, _ = self.call(self.argv())
        self.assertEqual((code, out, err), (0, "3 ejecuciones y 6 resultados cargados\n", ""))

    def test_conjunto_vacio_carga_igualmente_el_esquema_y_el_rol(self) -> None:
        code, out, err, double = self.call(["load", "--no-versioned", "--root", str(self.tmp)])
        self.assertEqual((code, out, err), (0, "0 ejecuciones y 0 resultados cargados\n", ""))
        self.assertEqual(len(double.calls), 1)
        payload = double.calls[0][1]["input"].decode("utf-8")
        # Sin ejecuciones se crea el esquema y se vacía, y el rol se crea y se le conceden los permisos: la guía de
        # arranque depende de que `load` deje el esquema aunque el manifiesto esté vacío.
        self.assertIn("CREATE SCHEMA IF NOT EXISTS evaluation", payload)
        self.assertIn("CREATE ROLE", payload)
        self.assertNotIn("INSERT INTO", payload)

    def test_la_salida_es_solo_el_resumen_aunque_psql_hable(self) -> None:
        code, out, err, _ = self.call(self.argv(), stdout=b"COMMIT\n", stderr=b"NOTICE:  ya existe\n")
        self.assertEqual((code, out, err), (0, "1 ejecuciones y 2 resultados cargados\n", ""))

    def test_main_pasa_el_conjunto_la_contrasena_y_el_comando_a_run_load(self) -> None:
        seen: dict = {}

        def fake(dataset, password, psql_command=None, timeout=None):
            seen.update(dataset=dataset, password=password, psql_command=psql_command)
            return "RESUMEN-FALSO"

        with mock.patch.object(tool, "run_load", side_effect=fake):
            code, out, err, double = self.call(self.argv())
        self.assertEqual((code, out, err), (0, "RESUMEN-FALSO\n", ""))
        self.assertEqual(seen["dataset"], tool.build_dataset([self.manifest_path], root=self.tmp))
        self.assertEqual(seen["password"], PW)
        # Sin `--psql-command` se usa el comando por defecto (`None` o la constante: ambos dan el mismo comando).
        self.assertEqual(tool.load_command(seen["psql_command"]), tool.load_command())
        self.assertEqual(double.calls, [])

    def test_main_pasa_la_contrasena_tal_cual_sin_recortarla(self) -> None:
        os.environ[PASSWORD_ENV] = "  con espacios y 'comillas'  "
        seen: dict = {}

        def fake(dataset, password, psql_command=None, timeout=None):
            seen["password"] = password
            return "x"

        with mock.patch.object(tool, "run_load", side_effect=fake):
            self.call(self.argv())
        self.assertEqual(seen["password"], "  con espacios y 'comillas'  ")

    # -- el comando de psql --

    def test_comando_por_defecto_cuando_no_se_da_psql_command(self) -> None:
        _, _, _, double = self.call(self.argv())
        self.assertEqual(double.calls[0][0], EXPECTED_DEFAULT_COMMAND + EXPECTED_FLAGS)

    def test_psql_command_se_parte_como_una_linea_de_comandos(self) -> None:
        command = "docker exec -i mi-contenedor psql -U postgres -d embeddings"
        code, out, err, double = self.call(self.argv("--psql-command", command))
        self.assertEqual((code, out, err), (0, "1 ejecuciones y 2 resultados cargados\n", ""))
        self.assertEqual(double.calls[0][0], [
            "docker", "exec", "-i", "mi-contenedor", "psql", "-U", "postgres", "-d", "embeddings",
            "-v", "ON_ERROR_STOP=1", "-X", "-q"])

    def test_psql_command_respeta_las_comillas_como_un_shell_posix(self) -> None:
        # `shlex.split` POSIX: las comillas agrupan y se quitan; con `split()` o `posix=False` quedarían dentro del argumento.
        command = "docker exec -i 'mi contenedor' psql -U \"post gres\" -d embeddings --flag=a\\ b"
        _, _, _, double = self.call(self.argv("--psql-command", command))
        self.assertEqual(double.calls[0][0], [
            "docker", "exec", "-i", "mi contenedor", "psql", "-U", "post gres", "-d", "embeddings", "--flag=a b",
            "-v", "ON_ERROR_STOP=1", "-X", "-q"])

    def test_psql_command_antes_o_despues_de_las_otras_opciones(self) -> None:
        argv = ["load", "--psql-command", "psql -U x", "--no-versioned", "--manifest", str(self.manifest_path),
                "--root", str(self.tmp)]
        code, out, _, double = self.call(argv)
        self.assertEqual(code, 0)
        self.assertEqual(double.calls[0][0], ["psql", "-U", "x"] + EXPECTED_FLAGS)

    def test_psql_command_se_pasa_a_run_load_como_lista(self) -> None:
        seen: dict = {}

        def fake(dataset, password, psql_command=None, timeout=None):
            seen["command"] = psql_command
            return "x"

        with mock.patch.object(tool, "run_load", side_effect=fake):
            self.call(self.argv("--psql-command", "docker exec -i c psql"))
        self.assertEqual(list(seen["command"]), ["docker", "exec", "-i", "c", "psql"])
        self.assertNotIsInstance(seen["command"], str)

    def test_la_contrasena_no_viaja_en_los_argumentos_ni_en_el_entorno_de_la_llamada(self) -> None:
        _, _, _, double = self.call(self.argv("--psql-command", "docker exec -i c psql"))
        args, kwargs = double.calls[0]
        self.assertNotIn(PW, repr(args))
        self.assertNotIn(PASSWORD_ENV, kwargs["env"])
        self.assertNotIn(PW, "\n".join(kwargs["env"].values()))
        self.assertEqual(kwargs["input"].count(PW.encode("utf-8")), 1)
        self.assertEqual(os.environ[PASSWORD_ENV], PW)

    def test_opciones_de_manifiesto_y_raiz_como_en_rows_y_sql(self) -> None:
        # Dos manifiestos locales sin el versionado: el conjunto es la unión (2 ejecuciones y 4 resultados).
        second = self.manifest(("JUP-071-otro",), name="segundo.json")
        argv = ["load", "--no-versioned", "--manifest", str(self.manifest_path), "--manifest", str(second),
                "--root", str(self.tmp)]
        code, out, _, _ = self.call(argv)
        self.assertEqual((code, out), (0, "2 ejecuciones y 4 resultados cargados\n"))

    def test_sin_no_versioned_se_lee_el_manifiesto_versionado_primero(self) -> None:
        # Se comprueba con un `build_dataset` espiado para no ejecutar Node: el primer manifiesto es el versionado.
        seen: dict = {}

        def fake(manifests, root=tool.ROOT):
            seen["manifests"] = list(manifests)
            return {"dataset_version": 1, "runs": []}

        with mock.patch.object(tool, "build_dataset", side_effect=fake):
            code, out, _, _ = self.call(["load", "--manifest", str(self.manifest_path), "--root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual(seen["manifests"], [tool.DEFAULT_MANIFEST, self.manifest_path])

    def test_no_versioned_quita_el_versionado(self) -> None:
        seen: dict = {}

        def fake(manifests, root=tool.ROOT):
            seen["manifests"] = list(manifests)
            return {"dataset_version": 1, "runs": []}

        with mock.patch.object(tool, "build_dataset", side_effect=fake):
            self.call(["load", "--no-versioned", "--manifest", str(self.manifest_path), "--root", str(self.tmp)])
        self.assertEqual(seen["manifests"], [self.manifest_path])

    # -- errores --

    def test_error_de_datos_devuelve_1_sin_ejecutar_psql(self) -> None:
        argv = ["load", "--no-versioned", "--manifest", str(self.tmp / "no-existe.json"), "--root", str(self.tmp)]
        code, out, err, double = self.call(argv)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn("no-existe.json", err)
        self.assertEqual(double.calls, [])

    def test_informe_que_incumple_el_contrato_devuelve_1_sin_ejecutar_psql(self) -> None:
        bad = copy.deepcopy(ROWS_DOCUMENT)
        bad["results"][0]["status"] = "inventado"
        report = write_json(self.tmp / "malo.json", bad)
        manifest = write_json(self.tmp / "malo-m.json", {"manifest_version": 1, "runs": [
            {"path": str(report), "format": "rows-v1", "milestone": False}]})
        code, out, err, double = self.call(["load", "--no-versioned", "--manifest", str(manifest), "--root", str(self.tmp)])
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("error: "), err)
        self.assertEqual(double.calls, [])

    def test_sql_error_y_adapter_error_de_build_sql_devuelven_1(self) -> None:
        for error in (tool.SqlError("literal no representable"), tool.AdapterError("runs[0]: algo")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(tool, "build_sql", side_effect=error):
                    code, out, err, double = self.call(self.argv())
                self.assertEqual((code, out, err), (1, "", f"error: {error}\n"))
                self.assertEqual(double.calls, [])

    def test_fallo_de_psql_devuelve_1_con_el_mensaje_de_carga_y_sin_salida(self) -> None:
        code, out, err, double = self.call(self.argv(), returncode=3, stderr=b"psql:<stdin>:9: ERROR:  la tabla no existe\n")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: load: psql terminó con código 3"), err)
        self.assertIn("psql:<stdin>:9: ERROR:  la tabla no existe", err)
        self.assertTrue(err.endswith("\n") and err.count("\n") == 1, err)
        self.assertEqual(len(double.calls), 1)

    def test_fallo_de_psql_con_la_contrasena_en_stderr_no_la_filtra(self) -> None:
        stderr = f"LINE 1: ALTER ROLE {READER} WITH LOGIN PASSWORD '{PW}'\n".encode()
        code, out, err, _ = self.call(self.argv(), returncode=3, stderr=stderr)
        self.assertEqual((code, out), (1, ""))
        self.assertNotIn(PW, err)
        self.assertIn("PASSWORD '***'", err)

    def test_ejecutable_inexistente_devuelve_1_con_el_mensaje_de_carga(self) -> None:
        double, patch = patched_run(effect=FileNotFoundError(2, "no such file"))
        out, err = io.StringIO(), io.StringIO()
        with patch, redirect_stdout(out), redirect_stderr(err):
            code = tool.main(self.argv("--psql-command", "no-existe-psql -U x"))
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertTrue(err.getvalue().startswith("error: load: "), err.getvalue())
        self.assertIn("no se encuentra", err.getvalue())
        self.assertIn("no-existe-psql", err.getvalue())

    def test_el_resumen_solo_se_escribe_si_la_carga_acaba_bien(self) -> None:
        code, out, err, _ = self.call(self.argv(), returncode=1, stderr=b"ERROR:  x\n")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: load: "), err)

    # -- uso incorrecto --

    def test_output_no_es_una_opcion_de_load(self) -> None:
        target = self.tmp / "salida.sql"
        code, out, err, double = self.call(self.argv("--output", str(target)))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        # Es una opción desconocida del subcomando (no un `invalid choice` del propio subcomando).
        self.assertIn("unrecognized arguments", err)
        self.assertIn("--output", err)
        self.assertFalse(target.exists())
        self.assertEqual(double.calls, [])

    def test_psql_command_solo_existe_en_load(self) -> None:
        # Se exige primero que `load` la acepte: una prueba que solo mirase `rows` pasaría con cualquier error de uso.
        code, out, err, _ = self.call(self.argv("--psql-command", "psql"))
        self.assertEqual((code, err), (0, ""))
        for command in ("rows", "sql"):
            with self.subTest(command=command):
                code, out, err, double = self.call([command, "--no-versioned", "--psql-command", "psql"])
                self.assertEqual(code, 2)
                self.assertIn("--psql-command", err)
                self.assertEqual(double.calls, [])

    def test_output_sigue_siendo_valida_en_rows_y_sql(self) -> None:
        # Regresión: al sacar `--output` del parser padre no puede desaparecer de los subcomandos que lo usan. Y `load` existe.
        self.assertEqual(self.call(self.argv())[0], 0)
        for command in ("rows", "sql"):
            with self.subTest(command=command):
                target = self.tmp / f"{command}.out"
                code, out, err, _ = self.call([command, "--no-versioned", "--manifest", str(self.manifest_path),
                                              "--root", str(self.tmp), "--output", str(target)])
                self.assertEqual((code, out, err), (0, "", ""))
                self.assertTrue(target.is_file())

    def test_opcion_desconocida_y_psql_command_sin_valor_son_errores_de_uso(self) -> None:
        code, _, err, double = self.call(self.argv("--no-existe"))
        self.assertEqual(code, 2)
        self.assertIn("unrecognized arguments", err)
        code, _, err, double = self.call(["load", "--no-versioned", "--psql-command"])
        self.assertEqual(code, 2)
        self.assertIn("expected one argument", err)
        self.assertEqual(double.calls, [])

    def test_la_ayuda_de_load_lista_sus_opciones(self) -> None:
        code, out, err, _ = self.call(["load", "--help"])
        self.assertEqual(code, 0)
        for option in ("--manifest", "--no-versioned", "--root", "--psql-command"):
            self.assertIn(option, out)
        self.assertNotIn("--output", out)

    def test_la_ayuda_general_lista_el_subcomando_load(self) -> None:
        _, out, _, _ = self.call(["--help"])
        self.assertIn("load", out)


# --- Con un psql FALSO: procesos reales sin Docker ----------------------------------------------------------------


# Un `psql` de mentira: guarda en un JSON lo que recibe (argumentos, entrada en hexadecimal, entorno y directorio) y
# sale como se le pide. Con `FAKE_PSQL_ECHO=1` hace lo que hace `psql` de verdad al fallar: repetir en `stderr` la
# línea de la sentencia que lleva la contraseña (aquí la del `ALTER ROLE`), de modo que la redacción se prueba con una
# fuga real y no con un texto inventado por la prueba. Se pide por variables de entorno que NO contienen la contraseña.
FAKE_PSQL = r'''
import json, os, sys, time
data = sys.stdin.buffer.read()
with open(os.environ["FAKE_PSQL_RECORD"], "w", encoding="utf-8") as handle:
    json.dump({"argv": sys.argv[1:], "stdin_hex": data.hex(), "env": dict(os.environ), "cwd": os.getcwd()}, handle)
if os.environ.get("FAKE_PSQL_SLEEP"):
    time.sleep(float(os.environ["FAKE_PSQL_SLEEP"]))
if os.environ.get("FAKE_PSQL_ECHO"):
    line = next(l for l in data.decode("utf-8").splitlines() if l.startswith("ALTER ROLE"))
    sys.stderr.buffer.write(("psql:<stdin>:77: ERROR:  fallo simulado\nLINE 1: " + line + "\n").encode("utf-8"))
sys.exit(int(os.environ.get("FAKE_PSQL_EXIT", "0")))
'''


class FakePsqlTest(TmpCase):
    def setUp(self) -> None:
        super().setUp()
        self.fake = self.tmp / "fake_psql.py"
        self.fake.write_text(FAKE_PSQL, encoding="utf-8")
        self.record = self.tmp / "registro.json"
        self.manifest_path = self.manifest()
        # El directorio de trabajo del proceso NO es la raíz del repositorio: así `cwd=ROOT` se distingue de heredarlo.
        previous = Path.cwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, previous)

    def psql_command(self) -> str:
        # `as_posix`: en Windows las barras invertidas se perderían con el `shlex.split` POSIX de `main`.
        return shlex.join([Path(sys.executable).as_posix(), self.fake.as_posix()])

    def environment(self, password: str = PW, **extra):
        values = {PASSWORD_ENV: password, "FAKE_PSQL_RECORD": str(self.record)}
        values.update({key: str(value) for key, value in extra.items()})
        return mock.patch.dict(os.environ, values)

    def recorded(self) -> dict:
        data = json.loads(self.record.read_text(encoding="utf-8"))
        data["stdin"] = bytes.fromhex(data["stdin_hex"])
        return data

    def main(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        argv = ["load", "--no-versioned", "--manifest", str(self.manifest_path), "--root", str(self.tmp),
                "--psql-command", self.psql_command(), *extra]
        with redirect_stdout(out), redirect_stderr(err):
            code = tool.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_exito_de_extremo_a_extremo(self) -> None:
        with self.environment(PW_HOSTILE):
            code, out, err = self.main()
        self.assertEqual((code, out, err), (0, "1 ejecuciones y 2 resultados cargados\n", ""))
        data = self.recorded()
        # Las opciones de `psql` llegan tal cual tras el comando.
        self.assertEqual(data["argv"], EXPECTED_FLAGS)
        # Los bytes que recibe son los UTF-8 de los dos scripts, con la contraseña unicode intacta.
        dataset = tool.build_dataset([self.manifest_path], root=self.tmp)
        expected = (tool.build_sql(dataset) + "\n" + tool.build_role_sql(PW_HOSTILE)).encode("utf-8")
        self.assertEqual(data["stdin"], expected)
        self.assertIn("日本".encode("utf-8"), data["stdin"])
        # El segundo script (tras el de datos y una línea en blanco) fija exactamente esa contraseña.
        role_part = data["stdin"].decode("utf-8")[len(tool.build_sql(dataset)) + 1:]
        self.assertEqual(password_of(role_part), PW_HOSTILE)

    def test_el_proceso_hijo_no_ve_la_contrasena_en_su_entorno_real(self) -> None:
        with self.environment():
            code, _, _ = self.main()
        self.assertEqual(code, 0)
        data = self.recorded()
        env = data["env"]
        self.assertNotIn(PASSWORD_ENV, {key.upper() for key in env})
        for key, value in env.items():
            self.assertNotIn(PW, value, key)
            self.assertNotIn(PW, key)
        self.assertNotIn(PW, " ".join(data["argv"]))
        self.assertEqual(env["PGCLIENTENCODING"], "UTF8")
        # El resto del entorno se hereda (el `psql` real necesita `PATH` y, en Windows, `SYSTEMROOT`).
        self.assertEqual(env["FAKE_PSQL_RECORD"], str(self.record))
        self.assertEqual(env.get("PATH"), os.environ.get("PATH"))

    def test_el_directorio_de_trabajo_del_hijo_es_la_raiz_del_repositorio(self) -> None:
        with self.environment():
            self.main()
        self.assertNotEqual(Path.cwd().resolve(), ROOT.resolve())
        self.assertEqual(Path(self.recorded()["cwd"]).resolve(), ROOT.resolve())

    def test_la_contrasena_unicode_con_comillas_llega_en_utf8_sin_corromperse(self) -> None:
        password = "contraseña-ñ-日本-it's-🔑"
        with self.environment(password):
            code, _, _ = self.main()
        self.assertEqual(code, 0)
        stdin = self.recorded()["stdin"]
        self.assertIn("'contraseña-ñ-日本-it''s-🔑'".encode("utf-8"), stdin)
        self.assertNotIn(b"\r", stdin)

    def test_fallo_que_repite_la_sentencia_con_la_contrasena_sale_tapado(self) -> None:
        with self.environment(PW_HOSTILE, FAKE_PSQL_EXIT=3, FAKE_PSQL_ECHO=1):
            code, out, err = self.main()
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("error: load: psql terminó con código 3: "), err)
        # `psql` imprimió la línea con la contraseña (escapada) y la herramienta la tapó.
        self.assertIn(f"LINE 1: ALTER ROLE {READER} WITH LOGIN PASSWORD '***'", err)
        escaped = PW_HOSTILE.replace("'", "''")
        for text in (PW_HOSTILE, escaped, "日本", "n''ew"):
            self.assertNotIn(text, err)
        self.assertEqual(err.count("\n"), 1)

    def test_codigo_de_salida_del_psql_falso(self) -> None:
        with self.environment(FAKE_PSQL_EXIT=2):
            code, out, err = self.main()
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("error: load: psql terminó con código 2"), err)

    def test_timeout_real_mata_al_proceso_y_da_load_error(self) -> None:
        dataset = tool.build_dataset([self.manifest_path], root=self.tmp)
        with self.environment(FAKE_PSQL_SLEEP=60):
            with self.assertRaises(tool.LoadError) as caught:
                tool.run_load(dataset, PW, [sys.executable, str(self.fake)], timeout=1)
        message = str(caught.exception)
        self.assertTrue(message.startswith("load: "), message)
        self.assertIn("timeout", message.lower())
        self.assertNotIn(PW, message)

    def test_ejecutable_inexistente_real(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with self.environment(), redirect_stdout(out), redirect_stderr(err):
            code = tool.main(["load", "--no-versioned", "--manifest", str(self.manifest_path), "--root", str(self.tmp),
                              "--psql-command", "ejecutable-inexistente-xyz -U postgres"])
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertTrue(err.getvalue().startswith("error: load: "), err.getvalue())
        self.assertIn("no se encuentra", err.getvalue())
        self.assertIn("ejecutable-inexistente-xyz", err.getvalue())
        self.assertNotIn(PW, err.getvalue())

    def test_el_run_load_real_devuelve_el_resumen(self) -> None:
        dataset = tool.build_dataset([self.manifest_path], root=self.tmp)
        with self.environment():
            summary = tool.run_load(dataset, PW, [sys.executable, str(self.fake)])
        self.assertEqual(summary, "1 ejecuciones y 2 resultados cargados")
        self.assertEqual(self.recorded()["argv"], EXPECTED_FLAGS)


# --- La CLI como proceso real -----------------------------------------------------------------------------------


def run_cli(*args, env_extra=None, env_remove=(), cwd=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    for key in env_remove:
        env.pop(key, None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(TOOL_PATH), *[str(arg) for arg in args]], capture_output=True, env=env,
                          timeout=240, check=False, cwd=None if cwd is None else str(cwd))


class CliProcessTest(TmpCase):
    def test_sin_la_variable_sale_con_1_y_el_mensaje_sin_tocar_docker(self) -> None:
        # El `--psql-command` apunta a un ejecutable que no existe: si la herramienta intentara cargar, el error sería
        # otro. Se mira la variable antes que nada, así que ni siquiera se lee el manifiesto inexistente.
        completed = run_cli("load", "--no-versioned", "--manifest", self.tmp / "no-existe.json", "--psql-command",
                            "ejecutable-inexistente-xyz", env_remove=(PASSWORD_ENV,))
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(completed.stderr.decode("utf-8").replace("\r\n", "\n"), MISSING_VARIABLE_ERROR)

    def test_con_la_variable_vacia_tambien(self) -> None:
        completed = run_cli("load", "--no-versioned", env_extra={PASSWORD_ENV: ""})
        self.assertEqual((completed.returncode, completed.stdout), (1, b""))
        self.assertEqual(completed.stderr.decode("utf-8").replace("\r\n", "\n"), MISSING_VARIABLE_ERROR)

    def test_exito_con_un_psql_falso_imprime_bytes_sin_retorno_de_carro(self) -> None:
        fake = self.tmp / "fake_psql.py"
        fake.write_text(FAKE_PSQL, encoding="utf-8")
        record = self.tmp / "registro.json"
        manifest = self.manifest()
        command = shlex.join([Path(sys.executable).as_posix(), fake.as_posix()])
        completed = run_cli("load", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--psql-command", command,
                            env_extra={PASSWORD_ENV: PW, "FAKE_PSQL_RECORD": str(record)}, cwd=self.tmp)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        # Bytes, sin traducción de saltos: como `rows` y `sql`, la salida es idéntica en Windows y en Linux.
        self.assertEqual(completed.stdout, b"1 ejecuciones y 2 resultados cargados\n")
        self.assertEqual(completed.stderr, b"")
        data = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(data["argv"], EXPECTED_FLAGS)
        self.assertNotIn(PASSWORD_ENV, data["env"])
        self.assertEqual(Path(data["cwd"]).resolve(), ROOT.resolve())

    def test_fallo_del_psql_falso_sale_con_1_por_stderr_y_sin_stdout(self) -> None:
        fake = self.tmp / "fake_psql.py"
        fake.write_text(FAKE_PSQL, encoding="utf-8")
        manifest = self.manifest()
        command = shlex.join([Path(sys.executable).as_posix(), fake.as_posix()])
        completed = run_cli("load", "--no-versioned", "--manifest", manifest, "--root", self.tmp, "--psql-command", command,
                            env_extra={PASSWORD_ENV: PW, "FAKE_PSQL_RECORD": str(self.tmp / "r.json"),
                                       "FAKE_PSQL_EXIT": "3", "FAKE_PSQL_ECHO": "1"})
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, b"")
        error = completed.stderr.decode("utf-8")
        self.assertTrue(error.startswith("error: load: psql terminó con código 3: "), error)
        self.assertNotIn(PW, error)
        self.assertIn("PASSWORD '***'", error)

    def test_output_en_load_es_un_error_de_uso_con_codigo_2(self) -> None:
        completed = run_cli("load", "--no-versioned", "--output", self.tmp / "x.sql", env_extra={PASSWORD_ENV: PW})
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, b"")
        self.assertIn(b"unrecognized arguments", completed.stderr)
        self.assertFalse((self.tmp / "x.sql").exists())


# --- Con PostgreSQL real -------------------------------------------------------------------------------------------


_SERVER: dict = {}


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo; se crea en la primera petición. Si no hay Docker, cada clase con base se salta."""
    if "failure" in _SERVER:
        raise unittest.SkipTest(_SERVER["failure"])
    if "instance" not in _SERVER:
        try:
            _SERVER["instance"] = evaluation_pg_helper.PostgresServer()
        except unittest.SkipTest as skip:
            _SERVER["failure"] = str(skip)
            raise
    return _SERVER["instance"]


def tearDownModule() -> None:
    # Además de `atexit` del ayudante: el contenedor desaparece al acabar el módulo aunque algún test falle.
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


def docker(args, *, env=None, input_bytes=None, timeout=120) -> subprocess.CompletedProcess:
    process = subprocess.run(["docker", *args], input=input_bytes, capture_output=True, timeout=timeout, env=env, check=False)
    return subprocess.CompletedProcess(process.args, process.returncode, process.stdout.decode("utf-8", "replace"),
                                       process.stderr.decode("utf-8", "replace"))


def container_address() -> str:
    """IP del contenedor en el puente de Docker: la imagen exige contraseña en las conexiones que no son locales."""
    if "address" not in _SERVER:
        result = docker(["inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}", server().name])
        addresses = result.stdout.split()
        if result.returncode != 0 or not addresses:
            raise RuntimeError(f"no se pudo obtener la IP del contenedor: {result.stdout} {result.stderr}")
        _SERVER["address"] = addresses[0]
    return _SERVER["address"]


def as_role(password: str | None, sql: str, user: str = READER) -> subprocess.CompletedProcess:
    """Ejecuta `sql` como `user` (por defecto, el rol de Grafana) conectando a la IP del contenedor.

    La contraseña se pasa por `PGPASSWORD` en el entorno del cliente de Docker (`-e PGPASSWORD` sin valor), con `-w`
    para que `psql` no la pida. Sin contraseña (`None`) no se define: la conexión debe rechazarse.
    """
    env = {key: value for key, value in os.environ.items() if key != "PGPASSWORD"}
    command = ["exec", "-i", "-e", "PGCLIENTENCODING=UTF8"]
    if password is not None:
        env["PGPASSWORD"] = password
        command += ["-e", "PGPASSWORD"]
    command += [server().name, "psql", "-h", container_address(), "-U", user, "-d", "embeddings", "-w", "-X", "-A", "-t", "-q",
                "-v", "ON_ERROR_STOP=1"]
    return docker(command, env=env, input_bytes=sql.encode("utf-8"))


def role_scalar(password: str, sql: str) -> str:
    result = as_role(password, sql)
    if result.returncode != 0:
        raise AssertionError(f"el rol no pudo ejecutar {sql!r}: {result.stderr.strip()}")
    return result.stdout.strip()


def psql_command() -> str:
    return shlex.join(["docker", "exec", "-i", "-e", "PGCLIENTENCODING=UTF8", server().name, "psql", "-U", "postgres",
                       "-d", "embeddings"])


def call_load(password: str, *extra, versioned: bool = False, manifest: Path | None = None):
    """Ejecuta `main(["load", ...])` contra el contenedor con la contraseña en el entorno. Devuelve `(código, stdout, stderr)`."""
    argv = ["load", "--psql-command", psql_command()]
    if not versioned:
        argv.append("--no-versioned")
    if manifest is not None:
        argv += ["--manifest", str(manifest), "--root", str(manifest.parent)]
    argv += list(extra)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, {PASSWORD_ENV: password}), redirect_stdout(out), redirect_stderr(err):
        try:
            code = tool.main(argv)
        except SystemExit as exit_:
            code = exit_.code
    return code, out.getvalue(), err.getvalue()


CLEAN_SQL = """
DROP SCHEMA IF EXISTS evaluation CASCADE;
DROP TABLE IF EXISTS public.evaluation_load_secret;
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grafana_evaluation_reader') THEN
    DROP OWNED BY grafana_evaluation_reader;
    DROP ROLE grafana_evaluation_reader;
  END IF;
END
$$;
"""
SECRET_TABLE_SQL = """
CREATE TABLE public.evaluation_load_secret (a integer);
INSERT INTO public.evaluation_load_secret VALUES (1);
"""


def reset_database() -> None:
    """Deja la base sin esquema `evaluation` ni rol, y con una tabla ajena en `public`: cada clase parte de cero."""
    result = server().psql(stdin=CLEAN_SQL + SECRET_TABLE_SQL)
    if result.returncode != 0:
        raise RuntimeError(f"no se pudo limpiar la base: {result.stderr.strip()}")


def count(table: str) -> str:
    return server().scalar(f"SELECT count(*) FROM evaluation.{table}")


class DbCase(unittest.TestCase):
    """Base de las pruebas con PostgreSQL real: arranca (o reutiliza) el servidor del módulo y parte de una base limpia."""

    @classmethod
    def setUpClass(cls) -> None:
        server()
        reset_database()

    @classmethod
    def tearDownClass(cls) -> None:
        # Sin el rol, el esquema ni la tabla ajena: la siguiente clase no hereda nada.
        server().psql(stdin=CLEAN_SQL)


class VersionedLoadTest(DbCase):
    """(a) y (b): `load` con el conjunto versionado crea los datos, el rol y sus permisos."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.result = call_load(PW, versioned=True)

    def test_carga_con_codigo_0_y_el_resumen_del_conjunto_versionado(self) -> None:
        code, out, err = self.result
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "6 ejecuciones y 405 resultados cargados\n")
        self.assertEqual(err, "")

    def test_las_tablas_tienen_las_filas_del_resumen(self) -> None:
        self.assertEqual(count("runs"), "6")
        self.assertEqual(count("results"), "405")

    def test_el_rol_existe_puede_iniciar_sesion_y_no_tiene_privilegios(self) -> None:
        rows = server().query(
            "SELECT rolcanlogin::text, rolsuper::text, rolcreatedb::text, rolcreaterole::text, rolreplication::text, "
            f"rolbypassrls::text FROM pg_roles WHERE rolname = '{READER}'")
        # LOGIN y ninguno de los atributos que dan poder sobre el servidor.
        self.assertEqual(rows, [["true", "false", "false", "false", "false", "false"]])
        self.assertEqual(server().scalar(f"SELECT count(*) FROM pg_roles WHERE rolname LIKE 'grafana%'"), "1")
        self.assertEqual(server().scalar(f"SELECT rolpassword IS NOT NULL FROM pg_authid WHERE rolname = '{READER}'"), "t")

    def test_no_pertenece_a_ningun_otro_rol(self) -> None:
        self.assertEqual(server().scalar(f"SELECT count(*) FROM pg_roles WHERE rolname = '{READER}'"), "1")
        # Un `GRANT pg_read_all_data TO ...` le daría lectura de todo; el contrato dice solo el esquema `evaluation`.
        self.assertEqual(server().scalar(
            "SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member "
            f"WHERE r.rolname = '{READER}'"), "0")

    def test_solo_tiene_select_y_sobre_las_dos_tablas_y_las_dos_vistas(self) -> None:
        rows = server().query(
            "SELECT table_schema, table_name, privilege_type FROM information_schema.table_privileges "
            f"WHERE grantee = '{READER}' ORDER BY table_schema, table_name, privilege_type")
        self.assertEqual(rows, [["evaluation", "comparable_runs", "SELECT"], ["evaluation", "config_changes", "SELECT"],
                                ["evaluation", "results", "SELECT"], ["evaluation", "runs", "SELECT"]])

    def test_permisos_de_base_y_de_esquemas(self) -> None:
        rows = server().query(
            f"SELECT has_database_privilege('{READER}', 'embeddings', 'CONNECT')::text, "
            f"has_database_privilege('{READER}', 'embeddings', 'CREATE')::text, "
            f"has_schema_privilege('{READER}', 'evaluation', 'USAGE')::text, "
            f"has_schema_privilege('{READER}', 'evaluation', 'CREATE')::text, "
            f"has_schema_privilege('{READER}', 'public', 'CREATE')::text")
        # CONNECT y USAGE sí; CREATE en la base, en `evaluation` y en `public`, no.
        self.assertEqual(rows, [["true", "false", "true", "false", "false"]])

    def test_una_tabla_creada_despues_en_evaluation_ya_nace_legible(self) -> None:
        # `ALTER DEFAULT PRIVILEGES`: sin él, una tabla o vista nueva (las tareas siguientes añaden más) quedaría
        # ilegible para Grafana hasta la siguiente carga.
        self.assertEqual(server().psql("CREATE TABLE evaluation.tabla_nueva (a integer)").returncode, 0)
        self.addCleanup(server().psql, "DROP TABLE IF EXISTS evaluation.tabla_nueva")
        self.assertEqual(server().scalar(f"SELECT has_table_privilege('{READER}', 'evaluation.tabla_nueva', 'SELECT')::text"),
                         "true")
        self.assertEqual(server().scalar(f"SELECT has_table_privilege('{READER}', 'evaluation.tabla_nueva', 'INSERT')::text"),
                         "false")


class RoleLoginTest(DbCase):
    """(c): iniciar sesión COMO el rol de Grafana, con su contraseña, y lo que puede y no puede hacer."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.result = call_load(PW, versioned=True)

    def test_la_carga_previa_fue_bien(self) -> None:
        self.assertEqual(self.result[0], 0, self.result[2])

    def test_lee_ejecuciones_resultados_y_las_dos_vistas(self) -> None:
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.runs"), "6")
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.results"), "405")
        for view in ("config_changes", "comparable_runs"):
            with self.subTest(view=view):
                # Lo que ve el rol es lo que ve el administrador (las vistas calculan sobre las tablas del esquema).
                self.assertEqual(role_scalar(PW, f"SELECT count(*) FROM evaluation.{view}"), count(view))

    def test_el_rol_es_el_usuario_de_la_sesion(self) -> None:
        # Garantiza que las pruebas de abajo se ejecutan COMO el rol y no como el superusuario.
        self.assertEqual(role_scalar(PW, "SELECT current_user"), READER)
        self.assertEqual(role_scalar(PW, "SELECT current_setting('is_superuser')"), "off")

    def test_escribir_en_el_esquema_de_evaluacion_es_rechazado(self) -> None:
        statements = {
            "INSERT en runs": "INSERT INTO evaluation.runs (run_id) VALUES ('intruso')",
            "INSERT en results": "INSERT INTO evaluation.results (run_id) VALUES ('intruso')",
            "UPDATE": "UPDATE evaluation.runs SET run_id = run_id",
            "UPDATE de results": "UPDATE evaluation.results SET status = status",
            "DELETE": "DELETE FROM evaluation.results",
            "DELETE de runs": "DELETE FROM evaluation.runs",
            "TRUNCATE results": "TRUNCATE evaluation.results",
            "TRUNCATE runs": "TRUNCATE evaluation.runs",
            "CREATE TABLE": "CREATE TABLE evaluation.intruso (a integer)",
            "CREATE VIEW": "CREATE VIEW evaluation.intruso AS SELECT 1 AS a",
        }
        for name, statement in statements.items():
            with self.subTest(name):
                result = as_role(PW, statement)
                self.assertNotEqual(result.returncode, 0, f"{statement} se ejecutó")
                self.assertIn("permission denied", result.stderr)

    def test_alterar_o_borrar_objetos_del_esquema_es_rechazado(self) -> None:
        for statement in ("DROP TABLE evaluation.results", "DROP VIEW evaluation.comparable_runs",
                          "ALTER TABLE evaluation.runs ADD COLUMN intruso integer", "DROP SCHEMA evaluation CASCADE"):
            with self.subTest(statement):
                result = as_role(PW, statement)
                self.assertNotEqual(result.returncode, 0, f"{statement} se ejecutó")
                self.assertRegex(result.stderr, r"permission denied|must be owner")

    def test_leer_otro_esquema_es_rechazado(self) -> None:
        # La tabla la creó `postgres` en `public` al limpiar la base (`reset_database`).
        self.assertEqual(server().scalar("SELECT count(*) FROM public.evaluation_load_secret"), "1")
        result = as_role(PW, "SELECT count(*) FROM public.evaluation_load_secret")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("permission denied", result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_crear_objetos_fuera_del_esquema_es_rechazado(self) -> None:
        for statement in ("CREATE TABLE public.intruso (a integer)", "CREATE SCHEMA intruso"):
            with self.subTest(statement):
                result = as_role(PW, statement)
                self.assertNotEqual(result.returncode, 0, f"{statement} se ejecutó")
                self.assertIn("permission denied", result.stderr)

    def test_no_puede_cambiar_de_rol_ni_leer_las_contrasenas(self) -> None:
        for statement in ("SET ROLE postgres", "SELECT rolpassword FROM pg_authid"):
            with self.subTest(statement):
                result = as_role(PW, statement)
                self.assertNotEqual(result.returncode, 0, f"{statement} se ejecutó")
                self.assertIn("permission denied", result.stderr)

    def test_los_intentos_de_escritura_no_cambiaron_nada(self) -> None:
        # Si algún permiso sobrara, las pruebas de arriba lo habrían notado; aquí se comprueba el estado final.
        self.assertEqual(count("runs"), "6")
        self.assertEqual(count("results"), "405")
        self.assertEqual(server().scalar("SELECT count(*) FROM pg_namespace WHERE nspname = 'intruso'"), "0")
        # `GRANT` sin ser dueño no falla (solo avisa): lo que importa es que no se concedió nada.
        as_role(PW, f"GRANT INSERT ON evaluation.runs TO {READER}")
        self.assertEqual(server().scalar(f"SELECT has_table_privilege('{READER}', 'evaluation.runs', 'INSERT')::text"), "false")

    def test_la_contrasena_equivocada_es_rechazada(self) -> None:
        self.assertEqual(role_scalar(PW, "SELECT 1"), "1")
        for wrong in (PW + "x", PW[:-1], PW.lower(), "otra"):
            with self.subTest(wrong=wrong):
                result = as_role(wrong, "SELECT 1")
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("password authentication failed", result.stderr)
                self.assertEqual(result.stdout.strip(), "")

    def test_sin_contrasena_es_rechazado(self) -> None:
        self.assertEqual(role_scalar(PW, "SELECT 1"), "1")
        result = as_role(None, "SELECT 1")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "")

    def test_la_comprobacion_de_contrasena_es_real(self) -> None:
        # Guarda de que la comprobación es real: con el mismo método de conexión (la IP del contenedor, no el socket que
        # confía en todos) una contraseña mala se rechaza y la correcta se admite.
        self.assertNotEqual(as_role("mala", "SELECT 1").returncode, 0)
        self.assertEqual(as_role(PW, "SELECT 1").returncode, 0)


class ReloadAndRotationTest(DbCase):
    """(d): una segunda carga con otra contraseña no falla, rota la contraseña y conserva los permisos."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.first = call_load(PW, versioned=True)
        cls.first_login = as_role(PW, "SELECT count(*) FROM evaluation.runs")
        cls.second = call_load(PW_HOSTILE, versioned=True)

    def test_la_primera_carga_dejo_entrar_con_la_primera_contrasena(self) -> None:
        self.assertEqual(self.first[0], 0, self.first[2])
        self.assertEqual(self.first_login.returncode, 0, self.first_login.stderr)
        self.assertEqual(self.first_login.stdout.strip(), "6")

    def test_la_segunda_carga_no_falla_porque_el_rol_ya_existe(self) -> None:
        code, out, err = self.second
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "6 ejecuciones y 405 resultados cargados\n")
        self.assertEqual(err, "")
        self.assertNotIn("already exists", err)

    def test_regeneracion_repetida_deja_el_mismo_numero_de_filas(self) -> None:
        # Escenario «Regeneración repetida» de la spec.
        self.assertEqual(count("runs"), "6")
        self.assertEqual(count("results"), "405")

    def test_la_contrasena_vieja_deja_de_valer(self) -> None:
        self.assertEqual(self.first_login.returncode, 0, self.first_login.stderr)
        self.assertEqual(self.second[0], 0, self.second[2])
        result = as_role(PW, "SELECT 1")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("password authentication failed", result.stderr)

    def test_la_nueva_con_comillas_barra_y_unicode_sirve(self) -> None:
        self.assertEqual(role_scalar(PW_HOSTILE, "SELECT count(*) FROM evaluation.runs"), "6")
        self.assertEqual(role_scalar(PW_HOSTILE, "SELECT count(*) FROM evaluation.results"), "405")

    def test_hay_un_unico_rol_aunque_se_cargue_dos_veces(self) -> None:
        self.assertEqual(server().scalar("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'grafana%'"), "1")

    def test_los_permisos_se_conservan_tras_el_truncate_de_la_segunda_carga(self) -> None:
        rows = server().query(
            "SELECT table_name, privilege_type FROM information_schema.table_privileges "
            f"WHERE grantee = '{READER}' AND table_schema = 'evaluation' ORDER BY table_name, privilege_type")
        self.assertEqual(rows, [["comparable_runs", "SELECT"], ["config_changes", "SELECT"], ["results", "SELECT"],
                                ["runs", "SELECT"]])
        for view in ("config_changes", "comparable_runs"):
            self.assertEqual(role_scalar(PW_HOSTILE, f"SELECT count(*) FROM evaluation.{view}"), count(view))

    def test_tras_la_segunda_carga_el_rol_sigue_sin_poder_escribir(self) -> None:
        for statement in ("INSERT INTO evaluation.runs (run_id) VALUES ('x')", "DELETE FROM evaluation.results",
                          "TRUNCATE evaluation.runs", "SELECT count(*) FROM public.evaluation_load_secret"):
            with self.subTest(statement):
                result = as_role(PW_HOSTILE, statement)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("permission denied", result.stderr)

    def test_una_tercera_carga_con_la_misma_contrasena_tambien_funciona(self) -> None:
        code, out, err = call_load(PW_HOSTILE, versioned=True)
        self.assertEqual((code, out, err), (0, "6 ejecuciones y 405 resultados cargados\n", ""))
        self.assertEqual(role_scalar(PW_HOSTILE, "SELECT count(*) FROM evaluation.runs"), "6")


class PreexistingRoleTest(DbCase):
    """El rol ya existía (creado a mano, con otra contraseña) antes de la primera carga: `CREATE ROLE` fallaría."""

    def test_load_adopta_el_rol_existente_y_cambia_su_contrasena(self) -> None:
        reset_database()
        result = server().psql(f"CREATE ROLE {READER} LOGIN PASSWORD 'vieja-contrasena'")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(role_scalar("vieja-contrasena", "SELECT 1"), "1")
        code, out, err = call_load(PW, versioned=False)
        self.assertEqual((code, out, err), (0, "0 ejecuciones y 0 resultados cargados\n", ""))
        self.assertNotEqual(as_role("vieja-contrasena", "SELECT 1").returncode, 0)
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.runs"), "0")

    def test_un_rol_existente_sin_login_recupera_el_inicio_de_sesion(self) -> None:
        reset_database()
        server().psql(f"CREATE ROLE {READER} NOLOGIN")
        code, _, err = call_load(PW)
        self.assertEqual(code, 0, err)
        self.assertEqual(server().scalar(f"SELECT rolcanlogin::text FROM pg_roles WHERE rolname = '{READER}'"), "true")
        self.assertEqual(role_scalar(PW, "SELECT 1"), "1")


class FailureMidLoadTest(DbCase):
    """(e): un fallo a mitad de la parte de datos deja los datos y el rol anteriores intactos y no filtra la contraseña."""

    OTHER = "otra-contrasena-que-no-debe-llegar-Zq1"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.first = call_load(PW, versioned=True)
        # Una restricción que ninguna fila nueva puede cumplir (`NOT VALID`: no revisa las filas ya cargadas). El segundo
        # `load` vacía las tablas y falla al insertar: justo «después de empezar».
        cls.block = server().psql("ALTER TABLE evaluation.results ADD CONSTRAINT zz_bloqueo CHECK (false) NOT VALID")
        cls.second = call_load(cls.OTHER, versioned=True)

    def test_la_preparacion_fue_bien(self) -> None:
        self.assertEqual(self.first[0], 0, self.first[2])
        self.assertEqual(self.block.returncode, 0, self.block.stderr)

    def test_el_fallo_devuelve_1_sin_salida_y_con_el_mensaje_de_carga(self) -> None:
        code, out, err = self.second
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: load: psql terminó con código 3"), err)
        self.assertEqual(err.count("\n"), 1)

    def test_la_contrasena_no_aparece_en_el_error(self) -> None:
        err = self.second[2]
        # Precondición: sí hubo un mensaje de error de carga (un `stderr` vacío no demostraría nada).
        self.assertTrue(err.startswith("error: load: "), err)
        self.assertNotIn(self.OTHER, err)
        self.assertNotIn(PW, err)

    def test_los_datos_anteriores_siguen_enteros(self) -> None:
        # El `TRUNCATE` estaba en la misma transacción que los `INSERT` que fallaron: se deshizo con ellos.
        self.assertEqual(count("runs"), "6")
        self.assertEqual(count("results"), "405")

    def test_el_rol_y_su_contrasena_anteriores_siguen_igual(self) -> None:
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.runs"), "6")
        result = as_role(self.OTHER, "SELECT 1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("password authentication failed", result.stderr)



class RecoveryAfterFailureTest(DbCase):
    """Tras un fallo a mitad de la carga, la siguiente carga correcta deja todo en orden (con su propio estado)."""

    def test_una_carga_correcta_despues_de_un_fallo_se_recupera(self) -> None:
        with tempfile.TemporaryDirectory(prefix="evaluation-load-") as directory:
            base = Path(directory)
            report = write_json(base / "informe.json", ROWS_DOCUMENT)
            manifest = write_json(base / "local.json", {"manifest_version": 1, "runs": [
                {"path": str(report), "format": "rows-v1", "milestone": False}]})
            self.assertEqual(call_load(PW, manifest=manifest)[0], 0)
            self.assertEqual(server().psql(
                "ALTER TABLE evaluation.results ADD CONSTRAINT zz_bloqueo CHECK (false) NOT VALID").returncode, 0)
            self.assertEqual(call_load("otra-Zq1", manifest=manifest)[0], 1)
            self.assertEqual(server().psql("ALTER TABLE evaluation.results DROP CONSTRAINT zz_bloqueo").returncode, 0)
            code, out, err = call_load("otra-Zq1", manifest=manifest)
        self.assertEqual((code, out, err), (0, "1 ejecuciones y 2 resultados cargados\n", ""))
        self.assertEqual(role_scalar("otra-Zq1", "SELECT count(*) FROM evaluation.results"), "2")
        self.assertNotEqual(as_role(PW, "SELECT 1").returncode, 0)


class NoLeakTest(DbCase):
    """(f): la contraseña no queda en los registros del contenedor ni en la actividad del servidor."""

    SECRET = "Zq7#kP!wV9&xJ2-fuga-no"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.result = call_load(cls.SECRET, versioned=True)

    def test_la_carga_fue_bien(self) -> None:
        self.assertEqual(self.result[0], 0, self.result[2])

    def test_no_esta_ni_en_stdout_ni_en_stderr_de_la_herramienta(self) -> None:
        self.assertEqual(self.result[0], 0, self.result[2])
        self.assertEqual(self.result[1], "6 ejecuciones y 405 resultados cargados\n")
        self.assertNotIn(self.SECRET, self.result[1])
        self.assertNotIn(self.SECRET, self.result[2])

    def test_no_esta_en_los_registros_del_contenedor(self) -> None:
        # Precondición: la contraseña SÍ llegó al servidor (con ella se inicia sesión); si no, que no esté en los registros no prueba nada.
        self.assertEqual(role_scalar(self.SECRET, "SELECT 1"), "1")
        logs = docker(["logs", server().name])
        self.assertEqual(logs.returncode, 0, logs.stderr)
        self.assertNotIn(self.SECRET, logs.stdout + logs.stderr)

    def test_no_esta_en_la_actividad_del_servidor(self) -> None:
        self.assertEqual(role_scalar(self.SECRET, "SELECT 1"), "1")
        rows = server().query("SELECT query FROM pg_stat_activity")
        self.assertNotIn(self.SECRET, "\n".join(" ".join(row) for row in rows))

    def test_el_rol_guarda_la_contrasena_en_hash_y_no_en_claro(self) -> None:
        # Guarda de que `ALTER ROLE ... PASSWORD` surtió efecto (hay contraseña) y de que el servidor la cifra.
        stored = server().scalar(f"SELECT rolpassword FROM pg_authid WHERE rolname = '{READER}'")
        self.assertTrue(stored.startswith("SCRAM-SHA-256$"), stored[:20])
        self.assertNotIn(self.SECRET, stored)


class EmptyDatabaseTest(DbCase):
    """(g): base vacía (`--no-versioned` sin manifiestos) y escenario de primer arranque."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.result = call_load(PW, versioned=False)

    def test_carga_con_codigo_0_y_el_resumen_vacio(self) -> None:
        self.assertEqual(self.result, (0, "0 ejecuciones y 0 resultados cargados\n", ""))

    def test_el_esquema_y_las_dos_tablas_y_vistas_existen(self) -> None:
        self.assertEqual(server().query(
            "SELECT relname, relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'evaluation' AND c.relkind IN ('r', 'v') ORDER BY relname"),
            [["comparable_runs", "v"], ["config_changes", "v"], ["results", "r"], ["runs", "r"]])
        self.assertEqual(count("runs"), "0")
        self.assertEqual(count("results"), "0")

    def test_el_rol_existe_y_lee_las_tablas_vacias(self) -> None:
        self.assertEqual(server().scalar(f"SELECT rolcanlogin::text FROM pg_roles WHERE rolname = '{READER}'"), "true")
        for relation in ("runs", "results", "config_changes", "comparable_runs"):
            with self.subTest(relation=relation):
                self.assertEqual(role_scalar(PW, f"SELECT count(*) FROM evaluation.{relation}"), "0")

    def test_el_rol_sigue_sin_poder_escribir(self) -> None:
        result = as_role(PW, "INSERT INTO evaluation.runs (run_id) VALUES ('x')")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permission denied", result.stderr)

    def test_cargar_despues_con_datos_no_pierde_los_permisos(self) -> None:
        # Del vacío al versionado y de vuelta: el rol sobrevive a los dos `TRUNCATE`.
        code, out, err = call_load(PW, versioned=True)
        self.assertEqual((code, out, err), (0, "6 ejecuciones y 405 resultados cargados\n", ""))
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.runs"), "6")
        code, out, err = call_load(PW, versioned=False)
        self.assertEqual((code, out), (0, "0 ejecuciones y 0 resultados cargados\n"))
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.runs"), "0")


class LocalManifestLoadTest(DbCase):
    """Un manifiesto local (no de hito) se carga junto al versionado y deja el esquema legible para el rol."""

    def test_carga_local_con_una_ejecucion_no_de_hito(self) -> None:
        with tempfile.TemporaryDirectory(prefix="evaluation-load-") as directory:
            base = Path(directory)
            report = write_json(base / "informe.json", ROWS_DOCUMENT)
            manifest = write_json(base / "local.json", {"manifest_version": 1, "runs": [
                {"path": str(report), "format": "rows-v1", "milestone": False}]})
            code, out, err = call_load(PW, versioned=False, manifest=manifest)
        self.assertEqual((code, out, err), (0, "1 ejecuciones y 2 resultados cargados\n", ""))
        self.assertEqual(role_scalar(PW, "SELECT run_id || ':' || milestone::text FROM evaluation.runs"),
                         "JUP-071-demo-1:false")
        self.assertEqual(role_scalar(PW, "SELECT count(*) FROM evaluation.results"), "2")


if __name__ == "__main__":
    unittest.main()
