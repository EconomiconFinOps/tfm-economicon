"""JUP-035: four independently committed additive schema steps.

No historical messages are updated and no placeholder is inserted.
"""
import re

from sqlalchemy import inspect, text


def schema_steps():
    return (
        """CREATE TABLE IF NOT EXISTS chat_operations (
            operation_id TEXT PRIMARY KEY NOT NULL,
            tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL REFERENCES conversations(id),
            client_request_id TEXT NOT NULL, question_message_id TEXT NOT NULL,
            question_content TEXT NOT NULL, canonical_input JSONB NOT NULL,
            input_hash TEXT NOT NULL, state TEXT NOT NULL,
            revision INT NOT NULL, attempt_count INT NOT NULL CHECK(attempt_count BETWEEN 0 AND 4),
            current_attempt_id TEXT, attempt_deadline TIMESTAMPTZ, retry_at TIMESTAMPTZ,
            attempts JSONB NOT NULL, private_control JSONB NOT NULL,
            result_message_id TEXT, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
            UNIQUE(tenant_id,user_id,conversation_id,client_request_id),
            CHECK(state IN ('active','waiting','paused','completed','cancelled','failed'))
        )""",
        """CREATE UNIQUE INDEX IF NOT EXISTS chat_operations_open
           ON chat_operations(tenant_id,conversation_id)
           WHERE state IN ('active','waiting','paused')""",
        """CREATE INDEX IF NOT EXISTS chat_operations_wait
           ON chat_operations(retry_at) WHERE state='waiting'""",
        "ALTER TABLE conversations ADD COLUMN dialogue_summary JSONB NULL",
    )


def normalize(expression):
    # The Cockroach catalog adds explicit casts; SQLite preserves source SQL.
    # Exact canonical expressions deliberately reject extra OR/AND clauses.
    expression = re.sub(r'::(?:STRING|TEXT|VARCHAR|INT|INT8|INTEGER)\b','',str(expression),flags=re.I)
    # PostgreSQL deparses literal IN lists as = ANY (ARRAY[...]). Restrict
    # conversion to a list of quoted literals; keep every surrounding clause.
    expression = re.sub(r"=\s*ANY\s*\(\s*ARRAY\[\s*('(?:[^']|'')*'(?:\s*,\s*'(?:[^']|'')*')*)\s*\]\s*\)",
                        r' IN (\1)', expression, flags=re.I)
    return re.sub(r'[\s()]','',expression).lower()


def step_applied(connection, index):
    catalog = inspect(connection)
    if index == 3:
        columns = {row['name']: row for row in catalog.get_columns('conversations')}
        if 'dialogue_summary' not in columns:
            return False
        column_type = str(columns['dialogue_summary']['type']).upper()
        if connection.dialect.name == 'sqlite':
            declared = connection.execute(text('PRAGMA table_info(conversations)')).mappings().all()
            column_type = next(row['type'] for row in declared if row['name']=='dialogue_summary')
        if 'JSON' not in column_type:
            raise RuntimeError('Incompatible chat summary column.')
        return True
    if index == 0:
        if not catalog.has_table('chat_operations'):
            return False
        required = {'operation_id','tenant_id','user_id','conversation_id','client_request_id',
                    'question_message_id','question_content','canonical_input','input_hash','state','revision',
                    'attempt_count','current_attempt_id','attempt_deadline','retry_at','attempts','private_control',
                    'result_message_id','created_at','updated_at'}
        columns = {row['name']:row for row in catalog.get_columns('chat_operations')}
        if set(columns) != required:
            raise RuntimeError('Incompatible chat operation table.')
        declared = {}
        if connection.dialect.name == 'sqlite':
            declared = {row['name']:row['type'] for row in connection.execute(text('PRAGMA table_info(chat_operations)')).mappings()}
        json_fields = {'canonical_input','attempts','private_control'}
        integer_fields = {'revision','attempt_count'}
        timestamp_fields = {'attempt_deadline','retry_at','created_at','updated_at'}
        optional = {'current_attempt_id','attempt_deadline','retry_at','result_message_id'}
        for name,column in columns.items():
            kind = declared.get(name,str(column['type'])).upper()
            expected = ('JSONB',) if name in json_fields else ('INT','INTEGER','BIGINT') if name in integer_fields else ('TIMESTAMPTZ','TIMESTAMP') if name in timestamp_fields else ('STRING','VARCHAR','TEXT')
            if kind not in expected or bool(column['nullable']) != (name in optional):
                raise RuntimeError('Incompatible chat operation column.')
            if name in timestamp_fields and not declared and not getattr(column['type'],'timezone',False):
                raise RuntimeError('Incompatible chat operation timestamp.')
        if catalog.get_pk_constraint('chat_operations')['constrained_columns'] != ['operation_id']:
            raise RuntimeError('Incompatible chat operation primary key.')
        identity = ['tenant_id','user_id','conversation_id','client_request_id']
        if not any(row['column_names']==identity for row in catalog.get_unique_constraints('chat_operations')):
            raise RuntimeError('Incompatible chat operation intent constraint.')
        if not any(row['constrained_columns']==['conversation_id'] and row['referred_table']=='conversations' and row['referred_columns']==['id'] for row in catalog.get_foreign_keys('chat_operations')):
            raise RuntimeError('Incompatible chat operation parent constraint.')
        checks = {normalize(row['sqltext']) for row in catalog.get_check_constraints('chat_operations')}
        attempt_check = ('attempt_count >= 0 AND attempt_count <= 4'
                         if connection.dialect.name == 'postgresql' else 'attempt_count BETWEEN 0 AND 4')
        expected_checks = {normalize(attempt_check), normalize("state IN ('active','waiting','paused','completed','cancelled','failed')")}
        if checks != expected_checks:
            raise RuntimeError('Incompatible chat operation checks.')
        return True
    name = 'chat_operations_open' if index == 1 else 'chat_operations_wait'
    rows = [row for row in catalog.get_indexes('chat_operations') if row['name'] == name]
    if not rows:
        return False
    expected = ['tenant_id','conversation_id'] if index == 1 else ['retry_at']
    if rows[0]['column_names'] != expected or bool(rows[0]['unique']) != (index == 1):
        raise RuntimeError('Incompatible chat operation index.')
    predicate = ' '.join(str(value) for key,value in rows[0].get('dialect_options',{}).items() if key.endswith('_where')).lower()
    expected_predicate = "state IN ('active','waiting','paused')" if index == 1 else "state='waiting'"
    if normalize(predicate) != normalize(expected_predicate):
        raise RuntimeError('Incompatible chat operation predicate.')
    return True


def verify(connection):
    for index in range(4):
        if not step_applied(connection,index):
            raise RuntimeError('Chat schema is not ready.')


def upgrade(connection):
    raise RuntimeError('Chat schema requires individually committed schema_steps.')
