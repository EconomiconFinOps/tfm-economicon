"""Remediación del QA de las tareas 4.2/4.3 de JUP-121: lo que el dashboard de evaluación MUESTRA (Red).

Los dos módulos hermanos (`test_evaluation_dashboard_structure.py` y `test_evaluation_dashboard_queries.py`) están
congelados. Este módulo fija, SIN tocarlos, cuatro contratos que el QA encontró sin cubrir. Reutiliza de ellos el
localizador de paneles (`S.buscar`, `S._unico`...) y las piezas puras de las consultas (macros, fábricas de filas,
comparaciones); el servidor PostgreSQL desechable es PROPIO de este módulo (uno por módulo, perezoso, siempre
limpiado), así que no comparte contenedor ni estado con el módulo de consultas.

* M2 (series de evolución, a5 automática y a6 juicio humano). Spec: «Una serie con una sola ejecución, o sin otra
  comparable, muestra "Sin datos: no hay con qué comparar" y no dibuja una línea ni un punto». Una serie es
  `comparability_key` + `metric_id` + `behavior`. Contrato: la consulta devuelve una serie SOLO si tiene al menos dos
  puntos MEDIDOS (en a6, al menos dos puntos de ejecuciones de hito). Ni la métrica `not_measured` de una de las dos
  ejecuciones ni una ejecución que no es de hito pueden dejar un punto suelto. Una métrica no medida en el medio de
  una serie no se interpola: la serie se dibuja con los puntos medidos.
* M1 (metadatos del resultado). Tarjeta: «Cada resultado se muestra con su batería, versión, commit, modelo y
  fecha». Las consultas de las tablas de calidad (a3), latencia y campaña (a4), calibración (a7), benchmark (a8), robustez (a9) y la de negocio (B) devuelven,
  además de lo que ya devolvían, las columnas `run_at`, `suite_version`, `commit_sha` y `generation_model`. Un
  metadato que la ejecución no registró llega NULL o `no registrado` (`run_at`, que es una fecha, solo NULL) y nunca
  un valor inventado o heredado de otra ejecución. En B el commit y el modelo pueden ser NULL; `suite_version` no
  (lo trae JUP-068). a1 y a2 ya las traen.
* M3 y M4: guardas que hoy pasan y matan mutantes (unidad y filtro de las series, texto de las tasas, anotación
  limitada a las dos series, ventana `1h` de las señales en vivo, series y anotación sin `$__timeFilter`).
* L4: la tabla de B muestra todas sus filas sin desplazarse y las tablas anchas de A ocupan el ancho completo.

Concreciones del contrato (el coder debe respetarlas):

* Las columnas nuevas se llaman exactamente `run_at`, `suite_version`, `commit_sha`, `generation_model`.
* a5 y a6 siguen devolviendo exactamente `time`, `metric`, `value`; la serie es el conjunto de filas con el mismo texto
  de `metric`. Ese texto NUNCA se comparte entre dos series y nombra el identificador de la métrica y la fuente; las
  series de ejecuciones no reales llevan `no real`.
* El texto formateado de una tasa (`valor_texto` de a3) se localiza como la celda de texto de la fila que coincide con
  `51.0 %` (separador decimal tolerante, espacio normal o duro): no se fija el nombre de la columna.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON` (como en los demás módulos) para comprobar una copia corregida o mutada.
Ejecución: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s scripts/tests -p test_evaluation_dashboard_visible.py -v`
"""
from __future__ import annotations

import json
import re
import secrets
import sys
import tempfile
import unittest
from pathlib import Path

# `unittest discover -s scripts/tests` ya pone este directorio en `sys.path`; se añade también para ejecutar el fichero suelto.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402  (contenedor desechable compartido con los demás módulos)
import test_evaluation_dashboard_queries as Q  # noqa: E402  (macros, fábricas de filas y comparaciones puras)
import test_evaluation_dashboard_structure as S  # noqa: E402  (localizador de paneles del contrato)

tool = Q.tool
TIMESTAMPTZ = Q.TIMESTAMPTZ
METADATOS = ("run_at", "suite_version", "commit_sha", "generation_model")


# --- Servidor propio: uno por módulo, perezoso y siempre limpiado ----------------------------------------------------

_SERVER: dict = {}
_ESTADO: dict = {"conjunto": None, "rol": False}
_RESULTADOS: dict = {}


def server() -> evaluation_pg_helper.PostgresServer:
    """Servidor del módulo; se crea en la primera petición. Si no hay Docker, el test con base se salta."""
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
    # Además del `atexit` del ayudante: el contenedor desaparece al acabar el módulo aunque algún test falle.
    instance = _SERVER.pop("instance", None)
    if instance is not None:
        instance.stop()


class Conjunto:
    """Conjunto de datos con nombre; `cargar()` lo deja cargado (vacía lo anterior) y crea el rol de lectura."""

    def __init__(self, clave, fabrica):
        self.clave = clave
        self.fabrica = fabrica

    def cargar(self) -> None:
        servidor = server()
        if _ESTADO["conjunto"] == self.clave:
            return
        servidor.load_dataset(self.fabrica(), tool)
        _ESTADO["conjunto"] = self.clave
        if not _ESTADO["rol"]:
            # Contraseña aleatoria que solo vive en esta sesión; los privilegios sobreviven a las recargas.
            resultado = servidor.psql(stdin=tool.build_role_sql(secrets.token_urlsafe(18)))
            if resultado.returncode != 0:
                raise RuntimeError(f"no se pudo crear el rol de lectura: {resultado.stderr.strip()}")
            _ESTADO["rol"] = True


