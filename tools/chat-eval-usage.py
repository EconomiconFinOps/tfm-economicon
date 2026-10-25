"""Extract only bounded accounting fields from the verified processor's logs."""
from datetime import datetime
import hashlib
import json
import re
import subprocess


def reports(raw, operation_id):
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError('Accounting log window too large')
    output, seen, duplicates = [], set(), 0
    for line in raw.decode('utf-8', errors='strict').splitlines():
        if len(line) > 65536:
            raise ValueError('Unbounded accounting log line')
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        wrapped = event.get('event')
        if isinstance(wrapped, str) and wrapped.startswith('chat_review_usage '):
            try:
                event = json.loads(wrapped[len('chat_review_usage '):])
            except ValueError:
                raise ValueError('Malformed accounting event') from None
        if not isinstance(event, dict) or event.get('event') != 'chat_review_usage':
            continue
        if event.get('operation_id') != operation_id:
            continue
        safe = {k: event.get(k) for k in ('event', 'operation_id', 'attempt_id', 'complete',
                                         'attempted_legs', 'reported_legs')}
        observed = event.get('observed')
        requests = event.get('requests')
        if not isinstance(observed, dict) or not isinstance(requests, list) or len(requests) > 2:
            raise ValueError('Invalid accounting structure')
        safe['observed'] = {k: observed[k] for k in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost_usd')
                            if k in observed}
        safe['requests'] = []
        for item in requests:
            if (not isinstance(item, dict) or item.get('phase') not in ('draft', 'final')
                    or not re.fullmatch('[a-f0-9]{64}', item.get('request_sha256', ''))):
                raise ValueError('Missing provider request provenance')
            safe['requests'].append({k: item[k] for k in
                                     ('phase', 'request_sha256', 'output_token_limit', 'input_tokens') if k in item})
        serialized = json.dumps(safe, sort_keys=True)
        if serialized in seen:
            duplicates += 1
            continue
        seen.add(serialized); output.append(safe)
    return {'operation_id': operation_id, 'reports': output, 'identical_duplicates': duplicates,
            'reports_sha256': hashlib.sha256(json.dumps(output, sort_keys=True).encode()).hexdigest()}


def read(container, operation_id, since):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,200}', container):
        raise ValueError('Invalid container identifier')
    timestamp = datetime.fromisoformat(since.replace('Z', '+00:00'))
    if timestamp.tzinfo is None:
        raise ValueError('Accounting window requires timezone')
    result = subprocess.run(['docker', 'logs', '--since', timestamp.isoformat(), container],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Cannot read processor accounting logs')
    # Docker separates container stdout/stderr. Parse both without echoing either.
    return reports(result.stdout + b'\n' + result.stderr, operation_id)
