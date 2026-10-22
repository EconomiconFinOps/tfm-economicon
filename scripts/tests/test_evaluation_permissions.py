"""Permisos del rol de Grafana en un PostgreSQL real (JUP-121, tarea 5.2).

La spec «Acceso de Grafana de solo lectura» exige que el rol `grafana_evaluation_reader` pueda leer el esquema
`evaluation` y NADA más: ni escribir en él ni leer las tablas de embeddings del asistente. Esta prueba lo comprueba
contra la base, con la CLI real `load`, de dos maneras que se refuerzan:

* INTROSPECCIÓN del catálogo (qué dice PostgreSQL que puede hacer el rol): atributos, pertenencia a otros roles,
  propiedad de objetos y privilegios sobre TODAS las relaciones de TODOS los esquemas, esquemas, bases de datos,
  funciones y parámetros. La referencia es un rol de control recién creado y sin ninguna concesión: lo único que el rol
  de Grafana puede hacer de más son exactamente cuatro `SELECT` sobre `evaluation`. Así no depende de acertar con la
  lista de lo prohibido: un privilegio que nadie imaginó también aparece en la diferencia.
* OPERACIONES reales conectado COMO el rol, con su contraseña y contra la IP del contenedor en el puente (la imagen
  oficial confía en el socket y en `127.0.0.1`, y solo comprueba la contraseña en el resto; igual que
  `test_evaluation_load.py`). La contraseña viaja por `PGPASSWORD` en el entorno del cliente de Docker.

Montaje (un contenedor desechable por módulo): `postgres` crea una tabla de documentos y otra de embeddings en `public`
(`public.knowledge_documents` y `public.knowledge_embeddings` con una fila y un vector), una vista de `public`, un
esquema ajeno y un rol de control. Después se carga con la CLI real (`python tools/evaluation-dashboard.py load
--psql-command "docker exec -i <contenedor> psql ..."`), con el manifiesto versionado más un manifiesto local que da
filas a las dos vistas, y una contraseña aleatoria en `GRAFANA_EVALUATION_DB_PASSWORD`.

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
CONTROL = "evaluation_test_control"
PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
DATABASE = "embeddings"
LECTURAS = [("evaluation", "comparable_runs", "SELECT"), ("evaluation", "config_changes", "SELECT"),
            ("evaluation", "results", "SELECT"), ("evaluation", "runs", "SELECT")]
PRIVILEGIOS_DE_TABLA = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
SISTEMA = "('pg_catalog', 'information_schema')"
# Un rechazo de PostgreSQL por falta de privilegios (SQLSTATE 42501) con alguno de sus mensajes habituales.
DENEGADO = re.compile(r"permission denied|must be owner|must be superuser|must have privileges|only roles with", re.I)

class _Estado(dict):
    """Estado del módulo (rutas, contraseña vigente, IP). Leer una clave que aún no existe monta antes el servidor, el
    manifiesto y la carga inicial (`server()`): así ninguna prueba depende del orden en que se ejecuten las clases."""

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


# --- Montaje ---------------------------------------------------------------------------------------------------------

FIXTURES_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE public.knowledge_documents (id serial PRIMARY KEY, title text NOT NULL);
INSERT INTO public.knowledge_documents (title) VALUES ('documento secreto');
CREATE TABLE public.knowledge_embeddings (
  id serial PRIMARY KEY, document_id integer NOT NULL REFERENCES public.knowledge_documents (id),
  embedding vector(3) NOT NULL);
INSERT INTO public.knowledge_embeddings (document_id, embedding) VALUES (1, '[1,2,3]');
CREATE VIEW public.vista_ajena AS SELECT id, title FROM public.knowledge_documents;
CREATE SCHEMA otro;
CREATE TABLE otro.tabla (a integer);
INSERT INTO otro.tabla VALUES (1);
CREATE ROLE evaluation_test_control NOLOGIN;
"""


def informe(run_id: str, fuente: str, run_at: str, modelo: str) -> dict:
    return {
        "contract_version": 1,
        "run": {"run_id": run_id, "source": fuente, "run_at": run_at, "commit": "abc1234", "suite": "JUP-069",
                "suite_version": "1.0.0", "generation_model": modelo, "retrieval": {"top_k": 4}},
        "results": [{"measure_type": "A", "grp": "accuracy", "metric_id": "ACC-2", "behavior": "all",
                     "status": "measured", "value": 0.5, "unit": "tasa", "numerator": 5, "denominator": 10,
                     "judgment": "automatic"}],
    }


def escribir_manifiesto_local(directorio: Path) -> Path:
    """Cuatro ejecuciones que dan filas a las dos vistas: dos comparables y un cambio de modelo entre dos consecutivas."""
    entradas = []
    for run_id, fuente, dia, modelo in (("perm-a1", "JUP-071", "10", "m1"), ("perm-a2", "JUP-071", "11", "m1"),
                                       ("perm-b1", "JUP-072", "12", "m1"), ("perm-b2", "JUP-072", "13", "m2")):
        ruta = directorio / f"{run_id}.json"
        ruta.write_text(json.dumps(informe(run_id, fuente, f"2026-10-{dia}T10:00:00Z", modelo)), encoding="utf-8")
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
        [sys.executable, str(TOOL_PATH), "load", "--psql-command", comando_psql(), "--manifest",
         str(_ESTADO["manifiesto"])],
        capture_output=True, env=entorno, timeout=180, check=False)
    resultado = subprocess.CompletedProcess(
        proceso.args, proceso.returncode, proceso.stdout.decode("utf-8", "replace"), proceso.stderr.decode("utf-8", "replace"))
    if resultado.returncode != 0:
        raise AssertionError(f"`load` falló con código {resultado.returncode}: {resultado.stderr.strip()}")
    _ESTADO["password"] = password
    return resultado


