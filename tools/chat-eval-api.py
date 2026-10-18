"""Current chat API transport for the evaluation runner.

Never call generate directly in a campaign: Ledger.dispatch must first commit
its reservation and dispatch intent. This module does not renew credentials.
"""
import importlib.util
import json
from pathlib import Path
from urllib import request

spec = importlib.util.spec_from_file_location('collect', Path(__file__).with_name('chat-eval-collect.py'))
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


class API:
    def __init__(self, origin, token, tenant):
        self.get = collect.reader(origin, token, tenant)  # validates origin
        self.origin = origin.rstrip('/')
        self.headers = {'Authorization': 'Bearer ' + token, 'X-Tenant-Id': tenant,
                        'Content-Type': 'application/json'}
        self.opener = request.build_opener(request.ProxyHandler({}), collect.NoRedirect())

    def post(self, path, payload):
        req = request.Request(self.origin + path, data=json.dumps(payload, ensure_ascii=False).encode(),
                              headers=self.headers, method='POST')
        return self.opener.open(req, timeout=20)

    def create_conversation(self, title):
        with self.post('/assistant/conversations', {'title': title}) as response:
            if response.status != 201 or response.headers.get_content_type() != 'application/json':
                raise ValueError('Unexpected conversation response')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError('Conversation response size limit')
            return collect.identifier(json.loads(raw)['id'])

    def generate(self, conversation_id, request_id, content, screen_context):
        path = '/assistant/conversations/' + collect.identifier(conversation_id) + '/generations'
        payload = {'request_id': request_id, 'content': content, 'screen_context': screen_context}
        with self.post(path, payload) as response:
            mime = response.headers.get_content_type()
            if mime == 'application/json':
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise ValueError('Operation response size limit')
                operation = json.loads(raw)
                if operation.get('request_id') != request_id:
                    raise ValueError('Unexpected request identity')
                return collect.identifier(operation['operation_id'])
            if mime != 'text/event-stream':
                raise ValueError('Unexpected generation response')
            # Initial started frame contains the durable operation handle. Close
            # only the observer connection afterwards; do not stop the operation.
            data, size = [], 0
            while size <= 262144:
                line = response.readline(65537)
                size += len(line)
                if len(line) > 65536 or not line:
                    raise ValueError('Missing bounded operation frame; reconcile by request_id')
                text = line.decode('utf-8').rstrip('\r\n')
                if text.startswith('data:'):
                    data.append(text[5:].lstrip(' '))
                elif not text and data:
                    event = json.loads('\n'.join(data)); data = []
                    operation = event.get('operation', {})
                    if operation.get('request_id') == request_id:
                        identifier = collect.identifier(operation['operation_id'])
                        if event.get('operation_id') != identifier:
                            raise ValueError('Inconsistent operation identity')
                        return identifier
            raise ValueError('Operation frame limit; reconcile by request_id')

    def recover_handle(self, conversation_id, request_id):
        items = self.get('/assistant/requests')['items']
        matches = [row['operation']['operation_id'] for row in items
                   if row.get('conversation_id') == conversation_id
                   and row.get('operation', {}).get('request_id') == request_id]
        if len(matches) > 1:
            raise ValueError('Ambiguous operation identity')
        return collect.identifier(matches[0]) if matches else None
