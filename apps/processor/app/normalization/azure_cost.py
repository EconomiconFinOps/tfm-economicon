from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TypeAlias

from app.clients.azure_cost import AzureCostQueryResult


DimensionValue: TypeAlias = int | float | str
_MISSING = object()
_TAG_PAIR = re.compile(r'"([^"\\]+)"\s*:\s*"([^"\\]*)"')
_TAG_KEY_SEPARATOR = re.compile(r"[^a-z0-9]+")

_DIMENSION_ALIASES = {
    "billing_account_id": ("BillingAccountId",),
    "subscription_name": ("SubscriptionName", "SubAccountName"),
    "resource_group": ("ResourceGroup", "ResourceGroupName", "x_ResourceGroupName"),
    "service_name": ("ServiceName", "MeterCategory", "ServiceCategory"),
}
_QUANTITY_ALIASES = ("ConsumedQuantity", "UsageQuantity", "Quantity")
_UNIT_ALIASES = ("ConsumedUnit", "UnitOfMeasure", "Unit")
_INDIVIDUAL_TAG_ALIASES = {
    "cost_center": ("CostCenter", "costcenter"),
    "project": ("Project",),
    "environment": ("env", "Environment"),
    "organization": ("org", "Organization"),
}


class AzureCostNormalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedCostRecord:
    usage_date: date | None
    pretax_cost: Decimal
    currency: str
    billing_account_id: str | None
    subscription_name: str | None
    resource_group: str | None
    service_name: str | None
    project: str | None
    consumed_quantity: Decimal | None
    consumed_unit: str | None
    tags: dict[str, str]
    dimensions: dict[str, DimensionValue]
    source_row_hash: str


class AzureCostNormalizer:
    def normalize(self, result: AzureCostQueryResult) -> tuple[NormalizedCostRecord, ...]:
        return tuple(self._normalize_row(row) for row in result.rows)

    @staticmethod
    def _normalize_row(row: dict[str, DimensionValue]) -> NormalizedCostRecord:
        remaining = dict(row)
        cost = _required_decimal("PreTaxCost", _take(remaining, ("PreTaxCost",)))
        currency = _required_currency(_take(remaining, ("Currency",)))
        usage_date = _usage_date(_take(remaining, ("UsageDate",)))

        promoted = {
            field: _optional_text(field, _take(remaining, aliases))
            for field, aliases in _DIMENSION_ALIASES.items()
        }
        quantity_value = _take(remaining, _QUANTITY_ALIASES)
        unit_value = _take(remaining, _UNIT_ALIASES)
        consumed_quantity = _optional_decimal("ConsumedQuantity", quantity_value)
        consumed_unit = _optional_text("consumed_unit", unit_value)
        if (consumed_quantity is None) != (consumed_unit is None):
            raise AzureCostNormalizationError(
                "ConsumedQuantity and ConsumedUnit must be supplied together"
            )

        tags = _normalized_tags(remaining)
        project = tags.get("project")
        dimensions = {
            key: _dimension_value(key, value)
            for key, value in remaining.items()
        }
        canonical = {
            "billingAccountId": promoted["billing_account_id"],
            "consumedQuantity": _canonical_decimal(consumed_quantity),
            "consumedUnit": consumed_unit,
            "currency": currency,
            "dimensions": dimensions,
            "pretaxCost": _canonical_decimal(cost),
            "project": project,
            "resourceGroup": promoted["resource_group"],
            "serviceName": promoted["service_name"],
            "subscriptionName": promoted["subscription_name"],
            "tags": tags,
            "usageDate": usage_date.isoformat() if usage_date else None,
        }
        source_row_hash = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return NormalizedCostRecord(
            usage_date=usage_date,
            pretax_cost=cost,
            currency=currency,
            billing_account_id=promoted["billing_account_id"],
            subscription_name=promoted["subscription_name"],
            resource_group=promoted["resource_group"],
            service_name=promoted["service_name"],
            project=project,
            consumed_quantity=consumed_quantity,
            consumed_unit=consumed_unit,
            tags=tags,
            dimensions=dimensions,
            source_row_hash=source_row_hash,
        )