def _preparar() -> None:
    """Montaje del módulo (una vez): manifiesto local, tablas ajenas y la carga inicial con la CLI real."""
    holder = tempfile.TemporaryDirectory(prefix="evaluation-permissions-")
    _SERVER["tmp"] = holder
    _ESTADO["manifiesto"] = escribir_manifiesto_local(Path(holder.name).resolve())
    montaje = server().psql(stdin=FIXTURES_SQL)
    if montaje.returncode != 0:
        raise RuntimeError(f"no se pudieron crear las tablas de prueba: {montaje.stderr.strip()}")
    resultado = cargar(secrets.token_urlsafe(24))
    # Precondición de todo lo demás: la carga fue completa (versionado 9 + local 4 ejecuciones) y ninguna tabla quedó vacía.
    assert resultado.stdout.startswith("16 ejecuciones y "), resultado.stdout


def tearDownModule() -> None:
    holder = _SERVER.pop("tmp", None)
    if holder is not None:
        holder.cleanup()
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


# --- Conexión COMO el rol --------------------------------------------------------------------------------------------


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


def como_el_rol(sql: str, password: str | None = None, usuario: str = READER, sin_contrasena: bool = False
                ) -> subprocess.CompletedProcess:
    """Ejecuta `sql` conectado COMO `usuario` por la IP del contenedor, con la contraseña actual salvo que se indique otra.

    La contraseña viaja por `PGPASSWORD` en el entorno del cliente de Docker (`-e PGPASSWORD` sin valor) y con `-w` para
    que `psql` no la pida; con `sin_contrasena` no se define y la conexión debe rechazarse.
    """
    entorno = {clave: valor for clave, valor in os.environ.items() if clave != "PGPASSWORD"}
    orden = ["exec", "-i", "-e", "PGCLIENTENCODING=UTF8"]
    if not sin_contrasena:
        entorno["PGPASSWORD"] = _ESTADO["password"] if password is None else password
        orden += ["-e", "PGPASSWORD"]
    orden += [server().name, "psql", "-h", direccion_del_contenedor(), "-U", usuario, "-d", DATABASE, "-w", "-X", "-A", "-t",
              "-q", "-v", "ON_ERROR_STOP=1"]
    return docker(orden, env=entorno, input_bytes=sql.encode("utf-8"))


def consulta_del_rol(sql: str):
    resultado = como_el_rol(sql)
    if resultado.returncode != 0:
        raise AssertionError(f"el rol no pudo ejecutar {sql!r}: {resultado.stderr.strip()}")
    return resultado.stdout.strip()


def filas(sql: str) -> list:
    """Filas de una consulta del administrador (`postgres`) como diccionarios, recogidas como JSON."""
    resultado = server().psql(f"SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM ({sql}) q")
    if resultado.returncode != 0:
        raise AssertionError(f"consulta del administrador fallida: {resultado.stderr.strip()}\n{sql}")
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


def uno(sql: str):
    return server().scalar(sql)


OID_ROL = f"(SELECT oid FROM pg_roles WHERE rolname = '{READER}')"
OID_CONTROL = f"(SELECT oid FROM pg_roles WHERE rolname = '{CONTROL}')"


_DIFERENCIA_DE_RELACIONES = (
    "SELECT n.nspname AS esquema, c.relname AS relacion, p AS privilegio "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    f"CROSS JOIN unnest(ARRAY{list(PRIVILEGIOS_DE_TABLA)}) AS p "
    "WHERE c.relkind IN ('r', 'v', 'm', 'f', 'p') "
    f"AND has_table_privilege({OID_ROL}, c.oid, p) AND NOT has_table_privilege({OID_CONTROL}, c.oid, p) "
    "ORDER BY 1, 2, 3")


def diferencia_de_relaciones() -> list:
    """Privilegios sobre relaciones (tablas, vistas, vistas materializadas, foráneas y particionadas, de TODOS los
    esquemas incluidos los del sistema) que el rol de Grafana tiene y el rol de control, sin concesiones, no."""
    return filas(_DIFERENCIA_DE_RELACIONES)


def privilegios_de(relaciones, rol: str = READER) -> dict:
    """`{relación: [privilegios de tabla que `rol` tiene]}` para varias relaciones, con UNA sola consulta."""
    lista = ", ".join(f"'{relacion}'" for relacion in relaciones)
    resultado = filas(
        "SELECT r AS relacion, p AS privilegio FROM unnest(ARRAY[" + lista + "]) AS r "
        f"CROSS JOIN unnest(ARRAY{list(PRIVILEGIOS_DE_TABLA)}) AS p WHERE has_table_privilege('{rol}', r::regclass, p) "
        "ORDER BY 1, 2")
    tienen = {relacion: [] for relacion in relaciones}
    for fila in resultado:
        tienen[fila["relacion"]].append(fila["privilegio"])
    return tienen


def como_tuplas(lista: list, *claves) -> list:
    return [tuple(fila[clave] for clave in claves) for fila in lista]


def instantanea() -> dict:
    """Todo lo que identifica los permisos del rol, para compararlo entre cargas (no se acumulan ni se pierden).

    Una sola consulta (cada llamada a Docker cuesta): devuelve un objeto JSON con la diferencia de privilegios de relación
    respecto al rol de control, las ACL de las cuatro relaciones, del esquema y de la base, los privilegios por defecto, los
    atributos y las pertenencias del rol.
    """
    consulta = f"""
SELECT jsonb_build_object(
  'relaciones', (SELECT COALESCE(jsonb_agg(to_jsonb(d)), '[]'::jsonb) FROM ({_DIFERENCIA_DE_RELACIONES}) d),
  'acl_de_evaluation', (SELECT COALESCE(jsonb_agg(jsonb_build_array(c.relname, c.relkind, c.relacl::text) ORDER BY c.relname), '[]'::jsonb)
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'evaluation' AND c.relkind IN ('r', 'v')),
  'acl_del_esquema', (SELECT nspacl::text FROM pg_namespace WHERE nspname = 'evaluation'),
  'acl_de_la_base', (SELECT datacl::text FROM pg_database WHERE datname = '{DATABASE}'),
  'privilegios_por_defecto', (SELECT COALESCE(jsonb_agg(jsonb_build_array(d.defaclnamespace::regnamespace::text, d.defaclobjtype, d.defaclacl::text)
      ORDER BY d.defaclnamespace, d.defaclobjtype), '[]'::jsonb) FROM pg_default_acl d),
  'atributos', (SELECT to_jsonb(r) FROM (SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls,
      rolinherit, rolconnlimit FROM pg_roles WHERE rolname = '{READER}') r),
  'pertenencias', (SELECT COALESCE(jsonb_agg(roleid::regrole::text), '[]'::jsonb) FROM pg_auth_members WHERE member = {OID_ROL}),
  'roles_con_el_mismo_nombre', (SELECT count(*) FROM pg_roles WHERE rolname = '{READER}'))
"""
    resultado = server().psql(consulta)
    if resultado.returncode != 0:
        raise AssertionError(f"no se pudo tomar la instantánea de permisos: {resultado.stderr.strip()}")
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


