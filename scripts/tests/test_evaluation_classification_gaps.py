"""Huecos de la clasificación de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.7, remediación de dos LOW del QA).

Complementa `test_evaluation_classification.py` (no se modifica) con dos comportamientos que ninguna prueba
fijaba y que un mutante podía cambiar sin que nada fallase:

* LOW-1: `comparability_key` es pública y NO valida `run`, así que puede recibir texto no ASCII. El JSON canónico
  debe serializarse con `ensure_ascii=True` (escapes `\\uXXXX`); con `False` la clave de un mismo texto cambiaría
  respecto de la ya guardada.
* LOW-2: `unclassified_metrics` solo carga el catálogo real cuando el argumento es EXACTAMENTE `None`. Un
  diccionario vacío (falso pero no `None`) no debe interpretarse como «no se pasó catálogo»: no tiene la clave
  `metrics`, así que debe lanzar `KeyError`, mientras que `{"metrics": []}` es un catálogo vacío válido.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_classification_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)


def minimal_run(**overrides):
    """Ejecución mínima con los 9 campos de la clave (valores válidos); `comparability_key` no valida el resto."""
    run = {
        "source": "JUP-070",
        "suite_version": "1.0.0",
        "suite_sha256": "a" * 64,
        "corpus_sha256": "b" * 64,
        "embedding_provider": "openai",
        "embedding_alias": "text-embedding",
        "retrieval": {"k": 5},
        "generation_model": "modelo",
        "prompt_sha256": "c" * 64,
        "generation_model_id": None, "generation_provider": None,
        "generation_quantization": None, "gateway_config_sha256": None,
    }
    run.update(overrides)
    return run


def expected_key(run, reasons=(), ensure_ascii=True):
    """Digest esperado calculado por la prueba, con el orden de campos del contrato y la opción indicada."""
    payload = [
        run["source"], run["suite_version"], run["suite_sha256"], run["corpus_sha256"],
        run["embedding_provider"], run["embedding_alias"], run["retrieval"], run["generation_model"],
        run["prompt_sha256"], list(reasons),
    ]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=ensure_ascii)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ComparabilityKeyNonAsciiTest(unittest.TestCase):
    """LOW-1: la clave de un texto no ASCII usa el JSON con escapes (`ensure_ascii=True`)."""

    def test_non_ascii_model_matches_escaped_json_digest(self):
        # Se calcula el digest esperado con `é` escapado por `json`: así la prueba fija el formato exacto
        # y no solo que haya «algún» hash.
        run = minimal_run(generation_model="modélo")
        self.assertEqual(tool.comparability_key(run, ()), expected_key(run, ensure_ascii=True))

    def test_non_ascii_key_differs_from_unescaped_serialisation(self):
        # Con `ensure_ascii=False` el texto UTF-8 sería otro y el digest también: si coincidieran, la prueba no
        # distinguiría el mutante.
        run = minimal_run(generation_model="modélo")
        unescaped = expected_key(run, ensure_ascii=False)
        self.assertNotEqual(expected_key(run, ensure_ascii=True), unescaped)
        self.assertNotEqual(tool.comparability_key(run, ()), unescaped)

    def test_distinct_non_ascii_values_give_distinct_keys(self):
        # `é` y `è` son caracteres distintos: sus claves deben diferir (y coincidir con el digest esperado).
        run_acute = minimal_run(generation_model="é")
        run_grave = minimal_run(generation_model="è")
        key_acute = tool.comparability_key(run_acute, ())
        key_grave = tool.comparability_key(run_grave, ())
        self.assertNotEqual(key_acute, key_grave)
        self.assertEqual(key_acute, expected_key(run_acute))
        self.assertEqual(key_grave, expected_key(run_grave))

    def test_non_ascii_key_is_64_lowercase_hex(self):
        # La clave sigue siendo una columna de tamaño fijo: 64 hexadecimales en minúscula, también con no ASCII.
        key = tool.comparability_key(minimal_run(generation_model="modélo"), ())
        self.assertIsInstance(key, str)
        self.assertRegex(key, r"\A[0-9a-f]{64}\Z")


class UnclassifiedMetricsEmptyCatalogueTest(unittest.TestCase):
    """LOW-2: `None` carga el catálogo real; cualquier otro valor se usa tal cual, aunque sea falso."""

    def test_catalogue_with_empty_metrics_list_returns_empty_list(self):
        # Un catálogo sin métricas no tiene nada sin clasificar: `[]`, sin cargar el catálogo real.
        self.assertEqual(tool.unclassified_metrics({"metrics": []}), [])

    def test_empty_dict_is_not_none_and_raises_key_error(self):
        # `{}` es falso pero NO `None`: no se carga el catálogo real; se intenta leer `metrics` y falta la clave.
        # Con `if not catalogue` se cargaría el catálogo real y devolvería `[]` en lugar de lanzar.
        with self.assertRaises(KeyError):
            tool.unclassified_metrics({})


if __name__ == "__main__":
    unittest.main()
