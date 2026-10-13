"""Authenticated rules, arithmetic boundaries and common stream projection."""

import copy
import asyncio
import json
import time
from pathlib import Path

import pytest

from app.core.chat_expressions import ExpressionRenderer, context_quantities
from app.core.chat_segments import render_response, render_segments
from app.clients.chat_stream_parser import SegmentAnswerJSON

FORMULA = "Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100"
BANDS = (
    "- verde: menor o igual a 5 %; "
    "- amarillo: mayor que 5 % y menor o igual a 10 %; "
    "- rojo: mayor que 10 %."
)


def source(index, text):
    return {
        "id": f"rules:chunk:{index}",
        "kind": "corpus",
        "title": "Reglas internas",
        "source": "business-rules.economicon-mvp",
        "content": text,
    }


def context(question="Importes: 700 EUR; 200 EUR; 100 EUR; 50 EUR."):
    sources = [source(3, "Coste No Asignado KPI: " + FORMULA), source(4, BANDS)]
    return {
        "authorized_evidence": sources,
        "messages": [
            {
                "role": "user",
                "content": "UNTRUSTED_CURRENT_CONTEXT\n"
                + json.dumps({"question": question}),
            },
            {
                "role": "user",
                "content": "UNTRUSTED_RETRIEVAL_CONTEXT\n"
                + json.dumps({"evidence": sources}),
            },
        ],
    }


def percentage(numerator="100 EUR", denominator=None):
    return {
        "operation": "percentage",
        "numerator": {"quantity": numerator},
        "denominator": denominator
        or {
            "operation": "sum",
            "left": {"quantity": "700 EUR"},
            "right": {
                "operation": "sum",
                "left": {"quantity": "200 EUR"},
                "right": {"quantity": "100 EUR"},
            },
        },
    }


def classification(expression=None):
    return {
        "classification": {
            "rule_id": "unallocated-cost-v1",
            "expression": expression or percentage(),
        }
    }


def rendered(value, segments):
    from app.core.chat_rules import context_rules

    return render_segments(
        segments,
        [],
        expressions=ExpressionRenderer(
            context_quantities(value), rules=context_rules(value)
        ),
    )


@pytest.mark.parametrize(
    "amount,color,interval",
    [
        ("0", "verde", "<= 5 %"),
        ("50", "verde", "<= 5 %"),
        ("50.000001", "amarillo", "> 5 % y <= 10 %"),
        ("100", "amarillo", "> 5 % y <= 10 %"),
        ("100.000001", "rojo", "> 10 %"),
        ("101", "rojo", "> 10 %"),
    ],
)
def test_server_applies_exact_inclusive_boundaries_before_display_rounding(
    amount, color, interval
):
    value = context(f"Importes: {amount} EUR; 1000 EUR.")
    result = rendered(
        value, [classification(percentage(amount + " EUR", {"quantity": "1000 EUR"}))]
    )
    assert color in result and interval in result


def test_compound_total_is_evaluated_without_excluded_cost():
    text = rendered(context(), [classification()])
    assert "(700 EUR + (200 EUR + 100 EUR))" in text
    assert "= 10 %" in text and "amarillo" in text and "50 EUR" not in text
    assert "Total elegible hipotético: 1000 EUR." in text


@pytest.mark.parametrize(
    "change",
    ["bands", "formula", "title_only", "foreign", "omitted", "other_document", "user"],
)
def test_rule_requires_exact_effective_formula_and_bands_from_same_authorized_document(
    change,
):
    from app.core.chat_rules import context_rules

    value = context()
    sources = copy.deepcopy(value["authorized_evidence"])
    if change == "bands":
        sources[1]["content"] = BANDS.replace("igual a 10", "igual a 11")
    elif change == "formula":
        sources[0]["content"] = FORMULA.replace("Total Eligible Cost", "Monthly Cost")
    elif change == "title_only":
        sources[1]["content"] = "Unallocated Cost, title and no bands."
    elif change == "other_document":
        sources[1]["id"] = "other:chunk:4"
    elif change == "user":
        sources[1]["kind"] = "user_input"
    elif change == "omitted":
        value["authorized_evidence"] = []
    elif change == "foreign":
        sources[1]["id"] = "foreign:chunk:4"
    if change not in ("omitted", "foreign"):
        value["authorized_evidence"] = sources
    value["messages"][-1]["content"] = "UNTRUSTED_RETRIEVAL_CONTEXT\n" + json.dumps(
        {"evidence": sources}
    )
    if change in ("foreign", "omitted", "user"):
        with pytest.raises(ValueError):
            context_rules(value)
    else:
        assert context_rules(value) == {}


