"""Documentary thresholds are scoped evidence, never financial authority."""

import copy
import json

import pytest

from app.core.chat_expressions import (
    context_quantities,
    ExpressionRenderer,
    MAX_QUANTITIES,
)


def context(
    question="Coste 84 EUR y base 70 EUR.",
    text="El indicador experimental alerta por encima de 17%.",
):
    source = {
        "id": "corpus:experiment:1",
        "kind": "corpus",
        "title": "Synthetic rule",
        "source": "Synthetic manual",
        "content": text,
    }
    return {
        "messages": [
            {
                "role": "user",
                "content": "UNTRUSTED_CURRENT_CONTEXT\n"
                + json.dumps({"question": question}),
            },
            {
                "role": "user",
                "content": "UNTRUSTED_RETRIEVAL_CONTEXT\n"
                + json.dumps({"evidence": [source]}),
            },
        ],
        "authorized_evidence": [source],
    }


def test_documentary_threshold_absent_from_question_is_available_with_provenance():
    catalog = context_quantities(context())
    key = "document:corpus:experiment:1:17 %"
    assert catalog[key]["provenance"] == [
        {"kind": "corpus", "id": "corpus:experiment:1", "source": "17%"}
    ]
    assert catalog["84 EUR"]["provenance"][0]["kind"] == "user"
    result = ExpressionRenderer(catalog).render(
        {
            "operation": "compare",
            "relation": "gt",
            "left": {
                "operation": "relative_change",
                "current": {"quantity": "84 EUR"},
                "baseline": {"quantity": "70 EUR"},
            },
            "right": {"quantity": key},
        }
    )
    assert "verdadero" in result and "17 %" in result
    assert "corpus:" not in result


def test_percentage_threshold_comparison_uses_document_units_not_money():
    catalog = context_quantities(
        context(
            question="Importes: 100 EUR; total 1000 EUR.",
            text="El limite incluido es 10%.",
        )
    )
    share = {
        "operation": "percentage",
        "numerator": {"quantity": "100 EUR"},
        "denominator": {"quantity": "1000 EUR"},
    }
    comparison = {
        "operation": "compare",
        "left": share,
        "right": {"quantity": "100 EUR"},
        "relation": "lte",
    }
    with pytest.raises(ValueError, match="Incompatible expression units"):
        ExpressionRenderer(catalog).render(comparison)
    comparison["right"] = {"quantity": "document:corpus:experiment:1:10 %"}
    assert "verdadero" in ExpressionRenderer(catalog).render(comparison)


def test_chat_prompt_explicitly_separates_percentage_and_monetary_comparisons():
    from pathlib import Path

    prompt = (
        Path(__file__).parents[1]
        / "app/agents/prompt_resources/jup035/chat/v3/system.md"
    ).read_text(encoding="utf-8")
    assert "Nunca compares un porcentaje con un importe" in prompt
    assert "umbral porcentual documentado del mismo KPI" in prompt
    assert "el servidor aplica" in prompt
    assert "No uses compare para este semáforo" in prompt


@pytest.mark.parametrize("change", ["omitted", "foreign", "changed"])
def test_only_exact_effective_documentary_content_is_allowed(change):
    value = context()
    if change == "omitted":
        value["authorized_evidence"] = []
    elif change == "foreign":
        value["authorized_evidence"][0] = dict(
            value["authorized_evidence"][0], id="corpus:foreign:1"
        )
    else:
        value["authorized_evidence"][0] = dict(
            value["authorized_evidence"][0], content="Altered 18%."
        )
    with pytest.raises(ValueError, match="not authorized"):
        context_quantities(value)


def test_documentary_units_must_be_explicit_and_never_inherited():
    catalog = context_quantities(
        context(
            text="Moneda EUR; gasto 42; memoria 13; presupuesto 72 EUR; umbral 17%."
        )
    )
    document = [v for k, v in catalog.items() if k.startswith("document:")]
    assert {(v["value"], v["unit"]) for v in document} == {("72", "EUR"), ("17", "%")}


def test_documentary_duplicates_preserve_origins_and_do_not_evict_user_options():
    value = context(
        question=" ".join(str(i) + " EUR;" for i in range(MAX_QUANTITIES - 1)),
        text="17% y 17%.",
    )
    catalog = context_quantities(value)
    assert len(catalog) == MAX_QUANTITIES
    assert all(str(i) + " EUR" in catalog for i in range(MAX_QUANTITIES - 1))
    assert len([k for k in catalog if k.startswith("document:")]) == 1
    forged = copy.deepcopy(catalog)
    with pytest.raises(ValueError, match="Unknown source"):
        ExpressionRenderer(forged).render(
            {
                "operation": "sum",
                "left": {"quantity": "document:other:17 %"},
                "right": {"quantity": "0 EUR"},
            }
        )


@pytest.mark.parametrize("width", [1, 7, 8192])
def test_documentary_expression_stream_equals_final_projection(width):
    from app.clients.chat_stream_parser import SegmentAnswerJSON
    from app.core.chat_segments import render_segments

    catalog = context_quantities(context())
    segments = [
        {"text": "Comparación hipotética: "},
        {
            "expression": {
                "operation": "compare",
                "relation": "gt",
                "left": {
                    "operation": "relative_change",
                    "current": {"quantity": "84 EUR"},
                    "baseline": {"quantity": "70 EUR"},
                },
                "right": {"quantity": "document:corpus:experiment:1:17 %"},
            }
        },
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


@pytest.mark.parametrize("evidence", [[], [{"id": "corpus:other:1", "kind": "corpus"}]])
def test_documentary_operand_requires_its_source_in_final_selected_evidence(evidence):
    from app.core.chat_segments import render_response

    catalog = context_quantities(context())
    value = {
        "answer": [
            {
                "expression": {
                    "operation": "sum",
                    "left": {"quantity": "document:corpus:experiment:1:17 %"},
                    "right": {"quantity": "document:corpus:experiment:1:17 %"},
                }
            }
        ],
        "assumptions": [],
        "limitations": [],
        "next_actions": [],
        "evidence": evidence,
    }
    with pytest.raises(ValueError, match="citation missing"):
        render_response(value, [], quantities=catalog)
    value["evidence"] = [{"id": "corpus:experiment:1", "kind": "corpus"}]
    assert "34 %" in render_response(value, [], quantities=catalog)["answer"]


def test_reused_compound_denominator_fits_existing_depth_and_operation_budget():
    # Contract capacity, not an assertion about the model's semantic choices.
    from app.core.chat_expressions import quantities
    from app.core.chat_segments import render_segments

    catalog = quantities("Volúmenes: 18 GB; 7 GB; 5 GB.")
    total = {
        "operation": "sum",
        "left": {"quantity": "18 GB"},
        "right": {
            "operation": "sum",
            "left": {"quantity": "7 GB"},
            "right": {"quantity": "5 GB"},
        },
    }
    part = {
        "operation": "percentage",
        "numerator": {"quantity": "5 GB"},
        "denominator": copy.deepcopy(total),
    }
    renderer = ExpressionRenderer(catalog)
    answer = render_segments(
        [{"expression": total}, {"text": "Participación: "}, {"expression": part}],
        [],
        expressions=renderer,
    )
    assert "30 GB" in answer and "16.666667 %" in answer
    assert renderer.operations == 5
