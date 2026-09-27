import ast
import re
from pathlib import Path

import pytest

APPS = Path(__file__).resolve().parents[2]
OWNED_TABLES = {
    "backend": {"tenants", "users", "user_tenants", "jobs", "conversations", "messages"},
    "processor": {"azure_cost_ingestion_runs", "azure_cost_records"},
}
NO_DDL_MIGRATIONS = {("processor", "001")}
DYNAMIC = "<name built outside the literal>"
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
    re.compile(
        r"\bALTER\s+(?:TABLE|VIEW|SEQUENCE)\s+" + IF_EXISTS + r"(?:ONLY\s+)?[^\s(),;@]+\s+RENAME\s+TO\s+" + NAME,
        re.I,
    ),
    re.compile(r"\bCOMMENT\s+ON\s+TABLE\s+" + NAME, re.I),
    re.compile(
        r"\bCREATE\s+(?:UNIQUE\s+|INVERTED\s+)?INDEX\s+(?:CONCURRENTLY\s+)?" + IF_EXISTS
        + r"(?:[^\s(]+\s+)?ON\s+(?:ONLY\s+)?" + NAME,
        re.I,
    ),
    re.compile(r"\b(?:ALTER|DROP)\s+INDEX\s+(?:CONCURRENTLY\s+)?" + IF_EXISTS + NAME + r"@", re.I),
    re.compile(r"\bCREATE\s+STATISTICS\s+\S+\s+ON\s+[^;]*?\bFROM\s+" + NAME, re.I),
    re.compile(r"\b(?:GRANT|REVOKE)\b[^;\n]*?\bON\s+(?:TABLE\s+)?" + NAME, re.I),
]
COLUMN_COMMENT = re.compile(r"\bCOMMENT\s+ON\s+COLUMN\s+" + NAME, re.I)
UNNAMED_INDEX_CHANGE = re.compile(
    r"\b(?:ALTER|DROP)\s+INDEX\s+(?:CONCURRENTLY\s+)?" + IF_EXISTS + r"(?![^\s(),;]*@)", re.I
)
SCHEMA_CALLS = {"create_all", "create", "exec_driver_sql"}
DDL_VERB = re.compile(r"\b(?:CREATE|ALTER|DROP|TRUNCATE)\b", re.I)
DANGLING_NAME = re.compile(r"\b(?:TABLE|VIEW|SEQUENCE|ON|ONLY|EXISTS)\s*$", re.I)
# SQL literals are kept so that a "--" inside quotes cannot hide the statement after it.
SQL_COMMENT_OR_LITERAL = re.compile(r"'(?:[^']|'')*'|--[^\n]*")


def _strip_sql_comments(sql: str) -> str:
    return SQL_COMMENT_OR_LITERAL.sub(lambda m: m.group(0) if m.group(0).startswith("'") else " ", sql)


def _table(raw: str) -> str:
    return raw.replace('"', "").split(".")[-1].lower()


def _targets(sql: str) -> set[str]:
    sql = _strip_sql_comments(sql)
    targets = set()
    for pattern in DDL_TARGETS:
        for match in pattern.finditer(sql):
            raw = [match.group(1)] + [part for part in (match.groups()[1:] or [""])[0].split(",") if part.strip()]
            targets.update(_table(name.strip()) for name in raw)
    for match in COLUMN_COMMENT.finditer(sql):
        targets.add(match.group(1).replace('"', "").split(".")[-2].lower())
    if DDL_VERB.search(sql) and DANGLING_NAME.search(sql):
        targets.add(DYNAMIC)
    return targets


def _strings(source: str) -> list[str]:
    strings = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
        elif isinstance(node, ast.JoinedStr):
            strings.append("".join(
                part.value if isinstance(part, ast.Constant) else "{}" for part in node.values
            ))
    return strings


def _source_targets(source: str) -> set[str]:
    return set().union(*(_targets(text) for text in _strings(source)))


def _forbidden(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name in SCHEMA_CALLS:
                return True
    return any(UNNAMED_INDEX_CHANGE.search(_strip_sql_comments(text)) for text in _strings(source))


def _migrations(service: str):
    return sorted((APPS / service / "app" / "db" / "migrations").glob("[0-9][0-9][0-9]_*.py"))


def _migration_targets(service: str) -> set[str]:
    return set().union(*(_source_targets(path.read_text(encoding="utf-8")) for path in _migrations(service)))


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
        r'connection.execute(text("-- add status column\n ALTER TABLE jobs ADD COLUMN x INT"))',
        r'connection.execute(text("# note\n ALTER TABLE jobs ADD COLUMN x INT"))',
        r"""text("UPDATE azure_cost_records SET tag = '#legacy'; ALTER TABLE jobs ADD COLUMN x INT")""",
        r"""text("ALTER TABLE azure_cost_records ALTER COLUMN tags SET DEFAULT '--'; DROP TABLE jobs")""",
        r'text("SELECT 1;\nALTER TABLE jobs ADD COLUMN x INT")',
        r"text('CREATE TABLE IF NOT EXISTS jobs (id STRING)')",
        r'text("CREATE TABLE " "jobs (id INT)")',
    ],
)
def test_ddl_inside_python_strings_is_seen(source):
    assert "jobs" in _source_targets(source)


@pytest.mark.parametrize(
    "source",
    [
        r'text("CREATE TABLE IF NOT EXISTS " + TABLE)',
        r'text("CREATE TABLE {}".format(TABLE))',
        r'text("CREATE TABLE %s" % TABLE)',
        r'text(f"CREATE TABLE {TABLE} (id INT)")',
    ],
)
def test_ddl_scanner_reports_names_it_cannot_resolve(source):
    assert _source_targets(source) - set().union(*OWNED_TABLES.values())


@pytest.mark.parametrize(
    "source",
    [
        "# grant the worker access on startup\nx = 1",
        r'text("-- we used to CREATE TABLE jobs here\nSELECT 1")',
        r'text("ALTER INDEX azure_cost_records@idx RENAME TO idx2")',
    ],
)
def test_ddl_scanner_ignores_comments_and_index_renames(source):
    assert _source_targets(source) <= OWNED_TABLES["processor"]


@pytest.mark.parametrize(
    "source",
    [
        r'text("DROP INDEX IF EXISTS jobs_status_idx")',
        r'text("ALTER INDEX jobs_status_idx CONFIGURE ZONE USING gc.ttlseconds = 1")',
        "metadata.create_all(connection)",
        'Table("jobs", metadata).create(connection)',
        "connection.exec_driver_sql(JOBS_DDL)",
    ],
)
def test_ddl_forms_without_a_resolvable_table_are_forbidden(source):
    assert _forbidden(source)


@pytest.mark.parametrize("service", sorted(OWNED_TABLES))
def test_each_service_only_touches_its_own_tables(service):
    targets = _migration_targets(service)
    assert targets, f"scanner found no DDL for {service}"
    assert targets <= OWNED_TABLES[service]


def test_every_migration_declares_its_tables_or_is_known_to_have_no_ddl():
    for service in OWNED_TABLES:
        for path in _migrations(service):
            source = path.read_text(encoding="utf-8")
            assert not _forbidden(source), path.name
            assert _source_targets(source) or (service, path.name[:3]) in NO_DDL_MIGRATIONS, path.name


def test_owned_table_sets_are_disjoint():
    assert OWNED_TABLES["backend"] & OWNED_TABLES["processor"] == set()
