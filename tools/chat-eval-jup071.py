"""Bridge JUP-071's versioned suite to terminal chat snapshots; GET only.

The suite root is trusted local Python code, imported explicitly. This tool never
creates conversations, generates answers, retries inference or evaluates quality.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


collector = load('chat_eval_collect', Path(__file__).with_name('chat-eval-collect.py'))
retrieval = load('chat_eval_retrieval', Path(__file__).with_name('chat-eval-retrieval.py'))


class AdapterError(ValueError):
    """Only adapter-owned, constant diagnostic messages may reach the CLI."""


def require(condition, message):
    if not condition:
        raise AdapterError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def suite_tool(root):
    return load('chat_eval_jup071_suite', Path(root).resolve() / 'tools/assistant-robustness.py')


def plan_for(tool, repetitions):
    require(type(repetitions) is int and repetitions in (1, 3, 5), 'Use N=1, 3 or 5')
    suite, baseline = tool.load_suite()  # The suite owns its corpus/hash validation.
    cases = tool.campaign(suite, baseline)
    require(len(cases) == 29 and len({c['id'] for c in cases}) == 29,
            'Review the adapter when the 29-case JUP-071 suite changes')
    sources = [Path(tool.__file__), tool.ROOT / 'tools/assistant-eval.py',
               tool.ROOT / 'tools/assistant-metrics.py', tool.ROOT / 'tools/retrieval-calibration.py',
               tool.SUITE, tool.BASELINE, tool.SERVICE, tool.evaluation.RULES_PATH,
               tool.ROOT / suite['methodology']['path'],
               *(tool.ROOT / s['path'] for s in suite['sources'].values())]
    return {'version': 2, 'jup': 'JUP-071', 'repetitions': repetitions,
            'bank_sha256': tool.file_digest(tool.SUITE), 'suite_sha256': tool.digest(suite),
            'suite_commit': tool.code_commit(),
            'suite_files': {p.relative_to(tool.ROOT).as_posix(): tool.file_digest(p) for p in sources},
            'samples': [{'sample_id': f"{c['id']}:r{r}", 'case_id': c['id'],
                         'repetition': r, 'content': tool.evaluation.prompt_text(c)}
                        for r in range(1, repetitions + 1) for c in cases]}


def validate_plan(plan, tool):
    expected = plan_for(tool, plan['repetitions'])
    if plan['version'] == 1:
        # Existing receipts remain readable under their original, commit-pinned contract.
        expected['version'] = 1
        for name in ('tools/assistant-metrics.py', 'tools/retrieval-calibration.py'):
            expected['suite_files'].pop(name)
    else:
        require(plan['version'] == 2, 'Unsupported plan version; prepare a new plan')
        expected['suite_commit'] = plan.get('suite_commit')  # Informational, not source identity.
    require(plan == expected, 'Plan or suite differs from frozen sources; prepare a new plan')


def outside(path, suite_root):
    path = Path(path).resolve()
    for root in (ROOT, Path(suite_root).resolve()):
        require(path != root and root not in path.parents, 'Outputs must be outside both checkouts')
    require(not any((p / '.git').exists() for p in path.parents), 'Output is inside another checkout')
    return path


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def handles_for(plan, rows):
    require(isinstance(rows, list), 'Handles must be a JSON list')
    expected = {s['sample_id'] for s in plan['samples']}
    result, conversations, operations = {}, set(), set()
    for row in rows:
        require(set(row) == {'sample_id', 'conversation_id', 'operation_id'}, 'Invalid handle fields')
        sid = row['sample_id']
        cid, oid = collector.identifier(row['conversation_id']), collector.identifier(row['operation_id'])
        require(sid in expected and sid not in result, 'Unknown or duplicate sample')
        require(cid not in conversations and oid not in operations, 'Use a fresh operation/conversation per sample')
        result[sid] = row
        conversations.add(cid)
        operations.add(oid)
    return result


def collect_all(plan, handles, get, output, snapshots=None):
    """Persist each attempt before the batch manifest; never overwrite a directory."""
    handles = handles_for(plan, handles)
    snapshots = snapshots or []
    require(isinstance(snapshots, list), 'Retrieval snapshots must be a list')
    by_operation = {}
    for snapshot in snapshots:
        oid = collector.identifier(snapshot['operation_id'])
        require(oid not in by_operation and oid in {h['operation_id'] for h in handles.values()},
                'Duplicate or unrelated retrieval snapshot')
        by_operation[oid] = snapshot
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'plan.json', plan)
    write_new(output / 'handles.json', list(handles.values()))
    entries = []
    for sample in plan['samples']:
        handle = handles.get(sample['sample_id'])
        if handle is None:
            continue  # Missing stays missing, never a fabricated answer.
        observation_errors = []
        def observed_get(path):
            try:
                return get(path)
            except Exception as exc:
                observation_errors.append({'class': type(exc).__name__,
                                           'http_status': getattr(exc, 'code', None)})
                raise
        try:
            row = collector.collect(observed_get, sample, handle['conversation_id'], handle['operation_id'])
        except Exception as exc:
            # Preserve an observation failure without leaking response/exception text.
            if hasattr(exc, 'close'):
                exc.close()
            row = {'id': sample['case_id'], 'repetition': sample['repetition'],
                   'conversation_id': handle['conversation_id'], 'operation': {'operation_id': handle['operation_id']},
                   'state': 'unobserved', 'collection_state': 'INCOMPLETE',
                   'collection_errors': {'observation': observation_errors[0] if observation_errors
                                         else {'class': type(exc).__name__}},
                   'resources': {}, 'resources_sha256': collector.digest({})}
        receipt = {'version': 1, 'bank_sha256': plan['bank_sha256'],
                   'repetitions': plan['repetitions'], 'plan_sha256': collector.digest(plan), 'results': [row]}
        name = sample['sample_id'].replace(':', '-') + '.json'
        write_new(output / 'originals' / name, receipt)
        original_sha = collector.digest(receipt)
        if handle['operation_id'] in by_operation:
            snapshot = by_operation[handle['operation_id']]
            write_new(output / 'retrieval' / name, snapshot)
            try:
                row = retrieval.reconcile(row, snapshot, sample)
                receipt = {**receipt, 'results': [row]}
            except (ValueError, KeyError, TypeError, AttributeError):
                row = {**row, 'collection_state': 'INCOMPLETE',
                       'collection_errors': {**row.get('collection_errors', {}),
                                             'retrieval_supplement': {'class': 'RejectedSnapshot'}}}
                receipt = {**receipt, 'results': [row]}
        write_new(output / name, receipt)
        entries.append({'sample_id': sample['sample_id'], 'file': name, 'sha256': collector.digest(receipt),
                        'original_sha256': original_sha})
    manifest = {'version': 1, 'plan_sha256': collector.digest(plan), 'receipts': entries,
                'collected_at': datetime.now(timezone.utc).isoformat()}
    write_new(output / 'manifest.json', manifest)
    return manifest


def rows_from(plan, directory):
    directory = Path(directory)
    require(read(directory / 'plan.json') == plan, 'Collection plan differs')
    manifest = read(directory / 'manifest.json')
    require(manifest['plan_sha256'] == collector.digest(plan), 'Manifest belongs to another plan')
    handles = handles_for(plan, read(directory / 'handles.json'))
    samples = {s['sample_id']: s for s in plan['samples']}
    rows = {}
    for entry in manifest['receipts']:
        sid = entry['sample_id']
        require(sid in handles and sid not in rows, 'Unknown or duplicate receipt')
        require(entry['file'] == sid.replace(':', '-') + '.json', 'Unexpected receipt path')
        receipt = read(directory / entry['file'])
        original = read(directory / 'originals' / entry['file'])
        require(collector.digest(original) == entry['original_sha256'], 'Original receipt changed')
        require(collector.digest(receipt) == entry['sha256'], 'Receipt changed after collection')
        require(receipt['plan_sha256'] == collector.digest(plan)
                and receipt['bank_sha256'] == plan['bank_sha256']
                and receipt['repetitions'] == plan['repetitions']
                and len(receipt['results']) == 1, 'Receipt does not match plan')
        row = receipt['results'][0]
        require(row['resources'] == original['results'][0]['resources'], 'Original public resources replaced')
        sample, handle = samples[sid], handles[sid]
        require(row['id'] == sample['case_id'] and row['repetition'] == sample['repetition']
                and row['conversation_id'] == handle['conversation_id']
                and row['operation']['operation_id'] == handle['operation_id'], 'Receipt identity differs')
        require(row['resources_sha256'] == collector.digest(row['resources']), 'Public resources changed')
        rows[sid] = row
    require(set(rows) == set(handles), 'A handled sample has no receipt; preserve the interrupted collection')
    return rows, manifest


def checked_row(sample, row):
    """Recheck from originals; never trust an edited VERIFIED flag or derived answer."""
    raw = row['resources']
    cid, oid = row['conversation_id'], row['operation']['operation_id']
    base = '/assistant/conversations/' + collector.identifier(cid)
    op = base + '/generations/' + collector.identifier(oid)
    calls = 0
    def get(path):
        nonlocal calls
        if path == op:
            calls += 1
            return raw['operation' if calls == 1 else 'operation_after']
        key = {base: 'history', op + '/context': 'context', op + '/evidence': 'evidence',
               op + '/result': 'result'}[path]
        return raw[key]
    try:
        checked = collector.collect(get, sample, cid, oid)
        if 'retrieval_supplement' in row:
            require(row['retrieval_supplement_sha256'] == collector.digest(row['retrieval_supplement']),
                    'Retrieval supplement changed')
            checked = retrieval.reconcile(checked, row['retrieval_supplement'], sample)
    except (ValueError, KeyError, TypeError, AttributeError):
        checked = None
    verified = (checked is not None and row['collection_state'] == 'VERIFIED_PUBLIC_SNAPSHOT'
          and checked['collection_state'] == 'VERIFIED_PUBLIC_SNAPSHOT'
          and checked['state'] == 'completed' and not row.get('collection_errors'))
    return checked, verified


def measured_distance(value):
    return type(value) in (int, float) and math.isfinite(value)


def public_row(sample, row, *, accepts_unmeasured_distance=False):
    checked, verified = checked_row(sample, row)
    corpus = [item for item in (checked or {}).get('authorized_evidence', []) if item.get('kind') == 'corpus']
    # Capability negotiation only permits absent/null distances, never malformed values.
    ok = verified and all(measured_distance(item.get('distance')) or
                          (accepts_unmeasured_distance is True and item.get('distance') is None)
                          for item in corpus)
    result = (checked or {}).get('result', {})
    response = result.get('metadata', {}).get('response', {})
    chunks = [{'chunk_id': item['id'], 'source': item['source'], 'content': item['content'],
               'distance': item.get('distance')} for item in corpus] if ok else []
    citations = [item['id'] for item in response.get('evidence', [])]
    statuses = ('ok', 'partial', 'no_data', 'insufficient_data', 'unsupported', 'refused', 'error')
    status = response.get('status')
    actions = response.get('next_actions')
    return {'case': sample['case_id'], 'prompt': sample['content'],
            'answer': result.get('content', '') if ok else '',
            'citations': citations if ok else [], 'retrieved': chunks,
            'public_evidence': (checked or {}).get('authorized_evidence', []),
            'structured': {'status': status if verified and status in statuses else None,
                           'has_next_actions': bool(actions) if verified and isinstance(actions, list) else None},
            'failure_category': None if ok else 'invalid_response', 'total_ms': None}


def server_reported(sample, row):
    """Copy provenance from rechecked public resources, never from run-info or sidecar labels."""
    checked, verified = checked_row(sample, row)
    raw = (checked or {}).get('resources', {})
    generation = (raw.get('result') or {}).get('metadata', {}).get('generation', {})
    initial = (raw.get('context') or {}).get('manifest', {})
    effective = generation.get('context_manifest', {})
    reported = {'sample_id': sample['sample_id'], 'snapshot_verified': verified,
                'attested': False}
    for key in ('prompt_version', 'prompt_sha256', 'response_schema_sha256',
                'assembler_sha256', 'tokenizer_sha256'):
        # prompt_version includes its server-provided bundle hash; it is not a prompt SHA.
        if key in effective:
            reported[key] = effective[key]
        elif key in initial:
            reported[key] = initial[key]
        elif key == 'prompt_version':
            reported[key] = generation.get(key, (raw.get('operation') or {}).get(key))
    if 'usage' in generation:
        reported['usage'] = generation['usage']
    return reported


def collection_summary(plan, rows):
    return {'planned': len(plan['samples']), 'observed': len(rows),
            'missing': len(plan['samples']) - len(rows),
            'collection_states': dict(sorted(Counter(row['collection_state'] for row in rows.values()).items())),
            'operation_states': dict(sorted(Counter(row['state'] for row in rows.values()).items()))}


def collection_complete(summary):
    return (summary['missing'] == 0
            and summary['collection_states'].get('VERIFIED_PUBLIC_SNAPSHOT', 0) == summary['planned']
            and summary['operation_states'].get('completed', 0) == summary['planned'])


def export_summary(raws):
    rows = [row for raw in raws for row in raw['cases']]
    return {'exported': len(rows), 'blocked': sum(row['failure_category'] is not None for row in rows),
            'structured_statuses': dict(sorted(Counter(row['structured']['status'] or 'unknown' for row in rows).items()))}


def export_raw(tool, plan, directory, repetition, config):
    validate_plan(plan, tool)
    require(type(repetition) is int and 1 <= repetition <= plan['repetitions'], 'Invalid repetition')
    fields = {'commit', 'corpus', 'provider', 'alias', 'retrieval', 'generation'}
    require(set(config) == fields and all(isinstance(v, str) and v.strip() for v in config.values()),
            'run-info needs exactly six nonempty descriptive strings; no credentials')
    rows, manifest = rows_from(plan, directory)
    suite, baseline = tool.load_suite()
    cases = tool.campaign(suite, baseline)
    configuration = {**config,
                     'collector_manifest_sha256': collector.digest(manifest),
                     'collector_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    execution = tool.provenance(suite, 'live_unverified', configuration)
    # Identity is the frozen source snapshot. Unrelated suite commits must not
    # change exports or make paired repetitions incomparable after collection.
    execution['harness_commit'] = plan['suite_commit']
    execution['collected_at'] = manifest['collected_at']
    execution['collection'] = {'plan_sha256': collector.digest(plan),
                               'manifest_sha256': collector.digest(manifest), 'repetition': repetition,
                               'collected_at': manifest['collected_at'],
                               'accepts_unmeasured_distance': getattr(tool, 'ACCEPTS_UNMEASURED_DISTANCE', False) is True,
                               'server_reported': [server_reported(s, rows[s['sample_id']]) for s in plan['samples']
                                                   if s['repetition'] == repetition and s['sample_id'] in rows],
                               'limitations': ['Runtime/model and latency not attested by GET snapshots.',
                                               'Server provenance and usage are reported, not attested.',
                                               'Unmeasured corpus distances require an explicit evaluator capability; otherwise scoring is blocked.']}
    raw = {'raw_version': 1, 'execution': execution,
           'cases': [public_row(s, rows[s['sample_id']], accepts_unmeasured_distance=
                                getattr(tool, 'ACCEPTS_UNMEASURED_DISTANCE', False) is True) for s in plan['samples']
                     if s['repetition'] == repetition and s['sample_id'] in rows]}
    tool.validate_raw(raw, suite, cases)
    return raw


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--suite-root', type=Path, required=True, help='Trusted checkout containing JUP-071 tooling')
    sub = cli.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--repetitions', type=int, choices=(1, 3, 5), default=3)
    prepare.add_argument('--output', type=Path, required=True)
    collect = sub.add_parser('collect')
    collect.add_argument('--plan', type=Path, required=True)
    collect.add_argument('--handles', type=Path, required=True)
    collect.add_argument('--base-url', required=True)
    collect.add_argument('--output-dir', type=Path, required=True)
    collect.add_argument('--strict', action='store_true', help='Save receipts, then exit 3 unless all samples are verified and completed')
    collect.add_argument('--retrieval-snapshots', type=Path,
                         help='Optional exact recorded tool payloads; never reconstructed by another search')
    export = sub.add_parser('export')
    export.add_argument('--plan', type=Path, required=True)
    export.add_argument('--receipts', type=Path, required=True)
    repetitions = export.add_mutually_exclusive_group(required=True)
    repetitions.add_argument('--repetition', type=int)
    repetitions.add_argument('--all-repetitions', action='store_true')
    export.add_argument('--run-info', type=Path, required=True)
    export.add_argument('--output', type=Path, help='New file for --repetition')
    export.add_argument('--output-dir', type=Path, help='New directory for --all-repetitions')
    export.add_argument('--strict', action='store_true', help='Save exports, then exit 3 if any sample is missing or blocked')
    try:
        args = cli.parse_args(argv)
        tool = suite_tool(args.suite_root)
        summary = None
        strict_failed = False
        if args.command == 'prepare':
            write_new(outside(args.output, args.suite_root), plan_for(tool, args.repetitions))
        else:
            plan = read(args.plan)
            validate_plan(plan, tool)
            if args.command == 'collect':
                output = outside(args.output_dir, args.suite_root)
                handles = read(args.handles)
                handles_for(plan, handles)  # Reject duplicates before the first GET.
                get = collector.reader(args.base_url, os.environ['CHAT_EVAL_TOKEN'], os.environ['CHAT_EVAL_TENANT'])
                snapshots = read(args.retrieval_snapshots) if args.retrieval_snapshots else None
                collect_all(plan, handles, get, output, snapshots)
                rows, _ = rows_from(plan, output)
                summary = collection_summary(plan, rows)
                strict_failed = args.strict and not collection_complete(summary)
            else:
                require((args.all_repetitions and args.output_dir is not None and args.output is None)
                        or (not args.all_repetitions and args.output is not None and args.output_dir is None),
                        'Use --repetition with --output, or --all-repetitions with --output-dir')
                output = outside(args.output_dir if args.all_repetitions else args.output, args.suite_root)
                require(not output.exists(), 'Output already exists')
                config = read(args.run_info)
                selected = range(1, plan['repetitions'] + 1) if args.all_repetitions else [args.repetition]
                raws = [export_raw(tool, plan, args.receipts, repetition, config) for repetition in selected]
                if args.all_repetitions:
                    output.mkdir(parents=True, exist_ok=False)
                    for raw in raws:
                        repetition = raw['execution']['collection']['repetition']
                        write_new(output / f'raw-r{repetition}.json', raw)
                else:
                    write_new(output, raws[0])
                summary = export_summary(raws)
                summary['missing'] = len(selected) * (len(plan['samples']) // plan['repetitions']) - summary['exported']
                strict_failed = args.strict and bool(summary['blocked'] or summary['missing'])
        print(json.dumps({'state': 'SAVED', 'quality_assessed': False, 'inference_started': False,
                          'summary': summary, 'strict_failed': strict_failed}))
        return 3 if strict_failed else 0
    except Exception as exc:
        # Imported validators, malformed input or HTTP errors can carry secrets.
        if isinstance(exc, AdapterError):
            reason = str(exc)
        elif isinstance(exc, FileExistsError):
            reason = 'Output already exists; choose a new destination'
        elif isinstance(exc, FileNotFoundError):
            reason = 'Required input file not found; check suite, plan and receipt paths'
        elif isinstance(exc, json.JSONDecodeError):
            reason = f'Invalid JSON at line {exc.lineno}, column {exc.colno}'
        elif isinstance(exc, KeyError):
            reason = 'Missing required field or environment setting; check the input contract'
        else:
            reason = type(exc).__name__ + '; imported validation or input failed; consult preserved sidecars'
        print('JUP-071 collector: ' + reason, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
