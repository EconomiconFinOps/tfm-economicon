"""Versioned, observed-cost evidence for JUP-030 and consumers such as JUP-038."""
from datetime import date, datetime, timezone
from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.billing import BillingPeriod, DecimalString
from app.schemas.budget import BudgetAmount, ThresholdPercent


class AnomalyDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date
    group_by: Literal["subscription", "resource_group", "service", "project"] = "service"
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$", max_length=3)]
    absolute_threshold: BudgetAmount | None = None
    deviation_threshold_percent: ThresholdPercent | None = None
    min_absolute_increase: BudgetAmount = "0.01"

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def explicit_date(cls, value):
        if type(value) is date:
            return value
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Expected an ISO date YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def valid_definition(self):
        days = (self.end_date - self.start_date).days
        if not 1 <= days <= 366:
            raise ValueError("Expected an interval of 1 to 366 days")
        if self.end_date > datetime.now(timezone.utc).date():
            raise ValueError("Only closed UTC days can be evaluated")
        if self.absolute_threshold is None and self.deviation_threshold_percent is None:
            raise ValueError("At least one detection rule is required")
        if self.absolute_threshold is not None and Decimal(self.absolute_threshold) <= 0:
            raise ValueError("Absolute threshold must be positive")
        if Decimal(self.min_absolute_increase) <= 0:
            raise ValueError("Minimum increase must be positive")
        if self.deviation_threshold_percent is not None:
            if not 0 < Decimal(self.deviation_threshold_percent) <= 1000:
                raise ValueError("Deviation threshold must be positive and at most 1000.00")
            if self.start_date.toordinal() <= days:
                raise ValueError("Baseline period is outside supported dates")
        return self

    @property
    def baseline_period(self) -> BillingPeriod | None:
        if self.deviation_threshold_percent is None:
            return None
        return BillingPeriod(start_date=self.start_date - (self.end_date - self.start_date),
                             end_date=self.start_date)


class AnomalyQuality(BaseModel):
    data_status: Literal["available", "partial", "empty"]
    record_count: int
    missing_dimension_count: int
    excluded_undated_count: int


class AnomalyAssessment(BaseModel):
    group_value: str | None
    subscription_id: str | None
    currency: str
    current_cost: DecimalString
    current_record_count: int
    baseline_record_count: int | None = None
    baseline_cost: DecimalString | None = None
    delta_amount: DecimalString | None = None
    deviation_percent: DecimalString | None = None
    threshold_status: Literal["disabled", "below", "triggered"]
    deviation_status: Literal["disabled", "below", "triggered", "baseline_missing", "baseline_nonpositive"]
    trigger_reasons: list[Literal["absolute_threshold", "period_increase"]]


class CostAnomaly(AnomalyAssessment):
    id: str
    evidence_id: str
    cause_status: Literal["not_established"] = "not_established"


class AnomalyEvaluation(BaseModel):
    contract_version: Literal[1] = 1
    source: Literal["billing_summary_v2"] = "billing_summary_v2"
    definition: AnomalyDefinition
    current_period: BillingPeriod
    baseline_period: BillingPeriod | None
    current_quality: AnomalyQuality
    baseline_quality: AnomalyQuality | None
    evaluation_status: Literal["evaluated", "provisional", "unavailable"]
    completeness: Literal["not_verified"] = "not_verified"
    limitations: list[str] = Field(default_factory=lambda: [
        "Window coverage and source freshness are not verified by billing_summary_v2.",
        "Periods are read separately; late ingestions may change a subsequent evaluation.",
        "Amounts are billing aggregates rounded to cents; no exchange-rate conversion is applied.",
        "A rule match is a candidate for investigation, not a demonstrated cause or saving.",
    ])
    alerts: list[CostAnomaly]
    assessments: list[AnomalyAssessment]
