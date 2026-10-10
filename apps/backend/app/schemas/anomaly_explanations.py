"""Consumer boundary for the JUP-030 v1 detection contract."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.billing import BillingPeriod, DecimalString
from app.schemas.budget import BudgetAmount, ThresholdPercent


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DetectionSelection(EvidenceModel):
    # JUP-030 owns date/rule validation; the adapter validates with its definition.
    start_date: Annotated[str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", max_length=10)]
    end_date: Annotated[str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", max_length=10)]
    group_by: Literal["subscription", "resource_group", "service", "project"] = "service"
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    absolute_threshold: BudgetAmount | None = None
    deviation_threshold_percent: ThresholdPercent | None = None
    min_absolute_increase: BudgetAmount = "0.01"


class ExplainAnomalyRequest(EvidenceModel):
    anomaly_id: Annotated[str, Field(pattern=r"^cost-[a-f0-9]{64}$")]
    evidence_id: Annotated[str, Field(pattern=r"^evidence-[a-f0-9]{64}$")]
    definition: DetectionSelection


class DetectionQuality(EvidenceModel):
    data_status: Literal["available", "partial", "empty"]
    record_count: int = Field(ge=0)
    missing_dimension_count: int = Field(ge=0)
    excluded_undated_count: int = Field(ge=0)


class DetectedAnomaly(EvidenceModel):
    id: str
    evidence_id: str
    group_value: str | None
    subscription_id: str | None
    currency: str
    current_cost: DecimalString
    current_record_count: int = Field(gt=0)
    baseline_record_count: int | None = Field(default=None, ge=0)
    baseline_cost: DecimalString | None = None
    delta_amount: DecimalString | None = None
    deviation_percent: DecimalString | None = None
    threshold_status: Literal["disabled", "below", "triggered"]
    deviation_status: Literal["disabled", "below", "triggered", "baseline_missing", "baseline_nonpositive"]
    trigger_reasons: list[Literal["absolute_threshold", "period_increase"]]
    cause_status: Literal["not_established"]


class DetectionSnapshot(EvidenceModel):
    contract_version: Literal[1]
    source: Literal["billing_summary_v2"]
    definition: DetectionSelection
    current_period: BillingPeriod
    baseline_period: BillingPeriod | None
    current_quality: DetectionQuality
    baseline_quality: DetectionQuality | None
    evaluation_status: Literal["evaluated", "provisional", "unavailable"]
    completeness: Literal["not_verified"]
    limitations: list[str]
    alerts: list[DetectedAnomaly]
    assessments: list[dict]


class AnomalyExplanation(EvidenceModel):
    contract_version: Literal[1] = 1
    content: str
    evidence: dict
    limitations: list[str]
    suggested_checks: list[str]
    cause_status: Literal["not_established"] = "not_established"
