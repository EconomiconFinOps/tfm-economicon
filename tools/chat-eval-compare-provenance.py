"""Compare audited campaigns after a provenance-only bank revision, offline.

This is explicitly descriptive. It does not bypass the strict same-bank compare,
relabel responses, transfer measurements to a new corpus, or grant acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('provenance_receipt_eval', Path(__file__).with_name('chat-receipt-eval.py'))
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def bank_content(bank):
    content = copy.deepcopy(bank)
    if not isinstance(content.get('suite_version'), str) or not isinstance(content.get('sources'), dict):
        raise ValueError('bank provenance missing')
    del content['suite_version'], content['sources']
    cases = content.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('empty bank')
    ids = [c['id'] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate bank case')
    return content


def rule_content(rules, bank):
    content = copy.deepcopy(rules)
    if content.pop('bank', None) != {'suite_version': bank['suite_version']}:
        raise ValueError('rules do not identify their bank version')
    return content


def validate_report(report, bank, bank_sha256, rules_sha256):
    if report.get('bank_sha256') != bank_sha256 or report.get('rules_sha256') != rules_sha256:
        raise ValueError('report bank/rules hash differs from original input')
    if report.get('partition_sha256') != evaluator.digest(evaluator.partition(bank, bank_sha256)):
        raise ValueError('report partition differs from original bank')
    repeats = report.get('summary', {}).get('repetitions_expected')
    if type(repeats) is not int or repeats not in (1, 3, 5):
        raise ValueError('invalid campaign repetition plan')
    cases = {c['id']: c for c in bank['cases']}
    index = {}
    for row in report['samples']:
        cid, rep = row['case_id'], row['repetition']
        if cid not in cases or type(rep) is not int or not 1 <= rep <= repeats:
            raise ValueError('unknown case or invalid repetition')
        if (cid, rep) in index:
            raise ValueError('duplicate paired sample')
        if row.get('repetitions_expected') != repeats:
            raise ValueError('mixed repetition plans')
        expected = evaluator.requirements(cases[cid])
        if set(row['checks']) != set(expected):
            raise ValueError('missing or additional report criterion')
        for key, original in expected.items():
            check = row['checks'][key]
            if any(check.get(k) != original[k] for k in ('criterion', 'criterion_sha256', 'origin')):
                raise ValueError('criterion content or hash differs from original bank')
            if evaluator.digest(check['criterion']) != check['criterion_sha256']:
                raise ValueError('criterion hash does not bind its content')
            status = check.get('status')
            if status not in ('pass', 'fail', 'uncertain', 'unreviewed'):
                raise ValueError('invalid judgment status')
            if status != 'unreviewed':
                if not check.get('reason') or not check.get('reviewer'):
                    raise ValueError('judgment needs original reason and reviewer')
                if not row.get('evidence_sha256') or check.get('evidence_sha256') != row['evidence_sha256']:
                    raise ValueError('stale evidence-bound judgment')
                if (not row.get('semantic_identity_sha256')
                        or check.get('semantic_identity_sha256') != row['semantic_identity_sha256']):
                    raise ValueError('stale response/context-bound judgment')
                if status == 'fail' and not check.get('failure_cluster'):
                    raise ValueError('failure needs response-local cluster')
        index[cid, rep] = row
    missing = sorted(set((cid, rep) for cid in cases for rep in range(1, repeats + 1)) - set(index))
    return index, missing


def compare_campaigns(before, after, before_bank, after_bank, before_rules, after_rules,
                      before_bank_hash, after_bank_hash, before_rules_hash, after_rules_hash):
    if bank_content(before_bank) != bank_content(after_bank):
        raise ValueError('bank questions, contexts, criteria or other non-provenance content changed')
    if rule_content(before_rules, before_bank) != rule_content(after_rules, after_bank):
        raise ValueError('evaluation rules changed beyond bank provenance')
    for field in ('version', 'scorer_sha256', 'heuristic_sha256'):
        if not before.get(field) or before[field] != after.get(field):
            raise ValueError('incompatible evaluation implementation: ' + field)
    left, missing_before = validate_report(before, before_bank, before_bank_hash, before_rules_hash)
    right, missing_after = validate_report(after, after_bank, after_bank_hash, after_rules_hash)
    transitions, excluded = [], []
    def exclusion(row):
        if row['state'] != 'completed':
            return 'technical_failure'
        if row.get('input_matches_bank') is not True:
            return 'input_unverified'
        if row.get('collection_state') != 'VERIFIED_PUBLIC_SNAPSHOT':
            return 'evidence_incomplete'
        return None
    for cid, rep in sorted(left.keys() & right.keys()):
        first, second = left[cid, rep], right[cid, rep]
        if exclusion(first) or exclusion(second):
            excluded.append({'case_id': cid, 'repetition': rep,
                             'before': exclusion(first), 'after': exclusion(second)})
            continue
        for key, a in first['checks'].items():
            b = second['checks'][key]
            transitions.append({'case_id': cid, 'repetition': rep, 'requirement': key,
                                'origin': a['origin'], 'criterion_sha256': a['criterion_sha256'],
                                'before': a['status'], 'after': b['status'],
                                'transition': a['status'] + '->' + b['status'],
                                'failure_cluster_before': a.get('failure_cluster'),
                                'failure_cluster_after': b.get('failure_cluster')})
    regressions = sorted({(t['case_id'], t['repetition']) for t in transitions
                          if t['before'] == 'pass' and t['after'] != 'pass'})
    return {'state': 'DESCRIPTIVE_PROVENANCE_ONLY_BANK_COMPARISON',
            'decision': 'NOT_ACCEPTANCE; changed systems/contexts are not a causal experiment',
            'before_bank_sha256': before_bank_hash, 'after_bank_sha256': after_bank_hash,
            'unchanged_bank_content_sha256': evaluator.digest(bank_content(before_bank)),
            'unchanged_rule_content_sha256': evaluator.digest(rule_content(before_rules, before_bank)),
            'before_product_commit': before.get('product_commit'), 'after_product_commit': after.get('product_commit'),
            'before_method': before.get('method'), 'after_method': after.get('method'),
            'counts': dict(Counter(t['transition'] for t in transitions)),
            'bank_counts': dict(Counter(t['transition'] for t in transitions if t['origin'] == 'bank')),
            'quality_counts': dict(Counter(t['transition'] for t in transitions if t['origin'] != 'bank')),
            'regressed_responses': regressions, 'transitions': transitions, 'excluded_pairs': excluded,
            'paired_responses': len(left.keys() & right.keys()),
            'unpaired_before': sorted(left.keys() - right.keys()), 'unpaired_after': sorted(right.keys() - left.keys()),
            'missing_before': missing_before, 'missing_after': missing_after,
            'human_acceptance': False, 'independent_adjudication': False,
            'original_reports_modified': False, 'labels_transferred': False,
            'limitations': ['Original audited local judgments retained, not independently adjudicated.',
                            'Each response is a correlated unit; requirement counts are not independent trials.',
                            'No new-corpus attribution of historical measurements or causal model superiority.',
                            'All missing, unpaired and excluded samples remain visible; no automatic quality gate.']}


def load_side(report_path, audit_path, bank_path, rules_path):
    report, audit = evaluator.read(report_path), evaluator.read(audit_path)
    binding = audit.get('local_review', {})
    if binding.get('review_file') != report_path.name or binding.get('review_sha256') != evaluator.file_hash(report_path):
        raise ValueError('audit does not bind the original report')
    if binding.get('notes_sha256') != report.get('notes_sha256') or not report.get('notes_sha256'):
        raise ValueError('audit does not bind original judgments')
    return report, evaluator.read(bank_path), evaluator.read(rules_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for side in ('before', 'after'):
        for kind in ('report', 'audit', 'bank', 'rules'):
            parser.add_argument('--' + side + '-' + kind, type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = {k: v for k, v in vars(args).items() if k != 'output'}
    output = args.output.resolve()
    if output == evaluator.ROOT or evaluator.ROOT in output.parents:
        raise ValueError('comparison reports must stay outside the repository')
    if output.exists() or output in {p.resolve() for p in inputs.values()}:
        raise ValueError('never overwrite an input or existing comparison')
    a = load_side(args.before_report, args.before_audit, args.before_bank, args.before_rules)
    b = load_side(args.after_report, args.after_audit, args.after_bank, args.after_rules)
    result = compare_campaigns(a[0], b[0], a[1], b[1], a[2], b[2],
                               evaluator.file_hash(args.before_bank), evaluator.file_hash(args.after_bank),
                               evaluator.file_hash(args.before_rules), evaluator.file_hash(args.after_rules))
    result['source_hashes'] = {k: evaluator.file_hash(p) for k, p in inputs.items()}
    result['comparison_tool_sha256'] = evaluator.file_hash(__file__)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ('state', 'paired_responses', 'bank_counts', 'quality_counts', 'regressed_responses')}))


if __name__ == '__main__':
    main()
