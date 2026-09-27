import re
from pathlib import Path

APPS = Path(__file__).resolve().parents[2]
DDL_TARGET = re.compile(
    r"\b(?:CREATE|ALTER|DROP)\s+TABLE\s+(?:IF\s+(?:NOT\s+)?EXISTS\s+)?(\w+)"
    r"|\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?\w+\s+ON\s+(\w+)",
    re.IGNORECASE,
)


def _ddl_targets(service: str) -> set[str]:
    folder = APPS / service / "app" / "db" / "migrations"
    targets = set()
    for migration in folder.glob("[0-9][0-9][0-9]_*.py"):
        for match in DDL_TARGET.finditer(migration.read_text(encoding="utf-8")):
            targets.add((match.group(1) or match.group(2)).lower())
    return targets


def test_ddl_scanner_sees_each_service_own_tables():
    assert {"jobs", "users", "user_tenants", "tenants"} <= _ddl_targets("backend")
    assert {"azure_cost_ingestion_runs", "azure_cost_records"} <= _ddl_targets("processor")


def test_no_table_is_created_or_altered_by_both_services():
    assert _ddl_targets("backend") & _ddl_targets("processor") == set()
