from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.clients.azure_cost import AzureCostQueryResult


class AzureCostNormalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedCostRecord:
    usage_date: date | None
    pretax_cost: Decimal
    currency: str
    dimensions: dict[str, int | float | str]
    source_row_hash: str


class AzureCostNormalizer:
    def normalize(self, result: AzureCostQueryResult) -> tuple[NormalizedCostRecord, ...]:
        return tuple(self._normalize_row(row) for row in result.rows)

    @staticmethod
    def _normalize_row(row: dict[str, int | float | str]) -> NormalizedCostRecord:
        raw_cost = row.get("PreTaxCost")
        if isinstance(raw_cost, bool) or not isinstance(raw_cost, (int, float, Decimal)):
            raise AzureCostNormalizationError("PreTaxCost must be numeric")
        try:
            cost = Decimal(str(raw_cost))
        except (InvalidOperation, ValueError) as exc:
            raise AzureCostNormalizationError("PreTaxCost cannot be normalized") from exc
        if not cost.is_finite():
            raise AzureCostNormalizationError("PreTaxCost must be finite")
        if cost.is_zero():
            cost = Decimal("0")

        currency = row.get("Currency")
        if not isinstance(currency, str) or not currency.strip():
            raise AzureCostNormalizationError("Currency cannot be normalized")
        currency = currency.strip().upper()
        if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
            raise AzureCostNormalizationError("Currency must be a three-letter code")

        usage_date = _usage_date(row.get("UsageDate"))
        dimensions = {
            key: value
            for key, value in row.items()
            if key not in {"PreTaxCost", "Currency", "UsageDate"}
        }
        canonical = json.dumps(
            {
                "currency": currency,
                "dimensions": dimensions,
                "pretaxCost": format(cost.normalize(), "f"),
                "usageDate": usage_date.isoformat() if usage_date else None,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return NormalizedCostRecord(
            usage_date=usage_date,
            pretax_cost=cost,
            currency=currency,
            dimensions=dimensions,
            source_row_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )


def _usage_date(value: int | float | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or len(str(value)) != 8:
        raise AzureCostNormalizationError("UsageDate must be a yyyyMMdd integer")
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except ValueError as exc:
        raise AzureCostNormalizationError("UsageDate is not a valid date") from exc
