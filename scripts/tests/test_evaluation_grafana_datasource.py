"""Datasource PostgreSQL de Grafana para el esquema `evaluation` (JUP-121, tarea 4.1, Red).

La tarea 4.1 provisiona en Grafana 11.3.0 un segundo datasource, de solo lectura, que consulta el esquema
`evaluation` de `postgres-pgvector` con el rol `grafana_evaluation_reader` (tarea 3.3, decisión ADR-0022). La
contraseña llega por la variable `GRAFANA_EVALUATION_DB_PASSWORD`, la misma que usa la carga (`load`). Este fichero
no carga la herramienta ni necesita Docker: lee `docker-compose.yml`, `.env.example`, el YAML del datasource y la
guía con la biblioteca estándar (recorrido por líneas y expresiones regulares, sin YAML externo).

Contrato que se valida:

* `apps/monitoring/grafana/provisioning/datasources/evaluation-postgres.yml`: `apiVersion: 1` y UN datasource
  `Evaluacion` (uid `evaluation-postgres`, tipo `grafana-postgresql-datasource`, acceso `proxy`, URL
  `postgres-pgvector:5432`, usuario `grafana_evaluation_reader`, no editable, SIN `isDefault: true`), con
  `jsonData` (`database: embeddings`, `sslmode: disable`, `postgresVersion: 1700`, `timescaledb: false` y límites
  de conexiones acotados) y `secureJsonData.password` como interpolación de variable de entorno de Grafana. La
  contraseña jamás va en claro. El datasource de Prometheus sigue intacto y es el predeterminado.
* `docker-compose.yml`: solo el servicio `grafana` recibe `GRAFANA_EVALUATION_DB_PASSWORD` con `:?required`
  (rechaza ausente y vacía; Compose se niega a arrancar y nombra la variable). Sin `depends_on` nuevos (el
  datasource se conecta al primer uso), sin puertos nuevos y con el resto del servicio y de `postgres-pgvector`
  idénticos.
* `.env.example`: la línea `GRAFANA_EVALUATION_DB_PASSWORD=` (sin valor) justo después de
  `GRAFANA_ADMIN_PASSWORD=`, una sola vez; se conservan las variables previas relevantes y se permiten
  ampliaciones independientes.
* La guía `docs/validation/evaluation-dashboard.md` nombra la variable y el datasource `evaluation-postgres`.

Rutas: por defecto los ficheros reales del repositorio. `EVALUATION_COMPOSE_YML`, `EVALUATION_ENV_EXAMPLE`,
`EVALUATION_DATASOURCE_YML` y `EVALUATION_DOC` permiten apuntar a copias (sirven para comprobar que los esperados
son alcanzables y que cada mutación se detecta).

Decisiones donde el enunciado admitía más de una lectura:

* El nombre visible del datasource es `Evaluacion` (sin tilde, para que no dependa de la codificación).
* `maxOpenConns` en 1..10, `maxIdleConns` en 1..`maxOpenConns` y `connMaxLifetime` entero en 60..14400 segundos;
  son límites razonables para un panel de solo lectura, no valores únicos.
* `password` admite `$VAR` o `${VAR}`, con o sin comillas dobles.
* El resto del servicio `grafana`, el servicio `postgres-pgvector`, el datasource de Prometheus y el dashboard
  técnico se fijan con su contenido de hoy (pasan hoy y deben seguir pasando).
"""

import hashlib
import os
import re
import unittest
from pathlib import Path

# Raíz del repositorio deducida de este fichero (scripts/tests/ -> raíz).
REPO_ROOT = Path(__file__).resolve().parents[2]
GRAFANA_DIR = REPO_ROOT / "apps" / "monitoring" / "grafana"

COMPOSE_YML = Path(os.environ.get("EVALUATION_COMPOSE_YML") or REPO_ROOT / "docker-compose.yml")
ENV_EXAMPLE = Path(os.environ.get("EVALUATION_ENV_EXAMPLE") or REPO_ROOT / ".env.example")
DATASOURCE_YML = Path(
    os.environ.get("EVALUATION_DATASOURCE_YML")
    or GRAFANA_DIR / "provisioning" / "datasources" / "evaluation-postgres.yml"
)
DOC = Path(os.environ.get("EVALUATION_DOC") or REPO_ROOT / "docs" / "validation" / "evaluation-dashboard.md")
# Ficheros que esta tarea NO toca (siempre los reales).
PROMETHEUS_YML = GRAFANA_DIR / "provisioning" / "datasources" / "prometheus.yml"
DATASOURCES_DIR = GRAFANA_DIR / "provisioning" / "datasources"
TECHNICAL_DASHBOARD = GRAFANA_DIR / "dashboards" / "technical-metrics.json"

