"""Pruebas de las guardas puras de entrada/salida del agente (app.agents.guardrails).

Son la frontera de seguridad del agente: validan tenant, origen y estado, redactan
metadatos sensibles antes de llegar al modelo y aceptan la respuesta del proveedor
solo si encaja en el esquema sin copiar su contenido a las excepciones. Los limites
(50, 100, 500, 4000, profundidad 4) se fijan aqui como LITERALES a proposito: si se
importaran las constantes del producto, un cambio accidental de una de ellas
movería también la expectativa y nadie lo notaría.
"""

import json
import math
import traceback
from datetime import date
from decimal import Decimal

import pytest

from app.agents.guardrails import (
    AgentGuardrailError,
    AgentResponseError,
    parse_and_validate_response,
    prepare_agent_input,
    sanitize_metadata,
    source_is_supported,
)
from app.agents.service import AgentRuntime
from app.core.config import Settings

SECRET = "SECRETO-SINTETICO-0001"
MARKER = "SECRETO-SINTETICO-RESPUESTA"


def _payload(**overrides) -> dict:
    payload = {"tenant_id": "tenant-core", "source": "azure", "metadata": {}}
    payload.update(overrides)
    return payload


def _without(key: str) -> dict:
    payload = _payload()
    del payload[key]
    return payload


def _meta(metadata: dict) -> dict:
    return json.loads(sanitize_metadata(metadata))


def _nested(levels: int, leaf):
    # `levels` claves anidadas: el valor hoja queda a profundidad `levels`.
    value = leaf
    for _ in range(levels):
        value = {"k": value}
    return value


# --------------------------------------------------------------- entrada


@pytest.mark.parametrize("payload", [None, [], "texto"])
def test_non_object_job_payload_is_rejected(payload):
    with pytest.raises(AgentGuardrailError, match="job payload must be an object"):
        prepare_agent_input(payload, "running")


@pytest.mark.parametrize(
    "payload",
    [
        _without("tenant_id"),
        _payload(tenant_id=None),
        _payload(tenant_id=5),
        _payload(tenant_id=""),
        _payload(tenant_id="   "),
    ],
)
def test_tenant_must_be_a_non_blank_string(payload):
    with pytest.raises(AgentGuardrailError, match="tenant context is required"):
        prepare_agent_input(payload, "running")


@pytest.mark.parametrize(
    "status", ["", None, 5, "run ning", "a;b", "a/b", "running\n", "s" * 65]
)
def test_unsafe_status_is_rejected(status):
    # "running\n" comprueba que el patron se aplica al texto completo (fullmatch)
    # y no solo a un prefijo: un salto de linea final no puede colarse en el prompt.
    with pytest.raises(AgentGuardrailError, match="unsupported characters"):
        prepare_agent_input(_payload(), status)


@pytest.mark.parametrize("status", ["S" * 64, "Run.ning_1-X"])
def test_safe_status_is_returned_unchanged(status):
    # Con mayusculas: el estado se valida pero no se normaliza (a diferencia del origen).
    assert prepare_agent_input(_payload(), status).status == status


@pytest.mark.parametrize(
    "payload",
    [_without("source"), _payload(source=None), _payload(source=""),
     _payload(source="   "), _payload(source=5)],
)
def test_source_must_be_a_non_empty_string(payload):
    with pytest.raises(AgentGuardrailError, match="non-empty string"):
        prepare_agent_input(payload, "running")


@pytest.mark.parametrize(
    "source", ["a b", "../x", "a/b", "-x", ".x", "a" * 65, "<script>"]
)
def test_unsafe_source_identifier_is_rejected(source):
    with pytest.raises(AgentGuardrailError, match="safe provider identifier"):
        prepare_agent_input(_payload(source=source), "running")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" Azure-Cost ", "azure-cost"),  # strip + minusculas
        ("A" * 64, "a" * 64),  # el limite de 64 caracteres es valido
        ("0.x_y-z", "0.x_y-z"),  # digito inicial y separadores permitidos
    ],
)
def test_source_is_normalized_to_lowercase_without_padding(raw, expected):
    assert prepare_agent_input(_payload(source=raw), "running").source == expected


@pytest.mark.parametrize("metadata", [[], "texto", None])
def test_metadata_must_be_an_object_when_present(metadata):
    # `None` explicito cuenta como presente (no se sustituye por {}).
    with pytest.raises(AgentGuardrailError, match="metadata must be an object"):
        prepare_agent_input(_payload(metadata=metadata), "running")


def test_absent_metadata_defaults_to_an_empty_object():
    assert prepare_agent_input(_without("metadata"), "running").metadata_json == "{}"


