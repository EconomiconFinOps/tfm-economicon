"""Pure scoped lifecycle of derived state at an existing canonical final.

This module neither installs nor consumes model output. The retained artifact
is immutable diagnostic evidence after invalidation; only its wrapper changes.
Malformed derived state cannot make otherwise valid canonical history fail.
"""
from copy import deepcopy
import hashlib
import re
from uuid import UUID

from app.db import chat_history


STATE_KEYS = frozenset(('v', 'scope', 'state_revision', 'lineage_epoch',
    'validity', 'artifact', 'invalidation'))
ARTIFACT_KEYS = frozenset(('artifact_id', 'artifact_revision', 'lineage_epoch',
    'parent_artifact_id', 'parent_artifact_sha256', 'previous_payload_used',
    'source_refs', 'frontier_processed', 'source_selection_hash', 'exact_output',
    'text_sha256', 'contract', 'observations'))
REF_KEYS = frozenset(('question_id', 'answer_id', 'question_ordinal',
    'answer_ordinal', 'question_sha256', 'answer_sha256'))
CONTRACT_KEYS = frozenset(('prompt_version', 'schema_sha256',
    'tokenizer_sha256', 'policy_version'))
INVALID_REASONS = frozenset(('retry_covered', 'invalid_summary',
    'foreign_summary_scope', 'invalid_summary_sources'))
SHA256 = re.compile(r'^[0-9a-f]{64}$')


def digest(value):
    return hashlib.sha256(chat_history.dumps(value).encode('utf-8')).hexdigest()


def _positive(value, minimum=1):
    return type(value) is int and value >= minimum


def _identifier(value):
    return isinstance(value, str) and bool(value)


