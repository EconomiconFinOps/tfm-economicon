"""JUP-030: independent cost examples and authenticated anomaly contract checks."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from unittest.mock import call as expected_call

import pytest

from app.schemas.anomalies import AnomalyDefinition
from app.schemas.billing import AmbiguousCostSource, BillingSummary
from app.services.anomalies import evaluate_anomalies
from billing_support import billing_schema, cost_reference, insert_cost, summary
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers


BODY = {
    "start_date": "2024-06-01", "end_date": "2024-07-01", "currency": "EUR",
    "absolute_threshold": "100.00", "deviation_threshold_percent": "20.00",
}
PATH = "/billing/anomalies/evaluate"
PRIOR_PERIOD = {"start_date": "2024-05-02", "end_date": "2024-06-01", "timezone": "UTC"}


def group(cost, value="Compute", *, currency="EUR", subscription_id=None, record_count=1):
    return {"cost": cost, "value": value, "currency": currency,
            "subscription_id": subscription_id, "record_count": record_count}


def observed(*groups, baseline=False, **changes):
    """Construct records independently of the production aggregate/evaluator functions."""
    totals = {}
    with localcontext() as context:
        context.prec = 100
        for item in groups:
            cost, count = totals.get(item["currency"], (Decimal(0), 0))
            totals[item["currency"]] = (cost + Decimal(item["cost"]), count + item["record_count"])
        rows = [{"currency": currency, "cost": format(cost, ".2f"), "record_count": count}
                for currency, (cost, count) in totals.items()]
    overrides = {"data_status": "available" if groups else "empty", "groups": list(groups),
                 "totals": rows, "missing_dimension_count": 0, "excluded_undated_count": 0}
    if baseline:
        overrides["period"] = PRIOR_PERIOD
    return BillingSummary(**summary(**{**overrides, **changes}))


def evaluate(current, baseline=None, *, tenant="tenant-a", **definition):
    return evaluate_anomalies(AnomalyDefinition(**{**BODY, **definition}), current, baseline, tenant_id=tenant)


@pytest.mark.parametrize("cost,status,alerts", [
    ("99.99", "below", 0), ("100.00", "triggered", 1), ("100.01", "triggered", 1),
    ("0.00", "below", 0), ("-2.00", "below", 0),
])
def test_absolute_threshold_includes_boundary_and_credits(cost, status, alerts):
    result = evaluate(observed(group(cost)), deviation_threshold_percent=None)
    assert result.evaluation_status == "evaluated"
    assert result.assessments[0].threshold_status == status
    assert result.assessments[0].deviation_status == "disabled"
    assert len(result.alerts) == alerts
    assert result.baseline_period is None
    assert result.baseline_quality is None


@pytest.mark.parametrize("cost,status,percent,delta", [
    ("119.99", "below", "19.99", "19.99"),
    ("120.00", "triggered", "20.00", "20.00"),
    ("120.01", "triggered", "20.01", "20.01"),
    ("100.00", "below", "0.00", "0.00"),
    ("90.00", "below", "-10.00", "-10.00"),
    ("-5.00", "below", "-105.00", "-105.00"),
])
def test_previous_equal_period_increase_examples(cost, status, percent, delta):
    result = evaluate(observed(group(cost)), observed(group("100.00"), baseline=True), absolute_threshold=None)
    [assessment] = result.assessments
    assert assessment.deviation_status == status
    assert assessment.deviation_percent == percent
    assert assessment.delta_amount == delta
    assert assessment.threshold_status == "disabled"
    assert result.baseline_period.model_dump(mode="json") == PRIOR_PERIOD


def test_one_alert_preserves_both_rules_and_does_not_claim_cause():
    result = evaluate(observed(group("120.00")), observed(group("100.00"), baseline=True))
    [alert] = result.alerts
    assert alert.trigger_reasons == ["absolute_threshold", "period_increase"]
    assert alert.cause_status == "not_established"
    assert alert.model_dump(exclude={"id", "evidence_id", "cause_status"}) == result.assessments[0].model_dump()
    assert result.source == "billing_summary_v2"
    assert result.contract_version == 1
    assert result.completeness == "not_verified"


def test_percentage_comparison_precedes_rounding():
    result = evaluate(observed(group("1199.99")), observed(group("1000.00"), baseline=True), absolute_threshold=None)
    [assessment] = result.assessments
    assert assessment.deviation_percent == "20.00"
    assert assessment.deviation_status == "below"
    assert result.alerts == []


@pytest.mark.parametrize("minimum,status", [("0.01", "triggered"), ("0.02", "below")])
def test_minimum_absolute_increase_filters_small_percentage_spikes(minimum, status):
    result = evaluate(observed(group("0.02")), observed(group("0.01"), baseline=True),
                      absolute_threshold=None, min_absolute_increase=minimum)
    assert result.assessments[0].deviation_percent == "100.00"
    assert result.assessments[0].deviation_status == status


def test_large_money_remains_exact_under_small_decimal_context():
    current = observed(group("9007199254740993.01"))
    baseline = observed(group("9007199254740993.00"), baseline=True)
    with localcontext() as context:
        context.prec = 6
        result = evaluate(current, baseline, absolute_threshold="9007199254740993.01")
    [alert] = result.alerts
    assert alert.current_cost == "9007199254740993.01"
    assert alert.delta_amount == "0.01"
    assert alert.deviation_percent == "0.00"
    assert alert.trigger_reasons == ["absolute_threshold"]


def test_nonterminating_ratio_uses_half_up_rounding():
    result = evaluate(observed(group("4.00")), observed(group("3.00"), baseline=True))
    assert result.assessments[0].deviation_percent == "33.33"
    result = evaluate(observed(group("200.01")), observed(group("200.00"), baseline=True))
    assert result.assessments[0].deviation_percent == "0.01"


@pytest.mark.parametrize("prior,status,delta", [
    (None, "baseline_missing", None), ("0.00", "baseline_nonpositive", "120.00"),
    ("-5.00", "baseline_nonpositive", "125.00"),
])
def test_missing_zero_and_negative_baselines_are_explicit(prior, status, delta):
    baseline = observed(*([] if prior is None else [group(prior)]), baseline=True)
    result = evaluate(observed(group("120.00")), baseline)
    assert result.evaluation_status == "provisional"
    [alert] = result.alerts
    assert alert.deviation_status == status
    assert alert.deviation_percent is None
    assert alert.delta_amount == delta
    assert alert.trigger_reasons == ["absolute_threshold"]


def test_selected_currency_never_compares_or_adds_other_currencies():
    current = observed(group("60.00"), group("900.00", currency="USD"))
    baseline = observed(group("100.00", currency="USD"), baseline=True)
    result = evaluate(current, baseline)
    [assessment] = result.assessments
    assert assessment.currency == "EUR"
    assert assessment.current_cost == "60.00"
    assert assessment.deviation_status == "baseline_missing"
    assert result.current_quality.record_count == 1
    assert result.baseline_quality.record_count == 0
    assert result.alerts == []


@pytest.mark.parametrize("current", [observed(), observed(group("400.00", currency="USD"))])
def test_absent_selected_currency_is_unavailable_not_zero(current):
    result = evaluate(current, deviation_threshold_percent=None)
    assert result.evaluation_status == "unavailable"
    assert result.current_quality.record_count == 0
    assert result.assessments == result.alerts == []


@pytest.mark.parametrize("partial_period", ["current", "baseline"])
def test_quality_counts_and_partial_status_survive_evaluation(partial_period):
    quality = {"data_status": "partial", "missing_dimension_count": 2, "excluded_undated_count": 3}
    current = observed(group("120.00", record_count=4), **(quality if partial_period == "current" else {}))
    baseline = observed(group("100.00", record_count=5), baseline=True,
                        **(quality if partial_period == "baseline" else {}))
    result = evaluate(current, baseline)
    assert result.evaluation_status == "provisional"
    retained = getattr(result, partial_period + "_quality")
    assert retained.data_status == "partial"
    assert retained.missing_dimension_count == 2
    assert retained.excluded_undated_count == 3
    assert result.current_quality.record_count == 4
    assert result.baseline_quality.record_count == 5
    assert result.assessments[0].current_record_count == 4
    assert result.assessments[0].baseline_record_count == 5


def test_missing_dimension_is_distinct_from_literal_unknown():
    current = observed(group("120.00", None), group("130.00", "Unknown"), data_status="partial", missing_dimension_count=1)
    baseline = observed(group("100.00", None), group("200.00", "Unknown"), baseline=True)
    result = evaluate(current, baseline)
    assert {item.group_value: item.deviation_status for item in result.assessments} == {
        None: "triggered", "Unknown": "below",
    }
    assert len({item.id for item in result.alerts}) == 2


def test_resource_group_matching_is_case_insensitive_and_subscription_scoped():
    current = observed(group("120.00", "SHARED", subscription_id="sub-a"),
                       group("120.00", "shared", subscription_id="sub-b"), group_by="resource_group")
    baseline = observed(group("100.00", "shared", subscription_id="sub-a"),
                        group("200.00", "Shared", subscription_id="sub-b"), baseline=True, group_by="resource_group")
    result = evaluate(current, baseline, group_by="resource_group", absolute_threshold=None)
    assert {item.subscription_id: item.deviation_status for item in result.assessments} == {
        "sub-a": "triggered", "sub-b": "below",
    }
    assert result.alerts[0].subscription_id == "sub-a"


def test_service_matching_preserves_case():
    result = evaluate(observed(group("120.00", "Compute")),
                      observed(group("100.00", "compute"), baseline=True), absolute_threshold=None)
    assert result.assessments[0].deviation_status == "baseline_missing"
    assert result.alerts == []


def test_repeated_and_reordered_evidence_has_stable_ids_but_scope_and_rules_differ():
    current = observed(group("120.00", "Compute"), group("140.00", "Storage"))
    baseline = observed(group("100.00", "Compute"), group("100.00", "Storage"), baseline=True)
    first = evaluate(current, baseline)
    reordered = evaluate(observed(*reversed(current.model_dump()["groups"])),
                         observed(*reversed(baseline.model_dump()["groups"]), baseline=True))
    assert first.model_dump() == reordered.model_dump()
    identities = {item.id for item in first.alerts}
    assert len(identities) == 2
    assert identities.isdisjoint(item.id for item in evaluate(current, baseline, tenant="tenant-b").alerts)
    assert identities.isdisjoint(item.id for item in evaluate(current, baseline, absolute_threshold="90.00").alerts)


def test_resource_group_case_changes_do_not_create_new_alert_identity():
    first = evaluate(observed(group("120.00", "SHARED", subscription_id="sub-a"), group_by="resource_group"),
                     group_by="resource_group", deviation_threshold_percent=None)
    second = evaluate(observed(group("121.00", "shared", subscription_id="sub-a"), group_by="resource_group"),
                      group_by="resource_group", deviation_threshold_percent=None)
    assert first.alerts[0].id == second.alerts[0].id
    assert first.alerts[0].evidence_id != second.alerts[0].evidence_id


def test_changed_quality_changes_evidence_but_not_alert_identity():
    first = evaluate(observed(group("120.00")), deviation_threshold_percent=None)
    second = evaluate(observed(group("120.00"), data_status="partial", excluded_undated_count=1),
                      deviation_threshold_percent=None)
    assert first.alerts[0].id == second.alerts[0].id
    assert first.alerts[0].evidence_id != second.alerts[0].evidence_id


@pytest.mark.parametrize("changes", [
    {"period": PRIOR_PERIOD}, {"group_by": "project"}, {"tag_key": "environment"},
    {"groups": [group("100.00"), group("100.00")]},
    {"groups": [group("100.00", record_count=0)]},
    {"data_status": "empty"},
    {"totals": [{"currency": "EUR", "cost": "100.00", "record_count": 1}] * 2},
])
def test_incompatible_or_ambiguous_internal_summary_fails(changes):
    with pytest.raises(ValueError):
        evaluate(observed(group("100.00"), **changes), deviation_threshold_percent=None)


def test_baseline_is_required_exactly_when_deviation_rule_is_enabled():
    with pytest.raises(ValueError, match="Baseline"):
        evaluate(observed(group("100.00")))
    with pytest.raises(ValueError, match="Baseline"):
        evaluate(observed(group("100.00")), observed(group("90.00"), baseline=True), deviation_threshold_percent=None)


@pytest.mark.parametrize("change", [
    {"absolute_threshold": None, "deviation_threshold_percent": None},
    {"absolute_threshold": "0.00"}, {"absolute_threshold": "-1.00"},
    {"absolute_threshold": 100}, {"absolute_threshold": 0.1}, {"absolute_threshold": "NaN"},
    {"absolute_threshold": "Infinity"}, {"absolute_threshold": "1e2"}, {"absolute_threshold": "01.00"},
    {"absolute_threshold": "1.001"}, {"absolute_threshold": "1"}, {"absolute_threshold": "9" * 27 + ".00"},
    {"deviation_threshold_percent": "0.00"}, {"deviation_threshold_percent": "1000.01"},
    {"deviation_threshold_percent": 20}, {"deviation_threshold_percent": "-1.00"},
    {"min_absolute_increase": "0.00"}, {"min_absolute_increase": "-0.01"},
    {"currency": "eur"}, {"currency": "EURO"}, {"currency": " EUR"},
    {"group_by": "tag"}, {"group_by": "tenant"}, {"tag_key": "owner"},
    {"start_date": "2024-07-01"}, {"end_date": "2024-05-01"},
    {"start_date": "2023-06-30"}, {"start_date": "2024-02-30"},
    {"start_date": 1717200000}, {"start_date": "2024-06-01T00:00:00Z"},
    {"tenant_id": "tenant-b"}, {"baseline_period": PRIOR_PERIOD},
    {"current_cost": "0.00"}, {"start_date": "0001-01-01", "end_date": "0001-01-02"},
])
@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_invalid_body_is_rejected_before_reading_costs(api, change):
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, **change})
    assert response.status_code == 422, response.text
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_unclosed_utc_day_is_rejected_before_reading_costs(api):
    today = datetime.now(timezone.utc).date()
    response = call(api, "POST", PATH, headers=headers(), json={
        **BODY, "start_date": today.isoformat(), "end_date": (today + timedelta(days=1)).isoformat(),
    })
    assert response.status_code == 422, response.text
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("group_by", ["subscription", "resource_group", "service", "project"])
def test_api_uses_authorized_tenant_and_exact_equal_periods(api, group_by):
    current = observed(group("120.00"), group_by=group_by)
    baseline = observed(group("100.00"), baseline=True, group_by=group_by)
    api.spies["fetch_billing_summary"].side_effect = [current.model_dump(mode="json"), baseline.model_dump(mode="json")]
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, "group_by": group_by})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["definition"] == {**BODY, "group_by": group_by, "min_absolute_increase": "0.01"}
    assert result["current_period"] == {"start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC"}
    assert result["baseline_period"] == PRIOR_PERIOD
    assert result["alerts"][0]["current_cost"] == "120.00"
    assert result["alerts"][0]["cause_status"] == "not_established"
    assert api.spies["fetch_billing_summary"].call_args_list == [
        expected_call("tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1), group_by=group_by, tag_key=None),
        expected_call("tenant-a", start_date=date(2024, 5, 2), end_date=date(2024, 6, 1), group_by=group_by, tag_key=None),
    ]


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_absolute_only_does_not_read_a_baseline(api):
    api.spies["fetch_billing_summary"].return_value = observed(group("120.00")).model_dump(mode="json")
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, "deviation_threshold_percent": None})
    assert response.status_code == 200, response.text
    assert response.json()["baseline_quality"] is None
    api.spies["fetch_billing_summary"].assert_called_once()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("authorization,tenant,expected", [(False, "tenant-a", 401), (True, "tenant-b", 403), (True, None, 400)])
def test_api_auth_and_membership_precede_costs(api, authorization, tenant, expected):
    response = call(api, "POST", PATH, headers=headers(tenant=tenant) if authorization else [], json=BODY)
    assert response.status_code == expected
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("overlap_period", ["current", "baseline"])
def test_ambiguous_source_in_either_period_never_returns_amounts(api, overlap_period):
    api.spies["fetch_billing_summary"].side_effect = (
        AmbiguousCostSource() if overlap_period == "current" else
        [observed(group("120.00")).model_dump(mode="json"), AmbiguousCostSource()]
    )
    response = call(api, "POST", PATH, headers=headers(), json=BODY)
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_cost_summary_preserves_tenant_currency_period_and_credits(cost_reference, api):
    response = call(api, "POST", PATH, headers=headers(), json={
        **BODY, "absolute_threshold": "1.00", "deviation_threshold_percent": None,
    })
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["evaluation_status"] == "provisional"
    assert result["current_quality"] == {
        "data_status": "partial", "record_count": 5,
        "missing_dimension_count": 1, "excluded_undated_count": 1,
    }
    assert {item["group_value"]: item["current_cost"] for item in result["alerts"]} == {
        "Compute": "10.00", "compute": "2.00",
    }
    assert {item["currency"] for item in result["assessments"]} == {"EUR"}
    assert next(item for item in result["assessments"] if item["group_value"] == "Storage")["current_cost"] == "-1.01"


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_cost_previous_period_comparison_uses_observed_baseline(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        insert_cost(connection, "comparison-baseline", day="2024-05-10", cost="1.00", service="Compute")
        insert_cost(connection, "foreign-baseline", run="foreign", tenant="tenant-b",
                    day="2024-05-10", cost="9999.00", service="Compute")
    response = call(api, "POST", PATH, headers=headers(), json={**BODY, "absolute_threshold": None})
    assert response.status_code == 200, response.text
    result = response.json()
    [alert] = result["alerts"]
    assert alert["group_value"] == "Compute"
    assert alert["currency"] == "EUR"
    assert alert["current_cost"] == "10.00"
    assert alert["baseline_cost"] == "1.00"
    assert alert["delta_amount"] == "9.00"
    assert alert["deviation_percent"] == "900.00"
    assert alert["current_record_count"] == alert["baseline_record_count"] == 1
    assert alert["trigger_reasons"] == ["period_increase"]
    assert result["source"] == "billing_summary_v2"
    assert result["baseline_period"] == PRIOR_PERIOD
