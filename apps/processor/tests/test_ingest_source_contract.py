"""JUP-113 (RF-086-004): contrato compartido del campo `source` entre backend y processor.

Recorre con `normalize_source` la MISMA tabla de casos que usa la admision del backend
(`apps/backend/tests/test_ingest_source_admission.py`). Describe comportamiento ya
existente del processor (por eso pasa desde el principio, no es Red): fija el
veredicto de referencia para que el backend no pueda derivar de el sin que alguna de
las dos pruebas falle.
"""

import json
from pathlib import Path

import pytest

from app.agents.guardrails import AgentGuardrailError, normalize_source

# Raiz del repo calculada desde este archivo (apps/processor/tests/<archivo>).
CASES_PATH = Path(__file__).resolve().parents[3] / "docs" / "api" / "ingest-source-contract-cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES["accepted"]])
def test_accepted_sources_normalize_to_the_documented_value(case):
    # El valor admitido se normaliza a la forma exacta documentada en la tabla.
    assert normalize_source(case["source"]) == case["normalized"]


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES["rejected"]])
def test_rejected_sources_raise_a_guardrail_error(case):
    # Cada origen rechazado debe lanzar el error de guarda (no otra excepcion ni pasar).
    with pytest.raises(AgentGuardrailError):
        normalize_source(case["source"])


def test_contract_table_is_not_empty_and_has_boundaries():
    # Guardian: una tabla vaciada o sin los limites de 64/65 haria pasar lo anterior en vacio.
    assert CASES["accepted"] and CASES["rejected"]
    assert any(len(c["source"]) == 64 for c in CASES["accepted"])
    assert any(len(c["source"]) == 65 for c in CASES["rejected"])