def ejecutar(sql: str, conjunto: Conjunto) -> dict:
    """Ejecuta `sql` (tal cual está en el dashboard) con el rol de solo lectura y devuelve columnas y filas tipadas."""
    clave = (conjunto.clave, sql)
    if clave in _RESULTADOS:
        return _RESULTADOS[clave]
    cuerpo = Q.sustituir_macros(sql).strip()
    cuerpo = cuerpo[:-1] if cuerpo.endswith(";") else cuerpo
    conjunto.cargar()
    guion = (
        f"SET ROLE {tool.READER_ROLE};\n"
        f"CREATE TEMP TABLE q AS\n{cuerpo}\n;\n"
        "SELECT jsonb_build_object("
        "'cols', (SELECT jsonb_agg(jsonb_build_array(a.attname::text, format_type(a.atttypid, a.atttypmod)) "
        "ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid = 'pg_temp.q'::regclass "
        "AND a.attnum > 0 AND NOT a.attisdropped), "
        "'rows', (SELECT COALESCE(jsonb_agg(to_jsonb(q)), '[]'::jsonb) FROM q));\n"
    )
    resultado = server().psql(stdin=guion)
    if resultado.returncode != 0:
        raise Q.ConsultaFallida(f"la consulta falló: {resultado.stderr.strip()}\n--- SQL ---\n{cuerpo}")
    lineas = [linea for linea in resultado.stdout.split("\n") if linea.strip()]
    datos = json.loads(lineas[-1])
    salida = {"columnas": [tuple(c) for c in datos["cols"]], "filas": datos["rows"]}
    _RESULTADOS[clave] = salida
    return salida


def de_panel(clave: str, conjunto: Conjunto) -> dict:
    return ejecutar(Q.consulta_panel(S._unico(clave)), conjunto)


def base_de_datos(sql: str, conjunto: Conjunto) -> list:
    """Filas de una consulta del propio test (rol administrador) sobre `conjunto`, que se carga si no lo está.

    Los resultados de los paneles se guardan en caché y no recargan la base: sin pedir aquí el conjunto, un test que
    llegara con la caché llena leería los datos del conjunto cargado por otro test.
    """
    conjunto.cargar()
    resultado = server().psql(f"SELECT COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb) FROM ({sql}) t;")
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip())
    return json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])


def runs_de_la_base(conjunto: Conjunto) -> dict:
    filas = base_de_datos(
        "SELECT run_id, source, run_at, is_real, non_real_reasons, comparability_key, milestone, commit_sha, "
        "suite, suite_version, generation_model FROM evaluation.runs", conjunto)
    return {fila["run_id"]: fila for fila in filas}


# --- Conjunto SINTÉTICO de evolución: series fabricadas para forzar cada caso límite --------------------------------


def _dia(numero):
    """Instante UTC del `numero`-ésimo día de octubre de 2026 a las 10:00: cada ejecución tiene el suyo."""
    return f"2026-10-{numero:02d}T10:00:00Z"


def _tasa(metric_id, juicio, valor, behavior="all"):
    grupo = "accuracy" if metric_id.startswith("ACC") else "relevance"
    return {**Q.fila_tasa(metric_id, grupo, juicio, valor), "behavior": behavior}


# Cada entrada: id, fuente, día, hito, campos de la ejecución que cambian, filas de tasa
# `(métrica, juicio, comportamiento, valor)` (`None` = métrica NO medida). `LAT-1` en ms se añade a la serie EV-A.
# Las claves de comparabilidad salen de fuente, batería, modelo, recuperación... (no de la fecha ni del id).
EJECUCIONES = [
    # (a)(b): EV-A, dos ejecuciones de hito. ACC-2 y ACC-1 medidos en ambas; REL-1 medida solo en la primera;
    # ACC-1 `judged` medido solo en la primera. Con `LAT-1` en ms (una unidad que no es una proporción).
    # ACC-2 `judged` (automática en este conjunto) también se mide solo en la primera: otra serie de la misma métrica
    # y clave con un solo punto, que no puede sumarse a los de `all` (la serie incluye el `behavior`).
    ("EA-1", "EV-A", 11, True, {}, [("ACC-2", "automatic", "all", 0.40), ("REL-1", "automatic", "all", 0.60),
                                    ("ACC-2", "automatic", "judged", 0.45),
                                    ("ACC-1", "human", "all", 0.10), ("ACC-1", "human", "judged", 0.20)]),
    ("EA-2", "EV-A", 12, True, {}, [("ACC-2", "automatic", "all", 0.50), ("REL-1", "automatic", "all", None),
                                    ("ACC-2", "automatic", "judged", None),
                                    ("ACC-1", "human", "all", 0.15), ("ACC-1", "human", "judged", None)]),
    # (c): EV-B, solo la primera es de hito. a5 sí (las automáticas no piden hito); a6 no (un único hito).
    ("EB-1", "EV-B", 13, True, {}, [("ACC-2", "automatic", "all", 0.30), ("ACC-1", "human", "all", 0.70)]),
    ("EB-2", "EV-B", 14, False, {}, [("ACC-2", "automatic", "all", 0.35), ("ACC-1", "human", "all", 0.80)]),
    # (d): EV-C, tres ejecuciones de hito y la métrica NO medida en la del medio: dos puntos medidos, el del medio
    # no se inventa (ni en a5 con ACC-2 ni en a6 con ACC-3).
    ("EC-1", "EV-C", 15, True, {}, [("ACC-2", "automatic", "all", 0.10), ("ACC-3", "human", "all", 0.50)]),
    ("EC-2", "EV-C", 16, True, {}, [("ACC-2", "automatic", "all", None), ("ACC-3", "human", "all", None)]),
    ("EC-3", "EV-C", 17, True, {}, [("ACC-2", "automatic", "all", 0.30), ("ACC-3", "human", "all", 0.70)]),
    # EV-F: tres ejecuciones y la del medio NO es de hito, con todo medido: a5 dibuja 3 puntos, a6 los 2 de hito.
    ("EF-1", "EV-F", 18, True, {}, [("ACC-2", "automatic", "all", 0.15), ("ACC-1", "human", "all", 0.25)]),
    ("EF-2", "EV-F", 19, False, {}, [("ACC-2", "automatic", "all", 0.16), ("ACC-1", "human", "all", 0.26)]),
    ("EF-3", "EV-F", 20, True, {}, [("ACC-2", "automatic", "all", 0.17), ("ACC-1", "human", "all", 0.27)]),
    # (e): dos series de claves distintas (misma fuente, otra recuperación) con ejecuciones INTERCALADAS en el
    # tiempo: serie D en los días 1 y 10, serie E en los días 2 y 9. Un 0.0 medido (EE-1) se dibuja, no desaparece.
    ("ED-1", "EV-D", 1, True, {"retrieval": {"top_k": 4}}, [("ACC-2", "automatic", "all", 0.11),
                                                             ("ACC-1", "human", "all", 0.21)]),
    ("EE-1", "EV-D", 2, True, {"retrieval": {"top_k": 6}}, [("ACC-2", "automatic", "all", 0.0),
                                                             ("ACC-1", "human", "all", 0.31)]),
    ("EE-2", "EV-D", 9, True, {"retrieval": {"top_k": 6}}, [("ACC-2", "automatic", "all", 0.51),
                                                             ("ACC-1", "human", "all", 0.32)]),
    ("ED-2", "EV-D", 10, True, {"retrieval": {"top_k": 4}}, [("ACC-2", "automatic", "all", 0.12),
                                                              ("ACC-1", "human", "all", 0.22)]),
    # (f): EV-N son dos ejecuciones NO reales (plantilla) con la misma clave: serie con `no real`.
    ("EN-1", "EV-N", 21, True, {"generation_model": "plantilla-sin-modelo"},
     [("ACC-2", "automatic", "all", 0.41), ("REL-1", "automatic", "all", 0.71), ("ACC-1", "human", "all", 0.61)]),
    ("EN-2", "EV-N", 22, True, {"generation_model": "plantilla-sin-modelo"},
     [("ACC-2", "automatic", "all", 0.42), ("REL-1", "automatic", "all", 0.72), ("ACC-1", "human", "all", 0.62)]),
    # (f): EV-R mezcla real, no real y real. La no real (EV-R-2) tiene otra clave y está sola: no forma serie ni se
    # une con las dos reales (que sí forman la suya).
    ("ER-1", "EV-R", 23, True, {}, [("ACC-2", "automatic", "all", 0.81), ("ACC-1", "human", "all", 0.91)]),
    ("ER-2", "EV-R", 24, True, {"generation_model": "plantilla-sin-modelo"},
     [("ACC-2", "automatic", "all", 0.82), ("ACC-1", "human", "all", 0.92)]),
    ("ER-3", "EV-R", 25, True, {}, [("ACC-2", "automatic", "all", 0.83), ("ACC-1", "human", "all", 0.93)]),
]
NO_REALES = {"EN-1", "EN-2", "ER-2"}
# Con fecha y con otra ejecución de su clave (las que entran en `comparable_runs`): todas menos la no real suelta ER-2
# y las dos de robustez (cada una sola en su clave).
COMPARABLES = {r[0] for r in EJECUCIONES} - {"ER-2"}
ID_ROBUSTEZ_COMPLETA = "RB-1"
ID_ROBUSTEZ_SIN_METADATOS = "RB-2"
METRICAS = ("ACC-1", "ACC-2", "ACC-3", "REL-1", "LAT-1")

