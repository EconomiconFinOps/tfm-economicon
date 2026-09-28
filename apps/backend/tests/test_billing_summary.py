"""JUP-026 API Red plus opt-in real Cockroach aggregation acceptance."""
import pytest
from sqlalchemy import text

from billing_support import PERIOD, billing_schema, cost_reference, insert_cost, insert_run, summary
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_v2_response_keeps_exact_money_nulls_and_period(api):
    expected = summary(
        groups=[{"currency": item["currency"], "subscription_id": None, "value": None,
                 "cost": item["cost"], "record_count": item["record_count"]}
                for item in summary()["totals"]],
        missing_dimension_count=7,
    )
    api.spies["fetch_billing_summary"].return_value = expected
    response = call(api, "GET", "/billing/summary?start_date=2024-06-01&end_date=2024-07-01&group_by=service", headers=headers())
    assert response.status_code == 200, response.text
    assert response.json() == expected


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", [
    "start_date=2024-06-01", "start_date=2024-06-31&end_date=2024-07-01",
    "start_date=2024-07-01&end_date=2024-07-01", "group_by=invalid",
    "group_by=tag", "group_by=tag&tag_key=%20", "group_by=service&tag_key=environment",
])
def test_invalid_selection_is_422_before_billing_read(api, query):
    response = call(api, "GET", "/billing/summary?" + query, headers=headers())
    assert response.status_code == 422, response.text
    api.spies["fetch_billing_summary"].assert_not_called()


# Explicit expected buckets, independent of production SQL and normalizers.
BUCKETS = {
    "subscription": [("sub-a", "sub-a", "10.01", 2), ("sub-b", "sub-b", "-1.00", 3)],
    "resource_group": [("sub-a", "Shared", "10.01", 2), ("sub-b", "Shared", "-1.01", 1),
                       ("sub-b", "Unknown", "0.01", 1), ("sub-b", None, "0.00", 1)],
    "service": [(None, "Compute", "10.00", 1), (None, "Storage", "-1.01", 1),
                (None, "Unknown", "0.01", 1), (None, "compute", "0.00", 1), (None, None, "0.00", 1)],
    "project": [(None, "Fallback", "0.00", 1), (None, "Typed", "10.00", 1),
                (None, "Unknown", "0.01", 1), (None, None, "-1.01", 2)],
    "tag": [(None, "Prod", "10.00", 1), (None, "Unknown", "0.01", 1),
            (None, "prod", "0.00", 1), (None, None, "-1.01", 2)],
}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
@pytest.mark.parametrize("group_by", list(BUCKETS))
def test_scoped_sql_reference_for_each_dimension(cost_reference, api, group_by):
    query = "start_date=2024-06-01&end_date=2024-07-01&group_by=" + group_by
    if group_by == "tag":
        query += "&tag_key=environment"
    response = call(api, "GET", "/billing/summary?" + query, headers=headers())
    assert response.status_code == 200, response.text
    groups = [{"currency": "EUR", "subscription_id": sub, "value": value, "cost": cost, "record_count": count}
              for sub, value, cost, count in BUCKETS[group_by]]
    value = {"subscription": "sub-a", "resource_group": "Shared", "service": "Compute", "project": "Typed", "tag": "Prod"}[group_by]
    for currency, cost in [("GBP", "0.00"), ("USD", "9007199254740993.01")]:
        groups.append({"currency": currency, "subscription_id": "sub-a" if group_by in {"subscription", "resource_group"} else None,
                       "value": value, "cost": cost, "record_count": 1})
    assert response.json() == summary(
        group_by=group_by, tag_key="environment" if group_by == "tag" else None, groups=groups,
        missing_dimension_count={"subscription": 0, "resource_group": 1, "service": 1, "project": 2, "tag": 2}[group_by],
    )


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_empty_partial_zero_and_literal_unknown_tag(cost_reference, api):
    path = "/billing/summary?start_date=2024-08-01&end_date=2024-09-01&group_by=service"
    response = call(api, "GET", path, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json() == summary(period={**PERIOD, "start_date": "2024-08-01", "end_date": "2024-09-01"},
                                      totals=[], missing_dimension_count=0)
    with api.db.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records WHERE usage_date IS NULL"))
    assert call(api, "GET", path, headers=headers()).json() == summary(
        period={**PERIOD, "start_date": "2024-08-01", "end_date": "2024-09-01"},
        totals=[], data_status="empty", missing_dimension_count=0, excluded_undated_count=0)
    with api.db.engine.begin() as connection:
        insert_cost(connection, "zero", day="2024-08-01", cost="0")
    zero = call(api, "GET", path, headers=headers()).json()
    assert zero == summary(period={**PERIOD, "start_date": "2024-08-01", "end_date": "2024-09-01"},
        totals=[{"currency": "EUR", "cost": "0.00", "record_count": 1}],
        groups=[{"currency": "EUR", "subscription_id": None, "value": None, "cost": "0.00", "record_count": 1}],
        excluded_undated_count=0, monthly_spend="0.00", currency="EUR")
    unknown = call(api, "GET", path.replace("group_by=service", "group_by=tag&tag_key=x%27%20OR%201%3D1--"), headers=headers())
    assert unknown.status_code == 200, unknown.text
    assert unknown.json() == {**zero, "group_by": "tag", "tag_key": "x' OR 1=1--"}
    available = call(api, "GET", path.replace("group_by=service", "group_by=subscription"), headers=headers()).json()
    assert available["data_status"] == "available"
    assert available["missing_dimension_count"] == 0


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_overlapping_completed_sources_conflict_without_writes_or_amounts(cost_reference, api):
    with api.db.engine.begin() as connection:
        insert_run(connection, "overlapping-source")
        insert_cost(connection, "disjoint-resource", run="overlapping-source", day="2024-06-01", service="Different")
    with api.db.engine.connect() as connection:
        before = [dict(row) for row in connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings()]
    response = call(api, "GET", "/billing/summary?start_date=2024-06-01&end_date=2024-07-01", headers=headers())
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "ambiguous_cost_source"
    assert not {"totals", "groups", "monthly_spend"}.intersection(response.json())
    assert "overlapping-source" not in response.text and "disjoint-resource" not in response.text
    with api.db.engine.connect() as connection:
        assert [dict(row) for row in connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings()] == before