# --- El rol: atributos, pertenencia y propiedad -------------------------------------------------------------------------


class RolTests(unittest.TestCase):
    def test_puede_iniciar_sesion_y_no_tiene_ningun_atributo_de_poder(self):
        atributos = filas(
            "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolconnlimit, "
            f"rolvaliduntil IS NULL AS sin_caducidad FROM pg_roles WHERE rolname = '{READER}'")
        # LOGIN y ninguno de los atributos que dan poder sobre el servidor: ni superusuario, ni crear bases ni roles,
        # ni replicación, ni saltarse la seguridad por filas; sin límite de conexiones ni caducidad que invente otro régimen.
        self.assertEqual(atributos, [{
            "rolcanlogin": True, "rolsuper": False, "rolcreatedb": False, "rolcreaterole": False,
            "rolreplication": False, "rolbypassrls": False, "rolconnlimit": -1, "sin_caducidad": True}])

    def test_hay_un_unico_rol_de_grafana_y_su_contrasena_esta_guardada_en_hash(self):
        self.assertEqual(uno("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'grafana%'"), "1")
        guardada = uno(f"SELECT rolpassword FROM pg_authid WHERE rolname = '{READER}'")
        self.assertTrue(guardada.startswith("SCRAM-SHA-256$"), guardada[:20])
        self.assertNotIn(_ESTADO["password"], guardada)

    def test_no_es_miembro_de_ningun_otro_rol(self):
        # Un `GRANT pg_read_all_data TO ...` (o `postgres`) le daría lectura (o todo) sin tocar ninguna tabla.
        self.assertEqual(filas(f"SELECT roleid::regrole::text AS rol FROM pg_auth_members WHERE member = {OID_ROL}"), [])

    def test_no_es_propietario_de_ningun_objeto(self):
        propiedades = filas(
            f"SELECT (SELECT count(*) FROM pg_class WHERE relowner = {OID_ROL}) AS relaciones, "
            f"(SELECT count(*) FROM pg_namespace WHERE nspowner = {OID_ROL}) AS esquemas, "
            f"(SELECT count(*) FROM pg_proc WHERE proowner = {OID_ROL}) AS funciones, "
            f"(SELECT count(*) FROM pg_type WHERE typowner = {OID_ROL}) AS tipos, "
            f"(SELECT count(*) FROM pg_database WHERE datdba = {OID_ROL}) AS bases_de_datos, "
            # `pg_shdepend` registra TODA dependencia de propiedad del rol, de cualquier clase de objeto.
            f"(SELECT count(*) FROM pg_shdepend WHERE refclassid = 'pg_authid'::regclass AND refobjid = {OID_ROL} "
            "AND deptype = 'o') AS dependencias_de_propiedad")
        self.assertEqual(propiedades, [{"relaciones": 0, "esquemas": 0, "funciones": 0, "tipos": 0, "bases_de_datos": 0,
                                        "dependencias_de_propiedad": 0}])

    def test_el_esquema_y_las_tablas_de_evaluation_son_del_administrador(self):
        propietarios = filas(
            "SELECT DISTINCT pg_get_userbyid(c.relowner) AS propietario FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'evaluation' AND c.relkind IN ('r', 'v')")
        self.assertEqual(propietarios, [{"propietario": "postgres"}])
        self.assertEqual(uno("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'evaluation'"), "postgres")

    def test_no_tiene_configuracion_propia_que_cambie_su_sesion(self):
        # Un `ALTER ROLE ... SET` (search_path, role...) cambiaría lo que ve o hace sin que ningún `GRANT` lo delate.
        self.assertEqual(uno(f"SELECT count(*) FROM pg_db_role_setting WHERE setrole = {OID_ROL}"), "0")


# --- Privilegios por introspección ------------------------------------------------------------------------------------


