"""Independent expected amounts, real scoped SQL plus authenticated route tests."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from billing_support import billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

PATH = "/billing/tag-coverage?start_date=2024-06-01&end_date=2024-07-01"
CONTROL = json.loads((Path(__file__).parent / "fixtures/tag_coverage.json").read_text())
TAGS = CONTROL["valid_tags"]


@pytest.fixture
def coverage_reference(cost_reference):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        for row in CONTROL["records"]:
            tags = TAGS if row["complete"] else {k: v for k, v in TAGS.items() if k not in {"owner", "application"}}
            insert_cost(connection, row["id"], cost=row["cost"], currency=row["currency"], tags=tags)
        insert_cost(connection, "foreign", run="foreign", tenant="tenant-b", cost="9999999", tags=TAGS)
        insert_cost(connection, "wrong-tenant", run="foreign", cost="9999999", tags=TAGS)
        insert_cost(connection, "wrong-subscription", subscription="sub-b", cost="9999999", tags=TAGS)
        insert_cost(connection, "unfinished", run="running", cost="9999999", tags=TAGS)
        insert_cost(connection, "failed", run="failed", cost="9999999", tags=TAGS)
        insert_cost(connection, "before", day="2024-05-31", cost="9999999", tags=TAGS)
        insert_cost(connection, "end", day="2024-07-01", cost="9999999", tags=TAGS)
        insert_cost(connection, "undated", day=None, cost="9999999", tags=TAGS)
    return cost_reference


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_positive_weighting_adjustments_currencies_and_isolation(coverage_reference, api):
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["required_tags"] == ["owner", "environment", "application", "cost_center", "project"]
    assert body["policy_version"] == "economicon-minimum-v1"
    assert body["data_status"] == "partial" and body["excluded_undated_count"] == 1
    by_currency = {row["currency"]: row for row in body["currencies"]}
    eur = by_currency["EUR"]
    assert {key: eur[key] for key in ("positive_cost", "compliant_cost", "noncompliant_cost",
        "negative_adjustments", "net_cost", "compliant_net_cost", "noncompliant_net_cost",
        "compliant_percent", "noncompliant_percent")} == {
        "positive_cost": "100.00", "compliant_cost": "80.00", "noncompliant_cost": "20.00",
        "negative_adjustments": "-30.00", "net_cost": "70.00", "compliant_net_cost": "50.00",
        "noncompliant_net_cost": "20.00", "compliant_percent": "80.00", "noncompliant_percent": "20.00",
    }
    assert eur["record_count"] == 3 and eur["compliant_record_count"] == 2
    assert eur["missing_or_invalid_tag_counts"] == {"owner": 1, "application": 1,
        "environment": 0, "project": 0, "cost_center": 0}
    assert by_currency["USD"]["compliant_cost"] == "9007199254740993.01"
    assert by_currency["USD"]["compliant_percent"] == "100.00"
    assert by_currency["GBP"]["compliant_percent"] is None
    assert by_currency["GBP"]["negative_adjustments"] == "-20.00"
    assert by_currency["GBP"]["no_positive_cost_reason"] == "negative_adjustments_only"
    assert by_currency["JPY"]["compliant_percent"] is None
    assert by_currency["JPY"]["no_positive_cost_reason"] == "zero_cost_only"


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
@pytest.mark.parametrize("key,value", [
    ("owner", None), ("owner", ""), ("owner", " \t\n"), ("owner", "unknown"),
    ("owner", "N/A"), ("owner", "null"), ("owner", "undefined"), ("owner", "unassigned"),
    ("owner", "-"), ("owner", False), ("owner", 123), ("owner", {"id": "team"}),
    ("owner", "Full Name"), ("owner", "x"*129), ("environment", "trey"),
    ("application", None), ("project", None), ("cost_center", None),
])
def test_invalid_values_invalidate_entire_cost(cost_reference, api, key, value):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        tags = {**TAGS, key: value, "organization": "platform-team", "extra": "extra"}
        insert_cost(connection, "invalid", cost="100", tags=tags)
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    row = response.json()["currencies"][0]
    assert row["compliant_percent"] == "0.00"
    assert row["noncompliant_cost"] == "100.00"
    assert row["missing_or_invalid_tag_counts"][key] == 1


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_aliases_empty_period_and_net_zero(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_cost(connection, "valid", cost="0.006", tags={**TAGS, "environment": " Production ", "owner": "\tplatform-team\n"})
        insert_cost(connection, "partial", cost="0.004", tags={"project": "jupiter", "cost_center": "cc-jupiter", "environment": "prod"})
        insert_cost(connection, "adjustment", cost="-0.01")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    row = response.json()["currencies"][0]
    assert row["net_cost"] == "0.00"
    assert row["positive_cost"] == "0.01"
    assert row["compliant_percent"] == "60.00" and row["noncompliant_percent"] == "40.00"
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
    empty = call(api, "GET", PATH, headers=headers()).json()
    assert empty["currencies"] == [] and empty["data_status"] == "empty"


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_overlapping_sources_rejected_without_amounts(coverage_reference, api):
    with coverage_reference.engine.begin() as connection:
        insert_run(connection, "extra")
        insert_cost(connection, "overlap", run="extra")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_normalized_null_and_boolean_markers_cannot_become_valid_owner(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        # Existing source normalization may stringify null/boolean tag values.
        for marker in ("None", "True", "False"):
            insert_cost(connection, marker, cost="1", tags={**TAGS, "owner": marker})
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    row = response.json()["currencies"][0]
    assert row["compliant_percent"] == "0.00" and row["noncompliant_cost"] == "3.00"
    assert row["missing_or_invalid_tag_counts"]["owner"] == 3


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", ["start_date=2024-06-01", "end_date=2024-07-01",
    "start_date=2024-06-31&end_date=2024-07-01",
    "start_date=2024-07-01&end_date=2024-07-01",
    "start_date=2024-07-02&end_date=2024-07-01"])
def test_bad_period_is_rejected_before_sql(api, monkeypatch, query):
    spy = MagicMock()
    monkeypatch.setattr(api.db, "fetch_tag_coverage", spy)
    response = call(api, "GET", "/billing/tag-coverage?"+query, headers=headers())
    assert response.status_code == 422
    spy.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("auth,tenant,status", [
    (False, "tenant-a", 401), (True, "tenant-b", 403), (True, None, 400),
])
def test_auth_and_membership_precede_sql(api, monkeypatch, auth, tenant, status):
    spy = MagicMock()
    monkeypatch.setattr(api.db, "fetch_tag_coverage", spy)
    response = call(api, "GET", PATH, headers=headers(tenant=tenant) if auth else [])
    assert response.status_code == status
    spy.assert_not_called()
