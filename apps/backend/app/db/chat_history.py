"""Versioned canonical conversation document; no legacy-table fallback.

JSONB is read as text and decoded with Decimal so original JSON numbers never
cross a binary float while verifying or migrating historical values.
"""
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text


SCOPE_KEYS = frozenset(('tenant_id', 'user_id', 'conversation_id'))
DOCUMENT_KEYS = frozenset(('schema_version', 'identity', 'revision', 'next_ordinal', 'messages'))
MESSAGE_KEYS = frozenset(('ordinal', 'id', 'role', 'author_id', 'question_id',
    'origin', 'content', 'metadata', 'created_at'))
UTC_STAMP = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$')


def invalid():
    from app.db.chat_repository import ChatError
    return ChatError(503, 'history_invalid')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key.')
        result[key] = value
    return result


def loads(value):
    def reject_constant(value):
        raise ValueError('Non-finite JSON number.')
    return json.loads(value, parse_float=Decimal, parse_int=int,
        parse_constant=reject_constant, object_pairs_hook=_unique_object)


def _number(value):
    if not value.is_finite():
        raise ValueError('Non-finite JSON number.')
    sign, digits, exponent = value.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    if not any(digits):
        return '0'
    prefix = '-' if sign else ''
    coefficient = ''.join(str(digit) for digit in digits)
    # Fixed representation when proportionate; scientific form avoids allocating
    # a million zeros for a valid small/large exponent. Both remain JSON numbers.
    if -64 <= exponent <= 64:
        point = len(coefficient)+exponent
        if exponent >= 0:
            return prefix+coefficient+'0'*exponent
        if point > 0:
            return prefix+coefficient[:point]+'.'+coefficient[point:]
        return prefix+'0.'+'0'*(-point)+coefficient
    return prefix+coefficient+'e'+str(exponent)


def dumps(value):
    """Canonical JSON with exact Decimal values (never numeric strings)."""
    if value is None: return 'null'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value, str): return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int): return _number(Decimal(value))
    if isinstance(value, Decimal): return _number(value)
    if isinstance(value, float):
        if not math.isfinite(value): raise ValueError('Non-finite JSON number.')
        return _number(Decimal(repr(value)))
    if isinstance(value, list): return '['+','.join(dumps(item) for item in value)+']'
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return '{'+','.join(dumps(key)+':'+dumps(value[key]) for key in sorted(value))+'}'
    raise ValueError('Unsupported JSON value.')


def utc(value):
    if isinstance(value, str): value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime): raise ValueError('Invalid SQL timestamp.')
    if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def empty(scope):
    return {'schema_version': 1, 'identity': {key: scope[key] for key in SCOPE_KEYS},
        'revision': 0, 'next_ordinal': 0, 'messages': []}


