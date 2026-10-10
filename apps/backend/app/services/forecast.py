"""Deterministic monthly forecasting; no external models, writes or anomaly detection."""
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

from app.schemas.forecast import BillingForecast, ForecastBacktest, ForecastPoint, ForecastSeries, ObservedMonth


def add_months(value: date, count: int) -> date:
    ordinal = value.year * 12 + value.month - 1 + count
    return date(ordinal // 12, ordinal % 12 + 1, 1)


def money(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if rounded == 0 else format(rounded, ".2f")


def predict(values: list[Decimal], horizon: int, method: str) -> list[Decimal]:
    if method == "last_month":
        return [values[-1]] * horizon
    n = len(values)
    center = Decimal(n - 1) / 2
    mean = sum(values) / n
    slope = sum((Decimal(i) - center) * (y - mean) for i, y in enumerate(values)) / sum(
        (Decimal(i) - center) ** 2 for i in range(n)
    )
    return [mean + slope * (Decimal(n + i) - center) for i in range(horizon)]


def _forecast_series(value, currency, rows, months, horizon):
    observed = {row["month"]: row for row in rows}
    missing = [month for month in months if month not in observed]
    values = [Decimal(row["cost"]) for row in rows]
    result = ForecastSeries(value=value, currency=currency, status="insufficient_data", missing_months=missing)
    if any(not amount.is_finite() for amount in values):
        result.status, result.reason = "invalid_data", "non_finite_cost"
        return result
    # Preserve cents even for large amounts and independent of caller precision.
    precision = max([50] + [len(y.as_tuple().digits) + abs(y.as_tuple().exponent) + 30 for y in values])
    with localcontext() as context:
        context.prec = precision
        result.history = [ObservedMonth(month=row["month"], cost=money(Decimal(row["cost"])),
                                        record_count=row["record_count"]) for row in rows]
        if value is None:
            result.reason = "missing_dimension"
            return result
        if missing:
            result.reason = "missing_months"
            return result
        # Three expanding-window origins, at least six months in the earliest train set.
        if len(values) < 8 + horizon:
            result.reason = "short_history"
            return result
        cuts = range(len(values) - horizon - 2, len(values) - horizon + 1)
        errors = {}
        for method in ("last_month", "linear_trend"):
            errors[method] = [
                [abs(actual - estimate) for actual, estimate in zip(
                    values[cut:cut + horizon], predict(values[:cut], horizon, method))]
                for cut in cuts
            ]
        mae = {method: sum(sum(fold) for fold in folds) / (3 * horizon)
               for method, folds in errors.items()}
        # A tie (including constant/zero series) keeps the simpler reference.
        method = "linear_trend" if mae["linear_trend"] < mae["last_month"] * Decimal("0.95") else "last_month"
        estimates = predict(values, horizon, method)
        baseline = predict(values, horizon, "last_month")
        widths = [max(fold[step] for fold in errors[method]) for step in range(horizon)]
        result.status, result.method = "forecast", method
        result.backtest = ForecastBacktest(origins=[months[cut] for cut in cuts], horizon_months=horizon,
                           baseline_mae=money(mae["last_month"]), trend_mae=money(mae["linear_trend"]),
                           selected_mae=money(mae[method]))
        result.points = [ForecastPoint(month=add_months(months[-1], step + 1), estimate=money(estimate),
                          baseline=money(baseline[step]), lower=money(estimate - widths[step]),
                          upper=money(estimate + widths[step])) for step, estimate in enumerate(estimates)]
    return result


def forecast_spend(history: dict, *, start_date: date, end_date: date, group_by: str,
                   horizon_months: int) -> BillingForecast:
    months = [add_months(start_date, i) for i in range(
        (end_date.year - start_date.year) * 12 + end_date.month - start_date.month)]
    grouped = defaultdict(list)
    for row in history["rows"]:
        grouped[(row["value"], row["currency"])].append(row)
    series = [_forecast_series(value, currency, sorted(rows, key=lambda row: row["month"]),
                               months, horizon_months)
              for (value, currency), rows in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0] or ""))]
    partial = history["excluded_undated_count"] or history["missing_dimension_count"] or any(
        item.status != "forecast" for item in series)
    return BillingForecast(
        history_period={"start_date": start_date, "end_date": end_date},
        forecast_period={"start_date": end_date, "end_date": add_months(end_date, horizon_months)},
        group_by=group_by, horizon_months=horizon_months, minimum_history_months=8 + horizon_months,
        data_status="partial" if partial else ("available" if series else "empty"),
        excluded_undated_count=history["excluded_undated_count"],
        missing_dimension_count=history["missing_dimension_count"], series=series,
        warnings=["Indicative net pre-tax costs in each original currency; credits can produce negative forecasts.",
                  "Monthly observations do not certify ingestion coverage or billing completeness.",
                  "Empirical error envelopes have no guaranteed coverage; model selection uses the same three backtest origins.",
                  "No seasonal, price, exchange-rate or infrastructure-change model; not Azure's native forecast."],
    )
