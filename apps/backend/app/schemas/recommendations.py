"""Versioned, read-only recommendation candidates from observed Azure costs."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.billing import DecimalString


Identifier = Annotated[str, Field(pattern=r"^[a-z-]+:sha256:[0-9a-f]{64}$")]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
RuleId = Literal["missing_project", "largest_project_cost"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecommendationPeriod(StrictModel):
    start_date: date
    end_date: date
    timezone: Literal["UTC"] = "UTC"

    @model_validator(mode="after")
    def ordered(self) -> "RecommendationPeriod":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class RecommendationScope(StrictModel):
    dimension: Literal["project"] = "project"
    value: str | None


class ObservedCost(StrictModel):
    amount: DecimalString
    currency: Currency
    record_count: int = Field(gt=0)


class RecommendationQuery(StrictModel):
    period: RecommendationPeriod
    group_by: Literal["project"] = "project"
    tag_key: None = None


class RecommendationEvidence(StrictModel):
    id: Identifier
    kind: Literal["cost_query"] = "cost_query"
    source: Literal["azure_cost_records"] = "azure_cost_records"
    query: RecommendationQuery
    rule_id: RuleId
    rule_version: Literal[1] = 1
    scope: RecommendationScope
    observed_cost: ObservedCost


class Recommendation(StrictModel):
    id: Identifier
    rule_id: RuleId
    rule_version: Literal[1] = 1
    category: Literal["tagging", "investigation"]
    qualification: Literal["supported", "investigation_candidate"]
    action: str = Field(min_length=1, max_length=500)
    rationale: str = Field(min_length=1, max_length=1000)
    scope: RecommendationScope
    observed_cost: ObservedCost
    estimated_savings: None = None
    currency: None = None
    confidence: Literal["low", "medium", "high"]
    risk: Literal["low", "medium", "high"]
    difficulty: Literal["low", "medium", "high", "unknown"]
    evidence_ids: list[Identifier] = Field(min_length=1, max_length=1)
    requires_human_approval: Literal[True] = True

    @model_validator(mode="after")
    def rule_classification(self) -> "Recommendation":
        expected = {
            "missing_project": ("tagging", "supported"),
            "largest_project_cost": ("investigation", "investigation_candidate"),
        }
        if (self.category, self.qualification) != expected[self.rule_id]:
            raise ValueError("Recommendation classification must match its rule")
        if (self.scope.value is None) != (self.rule_id == "missing_project"):
            raise ValueError("Recommendation scope must match its rule")
        return self


class NotEvaluatedAction(StrictModel):
    action: Literal["rightsizing", "scheduling", "orphan_cleanup", "rate_optimization", "savings_impact"]
    missing_inputs: list[str] = Field(min_length=1)


class RecommendationReport(StrictModel):
    contract_version: Literal[1] = 1
    period: RecommendationPeriod
    source: Literal["azure_cost_records"] = "azure_cost_records"
    cloud: Literal["azure"] = "azure"
    data_environment: Literal["simulated"] = "simulated"
    data_status: Literal["available", "partial", "empty"]
    status: Literal["available", "insufficient_data"]
    recommendations: list[Recommendation] = Field(max_length=50)
    evidence: list[RecommendationEvidence] = Field(max_length=50)
    total_candidates: int = Field(ge=0)
    truncated: bool
    assumptions: list[str]
    limitations: list[str]
    not_evaluated: list[NotEvaluatedAction]
    missing_dimension_count: int = Field(ge=0)
    excluded_undated_count: int = Field(ge=0)

    @model_validator(mode="after")
    def consistent_evidence(self) -> "RecommendationReport":
        identifiers = [item.id for item in self.recommendations]
        evidence = {item.id: item for item in self.evidence}
        if len(identifiers) != len(set(identifiers)) or len(evidence) != len(self.evidence):
            raise ValueError("Recommendation and evidence identifiers must be unique")
        referenced = set()
        for item in self.recommendations:
            for identifier in item.evidence_ids:
                source = evidence.get(identifier)
                if source is None:
                    raise ValueError("Recommendation must reference existing evidence")
                if (source.rule_id, source.rule_version, source.scope, source.observed_cost) != (
                    item.rule_id, item.rule_version, item.scope, item.observed_cost
                ) or source.query.period != self.period:
                    raise ValueError("Recommendation must match its evidence and report period")
                referenced.add(identifier)
        if referenced != set(evidence):
            raise ValueError("Evidence must belong to a returned recommendation")
        if self.total_candidates < len(self.recommendations):
            raise ValueError("total_candidates cannot be less than returned candidates")
        if self.truncated != (self.total_candidates > len(self.recommendations)):
            raise ValueError("truncated must describe the returned candidate count")
        if self.status == "insufficient_data" and (self.total_candidates or self.evidence):
            raise ValueError("Insufficient data cannot contain recommendations or evidence")
        return self