def validate(value, scope):
    try:
        if not isinstance(value, dict): raise ValueError()
        keys = set(value)
        if keys not in (DOCUMENT_KEYS, DOCUMENT_KEYS | {'migration'}): raise ValueError()
        if type(value['schema_version']) is not int or value['schema_version'] != 1: raise ValueError()
        identity = value['identity']
        if (not isinstance(identity, dict) or set(identity) != SCOPE_KEYS
                or any(not isinstance(identity[key], str) or not identity[key]
                    or identity[key] != scope[key] for key in SCOPE_KEYS)): raise ValueError()
        for key in ('revision', 'next_ordinal'):
            if type(value[key]) is not int or value[key] < 0: raise ValueError()
        messages = value['messages']
        if not isinstance(messages, list) or value['next_ordinal'] != len(messages): raise ValueError()
        all_messages = {m.get('id'): m for m in messages if isinstance(m, dict) and isinstance(m.get('id'), str)}
        by_id = {}
        for index, message in enumerate(messages):
            if not isinstance(message, dict) or set(message) != MESSAGE_KEYS: raise ValueError()
            if type(message['ordinal']) is not int or message['ordinal'] != index: raise ValueError()
            if not isinstance(message['id'], str) or not message['id'] or message['id'] in by_id: raise ValueError()
            if not isinstance(message['role'], str) or not message['role']: raise ValueError()
            if message['origin'] not in ('completed', 'legacy'): raise ValueError()
            if message['author_id'] is not None and (not isinstance(message['author_id'], str)
                    or message['author_id'] != identity['user_id']): raise ValueError()
            if not isinstance(message['content'], str): raise ValueError()
            stamp = message['created_at']
            if not isinstance(stamp, str) or not UTC_STAMP.fullmatch(stamp) or utc(stamp) != stamp: raise ValueError()
            question = message['question_id']
            if question is not None and (not isinstance(question, str) or not question): raise ValueError()
            if message['role'] == 'user' and question != message['id']: raise ValueError()
            if message['role'] != 'user' and question is not None:
                target = (by_id if message['origin'] == 'completed' else all_messages).get(question)
                if target is None or target['role'] != 'user': raise ValueError()
            if message['origin'] == 'completed':
                if (message['role'] not in ('user', 'assistant') or message['author_id'] != identity['user_id']
                        or question is None or not isinstance(message['metadata'], dict)): raise ValueError()
            # Recursive JSON validation also rejects non-finite/unsupported values.
            dumps(message['metadata'])
            by_id[message['id']] = message
        if 'migration' in value:
            receipt = value['migration']
            if (not isinstance(receipt, dict) or set(receipt) != {'version', 'source_count', 'source_sha256'}
                    or receipt['version'] != '003' or type(receipt['source_count']) is not int
                    or receipt['source_count'] < 0 or receipt['source_count'] > len(messages)
                    or not isinstance(receipt['source_sha256'], str)
                    or not re.fullmatch('[0-9a-f]{64}', receipt['source_sha256'])): raise ValueError()
        return value
    except (KeyError, ValueError, TypeError, OverflowError, RecursionError):
        raise invalid() from None


def decode(raw, scope):
    try:
        if raw is None: raise ValueError()
        return validate(loads(raw), scope)
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise invalid() from None


def read(connection, scope):
    row = connection.execute(text('SELECT CAST(dialogue_history AS TEXT) AS history '
        'FROM conversations WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'), scope).first()
    return None if row is None else decode(row.history, scope)


def projection(value):
    return [{'id': m['id'], 'role': m['role'], 'content': m['content'],
        'metadata': m['metadata'], 'created_at': datetime.fromisoformat(m['created_at'].replace('Z', '+00:00'))}
        for m in value['messages']]


def source_hash(scope, records):
    return hashlib.sha256(dumps({'scope': {key: scope[key] for key in SCOPE_KEYS},
        'records': sorted(records, key=lambda record: record['id'])}).encode('utf-8')).hexdigest()


def legacy_values(value):
    return [{key: message[key] for key in ('id', 'role', 'content', 'metadata', 'author_id', 'created_at')}
        for message in value['messages']]


