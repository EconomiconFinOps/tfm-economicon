"""Cada campo de identidad del modelo, por separado, en `evaluation.config_changes` (hueco de JUP-133)."""
from __future__ import annotations

import unittest

import test_evaluation_views as views
from test_evaluation_views import ViewsTestCase, pair_scenarios

FULL = {"generation_model_id": "m/a", "generation_provider": "p1", "generation_quantization": "fp8",
        "gateway_config_sha256": "aa" * 32}
NOT_REGISTERED = "identidad del modelo no registrada en una de las dos"

SCENARIOS = [
    ("id-igual", FULL, dict(FULL), []),
    ("id-modelo", FULL, {**FULL, "generation_model_id": "m/b"}, ["identificador de modelo"]),
    ("id-proveedor", FULL, {**FULL, "generation_provider": "p2"}, ["proveedor del modelo"]),
    ("id-cuantizacion", FULL, {**FULL, "generation_quantization": "fp16"}, ["cuantizacion"]),
    ("id-huella", FULL, {**FULL, "gateway_config_sha256": "bb" * 32}, ["configuracion del gateway"]),
    ("id-proveedor-nulo", FULL, {**FULL, "generation_provider": None}, ["proveedor del modelo"]),
    ("id-huella-nula", FULL, {**FULL, "gateway_config_sha256": None}, ["configuracion del gateway"]),
    ("id-ninguna", FULL, {}, [NOT_REGISTERED]),
    ("id-solo-huella", {"gateway_config_sha256": "aa" * 32}, {}, [NOT_REGISTERED]),
    ("id-solo-huella-inversa", {}, {"gateway_config_sha256": "aa" * 32}, [NOT_REGISTERED]),
    ("id-ambas-sin", {}, {}, []),
]


class IdentityLabelsOneByOneTests(ViewsTestCase):
    def test_each_identity_field_produces_only_its_own_label(self) -> None:
        items, expected = pair_scenarios(SCENARIOS)
        views.load(items)
        actual = {(row[2], row[4]) for row in views.change_rows()}
        wanted = {(row[2], row[4]) for row in expected}
        self.assertEqual(actual, wanted)
        self.assertEqual(len(views.change_rows()), len(expected))


if __name__ == "__main__":
    unittest.main()
