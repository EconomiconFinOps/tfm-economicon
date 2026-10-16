"""Remediación del re-QA de JUP-121 (hallazgo M-2): la etiqueta de las series de evolución lleva los MOTIVOS (Red).

Hallazgo: la etiqueta de las series de la evolución con juicio humano (a6) perdía los motivos de las ejecuciones no
reales y quedaba en `no real:` a secas, mientras que la automática (a5) decía `no real: plantilla`. Los motivos son
los de la herramienta (`non_real_reasons`: `plantilla`, `doble`, `sintetica`, `sin_modelo_verificado`) y el usuario del
dashboard necesita verlos en la leyenda para saber POR QUÉ una serie no es calidad del asistente.

Contrato (el coder debe respetarlo): la consulta de a5 y la de a6 generan la etiqueta de la serie (columna `metric`)
con la misma regla: las series de ejecuciones no reales terminan en `no real: <motivos separados por ", ">`, con los
motivos de la ejecución en el orden fijo de la herramienta; las reales no mencionan `no real`. Lo que viene antes del
motivo (identificador de la métrica, comportamiento, fuente, clave abreviada de la serie) lo decide el dashboard y no se
fija aquí, salvo que el identificador de la métrica va primero y que es lo ÚNICO que puede diferir entre a5 y a6 para la
misma serie (a5 dibuja métricas automáticas y a6 humanas: `ACC-2` frente a `ACC-1`).

Este módulo es nuevo: los de `structure`, `queries` y `visible` están congelados. Reutiliza de ellos solo las piezas
puras (localizador de paneles, macros, fábricas de filas); el servidor PostgreSQL desechable y la caché son PROPIOS
(uno por módulo, perezoso, siempre limpiado), de modo que nada se comparte con otros módulos aunque corran juntos.

Conjunto: `rows-v1` escrito en un tmpdir con series NO reales de motivos distintos (una `plantilla`, otra `plantilla`
+ `doble`, otra `sintetica`, otra `sin_modelo_verificado` y otra con tres motivos a la vez), dos series con el MISMO
motivo pero distinta configuración, una serie real y series donde algunas ejecuciones no son de hito.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON` (como en los demás módulos) para comprobar una copia corregida o mutada.
Ejecución: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s scripts/tests -p test_evaluation_dashboard_labels.py -v`
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

# --- Servidor propio: uno por módulo, perezoso y siempre limpiado ----------------------------------------------------

_SERVER: dict = {}
_ESTADO: dict = {"cargado": False, "rol": False}
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


# --- Conjunto de datos --------------------------------------------------------------------------------------------------

# Cada grupo es una serie (misma clave de comparabilidad): `{motivos esperados}`. Los motivos se comprueban contra la
# base (`non_real_reasons`, calculados por la herramienta) en `test_el_montaje_...`; aquí solo se documenta la intención.
MOTIVOS_ESPERADOS = {
    "REAL": (),
    "PLA": ("plantilla",),
    "PLA6": ("plantilla",),  # mismo motivo que PLA, otra recuperación: otra serie
    "PLADOB": ("plantilla", "doble"),
    "SIN": ("sintetica",),
    "SMV": ("sin_modelo_verificado",),
    "TRES": ("plantilla", "doble", "sintetica"),
    "DOB": ("doble",),
}

# Ejecuciones: (id, grupo, fuente, día, hito, campos que cambian). Cada ejecución tiene su día, así que `time` la
# identifica. Las dos primeras de PLA y la tercera (sin hito) prueban que a5 dibuja 3 puntos y a6 solo los 2 de hito.
EJECUCIONES = [
    ("REAL-1", "REAL", "NR", 1, True, {}),
    ("REAL-2", "REAL", "NR", 2, True, {}),
    ("PLA-1", "PLA", "NR", 3, True, {"generation_model": "plantilla-sin-modelo"}),
    ("PLA-2", "PLA", "NR", 4, True, {"generation_model": "plantilla-sin-modelo"}),
    ("PLA-3", "PLA", "NR", 5, False, {"generation_model": "plantilla-sin-modelo"}),
    ("PLA6-1", "PLA6", "NR", 6, True, {"generation_model": "plantilla-sin-modelo", "retrieval": {"top_k": 6}}),
    ("PLA6-2", "PLA6", "NR", 7, True, {"generation_model": "plantilla-sin-modelo", "retrieval": {"top_k": 6}}),
    ("PLADOB-1", "PLADOB", "NR", 8, True, {"generation_model": "plantilla-sin-modelo", "embedding_provider": "mock"}),
    ("PLADOB-2", "PLADOB", "NR", 9, True, {"generation_model": "plantilla-sin-modelo", "embedding_provider": "mock"}),
    ("SIN-1", "SIN", "NR", 10, True, {"synthetic": True}),
    ("SIN-2", "SIN", "NR", 11, True, {"synthetic": True}),
    # `sin_modelo_verificado` solo se aplica a las campañas sobre el chat (JUP-070 y JUP-071) sin modelo registrado.
    ("SMV-1", "SMV", "JUP-070", 12, True, {"generation_model": None}),
    ("SMV-2", "SMV", "JUP-070", 13, True, {"generation_model": None}),
    ("TRES-1", "TRES", "NR", 14, True, {"generation_model": "plantilla-sin-modelo", "embedding_alias": "mock",
                                         "synthetic": True}),
    ("TRES-2", "TRES", "NR", 15, True, {"generation_model": "plantilla-sin-modelo", "embedding_alias": "mock",
                                         "synthetic": True}),
    # Serie sin ninguna ejecución de hito: solo a5 la dibuja (a6 pide hito).
    ("DOB-1", "DOB", "NR", 16, False, {"embedding_alias": "mock"}),
    ("DOB-2", "DOB", "NR", 17, False, {"embedding_alias": "mock"}),
]
# Series que cada panel debe dibujar (al menos dos puntos medidos; en a6, de hito).
GRUPOS_A5 = {"REAL", "PLA", "PLA6", "PLADOB", "SIN", "SMV", "TRES", "DOB"}
GRUPOS_A6 = {"REAL", "PLA", "PLA6", "PLADOB", "SIN", "SMV", "TRES"}
# Series con motivos que cada panel debe dibujar: sin ellas el resto de comprobaciones serían vacuas.
NO_REALES_A5 = GRUPOS_A5 - {"REAL"}
NO_REALES_A6 = GRUPOS_A6 - {"REAL"}


def _grupo(run_id: str) -> str:
    return next(g for r, g, *_ in EJECUCIONES if r == run_id)


def _dia(numero):
    """Instante UTC del `numero`-ésimo día de octubre de 2026 a las 10:00."""
    return f"2026-10-{numero:02d}T10:00:00Z"


def _construir() -> dict:
    """Escribe un `rows-v1` por ejecución y un manifiesto en un tmpdir y devuelve `build_dataset`."""
    with tempfile.TemporaryDirectory(prefix="evaluation-labels-") as directorio:
        base = Path(directorio)
        entradas = []
        for indice, (run_id, _grupo_, fuente, numero, hito, campos) in enumerate(EJECUCIONES):
            ejecucion = {**Q.BASE_RUN, "run_id": run_id, "source": fuente, "run_at": _dia(numero), **campos}
            # ACC-2 automática (a5) y ACC-1 humana (a6), ambas medidas en todas las ejecuciones; los valores cambian
            # de una ejecución a otra para que los puntos sean distinguibles.
            filas = [Q.fila_tasa("ACC-2", "accuracy", "automatic", round(0.10 + 0.01 * indice, 2)),
                     Q.fila_tasa("ACC-1", "accuracy", "human", round(0.50 + 0.01 * indice, 2))]
            ruta = base / f"{run_id}.json"
            ruta.write_text(json.dumps({"contract_version": 1, "run": ejecucion, "results": filas}), encoding="utf-8")
            entradas.append({"path": str(ruta), "format": "rows-v1", "milestone": hito})
        manifiesto = base / "manifest.json"
        manifiesto.write_text(json.dumps({"manifest_version": 1, "runs": entradas}), encoding="utf-8")
        return tool.build_dataset([manifiesto], root=base)


def _cargar() -> None:
    servidor = server()
    if _ESTADO["cargado"]:
        return
    servidor.load_dataset(_construir(), tool)
    _ESTADO["cargado"] = True
    if not _ESTADO["rol"]:
        # Contraseña aleatoria que solo vive en esta sesión; los privilegios sobreviven a las recargas.
        resultado = servidor.psql(stdin=tool.build_role_sql(secrets.token_urlsafe(18)))
        if resultado.returncode != 0:
            raise RuntimeError(f"no se pudo crear el rol de lectura: {resultado.stderr.strip()}")
        _ESTADO["rol"] = True


def _ejecutar_panel(clave: str) -> dict:
    """Filas `[{time, metric, value}]` de la consulta del panel `clave` tal cual está en el dashboard (rol de lectura)."""
    if clave in _RESULTADOS:
        return _RESULTADOS[clave]
    cuerpo = Q.sustituir_macros(Q.consulta_panel(S._unico(clave))).strip()
    cuerpo = cuerpo[:-1] if cuerpo.endswith(";") else cuerpo
    _cargar()
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


def _runs_de_la_base() -> dict:
    """`{run_id: fila}` de `evaluation.runs` leída con el rol administrador (motivos calculados por la herramienta)."""
    _cargar()
    resultado = server().psql(
        "SELECT COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb) FROM "
        "(SELECT run_id, run_at, is_real, non_real_reasons, comparability_key FROM evaluation.runs) t;")
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip())
    filas = json.loads([linea for linea in resultado.stdout.split("\n") if linea.strip()][-1])
    return {fila["run_id"]: fila for fila in filas}


# --- Series: agrupación de los puntos de cada panel --------------------------------------------------------------------


class Serie:
    """Una serie dibujada: su etiqueta, el grupo del conjunto al que pertenece y sus motivos según la base."""

    def __init__(self, etiqueta, metrica, grupo, claves, motivos, reales, puntos):
        self.etiqueta = etiqueta
        self.metrica = metrica
        self.grupo = grupo
        self.claves = claves
        self.motivos = motivos
        self.reales = reales
        self.puntos = puntos

    def sin_metrica(self) -> str:
        """Etiqueta con el identificador de la métrica sustituido: lo único que puede diferir entre a5 y a6."""
        return re.sub(rf"(?<![\w-]){re.escape(self.metrica)}(?![\w-])", "<METRICA>", self.etiqueta, count=1)


def _series(clave: str, metrica: str) -> dict:
    """`{etiqueta: Serie}` de a5 o a6; valida la forma de la salida y que cada etiqueta sea de UNA sola serie."""
    resultado = _ejecutar_panel(clave)
    assert Q.nombres(resultado) == ["time", "metric", "value"], Q.nombres(resultado)
    runs = _runs_de_la_base()
    por_instante = {Q.instante(f["run_at"]): r for r, f in runs.items()}
    puntos_por_etiqueta: dict = {}
    for fila in resultado["filas"]:
        puntos_por_etiqueta.setdefault(fila["metric"], []).append(por_instante[Q.instante(fila["time"])])
    series = {}
    for etiqueta, ejecuciones in puntos_por_etiqueta.items():
        grupos = {_grupo(r) for r in ejecuciones}
        claves = {runs[r]["comparability_key"] for r in ejecuciones}
        motivos = {tuple(runs[r]["non_real_reasons"]) for r in ejecuciones}
        reales = {runs[r]["is_real"] for r in ejecuciones}
        # Una etiqueta que une varias series (distinta clave) haría ilegible la leyenda; falla con un mensaje claro.
        assert len(claves) == 1 and len(grupos) == 1, f"la etiqueta {etiqueta!r} mezcla series: {sorted(grupos)}"
        assert len(motivos) == 1 and len(reales) == 1, etiqueta
        series[etiqueta] = Serie(etiqueta, metrica, grupos.pop(), claves.pop(), motivos.pop(), reales.pop(),
                                 sorted(ejecuciones))
    return series


def _por_grupo(series: dict) -> dict:
    por_grupo = {}
    for serie in series.values():
        assert serie.grupo not in por_grupo, f"el grupo {serie.grupo} aparece con dos etiquetas: {list(series)}"
        por_grupo[serie.grupo] = serie
    return por_grupo


def _cola_de_motivos(etiqueta: str):
    """Texto que sigue a `no real: ` hasta el final de la etiqueta, o `None` si la etiqueta no lo contiene."""
    encontrado = re.search(r"no real: (.*)$", etiqueta, flags=re.DOTALL)
    return None if encontrado is None else encontrado.group(1)


class EtiquetasDeLasSeriesTests(unittest.TestCase):
    def _a5(self):
        return _series("a5", "ACC-2")

    def _a6(self):
        return _series("a6", "ACC-1")

    def test_el_montaje_es_el_que_las_pruebas_suponen(self):
        # Valida el propio conjunto: los motivos que la herramienta guarda en la base son los que cada grupo pretende
        # y las series de cada panel son las esperadas. Sin esto los demás tests podrían pasar vacuos (p. ej. si la
        # herramienta dejara de clasificar un motivo, o si el panel no dibujara ninguna serie no real).
        S.dashboard()
        runs = _runs_de_la_base()
        self.assertEqual(set(runs), {r for r, *_ in EJECUCIONES})
        for run_id, grupo, *_ in EJECUCIONES:
            with self.subTest(run=run_id):
                self.assertEqual(tuple(runs[run_id]["non_real_reasons"]), MOTIVOS_ESPERADOS[grupo])
                self.assertEqual(runs[run_id]["is_real"], MOTIVOS_ESPERADOS[grupo] == ())
        # Todos los motivos del contrato aparecen en alguna serie.
        self.assertEqual({m for motivos in MOTIVOS_ESPERADOS.values() for m in motivos},
                         {"plantilla", "doble", "sintetica", "sin_modelo_verificado"})
        self.assertEqual({s.grupo for s in self._a5().values()}, GRUPOS_A5)
        self.assertEqual({s.grupo for s in self._a6().values()}, GRUPOS_A6)

    def _comprobar_motivos(self, series, grupos_no_reales):
        # Cada serie no real termina EXACTAMENTE en `no real: ` + sus motivos (los de la base) separados por `, `.
        # Se compara la cola entera y no una subcadena: así un motivo de más, de menos, otro separador o un orden
        # distinto (el de la herramienta es fijo) hacen fallar el caso.
        por_grupo = _por_grupo(series)
        self.assertTrue(grupos_no_reales <= set(por_grupo), (grupos_no_reales, sorted(por_grupo)))
        for grupo in sorted(grupos_no_reales):
            serie = por_grupo[grupo]
            with self.subTest(serie=grupo, etiqueta=serie.etiqueta):
                self.assertFalse(serie.reales)
                self.assertGreater(len(serie.motivos), 0)
                self.assertEqual(_cola_de_motivos(serie.etiqueta), ", ".join(serie.motivos), serie.etiqueta)
                # El hueco que dejaba el defecto: `no real:` sin nada detrás.
                self.assertNotRegex(serie.etiqueta, r"no real:\s*$")

    def test_a5_cada_serie_no_real_termina_en_no_real_y_exactamente_sus_motivos(self):
        self._comprobar_motivos(self._a5(), NO_REALES_A5)

    def test_a6_cada_serie_no_real_termina_en_no_real_y_exactamente_sus_motivos(self):
        # Caso del hallazgo M-2: antes de la corrección a6 dejaba `no real:` sin motivos.
        self._comprobar_motivos(self._a6(), NO_REALES_A6)

    def test_la_etiqueta_de_la_misma_serie_es_identica_en_a5_y_a6(self):
        # a5 y a6 dibujan la misma serie (misma clave de comparabilidad) con métricas distintas (`ACC-2` automática y
        # `ACC-1` humana): salvo el identificador de la métrica la etiqueta debe ser idéntica, motivos incluidos, para
        # que el usuario vea el mismo rótulo en las dos gráficas. Solo se comparan las series presentes en las dos.
        a5 = {s.claves: s for s in self._a5().values()}
        a6 = {s.claves: s for s in self._a6().values()}
        comunes = set(a5) & set(a6)
        self.assertEqual(len(comunes), len(GRUPOS_A6), "las series de hito deben dibujarse en los dos paneles")
        for clave in comunes:
            with self.subTest(serie=a5[clave].grupo):
                self.assertEqual(a5[clave].sin_metrica(), a6[clave].sin_metrica())
                # Y la regla de las no reales vale para las dos (no basta que coincidan en estar ambas incompletas).
                if not a5[clave].reales:
                    self.assertEqual(_cola_de_motivos(a6[clave].etiqueta), ", ".join(a6[clave].motivos))

    def test_las_series_reales_no_llevan_no_real(self):
        for clave, metrica in (("a5", "ACC-2"), ("a6", "ACC-1")):
            series = _series(clave, metrica)
            real = _por_grupo(series)["REAL"]
            with self.subTest(panel=clave, etiqueta=real.etiqueta):
                self.assertTrue(real.reales)
                self.assertNotIn("no real", real.etiqueta.lower())
                self.assertNotIn("plantilla", real.etiqueta.lower())
            # Y ninguna serie con motivos se queda sin `no real` (la regla recíproca).
            for serie in series.values():
                if not serie.reales:
                    with self.subTest(panel=clave, serie=serie.grupo):
                        self.assertIn("no real: ", serie.etiqueta)

    def test_dos_series_distintas_no_comparten_etiqueta_y_distinto_motivo_da_distinta_cola(self):
        for clave, metrica in (("a5", "ACC-2"), ("a6", "ACC-1")):
            series = _series(clave, metrica)
            with self.subTest(panel=clave):
                # Una etiqueta por serie y viceversa (la agrupación por clave ya garantiza lo primero; el recuento
                # detecta etiquetas repetidas entre grupos).
                self.assertEqual(len(series), len({s.claves for s in series.values()}))
                self.assertEqual(len({s.etiqueta for s in series.values()}), len(series))
                # Dos series con DISTINTOS motivos no comparten la cola `no real: ...`; con el MISMO motivo (PLA y PLA6)
                # la cola coincide pero la etiqueta entera no (son series de otra recuperación).
                colas = {}
                for serie in series.values():
                    if not serie.reales:
                        colas.setdefault(serie.motivos, set()).add(_cola_de_motivos(serie.etiqueta))
                for motivos, textos in colas.items():
                    self.assertEqual(textos, {", ".join(motivos)}, motivos)
                self.assertEqual(len(colas), len({t for textos in colas.values() for t in textos}))
        a5 = _por_grupo(_series("a5", "ACC-2"))
        self.assertEqual(a5["PLA"].motivos, a5["PLA6"].motivos)
        self.assertNotEqual(a5["PLA"].etiqueta, a5["PLA6"].etiqueta)

    def test_las_series_con_varios_motivos_los_llevan_todos_y_en_el_orden_de_la_herramienta(self):
        # Una ejecución con tres motivos a la vez: no se queda con el primero, no los reordena y no los repite.
        for clave, metrica in (("a5", "ACC-2"), ("a6", "ACC-1")):
            etiqueta = _por_grupo(_series(clave, metrica))["TRES"].etiqueta
            with self.subTest(panel=clave):
                self.assertEqual(_cola_de_motivos(etiqueta), "plantilla, doble, sintetica", etiqueta)
        # `sin_modelo_verificado` (el motivo más largo y solo de las campañas de chat) también llega entero.
        for clave, metrica in (("a5", "ACC-2"), ("a6", "ACC-1")):
            etiqueta = _por_grupo(_series(clave, metrica))["SMV"].etiqueta
            with self.subTest(panel=clave):
                self.assertEqual(_cola_de_motivos(etiqueta), "sin_modelo_verificado", etiqueta)

    def test_a5_dibuja_las_series_sin_hito_con_sus_motivos_y_a6_no_las_dibuja(self):
        # DOB no tiene ninguna ejecución de hito: a5 (que no pide hito) la dibuja con su motivo `doble` y a6 no. Fija que
        # el motivo no depende de que la ejecución sea de hito y que a6 sigue filtrando por hito.
        a5 = _por_grupo(self._a5())
        self.assertEqual(_cola_de_motivos(a5["DOB"].etiqueta), "doble")
        self.assertNotIn("DOB", {s.grupo for s in self._a6().values()})
        # La serie PLA tiene 3 ejecuciones (una sin hito): a5 la dibuja con 3 puntos y a6 con los 2 de hito, con la
        # misma etiqueta salvo la métrica.
        a6 = _por_grupo(self._a6())
        self.assertEqual(len(a5["PLA"].puntos), 3)
        self.assertEqual(len(a6["PLA"].puntos), 2)
        self.assertEqual(a5["PLA"].sin_metrica(), a6["PLA"].sin_metrica())


if __name__ == "__main__":
    unittest.main()
