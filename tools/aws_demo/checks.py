"""Fail-closed live rehearsal acceptance. Import and ordinary local execution are offline."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import sys
import time
from urllib.parse import urlsplit, urlencode
from uuid import UUID, uuid4

try:
    from .bootstrap import ROOT, WORK, load_control_context, sdk_client, _read_secret
except ImportError:
    from bootstrap import ROOT, WORK, load_control_context, sdk_client, _read_secret


class CheckError(RuntimeError):
    pass


def expect(condition, stage):
    if not condition:
        raise CheckError(stage)


def identifier(value):
    try:
        expect(isinstance(value, str) and str(UUID(value)) == value, 'identifier')
        return value
    except Exception:
        raise CheckError('identifier') from None


@dataclass(frozen=True)
class Reply:
    status: int
    body: bytes
    content_type: str


def decoded(reply, status=200, stage='api'):
    try:
        expect(reply.status == status and reply.content_type.split(';')[0] == 'application/json', stage)
        value = json.loads(reply.body)
        expect(isinstance(value, dict), stage)
        return value
    except Exception:
        raise CheckError(stage) from None


def validate_upload_url(url, bucket):
    try:
        parsed = urlsplit(url)
        expect(parsed.scheme == 'https' and not parsed.username and not parsed.password
               and parsed.port in {None, 443} and not parsed.fragment
               and parsed.hostname == 's3.eu-west-1.amazonaws.com'
               and parsed.path.startswith('/' + bucket + '/staging/') and bool(parsed.query), 'upload-url')
        return url
    except Exception:
        raise CheckError('upload-url') from None


class HTTP:
    def __init__(self, domain, token):
        expect(domain == 'economicon.danteinferno.es' and isinstance(token, str) and 1 <= len(token) <= 16384, 'api-origin')
        self.domain, self.token = domain, token

    @staticmethod
    def exchange(host, method, path, body, headers, *, stream=False):
        connection = http.client.HTTPSConnection(host, 443, timeout=15, context=ssl.create_default_context())
        try:
            deadline = time.monotonic() + 90
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            raw = bytearray()
            while True:
                expect(time.monotonic() < deadline and len(raw) <= 2097152, 'http-limit')
                chunk = response.read1(min(65536, 2097153 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
                # Closing an observation stream never cancels its durable operation.
                if stream and b'event: started\n' in raw and b'\n\n' in raw[raw.find(b'event: started\n'):]:
                    break
            expect(len(raw) <= 2097152, 'http-limit')
            return Reply(response.status, bytes(raw), response.getheader('Content-Type', ''))
        except Exception:
            raise CheckError('http') from None
        finally:
            connection.close()

    def request(self, method, path, payload=None, *, tenant='tenant-core', authenticated=True, stream=False):
        expect(path == '/' or path.startswith('/api/') and not path.startswith('//'), 'api-path')
        headers = {'Content-Type': 'application/json', 'X-Tenant-Id': tenant}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + self.token
        body = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        return self.exchange(self.domain, method, path, body, headers, stream=stream)

    def upload(self, url, headers, content, bucket):
        validate_upload_url(url, bucket)
        expect(headers == {'Content-Type': 'application/octet-stream'}, 'upload-headers')
        parsed = urlsplit(url)
        reply = self.exchange(parsed.hostname, 'PUT', parsed.path + '?' + parsed.query, content, headers)
        expect(reply.status == 200, 'upload')


def _operation(reply):
    if reply.content_type.split(';')[0] == 'application/json':
        return identifier(decoded(reply)['operation_id'])
    expect(reply.status == 200 and reply.content_type.split(';')[0] == 'text/event-stream', 'generation-open')
    try:
        for frame in reply.body.decode('utf-8').split('\n\n'):
            lines = frame.splitlines()
            if 'event: started' in lines:
                data = '\n'.join(line[6:] for line in lines if line.startswith('data: '))
                return identifier(json.loads(data)['operation']['operation_id'])
    except Exception:
        pass
    raise CheckError('generation-open')


def validate_result(result, job, fixture):
    try:
        from jsonschema import Draft202012Validator
        metadata = result['metadata']
        response = metadata['response']
        schema = json.loads((ROOT / 'apps/backend/app/schemas/finops_response_v1.json').read_text(encoding='utf-8'))
        Draft202012Validator(schema).validate(response)
        expect(response['status'] == 'ok', 'assistant-status')
        citations = metadata['source_citations']
        expect(isinstance(citations, list) and citations, 'assistant-citations')
        allowed = {fixture['tenants'][0]['document_id'], job}
        expect(all(c['document_id'] in allowed for c in citations), 'assistant-isolation')
        selected = {item['id'] for item in response['evidence'] if item['kind'] == 'corpus'}
        expect(any(c['document_id'] == job and c['evidence_id'] in selected and c.get('content') for c in citations), 'assistant-ingestion-citation')
        expect('COSTE_GROWTH_PRIVADO' not in json.dumps(result), 'assistant-isolation')
        generation = metadata['generation']
        usage = generation['usage']
        expect(generation['state'] == 'completed' and isinstance(usage, dict), 'assistant-usage')
        counts = {key: usage[key] for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
        expect(all(type(v) is int and v > 0 for v in counts.values())
               and counts['prompt_tokens'] + counts['completion_tokens'] == counts['total_tokens'], 'assistant-usage')
        return {'citation_count': len(citations), 'usage': counts}
    except Exception:
        raise CheckError('assistant-result') from None


def run_checks(api, fixture, identity, bucket, record, *, pause=time.sleep):
    root = api.request('GET', '/', authenticated=False)
    expect(root.status == 200 and root.content_type.split(';')[0] == 'text/html'
           and (b'<script' in root.body or b'id="root"' in root.body), 'frontend')
    record('frontend', {'status': 'PASS'})
    for attempt in range(30):
        health = decoded(api.request('GET', '/api/health', authenticated=False), stage='health')
        if health.get('status') == 'ok' and health.get('services') == dict.fromkeys(['database', 'rabbitmq', 'vector_store'], 'ok'):
            break
        pause(2)
    else:
        raise CheckError('health')
    record('health', {'status': 'PASS'})
    expect(api.request('GET', '/api/me', authenticated=False).status == 401, 'anonymous-access')
    user = decoded(api.request('GET', '/api/me'), stage='identity')
    expect(user.get('id') == identity['id'] and user.get('email') == identity['email'], 'identity')
    tenants = decoded(api.request('GET', '/api/tenants'), stage='tenants')
    expect([tenant['id'] for tenant in tenants.get('items', [])] == ['tenant-core'], 'tenants')
    record('identity', {'status': 'PASS', 'binding': 'cognito-sub'})
    path = '/api/billing/summary?' + urlencode(dict(fixture['period'], group_by='service'))
    expect(api.request('GET', path, tenant='tenant-growth').status == 403, 'tenant-isolation')
    record('tenant-isolation', {'status': 'PASS', 'forbidden_status': 403})
    billing = decoded(api.request('GET', path), stage='billing')
    expect(billing.get('totals') == [{'currency': 'EUR', 'cost': fixture['tenants'][0]['cost_eur'], 'record_count': 1}], 'billing')
    record('billing', {'status': 'PASS', 'expected_eur': fixture['tenants'][0]['cost_eur'], 'synthetic': True})
    marker = 'ENSAYO_' + uuid4().hex
    content = ('# Ensayo ' + marker + '\n\n' + fixture['tenants'][0]['text']).encode('utf-8')
    upload = decoded(api.request('POST', '/api/jobs/uploads', {'filename': 'ensayo-' + marker + '.md',
        'file_size': len(content), 'content_hash': hashlib.sha256(content).hexdigest()}), 201, 'upload-admission')
    upload_id = identifier(upload['upload_id'])
    api.upload(upload['upload_url'], upload['headers'], content, bucket)
    confirmed = decoded(api.request('POST', '/api/jobs/uploads/' + upload_id + '/confirm'), 202, 'upload-confirmation')
    job = identifier(confirmed['job_id'])
    for attempt in range(60):
        status = decoded(api.request('GET', '/api/jobs/uploads/' + upload_id), stage='ingestion')
        expect(status.get('job_id') == job and status.get('job_status') not in {'failed', 'cancelled'}, 'ingestion')
        if status.get('job_status') == 'completed':
            break
        pause(3)
    else:
        raise CheckError('ingestion-timeout')
    document = decoded(api.request('GET', '/api/jobs/documents/' + job), stage='extraction')
    expect(document.get('tenant_id') == 'tenant-core' and document.get('document_id') == job
           and marker in document.get('text', ''), 'extraction')
    record('ingestion', {'status': 'PASS', 'job_id': job, 'content_sha256': hashlib.sha256(content).hexdigest()})
    expect(decoded(api.request('GET', '/api/assistant/capabilities')).get('chat_enabled') is True, 'chat-capability')
    conversation = decoded(api.request('POST', '/api/assistant/conversations', {'title': 'Ensayo AWS'}), 201, 'conversation')
    conversation_id = identifier(conversation['id'])
    base = '/api/assistant/conversations/' + conversation_id + '/generations'
    screen = {'schema_version': '2', 'screen_version': 'aws-acceptance-v1', 'route': '/assistant', 'tab_id': str(uuid4()),
              'source': 'no-adapter', 'identity': {'tenant_id': 'tenant-core', 'user_id': identity['id']},
              'captured_at': datetime.now(timezone.utc).isoformat(), 'selection': {}, 'datasets': []}
    question = 'Según el documento de ensayo ' + marker + ', ¿qué mediciones hay que revisar antes de reducir una instancia? Consulta ese documento y cita la fuente.'
    operation = _operation(api.request('POST', base, {'request_id': str(uuid4()), 'content': question, 'screen_context': screen}, stream=True))
    for attempt in range(90):
        state = decoded(api.request('GET', base + '/' + operation), stage='generation')
        expect(state.get('operation_id') == operation and state.get('state') not in {'failed', 'cancelled', 'paused'}, 'generation')
        if state.get('state') == 'completed':
            break
        pause(2)
    else:
        raise CheckError('generation-timeout')
    result = decoded(api.request('GET', base + '/' + operation + '/result'), stage='generation-result')
    receipt = validate_result(result, job, fixture)
    record('assistant', dict(receipt, status='PASS', operation_id=operation, configured_provider='bedrock'))


def prepare_live(config, outputs, record):
    """SDK readiness and configuration receipts precede application acceptance."""
    cluster = 'economicon-' + config['cycle_id']
    expect(outputs['ecs_cluster_name'] == cluster, 'cluster')
    ecs = sdk_client('ecs', 'eu-west-1')
    names = ['backend', 'processor', 'azure-cost-api']
    ecs.get_waiter('services_stable').wait(cluster=cluster, services=names, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
    response = ecs.describe_services(cluster=cluster, services=names)
    expect(not response.get('failures') and len(response.get('services', [])) == 3
           and {s['serviceName'] for s in response['services']} == set(names), 'ecs')
    for service in response['services']:
        expect(service['serviceName'] in names and service['desiredCount'] == 2 and service['runningCount'] == 2
               and service['pendingCount'] == 0 and len(service['deployments']) == 1
               and service['deployments'][0].get('rolloutState') == 'COMPLETED', 'ecs')
        if service['serviceName'] in {'backend', 'processor'}:
            definition = ecs.describe_task_definition(taskDefinition=service['taskDefinition'])['taskDefinition']
            containers = definition['containerDefinitions']
            expect(len(containers) == 1, 'ecs-runtime')
            env = {item['name']: item['value'] for item in containers[0]['environment']}
            expect(env.get('EMBEDDING_PROVIDER') == 'bedrock' and env.get('EMBEDDING_DIMENSION') == '1024'
                   and env.get('EMBEDDING_MODEL') == 'amazon.titan-embed-text-v2:0'
                   and env.get('BEDROCK_REGION') == 'eu-west-1', 'ecs-runtime')
            if service['serviceName'] == 'processor':
                expect(env.get('LLM_PROVIDER') == 'bedrock' and env.get('BEDROCK_CHAT_MODEL_ID') == outputs['bedrock_chat']['profile_id']
                       and env.get('BEDROCK_CHAT_MODEL_ID') in {
                    'eu.amazon.nova-micro-v1:0', 'eu.amazon.nova-lite-v1:0'}, 'ecs-runtime')
    readiness = outputs['readiness']
    expect(re.fullmatch(f"arn:aws:elasticloadbalancing:eu-west-1:{config['account_id']}:targetgroup/{cluster}-api/[a-f0-9]{{16}}",
                        readiness['api_target_group_arn']), 'alb-reference')
    lb = sdk_client('elbv2', 'eu-west-1')
    lb.get_waiter('target_in_service').wait(TargetGroupArn=readiness['api_target_group_arn'],
                                          WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
    targets = lb.describe_target_health(TargetGroupArn=readiness['api_target_group_arn'])['TargetHealthDescriptions']
    expect(len(targets) == 2 and all(t['TargetHealth']['State'] == 'healthy' for t in targets), 'alb')
    cf = sdk_client('cloudfront', 'us-east-1')
    cf.get_waiter('distribution_deployed').wait(Id=outputs['cloudfront_distribution_id'], WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
    record('infrastructure', {'status': 'PASS', 'services': 3, 'healthy_targets': 2, 'desired_tasks': 6})
    prefix = f"arn:aws:secretsmanager:eu-west-1:{config['account_id']}:secret:{cluster}/rehearsal/credentials-"
    arn = outputs['rehearsal_secret_arn']
    expect(re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9]{6}', arn), 'credentials-reference')
    bundle = _read_secret(sdk_client('secretsmanager', 'eu-west-1'), arn, config)
    expect(bundle['_cycle_id'] == config['cycle_id'] and bundle['_source_sha'] == config['source_sha'], 'credentials-ownership')
    user = bundle['smoke_user']
    expect(user['email'] == 'aws-defensa+' + config['cycle_id'] + '@example.com', 'credentials-ownership')
    pool = outputs['cognito']['user_pool_id']
    expect(re.fullmatch(r'eu-west-1_[A-Za-z0-9]+', pool), 'cognito-pool')
    cognito = sdk_client('cognito-idp', 'eu-west-1')
    response = cognito.admin_get_user(UserPoolId=pool, Username=user['email'])
    attributes = {a['Name']: a['Value'] for a in response['UserAttributes']}
    sub = identifier(attributes['sub'])
    expect(attributes.get('custom:rehearsal') == 'JUP-131:' + config['cycle_id'] + ':' + config['source_sha']
           and attributes.get('email') == user['email'] and response.get('UserStatus') == 'CONFIRMED', 'cognito-identity')
    login = cognito.admin_initiate_auth(UserPoolId=pool, ClientId=outputs['cognito']['client_id'],
        AuthFlow='ADMIN_USER_PASSWORD_AUTH', AuthParameters={'USERNAME': user['email'], 'PASSWORD': user['password']})
    expect(not login.get('ChallengeName'), 'cognito-login')
    token = login['AuthenticationResult']['AccessToken']
    return HTTP(config['frontend_domain'], token), {'id': sub, 'email': user['email']}


def main():
    report = None
    try:
        config, outputs = load_control_context()
        report = {'cycle_id': config['cycle_id'], 'source_sha': config['source_sha'], 'result': 'RUNNING', 'checks': []}
        def save():
            temporary = WORK / 'acceptance.tmp'
            temporary.write_text(json.dumps(report, sort_keys=True) + '\n')
            os.chmod(temporary, 0o600)
            temporary.replace(WORK / 'acceptance.json')
        def record(name, proof):
            report['checks'].append({'name': name, **proof})
            save()
        api, identity = prepare_live(config, outputs, record)
        expect(outputs['buckets']['documents'].startswith('economicon-' + config['cycle_id'] + '-documents-'), 'documents-bucket')
        fixture = json.loads((ROOT / 'apps/processor/app/resources/rehearsal-v1.json').read_text(encoding='utf-8'))
        run_checks(api, fixture, identity, outputs['buckets']['documents'], record)
        report.update(result='SUCCESS', completed_at=datetime.now(timezone.utc).isoformat())
        save()
        print(json.dumps({'phase': 'acceptance', 'result': 'SUCCESS', 'source_sha': config['source_sha']}))
        return 0
    except Exception as error:
        if report is not None:
            report.update(result='FAILED', failure_stage=str(error) if isinstance(error, CheckError) else 'dependency')
            save()
        print('Rehearsal acceptance failed; inspect the restricted acceptance report.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
