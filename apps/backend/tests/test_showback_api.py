"""Showback HTTP contract; real auth/membership, double only at the cost read."""
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes import showback as route
from app.core.security import create_access_token
from app.schemas.billing import AmbiguousCostSource
from conftest import SYNTHETIC_ENV
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database


PERIOD_QUERY = "start_date=2024-06-01&end_date=2024-07-01"


def headers(user="alice", tenant="tenant-a"):
    token = create_access_token(user, SYNTHETIC_ENV["AUTH_SECRET_KEY"], 5)
    return {"Authorization": "Bearer " + token, **({"X-Tenant-Id": tenant} if tenant else {})}


@pytest.fixture
def showback_api(populated_database, monkeypatch):
    app = FastAPI()
    app.state.database = populated_database
    app.include_router(route.router)
    read = MagicMock(return_value=([], 0))
    monkeypatch.setattr(route, "fetch_showback", read)
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, read=read, db=populated_database)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", [
    "start_date=2024-06-01", "end_date=2024-07-01",
    "start_date=0&end_date=2024-07-01", "start_date=20240601&end_date=2024-07-01",
    "start_date=2024-06-31&end_date=2024-07-01",
    "start_date=2024-07-01&end_date=2024-07-01",
    "start_date=2024-07-02&end_date=2024-07-01",
    PERIOD_QUERY + "&dimension=organization", PERIOD_QUERY + "&dimension=",
    PERIOD_QUERY + "&dimension=owner%27%20OR%201%3D1--",
])
def test_invalid_period_or_dimension_rejected_before_cost_read(showback_api, query):
    response = showback_api.client.get("/billing/showback?" + query, headers=headers())
    assert response.status_code == 422, response.text
    showback_api.read.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("dimension", ["owner", "project", "application", "cost_center"])
def test_each_dimension_reaches_the_authorized_tenant(showback_api, dimension):
    response = showback_api.client.get(
        "/billing/showback?" + PERIOD_QUERY + "&dimension=" + dimension + "&tenant_id=tenant-b",
        headers=headers(),
    )
    assert response.status_code == 200, response.text
    assert response.json()["dimension"] == dimension
    assert response.json()["currencies"] == []
    assert response.json()["data_status"] == "empty"
    showback_api.read.assert_called_once_with(
        showback_api.db, "tenant-a", start_date=date(2024, 6, 1),
        end_date=date(2024, 7, 1), dimension=dimension,
    )


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("user,tenant,status", [
    (None, "tenant-a", 401), ("unknown-user", "tenant-a", 401),
    ("alice", None, 400), ("alice", "tenant-b", 403),
    ("alice", "nonexistent", 403), ("admin-alone", "tenant-a", 403),
])
def test_bearer_and_tenant_membership_required_before_cost_read(showback_api, user, tenant, status):
    response = showback_api.client.get(
        "/billing/showback?" + PERIOD_QUERY,
        headers=headers(user, tenant) if user else {},
    )
    assert response.status_code == status, response.text
    showback_api.read.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_default_period_is_current_utc_month_across_year_boundary(showback_api, monkeypatch):
    class DecemberClock:
        @staticmethod
        def now(tz):
            assert tz is timezone.utc
            return datetime(2024, 12, 31, 23, 59, tzinfo=timezone.utc)

    monkeypatch.setattr(route, "datetime", DecemberClock)
    response = showback_api.client.get("/billing/showback", headers=headers())
    assert response.status_code == 200, response.text
    assert response.json()["period"] == {
        "start_date": "2024-12-01", "end_date": "2025-01-01", "timezone": "UTC",
    }
    showback_api.read.assert_called_once_with(
        showback_api.db, "tenant-a", start_date=date(2024, 12, 1),
        end_date=date(2025, 1, 1), dimension="owner",
    )


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_ambiguous_source_returns_409_without_costs_or_internal_details(showback_api):
    showback_api.read.side_effect = AmbiguousCostSource("private-ingestion-id")
    response = showback_api.client.get("/billing/showback?" + PERIOD_QUERY, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
    assert "private-ingestion-id" not in response.text


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_exact_money_and_explicit_unassigned_buckets_survive_http_serialization(showback_api):
    showback_api.read.return_value = ([
        {"currency": "USD", "value": "team-a", "cost": Decimal("9007199254740993.005"), "record_count": 1},
        {"currency": "EUR", "value": "FinOps", "cost": Decimal("10.004"), "record_count": 1},
        {"currency": "EUR", "value": None, "cost": Decimal("-1.005"), "record_count": 1},
        {"currency": "EUR", "value": "Unknown", "cost": Decimal("0.005"), "record_count": 1},
    ], 2)
    response = showback_api.client.get("/billing/showback?" + PERIOD_QUERY, headers=headers())
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["contract_version"] == 1
    assert report["policy_version"] == "jup027-provisional-syntax-v1-pending-jup015"
    assert report["catalog_status"] == "not_provided"
    assert report["organizationally_valid"] is None
    assert report["dimension"] == "owner"
    assert report["period"] == {"start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC"}
    assert report["excluded_undated_count"] == 2
    assert report["data_status"] == "partial"
    assert report["currencies"] == [
        {
            "currency": "EUR", "total_cost": "9.004", "assigned_cost": "10.004",
            "unassigned_cost": "-1.00", "record_count": 3,
            "assigned_record_count": 1, "unassigned_record_count": 2,
            "groups": [{"value": "FinOps", "cost": "10.004", "record_count": 1}],
            "unassigned": [
                {"reason": "missing", "cost": "-1.005", "record_count": 1},
                {"reason": "invalid", "cost": "0.005", "record_count": 1},
            ],
            "reconciliation_difference": "0.00",
        },
        {
            "currency": "USD", "total_cost": "9007199254740993.005", "assigned_cost": "9007199254740993.005",
            "unassigned_cost": "0.00", "record_count": 1,
            "assigned_record_count": 1, "unassigned_record_count": 0,
            "groups": [{"value": "team-a", "cost": "9007199254740993.005", "record_count": 1}],
            "unassigned": [
                {"reason": "missing", "cost": "0.00", "record_count": 0},
                {"reason": "invalid", "cost": "0.00", "record_count": 0},
            ],
            "reconciliation_difference": "0.00",
        },
    ]
