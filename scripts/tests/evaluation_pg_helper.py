"""Ayudante de pruebas con PostgreSQL real para el panel de evaluación (JUP-121, tareas 3.2, 3.3 y 5.x).

NO es un módulo de pruebas (sin `unittest.TestCase`): los tests lo importan con `import evaluation_pg_helper`, que
funciona porque `unittest discover -s scripts/tests` pone este directorio en `sys.path`.

Levanta un contenedor DESECHABLE y aislado de la imagen EXACTA que usa el servicio `postgres-pgvector` de
`docker-compose.yml` (se lee de ahí, con su huella `@sha256`, para que las pruebas corran contra la misma versión
de PostgreSQL y pgvector que el despliegue). Reglas de aislamiento:

* nombre único (`evaluation-test-pg-<pid>-<aleatorio>`), contraseña aleatoria solo para esa sesión y puerto
  efímero publicado únicamente en `127.0.0.1`; no toca ni el compose del proyecto ni sus volúmenes;
* los comandos de las pruebas se ejecutan DENTRO del contenedor (`docker exec ... psql`, por el socket local), así
  que ni la contraseña ni el puerto salen de este módulo;
* se limpia siempre: `stop()` es idempotente y se engancha a `atexit` además de a `tearDownModule` de cada módulo,
  de modo que un test que falla (o un Ctrl+C) no deja contenedores ni volúmenes anónimos;
* un solo servidor por módulo de tests (`setUpModule`): arrancar PostgreSQL cuesta segundos y cada test limpia con
  `load_dataset`, que vacía y vuelve a cargar todo en una transacción.

Si no hay CLI `docker` o el demonio no responde se lanza `unittest.SkipTest("Docker no disponible")`: es la única
excepción a «sin skip», porque son pruebas contra un servicio real que en una máquina sin Docker no se pueden
ejecutar (igual que las demás pruebas del repositorio con servicios reales).
"""
from __future__ import annotations

import atexit
import importlib.util
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = ROOT / "docker-compose.yml"
SERVICE = "postgres-pgvector"
DATABASE = "embeddings"
READY_TIMEOUT_SECONDS = 90
COMMAND_TIMEOUT_SECONDS = 120

_LIVE_SERVERS: list["PostgresServer"] = []


def compose_image(compose_path: Path = COMPOSE_PATH, service: str = SERVICE) -> str:
    """Imagen del servicio `postgres-pgvector` tal como está escrita en `docker-compose.yml` (con su huella)."""
    inside = False
    for line in compose_path.read_text(encoding="utf-8").splitlines():
        # Un servicio es una clave con dos espacios de sangría; al llegar a la siguiente se acaba el bloque.
        if re.match(r"^  [A-Za-z0-9_.-]+:\s*$", line):
            inside = line.strip() == f"{service}:"
            continue
        if inside:
            match = re.match(r"^    image:\s*(\S+)\s*$", line)
            if match:
                return match.group(1)
    raise RuntimeError(f"no se encontró la imagen del servicio {service} en {compose_path}")


def _docker(args: list[str], *, input_bytes: bytes | None = None, timeout: int = COMMAND_TIMEOUT_SECONDS,
            env: dict | None = None) -> subprocess.CompletedProcess:
    # Bytes y no texto: la decodificación UTF-8 es explícita y no depende de la página de códigos de Windows.
    process = subprocess.run(["docker", *args], input=input_bytes, capture_output=True, timeout=timeout,
                             env=env, check=False)
    return subprocess.CompletedProcess(
        process.args, process.returncode, process.stdout.decode("utf-8", "replace"),
        process.stderr.decode("utf-8", "replace"))


def _require_docker() -> None:
    if shutil.which("docker") is None:
        raise unittest.SkipTest("Docker no disponible")
    try:
        info = _docker(["info", "--format", "{{.ServerVersion}}"], timeout=60)
    except (OSError, subprocess.SubprocessError):
        raise unittest.SkipTest("Docker no disponible") from None
    if info.returncode != 0:
        raise unittest.SkipTest("Docker no disponible")


