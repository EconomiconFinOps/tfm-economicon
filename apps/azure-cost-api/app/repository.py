from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


TAG_PAIR = re.compile(r'"([^"\\]+)"\s*:\s*"([^"\\]*)"')


class DatasetError(RuntimeError):
    """Raised when the configured fixture cannot satisfy the contract."""


@dataclass(frozen=True)
class CostRecord:
    values: Mapping[str, str]
    usage_date: date
    cost: Decimal
    tags: Mapping[str, str]


def parse_tags(raw: str) -> Mapping[str, str]:
    raw = raw.strip()
    if not raw:
        return MappingProxyType({})
    candidate = raw if raw.startswith("{") else "{" + raw + "}"
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return MappingProxyType({str(key): str(value) for key, value in parsed.items()})
    except json.JSONDecodeError:
        pass
    return MappingProxyType(dict(TAG_PAIR.findall(raw)))


class CostRepository:
    def __init__(self, dataset_path: Path, mapping_path: Path):
        self.dataset_path = dataset_path
        self.mapping_path = mapping_path
        self.mapping = self._load_mapping(mapping_path)
        self.scope_column = self.mapping["scope"]["sourceColumn"]
        self.date_column = self.mapping["systemColumns"]["UsageDate"]["sourceColumn"]
        self.currency_column = self.mapping["systemColumns"]["Currency"]["sourceColumn"]
        self.cost_column = self.mapping["metrics"]["PreTaxCost"]["sourceColumn"]
        self.tags_column = self.mapping["tags"]["sourceColumn"]
        self.records, self.columns = self._load_records(dataset_path)
        self.subscription_ids = frozenset(
            record.values[self.scope_column] for record in self.records
        )
        self.max_usage_date = max(record.usage_date for record in self.records)

    @staticmethod
    def _load_mapping(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetError(f"Cannot load mapping file: {path}") from exc

    def _required_columns(self) -> set[str]:
        columns = {self.mapping["scope"]["sourceColumn"]}
        columns.update(item["sourceColumn"] for item in self.mapping["metrics"].values())
        columns.update(item["sourceColumn"] for item in self.mapping["dimensions"].values())
        columns.update(item["sourceColumn"] for item in self.mapping["systemColumns"].values())
        columns.add(self.mapping["tags"]["sourceColumn"])
        return columns

    def _load_records(self, path: Path) -> tuple[tuple[CostRecord, ...], frozenset[str]]:
        try:
            source = path.open(encoding="utf-8-sig", newline="")
        except OSError as exc:
            raise DatasetError(f"Cannot open Azure cost fixture: {path}") from exc

        records: list[CostRecord] = []
        with source:
            reader = csv.DictReader(source)
            columns = frozenset(reader.fieldnames or [])
            missing = sorted(self._required_columns() - columns)
            if missing:
                raise DatasetError(f"Fixture is missing required columns: {', '.join(missing)}")
            for row_number, row in enumerate(reader, start=2):
                try:
                    usage_date = datetime.strptime(row[self.date_column], "%m/%d/%Y").date()
                    cost = Decimal(row[self.cost_column])
                except (KeyError, ValueError, InvalidOperation) as exc:
                    raise DatasetError(f"Invalid fixture row {row_number}") from exc
                records.append(
                    CostRecord(
                        values=MappingProxyType(dict(row)),
                        usage_date=usage_date,
                        cost=cost,
                        tags=parse_tags(row[self.tags_column]),
                    )
                )
        if not records:
            raise DatasetError("Azure cost fixture contains no rows")
        return tuple(records), columns

    def has_subscription(self, subscription_id: str) -> bool:
        expected = subscription_id.casefold()
        return any(item.casefold() == expected for item in self.subscription_ids)

    def dimension_value(self, record: CostRecord, name: str) -> str:
        source_column = self.mapping["dimensions"][name]["sourceColumn"]
        return record.values[source_column]

    def tag_value(self, record: CostRecord, name: str) -> str:
        expected = name.casefold()
        return next((value for key, value in record.tags.items() if key.casefold() == expected), "")
