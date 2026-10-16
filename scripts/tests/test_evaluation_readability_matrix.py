"""Tabla «Resultados por métrica y ejecución» de la sección A (JUP-121, change `jup-121-lectura-dashboard`, Red).

Requisito de la spec: «Resultados por métrica y ejecución» (decisión D3 del diseño). Hoy la calidad se lee en tablas de
una fila por (métrica, ejecución) con identificadores sin nombre (`ACC-2 · judged`) y con los metadatos de la ejecución
repetidos en cada fila. La tabla nueva tiene UNA FILA POR MÉTRICA Y VARIANTE con su nombre legible y UNA COLUMNA POR
EJECUCIÓN, sin metadatos repetidos.

Cómo funciona (fijado en una prueba real con Grafana 11.3.0): la consulta devuelve una fila por (métrica, variante,
ejecución) con cuatro columnas, `metrica` (texto legible), `orden`, `ejecucion` (cabecera: fecha UTC y «real» o «no real:
motivos») y `celda` (TEXTO ya formateado), y la transformación `groupingToMatrix` (columnas = `ejecucion`, filas =
`metrica`, valores = `celda`) la pivota; `organize` renombra la primera columna a «Métrica». Las celdas son texto para
poder llevar valor, k/n e IC95 a la vez, y por eso la consulta es la que formatea y la que cruza las ejecuciones con las
métricas presentes (una celda sin dato dice «—», una `not_measured` dice «No medido»; nunca 0 ni vacío).

Qué fija este módulo:

* Estructura del panel (tipo, datasource, formato, transformaciones, `noValue`, `minWidth`, `wrapText`) y que las tablas
  por fila antiguas se conservan como detalle (títulos que terminan en « (detalle)»).
* Nombres: TODAS las métricas del catálogo `docs/validation/JUP-067-metrics-catalogue.json` (17) tienen nombre en la
  consulta (estáticamente: el SQL contiene cada `id` y su nombre; y de forma observable: una ejecución sintética con una
  fila por métrica del catálogo produce el nombre del catálogo para cada una). El catálogo está en ASCII y el dashboard
  puede llevar las tildes correctas: se compara normalizando acentos.
* Variantes traducidas (all->todas, judged->con juicio humano, ...) y las categorías de fallo de STR-2 con nombre en
  español, siempre con el formato «ACC-1 · Casos con resultado pass · todas».
* Contra PostgreSQL real con el manifiesto versionado: dos columnas de ejecución (las dos de JUP-070), una fila por
  métrica y variante, orden del catálogo, una celda de la ejecución 2 que coincide con el informe ORIGINAL (k/n e IC95),
  formato por unidad en todas las celdas y ninguna celda vacía.
* Con una tercera ejecución sintética aparece una tercera columna con el mismo dashboard; lo no medido dice «No medido»,
  lo ausente dice «—», un cero medido es «0.0 %» (no «No medido» ni «—») y el IC95 solo aparece con ambos límites.

Nota sobre «ninguna celda vale 0»: lo que se prohíbe es que lo no medido o lo ausente se vea como 0. Un recuento medido
que vale cero (STR-2 y GRD-2 en los datos versionados) es legítimo y su celda es `0`: lo que se comprueba es que ese `0`
sale de una fila `measured` con valor 0 y no de un hueco.

Los paneles se localizan por título, no por `id` ni posición. Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_matrix.py`
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402

NBSP = "\u00a0"
TITULO = "Resultados por métrica y ejecución"
SIN_EJECUCIONES = "Sin datos: todavía no se han cargado ejecuciones (evaluation-dashboard:load)"
GROUPING = {"columnField": "ejecucion", "rowField": "metrica", "valueField": "celda"}
# Metadatos de la ejecución que NO pueden repetirse en cada fila de la matriz.
METADATOS_PROHIBIDOS = {"commit", "commit_sha", "commit_corto", "suite", "suite_version", "generation_model"}

# Traducciones fijadas por la spec (sin tildes y en minúsculas: se compara normalizando acentos).
VARIANTES = {
    "all": "todas", "judged": "con juicio humano", "clarify": "aclarar", "abstain": "abstenerse", "answer": "responder",
    "median": "mediana", "q1": "primer cuartil", "q3": "tercer cuartil", "embedding": "embedding",
    "retrieval": "recuperacion", "generation": "generacion", "total": "total",
}
# Categorías de fallo de STR-2: el nombre en español lo elige el coder; aquí solo se exige que exista y que no sea el crudo.
CATEGORIAS_STR2 = ("timeout", "connection", "transport", "authentication", "request", "redirect", "rate_limit",
                   "upstream", "invalid_response", "schema_validation")


# --- Localizadores y lectura de la matriz -----------------------------------------------------------------------------


def panel():
    return R.por_titulo(TITULO, "A")


def resultado(preparacion: str = "") -> dict:
    return R.ejecutar(R.consulta_unica(panel()), preparacion)


def nombre_de_catalogo(metric_id: str) -> str:
    return next(m["name"] for m in R.catalogo() if m["id"] == metric_id)


def separar(metrica: str) -> tuple:
    """`(id, nombre, variante)` de un rótulo «ACC-1 · Casos con resultado pass · todas»."""
    partes = metrica.split(" · ")
    if len(partes) != 3:
        raise AssertionError(f"el nombre de la fila debe tener la forma «id · nombre · variante» y es {metrica!r}")
    return tuple(partes)


class Matriz:
    """La consulta del panel pivotada como lo haría `groupingToMatrix`: filas por primera aparición de `metrica`,
    columnas por primera aparición de `ejecucion`."""

    def __init__(self, datos: dict):
        self.columnas_sql = R.nombres(datos)
        self.filas_sql = datos["filas"]
        self.metricas, self.ejecuciones, self.celdas = [], [], {}
        for fila in self.filas_sql:
            metrica, ejecucion = fila["metrica"], fila["ejecucion"]
            if metrica not in self.metricas:
                self.metricas.append(metrica)
            if ejecucion not in self.ejecuciones:
                self.ejecuciones.append(ejecucion)
            if (metrica, ejecucion) in self.celdas:
                raise AssertionError(f"dos filas para la misma celda ({metrica!r}, {ejecucion!r}): la matriz las mezclaría")
            self.celdas[(metrica, ejecucion)] = fila["celda"]

    def columna(self, prefijo_fecha: str) -> str:
        """Cabecera de la ejecución cuya fecha UTC (`AAAA-MM-DD HH:MM`, ISO) empieza por `prefijo_fecha`."""
        encontradas = [e for e in self.ejecuciones if e.startswith(prefijo_fecha)]
        if len(encontradas) != 1:
            raise AssertionError(f"se esperaba una cabecera que empiece por {prefijo_fecha!r}: {self.ejecuciones}")
        return encontradas[0]

    def fila(self, metric_id: str, variante: str) -> str:
        """Nombre de la fila del `metric_id` con la variante (comparada sin tildes)."""
        encontradas = [m for m in self.metricas
                       if separar(m)[0] == metric_id and R.sin_acentos(separar(m)[2]).lower() == variante]
        if len(encontradas) != 1:
            raise AssertionError(f"se esperaba una fila {metric_id} · {variante} y hay {encontradas}; filas: {self.metricas}")
        return encontradas[0]


# --- Valores esperados, calculados de la base y de los informes (nunca de la consulta del panel) -------------------------


def a_decimal(valor: float, decimales: str) -> str:
    """Redondeo de «mitad hacia arriba» sobre la forma decimal más corta del número (la que muestra PostgreSQL)."""
    return str(Decimal(repr(float(valor))).quantize(Decimal(decimales), rounding=ROUND_HALF_UP))


def texto_del_valor(unidad: str, valor: float) -> str:
    """Valor formateado por unidad como en las tablas existentes (separador decimal `.`; la prueba admite `,`)."""
    if unidad == "tasa":
        return a_decimal(valor * 100, "0.1") + " %"
    if unidad == "porcentaje":
        return a_decimal(valor, "0.1") + " %"
    if unidad == "ms":
        return a_decimal(valor, "0.1") + " ms"
    if unidad == "similitud":
        return a_decimal(valor, "0.001")
    if unidad == "recuento":
        return a_decimal(valor, "1")
    raise AssertionError(f"unidad sin formato esperado en esta prueba: {unidad}")


def patron_del_valor(texto: str) -> str:
    """Regex tolerante con el formato regional: `.` o `,` decimales, espacio normal o duro y separador de miles opcional."""
    entero, _, resto = texto.partition(".")
    cifras = re.match(r"^\d+", entero).group(0)
    sufijo_entero = entero[len(cifras):]
    grupos = []
    while cifras:
        grupos.insert(0, cifras[-3:])
        cifras = cifras[:-3]

    def espacios(trozo: str) -> str:
        # Un espacio del texto esperado admite también el espacio duro (U+00A0) que usan algunos formatos regionales.
        return re.escape(trozo).replace(re.escape(" "), "[ " + NBSP + "]")

    patron = ("[.," + NBSP + " ]?").join(grupos) + espacios(sufijo_entero)
    if resto:
        patron += "[.,]" + espacios(resto)
    return "^" + patron + "$"


def comprobar_celda(caso: unittest.TestCase, celda: str, esperado: dict, etiqueta=""):
    """`celda` coincide con la fila de la base `esperado` (claves: status, unit, value, numerator, denominator, ci_low, ci_high).

    Reglas de la spec: lo no medido dice «No medido»; el valor va formateado por unidad; « · k/n» solo si hay numerador
    Y denominador; « · IC95 lo–hi %» solo si hay AMBOS límites; nada más.
    """
    caso.assertIsInstance(celda, str, etiqueta)
    if esperado is None:
        caso.assertEqual(celda, "—", f"{etiqueta}: una celda sin dato dice «—»")
        return
    if esperado["status"] == "not_measured":
        caso.assertEqual(celda, "No medido", f"{etiqueta}: lo no medido dice «No medido»")
        return
    partes = celda.split(" · ")
    caso.assertRegex(partes[0], patron_del_valor(texto_del_valor(esperado["unit"], esperado["value"])),
                     f"{etiqueta}: valor mal formateado en {celda!r}")
    resto = partes[1:]
    con_kn = esperado["numerator"] is not None and esperado["denominator"] is not None
    con_ic = esperado["ci_low"] is not None and esperado["ci_high"] is not None
    if con_kn:
        k = esperado["numerator"]
        k = int(k) if float(k).is_integer() else k
        caso.assertTrue(resto and resto[0] == f"{k}/{esperado['denominator']}",
                        f"{etiqueta}: falta « · {k}/{esperado['denominator']}» en {celda!r}")
        resto = resto[1:]
    if con_ic:
        caso.assertTrue(resto, f"{etiqueta}: falta el IC95 en {celda!r}")
        ic = re.match(r"^IC95 (\d+(?:[.,]\d+)?) ?[–-] ?(\d+(?:[.,]\d+)?) ?%$", resto[0].replace("\u00a0", " "))
        caso.assertIsNotNone(ic, f"{etiqueta}: IC95 mal formado en {celda!r}")
        inferior, superior = (float(g.replace(",", ".")) for g in ic.groups())
        # Tolerancia de medio punto: el IC puede mostrarse entero (67-89 %) o con decimales.
        caso.assertAlmostEqual(inferior, esperado["ci_low"] * 100, delta=0.51, msg=f"{etiqueta}: límite inferior de {celda!r}")
        caso.assertAlmostEqual(superior, esperado["ci_high"] * 100, delta=0.51, msg=f"{etiqueta}: límite superior de {celda!r}")
        resto = resto[1:]
    caso.assertEqual(resto, [], f"{etiqueta}: la celda lleva de más {resto} (k/n o intervalo inventados) en {celda!r}")


def resultados_de_la_base(preparacion: str = "") -> list:
    return R.administrar(
        "SELECT r.run_id, r.run_at, r.is_real, r.non_real_reasons, x.metric_id, x.behavior, x.status, x.unit, x.value,"
        " x.numerator, x.denominator, x.ci_low, x.ci_high FROM evaluation.results x JOIN evaluation.runs r USING (run_id)"
        " WHERE x.grp IN (" + ", ".join(f"'{f}'" for f in R.FAMILIAS) + ")", preparacion)


def cabecera_esperada(fila_db: dict) -> str:
    instante = datetime.fromisoformat(fila_db["run_at"]).astimezone(timezone.utc)
    return instante.strftime("%Y-%m-%d %H:%M")


def informe(numero: int) -> dict:
    return json.loads((R.ROOT / f"docs/evidence/JUP-070-run-{numero}-report.json").read_text(encoding="utf-8"))


# --- Estructura del panel -----------------------------------------------------------------------------------------------


class EstructuraTests(unittest.TestCase):
    def test_existe_un_unico_panel_de_tabla_en_la_seccion_a(self):
        self.assertEqual(panel()["type"], "table")

    def test_es_tipo_a_con_el_datasource_de_postgres_y_formato_tabla(self):
        # `rawQuery`, `editorMode` y `format: table` los exige Grafana para tratar el resultado como tabla.
        p = panel()
        self.assertEqual(p["datasource"], R.DS_POSTGRES)
        self.assertTrue(p["description"].startswith("Tipo: A"))
        self.assertEqual(len(p["targets"]), 1)
        objetivo = p["targets"][0]
        self.assertEqual(objetivo["datasource"], R.DS_POSTGRES)
        self.assertEqual(objetivo["format"], "table")
        self.assertIs(objetivo["rawQuery"], True)
        self.assertEqual(objetivo["editorMode"], "code")

    def test_group_to_matrix_con_las_tres_columnas_y_organize_renombra_la_primera(self):
        # `groupingToMatrix` nombra la primera columna «<rowField>\<columnField>»; sin el `organize` que la renombra
        # la cabecera se vería como `metrica\ejecucion`. La clave del renombrado es la que Grafana 11.3.0 genera.
        transformaciones = panel().get("transformations")
        self.assertIsInstance(transformaciones, list)
        self.assertEqual(transformaciones[0]["id"], "groupingToMatrix")
        opciones = transformaciones[0]["options"]
        for clave, valor in GROUPING.items():
            self.assertEqual(opciones.get(clave), valor)
        siguientes = [t for t in transformaciones[1:] if t["id"] == "organize"]
        self.assertEqual(len(siguientes), 1, "tras groupingToMatrix debe haber un `organize`")
        self.assertEqual(siguientes[0]["options"]["renameByName"].get("metrica\\ejecucion"), "Métrica")

    def test_aviso_sin_datos_ancho_minimo_y_texto_que_envuelve(self):
        # Las celdas llevan valor, k/n e IC95 (más de 30 caracteres): sin `minWidth` y `wrapText` se cortarían.
        por_defecto = R.defaults(panel())
        self.assertEqual(por_defecto.get("noValue"), SIN_EJECUCIONES)
        personalizado = por_defecto.get("custom", {})
        self.assertGreaterEqual(personalizado.get("minWidth", 0), 280)
        self.assertIs(personalizado.get("cellOptions", {}).get("wrapText"), True)

    def test_las_tablas_por_fila_se_conservan_como_detalle(self):
        # La conciliación con los informes originales usa las consultas por fila: no se rehacen, se rotulan «(detalle)».
        for prefijo in ("Exactitud, relevancia y fundamento", "Latencia, formato y disponibilidad de la campaña"):
            with self.subTest(panel=prefijo):
                detalle = R.por_titulo(prefijo, "A")
                self.assertTrue(detalle["title"].endswith(" (detalle)"), detalle["title"])
                self.assertEqual(detalle["type"], "table")
                self.assertRegex(R.sql_de(detalle), r"\bAS\s+valor_texto\b")

    def test_la_consulta_nombra_cada_metrica_del_catalogo_con_su_nombre(self):
        # Estático: el SQL del panel contiene el identificador y el nombre de las 17 métricas de JUP-067. El catálogo
        # está en ASCII y el dashboard puede llevar tildes: se compara sin ellas.
        sql = R.sin_acentos(R.plano(R.consulta_unica(panel())))
        metricas = R.catalogo()
        self.assertEqual(len(metricas), 17)
        for metrica in metricas:
            with self.subTest(metrica=metrica["id"]):
                self.assertRegex(sql, rf"(?<![\w-]){re.escape(metrica['id'])}(?![\w-])",
                                 f"el SQL no menciona la métrica {metrica['id']}")
                self.assertIn(metrica["name"], sql, f"el SQL no lleva el nombre «{metrica['name']}»")

    def test_las_variantes_estan_traducidas_en_la_consulta(self):
        sql = R.sin_acentos(R.plano(R.consulta_unica(panel()))).lower()
        for crudo, traducida in VARIANTES.items():
            if crudo in ("embedding", "total"):
                continue  # se escriben igual en español
            with self.subTest(variante=crudo):
                self.assertIn(f"'{crudo}'", sql)
                self.assertIn(traducida, sql)


# --- Contra PostgreSQL real con el manifiesto versionado ------------------------------------------------------------------


class ConManifiestoVersionadoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Se localiza el panel antes de arrancar nada: sin el panel nuevo el Red falla sin levantar Docker.
        panel()
        cls.datos = resultado()
        cls.matriz = Matriz(cls.datos)
        cls.base = resultados_de_la_base()

    def test_las_columnas_son_las_cuatro_de_la_matriz_y_no_repiten_metadatos(self):
        columnas = set(self.matriz.columnas_sql)
        self.assertLessEqual({"metrica", "orden", "ejecucion", "celda"}, columnas)
        self.assertFalse(columnas & METADATOS_PROHIBIDOS,
                         "los metadatos de la ejecución no se repiten en cada fila de la matriz")
        tipos = dict(self.datos["columnas"])
        self.assertIn(tipos["celda"], ("text", "character varying"))
        self.assertIn(tipos["orden"], ("integer", "bigint", "smallint", "numeric"))

    def test_hay_dos_columnas_de_ejecucion_y_una_fila_por_metrica_y_variante(self):
        pares = {(f["metric_id"], f["behavior"]) for f in self.base}
        self.assertEqual(len(pares), 44)
        self.assertEqual(len(self.matriz.ejecuciones), 2, self.matriz.ejecuciones)
        self.assertEqual(len(self.matriz.metricas), len(pares), "una fila por métrica y variante")
        # La matriz está completa: cada fila tiene celda en cada columna (la consulta cruza ejecuciones con métricas).
        self.assertEqual(len(self.matriz.celdas), len(pares) * 2)
        self.assertEqual(len(self.datos["filas"]), len(pares) * 2)

    def test_las_cabeceras_llevan_fecha_utc_y_tipo_de_ejecucion(self):
        runs = {f["run_id"]: f for f in self.base if f["run_id"].startswith("jup-070-")}
        self.assertEqual(len(runs), 2)
        for cabecera in self.matriz.ejecuciones:
            self.assertRegex(cabecera, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} · (real|no real: .+)$")
        # Las dos campañas son de plantilla: no reales, con sus motivos (la primera además con dobles de prueba).
        primera = self.matriz.columna("2026-10-08 20:13")
        segunda = self.matriz.columna("2026-10-08 21:01")
        self.assertTrue(primera.startswith("2026-10-08 20:13 · no real: ") and segunda.startswith("2026-10-08 21:01 · no real: "))
        for motivo in ("plantilla", "doble"):
            self.assertIn(motivo, primera)
        self.assertIn("plantilla", segunda)
        self.assertNotIn("doble", segunda)

    def test_las_columnas_siguen_el_orden_cronologico(self):
        # `groupingToMatrix` ordena las columnas por primera aparición: la consulta debe emitir las ejecuciones por fecha.
        self.assertEqual([e[:16] for e in self.matriz.ejecuciones], ["2026-10-08 20:13", "2026-10-08 21:01"])

    def test_las_filas_siguen_el_orden_del_catalogo(self):
        # ACC, REL, GRD, LAT, STR, AVL = el orden de las familias y de los ids de JUP-067 (no el alfabético).
        posicion = {m["id"]: i for i, m in enumerate(R.catalogo())}
        ids = [separar(m)[0] for m in self.matriz.metricas]
        indices = [posicion[i] for i in ids]
        self.assertEqual(indices, sorted(indices), f"filas fuera del orden del catálogo: {ids}")
        self.assertEqual(ids[0][:3], "ACC")
        self.assertEqual(ids[-1][:3], "AVL")
        # `orden` es la clave que ordena: constante dentro de una fila y creciente entre filas.
        orden_de = {}
        for fila in self.datos["filas"]:
            self.assertEqual(orden_de.setdefault(fila["metrica"], fila["orden"]), fila["orden"])
        valores = [orden_de[m] for m in self.matriz.metricas]
        self.assertEqual(valores, sorted(set(valores)), "`orden` debe crecer estrictamente de una fila a la siguiente")

    def test_nombres_con_id_nombre_del_catalogo_y_variante_traducida(self):
        # Formato «ACC-1 · Casos con resultado pass · todas»; el nombre sale del catálogo (sin tildes se compara igual).
        vistas = set()
        for metrica in self.matriz.metricas:
            identificador, nombre, variante = separar(metrica)
            with self.subTest(metrica=metrica):
                self.assertEqual(R.sin_acentos(nombre), nombre_de_catalogo(identificador))
                crudos = {f["behavior"] for f in self.base if f["metric_id"] == identificador}
                normalizada = R.sin_acentos(variante).lower()
                esperadas = {VARIANTES[c] for c in crudos if c in VARIANTES}
                if identificador == "STR-2" and normalizada not in esperadas:
                    # Categoría de fallo: nombre en español, distinto del identificador crudo y sin guiones bajos.
                    self.assertNotIn(normalizada, {c.lower() for c in CATEGORIAS_STR2})
                    self.assertNotIn("_", variante)
                    self.assertTrue(variante.strip())
                else:
                    self.assertIn(normalizada, esperadas)
                vistas.add((identificador, normalizada))
        self.assertEqual(len(vistas), len(self.matriz.metricas), "dos variantes distintas comparten el mismo nombre")

    def test_las_diez_categorias_de_fallo_tienen_nombre_propio(self):
        categorias = [separar(m)[2] for m in self.matriz.metricas
                      if separar(m)[0] == "STR-2" and R.sin_acentos(separar(m)[2]).lower() != "todas"]
        self.assertEqual(len(categorias), 10)
        self.assertEqual(len({c.lower() for c in categorias}), 10)

    def test_cada_celda_lleva_el_valor_por_unidad_k_n_e_ic_solo_si_existen(self):
        # Para las 88 celdas: el valor formateado por unidad; « · k/n» si hay numerador y denominador; IC95 si hay ambos
        # límites; una métrica sin intervalo (latencia, similitud, recuentos) no lleva uno inventado.
        por_ejecucion = {}
        for fila in self.base:
            por_ejecucion.setdefault(cabecera_esperada(fila), {}).setdefault(fila["metric_id"], []).append(fila)
        for cabecera, por_id in por_ejecucion.items():
            columna = self.matriz.columna(cabecera)
            for metrica in self.matriz.metricas:
                identificador, _, variante = separar(metrica)
                normalizada = R.sin_acentos(variante).lower()
                candidatos = [f for f in por_id[identificador]
                              if VARIANTES.get(f["behavior"]) == normalizada
                              or (f["behavior"] in CATEGORIAS_STR2 and normalizada not in VARIANTES.values())]
                self.assertTrue(candidatos, (cabecera, metrica))
                celda = self.matriz.celdas[(metrica, columna)]
                with self.subTest(metrica=metrica, ejecucion=columna):
                    self.assertTrue(celda and celda.strip(), "ninguna celda queda vacía")
                    errores = []
                    for candidato in candidatos:
                        try:
                            comprobar_celda(self, celda, candidato, f"{metrica} / {columna}")
                            break
                        except AssertionError as error:
                            errores.append(str(error))
                    else:
                        self.fail("; ".join(errores[:2]))

    def test_ninguna_celda_vacia_y_los_ceros_son_ceros_medidos(self):
        # «Nunca 0 ni vacío» para lo no medido o ausente: aquí todo está medido, así que un `0` pelado solo puede ser
        # un recuento medido que vale cero (STR-2 y GRD-2). Cualquier otra celda lleva unidad.
        medidos_a_cero = {(f["metric_id"], cabecera_esperada(f)) for f in self.base
                          if f["status"] == "measured" and f["unit"] == "recuento" and f["value"] == 0}
        for (metrica, ejecucion), celda in self.matriz.celdas.items():
            with self.subTest(metrica=metrica, ejecucion=ejecucion):
                self.assertTrue(celda.strip())
                if celda.strip() == "0":
                    self.assertIn((separar(metrica)[0], ejecucion[:16]), medidos_a_cero)

    def test_una_celda_de_la_ejecucion_2_coincide_con_el_informe_original(self):
        # Los k/n y los intervalos salen del JSON del informe de JUP-070 (la conciliación existente), no de la base.
        original = informe(2)
        columna = self.matriz.columna("2026-10-08 21:01")
        casos = [
            ("ACC-2", "todas", original["metrics"]["ACC-2"]),
            ("ACC-2", "con juicio humano", original["metrics"]["ACC-2"]["judged"]),
            ("ACC-1", "todas", original["metrics"]["ACC-1"]),
            ("REL-2", "todas", original["metrics"]["REL-2"]),
        ]
        for identificador, variante, datos in casos:
            celda = self.matriz.celdas[(self.matriz.fila(identificador, variante), columna)]
            with self.subTest(metrica=identificador, variante=variante):
                esperado = {"status": "measured", "unit": "tasa", "value": datos["rate"], "numerator": datos["k"],
                            "denominator": datos["n"], "ci_low": datos["ci95"][0], "ci_high": datos["ci95"][1]}
                comprobar_celda(self, celda, esperado, f"{identificador} {variante}")
        # La ejecución 2 de ACC-2 es 25/51 y la 1 es 26/51: cada columna conserva SU valor (no se cruzan).
        fila_acc2 = self.matriz.fila("ACC-2", "todas")
        self.assertIn(" · 25/51 · ", self.matriz.celdas[(fila_acc2, columna)])
        self.assertIn(" · 26/51 · ", self.matriz.celdas[(fila_acc2, self.matriz.columna("2026-10-08 20:13"))])
        self.assertRegex(self.matriz.celdas[(fila_acc2, columna)], r"^49[.,]0 ?%")

    def test_una_metrica_sin_intervalo_no_lo_lleva(self):
        columna = self.matriz.columna("2026-10-08 21:01")
        for identificador, variante in (("LAT-1", "total"), ("REL-4", "mediana"), ("GRD-2", "todas")):
            celda = self.matriz.celdas[(self.matriz.fila(identificador, variante), columna)]
            with self.subTest(metrica=identificador):
                self.assertNotIn("IC95", celda)
                self.assertNotIn("/", celda, "sin numerador no hay k/n")

    def test_latencia_y_similitud_con_su_unidad(self):
        columna = self.matriz.columna("2026-10-08 21:01")
        self.assertRegex(self.matriz.celdas[(self.matriz.fila("LAT-2", "total"), columna)], r"^4[.,\u00a0 ]?561[.,]7[ \u00a0]ms$")
        self.assertRegex(self.matriz.celdas[(self.matriz.fila("REL-4", "mediana"), columna)], r"^0[.,]617$")


# --- Escenarios sintéticos (siempre con ROLLBACK: el conjunto versionado no cambia) ----------------------------------------


def tercera_ejecucion() -> str:
    """Tercera campaña real de JUP-070 con nulos, ceros medidos, intervalos incompletos y una variante nueva."""
    ejecucion = "rd-s3"
    return R.insertar_ejecucion(ejecucion, "JUP-070", "2026-10-14T09:30:00Z", real=True) + "".join([
        R.insertar_resultado(ejecucion, "accuracy", "ACC-1", estado="not_measured", denominador=20, juicio="human"),
        R.insertar_resultado(ejecucion, "accuracy", "ACC-2", valor=0.8, numerador=40, denominador=50, ci_bajo=0.67,
                             ci_alto=0.89),
        R.insertar_resultado(ejecucion, "accuracy", "ACC-3", "answer", valor=0.5, numerador=5, denominador=10),
        R.insertar_resultado(ejecucion, "relevance", "REL-1", valor=0.0, numerador=0, denominador=10),
        R.insertar_resultado(ejecucion, "grounding", "GRD-1", valor=0.3, numerador=3, ci_bajo=0.1, ci_alto=0.6),
        R.insertar_resultado(ejecucion, "grounding", "GRD-2", valor=3, unidad="recuento"),
        R.insertar_resultado(ejecucion, "latency", "LAT-1", "total", valor=1234.5, unidad="ms", denominador=10),
        R.insertar_resultado(ejecucion, "availability", "AVL-1", valor=0.9, numerador=9, denominador=10, ci_bajo=0.6),
    ])


# Fila de la base que cada celda sintética debe reflejar (lo insertado arriba).
S3 = {
    ("ACC-1", "todas"): {"status": "not_measured"},
    ("ACC-2", "todas"): {"status": "measured", "unit": "tasa", "value": 0.8, "numerator": 40, "denominator": 50,
                         "ci_low": 0.67, "ci_high": 0.89},
    ("ACC-3", "responder"): {"status": "measured", "unit": "tasa", "value": 0.5, "numerator": 5, "denominator": 10,
                             "ci_low": None, "ci_high": None},
    ("REL-1", "todas"): {"status": "measured", "unit": "tasa", "value": 0.0, "numerator": 0, "denominator": 10,
                         "ci_low": None, "ci_high": None},
    ("GRD-1", "todas"): {"status": "measured", "unit": "tasa", "value": 0.3, "numerator": 3, "denominator": None,
                         "ci_low": 0.1, "ci_high": 0.6},
    ("GRD-2", "todas"): {"status": "measured", "unit": "recuento", "value": 3, "numerator": None, "denominator": None,
                         "ci_low": None, "ci_high": None},
    ("LAT-1", "total"): {"status": "measured", "unit": "ms", "value": 1234.5, "numerator": None, "denominator": 10,
                         "ci_low": None, "ci_high": None},
    ("AVL-1", "todas"): {"status": "measured", "unit": "tasa", "value": 0.9, "numerator": 9, "denominator": 10,
                         "ci_low": 0.6, "ci_high": None},
}


class TerceraEjecucionSinteticaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        panel()
        cls.matriz = Matriz(resultado(tercera_ejecucion()))

    def test_aparece_una_tercera_columna_sin_tocar_el_dashboard(self):
        self.assertEqual(len(self.matriz.ejecuciones), 3, self.matriz.ejecuciones)
        self.assertEqual(self.matriz.ejecuciones[-1], "2026-10-14 09:30 · real")
        # Una ejecución real no lleva «no real» ni motivos en la cabecera.
        self.assertNotIn("no real", self.matriz.ejecuciones[-1])

    def test_una_fila_nueva_se_inserta_en_su_sitio_del_catalogo_y_las_demas_columnas_dicen_sin_dato(self):
        # `ACC-3 · responder` solo existe en la ejecución sintética: aparece como fila nueva y en las otras dos
        # ejecuciones su celda es «—» (no 0, no vacía). Sigue después de ACC-2 y antes de REL-1 (orden del catálogo).
        fila = self.matriz.fila("ACC-3", "responder")
        for cabecera in self.matriz.ejecuciones[:2]:
            self.assertEqual(self.matriz.celdas[(fila, cabecera)], "—")
        ids = [separar(m)[0] for m in self.matriz.metricas]
        self.assertLess(ids.index("ACC-2"), ids.index("ACC-3"))
        self.assertLess(len(ids) - 1 - ids[::-1].index("ACC-3"), ids.index("REL-1"))
        self.assertEqual(len(self.matriz.metricas), 45)

    def test_una_metrica_ausente_de_la_ejecucion_dice_sin_dato(self):
        # REL-2 existe en las dos campañas de plantilla y no en la sintética: «—» y no 0 % ni «No medido».
        celda = self.matriz.celdas[(self.matriz.fila("REL-2", "todas"), self.matriz.ejecuciones[-1])]
        self.assertEqual(celda, "—")

    def test_cada_celda_sintetica_refleja_su_fila(self):
        ultima = self.matriz.ejecuciones[-1]
        for (identificador, variante), esperado in S3.items():
            with self.subTest(metrica=identificador, variante=variante):
                comprobar_celda(self, self.matriz.celdas[(self.matriz.fila(identificador, variante), ultima)],
                                esperado, f"{identificador} {variante}")

    def test_lo_no_medido_dice_no_medido_y_un_cero_medido_no_se_confunde_con_el_(self):
        ultima = self.matriz.ejecuciones[-1]
        self.assertEqual(self.matriz.celdas[(self.matriz.fila("ACC-1", "todas"), ultima)], "No medido")
        cero = self.matriz.celdas[(self.matriz.fila("REL-1", "todas"), ultima)]
        self.assertRegex(cero, r"^0[.,]0 ?% · 0/10$")
        self.assertNotIn(cero, ("0", "", "No medido", "—"))

    def test_el_intervalo_exige_ambos_limites(self):
        ultima = self.matriz.ejecuciones[-1]
        # Solo límite inferior (AVL-1): ni IC95 ni medio intervalo inventado.
        self.assertNotIn("IC95", self.matriz.celdas[(self.matriz.fila("AVL-1", "todas"), ultima)])
        # Sin intervalo en la base (ACC-3 responder, REL-1 con k/n): el k/n sí, el IC95 no.
        for identificador, variante in (("ACC-3", "responder"), ("REL-1", "todas")):
            self.assertNotIn("IC95", self.matriz.celdas[(self.matriz.fila(identificador, variante), ultima)])
        # Intervalo sin denominador (GRD-1): IC95 sí, k/n no.
        celda = self.matriz.celdas[(self.matriz.fila("GRD-1", "todas"), ultima)]
        self.assertIn("IC95", celda)
        self.assertNotRegex(celda, r"\d/\d")


class TodasLasMetricasDelCatalogoTests(unittest.TestCase):
    """Una ejecución sintética con UNA fila por cada métrica del catálogo, variante `total` (que los datos versionados no usan)."""

    @classmethod
    def setUpClass(cls):
        panel()
        preparacion = R.insertar_ejecucion("rd-cat", "JUP-070", "2026-10-14T10:00:00Z", real=True)
        for metrica in R.catalogo():
            preparacion += R.insertar_resultado("rd-cat", metrica["family"], metrica["id"], "total", valor=0.5,
                                                unidad=metrica["unit"], denominador=10)
        cls.matriz = Matriz(resultado(preparacion))

    def test_las_17_metricas_del_catalogo_tienen_nombre_y_el_nombre_es_el_del_catalogo(self):
        for metrica in R.catalogo():
            with self.subTest(metrica=metrica["id"]):
                fila = self.matriz.fila(metrica["id"], "total")
                self.assertEqual(R.sin_acentos(separar(fila)[1]), metrica["name"])

    def test_el_orden_de_las_17_sigue_el_del_catalogo(self):
        posicion = {m["id"]: i for i, m in enumerate(R.catalogo())}
        indices = [posicion[separar(m)[0]] for m in self.matriz.metricas]
        self.assertEqual(indices, sorted(indices))


class SinEjecucionesTests(unittest.TestCase):
    def test_sin_ejecuciones_con_resultados_no_hay_filas_y_la_consulta_no_falla(self):
        # El `noValue` del panel («Sin datos: todavía no se han cargado ejecuciones») solo se ve con CERO filas: la
        # consulta no puede inventar una fila vacía ni fallar cuando no hay nada cargado.
        panel()
        datos = resultado("DELETE FROM evaluation.runs;")
        self.assertEqual(datos["filas"], [])
        self.assertLessEqual({"metrica", "orden", "ejecucion", "celda"}, set(R.nombres(datos)))


if __name__ == "__main__":
    unittest.main()
