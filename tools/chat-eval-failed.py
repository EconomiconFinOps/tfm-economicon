"""Validate a tenant-scoped durable input supplement without erasing a failure.

The caller must obtain snapshot through a read-only tenant-scoped database query.
This validates consistency, not the authenticity of arbitrary supplied files.
Accounting is separate and remains mandatory before another dispatch.
"""
import copy
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('collect', Path(__file__).with_name('chat-eval-collect.py'))
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


def reconcile(row, snapshot, sample, tenant_id):
    raw = row['resources']
    operation = raw['operation']
    if collect.digest(raw) != row['resources_sha256'] or operation != row['operation']:
        raise ValueError('Original API resources changed')
    if operation.get('state') not in ('failed', 'cancelled'):
        raise ValueError('Only terminal failures accept durable input supplements')
    if (not tenant_id or snapshot.get('tenant_id') != tenant_id
            or snapshot.get('operation_id') != operation['operation_id']
            or snapshot.get('conversation_id') != row['conversation_id']
            or snapshot.get('client_request_id') != operation.get('request_id')
            or snapshot.get('question_message_id') != operation.get('question_id')
            or snapshot.get('state') != operation['state']
            or snapshot.get('question_content') != sample['content']
            or row['id'] != sample['case_id'] or row['repetition'] != sample['repetition']):
        raise ValueError('Durable input identity or content mismatch')
    attempts = snapshot.get('attempt_ids')
    if (not isinstance(attempts, list) or not all(isinstance(a, str) and a for a in attempts)
            or len(attempts) != len(set(attempts))
            or len(attempts) != operation.get('attempt_count')
            or snapshot.get('attempt_count') != len(attempts)):
        raise ValueError('Durable attempt identity mismatch')
    base = '/assistant/conversations/' + collect.identifier(row['conversation_id'])
    op = base + '/generations/' + collect.identifier(operation['operation_id'])
    paths = {base: 'history', op + '/context': 'context', op + '/evidence': 'evidence'}
    reads = 0
    def get(path):
        nonlocal reads
        if path == op:
            reads += 1
            return copy.deepcopy(raw['operation' if reads == 1 else 'operation_after'])
        return copy.deepcopy(raw[paths[path]])
    result = collect.collect(get, sample, row['conversation_id'], operation['operation_id'])
    result['verification']['input_matches_bank'] = True
    result['collection_state'] = ('VERIFIED_PUBLIC_SNAPSHOT'
        if not result['collection_errors'] and result['verification']['stable_snapshot']
        and result['verification']['citation_ids_known'] else 'INCOMPLETE')
    result['durable_input_supplement'] = copy.deepcopy(snapshot)
    result['durable_input_supplement_sha256'] = collect.digest(snapshot)
    result['derivation'] = {'original_row_sha256': collect.digest(row),
        'original_collection_state': row['collection_state'],
        'method': 'tenant-scoped durable input supplement; original API resources preserved'}
    result['limitations'].append('Failed input verified through durable SQL, not public history; failed state retained. Cost reconciliation is separate.')
    return result
