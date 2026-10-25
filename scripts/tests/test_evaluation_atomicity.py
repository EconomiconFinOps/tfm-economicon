"""Idempotencia y atomicidad de la carga del dashboard de evaluación en un PostgreSQL real (JUP-121, tarea 5.3).

El contrato de `load` (ADR-0022, `design.md` y la spec «Regeneración con un único comando») dice que regenerar los datos
es seguro: dos cargas dejan lo mismo, una carga que falla conserva la anterior y la carga no toca nada fuera del esquema
`evaluation`. Esta prueba lo comprueba con la CLI REAL (`python tools/evaluation-dashboard.py load --psql-command
"docker exec -i <contenedor> psql ..."`) contra el contenedor desechable de `evaluation_pg_helper` (la imagen exacta de
`postgres-pgvector`), con `GRANT`/contraseña aleatoria como en producción.

Cómo se mide «lo mismo». No se cuentan filas: se calcula una HUELLA md5 del contenido (cada fila convertida a texto, con
TODAS sus columnas, ordenada) de `evaluation.runs`, `evaluation.results` y de las dos vistas. Una celda distinta, una fila
de más o de menos o un orden alterado la cambian; una prueba lo demuestra cambiando una celda en una transacción que se
deshace. Junto a la huella se comparan los identificadores internos de las tablas (`oid`) y sus ACL, porque
`TRUNCATE` conserva ambos y `DROP`+`CREATE` no.

Los escenarios, uno por pregunta:

* (a) idempotencia: dos y tres cargas del MISMO conjunto, con la misma contraseña y con otra;
* (b) reemplazo: un conjunto distinto sustituye al anterior sin que sobreviva nada de él;
* (c) atomicidad, provocada de cinco maneras, con la huella antes y después idéntica y SIN que el script del rol llegue a
  ejecutarse (la contraseña anterior sigue valiendo y la nueva no): una fila que la base rechaza (`CHECK (false) NOT
  VALID` creada a mano), un `run_id` duplicado a mano, una conexión cortada justo tras el `TRUNCATE`, a mitad de un
  `INSERT` y justo antes del `COMMIT` (un `psql` falso que reenvía al `psql` real solo el principio del script y sale con
  error) y la comprobación de que `ON_ERROR_STOP` es lo que detiene la carga;
* (d) alcance: la carga solo crea objetos en `evaluation` (y el rol); no toca `public`, las tablas de embeddings ni otro
  esquema;
* (e) conjunto vacío (`--no-versioned` sin manifiestos): vacía las tablas y conserva esquema, vistas y rol;
* (f) manifiesto local: suma al versionado y una recarga sin él lo quita;
* (g) concurrencia: dos cargas simultáneas del mismo conjunto. LIMITACIÓN CONOCIDA y diferida: las transacciones de catálogo
  del script del rol y de las vistas actualizan las mismas tuplas y una de las dos cargas puede abortar (`tuple
  concurrently updated` o `deadlock detected`). Se fija lo seguro: al menos una termina bien, la otra bien o con un error
  limpio de `load`, el contenido es siempre el de una sola carga, el rol conserva permisos y una carga posterior funciona.

La herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
import textwrap
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (contenedor desechable compartido con 3.2, 3.3 y 5.x)

TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")

# Valores literales del contrato (no se leen de la herramienta para poder compararlos con ella).
READER = "grafana_evaluation_reader"
PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
DATABASE = "embeddings"
from evaluation_fixture_support import VERSIONED_RUNS, VERSIONED_RESULTS, LOAD_SUMMARY

VERSIONADO = {"runs": VERSIONED_RUNS, "results": VERSIONED_RESULTS}
RELACIONES_DE_EVALUATION = ["comparable_runs", "config_changes", "results", "results_pkey", "runs", "runs_pkey"]

class _Estado(dict):
    """Estado del módulo (rutas, IP del contenedor). Leer una clave que aún no existe monta antes el servidor, los
    manifiestos y los `psql` falsos (`server()`): así ninguna prueba depende del orden en que se ejecuten las clases."""

    def __missing__(self, clave):
        server()
        if clave not in self:
            raise KeyError(clave)
        return dict.__getitem__(self, clave)


_SERVER: dict = {}
_ESTADO = _Estado()


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo, creado de forma perezosa en el primer uso (como en las demás pruebas con PostgreSQL).

    Sin Docker lanza `SkipTest` (y recuerda el motivo); si el montaje falla, el error se repite en cada uso en lugar de
    levantar otro contenedor. Si algo falla después, el contenedor lo borra el `atexit` del ayudante aunque
    `tearDownModule` no llegue a ejecutarse."""
    if "failure" in _SERVER:
        raise unittest.SkipTest(_SERVER["failure"])
    if "error" in _SERVER:
        raise RuntimeError(_SERVER["error"])
    if "instance" not in _SERVER:
        try:
            _SERVER["instance"] = evaluation_pg_helper.PostgresServer()
        except unittest.SkipTest as skip:
            _SERVER["failure"] = str(skip)
            raise
        try:
            _preparar()
        except BaseException as error:
            _SERVER["error"] = f"no se pudo montar la prueba: {error}"
            raise
    return _SERVER["instance"]


# --- Conjuntos de datos locales ---------------------------------------------------------------------------------------


def informe(run_id: str, fuente: str, run_at: str, modelo: str, valor: float, extra: int = 0) -> dict:
    """Documento `rows-v1` de una ejecución con 2 + `extra` resultados."""
    resultados = [
        {"measure_type": "A", "grp": "accuracy", "metric_id": "ACC-2", "behavior": "all", "status": "measured", "value": valor,
         "unit": "tasa", "numerator": round(valor * 10), "denominator": 10, "judgment": "automatic"},
        {"measure_type": "A", "grp": "cases", "metric_id": "cases", "behavior": "all", "status": "pass", "count": 3,
         "unit": "casos", "denominator": 4, "judgment": "human"},
    ]
    for indice in range(extra):
        resultados.append({"measure_type": "A", "grp": "latency", "metric_id": "LAT-1", "behavior": f"etapa{indice}",
                           "status": "measured", "value": 100.5 + indice, "unit": "ms", "denominator": 4,
                           "judgment": "automatic"})
    return {
        "contract_version": 1,
        "run": {"run_id": run_id, "source": fuente, "run_at": run_at, "commit": "abc1234", "suite": "JUP-069",
                "suite_version": "1.0.0", "generation_model": modelo, "retrieval": {"top_k": 4}},
        "results": resultados,
    }


