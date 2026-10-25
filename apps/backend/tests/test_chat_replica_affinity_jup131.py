"""Two real HTTP replicas behind rotating DNS; no AWS or model calls."""
import asyncio
import hashlib
import hmac
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import pytest

from app.db.chat_repository import ChatError
from app.services.chat_transport import PrivateChatTransport

KEY = b'jup131-synthetic-replica-affinity-key-only'


@pytest.fixture
def replicas(monkeypatch):
    calls = []
    order = ['127.0.0.1', '127.0.0.2']
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def exchange(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            nonce = self.headers['X-Chat-Nonce']
            signed = f'chat-v2\n{self.command}\n{self.path}\n{self.headers["X-Chat-Time"]}\n{nonce}\n{hashlib.sha256(raw).hexdigest()}'.encode()
            assert hmac.compare_digest(self.headers['X-Chat-Signature'], hmac.new(KEY, signed, hashlib.sha256).hexdigest())
            value = json.loads(raw) if raw else {}
            calls.append((self.server.boot, self.command, self.path, value))
            return value
        def reply(self, value, status=200, stream=False):
            raw = json.dumps(value).encode() + (b'\n' if stream else b'')
            nonce = self.headers['X-Chat-Nonce']
            signature = hmac.new(KEY, f'chat-v2-response\n{nonce}\n{status}\n{hashlib.sha256(raw).hexdigest()}'.encode(), hashlib.sha256).hexdigest()
            self.send_response(status)
            self.send_header('Content-Type', 'application/x-ndjson' if stream else 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('X-Chat-Nonce', nonce)
            self.send_header('X-Chat-Signature', '0'*64 if self.server.bad_signature else signature)
            self.end_headers(); self.wfile.write(raw)
        def do_GET(self):
            value = self.exchange()
            if self.path.endswith('/descriptor'):
                self.reply({'v': 2, 'boot_id': self.server.boot, 'prompt_version': 'synthetic', 'capacity': 5,
                    'summary_version': 'synthetic', 'manifest_sha256': 'a'*64, 'tokenizer_sha256': 'b'*64,
                    'response_schema_sha256': 'c'*64, 'context_budget': {}})
            else:
                self.reply({**self.server.job, 'state': 'running', 'settled': False})
        def do_POST(self):
            value = self.exchange()
            claim = value.get('claim', value)
            if claim.get('boot_id') != self.server.boot:
                self.reply({'code': 'claim_not_current'}, 404); return
            if self.path == '/internal/chat/v2/attempts':
                self.reply({'v': 2, 'type': 'error', 'category': 'synthetic-finish'}, stream=True)
            elif self.path.endswith('/tool-result'):
                self.reply({'v': 2, 'accepted': True, 'tool_call_id': value['tool_result']['tool_call_id']})
            elif self.path == '/internal/chat/v2/summaries':
                self.server.job = {k: value[k] for k in ('v', 'job_id', 'scope', 'boot_id', 'input_hash', 'summary_version')}
                self.reply({**self.server.job, 'state': 'running', 'settled': False})
            elif '/summaries/' in self.path:
                self.reply({**self.server.job, 'state': 'cancelled', 'settled': True})
            else:
                self.reply({'v': 2, 'accepted': True})
    first = ThreadingHTTPServer((order[0], 0), Handler)
    second = ThreadingHTTPServer((order[1], first.server_port), Handler)
    servers = [first, second]
    threads = []
    for server in servers:
        server.boot = str(uuid4()); server.bad_signature = False
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start(); threads.append(worker)
    real = socket.getaddrinfo
    def dns(host, port, *args, **kwargs):
        if host == 'processor.test':
            return [entry for ip in order for entry in real(ip, port, *args, **kwargs)]
        return real(host, port, *args, **kwargs)
    monkeypatch.setattr(socket, 'getaddrinfo', dns)
    try:
        yield f'http://processor.test:{first.server_port}', servers, calls, order
    finally:
        for server in servers: server.shutdown(); server.server_close()
        for worker in threads: worker.join(timeout=2)


def claim(boot):
    return {'boot_id': boot, 'attempt_id': str(uuid4()), 'deadline': time.time()+30}


def test_chat_attempt_tool_result_and_cancel_stay_on_authenticated_replica(replicas):
    base, servers, calls, order = replicas
    async def scenario():
        transport = PrivateChatTransport(base, KEY)
        a = await transport.descriptor()
        order.reverse()
        b = await transport.descriptor()
        assert a['boot_id'] != b['boot_id']
        operation = claim(a['boot_id'])
        records = [item async for item in transport.stream(operation)]
        assert records == [{'v': 2, 'type': 'error', 'category': 'synthetic-finish'}]
        await transport.tool_result(operation, {'tool_call_id': 'synthetic-tool'})
        await transport.cancel(operation)
        posts = [item for item in calls if item[1] == 'POST']
        assert len(posts) == 3 and all(item[0] == a['boot_id'] for item in posts)
        assert transport.host == 'processor.test'
    asyncio.run(scenario())


def test_cold_backend_summary_controls_find_original_boot_without_redispatch(replicas):
    base, servers, calls, order = replicas
    async def scenario():
        transport = PrivateChatTransport(base, KEY)
        descriptor = await transport.summary.descriptor()
        job = {'v': 2, 'job_id': str(uuid4()), 'scope': {'tenant_id': 't', 'user_id': 'u', 'conversation_id': 'c'},
               'boot_id': descriptor['boot_id'], 'input_hash': 'd'*64, 'summary_version': 'synthetic',
               'deadline': time.time()+30, 'payload': {}}
        order.reverse()
        assert (await transport.summary.submit(job))['state'] == 'running'
        cold = PrivateChatTransport(base, KEY)
        assert (await cold.summary.status(job))['state'] == 'running'
        assert (await cold.summary.cancel(job))['state'] == 'cancelled'
        posts = [item for item in calls if item[1] == 'POST']
        assert len(posts) == 2 and all(item[0] == descriptor['boot_id'] for item in posts)
        assert sum(item[2] == '/internal/chat/v2/summaries' for item in posts) == 1
    asyncio.run(scenario())


def test_concurrent_attempts_keep_independent_peer_bindings(replicas):
    base, servers, calls, order = replicas
    async def scenario():
        transport = PrivateChatTransport(base, KEY)
        a = await transport.descriptor()
        order.reverse()
        b = await transport.descriptor()
        async def consume(boot):
            return [record async for record in transport.stream(claim(boot))]
        results = await asyncio.gather(consume(a['boot_id']), consume(b['boot_id']))
        assert all(records == [{'v': 2, 'type': 'error', 'category': 'synthetic-finish'}] for records in results)
        posts = [item for item in calls if item[1] == 'POST']
        assert len(posts) == 2 and all(item[0] == item[3]['boot_id'] for item in posts)
    asyncio.run(scenario())


def test_restarted_peer_never_redispatches_attempt_to_another_replica(replicas):
    base, servers, calls, order = replicas
    async def scenario():
        transport = PrivateChatTransport(base, KEY)
        before = await transport.descriptor()
        servers[0].boot = str(uuid4())
        order.reverse()
        operation = {**claim(before['boot_id']), 'host': 'attacker.invalid', 'port': 80}
        records = [record async for record in transport.stream(operation)]
        assert records == [{'type': 'error', 'status': 404, 'retry_after': None}]
        posts = [item for item in calls if item[1] == 'POST']
        assert len(posts) == 1 and posts[0][0] == servers[0].boot
        assert transport.host == 'processor.test'
    asyncio.run(scenario())


@pytest.mark.parametrize('bad_signature', [False, True])
def test_unknown_or_unauthenticated_boot_never_receives_post(replicas, bad_signature):
    base, servers, calls, order = replicas
    for server in servers: server.bad_signature = bad_signature
    async def scenario():
        transport = PrivateChatTransport(base, KEY)
        operation = claim(servers[0].boot if bad_signature else str(uuid4()))
        try:
            await transport.cancel(operation)
        except (ChatError, TimeoutError):
            pass
        assert not [item for item in calls if item[1] == 'POST']
    asyncio.run(scenario())


def test_summary_control_deadline_includes_blocked_dns(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    def dns(*args, **kwargs):
        entered.set(); release.wait(5)
        return []
    monkeypatch.setattr(socket, 'getaddrinfo', dns)
    async def scenario():
        transport = PrivateChatTransport('http://processor.test:8003', KEY)
        identity = {'job_id': str(uuid4()), 'boot_id': 'original', 'scope': {},
                    'input_hash': 'd'*64, 'summary_version': 'synthetic'}
        task = asyncio.create_task(transport.summary.status(identity))
        try:
            assert await asyncio.to_thread(entered.wait, 1)
            done, _ = await asyncio.wait({task}, timeout=2.5)
            assert task in done
            with pytest.raises(ChatError) as error: await task
            assert error.value.code == 'summary_outcome_unknown'
        finally:
            release.set()
            await asyncio.gather(task, return_exceptions=True)
            await transport.summary.close()
    asyncio.run(scenario())


def test_cancelled_dns_resolution_cannot_probe_or_post_later(monkeypatch):
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    calls = []
    transport = PrivateChatTransport('http://processor.test:8003', KEY)
    original = transport.peer_for
    def resolving(*args, **kwargs):
        try: return original(*args, **kwargs)
        finally: finished.set()
    def dns(*args, **kwargs):
        entered.set(); release.wait(5)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 8003))]
    def unexpected(*args, **kwargs):
        calls.append(args)
        raise AssertionError('Cancelled resolution must not perform I/O.')
    monkeypatch.setattr(socket, 'getaddrinfo', dns)
    monkeypatch.setattr(transport, 'peer_for', resolving)
    monkeypatch.setattr(transport, '_open', unexpected)
    async def scenario():
        task = asyncio.create_task(transport.cancel(claim('original')))
        try:
            assert await asyncio.to_thread(entered.wait, 1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError): await task
        finally:
            release.set()
            assert await asyncio.to_thread(finished.wait, 1)
        assert calls == []
    asyncio.run(scenario())
