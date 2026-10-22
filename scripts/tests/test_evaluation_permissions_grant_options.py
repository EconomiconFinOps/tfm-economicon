"""El rol de Grafana no puede reconceder nada: ni USAGE, ni CONNECT, ni nada (JUP-121, tarea 5.2, hallazgo M2 del QA).

`test_evaluation_permissions.py` comprueba que los `SELECT` sobre las cuatro relaciones de `evaluation` no son
reconcedibles (`is_grantable`), pero no que lo sean `USAGE` del esquema ni `CONNECT` de la base. Un `GRANT ... WITH GRANT
OPTION` en cualquiera de ellos (o en un privilegio por defecto, o en un esquema ajeno como `public`) dejaría al rol
repartir su acceso a otros roles, algo que la spec «Acceso de Grafana de solo lectura» no permite. Este fichero cierra
ese hueco de dos maneras que se refuerzan, contra un PostgreSQL real cargado con la CLI real `load`:

* INTROSPECCIÓN: `aclexplode` sobre TODOS los catálogos con ACL (relaciones, columnas, esquemas, bases, funciones,
  lenguajes, FDW, servidores foráneos, tablespaces, tipos, privilegios por defecto, objetos grandes y parámetros). Ninguna
  entrada del rol es reconcedible y ninguna ACL la ha concedido el propio rol (`grantor`). (PostgreSQL no permite dar la
  opción de reconceder a PUBLIC: `grant options can only be granted to roles`; por eso solo se mira al rol.) Una
  guarda anti-vacío exige que el rol SÍ aparezca en esas ACL con sus concesiones reales: una consulta que no viera nada
  daría «verde» sin demostrar nada.
* OPERACIONES conectado COMO el rol (contra la IP del contenedor, con `PGPASSWORD` por el entorno del cliente Docker):
  `GRANT USAGE ON SCHEMA evaluation`, `GRANT SELECT ON evaluation.runs` y `GRANT CONNECT ON DATABASE embeddings` a PUBLIC.
  PostgreSQL puede responder con error o solo con un `WARNING: no privileges were granted` y código 0, así que no basta
  con mirar la salida: se compara el estado real de las ACL antes y después.

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
import unittest
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
OID_ROL = f"(SELECT oid FROM pg_roles WHERE rolname = '{READER}')"
# Un rechazo de PostgreSQL por falta de privilegios con alguno de sus mensajes habituales.
DENEGADO = re.compile(r"permission denied|must be owner|must be superuser|must have privileges|only roles with", re.I)
SIN_CONCESION = "no privileges were granted"

_SERVER: dict = {}
_ESTADO: dict = {}


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo, creado de forma perezosa en el primer uso (como en las demás pruebas con PostgreSQL).

    Sin Docker lanza `SkipTest`; si el montaje falla, el error se repite en cada uso en lugar de levantar otro contenedor.
    Si algo falla después, el contenedor lo borra el `atexit` del ayudante aunque `tearDownModule` no llegue a ejecutarse."""
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


# --- Montaje ---------------------------------------------------------------------------------------------------------

# Objetos ajenos a `evaluation` de cada clase con ACL (esquema, tabla, función y tipo en `public`): sin ellos un `GRANT ... ON ALL
# FUNCTIONS IN SCHEMA public ... WITH GRANT OPTION` no tendría nada que alcanzar y el barrido de ACL no vería la diferencia.
FIXTURES_SQL = """
CREATE SCHEMA otro;
CREATE TABLE otro.tabla (a integer);
CREATE TABLE public.documentos (id serial PRIMARY KEY, titulo text);
CREATE FUNCTION public.funcion_ajena() RETURNS integer LANGUAGE sql AS 'SELECT 1';
CREATE TYPE public.tipo_ajeno AS ENUM ('a', 'b');
"""