def escribir_manifiesto(directorio: Path, nombre: str, informes: list) -> Path:
    entradas = []
    for documento in informes:
        ruta = directorio / f"{documento['run']['run_id']}.json"
        ruta.write_text(json.dumps(documento), encoding="utf-8")
        entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": False})
    manifiesto = directorio / nombre
    manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
    return manifiesto


# Cuatro ejecuciones: dos comparables (misma configuración), y otras dos con un cambio de modelo (filas en las dos vistas).
LOCAL = [("atom-1", "JUP-071", "2026-10-10T10:00:00Z", "m1", 0.5, 1), ("atom-2", "JUP-071", "2026-10-11T10:00:00Z", "m1", 0.6, 0),
         ("atom-3", "JUP-072", "2026-10-12T10:00:00Z", "m1", 0.7, 2), ("atom-4", "JUP-072", "2026-10-13T10:00:00Z", "m2", 0.8, 0)]
OTRO = [("otro-1", "JUP-073", "2026-11-01T10:00:00Z", "m9", 0.1, 3), ("otro-2", "JUP-073", "2026-11-02T10:00:00Z", "m9", 0.2, 0)]
ID_LOCALES = sorted(fila[0] for fila in LOCAL)
ID_OTROS = sorted(fila[0] for fila in OTRO)

FIXTURES_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE public.control_datos (a integer PRIMARY KEY, texto text);
INSERT INTO public.control_datos VALUES (1, 'uno'), (2, 'dos'), (3, 'tres');
CREATE TABLE public.knowledge_documents (id serial PRIMARY KEY, title text NOT NULL);
INSERT INTO public.knowledge_documents (title) VALUES ('documento');
CREATE TABLE public.knowledge_embeddings (
  id serial PRIMARY KEY, document_id integer NOT NULL REFERENCES public.knowledge_documents (id), embedding vector(3) NOT NULL);
