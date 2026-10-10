"""JUP-031 API: real bearer/membership checks; explicit cost-history read double.

These tests exercise the mounted application and real forecasting service. They
do not claim to exercise Azure ingestion or the Cockroach history query.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, call as mock_call

import pytest

from app.schemas.billing import AmbiguousCostSource
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers, no_effects


pytestmark = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
PATH = "/billing/forecast?start_date=2023-01-01&end_date=2024-01-01"


@pytest.fixture
def history_read(monkeypatch):
    from app.api.routes import forecast

    class JanuaryClock(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz == timezone.utc
            return datetime(2024, 1, 15, tzinfo=timezone.utc)

    monkeypatch.setattr(forecast, "datetime", JanuaryClock)
    reader = MagicMock(return_value={
        "rows": [], "excluded_undated_count": 0, "missing_dimension_count": 0,
    })
    monkeypatch.setattr(forecast, "fetch_forecast_history", reader)
    return reader


@pytest.mark.parametrize("kind,expected", [
    ("missing_token", 401), ("invalid_token", 401), ("unknown_user", 401),
    ("missing_tenant", 400), ("duplicate_tenant", 400),
    ("foreign_tenant", 403), ("admin_without_membership", 403),
])
def test_authentication_and_membership_precede_history_reads(api, history_read, kind, expected):
    selected_headers = {
        "missing_token": [],
        "invalid_token": [("Authorization", "Bearer invalid"), ("X-Tenant-Id", "tenant-a")],
        "unknown_user": headers(user="not-a-user"),
        "missing_tenant": headers(tenant=None),
        "duplicate_tenant": headers() + [("X-Tenant-Id", "tenant-b")],
        "foreign_tenant": headers(tenant="tenant-b"),
        "admin_without_membership": headers(user="admin-alone"),
    }[kind]
    response = call(api, "GET", PATH, headers=selected_headers)
    assert response.status_code == expected, response.text
    history_read.assert_not_called()
    no_effects(api)


def test_authorized_tenant_switch_passes_only_active_tenant_to_history(api, history_read):
    def scoped_history(database, tenant_id, **selection):
        assert database is api.db
        return {
            "rows": [{"month": date(2023, 1, 1), "value": tenant_id + "-service",
                      "currency": "EUR", "cost": Decimal("11.01" if tenant_id == "tenant-a" else "42.02"),
                      "record_count": 1}],
            "excluded_undated_count": 0, "missing_dimension_count": 0,
        }

    history_read.side_effect = scoped_history
    for tenant_id, cost, foreign in (("tenant-a", "11.01", "tenant-b"), ("tenant-b", "42.02", "tenant-a")):
        response = call(api, "GET", PATH + "&group_by=service&tenant_id=" + foreign,
                        headers=headers(user="multi", tenant=tenant_id))
        assert response.status_code == 200, response.text
        [series] = response.json()["series"]
        assert series["value"] == tenant_id + "-service"
        assert series["history"] == [{"month": "2023-01-01", "cost": cost, "record_count": 1}]
        assert foreign + "-service" not in response.text
    assert history_read.call_args_list == [
        mock_call(api.db, tenant_id, start_date=date(2023, 1, 1), end_date=date(2024, 1, 1), group_by="service")
        for tenant_id in ("tenant-a", "tenant-b")
    ]
    no_effects(api)


@pytest.mark.parametrize("selection", [
    "start_date=2023-01-01", "end_date=2024-01-01",
    "start_date=2023-02-30&end_date=2024-01-01",
    "start_date=2023-01-02&end_date=2024-01-01",
    "start_date=2023-01-01&end_date=2023-12-31",
    "start_date=2024-01-01&end_date=2024-01-01",
    "start_date=2024-01-01&end_date=2023-01-01",
    "start_date=2021-12-01&end_date=2024-01-01",
    "start_date=2023-01-01&end_date=2024-02-01",
])
def test_invalid_or_unclosed_history_period_is_rejected_before_read(api, history_read, selection):
    response = call(api, "GET", "/billing/forecast?" + selection, headers=headers())
    assert response.status_code == 422, response.text
    history_read.assert_not_called()
    no_effects(api)


@pytest.mark.parametrize("option", [
    "horizon_months=0", "horizon_months=4", "horizon_months=-1",
    "horizon_months=1.5", "horizon_months=abc", "group_by=resource_group",
    "group_by=tag", "group_by=invalid",
])
def test_invalid_horizon_and_unsupported_dimensions_are_rejected_before_read(api, history_read, option):
    response = call(api, "GET", PATH + "&" + option, headers=headers())
    assert response.status_code == 422, response.text
    history_read.assert_not_called()
    no_effects(api)


@pytest.mark.parametrize("start,horizon", [("2023-12-01", 1), ("2022-01-01", 3)])
@pytest.mark.parametrize("group_by", ["subscription", "service", "project"])
def test_inclusive_history_limits_and_supported_dimensions(api, history_read, start, horizon, group_by):
    response = call(api, "GET", f"/billing/forecast?start_date={start}&end_date=2024-01-01"
                    f"&horizon_months={horizon}&group_by={group_by}", headers=headers())
    assert response.status_code == 200, response.text
    history_read.assert_called_once_with(api.db, "tenant-a", start_date=date.fromisoformat(start),
                                          end_date=date(2024, 1, 1), group_by=group_by)
    body = response.json()
    assert body["group_by"] == group_by
    assert body["horizon_months"] == horizon
    assert body["minimum_history_months"] == 8 + horizon
    assert body["forecast_period"] == {
        "start_date": "2024-01-01", "end_date": f"2024-0{1 + horizon}-01", "timezone": "UTC",
    }


def test_empty_history_has_explicit_no_data_and_no_fabricated_forecast(api, history_read):
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == 1
    assert body["history_period"] == {"start_date": "2023-01-01", "end_date": "2024-01-01", "timezone": "UTC"}
    assert body["forecast_period"] == {"start_date": "2024-01-01", "end_date": "2024-02-01", "timezone": "UTC"}
    assert body["group_by"] == "subscription"
    assert body["horizon_months"] == 1
    assert body["minimum_history_months"] == 9
    assert body["data_status"] == "empty"
    assert body["series"] == []
    assert body["excluded_undated_count"] == body["missing_dimension_count"] == 0
    assert body["warnings"]
    no_effects(api)


def test_ambiguous_sources_return_safe_conflict_without_costs(api, history_read):
    history_read.side_effect = AmbiguousCostSource("private-ingestion-marker cost=987654.32")
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 409, response.text
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
    assert "private-ingestion-marker" not in response.text and "987654.32" not in response.text
    no_effects(api)


def test_full_forecast_preserves_large_money_baseline_backtest_and_uncertainty(api, history_read):
    history_read.return_value = {
        "rows": [{"month": date(2023, month, 1), "value": "Compute", "currency": "USD",
                  "cost": Decimal("9007199254740993.00") + Decimal(month) / 100, "record_count": 2}
                 for month in range(1, 13)],
        "excluded_undated_count": 0, "missing_dimension_count": 0,
    }
    response = call(api, "GET", PATH + "&group_by=service&horizon_months=3", headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "available"
    assert body["minimum_history_months"] == 11
    [series] = body["series"]
    assert series["currency"] == "USD"
    assert series["value"] == "Compute"
    assert series["status"] == "forecast" and series["reason"] is None
    assert series["missing_months"] == []
    assert series["method"] == "linear_trend"
    assert series["history"] == [
        {"month": f"2023-{month:02d}-01", "cost": f"9007199254740993.{month:02d}", "record_count": 2}
        for month in range(1, 13)
    ]
    assert series["backtest"] == {
        "origins": ["2023-08-01", "2023-09-01", "2023-10-01"], "horizon_months": 3,
        "baseline_mae": "0.02", "trend_mae": "0.00", "selected_mae": "0.00",
        "interval_method": "max_absolute_backtest_error_by_horizon", "nominal_coverage": None,
    }
    assert series["points"] == [
        {"month": f"2024-{month:02d}-01", "estimate": f"9007199254740993.{12 + month}",
         "baseline": "9007199254740993.12", "lower": f"9007199254740993.{12 + month}",
         "upper": f"9007199254740993.{12 + month}"}
        for month in range(1, 4)
    ]
    assert any("no guaranteed coverage" in warning for warning in body["warnings"])
    no_effects(api)
