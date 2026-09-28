from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field


BillingGrouping = Literal["subscription", "resource_group", "service", "project", "tag"]
DecimalString = Annotated[str, Field(pattern=r"^-?(0|[1-9][0-9]*)\.[0-9]{2}$")]


class AmbiguousCostSource(ValueError):
    pass


class BillingPeriod(BaseModel):
    start_date: date
    end_date: date
    timezone: Literal["UTC"] = "UTC"


class BillingTotal(BaseModel):
    currency: str
    cost: DecimalString
    record_count: int


class BillingGroup(BillingTotal):
    subscription_id: str | None
    value: str | None


class BillingSummary(BaseModel):
    contract_version: Literal[2] = 2
    period: BillingPeriod
    group_by: BillingGrouping
    tag_key: str | None
    data_status: Literal["available", "partial", "empty"]
    totals: list[BillingTotal]
    groups: list[BillingGroup]
    missing_dimension_count: int
    excluded_undated_count: int
    monthly_spend: DecimalString | None
    savings_identified: None = None
    open_ingestions: int
    currency: str | None