INSERT INTO public.knowledge_embeddings (document_id, embedding) VALUES (1, '[1,2,3]');
CREATE SCHEMA otro;
CREATE TABLE otro.tabla (a integer);
INSERT INTO otro.tabla VALUES (7);
"""

# `psql` FALSO que corta la conexión: lee todo el script, reenvía al `psql` real solo el principio (hasta el punto que
# diga el modo) y sale con código 2 como si la conexión se hubiera perdido. El `psql` real recibe un script sin `COMMIT`
# y, al acabar la entrada, la sesión termina: PostgreSQL deshace la transacción abierta.
FAKE_PSQL_CORTADO = textwrap.dedent('''\
    import re, subprocess, sys
    modo, comando = sys.argv[1], sys.argv[2:]
    datos = sys.stdin.buffer.read()
    if modo == "tras-truncate":
        corte = re.search(rb"TRUNCATE[^;]*;", datos).end()
    elif modo == "mitad-del-insert":
        # A mitad de la primera sentencia de resultados: ni siquiera llega a ser una sentencia completa.
        corte = datos.index(b"INSERT INTO evaluation.results") + 700
    elif modo == "antes-del-commit":
        # Todo el script de datos salvo el `COMMIT;` final de la transacción de datos (el primero del flujo).
        corte = datos.index(b"COMMIT;")
    else:
        raise SystemExit(f"modo desconocido: {modo}")
    subprocess.run(comando, input=datos[:corte], check=False)
    sys.stderr.write("psql: error: connection to server was lost\\n")
    raise SystemExit(2)
''')


def _preparar() -> None:
    """Montaje del módulo (una vez): manifiestos locales, `psql` falsos y las tablas ajenas que la carga no debe tocar."""
    holder = tempfile.TemporaryDirectory(prefix="evaluation-atomicity-")
    _SERVER["tmp"] = holder
    base = Path(holder.name).resolve()
    _ESTADO["base"] = base
    _ESTADO["local"] = escribir_manifiesto(base, "local.json", [informe(*fila[:5], extra=fila[5]) for fila in LOCAL])
    _ESTADO["otro"] = escribir_manifiesto(base, "otro.json", [informe(*fila[:5], extra=fila[5]) for fila in OTRO])
    (base / "fake_cortado.py").write_text(FAKE_PSQL_CORTADO, encoding="utf-8")
    montaje = server().psql(stdin=FIXTURES_SQL)
    if montaje.returncode != 0:
        raise RuntimeError(f"no se pudieron crear las tablas de prueba: {montaje.stderr.strip()}")


def tearDownModule() -> None:
    holder = _SERVER.pop("tmp", None)
    if holder is not None:
        holder.cleanup()
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


# --- La CLI real y la base ---------------------------------------------------------------------------------------------


def comando_psql() -> list:
    return ["docker", "exec", "-i", "-e", "PGCLIENTENCODING=UTF8", server().name, "psql", "-U", "postgres", "-d", DATABASE]


def lanzar(password: str, *, versionado: bool = True, manifiestos=(), psql: list | None = None) -> subprocess.Popen:
    """Arranca la CLI real `load` (sin esperar) con la contraseña en el entorno y `psql` = `psql` (por defecto, el real)."""
    orden = [sys.executable, str(TOOL_PATH), "load", "--psql-command", shlex.join(psql or comando_psql())]
    if not versionado:
        orden.append("--no-versioned")
    for manifiesto in manifiestos:
        orden += ["--manifest", str(manifiesto)]
    entorno = {**os.environ, PASSWORD_ENV: password, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    return subprocess.Popen(orden, env=entorno, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def terminar(proceso: subprocess.Popen, timeout: int = 180) -> subprocess.CompletedProcess:
    salida, errores = proceso.communicate(timeout=timeout)
    return subprocess.CompletedProcess(proceso.args, proceso.returncode, salida.decode("utf-8", "replace"),
                                       errores.decode("utf-8", "replace"))


def cargar(password: str, **opciones) -> subprocess.CompletedProcess:
    """Una carga con la CLI real; devuelve el resultado SIN comprobarlo (los escenarios de fallo lo esperan)."""
    return terminar(lanzar(password, **opciones))


def cargar_bien(password: str, **opciones) -> subprocess.CompletedProcess:
    resultado = cargar(password, **opciones)
    if resultado.returncode != 0:
        raise AssertionError(f"`load` falló con código {resultado.returncode}: {resultado.stderr.strip()}")
    return resultado


def reiniciar() -> None:
    """Deja la base sin esquema `evaluation` ni rol de Grafana (las tablas ajenas se conservan).

    Solo lo usan los escenarios que miran la PRIMERA carga o el estado previo (idempotencia, atomicidad y alcance). Los demás
    arrancan con su propia carga, que sustituye por completo lo que hubiera: reiniciar de nuevo solo añadiría una llamada a
    Docker (unos 0,3 s) sin cambiar lo que comprueban."""
    resultado = server().psql(stdin=(
        "DROP SCHEMA IF EXISTS evaluation CASCADE;\n"
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grafana_evaluation_reader') THEN "
        "DROP OWNED BY grafana_evaluation_reader; DROP ROLE grafana_evaluation_reader; END IF; END $$;\n"))
    if resultado.returncode != 0:
        raise RuntimeError(f"no se pudo reiniciar la base: {resultado.stderr.strip()}")


def json_de(sql: str):
    resultado = server().psql(sql)
    if resultado.returncode != 0:
        raise AssertionError(f"consulta fallida: {resultado.stderr.strip()}\n{sql}")
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


def _huella_de(tabla: str) -> str:
    return (f"(SELECT md5(COALESCE(string_agg(t::text, chr(10) ORDER BY t::text), '')) FROM {tabla} t)")


HUELLA_SQL = (
    "SELECT jsonb_build_object("
    f"'runs', {_huella_de('evaluation.runs')}, 'results', {_huella_de('evaluation.results')}, "
    f"'config_changes', {_huella_de('evaluation.config_changes')}, 'comparable_runs', {_huella_de('evaluation.comparable_runs')}, "
    "'n_runs', (SELECT count(*) FROM evaluation.runs), 'n_results', (SELECT count(*) FROM evaluation.results), "
    "'n_config_changes', (SELECT count(*) FROM evaluation.config_changes), "
    "'n_comparable_runs', (SELECT count(*) FROM evaluation.comparable_runs), "
    "'ids', (SELECT COALESCE(jsonb_agg(run_id ORDER BY run_id), '[]'::jsonb) FROM evaluation.runs))")


def huella() -> dict:
    """Huella md5 del contenido (todas las columnas) de las dos tablas y las dos vistas, más sus recuentos."""
    return json_de(HUELLA_SQL)


IDENTIDAD_SQL = (
    "SELECT jsonb_build_object("
    "'relaciones', (SELECT COALESCE(jsonb_agg(jsonb_build_array(c.relname, c.oid::bigint, c.relacl::text) ORDER BY c.relname), '[]'::jsonb) "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'evaluation'), "
    "'esquema', (SELECT jsonb_build_array(oid::bigint, nspacl::text) FROM pg_namespace WHERE nspname = 'evaluation'), "
    "'por_defecto', (SELECT COALESCE(jsonb_agg(defaclacl::text), '[]'::jsonb) FROM pg_default_acl), "
    "'rol', (SELECT oid::bigint FROM pg_roles WHERE rolname = 'grafana_evaluation_reader'))")


def identidad_y_permisos() -> dict:
    """`oid` y ACL de las relaciones de `evaluation` y del esquema: `TRUNCATE` los conserva, `DROP`+`CREATE` no."""
    return json_de(IDENTIDAD_SQL)


# Todo lo que hay fuera de `evaluation` y que una carga no debe tocar: esquemas, objetos de todos los esquemas (con su
# ACL), funciones, tipos, extensiones, roles y el CONTENIDO de las tablas ajenas.
FUERA_DE_EVALUATION_SQL = """
SELECT jsonb_build_object(
  'esquemas', (SELECT jsonb_agg(nspname ORDER BY nspname) FROM pg_namespace
      WHERE nspname <> 'evaluation' AND nspname NOT LIKE 'pg\\_temp\\_%' AND nspname NOT LIKE 'pg\\_toast\\_temp\\_%'),
  'objetos', (SELECT jsonb_agg(jsonb_build_array(n.nspname, c.relname, c.relkind, c.relacl::text) ORDER BY n.nspname, c.relname)
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname NOT IN ('evaluation', 'pg_toast') AND n.nspname NOT LIKE 'pg\\_temp\\_%' AND n.nspname NOT LIKE 'pg\\_toast\\_temp\\_%'),
  'funciones', (SELECT jsonb_agg(p.oid::regprocedure::text ORDER BY p.oid::regprocedure::text) FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')),
  'tipos', (SELECT jsonb_agg(t.oid::regtype::text ORDER BY t.oid::regtype::text) FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
      WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'evaluation', 'pg_toast') AND t.typtype <> 'c' AND t.typelem = 0),
  'extensiones', (SELECT jsonb_agg(extname ORDER BY extname) FROM pg_extension),
  'roles', (SELECT jsonb_agg(rolname ORDER BY rolname) FROM pg_roles WHERE rolname NOT LIKE 'pg\\_%'),
  'datos_ajenos', jsonb_build_object(
    'control_datos', (SELECT md5(string_agg(t::text, chr(10) ORDER BY t::text)) FROM public.control_datos t),
    'knowledge_documents', (SELECT md5(string_agg(t::text, chr(10) ORDER BY t::text)) FROM public.knowledge_documents t),
    'knowledge_embeddings', (SELECT md5(string_agg(t::text, chr(10) ORDER BY t::text)) FROM public.knowledge_embeddings t),
    'otro', (SELECT md5(string_agg(t::text, chr(10) ORDER BY t::text)) FROM otro.tabla t)))
