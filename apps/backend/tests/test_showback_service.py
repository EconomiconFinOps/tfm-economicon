"""JUP-027 independent attribution examples; no database or taxonomy catalog."""

from datetime import date
from decimal import Decimal, localcontext

import pytest

from app.services.showback import build_showback, classify_unit


START = date(2024, 6, 1)
END = date(2024, 7, 1)


def row(value, cost, *, currency="EUR", count=1):
    return {"value": value, "cost": Decimal(cost), "currency": currency, "record_count": count}


def report(rows, **options):
    return build_showback(rows, start_date=START, end_date=END,
                          dimension=options.pop("dimension", "owner"),
                          excluded_undated_count=options.pop("excluded_undated_count", 0),
                          **options).model_dump(mode="json")


@pytest.mark.parametrize("dimension", ["owner", "project", "application", "cost_center"])
def test_selected_dimension_receives_full_signed_cost_once(dimension):
    result = report([
        row("platform", "80.004", count=2),
        row("platform", "-10.005"),
        row("finance", "20.006"),
        row(None, "5.001"),
        row(" UNKNOWN ", "-2.002"),
        row(None, "0"),
    ], dimension=dimension)
    assert result["dimension"] == dimension
    assert result["contract_version"] == 1
    assert result["policy_version"] == "jup027-provisional-syntax-v1-pending-jup015"
    assert result["catalog_status"] == "not_provided"
    assert result["organizationally_valid"] is None
    assert result["period"] == {
        "start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC",
    }
    assert result["data_status"] == "partial"
    assert result["currencies"] == [{
        "currency": "EUR", "total_cost": "93.004", "assigned_cost": "90.005",
        "unassigned_cost": "2.999", "record_count": 7,
        "assigned_record_count": 4, "unassigned_record_count": 3,
        "groups": [
            {"value": "finance", "cost": "20.006", "record_count": 1},
            {"value": "platform", "cost": "69.999", "record_count": 3},
        ],
        "unassigned": [
            {"reason": "missing", "cost": "5.001", "record_count": 2},
            {"reason": "invalid", "cost": "-2.002", "record_count": 1},
        ],
        "reconciliation_difference": "0.00",
    }]


def test_exact_reconciliation_survives_large_values_and_small_global_decimal_context():
    # Each value fits DECIMAL(38,12); their sum exceeds its integer width and
    # Python's default 28 significant digits. A float or rounded subtotal fails.
    rows = [
        row("alpha", "99999999999999999999999999.999999999999"),
        row("beta", "99999999999999999999999999.999999999999"),
        row(None, "0.000000000002"),
    ]
    with localcontext() as context:
        context.prec = 6
        result = report(rows)["currencies"][0]
        assert context.prec == 6
    assert result["total_cost"] == "200000000000000000000000000.00"
    assert result["assigned_cost"] == "199999999999999999999999999.999999999998"
    assert result["unassigned_cost"] == "0.000000000002"
    assert result["reconciliation_difference"] == "0.00"
    assert [group["cost"] for group in result["groups"]] == [
        "99999999999999999999999999.999999999999",
        "99999999999999999999999999.999999999999",
    ]


def test_cancellation_preserves_small_remainder_independently_of_input_order():
    rows = [
        row("same", "99999999999999999999999999.999999999999"),
        row("same", "0.000000000001"),
        row("same", "-99999999999999999999999999.999999999999"),
    ]
    forward = report(rows)
    assert forward == report(list(reversed(rows)))
    currency = forward["currencies"][0]
    assert currency["total_cost"] == currency["assigned_cost"] == "0.000000000001"
    assert currency["groups"] == [{"value": "same", "cost": "0.000000000001", "record_count": 3}]


