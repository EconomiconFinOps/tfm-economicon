from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from itertools import groupby

from app.errors import ApiError
from app.models import (
    Granularity,
    GroupingType,
    QueryColumn,
    QueryDefinition,
    QueryFilter,
    QueryProperties,
    Timeframe,
)
from app.repository import CostRecord, CostRepository


class QueryEngine:
    def __init__(self, repository: CostRepository):
        self.repository = repository
        self.dimensions = frozenset(repository.mapping["dimensions"])
        self.tags = frozenset(repository.mapping["tags"]["supportedNames"])

    def execute(self, subscription_id: str, query: QueryDefinition) -> QueryProperties:
        if not self.repository.has_subscription(subscription_id):
            raise ApiError(404, "SubscriptionNotFound", "The subscription is not present in the fixture.")
        self._validate_supported_fields(query)
        start, end = self._date_interval(query)
        records = [
            record
            for record in self.repository.records
            if record.values[self.repository.scope_column].casefold() == subscription_id.casefold()
            and start <= datetime.combine(record.usage_date, time.min, tzinfo=UTC) < end
            and self._matches_filter(record, query.dataset.filter)
        ]
        columns = self._columns(query)
        rows = self._aggregate(records, query)
        return QueryProperties(columns=columns, rows=rows, next_link=None)

    def _validate_supported_fields(self, query: QueryDefinition) -> None:
        for grouping in query.dataset.grouping:
            supported = self.dimensions if grouping.type is GroupingType.dimension else self.tags
            if grouping.name not in supported:
                raise ApiError(400, "BadRequest", f"Unsupported {grouping.type.value.lower()}: {grouping.name}")
        self._validate_filter(query.dataset.filter)

    def _validate_filter(self, expression: QueryFilter | None) -> None:
        if expression is None:
            return
        for child in expression.and_ or expression.or_ or []:
            self._validate_filter(child)
        if expression.dimensions and expression.dimensions.name not in self.dimensions:
            raise ApiError(400, "BadRequest", f"Unsupported dimension: {expression.dimensions.name}")
        if expression.tags and expression.tags.name not in self.tags:
            raise ApiError(400, "BadRequest", f"Unsupported tag: {expression.tags.name}")

    def _date_interval(self, query: QueryDefinition) -> tuple[datetime, datetime]:
        if query.timeframe is Timeframe.custom:
            assert query.timePeriod is not None
            return query.timePeriod.from_.astimezone(UTC), query.timePeriod.to.astimezone(UTC)
        clock = self.repository.max_usage_date
        if query.timeframe is Timeframe.month_to_date:
            start = datetime.combine(clock.replace(day=1), time.min, tzinfo=UTC)
            end = datetime.combine(clock + timedelta(days=1), time.min, tzinfo=UTC)
            return start, end
        previous_month_end = clock.replace(day=1) - timedelta(days=1)
        start = datetime.combine(previous_month_end.replace(day=1), time.min, tzinfo=UTC)
        end = datetime.combine(previous_month_end + timedelta(days=1), time.min, tzinfo=UTC)
        return start, end

    def _matches_filter(self, record: CostRecord, expression: QueryFilter | None) -> bool:
        if expression is None:
            return True
        if expression.and_ is not None:
            return all(self._matches_filter(record, child) for child in expression.and_)
        if expression.or_ is not None:
            return any(self._matches_filter(record, child) for child in expression.or_)
        if expression.dimensions is not None:
            actual = self.repository.dimension_value(record, expression.dimensions.name)
            return self._matches_values(actual, expression.dimensions.values)
        assert expression.tags is not None
        actual = self.repository.tag_value(record, expression.tags.name)
        return self._matches_values(actual, expression.tags.values)

    @staticmethod
    def _matches_values(actual: str, expected: list[str]) -> bool:
        actual_folded = actual.casefold()
        return any(actual_folded == value.casefold() for value in expected)

    def _group_value(self, record: CostRecord, grouping_type: GroupingType, name: str) -> str:
        if grouping_type is GroupingType.dimension:
            return self.repository.dimension_value(record, name)
        return self.repository.tag_value(record, name)

    def _key(self, record: CostRecord, query: QueryDefinition) -> tuple:
        key: list[str | int] = [
            self._group_value(record, grouping.type, grouping.name)
            for grouping in query.dataset.grouping
        ]
        if query.dataset.granularity is Granularity.daily:
            key.append(int(record.usage_date.strftime("%Y%m%d")))
        key.append(record.values[self.repository.currency_column])
        return tuple(key)

    def _aggregate(self, records: list[CostRecord], query: QueryDefinition) -> list[list]:
        sorted_records = sorted(records, key=lambda record: self._sortable_key(self._key(record, query)))
        rows: list[list] = []
        for key, group in groupby(sorted_records, key=lambda record: self._key(record, query)):
            total = sum((record.cost for record in group), start=Decimal("0"))
            metrics = [self._number(total) for _ in query.dataset.aggregation.values()]
            rows.append([*metrics, *key])
        return rows

    @staticmethod
    def _sortable_key(key: tuple) -> tuple:
        return tuple(value.casefold() if isinstance(value, str) else value for value in key)

    @staticmethod
    def _number(value: Decimal) -> int | float:
        return int(value) if value == value.to_integral_value() else float(value)

    @staticmethod
    def _columns(query: QueryDefinition) -> list[QueryColumn]:
        columns = [
            QueryColumn(name=aggregation.name, type="Number")
            for aggregation in query.dataset.aggregation.values()
        ]
        columns.extend(
            QueryColumn(name=grouping.name, type="String") for grouping in query.dataset.grouping
        )
        if query.dataset.granularity is Granularity.daily:
            columns.append(QueryColumn(name="UsageDate", type="Number"))
        columns.append(QueryColumn(name="Currency", type="String"))
        return columns
