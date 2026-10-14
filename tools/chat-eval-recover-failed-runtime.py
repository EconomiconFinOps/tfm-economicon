"""Recover the latest isolated campaign failure; never dispatch inference.

Uses the existing operator adapter for private credentials and verified runtime.
Stops on identity, accounting, provider, attempt or snapshot ambiguity.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUERY = """
import json,sys
from sqlalchemy import create_engine,text
from app.core.config import Settings
p=json.load(sys.stdin)
with create_engine(Settings().database_url.get_secret_value()).connect() as c:
 r=c.execute(text('SELECT tenant_id,operation_id,conversation_id,client_request_id,question_message_id,question_content,state,attempt_count,attempts FROM chat_operations WHERE operation_id=:id AND tenant_id=:tenant'),p).mappings().one()
 d={k:str(r[k]) if k.endswith('_id') else r[k] for k in r if k!='attempts'}
 a=r['attempts'];a=json.loads(a) if isinstance(a,str) else a
 d['attempt_ids']=[x['attempt_id'] for x in a]
 print(json.dumps(d))
"""


def main(root):
    adapter = load('operator_adapter', root / 'live-step.py')
    failed = load('failed', Path(__file__).with_name('chat-eval-failed.py'))
    ledger = adapter.module('ledger').Ledger(root / 'evaluation-ledger.sqlite')
    entries = ledger.pending()
    pending = [e for e in entries if e['operation_id'] and json.loads(e['reservation'])['state'] != 'COST_OBSERVED']
    if not pending:
        return {'state': 'NO_PENDING_FAILURE'}
    if len(pending) != 1 or pending[0] != entries[-1]:
        raise ValueError('Only the latest exclusive operation can be reconciled')
    entry = pending[0]
    path = root / 'baseline-n3' / (entry['sample_id'].replace(':', '-') + '.json')
    if not path.exists(): return {'state': 'NO_TERMINAL_RECEIPT'}
    raw = path.read_bytes(); receipt = json.loads(raw); row = receipt['results'][0]
    if row['operation']['state'] != 'failed': return {'state': 'NOT_FAILED'}
    plan = json.loads((root / 'baseline-plan-temperature0.json').read_text())
    sample = next(s for s in plan['samples'] if s['sample_id'] == entry['sample_id'])
    if receipt['plan_sha256'] != entry['plan_hash'] or failed.collect.digest(plan) != entry['plan_hash']:
        raise ValueError('Plan differs from ledger')
    if row['operation']['operation_id'] != entry['operation_id']:
        raise ValueError('Operation differs from ledger')
    adapter.module('runtime').verify_container(plan, 'backend', adapter.PROJECT + '-backend-1', adapter.PROJECT)
    output = subprocess.run(['docker', 'exec', '-i', adapter.PROJECT + '-backend-1', 'python', '-c', QUERY],
        input=json.dumps({'id': entry['operation_id'], 'tenant': 'tenant-core'}).encode(), capture_output=True, timeout=30)
    if output.returncode: raise ValueError('Cannot read durable input')
    snapshot = json.loads(output.stdout)
    derived = failed.reconcile(row, snapshot, sample, 'tenant-core')
    if derived['collection_state'] != 'VERIFIED_PUBLIC_SNAPSHOT': raise ValueError('Unstable/incomplete public evidence')
    pre = json.loads((root / 'last-preflight.json').read_text())
    if pre['accounting']['evidence_sha256'] != json.loads(entry['reservation'])['accounting_evidence_sha256']:
        raise ValueError('Preflight does not belong to latest reservation')
    usage = adapter.module('usage').read(adapter.PROJECT + '-processor-1', entry['operation_id'], pre['observed_at'])
    if len(snapshot['attempt_ids']) != 1 or len(usage['reports']) != 1:
        raise ValueError('Multiple/missing attempts require manual reconciliation')
    report = usage['reports'][0]
    if report['attempt_id'] != snapshot['attempt_ids'][0] or report['attempted_legs'] != len(report['requests']):
        raise ValueError('Attempt/leg mismatch')
    ge = adapter.envfile(Path('/home/danteadmin/economicon-jup078-gateway/.env'))
    keys = json.loads((root / 'validation-keys.json').read_text())
    since = datetime.fromisoformat(pre['observed_at'])
    logs = adapter.request('http://127.0.0.1:44000/spend/logs?' + urlencode({
        'api_key': keys['processor'], 'start_date': since.date().isoformat(), 'summarize': 'false'}), token=ge['LITELLM_MASTER_KEY'])
    gateway = [{k: x.get(k) for k in ('request_id', 'spend', 'startTime', 'endTime', 'model')}
               for x in logs if datetime.fromisoformat(x['startTime'].replace('Z', '+00:00')) >= since]
    if len(gateway) != report['attempted_legs'] or len({x['request_id'] for x in gateway}) != len(gateway):
        raise ValueError('Gateway phase count mismatch')
    upstream = []
    for item in gateway:
        data = adapter.request('https://openrouter.ai/api/v1/generation?' + urlencode({'id': item['request_id']}), token=ge['OPENROUTER_API_KEY'])['data']
        if (data['id'] != item['request_id'] or data['provider_name'] != 'DeepInfra'
                or not data['model'].startswith('z-ai/glm-5.2') or item['model'] != 'openrouter/z-ai/glm-5.2'):
            raise ValueError('Provider mismatch')
        upstream.append({k: data.get(k) for k in ('id', 'total_cost', 'provider_name', 'model', 'created_at', 'finish_reason')})
    money = adapter.module('budget').money
    infos = {k: adapter.request('http://127.0.0.1:44000/key/info?' + urlencode({'key': v}), token=ge['LITELLM_MASTER_KEY'])['info'] for k, v in keys.items()}
    before = pre['accounting']['evidence']['keys']
    delta = money(infos['processor']['spend']) - money(before['processor']['spend'])
    observed = sum((money(x['spend']) for x in gateway), Decimal(0))
    if abs(delta - observed) > Decimal('0.000000001'): raise ValueError('Gateway key spend not settled')
    chat = sum((max(money(g['spend']), money(u['total_cost'])) for g, u in zip(gateway, upstream)), Decimal(0))
    if chat < money(report['observed']['cost_usd']): raise ValueError('Upstream costs below SDK observed cost')
    auxiliary = money(infos['backend']['spend']) - money(before['backend']['spend'])
    if not 0 <= auxiliary <= Decimal('.002'): raise ValueError('Auxiliary cost mismatch')
    proof = {'durable_input': snapshot, 'usage': usage, 'gateway': gateway, 'upstream': upstream,
             'auxiliary_cost_usd': str(auxiliary), 'total_cost_usd': str(chat + auxiliary), 'preflight': pre}
    rawpath = root / 'baseline-raw-api' / path.name
    if rawpath.exists():
        if rawpath.read_bytes() != raw: raise ValueError('Different original receipt already preserved')
    else:
        with rawpath.open('xb') as handle: handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    proofpath = root / ('failed-reconciliation-' + entry['operation_id'] + '.json')
    with proofpath.open('w') as handle: json.dump(proof, handle); handle.flush(); os.fsync(handle.fileno())
    with ledger.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = db.execute('SELECT * FROM attempts WHERE request_id=?', (entry['request_id'],)).fetchone()
        if dict(current) != entry: raise ValueError('Ledger changed during reconciliation')
        reservation = json.loads(entry['reservation'])
        if chat + auxiliary > money(reservation['reserved_usd']): raise ValueError('Cost exceeds reservation')
        reservation.update(maximum_reserved_usd=reservation['reserved_usd'], reserved_usd=str(chat + auxiliary),
            state='COST_OBSERVED', attempt_reports=usage['reports'], upstream_reconciliation=proof,
            auxiliary_cost_usd=str(auxiliary))
        db.execute('UPDATE attempts SET reservation=? WHERE request_id=?', (json.dumps(reservation), entry['request_id']))
    receipt['results'] = [derived]
    temp = path.with_suffix('.reconciled.tmp')
    with temp.open('w') as handle: json.dump(receipt, handle, ensure_ascii=False, indent=2); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)
    return {'state': 'FAILED_RECONCILED', 'sample_id': entry['sample_id'], 'cost_usd': str(chat + auxiliary)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try: print(json.dumps(main(args.root)))
    except Exception as exc:
        # Never print URL-bearing exception messages: gateway URLs contain keys.
        print(json.dumps({'state': 'RECONCILIATION_STOPPED', 'exception_class': type(exc).__name__}))
        raise SystemExit(1)