class PrivilegiosTests(unittest.TestCase):
    def test_sobre_todas_las_relaciones_de_todos_los_esquemas_solo_hay_select_sobre_las_cuatro_de_evaluation(self):
        # La diferencia con un rol sin concesiones, sobre TODAS las tablas y vistas de TODOS los esquemas (también los del
        # sistema, p. ej. `pg_authid`), son exactamente cuatro `SELECT`: ni `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`,
        # `REFERENCES` o `TRIGGER`, ni lectura de `public`, de los embeddings ni de un esquema ajeno.
        diferencia = diferencia_de_relaciones()
        self.assertEqual(como_tuplas(diferencia, "esquema", "relacion", "privilegio"), LECTURAS, diferencia[:12])

    def test_el_catalogo_de_privilegios_coincide_con_la_vista_role_table_grants(self):
        # Segunda fuente, la que citan la spec y la documentación: lo que `information_schema` dice haber concedido.
        concedidos = filas(
            "SELECT table_schema, table_name, privilege_type, is_grantable FROM information_schema.role_table_grants "
            f"WHERE grantee = '{READER}' ORDER BY 1, 2, 3")
        self.assertEqual(como_tuplas(concedidos, "table_schema", "table_name", "privilege_type"), LECTURAS)
        self.assertEqual({fila["is_grantable"] for fila in concedidos}, {"NO"})

    def test_las_tablas_de_public_y_de_embeddings_no_se_pueden_ni_leer(self):
        # Fixtures creados por `postgres`: la tabla de documentos, la de embeddings (con un vector), una vista de `public`
        # y una tabla de un esquema ajeno. Sobre ninguna hay NINGÚN privilegio, de los siete de tabla.
        ajenas = ("public.knowledge_documents", "public.knowledge_embeddings", "public.vista_ajena", "otro.tabla")
        self.assertEqual(uno("SELECT count(*) FROM public.knowledge_embeddings"), "1")  # precondición: no están vacías
        self.assertEqual(privilegios_de(ajenas), {tabla: [] for tabla in ajenas})

    def test_cada_relacion_de_evaluation_tiene_select_y_ningun_otro_privilegio(self):
        relaciones = [f"evaluation.{nombre}" for nombre in ("runs", "results", "config_changes", "comparable_runs")]
        self.assertEqual(privilegios_de(relaciones), {relacion: ["SELECT"] for relacion in relaciones})

    def test_ningun_privilegio_se_concede_a_public_ni_con_opcion_de_reconceder_ni_por_columnas(self):
        # `GRANT ... TO PUBLIC` lo daría a todos los roles (y el rol de control lo heredaría: la diferencia no lo vería).
        publico = filas(
            "SELECT n.nspname AS esquema, c.relname AS relacion, a.privilege_type AS privilegio FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a "
            f"WHERE n.nspname = 'evaluation' AND a.grantee = 0")
        self.assertEqual(publico, [])
        reconcedibles = filas(
            "SELECT c.relname AS relacion FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            f"CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE n.nspname = 'evaluation' AND a.grantee = {OID_ROL} AND a.is_grantable")
        self.assertEqual(reconcedibles, [])
        # Privilegios por columna (`GRANT UPDATE (value) ON ...`): no aparecen en `has_table_privilege` de tabla.
        self.assertEqual(uno(f"SELECT count(*) FROM pg_attribute WHERE attacl IS NOT NULL AND attacl::text LIKE '%{READER}=%'"), "0")

    def test_no_puede_crear_en_ningun_esquema_ni_en_ninguna_base(self):
        crear = filas(
            "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\\_temp\\_%' AND nspname NOT LIKE 'pg\\_toast\\_temp\\_%' "
            f"AND has_schema_privilege({OID_ROL}, oid, 'CREATE') ORDER BY 1")
        self.assertEqual(crear, [], "el rol puede crear objetos en estos esquemas")
        self.assertEqual(filas(f"SELECT datname FROM pg_database WHERE has_database_privilege({OID_ROL}, oid, 'CREATE')"), [])
        # Solo CONNECT y TEMP, los dos que da PUBLIC por defecto: ninguno es una concesión propia más allá de CONNECT.
        privilegios = filas(
            f"SELECT has_database_privilege({OID_ROL}, '{DATABASE}', 'CONNECT') AS connect, "
            f"has_database_privilege({OID_ROL}, '{DATABASE}', 'CREATE') AS \"create\", "
            f"has_database_privilege({OID_ROL}, '{DATABASE}', 'TEMP') AS temp")
        self.assertEqual(privilegios, [{"connect": True, "create": False, "temp": True}])

    def test_usage_solo_en_evaluation_respecto_a_un_rol_sin_concesiones(self):
        usage = filas(
            "SELECT nspname FROM pg_namespace "
            f"WHERE has_schema_privilege({OID_ROL}, oid, 'USAGE') AND NOT has_schema_privilege({OID_CONTROL}, oid, 'USAGE')")
        self.assertEqual(usage, [{"nspname": "evaluation"}])
        self.assertEqual(uno(f"SELECT has_schema_privilege('{READER}', 'otro', 'USAGE')::text"), "false")

    def test_nada_mas_en_secuencias_funciones_ni_parametros_del_servidor(self):
        secuencias = filas(
            "SELECT n.nspname || '.' || c.relname AS secuencia, p AS privilegio FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "CROSS JOIN unnest(ARRAY['USAGE', 'SELECT', 'UPDATE']) AS p WHERE c.relkind = 'S' "
            f"AND has_sequence_privilege({OID_ROL}, c.oid, p) AND NOT has_sequence_privilege({OID_CONTROL}, c.oid, p)")
        self.assertEqual(secuencias, [])
        # Ejecutar funciones que un rol sin concesiones no puede (`pg_read_file`, `lo_import`...) es lo que daría una
        # pertenencia a `pg_read_server_files` o a `postgres`.
        funciones = filas(
            "SELECT p.oid::regprocedure::text AS funcion FROM pg_proc p "
            f"WHERE has_function_privilege({OID_ROL}, p.oid, 'EXECUTE') AND NOT has_function_privilege({OID_CONTROL}, p.oid, 'EXECUTE')")
        self.assertEqual(funciones, [])
        parametros = filas(
            "SELECT name FROM pg_settings "
            f"WHERE (has_parameter_privilege({OID_ROL}, name, 'SET') AND NOT has_parameter_privilege({OID_CONTROL}, name, 'SET') "
            f"OR has_parameter_privilege({OID_ROL}, name, 'ALTER SYSTEM') AND NOT has_parameter_privilege({OID_CONTROL}, name, 'ALTER SYSTEM'))")
        self.assertEqual(parametros, [])
        self.assertEqual(uno(f"SELECT has_parameter_privilege('{READER}', 'session_replication_role', 'SET')::text"), "false")

    def test_los_privilegios_por_defecto_son_solo_select_sobre_tablas_de_evaluation(self):
        por_defecto = filas(
            "SELECT d.defaclnamespace::regnamespace::text AS esquema, d.defaclobjtype AS tipo, a.privilege_type AS privilegio, "
            "a.is_grantable AS reconcedible, pg_get_userbyid(d.defaclrole) AS creador FROM pg_default_acl d "
            f"CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE a.grantee = {OID_ROL}")
        # Una sola regla: lo que `postgres` cree en `evaluation` nace legible. Ninguna regla global (sin esquema) ni de
        # otros tipos de objeto (secuencias, funciones, tipos).
        self.assertEqual(por_defecto, [{"esquema": "evaluation", "tipo": "r", "privilegio": "SELECT",
                                        "reconcedible": False, "creador": "postgres"}])


# --- Operaciones reales conectado como el rol -------------------------------------------------------------------------

ESCRIBIR_RUN = ("INSERT INTO evaluation.runs (run_id, source, synthetic, is_real, non_real_reasons, comparability_key, format, "
                "milestone, report_sha256) VALUES ('intruso', 'x', false, true, '{}', 'k', 'f', false, 's')")

# (clave, sentencia). Cada una se ejecuta DENTRO de una sesión abierta como el rol; todas deben fallar por privilegios.
DENEGADAS = [
    ("leer embeddings", "SELECT * FROM public.knowledge_embeddings"),
    ("leer una columna de embeddings", "SELECT embedding FROM public.knowledge_embeddings"),
    ("leer documentos de public", "SELECT * FROM public.knowledge_documents"),
    ("leer una vista de public", "SELECT * FROM public.vista_ajena"),
    ("leer un esquema ajeno", "SELECT * FROM otro.tabla"),
    ("INSERT en runs", ESCRIBIR_RUN),
    ("INSERT en results", "INSERT INTO evaluation.results (run_id) VALUES ('intruso')"),
    ("UPDATE", "UPDATE evaluation.runs SET source = source"),
    ("DELETE", "DELETE FROM evaluation.results"),
    ("TRUNCATE", "TRUNCATE evaluation.results, evaluation.runs"),
    ("LOCK exclusivo", "LOCK TABLE evaluation.runs IN ACCESS EXCLUSIVE MODE"),
    ("DROP TABLE", "DROP TABLE evaluation.results"),
    ("DROP VIEW", "DROP VIEW evaluation.comparable_runs"),
    ("DROP SCHEMA", "DROP SCHEMA evaluation CASCADE"),
    ("ALTER TABLE", "ALTER TABLE evaluation.runs ADD COLUMN intruso integer"),
    ("COMMENT", "COMMENT ON TABLE evaluation.runs IS 'intruso'"),
    ("CREATE INDEX", "CREATE INDEX intruso ON evaluation.runs (source)"),
    ("CREATE TABLE en evaluation", "CREATE TABLE evaluation.intruso (a integer)"),
    ("CREATE VIEW en evaluation", "CREATE VIEW evaluation.intruso AS SELECT 1 AS a"),
    ("CREATE FUNCTION en evaluation", "CREATE FUNCTION evaluation.intruso() RETURNS integer LANGUAGE sql AS 'SELECT 1'"),
    ("CREATE TABLE en public", "CREATE TABLE public.intruso (a integer)"),
    ("CREATE TABLE en un esquema ajeno", "CREATE TABLE otro.intruso (a integer)"),
    ("CREATE SCHEMA", "CREATE SCHEMA intruso"),
    ("DROP TABLE de public", "DROP TABLE public.knowledge_documents"),
    ("ALTER TABLE de public", "ALTER TABLE public.knowledge_documents RENAME TO intruso"),
    ("leer pg_authid", "SELECT * FROM pg_authid"),
    ("leer pg_shadow", "SELECT * FROM pg_shadow"),
    ("leer un fichero del servidor", "SELECT pg_read_file('/etc/passwd')"),
    ("listar un directorio del servidor", "SELECT pg_ls_dir('/')"),
    ("importar un fichero como objeto grande", "SELECT lo_import('/etc/passwd')"),
    ("COPY a un programa", "COPY (SELECT 1) TO PROGRAM 'true'"),
    ("COPY a un fichero", "COPY (SELECT 1) TO '/tmp/intruso.csv'"),
    ("SET ROLE postgres", "SET ROLE postgres"),
    ("crear un rol", "CREATE ROLE intruso"),
    ("hacerse superusuario", f"ALTER ROLE {READER} WITH SUPERUSER"),
    ("ser miembro de postgres", f"GRANT postgres TO {READER}"),
    ("borrar el rol del administrador", "DROP ROLE postgres"),
    ("leer el directorio de datos", "SELECT current_setting('data_directory')"),
    ("leer pg_hba", "SELECT * FROM pg_hba_file_rules"),
    ("recargar la configuración", "SELECT pg_reload_conf()"),
]
# Mensajes que, según la tarea, deben decir literalmente «permission denied» (no «must be owner» ni parecido).
CON_PERMISSION_DENIED = {
    "leer embeddings", "leer documentos de public", "leer una vista de public", "leer un esquema ajeno", "INSERT en runs",
    "INSERT en results", "UPDATE", "DELETE", "TRUNCATE", "CREATE TABLE en evaluation", "CREATE TABLE en public", "CREATE SCHEMA",
    "leer pg_authid", "leer un fichero del servidor", "COPY a un programa", "SET ROLE postgres",
}
PERMITIDAS = [
    ("leer runs", "SELECT count(*) FROM evaluation.runs"),
    ("leer results", "SELECT count(*) FROM evaluation.results"),
    ("leer config_changes", "SELECT count(*) FROM evaluation.config_changes"),
    ("leer comparable_runs", "SELECT count(*) FROM evaluation.comparable_runs"),
    ("tabla temporal propia", "CREATE TEMP TABLE propia (a integer)"),
]


def lote_de_operaciones() -> dict:
    """Ejecuta cada sentencia de `DENEGADAS` y `PERMITIDAS` en UNA sesión abierta como el rol y devuelve su resultado.

    Cada sentencia va en su propio bloque con manejo de excepción (subtransacción) y todo dentro de una transacción que
    se DESHACE al final: si el rol pudiera hacer algo de lo prohibido no dejaría rastro en la base de la prueba. El
    resultado de cada una es su SQLSTATE y su mensaje (`00000` si se ejecutó).
    """
    cuerpo = ["BEGIN;", "CREATE TEMP TABLE resultados (i integer, estado text, mensaje text) ON COMMIT DROP;"]
    sentencias = DENEGADAS + PERMITIDAS
    for indice, (_, sentencia) in enumerate(sentencias):
        assert "$q$" not in sentencia
        cuerpo.append(
            "DO $do$ BEGIN\n"
            f"  BEGIN EXECUTE $q${sentencia}$q$; INSERT INTO resultados VALUES ({indice}, '00000', NULL);\n"
            f"  EXCEPTION WHEN OTHERS THEN INSERT INTO resultados VALUES ({indice}, SQLSTATE, SQLERRM); END;\n"
            "END $do$;")
    cuerpo.append("SELECT jsonb_build_object('usuario', current_user, 'sesion', session_user, "
                  "'superusuario', current_setting('is_superuser'), "
                  "'resultados', (SELECT jsonb_agg(to_jsonb(r) ORDER BY i) FROM resultados r));")
    cuerpo.append("ROLLBACK;")
    resultado = como_el_rol("\n".join(cuerpo))
    if resultado.returncode != 0:
        raise AssertionError(f"el lote de operaciones no se pudo ejecutar: {resultado.stderr.strip()}")
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip().startswith("{")]
    datos = json.loads(lineas[-1])
    datos["por_clave"] = {sentencias[fila["i"]][0]: fila for fila in datos["resultados"]}
    return datos


class OperacionesComoElRolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lote = lote_de_operaciones()

    def test_la_sesion_es_realmente_la_del_rol_y_no_la_de_un_superusuario(self):
        self.assertEqual((self.lote["usuario"], self.lote["sesion"], self.lote["superusuario"]), (READER, READER, "off"))
        self.assertEqual(len(self.lote["resultados"]), len(DENEGADAS) + len(PERMITIDAS))

    def test_cada_operacion_prohibida_falla_por_falta_de_privilegios(self):
        for clave, sentencia in DENEGADAS:
            with self.subTest(operacion=clave):
                resultado = self.lote["por_clave"][clave]
                self.assertEqual(resultado["estado"], "42501", f"{clave}: {sentencia} -> {resultado}")
                self.assertRegex(resultado["mensaje"], DENEGADO, clave)
                if clave in CON_PERMISSION_DENIED:
                    self.assertIn("permission denied", resultado["mensaje"], clave)

    def test_lo_que_debe_poder_hacer_si_lo_hace(self):
        # Guarda anti-vacío: si todo fallara (p. ej. la sesión rota) la prueba anterior pasaría sin demostrar nada. Leer
        # el esquema `evaluation` y usar una tabla temporal propia (el `TEMP` que da PUBLIC) funciona.
        for clave, sentencia in PERMITIDAS:
            with self.subTest(operacion=clave):
                self.assertEqual(self.lote["por_clave"][clave]["estado"], "00000", f"{clave}: {sentencia}")

    def test_alter_system_y_create_database_fuera_de_una_transaccion_tambien_se_rechazan(self):
        # No se pueden ejecutar dentro del bloque de arriba (exigen una sesión sin transacción): sesiones propias.
        for sentencia in ("ALTER SYSTEM SET work_mem = '64MB'", "CREATE DATABASE intruso"):
            with self.subTest(sentencia=sentencia):
                resultado = como_el_rol(sentencia)
                self.assertNotEqual(resultado.returncode, 0, f"{sentencia} se ejecutó")
                self.assertIn("permission denied", resultado.stderr)

    def test_en_una_sesion_propia_las_escrituras_y_la_lectura_de_embeddings_dan_permission_denied(self):
        # Una sentencia por sesión, sin bloque ni transacción: lo que ve de verdad quien se conecta con la contraseña.
        for nombre, sentencia in (("INSERT", ESCRIBIR_RUN), ("TRUNCATE", "TRUNCATE evaluation.runs, evaluation.results"),
                                  ("SELECT de embeddings", "SELECT * FROM public.knowledge_embeddings"),
                                  ("CREATE TABLE", "CREATE TABLE public.intruso (a integer)")):
            with self.subTest(operacion=nombre):
                resultado = como_el_rol(sentencia)
                self.assertNotEqual(resultado.returncode, 0, f"{sentencia} se ejecutó")
                self.assertIn("permission denied", resultado.stderr)
                self.assertEqual(resultado.stdout.strip(), "", "una sentencia rechazada no debe devolver datos")

    def test_los_intentos_no_cambiaron_nada_en_la_base(self):
        self.assertEqual(uno("SELECT count(*) FROM evaluation.runs"), "16")
        self.assertEqual(uno("SELECT count(*) FROM pg_namespace WHERE nspname = 'intruso'"), "0")
        self.assertEqual(uno("SELECT count(*) FROM information_schema.tables WHERE table_name = 'intruso'"), "0")
        self.assertEqual(uno("SELECT count(*) FROM public.knowledge_embeddings"), "1")

    def test_un_grant_hecho_por_el_propio_rol_no_le_concede_nada(self):
        # `GRANT` sin ser propietario ni tener la opción de reconceder no falla (solo avisa): lo que importa es que no se
        # concede nada, ni a él ni a PUBLIC (un rol de control sin concesiones hereda lo que se dé a PUBLIC).
        como_el_rol(f"GRANT ALL ON ALL TABLES IN SCHEMA evaluation TO {READER}; GRANT INSERT ON evaluation.runs TO PUBLIC")
        self.assertEqual(como_tuplas(diferencia_de_relaciones(), "esquema", "relacion", "privilegio"), LECTURAS)
        self.assertEqual(uno(f"SELECT has_table_privilege('{CONTROL}', 'evaluation.runs', 'INSERT')::text"), "false")


