"""JUP-133: reproduce descriptive 23/25 October projections, without network or model calls.

Only allowlisted, public observations are inputs. `--check` verifies committed
artifacts. The generated SQL is additive and must be reviewed before deployment;
this program never connects to a database or changes credentials.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'docs/evidence/JUP-133/evolution-20261025'
MANIFEST = ROOT / 'docs/validation/evaluation-evolution-runs.json'
RUN_IDS = {'friday': 'jup133-evolution-friday-20261023', 'sunday': 'jup133-evolution-sunday-20261025'}


def load_tool():
    spec = importlib.util.spec_from_file_location('evaluation_dashboard', ROOT / 'tools/evaluation-dashboard.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def common(rows, period):
    """Exclude Friday's 13 repeated references per robustness run and Sunday's six extras."""
    if period == 'friday':
        return [r for r in rows if not (r['campaign'] == 'jup071' and r['case_id'].startswith('JUP-069-'))]
    return [r for r in rows if r['case_id'].startswith(('JUP-069-', 'JUP-071-'))]


def validate_observations(report):
    expected_ids = {f'JUP-069-{i:03}' for i in range(1, 29)} | {f'JUP-071-{i:03}' for i in range(1, 17)}
    for period, size, repeats in (('friday', 171, 3), ('sunday', 50, 1)):
        rows = report[period]['cases']
        if len(rows) != size:
            raise ValueError(f'{period}: unexpected population')
        selected = common(rows, period)
        if Counter(r['case_id'] for r in selected) != Counter({k: repeats for k in expected_ids}):
            raise ValueError(f'{period}: missing or duplicated paired case')
        keys = [(r.get('campaign'), r.get('repetition'), r['case_id']) for r in rows]
        if len(set(keys)) != len(keys):
            raise ValueError(f'{period}: duplicate observation')
        for r in rows:
            if r['state'] not in ('completed', 'failed') or type(r['attempts']) is not int or r['attempts'] < 1:
                raise ValueError('invalid terminal state or attempt count')
            if type(r['seconds']) not in (int, float) or not math.isfinite(r['seconds']) or r['seconds'] < 0:
                raise ValueError('invalid elapsed time')
            cost = Decimal(r['cost_usd'])
            if not cost.is_finite() or cost < 0:
                raise ValueError('invalid observed cost')
            if period == 'sunday' and r['functional_verdict'] not in ('PASS', 'PARTIAL', 'FAIL'):
                raise ValueError('invalid functional verdict')
    if report['accepted'] is not False or report['matching']['exact_prompt_equal'] != 0:
        raise ValueError('unexpected acceptance or prompt comparability')


def statistics_for(rows):
    times = sorted(r['seconds'] for r in rows)
    return dict(operations=len(rows), completed=sum(r['state'] == 'completed' for r in rows),
                failed=sum(r['state'] == 'failed' for r in rows),
                attempts=sum(r['attempts'] for r in rows),
                retried=sum(r['attempts'] > 1 for r in rows),
                median_seconds=statistics.median(times), p95_seconds=times[math.ceil(len(times)*.95)-1],
                max_seconds=max(times), observed_cost_usd=str(sum((Decimal(r['cost_usd']) for r in rows), Decimal(0))))


def metric(group, name, population, value, unit, denominator=None, numerator=None, judgment='automatic'):
    return dict(measure_type='A', grp=group, metric_id=name, behavior=population,
                status='not_measured' if value is None else 'measured', count=None, value=value,
                unit=unit, numerator=numerator, denominator=denominator, ci_low=None, ci_high=None,
                judgment=judgment, selected=False)


def project(report, period, tool):
    observed = report[period]
    selected = common(observed['cases'], period)
    populations = {'full': observed['cases'], 'common44': selected,
                   'general28': [r for r in selected if r['case_id'].startswith('JUP-069-')],
                   'robust16': [r for r in selected if r['case_id'].startswith('JUP-071-')]}
    if period == 'sunday':
        populations['reported4'] = [r for r in observed['cases'] if r['bank'] == 'reported']
        populations['screen2'] = [r for r in observed['cases'] if r['case_id'].startswith('screen-')]
    run = {k: None for k in tool.RUN_KEYS}
    run.update(run_id=RUN_IDS[period], source='JUP-133', run_at=observed['ended_at'],
               commit=observed['commit'], suite='descriptive-friday-sunday',
               suite_version='polling-v1' if period == 'friday' else 'client-capture-v1',
               suite_sha256=hashlib.sha256(render(report['matching']).encode()).hexdigest(),
               synthetic=False, **{k: report['identity'][k] for k in tool.IDENTITY_KEYS if k in report['identity']})
    # NULL aliases/hashes remain unknown; never copy Friday's key to create a comparable series.
    rows, summary = [], {}
    for name, samples in populations.items():
        if not samples:
            raise ValueError(f'{period}.{name}: empty population')
        stats = statistics_for(samples); summary[name] = stats
        n = stats['operations']
        for key in ('operations', 'completed', 'failed', 'attempts', 'retried'):
            rows.append(metric('evolution_operations', key, name, stats[key], 'recuento', n))
        for key in ('completed', 'retried'):
            rows.append(metric('evolution_operations', key + '_rate', name, stats[key]/n, 'tasa', n, stats[key]))
        for key in ('median_seconds', 'p95_seconds', 'max_seconds'):
            rows.append(metric('evolution_times', key, name, stats[key], 's', n))
        # Different metric IDs prevent an accidental cross-period homogeneous cost series.
        cost_id = 'gateway_settled_with_embeddings' if period == 'friday' else 'chat_observed_incomplete'
        rows.append(metric('evolution_cost', cost_id, name, float(stats['observed_cost_usd']), 'usd', n))
        if period == 'sunday':
            for verdict in ('PASS', 'PARTIAL', 'FAIL'):
                rows.append(metric('evolution_agent_functional', verdict.lower(), name,
                                   sum(r['functional_verdict'] == verdict for r in samples), 'casos', n))
    rows.append(metric('evolution_human', 'acceptance', 'full', None, 'tasa', judgment='human'))
    document = dict(contract_version=1, run=run, results=rows)
    tool.validate_rows(run, rows)
    return document, summary


def additive_sql(dataset, tool):
    """Existing identity must match ALL metadata and rows, not merely its digest."""
    pairs = tool._validate_dataset(dataset)
    if {run['run_id'] for run, _ in pairs} != set(RUN_IDS.values()):
        raise ValueError('Only the two fixed JUP-133 projections may be appended')
    inserts = '\n\n'.join(tool._insert_blocks(pairs))
    inserts = inserts.replace('INSERT INTO evaluation.runs', 'INSERT INTO evolution_runs')
    inserts = inserts.replace('INSERT INTO evaluation.results', 'INSERT INTO evolution_results')
    return r"""\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '15s';
