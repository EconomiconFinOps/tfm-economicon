"""Real auth/membership; explicit aggregation double except opt-in Cockroach tests."""
from datetime import date

import pytest
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource
from billing_support import billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers, no_effects
from test_recommendations import source


PATH = "/billing/recommendations?start_date=2024-06-01&end_date=2024-07-01"


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_endpoint_uses_single_authorized_project_query_and_has_no_effects(api):
    api.spies["fetch_billing_summary"].return_value = source().model_dump(mode="json")
    response = call(api, "GET", PATH + "&tenant_id=tenant-b", headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == 1 and len(body["recommendations"]) == 3
    assert body["source"] == "azure_cost_records"
    api.spies["fetch_billing_summary"].assert_called_once_with(
        "tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1),
        group_by="project", tag_key=None,
    )
    no_effects(api, resource_reads=False)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("case,status", [("no_auth", 401), ("no_tenant", 400), ("foreign", 403), ("duplicate", 400)])
def test_unauthorized_scope_cannot_read_costs(api, case, status):
    selected = {"no_auth": [], "no_tenant": headers(tenant=None),
                "foreign": headers(tenant="tenant-b"),
                "duplicate": headers() + [("X-Tenant-Id", "tenant-b")]}[case]
    response = call(api, "GET", PATH, headers=selected)
    assert response.status_code == status
    no_effects(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", [
    "", "start_date=2024-06-01", "start_date=2024-06-31&end_date=2024-07-01",
    "start_date=2024-07-01&end_date=2024-07-01",
    "start_date=2024-07-02&end_date=2024-07-01",
    "start_date=2023-01-01&end_date=2024-01-03",
    "start_date=2024-6-1&end_date=2024-07-01",
])
def test_invalid_period_fails_before_aggregation(api, query):
    response = call(api, "GET", "/billing/recommendations?" + query, headers=headers())
    assert response.status_code == 422, response.text
    no_effects(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_source_conflict_returns_409_without_candidates_or_source_details(api):
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource("private-run-marker")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
    no_effects(api, resource_reads=False)


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_scoped_aggregation_preserves_fallback_credit_and_exclusions(cost_reference, api):
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "partial" and body["excluded_undated_count"] == 1
    assert body["missing_dimension_count"] == 2
    assert {(x["category"], x["scope"]["value"], x["observed_cost"]["currency"], x["observed_cost"]["amount"])
            for x in body["recommendations"]} == {
        ("tagging", None, "EUR", "-1.01"),
        ("investigation", "Typed", "EUR", "10.00"),
        ("investigation", "Typed", "USD", "9007199254740993.01"),
    }
    no_effects(api, resource_reads=False)


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_overlapping_sources_cannot_create_proposals(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        insert_run(connection, "overlap")
        insert_cost(connection, "overlap-record", run="overlap", day="2024-06-01")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409 and "recommendations" not in response.json()
    no_effects(api, resource_reads=False)


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_project_selection_combines_subscriptions_before_comparison(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_cost(connection, "alpha-a", cost="60", project="Alpha")
        insert_cost(connection, "alpha-b", run="run-b", subscription="sub-b", cost="60", project="Alpha")
        insert_cost(connection, "beta", cost="100", project="Beta")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    [candidate] = response.json()["recommendations"]
    assert candidate["scope"] == {"dimension": "project", "value": "Alpha"}
    assert candidate["observed_cost"] == {"amount": "120.00", "currency": "EUR", "record_count": 2}
    no_effects(api, resource_reads=False)