# --- Inicio de sesión y contraseñas ------------------------------------------------------------------------------------


class InicioDeSesionTests(unittest.TestCase):
    def test_con_la_contrasena_correcta_entra_y_lee(self):
        self.assertEqual(consulta_del_rol("SELECT current_user"), READER)
        self.assertEqual(consulta_del_rol("SELECT count(*) FROM evaluation.runs"), "16")

    def test_con_una_contrasena_incorrecta_o_sin_contrasena_no_entra(self):
        # Guarda anti-vacío: la conexión es la que comprueba contraseña (la IP del contenedor) y la correcta sí entra.
        self.assertEqual(como_el_rol("SELECT 1").returncode, 0)
        for incorrecta in (_ESTADO["password"] + "x", "otra"):
            with self.subTest(contrasena="distinta"):
                resultado = como_el_rol("SELECT 1", password=incorrecta)
                self.assertNotEqual(resultado.returncode, 0, resultado.stdout)
                self.assertIn("password authentication failed", resultado.stderr)
                self.assertEqual(resultado.stdout.strip(), "")
        sin = como_el_rol("SELECT 1", sin_contrasena=True)
        self.assertNotEqual(sin.returncode, 0, sin.stdout)
        self.assertEqual(sin.stdout.strip(), "")

    def test_no_ve_las_contrasenas_de_los_roles(self):
        # `pg_roles` es legible por todos pero enmascara la contraseña; la tabla real (`pg_authid`) no se puede leer.
        salida = consulta_del_rol("SELECT rolname || '=' || coalesce(rolpassword, 'NULL') FROM pg_roles ORDER BY 1")
        self.assertIn(f"{READER}=********", salida)
        for linea in salida.splitlines():
            self.assertTrue(linea.endswith("=********") or linea.endswith("=NULL"), linea)
        self.assertNotIn("SCRAM", salida)
        self.assertNotIn(_ESTADO["password"], salida)
        denegado = como_el_rol("SELECT rolpassword FROM pg_authid")
        self.assertNotEqual(denegado.returncode, 0)
        self.assertIn("permission denied for table pg_authid", denegado.stderr)