def test_versioned_rule_matches_chunk_whitespace_but_not_changed_thresholds():
    from app.core.chat_rules import context_rules, RULE_CATALOG_SHA256

    value = context()
    value["authorized_evidence"][1]["content"] = BANDS.replace("; ", ";\n")
    value["messages"][-1]["content"] = "UNTRUSTED_RETRIEVAL_CONTEXT\n" + json.dumps(
        {"evidence": value["authorized_evidence"]}
    )
    assert set(context_rules(value)) == {"unallocated-cost-v1"}
    assert len(RULE_CATALOG_SHA256) == 64


def test_zero_denominator_is_undefined_without_a_color():
    text = rendered(
        context("100 EUR; 0 EUR."),
        [classification(percentage("100 EUR", {"quantity": "0 EUR"}))],
    )
    assert "indefinid" in text and "cero" in text
    assert not any(color in text for color in ("verde", "amarillo", "rojo"))


@pytest.mark.parametrize(
    "bad",
    [
        {"rule_id": "foreign", "expression": percentage()},
        {"rule_id": "unallocated-cost-v1", "expression": percentage(), "color": "rojo"},
        {"rule_id": "unallocated-cost-v1", "expression": {"quantity": "100 EUR"}},
        {
            "rule_id": "unallocated-cost-v1",
            "expression": {
                "operation": "ratio",
                "numerator": {"quantity": "100 EUR"},
                "denominator": {"quantity": "700 EUR"},
            },
        },
        {
            "rule_id": "unallocated-cost-v1",
            "expression": percentage("100 EUR", {"quantity": "1 pedido"}),
        },
    ],
)
def test_invalid_classification_shape_or_units_rejected(bad):
    with pytest.raises(ValueError):
        rendered(
            context("700 EUR; 200 EUR; 100 EUR; 1 pedido."), [{"classification": bad}]
        )


@pytest.mark.parametrize(
    "text",
    [
        "El 10 % es amarillo. ",
        "Verde hasta 5 %, amarillo hasta 10 % y rojo por encima. ",
    ],
)
@pytest.mark.parametrize("after", [False, True])
def test_coherent_explanation_can_repeat_classification(text, after):
    segments = (
        [classification(), {"text": text}]
        if after
        else [{"text": text}, classification()]
    )
    result = rendered(context(), segments)
    assert text.strip() in result and "10 %" in result
    from app.core.chat_rules import context_rules

    value = context()
    parser = SegmentAnswerJSON(
        [], quantities=context_quantities(value), rules=context_rules(value)
    )
    parser.feed(json.dumps({"answer": segments}))
    assert parser.finish().strip() == result


def test_duplicate_classification_rejected():
    with pytest.raises(ValueError, match="Duplicate classification"):
        rendered(context(), [classification(), classification()])


@pytest.mark.parametrize("failure", ["wrong_quote", "source"])
def test_classification_requires_both_actual_passages_in_selected_citations(failure):
    from app.core.chat_rules import context_rules

    value = context()
    citations = [
        {
            **{k: s[k] for k in ("id", "kind", "title", "source")},
            "support_quote": s["content"],
        }
        for s in value["authorized_evidence"]
    ]
    candidate = {
        "answer": [classification()],
        "evidence": citations,
        "assumptions": [],
        "limitations": [],
        "next_actions": [],
    }
    if failure == "source":
        candidate["evidence"][1]["source"] = "other"
    else:
        candidate["evidence"][1]["support_quote"] = "- verde: menor o igual a 5 %;"
    with pytest.raises(ValueError, match="classification citation"):
        render_response(
            candidate,
            [],
            quantities=context_quantities(value),
            rules=context_rules(value),
        )


def test_server_publishes_its_rule_citations_without_model_selection_and_keeps_foreign_ids_rejected():
    from app.core.chat_rules import context_rules
    from app.agents.schemas import assemble_chat_response
    from test_chat_gateway_jup035 import ANSWER, _provider

    value = context()
    candidate = _provider(ANSWER)
    candidate["answer"] = [classification()]
    candidate["evidence"] = []
    rendered = render_response(
        candidate, [], quantities=context_quantities(value), rules=context_rules(value)
    )
    assert {e["id"] for e in rendered["evidence"]} == {"rules:chunk:3", "rules:chunk:4"}
    assert all(
        e["support_quote"] in s["content"]
        for e, s in zip(rendered["evidence"], value["authorized_evidence"])
    )
    public = assemble_chat_response(
        rendered, None, authorized_evidence=value["authorized_evidence"]
    )
    assert len(public["evidence"]) == 2 and public["metrics"] == []
    rendered["evidence"][0]["id"] = "foreign:chunk:3"
    with pytest.raises(ValueError):
        assemble_chat_response(
            rendered, None, authorized_evidence=value["authorized_evidence"]
        )


