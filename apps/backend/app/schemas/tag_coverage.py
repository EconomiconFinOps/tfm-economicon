from typing import Literal

from pydantic import BaseModel

from app.schemas.billing import BillingPeriod, DecimalString


class CurrencyTagCoverage(BaseModel):
    currency: str
    record_count: int
    compliant_record_count: int
    noncompliant_record_count: int
    positive_cost: DecimalString
    compliant_cost: DecimalString
    noncompliant_cost: DecimalString
    negative_adjustments: DecimalString
    compliant_negative_adjustments: DecimalString
    noncompliant_negative_adjustments: DecimalString
    net_cost: DecimalString
    compliant_net_cost: DecimalString
    noncompliant_net_cost: DecimalString
    compliant_percent: DecimalString | None
    noncompliant_percent: DecimalString | None
    no_positive_cost_reason: Literal["zero_cost_only", "negative_adjustments_only"] | None
    missing_or_invalid_tag_counts: dict[str, int]


class TagCoverage(BaseModel):
    contract_version: Literal[1] = 1
    policy_version: Literal["economicon-minimum-v1"]
    required_tags: list[str]
    period: BillingPeriod
    data_status: Literal["available", "partial", "empty"]
    excluded_undated_count: int
    currencies: list[CurrencyTagCoverage]
