"""Sequential isolated campaign: collect/reconcile each sample before advancing."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main(root, covered_step=False, additional_plans=(), adapter_path=None, retrieval_path=None, retain_unknown_cost=False):
    if additional_plans and not covered_step:
        raise ValueError('Additional campaigns require audited coverage')
    if adapter_path and (not covered_step or not retrieval_path):
        raise ValueError('Candidate adapter requires audited coverage and explicit retrieval recovery')
    for _ in range(3000):
        commands = [
            [sys.executable, str(retrieval_path or root / 'recover-retrieval.py')],
            [sys.executable, str(Path(__file__).with_name('chat-eval-recover-failed-runtime.py')), '--root', str(root)],
        ]
        if retain_unknown_cost:
            commands[1].append('--retain-unknown-cost')
        if adapter_path:
            commands[1].extend(['--adapter', str(adapter_path)])
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True, timeout=90)
            if result.returncode:
                print(json.dumps({'campaign': 'STOPPED', 'reason': 'evidence/cost reconciliation requires inspection'}), flush=True)
                return
        step = ([sys.executable, str(Path(__file__).with_name('chat-eval-covered-step.py')), '--root', str(root)]
                if covered_step else [sys.executable, str(root / 'live-step.py')])
        for plan in additional_plans:
            step.extend(['--additional-plan', str(plan)])
        if adapter_path:
            step.extend(['--adapter', str(adapter_path)])
        result = subprocess.run(step, capture_output=True, text=True, timeout=90)
        if result.returncode:
            print(json.dumps({'campaign': 'STOPPED', 'reason': 'step error; preserve ledger and inspect'}), flush=True)
            return
        state = json.loads(result.stdout.strip().splitlines()[-1])
        print(json.dumps(state), flush=True)
        if state.get('state') not in ('OBSERVING', 'COLLECTED_ONE', 'COST_RECONCILED', 'WAITING_ACCOUNTING'):
            print(json.dumps({'campaign': 'STOPPED', 'reason': state.get('state')}), flush=True)
            return
        time.sleep(10 if state['state'] in ('OBSERVING', 'WAITING_ACCOUNTING') else 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--covered-step', action='store_true')
    parser.add_argument('--additional-plan', type=Path, action='append', default=[])
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--retrieval-recovery', type=Path)
    parser.add_argument('--retain-unknown-cost', action='store_true')
    args = parser.parse_args()
    try: main(args.root, args.covered_step, args.additional_plan, args.adapter, args.retrieval_recovery, args.retain_unknown_cost)
    except Exception as exc:
        print(json.dumps({'campaign': 'STOPPED', 'exception_class': type(exc).__name__}), flush=True)
        raise SystemExit(1)