def informe(run_id: str, fuente: str, run_at: str) -> dict:
    return {
        "contract_version": 1,
        "run": {"run_id": run_id, "source": fuente, "run_at": run_at, "commit": "abc1234", "suite": "JUP-069",
                "suite_version": "1.0.0", "generation_model": "m1", "retrieval": {"top_k": 4}},
        "results": [{"measure_type": "A", "grp": "accuracy", "metric_id": "ACC-2", "behavior": "all",
                     "status": "measured", "value": 0.5, "unit": "tasa", "numerator": 5, "denominator": 10,
                     "judgment": "automatic"}],
    }


def escribir_manifiesto_local(directorio: Path) -> Path:
    """Dos ejecuciones locales además de las versionadas: las tablas tienen filas y las vistas no están vacías de contexto."""
    entradas = []
    for run_id, fuente, dia in (("opc-a1", "JUP-071", "10"), ("opc-a2", "JUP-071", "11")):
        ruta = directorio / f"{run_id}.json"
        ruta.write_text(json.dumps(informe(run_id, fuente, f"2026-10-{dia}T10:00:00Z")), encoding="utf-8")
        entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": False})
    manifiesto = directorio / "local.json"
    manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
    return manifiesto


def comando_psql() -> str:
    return shlex.join(["docker", "exec", "-i", "-e", "PGCLIENTENCODING=UTF8", server().name, "psql", "-U", "postgres",
                       "-d", DATABASE])


