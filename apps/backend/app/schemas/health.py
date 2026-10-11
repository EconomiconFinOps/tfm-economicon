from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
    checked_at: datetime

from typing import Literal
from pydantic import ConfigDict, Field

HealthState = Literal["ok", "degraded", "failed", "unknown"]
Reason = Literal["none", "connection", "upstream_error", "authentication", "timeout", "invalid_response", "not_configured", "not_initialized", "not_verified", "busy", "cooldown", "budget_unavailable", "stale"]
ComponentId = Literal["backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter"]
JobState = Literal["publish_pending", "publish_failed", "publish_unknown", "queued", "running", "completed", "failed", "other"]
RunState = Literal["running", "completed", "failed", "other"]


class HealthComponent(BaseModel):
    id: ComponentId
    status: HealthState
    reason_code: Reason
    source_kind: Literal["live", "simulated", "mock", "unverified"]
    checked_at: datetime
    latency_ms: float | None = Field(default=None, ge=0)
    worker_status: Literal["unknown"] | None = None
    verified_at: datetime | None = None
    last_attempt_at: datetime | None = None
    expires_at: datetime | None = None
    check_id: str | None = None
    reported_model: str | None = Field(default=None, max_length=256)
    model_identity: Literal["unconfirmed"] = "unconfirmed"
    reported_cost_usd: str | None = None
    cost_status: Literal["gateway_reported", "unavailable", "invalid"] = "unavailable"
    cost_confirmation: Literal["unconfirmed"] = "unconfirmed"


class JobHealthSummary(BaseModel):
    data_status: Literal["available", "empty", "unavailable"]
    counts: dict[JobState, int] | None
    failed_last_24h: int | None = Field(ge=0)
    last_updated_at: datetime | None


class IngestionHealthSummary(BaseModel):
    data_status: Literal["available", "empty", "unavailable"]
    counts: dict[RunState, int] | None
    failed_last_24h: int | None = Field(ge=0)
    last_completed_at: datetime | None


class HealthWindow(BaseModel):
    start: datetime
    end: datetime


class SystemHealthResponse(BaseModel):
    status: HealthState
    checked_at: datetime
    tenant_id: str
    window: HealthWindow
    components: list[HealthComponent]
    jobs: JobHealthSummary
    ingestion: IngestionHealthSummary


class ProviderCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