# --- Vistas ------------------------------------------------------------------------------------------------------------


class VistasTests(unittest.TestCase):
    def test_las_vistas_dan_filas_al_rol_las_mismas_que_al_administrador(self):
        # Los datos locales de la prueba dan dos filas a `config_changes` (cambio de modelo y el de batería respecto a la campaña de JUP-071 versionada) y dos a `comparable_runs`.
        for vista, esperado in (("config_changes", "5"), ("comparable_runs", "2")):
            with self.subTest(vista=vista):
                self.assertEqual(uno(f"SELECT count(*) FROM evaluation.{vista}"), esperado)
                self.assertEqual(consulta_del_rol(f"SELECT count(*) FROM evaluation.{vista}"), esperado)

    def test_las_vistas_solo_leen_de_runs_y_no_dan_acceso_a_nada_extra(self):
        dependencias = filas(
            "SELECT DISTINCT v.relname AS vista, d.refobjid::regclass::text AS lee FROM pg_class v "
            "JOIN pg_namespace n ON n.oid = v.relnamespace JOIN pg_rewrite r ON r.ev_class = v.oid "
            "JOIN pg_depend d ON d.objid = r.oid AND d.refclassid = 'pg_class'::regclass "
            "WHERE n.nspname = 'evaluation' AND v.relkind = 'v' AND d.refobjid <> v.oid AND d.deptype = 'n' ORDER BY 1, 2")
        self.assertEqual(como_tuplas(dependencias, "vista", "lee"),
                         [("comparable_runs", "evaluation.runs"), ("config_changes", "evaluation.runs")])
        # Y sobre las vistas solo tiene SELECT: ni un privilegio de escritura ni de `TRIGGER` o `REFERENCES`.
        vistas = ["evaluation.config_changes", "evaluation.comparable_runs"]
        self.assertEqual(privilegios_de(vistas), {vista: ["SELECT"] for vista in vistas})


# --- Objetos creados después -------------------------------------------------------------------------------------------


class ObjetosPosterioresTests(unittest.TestCase):
    CREAR = """
CREATE TABLE evaluation.tabla_posterior (a integer);
CREATE VIEW evaluation.vista_posterior AS SELECT 1 AS a;
CREATE TABLE evaluation.con_serie (id serial, b integer);
CREATE TABLE public.tabla_posterior (a integer);
CREATE VIEW public.vista_posterior AS SELECT 1 AS a;
CREATE TABLE otro.tabla_posterior (a integer);
CREATE SCHEMA nuevo;
CREATE TABLE nuevo.tabla_posterior (a integer);
"""
    BORRAR = """
DROP TABLE IF EXISTS evaluation.tabla_posterior, evaluation.con_serie, public.tabla_posterior, otro.tabla_posterior;
DROP VIEW IF EXISTS evaluation.vista_posterior, public.vista_posterior;
DROP SCHEMA IF EXISTS nuevo CASCADE;
"""

    @classmethod
    def setUpClass(cls):
        server().psql(stdin=cls.BORRAR)
        creado = server().psql(stdin=cls.CREAR)
        if creado.returncode != 0:
            raise RuntimeError(creado.stderr)

    @classmethod
    def tearDownClass(cls):
        server().psql(stdin=cls.BORRAR)

    def test_una_tabla_o_vista_nueva_de_evaluation_nace_legible_solo_con_select(self):
        relaciones = ["evaluation.tabla_posterior", "evaluation.vista_posterior", "evaluation.con_serie"]
        self.assertEqual(privilegios_de(relaciones), {relacion: ["SELECT"] for relacion in relaciones})

    def test_lo_nuevo_de_evaluation_no_nace_legible_para_nadie_mas_que_el_rol_de_grafana(self):
        # Un privilegio por defecto `... TO PUBLIC` haría legible por TODOS los roles lo que se cree después en `evaluation`
        # sin que el rol de Grafana lo delate (él ya lee con su propia regla). El rol de control, sin concesiones, solo puede
        # leer lo que dé PUBLIC: no debe poder leer nada de lo nuevo.
        relaciones = ["evaluation.tabla_posterior", "evaluation.vista_posterior", "evaluation.con_serie"]
        self.assertEqual(privilegios_de(relaciones, rol=CONTROL), {relacion: [] for relacion in relaciones})
        # Y en el propio catálogo de privilegios por defecto solo pueden aparecer el rol de Grafana y, si PostgreSQL la guarda,
        # la entrada del creador: nunca PUBLIC ni otro rol.
        beneficiarios = filas(
            "SELECT DISTINCT CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END AS beneficiario "
            "FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a ORDER BY 1")
        nombres = {fila["beneficiario"] for fila in beneficiarios}
        self.assertIn(READER, nombres)
        self.assertLessEqual(nombres, {READER, "postgres"}, beneficiarios)

    def test_en_otros_esquemas_lo_nuevo_no_nace_legible(self):
        relaciones = ["public.tabla_posterior", "public.vista_posterior", "otro.tabla_posterior", "nuevo.tabla_posterior"]
        self.assertEqual(privilegios_de(relaciones), {relacion: [] for relacion in relaciones})

    def test_la_secuencia_de_una_tabla_nueva_no_es_utilizable_por_el_rol(self):
        for privilegio in ("USAGE", "SELECT", "UPDATE"):
            with self.subTest(privilegio=privilegio):
                self.assertEqual(
                    uno(f"SELECT has_sequence_privilege('{READER}', 'evaluation.con_serie_id_seq', '{privilegio}')::text"), "false")

    def test_el_rol_lee_lo_nuevo_de_evaluation_y_no_lo_de_public(self):
        self.assertEqual(consulta_del_rol("SELECT count(*) FROM evaluation.tabla_posterior"), "0")
        denegado = como_el_rol("SELECT count(*) FROM public.tabla_posterior")
        self.assertNotEqual(denegado.returncode, 0)
        self.assertIn("permission denied", denegado.stderr)