# Series esperadas: conjuntos de puntos `(ejecución, métrica, valor)`; cada serie se identifica por su contenido.
A5_ESPERADAS = [
    {("EA-1", "ACC-2", 0.40), ("EA-2", "ACC-2", 0.50)},
    {("EB-1", "ACC-2", 0.30), ("EB-2", "ACC-2", 0.35)},
    {("EC-1", "ACC-2", 0.10), ("EC-3", "ACC-2", 0.30)},
    {("EF-1", "ACC-2", 0.15), ("EF-2", "ACC-2", 0.16), ("EF-3", "ACC-2", 0.17)},
    {("ED-1", "ACC-2", 0.11), ("ED-2", "ACC-2", 0.12)},
    {("EE-1", "ACC-2", 0.0), ("EE-2", "ACC-2", 0.51)},
    {("EN-1", "ACC-2", 0.41), ("EN-2", "ACC-2", 0.42)},
    {("EN-1", "REL-1", 0.71), ("EN-2", "REL-1", 0.72)},
    {("ER-1", "ACC-2", 0.81), ("ER-3", "ACC-2", 0.83)},
]
A6_ESPERADAS = [
    {("EA-1", "ACC-1", 0.10), ("EA-2", "ACC-1", 0.15)},
    {("EC-1", "ACC-3", 0.50), ("EC-3", "ACC-3", 0.70)},
    {("EF-1", "ACC-1", 0.25), ("EF-3", "ACC-1", 0.27)},
    {("ED-1", "ACC-1", 0.21), ("ED-2", "ACC-1", 0.22)},
    {("EE-1", "ACC-1", 0.31), ("EE-2", "ACC-1", 0.32)},
    {("EN-1", "ACC-1", 0.61), ("EN-2", "ACC-1", 0.62)},
    {("ER-1", "ACC-1", 0.91), ("ER-3", "ACC-1", 0.93)},
]


def _documentos_evolucion() -> list:
    documentos = []
    for run_id, fuente, numero, hito, campos, tasas in EJECUCIONES:
        ejecucion = {**Q.BASE_RUN, "run_id": run_id, "source": fuente, "run_at": _dia(numero), **campos}
        filas = [_tasa(metrica, juicio, valor, comportamiento) for metrica, juicio, comportamiento, valor in tasas]
        if run_id in ("EA-1", "EA-2"):
            # Una latencia en milisegundos medida en dos ejecuciones comparables: no es una proporción y no debe
            # salir en una serie que se dibuja en porcentaje.
            filas.append(Q.fila_otra("latency", "LAT-1", "all", "measured", "ms",
                                     value=1500.0 if run_id == "EA-1" else 1600.0, denominator=10))
        documentos.append((ejecucion, filas, hito))
    robustez = [Q.fila_otra("robustness", "ROB-1", "categoria=a,perturbacion=b", "measured", "tasa",
                            value=0.5, numerator=5, denominator=10)]
    # RB-1 registra su commit y su modelo; RB-2 no registra ninguno de los dos (una ejecución de robustez sin modelo
    # verificado): sus celdas no pueden heredar los de RB-1 ni rellenarse con otro valor.
    documentos.append(({**Q.BASE_RUN, "run_id": ID_ROBUSTEZ_COMPLETA, "source": "JUP-071", "run_at": _dia(26),
                        "commit": "abc1234", "generation_model": "modelo-1"}, robustez, True))
    documentos.append(({**Q.BASE_RUN, "run_id": ID_ROBUSTEZ_SIN_METADATOS, "source": "JUP-071", "run_at": _dia(27),
                        "commit": None, "generation_model": None}, robustez, True))
    return documentos


