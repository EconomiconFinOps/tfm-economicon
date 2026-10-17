"""Huecos de mutación de la validación común de filas `rows-v1` (JUP-121, tarea 2.6, remediación de mutación).

Mutantes supervivientes en `_status_rules` de `tools/evaluation-dashboard.py`: la tupla de campos prohibidos del
estado `not_measured`, `("count", "value", "numerator", "ci_low", "ci_high")`, podía perder `ci_low` o `ci_high`
(mutaciones `XXci_low` / `XXci_high`) sin que ninguna prueba lo notara, porque ninguna comprobaba que una fila
`not_measured` NO admite intervalo (sí se comprobaban `count`, `value` y `numerator`).

Este fichero NO modifica pruebas ya commiteadas: añade casos nuevos. Cada caso se ejecuta con `validate_rows` y con
`adapt_rows_v1` (la validación común es la misma, pero el adaptador la invoca tras rellenar lo opcional y las dos
vías deben informar la misma ruta). Las filas de ejemplo se construyen aquí a mano, sin depender de los informes
reales, para que cambie solo el dato que se quiere probar.

Además se fijan las reglas vecinas del intervalo que comparten la ruta de error con el hueco: un intervalo lleva
los dos límites o ninguno, en un estado de caso (`pass`) y en `measured`; y, por decisión documentada, un `pass`
con los dos límites NO se prohíbe.

La ruta de la herramienta se puede sustituir con la variable de entorno `EVALUATION_DASHBOARD_TOOL` para apuntar
estas pruebas a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_rows_contract_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

# Claves literales del contrato (no se leen de la herramienta para poder comparar contra ella).
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
)
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)


def make_run() -> dict:
    # Ejecución mínima válida: solo run_id y source son obligatorios con valor; el resto, None o False.
    run = dict.fromkeys(RUN_KEYS)
    run.update({"run_id": "run-gaps", "source": "gaps-test", "synthetic": False})
    return run


def make_row(**changes) -> dict:
    # Fila `not_measured` válida: tipo A, unidad `tasa`, solo denominador (regla 5: lo no medido conserva el
    # denominador y no lleva ni valor, ni numerador, ni recuento, ni intervalo).
    row = dict.fromkeys(RESULT_KEYS)
    row.update({
        "measure_type": "A", "grp": "grp-a", "metric_id": "M-1", "behavior": "behavior-a",
        "status": "not_measured", "unit": "tasa", "denominator": 20, "judgment": "automatic", "selected": False,
    })
    row.update(changes)
    return row


def make_case_row(**changes) -> dict:
    # Fila de estado de caso `pass` válida: lleva recuento y no valor ni numerador (regla 2).
    return make_row(status="pass", count=3, **changes)


def make_measured_row(**changes) -> dict:
    # Fila `measured` válida: lleva valor y no recuento (regla 1).
    return make_row(status="measured", value=0.5, numerator=10, **changes)


def document(row: dict) -> dict:
    # Documento `rows-v1` equivalente a (make_run(), [row]); el adaptador rellena lo opcional que falte.
    return {"contract_version": 1, "run": make_run(), "results": [row]}


class RowsContractGapsBase(unittest.TestCase):
    def assert_rejected(self, row: dict, prefix: str) -> None:
        """La fila se rechaza con `AdapterError` cuyo mensaje EMPIEZA por `prefix`, por las dos vías."""
        # Copias profundas: ninguna vía debe poder alterar la entrada de la otra (y se comprueba que no se muta).
        for name, call in (
            ("validate_rows", lambda: tool.validate_rows(make_run(), [copy.deepcopy(row)])),
            ("adapt_rows_v1", lambda: tool.adapt_rows_v1(document(copy.deepcopy(row)))),
        ):
            with self.subTest(via=name):
                with self.assertRaises(tool.AdapterError) as caught:
                    call()
                self.assertTrue(
                    str(caught.exception).startswith(prefix),
                    f"se esperaba el prefijo {prefix!r} y llegó {str(caught.exception)!r}",
                )

    def assert_accepted(self, row: dict) -> None:
        """La fila es válida por las dos vías (sin excepción)."""
        with self.subTest(via="validate_rows"):
            tool.validate_rows(make_run(), [copy.deepcopy(row)])
        with self.subTest(via="adapt_rows_v1"):
            _, results = tool.adapt_rows_v1(document(copy.deepcopy(row)))
            self.assertEqual(results, [row])


class NotMeasuredForbiddenFieldsTests(RowsContractGapsBase):
    """Una fila `not_measured` no admite ningún campo de medición ni de intervalo (tupla de `_status_rules`)."""

    def test_not_measured_with_only_denominator_is_valid(self) -> None:
        # Control: el denominador SÍ se conserva en lo no medido (regla 5); sin él las rechazadas de abajo
        # podrían fallar por otro motivo que el campo prohibido.
        self.assert_accepted(make_row())

    def test_not_measured_rejects_ci_low_alone(self) -> None:
        # Mata `XXci_low`: con el nombre corrompido, `ci_low` dejaría de ser un campo prohibido y, como el
        # intervalo incompleto lo pillaría solo en `ci_high`, la ruta ya no sería `ci_low`.
        self.assert_rejected(make_row(ci_low=0.1), "results[0].ci_low: ")

    def test_not_measured_rejects_ci_high_alone(self) -> None:
        # Mata `XXci_high`: sin ser campo prohibido, el error (si lo hubiera) saldría del intervalo incompleto
        # y en `ci_low`, no en `ci_high`.
        self.assert_rejected(make_row(ci_high=0.5), "results[0].ci_high: ")

    def test_not_measured_with_both_limits_reports_ci_low_first(self) -> None:
        # Con los dos límites, el primero en el orden de RESULT_KEYS es `ci_low`. Fija además que un intervalo
        # completo tampoco rescata a un `not_measured`.
        self.assert_rejected(make_row(ci_low=0.1, ci_high=0.5), "results[0].ci_low: ")

    def test_not_measured_with_zero_limits_is_rejected(self) -> None:
        # Falsos valores: 0.0 no es None, y publicar un intervalo de ceros como «no medido» sería un cero.
        self.assert_rejected(make_row(ci_low=0.0), "results[0].ci_low: ")
        self.assert_rejected(make_row(ci_high=0.0), "results[0].ci_high: ")

    def test_not_measured_still_rejects_count_value_numerator(self) -> None:
        # Controles de la misma tupla (ya cubiertos en otro fichero): se repiten para que, si alguien reordena
        # o recorta la tupla, este fichero lo siga notando por sí solo.
        self.assert_rejected(make_row(count=1), "results[0].count: ")
        self.assert_rejected(make_row(value=0.5), "results[0].value: ")
        self.assert_rejected(make_row(numerator=5), "results[0].numerator: ")


class IntervalNeedsBothLimitsTests(RowsContractGapsBase):
    """El intervalo lleva los dos límites o ninguno; el error se informa en el límite que falta."""

    def test_case_status_with_only_ci_low_reports_ci_high(self) -> None:
        self.assert_rejected(make_case_row(ci_low=0.1), "results[0].ci_high: ")

    def test_case_status_with_only_ci_high_reports_ci_low(self) -> None:
        self.assert_rejected(make_case_row(ci_high=0.5), "results[0].ci_low: ")

    def test_case_status_with_both_limits_is_valid(self) -> None:
        # Decisión documentada: un estado de caso con intervalo completo no se prohíbe (solo `not_measured` lo
        # prohíbe). Fija la decisión para que una prohibición futura sea deliberada y no accidental.
        self.assert_accepted(make_case_row(ci_low=0.1, ci_high=0.5))

    def test_case_status_without_interval_is_valid(self) -> None:
        # Control: el `pass` base (sin intervalo) es válido, así que los rechazos de arriba se deben al límite.
        self.assert_accepted(make_case_row())

    def test_measured_with_only_ci_low_reports_ci_high(self) -> None:
        self.assert_rejected(make_measured_row(ci_low=0.1), "results[0].ci_high: ")

    def test_measured_with_only_ci_high_reports_ci_low(self) -> None:
        self.assert_rejected(make_measured_row(ci_high=0.9), "results[0].ci_low: ")

    def test_measured_with_both_limits_is_valid(self) -> None:
        # Control: `measured` con intervalo completo es el caso normal.
        self.assert_accepted(make_measured_row(ci_low=0.3, ci_high=0.7))


if __name__ == "__main__":
    unittest.main()
