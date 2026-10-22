import copy
import json
from pathlib import Path
from unittest.mock import Mock, patch
import unittest


ID = 'dd0a7871-d3c3-441f-9c40-d01aee724131'
OP = '18161cdb-9907-4f56-b80c-3ef1fc7cb131'


class ChecksTests(unittest.TestCase):
    def test_sdk_readiness_requires_native_runtime_healthy_targets_and_owned_identity(self):
        from tools.aws_demo import checks
        from tools.aws_demo.test_control import config as valid_config
        config = valid_config()
        for failure in (None, 'mock-runtime', 'unhealthy-target', 'foreign-identity', 'auth-challenge'):
            with self.subTest(failure=failure):
                ecs, lb, cf, cognito = Mock(), Mock(), Mock(), Mock()
                services = [{'serviceName': name, 'taskDefinition': name, 'desiredCount': 2, 'runningCount': 2,
                             'pendingCount': 0, 'deployments': [{'rolloutState': 'COMPLETED'}]}
                            for name in ['backend', 'processor', 'azure-cost-api']]
                ecs.describe_services.return_value = {'services': services}
                def definition(**kwargs):
                    env = {'EMBEDDING_PROVIDER': 'mock' if failure == 'mock-runtime' else 'bedrock',
                           'EMBEDDING_DIMENSION': '1024', 'EMBEDDING_MODEL': 'amazon.titan-embed-text-v2:0',
                           'BEDROCK_REGION': 'eu-south-2', 'LLM_PROVIDER': 'bedrock', 'BEDROCK_CHAT_MODEL_ID': 'eu.amazon.nova-micro-v1:0'}
                    return {'taskDefinition': {'containerDefinitions': [{'environment': [{'name': k, 'value': v} for k, v in env.items()]}]}}
                ecs.describe_task_definition.side_effect = definition
                lb.describe_target_health.return_value = {'TargetHealthDescriptions': [{'TargetHealth': {
                    'State': 'unhealthy' if failure == 'unhealthy-target' else 'healthy'}}] * 2}
                cognito.admin_get_user.return_value = {'UserStatus': 'CONFIRMED', 'UserAttributes': [{'Name': k, 'Value': v} for k, v in {
                    'sub': ID, 'email': 'aws-defensa+ensayo1@example.com', 'custom:rehearsal':
                        'foreign' if failure == 'foreign-identity' else 'JUP-131:ensayo1:' + 'a' * 40}.items()]}
                cognito.admin_initiate_auth.return_value = {'AuthenticationResult': {'AccessToken': 'synthetic-access-token'}}
                if failure == 'auth-challenge':
                    cognito.admin_initiate_auth.return_value['ChallengeName'] = 'SMS_MFA'
                clients = {'ecs': ecs, 'elbv2': lb, 'cloudfront': cf, 'cognito-idp': cognito, 'secretsmanager': Mock()}
                outputs = {'ecs_cluster_name': 'economicon-ensayo1', 'readiness': {'api_target_group_arn':
                    'arn:aws:elasticloadbalancing:eu-south-2:123456789012:targetgroup/economicon-ensayo1-api/' + 'a' * 16},
                    'cloudfront_distribution_id': 'ESYNTHETIC131', 'bedrock_chat': {'profile_id': 'eu.amazon.nova-micro-v1:0'},
                    'rehearsal_secret_arn': 'arn:aws:secretsmanager:eu-south-2:123456789012:secret:economicon-ensayo1/rehearsal/credentials-ABC123',
                    'cognito': {'user_pool_id': 'eu-south-2_Synthetic131', 'client_id': 'syntheticclient131'}}
                bundle = {'_cycle_id': 'ensayo1', '_source_sha': 'a' * 40,
                          'smoke_user': {'email': 'aws-defensa+ensayo1@example.com', 'password': 'synthetic-private-password'}}
                events = []
                with patch.object(checks, 'sdk_client', side_effect=lambda name, region: clients[name]), \
                     patch.object(checks, '_read_secret', return_value=bundle):
                    if failure is None:
                        api, identity = checks.prepare_live(config, outputs, lambda name, proof: events.append((name, proof)))
                        self.assertEqual(identity['id'], ID)
                        self.assertEqual(cognito.admin_initiate_auth.call_args.kwargs['AuthFlow'], 'ADMIN_USER_PASSWORD_AUTH')
                        self.assertNotIn('synthetic-private-password', json.dumps(events))
                    else:
                        with self.assertRaises(checks.CheckError):
                            checks.prepare_live(config, outputs, lambda *args: None)
                        if failure != 'auth-challenge':
                            cognito.admin_initiate_auth.assert_not_called()

    def test_http_stream_stops_observing_after_started_and_never_follows_redirects(self):
        from tools.aws_demo import checks
        connection = Mock()
        response = connection.getresponse.return_value
        response.status = 200
        response.getheader.return_value = 'text/event-stream'
        response.read1.side_effect = [b'event: started\ndata: {"operation":{"operation_id":"' + OP.encode() + b'"}}\n\n',
                                     AssertionError('Should not read the complete model stream')]
        with patch.object(checks.http.client, 'HTTPSConnection', return_value=connection):
            api = checks.HTTP('economicon.danteinferno.es', 'synthetic-access-token')
            reply = api.request('POST', '/api/assistant/test', {}, stream=True)
            self.assertEqual(checks._operation(reply), OP)
        connection.close.assert_called_once()
        self.assertEqual(response.read1.call_count, 1)
        connection.reset_mock()
        response.status = 302
        response.getheader.return_value = 'text/html'
        response.read1.side_effect = [b'Location: https://foreign.invalid', b'']
        with patch.object(checks.http.client, 'HTTPSConnection', return_value=connection) as constructor:
            self.assertEqual(api.request('GET', '/api/me').status, 302)
        constructor.assert_called_once()

    def test_local_entrypoint_never_reads_credentials_or_constructs_sdk(self):
        from tools.aws_demo import checks
        with patch.dict('os.environ', {}, clear=True), patch.object(checks, 'sdk_client', side_effect=AssertionError('AWS forbidden')) as sdk:
            self.assertEqual(checks.main(), 1)
        sdk.assert_not_called()

    def test_unsafe_signed_upload_urls_are_rejected(self):
        from tools.aws_demo.checks import validate_upload_url, CheckError
        valid = 'https://s3.eu-south-2.amazonaws.com/owned-bucket/staging/file?X-Amz-Signature=synthetic'
        self.assertEqual(validate_upload_url(valid, 'owned-bucket'), valid)
        for url in [valid.replace('s3.eu-south-2.amazonaws.com', 'credential-sink.invalid'),
                    valid.replace('/owned-bucket/', '/foreign/'), valid.replace('/staging/', '/confirmed/'),
                    valid.replace('https:', 'http:'), valid.replace('https://', 'https://user@')]:
            with self.assertRaises(CheckError):
                validate_upload_url(url, 'owned-bucket')

    def test_complete_workflow_requires_every_functional_stage(self):
        from tools.aws_demo import checks
        fixture = json.loads((checks.ROOT / 'apps/processor/app/resources/rehearsal-v1.json').read_text(encoding='utf-8'))
        for failure in [None, 'health', 'identity', 'tenants', 'isolation', 'billing', 'ingestion', 'generation', 'citation', 'usage', 'schema']:
            with self.subTest(failure=failure):
                api = FakeAPI(checks, failure)
                events = []
                callback = lambda name, value: events.append((name, value))
                if failure is None:
                    checks.run_checks(api, fixture, {'id': ID, 'email': 'aws-defensa+ensayo1@example.com'}, 'owned-bucket', callback, pause=lambda _: None)
                    self.assertEqual([name for name, _ in events], ['frontend', 'health', 'identity', 'tenant-isolation', 'billing', 'ingestion', 'assistant'])
                    self.assertEqual(api.uploads, 1)
                    self.assertNotIn('synthetic-access-token', json.dumps(events))
                    self.assertTrue(any(call[1].endswith('/generations') for call in api.calls))
                else:
                    with self.assertRaises(checks.CheckError):
                        checks.run_checks(api, fixture, {'id': ID, 'email': 'aws-defensa+ensayo1@example.com'}, 'owned-bucket', callback, pause=lambda _: None)
                    self.assertNotIn('assistant', [name for name, _ in events])


