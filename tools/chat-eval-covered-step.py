"""Run the isolated adapter with audited, complete post-history ledger coverage."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main(root):
    original = load('operator_adapter', root / 'live-step.py')
    old_module = original.module
    budget = load('covered_budget', Path(__file__).with_name('chat-eval-budget.py'))
    ledger = load('covered_ledger', Path(__file__).with_name('chat-eval-ledger.py'))
    snapshot = budget.accounting_snapshot
    def audited_snapshot(upstream, keys, now):
        value = snapshot(upstream, keys, now)
        rows = ledger.Ledger(root / 'evaluation-ledger.sqlite').pending()
        plan = json.loads((root / 'baseline-plan-temperature0.json').read_text())
        chat = [row for row in rows if row['operation_id']]
        if [row['sample_id'] for row in chat] != [s['sample_id'] for s in plan['samples'][:len(chat)]]:
            raise ValueError('Ledger is not the complete campaign prefix')
        if any(json.loads(row['reservation'])['state'] != 'COST_OBSERVED' for row in chat):
            raise ValueError('Previous operation cost unresolved')
        nonchat = [row for row in rows if not row['operation_id']]
        if len(nonchat) != 2:
            raise ValueError('Unexpected non-chat reservation')
        seed = next(row for row in nonchat if row['sample_id'] == 'seed-once')
        rejected = next(row for row in nonchat if row['sample_id'].endswith(':admission413'))
        if (json.loads(seed['reservation'])['reserved_usd'] != '0.002'
                or json.loads(rejected['reservation'])['state'] != 'VERIFIED_NO_DISPATCH_COST'
                or json.loads(rejected['reservation'])['reserved_usd'] != '0'):
            raise ValueError('Seed/rejection accounting changed')
        code = """import json
from sqlalchemy import create_engine,text
from app.core.config import Settings
with create_engine(Settings().database_url.get_secret_value()).connect() as c:
 print(json.dumps([str(r[0]) for r in c.execute(text('SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant'),{'tenant':'tenant-core'})]))
"""
        result = subprocess.run(['docker', 'exec', original.PROJECT + '-backend-1', 'python', '-c', code], capture_output=True, timeout=30)
        if result.returncode or set(json.loads(result.stdout)) != {r['operation_id'] for r in chat}:
            raise ValueError('Unaccounted durable operation')
        value['complete_ledger_history'] = {
            'historical_floor_usd': str(budget.HISTORICAL_FLOOR),
            'request_ids_sha256': hashlib.sha256(json.dumps(sorted(r['request_id'] for r in rows)).encode()).hexdigest(),
            'basis': 'exclusive B keys; complete ordered campaign ledger equals isolated tenant operations; seed and rejected admission retained',
        }
        return value
    budget.accounting_snapshot = audited_snapshot
    original.module = lambda name: budget if name == 'budget' else ledger if name == 'ledger' else old_module(name)
    try: original.main()
    except original.AccountingPending:
        print(json.dumps({'state': 'WAITING_ACCOUNTING', 'action': 'read counters again; no new generation'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try: main(args.root)
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'action': 'preserve ledger; inspect coverage or budget'}))
        raise SystemExit(1)