def _construir_evolucion() -> dict:
    """Escribe un `rows-v1` por ejecución y un manifiesto en un tmpdir y devuelve `build_dataset`."""
    with tempfile.TemporaryDirectory(prefix="evaluation-visible-") as directorio:
        base = Path(directorio)
        entradas = []
        for ejecucion, filas, hito in _documentos_evolucion():
            ruta = base / f"{ejecucion['run_id']}.json"
            ruta.write_text(json.dumps({"contract_version": 1, "run": ejecucion, "results": filas}), encoding="utf-8")
            entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": hito})
        manifiesto = base / "manifest.json"
        manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
        return tool.build_dataset([manifiesto], root=base)


REAL = Conjunto("real", Q._construir_real)
EVOLUCION = Conjunto("evolucion", _construir_evolucion)


# --- M2: una serie con un solo punto efectivo no puede aparecer ---------------------------------------------------------


class SeriesDeEvolucionTests(unittest.TestCase):
    def _series(self, clave):
        """`{etiqueta: lista de (ejecución, métrica, valor)}` de a5 o a6; valida forma y tipos de la salida."""
        resultado = de_panel(clave, EVOLUCION)
        self.assertEqual(Q.nombres(resultado), ["time", "metric", "value"])
        self.assertEqual(Q.tipo_de(resultado, "time"), TIMESTAMPTZ)
        self.assertIn(Q.tipo_de(resultado, "metric"), ("text", "character varying"))
        self.assertIn(Q.tipo_de(resultado, "value"), Q.NUMERICOS)
        runs = runs_de_la_base(EVOLUCION)
        por_instante = {Q.instante(f["run_at"]): r for r, f in runs.items() if f["run_at"] is not None}
        series = {}
        for fila in resultado["filas"]:
            # (g) ningún punto sin valor: lo no medido no se dibuja ni se convierte en 0.
            self.assertIsNotNone(fila["value"], fila)
            self.assertIsNotNone(fila["time"], fila)
            self.assertIn(Q.instante(fila["time"]), por_instante, fila)
            etiqueta = fila["metric"]
            ids = [m for m in METRICAS if re.search(rf"(?<![\w-]){m}(?![\w-])", etiqueta)]
            self.assertEqual(len(ids), 1, etiqueta)
            series.setdefault(etiqueta, []).append(
                (por_instante[Q.instante(fila["time"])], ids[0], round(fila["value"], 9)))
        for etiqueta, puntos in series.items():
            self.assertEqual(len(puntos), len(set(puntos)), f"punto repetido en {etiqueta!r}")
        return series

    def _contenidos(self, clave):
        return [frozenset(puntos) for puntos in self._series(clave).values()]

    def _comprobar_que_aparece(self, clave, esperada):
        self.assertIn(frozenset(esperada), self._contenidos(clave))

    def _comprobar_que_no_aparece(self, clave, ejecucion, metrica):
        # Ningún punto de esa métrica en esa ejecución, ni dentro de otra serie ni suelto.
        puntos = {(r, m) for lista in self._series(clave).values() for r, m, _ in lista}
        self.assertNotIn((ejecucion, metrica), puntos)

    def test_el_conjunto_sintetico_es_el_que_las_pruebas_suponen(self):
        # Valida el propio montaje: qué ejecuciones tienen otra comparable. Primero exige que el dashboard exista
        # (sin él no hay nada que probar ni se arranca Docker) y después consulta la vista real de la base.
        S.dashboard()
        EVOLUCION.cargar()
        comparables = base_de_datos("SELECT run_id FROM evaluation.comparable_runs", EVOLUCION)
        self.assertEqual({f["run_id"] for f in comparables}, COMPARABLES)
        runs = runs_de_la_base(EVOLUCION)
        self.assertEqual({r for r, f in runs.items() if not f["is_real"] and r.startswith("E")}, NO_REALES)
        # La clave de EV-R-2 (no real) difiere de la de las dos reales, y las dos series intercaladas tienen la suya.
        self.assertEqual(runs["ER-1"]["comparability_key"], runs["ER-3"]["comparability_key"])
        self.assertNotEqual(runs["ER-1"]["comparability_key"], runs["ER-2"]["comparability_key"])
        self.assertNotEqual(runs["ED-1"]["comparability_key"], runs["EE-1"]["comparability_key"])
        self.assertEqual(runs["ED-1"]["comparability_key"], runs["ED-2"]["comparability_key"])
        self.assertEqual(runs["EE-1"]["comparability_key"], runs["EE-2"]["comparability_key"])

    # -- a5: evolución automática -------------------------------------------------------------------------------------

    def test_a5_a_una_serie_con_dos_ejecuciones_medidas_aparece_con_sus_dos_puntos(self):
        # Caso base del contrato: ACC-2 está medida en EA-1 y EA-2 (comparables): la serie se dibuja con 2 puntos.
        self._comprobar_que_aparece("a5", {("EA-1", "ACC-2", 0.40), ("EA-2", "ACC-2", 0.50)})

    def test_a5_b_una_metrica_no_medida_en_una_de_las_dos_ejecuciones_no_deja_un_punto_suelto(self):
        # REL-1 se midió en EA-1 pero es `not_measured` en EA-2: queda UN solo punto efectivo, y por la spec no se
        # dibuja ni una línea ni un punto (el panel enseña «Sin datos: no hay con qué comparar»). ACC-2 de las
        # mismas ejecuciones sí aparece: lo que cuenta es la serie de cada métrica y no la pareja de ejecuciones.
        self._comprobar_que_no_aparece("a5", "EA-1", "REL-1")
        self._comprobar_que_no_aparece("a5", "EA-2", "REL-1")
        # Lo mismo con ACC-2 `judged` (un solo punto medido) aunque ACC-2 `all` tenga dos: son series distintas.
        puntos = {(r, m, v) for lista in self._series("a5").values() for r, m, v in lista}
        self.assertNotIn(("EA-1", "ACC-2", 0.45), puntos)
        self._comprobar_que_aparece("a5", {("EA-1", "ACC-2", 0.40), ("EA-2", "ACC-2", 0.50)})

    def test_a5_d_una_metrica_no_medida_en_el_medio_no_se_inventa(self):
        # EV-C tiene tres ejecuciones y ACC-2 es `not_measured` en la del medio: la serie aparece con los dos puntos
        # medidos y NINGÚN punto para EC-2 (ni 0 ni interpolado: el hueco se verá como hueco).
        self._comprobar_que_aparece("a5", {("EC-1", "ACC-2", 0.10), ("EC-3", "ACC-2", 0.30)})
        self._comprobar_que_no_aparece("a5", "EC-2", "ACC-2")

    def test_a5_e_dos_series_con_ejecuciones_intercaladas_conservan_sus_dos_puntos_exactos(self):
        # Series de claves distintas con fechas 1, 2, 9 y 10 de octubre (D en {1, 10}, E en {2, 9}): cada una conserva
        # sus dos puntos y ninguna se mezcla con la otra por el orden temporal. El 0.0 medido de EE-1 se dibuja.
        contenidos = self._contenidos("a5")
        self.assertIn(frozenset({("ED-1", "ACC-2", 0.11), ("ED-2", "ACC-2", 0.12)}), contenidos)
        self.assertIn(frozenset({("EE-1", "ACC-2", 0.0), ("EE-2", "ACC-2", 0.51)}), contenidos)

    def test_a5_las_no_reales_se_etiquetan_y_no_se_mezclan_con_las_reales(self):
        # (f) La serie de EV-N lleva `no real` y su motivo; las dos reales de EV-R forman su serie sin `no real`; la
        # no real suelta ER-2 (otra clave) no se une a ellas ni aparece.
        series = self._series("a5")
        runs = runs_de_la_base(EVOLUCION)
        for etiqueta, puntos in series.items():
            reales = {r not in NO_REALES for r, _, _ in puntos}
            self.assertEqual(len(reales), 1, f"la serie {etiqueta!r} mezcla reales y no reales")
            claves = {runs[r]["comparability_key"] for r, _, _ in puntos}
            self.assertEqual(len(claves), 1, f"la serie {etiqueta!r} mezcla claves de comparabilidad")
            fuentes = {runs[r]["source"] for r, _, _ in puntos}
            self.assertEqual(len(fuentes), 1)
            self.assertIn(fuentes.pop(), etiqueta)
            if reales == {False}:
                self.assertIn("no real", etiqueta.lower(), etiqueta)
                self.assertIn("plantilla", etiqueta.lower(), etiqueta)
            else:
                self.assertNotIn("no real", etiqueta.lower(), etiqueta)
        self._comprobar_que_no_aparece("a5", "ER-2", "ACC-2")

    def test_a5_g_ninguna_serie_tiene_menos_de_dos_puntos_y_el_conjunto_es_exactamente_el_esperado(self):
        # Invariante central de M2 y comprobación exacta: nada de series de un punto, ni de métricas no medidas, ni
        # de otra unidad. Las series se comparan por contenido y su número (dos etiquetas con el mismo contenido o una
        # etiqueta que une dos series fallarían aquí).
        series = self._series("a5")
        for etiqueta, puntos in series.items():
            self.assertGreaterEqual(len(puntos), 2, f"la serie {etiqueta!r} tiene un solo punto")
        contenidos = [frozenset(puntos) for puntos in series.values()]
        self.assertEqual(len(contenidos), len(set(contenidos)))
        self.assertEqual(set(contenidos), {frozenset(e) for e in A5_ESPERADAS})
        self.assertEqual(len(series), len(A5_ESPERADAS))

    # -- a6: evolución con juicio humano ------------------------------------------------------------------------------

    def test_a6_a_una_serie_con_dos_hitos_medidos_aparece_con_sus_dos_puntos(self):
        self._comprobar_que_aparece("a6", {("EA-1", "ACC-1", 0.10), ("EA-2", "ACC-1", 0.15)})

    def test_a6_b_una_metrica_humana_no_medida_en_una_de_las_dos_no_deja_un_punto_suelto(self):
        # ACC-1 `judged` se midió en EA-1 y es `not_measured` en EA-2: un único punto efectivo no se dibuja, aunque
        # ACC-1 `all` (otra serie de la misma métrica y las mismas ejecuciones) sí tenga sus dos puntos.
        puntos = {(r, m, v) for lista in self._series("a6").values() for r, m, v in lista}
        self.assertNotIn(("EA-1", "ACC-1", 0.20), puntos)
        self.assertIn(("EA-1", "ACC-1", 0.10), puntos)

    def test_a6_c_si_solo_una_de_las_dos_ejecuciones_comparables_es_de_hito_no_aparece(self):
        # EB-1 es de hito y EB-2 no: con juicio humano queda un solo punto de hito. El mismo par SÍ aparece en a5,
        # que no pide hito, así que la ausencia es de a6 y no de la comparabilidad.
        self._comprobar_que_no_aparece("a6", "EB-1", "ACC-1")
        self._comprobar_que_no_aparece("a6", "EB-2", "ACC-1")
        self._comprobar_que_aparece("a5", {("EB-1", "ACC-2", 0.30), ("EB-2", "ACC-2", 0.35)})

    def test_a6_d_con_una_no_medida_en_el_medio_o_una_que_no_es_de_hito_solo_salen_los_puntos_validos(self):
        # EV-C: ACC-3 `not_measured` en EC-2 (de hito): salen EC-1 y EC-3. EV-F: EF-2 está medida pero no es de hito:
        # sale la serie con EF-1 y EF-3 (en a5 salen los tres puntos). Ni uno ni otro se interpola.
        self._comprobar_que_aparece("a6", {("EC-1", "ACC-3", 0.50), ("EC-3", "ACC-3", 0.70)})
        self._comprobar_que_no_aparece("a6", "EC-2", "ACC-3")
        self._comprobar_que_aparece("a6", {("EF-1", "ACC-1", 0.25), ("EF-3", "ACC-1", 0.27)})
        self._comprobar_que_no_aparece("a6", "EF-2", "ACC-1")

    def test_a6_e_dos_series_con_ejecuciones_intercaladas_conservan_sus_dos_puntos_exactos(self):
        contenidos = self._contenidos("a6")
        self.assertIn(frozenset({("ED-1", "ACC-1", 0.21), ("ED-2", "ACC-1", 0.22)}), contenidos)
        self.assertIn(frozenset({("EE-1", "ACC-1", 0.31), ("EE-2", "ACC-1", 0.32)}), contenidos)

    def test_a6_las_no_reales_se_etiquetan_y_no_se_mezclan_con_las_reales(self):
        series = self._series("a6")
        runs = runs_de_la_base(EVOLUCION)
        for etiqueta, puntos in series.items():
            reales = {r not in NO_REALES for r, _, _ in puntos}
            self.assertEqual(len(reales), 1, f"la serie {etiqueta!r} mezcla reales y no reales")
            self.assertEqual(len({runs[r]["comparability_key"] for r, _, _ in puntos}), 1, etiqueta)
            if reales == {False}:
                self.assertIn("no real", etiqueta.lower(), etiqueta)
            else:
                self.assertNotIn("no real", etiqueta.lower(), etiqueta)
        self._comprobar_que_no_aparece("a6", "ER-2", "ACC-1")

    def test_a6_g_ninguna_serie_tiene_menos_de_dos_puntos_y_el_conjunto_es_exactamente_el_esperado(self):
        series = self._series("a6")
        for etiqueta, puntos in series.items():
            self.assertGreaterEqual(len(puntos), 2, f"la serie {etiqueta!r} tiene un solo punto")
        contenidos = [frozenset(puntos) for puntos in series.values()]
        self.assertEqual(len(contenidos), len(set(contenidos)))
        self.assertEqual(set(contenidos), {frozenset(e) for e in A6_ESPERADAS})
        self.assertEqual(len(series), len(A6_ESPERADAS))

    # -- M3 (1): las series solo mezclan proporciones --------------------------------------------------------------------

    def test_a5_no_dibuja_una_latencia_en_milisegundos_junto_a_las_proporciones(self):
        # El eje del panel es un porcentaje (`percentunit`): una latencia de 1500 ms medida en dos ejecuciones
        # comparables saldría como 150000 % y aplastaría las series. La consulta se limita a `unit = 'tasa'`.
        for clave in ("a5", "a6"):
            etiquetas = list(self._series(clave))
            with self.subTest(pieza=clave):
                self.assertFalse([e for e in etiquetas if "LAT-1" in e], etiquetas)
        # La ejecución sí tiene la latencia medida: sin esto el test no probaría nada.
        medidas = base_de_datos(
            "SELECT run_id FROM evaluation.results "
            "WHERE metric_id = 'LAT-1' AND status = 'measured' AND unit = 'ms'", EVOLUCION)
        self.assertEqual({f["run_id"] for f in medidas}, {"EA-1", "EA-2"})


