"""Read-only audit of the pinned Atlas candidate; stdlib only, no services."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = 'ffb5d307772f697cffb8b1e73e6330250e093601'
CANDIDATE = 'e730dc15fb3feb45a3b346fc9e48332c4608b049'

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == CANDIDATE
spec = importlib.util.spec_from_file_location('evaluation_review', ROOT / 'tools/evaluation-dashboard.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
dataset = evaluation.build_dataset([evaluation.DEFAULT_MANIFEST], root=ROOT)
paired_manifest = ROOT / 'docs/validation/evaluation-glm-deepseek-runs.json'
assert paired_manifest.is_file(), 'Find the versioned paired manifest before continuing'
dataset['runs'].extend(evaluation.build_dataset([paired_manifest], root=ROOT)['runs'])
pairs = evaluation._validate_dataset(dataset)
expected_runs = [evaluation._tuple_line(evaluation.RUN_COLUMNS, run) for run, _ in pairs]
expected_results = [evaluation._tuple_line(evaluation.RESULT_COLUMNS, row, (evaluation.sql_literal(run['run_id']),)) for run, rows in pairs for row in rows]
raw = (ROOT / 'apps/backend/app/aws_atlas_data/evaluations.sql').read_bytes()
sql = raw.decode('utf-8')
incoming_runs = sql.split('INSERT INTO handoff_incoming_runs ', 1)[1].split(' VALUES\n', 1)[1].split('\n\n', 1)[0]
incoming_results = re.findall(r'INSERT INTO handoff_incoming_results [^\n]+ VALUES\n(.*?);\n', sql, re.S)
actual_runs = [line.rstrip(',;') for line in incoming_runs.splitlines()]
actual_results = [line.rstrip(',;') for block in incoming_results for line in block.splitlines()]
assert Counter(actual_runs) == Counter(expected_runs)
assert Counter(actual_results) == Counter(expected_results)
assert len(actual_runs) == 19 and len(actual_results) == 1688
assert hashlib.sha256(raw).hexdigest() == 'b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09'
manifest = json.loads((ROOT / 'apps/backend/app/aws_atlas_data/manifest.json').read_text())
assert {entry['run_id']: (entry['report_sha256'], entry['results']) for entry in manifest['entries']} == {run['run_id']: (run['report_sha256'], len(rows)) for run, rows in pairs}
dashboards = []
for path in sorted((ROOT / 'apps/monitoring/grafana/dashboards').glob('*.json')):
    rel = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(['git', 'show', BASE + ':' + rel], cwd=ROOT)
    assert original.replace(b'\r\n', b'\n') == path.read_bytes().replace(b'\r\n', b'\n')
    doc = json.loads(path.read_text(encoding='utf-8'))
    dashboards.append({'uid': doc['uid'], 'panels': len(doc['panels']), 'base_unchanged': True})
assert len(dashboards) == 3
print(json.dumps({'base': BASE, 'candidate': CANDIDATE, 'sql_sha256': hashlib.sha256(raw).hexdigest(), 'all_source_rows_equal': True, 'runs': len(actual_runs), 'results': len(actual_results), 'manifest_matches': True, 'dashboards': dashboards, 'rolling_vcpu': 3 * (2 * 150 // 100) * .5 + 1}, indent=2))