VARIABLE = "GRAFANA_EVALUATION_DB_PASSWORD"
COMPOSE_LINE = "GRAFANA_EVALUATION_DB_PASSWORD: ${GRAFANA_EVALUATION_DB_PASSWORD:?required}"
ENV_LINE = "GRAFANA_EVALUATION_DB_PASSWORD="
PASSWORD_VALUES = ("$GRAFANA_EVALUATION_DB_PASSWORD", "${GRAFANA_EVALUATION_DB_PASSWORD}")

# Datasource de Prometheus tal como está hoy (no debe cambiar).
PROMETHEUS_TEXT = (
    "apiVersion: 1\n"
    "\n"
    "datasources:\n"
    "  - name: Prometheus\n"
    "    uid: prometheus\n"
    "    type: prometheus\n"
    "    access: proxy\n"
    "    url: http://prometheus:9090\n"
    "    isDefault: true\n"
)

# Servicio `grafana` de hoy, sin la variable nueva (el resto del bloque no debe cambiar).
GRAFANA_BLOCK_TODAY = [
    "  grafana:",
    "    image: grafana/grafana:11.3.0",
    "    environment:",
    "      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}",
    "      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:?required}",
    '      GF_AUTH_ANONYMOUS_ENABLED: "false"',
    "    volumes:",
    "      - ./apps/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro",
    "      - ./apps/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro",
    "      - grafana-data:/var/lib/grafana",
    "    depends_on:",
    "      prometheus:",
    "        condition: service_healthy",
    "    ports:",
    '      - "127.0.0.1:${GRAFANA_PORT:-3000}:3000"',
]

# SHA-256 del servicio `postgres-pgvector` (líneas unidas con `\n`) y del dashboard técnico, tal como están hoy.
POSTGRES_BLOCK_SHA256 = "6e91e98f0ed2ec1dc8dd321c3079361431d3d488c151372a3e8423fc8cae8aab"
TECHNICAL_DASHBOARD_SHA256 = "d9560fdca39be806fa66268a4950de7a3f1a2bb94adabeeda0534b2b8ee70976"

# Declaraciones previas relevantes: se conservan sin limitar ampliaciones independientes de `.env.example`.
ENV_REQUIRED_LITERALS = [
    "GRAFANA_ADMIN_PASSWORD=",
    "POSTGRES_PASSWORD=",
    "RABBITMQ_ERLANG_COOKIE=",
    "PGVECTOR_PORT=5433",
    "EMBEDDING_PROVIDER=mock",
]


def _leer(ruta):
    """Lee un fichero de texto; si no existe falla con una aserción (Red legible, no un error de E/S)."""
    if not ruta.is_file():
        raise AssertionError(f"no existe el fichero esperado: {ruta}")
    return ruta.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _lineas(ruta):
    return _leer(ruta).splitlines()


def _sangria(linea):
    return len(linea) - len(linea.lstrip(" "))


def _bloque_servicio(lineas, nombre):
    """Líneas del servicio `nombre` de Compose: de `  nombre:` hasta la siguiente línea de sangría <= 2."""
    inicio = next((i for i, linea in enumerate(lineas) if linea == f"  {nombre}:"), None)
    if inicio is None:
        raise AssertionError(f"no se encuentra el servicio `{nombre}` en {COMPOSE_YML}")
    fin = inicio + 1
    while fin < len(lineas) and (lineas[fin].strip() == "" or _sangria(lineas[fin]) > 2):
        fin += 1
    bloque = lineas[inicio:fin]
    while bloque and bloque[-1].strip() == "":
        bloque.pop()
    return bloque


def _nombres_de_servicios(lineas):
    """Nombres de los servicios: líneas `  nombre:` dentro de `services:` (hasta la siguiente clave de raíz)."""
    inicio = lineas.index("services:")
    nombres = []
    for linea in lineas[inicio + 1 :]:
        if linea and not linea.startswith(" ") and not linea.startswith("#"):
            break
        coincidencia = re.fullmatch(r"  ([\w.-]+):", linea)
        if coincidencia:
            nombres.append(coincidencia.group(1))
    return nombres