def test_currency_separation_and_deterministic_case_sensitive_units():
    rows = [row("Z", "-2", currency="USD"), row("team", "0.005"),
            row(" Team ", "0.005"), row("Team", "0.001"),
            row(None, "-1", currency="GBP")]
    result = report(rows)
    assert result == report(list(reversed(rows)))
    assert [item["currency"] for item in result["currencies"]] == ["EUR", "GBP", "USD"]
    assert [item["total_cost"] for item in result["currencies"]] == ["0.011", "-1.00", "-2.00"]
    assert result["currencies"][0]["groups"] == [
        {"value": "Team", "cost": "0.006", "record_count": 2},
        {"value": "team", "cost": "0.005", "record_count": 1},
    ]


def test_empty_zero_and_cancelled_unassigned_have_distinct_status_and_counts():
    empty = report([])
    assert empty["data_status"] == "empty" and empty["currencies"] == []
    undated = report([], excluded_undated_count=2)
    assert undated["data_status"] == "partial" and undated["currencies"] == []
    assert undated["excluded_undated_count"] == 2
    zero = report([row("platform", "-0.000000000000")])
    assert zero["data_status"] == "available"
    assert zero["currencies"][0]["total_cost"] == "0.00"
    assert zero["currencies"][0]["record_count"] == 1
    cancelled = report([row(None, "7"), row(None, "-7")])
    assert cancelled["data_status"] == "partial"
    assert cancelled["currencies"][0]["total_cost"] == "0.00"
    assert cancelled["currencies"][0]["unassigned_record_count"] == 2


@pytest.mark.parametrize("value,expected", [
    (None, (None, "missing")), (" \t ", (None, "missing")),
    (" Unknown ", (None, "invalid")), ("unassigned", (None, "invalid")),
    ("N/A", (None, "invalid")), ("none", (None, "invalid")),
    ("true", (None, "invalid")), ("false", (None, "invalid")),
    ("null", (None, "invalid")), ("undefined", (None, "invalid")),
    ("-", (None, "invalid")), ("_team", (None, "invalid")),
    ("team/ops", (None, "invalid")), ("team\nops", (None, "invalid")),
    ("équipo", (None, "invalid")), ("a" * 129, (None, "invalid")),
    (True, (None, "invalid")), (123, (None, "invalid")),
    (" team.ops:alpha-1 ", ("team.ops:alpha-1", None)),
    ("a" * 128, ("a" * 128, None)),
])
def test_provisional_classifier_does_not_certify_a_catalog(value, expected):
    assert classify_unit(value) == expected


@pytest.mark.parametrize("cost", [Decimal("NaN"), Decimal("Infinity"),
                                  Decimal("-Infinity"), Decimal("0.0000000000001"),
                                  0.1, "1.00"])
def test_invalid_cost_is_an_error_instead_of_a_zero_or_rounded_result(cost):
    with pytest.raises(ValueError, match="finite exact costs"):
        report([{**row("team", "1"), "cost": cost}])


@pytest.mark.parametrize("patch", [{"currency": "eur"}, {"currency": "EURO"},
                                   {"record_count": 0}, {"record_count": -1},
                                   {"record_count": True}, {"record_count": 1.5}])
def test_invalid_aggregate_metadata_is_rejected(patch):
    with pytest.raises(ValueError):
        report([{**row("team", "1"), **patch}])


def test_non_significant_decimal_zeros_do_not_cause_rounding_or_rejection():
    result = report([row("team", "1.000000000000000"), row("team", "1E+25")])
    assert result["currencies"][0]["total_cost"] == "10000000000000000000000001.00"


@pytest.mark.parametrize("dimension", ["organization", "environment", "subscription"])
def test_non_showback_dimension_is_rejected(dimension):
    with pytest.raises(ValueError, match="selection"):
        report([], dimension=dimension)


@pytest.mark.parametrize("count", [-1, True, 0.5])
def test_invalid_undated_count_is_rejected(count):
    with pytest.raises(ValueError, match="undated"):
        report([], excluded_undated_count=count)


def test_invalid_period_is_rejected():
    with pytest.raises(ValueError, match="selection"):
        build_showback([], start_date=END, end_date=START, dimension="owner",
                       excluded_undated_count=0)
