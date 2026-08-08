from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator


class QueryType(str, Enum):
    usage = "Usage"
    actual_cost = "ActualCost"


class Timeframe(str, Enum):
    custom = "Custom"
    month_to_date = "MonthToDate"
    the_last_month = "TheLastMonth"


class Granularity(str, Enum):
    daily = "Daily"
    none = "None"


class GroupingType(str, Enum):
    dimension = "Dimension"
    tag = "Tag"


class QueryTimePeriod(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> "QueryTimePeriod":
        if self.from_.utcoffset() is None or self.to.utcoffset() is None:
            raise ValueError("timePeriod.from and timePeriod.to must include a timezone")
        if self.from_ >= self.to:
            raise ValueError("timePeriod.from must be earlier than timePeriod.to")
        return self


class QueryAggregation(BaseModel):
    name: Literal["PreTaxCost"]
    function: Literal["Sum"]


class QueryGrouping(BaseModel):
    type: GroupingType
    name: str = Field(min_length=1)


class QueryComparisonExpression(BaseModel):
    name: str = Field(min_length=1)
    operator: Literal["In"]
    values: Annotated[list[str], Field(min_length=1)]


class QueryFilter(BaseModel):
    and_: list["QueryFilter"] | None = Field(default=None, alias="and")
    or_: list["QueryFilter"] | None = Field(default=None, alias="or")
    dimensions: QueryComparisonExpression | None = None
    tags: QueryComparisonExpression | None = None

    @model_validator(mode="after")
    def validate_expression(self) -> "QueryFilter":
        populated = [
            self.and_ is not None,
            self.or_ is not None,
            self.dimensions is not None,
            self.tags is not None,
        ]
        if sum(populated) != 1:
            raise ValueError("filter must contain exactly one of and, or, dimensions or tags")
        if self.and_ is not None and len(self.and_) < 2:
            raise ValueError("filter.and requires at least two operands")
        if self.or_ is not None and len(self.or_) < 2:
            raise ValueError("filter.or requires at least two operands")
        return self


class QueryDataset(BaseModel):
    granularity: Granularity
    aggregation: Annotated[dict[str, QueryAggregation], Field(min_length=1, max_length=2)]
    grouping: Annotated[list[QueryGrouping], Field(max_length=2)] = Field(default_factory=list)
    filter: QueryFilter | None = None


class QueryDefinition(BaseModel):
    type: QueryType
    timeframe: Timeframe
    timePeriod: QueryTimePeriod | None = None
    dataset: QueryDataset

    @model_validator(mode="after")
    def validate_timeframe(self) -> "QueryDefinition":
        if self.timeframe is Timeframe.custom and self.timePeriod is None:
            raise ValueError("timePeriod is required when timeframe is Custom")
        if self.timeframe is not Timeframe.custom and self.timePeriod is not None:
            raise ValueError("timePeriod is only supported when timeframe is Custom")
        return self


class QueryColumn(BaseModel):
    name: str
    type: Literal["Number", "String"]


class QueryProperties(BaseModel):
    columns: list[QueryColumn]
    rows: list[list[Any]]
    next_link: str | None = Field(serialization_alias="nextLink")


class QueryResult(BaseModel):
    id: str
    name: str
    type: Literal["microsoft.costmanagement/Query"]
    properties: QueryProperties
