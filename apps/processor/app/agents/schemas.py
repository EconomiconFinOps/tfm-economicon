from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


ShortText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
AnswerText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]
EvidenceId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    ),
]
DecimalText = Annotated[
    str,
    StringConstraints(pattern=r"^-?(?:0|[1-9]\d*)(?:\.\d{1,12})?$"),
]
NonNegativeDecimalText = Annotated[
    str,
    StringConstraints(pattern=r"^(?:0|[1-9]\d*)(?:\.\d{1,12})?$"),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponseStatus(str, Enum):
    ok = "ok"
    partial = "partial"
    no_data = "no_data"
    insufficient_data = "insufficient_data"
    unsupported = "unsupported"
    refused = "refused"
    error = "error"


class EvidenceKind(str, Enum):
    cost_query = "cost_query"
    corpus = "corpus"
    user_input = "user_input"


class RecommendationCategory(str, Enum):
    tagging = "tagging"
    investigation = "investigation"
    rightsizing = "rightsizing"
    scheduling = "scheduling"
    orphan_cleanup = "orphan_cleanup"
    storage_optimization = "storage_optimization"
    observability_optimization = "observability_optimization"
    rate_optimization = "rate_optimization"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Risk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Period(StrictModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")

    @model_validator(mode="after")
    def validate_order(self) -> "Period":
        if self.from_date >= self.to_date:
            raise ValueError("period.from must be before period.to")
        return self


class ResponseScope(StrictModel):
    cloud: Literal["azure"]
    data_environment: Literal["simulated"]
    subscription_ids: list[ShortText] = Field(max_length=20)
    period: Period | None


class Evidence(StrictModel):
    id: EvidenceId
    kind: EvidenceKind
    title: ShortText
    source: ShortText


class Metric(StrictModel):
    name: ShortText
    value: DecimalText
    unit: ShortText
    evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=20)


class Recommendation(StrictModel):
    category: RecommendationCategory
    action: ShortText
    rationale: ShortText
    estimated_savings: NonNegativeDecimalText | None
    currency: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Z]{3}$"),
    ] | None
    confidence: Confidence
    risk: Risk
    evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=20)
    requires_human_approval: Literal[True]

    @model_validator(mode="after")
    def validate_savings_currency(self) -> "Recommendation":
        if (self.estimated_savings is None) != (self.currency is None):
            raise ValueError(
                "estimated_savings and currency must either both be set or both be null"
            )
        return self


class FinOpsResponse(StrictModel):
    schema_version: Literal["1.0"]
    status: ResponseStatus
    answer: AnswerText
    scope: ResponseScope
    evidence: list[Evidence] = Field(max_length=20)
    metrics: list[Metric] = Field(max_length=20)
    recommendations: list[Recommendation] = Field(max_length=10)
    assumptions: list[ShortText] = Field(max_length=10)
    limitations: list[ShortText] = Field(max_length=10)
    next_actions: list[ShortText] = Field(max_length=10)

    @model_validator(mode="after")
    def validate_evidence_and_status(self) -> "FinOpsResponse":
        evidence_ids = [item.id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence ids must be unique")

        non_actionable_statuses = {
            ResponseStatus.no_data,
            ResponseStatus.insufficient_data,
            ResponseStatus.unsupported,
            ResponseStatus.refused,
            ResponseStatus.error,
        }
        if self.status in non_actionable_statuses and (
            self.metrics or self.recommendations
        ):
            raise ValueError(
                "non-actionable responses cannot contain metrics or recommendations"
            )

        known_ids = set(evidence_ids)
        referenced_ids = {
            evidence_id
            for metric in self.metrics
            for evidence_id in metric.evidence_ids
        }
        referenced_ids.update(
            evidence_id
            for recommendation in self.recommendations
            for evidence_id in recommendation.evidence_ids
        )
        unknown_ids = sorted(referenced_ids - known_ids)
        if unknown_ids:
            raise ValueError("metrics and recommendations must reference known evidence")

        if self.status in {ResponseStatus.ok, ResponseStatus.partial} and not self.evidence:
            raise ValueError("ok and partial responses require evidence")
        return self


def finops_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "economicon_finops_response_v1",
            "strict": True,
            "schema": FinOpsResponse.model_json_schema(by_alias=True),
        },
    }
