"""Independent arithmetic examples and authenticated JUP-029 acceptance tests."""
from datetime import date
from decimal import localcontext

import pytest
from app.schemas.billing import AmbiguousCostSource, BillingSummary
from app.schemas.budget import BudgetDefinition
from app.services.budget import evaluate_budget
from billing_support import billing_schema, cost_reference, summary
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging


BODY = {"amount": "100.00", "currency": "EUR", "start_date": "2024-06-01", "end_date": "2024-07-01"}
PATH = "/billing/budget/evaluate"


def observed(cost, **changes):
    return BillingSummary(**summary(
        data_status="available", missing_dimension_count=0, excluded_undated_count=0,
        totals=[{"currency": "EUR", "cost": cost, "record_count": 2}], **changes,
    ))


@pytest.mark.parametrize("spend,consumption,remaining,deviation,reached", [
    ("0.00", "0.00", "100.00", "-100.00", []),
    ("79.99", "79.99", "20.01", "-20.01", []),
    ("80.00", "80.00", "20.00", "-20.00", ["80.00"]),
    ("99.99", "99.99", "0.01", "-0.01", ["80.00"]),
    ("100.00", "100.00", "0.00", "0.00", ["80.00", "100.00"]),
    ("125.25", "125.25", "-25.25", "25.25", ["80.00", "100.00"]),
    ("-12.34", "-12.34", "112.34", "-112.34", []),
])
def test_reference_calculations(spend, consumption, remaining, deviation, reached):
    result = evaluate_budget(BudgetDefinition(**BODY), observed(spend))
    assert result.evaluation_status == "evaluated"
    assert result.observed_spend == spend
    assert result.consumption_percent == consumption
    assert result.remaining_amount == remaining
    assert result.deviation_amount == deviation
    assert result.deviation_percent == deviation  # B=100 makes the independent expectation equal.
    assert result.reached_thresholds_percent == reached
    assert result.highest_reached_threshold_percent == (reached[-1] if reached else None)


def test_threshold_comparison_precedes_rounding_and_supports_custom_limits():
    budget = BudgetDefinition(**{**BODY, "amount": "1000.00", "thresholds_percent": ["80.00", "125.00"]})
    result = evaluate_budget(budget, observed("799.99"))
    assert result.consumption_percent == "80.00"
    assert result.deviation_percent == "-20.00"
    assert result.reached_thresholds_percent == []
    assert evaluate_budget(budget, observed("1250.00")).reached_thresholds_percent == ["80.00", "125.00"]


def test_negative_zero_is_never_displayed():
    budget = BudgetDefinition(**{**BODY, "amount": "1000.00"})
    assert evaluate_budget(budget, observed("-0.01")).consumption_percent == "0.00"


def test_documented_maximums_are_accepted_and_keep_exact_comparison():
    budget = BudgetDefinition(**{
        **BODY, "amount": "9" * 26 + ".99", "thresholds_percent": ["80.00", "1000.00"],
    })
    below = evaluate_budget(budget, observed("7" + "9" * 25 + ".99"))
    assert below.consumption_percent == "80.00"
    assert below.reached_thresholds_percent == []
    assert evaluate_budget(budget, observed("8" + "0" * 25 + ".00")).reached_thresholds_percent == ["80.00"]


def test_large_money_and_decimal_context_do_not_lose_cents():
    budget = BudgetDefinition(**{**BODY, "amount": "9007199254740993.00"})
    with localcontext() as context:
        context.prec = 6
        result = evaluate_budget(budget, observed("9007199254740993.01"))
    assert result.remaining_amount == "-0.01"
    assert result.deviation_amount == "0.01"
    assert result.consumption_percent == "100.00"
    assert result.highest_reached_threshold_percent == "100.00"


def test_nonterminating_ratio_and_half_up_rounding():
    budget = BudgetDefinition(**{**BODY, "amount": "3.00"})
    result = evaluate_budget(budget, observed("1.00"))
    assert (result.consumption_percent, result.deviation_percent) == ("33.33", "-66.67")
    budget = BudgetDefinition(**{**BODY, "amount": "200.00"})
    result = evaluate_budget(budget, observed("0.01"))
    assert (result.consumption_percent, result.deviation_percent) == ("0.01", "-100.00")


