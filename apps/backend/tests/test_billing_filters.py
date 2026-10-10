"""JUP-056: request boundaries plus real Cockroach filtered Decimal aggregation."""
from urllib.parse import urlencode

import pytest

from billing_support import billing_schema, cost_reference, insert_cost, insert_run, summary
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers


def path(**filters):
    return "/billing/summary?" + urlencode({
        "start_date": "2024-06-01", "end_date": "2024-07-01", "group_by": "service", **filters,
    })


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_filters_are_bound_canonicalized_and_echoed_without_changing_unfiltered_v2(api):
    api.spies["fetch_billing_summary"].return_value = summary()
    baseline = call(api, "GET", path(), headers=headers())
    assert baseline.json() == summary()
    selections = {
        "subscription_id": "sub-a", "service_name": "Compute", "project": " Typed ",
        "filter_tag_key": " __Cost,,,Centre__ ", "filter_tag_value": "Finance",
    }
    response = call(api, "GET", path(**selections), headers=headers())
    assert response.status_code == 200, response.text
    expected = {**selections, "filter_tag_key": "cost_center"}
    assert response.json() == {**summary(), "filters": expected}
    arguments = api.spies["fetch_billing_summary"].call_args
    assert arguments.args == ("tenant-a",)
    assert {key: arguments.kwargs[key] for key in expected} == expected
    single = call(api, "GET", path(service_name="Storage"), headers=headers())
    assert single.json()["filters"] == {"service_name": "Storage"}


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("filters", [
    {"subscription_id": ""}, {"service_name": "   "}, {"project": "a\x00b"},
    {"service_name": "Compute\n"}, {"filter_tag_key": "env"},
    {"filter_tag_value": "Prod"}, {"filter_tag_key": "---", "filter_tag_value": "Prod"},
    {"filter_tag_key": "env", "filter_tag_value": " "},
    {"filter_tag_key": "env\x7f", "filter_tag_value": "Prod"},
])
def test_invalid_filters_are_rejected_before_database_reads(api, filters):
    response = call(api, "GET", path(**filters), headers=headers())
    assert response.status_code == 422, response.text
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_account_filter_never_grants_foreign_tenant_access(api):
    response = call(api, "GET", path(subscription_id="sub-a"), headers=headers(tenant="tenant-b"))
    assert response.status_code == 403
    api.spies["fetch_billing_summary"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_combined_filters_preserve_exact_money_currencies_and_source_scope(cost_reference, api):
    filters = {
        "subscription_id": "sub-a", "service_name": "Compute", "project": "Typed",
        "filter_tag_key": "env", "filter_tag_value": "Prod",
    }
    response = call(api, "GET", path(**filters), headers=headers())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["filters"] == {**filters, "filter_tag_key": "environment"}
    assert result["totals"] == [
        {"currency": "EUR", "cost": "10.00", "record_count": 1},
        {"currency": "GBP", "cost": "0.00", "record_count": 1},
        {"currency": "USD", "cost": "9007199254740993.01", "record_count": 1},
    ]
    assert result["groups"] == [{**total, "subscription_id": None, "value": "Compute"} for total in result["totals"]]
    assert result["missing_dimension_count"] == 0
    assert result["excluded_undated_count"] == 1  # Existing tenant-global count.
    assert result["data_status"] == "partial"
    assert result["monthly_spend"] is None and result["currency"] is None
    account = call(api, "GET", path(subscription_id="sub-a"), headers=headers()).json()
    assert account["totals"][0] == {"currency": "EUR", "cost": "12.01", "record_count": 2}
    refund = call(api, "GET", path(service_name="Storage"), headers=headers()).json()
    assert refund["totals"] == [{"currency": "EUR", "cost": "-1.01", "record_count": 1}]
    # Every predicate participates in the intersection; no OR broadening.
    for key, value in {
        "subscription_id": "sub-b", "service_name": "compute", "project": "Fallback",
        "filter_tag_value": "prod", "filter_tag_key": "extra",
    }.items():
        unmatched = call(api, "GET", path(**{**filters, key: value}), headers=headers())
        assert unmatched.status_code == 200, unmatched.text
        assert unmatched.json()["totals"] == []
        assert unmatched.json()["groups"] == []
        assert unmatched.json()["monthly_spend"] is None


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_project_fallback_and_filtering_by_a_different_tag_than_grouping(cost_reference, api):
    response = call(api, "GET", path(
        group_by="tag", tag_key="org", project="Fallback", filter_tag_key="env", filter_tag_value="prod",
    ), headers=headers())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["tag_key"] == "organization"
    assert result["totals"] == [{"currency": "EUR", "cost": "2.00", "record_count": 1}]
    assert result["groups"] == [{"currency": "EUR", "cost": "2.00", "record_count": 1,
                                 "subscription_id": None, "value": "team"}]
    # Typed project wins over project tag on rows a/f/g.
    assert call(api, "GET", path(project="Ignored"), headers=headers()).json()["totals"] == []


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_nonmatching_and_sql_metacharacters_never_widen_filter_scope(cost_reference, api):
    for selection in ({"service_name": "' OR 1=1--"}, {"project": "unknown"}, {"subscription_id": "missing"}):
        response = call(api, "GET", path(**selection), headers=headers())
        assert response.status_code == 200, response.text
        assert response.json()["totals"] == []
    # A valid filter and shared subscription still see only the authorized tenant.
    foreign = call(api, "GET", path(subscription_id="sub-a"), headers=headers("bob", "tenant-b"))
    assert foreign.status_code == 200, foreign.text
    assert foreign.json()["totals"] == [{"currency": "EUR", "cost": "1000.00", "record_count": 1}]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_filters_cannot_hide_overlapping_completed_sources(cost_reference, api):
    with api.db.engine.begin() as connection:
        insert_run(connection, "filtered-overlap")
        insert_cost(connection, "excluded-service", run="filtered-overlap", day="2024-06-01", service="Other")
    response = call(api, "GET", path(service_name="Compute"), headers=headers())
    assert response.status_code == 409, response.text
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
