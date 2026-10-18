"""Aggregate immutable operation receipts without selecting successful retries."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def aggregate(plan, receipts):
    expected = {(s['case_id'], s['repetition']): s for s in plan['samples']}
    if len(expected) != len(plan['samples']):
        raise ValueError('Duplicate planned sample')
    rows, seen, operations, conversations, sources = [], set(), set(), set(), []
    for receipt in receipts:
        if (receipt.get('plan_sha256') != digest(plan)
                or receipt.get('bank_sha256') != plan['bank_sha256']
                or receipt.get('repetitions') != plan['repetitions']):
            raise ValueError('Receipt belongs to another plan or bank')
        sources.append(digest(receipt))
        for row in receipt['results']:
            key = (row['id'], row['repetition'])
            if key not in expected or key in seen:
                raise ValueError('Unknown or duplicate sample; never select a best attempt')
            operation = row['operation']['operation_id']
            conversation = row['conversation_id']
            if operation in operations or conversation in conversations:
                raise ValueError('Repeated sample must use a fresh conversation and operation')
            seen.add(key); operations.add(operation); conversations.add(conversation)
            if digest(row['resources']) != row['resources_sha256']:
                raise ValueError('Resource hash mismatch')
            rows.append(row)
    rows.sort(key=lambda row: (row['repetition'], row['id']))
    missing = [{'case_id': key[0], 'repetition': key[1]} for key in expected if key not in seen]
    return {'version': 1, 'bank_sha256': plan['bank_sha256'], 'plan_sha256': digest(plan),
            'repetitions': plan['repetitions'], 'commit': plan['commit'],
            'source_receipt_sha256': sources, 'results': rows, 'missing_samples': missing,
            'state': 'PARTIAL' if missing else 'COLLECTED',
            'acceptance': 'NOT_ASSESSED',
            'limitations': ['Coverage does not prove runtime provenance, cost, or semantic acceptance.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('receipts', type=Path, nargs='+')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output == root or root in output.parents or output.exists():
        raise ValueError('Use a new output outside the repository')
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    result = aggregate(read(args.plan), [read(path) for path in args.receipts])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'state': result['state'], 'samples': len(result['results']),
                      'missing': len(result['missing_samples'])}))


if __name__ == '__main__':
    main()
