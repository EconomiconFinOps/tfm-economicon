from sqlalchemy import text


def upgrade(connection) -> None:
    # Historical callable API; the exclusive runner uses resumable steps.
    for statement in schema_steps():
        connection.execute(text(statement))


def schema_steps():
    return (
        """CREATE TABLE IF NOT EXISTS anomaly_episodes (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                currency TEXT NOT NULL,
                service TEXT,
                service_key TEXT NOT NULL,
                start_date DATE NOT NULL,
                last_seen_date DATE NOT NULL,
                observation TEXT NOT NULL CHECK (observation IN ('observed', 'no_longer_observed')),
                no_longer_observed_on DATE,
                reference_week_cost DECIMAL NOT NULL,
                opening_observed_cost DECIMAL NOT NULL,
                impact_numerator DECIMAL NOT NULL,
                impact_day_count INT NOT NULL,
                impact_through_date DATE NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('P1', 'P2', 'P3')),
                status TEXT NOT NULL CHECK (status IN ('new', 'investigating', 'resolved', 'false_positive')),
                status_changed_by TEXT,
                status_changed_at TIMESTAMPTZ,
                first_reviewed_at TIMESTAMPTZ,
                first_reviewed_by TEXT,
                closed_at TIMESTAMPTZ,
                closure_reason TEXT,
                previous_episode_id TEXT,
                rules_version TEXT NOT NULL,
                rules JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )""",
        """CREATE UNIQUE INDEX IF NOT EXISTS anomaly_episodes_one_tracking
            ON anomaly_episodes (tenant_id, currency, service_key)
            WHERE observation = 'observed' AND status IN ('new', 'investigating')""",
        """CREATE INDEX IF NOT EXISTS anomaly_episodes_tenant_start ON anomaly_episodes (tenant_id, start_date)""",
        """CREATE TABLE IF NOT EXISTS anomaly_detection_state (
                tenant_id TEXT PRIMARY KEY,
                last_evaluated_date DATE NOT NULL,
                rules_version TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )""",
    )


def step_applied(connection, index):
    from sqlalchemy import inspect
    from importlib import import_module
    normalize = import_module('app.db.migrations.002_chat_operations').normalize
    catalog = inspect(connection)
    if index in (0, 3):
        table = 'anomaly_episodes' if index == 0 else 'anomaly_detection_state'
        if not catalog.has_table(table):
            return False
        # Compare all declared columns, nullability and primary key. Extra or
        # incompatible columns are not silently adopted as the historical 002.
        definition = schema_steps()[index].split('(', 1)[1].rsplit(')', 1)[0]
        import re
        expected = {}
        for line in definition.splitlines():
            match = re.match(r'\s*(\w+)\s+(STRING|TEXT|DATE|DECIMAL|INT|TIMESTAMPTZ|JSONB)\b(.*)', line)
            if match:
                name, kind, suffix = match.groups()
                expected[name] = (kind, 'NOT NULL' not in suffix and 'PRIMARY KEY' not in suffix)
        columns = {row['name']: row for row in catalog.get_columns(table)}
        if set(columns) != set(expected):
            raise RuntimeError('Incompatible anomaly columns.')
        declared = {}
        if connection.dialect.name == 'sqlite':
            declared = {row['name']: row['type'] for row in connection.execute(text('PRAGMA table_info('+table+')')).mappings()}
        aliases = {'STRING': {'STRING','VARCHAR','TEXT'}, 'TEXT': {'STRING','VARCHAR','TEXT'}, 'INT': {'INT','INTEGER','BIGINT'},
                   'DECIMAL': {'DECIMAL','NUMERIC'}, 'TIMESTAMPTZ': {'TIMESTAMPTZ','TIMESTAMP'}}
        for name, (kind, nullable) in expected.items():
            column = columns[name]
            actual = declared.get(name, str(column['type'])).upper().split('(')[0]
            # Historical SQLite PRIMARY KEY does not imply NOT NULL; native
            # Cockroach does. All explicitly NOT NULL fields must match.
            primary = name == ('id' if index == 0 else 'tenant_id')
            if actual not in aliases.get(kind, {kind}) or (not primary and bool(column['nullable']) != nullable):
                raise RuntimeError('Incompatible anomaly column.')
            if kind == 'TIMESTAMPTZ' and not declared and not getattr(column['type'], 'timezone', False):
                raise RuntimeError('Incompatible anomaly timestamp.')
        primary = ['id'] if index == 0 else ['tenant_id']
        if catalog.get_pk_constraint(table)['constrained_columns'] != primary:
            raise RuntimeError('Incompatible anomaly primary key.')
        if index == 0:
            checks = {normalize(row['sqltext']) for row in catalog.get_check_constraints(table)}
            wanted = {normalize("observation IN ('observed', 'no_longer_observed')"),
                      normalize("severity IN ('P1', 'P2', 'P3')"),
                      normalize("status IN ('new', 'investigating', 'resolved', 'false_positive')")}
            if checks != wanted:
                raise RuntimeError('Incompatible anomaly checks.')
        return True
    if index not in (1, 2):
        raise RuntimeError('Invalid anomaly schema step.')
    name = 'anomaly_episodes_one_tracking' if index == 1 else 'anomaly_episodes_tenant_start'
    rows = [row for row in catalog.get_indexes('anomaly_episodes') if row['name'] == name]
    if not rows:
        return False
    row = rows[0]
    expected = ['tenant_id','currency','service_key'] if index == 1 else ['tenant_id','start_date']
    if row['column_names'] != expected or bool(row['unique']) != (index == 1):
        raise RuntimeError('Incompatible anomaly index.')
    predicate = ' '.join(str(value) for key,value in row.get('dialect_options',{}).items() if key.endswith('_where'))
    expected_predicate = "observation = 'observed' AND status IN ('new', 'investigating')" if index == 1 else ''
    if normalize(predicate) != normalize(expected_predicate):
        raise RuntimeError('Incompatible anomaly predicate.')
    return True


def verify(connection):
    for index in range(4):
        if not step_applied(connection, index):
            raise RuntimeError('Anomaly schema is not ready.')
