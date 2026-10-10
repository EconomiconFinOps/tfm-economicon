"""JUP-031 monthly reader: real Cockroach SQL tests plus no-engine input guards.

SQL cases require the existing isolated JUP086_COCKROACH_TEST_URL fixture; a
skip does not demonstrate SQL compatibility. No aggregation is replaced by a
double in these cases.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.db.forecast import fetch_forecast_history
from app.schemas.billing import AmbiguousCostSource
from billing_support import billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import tenant_cockroach_database


def read(database, group_by="subscription", start="2024-06-01", end="2024-07-01"):
    return fetch_forecast_history(
        database, "tenant-a", start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end), group_by=group_by,
    )


# Literal independent expectations preserve sub-cent precision and credits.
BUCKETS = {
    "subscription": [("sub-a", "12.008", 2), ("sub-b", "-1.000", 3)],
    "service": [("Compute", "10.004", 1), ("Storage", "-1.005", 1),
                ("Unknown", "0.005", 1), ("compute", "2.004", 1), (None, "0", 1)],
    "project": [("Fallback", "2.004", 1), ("Typed", "10.004", 1),
                ("Unknown", "0.005", 1), (None, "-1.005", 2)],
}


@pytest.mark.parametrize("group_by", list(BUCKETS))
def test_sql_exact_monthly_buckets_and_completed_tenant_join(cost_reference, group_by):
    result = read(cost_reference, group_by)
    expected = [
        {"month": date(2024, 6, 1), "value": value, "currency": "EUR",
         "cost": Decimal(cost), "record_count": count}
        for value, cost, count in BUCKETS[group_by]
    ]
    extra_value = {"subscription": "sub-a", "service": "Compute", "project": "Typed"}[group_by]
    for currency, cost in [("GBP", "-0.004"), ("USD", "9007199254740993.005")]:
        expected.append({"month": date(2024, 6, 1), "value": extra_value, "currency": currency,
                         "cost": Decimal(cost), "record_count": 1})
    expected.sort(key=lambda row: (row["value"] is None, row["value"] or "", row["currency"]))
    assert result == {
        "rows": expected, "excluded_undated_count": 1,
        "missing_dimension_count": {"subscription": 0, "service": 1, "project": 2}[group_by],
    }
    assert all(type(row["month"]) is date and isinstance(row["cost"], Decimal) for row in result["rows"])


def test_sql_missing_months_are_not_zero_and_period_is_half_open(cost_reference):
    with cost_reference.engine.begin() as connection:
        # Preserve only June observations, then add distinct months and the
        # exclusive-end marker. No normalizer or forecast helper builds inputs.
        connection.execute(text("DELETE FROM azure_cost_records WHERE usage_date < '2024-06-01' OR usage_date >= '2024-07-01'"))
        insert_cost(connection, "august", day="2024-08-31", cost="-5.005")
        insert_cost(connection, "september", day="2024-09-01", cost="9999")
    rows = read(cost_reference, start="2024-06-01", end="2024-09-01")["rows"]
    assert sorted({row["month"] for row in rows}) == [date(2024, 6, 1), date(2024, 8, 1)]
    assert [row for row in rows if row["month"] == date(2024, 8, 1)] == [
        {"month": date(2024, 8, 1), "value": "sub-a", "currency": "EUR",
         "cost": Decimal("-5.005"), "record_count": 1},
    ]


def test_sql_empty_and_undated_status_are_distinct_from_observed_zero(cost_reference):
    assert read(cost_reference, start="2025-01-01", end="2025-02-01") == {
        "rows": [], "excluded_undated_count": 1, "missing_dimension_count": 0,
    }
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records WHERE usage_date IS NULL"))
        insert_cost(connection, "observed-zero", day="2025-01-31", cost="0")
    assert read(cost_reference, start="2025-01-01", end="2025-02-01") == {
        "rows": [{"month": date(2025, 1, 1), "value": "sub-a", "currency": "EUR",
                  "cost": Decimal("0"), "record_count": 1}],
        "excluded_undated_count": 0, "missing_dimension_count": 0,
    }


@pytest.mark.parametrize("group_by", list(BUCKETS))
def test_sql_source_conflict_precedes_grouping_and_does_not_write(cost_reference, group_by):
    with cost_reference.engine.begin() as connection:
        insert_run(connection, "forecast-overlap")
        insert_cost(connection, "different-dimension", run="forecast-overlap", day="2024-06-01",
                    service="Unrelated", project="Unrelated", cost="987654")
        before = connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings().all()
    with pytest.raises(AmbiguousCostSource):
        read(cost_reference, group_by)
    with cost_reference.engine.connect() as connection:
        after = connection.execute(text("SELECT * FROM azure_cost_records ORDER BY id")).mappings().all()
    assert after == before


def test_sql_foreign_only_scope_is_empty(cost_reference):
    result = fetch_forecast_history(
        cost_reference, "tenant-with-no-data", start_date=date(2024, 6, 1),
        end_date=date(2024, 7, 1), group_by="project",
    )
    assert result == {"rows": [], "excluded_undated_count": 0, "missing_dimension_count": 0}


def test_sql_twelve_month_observations_reach_forecast_with_literal_reference(cost_reference):
    from app.services.forecast import forecast_spend

    assert cost_reference.test_owned_name.startswith("jup086_backend_")
    assert cost_reference.engine.url.database == cost_reference.test_owned_name
    observations = [
        ("2023-01-15", "100"), ("2023-02-15", "110"), ("2023-03-15", "120"),
        ("2023-04-15", "130"), ("2023-05-15", "140"), ("2023-06-15", "150"),
        ("2023-07-15", "160"), ("2023-08-15", "170"), ("2023-09-15", "180"),
        ("2023-10-15", "190"), ("2023-11-15", "200"), ("2023-12-15", "210"),
    ]
    with cost_reference.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        for index, (day, cost) in enumerate(observations):
            insert_cost(connection, f"forecast-month-{index}", day=day, cost=cost,
                        service="Compute", project="Plan")
    history = read(cost_reference, start="2023-01-01", end="2024-01-01")
    result = forecast_spend(history, start_date=date(2023, 1, 1), end_date=date(2024, 1, 1),
                            group_by="subscription", horizon_months=3)
    assert result.data_status == "available"
    assert (result.excluded_undated_count, result.missing_dimension_count) == (0, 0)
    assert len(result.series) == 1
    series = result.series[0]
    assert (series.value, series.currency, series.status, series.method) == (
        "sub-a", "EUR", "forecast", "linear_trend",
    )
    assert [point.model_dump() for point in series.points] == [
        {"month": date(2024, 1, 1), "estimate": "220.00", "baseline": "210.00", "lower": "220.00", "upper": "220.00"},
        {"month": date(2024, 2, 1), "estimate": "230.00", "baseline": "210.00", "lower": "230.00", "upper": "230.00"},
        {"month": date(2024, 3, 1), "estimate": "240.00", "baseline": "210.00", "lower": "240.00", "upper": "240.00"},
    ]
    assert series.backtest.baseline_mae == "20.00"
    assert series.backtest.trend_mae == series.backtest.selected_mae == "0.00"
    assert series.backtest.nominal_coverage is None


@pytest.mark.parametrize("group_by,start,end", [
    ("resource_group", date(2024, 6, 1), date(2024, 7, 1)),
    ("subscription; DROP TABLE azure_cost_records", date(2024, 6, 1), date(2024, 7, 1)),
    ("subscription", date(2024, 6, 1), date(2024, 6, 1)),
    ("service", date(2024, 7, 1), date(2024, 6, 1)),
])
def test_no_engine_guard_rejects_invalid_selection(group_by, start, end):
    # Deliberately lacks an engine: proves guard failures precede any DB access.
    no_engine_double = SimpleNamespace()
    with pytest.raises(ValueError, match="Invalid forecast history selection"):
        fetch_forecast_history(no_engine_double, "tenant-a", start_date=start, end_date=end, group_by=group_by)
