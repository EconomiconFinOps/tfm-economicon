"""JUP-028: independent amounts, real scoped SQL and authenticated route tests."""
from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource
from billing_support import billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging


PATH = "/billing/unallocated-cost?start_date=2024-06-01&end_date=2024-07-01"
TAGS = {
    "owner": "platform-team", "environment": "prod", "application": "economicon",
    "cost_center": "cc-jupiter", "project": "jupiter",
}
REQUIRED_TAGS = ["owner", "environment", "application", "cost_center", "project"]


def without(*keys):
    return {key: value for key, value in TAGS.items() if key not in keys}


@pytest.fixture
def unallocated_reference(cost_reference):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        rows = [
            ("assigned", "80", "EUR", TAGS),
            ("owner", "10", "EUR", without("owner")),
            ("classification", "6", "EUR", without("application")),
            ("both", "4", "EUR", without("owner", "cost_center", "project")),
            ("assigned-adjustment", "-30", "EUR", TAGS),
            ("owner-adjustment", "-3", "EUR", without("owner")),
            ("classification-adjustment", "-2", "EUR", without("application")),
            ("both-adjustment", "-1", "EUR", without("owner", "cost_center", "project")),
            ("both-zero", "0", "EUR", without("owner", "cost_center", "project")),
            ("large", "9007199254740993.004", "USD", TAGS),
            ("tiny", "0.006", "USD", without("owner")),
            ("assigned-negative-only", "-2", "GBP", TAGS),
            ("unallocated-negative-only", "-18", "GBP", without("owner")),
            ("assigned-zero-only", "0", "JPY", TAGS),
            ("unallocated-zero-only", "0", "JPY", without("owner")),
        ]
        for identifier, cost, currency, tags in rows:
            # The first and last included days establish a half-open interval.
            day = "2024-06-01" if identifier == "assigned" else "2024-06-30"
            insert_cost(connection, identifier, cost=cost, currency=currency, tags=tags, day=day)
        for identifier, changes in [
            ("foreign", {"run": "foreign", "tenant": "tenant-b"}),
            ("wrong-record-tenant", {"tenant": "tenant-b"}),
            ("wrong-run-tenant", {"run": "foreign"}),
            ("wrong-subscription", {"subscription": "sub-b"}),
            ("unfinished", {"run": "running"}),
            ("failed", {"run": "failed"}),
            ("before", {"day": "2024-05-31"}),
            ("end", {"day": "2024-07-01"}),
            ("outside-overlap", {"run": "outside", "day": "2024-07-01"}),
            ("undated", {"day": None}),
        ]:
            insert_cost(connection, identifier, cost="9999999", **changes)
    return cost_reference


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_exclusive_groups_signed_costs_currencies_and_scoped_sources(unallocated_reference, api):
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == 1
    assert body["policy_version"] == "economicon-minimum-v1"
    assert body["detection_basis"] == "observed_required_tags"
    assert body["allocation_status"] == "not_evaluated"
    assert body["required_tags"] == REQUIRED_TAGS
    assert body["period"] == {
        "start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC",
    }
    assert body["data_status"] == "partial" and body["excluded_undated_count"] == 1
    assert [row["currency"] for row in body["currencies"]] == ["EUR", "GBP", "JPY", "USD"]
    by_currency = {row["currency"]: row for row in body["currencies"]}
    assert by_currency["EUR"] == {
        "currency": "EUR", "record_count": 9, "candidate_record_count": 7,
        "positive_cost": "100.00", "complete_metadata_cost": "80.00", "candidate_cost": "20.00",
        "negative_adjustments": "-36.00", "complete_metadata_negative_adjustments": "-30.00",
        "candidate_negative_adjustments": "-6.00", "net_cost": "64.00",
        "complete_metadata_net_cost": "50.00", "candidate_net_cost": "14.00",
        "candidate_percent": "20.00", "no_positive_cost_reason": None,
        "groups": [
            {"missing_or_invalid_tags": ["owner"], "reason": "no_owner", "record_count": 2,
             "positive_cost": "10.00", "negative_adjustments": "-3.00", "net_cost": "7.00"},
            {"missing_or_invalid_tags": ["application"], "reason": "unclassified", "record_count": 2,
             "positive_cost": "6.00", "negative_adjustments": "-2.00", "net_cost": "4.00"},
            {"missing_or_invalid_tags": ["owner", "cost_center", "project"],
             "reason": "no_owner_and_unclassified", "record_count": 3,
             "positive_cost": "4.00", "negative_adjustments": "-1.00", "net_cost": "3.00"},
        ],
    }
    # The owner-only group retains a valid cost_center. It is a metadata
    # candidate, not proof that the separate financial allocation rules failed.
    assert "unallocated_cost" not in by_currency["EUR"]
    usd = by_currency["USD"]
    assert usd["positive_cost"] == "9007199254740993.01"
    assert usd["complete_metadata_cost"] == "9007199254740993.00"
    assert usd["candidate_cost"] == "0.01" and usd["candidate_percent"] == "0.00"
    assert usd["groups"][0]["positive_cost"] == "0.01"
    gbp = by_currency["GBP"]
    assert gbp["positive_cost"] == "0.00" and gbp["candidate_cost"] == "0.00"
    assert gbp["negative_adjustments"] == "-20.00"
    assert gbp["complete_metadata_negative_adjustments"] == "-2.00"
    assert gbp["candidate_negative_adjustments"] == "-18.00"
    assert gbp["net_cost"] == "-20.00" and gbp["candidate_net_cost"] == "-18.00"
    assert gbp["candidate_percent"] is None
    assert gbp["no_positive_cost_reason"] == "negative_adjustments_only"
    jpy = by_currency["JPY"]
    assert jpy["record_count"] == 2 and jpy["candidate_record_count"] == 1
    assert jpy["positive_cost"] == "0.00" and jpy["net_cost"] == "0.00"
    assert jpy["candidate_percent"] is None
    assert jpy["no_positive_cost_reason"] == "zero_cost_only"
    assert jpy["groups"][0]["record_count"] == 1


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_tag_values_cannot_become_valid_through_coercion_or_fallback(cost_reference, api):
    invalid_owner_values = [
        None, "", " \t\n", "unknown", " N/A ", "null", "None", "True", "False",
        "undefined", "unassigned", "-", False, True, 123, {"id": "team"}, ["team"],
        "Full Name", "x" * 129,
    ]
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        for index, value in enumerate(invalid_owner_values):
            insert_cost(connection, f"invalid-owner-{index}", cost="1", tags={**TAGS, "owner": value})
        # An organization is not an owner, nor is a typed project a required tag.
        insert_cost(connection, "organization", cost="1", tags={**without("owner"), "organization": "platform-team"})
        insert_cost(connection, "typed-project", cost="1", project="jupiter", tags=without("project"))
        for key in ("environment", "application", "cost_center", "project"):
            insert_cost(connection, f"null-{key}", cost="1", tags={**TAGS, key: None})
        insert_cost(connection, "invalid-environment", cost="1", tags={**TAGS, "environment": "production-typo"})
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "available" and body["excluded_undated_count"] == 0
    [row] = body["currencies"]
    assert row["record_count"] == 26 and row["candidate_record_count"] == 26
    assert row["complete_metadata_cost"] == "0.00" and row["candidate_cost"] == "26.00"
    assert row["candidate_percent"] == "100.00"
    assert [(group["missing_or_invalid_tags"], group["record_count"]) for group in row["groups"]] == [
        (["owner"], 20), (["environment"], 2), (["application"], 1),
        (["cost_center"], 1), (["project"], 2),
    ]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_accepted_environment_aliases_and_valid_identifier_boundaries(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        for index, environment in enumerate(("dev", " Development ", "test", "testing", "STAGING", "stage", "prod", " Production ")):
            insert_cost(connection, f"alias-{index}", cost="1", tags={
                **TAGS, "environment": environment, "owner": "\tplatform-team\n",
                "application": "app.v1:test_blue-green", "project": "x" * 128,
            })
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    [row] = response.json()["currencies"]
    assert row["complete_metadata_cost"] == "8.00" and row["candidate_cost"] == "0.00"
    assert row["candidate_percent"] == "0.00"
    assert row["candidate_record_count"] == 0 and row["groups"] == []


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_percent_uses_unrounded_positive_cost_and_half_up_at_output(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_cost(connection, "assigned", cost="0.006", tags=TAGS)
        insert_cost(connection, "unallocated", cost="0.004", tags=without("owner", "application"))
        insert_cost(connection, "adjustment", cost="-0.005", tags=without("owner", "application"))
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    [row] = response.json()["currencies"]
    assert row["positive_cost"] == "0.01" and row["complete_metadata_cost"] == "0.01"
    assert row["candidate_cost"] == "0.00" and row["candidate_percent"] == "40.00"
    assert row["negative_adjustments"] == "-0.01" and row["net_cost"] == "0.01"
    assert row["candidate_net_cost"] == "0.00"
    assert row["groups"] == [{
        "missing_or_invalid_tags": ["owner", "application"], "reason": "no_owner_and_unclassified",
        "record_count": 2, "positive_cost": "0.00", "negative_adjustments": "-0.01", "net_cost": "0.00",
    }]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_displayed_complement_matches_tag_coverage_even_when_net_cost_is_zero(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_cost(connection, "complete", cost="19999", tags=TAGS)
        insert_cost(connection, "candidate", cost="1", tags=without("owner"))
        insert_cost(connection, "adjustment", cost="-20000", tags=TAGS)
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    [row] = response.json()["currencies"]
    assert row["positive_cost"] == "20000.00"
    assert row["complete_metadata_cost"] == "19999.00" and row["candidate_cost"] == "1.00"
    # JUP-017 displays the complement of its rounded 99.995% -> 100.00%.
    # Independently rounding the candidate's exact 0.005% would yield 0.01%.
    assert row["candidate_percent"] == "0.00"
    assert row["negative_adjustments"] == "-20000.00" and row["net_cost"] == "0.00"
    assert row["no_positive_cost_reason"] is None


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_empty_and_undated_only_periods_do_not_claim_zero_candidate_cost(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
    empty = call(api, "GET", PATH, headers=headers())
    assert empty.status_code == 200, empty.text
    assert empty.json()["currencies"] == [] and empty.json()["data_status"] == "empty"
    assert empty.json()["excluded_undated_count"] == 0
    with cost_reference.engine.begin() as connection:
        insert_cost(connection, "undated", day=None, tags=TAGS)
    partial = call(api, "GET", PATH, headers=headers())
    assert partial.status_code == 200, partial.text
    assert partial.json()["currencies"] == [] and partial.json()["data_status"] == "partial"
    assert partial.json()["excluded_undated_count"] == 1


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_overlap_rejected_even_for_complete_tags_in_different_currencies(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_run(connection, "extra")
        insert_cost(connection, "one", tags=TAGS, currency="EUR")
        insert_cost(connection, "overlap", run="extra", tags=TAGS, currency="USD")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_distinct_days_and_subscriptions_are_not_overlapping_sources(cost_reference, api):
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        insert_run(connection, "other-day")
        insert_cost(connection, "one", cost="1", tags=TAGS)
        insert_cost(connection, "other-subscription", run="run-b", subscription="sub-b", cost="2")
        insert_cost(connection, "other-day", run="other-day", day="2024-06-16", cost="3")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    [row] = response.json()["currencies"]
    assert row["positive_cost"] == "6.00" and row["candidate_cost"] == "5.00"
    assert row["candidate_percent"] == "83.33"
    assert row["groups"] == [{
        "missing_or_invalid_tags": REQUIRED_TAGS, "reason": "no_owner_and_unclassified",
        "record_count": 2, "positive_cost": "5.00", "negative_adjustments": "0.00", "net_cost": "5.00",
    }]


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", [
    "", "start_date=2024-06-01", "end_date=2024-07-01",
    "start_date=&end_date=2024-07-01", "start_date=2024-06-01&end_date=",
    "start_date=2024-6-01&end_date=2024-07-01",
    "start_date=2024-06-01T00:00:00Z&end_date=2024-07-01",
    "start_date=2024-06-31&end_date=2024-07-01",
    "start_date=2024-06-01&end_date=2024-07-32",
    "start_date=2024-07-01&end_date=2024-07-01",
    "start_date=2024-07-02&end_date=2024-07-01",
])
def test_explicit_valid_interval_is_required_before_cost_sql(api, monkeypatch, query):
    spy = MagicMock()
    monkeypatch.setattr(api.db, "fetch_unallocated_cost", spy)
    response = call(api, "GET", "/billing/unallocated-cost?" + query, headers=headers())
    assert response.status_code == 422
    spy.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("auth,tenant,status", [
    (False, "tenant-a", 401), (True, "tenant-b", 403), (True, None, 400),
])
def test_authorization_and_membership_precede_cost_sql(api, monkeypatch, auth, tenant, status):
    spy = MagicMock()
    monkeypatch.setattr(api.db, "fetch_unallocated_cost", spy)
    response = call(api, "GET", PATH, headers=headers(tenant=tenant) if auth else [])
    assert response.status_code == status
    spy.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_route_passes_selected_tenant_dates_and_redacts_overlap_details(api, monkeypatch):
    # Explicit repository double: this tests route behavior, not the overlap SQL.
    spy = MagicMock(side_effect=AmbiguousCostSource("private-source-marker"))
    monkeypatch.setattr(api.db, "fetch_unallocated_cost", spy)
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
    spy.assert_called_once_with("tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1))
