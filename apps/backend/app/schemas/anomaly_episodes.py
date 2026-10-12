"""Stored cost-anomaly candidate episodes (JUP-114, ADR-0019)."""
from datetime import date, datetime
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.billing import DecimalString

EpisodeStatus = Literal["new", "investigating", "resolved", "false_positive"]


class AnomalyEpisode(BaseModel):
    id: str
    kind: Literal["cost_anomaly_candidate"]
    currency: str
    service: str | None
    start_date: date
    last_seen_date: date
    observation: Literal["observed", "no_longer_observed"]
    no_longer_observed_on: date | None
    reference_daily_cost: DecimalString
    opening_observed_cost: DecimalString
    accumulated_impact: DecimalString
    impact_day_count: int
    impact_through_date: date
    severity: Literal["P1", "P2", "P3"]
    status: EpisodeStatus
    status_changed_by: str | None
    status_changed_at: datetime | None
    first_reviewed_at: datetime | None
    first_reviewed_by: str | None
    closed_at: datetime | None
    closure_reason: str | None
    previous_episode_id: str | None
    rules_version: str
    rules: dict
    cause_status: Literal["not_established"]
    limitations: list[str]
    created_at: datetime
    updated_at: datetime


class AnomalyEpisodeList(BaseModel):
    contract_version: Literal[1] = 1
    scope: Literal["open", "all"]
    episodes: list[AnomalyEpisode]


class SkippedDay(BaseModel):
    date: date
    reason: Literal["not_observed", "reference_incomplete"]


class DateRange(BaseModel):
    start_date: date
    end_date: date


class AnomalyDetectionRun(BaseModel):
    status: Literal["completed", "up_to_date", "insufficient_data"]
    rules_version: str
    last_complete_day: date | None
    evaluated_days: list[date]
    skipped_days: list[SkippedDay]
    unevaluated_range: DateRange | None
    unsupported_currencies: list[str]
    opened: int
    continued: int
    no_longer_observed: int


class EpisodeStatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EpisodeStatus
    reason: str | None = None

    @model_validator(mode="after")
    def closing_reason(self):
        closing = self.status in {"resolved", "false_positive"}
        if not closing:
            if self.reason is not None:
                raise ValueError("A reason is only accepted when closing an episode")
            return self
        reason = (self.reason or "").strip()
        hidden = any(unicodedata.category(char).startswith("C") or unicodedata.category(char) in {"Zl", "Zp"}
                     for char in reason)
        if not 1 <= len(reason) <= 500 or hidden:
            raise ValueError("Closing requires a reason of 1 to 500 characters without control characters")
        self.reason = reason
        return self
