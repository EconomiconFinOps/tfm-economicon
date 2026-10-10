"""JUP-034: independent arithmetic references and real route/auth with SQLite.

The caller supplies hypothetical scenarios. External startup resources use the
existing doubles; calculation, request validation, JWT and membership are real.
"""
from decimal import ROUND_DOWN, getcontext, localcontext

import pytest
from pydantic import ValidationError

from app.schemas.recommendation_impact import ImpactRequest
from app.services.recommendation_impact import evaluate_recommendation_impact
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers, no_effects


PATH = "/recommendations/impact/evaluate"


def scenario(identifier="rec-a", **changes):
    return {
        "recommendation_id": identifier,
        "cost_scope_ids": ["/subscriptions/sub-a/resources/" + identifier],
        "currency": "EUR",
        "baseline_monthly_cost": "250.75",
        "target_monthly_cost": "100.25",
        "evidence_ids": ["user-input:cost-scenario"],
        "assumptions": ["Same full month, usage and price basis; supplied by the operator."],
        **changes,
    }


def body(*scenarios, **changes):
    return {"baseline_month": "2024-06-01", "scenarios": list(scenarios), **changes}


def evaluate(*scenarios):
    return evaluate_recommendation_impact(ImpactRequest.model_validate(body(*scenarios)), "tenant-a")


def test_monthly_annual_and_evidence_remain_hypothetical():
    report = evaluate(scenario())
    [item] = report.recommendations
    [total] = report.totals
    assert (item.status, item.potential_monthly_savings, item.potential_annual_savings) == (
        "estimated", "150.50", "1806.00",
    )
    assert item.scenario.evidence_ids == ["user-input:cost-scenario"]
    assert item.scenario.assumptions == ["Same full month, usage and price basis; supplied by the operator."]
    assert report.basis == "caller_supplied_scenario"
    assert item.observed_savings is None and total.observed_savings is None
    assert total.included_recommendation_ids == ["rec-a"]
    assert (total.potential_monthly_savings, total.potential_annual_savings) == ("150.50", "1806.00")
    assert any("12 months" in statement for statement in report.assumptions)
    assert any("not verified" in statement for statement in report.limitations)
    assert any("implementation costs" in statement for statement in report.limitations)


@pytest.mark.parametrize("baseline,target", [("0", "0"), ("20.00", "20.00"), ("10", "20")])
def test_calculable_zero_does_not_mean_missing_data(baseline, target):
    report = evaluate(scenario(baseline_monthly_cost=baseline, target_monthly_cost=target))
    [item] = report.recommendations
    assert (item.status, item.potential_monthly_savings, item.potential_annual_savings) == (
        "no_savings", "0.00", "0.00",
    )
    assert item.included_in_total is True
    assert report.totals[0].potential_monthly_savings == "0.00"


def test_unknown_costs_are_null_even_when_another_scenario_is_estimable():
    unknown = scenario("unknown", baseline_monthly_cost=None, target_monthly_cost=None)
    only_unknown = evaluate(unknown)
    [item] = only_unknown.recommendations
    assert (item.status, item.potential_monthly_savings, item.potential_annual_savings) == (
        "insufficient_data", None, None,
    )
    assert item.included_in_total is False and item.excluded_by == []
    assert only_unknown.totals[0].potential_monthly_savings is None
    assert only_unknown.totals[0].potential_annual_savings is None
    mixed = evaluate(unknown, scenario("known"))
    assert mixed.totals[0].potential_monthly_savings == "150.50"
    assert mixed.totals[0].unestimated_recommendation_ids == ["unknown"]
    assert mixed.totals[0].included_recommendation_ids == ["known"]


def test_round_once_from_unrounded_delta_for_annual_and_total():
    report = evaluate(
        scenario("a", baseline_monthly_cost="1.005", target_monthly_cost="1"),
        scenario("b", baseline_monthly_cost="0.005", target_monthly_cost="0"),
    )
    assert [(item.potential_monthly_savings, item.potential_annual_savings)
            for item in report.recommendations] == [("0.01", "0.06"), ("0.01", "0.06")]
    assert (report.totals[0].potential_monthly_savings, report.totals[0].potential_annual_savings) == (
        "0.01", "0.12",
    )


def test_tiny_positive_potential_is_estimable_even_when_display_rounds_to_zero():
    report = evaluate(scenario(baseline_monthly_cost="0.000001", target_monthly_cost="0"))
    assert report.recommendations[0].status == "estimated"
    assert report.recommendations[0].potential_monthly_savings == "0.00"
    assert report.recommendations[0].potential_annual_savings == "0.00"


