"""Exact, currency-separated organizational cost attribution (JUP-027)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.billing import BillingPeriod


ShowbackDimension = Literal["owner", "project", "application", "cost_center"]
ExactCost = Annotated[str, Field(pattern=r"^-?(0|[1-9][0-9]*)\.[0-9]{2,12}$")]
RecordCount = Annotated[int, Field(ge=0)]
UnassignedReason = Literal["missing", "invalid"]


class ShowbackGroup(BaseModel):
    value: str
    cost: ExactCost
    record_count: RecordCount


class ShowbackUnassigned(BaseModel):
    reason: UnassignedReason
    cost: ExactCost
    record_count: RecordCount


class ShowbackCurrency(BaseModel):
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    total_cost: ExactCost
    assigned_cost: ExactCost
    unassigned_cost: ExactCost
    record_count: RecordCount
    assigned_record_count: RecordCount
    unassigned_record_count: RecordCount
    groups: list[ShowbackGroup]
    unassigned: list[ShowbackUnassigned]
    reconciliation_difference: ExactCost


class ShowbackReport(BaseModel):
    contract_version: Literal[1] = 1
    dimension: ShowbackDimension
    policy_version: Literal["jup027-provisional-syntax-v1-pending-jup015"] = (
        "jup027-provisional-syntax-v1-pending-jup015"
    )
    catalog_status: Literal["not_provided"] = "not_provided"
    organizationally_valid: None = None
    period: BillingPeriod
    data_status: Literal["available", "partial", "empty"]
    currencies: list[ShowbackCurrency]
    excluded_undated_count: RecordCount