def append_final(connection, scope, question, assistant):
    """Called under the same parent lock/transaction as the completed operation."""
    from copy import deepcopy
    from app.db.chat_repository import ChatError
    value = read(connection, scope)
    if value is None: raise ChatError(404, 'not_found')
    previous = value['revision']
    before = value
    value = deepcopy(value)
    by_id = {message['id']: message for message in value['messages']}
    existing = by_id.get(question['id'])
    if existing is not None and (existing['role'] != 'user' or existing['content'] != question['content']
            or existing['author_id'] not in (None, scope['user_id'])):
        raise ChatError(409, 'question_integrity')
    if assistant['id'] in by_id or assistant['id'] == question['id']:
        raise ChatError(409, 'result_integrity')
    if existing is None:
        value['messages'].append({'ordinal': len(value['messages']), 'id': question['id'],
            'role': 'user', 'author_id': scope['user_id'], 'question_id': question['id'],
            'origin': 'completed', 'content': question['content'], 'metadata': question['metadata'],
            'created_at': utc(question['created_at'])})
    metadata = deepcopy(assistant['metadata'])
    if not isinstance(metadata, dict): raise ChatError(409, 'result_integrity')
    generation = metadata.setdefault('generation', {'question_message_id': question['id']})
    if not isinstance(generation, dict) or generation.get('question_message_id') != question['id']:
        raise ChatError(409, 'result_integrity')
    value['messages'].append({'ordinal': len(value['messages']), 'id': assistant['id'],
        'role': 'assistant', 'author_id': scope['user_id'], 'question_id': question['id'],
        'origin': 'completed', 'content': assistant['content'], 'metadata': metadata,
        'created_at': utc(assistant['created_at'])})
    value['revision'] += 1
    value['next_ordinal'] = len(value['messages'])
    validate(value, scope)
    from app.db.chat_summary import final_transition
    raw_summary = connection.execute(text('SELECT CAST(dialogue_summary AS TEXT) FROM conversations '
        'WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'), scope).scalar_one()
    summary = final_transition(raw_summary, scope, before, value, question['id'], assistant['id'])
    invalidation = ', dialogue_summary=:summary' if summary is not None else ''
    parameters = {**scope, 'document': dumps(value), 'now': assistant['created_at'], 'previous': previous}
    if summary is not None:
        parameters['summary'] = summary
    updated = connection.execute(text('UPDATE conversations SET dialogue_history=:document, updated_at=:now'+invalidation+
        ' WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id '
        "AND CAST(dialogue_history ->> 'revision' AS BIGINT)=:previous"), parameters)
    if updated.rowcount != 1: raise ChatError(409, 'history_changed')
    return value


def completed_result(connection, scope, operation):
    value = read(connection, scope)
    if value is None: raise invalid()
    by_id = {message['id']: message for message in value['messages']}
    question = by_id.get(operation['question_message_id'])
    assistant = by_id.get(operation['result_message_id'])
    if (question is None or question['role'] != 'user' or question['content'] != operation['question_content']
            or assistant is None or assistant['role'] != 'assistant'
            or assistant['question_id'] != question['id']): raise invalid()
    generation = assistant['metadata'].get('generation')
    if not isinstance(generation, dict) or generation.get('question_message_id') != question['id']: raise invalid()
    return {'id': assistant['id'], 'content': assistant['content'], 'metadata': assistant['metadata']}


def http_response(value, status_code=200):
    """Avoid default encoders which round Decimal or turn numbers into strings."""
    from fastapi import Response
    def transport(item):
        if isinstance(item, datetime): return utc(item)
        if isinstance(item, dict): return {key: transport(child) for key, child in item.items()}
        if isinstance(item, list): return [transport(child) for child in item]
        return item
    return Response(content=dumps(transport(value)), status_code=status_code, media_type='application/json')


def latest_pairs(value):
    """Latest eligible assistant by ordinal, retaining original question order.

    Original metadata is opaque historical evidence. Only the canonical link
    establishes a pair; neither timestamps, UUIDs nor adjacency can invent one.
    """
    questions = {message['id']: message for message in value['messages'] if message['role'] == 'user'}
    latest, excluded = {}, []
    for message in value['messages']:
        if message['role'] == 'user': continue
        if message['role'] != 'assistant':
            excluded.append({'message_id': message['id'], 'reason': 'unsupported_legacy_role'})
            continue
        question = questions.get(message['question_id'])
        if question is None:
            excluded.append({'message_id': message['id'], 'reason': 'unlinked_legacy_message'})
            continue
        latest[question['id']] = {'question_id': question['id'], 'answer_id': message['id'],
            'question': question['content'], 'answer': message['content']}
    for question in questions.values():
        if question['id'] not in latest:
            excluded.append({'message_id': question['id'], 'reason': 'incomplete_legacy_question'})
    ordered = [latest[question['id']] for question in questions.values() if question['id'] in latest]
    return ordered, excluded
