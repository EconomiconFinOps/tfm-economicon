import asyncio
import json
import time

import pytest

from app.core.chat_expressions import (
    ExpressionRenderer,
    quantities,
    expression_definitions,
)
from app.core.chat_segments import render_response, render_segments
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_resources import (
    retrieval_control,
    validate_search_call,
    continuation_messages,
)


def leaf(value):
    return {"quantity": value}


def difference(current, baseline):
    return {"operation": "difference", "current": current, "baseline": baseline}


def context(question):
    return {
        "messages": [
            {
                "role": "user",
                "content": "UNTRUSTED_CURRENT_CONTEXT\n"
                + json.dumps({"question": question}),
            }
        ]
    }


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Moneda EUR; memoria 40; gasto 100", {"40", "100 EUR"}),
        ("Moneda EUR; versión 3; tipo de cambio 1.1", {"3", "1.1"}),
        ("Presupuesto 1000 EUR. A fecha 15 de agosto", {"1000 EUR", "15"}),
        (
            "Moneda EUR. Coste actual: Compute 600; Storage 250; Logs 150.",
            {"600 EUR", "250 EUR", "150 EUR"},
        ),
        ("10 recursos etiquetables. Nueve cumplen.", {"10 recurso", "9 recurso"}),
        ("Gasto diario 100 EUR; presupuesto 3000 EUR", {"100 EUR/día", "3000 EUR"}),
        (
            "Baseline diario 400 EUR; observado 550 EUR; delta > 100 EUR/día",
            {"400 EUR/día", "550 EUR/día", "100 EUR/día"},
        ),
        (
            "80 eur / 10 pedidos; 90 € / 15 pedido",
            {"80 EUR", "10 pedido", "90 EUR", "15 pedido"},
        ),
        ("73, luego 20. cost-73-item 1.234.567", {"73", "20"}),
        ("10 $ y 20 USD", {"10 $", "20 USD"}),
    ],
)
def test_quantity_binding_preserves_observed_dimensions(question, expected):
    assert set(quantities(question)) == expected


def test_catalog_bound_and_schema_not_exponentially_expanded():
    assert quantities(" ".join(str(i) for i in range(129))) == {}
    catalog = quantities("80 EUR y 10 pedidos")
    schema = expression_definitions(catalog)
    raw = json.dumps(schema)
    assert raw.count("80 EUR") == 1
    assert len(raw) < 10000


def test_semantic_relative_change_of_cost_per_count():
    renderer = ExpressionRenderer(
        quantities("80 EUR y 10 pedidos; 90 EUR y 15 pedidos")
    )

    def rate(a, b):
        return {"operation": "ratio", "numerator": leaf(a), "denominator": leaf(b)}

    expression = {
        "operation": "relative_change",
        "current": rate("90 EUR", "15 pedido"),
        "baseline": rate("80 EUR", "10 pedido"),
    }
    rendered = renderer.render(expression)
    assert "= -25 %" in rendered
    assert renderer.operations == 3


@pytest.mark.parametrize(
    "operator,fields",
    [
        ("ratio", ("numerator", "denominator")),
        ("percentage", ("numerator", "denominator")),
        ("relative_change", ("current", "baseline")),
    ],
)
def test_zero_denominator_is_explicit_undefined_not_fabricated(operator, fields):
    renderer = ExpressionRenderer(quantities("10 EUR; 0 EUR"))
    text = renderer.render(
        {"operation": operator, fields[0]: leaf("10 EUR"), fields[1]: leaf("0 EUR")}
    )
    assert "indefinid" in text and "cero" in text and "= 0" not in text


def test_currency_conversion_cannot_hide_in_rate_dimensions():
    r = ExpressionRenderer(quantities("100 EUR/día y 200 USD/día"))
    text = r.render(
        {
            "operation": "ratio",
            "numerator": leaf("100 EUR/día"),
            "denominator": leaf("200 USD/día"),
        }
    )
    assert "no autorizada" in text and "0.5" not in text


def test_percentage_difference_is_displayed_as_percentage_points():
    result = ExpressionRenderer(quantities("20 % y 5 %")).render(
        difference(leaf("20 %"), leaf("5 %"))
    )
    assert "= 15 puntos porcentuales" in result


@pytest.mark.parametrize(
    "node",
    [
        {"operation": []},
        {"quantity": True},
        {"quantity": "99 EUR"},
        {"quantity": "10 EUR", "unit": "USD"},
        {
            "operation": "sum",
            "left": {"quantity": "10 EUR"},
            "right": {"quantity": "2 pedido"},
        },
        {
            "operation": "compare",
            "left": {"quantity": "10 EUR"},
            "right": {"quantity": "10 EUR"},
            "relation": [],
        },
    ],
)
def test_structural_or_grounding_errors_are_closed(node):
    with pytest.raises(ValueError):
        ExpressionRenderer(quantities("10 EUR; 2 pedidos")).render(node)


