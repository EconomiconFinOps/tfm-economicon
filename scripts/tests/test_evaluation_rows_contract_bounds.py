"""Cotas y formato de la validación común de filas `rows-v1` (JUP-121, tarea 2.6, remediación de hallazgos de QA).

Tres huecos del contrato que dejó el QA sobre `validate_rows` / `adapt_rows_v1` de `tools/evaluation-dashboard.py`:

* M1. `run.run_at` solo se validaba con `datetime.fromisoformat`, que en Python 3.13 admite cualquier carácter
  como separador entre fecha y hora y formas como `2026-W42-3` o `20261014`. Un valor así llegaría tal cual a un
  script SQL. Contrato nuevo: `run_at` es `None` o una cadena de formato EXACTO
  `AAAA-MM-DDThh:mm:ss[.f{1,6}](Z|±hh:mm)` que además `fromisoformat` acepta (fecha y hora reales). El error
  empieza por `run.run_at: ` y NO repite el valor recibido (L1: no se vuelca texto de un informe en un mensaje).
* M2. Los enteros de Python tienen precisión arbitraria, pero la carga SQL usa columnas `bigint` y
  `double precision`. Cota `ROW_MAX_INTEGER = 2**53 - 1` (el mayor entero que un float representa sin pérdida):
  `count` y `denominator` en `[0, ROW_MAX_INTEGER]`; `value`, `numerator`, `ci_low` y `ci_high` con
  `abs(x) <= ROW_MAX_INTEGER` cuando son enteros. Los flotantes finitos NO tienen cota nueva.
* L2. Orden de los errores cuando una fila tiene dos defectos a la vez. Hoy se cumple; estas pruebas lo fijan para
  que invertir el orden de las dos comprobaciones (claves desconocidas antes que ausentes; intervalo antes que
  tasa) no sea un mutante superviviente.

Este fichero NO modifica pruebas ya commiteadas: añade casos nuevos. Cada caso se ejecuta con `validate_rows` y con
`adapt_rows_v1`. Las filas de ejemplo se construyen a mano para que cambie solo el dato que se quiere probar; para
`run_at` se usan además los informes REALES de JUP-070 (run-2 y run-1) y de JUP-022 con sus adaptadores.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para apuntar
estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_contract_bounds", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

EVIDENCE = ROOT / "docs" / "evidence"
JUP_070_RUN_1 = EVIDENCE / "JUP-070-run-1-report.json"
JUP_070_RUN_2 = EVIDENCE / "JUP-070-run-2-report.json"
JUP_022_REPORT = ROOT / "docs" / "spikes" / "JUP-022-retrieval-calibration.json"

# Claves literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
    "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)

# Cota literal (no se importa de la herramienta: así las fronteras se comprueban contra el número del contrato).
MAX_INT = 2 ** 53 - 1
# Formato exacto que el contrato exige a `run_at`; se repite aquí para comprobar que las salidas reales lo cumplen.
RUN_AT_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|[+-]\d{2}:\d{2})\Z")


def make_run(**changes) -> dict:
    # Ejecución mínima válida: solo run_id y source son obligatorios con valor; el resto, None o False.
    run = dict.fromkeys(RUN_KEYS)
    run.update({"run_id": "run-bounds", "source": "bounds-test", "synthetic": False})
    run.update(changes)
    return run


def make_row(**changes) -> dict:
    # Fila `not_measured` válida: tipo A, unidad `tasa`, solo denominador.
    row = dict.fromkeys(RESULT_KEYS)
    row.update({
        "measure_type": "A", "grp": "grp-a", "metric_id": "M-1", "behavior": "behavior-a",
        "status": "not_measured", "unit": "tasa", "denominator": 20, "judgment": "automatic", "selected": False,
    })
    row.update(changes)
    return row


def make_case_row(**changes) -> dict:
    # Fila de estado de caso `pass` válida: lleva recuento y no valor ni numerador.
    # Se mezcla en un dict para que `changes` pueda sustituir `count` sin chocar con el argumento fijo.
    return make_row(**{"status": "pass", "count": 3, **changes})


def make_measured_row(**changes) -> dict:
    # Fila `measured` tipo A válida: lleva valor y no recuento; tasa 10/20.
    return make_row(**{"status": "measured", "value": 0.5, "numerator": 10, **changes})


def make_measured_b_row(**changes) -> dict:
    # Fila `measured` tipo B con unidad `eur_minor_2`: no es `tasa`, así que el numerador NO está acotado por el
    # denominador y se puede probar la cota de enteros sin que la regla de la tasa se adelante. El tipo B no tiene
    # rúbrica: su juicio es None.
    return make_row(**{"measure_type": "B", "status": "measured", "value": 0.5, "numerator": 10,
                       "unit": "eur_minor_2", "judgment": None, **changes})


def document(run: dict, row: dict) -> dict:
    # Documento `rows-v1` equivalente a (run, [row]); el adaptador rellena lo opcional que falte.
    return {"contract_version": 1, "run": run, "results": [row]}


class BoundsBase(unittest.TestCase):
    def assert_rejected_pair(self, run: dict, row: dict, prefix: str, forbidden: str | None = None) -> None:
        """(run, [row]) se rechaza con `AdapterError` cuyo mensaje EMPIEZA por `prefix`, por las dos vías.

        Si `forbidden` no es None, además NO debe aparecer en el mensaje (el error no repite el valor recibido).
        """
        for name, call in (
            ("validate_rows", lambda: tool.validate_rows(copy.deepcopy(run), [copy.deepcopy(row)])),
            ("adapt_rows_v1", lambda: tool.adapt_rows_v1(document(copy.deepcopy(run), copy.deepcopy(row)))),
        ):
            with self.subTest(via=name):
                with self.assertRaises(tool.AdapterError) as caught:
                    call()
                message = str(caught.exception)
                self.assertTrue(
                    message.startswith(prefix),
                    f"se esperaba el prefijo {prefix!r} y llegó {message!r}",
                )
                if forbidden is not None:
                    self.assertNotIn(forbidden, message, "el mensaje no debe repetir el valor recibido")

    def assert_accepted_pair(self, run: dict, row: dict) -> None:
        """(run, [row]) es válido por las dos vías (sin excepción) y el adaptador devuelve lo mismo que recibió."""
        with self.subTest(via="validate_rows"):
            tool.validate_rows(copy.deepcopy(run), [copy.deepcopy(row)])
        with self.subTest(via="adapt_rows_v1"):
            out_run, out_results = tool.adapt_rows_v1(document(copy.deepcopy(run), copy.deepcopy(row)))
            self.assertEqual(out_run, run)
            self.assertEqual(out_results, [row])

    def assert_rejected(self, row: dict, prefix: str) -> None:
        self.assert_rejected_pair(make_run(), row, prefix)

    def assert_accepted(self, row: dict) -> None:
        self.assert_accepted_pair(make_run(), row)


# --- M1: run_at estricto ------------------------------------------------------------------------------------

class RunAtAcceptedTests(BoundsBase):
    """Formas válidas de `run_at`: las de los informes reales y las variantes del formato exacto."""

    def test_valid_forms_are_accepted(self) -> None:
        valid = (
            "2026-10-08T21:01:44Z",                # JUP-070: segundos y Z, sin fracción.
            "2026-10-03T07:15:32.826486+00:00",    # JUP-022: seis dígitos de fracción y desplazamiento +00:00.
            "2026-10-14T10:00:00-05:30",           # Desplazamiento negativo con minutos distintos de cero.
            "2026-10-14T10:00:00.1Z",              # Fracción de un solo dígito (límite inferior de 1 a 6).
            "2026-10-14T10:00:00.123456Z",         # Fracción de seis dígitos (límite superior).
            "2024-02-29T23:59:59Z",                # 29 de febrero de un año bisiesto: fecha real.
        )
        for value in valid:
            with self.subTest(run_at=value):
                self.assert_accepted_pair(make_run(run_at=value), make_row())

    def test_none_is_accepted(self) -> None:
        # `run_at` es opcional: None significa «no registrado» y no es un error.
        self.assert_accepted_pair(make_run(run_at=None), make_row())


class RunAtRejectedTests(BoundsBase):
    """Todo lo que no cumple el formato exacto se rechaza en `run.run_at`, aunque `fromisoformat` lo acepte."""

    PREFIX = "run.run_at: "

    def test_wrong_separator_is_rejected(self) -> None:
        # `fromisoformat` de Python 3.13 admite CUALQUIER carácter como separador; el contrato solo admite la `T`
        # mayúscula. Se cubren las comillas y el punto y coma (inyección SQL), un NUL, el espacio y la `t` minúscula.
        for value in ("2026-10-14'10:00:00Z", "2026-10-14;10:00:00Z", "2026-10-14\x0010:00:00Z",
                      "2026-10-14 10:00:00Z", "2026-10-14t10:00:00Z"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_non_extended_date_forms_are_rejected(self) -> None:
        # Formas ISO 8601 válidas para `fromisoformat` (semana ISO, fecha básica) pero fuera del formato exacto.
        for value in ("2026-W42-3", "20261014"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_missing_parts_are_rejected(self) -> None:
        # Hora, segundos y zona son obligatorios: una fecha sin hora, una hora sin segundos o sin zona no cumple.
        for value in ("2026-10-14", "2026-10-14T10:00Z", "2026-10-14T10:00:00"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_bad_fraction_is_rejected(self) -> None:
        # Fracción vacía (punto sin dígitos) y de 7 dígitos (el contrato admite de 1 a 6).
        for value in ("2026-10-14T10:00:00.Z", "2026-10-14T10:00:00.1234567Z"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_impossible_dates_and_times_are_rejected(self) -> None:
        # Cumplen el patrón de dígitos pero no son una fecha u hora reales: mes 13, 30 de febrero, hora 25. Atrapa
        # un validador que solo mirase el patrón y no `fromisoformat`.
        for value in ("2026-13-01T00:00:00Z", "2026-02-30T00:00:00Z", "2026-10-14T25:00:00Z"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_trailing_or_leading_garbage_is_rejected(self) -> None:
        # `$` en una expresión regular admite un salto de línea final; aquí no. Y un espacio inicial tampoco.
        for value in ("2026-10-14T10:00:00Z\n", " 2026-10-14T10:00:00Z", "2026-10-14T10:00:00Z "):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_offset_without_colon_is_rejected(self) -> None:
        # `+0000` es ISO 8601 válido para `fromisoformat`, pero el contrato exige `+hh:mm`.
        self.assert_rejected_pair(make_run(run_at="2026-10-14T10:00:00+0000"), make_row(), self.PREFIX)

    def test_empty_string_is_rejected(self) -> None:
        # La cadena vacía no es None: no se trata como «no registrado».
        self.assert_rejected_pair(make_run(run_at=""), make_row(), self.PREFIX)

    def test_non_string_values_are_rejected(self) -> None:
        # Un entero y un booleano (True es un int en Python) no son cadenas de fecha.
        for value in (5, True, 1.5, ["2026-10-14T10:00:00Z"]):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX)

    def test_message_does_not_echo_the_received_value(self) -> None:
        # L1: el mensaje se imprime en consola y en el diagnóstico de la carga; repetir texto de un informe
        # (posiblemente hostil) en él es una vía de inyección. El marcador solo puede aparecer si el error vuelca
        # el valor (por ejemplo, el texto de la excepción de `fromisoformat`, que lo cita).
        for value in ("2026-10-14MARCADOR'x10:00:00Z", "MARCADOR'x", "2026-10-14T10:00:00ZMARCADOR'x",
                      "2026-13-01T00:00:00Z-MARCADOR'x"):
            with self.subTest(run_at=value):
                self.assert_rejected_pair(make_run(run_at=value), make_row(), self.PREFIX, forbidden="MARCADOR")


class RunAtRealReportsTests(BoundsBase):
    """Las salidas reales de los adaptadores de JUP-070 y JUP-022 siguen siendo válidas con el formato estricto."""

    def check(self, path: Path, adapter) -> None:
        report = json.loads(path.read_text(encoding="utf8"))
        run, results = adapter(report, "id-real")
        # El informe real trae `run_at`: si el adaptador lo dejase en None la prueba no ejercitaría el formato.
        self.assertIsNotNone(run["run_at"], f"{path.name} debería traer run_at")
        self.assertRegex(run["run_at"], RUN_AT_FORMAT)
        tool.validate_rows(run, results)

    def test_jup070_run_2_output_is_valid(self) -> None:
        self.check(JUP_070_RUN_2, tool.adapt_jup070)

    def test_jup070_run_1_output_is_valid(self) -> None:
        self.check(JUP_070_RUN_1, tool.adapt_jup070)

    def test_jup022_output_is_valid(self) -> None:
        self.check(JUP_022_REPORT, tool.adapt_jup022)


# --- M2: cotas de enteros ----------------------------------------------------------------------------------

class IntegerBoundConstantTests(unittest.TestCase):
    def test_constant_exists_and_is_2_pow_53_minus_1(self) -> None:
        # Mayor entero que un float de doble precisión representa sin pérdida; es también la cota segura de la
        # carga SQL (`bigint` y `double precision`).
        self.assertTrue(hasattr(tool, "ROW_MAX_INTEGER"), "falta la constante ROW_MAX_INTEGER")
        self.assertEqual(tool.ROW_MAX_INTEGER, 2 ** 53 - 1)
        self.assertIs(type(tool.ROW_MAX_INTEGER), int)


class CountAndDenominatorBoundsTests(BoundsBase):
    """`count` y `denominator`: enteros en `[0, ROW_MAX_INTEGER]`."""

    def test_count_at_the_maximum_is_valid(self) -> None:
        self.assert_accepted(make_case_row(count=MAX_INT))

    def test_count_above_the_maximum_is_rejected(self) -> None:
        self.assert_rejected(make_case_row(count=MAX_INT + 1), "results[0].count: ")

    def test_denominator_at_the_maximum_is_valid(self) -> None:
        self.assert_accepted(make_row(denominator=MAX_INT))

    def test_denominator_above_the_maximum_is_rejected(self) -> None:
        self.assert_rejected(make_row(denominator=MAX_INT + 1), "results[0].denominator: ")

    def test_zero_is_still_valid_for_count_and_denominator(self) -> None:
        # Control del límite inferior: el 0 se conserva (no se confunde con «ausente» ni se rechaza).
        self.assert_accepted(make_case_row(count=0))
        self.assert_accepted(make_row(denominator=0))

    def test_negative_count_and_denominator_stay_rejected(self) -> None:
        # Control de que la cota nueva no sustituye al «mayor o igual que 0» existente.
        self.assert_rejected(make_case_row(count=-1), "results[0].count: ")
        self.assert_rejected(make_row(denominator=-1), "results[0].denominator: ")

    def test_very_large_integers_are_rejected(self) -> None:
        # 2**63 (desborda un bigint), 10**20 y 10**400 (ni cabe en un float).
        for big in (2 ** 63, 10 ** 20, 10 ** 400):
            with self.subTest(count=big):
                self.assert_rejected(make_case_row(count=big), "results[0].count: ")
            with self.subTest(denominator=big):
                self.assert_rejected(make_row(denominator=big), "results[0].denominator: ")


class SignedIntegerBoundsTests(BoundsBase):
    """`value`, `numerator`, `ci_low` y `ci_high`: los enteros cumplen `abs(x) <= ROW_MAX_INTEGER`."""

    def test_value_at_the_maximum_is_valid_and_above_is_rejected(self) -> None:
        # En tipo A `tasa` el valor no está acotado por el numerador; solo la cota de enteros se ejercita.
        self.assert_accepted(make_measured_row(value=MAX_INT))
        self.assert_rejected(make_measured_row(value=MAX_INT + 1), "results[0].value: ")

    def test_value_at_minus_maximum_is_valid_and_below_is_rejected(self) -> None:
        # La cota es simétrica: el valor puede ser negativo (un ahorro de tiempo, por ejemplo).
        self.assert_accepted(make_measured_row(value=-MAX_INT))
        self.assert_rejected(make_measured_row(value=-MAX_INT - 1), "results[0].value: ")

    def test_numerator_at_the_maximum_is_valid_and_above_is_rejected(self) -> None:
        # Tipo B con unidad `eur_minor_2`: la regla de la tasa no interviene y el rechazo se debe a la cota.
        self.assert_accepted(make_measured_b_row(numerator=MAX_INT))
        self.assert_rejected(make_measured_b_row(numerator=MAX_INT + 1), "results[0].numerator: ")

    def test_numerator_at_minus_maximum_is_valid_and_below_is_rejected(self) -> None:
        self.assert_accepted(make_measured_b_row(numerator=-MAX_INT))
        self.assert_rejected(make_measured_b_row(numerator=-MAX_INT - 1), "results[0].numerator: ")

    def test_ci_high_at_the_maximum_is_valid_and_above_is_rejected(self) -> None:
        self.assert_accepted(make_measured_row(ci_low=0.1, ci_high=MAX_INT))
        self.assert_rejected(make_measured_row(ci_low=0.1, ci_high=MAX_INT + 1), "results[0].ci_high: ")

    def test_ci_low_at_minus_maximum_is_valid_and_below_is_rejected(self) -> None:
        # Cota simétrica también en el límite inferior del intervalo.
        self.assert_accepted(make_measured_row(ci_low=-MAX_INT, ci_high=0.9))
        self.assert_rejected(make_measured_row(ci_low=-MAX_INT - 1, ci_high=0.9), "results[0].ci_low: ")

    def test_ci_low_above_the_maximum_is_rejected(self) -> None:
        self.assert_rejected(make_measured_row(ci_low=MAX_INT + 1, ci_high=MAX_INT), "results[0].ci_low: ")

    def test_very_large_integers_are_rejected_in_every_signed_field(self) -> None:
        # 2**63, 10**20 y 10**400 (este último ya falla por `_is_number`: se incluye para fijar la misma ruta).
        for big in (2 ** 63, 10 ** 20, 10 ** 400, -(2 ** 63), -(10 ** 20)):
            with self.subTest(value=big):
                self.assert_rejected(make_measured_row(value=big), "results[0].value: ")
            with self.subTest(numerator=big):
                self.assert_rejected(make_measured_b_row(numerator=big), "results[0].numerator: ")
            with self.subTest(ci_high=big):
                self.assert_rejected(make_measured_row(ci_low=0.1, ci_high=big), "results[0].ci_high: ")
            with self.subTest(ci_low=big):
                self.assert_rejected(make_measured_row(ci_low=big, ci_high=0.9), "results[0].ci_low: ")

    def test_finite_floats_have_no_new_bound(self) -> None:
        # La cota es solo de ENTEROS: un float finito, aunque enorme, cabe en `double precision` y sigue siendo
        # válido. Evita que una implementación aplique `abs(x) <= MAX` a todo número.
        self.assert_accepted(make_measured_row(value=1e308))
        self.assert_accepted(make_measured_row(value=2.0 ** 60))
        self.assert_accepted(make_measured_row(value=-(2.0 ** 60)))
        self.assert_accepted(make_measured_b_row(numerator=2.0 ** 60))
        self.assert_accepted(make_measured_row(ci_low=0.1, ci_high=1e308))


# --- L2: orden de los errores con dos defectos a la vez ----------------------------------------------------

class ErrorOrderTests(BoundsBase):
    """Con dos defectos a la vez se informa siempre el mismo primero (fija el orden de las comprobaciones)."""

    def test_row_unknown_key_is_reported_before_missing_key(self) -> None:
        # Fila con una clave desconocida Y una obligatoria ausente (`grp`, que el adaptador tampoco rellena): se
        # informa primero la desconocida. Mata el mutante que invierta «desconocidas, luego ausentes».
        row = make_row()
        row["extra"] = 1
        del row["grp"]
        self.assert_rejected_pair(make_run(), row, "results[0].extra: ")

    def test_run_unknown_key_is_reported_before_missing_key(self) -> None:
        # Lo mismo en `run`: clave desconocida (`milestone`) y `run_id` ausente (obligatoria en el documento).
        run = make_run(milestone=True)
        del run["run_id"]
        self.assert_rejected_pair(run, make_row(), "run.milestone: ")

    def test_interval_is_reported_before_rate(self) -> None:
        # Fila `measured` de unidad `tasa` con numerador 30 > denominador 20 (viola la tasa) Y solo `ci_low`
        # (viola el intervalo): se informa primero el intervalo, en el límite que falta. Mata el mutante que
        # invierta «intervalo, luego tasa».
        self.assert_rejected(make_measured_row(numerator=30, ci_low=0.1), "results[0].ci_high: ")
        self.assert_rejected(make_measured_row(numerator=30, ci_high=0.9), "results[0].ci_low: ")

    def test_rate_alone_is_reported_on_the_numerator(self) -> None:
        # Control: sin el defecto del intervalo, el mismo numerador fuera de rango se informa en `numerator`; así
        # el caso anterior demuestra de verdad que el intervalo gana (y no que la tasa no se compruebe).
        self.assert_rejected(make_measured_row(numerator=30), "results[0].numerator: ")


if __name__ == "__main__":
    unittest.main()