def _subseccion(bloque, clave):
    """Líneas (con su sangría original) bajo `    clave:` de un servicio, mientras tengan más de 4 espacios."""
    inicio = next((i for i, linea in enumerate(bloque) if linea == f"    {clave}:"), None)
    if inicio is None:
        return None
    resultado = []
    for linea in bloque[inicio + 1 :]:
        if linea.strip() == "" or _sangria(linea) <= 4:
            break
        resultado.append(linea)
    return resultado


def _sin_comillas(valor):
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return valor[1:-1]
    return valor


def _parsear_datasource(texto):
    """Mini analizador del YAML de provisionamiento: mapas anidados de escalares y elementos de lista `- `.

    Devuelve (árbol, número de elementos de lista). Rechaza claves repetidas en el mismo mapa: un fichero con dos
    datasources o con `password` dos veces no se confunde con uno bueno por sobrescritura silenciosa.
    """
    raiz = {}
    pila = [(-1, raiz)]
    elementos = 0
    for cruda in texto.splitlines():
        if cruda.strip() == "" or cruda.lstrip().startswith("#"):
            continue
        sangria = _sangria(cruda)
        contenido = cruda.strip()
        if contenido.startswith("- "):
            elementos += 1
            sangria += 2
            contenido = contenido[2:]
        clave, separador, valor = contenido.partition(":")
        if not separador:
            raise AssertionError(f"línea que no es `clave: valor`: {cruda!r}")
        while pila[-1][0] >= sangria:
            pila.pop()
        padre = pila[-1][1]
        if clave in padre:
            raise AssertionError(f"clave repetida en el mismo nivel: {clave!r}")
        valor = valor.strip()
        if valor == "":
            hijo = {}
            padre[clave] = hijo
            pila.append((sangria, hijo))
        else:
            padre[clave] = _sin_comillas(valor)
    return raiz, elementos


def _datasource():
    """Devuelve el único datasource del fichero como diccionario (exige apiVersion 1 y un solo elemento)."""
    arbol, elementos = _parsear_datasource(_leer(DATASOURCE_YML))
    if elementos != 1:
        raise AssertionError(f"el fichero debe declarar exactamente un datasource, hay {elementos}")
    return arbol


def _plano(arbol):
    """Aplana el árbol al estilo `datasources.name`; los elementos de lista comparten el mapa `datasources`."""
    return arbol["datasources"]


