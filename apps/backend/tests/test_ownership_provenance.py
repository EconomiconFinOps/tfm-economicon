"""JUP-037 opt-in provenance over the exact authorized billing snapshot."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.db.database import Database
from app.schemas.billing import AmbiguousCostSource
from billing_support import TOTALS, billing_schema, cost_reference, insert_cost, insert_run
from tenant_isolation_support import tenant_cockroach_database


START, END = date(2024, 6, 1), date(2024, 7, 1)
PERIOD_PROVENANCE = {
    "ingestion_ids": ["run-a", "run-b"],
    "first_usage_date": "2024-06-01",
    "last_usage_date": "2024-06-30",
    "observed_day_count": 3,
}
EMPTY_PROVENANCE = {
    "ingestion_ids": [], "first_usage_date": None,
    "last_usage_date": None, "observed_day_count": 0,
}


def test_default_response_remains_compatible_without_provenance_columns():
    # The existing billing double deliberately lacks provenance columns. This
    # checks the opt-in boundary; it is not evidence that SQL scoping is correct.
    row = {
        "kind": "total", "currency": "EUR", "cost": Decimal("1.005"),
        "record_count": 1, "undated": 0, "missing": 0, "ambiguous": 0,
    }
    db = Database.__new__(Database)
    db.engine = MagicMock()
    connection = db.engine.connect.return_value.execution_options.return_value.__enter__.return_value
    connection.execute.return_value.mappings.return_value.all.return_value = [row]
    connection.execute.return_value.scalar_one.return_value = 0

    result = db.fetch_billing_summary("tenant-a", start_date=START, end_date=END, group_by="project")

    assert "provenance" not in result
    assert result["contract_version"] == 2
    assert result["totals"] == [{"currency": "EUR", "cost": "1.01", "record_count": 1}]
    assert result["monthly_spend"] == "1.01"


@pytest.mark.parametrize("group_by,tag_key", [("project", None), ("tag", "application")])
def test_real_provenance_matches_completed_authorized_period_and_preserves_billing(cost_reference, group_by, tag_key):
    db = cost_reference
    arguments = {"start_date": START, "end_date": END, "group_by": group_by, "tag_key": tag_key}

    original = db.fetch_billing_summary("tenant-a", **arguments)
    enriched = db.fetch_billing_summary("tenant-a", **arguments, include_provenance=True)

    assert "provenance" not in original
    assert enriched.pop("provenance") == PERIOD_PROVENANCE
    assert enriched == original
    assert original["totals"] == TOTALS
    # Fixture includes foreign tenant, mismatched tenant/subscription joins,
    # incomplete ingestions, undated rows and end-exclusive rows: none can
    # contribute their ingestion IDs or observed days to PERIOD_PROVENANCE.
    assert original["excluded_undated_count"] == 1


def test_real_empty_period_has_no_provenance_even_with_undated_records(cost_reference):
    result = cost_reference.fetch_billing_summary(
        "tenant-a", start_date=date(2024, 8, 1), end_date=date(2024, 9, 1),
        group_by="tag", tag_key="owner", include_provenance=True,
    )

    assert result["provenance"] == EMPTY_PROVENANCE
    assert result["totals"] == []
    assert result["excluded_undated_count"] == 1


def test_real_other_tenant_provenance_is_scoped(cost_reference):
    result = cost_reference.fetch_billing_summary(
        "tenant-b", start_date=START, end_date=END, group_by="project", include_provenance=True,
    )

    assert result["provenance"] == {
        "ingestion_ids": ["foreign"], "first_usage_date": "2024-06-15",
        "last_usage_date": "2024-06-15", "observed_day_count": 1,
    }
    assert result["totals"] == [{"currency": "EUR", "cost": "1000.00", "record_count": 1}]


def test_real_ambiguous_sources_raise_before_returning_provenance(cost_reference):
    with cost_reference.engine.begin() as connection:
        insert_run(connection, "ownership-overlap")
        insert_cost(connection, "ownership-overlap-row", run="ownership-overlap", day="2024-06-01")

    with pytest.raises(AmbiguousCostSource):
        cost_reference.fetch_billing_summary(
            "tenant-a", start_date=START, end_date=END,
            group_by="tag", tag_key="application", include_provenance=True,
        )
