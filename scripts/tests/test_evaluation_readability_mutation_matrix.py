"""Tabla «Resultados por métrica y ejecución»: casos añadidos tras la fase de mutación (JUP-121, change `jup-121-lectura-dashboard`).

Complementa a `test_evaluation_readability_matrix.py` (commiteado, no se toca). Las pruebas originales comprueban las
celdas con tolerancia (guion o raya en el intervalo, con o sin decimales) y usan sobre todo los datos versionados, que no
ejercitan todas las ramas de la consulta. Los mutantes que sobrevivieron señalaron estos huecos, que aquí se cierran con
escenarios sintéticos (siempre con `ROLLBACK`) y con valores EXACTOS esperados:

* Formato del intervalo: `IC95 lo–hi %` con raya larga y un decimal, tal como lo documenta la guía. Un intervalo con SOLO
  el límite superior no se muestra (la prueba original solo probaba el caso del límite inferior).
* Unidades con rama propia que los datos versionados no usan: `porcentaje` (no se multiplica por 100) y una unidad
  desconocida (valor redondeado a 4 decimales seguido de su unidad, sin perderla).
* Nombres de lo que no está en el catálogo: una variante nueva se muestra tal cual (no desaparece) y un identificador
  desconocido no repite su propio id como si fuera su nombre.
* Orden: dentro de una métrica la variante «todas» va primera aunque otra sea alfabéticamente anterior; las columnas
  van por fecha UTC, con desempate por identificador y las ejecuciones sin fecha al final (con su identificador en la
  cabecera para distinguirlas).
* Una ejecución que solo trae disponibilidad también es una columna.
* Una misma métrica y variante en dos grupos distintos no se mezclan en la celda.

Ruta del dashboard: `EVALUATION_DASHBOARD_JSON`.
Ejecución: `python -m unittest scripts/tests/test_evaluation_readability_mutation_matrix.py`
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R  # noqa: E402
import test_evaluation_readability_matrix as M  # noqa: E402  (solo sus ayudantes: Matriz, separar, resultado)

DECIMAL = "[.,]"  # la prueba admite coma o punto decimal según la configuración regional de la base


def fila_de(matriz, identificador: str, variante: str) -> str:
    """Nombre de la fila `identificador` con esa variante (sin tildes). Propio porque `Matriz.fila` exige el formato de 3
    partes y aquí hay filas deliberadamente sin nombre (identificador fuera del catálogo)."""
    encontradas = [m for m in matriz.metricas
                   if m.split(" · ")[0] == identificador and R.sin_acentos(m.split(" · ")[-1]).lower() == variante]
    if len(encontradas) != 1:
        raise AssertionError(f"se esperaba una fila {identificador} · {variante} y hay {encontradas}")
    return encontradas[0]


def preparacion_de_formatos() -> str:
    """Una ejecución real sintética con una fila por cada rama de formato que los datos versionados no ejercitan."""
    r = "rm-f"
    return R.insertar_ejecucion(r, "JUP-070", "2026-10-14T09:30:00Z", real=True) + "".join([
        # Intervalo completo con k/n: la celda de referencia del formato.
        R.insertar_resultado(r, "accuracy", "ACC-2", valor=0.8, numerador=40, denominador=50, ci_bajo=0.67, ci_alto=0.89),
        # Dos variantes de la misma métrica: «all» debe ir antes que «abstain» aunque «abstain» sea anterior alfabéticamente.
        R.insertar_resultado(r, "accuracy", "ACC-3", "all", valor=0.5, numerador=5, denominador=10),
        R.insertar_resultado(r, "accuracy", "ACC-3", "abstain", valor=0.25, numerador=1, denominador=4),
        # Solo el límite SUPERIOR: no hay intervalo que mostrar (el loader lo prohíbe, la base lo permitiría).
        R.insertar_resultado(r, "grounding", "GRD-1", valor=0.3, numerador=3, denominador=10, ci_alto=0.6),
        # Unidad `porcentaje`: el valor ya viene en tanto por ciento, no se multiplica por 100.
        R.insertar_resultado(r, "accuracy", "ACC-1", "all", valor=12.5, unidad="porcentaje"),
        # Variante que el CASE de traducciones no conoce: se muestra el valor de la base, no se pierde.
        R.insertar_resultado(r, "accuracy", "ACC-1", "zz_nueva", valor=0.2),
        # Unidad desconocida: valor redondeado a 4 decimales + su unidad; un entero no lleva decimales.
        R.insertar_resultado(r, "relevance", "REL-2", valor=2, unidad="zzz"),
        R.insertar_resultado(r, "relevance", "REL-3", valor=0.12345678, unidad="zzz"),
        # Numerador con ruido de coma flotante (0.1 + 0.2 se guarda como 0.30000000000000004): la celda lo muestra limpio.
        R.insertar_resultado(r, "grounding", "GRD-3", valor=0.03, numerador=0.1 + 0.2, denominador=10),
        # Identificador que no está en el catálogo: sin nombre, pero tampoco con su id repetido como nombre.
        R.insertar_resultado(r, "accuracy", "XYZ-9", valor=0.1),
    ])


class FormatosExactosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        M.panel()
        cls.matriz = M.Matriz(M.resultado(preparacion_de_formatos()))
        cls.columna = cls.matriz.columna("14-10 09:30")

    def celda(self, identificador: str, variante: str) -> str:
        return self.matriz.celdas[(fila_de(self.matriz, identificador, variante), self.columna)]

    def test_intervalo_completo_con_raya_larga_y_un_decimal(self):
        # Formato documentado en la guía: `IC95 lo–hi %`. La prueba original aceptaba también el guion corto y la
        # cifra entera; el formato es parte del contrato porque la guía lo describe con esa forma exacta.
        self.assertRegex(self.celda("ACC-2", "todas"), rf"^80{DECIMAL}0 % · 40/50 · IC95 67{DECIMAL}0–89{DECIMAL}0 %$")

    def test_solo_el_limite_superior_no_muestra_intervalo_pero_conserva_valor_y_k_n(self):
        celda = self.celda("GRD-1", "todas")
        self.assertNotIn("IC95", celda)
        self.assertRegex(celda, rf"^30{DECIMAL}0 % · 3/10$")

    def test_el_numerador_no_arrastra_ruido_de_coma_flotante(self):
        # Caso límite: un informe generado con sumas de decimales trae 0.30000000000000004; la celda debe decir «0.3/10»,
        # no la cola de la representación binaria (la consulta normaliza el numerador antes de escribirlo).
        self.assertRegex(self.celda("GRD-3", "todas"), rf"^3{DECIMAL}0 % · 0{DECIMAL}3/10$")

    def test_unidad_porcentaje_no_se_multiplica_por_cien(self):
        self.assertRegex(self.celda("ACC-1", "todas"), rf"^12{DECIMAL}5 %$")

    def test_unidad_desconocida_redondea_a_cuatro_decimales_y_conserva_la_unidad(self):
        self.assertRegex(self.celda("REL-3", "todas"), rf"^0{DECIMAL}1235 zzz$")
        self.assertEqual(self.celda("REL-2", "todas"), "2 zzz")

    def test_una_variante_nueva_se_muestra_tal_cual_en_el_nombre_de_la_fila(self):
        fila = [m for m in self.matriz.metricas if m.startswith("ACC-1 · ") and m.endswith(" · zz_nueva")]
        self.assertEqual(len(fila), 1, self.matriz.metricas)
        self.assertEqual(fila[0], "ACC-1 · Casos con resultado pass · zz_nueva")

    def test_un_identificador_fuera_del_catalogo_no_repite_su_id_como_nombre(self):
        fila = [m for m in self.matriz.metricas if m.startswith("XYZ-9")]
        self.assertEqual(fila, ["XYZ-9 · todas"])

    def test_la_variante_todas_va_antes_que_las_demas_de_su_metrica(self):
        # «abstain» < «all» alfabéticamente: un orden por nombre de variante pondría «abstenerse» primero.
        filas = [m for m in self.matriz.metricas if m.startswith("ACC-3 · ")]
        variantes = [M.separar(m)[2] for m in filas]
        self.assertEqual(variantes[0], "todas", variantes)
        self.assertEqual(set(variantes), {"todas", "abstenerse", "aclarar"}, variantes)


def preparacion_de_calendario() -> str:
    """Ejecuciones que prueban el orden y la cabecera de las columnas, insertadas A PROPÓSITO en el orden contrario."""
    sql = ""
    # Misma fecha, tipos distintos (cabeceras distintas): u1 (real) debe ir antes que u2 (no real) aunque se inserte después.
    sql += R.insertar_ejecucion("rm-u2", "JUP-070", "2026-10-14T09:30:00Z", real=False, motivos=("doble",))
    sql += R.insertar_ejecucion("rm-u1", "JUP-070", "2026-10-14T09:30:00Z", real=True)
    # Dos sin fecha, insertadas al revés: van al final, ordenadas por identificador, con el identificador en la cabecera.
    sql += R.insertar_ejecucion("rm-t1", "JUP-070", None, real=False, motivos=("sintetica",))
    sql += R.insertar_ejecucion("rm-t0", "JUP-070", None, real=False, motivos=("sintetica",))
    # Una ejecución que SOLO trae disponibilidad (grupo `availability`): también es una columna de la matriz.
    sql += R.insertar_ejecucion("rm-av", "JUP-070", "2026-10-13T08:00:00Z", real=True)
    sql += R.insertar_resultado("rm-av", "availability", "AVL-1", valor=0.9, numerador=9, denominador=10)
    for ejecucion in ("rm-u1", "rm-u2", "rm-t0", "rm-t1"):
        sql += R.insertar_resultado(ejecucion, "accuracy", "ACC-1", valor=0.5)
    return sql


class CalendarioDeColumnasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        M.panel()
        cls.matriz = M.Matriz(M.resultado(preparacion_de_calendario()))

    def test_orden_exacto_de_las_columnas_y_cabecera_de_las_sin_fecha(self):
        # Las dos campañas versionadas (08-10) van primero; después por fecha; a igual fecha, por identificador; y las
        # ejecuciones sin fecha al final, por identificador, con «sin fecha · <id>» para distinguirlas entre sí.
        esperado = [
            "13-10 08:00 · real",
            "14-10 09:30 · real",
            "14-10 09:30 · no real: doble",
            "sin fecha · rm-t0 · no real: sintetica",
            "sin fecha · rm-t1 · no real: sintetica",
        ]
        self.assertEqual(self.matriz.ejecuciones[2:], esperado, self.matriz.ejecuciones)

    def test_la_ejecucion_que_solo_trae_disponibilidad_tiene_su_columna_y_su_celda(self):
        columna = self.matriz.columna("13-10 08:00")
        celda = self.matriz.celdas[(fila_de(self.matriz, "AVL-1", "todas"), columna)]
        self.assertRegex(celda, rf"^90{DECIMAL}0 % · 9/10$")
        # Y no inventa nada en las demás métricas: «—».
        self.assertEqual(self.matriz.celdas[(fila_de(self.matriz, "ACC-1", "todas"), columna)], "—")


class MismaMetricaEnDosGruposTests(unittest.TestCase):
    def test_la_celda_de_cada_grupo_solo_toma_las_filas_de_su_grupo(self):
        # Caso límite del esquema: la clave primaria incluye `grp`, así que una misma (métrica, variante) puede existir
        # en dos grupos. Cada fila del catálogo debe cruzarse solo con las filas de SU grupo; si no, una celda se
        # duplicaría con el valor del otro grupo. Se examinan las filas crudas porque ambos nombres coinciden.
        r = "rm-g"
        preparacion = (R.insertar_ejecucion(r, "JUP-070", "2026-10-14T11:00:00Z", real=True)
                       + R.insertar_resultado(r, "accuracy", "ACC-1", valor=0.5)
                       + R.insertar_resultado(r, "relevance", "ACC-1", valor=0.9))
        filas = [f for f in M.resultado(preparacion)["filas"]
                 if f["ejecucion"].startswith("14-10 11:00") and f["metrica"].startswith("ACC-1 · ")]
        celdas = sorted(re.sub(r"[.,]", ".", f["celda"]) for f in filas)
        self.assertEqual(celdas, ["50.0 %", "90.0 %"], filas)


if __name__ == "__main__":
    unittest.main()