class FicheroDelDatasourceTests(unittest.TestCase):
    """Forma y contenido de `evaluation-postgres.yml`."""

    def test_el_fichero_existe_en_el_directorio_de_provisionamiento(self):
        # Grafana lee todo el directorio montado en /etc/grafana/provisioning/datasources.
        self.assertTrue(DATASOURCE_YML.is_file(), f"falta {DATASOURCE_YML}")

    def test_el_directorio_solo_tiene_prometheus_y_el_nuevo(self):
        # Ningún otro fichero de datasource se cuela (p. ej. una copia de seguridad que Grafana también cargaría).
        nombres = {p.name for p in DATASOURCES_DIR.iterdir()}
        if DATASOURCE_YML.parent != DATASOURCES_DIR:
            # Con una copia apuntada por variable de entorno, el fichero real no existe: se da por presente.
            nombres.add("evaluation-postgres.yml")
        self.assertEqual(sorted(nombres), ["evaluation-postgres.yml", "prometheus.yml"])

    def test_formato_sin_tabuladores_con_sangria_de_dos_espacios_y_ascii(self):
        # YAML prohíbe tabuladores de sangría; la sangría es de 2 espacios como en prometheus.yml; el fichero es
        # ASCII (el nombre del datasource no lleva tilde), acaba en un único salto de línea y no tiene CR ni
        # espacios al final de línea.
        crudo = DATASOURCE_YML.read_bytes() if DATASOURCE_YML.is_file() else None
        self.assertIsNotNone(crudo, f"falta {DATASOURCE_YML}")
        self.assertNotIn(b"\t", crudo)
        self.assertNotIn(b"\r", crudo)
        crudo.decode("ascii")  # lanza UnicodeDecodeError si hay algún carácter no ASCII
        texto = crudo.decode("ascii")
        self.assertTrue(texto.endswith("\n") and not texto.endswith("\n\n"))
        for linea in texto.splitlines():
            with self.subTest(linea=linea):
                self.assertEqual(_sangria(linea) % 2, 0)
                self.assertEqual(linea, linea.rstrip())

    def test_api_version_1_y_un_unico_datasource(self):
        arbol, elementos = _parsear_datasource(_leer(DATASOURCE_YML))
        self.assertEqual(arbol.get("apiVersion"), "1")
        self.assertEqual(list(arbol), ["apiVersion", "datasources"])
        self.assertEqual(elementos, 1)

    def test_identidad_del_datasource(self):
        # Valores exactos: el dashboard referenciará el uid, y el tipo debe ser el plugin PostgreSQL nativo de
        # Grafana 11 (`postgres` es el nombre antiguo del plugin).
        ds = _plano(_datasource())
        self.assertEqual(ds.get("name"), "Evaluacion")
        self.assertEqual(ds.get("uid"), "evaluation-postgres")
        self.assertEqual(ds.get("type"), "grafana-postgresql-datasource")
        self.assertEqual(ds.get("access"), "proxy")

    def test_conexion_al_servicio_postgres_con_el_rol_de_solo_lectura(self):
        ds = _plano(_datasource())
        self.assertEqual(ds.get("url"), "postgres-pgvector:5432")
        self.assertEqual(ds.get("user"), "grafana_evaluation_reader")

    def test_no_editable(self):
        # Un datasource provisionado de solo lectura no se puede alterar desde la interfaz.
        self.assertEqual(_plano(_datasource()).get("editable"), "false")

    def test_no_es_el_datasource_predeterminado(self):
        # El predeterminado sigue siendo Prometheus: el dashboard técnico depende de ello. Se admite
        # `isDefault: false` explícito o la ausencia de la clave, nunca `true`.
        ds = _plano(_datasource())
        self.assertIn(ds.get("isDefault", "false"), ("false",))
        self.assertNotRegex(_leer(DATASOURCE_YML), r"(?im)^\s*isDefault\s*:\s*[\"']?true")

    def test_json_data_con_la_base_el_ssl_y_la_version(self):
        # `sslmode: disable` porque el tráfico no sale de la red de Compose; la versión 1700 es PostgreSQL 17
        # (imagen pgvector:pg17); sin TimescaleDB.
        datos = _plano(_datasource()).get("jsonData")
        self.assertIsInstance(datos, dict)
        self.assertEqual(datos.get("database"), "embeddings")
        self.assertEqual(datos.get("sslmode"), "disable")
        self.assertEqual(datos.get("postgresVersion"), "1700")
        self.assertEqual(datos.get("timescaledb"), "false")

    def test_limites_de_conexiones_acotados(self):
        # Un panel de solo lectura no necesita muchas conexiones: se acota el máximo para no agotar las del
        # servidor, y se cierran las inactivas con un tiempo de vida razonable.
        datos = _plano(_datasource()).get("jsonData") or {}
        for clave in ("maxOpenConns", "maxIdleConns", "connMaxLifetime"):
            self.assertRegex(datos.get(clave, ""), r"[0-9]+", f"{clave} debe ser un entero")
        abiertas = int(datos["maxOpenConns"])
        inactivas = int(datos["maxIdleConns"])
        vida = int(datos["connMaxLifetime"])
        self.assertTrue(1 <= abiertas <= 10, abiertas)
        self.assertTrue(1 <= inactivas <= abiertas, inactivas)
        self.assertTrue(60 <= vida <= 14400, vida)

    def test_la_contrasena_es_una_interpolacion_de_variable_de_entorno(self):
        # `secureJsonData.password` toma el valor de la variable de entorno del contenedor de Grafana.
        seguro = _plano(_datasource()).get("secureJsonData")
        self.assertIsInstance(seguro, dict)
        self.assertEqual(list(seguro), ["password"])
        self.assertIn(seguro["password"], PASSWORD_VALUES)

    def test_password_es_la_unica_linea_con_ese_texto_y_nunca_en_claro(self):
        # Defensa contra credenciales en claro: exactamente una línea menciona `password` (sin distinguir
        # mayúsculas) y es la clave de `secureJsonData`; fuera del nombre de la variable no aparece `PASSWORD`;
        # la contraseña no se repite en `jsonData` ni en otro campo.
        texto = _leer(DATASOURCE_YML)
        con_password = [l for l in texto.splitlines() if re.search("password", l, re.IGNORECASE)]
        self.assertEqual(len(con_password), 1, con_password)
        self.assertRegex(con_password[0], r"^ {6}password: [\"']?\$\{?GRAFANA_EVALUATION_DB_PASSWORD\}?[\"']?$")
        self.assertNotIn("PASSWORD", texto.replace(VARIABLE, ""))
        self.assertNotRegex(texto, r"(?i)\b(secret|token|apikey|api_key)\b")

    def test_la_variable_aparece_una_sola_vez_en_el_datasource(self):
        self.assertEqual(_leer(DATASOURCE_YML).count(VARIABLE), 1)

    def test_ningun_valor_parece_una_credencial(self):
        # Ningún valor escalar salvo la interpolación contiene un literal opaco largo (cadena de >= 20
        # caracteres alfanuméricos sin guiones ni dos puntos, típica de claves) ni una URL con usuario:clave@.
        texto = _leer(DATASOURCE_YML)
        self.assertNotRegex(texto, r"://[^/\s]*:[^/\s]*@")
        for linea in texto.splitlines():
            valor = linea.partition(":")[2].strip()
            if valor in PASSWORD_VALUES:
                continue
            with self.subTest(linea=linea):
                self.assertNotRegex(valor, r"^[A-Za-z0-9+/=]{20,}$")