class FakeAPI:
    def __init__(self, checks, failure):
        self.checks, self.failure, self.uploads, self.calls = checks, failure, 0, []

    def upload(self, url, headers, content, bucket):
        self.checks.validate_upload_url(url, bucket)
        self.uploads += 1
        self.content = content.decode('utf-8')

    def request(self, method, path, payload=None, *, tenant='tenant-core', authenticated=True, stream=False):
        self.calls.append((method, path, copy.deepcopy(payload)))
        status, content_type = 200, 'application/json'
        if path == '/':
            return self.checks.Reply(200, b'<!doctype html><div id="root"></div>', 'text/html')
        if path == '/api/health':
            body = {'status': 'degraded' if self.failure == 'health' else 'ok',
                    'services': dict.fromkeys(['database', 'rabbitmq', 'vector_store'], 'ok')}
        elif path == '/api/me':
            body = {'id': 'foreign' if self.failure == 'identity' else ID, 'email': 'aws-defensa+ensayo1@example.com'}
            if not authenticated:
                status = 401
        elif path == '/api/tenants':
            body = {'items': [{'id': 'tenant-core'}] + ([{'id': 'tenant-growth'}] if self.failure == 'tenants' else [])}
        elif path.startswith('/api/billing/summary'):
            status = 403 if tenant == 'tenant-growth' and self.failure != 'isolation' else 200
            body = {'totals': [{'currency': 'EUR', 'cost': '33.00' if self.failure == 'billing' else '12.50', 'record_count': 1}]}
        elif path == '/api/jobs/uploads':
            status, body = 201, {'upload_id': ID, 'upload_url': 'https://s3.eu-south-2.amazonaws.com/owned-bucket/staging/file?X-Amz-Signature=synthetic',
                                 'headers': {'Content-Type': 'application/octet-stream'}}
        elif path.endswith('/confirm'):
            status, body = 202, {'job_id': ID}
        elif path == '/api/jobs/uploads/' + ID:
            body = {'job_id': ID, 'job_status': 'failed' if self.failure == 'ingestion' else 'completed'}
        elif path == '/api/jobs/documents/' + ID:
            body = {'document_id': ID, 'tenant_id': 'tenant-core', 'text': self.content}
        elif path == '/api/assistant/capabilities':
            body = {'chat_enabled': True}
        elif path == '/api/assistant/conversations':
            status, body = 201, {'id': ID}
        elif path.endswith('/generations'):
            return self.checks.Reply(200, ('event: started\ndata: ' + json.dumps({'operation': {'operation_id': OP}}) + '\n\n').encode(), 'text/event-stream')
        elif path.endswith('/result'):
            citation = {'id': 'doc:0', 'kind': 'corpus', 'title': 'Ensayo', 'source': 'synthetic'}
            response = {'schema_version': '1.0', 'status': 'ok', 'answer': 'Medir CPU, memoria y latencia.',
                        'scope': {'cloud': 'azure', 'data_environment': 'simulated', 'subscription_ids': [], 'period': None},
                        'evidence': [citation], 'metrics': [], 'recommendations': [], 'assumptions': [], 'limitations': [], 'next_actions': []}
            if self.failure == 'schema':
                response['unapproved'] = True
            body = {'id': ID, 'metadata': {'response': response, 'source_citations': [] if self.failure == 'citation' else [
                {'evidence_id': 'doc:0', 'document_id': ID, 'content': 'synthetic extracted text'}],
                'generation': {'state': 'completed', 'usage': None if self.failure == 'usage' else {
                    'prompt_tokens': 20, 'completion_tokens': 10, 'total_tokens': 30}}}}
        elif path.endswith('/generations/' + OP):
            body = {'operation_id': OP, 'state': 'failed' if self.failure == 'generation' else 'completed'}
        else:
            raise AssertionError('Unexpected check request: ' + method + ' ' + path)
        return self.checks.Reply(status, json.dumps(body).encode(), content_type)
