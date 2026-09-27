import re
from pathlib import Path

import pytest

APPS = Path(__file__).resolve().parents[2]
NAME = r'([\w."{}]+)'
DDL_TARGETS = [
    re.compile(r"\b(?:CREATE|ALTER|DROP|TRUNCATE)\s+TABLE\s+(?:IF\s+(?:NOT\s+)?EXISTS\s+)?" + NAME, re.I),
    re.compile(r"\bTRUNCATE\s+(?!TABLE\b)" + NAME, re.I),
    re.compile(r"\bRENAME\s+TO\s+" + NAME, re.I),
    re.compile(r"\bCOMMENT\s+ON\s+TABLE\s+" + NAME, re.I),
    re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:VIEW|SEQUENCE)\s+(?:IF\s+NOT\s+EXISTS\s+)?" + NAME, re.I),
    re.compile(
        r"\bCREATE\s+(?:UNIQUE\s+|INVERTED\s+)?INDEX\s+(?:CONCURRENTLY\s+)?"
        r"(?:IF\s+NOT\s+EXISTS\s+)?(?:[\w\"]+\s+)?ON\s+" + NAME,
        re.I,
    ),
    re.compile(r"\bDROP\s+INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+EXISTS\s+)?" + NAME + r"@", re.I),
]


def _table(raw: str) -> str:
    return raw.replace('"', "").split(".")[-1].lower()


def _targets(sql: str) -> set[str]:
    return {_table(match.group(1)) for pattern in DDL_TARGETS for match in pattern.finditer(sql)}


def _migration_targets(service: str) -> set[str]:
    folder = APPS / service / "app" / "db" / "migrations"
    return set().union(*(
        _targets(path.read_text(encoding="utf-8")) for path in folder.glob("[0-9][0-9][0-9]_*.py")
    ))


@pytest.mark.parametrize(
    "statement,table",
    [
        ("CREATE TABLE IF NOT EXISTS public.jobs (id STRING)", "jobs"),
        ('ALTER TABLE "users" ADD COLUMN x INT', "users"),
        ("CREATE INVERTED INDEX IF NOT EXISTS idx ON jobs (payload)", "jobs"),
        ("CREATE INDEX ON tenants (name)", "tenants"),
        ("CREATE UNIQUE INDEX CONCURRENTLY idx ON public.jobs (id)", "jobs"),
        ('CREATE INDEX idx ON "jobs" (id)', "jobs"),
        ("DROP INDEX messages@idx", "messages"),
        ("DROP INDEX IF EXISTS public.messages@idx", "messages"),
        ("ALTER TABLE staging RENAME TO jobs", "jobs"),
        ("TRUNCATE jobs", "jobs"),
        ("TRUNCATE TABLE jobs", "jobs"),
        ("COMMENT ON TABLE conversations IS 'x'", "conversations"),
        ("CREATE VIEW IF NOT EXISTS user_tenants AS SELECT 1", "user_tenants"),
        ("DROP TABLE IF EXISTS Messages", "messages"),
    ],
)
def test_ddl_scanner_detects_hostile_forms(statement, table):
    assert table in _targets(statement)


def test_ddl_scanner_sees_each_service_own_tables():
    assert {"jobs", "users", "user_tenants", "tenants"} <= _migration_targets("backend")
    assert {"azure_cost_ingestion_runs", "azure_cost_records"} <= _migration_targets("processor")


def test_migration_ddl_targets_are_resolvable():
    for service in ("backend", "processor"):
        assert not {name for name in _migration_targets(service) if "{" in name}, service


def test_no_table_is_created_or_altered_by_both_services():
    assert _migration_targets("backend") & _migration_targets("processor") == set()