def cargar(password: str) -> subprocess.CompletedProcess:
    """Ejecuta la CLI real `load` con la contraseña en el entorno (no en los argumentos) y comprueba que termina bien."""
    entorno = {**os.environ, PASSWORD_ENV: password, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    proceso = subprocess.run(
        [sys.executable, str(TOOL_PATH), "load", "--psql-command", comando_psql(), "--manifest", str(_ESTADO["manifiesto"])],
        capture_output=True, env=entorno, timeout=180, check=False)
    resultado = subprocess.CompletedProcess(
        proceso.args, proceso.returncode, proceso.stdout.decode("utf-8", "replace"), proceso.stderr.decode("utf-8", "replace"))
    if resultado.returncode != 0:
        raise AssertionError(f"`load` falló con código {resultado.returncode}: {resultado.stderr.strip()}")
    _ESTADO["password"] = password
    return resultado


def _preparar() -> None:
    """Montaje del módulo (una vez): manifiesto local, objetos ajenos y la carga inicial con la CLI real."""
    holder = tempfile.TemporaryDirectory(prefix="evaluation-grant-options-")
    _SERVER["tmp"] = holder
    _ESTADO["manifiesto"] = escribir_manifiesto_local(Path(holder.name).resolve())
    montaje = server().psql(stdin=FIXTURES_SQL)
    if montaje.returncode != 0:
        raise RuntimeError(f"no se pudieron crear los objetos de prueba: {montaje.stderr.strip()}")
    resultado = cargar(secrets.token_urlsafe(24))
    # Precondición de todo lo demás: la carga fue completa (versionado 9 + local 2 ejecuciones).
    assert resultado.stdout.startswith("14 ejecuciones y "), resultado.stdout


def tearDownModule() -> None:
    holder = _SERVER.pop("tmp", None)
    if holder is not None:
        holder.cleanup()
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


# --- Consultas y conexión COMO el rol ---------------------------------------------------------------------------------


def docker(args, *, env=None, input_bytes=None, timeout=120) -> subprocess.CompletedProcess:
    proceso = subprocess.run(["docker", *args], input=input_bytes, capture_output=True, timeout=timeout, env=env, check=False)
    return subprocess.CompletedProcess(proceso.args, proceso.returncode, proceso.stdout.decode("utf-8", "replace"),
                                       proceso.stderr.decode("utf-8", "replace"))


def direccion_del_contenedor() -> str:
    """IP del contenedor en el puente de Docker: la imagen solo comprueba la contraseña en las conexiones que no son locales."""
    if "direccion" not in _ESTADO:
        resultado = docker(["inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}", server().name])
        direcciones = resultado.stdout.split()
        if resultado.returncode != 0 or not direcciones:
            raise RuntimeError(f"no se pudo obtener la IP del contenedor: {resultado.stdout} {resultado.stderr}")
        _ESTADO["direccion"] = direcciones[0]
    return _ESTADO["direccion"]


def como_el_rol(sql: str) -> subprocess.CompletedProcess:
    """Ejecuta `sql` en una sesión propia conectada COMO el rol por la IP del contenedor.

    La contraseña viaja por `PGPASSWORD` en el entorno del cliente de Docker (`-e PGPASSWORD` sin valor) y con `-w` para
    que `psql` no la pida."""
    server()  # asegura el montaje (y por tanto la contraseña vigente)
    entorno = {clave: valor for clave, valor in os.environ.items() if clave != "PGPASSWORD"}
    entorno["PGPASSWORD"] = _ESTADO["password"]
    orden = ["exec", "-i", "-e", "PGCLIENTENCODING=UTF8", "-e", "PGPASSWORD", server().name, "psql", "-h",
             direccion_del_contenedor(), "-U", READER, "-d", DATABASE, "-w", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1"]
    return docker(orden, env=entorno, input_bytes=sql.encode("utf-8"))


def filas(sql: str) -> list:
    """Filas de una consulta del administrador (`postgres`) como diccionarios, recogidas como JSON."""
    resultado = server().psql(f"SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM ({sql}) q")
    if resultado.returncode != 0:
        raise AssertionError(f"consulta del administrador fallida: {resultado.stderr.strip()}\n{sql}")
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


def uno(sql: str):
    return server().scalar(sql)


def _acl(catalogo: str, objeto: str, columna: str, desde: str, donde: str = "") -> str:
    """Un trozo de la unión: las entradas de la ACL `columna` de `desde` (una fila por objeto y privilegio concedido)."""
    return (f"SELECT '{catalogo}' AS catalogo, {objeto} AS objeto, a.grantor, a.grantee, a.privilege_type, a.is_grantable "
            f"FROM {desde} CROSS JOIN LATERAL aclexplode({columna}) a WHERE {columna} IS NOT NULL {donde}")


# TODOS los catálogos que guardan una ACL. `pg_parameter_acl` (parámetros del servidor) existe desde PostgreSQL 15 y la
# imagen del proyecto es la 17. Cada entrada es `(privilegio, quién lo concedió, a quién, si se puede reconceder)`.
TODAS_LAS_ACL = " UNION ALL ".join([
    _acl("pg_class", "c.oid::regclass::text", "c.relacl", "pg_class c"),
    _acl("pg_attribute", "t.attrelid::regclass::text || '.' || t.attname", "t.attacl", "pg_attribute t"),
    _acl("pg_namespace", "n.nspname", "n.nspacl", "pg_namespace n"),
    _acl("pg_database", "d.datname", "d.datacl", "pg_database d"),
    _acl("pg_proc", "p.oid::regprocedure::text", "p.proacl", "pg_proc p"),
    _acl("pg_language", "l.lanname", "l.lanacl", "pg_language l"),
    _acl("pg_foreign_data_wrapper", "w.fdwname", "w.fdwacl", "pg_foreign_data_wrapper w"),
    _acl("pg_foreign_server", "s.srvname", "s.srvacl", "pg_foreign_server s"),
    _acl("pg_tablespace", "s.spcname", "s.spcacl", "pg_tablespace s"),
    _acl("pg_type", "t.oid::regtype::text", "t.typacl", "pg_type t"),
    _acl("pg_default_acl", "d.defaclnamespace::regnamespace::text || '/' || d.defaclobjtype::text", "d.defaclacl", "pg_default_acl d"),
    _acl("pg_largeobject_metadata", "m.oid::text", "m.lomacl", "pg_largeobject_metadata m"),
    _acl("pg_parameter_acl", "p.parname", "p.paracl", "pg_parameter_acl p"),
])
CATALOGOS_CON_ACL = 13


def entradas_de_acl(donde: str) -> list:
    """Entradas de ACL de todos los catálogos que cumplen `donde` (un filtro SQL sobre `catalogo`, `objeto`, `grantor`,
    `grantee`, `privilege_type`, `is_grantable`), con los nombres de rol ya resueltos para que el mensaje de error sirva."""
    return filas(
        "SELECT catalogo, objeto, privilege_type, is_grantable, "
        "CASE grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(grantee) END AS beneficiario, "
        "pg_get_userbyid(grantor) AS concedido_por "
        f"FROM ({TODAS_LAS_ACL}) e WHERE {donde} ORDER BY 1, 2, 3, 5")


def estado_de_acl() -> dict:
    """Foto de lo que las operaciones del rol podrían cambiar: las ACL (texto exacto, con su `grantor`) del esquema, de la
    base y de `evaluation.runs`, las entradas de PUBLIC sobre los tres, y si un rol sin concesiones puede usar el esquema o
    leer la tabla (lo heredaría de PUBLIC). Una sola consulta: cada llamada a Docker cuesta."""
    consulta = f"""
SELECT jsonb_build_object(
  'esquema', (SELECT nspacl::text FROM pg_namespace WHERE nspname = 'evaluation'),
  'base', (SELECT datacl::text FROM pg_database WHERE datname = '{DATABASE}'),
  'runs', (SELECT relacl::text FROM pg_class WHERE oid = 'evaluation.runs'::regclass),
  'concedido_por_el_rol', (SELECT COALESCE(jsonb_agg(jsonb_build_array(catalogo, objeto, privilege_type) ORDER BY 1, 2, 3),
      '[]'::jsonb) FROM ({TODAS_LAS_ACL}) e WHERE grantor = {OID_ROL}),
  'entradas_de_public', (SELECT COALESCE(jsonb_agg(jsonb_build_array(catalogo, objeto, privilege_type) ORDER BY 1, 2, 3),
      '[]'::jsonb) FROM ({TODAS_LAS_ACL}) e WHERE grantee = 0 AND catalogo IN ('pg_namespace', 'pg_database')
      AND objeto IN ('evaluation', '{DATABASE}') OR grantee = 0 AND catalogo = 'pg_class' AND objeto = 'evaluation.runs'))
"""
    resultado = server().psql(consulta)
    if resultado.returncode != 0:
        raise AssertionError(f"no se pudo tomar la foto de las ACL: {resultado.stderr.strip()}")
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


# --- Introspección: ningún privilegio del rol es reconcedible -------------------------------------------------------------


class AclDelRolTests(unittest.TestCase):
    def test_usage_del_esquema_evaluation_esta_concedido_y_no_es_reconcedible(self):
        # `USAGE ... WITH GRANT OPTION` dejaría al rol dar acceso al esquema a otros roles. Se mira la entrada exacta del
        # esquema en `pg_namespace`: el privilegio existe (guarda anti-vacío) y su `is_grantable` es falso.
        usage = filas(
            "SELECT a.privilege_type, a.is_grantable, pg_get_userbyid(a.grantor) AS concedido_por FROM pg_namespace n "
            f"CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE n.nspname = 'evaluation' AND a.grantee = {OID_ROL} ORDER BY 1")
        self.assertIn("USAGE", [fila["privilege_type"] for fila in usage], "el rol no tiene USAGE en evaluation")
        self.assertEqual([fila for fila in usage if fila["is_grantable"]], [], "USAGE (u otro) reconcedible en el esquema")
        # Concedido por el propietario del esquema, no por el propio rol.
        self.assertEqual({fila["concedido_por"] for fila in usage}, {"postgres"})

    def test_connect_de_la_base_si_aparece_en_su_acl_no_es_reconcedible(self):
        # `CONNECT ... WITH GRANT OPTION` dejaría al rol repartir el acceso a la base. PUBLIC ya tiene CONNECT por defecto,
        # así que el rol puede no figurar en el ACL de la base; si figura (la carga lo concede explícitamente), debe ser
        # como `CONNECT` y no reconcedible.
        base = filas(
            "SELECT a.privilege_type, a.is_grantable FROM pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) a "
            f"WHERE d.datname = '{DATABASE}' AND a.grantee = {OID_ROL} ORDER BY 1")
        if base:
            self.assertIn("CONNECT", [fila["privilege_type"] for fila in base])
            self.assertEqual([fila for fila in base if fila["is_grantable"]], [], "privilegio reconcedible en la base")

    def test_el_rol_aparece_en_las_acl_con_sus_concesiones_reales(self):
        # Guarda anti-vacío de las pruebas siguientes: si la unión de catálogos no viera al rol, «ninguna entrada es
        # reconcedible» sería cierto por no mirar nada. Sus concesiones son exactamente las de la carga: `SELECT` sobre las
        # cuatro relaciones, `USAGE` del esquema, `SELECT` por defecto sobre tablas nuevas y, si figura, `CONNECT`.
        propias = entradas_de_acl(f"grantee = {OID_ROL}")
        esperadas = {("pg_class", f"evaluation.{tabla}", "SELECT") for tabla in ("runs", "results", "config_changes", "comparable_runs")}
        esperadas |= {("pg_namespace", "evaluation", "USAGE"), ("pg_default_acl", "evaluation/r", "SELECT")}
        vistas = {(fila["catalogo"], fila["objeto"], fila["privilege_type"]) for fila in propias}
        self.assertTrue(esperadas <= vistas, f"faltan concesiones del rol: {sorted(esperadas - vistas)}")
        # Y nada más allá del `CONNECT` opcional de la base.
        self.assertLessEqual(vistas - esperadas, {("pg_database", DATABASE, "CONNECT")}, sorted(vistas - esperadas))

    def test_ninguna_entrada_de_ninguna_acl_del_rol_es_reconcedible(self):
        # Barrido sobre TODOS los catálogos con ACL: relaciones y sus columnas, esquemas (incluido `public` y los del
        # sistema), bases, funciones, lenguajes, FDW, servidores foráneos, tablespaces, tipos, privilegios por defecto,
        # objetos grandes y parámetros. Un `WITH GRANT OPTION` en cualquiera, también uno que nadie imaginó, aparece aquí.
        self.assertEqual(entradas_de_acl(f"is_grantable AND grantee = {OID_ROL}"), [])

    def test_ninguna_acl_la_ha_concedido_el_propio_rol(self):
        # Si el rol hubiera reconcedido algo (porque tuvo la opción alguna vez), la entrada llevaría al rol como `grantor`
        # aunque su propia opción ya no exista. El rol no es propietario de nada: no puede haber ninguna.
        self.assertEqual(entradas_de_acl(f"grantor = {OID_ROL}"), [])

    def test_el_barrido_cubre_todos_los_catalogos_con_acl(self):
        # El barrido es válido solo si la unión consulta de verdad los trece catálogos y ninguno falla ni se pierde:
        # cada uno devuelve su columna de catálogo con un recuento propio (cero es legítimo en los que no tienen ACL).
        catalogos = filas(f"SELECT DISTINCT catalogo FROM ({TODAS_LAS_ACL}) e")
        self.assertEqual(TODAS_LAS_ACL.count("UNION ALL") + 1, CATALOGOS_CON_ACL)
        # Los que SÍ tienen entradas en una base recién creada y cargada: relaciones, esquemas, bases, tipos o funciones.
        self.assertTrue({"pg_class", "pg_namespace", "pg_default_acl"} <= {fila["catalogo"] for fila in catalogos}, catalogos)


# --- Operaciones reales conectado como el rol ---------------------------------------------------------------------------

REGRANTS = [
    ("USAGE del esquema", "GRANT USAGE ON SCHEMA evaluation TO PUBLIC"),
    ("SELECT de runs", "GRANT SELECT ON evaluation.runs TO PUBLIC"),
    ("CONNECT de la base", f"GRANT CONNECT ON DATABASE {DATABASE} TO PUBLIC"),
]


class ReconcederComoElRolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.antes = estado_de_acl()
        # Cada intento en su propia sesión: el resultado de uno no depende de que otro falle antes.
        cls.resultados = {clave: como_el_rol(sentencia) for clave, sentencia in REGRANTS}
        cls.despues = estado_de_acl()

    def test_la_foto_inicial_no_esta_vacia_y_nada_es_de_public(self):
        # Guarda anti-vacío: se compara una foto real (esquema, base y tabla con ACL de verdad) y, de partida, PUBLIC no
        # tiene ninguna entrada propia sobre el esquema ni sobre la tabla (en la base solo el CONNECT/TEMP por defecto).
        self.assertIn("grafana_evaluation_reader=U/postgres", self.antes["esquema"])
        self.assertIn("grafana_evaluation_reader=r/postgres", self.antes["runs"])
        for clave in ("esquema", "base", "runs"):
            self.assertIsNotNone(self.antes[clave], clave)
        self.assertNotIn(["pg_namespace", "evaluation", "USAGE"], self.antes["entradas_de_public"])
        self.assertNotIn(["pg_class", "evaluation.runs", "SELECT"], self.antes["entradas_de_public"])

    def test_cada_regrant_del_rol_es_rechazado_o_no_concede_nada(self):
        for clave, sentencia in REGRANTS:
            with self.subTest(operacion=clave):
                resultado = self.resultados[clave]
                if resultado.returncode == 0:
                    # `GRANT` sin la opción no falla: avisa y no concede nada (y no debe haber salido nada más por stdout).
                    self.assertIn(SIN_CONCESION, resultado.stderr, f"{sentencia} terminó bien sin aviso: {resultado.stderr!r}")
                else:
                    self.assertRegex(resultado.stderr, DENEGADO, f"{sentencia}: {resultado.stderr!r}")

    def test_despues_de_los_intentos_las_acl_son_exactamente_las_de_antes(self):
        # El código de salida no basta: con la opción concedida el `GRANT` termina bien y cambia la ACL (añade una entrada
        # con el propio rol como `grantor`). Por eso se compara el texto exacto de las tres ACL.
        for clave in ("esquema", "base", "runs"):
            with self.subTest(acl=clave):
                self.assertEqual(self.despues[clave], self.antes[clave])

    def test_el_rol_no_ha_concedido_nada_y_public_no_gana_entradas(self):
        self.assertEqual(self.despues["concedido_por_el_rol"], [])
        self.assertEqual(self.despues["entradas_de_public"], self.antes["entradas_de_public"])

    def test_un_rol_sin_concesiones_no_hereda_acceso_al_esquema_ni_a_la_tabla(self):
        # Efecto observable de un regrant a PUBLIC que sí prosperara: cualquier rol, también uno recién creado, podría usar
        # el esquema y leer la tabla. Se comprueba con un rol de control temporal, que se borra aunque la comprobación falle.
        control = f"evaluation_grant_control_{secrets.token_hex(3)}"
        server().psql(f"CREATE ROLE {control} NOLOGIN")
        try:
            self.assertEqual(uno(f"SELECT has_schema_privilege('{control}', 'evaluation', 'USAGE')::text"), "false")
            self.assertEqual(uno(f"SELECT has_table_privilege('{control}', 'evaluation.runs', 'SELECT')::text"), "false")
        finally:
            server().psql(f"DROP ROLE IF EXISTS {control}")


if __name__ == "__main__":
    unittest.main()