@pytest.mark.parametrize("width", [1, 7, 8192])
def test_stream_and_final_share_classification_text_and_citation_requirements(width):
    from app.core.chat_rules import context_rules

    value = context()
    rules = context_rules(value)
    catalog = context_quantities(value)
    segments = [
        {"text": "Ejercicio hipotético. "},
        classification(),
        {"text": " No es facturación verificada."},
    ]
    raw = json.dumps({"answer": segments}, ensure_ascii=True)
    parser = SegmentAnswerJSON([], quantities=catalog, rules=rules)
    streamed = "".join(
        parser.feed(raw[i : i + width]) for i in range(0, len(raw), width)
    )
    assert streamed == parser.finish() == rendered(value, segments)


def test_schema_only_offers_authorized_rule_and_percentage_expression():
    from app.core.chat_rules import context_rules
    from app.agents.schemas import chat_provider_schema

    value = context()
    schema = chat_provider_schema(
        authorized_evidence=value["authorized_evidence"],
        quantities=context_quantities(value),
        rules=context_rules(value),
    )
    branch = schema["anyOf"][0]["properties"]["answer"]["items"]["anyOf"][-1]
    assert set(branch["properties"]) == {"classification"}
    private = branch["properties"]["classification"]
    assert set(private["properties"]) == {"rule_id", "expression"}
    assert private["properties"]["rule_id"]["enum"] == ["unallocated-cost-v1"]
    assert (
        private["properties"]["expression"]["properties"]["operation"]["const"]
        == "percentage"
    )
    assert "classification" not in json.dumps(
        chat_provider_schema(quantities=context_quantities(value))
    )


def test_metric_and_recommendation_references_are_constrained_to_authorized_chunk_ids():
    from app.agents.schemas import chat_provider_schema

    value = context()
    schema = chat_provider_schema(authorized_evidence=value["authorized_evidence"])
    for name in ("Metric", "Recommendation"):
        items = schema["$defs"][name]["properties"]["evidence_ids"]["items"]
        assert items["enum"] == ["rules:chunk:3", "rules:chunk:4"]


def test_tagging_prompt_requires_actual_policy_passage_or_omission():
    prompt = (
        Path(__file__).parents[1]
        / "app/agents/prompt_resources/jup035/chat/v3/system.md"
    ).read_text(encoding="utf-8")
    assert "Si no se recuperó el pasaje de la política de tags, omite" in prompt
    assert "classification" in prompt
    assert "Explica el resultado con naturalidad" in prompt
    assert "No escribas colores" not in prompt
    assert "No enumeres las bandas ni repitas el color en prosa" not in prompt


@pytest.mark.parametrize("width", [1, 7, 8192])
def test_controlled_gateway_emits_same_classification_and_final_citations_in_one_generation(
    monkeypatch, width
):
    from test_chat_auto_jup035 import provider, wire
    from test_chat_gateway_jup035 import ANSWER, _provider

    value = context()
    sources = value["authorized_evidence"]
    candidate = _provider(ANSWER)
    candidate["status"] = "ok"
    candidate["answer"] = [{"text": "Ejercicio hipotético. "}, classification()]
    candidate["evidence"] = [
        {
            **{k: s[k] for k in ("id", "kind", "title", "source")},
            "support_quote": s["content"],
        }
        for s in sources
    ]
    gateway, requests = provider(
        monkeypatch,
        [wire({"content": json.dumps(candidate)}, tokens=24)],
        read_size=width,
    )
    initial = {
        "tool_protocol": "server-documentation-v4",
        "financial_metrics_allowed": False,
        "authorized_evidence": [],
        "messages": value["messages"][:1],
    }
    frozen = copy.deepcopy(initial)
    controls = []

    async def retrieve(control):
        from app.core.chat_resources import validate_search_call

        controls.append(control)
        return {
            "tool_call_id": validate_search_call(control)[0],
            "content": json.dumps({"evidence": sources, "omissions": []}),
            "variable_tokens": 0,
        }

    async def exercise():
        return [
            r async for r in gateway(initial, time.time() + 60, tool_result=retrieve)
        ]

    records = asyncio.run(exercise())
    assert records[-1]["type"] == "candidate", records
    assert len(controls) == len(requests) == 1 and initial == frozen
    assert requests[0]["max_tokens"] == 6400
    assert "tools" not in requests[0] and requests[0]["num_retries"] == 0
    answer = records[-1]["result"]["answer"]
    assert "".join(r["text"] for r in records if r["type"] == "delta") == answer
    assert "= 10 %" in answer and "amarillo" in answer
    assert records[-1]["usage"]["total_tokens"] == 24
    assert all("support_quote" not in e for e in records[-1]["result"]["evidence"])
