"""Freeze a synthetic repeated campaign plan, without starting it or spending.

The saved plan is NOT a result or authorization to deploy. Runtime provenance,
retrieval snapshots and live accounting must be attached at execution time.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'docs/validation/JUP-069-questions.json'
EXPECTED_BANK = '0bd8a31792d68ff82c2bb222d42593f139d9596e2d24ad37f77c08d648a9f2e7'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def campaign(bank, repetitions):
    if repetitions not in (3, 5):
        raise ValueError('Use N=3 baseline or N=5 confirmation; no best-of selection')
    if len(bank['cases']) != 28 or len({c['id'] for c in bank['cases']}) != 28:
        raise ValueError('The complete original 28-case bank is required')
    return [{'sample_id': f"{case['id']}:r{repeat}", 'case_id': case['id'],
             'repetition': repeat, 'initial_history': [],
             'content': case['question'] + '\n\nContexto del escenario: ' + case['context'],
             'state': 'NOT_RUN'}
            for repeat in range(1, repetitions + 1) for case in bank['cases']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, choices=[3, 5], default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == ROOT or ROOT in destination.parents or destination.exists():
        raise ValueError('Use a new output file outside the repository')
    if git('status', '--porcelain'):
        raise ValueError('Freeze only a clean local commit')
    if sha(BANK) != EXPECTED_BANK:
        raise ValueError('The original bank has changed')
    bank = json.loads(BANK.read_text(encoding='utf-8'))
    for source in bank['sources'].values():
        if sha(ROOT / source['path']) != source['sha256']:
            raise ValueError('Corpus no longer matches the bank')
    paths = git('ls-files', 'apps/backend/app', 'apps/processor/app',
                'apps/frontend/src', 'docs/assistant-corpus',
                'docs/validation/JUP-069-questions.json',
                'docs/validation/JUP-035-evaluation-partition.json',
                'docs/validation/JUP-070-evaluation-rules.json',
                'tools/chat-receipt-eval.py', 'tools/assistant-eval.py').splitlines()
    hashes = {path: sha(ROOT / path) for path in paths}
    data = {'version': 1, 'state': 'NOT_RUN', 'commit': git('rev-parse', 'HEAD'),
            'bank_sha256': EXPECTED_BANK, 'file_hashes': hashes,
            'repetitions': args.repetitions, 'samples': campaign(bank, args.repetitions),
            'provider_constraint': {'provider': 'OpenRouter', 'model': 'z-ai/glm-5.2',
                                    'routing': 'DeepInfra', 'fallbacks': False},
            'budget': {'absolute_cumulative_cap_usd': '2.00',
                       'last_confirmed_cumulative_usd': '0.957927619',
                       'live_accounting_verified': False,
                       'note': 'Historical spend is not a live balance. Include embeddings and any judge.'},
            'execution_prerequisites': [
                'Isolated authorized runtime must match the frozen commit and hashes.',
                'Verify live provider and gateway accounting and reserve a bounded attempt cost before every call.',
                'Capture actual provider/model parameters; temperature 0 only if supported; no fallback.',
                'Save actual prompt/context manifest and retrieved chunks per attempt; never fabricate their hashes.',
                'New conversation for each sample; preserve all attempts, failures, usage and public/history parity.',
                'No best-of reruns and no automatic PASS from completed or absence of heuristic matches.',
            ]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'state': 'NOT_RUN', 'samples': len(data['samples']),
                      'commit': data['commit'], 'plan_sha256': sha(destination)}))


if __name__ == '__main__':
    main()