@pytest.mark.parametrize("currency,status", [("EUR", "provisional"), ("GBP", "provisional"), ("JPY", "unavailable")])
def test_currency_selection_partial_and_observed_zero(currency, status):
    result = evaluate_budget(BudgetDefinition(**{**BODY, "currency": currency}), BillingSummary(**summary()))
    assert result.evaluation_status == status
    assert result.data_status == "partial"
    assert result.excluded_undated_count == 1
    assert result.missing_dimension_count == 1
    assert result.observed_spend == {"EUR": "11.01", "GBP": "0.00", "JPY": None}[currency]
    if status == "unavailable":
        assert result.consumption_percent is None
        assert result.remaining_amount is None
        assert result.deviation_amount is None
        assert result.deviation_percent is None
        assert result.reached_thresholds_percent is None


def test_empty_is_not_zero():
    result = evaluate_budget(BudgetDefinition(**BODY), BillingSummary(**summary(totals=[], data_status="empty")))
    assert result.evaluation_status == "unavailable"
    assert result.observed_spend is None
    assert result.reached_thresholds_percent is None


@pytest.mark.parametrize("change", [
    {"amount": "0.00"}, {"amount": "-1.00"}, {"amount": 100}, {"amount": 0.1},
    {"amount": "NaN"}, {"amount": "Infinity"}, {"amount": "1e2"}, {"amount": "01.00"},
    {"amount": "1.001"}, {"amount": "1"}, {"amount": "9" * 27 + ".00"},
    {"currency": "eur"}, {"currency": "EURO"}, {"currency": " EUR"},
    {"start_date": "2024-07-01"}, {"end_date": "2024-05-01"},
    {"start_date": "2024-02-30"}, {"start_date": 1717200000},
    {"start_date": "2024-06-01T00:00:00Z"},
    {"thresholds_percent": []}, {"thresholds_percent": ["0.00"]},
    {"thresholds_percent": ["1000.01"]}, {"thresholds_percent": ["80.00", "80.00"]},
    {"thresholds_percent": ["100.00", "80.00"]}, {"thresholds_percent": [80]},
    {"thresholds_percent": [f"{n}.00" for n in range(1, 12)]},
    {"tenant_id": "tenant-b"}, {"observed_spend": "0.00"},
])
@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_invalid_body_rejected_before_cost_read(api, change):
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, **change})
    assert response.status_code == 422, response.text
    api.spies["fetch_billing_summary"].assert_not_called()


def test_internal_mismatched_period_and_duplicate_currency_fail():
    budget = BudgetDefinition(**BODY)
    with pytest.raises(ValueError, match="period"):
        evaluate_budget(budget, BillingSummary(**summary(period={"start_date": "2024-05-01", "end_date": "2024-06-01"})))
    with pytest.raises(ValueError, match="unique"):
        evaluate_budget(budget, BillingSummary(**summary(totals=summary()["totals"] * 2)))


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_api_forwards_authorized_tenant_and_exact_dates(api):
    api.spies["fetch_billing_summary"].return_value = observed("80.00").model_dump(mode="json")
    response = call(api, "POST", PATH, headers=headers(), json=BODY)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["budget"] == {**BODY, "thresholds_percent": ["80.00", "100.00"]}
    assert result["observed_spend"] == "80.00"
    assert result["highest_reached_threshold_percent"] == "80.00"
    assert result["timezone"] == "UTC"
    api.spies["fetch_billing_summary"].assert_called_once_with(
        "tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1),
        group_by="subscription", tag_key=None,
    )


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("authorization,tenant,expected", [(False, "tenant-a", 401), (True, "tenant-b", 403), (True, None, 400)])
def test_api_auth_and_membership_precede_costs(api, authorization, tenant, expected):
    response = call(api, "POST", PATH, headers=headers(tenant=tenant) if authorization else [], json=BODY)
    assert response.status_code == expected
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_api_overlap_never_returns_amounts(api):
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource()
    response = call(api, "POST", PATH, headers=headers(), json=BODY)
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_costs_preserve_period_tenant_currency_and_credit_exclusions(cost_reference, api):
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, "amount": "10.00"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["observed_spend"] == "11.01"
    assert result["record_count"] == 5
    assert result["remaining_amount"] == "-1.01"
    assert result["consumption_percent"] == "110.10"
    assert result["deviation_percent"] == "10.10"
    assert result["evaluation_status"] == "provisional"
    assert result["excluded_undated_count"] == 1
    assert result["reached_thresholds_percent"] == ["80.00", "100.00"]