class SeriesDeEvolucionEstructuraTests(unittest.TestCase):
    def test_los_paneles_de_evolucion_se_dibujan_en_porcentaje_y_filtran_por_tasa(self):
        # `percentunit` formatea 0.5 como 50 %: es lo correcto para proporciones y absurdo para milisegundos, así
        # que el SQL debe limitarse a la unidad `tasa` (la que el eje supone).
        for clave in ("a5", "a6"):
            panel = S._unico(clave)
            with self.subTest(pieza=clave):
                self.assertEqual(S._defaults(panel).get("unit"), "percentunit")
                self.assertRegex(S._plano(S.sql_de(panel)), r"\bunit\s*=\s*'tasa'")

    def test_las_series_y_la_anotacion_no_dependen_del_rango_del_selector(self):
        # Los resultados son históricos (el dashboard abre en `now-1y`): una serie recortada por `$__timeFilter`
        # perdería puntos al estrechar el rango y la comparación con la ejecución anterior se rompería.
        consultas = [S.sql_de(S._unico("a5")), S.sql_de(S._unico("a6")), S.anotaciones_propias()[0]["target"]["rawSql"]]
        for sql in consultas:
            with self.subTest(sql=sql[:40]):
                self.assertNotRegex(sql, r"\$\{?__time(Filter|From|To)")

    def test_la_anotacion_solo_se_muestra_en_los_dos_paneles_de_evolucion(self):
        # `filter.ids` limita la anotación a los paneles que la necesitan (a5 y a6) y `exclude: false` la hace una
        # lista de inclusión: con `exclude: true` se mostraría en todos MENOS en esos dos.
        filtro = S.anotaciones_propias()[0].get("filter")
        self.assertIsInstance(filtro, dict)
        self.assertIs(filtro.get("exclude"), False)
        ids = filtro.get("ids")
        self.assertIsInstance(ids, list)
        esperados = {S._unico("a5")["id"], S._unico("a6")["id"]}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), esperados)
        self.assertEqual(len(esperados), 2)


