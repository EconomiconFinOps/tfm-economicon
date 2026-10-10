"""Candidates with incomplete metadata; financial allocation is not evaluated."""
from typing import Literal

from pydantic import BaseModel

from app.schemas.billing import BillingPeriod, DecimalString


class UnallocatedGroup(BaseModel):
    missing_or_invalid_tags: list[str]
    reason: Literal["no_owner", "unclassified", "no_owner_and_unclassified"]
    record_count: int
    positive_cost: DecimalString
    negative_adjustments: DecimalString
    net_cost: DecimalString


class UnallocatedCurrency(BaseModel):
    currency: str
    record_count: int
    candidate_record_count: int
    positive_cost: DecimalString
    complete_metadata_cost: DecimalString
    candidate_cost: DecimalString
    negative_adjustments: DecimalString
    complete_metadata_negative_adjustments: DecimalString
    candidate_negative_adjustments: DecimalString
    net_cost: DecimalString
    complete_metadata_net_cost: DecimalString
    candidate_net_cost: DecimalString
    candidate_percent: DecimalString | None
    no_positive_cost_reason: Literal["negative_adjustments_only", "zero_cost_only"] | None
    groups: list[UnallocatedGroup]


class UnallocatedCost(BaseModel):
    contract_version: Literal[1] = 1
    detection_basis: Literal["observed_required_tags"]
    allocation_status: Literal["not_evaluated"]
    policy_version: str
    required_tags: list[str]
    period: BillingPeriod
    data_status: Literal["available", "partial", "empty"]
    excluded_undated_count: int
    currencies: list[UnallocatedCurrency]
