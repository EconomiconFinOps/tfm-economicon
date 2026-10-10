"""Build showback from exact, scoped SQL aggregates without redistribution.

The caller owns source selection, tenancy, dates and overlap detection. This
service receives only aggregates of the selected normalized dimension. Its
provisional classifier mirrors JUP-017's economicon-minimum-v1 syntax and the
JUP-015 reference evaluator, not a corporate ownership catalog. No runtime
dependency on the unmerged JUP-015 tool is claimed; that integration can replace
this isolated policy boundary under a new version.
"""

from datetime import date
from decimal import Decimal, localcontext
import re
from typing import get_args

from app.schemas.showback import ShowbackDimension, ShowbackReport, UnassignedReason


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_CURRENCY = re.compile(r"[A-Z]{3}\Z")
_INVALID_VALUES = frozenset({
    "unknown", "n/a", "null", "none", "true", "false", "undefined", "unassigned", "-",
})
_ZERO = Decimal("0")


def classify_unit(value: object) -> tuple[str | None, UnassignedReason | None]:
    """Resolve one selected value, preserving case and never inferring aliases."""
    if value is None:
        return None, "missing"
    if not isinstance(value, str):
        return None, "invalid"
    selected = value.strip()
    if not selected:
        return None, "missing"
    if selected.casefold() in _INVALID_VALUES or _IDENTIFIER.fullmatch(selected) is None:
        return None, "invalid"
    return selected, None


def _decimal_places(value: Decimal) -> int:
    """Count significant fractional places without context-sensitive normalize."""
    if value.is_zero():
        return 0
    digits, exponent = value.as_tuple().digits, value.as_tuple().exponent
    trailing = 0
    for digit in reversed(digits):
        if digit != 0:
            break
        trailing += 1
    return max(0, -exponent - trailing)


def _amount(value: Decimal) -> str:
    if value.is_zero():
        return "0.00"
    result = format(value, "f")
    if "." not in result:
        return result + ".00"
    whole, fraction = result.split(".")
    return whole + "." + fraction.rstrip("0").ljust(2, "0")


def build_showback(
    rows: list[dict], *, start_date: date, end_date: date,
    dimension: ShowbackDimension, excluded_undated_count: int,
) -> ShowbackReport:
    """Preserve every selected charge, adjustment and zero exactly once.

    Invalid aggregate input is an error, never a successful zero-cost report.
    Missing and invalid labels remain in explicit unassigned buckets. Other
    dimensions cannot change attribution of the selected dimension.
    """
    if dimension not in get_args(ShowbackDimension) or start_date >= end_date:
        raise ValueError("Invalid showback selection")
    if (type(excluded_undated_count) is not int or excluded_undated_count < 0):
        raise ValueError("Invalid undated record count")

    for row in rows:
        cost, count, currency = row["cost"], row["record_count"], row["currency"]
        if (not isinstance(cost, Decimal) or not cost.is_finite()
                or _decimal_places(cost) > 12):
            raise ValueError("Showback requires finite exact costs at stored precision")
        if type(count) is not int or count < 1:
            raise ValueError("Invalid showback aggregate record count")
        if not isinstance(currency, str) or _CURRENCY.fullmatch(currency) is None:
            raise ValueError("Invalid showback currency")

    # Addition can grow by log10(row count). Reserve room for every fractional
    # place even when very large positive and negative amounts cancel.
    integer_digits = max((max(1, row["cost"].adjusted() + 1) for row in rows), default=1)
    fractional_digits = max((_decimal_places(row["cost"]) for row in rows), default=0)
    precision = max(28, integer_digits + fractional_digits + len(str(len(rows))) + 2)
    with localcontext() as context:
        context.prec = precision
        buckets: dict[str, dict] = {}
        for row in rows:
            bucket = buckets.setdefault(row["currency"], {
                "total": _ZERO, "count": 0, "groups": {},
                "unassigned": {reason: {"cost": _ZERO, "count": 0}
                               for reason in ("missing", "invalid")},
            })
            cost, count = row["cost"], row["record_count"]
            bucket["total"] += cost
            bucket["count"] += count
            unit, reason = classify_unit(row["value"])
            target = (bucket["unassigned"][reason] if reason else
                      bucket["groups"].setdefault(unit, {"cost": _ZERO, "count": 0}))
            target["cost"] += cost
            target["count"] += count

        currencies = []
        for currency, bucket in sorted(buckets.items()):
            assigned = sum((group["cost"] for group in bucket["groups"].values()), _ZERO)
            unassigned = sum((group["cost"] for group in bucket["unassigned"].values()), _ZERO)
            assigned_count = sum(group["count"] for group in bucket["groups"].values())
            unassigned_count = sum(group["count"] for group in bucket["unassigned"].values())
            difference = bucket["total"] - assigned - unassigned
            if difference != 0 or bucket["count"] != assigned_count + unassigned_count:
                raise ValueError("Showback reconciliation failed")
            currencies.append({
                "currency": currency,
                "total_cost": _amount(bucket["total"]),
                "assigned_cost": _amount(assigned),
                "unassigned_cost": _amount(unassigned),
                "record_count": bucket["count"],
                "assigned_record_count": assigned_count,
                "unassigned_record_count": unassigned_count,
                "groups": [
                    {"value": unit, "cost": _amount(group["cost"]), "record_count": group["count"]}
                    for unit, group in sorted(bucket["groups"].items())
                ],
                "unassigned": [
                    {"reason": reason, "cost": _amount(group["cost"]), "record_count": group["count"]}
                    for reason, group in bucket["unassigned"].items()
                ],
                "reconciliation_difference": _amount(difference),
            })

    partial = excluded_undated_count > 0 or any(item["unassigned_record_count"] for item in currencies)
    return ShowbackReport(
        dimension=dimension,
        period={"start_date": start_date, "end_date": end_date, "timezone": "UTC"},
        data_status="partial" if partial else ("available" if rows else "empty"),
        currencies=currencies,
        excluded_undated_count=excluded_undated_count,
    )