# --- M1: metadatos del resultado en todas las tablas de resultados -----------------------------------------------------


def comprobar_metadatos(caso, filas, runs, laxos=()):
    """Cada fila trae fecha, versión, commit y modelo de SU ejecución; lo no registrado llega NULL o `no registrado`.

    `laxos` son las columnas que, además de coincidir con la ejecución, pueden llegar NULL o `no registrado`
    aunque la ejecución sí las tenga (en B: el commit y el modelo). Nunca se admite un valor distinto del de la
    ejecución: ni inventado ni heredado de otra.
    """
    caso.assertGreater(len(filas), 0)
    for fila in filas:
        run = runs[fila["run_id"]]
        with caso.subTest(run_id=fila["run_id"], metrica=fila.get("metric_id")):
            for columna in METADATOS:
                caso.assertIn(columna, fila)
            if run["run_at"] is None:
                # La fecha de una ejecución sin fecha se queda en NULL (no se inventa ni es un texto).
                caso.assertIsNone(fila["run_at"])
            else:
                caso.assertIsNotNone(fila["run_at"])
                caso.assertEqual(Q.instante(fila["run_at"]), Q.instante(run["run_at"]))
            for columna in ("suite_version", "commit_sha", "generation_model"):
                sin_dato = fila[columna] is None or str(fila[columna]).strip().lower() == "no registrado"
                if columna in laxos and sin_dato:
                    continue
                Q.comprobar_texto_o_nulo(caso, fila[columna], run[columna], columna)


