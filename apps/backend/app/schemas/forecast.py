"""Versioned, currency-separated monthly forecasting contract (JUP-031)."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.billing import BillingPeriod, DecimalString

ForecastGrouping = Literal["subscription", "service", "project"]
ForecastMethod = Literal["last_month", "linear_trend"]


class ObservedMonth(BaseModel):
    month: date
    cost: DecimalString
    record_count: int


class ForecastPoint(BaseModel):
    month: date
    estimate: DecimalString
    baseline: DecimalString
    lower: DecimalString
    upper: DecimalString


class ForecastBacktest(BaseModel):
    origins: list[date]
    horizon_months: int
    baseline_mae: DecimalString
    trend_mae: DecimalString
    selected_mae: DecimalString
    interval_method: Literal["max_absolute_backtest_error_by_horizon"] = "max_absolute_backtest_error_by_horizon"
    nominal_coverage: None = None


class ForecastSeries(BaseModel):
    value: str | None
    currency: str
    status: Literal["forecast", "insufficient_data", "invalid_data"]
    reason: str | None = None
    history: list[ObservedMonth] = Field(default_factory=list)
    missing_months: list[date] = Field(default_factory=list)
    method: ForecastMethod | None = None
    backtest: ForecastBacktest | None = None
    points: list[ForecastPoint] = Field(default_factory=list)


class BillingForecast(BaseModel):
    contract_version: Literal[1] = 1
    history_period: BillingPeriod
    forecast_period: BillingPeriod
    group_by: ForecastGrouping
    horizon_months: int
    minimum_history_months: int
    data_status: Literal["available", "partial", "empty"]
    excluded_undated_count: int
    missing_dimension_count: int
    series: list[ForecastSeries]
    warnings: list[str]