def _hash(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _epoch(value):
    if _hash(value):
        return True
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def _closed(value, keys):
    return isinstance(value, dict) and set(value) == keys


def _header_reason(state, scope):
    if not _closed(state, STATE_KEYS):
        return 'invalid_summary'
    if (type(state['v']) is not int or state['v'] != 2
            or not _positive(state['state_revision'], 0)
            or not _epoch(state['lineage_epoch'])):
        return 'invalid_summary'
    if (not _closed(state['scope'], chat_history.SCOPE_KEYS)
            or any(not _identifier(state['scope'][key]) for key in chat_history.SCOPE_KEYS)):
        return 'invalid_summary'
    if state['scope'] != scope:
        return 'foreign_summary_scope'
    validity = state['validity']
    if not _closed(validity, {'valid', 'reason'}) or type(validity['valid']) is not bool:
        return 'invalid_summary'
    if validity['valid']:
        if validity['reason'] is not None or state['invalidation'] is not None:
            return 'invalid_summary'
    elif (not isinstance(validity['reason'], str)
            or validity['reason'] not in INVALID_REASONS
            or not isinstance(state['invalidation'], dict)):
        return 'invalid_summary'
    return None


def _artifact_reason(state, document, scope):
    artifact = state['artifact']
    if artifact is None:
        # A quarantine remains opaque internal evidence, without nested rewraps.
        diagnostic = state['invalidation']
        if (state['validity']['valid'] or not isinstance(diagnostic, dict)
                or 'diagnostic_raw' not in diagnostic
                or diagnostic.get('diagnostic_sha256') != digest(diagnostic['diagnostic_raw'])):
            return 'invalid_summary'
        return None
    if not _closed(artifact, ARTIFACT_KEYS):
        return 'invalid_summary'
    if (not _epoch(artifact['artifact_id'])
            or not _positive(artifact['artifact_revision'])
            or not _epoch(artifact['lineage_epoch'])
            or (state['validity']['valid'] and artifact['lineage_epoch'] != state['lineage_epoch'])):
        return 'invalid_summary'
    parent = artifact['parent_artifact_id']
    if parent is None:
        if artifact['parent_artifact_sha256'] is not None or artifact['previous_payload_used'] is not None:
            return 'invalid_summary'
    elif (not _epoch(parent) or not _hash(artifact['parent_artifact_sha256'])
            or not isinstance(artifact['previous_payload_used'], dict)):
        return 'invalid_summary'
    output, contract = artifact['exact_output'], artifact['contract']
    if (not isinstance(output, dict) or not _hash(artifact['text_sha256'])
            or artifact['text_sha256'] != digest(output)
            or not _closed(contract, CONTRACT_KEYS)
            or not _identifier(contract['prompt_version'])
            or not _identifier(contract['policy_version'])
            or not _hash(contract['schema_sha256']) or not _hash(contract['tokenizer_sha256'])
            or not isinstance(artifact['observations'], dict)):
        return 'invalid_summary'
    # Exact finite JSON preserves opaque observations without converting Decimal.
    chat_history.dumps(artifact)
    ledger = artifact['source_refs']
    if not isinstance(ledger, list) or not ledger:
        return 'invalid_summary_sources'
    pairs, _ = chat_history.latest_pairs(document, for_model=True)
    if len(ledger) > len(pairs):
        return 'invalid_summary_sources'
    by_id = {message['id']: message for message in document['messages']}
    for index, ref in enumerate(ledger):
        if (not _closed(ref, REF_KEYS) or not _identifier(ref['question_id'])
                or not _identifier(ref['answer_id'])
                or not _positive(ref['question_ordinal'], 0)
                or not _positive(ref['answer_ordinal'], 0)
                or not _hash(ref['question_sha256']) or not _hash(ref['answer_sha256'])):
            return 'invalid_summary_sources'
        question, answer = by_id.get(ref['question_id']), by_id.get(ref['answer_id'])
        if (question is None or answer is None or question['role'] != 'user'
                or answer['role'] != 'assistant' or answer['question_id'] != question['id']
                or question['ordinal'] != ref['question_ordinal']
                or answer['ordinal'] != ref['answer_ordinal']
                or digest(question) != ref['question_sha256']
                or digest(answer) != ref['answer_sha256']
                or pairs[index]['question_id'] != question['id']
                or (state['validity']['valid'] and pairs[index]['answer_id'] != answer['id'])):
            return 'invalid_summary_sources'
    if (artifact['frontier_processed'] != ledger[-1]
            or not _hash(artifact['source_selection_hash'])
            or artifact['source_selection_hash'] != digest({'scope': scope, 'pairs': ledger})):
        return 'invalid_summary_sources'
    return None


def _next_epoch(scope, previous, result_id):
    # The final result ID is already stable before entering a SERIALIZABLE retry.
    return digest({'scope': scope, 'previous_epoch': previous, 'result_id': result_id})


def final_transition(raw, scope, before, after, question_id, result_id):
    """Return serialized replacement, or None when no summary assignment is needed.

    Caller owns the scoped parent lock and persists this value in the SAME UPDATE
    and transaction as the canonical final. SQL NULL and untouched prefixes do
    not acquire derived state or even rewrite its existing representation.
    """
    if raw is None:
        return None
    try:
        original = chat_history.loads(raw)
    except (TypeError, ValueError):
        original = raw
    try:
        reason = _header_reason(original, scope)
        if reason is None:
            reason = _artifact_reason(original, before, scope)
    except (TypeError, ValueError, KeyError, OverflowError):
        reason = 'invalid_summary'
    final = {'history_revision': after['revision'],
        'question_id': question_id, 'result_message_id': result_id}
    if reason is not None:
        raw_hash = digest(original)
        # Do not trust foreign or malformed header revisions/epochs as lineage.
        state = {'v': 2, 'scope': dict(scope), 'state_revision': 1,
            'lineage_epoch': _next_epoch(scope, raw_hash, result_id),
            'validity': {'valid': False, 'reason': reason}, 'artifact': None,
            'invalidation': {**final, 'reason': reason, 'diagnostic_raw': original,
                'diagnostic_sha256': raw_hash}}
        return chat_history.dumps(state)
    artifact = original['artifact']
    if artifact is None or not any(ref['question_id'] == question_id for ref in artifact['source_refs']):
        return None
    state = deepcopy(original)
    state['state_revision'] += 1
    state['lineage_epoch'] = _next_epoch(scope, original['lineage_epoch'], result_id)
    state['validity'] = {'valid': False, 'reason': 'retry_covered'}
    state['invalidation'] = {**final, 'reason': 'retry_covered'}
    return chat_history.dumps(state)