def _take(row: dict[str, DimensionValue], aliases: tuple[str, ...]) -> object:
    expected = {alias.casefold() for alias in aliases}
    matches = [(key, value) for key, value in row.items() if key.casefold() in expected]
    if not matches:
        return _MISSING
    values = {_comparable(value) for _, value in matches}
    if len(values) > 1:
        raise AzureCostNormalizationError(
            f"Conflicting aliases for {aliases[0]}: {', '.join(key for key, _ in matches)}"
        )
    for key, _ in matches:
        row.pop(key)
    return matches[0][1]


def _comparable(value: DimensionValue) -> tuple[str, str]:
    if isinstance(value, bool):
        return "bool", str(value)
    if isinstance(value, (int, float, Decimal)):
        try:
            return "number", _canonical_decimal(Decimal(str(value))) or ""
        except InvalidOperation:
            return "number", str(value)
    return "text", value.strip().casefold()


def _required_decimal(field: str, value: object) -> Decimal:
    parsed = _optional_decimal(field, value)
    if parsed is None:
        raise AzureCostNormalizationError(f"{field} must be numeric")
    return parsed


def _optional_decimal(field: str, value: object) -> Decimal | None:
    if value is _MISSING or value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise AzureCostNormalizationError(f"{field} must be numeric")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AzureCostNormalizationError(f"{field} cannot be normalized") from exc
    if not parsed.is_finite():
        raise AzureCostNormalizationError(f"{field} must be finite")
    return Decimal("0") if parsed.is_zero() else parsed


def _required_currency(value: object) -> str:
    currency = _optional_text("currency", value)
    if currency is None:
        raise AzureCostNormalizationError("Currency cannot be normalized")
    currency = currency.upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise AzureCostNormalizationError("Currency must be a three-letter code")
    return currency


def _optional_text(field: str, value: object) -> str | None:
    if value is _MISSING or value is None:
        return None
    if not isinstance(value, str):
        raise AzureCostNormalizationError(f"{field} must be text")
    normalized = value.strip()
    return normalized or None


def _normalized_tags(row: dict[str, DimensionValue]) -> dict[str, str]:
    tags: dict[str, str] = {}
    raw_tags = _take(row, ("Tags",))
    if raw_tags is not _MISSING:
        if not isinstance(raw_tags, str):
            raise AzureCostNormalizationError("Tags must be text")
        candidate = raw_tags.strip()
        if candidate:
            parsed = _parse_tag_map(candidate)
            for key, value in parsed.items():
                _merge_tag(tags, _canonical_tag_key(key), value)

    for canonical, aliases in _INDIVIDUAL_TAG_ALIASES.items():
        value = _optional_text(canonical, _take(row, aliases))
        if value is not None:
            _merge_tag(tags, canonical, value)
    return dict(sorted(tags.items()))


def _parse_tag_map(value: str) -> dict[str, str]:
    candidate = value if value.startswith("{") else "{" + value + "}"
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return {
                str(key): str(item).strip()
                for key, item in parsed.items()
                if str(item).strip()
            }
    except json.JSONDecodeError:
        pass
    return {key: item.strip() for key, item in _TAG_PAIR.findall(value) if item.strip()}


def _canonical_tag_key(value: str) -> str:
    normalized = _TAG_KEY_SEPARATOR.sub("_", value.strip().casefold()).strip("_")
    aliases = {
        "costcenter": "cost_center",
        "cost_centre": "cost_center",
        "env": "environment",
        "org": "organization",
    }
    return aliases.get(normalized, normalized)


def _merge_tag(tags: dict[str, str], key: str, value: str) -> None:
    if not key:
        return
    existing = tags.get(key)
    if existing is not None and existing.casefold() != value.casefold():
        raise AzureCostNormalizationError(f"Conflicting values for tag {key}")
    tags[key] = existing or value


def _dimension_value(key: str, value: DimensionValue) -> DimensionValue:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise AzureCostNormalizationError(f"Dimension {key} has an unsupported value")
    return value.strip() if isinstance(value, str) else value


def _canonical_decimal(value: Decimal | None) -> str | None:
    return format(value.normalize(), "f") if value is not None else None


def _usage_date(value: object) -> date | None:
    if value is _MISSING or value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or len(str(value)) != 8:
        raise AzureCostNormalizationError("UsageDate must be a yyyyMMdd integer")
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except ValueError as exc:
        raise AzureCostNormalizationError("UsageDate is not a valid date") from exc