def test_largest_supported_portfolio_and_low_ambient_precision_are_exact():
    request = ImpactRequest.model_validate(body(*[
        scenario(str(index), baseline_monthly_cost="999999999999999999.999999", target_monthly_cost="0")
        for index in range(100)
    ]))
    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        report = evaluate_recommendation_impact(request, "tenant-a")
        assert getcontext().prec == 4 and getcontext().rounding == ROUND_DOWN
    assert report.recommendations[0].potential_monthly_savings == "1000000000000000000.00"
    assert report.recommendations[0].potential_annual_savings == "12000000000000000000.00"
    assert report.totals[0].potential_monthly_savings == "100000000000000000000.00"
    assert report.totals[0].potential_annual_savings == "1200000000000000000000.00"
    assert len(report.totals[0].included_recommendation_ids) == 100


def test_shared_scopes_are_alternatives_after_case_and_trailing_slash_normalization():
    report = evaluate(
        scenario("small", cost_scope_ids=[" /Subscriptions/SUB-A/resources/VM-A/// "],
                 baseline_monthly_cost="50", target_monthly_cost="0"),
        scenario("large", cost_scope_ids=["/subscriptions/sub-a/resources/vm-a"],
                 baseline_monthly_cost="80", target_monthly_cost="0"),
        scenario("other", cost_scope_ids=["/subscriptions/sub-b/resources/vm-a"],
                 baseline_monthly_cost="30", target_monthly_cost="0"),
    )
    small, large, other = report.recommendations
    assert small.scenario.cost_scope_ids == ["/subscriptions/sub-a/resources/vm-a"]
    assert small.excluded_by == ["large"] and small.included_in_total is False
    assert large.included_in_total is True and other.included_in_total is True
    assert small.potential_monthly_savings == "50.00"  # Still inspectable as an alternative.
    assert report.totals[0].included_recommendation_ids == ["large", "other"]
    assert report.totals[0].potential_monthly_savings == "110.00"


def test_multiple_intersections_explain_each_selected_conflict():
    report = evaluate(
        scenario("a", cost_scope_ids=["scope-a"], baseline_monthly_cost="80", target_monthly_cost="0"),
        scenario("b", cost_scope_ids=["scope-b"], baseline_monthly_cost="70", target_monthly_cost="0"),
        scenario("both", cost_scope_ids=["scope-a", "scope-b"], baseline_monthly_cost="60", target_monthly_cost="0"),
    )
    assert report.recommendations[2].excluded_by == ["a", "b"]
    assert report.totals[0].potential_monthly_savings == "150.00"


def test_ties_are_independent_of_request_order_and_greedy_is_not_claimed_optimal():
    candidates = [
        scenario("z", cost_scope_ids=["scope"], baseline_monthly_cost="40", target_monthly_cost="0"),
        scenario("a", cost_scope_ids=["scope"], baseline_monthly_cost="40", target_monthly_cost="0"),
    ]
    forward, reverse = evaluate(*candidates), evaluate(*reversed(candidates))
    assert forward.totals == reverse.totals
    assert forward.totals[0].included_recommendation_ids == ["a"]
    assert {item.scenario.recommendation_id: item.excluded_by for item in reverse.recommendations} == {
        "a": [], "z": ["a"],
    }
    nonoptimal = evaluate(
        scenario("combined", cost_scope_ids=["a", "b"], baseline_monthly_cost="100", target_monthly_cost="0"),
        scenario("a", cost_scope_ids=["a"], baseline_monthly_cost="60", target_monthly_cost="0"),
        scenario("b", cost_scope_ids=["b"], baseline_monthly_cost="60", target_monthly_cost="0"),
    )
    assert nonoptimal.totals[0].potential_monthly_savings == "100.00"
    assert any("not necessarily optimal" in statement for statement in nonoptimal.limitations)


def test_disjoint_currencies_never_convert_or_sum_together():
    report = evaluate(scenario("usd", currency="USD"), scenario("eur", currency="EUR"))
    assert [(total.currency, total.potential_monthly_savings, total.included_recommendation_ids)
            for total in report.totals] == [("EUR", "150.50", ["eur"]), ("USD", "150.50", ["usd"])]


@pytest.mark.parametrize("bad", [
    "-0.01", "-0", "NaN", "Infinity", "1e2", "01.00", "0.0000001",
    "1000000000000000000", "1,00", "", 1, 1.5, True,
])
def test_money_requires_bounded_nonnegative_decimal_text(bad):
    with pytest.raises(ValidationError):
        ImpactRequest.model_validate(body(scenario(baseline_monthly_cost=bad)))