class PrometheusIntactoTests(unittest.TestCase):
    """Estos tests pasan hoy y deben seguir pasando: la tarea no toca lo que ya existe."""

    def test_el_datasource_de_prometheus_no_cambia(self):
        self.assertEqual(PROMETHEUS_YML.read_bytes().decode("utf-8").replace("\r\n", "\n"), PROMETHEUS_TEXT)

    def test_prometheus_sigue_siendo_el_predeterminado_con_uid_prometheus(self):
        arbol, _ = _parsear_datasource(PROMETHEUS_YML.read_text(encoding="utf-8"))
        ds = arbol["datasources"]
        self.assertEqual(ds["uid"], "prometheus")
        self.assertEqual(ds["isDefault"], "true")

    def test_el_dashboard_tecnico_y_su_provisionamiento_siguen_como_estaban(self):
        # El dashboard técnico usa el datasource predeterminado; si cambiara su JSON, la tarea habría tocado algo
        # ajeno. Se fija su huella y que sigue sin referenciar el datasource nuevo.
        normalizado = TECHNICAL_DASHBOARD.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(normalizado).hexdigest(), TECHNICAL_DASHBOARD_SHA256)
        self.assertNotIn(b"evaluation-postgres", normalizado)

    def test_los_dos_datasources_no_comparten_uid_ni_nombre(self):
        # Dos datasources con el mismo uid o nombre harían que Grafana rechazara el provisionamiento o que uno
        # pisara al otro.
        nuevo = _plano(_datasource())
        antiguo = _parsear_datasource(PROMETHEUS_YML.read_text(encoding="utf-8"))[0]["datasources"]
        self.assertNotEqual(nuevo.get("uid"), antiguo["uid"])
        self.assertNotEqual(nuevo.get("name"), antiguo["name"])
        self.assertTrue(nuevo.get("uid"))
        self.assertTrue(nuevo.get("name"))


