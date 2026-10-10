"""JUP-033: independent billing inputs, exact evidence and conservative proposals."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.billing import BillingSummary
from app.schemas.recommendations import RecommendationReport
from app.services.recommendations import generate_recommendations


def cost_group(value, amount, currency="EUR", count=1):
    return {"subscription_id": None, "value": value, "cost": amount,
            "currency": currency, "record_count": count}


def source(groups=None, **changes):
    groups = groups if groups is not None else [
        cost_group(None, "-10.00", count=2),
        cost_group("Checkout", "250.00", count=3),
        cost_group("Search", "100.00"),
        cost_group("Analytics", "9007199254740993.01", "USD"),
    ]
    # Totals deliberately independent of the production code; credits remain net.
    return BillingSummary(**{
        "period": {"start_date": "2024-06-01", "end_date": "2024-07-01"},
        "group_by": "project", "tag_key": None, "data_status": "partial",
        "totals": [{"currency": "EUR", "cost": "340.00", "record_count": 6},
                   {"currency": "USD", "cost": "9007199254740993.01", "record_count": 1}],
        "groups": groups, "missing_dimension_count": 2, "excluded_undated_count": 1,
        "monthly_spend": None, "savings_identified": None, "open_ingestions": 0,
        "currency": None, **changes,
    })


def report(summary=None, tenant="tenant-a"):
    return generate_recommendations(summary if summary is not None else source(), tenant_id=tenant)


def test_supported_tagging_and_investigation_keep_evidence_not_savings():
    result = report()
    assert result.contract_version == 1
    assert result.cloud == "azure" and result.data_environment == "simulated"
    assert result.status == "available" and result.data_status == "partial"
    assert result.missing_dimension_count == 2 and result.excluded_undated_count == 1
    assert len(result.recommendations) == 3
    by_category = {item.category: item for item in result.recommendations}
    tagging = by_category["tagging"]
    assert tagging.qualification == "supported"
    assert tagging.scope.value is None
    assert tagging.observed_cost.amount == "-10.00"
    assert tagging.observed_cost.record_count == 2
    investigations = [item for item in result.recommendations if item.category == "investigation"]
    assert {(x.scope.value, x.observed_cost.amount, x.observed_cost.currency) for x in investigations} == {
        ("Checkout", "250.00", "EUR"), ("Analytics", "9007199254740993.01", "USD"),
    }
    evidence = {item.id: item for item in result.evidence}
    for item in result.recommendations:
        assert item.estimated_savings is None and item.currency is None
        assert item.requires_human_approval is True
        assert item.evidence_ids
        proof = evidence[item.evidence_ids[0]]
        assert proof.observed_cost == item.observed_cost and proof.scope == item.scope
        assert proof.query.group_by == "project" and proof.query.tag_key is None
        assert proof.query.period == result.period
    assert result.not_evaluated and result.limitations and result.assumptions


@pytest.mark.parametrize("net_cost", ["0.00", "-2.00", "5.00"])
def test_missing_project_still_actionable_for_zero_or_credit(net_cost):
    result = report(source([cost_group(None, net_cost)]))
    assert [(x.category, x.observed_cost.amount) for x in result.recommendations] == [("tagging", net_cost)]


def test_unknown_is_a_literal_project_and_nonpositive_projects_are_not_waste():
    result = report(source([
        cost_group("Unknown", "1.00"), cost_group("Negative", "-20.00"),
        cost_group("Zero", "0.00"),
    ], missing_dimension_count=0))
    assert [(x.category, x.scope.value) for x in result.recommendations] == [("investigation", "Unknown")]
    assert report(source([cost_group("Zero", "0.00")])).recommendations == []


def test_ties_are_deterministic_with_input_order_irrelevant():
    groups = [cost_group("b", "1.00"), cost_group("a", "1.00"), cost_group(None, "0.00")]
    left, right = report(source(groups)), report(source(list(reversed(groups))))
    assert left == right
    assert [x.scope.value for x in left.recommendations if x.category == "investigation"] == ["a"]


def test_identity_is_scoped_and_evidence_changes_with_cost_or_competitor():
    baseline = report()
    assert report() == baseline
    assert {x.id for x in baseline.recommendations}.isdisjoint(x.id for x in report(tenant="tenant-b").recommendations)
    changed = source()
    changed.groups[1].cost = "251.00"
    current = report(changed)
    assert [x.id for x in current.recommendations] == [x.id for x in baseline.recommendations]
    assert [x.id for x in current.evidence] != [x.id for x in baseline.evidence]
    changed = source()
    changed.groups[2].cost = "99.00"
    assert [x.id for x in report(changed).evidence] != [x.id for x in baseline.evidence]
    changed = source()
    changed.period.start_date = changed.period.start_date.replace(day=2)
    assert {x.id for x in baseline.recommendations}.isdisjoint(x.id for x in report(changed).recommendations)


@pytest.mark.parametrize("data_status,undated", [("empty", 0), ("partial", 2)])
def test_empty_period_does_not_invent_recommendations(data_status, undated):
    result = report(source([], totals=[], data_status=data_status, excluded_undated_count=undated,
                           missing_dimension_count=0))
    assert result.status == "insufficient_data"
    assert result.recommendations == [] and result.evidence == []
    assert result.data_status == data_status


def test_output_bound_is_explicit_and_never_compares_currency_amounts():
    currencies = ["X" + chr(65 + n // 26) + chr(65 + n % 26) for n in range(55)]
    groups = [cost_group("Project", f"{n+1}.00", currency) for n, currency in enumerate(currencies)]
    result = report(source(groups))
    assert result.total_candidates == 55 and result.truncated is True
    assert len(result.recommendations) == 50
    assert [x.observed_cost.currency for x in result.recommendations] == currencies[:50]
    assert len(result.evidence) == 50


@pytest.mark.parametrize("field,value", [
    ("estimated_savings", "20.00"), ("currency", "EUR"),
    ("requires_human_approval", False), ("evidence_ids", ["unknown"]),
])
def test_contract_rejects_unsupported_savings_or_evidence(field, value):
    payload = report().model_dump(mode="json")
    payload["recommendations"][0][field] = value
    with pytest.raises(ValidationError):
        RecommendationReport.model_validate(payload)


def test_generation_does_not_mutate_its_input():
    original = source()
    before = deepcopy(original)
    report(original)
    assert original == before


@pytest.mark.parametrize("group_by,tag_key", [("service", None), ("tag", "project")])
def test_wrong_source_dimension_fails_closed(group_by, tag_key):
    with pytest.raises(ValueError):
        report(source(group_by=group_by, tag_key=tag_key))
