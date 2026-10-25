from __future__ import annotations

from pathlib import Path

from app.db.migration_safety import migration_needs_non_transactional_opt_out

MIGRATIONS_DIR = Path(__file__).parents[1] / "app" / "db" / "migrations"

_PRE_FIX_MIGRATION_003 = '''
from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            ALTER TABLE azure_cost_records
                ADD COLUMN IF NOT EXISTS billing_account_id STRING
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE azure_cost_records
            SET billing_account_id = dimensions->>'BillingAccountId'
            WHERE billing_account_id IS NULL
            """
        )
    )
'''

_FIXED_MIGRATION_003 = (
    "transactional = False\n\n" + _PRE_FIX_MIGRATION_003
)

_CREATE_TABLE_ONLY_MIGRATION = '''
from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id STRING PRIMARY KEY
            )
            """
        )
    )
'''


def test_flags_column_add_and_same_file_backfill_without_opt_out():
    assert migration_needs_non_transactional_opt_out(_PRE_FIX_MIGRATION_003) is True


def test_does_not_flag_migration_declaring_the_opt_out():
    assert migration_needs_non_transactional_opt_out(_FIXED_MIGRATION_003) is False


def test_does_not_flag_migrations_without_column_add_and_backfill():
    assert migration_needs_non_transactional_opt_out(_CREATE_TABLE_ONLY_MIGRATION) is False


def test_no_existing_migration_needs_the_opt_out_and_lacks_it():
    violations = [
        path.name
        for path in sorted(MIGRATIONS_DIR.glob("*.py"))
        if path.name != "__init__.py"
        and migration_needs_non_transactional_opt_out(path.read_text(encoding="utf-8"))
    ]

    assert violations == []