# --- Recargas ------------------------------------------------------------------------------------------------------------


class RecargaTests(unittest.TestCase):
    """Dos cargas más (con contraseñas nuevas), un `TRUNCATE` directo y una carga final: se hacen UNA vez para toda la clase
    (cada carga cuesta unos segundos) y cada prueba mira un aspecto distinto de lo que quedó."""

    @classmethod
    def setUpClass(cls):
        cls.vieja = _ESTADO["password"]
        cls.oid_antes = uno(f"SELECT oid FROM pg_roles WHERE rolname = '{READER}'")
        cls.antes = instantanea()
        cls.login_con_la_vieja_antes = como_el_rol("SELECT 1", password=cls.vieja).returncode
        cargar(secrets.token_urlsafe(24))
        cls.segunda = _ESTADO["password"]
        cls.tras_segunda = instantanea()
        cls.login_vieja_tras_segunda = como_el_rol("SELECT 1", password=cls.vieja)
        cls.login_nueva_tras_segunda = como_el_rol("SELECT 1", password=cls.segunda)
        cargar(secrets.token_urlsafe(24))
        cls.tras_tercera = instantanea()
        cls.login_segunda_tras_tercera = como_el_rol("SELECT 1", password=cls.segunda)
        # `TRUNCATE` directo del administrador: las vistas y las tablas quedan vacías pero los permisos no cambian.
        truncado = server().psql("TRUNCATE evaluation.results, evaluation.runs")
        cls.truncado_ok = truncado.returncode
        cls.tras_truncate = instantanea()
        # Sin lanzar si el rol no puede entrar: el fallo lo debe señalar la prueba que mira este resultado, no la preparación.
        cls.filas_tras_truncate = {tabla: como_el_rol(f"SELECT count(*) FROM evaluation.{tabla}").stdout.strip()
                                   for tabla in ("runs", "results", "config_changes", "comparable_runs")}
        cargar(secrets.token_urlsafe(24))  # deja la base cargada para el resto de las pruebas
        cls.oid_despues = uno(f"SELECT oid FROM pg_roles WHERE rolname = '{READER}'")

    def test_tras_otra_carga_los_privilegios_son_identicos_y_no_se_acumulan(self):
        # Precondición: la instantánea no está vacía (de lo contrario «idéntico» no demostraría nada).
        self.assertEqual(como_tuplas(self.antes["relaciones"], "esquema", "relacion", "privilegio"), LECTURAS)
        self.assertEqual(len(self.antes["privilegios_por_defecto"]), 1)
        self.assertEqual(len(self.antes["acl_de_evaluation"]), 4)
        self.assertEqual(self.tras_segunda, self.antes)

    def test_una_tercera_carga_tampoco_acumula_entradas_en_las_acl(self):
        # Las ACL siguen siendo las mismas entradas, no copias repetidas de la misma concesión.
        self.assertEqual(self.tras_tercera, self.antes)

    def test_la_carga_rota_la_contrasena(self):
        self.assertEqual(self.login_con_la_vieja_antes, 0, "precondición: la contraseña inicial servía")
        self.assertNotEqual(self.vieja, self.segunda)
        self.assertNotEqual(self.login_vieja_tras_segunda.returncode, 0)
        self.assertIn("password authentication failed", self.login_vieja_tras_segunda.stderr)
        self.assertEqual(self.login_nueva_tras_segunda.returncode, 0, self.login_nueva_tras_segunda.stderr)
        # Y la tercera carga volvió a rotarla: la segunda ya no sirve.
        self.assertNotEqual(self.login_segunda_tras_tercera.returncode, 0)
        self.assertIn("password authentication failed", self.login_segunda_tras_tercera.stderr)

    def test_un_truncate_directo_conserva_los_privilegios_y_el_rol_sigue_leyendo(self):
        self.assertEqual(self.truncado_ok, 0)
        self.assertEqual(self.tras_truncate, self.antes)
        self.assertEqual(self.filas_tras_truncate, {"runs": "0", "results": "0", "config_changes": "0", "comparable_runs": "0"})

    def test_la_carga_no_recrea_el_rol_y_conserva_su_identidad(self):
        # Una recarga adopta el rol existente (solo cambia su contraseña): si lo borrara y lo creara de nuevo cambiaría su
        # identificador y se perderían las concesiones que Grafana ya usa.
        self.assertEqual(self.oid_despues, self.oid_antes)


if __name__ == "__main__":
    unittest.main()