SET LOCAL standard_conforming_strings = on;
LOCK TABLE evaluation.runs, evaluation.results IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE evolution_runs (LIKE evaluation.runs INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE evolution_results (LIKE evaluation.results INCLUDING ALL) ON COMMIT DROP;
""" + inserts + """
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM evolution_runs n JOIN evaluation.runs o USING (run_id)
    WHERE to_jsonb(n) IS DISTINCT FROM to_jsonb(o)
  ) OR EXISTS (
    (SELECT to_jsonb(n) FROM evolution_results n JOIN evaluation.runs o USING(run_id)
     EXCEPT ALL
     SELECT to_jsonb(o) FROM evaluation.results o JOIN evolution_runs n USING(run_id))
    UNION ALL
    (SELECT to_jsonb(o) FROM evaluation.results o JOIN evolution_runs n USING(run_id)
     EXCEPT ALL
     SELECT to_jsonb(n) FROM evolution_results n JOIN evaluation.runs o USING(run_id))
  ) THEN
    RAISE EXCEPTION 'JUP-133 evolution identity/content conflict; reconcile before loading';
  END IF;
END $$;
CREATE TEMP TABLE evolution_missing ON COMMIT DROP AS
SELECT n.run_id FROM evolution_runs n WHERE NOT EXISTS
(SELECT 1 FROM evaluation.runs o WHERE o.run_id=n.run_id);
INSERT INTO evaluation.runs SELECT n.* FROM evolution_runs n JOIN evolution_missing m USING(run_id);
INSERT INTO evaluation.results SELECT n.* FROM evolution_results n JOIN evolution_missing m USING(run_id);
COMMIT;
"""


def artifacts():
    tool = load_tool()
    report = json.loads((DIRECTORY / 'observations.json').read_text(encoding='utf-8'))
    validate_observations(report)
    outputs, summary = {}, {}
    for period in RUN_IDS:
        rows, summary[period] = project(report, period, tool)
        outputs[DIRECTORY / f'{period}.rows.json'] = render(rows)
    outputs[DIRECTORY / 'summary.json'] = render(summary)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify committed projections without writing')
    args = parser.parse_args()
    outputs = artifacts()
    if args.check:
        for path, content in outputs.items():
            if path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Outdated projection: {path.relative_to(ROOT)}')
    else:
        for path, content in outputs.items():
            path.write_text(content, encoding='utf-8')
    tool = load_tool()
    sql = additive_sql(tool.build_dataset([MANIFEST], root=ROOT), tool)
    path = DIRECTORY / 'append.sql'
    if args.check:
        if path.read_text(encoding='utf-8') != sql:
            raise SystemExit('Outdated additive SQL')
    else:
        path.write_text(sql, encoding='utf-8')
    print('JUP-133: two projections and additive SQL verified' if args.check else 'JUP-133: artifacts generated; no database contacted')


if __name__ == '__main__':
    main()
