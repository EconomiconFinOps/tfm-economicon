"""Read an existing synthetic operation; never start, resume or retry inference.

Authentication is supplied through environment variables, never receipt fields.
This collector is one component of the repeated runner, not proof of a campaign.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib import request, error, parse


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value):
        raise ValueError('Invalid operation/conversation identifier')
    return value


def collect(get, sample, conversation_id, operation_id):
    """Keep failures and raw public resources; verify a stable terminal snapshot."""
    conversation = '/assistant/conversations/' + identifier(conversation_id)
    operation = conversation + '/generations/' + identifier(operation_id)
    resources, errors = {}, {}
    def fetch(key, path):
        try:
            resources[key] = get(path)
        except Exception as exc:
            # Exception text may contain credentials, response bodies or URLs.
            errors[key] = {'class': type(exc).__name__,
                           'http_status': exc.code if isinstance(exc, error.HTTPError) else None}
            if isinstance(exc, error.HTTPError):
                exc.close()
        return resources.get(key)
    before = fetch('operation', operation)
    if not isinstance(before, dict) or before.get('operation_id') != operation_id:
        raise ValueError('Operation identity not verified')
    if before.get('state') not in ('completed', 'failed', 'cancelled'):
        raise ValueError('Operation is not terminal; preserve its handle and observe it later')
    fetch('context', operation + '/context')
    fetch('evidence', operation + '/evidence')
    fetch('history', conversation)
    if before['state'] == 'completed':
        fetch('result', operation + '/result')
    after = fetch('operation_after', operation)
    stable = after == before
    history = resources.get('history') or {}
    messages = history.get('messages', [])
    users = [m for m in messages if m.get('role') == 'user']
    input_matches = (len(users) == 1 and users[0].get('content') == sample['content']
                     and users[0].get('id') == before.get('question_id'))
    result = resources.get('result') or {}
    response = (result.get('metadata') or {}).get('response') or {}
    assistants = [m for m in messages if m.get('role') == 'assistant']
    matches = [m for m in assistants if m.get('id') == result.get('id')]
    parity = (len(assistants) == 1 and len(matches) == 1
              and all(matches[0].get(k) == result.get(k) for k in ('content', 'metadata'))
              and response.get('answer') == result.get('content')) if before['state'] == 'completed' else None
    authorized = (resources.get('evidence') or {}).get('items', [])
    cited_ids = {item.get('id') for item in response.get('evidence', [])}
    cited = [item for item in authorized if item.get('id') in cited_ids]
    citation_ids_known = cited_ids <= {item.get('id') for item in authorized}
    verification = {'input_matches_bank': input_matches, 'stable_snapshot': stable,
                    'public_history_parity': parity, 'citation_ids_known': citation_ids_known}
    verified = (not errors and stable and input_matches and citation_ids_known
                and (parity is True or before['state'] != 'completed'))
    return {'id': sample['case_id'], 'repetition': sample['repetition'],
            'state': before['state'], 'conversation_id': conversation_id,
            'operation': before, 'result': result, 'history': history,
            'cited_chunks': cited, 'authorized_evidence': authorized,
            'verification': verification,
            'collection_state': 'VERIFIED_PUBLIC_SNAPSHOT' if verified else 'INCOMPLETE',
            'collection_errors': errors, 'resources': resources,
            'resources_sha256': digest(resources),
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'limitations': ['Public snapshot does not prove runtime commit, provider routing, '
                            'full request payloads, per-attempt usage or live cumulative spend.']}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def reader(base_url, token, tenant):
    parsed = parse.urlsplit(base_url)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
        raise ValueError('Use an API origin without credentials, path, query or fragment')
    if parsed.scheme == 'http' and parsed.hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('Plain HTTP is restricted to loopback')
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    def get(path):
        req = request.Request(base_url.rstrip('/') + path,
                              headers={'Authorization': 'Bearer ' + token, 'X-Tenant-Id': tenant})
        with opener.open(req, timeout=20) as response:
            if response.headers.get_content_type() != 'application/json':
                raise ValueError('Expected JSON resource')
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('Resource size limit')
            return json.loads(raw)
    return get


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'sample', 'conversation', 'operation', 'base-url', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    sample = next(s for s in plan['samples'] if s['sample_id'] == args.sample)
    token, tenant = os.environ['CHAT_EVAL_TOKEN'], os.environ['CHAT_EVAL_TENANT']
    destination = Path(args.output).resolve()
    root = Path(__file__).resolve().parents[1]
    if destination == root or root in destination.parents or destination.exists():
        raise ValueError('Use a new receipt outside the repository')
    row = collect(reader(args.base_url, token, tenant), sample, args.conversation, args.operation)
    receipt = {'version': 1, 'bank_sha256': plan['bank_sha256'],
               'repetitions': plan['repetitions'], 'plan_sha256': digest(plan), 'results': [row]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents replacing a failed attempt with a later success.
    with destination.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps({'state': row['collection_state'], 'receipt': str(destination)}))


if __name__ == '__main__':
    main()