class PostgresServer:
    """Contenedor PostgreSQL desechable. Crear la instancia lo arranca y espera a que acepte conexiones."""

    def __init__(self) -> None:
        _require_docker()
        self.image = compose_image()
        self.name = f"evaluation-test-pg-{os.getpid()}-{secrets.token_hex(4)}"
        self.password = secrets.token_urlsafe(24)
        self.volumes: list[str] = []
        self.port: str | None = None
        self._stopped = False
        # Se registra ANTES de arrancar: si `docker run` falla a medias o llega un Ctrl+C durante la espera, la
        # limpieza igualmente intenta borrar lo que haya quedado.
        _LIVE_SERVERS.append(self)
        atexit.register(self.stop)
        try:
            self._start()
        except BaseException:
            self.stop()
            raise

    # -- ciclo de vida ----------------------------------------------------------------------------------------

    def _start(self) -> None:
        # La contraseña viaja por el entorno del cliente de Docker (`-e VAR` sin valor) y no en la línea de
        # comandos, que cualquier proceso de la máquina puede ver. `fsync=off` y `synchronous_commit=off` aceleran
        # la carga: es un contenedor desechable, así que la durabilidad no importa.
        env = {**os.environ, "POSTGRES_PASSWORD": self.password}
        run = _docker([
            "run", "-d", "--rm", "--name", self.name,
            "-e", "POSTGRES_PASSWORD", "-e", f"POSTGRES_DB={DATABASE}",
            "-p", "127.0.0.1::5432", self.image,
            "postgres", "-c", "fsync=off", "-c", "synchronous_commit=off", "-c", "full_page_writes=off",
        ], env=env)
        if run.returncode != 0:
            raise RuntimeError(f"no se pudo arrancar {self.image}: {run.stderr.strip()}")
        mounts = _docker(["inspect", "-f", "{{range .Mounts}}{{.Name}} {{end}}", self.name])
        self.volumes = [name for name in mounts.stdout.split() if name]
        port = _docker(["port", self.name, "5432/tcp"])
        if port.returncode == 0 and port.stdout.strip():
            self.port = port.stdout.strip().splitlines()[0].rsplit(":", 1)[-1]
        self._wait_until_ready()

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            running = _docker(["inspect", "-f", "{{.State.Running}}", self.name])
            if running.returncode != 0 or running.stdout.strip() != "true":
                logs = _docker(["logs", "--tail", "30", self.name])
                raise RuntimeError(f"el contenedor {self.name} se detuvo al arrancar: {logs.stdout}{logs.stderr}")
            # `-h 127.0.0.1` es imprescindible: durante la inicialización el entrypoint levanta un servidor
            # temporal que solo escucha por socket Unix y `pg_isready` sin `-h` lo daría por listo demasiado pronto.
            ready = _docker(["exec", self.name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", DATABASE])
            if ready.returncode == 0:
                check = self.psql("SELECT 1")
                if check.returncode == 0:
                    return
            time.sleep(0.5)
        raise RuntimeError(f"PostgreSQL no estuvo listo en {READY_TIMEOUT_SECONDS} s")

    def stop(self) -> None:
        """Borra el contenedor y los volúmenes anónimos que hubieran quedado. Idempotente y sin lanzar errores."""
        if self._stopped:
            return
        self._stopped = True
        try:
            _docker(["rm", "-f", "-v", self.name], timeout=60)
            for volume in self.volumes:
                # `--rm` ya los borra casi siempre; si quedó alguno (carrera con el borrado automático) se retira aquí.
                _docker(["volume", "rm", "-f", volume], timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            if self in _LIVE_SERVERS:
                _LIVE_SERVERS.remove(self)

    # -- consultas --------------------------------------------------------------------------------------------

    def psql(self, sql: str | None = None, args=(), stdin=None) -> subprocess.CompletedProcess:
        """Ejecuta `psql` dentro del contenedor. `sql` o `stdin` (str o bytes) van por la entrada estándar.

        No lanza si `psql` falla: el llamador mira `returncode` y `stderr`. Usa `ON_ERROR_STOP`, así que un error en
        cualquier sentencia da código distinto de cero. La salida es sin formato (`-A -t`: sin alineación ni
        cabeceras) y los datos entran y salen en UTF-8.
        """
        command = ["exec", "-i", "-e", "PGCLIENTENCODING=UTF8", self.name, "psql", "-U", "postgres", "-d", DATABASE,
                   "-v", "ON_ERROR_STOP=1", "-X", "-A", "-t", "-q"]
        command += list(args)
        if sql is not None and stdin is not None:
            raise ValueError("psql: usa `sql` o `stdin`, no los dos")
        # `sql` también viaja por la entrada estándar y en bytes UTF-8, no con `-c`: los argumentos de línea de
        # comandos pasan por la página de códigos de Windows y un texto no ASCII llegaría corrupto.
        if sql is not None:
            stdin = sql
        data = stdin.encode("utf-8") if isinstance(stdin, str) else stdin
        return _docker(command, input_bytes=data)

    def query(self, sql: str) -> list[list[str]]:
        """Filas de una consulta como listas de textos (columnas separadas por `|`; NULL sale como cadena vacía)."""
        result = self.psql(sql)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"psql terminó con código {result.returncode}")
        return [line.split("|") for line in result.stdout.split("\n") if line != ""]

    def scalar(self, sql: str) -> str:
        """Primer valor de la única fila de una consulta."""
        rows = self.query(sql)
        if len(rows) != 1 or len(rows[0]) != 1:
            raise RuntimeError(f"se esperaba un único valor y llegó {rows!r}")
        return rows[0][0]

    def load_dataset(self, dataset: dict, tool=None) -> None:
        """Carga `dataset` con el script de `build_sql` de la herramienta, por la entrada estándar de `psql`.

        Sin `tool` usa la herramienta de `EVALUATION_DASHBOARD_TOOL` (o la del repositorio), la misma que usan las
        pruebas: así una copia mutada se carga con su propio `build_sql`. Falla si el script no se ejecuta entero.
        """
        script = (tool or load_tool()).build_sql(dataset)
        result = self.psql(stdin=script)
        if result.returncode != 0:
            raise RuntimeError(f"la carga del conjunto de datos falló: {result.stderr.strip()}")


_TOOL: dict = {}


def load_tool():
    """Módulo `tools/evaluation-dashboard.py` (o el de `EVALUATION_DASHBOARD_TOOL`), cargado una sola vez."""
    if "module" not in _TOOL:
        path = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
        spec = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_pg_helper", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _TOOL["module"] = module
    return _TOOL["module"]