@pytest.mark.parametrize("changes", [
    {"baseline_monthly_cost": None}, {"target_monthly_cost": None},
    {"evidence_ids": []}, {"evidence_ids": ["ref", " ref "]}, {"assumptions": []},
    {"cost_scope_ids": []}, {"cost_scope_ids": ["/"]}, {"cost_scope_ids": ["A", "a/"]},
    {"currency": "eur"}, {"observed_savings": "150.50"},
])
def test_incomplete_or_ambiguous_scenario_is_rejected(changes):
    with pytest.raises(ValidationError):
        ImpactRequest.model_validate(body(scenario(**changes)))


@pytest.mark.parametrize("month", ["2024-06-02", "2024-02-30", "2024-06-01T00:00:00", 1717200000])
def test_baseline_requires_explicit_complete_calendar_month(month):
    with pytest.raises(ValidationError):
        ImpactRequest.model_validate(body(scenario(), baseline_month=month))


def test_duplicate_ids_and_cross_currency_overlap_are_rejected():
    with pytest.raises(ValidationError, match="recommendation_id must be unique"):
        ImpactRequest.model_validate(body(scenario("a"), scenario(" a ")))
    with pytest.raises(ValidationError, match="overlapping scopes must use the same currency"):
        ImpactRequest.model_validate(body(
            scenario("a", cost_scope_ids=["/SUB/VM/"], currency="EUR"),
            scenario("b", cost_scope_ids=["/sub/vm"], currency="USD"),
        ))
    with pytest.raises(ValidationError):
        ImpactRequest.model_validate(body(*[scenario(str(index)) for index in range(101)]))


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_api_returns_real_calculation_and_authenticated_scope_without_effects(api):
    response = call(api, "POST", PATH, headers=headers(), json=body(scenario()))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["tenant_id"] == "tenant-a"
    assert result["baseline_month"] == "2024-06-01"
    assert result["recommendations"][0]["potential_annual_savings"] == "1806.00"
    assert result["recommendations"][0]["observed_savings"] is None
    assert result["recommendations"][0]["scenario"]["assumptions"] == scenario()["assumptions"]
    assert result["totals"][0]["observed_savings"] is None
    assert result["basis"] == "caller_supplied_scenario"
    assert any("12 months" in assumption for assumption in result["assumptions"])
    api.spies["user_has_tenant"].assert_called_once_with("alice", "tenant-a")
    no_effects(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_empty_api_report_has_no_fabricated_totals(api):
    response = call(api, "POST", PATH, headers=headers(), json=body())
    assert response.status_code == 200, response.text
    assert response.json()["recommendations"] == []
    assert response.json()["totals"] == []
    no_effects(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("case,expected", [
    ("missing_auth", 401), ("bad_token", 401), ("unknown_user", 401),
    ("missing_tenant", 400), ("duplicate_tenant", 400),
    ("foreign_tenant", 403), ("admin_without_membership", 403),
])
def test_api_authorization_uses_real_membership_before_calculation(api, case, expected):
    choices = {
        "missing_auth": [],
        "bad_token": [("Authorization", "Bearer invalid"), ("X-Tenant-Id", "tenant-a")],
        "unknown_user": headers(user="missing"),
        "missing_tenant": headers(tenant=None),
        "duplicate_tenant": headers() + [("X-Tenant-Id", "tenant-a")],
        "foreign_tenant": headers(tenant="tenant-b"),
        "admin_without_membership": headers(user="admin-alone"),
    }
    response = call(api, "POST", PATH, headers=choices[case], json=body(scenario()))
    assert response.status_code == expected, response.text
    assert "potential_monthly_savings" not in response.text
    no_effects(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("nested,field,value", [
    (False, "tenant_id", "tenant-b"), (False, "user_id", "bob"),
    (False, "observed_savings", "999"), (True, "observed_savings", "999"),
    (True, "tenant_id", "tenant-b"),
])
def test_body_cannot_supply_authority_or_observed_claims(api, nested, field, value):
    payload = body(scenario())
    target = payload["scenarios"][0] if nested else payload
    target[field] = value
    response = call(api, "POST", PATH, headers=headers(), json=payload)
    assert response.status_code == 422, response.text
    assert response.json() == {"detail": [{"type": "validation_error", "msg": "Invalid request value"}]}
    no_effects(api)
