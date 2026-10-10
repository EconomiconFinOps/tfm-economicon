"""Versioned, caller-supplied scenarios; never a claim of realised savings."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
Money = Annotated[str, StringConstraints(pattern=r"^(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,6})?$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImpactScenario(StrictModel):
    recommendation_id: Identifier
    # Atomic cost scopes, qualified by subscription/resource, shared across alternatives.
    cost_scope_ids: list[Identifier] = Field(min_length=1, max_length=100)
    currency: Currency
    baseline_monthly_cost: Money | None = None
    target_monthly_cost: Money | None = None
    evidence_ids: list[Identifier] = Field(min_length=1, max_length=20)
    assumptions: list[Text] = Field(min_length=1, max_length=20)

    @field_validator("cost_scope_ids")
    @classmethod
    def canonical_scopes(cls, values: list[str]) -> list[str]:
        normalized = [value.casefold().rstrip("/") for value in values]
        if any(not value for value in normalized) or len(normalized) != len(set(normalized)):
            raise ValueError("cost_scope_ids must be nonempty and unique after normalization")
        return normalized

    @model_validator(mode="after")
    def costs_are_paired(self) -> "ImpactScenario":
        if (self.baseline_monthly_cost is None) != (self.target_monthly_cost is None):
            raise ValueError("baseline and target costs must both be supplied or both be null")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")
        return self


class ImpactRequest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    baseline_month: date
    scenarios: list[ImpactScenario] = Field(max_length=100)

    @field_validator("baseline_month", mode="before")
    @classmethod
    def month_is_date_only(cls, value):
        if not isinstance(value, (str, date)) or (isinstance(value, str) and len(value) != 10):
            raise ValueError("baseline_month must be a YYYY-MM-01 date")
        return value

    @model_validator(mode="after")
    def validate_scopes(self) -> "ImpactRequest":
        if self.baseline_month.day != 1:
            raise ValueError("baseline_month must be the first day of a calendar month")
        ids = [item.recommendation_id for item in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("recommendation_id must be unique")
        currencies: dict[str, str] = {}
        for item in self.scenarios:
            for scope in item.cost_scope_ids:
                if scope in currencies and currencies[scope] != item.currency:
                    raise ValueError("overlapping scopes must use the same currency")
                currencies[scope] = item.currency
        return self


class RecommendationImpact(StrictModel):
    scenario: ImpactScenario
    status: Literal["estimated", "no_savings", "insufficient_data"]
    potential_monthly_savings: str | None
    potential_annual_savings: str | None
    observed_savings: None = None
    included_in_total: bool = False
    excluded_by: list[str] = Field(default_factory=list)


class CurrencyImpact(StrictModel):
    currency: Currency
    potential_monthly_savings: str | None
    potential_annual_savings: str | None
    included_recommendation_ids: list[str]
    unestimated_recommendation_ids: list[str]
    observed_savings: None = None


class ImpactReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    tenant_id: str
    baseline_month: date
    basis: Literal["caller_supplied_scenario"] = "caller_supplied_scenario"
    aggregation_method: Literal["descending_savings_disjoint_scopes"] = "descending_savings_disjoint_scopes"
    recommendations: list[RecommendationImpact]
    totals: list[CurrencyImpact]
    assumptions: list[str]
    limitations: list[str]
