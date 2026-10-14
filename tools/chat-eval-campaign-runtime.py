"""Sequential isolated campaign: collect/reconcile each sample before advancing."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main(root):
    for _ in range(3000):
        commands = [
            [sys.executable, str(root / 'recover-retrieval.py')],
            [sys.executable, str(Path(__file__).with_name('chat-eval-recover-failed-runtime.py')), '--root', str(root)],
        ]
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True, timeout=90)
            if result.returncode:
                print(json.dumps({'campaign': 'STOPPED', 'reason': 'evidence/cost reconciliation requires inspection'}), flush=True)
                return
        result = subprocess.run([sys.executable, str(root / 'live-step.py')], capture_output=True, text=True, timeout=90)
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
    args = parser.parse_args()
    try: main(args.root)
    except Exception as exc:
        print(json.dumps({'campaign': 'STOPPED', 'exception_class': type(exc).__name__}), flush=True)
        raise SystemExit(1)