class ComposeTests(unittest.TestCase):
    """Servicio `grafana` de `docker-compose.yml`."""

    def setUp(self):
        self.lineas = _lineas(COMPOSE_YML)
        self.grafana = _bloque_servicio(self.lineas, "grafana")

    def test_grafana_recibe_la_variable_requerida_en_environment(self):
        # `:?required` rechaza la variable ausente Y vacía (como las demás credenciales), y Compose indica qué
        # variable falta. La línea va dentro de `environment`, con la sangría de las otras variables.
        entorno = _subseccion(self.grafana, "environment")
        self.assertIsNotNone(entorno)
        self.assertIn("      " + COMPOSE_LINE, entorno)

    def test_la_variable_aparece_una_sola_vez_en_todo_el_compose(self):
        # En un único servicio y una única línea: ningún otro contenedor recibe la contraseña de lectura.
        con_variable = [l for l in self.lineas if VARIABLE in l]
        self.assertEqual(con_variable, ["      " + COMPOSE_LINE])

    def test_ningun_otro_servicio_recibe_la_variable(self):
        # Comprobación por servicio, con mensaje claro del culpable, incluida la forma `${VAR...}` en `environment`
        # de cualquier otro servicio (incluido postgres-pgvector, que no se toca).
        servicios = _nombres_de_servicios(self.lineas)
        self.assertIn("grafana", servicios)
        self.assertIn("postgres-pgvector", servicios)
        for nombre in servicios:
            if nombre == "grafana":
                continue
            with self.subTest(servicio=nombre):
                self.assertNotIn(VARIABLE, "\n".join(_bloque_servicio(self.lineas, nombre)))

    def test_depends_on_de_grafana_sigue_siendo_solo_prometheus(self):
        # El datasource se conecta al primer uso: Grafana no espera a PostgreSQL. Un `depends_on` nuevo (p. ej.
        # postgres-pgvector) acoplaría el arranque del panel técnico a la base de datos.
        dependencias = _subseccion(self.grafana, "depends_on")
        self.assertEqual(dependencias, ["      prometheus:", "        condition: service_healthy"])

    def test_no_se_publican_puertos_nuevos(self):
        self.assertEqual(
            _subseccion(self.grafana, "ports"),
            ['      - "127.0.0.1:${GRAFANA_PORT:-3000}:3000"'],
        )
        self.assertFalse([l for l in self.grafana if l.startswith("    expose:")])

    def test_las_demas_variables_de_grafana_siguen_intactas(self):
        entorno = _subseccion(self.grafana, "environment")
        self.assertIsNotNone(entorno)
        for linea in (
            "      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}",
            "      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:?required}",
            '      GF_AUTH_ANONYMOUS_ENABLED: "false"',
        ):
            with self.subTest(linea=linea):
                self.assertIn(linea, entorno)

    def test_el_resto_del_servicio_grafana_no_cambia(self):
        # Con la línea nueva quitada, el bloque es idéntico al de hoy (misma imagen, volúmenes, dependencias y
        # puertos, sin claves añadidas).
        resto = [l for l in self.grafana if VARIABLE not in l]
        self.assertEqual(resto, GRAFANA_BLOCK_TODAY)

    def test_postgres_pgvector_no_se_toca(self):
        bloque = _bloque_servicio(self.lineas, "postgres-pgvector")
        self.assertEqual(hashlib.sha256("\n".join(bloque).encode()).hexdigest(), POSTGRES_BLOCK_SHA256)


class EnvExampleTests(unittest.TestCase):
    """`.env.example` declara la variable vacía junto a la contraseña de administración de Grafana."""

    def setUp(self):
        self.lineas = _lineas(ENV_EXAMPLE)

    def test_la_linea_existe_exacta_y_una_sola_vez(self):
        # Sin valor (el fichero de ejemplo nunca lleva secretos) y sin duplicados ni comentarios que la nombren.
        con_variable = [l for l in self.lineas if VARIABLE in l]
        self.assertEqual(con_variable, [ENV_LINE])

    def test_va_justo_despues_de_grafana_admin_password(self):
        self.assertEqual(self.lineas.count("GRAFANA_ADMIN_PASSWORD="), 1)
        posicion = self.lineas.index("GRAFANA_ADMIN_PASSWORD=")
        self.assertEqual(self.lineas[posicion + 1 : posicion + 2], [ENV_LINE])

    def test_las_variables_previas_relevantes_se_conservan(self):
        # Cada declaración relevante sigue siendo única; otras funcionalidades pueden añadir variables.
        for linea in ENV_REQUIRED_LITERALS:
            with self.subTest(linea=linea):
                self.assertEqual(self.lineas.count(linea), 1)


class DocumentacionTests(unittest.TestCase):
    def test_la_guia_nombra_la_variable_y_el_datasource(self):
        # La guía de validación debe explicar la contraseña (ya lo hace) y el datasource que lee la base.
        texto = _leer(DOC)
        self.assertIn(VARIABLE, texto)
        self.assertIn("evaluation-postgres", texto)


if __name__ == "__main__":
    unittest.main()