@pytest.mark.parametrize(
    ("source", "supported"),
    [
        ("azure", True),
        ("azure-cost", True),
        ("azure-cost-api", True),
        ("azure-cost-management", True),
        ("azure-cost-simulator", True),
        ("aws-cur", False),
        ("azure-other", False),
        ("Azure", False),  # espera el origen ya normalizado
        ("", False),
    ],
)
def test_only_the_azure_allowlist_is_supported(source, supported):
    assert source_is_supported(source) is supported


class _CountingProvider:
    def __init__(self):
        self.calls = 0

    def invoke(self, prompt, *, response_format):
        self.calls += 1
        return "{}"


def test_invalid_input_is_rejected_before_the_provider_is_called():
    provider = _CountingProvider()
    runtime = AgentRuntime(Settings(llm_provider="mock"), provider=provider)

    with pytest.raises(AgentGuardrailError, match="metadata must be an object"):
        runtime.invoke(_payload(metadata=[SECRET]), status="running")

    assert provider.calls == 0


# ------------------------------------------------------ saneado de metadatos


@pytest.mark.parametrize(
    "key",
    [
        "authorization", "Authorization", "API_KEY", "api-key", "apikey",
        "Password", "secret", "Client-Secret", "token", "credential",
        "x_auth_token", "db_password",
    ],
)
def test_sensitive_keys_are_redacted_at_any_depth_and_case(key):
    metadata = {
        "ResourceGroup": "rg-public",
        key: SECRET,
        "items": [{key: SECRET, "CostCenter": "CC-1"}],
    }

    rendered = sanitize_metadata(metadata)

    assert SECRET not in rendered
    parsed = json.loads(rendered)
    assert parsed[key] == "[REDACTED]"
    assert parsed["items"][0] == {key: "[REDACTED]", "CostCenter": "CC-1"}
    assert parsed["ResourceGroup"] == "rg-public"  # las claves publicas se conservan


def test_a_sensitive_key_hides_the_whole_structured_value():
    rendered = sanitize_metadata({"credentials": {"user": "u", "pw": [SECRET]}})

    assert SECRET not in rendered
    assert json.loads(rendered) == {"credentials": "[REDACTED]"}


def test_non_string_keys_are_stringified_before_the_sensitivity_check():
    parsed = _meta({1: "uno", ("token", 2): SECRET})

    assert parsed == {"(\'token\', 2)": "[REDACTED]", "1": "uno"}


def test_depth_boundary_keeps_values_below_four_and_truncates_at_four():
    assert _meta(_nested(3, "hoja")) == _nested(3, "hoja")
    assert _meta(_nested(4, "hoja")) == _nested(4, "[TRUNCATED]")
    # Las listas consumen un nivel igual que los dicts.
    assert _meta({"a": [[["hoja"]]]}) == {"a": [[["[TRUNCATED]"]]]}


def test_dicts_keep_the_first_fifty_keys_in_sorted_order():
    # Insertadas al reves: el recorte se hace tras ordenar por clave, no por llegada.
    metadata = {f"k{i:02d}": i for i in reversed(range(51))}

    parsed = _meta(metadata)

    assert list(parsed) == [f"k{i:02d}" for i in range(50)]


def test_lists_and_tuples_keep_the_first_fifty_items():
    parsed = _meta({"lista": list(range(51)), "tupla": tuple(range(51))})

    assert parsed["lista"] == list(range(50))
    assert parsed["tupla"] == list(range(50))


def test_strings_and_keys_are_cut_to_their_limits():
    parsed = _meta({"k" * 100: "x" * 500, "m" * 101: "y" * 501})

    assert parsed == {"k" * 100: "x" * 500, "m" * 100: "y" * 500}


def test_nested_strings_are_also_cut_to_five_hundred_characters():
    # El recorte debe aplicarse a cualquier profundidad (listas y dicts anidados),
    # no solo a los valores del nivel superior.
    parsed = _meta({"lista": ["a" * 501], "dict": {"interno": "b" * 501}})

    assert parsed == {"lista": ["a" * 500], "dict": {"interno": "b" * 500}}


def test_scalars_survive_and_non_finite_floats_are_replaced_everywhere():
    metadata = {
        "bool": True, "none": None, "int": 3, "float": 1.5,
        "nan": math.nan, "ninf": -math.inf, "inf": math.inf,
        "lista": [math.nan],
    }

    assert _meta(metadata) == {
        "bool": True, "none": None, "int": 3, "float": 1.5,
        "nan": "[NON_FINITE_NUMBER]", "ninf": "[NON_FINITE_NUMBER]",
        "inf": "[NON_FINITE_NUMBER]", "lista": ["[NON_FINITE_NUMBER]"],
    }


def test_unknown_types_are_stringified_and_capped():
    parsed = _meta(
        {
            "dec": Decimal("1.50"), "fecha": date(2024, 1, 2), "set": {7},
            "bytes": b"ab", "largo": Decimal("1." + "0" * 600),
        }
    )

    assert parsed["dec"] == "1.50"
    assert parsed["fecha"] == "2024-01-02"
    assert parsed["set"] == "{7}"
    assert parsed["bytes"] == "b'ab'"
    assert parsed["largo"] == str(Decimal("1." + "0" * 600))[:500]


