"""Real Cockroach showback selection; opt-in database and independent cost ledger."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource
from app.services.showback import build_showback
from app.services.showback_repository import fetch_showback
from billing_support import billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import tenant_cockroach_database


START, END = date(2024, 6, 1), date(2024, 7, 1)


def fetch(database, dimension="owner", tenant="tenant-a", start=START, end=END):
    return fetch_showback(database, tenant, start_date=start, end_date=end, dimension=dimension)


def amounts(rows):
    return {(row["currency"], row["value"]): (row["cost"], row["record_count"]) for row in rows}


@pytest.mark.parametrize("dimension,expected,assigned,missing,invalid", [
    ("owner", {None: ("11.008", 5)}, "0.00", 5, 0),
    ("application", {None: ("11.008", 5)}, "0.00", 5, 0),
    ("cost_center", {"Finance": ("10.004", 1), "finance": ("2.004", 1),
                     "Unknown": ("0.005", 1), None: ("-1.005", 2)}, "12.008", 2, 1),
    ("project", {"Typed": ("10.004", 1), "Fallback": ("2.004", 1),
                 "Unknown": ("0.005", 1), None: ("-1.005", 2)}, "12.008", 2, 1),
])
def test_exact_completed_tenant_period_selection_and_missing_counts(
    cost_reference, dimension, expected, assigned, missing, invalid,
):
    rows, undated = fetch(cost_reference, dimension)
    currency_value = {"project": "Typed", "cost_center": "Finance"}.get(dimension)
    assert amounts(rows) == {
        **{("EUR", value): (Decimal(cost), count) for value, (cost, count) in expected.items()},
        ("GBP", currency_value): (Decimal("-0.004"), 1),
        ("USD", currency_value): (Decimal("9007199254740993.005"), 1),
    }
    assert undated == 1
    report = build_showback(rows, start_date=START, end_date=END, dimension=dimension, excluded_undated_count=undated)
    eur, gbp, usd = report.currencies
    assert (eur.total_cost, eur.assigned_cost, eur.record_count) == ("11.008", assigned, 5)
    assert (eur.unassigned_record_count, eur.assigned_record_count) == (missing + invalid, 5 - missing - invalid)
    assert [(item.reason, item.record_count) for item in eur.unassigned] == [("missing", missing), ("invalid", invalid)]
    assert eur.unassigned_cost == ("11.008" if dimension in {"owner", "application"} else "-1.00")
    assert gbp.total_cost == "-0.004"
    assert usd.total_cost == "9007199254740993.005"
    assert all(currency.reconciliation_difference == "0.00" for currency in report.currencies)
    assert report.data_status == "partial"


def test_foreign_tenant_and_empty_period_keep_independent_metadata(cost_reference):
    rows, undated = fetch(cost_reference, tenant="tenant-b")
    assert amounts(rows) == {("EUR", None): (Decimal("1000"), 1)}
    assert undated == 0
    rows, undated = fetch(cost_reference, tenant="absent-tenant")
    assert rows == [] and undated == 0
    rows, undated = fetch(cost_reference, start=date(2024, 8, 1), end=date(2024, 9, 1))
    assert rows == [] and undated == 1


def test_overlapping_completed_sources_fail_without_mutating_ledger(cost_reference):
    with cost_reference.engine.begin() as connection:
        insert_run(connection, "overlap")
        insert_cost(connection, "other-resource", run="overlap", day="2024-06-01", project="Different")
    with cost_reference.engine.connect() as connection:
        before = [dict(row) for row in connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings()]
    with pytest.raises(AmbiguousCostSource):
        fetch(cost_reference, dimension="project")
    with cost_reference.engine.connect() as connection:
        after = [dict(row) for row in connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings()]
    assert after == before


def test_json_nonstring_dimension_values_are_invalid_without_losing_cost(cost_reference):
    with cost_reference.engine.begin() as connection:
        for index, value in enumerate([123, True, None, ["Team"], {"unit": "Team"}]):
            insert_cost(connection, "invalid-tag-" + str(index), cost="0.125", tags={"owner": value})
    rows, undated = fetch(cost_reference)
    report = build_showback(rows, start_date=START, end_date=END, dimension="owner", excluded_undated_count=undated)
    eur = report.currencies[0]
    assert eur.total_cost == "11.633"
    assert eur.assigned_cost == "0.00"
    assert eur.unassigned_cost == "11.633"
    assert eur.groups == []
    assert [(item.reason, item.cost, item.record_count) for item in eur.unassigned] == [
        ("missing", "11.008", 5), ("invalid", "0.625", 5),
    ]
    assert eur.reconciliation_difference == "0.00"


def test_project_whitespace_falls_back_but_populated_typed_project_wins(cost_reference):
    with cost_reference.engine.begin() as connection:
        insert_cost(connection, "whitespace-project", cost="3.125", project="\t\r\n ", tags={"project": "Fallback"})
        insert_cost(connection, "typed-project", cost="4.125", project="Team", tags={"project": "Ignored"})
    rows, _ = fetch(cost_reference, dimension="project")
    actual = amounts(rows)
    assert actual[("EUR", "Fallback")] == (Decimal("5.129"), 2)
    assert actual[("EUR", "Team")] == (Decimal("4.125"), 1)
    assert not any(value == "Ignored" for _, value in actual)


def test_http_report_attributes_real_sql_team_and_application_costs(cost_reference):
    # Only the authenticated identity is substituted; routing, SQL, aggregation,
    # classification and serialization are real. Auth itself is covered in API tests.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.dependencies import get_active_tenant, get_database
    from app.api.routes.showback import router

    with cost_reference.engine.begin() as connection:
        insert_cost(connection, "team-charge", cost="3.125", tags={"owner": " Team.A ", "application": "AppA"})
        insert_cost(connection, "team-credit", cost="-1.005", tags={"owner": "Team.A", "application": "AppA"})
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_active_tenant] = lambda: "tenant-a"
    app.dependency_overrides[get_database] = lambda: cost_reference
    with TestClient(app) as client:
        for dimension, value in (("owner", "Team.A"), ("application", "AppA")):
            response = client.get(
                f"/billing/showback?start_date=2024-06-01&end_date=2024-07-01&dimension={dimension}"
            )
            assert response.status_code == 200, response.text
            eur = response.json()["currencies"][0]
            assert eur["groups"] == [{"value": value, "cost": "2.12", "record_count": 2}]
            assert (eur["assigned_cost"], eur["unassigned_cost"], eur["total_cost"]) == ("2.12", "11.008", "13.128")
            assert eur["reconciliation_difference"] == "0.00"
