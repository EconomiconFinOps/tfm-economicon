"""Exclusive additive transition; legacy rows retained, never a runtime source."""
from sqlalchemy import inspect, text

from app.db import chat_history as history


def schema_steps():
    return ('ALTER TABLE conversations ADD COLUMN dialogue_history JSONB NULL',)


def step_applied(connection, index):
    if index != 0: raise RuntimeError('Invalid history schema step.')
    columns = {column['name']: column for column in inspect(connection).get_columns('conversations')}
    if 'dialogue_history' not in columns: return False
    declared = str(columns['dialogue_history']['type']).upper()
    if connection.dialect.name == 'sqlite':
        declared = next(row['type'] for row in connection.execute(text('PRAGMA table_info(conversations)')).mappings()
            if row['name'] == 'dialogue_history').upper()
    if declared != 'JSONB': raise RuntimeError('Incompatible canonical history column.')
    if not columns['dialogue_history']['nullable']: raise RuntimeError('Incompatible canonical history column.')
    return True


def verify(connection):
    if not step_applied(connection, 0): raise RuntimeError('Canonical history column is missing.')
    # Backend verify and startup must never consult frozen legacy messages.
    for parent in connection.execute(text('SELECT id AS conversation_id, tenant_id, user_id, '
            'CAST(dialogue_history AS TEXT) AS history FROM conversations')).mappings():
        history.decode(parent['history'], parent)


def _source(connection, scope):
    records = []
    for row in connection.execute(text('SELECT id,tenant_id,user_id,role,content, '
            'CAST(metadata AS TEXT) AS metadata,created_at FROM messages WHERE conversation_id=:conversation_id'), scope).mappings():
        if row['tenant_id'] != scope['tenant_id'] or row['user_id'] not in (None, scope['user_id']):
            raise RuntimeError('Legacy history integrity check failed.')
        if not isinstance(row['id'], str) or not row['id'] or not isinstance(row['role'], str) or not row['role']:
            raise RuntimeError('Legacy history integrity check failed.')
        if not isinstance(row['content'], str): raise RuntimeError('Legacy history integrity check failed.')
        records.append({'id': row['id'], 'role': row['role'], 'author_id': row['user_id'],
            'content': row['content'], 'metadata': history.loads(row['metadata']) if row['metadata'] is not None else None,
            'created_at': history.utc(row['created_at'])})
    return records


def _candidate(scope, records):
    by_id = {record['id']: record for record in records}
    if len(by_id) != len(records): raise RuntimeError('Legacy history integrity check failed.')
    links = {}
    for record in records:
        if record['role'] == 'user': links[record['id']] = record['id']
        elif record['role'] == 'assistant':
            metadata = record['metadata']
            generation = metadata.get('generation') if isinstance(metadata, dict) else None
            reference = generation.get('question_message_id') if isinstance(generation, dict) else None
            target = by_id.get(reference) if isinstance(reference, str) else None
            links[record['id']] = reference if target is not None and target['role'] == 'user' else None
        else: links[record['id']] = None
    def order(record):
        reference = links[record['id']]
        target = by_id.get(reference)
        if (record['role'] == 'assistant' and target is not None
                and target['created_at'] == record['created_at']):
            return record['created_at'], reference, 1, record['id']
        return record['created_at'], record['id'], 0, record['id']
    result = history.empty(scope)
    for ordinal, record in enumerate(sorted(records, key=order)):
        result['messages'].append({**record, 'ordinal': ordinal,
            'question_id': links[record['id']], 'origin': 'legacy'})
    result['next_ordinal'] = len(records)
    result['migration'] = {'version': '003', 'source_count': len(records),
        'source_sha256': history.source_hash(scope, records)}
    history.validate(result, scope)
    if history.source_hash(scope, history.legacy_values(result)) != result['migration']['source_sha256']:
        raise RuntimeError('Legacy history conservation check failed.')
    return result


def _conversation(connection, scope):
    suffix = '' if connection.dialect.name == 'sqlite' else ' FOR UPDATE'
    row = connection.execute(text('SELECT CAST(dialogue_history AS TEXT) AS history FROM conversations '
        'WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'+suffix), scope).first()
    if row is None: raise RuntimeError('Legacy history integrity check failed.')
    records = _source(connection, scope)
    candidate = _candidate(scope, records)
    encoded = history.dumps(candidate)
    if row.history is None:
        updated = connection.execute(text('UPDATE conversations SET dialogue_history=:history '
            'WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id AND dialogue_history IS NULL'),
            {**scope, 'history': encoded})
        if updated.rowcount != 1: raise RuntimeError('Legacy history checkpoint changed.')
    persisted = history.read(connection, scope)
    if history.dumps(persisted) != encoded:
        raise RuntimeError('Legacy history checkpoint differs; original retained.')
    if (len(persisted['messages']) != len(records)
            or {m['id'] for m in persisted['messages']} != {m['id'] for m in records}
            or history.source_hash(scope, history.legacy_values(persisted)) != candidate['migration']['source_sha256']):
        raise RuntimeError('Legacy history conservation check failed.')


def backfill(engine):
    try:
        with engine.connect() as connection:
            if connection.execute(text('SELECT m.id FROM messages m LEFT JOIN conversations c ON c.id=m.conversation_id '
                    'WHERE c.id IS NULL LIMIT 1')).first() is not None:
                raise RuntimeError('Legacy history integrity check failed.')
            scopes = [dict(row) for row in connection.execute(text(
                'SELECT id AS conversation_id,tenant_id,user_id FROM conversations ORDER BY id')).mappings()]
        for scope in scopes:
            # Durable per-conversation checkpoint, retained if a later one fails.
            # An ambiguous COMMIT is resolved by rerunning against its receipt.
            with engine.begin() as connection:
                _conversation(connection, scope)
        with engine.connect() as connection:
            verify(connection)
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError('Legacy history integrity check failed; source retained.') from None
