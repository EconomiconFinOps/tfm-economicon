"""Deterministic arithmetic acceptance; not evidence of model operand selection."""

import copy

import pytest


@pytest.mark.parametrize("operator", ["sum", "percentage", "compare"])
def test_unit_mismatch_diagnostic_is_structural_and_keeps_rejection(operator, caplog):
    import json
    import logging
    from app.clients.chat_gateway import _record_diagnostic

    catalog = quantities("700 EUR; 5 %; 100 EUR.")
    expression = {"operation": operator}
    if operator == "percentage":
        expression.update(numerator={"quantity": "700 EUR"}, denominator={"quantity": "5 %"})
    else:
        expression.update(left={"quantity": "700 EUR"}, right={"quantity": "5 %"})
        if operator == "compare":
            expression["relation"] = "lte"
    with pytest.raises(ValueError, match="Incompatible expression units") as rejected:
        ExpressionRenderer(catalog).render(expression)
    caplog.set_level(logging.WARNING, logger="app.clients.chat_gateway")
    _record_diagnostic("provisional_answer", rejected.value, "0" * 64, None, category="invalid_response")
    event = json.loads(caplog.records[-1].getMessage())
    assert event["rule_code"] == "expression_incompatible_units"
    assert event["expression"] == {"operation": operator, "depth": 0, "left_unit": "currency", "right_unit": "percent"}
    assert "700" not in caplog.text and "EUR" not in caplog.text


def test_expression_diagnostic_does_not_log_untrusted_units_or_operator(caplog):
    import json
    import logging
    from app.core.chat_expressions import ExpressionUnitError
    from app.clients.chat_gateway import _record_diagnostic

    failure = ExpressionUnitError("SECRET_OPERATOR", "SECRET_LEFT", "SECRET_RIGHT", 999)
    caplog.set_level(logging.WARNING, logger="app.clients.chat_gateway")
    _record_diagnostic("provisional_answer", failure, "0" * 64, None, category="invalid_response")
    event = json.loads(caplog.records[-1].getMessage())
    assert event["expression"] == {"operation": "other", "depth": None, "left_unit": "other", "right_unit": "other"}
    assert "SECRET" not in caplog.text

from app.core.chat_expressions import ExpressionRenderer, quantities
from app.core.chat_segments import render_segments


def leaf(value):
    return {"quantity": value}


def total():
    return {
        "operation": "sum",
        "left": leaf("700 EUR"),
        "right": {
            "operation": "sum",
            "left": leaf("200 EUR"),
            "right": leaf("100 EUR"),
        },
    }


@pytest.mark.parametrize(
    "part,expected,color",
    [("100", "10", "yellow"), ("50", "5", "green"), ("101", "10.1", "red")],
)
def test_eligible_total_and_inclusive_thresholds(part, expected, color):
    catalog = quantities(
        f"700 EUR; 200 EUR; 100 EUR; excluded 50 EUR; unallocated {part} EUR; 5 %; 10 %."
    )
    share = {
        "operation": "percentage",
        "numerator": leaf(part + " EUR"),
        "denominator": total(),
    }
    renderer = ExpressionRenderer(catalog)
    rendered = render_segments(
        [{"expression": total()}, {"expression": copy.deepcopy(share)}],
        [],
        expressions=renderer,
    )
    assert "= 1000 EUR" in rendered
    assert "= " + expected + " %" in rendered
    for threshold, relation, truth in [
        ("5 %", "lte", color == "green"),
        ("10 %", "gt", color == "red"),
    ]:
        comparison = {
            "operation": "compare",
            "left": share,
            "right": leaf(threshold),
            "relation": relation,
        }
        text = ExpressionRenderer(catalog).render(comparison)
        assert ("verdadero" if truth else "falso") in text


def test_zero_daily_baseline_and_monthly_realization_preserve_units():
    renderer = ExpressionRenderer(
        quantities("Baseline diario 0 EUR; observado 150 EUR/día.")
    )
    change = {
        "operation": "difference",
        "current": leaf("150 EUR/día"),
        "baseline": leaf("0 EUR/día"),
    }
    assert "= 150 EUR/día" in renderer.render(change)
    change["operation"] = "relative_change"
    assert "indefinida" in renderer.render(change)
    monthly = ExpressionRenderer(
        quantities(
            "Identificado 200 EUR/mes; estimado 150 EUR/mes; realizado 80 EUR/mes."
        )
    )
    assert "= 40 %" in monthly.render(
        {
            "operation": "percentage",
            "numerator": leaf("80 EUR/mes"),
            "denominator": leaf("200 EUR/mes"),
        }
    )


def test_incompatible_time_units_and_legacy_calculation_ids_are_rejected():
    renderer = ExpressionRenderer(quantities("150 EUR/día; 200 EUR/mes."))
    with pytest.raises(ValueError, match="units"):
        renderer.render(
            {
                "operation": "percentage",
                "numerator": leaf("150 EUR/día"),
                "denominator": leaf("200 EUR/mes"),
            }
        )
    with pytest.raises(ValueError):
        render_segments(
            [{"calculation_id": "n:0"}], [{"id": "n:0", "equation": "invented"}]
        )


@pytest.mark.parametrize("quote", [None, "", "Paraphrased rule", "A different source."])
def test_corpus_passage_must_belong_to_its_authorized_source(quote):
    from app.agents.schemas import assemble_chat_response
    from test_chat_gateway_jup035 import ANSWER

    source = {"id": "corpus:owned:1", "kind": "corpus", "title": "Rule", "source": "Manual", "content": "The complete authorized rule."}
    response = copy.deepcopy(ANSWER)
    response["scope"].pop("period")
    response["scope"].pop("subscription_ids")
    record = {key: source[key] for key in ("id", "kind", "title", "source")}
    response["evidence"] = [{**record, **({"support_quote": quote} if quote is not None else {})}]
    with pytest.raises(ValueError):
        assemble_chat_response(response, None, authorized_evidence=[source])
    response["evidence"] = [{**record, "support_quote": source["content"]}]
    public = assemble_chat_response(response, None, authorized_evidence=[source])
    assert public["evidence"] == [record]
    assert "support_quote" not in str(public)