@pytest.mark.parametrize("width", [1, 7, 8192])
def test_complete_expression_blocks_stream_exactly_like_public_projection(width):
    catalog = quantities("73 EUR y 20 EUR")
    segments = [
        {"text": "  Ejercicio hipotético 😀: "},
        {"expression": difference(leaf("73 EUR"), leaf("20 EUR"))},
        {"text": " Fin.  "},
    ]
    raw = json.dumps({"answer": segments}, ensure_ascii=True)
    parser = SegmentAnswerJSON([], quantities=catalog)
    streamed = "".join(
        parser.feed(raw[i : i + width]) for i in range(0, len(raw), width)
    )
    assert (
        streamed
        == parser.finish()
        == render_segments(segments, [], expressions=ExpressionRenderer(catalog))
    )
    assert "\nCálculo:" in streamed and "= 53 EUR.\n" in streamed


def test_operations_count_across_answer_and_depth():
    catalog = quantities("73 EUR y 20 EUR")
    segment = {"expression": difference(leaf("73 EUR"), leaf("20 EUR"))}
    value = {
        "answer": [segment] * 13,
        "assumptions": [],
        "limitations": [],
        "next_actions": [],
    }
    with pytest.raises(ValueError, match="operation limit"):
        render_response(value, [], quantities=catalog)
    node = leaf("73 EUR")
    for _ in range(5):
        node = difference(node, leaf("20 EUR"))
    with pytest.raises(ValueError, match="depth"):
        ExpressionRenderer(catalog).render(node)


def test_displayed_root_is_operation_and_short_items_are_single_bounded_prose():
    catalog = quantities("73 EUR y 20 EUR")
    with pytest.raises(ValueError, match="requires an operation"):
        ExpressionRenderer(catalog).render(leaf("20 EUR"))
    from app.agents.schemas import chat_provider_schema
    from app.core.chat_expressions import expression_definitions

    definitions = expression_definitions(catalog)
    assert all(
        item.get("properties", {}).get("operation")
        for item in definitions["RenderedExpression"]["anyOf"]
    )
    schema = chat_provider_schema(quantities=catalog)
    for branch in schema["anyOf"]:
        item = branch["properties"]["limitations"]["items"]
        assert item["minItems"] == item["maxItems"] == 1
        assert item["items"]["properties"] == {
            "text": {"type": "string", "maxLength": 500}
        }
    response = {
        "answer": [{"text": "Respuesta."}],
        "assumptions": [],
        "limitations": [],
        "next_actions": [],
    }
    for bad in (
        [{"text": "a"}, {"text": "b"}],
        [{"expression": difference(leaf("73 EUR"), leaf("20 EUR"))}],
    ):
        with pytest.raises(ValueError, match="short prose"):
            render_response({**response, "limitations": [bad]}, [], quantities=catalog)
    with pytest.raises(ValueError, match="text limit"):
        render_response(
            {**response, "limitations": [[{"text": "a" * 501}]]}, [], quantities=catalog
        )
    assert render_response(
        {**response, "limitations": [[{"text": "a" * 500}]]}, [], quantities=catalog
    )["limitations"] == ["a" * 500]


@pytest.mark.parametrize(
    "alteration",
    [
        {"action": "search", "query": "different"},
        {"action": "none", "query": None},
        {"action": "search", "query": "same", "tenant": "foreign"},
    ],
)
def test_retrieval_control_is_bound_to_canonical_question(alteration):
    with pytest.raises(ValueError):
        validate_search_call(alteration, context("same"))


def test_one_server_retrieval_precedes_exactly_one_generation(monkeypatch):
    from test_chat_auto_jup035 import provider, wire
    from test_chat_gateway_jup035 import ANSWER, _provider

    value = _provider(ANSWER)
    gateway, requests = provider(monkeypatch, [wire({"content": json.dumps(value)})])
    ctx = {
        **context("Explica costes"),
        "tool_protocol": "server-documentation-v4",
        "financial_metrics_allowed": False,
        "authorized_evidence": [],
    }
    calls = []

    async def retrieve(control):
        assert requests == []
        calls.append(control)
        return {
            "tool_call_id": validate_search_call(control, ctx)[0],
            "content": '{"evidence":[],"omissions":[]}',
            "variable_tokens": 0,
        }

    async def exercise():
        return [
            event
            async for event in gateway(ctx, time.time() + 60, tool_result=retrieve)
        ]

    events = asyncio.run(exercise())
    assert len(calls) == len(requests) == 1
    assert events[0]["type"] == "tool_call"
    assert any(event["type"] == "candidate" for event in events), events
    assert requests[0]["response_format"]["json_schema"]["name"] == "FinOpsResponse"
    assert "tools" not in requests[0]
