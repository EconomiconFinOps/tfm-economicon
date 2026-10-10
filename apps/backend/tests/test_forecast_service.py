"""Synthetic monthly series with independent arithmetic expectations; no Azure claims."""
from datetime import date
from decimal import Decimal, localcontext

import pytest

from app.services.forecast import add_months, forecast_spend


def history(values, **changes):
    return {"rows": [{"month": add_months(date(2024, 1, 1), i), "cost": Decimal(str(value)),
                      "value": "sub-a", "currency": "EUR", "record_count": 2}
                     for i, value in enumerate(values)],
            "excluded_undated_count": 0, "missing_dimension_count": 0, **changes}


def run(source, horizon=1, months=12):
    return forecast_spend(source, start_date=date(2024, 1, 1), end_date=add_months(date(2024, 1, 1), months),
                          group_by="subscription", horizon_months=horizon)


def test_trend_beats_last_month_with_multistep_holdout():
    result = run(history(range(100, 220, 10)), horizon=3)
    series = result.series[0]
    assert result.minimum_history_months == 11
    assert series.method == "linear_trend"
    assert [point.estimate for point in series.points] == ["220.00", "230.00", "240.00"]
    assert [point.baseline for point in series.points] == ["210.00"] * 3
    assert series.backtest.baseline_mae == "20.00"
    assert series.backtest.trend_mae == series.backtest.selected_mae == "0.00"
    assert series.backtest.origins == [date(2024, 8, 1), date(2024, 9, 1), date(2024, 10, 1)]
    assert series.backtest.nominal_coverage is None
    assert result.forecast_period.end_date == date(2025, 4, 1)


@pytest.mark.parametrize("value", ["0", "100", "-12.34", "9007199254740993.01"])
def test_constant_zero_credit_and_large_money_keep_baseline(value):
    with localcontext() as context:
        context.prec = 6
        series = run(history([value] * 12)).series[0]
    assert series.method == "last_month"
    assert Decimal(series.points[0].estimate) == Decimal(value)
    assert series.points[0].lower == series.points[0].upper == series.points[0].estimate


def test_sudden_change_retains_better_baseline_and_nonzero_error_envelope():
    series = run(history([10] * 6 + [100] * 6)).series[0]
    assert series.method == "last_month"
    assert series.backtest.selected_mae == "0.00"
    assert Decimal(series.backtest.trend_mae) > 0
    noisy = run(history([100, 100, 100, 100, 100, 100, 100, 100, 100, 110, 90, 110])).series[0]
    assert Decimal(noisy.points[0].lower) < Decimal(noisy.points[0].estimate) < Decimal(noisy.points[0].upper)


def test_validation_does_not_train_on_heldout_future(monkeypatch):
    from app.services import forecast
    real = forecast.predict
    calls = []
    def spy(values, horizon, method):
        calls.append((list(values), horizon, method))
        return real(values, horizon, method)
    monkeypatch.setattr(forecast, "predict", spy)
    run(history(range(12)), horizon=3)
    assert [len(values) for values, _, _ in calls] == [7, 8, 9, 7, 8, 9, 12, 12]
    assert all(values == list(map(Decimal, range(len(values)))) for values, _, _ in calls)


def test_empty_and_short_series_never_forecast():
    result = run(history([]))
    assert result.data_status == "empty" and result.series == []
    series = run(history([1] * 8), months=8).series[0]
    assert series.reason == "short_history"
    assert series.points == [] and series.backtest is None
    assert run(history([1] * 9), months=9).series[0].status == "forecast"
    assert run(history([1] * 10), months=10, horizon=3).series[0].reason == "short_history"


@pytest.mark.parametrize("missing_index", [0, 5, 11])
def test_leading_internal_and_trailing_holes_are_not_zero(missing_index):
    source = history([0] * 12)
    removed = source["rows"].pop(missing_index)
    series = run(source).series[0]
    assert series.reason == "missing_months"
    assert series.missing_months == [removed["month"]]
    assert len(series.history) == 11 and series.points == []


def test_currency_dimension_and_unallocated_series_remain_separate():
    source = history([100] * 12)
    source["rows"] += [dict(row, currency="USD", cost=Decimal(200)) for row in source["rows"]]
    source["rows"] += [dict(row, value="project-b", cost=Decimal(300)) for row in source["rows"][:12]]
    source["rows"] += [dict(row, value=None) for row in source["rows"][:12]]
    source.update(excluded_undated_count=1, missing_dimension_count=24)
    result = run(source)
    assert result.data_status == "partial" and len(result.series) == 4
    assert result.series[0].reason == "missing_dimension"
    assert {(item.value, item.currency, item.points[0].estimate) for item in result.series if item.points} == {
        ("sub-a", "EUR", "100.00"), ("sub-a", "USD", "200.00"), ("project-b", "EUR", "300.00")}


@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_cost_returns_invalid_data(invalid):
    source = history([1] * 12)
    source["rows"][3]["cost"] = Decimal(invalid)
    series = run(source).series[0]
    assert series.status == "invalid_data" and series.reason == "non_finite_cost"
    assert series.points == []


def test_order_and_decimal_rounding_are_stable():
    source = history(["0.005"] * 12)
    source["rows"].reverse()
    result = run(source)
    assert result.series[0].history[0].cost == "0.01"
    assert result.series[0].points[0].estimate == "0.01"
    # JSON emits typed nested defaults and exact monetary strings.
    assert result.model_dump(mode="json")["series"][0]["backtest"]["nominal_coverage"] is None
