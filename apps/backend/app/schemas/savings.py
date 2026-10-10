"""JUP-039 consumer contract. Provider rows are internal, never request data."""
from datetime import date
import re
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Money = Annotated[str, StringConstraints(pattern=r"^(0|[1-9][0-9]{0,25})\.[0-9]{2}$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SavingsSelection(StrictModel):
    start_date: date
    end_date: date
    subscription_id: Identifier | None = None
    top_n: int = Field(default=5, ge=1, le=20, strict=True)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def iso_calendar_date(cls, value):
        if type(value) is date:
            return value
        if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
            raise ValueError("Use an ISO calendar date YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must precede end_date (exclusive)")
        return self


class SavingsSource(StrictModel):
    evidence_id: Identifier
    title: Text
    reference: Text


class SavingsOpportunity(StrictModel):
    recommendation_id: Identifier
    tenant_id: Identifier
    subscription_id: Identifier | None
    title: Text
    action: Text
    state: Literal["proposed", "accepted", "dismissed", "implemented", "expired"]
    currency: Currency
    monthly_estimate: Money | None
    annual_estimate: Money | None
    # Same basis means possibly overlapping benefits; None means not assessed.
    independent_cost_basis: Identifier | None
    risk: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    assumptions: list[Text] = Field(min_length=1, max_length=60)
    sources: list[SavingsSource] = Field(min_length=1, max_length=40)
    limitations: list[Text] = Field(default_factory=list, max_length=60)

    @model_validator(mode="after")
    def estimates_are_paired(self):
        if (self.monthly_estimate is None) != (self.annual_estimate is None):
            raise ValueError("monthly and annual estimates must both be supplied or unavailable")
        if self.monthly_estimate is None and not self.limitations:
            raise ValueError("unavailable estimates require a limitation")
        return self


class SavingsSnapshot(StrictModel):
    contract_version: Literal["savings-input.v1"]
    tenant_id: Identifier
    start_date: date
    end_date: date
    subscription_id: Identifier | None
    generated_at: AwareDatetime
    data_status: Literal["available", "partial", "empty"]
    opportunities: list[SavingsOpportunity] = Field(max_length=200)
    limitations: list[Text] = Field(default_factory=list, max_length=60)
    upstream_reports: dict[str, dict] = Field(default_factory=dict)

    @model_validator(mode="after")
    def consistent_coverage(self):
        if self.start_date >= self.end_date:
            raise ValueError("invalid snapshot period")
        if (self.data_status == "empty") != (len(self.opportunities) == 0):
            raise ValueError("empty status must match empty input")
        if self.data_status == "partial" and not self.limitations:
            raise ValueError("partial coverage requires a limitation")
        return self