"""


def fuera_de_evaluation() -> dict:
    return json_de(FUERA_DE_EVALUATION_SQL)


def foto() -> dict:
    """Huella del contenido, identidad y permisos de `evaluation` y estado de todo lo ajeno, con UNA sola llamada a Docker
    (cada `docker exec` cuesta unos 0,3 s y esta prueba las hace por decenas)."""
    return json_de(f"SELECT jsonb_build_object('huella', ({HUELLA_SQL}), 'identidad', ({IDENTIDAD_SQL}), "
                   f"'fuera', ({FUERA_DE_EVALUATION_SQL}))")


def relaciones_de(identidad: dict) -> list:
    """Nombres de las relaciones de `evaluation` (tablas, vistas y claves) según una `identidad_y_permisos()`."""
    return [fila[0] for fila in identidad["relaciones"]]


# --- Conexión como el rol (para saber qué contraseña vale) -----------------------------------------------------------


def direccion_del_contenedor() -> str:
    if "direccion" not in _ESTADO:
        proceso = subprocess.run(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}", server().name],
            capture_output=True, timeout=60, check=False)
        direcciones = proceso.stdout.decode("utf-8", "replace").split()
        if proceso.returncode != 0 or not direcciones:
            raise RuntimeError("no se pudo obtener la IP del contenedor")
        _ESTADO["direccion"] = direcciones[0]
    return _ESTADO["direccion"]


def entra_con(password: str) -> bool:
    """¿Puede el rol de Grafana iniciar sesión con esa contraseña? Conecta por la IP del contenedor: la imagen confía en el
    socket y en `127.0.0.1` y solo comprueba la contraseña en el resto (igual que `test_evaluation_load.py`). La contraseña
    viaja por `PGPASSWORD` en el entorno del cliente de Docker."""
    entorno = {clave: valor for clave, valor in os.environ.items() if clave != "PGPASSWORD"}
    entorno["PGPASSWORD"] = password
    proceso = subprocess.run(
        ["docker", "exec", "-i", "-e", "PGPASSWORD", server().name, "psql", "-h", direccion_del_contenedor(), "-U", READER,
         "-d", DATABASE, "-w", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1"],
        input=b"SELECT 1", capture_output=True, env=entorno, timeout=60, check=False)
    return proceso.returncode == 0


def a_la_vez(*llamadas) -> list:
    """Ejecuta varias llamadas independientes (consultas y conexiones, cada una un `docker exec` de unos 0,4 s) EN PARALELO y
    devuelve sus resultados en el mismo orden. Solo se usa con llamadas de LECTURA que no dependen unas de otras."""
    with ThreadPoolExecutor(max_workers=len(llamadas)) as grupo:
        return [futuro.result() for futuro in [grupo.submit(llamada) for llamada in llamadas]]


def entran_con(*contrasenas: str) -> list:
    """`entra_con` de varias contraseñas a la vez."""
    return a_la_vez(*[(lambda clave=clave: entra_con(clave)) for clave in contrasenas])


def contrasena() -> str:
    return secrets.token_urlsafe(24)


# --- (a) Idempotencia --------------------------------------------------------------------------------------------------


class IdempotenciaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reiniciar()
        cls.p1, cls.p2 = contrasena(), contrasena()
        cls.salidas = [cargar_bien(cls.p1)]
        primera = foto()
        cls.tras_la_primera, cls.identidad_primera = primera["huella"], primera["identidad"]
        cls.salidas.append(cargar_bien(cls.p1))
        cls.tras_la_segunda = huella()
        cls.salidas.append(cargar_bien(cls.p2))  # la tercera, con otra contraseña
        tercera = foto()
        cls.tras_la_tercera, cls.identidad_tercera = tercera["huella"], tercera["identidad"]

    def test_la_primera_carga_dejo_el_conjunto_versionado_completo(self):
        # Precondición de lo demás: «idéntico» tiene que ser sobre algo (12 ejecuciones y 647 resultados, no una base vacía).
        for salida in self.salidas:
            self.assertEqual(salida.stdout, LOAD_SUMMARY)
        self.assertEqual((self.tras_la_primera["n_runs"], self.tras_la_primera["n_results"]), (VERSIONED_RUNS, VERSIONED_RESULTS))
        # El versionado tiene tres cambios anotados desde JUP-133: modelo servido de JUP-071, banco con chat real frente a plantilla y ventana de coste.
        # Las dos proyecciones JUP-133 añaden un cambio de protocolo, no una serie comparable.
        self.assertEqual(self.tras_la_primera["n_config_changes"], 6)
        vacia = json_de(f"SELECT jsonb_build_object('h', md5(''))")["h"]
        self.assertNotEqual(self.tras_la_primera["runs"], vacia)
        self.assertNotEqual(self.tras_la_primera["results"], vacia)

    def test_dos_y_tres_cargas_del_mismo_conjunto_dejan_el_mismo_contenido(self):
        self.assertEqual(self.tras_la_segunda, self.tras_la_primera)
        self.assertEqual(self.tras_la_tercera, self.tras_la_primera)

    def test_las_tablas_se_vacian_y_se_llenan_sin_recrearse(self):
        # `TRUNCATE` y no `DROP`: los identificadores internos y las ACL de tablas, vistas y esquema son los mismos.
        self.assertEqual(self.identidad_tercera, self.identidad_primera)
        self.assertEqual([fila[0] for fila in self.identidad_primera["relaciones"]], RELACIONES_DE_EVALUATION)
        # Las dos tablas y las dos vistas llevan la ACL del rol de Grafana (los índices de las claves no tienen ACL).
        con_acl = [fila[0] for fila in self.identidad_primera["relaciones"] if fila[2]]
        self.assertEqual(con_acl, ["comparable_runs", "config_changes", "results", "runs"])

    def test_la_huella_cambia_si_cambia_cualquier_celda_o_fila(self):
        # Guarda de la propia medida: una huella que no notara un cambio daría por buenas cargas distintas. Cada variante
        # modifica una columna en una transacción que se DESHACE y la huella debe diferir de la original.
        variantes = {
            "results.value": "UPDATE evaluation.results SET value = value + 1 WHERE ctid = (SELECT ctid FROM evaluation.results WHERE value IS NOT NULL LIMIT 1)",
            "results.numerator": "UPDATE evaluation.results SET numerator = numerator + 1 WHERE ctid = (SELECT ctid FROM evaluation.results WHERE numerator IS NOT NULL LIMIT 1)",
            "results.selected": "UPDATE evaluation.results SET selected = NOT selected WHERE ctid = (SELECT ctid FROM evaluation.results LIMIT 1)",
            "results.unit": "UPDATE evaluation.results SET unit = unit || 'x' WHERE ctid = (SELECT ctid FROM evaluation.results LIMIT 1)",
            "results.ci_high": "UPDATE evaluation.results SET ci_high = ci_high + 0.5 WHERE ctid = (SELECT ctid FROM evaluation.results WHERE ci_high IS NOT NULL LIMIT 1)",
            "runs.run_at": "UPDATE evaluation.runs SET run_at = run_at + interval '1 second' WHERE run_at IS NOT NULL",
            "runs.retrieval": "UPDATE evaluation.runs SET retrieval = '{\"top_k\": 99}' WHERE retrieval IS NOT NULL",
            "runs.non_real_reasons": "UPDATE evaluation.runs SET non_real_reasons = ARRAY['x'] WHERE cardinality(non_real_reasons) = 0",
            "una fila de menos": "DELETE FROM evaluation.results WHERE ctid = (SELECT ctid FROM evaluation.results LIMIT 1)",
        }
        guion = []
        for sentencia in variantes.values():
            guion.append(f"BEGIN;\n{sentencia};\n{HUELLA_SQL};\nROLLBACK;")
        resultado = server().psql(stdin="\n".join(guion))
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        salidas = [json.loads(linea) for linea in resultado.stdout.split("\n") if linea.strip().startswith("{")]
        self.assertEqual(len(salidas), len(variantes))
        for (nombre, _), cambiada in zip(variantes.items(), salidas):
            with self.subTest(variante=nombre):
                self.assertNotEqual(cambiada, self.tras_la_tercera)
        self.assertEqual(huella(), self.tras_la_tercera, "las transacciones de prueba se deshicieron")

    def test_la_carga_de_datos_por_si_sola_conserva_identidad_y_permisos(self):
        # El script de datos (`build_sql`, sin el del rol) usa `TRUNCATE` y `CREATE OR REPLACE VIEW`: no debe quitar ni los
        # permisos ni los identificadores de lo ya creado. Con un `DROP` de esquema, de tabla o de vista se perderían.
        herramienta = evaluation_pg_helper.load_tool()
        guion = herramienta.build_sql(herramienta.build_dataset([herramienta.DEFAULT_MANIFEST]))
        resultado = server().psql(stdin=guion)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        actual = foto()
        self.assertEqual(actual["identidad"], self.identidad_tercera)
        self.assertEqual(actual["huella"], self.tras_la_tercera)


# --- (b) Reemplazo ---------------------------------------------------------------------------------------------------------


class ReemplazoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = contrasena()
        cargar_bien(cls.p, versionado=False, manifiestos=[_ESTADO["local"]])
        cls.local_en_limpio = huella()
        cargar_bien(cls.p, versionado=True)  # el versionado sustituye al local
        cls.versionado_tras_local = huella()
        cargar_bien(cls.p, versionado=False, manifiestos=[_ESTADO["local"]])  # y vuelta al local
        cls.local_tras_versionado = huella()
        cargar_bien(cls.p, versionado=False, manifiestos=[_ESTADO["otro"]])  # un tercer conjunto, distinto de los dos
        cls.otro = {"huella": huella(),
                    "sobrantes": json_de(
                        "SELECT jsonb_build_object('de_runs', (SELECT count(*) FROM evaluation.runs WHERE run_id NOT LIKE 'otro-%'), "
                        "'de_results', (SELECT count(*) FROM evaluation.results WHERE run_id NOT LIKE 'otro-%'))")}

    def test_el_conjunto_versionado_sustituye_por_completo_al_local(self):
        self.assertEqual(self.versionado_tras_local["n_runs"], VERSIONADO["runs"])
        self.assertEqual(self.versionado_tras_local["n_results"], VERSIONADO["results"])
        self.assertEqual(sorted(set(self.versionado_tras_local["ids"]) & set(ID_LOCALES)), [])

    def test_tras_ir_y_volver_el_contenido_es_el_de_cargar_ese_conjunto_en_limpio(self):
        # Nada de la historia sobrevive: el estado depende solo del último conjunto, no de lo que hubiera antes.
        self.assertEqual(self.local_en_limpio["n_runs"], len(LOCAL))
        self.assertEqual(self.local_tras_versionado["ids"], ID_LOCALES)
        self.assertEqual(self.local_tras_versionado, self.local_en_limpio)

    def test_un_tercer_conjunto_no_deja_filas_de_los_anteriores(self):
        self.assertEqual(self.otro["huella"]["ids"], ID_OTROS)
        self.assertEqual(self.otro["sobrantes"], {"de_runs": 0, "de_results": 0})
        self.assertNotEqual(self.otro["huella"], self.local_en_limpio)
        self.assertEqual(self.otro["huella"]["n_runs"], len(OTRO))


# --- (c) Atomicidad ------------------------------------------------------------------------------------------------------------


class AtomicidadTests(unittest.TestCase):
    """Cada prueba provoca un fallo a mitad de una carga y comprueba que lo anterior queda EXACTAMENTE como estaba."""

    @classmethod
    def setUpClass(cls):
        reiniciar()
        cls.anterior = contrasena()
        cargar_bien(cls.anterior)
        anterior = foto()
        cls.huella_anterior, cls.identidad_anterior, cls.fuera_anterior = anterior["huella"], anterior["identidad"], anterior["fuera"]
        # Precondición: la contraseña anterior vale (y la de los intentos no valdrá).
        assert entra_con(cls.anterior)

    def comprobar_intacto(self, nueva: str) -> None:
        """La huella (todas las columnas, tablas y vistas), identidad, ACL y lo ajeno son los de antes, y el script del rol
        no llegó a ejecutarse: la contraseña anterior sigue valiendo y la nueva no."""
        actual, vale_la_anterior, vale_la_nueva = a_la_vez(foto, lambda: entra_con(self.anterior), lambda: entra_con(nueva))
        self.assertEqual(actual["huella"], self.huella_anterior)
        self.assertEqual(actual["identidad"], self.identidad_anterior)
        self.assertEqual(actual["fuera"], self.fuera_anterior)
        self.assertTrue(vale_la_anterior, "la contraseña anterior dejó de valer: el script del rol se ejecutó")
        self.assertFalse(vale_la_nueva, "la contraseña nueva ya vale: el script del rol se ejecutó pese al fallo")

    def comprobar_fallo_de_carga(self, resultado: subprocess.CompletedProcess, codigo_de_psql: int) -> None:
        self.assertEqual(resultado.returncode, 1, resultado.stdout)
        self.assertEqual(resultado.stdout, "", "una carga fallida no escribe el resumen")
        self.assertTrue(resultado.stderr.startswith(f"error: load: psql terminó con código {codigo_de_psql}"), resultado.stderr)

    def test_una_fila_que_la_base_rechaza_deja_todo_como_estaba(self):
        # Una restricción que ninguna fila nueva cumple (`NOT VALID`: no revisa las ya cargadas). La carga vacía las tablas,
        # inserta las ejecuciones y falla al insertar los resultados: justo «a mitad» y con un `TRUNCATE` ya hecho.
        self.assertEqual(server().psql("ALTER TABLE evaluation.results ADD CONSTRAINT zz_bloqueo CHECK (false) NOT VALID").returncode, 0)
        self.addCleanup(server().psql, "ALTER TABLE evaluation.results DROP CONSTRAINT IF EXISTS zz_bloqueo")
        nueva = contrasena()
        resultado = cargar(nueva, versionado=False, manifiestos=[_ESTADO["local"]])
        self.comprobar_fallo_de_carga(resultado, 3)
        self.assertIn("zz_bloqueo", server().psql("SELECT conname FROM pg_constraint WHERE conname = 'zz_bloqueo'").stdout)
        # `ON_ERROR_STOP` es lo que detiene la carga en el primer error: sin él `psql` seguiría con el script del rol (y
        # rotaría la contraseña aunque los datos no se cargaran) y saldría con código 0. Se exige el código de error y, en
        # `comprobar_intacto`, que la contraseña anterior siga vigente y la nueva no (la contraprueba, más abajo, demuestra
        # que sin `ON_ERROR_STOP` el script del rol SÍ se ejecutaría).
        self.assertEqual(server().psql("ALTER TABLE evaluation.results DROP CONSTRAINT zz_bloqueo").returncode, 0)
        self.comprobar_intacto(nueva)

    def test_un_run_id_duplicado_a_mano_deja_todo_como_estaba(self):
        # Se parte del script real de datos y se DUPLICA a mano la primera ejecución: la clave primaria rechaza la segunda
        # tupla cuando el `TRUNCATE` ya se ejecutó y la mitad del script ya corrió.
        herramienta = evaluation_pg_helper.load_tool()
        script = herramienta.build_sql(herramienta.build_dataset([_ESTADO["local"]], root=_ESTADO["base"]))
        lineas = script.split("\n")
        primera = next(i for i, linea in enumerate(lineas) if linea.startswith("  ('atom-1'"))
        self.assertTrue(lineas[primera].endswith(","), "la primera ejecución no es la última tupla de su INSERT")
        lineas.insert(primera + 1, lineas[primera])
        resultado = server().psql(stdin="\n".join(lineas))
        self.assertNotEqual(resultado.returncode, 0, "el script con un run_id duplicado se ejecutó")
        self.assertIn("duplicate key", resultado.stderr)
        self.comprobar_intacto(contrasena())

    def test_un_psql_que_se_cae_justo_tras_el_truncate_deja_todo_como_estaba(self):
        self._conexion_cortada("tras-truncate")

    def test_un_psql_que_se_cae_a_mitad_de_un_insert_deja_todo_como_estaba(self):
        self._conexion_cortada("mitad-del-insert")

    def test_un_psql_que_se_cae_justo_antes_del_commit_deja_todo_como_estaba(self):
        # Lo más exigente: se ejecutó todo el script de datos salvo el `COMMIT;`. Sin él nada es definitivo.
        self._conexion_cortada("antes-del-commit")

    def _conexion_cortada(self, modo: str) -> None:
        fake = (_ESTADO["base"] / "fake_cortado.py").as_posix()
        psql = [Path(sys.executable).as_posix(), fake, modo] + comando_psql()
        nueva = contrasena()
        resultado = cargar(nueva, versionado=False, manifiestos=[_ESTADO["local"]], psql=psql)
        self.comprobar_fallo_de_carga(resultado, 2)
        self.assertIn("connection to server was lost", resultado.stderr)
        self.comprobar_intacto(nueva)

    def test_el_script_cortado_si_hace_el_trabajo_dentro_de_su_transaccion(self):
        # Guarda anti-vacío de las tres pruebas de conexión cortada: el script truncado ANTES del `COMMIT;` de verdad vacía
        # y llena las tablas dentro de su transacción (se ve en la propia sesión); si lo anterior sobrevive es porque la
        # transacción nunca se confirmó, no porque el script no hiciera nada.
        herramienta = evaluation_pg_helper.load_tool()
        script = herramienta.build_sql(herramienta.build_dataset([_ESTADO["local"]], root=_ESTADO["base"]))
        antes_del_commit = script[:script.index("COMMIT;")]
        resultado = server().psql(
            stdin=antes_del_commit + "\nSELECT (SELECT count(*) FROM evaluation.runs) || ',' || (SELECT count(*) FROM evaluation.results);\n")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.strip(), f"{len(LOCAL)},{sum(2 + fila[5] for fila in LOCAL)}")
        # Y al terminar la sesión sin `COMMIT` lo anterior sigue entero.
        self.assertEqual(huella(), self.huella_anterior)

    def test_sin_on_error_stop_la_carga_fallida_seguiria_con_el_script_del_rol(self):
        # Contraprueba de la anterior: demuestra que el escenario de fallo ES capaz de llegar al script del rol si nada lo
        # detiene (el mismo flujo con `ON_ERROR_STOP=0`). Se hace en una sesión propia con el SQL real y se DESHACE a mano.
        herramienta = evaluation_pg_helper.load_tool()
        datos = herramienta.build_sql(herramienta.build_dataset([_ESTADO["local"]], root=_ESTADO["base"]))
        nueva = contrasena()
        flujo = datos + "\n" + herramienta.build_role_sql(nueva)
        self.assertEqual(server().psql("ALTER TABLE evaluation.results ADD CONSTRAINT zz_bloqueo CHECK (false) NOT VALID").returncode, 0)
        try:
            resultado = server().psql(stdin=flujo, args=["-v", "ON_ERROR_STOP=0"])  # el último `-v` manda
            self.assertEqual(resultado.returncode, 0, "sin ON_ERROR_STOP psql sale con 0 pese al error")
            self.assertIn("zz_bloqueo", resultado.stderr)
            self.assertTrue(entra_con(nueva), "sin ON_ERROR_STOP el script del rol sí se ejecuta tras el fallo")
        finally:
            server().psql("ALTER TABLE evaluation.results DROP CONSTRAINT IF EXISTS zz_bloqueo")
            # Se restablece el estado del resto de las pruebas de la clase: la contraseña anterior (los datos no cambiaron,
            # el `COMMIT` tras el error deshizo la transacción) con el propio script del rol.
            server().psql(stdin=herramienta.build_role_sql(self.anterior))
        self.assertEqual(huella(), self.huella_anterior)


# --- (d) La carga no toca nada fuera de `evaluation` --------------------------------------------------------------------


class AlcanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reiniciar()
        cls.antes = fuera_de_evaluation()
        cls.password = contrasena()
        cargar_bien(cls.password)
        primera = foto()
        cls.tras_la_primera, cls.relaciones = primera["fuera"], relaciones_de(primera["identidad"])
        cargar_bien(contrasena(), versionado=False, manifiestos=[_ESTADO["otro"]])
        otra = foto()
        cls.tras_otra_carga, cls.tras_otra_carga_relaciones = otra["fuera"], relaciones_de(otra["identidad"])

    def test_la_primera_carga_solo_crea_el_rol_y_objetos_de_evaluation(self):
        # Las tablas de `public` (incluidas las de embeddings) y de otros esquemas, sus ACL, las funciones, los tipos y las
        # extensiones son los de antes; lo único nuevo fuera del esquema es el rol de Grafana.
        esperado = {**self.antes, "roles": sorted(self.antes["roles"] + [READER])}
        self.assertEqual(self.tras_la_primera, esperado)

    def test_los_objetos_de_evaluation_son_exactamente_las_dos_tablas_las_dos_vistas_y_sus_claves(self):
        self.assertEqual(self.relaciones, RELACIONES_DE_EVALUATION)
        self.assertEqual(self.tras_otra_carga_relaciones, RELACIONES_DE_EVALUATION)

    def test_cargar_otro_conjunto_tampoco_toca_lo_ajeno(self):
        self.assertEqual(self.tras_otra_carga, self.tras_la_primera)

    def test_los_datos_ajenos_siguen_ahi(self):
        # Guarda anti-vacío: las tablas de control tienen filas y su huella existe (no es NULL de una tabla vacía).
        datos = self.tras_la_primera["datos_ajenos"]
        self.assertEqual(set(datos), {"control_datos", "knowledge_documents", "knowledge_embeddings", "otro"})
        self.assertTrue(all(valor for valor in datos.values()), datos)
        self.assertEqual(server().scalar("SELECT count(*) FROM public.control_datos"), "3")
        self.assertEqual(server().scalar("SELECT count(*) FROM public.knowledge_embeddings"), "1")


# --- (e) Conjunto vacío ------------------------------------------------------------------------------------------------------


class ConjuntoVacioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p1, cls.p2 = contrasena(), contrasena()
        cargar_bien(cls.p1)
        cls.lleno = identidad_y_permisos()
        cls.salida = cargar(cls.p2, versionado=False)
        privilegios = (
            f"SELECT jsonb_build_object('lectura', (SELECT jsonb_agg(c.relname ORDER BY c.relname) FROM pg_class c "
            f"JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'evaluation' AND c.relkind IN ('r', 'v') "
            f"AND has_table_privilege('{READER}', c.oid, 'SELECT')), 'escritura', (SELECT count(*) FROM pg_class c "
            f"JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'evaluation' AND c.relkind IN ('r', 'v') "
            f"AND (has_table_privilege('{READER}', c.oid, 'INSERT') OR has_table_privilege('{READER}', c.oid, 'UPDATE') "
            f"OR has_table_privilege('{READER}', c.oid, 'DELETE') OR has_table_privilege('{READER}', c.oid, 'TRUNCATE'))))")
        vacio, cls.entra_con_la_nueva, cls.entra_con_la_vieja, cls.privilegios = a_la_vez(
            foto, lambda: entra_con(cls.p2), lambda: entra_con(cls.p1), lambda: json_de(privilegios))
        cls.vacio, cls.identidad = vacio["huella"], vacio["identidad"]
        cls.relaciones = relaciones_de(cls.identidad)

    def test_la_carga_vacia_vacia_las_tablas(self):
        self.assertEqual((self.salida.returncode, self.salida.stdout), (0, "0 ejecuciones y 0 resultados cargados\n"), self.salida.stderr)
        self.assertEqual(self.vacio["n_runs"], 0)
        self.assertEqual(self.vacio["n_results"], 0)
        self.assertEqual((self.vacio["n_config_changes"], self.vacio["n_comparable_runs"]), (0, 0))

    def test_conserva_el_esquema_las_tablas_las_vistas_y_sus_identificadores(self):
        self.assertEqual(self.relaciones, RELACIONES_DE_EVALUATION)
        self.assertEqual(self.identidad, self.lleno)

    def test_conserva_el_rol_con_la_contrasena_nueva_y_sus_permisos_de_lectura(self):
        self.assertTrue(self.entra_con_la_nueva)
        self.assertFalse(self.entra_con_la_vieja)
        self.assertEqual(self.privilegios, {"lectura": ["comparable_runs", "config_changes", "results", "runs"], "escritura": 0})

    def test_una_carga_posterior_con_datos_recupera_el_contenido(self):
        cargar_bien(self.p2)
        recuperado = huella()
        self.assertEqual((recuperado["n_runs"], recuperado["n_results"]), (VERSIONADO["runs"], VERSIONADO["results"]))
        self.assertTrue(entra_con(self.p2))


# --- (f) Manifiesto local -----------------------------------------------------------------------------------------------------


class ManifiestoLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = contrasena()
        cargar_bien(cls.p)
        cls.solo_versionado = huella()
        cls.salida_con_local = cargar_bien(cls.p, manifiestos=[_ESTADO["local"]])
        cls.con_local = huella()
        cargar_bien(cls.p)
        cls.sin_local = huella()

    def test_la_carga_con_un_manifiesto_local_suma_al_versionado(self):
        resultados_locales = sum(2 + fila[5] for fila in LOCAL)
        self.assertEqual(self.salida_con_local.stdout,
                         f"{VERSIONADO['runs'] + len(LOCAL)} ejecuciones y {VERSIONADO['results'] + resultados_locales} resultados cargados\n")
        self.assertEqual(self.con_local["n_runs"], VERSIONADO["runs"] + len(LOCAL))
        self.assertEqual(self.con_local["n_results"], VERSIONADO["results"] + resultados_locales)
        self.assertEqual(sorted(set(self.con_local["ids"]) & set(ID_LOCALES)), ID_LOCALES)
        self.assertNotEqual(self.con_local, self.solo_versionado)
        # Las vistas notan las ejecuciones nuevas (cambio de modelo y de batería entre consecutivas y dos comparables).
        self.assertEqual((self.con_local["n_config_changes"], self.con_local["n_comparable_runs"]), (8, 8))

    def test_una_recarga_sin_el_manifiesto_local_lo_quita_y_deja_el_contenido_versionado_original(self):
        self.assertEqual(sorted(set(self.sin_local["ids"]) & set(ID_LOCALES)), [])
        self.assertEqual(self.sin_local, self.solo_versionado)


# --- (g) Concurrencia -----------------------------------------------------------------------------------------------------------

# Motivos con los que una de dos cargas simultáneas puede fallar. `load` cita solo la ÚLTIMA línea del error de `psql`, y para
# estos dos errores esa línea es una de cuatro: el mensaje, su `CONTEXT` o el `HINT` que acompaña a un interbloqueo.
MOTIVOS_ESPERADOS = re.compile(
    r"ERROR:\s+tuple concurrently updated$"
    r"|ERROR:\s+deadlock detected$"
    r"|HINT:\s+See server log for query details\.$"
    r'|CONTEXT:\s+while (?:updating|locking) tuple \(\d+,\d+\) in relation "pg_\w+"$')
RONDAS_DE_CONCURRENCIA = 6


class ConcurrenciaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = contrasena()
        cargar_bien(cls.p)
        una_sola = foto()
        cls.una_sola_carga, cls.identidad = una_sola["huella"], una_sola["identidad"]

    def test_dos_cargas_simultaneas_dejan_el_contenido_de_una_sola_y_a_lo_sumo_una_falla_limpiamente(self):
        """Dos `load` del mismo conjunto lanzados A LA VEZ: lo que ocurre de verdad y lo que se exige.

        LIMITACIÓN CONOCIDA (hallazgo diferido, no es un defecto de esta prueba). La carga son DOS transacciones: la de datos
        (`TRUNCATE` + inserciones + `CREATE OR REPLACE VIEW`) y la del rol (`ALTER ROLE`, `GRANT`, `ALTER DEFAULT
        PRIVILEGES`). El `TRUNCATE` serializa solo la de datos; la del rol de una carga corre a la vez que la de datos de la
        otra, y ambas actualizan las MISMAS tuplas del catálogo (`pg_class` por las ACL de tablas y vistas, `pg_authid`).
        PostgreSQL no bloquea esas tuplas por fila y una de las dos sentencias aborta con `tuple concurrently updated` o
        con `deadlock detected`. Reproducción mínima: dos `psql` a la vez, cada uno con `build_sql` + `build_role_sql` sobre
        la misma base; en 28 de 30 rondas una de las dos falla (la mitad con cada error). El endurecimiento propuesto,
        anteponer `SELECT pg_advisory_lock(<clave>);` a la entrada de `psql` (bloqueo de sesión que se libera al salir), queda
        DIFERIDO: cambiaría el texto exacto que fijan las pruebas de `load` y del SQL. Con él las dos cargas se serializan.

        Por eso esta prueba fija el comportamiento REAL y SEGURO, sin depender de que falle una vez concreta. En cada una de
        varias rondas: (1) al menos una carga termina con código 0 (una sola se aborta por una colisión: la otra sigue y,
        cuando el aborto llega, ya no queda nadie con quien colisionar); (2) la otra termina bien o con un error LIMPIO de
        `load` (código 1, `error: load: psql terminó con código N`, sin salida estándar, sin traza ni contraseña) por uno de
        los motivos esperados; cualquier otro motivo hace fallar la prueba; (3) el contenido es EXACTAMENTE el de una sola
        carga (huella md5 de todas las columnas, sin duplicados ni filas a medias), el rol conserva su identidad y sus ACL y
        entra con la contraseña de una carga que terminó bien, y no con la de la que falló (su transacción del rol no se
        confirma). Al final, (4) una carga sin concurrencia termina bien y deja el contenido esperado.
        """
        resumen = LOAD_SUMMARY
        for ronda in range(RONDAS_DE_CONCURRENCIA):
            contrasenas = [contrasena(), contrasena()]
            procesos = [lanzar(clave) for clave in contrasenas]
            salidas = [terminar(proceso) for proceso in procesos]
            con_ronda = f"ronda {ronda}"
            buenas = [i for i, salida in enumerate(salidas) if salida.returncode == 0]
            self.assertGreaterEqual(len(buenas), 1, f"{con_ronda}: las dos cargas fallaron: {[s.stderr for s in salidas]}")
            for i, salida in enumerate(salidas):
                with self.subTest(ronda=ronda, carga=i):
                    self.assertNotIn("Traceback", salida.stderr)
                    self.assertNotIn(contrasenas[i], salida.stderr + salida.stdout)
                    if salida.returncode == 0:
                        self.assertEqual((salida.stdout, salida.stderr), (resumen, ""))
                        continue
                    self.assertEqual(salida.returncode, 1, salida.stderr)
                    self.assertEqual(salida.stdout, "", "una carga fallida no escribe el resumen")
                    motivo = re.fullmatch(r"error: load: psql terminó con código \d+: (.+?)\s*", salida.stderr)
                    self.assertIsNotNone(motivo, f"{con_ronda}: el error no es el de `load`: {salida.stderr!r}")
                    self.assertRegex(motivo.group(1), MOTIVOS_ESPERADOS, f"{con_ronda}: motivo inesperado")
            # Lo que quedó: contenido, identidad y permisos, y quién puede entrar, con las tres lecturas a la vez.
            actual, *entran = a_la_vez(foto, *[(lambda clave=clave: entra_con(clave)) for clave in contrasenas])
            self.assertEqual(actual["huella"], self.una_sola_carga, f"{con_ronda}: el contenido no es el de una sola carga")
            self.assertEqual(actual["identidad"], self.identidad, f"{con_ronda}: cambió la identidad o los permisos")
            for i, entra in enumerate(entran):
                if i not in buenas:
                    self.assertFalse(entra, f"{con_ronda}: vale la contraseña de la carga que falló")
            self.assertTrue(any(entran[i] for i in buenas), f"{con_ronda}: no vale la contraseña de ninguna carga correcta")
        # (4) Sin concurrencia, la carga siguiente es normal.
        final = contrasena()
        self.assertEqual(cargar_bien(final).stdout, resumen)
        tras, vale = a_la_vez(foto, lambda: entra_con(final))
        self.assertEqual(tras["huella"], self.una_sola_carga)
        self.assertEqual(tras["identidad"], self.identidad)
        self.assertTrue(vale)


if __name__ == "__main__":
    unittest.main()
