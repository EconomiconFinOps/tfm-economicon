"""Supplement a public receipt with exact, hash-verified post-retrieval evidence.

No inference or database writes. The original API resources remain unchanged.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('collect', Path(__file__).with_name('chat-eval-collect.py'))
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


def reconcile(row, snapshot, sample):
    raw = row['resources']
    if collect.digest(raw) != row['resources_sha256']:
        raise ValueError('Original API resources changed')
    operation = raw['operation']
    if operation['state'] != 'completed' or operation != row['operation']:
        raise ValueError('Completed matching operation required')
    if snapshot['operation_id'] != operation['operation_id']:
        raise ValueError('Retrieval snapshot belongs to another operation')
    base = '/assistant/conversations/' + collect.identifier(row['conversation_id'])
    op = base + '/generations/' + collect.identifier(operation['operation_id'])
    paths = {base: 'history', op + '/context': 'context', op + '/evidence': 'evidence', op + '/result': 'result'}
    reads = 0
    def get(path):
        nonlocal reads
        if path == op:
            reads += 1
            return copy.deepcopy(raw['operation' if reads == 1 else 'operation_after'])
        return copy.deepcopy(raw[paths[path]])
    result = collect.collect(get, sample, row['conversation_id'], operation['operation_id'])
    manifest = raw['result']['metadata']['generation']['context_manifest']
    content = json.dumps({'evidence': snapshot['evidence'], 'omissions': snapshot['omissions']},
                         sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    content = content.replace('<', '\\u003c').replace('>', '\\u003e')
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != manifest['tool_result']['content_sha256'] or actual != snapshot['content_sha256']:
        raise ValueError('Retrieved payload differs from the recorded model context')
    initial = raw['evidence']['items']
    if any(item.get('kind') != 'corpus' for item in snapshot['evidence']):
        raise ValueError('Retrieval must contain only corpus evidence')
    authorized = initial + snapshot['evidence']
    ids = [item['id'] for item in authorized]
    if len(ids) != len(set(ids)) or ids != manifest['evidence_ids']:
        raise ValueError('Evidence identities/order differ from the recorded context')
    cited = {item['id'] for item in raw['result']['metadata']['response'].get('evidence', [])}
    result['authorized_evidence'] = copy.deepcopy(authorized)
    result['cited_chunks'] = [copy.deepcopy(item) for item in authorized if item['id'] in cited]
    result['verification']['citation_ids_known'] = cited <= set(ids)
    result['collection_state'] = ('VERIFIED_PUBLIC_SNAPSHOT' if not result['collection_errors']
                                  and all(v is True for v in result['verification'].values()) else 'INCOMPLETE')
    result['retrieval_supplement'] = copy.deepcopy(snapshot)
    result['retrieval_supplement_sha256'] = collect.digest(snapshot)
    result['derivation'] = {'original_row_sha256': collect.digest(row),
                            'original_collection_state': row['collection_state'],
                            'method': 'exact recorded retrieval payload hash; original API resources preserved'}
    result['limitations'].append('RAG evidence is a hash-verified supplement, not returned by the initial-context API.')
    return result