def _metadata_rendering_exactly(length: int) -> dict:
    # Siete cadenas de 500 mas una final de relleno para clavar el tamaño renderizado.
    metadata = {f"k{i}": "x" * 500 for i in range(7)}
    metadata["z"] = ""
    base = len(json.dumps(metadata, sort_keys=True, separators=(",", ":")))
    filler = length - base
    assert 0 <= filler <= 500
    metadata["z"] = "x" * filler
    return metadata


def test_rendered_metadata_of_exactly_4000_characters_is_not_truncated():
    metadata = _metadata_rendering_exactly(4000)

    rendered = sanitize_metadata(metadata)

    assert len(rendered) == 4000
    assert json.loads(rendered) == metadata


def test_oversized_metadata_is_replaced_by_a_preview_of_3900_characters():
    metadata = _metadata_rendering_exactly(4001)
    metadata["k0"] = "ñ" + "x" * 499  # el aviso tambien conserva no ASCII
    full = json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert len(full) == 4001

    rendered = sanitize_metadata(metadata)

    assert rendered.startswith('{"notice":"metadata_truncated","preview":"')
    assert "\\u" not in rendered
    parsed = json.loads(rendered)  # sigue siendo JSON valido
    assert parsed == {"notice": "metadata_truncated", "preview": full[:3900]}
    assert len(parsed["preview"]) == 3900


# ---------------------------------------------------- respuesta del proveedor


@pytest.mark.parametrize("raw", [None, "", "   ", "\n\t", b"{}", {}, 5])
def test_empty_or_non_text_provider_response_is_rejected(raw):
    # bytes/dict/int llegan a la misma rama: la guarda exige `str` antes de strip().
    with pytest.raises(AgentResponseError, match="empty response"):
        parse_and_validate_response(raw)


@pytest.mark.parametrize(
    "raw",
    [
        f'{{"answer": "{MARKER}"}}',  # JSON valido que no encaja en el esquema
        f'{{"answer": "{MARKER}',  # JSON truncado
        '{"answer": "' + MARKER + '\x00"}',  # caracter de control
        '{"answer": "' + MARKER + '\\ud800"}',  # surrogate suelto
        f'\ufeff{{"x": "{MARKER}"}}',  # BOM inicial
    ],
)
def test_malformed_provider_output_never_leaks_its_content(raw):
    # La rama `except ValueError` ("not valid JSON") es codigo inalcanzable: pydantic v2
    # envuelve incluso el JSON invalido en ValidationError (subclase de ValueError, ya
    # capturada antes). Todas estas entradas dan el mensaje de esquema; no se fuerza por mock.
    with pytest.raises(AgentResponseError, match="does not match the FinOps response") as info:
        parse_and_validate_response(raw)

    error = info.value
    assert MARKER not in str(error)
    assert error.__cause__ is None
    assert error.__context__ is None
    rendered = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )
    assert MARKER not in rendered


def _answer_without_evidence(answer: str) -> str:
    # Respuesta minima valida sin evidencias ni metricas: con status no accionable,
    # el esquema la admite y solo la guarda NUMERIC_CLAIM puede rechazarla.
    return json.dumps(
        {
            "schema_version": "1.0", "status": "insufficient_data", "answer": answer,
            "scope": {"cloud": "azure", "data_environment": "simulated",
                      "subscription_ids": [], "period": None},
            "evidence": [], "metrics": [], "recommendations": [],
            "assumptions": [], "limitations": [], "next_actions": [],
        }
    )


@pytest.mark.parametrize(
    "answer",
    ["12,5 EUR", "10 %", "3 USD", "-4 euros", "4 euro", "5 eur", "1.5€", "gasto de 7 EUR."],
)
def test_numeric_claim_without_evidence_is_rejected_for_every_unit_form(answer):
    # Cifra + unidad (EUR/USD/euro(s)/euro-simbolo/%), en mayusculas o minusculas,
    # con o sin espacio: una cifra monetaria sin evidencia estructurada es inventada.
    with pytest.raises(AgentResponseError, match="numeric claim"):
        parse_and_validate_response(_answer_without_evidence(answer))


@pytest.mark.parametrize(
    "answer", ["Q3", "EUR2", "la factura de EUR", "100 unidades", "3 USDT"]
)
def test_figures_without_unit_or_units_without_figure_are_accepted(answer):
    # Contrapeso: sin cifra+unidad no hay afirmacion numerica; evita que una guarda
    # que rechace todo pase los casos de rechazo. "3 USDT" comprueba el limite de palabra.
    response = parse_and_validate_response(_answer_without_evidence(answer))

    assert response.answer == answer
