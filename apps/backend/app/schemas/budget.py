"""Stateless JUP-029 budget definition and observed evaluation contract."""
from datetime import date
from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.billing import DecimalString


BudgetAmount = Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,25})\.[0-9]{2}$", max_length=29)]
ThresholdPercent = Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,3})\.[0-9]{2}$", max_length=7)]


class BudgetDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: BudgetAmount
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$", max_length=3)]
    start_date: date
    end_date: date
    thresholds_percent: Annotated[list[ThresholdPercent], Field(min_length=1, max_length=10)] = Field(
        default_factory=lambda: ["80.00", "100.00"]
    )

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
        if Decimal(self.amount) <= 0:
            raise ValueError("Budget amount must be positive")
        if self.start_date >= self.end_date:
            raise ValueError("Budget start must precede exclusive end")
        values = [Decimal(item) for item in self.thresholds_percent]
        if any(item <= 0 or item > 1000 for item in values):
            raise ValueError("Thresholds must be positive and at most 1000.00")
        if any(left >= right for left, right in zip(values, values[1:])):
            raise ValueError("Thresholds must be strictly increasing")
        return self


class BudgetEvaluation(BaseModel):
    contract_version: Literal[1] = 1
    budget: BudgetDefinition
    timezone: Literal["UTC"] = "UTC"
    data_status: Literal["available", "partial", "empty"]
    evaluation_status: Literal["evaluated", "provisional", "unavailable"]
    record_count: int
    missing_dimension_count: int
    excluded_undated_count: int
    observed_spend: DecimalString | None = None
    consumption_percent: DecimalString | None = None
    remaining_amount: DecimalString | None = None
    deviation_amount: DecimalString | None = None
    deviation_percent: DecimalString | None = None
    reached_thresholds_percent: list[ThresholdPercent] | None = None
    highest_reached_threshold_percent: ThresholdPercent | None = None
