import re
from pathlib import Path

import pytest

APPS = Path(__file__).resolve().parents[2]
OWNED_TABLES = {
    "backend": {"tenants", "users", "user_tenants", "jobs", "conversations", "messages"},
    "processor": {"azure_cost_ingestion_runs", "azure_cost_records"},
}
IF_EXISTS = r"(?:IF\s+(?:NOT\s+)?EXISTS\s+)?"
NAME = r"""([^\s(),;@]+)"""
NAMES = NAME + r"((?:\s*,\s*[^\s(),;@]+)*)"
DDL_TARGETS = [
    re.compile(
        r"\b(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:(?:TEMP|TEMPORARY|UNLOGGED)\s+)?|ALTER\s+|DROP\s+)"
        r"(?:MATERIALIZED\s+)?(?:TABLE|VIEW|SEQUENCE)\s+" + IF_EXISTS + r"(?:ONLY\s+)?" + NAMES,
        re.I,
    ),
    re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?(?:ONLY\s+)?" + NAMES, re.I),
    re.compile(r"\bRENAME\s+TO\s+" + NAME, re.I),
    re.compile(r"\bCOMMENT\s+ON\s+TABLE\s+" + NAME, re.I),
    re.compile(
        r"\bCREATE\s+(?:UNIQUE\s+|INVERTED\s+)?INDEX\s+(?:CONCURRENTLY\s+)?" + IF_EXISTS
        + r"(?:[^\s(]+\s+)?ON\s+(?:ONLY\s+)?" + NAME,
        re.I,
    ),
    re.compile(r"\b(?:ALTER|DROP)\s+INDEX\s+(?:CONCURRENTLY\s+)?" + IF_EXISTS + NAME + r"@", re.I),
    re.compile(r"\bCREATE\s+STATISTICS\s+\S+\s+ON\s+[^;]*?\bFROM\s+" + NAME, re.I),
    re.compile(r"\b(?:GRANT|REVOKE)\b[^;]*?\bON\s+(?:TABLE\s+)?" + NAME, re.I),
]
COLUMN_COMMENT = re.compile(r"\bCOMMENT\s+ON\s+COLUMN\s+" + NAME, re.I)


def _table(raw: str) -> str:
    return raw.replace('"', "").split(".")[-1].lower()


def _targets(sql: str) -> set[str]:
    targets = set()
    for pattern in DDL_TARGETS:
        for match in pattern.finditer(sql):
            raw = [match.group(1)] + [part for part in (match.groups()[1:] or [""])[0].split(",") if part.strip()]
            targets.update(_table(name.strip()) for name in raw)
    for match in COLUMN_COMMENT.finditer(sql):
        targets.add(match.group(1).replace('"', "").split(".")[-2].lower())
    return targets


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
        ("ALTER TABLE ONLY jobs ADD COLUMN x INT", "jobs"),
        ("CREATE TEMP TABLE jobs (id INT)", "jobs"),
        ("CREATE UNLOGGED TABLE IF NOT EXISTS jobs (id INT)", "jobs"),
        ("CREATE INVERTED INDEX IF NOT EXISTS idx ON jobs (payload)", "jobs"),
        ("CREATE INDEX ON tenants (name)", "tenants"),
        ("CREATE INDEX idx ON ONLY jobs (id)", "jobs"),
        ("CREATE UNIQUE INDEX CONCURRENTLY idx ON public.jobs (id)", "jobs"),
        ('CREATE INDEX idx ON "jobs" (id)', "jobs"),
        ("DROP INDEX messages@idx", "messages"),
        ("DROP INDEX IF EXISTS public.messages@idx", "messages"),
        ("ALTER INDEX IF EXISTS jobs@idx CONFIGURE ZONE USING gc.ttlseconds = 1", "jobs"),
        ("ALTER TABLE staging RENAME TO jobs", "jobs"),
        ("DROP TABLE staging, jobs", "jobs"),
        ("TRUNCATE staging, jobs", "jobs"),
        ("TRUNCATE TABLE jobs", "jobs"),
        ("COMMENT ON TABLE conversations IS 'x'", "conversations"),
        ("COMMENT ON COLUMN jobs.status IS 'x'", "jobs"),
        ("CREATE VIEW IF NOT EXISTS user_tenants AS SELECT 1", "user_tenants"),
        ("CREATE MATERIALIZED VIEW jobs AS SELECT 1", "jobs"),
        ("DROP VIEW jobs", "jobs"),
        ("DROP SEQUENCE jobs", "jobs"),
        ("CREATE STATISTICS s ON status FROM jobs", "jobs"),
        ("GRANT SELECT ON TABLE jobs TO reader", "jobs"),
        ("DROP TABLE IF EXISTS Messages", "messages"),
    ],
)
def test_ddl_scanner_detects_hostile_forms(statement, table):
    assert table in _targets(statement)


@pytest.mark.parametrize(
    "source",
    [
        '"CREATE TABLE IF NOT EXISTS " + TABLE',
        '"CREATE TABLE {}".format(TABLE)',
        '"CREATE TABLE %s" % TABLE',
        'f"CREATE TABLE {TABLE} (id INT)"',
    ],
)
def test_ddl_scanner_reports_names_it_cannot_resolve(source):
    assert _targets(source) - set().union(*OWNED_TABLES.values())


@pytest.mark.parametrize("service", sorted(OWNED_TABLES))
def test_each_service_only_touches_its_own_tables(service):
    targets = _migration_targets(service)
    assert targets, f"scanner found no DDL for {service}"
    assert targets <= OWNED_TABLES[service]


def test_owned_table_sets_are_disjoint():
    assert OWNED_TABLES["backend"] & OWNED_TABLES["processor"] == set()