class MetadatosDelResultadoTests(unittest.TestCase):
    def _comprobar_campana_jup_070(self, clave, grupos, filas_esperadas=None):
        """a3 y a4 (solo JUP-070 con los datos versionados): cada fila trae la fecha, la versión, el commit y el modelo
        de SU ejecución. Las dos ejecuciones tienen commits y fechas distintos, así que una consulta que tomara los
        metadatos de otra (o los fijara) se delata; la versión (`1.0.0`) y el modelo son comunes a las dos."""
        resultado = de_panel(clave, REAL)
        self.assertTrue(set(METADATOS) <= set(Q.nombres(resultado)), Q.nombres(resultado))
        self.assertTrue({"run_id", "metric_id", "behavior", "status", "value", "numerator", "denominator"}
                        <= set(Q.nombres(resultado)))
        runs = runs_de_la_base(REAL)
        lista = ", ".join(f"'{g}'" for g in grupos)
        esperadas = base_de_datos(f"SELECT run_id FROM evaluation.results WHERE grp IN ({lista})", REAL)
        self.assertEqual(len(resultado["filas"]), len(esperadas))
        if filas_esperadas is not None:
            self.assertEqual(len(resultado["filas"]), filas_esperadas)
        comprobar_metadatos(self, resultado["filas"], runs)
        por_ejecucion = {}
        for fila in resultado["filas"]:
            por_ejecucion.setdefault(fila["run_id"], set()).add(
                (fila["run_at"], fila["suite_version"], fila["commit_sha"], fila["generation_model"]))
        jup070 = {r for r, f in runs.items() if f["source"] == "JUP-070"}
        self.assertEqual(set(por_ejecucion), jup070)
        for run_id, metadatos in por_ejecucion.items():
            with self.subTest(run_id=run_id):
                # Un único juego de metadatos por ejecución, con el valor registrado (no NULL: JUP-070 los trae).
                self.assertEqual(len(metadatos), 1, metadatos)
                (run_at, version, commit, modelo), = metadatos
                self.assertEqual(Q.instante(run_at), Q.instante(runs[run_id]["run_at"]))
                self.assertEqual(version, "1.0.0")
                self.assertEqual(modelo, "plantilla-sin-modelo")
                self.assertEqual(commit, runs[run_id]["commit_sha"])
                self.assertTrue(commit and commit != "no registrado")
        commits = {next(iter(m))[2] for m in por_ejecucion.values()}
        fechas = {next(iter(m))[0] for m in por_ejecucion.values()}
        self.assertEqual(len(commits), 2, commits)
        self.assertEqual(len(fechas), 2, fechas)

    def test_a3_calidad_muestra_los_metadatos_de_su_propia_ejecucion(self):
        # 32 filas (16 métricas de calidad en cada una de las dos ejecuciones de JUP-070).
        self._comprobar_campana_jup_070("a3", ("accuracy", "relevance", "grounding"), 32)

    def test_a4_latencia_y_campana_muestra_los_metadatos_de_su_propia_ejecucion(self):
        self._comprobar_campana_jup_070("a4", ("latency", "robustness", "availability"))

    def test_a7_calibracion_muestra_fecha_version_commit_y_modelo(self):
        # Las 140 filas de calibración son de JUP-022: con fecha y versión de batería; el informe no trae commit ni
        # modelo (la calibración no genera respuestas) y llegan NULL o `no registrado`.
        resultado = de_panel("a7", REAL)
        self.assertTrue(set(METADATOS) <= set(Q.nombres(resultado)), Q.nombres(resultado))
        self.assertTrue(
            {"run_id", "metric_id", "behavior", "value", "numerator", "denominator", "selected"}
            <= set(Q.nombres(resultado)))
        self.assertEqual(len(resultado["filas"]), 140)
        runs = runs_de_la_base(REAL)
        comprobar_metadatos(self, resultado["filas"], runs)
        fila = resultado["filas"][0]
        self.assertEqual(Q.instante(fila["run_at"]), Q.instante(runs[fila["run_id"]]["run_at"]))
        # Actualizado tras integrar develop: JUP-120 regeneró el informe de calibración con el banco 1.0.1 (antes
        # 1.0.0). La versión esperada se lee del propio informe real (`bank.suite_version`) y se exige que sea una
        # cadena no vacía, para que la comprobación siga siendo independiente de la consulta del dashboard.
        informe = json.loads((Path(__file__).resolve().parents[2] / "docs" / "spikes"
                              / "JUP-022-retrieval-calibration.json").read_text(encoding="utf8"))
        version_del_informe = informe["bank"]["suite_version"]
        self.assertIsInstance(version_del_informe, str)
        self.assertTrue(version_del_informe)
        self.assertEqual(fila["suite_version"], version_del_informe)

    def test_a8_benchmark_no_rellena_la_fecha_ni_el_commit_que_el_informe_no_trae(self):
        # El informe de JUP-078 no registra fecha, commit, versión de batería ni modelo (el alias de cada modelo
        # va en `behavior`). Las dos filas llegan con esos cuatro metadatos NULL o `no registrado`, nunca con un
        # valor inventado, y la fecha, que es un instante, solo puede ser NULL.
        resultado = de_panel("a8", REAL)
        self.assertTrue(set(METADATOS) <= set(Q.nombres(resultado)), Q.nombres(resultado))
        self.assertTrue({"run_id", "behavior", "successful", "cases", "keyword_score", "latency_p95", "cost"}
                        <= set(Q.nombres(resultado)))
        self.assertEqual(len(resultado["filas"]), 2)
        runs = runs_de_la_base(REAL)
        comprobar_metadatos(self, resultado["filas"], runs)
        for fila in resultado["filas"]:
            self.assertIsNone(fila["run_at"])
            for columna in ("suite_version", "commit_sha", "generation_model"):
                self.assertIn(fila[columna], (None, "no registrado"), (columna, fila[columna]))

    def test_a9_robustez_muestra_los_metadatos_de_cada_ejecucion_sin_mezclarlos(self):
        # Con un informe de robustez futuro (`source = 'JUP-071'`): RB-1 registra commit y modelo y RB-2 no. Cada
        # fila trae los suyos; RB-2 no hereda ni inventa los de RB-1.
        resultado = de_panel("a9", EVOLUCION)
        self.assertTrue(set(METADATOS) <= set(Q.nombres(resultado)), Q.nombres(resultado))
        self.assertTrue(
            {"run_id", "source", "metric_id", "behavior", "status", "value", "numerator", "denominator"}
            <= set(Q.nombres(resultado)))
        por_ejecucion = {f["run_id"]: f for f in resultado["filas"]}
        self.assertEqual(len(resultado["filas"]), 2)
        self.assertEqual(set(por_ejecucion), {ID_ROBUSTEZ_COMPLETA, ID_ROBUSTEZ_SIN_METADATOS})
        completa = por_ejecucion[ID_ROBUSTEZ_COMPLETA]
        self.assertEqual(Q.instante(completa["run_at"]), Q.instante(_dia(26)))
        self.assertEqual(completa["suite_version"], "1.0.0")
        self.assertEqual(completa["commit_sha"], "abc1234")
        self.assertEqual(completa["generation_model"], "modelo-1")
        sin_metadatos = por_ejecucion[ID_ROBUSTEZ_SIN_METADATOS]
        self.assertEqual(Q.instante(sin_metadatos["run_at"]), Q.instante(_dia(27)))
        self.assertEqual(sin_metadatos["suite_version"], "1.0.0")
        for columna in ("commit_sha", "generation_model"):
            self.assertIn(sin_metadatos[columna], (None, "no registrado"), (columna, sin_metadatos[columna]))
        comprobar_metadatos(self, resultado["filas"], runs_de_la_base(EVOLUCION))

    def test_b_la_tabla_de_negocio_muestra_la_version_de_la_bateria_y_los_demas_metadatos_si_los_hay(self):
        # JUP-068 trae su versión de batería (`JUP-068-example-v1`) y no trae fecha. El commit y el modelo pueden ser
        # NULL (la ejecución de negocio es sintética), pero si se muestran deben ser los de la ejecución.
        paneles_b = S._hay("b_tabla")
        runs = runs_de_la_base(REAL)
        filas = []
        for panel in paneles_b:
            resultado = ejecutar(Q.consulta_panel(panel), REAL)
            self.assertTrue(set(METADATOS) <= set(Q.nombres(resultado)), Q.nombres(resultado))
            self.assertTrue({"run_id", "metric_id", "behavior", "status", "value"} <= set(Q.nombres(resultado)))
            filas.extend(resultado["filas"])
        self.assertGreater(len(filas), 0)
        comprobar_metadatos(self, filas, runs, laxos=("commit_sha", "generation_model"))
        for fila in filas:
            self.assertEqual(fila["suite_version"], "JUP-068-example-v1")
            self.assertIsNone(fila["run_at"])


