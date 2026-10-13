"""Offline, conservative requirement ledger for JUP-035 receipts.

No network calls. Existing JUP-070 heuristics are diagnostics, never semantic
acceptance. Historical verdicts are preserved but not promoted to new labels.
See docs/validation/JUP-035-receipt-evaluation.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'docs/validation/JUP-069-questions.json'
RULES = ROOT / 'docs/validation/JUP-070-evaluation-rules.json'
VERSION = 1


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def legacy():
    spec = importlib.util.spec_from_file_location('jup070_receipt_rules', ROOT / 'tools/assistant-eval.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def requirements(case):
    result = {f'{kind}-{i}': {'criterion': value, 'criterion_sha256': digest(value), 'origin': 'bank'}
            for kind in ('required', 'forbidden', 'numbers')
            for i, value in enumerate(case['expected'][kind], 1)}
    for key, value in {
        'quality-grounding': 'Each cited fragment supports an actual claim; documentary claims have support in supplied evidence.',
        'quality-consistency': 'Public answer and auxiliary fields contain no contradictory conclusions or unsupported invented facts.',
    }.items():
        result[key] = {'criterion': value, 'criterion_sha256': digest(value),
                       'origin': 'provisional-local-rubric-v1'}
    return result


def normalize(receipt, bank, bank_hash, receipt_hash, section):
    declared = receipt.get('bank_sha256')
    if declared != bank_hash:
        raise ValueError('receipt bank hash missing or different')
    rows = receipt.get(section)
    if not isinstance(rows, list):
        raise ValueError(f'missing receipt section: {section}')
    cases = {case['id']: case for case in bank['cases']}
    samples, seen = [], set()
    for row in rows:
        case_id = row['id']
        if case_id not in cases or case_id in seen:
            raise ValueError(f'unknown/duplicate case: {case_id}')
        seen.add(case_id)
        case = cases[case_id]
        result = row.get('result') or {}
        metadata = result.get('metadata') or {}
        response = row.get('response') or metadata.get('response') or {}
        answer = response.get('answer', result.get('content', ''))
        if not isinstance(answer, str):
            raise ValueError('receipt requires a public string answer')
        verification = row.get('verification') or {}
        # Recorded verification is supplementary: check available original input.
        messages = (row.get('history') or {}).get('messages', [])
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        expected_prompt = case['question'] + '\n\nContexto del escenario: ' + case['context']
        if 'question' in row:
            input_match = (row['question'] == case['question'] and
                           row.get('synthetic_context') == case['context'])
        elif user_messages:
            input_match = user_messages == [expected_prompt]
        else:
            input_match = None
        samples.append({
            'sample_id': f'{receipt_hash}:{section}:{case_id}', 'case_id': case_id,
            'receipt_sha256': receipt_hash, 'section': section, 'repetition': 1,
            'state': row.get('state', (row.get('operation') or {}).get('state', 'unknown')),
            'answer': answer, 'response': response, 'cited_chunks': row.get('cited_chunks', []),
            'input_matches_bank': input_match,
            'recorded_input_matches_bank': verification.get('input_matches_bank'),
            'historical_label': row.get('content_review', {
                'verdict': row.get('manual_assessment'), 'note': row.get('note')}),
            'requirements': requirements(case),
        })
        samples[-1]['evidence_sha256'] = digest({k: samples[-1][k] for k in
            ('answer', 'response', 'cited_chunks', 'input_matches_bank', 'state')})
    return samples


def partition(bank, bank_hash):
    # Entire families reserved across ALL campaigns; no random sample leakage.
    reserved = {'budgets', 'recommendations'}
    return {'version': VERSION, 'bank_sha256': bank_hash,
            'policy': 'family-heldout-v1; budgets and recommendations; no tuning on reserve',
            'cases': {c['id']: 'reserve' if c['category'] in reserved else 'calibration'
                      for c in bank['cases']}}


def diagnostics(case, answer, rules, evaluator):
    prompt = evaluator.prompt_text(case)
    aliases = rules['aliases'].get(case['id'], {})
    result = {}
    for i, number in enumerate(case['expected']['numbers'], 1):
        own = aliases.get(str(i), [])
        others = [a for k, values in aliases.items() if k != str(i) for a in values]
        result[f'numbers-{i}'] = {'heuristic_match': evaluator.check_number(
            answer, number, own, prompt, others), 'semantic_status': 'unreviewed'}
    for i, _ in enumerate(case['expected']['forbidden'], 1):
        result[f'forbidden-{i}'] = {'heuristic_hit': evaluator.rule_hits(
            rules['forbidden'][case['id']][str(i)], answer, prompt),
            'semantic_status': 'unreviewed'}
    return result


def score(samples, bank, judgments, manifest, evaluator=None, rules=None):
    cases = {c['id']: c for c in bank['cases']}
    known = {s['sample_id']: s for s in samples}
    if set(judgments) - set(known):
        raise ValueError('judgments reference a sample outside this receipt')
    output = []
    for sample in samples:
        sample_labels = judgments.get(sample['sample_id'], {})
        if set(sample_labels) - set(sample['requirements']):
            raise ValueError('unknown requirement in judgments')
        checks = {}
        for key, requirement in sample['requirements'].items():
            label = sample_labels.get(key)
            check = dict(requirement, status='unreviewed')
            if label:
                if (label.get('evidence_sha256') != sample['evidence_sha256'] or
                        label.get('criterion_sha256') != requirement['criterion_sha256']):
                    raise ValueError('stale judgment: evidence or criterion hash differs')
                if label.get('status') not in ('pass', 'fail', 'uncertain'):
                    raise ValueError('invalid judgment status')
                if not label.get('reviewer') or not label.get('reason'):
                    raise ValueError('judgment needs reviewer and reason')
                if label['status'] == 'fail' and not label.get('failure_cluster'):
                    raise ValueError('failed judgment needs a response-local causal cluster')
                check.update(label)
            checks[key] = check
        operational = sample['state'] == 'completed' and bool(sample['answer'])
        states = Counter(c['status'] for c in checks.values())
        verdict = ('technical_failure' if not operational else
                   'input_unverified' if sample['input_matches_bank'] is not True else
                   'fail' if states['fail'] else
                   'pending' if states['unreviewed'] or states['uncertain'] else 'pass')
        output.append({**sample, 'partition': manifest['cases'][sample['case_id']],
                       'checks': checks, 'verdict': verdict,
                       'failure_clusters': sorted({c['failure_cluster'] for c in checks.values()
                                                   if c['status'] == 'fail'}),
                       'diagnostics': diagnostics(cases[sample['case_id']], sample['answer'], rules,
                                                  evaluator) if evaluator else {}})
    counts = Counter(row['verdict'] for row in output)
    requirement_counts = Counter(c['status'] for row in output for c in row['checks'].values())
    return {'version': VERSION, 'bank_sha256': manifest['bank_sha256'],
            'partition_sha256': digest(manifest), 'samples': output,
            'summary': {'cases_expected': len(cases), 'samples': len(output),
                        'verdicts': dict(counts), 'requirements': dict(requirement_counts),
                        'response_failure_clusters': sum(len(r['failure_clusters']) for r in output),
                        'missing_cases': sorted(set(cases) - {r['case_id'] for r in output}),
                        'acceptance': 'NOT_ASSESSED; provisional local review only'}}


def compare(left, right):
    for key in ('version', 'bank_sha256', 'partition_sha256', 'scorer_sha256', 'rules_sha256', 'heuristic_sha256'):
        if not left.get(key) or left[key] != right.get(key):
            raise ValueError(f'incompatible reports: {key}')
    def index(report):
        result = {}
        for row in report['samples']:
            key = (row['case_id'], row['repetition'])
            if key in result:
                raise ValueError('duplicate paired sample')
            result[key] = row
        return result
    a, b = index(left), index(right)
    transitions, technical = [], []
    for key in sorted(a.keys() & b.keys()):
        x, y = a[key], b[key]
        if x['verdict'] in ('technical_failure', 'input_unverified') or y['verdict'] in ('technical_failure', 'input_unverified'):
            technical.append({'case_id': key[0], 'repetition': key[1], 'before': x['verdict'], 'after': y['verdict']})
            continue
        for req in x['checks']:
            first, second = x['checks'][req], y['checks'][req]
            if first['criterion_sha256'] != second['criterion_sha256']:
                raise ValueError('criterion changed inside report')
            before, after = first['status'], second['status']
            transitions.append({'case_id': key[0], 'repetition': key[1], 'requirement': req,
                                'before': before, 'after': after,
                                'transition': f'{before}->{after}',
                                'failure_cluster_before': first.get('failure_cluster'),
                                'failure_cluster_after': second.get('failure_cluster')})
    counts = Counter(t['transition'] for t in transitions)
    regressions = sorted({(t['case_id'], t['repetition']) for t in transitions
                          if t['transition'] == 'pass->fail'})
    return {'counts': dict(counts), 'transitions': transitions, 'technical_pairs': technical,
            'regressed_responses': regressions,
            'unpaired_before': sorted(a.keys() - b.keys()), 'unpaired_after': sorted(b.keys() - a.keys()),
            'decision': 'DESCRIPTIVE_ONLY; historical N=1 is not repeated acceptance evidence'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('score')
    prepare.add_argument('--receipt', type=Path, required=True)
    prepare.add_argument('--section', choices=['results', 'full28', 'focal'], required=True)
    prepare.add_argument('--judgments', type=Path)
    prepare.add_argument('--partition', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    compare_parser = sub.add_parser('compare')
    compare_parser.add_argument('before', type=Path)
    compare_parser.add_argument('after', type=Path)
    compare_parser.add_argument('--output', type=Path, required=True)
    freeze = sub.add_parser('partition')
    freeze.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if args.command == 'partition':
        if destination != (ROOT / 'docs/validation/JUP-035-evaluation-partition.json').resolve():
            raise ValueError('partition output must be the versioned manifest')
    elif destination == ROOT or ROOT in destination.parents:
        raise ValueError('reports containing answers and judgments must be outside the repository')
    inputs = [getattr(args, name, None) for name in ('receipt', 'judgments', 'partition', 'before', 'after')]
    if any(p and p.resolve() == destination for p in inputs):
        raise ValueError('output cannot replace an input')
    bank, bank_hash = read(BANK), file_hash(BANK)
    if args.command == 'partition':
        result = partition(bank, bank_hash)
    elif args.command == 'compare':
        result = compare(read(args.before), read(args.after))
    else:
        manifest = read(args.partition)
        if manifest != partition(bank, bank_hash):
            raise ValueError('partition differs from frozen family policy or bank')
        evaluator, rules = legacy(), read(RULES)
        evaluator.validate_rules(rules, bank)
        samples = normalize(read(args.receipt), bank, bank_hash, file_hash(args.receipt), args.section)
        result = score(samples, bank, read(args.judgments) if args.judgments else {}, manifest, evaluator, rules)
        result.update(scorer_sha256=file_hash(__file__), rules_sha256=file_hash(RULES),
                      heuristic_sha256=file_hash(ROOT / 'tools/assistant-eval.py'),
                      receipt_sha256=file_hash(args.receipt))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result.get('summary', {'written': str(args.output)}), ensure_ascii=False))


if __name__ == '__main__':
    main()