# --- M3 (2): el texto formateado de las tasas -------------------------------------------------------------------------


class TextoDeLasTasasTests(unittest.TestCase):
    def _textos(self, run_prefijo, metrica, comportamiento):
        resultado = de_panel("a3", REAL)
        filas = [f for f in resultado["filas"]
                 if f["run_id"].startswith(run_prefijo) and f["metric_id"] == metrica
                 and f["behavior"] == comportamiento]
        self.assertEqual(len(filas), 1, (run_prefijo, metrica, comportamiento))
        return Q.celdas(filas[0])

    def _comprobar(self, run_prefijo, metrica, comportamiento, patron):
        # El separador decimal y el espacio antes de `%` son tolerantes (coma o punto; espacio normal o duro): lo que
        # se fija es el valor redondeado a un decimal, multiplicado por 100 y con el signo de porcentaje.
        textos = self._textos(run_prefijo, metrica, comportamiento)
        self.assertTrue([t for t in textos if re.fullmatch(patron, t.strip())], (metrica, textos))

    def test_acc_2_de_la_primera_ejecucion_es_51_por_ciento(self):
        # 0.509804 de la ejecución 20261008T201354Z: 50.9804 % redondeado a un decimal es 51.0 %, no 50.98 ni 0.5.
        self._comprobar("jup-070-20261008T201354Z", "ACC-2", "all", r"51[.,]0[  ]?%")

    def test_acc_2_de_la_segunda_ejecucion_es_49_por_ciento(self):
        self._comprobar("jup-070-20261008T210144Z", "ACC-2", "all", r"49[.,]0[  ]?%")

    def test_acc_1_medido_en_cero_se_ve_como_0_por_ciento_y_no_como_no_medido(self):
        # Un 0.0 medido es un resultado (la rúbrica humana no aprobó nada), no un hueco.
        self._comprobar("jup-070-20261008T201354Z", "ACC-1", "all", r"0[.,]0[  ]?%")

    def test_grd_1_es_100_por_ciento(self):
        self._comprobar("jup-070-20261008T201354Z", "GRD-1", "all", r"100[.,]0[  ]?%")


# --- M4 (1): las señales en vivo de la sección C ---------------------------------------------------------------------


class SenalesEnVivoTests(unittest.TestCase):
    def test_los_cinco_paneles_de_prometheus_miran_la_ultima_hora(self):
        # Las señales de C se ven con `timeFrom` de 1 h: el selector del dashboard abre en `now-1y` (por las series de
        # A) y sin esta ventana propia un `rate(...[5m])` se estiraría un año de datos de tráfico.
        paneles = [p for p in S.de_seccion("C") if S.expresiones(p) and any(S.expresiones(p))]
        self.assertEqual(len(paneles), 5, [p["title"] for p in paneles])
        for panel in paneles:
            with self.subTest(panel=panel["title"]):
                self.assertEqual(panel.get("datasource", {}).get("uid"), "prometheus")
                self.assertEqual(panel.get("timeFrom"), "1h")


# --- L4: tamaño de las tablas ------------------------------------------------------------------------------------------


class TamanoDeLasTablasTests(unittest.TestCase):
    def test_la_tabla_de_negocio_muestra_sus_23_filas_sin_desplazarse(self):
        # La tabla de B tiene 23 filas (los datos de JUP-068) y con 14 unidades de alto solo se ven 17: el resto
        # exige desplazar dentro del panel y lo no visto parece que no existe.
        panel = S._unico("b_tabla")
        self.assertGreaterEqual(panel["gridPos"]["h"], 26)

    def test_las_tablas_anchas_de_a_ocupan_todo_el_ancho(self):
        # Doce columnas o más no caben en media pantalla: cada tabla de la sección A ocupa las 24 columnas.
        tablas = [p for p in S.de_seccion("A") if p.get("type") == "table"]
        self.assertGreaterEqual(len(tablas), 7)
        for panel in tablas:
            with self.subTest(panel=panel["title"]):
                self.assertEqual(panel["gridPos"]["w"], 24)
                self.assertEqual(panel["gridPos"]["x"], 0)


if __name__ == "__main__":
    unittest.main()
