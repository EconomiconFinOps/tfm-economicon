"""Gateway deadlines/cancellation own resolver children and connecting sockets."""

import asyncio
import errno
import socket
import ssl
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest
from app.clients import chat_gateway as module
from app.clients.litellm import _AttemptDeadline
from test_chat_gateway_jup035 import gateway, private


def gateway_instance():
    return module.configured_gateway()


async def collect(gateway, deadline):
    return [
        record
        async for record in gateway(
            {
                "messages": [{"role": "system", "content": "Synthetic"}],
                "financial_metrics_allowed": False,
                "tool_protocol": None,
            },
            deadline,
        )
    ]


def blocked_dns(monkeypatch):
    original_dns = socket.getaddrinfo
    original_popen = subprocess.Popen
    release = threading.Event()
    parent_live = threading.Event()
    children = []

    def parent(*args, **kwargs):
        parent_live.set()
        try:
            release.wait(10)
            return original_dns(*args, **kwargs)
        finally:
            parent_live.clear()

    def child(command, *args, **kwargs):
        process = original_popen(
            [sys.executable, "-I", "-S", "-c", "import time; time.sleep(10)"],
            *args,
            **kwargs
        )
        children.append(process)
        return process

    monkeypatch.setattr(socket, "getaddrinfo", parent)
    monkeypatch.setattr(subprocess, "Popen", child)
    return release, parent_live, children


async def wait_started(parent, children):
    for _ in range(100):
        if parent.is_set() or children:
            return
        await asyncio.sleep(0.005)
    pytest.fail("Synthetic DNS did not start")


async def cleanup(release, children, task):
    release.set()
    for child in children:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=1)
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await asyncio.sleep(0.05)


def test_cancel_during_blocked_dns_reaps_own_child_and_releases_worker_without_http(
    gateway, monkeypatch
):
    release, parent, children = blocked_dns(monkeypatch)

    async def scenario():
        task = asyncio.create_task(collect(gateway_instance(), time.time() + 120))
        try:
            await wait_started(parent, children)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            for _ in range(60):
                if not parent.is_set() and all(
                    child.poll() is not None for child in children
                ):
                    break
                await asyncio.sleep(0.005)
            assert not parent.is_set(), "Cancelled DNS still occupies its worker"
            assert all(
                child.poll() is not None for child in children
            ), "Cancelled DNS child still alive"
            assert gateway[1] == []
        finally:
            await cleanup(release, children, task)

    asyncio.run(scenario())


def test_dns_consumes_inherited_budget_and_terminates_without_renewal_or_dispatch(
    gateway, monkeypatch
):
    release, parent, children = blocked_dns(monkeypatch)

    async def scenario():
        task = asyncio.create_task(collect(gateway_instance(), time.time() + 5.3))
        try:
            await wait_started(parent, children)
            records = await asyncio.wait_for(task, 1)
            assert len(records) == 1 and records[0]["type"] == "error"
            assert records[0]["category"] in ("timeout", "transport")
            assert not parent.is_set() and all(
                child.poll() is not None for child in children
            )
            assert gateway[1] == []
        finally:
            await cleanup(release, children, task)

    asyncio.run(scenario())


class FakeSocket:
    def __init__(self, *args, live, release=None, entered=None, **kwargs):
        self.live = live
        self.release = release
        self.entered = entered
        self.location = None
        self.timeout = None
        live.add(self)

    def bind(self, value):
        pass

    def settimeout(self, value):
        self.timeout = value

    def setblocking(self, value):
        pass

    def connect(self, location):
        self.location = location
        if self.entered:
            self.entered.set()
        if self.release:
            self.release.wait(10)

    def connect_ex(self, location):
        self.location = location
        if self.entered:
            self.entered.set()
        return errno.EINPROGRESS if self.release else 0

    def getsockopt(self, *args):
        return 0

    def setsockopt(self, *args):
        pass

    def fileno(self):
        return -1

    def close(self):
        self.live.discard(self)


def test_cancel_while_connecting_closes_only_its_socket_before_dns_budget_expires(
    gateway, monkeypatch
):
    live = set()
    release = threading.Event()
    entered = threading.Event()

    def selecting(*args):
        time.sleep(min(args[-1], 0.01))
        return [], [], []

    async def scenario():
        # Patch after creation of the asyncio loop; no global event-loop socket is changed.
        monkeypatch.setattr(
            socket,
            "socket",
            lambda *args, **kwargs: FakeSocket(
                *args, **kwargs, live=live, release=release, entered=entered
            ),
        )
        monkeypatch.setattr(
            module, "select", SimpleNamespace(select=selecting), raising=False
        )
        task = asyncio.create_task(collect(gateway_instance(), time.time() + 120))
        try:
            for _ in range(100):
                if entered.is_set():
                    break
                await asyncio.sleep(0.005)
            assert entered.is_set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            for _ in range(60):
                if not live:
                    break
                await asyncio.sleep(0.005)
            assert not live, "Cancelled connect left an open socket"
            assert gateway[1] == []
        finally:
            release.set()
            await asyncio.sleep(0.05)
            for sock in list(live):
                sock.close()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(scenario())


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_numeric_ipv4_ipv6_return_correct_address_and_leave_no_child_or_open_socket(
    monkeypatch, host
):
    live = set()
    children = []
    environments = []
    original_popen = subprocess.Popen

    def launch(command, *args, **kwargs):
        environments.append(kwargs.get("env"))
        child = original_popen(command, *args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setenv("LITELLM_API_KEY", "private-synthetic-secret")
    monkeypatch.setattr(subprocess, "Popen", launch)
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: FakeSocket(*args, **kwargs, live=live)
    )
    connection = module._ChatHTTPConnection(host, deadline=_AttemptDeadline(3))
    try:
        resolved = connection._connect_socket((host, 12345), 3, None)
        assert resolved.location[0] == host and resolved.location[1] == 12345
        assert len(resolved.location) == (2 if host == "127.0.0.1" else 4)
        resolved.close()
        assert not live and all(child.poll() is not None for child in children)
        for environment in environments:
            assert environment is not None and "LITELLM_API_KEY" not in environment
            assert "private-synthetic-secret" not in str(environment)
    finally:
        connection.close()
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)
        for sock in list(live):
            sock.close()


def test_tls_shares_dns_connect_budget_instead_of_starting_another_five_seconds(
    monkeypatch,
):
    live = set()
    base = time.monotonic()
    clock = [base]
    fake_time = SimpleNamespace(time=time.time, monotonic=lambda: clock[0])
    original_dns = socket.getaddrinfo
    original_popen = subprocess.Popen

    def resolving(*args, **kwargs):
        clock[0] += 4.8
        return original_dns(*args, **kwargs)

    def spawning(*args, **kwargs):
        clock[0] += 4.8
        return original_popen(*args, **kwargs)

    def selecting(*args):
        clock[0] += 0.25
        return [], [], []

    monkeypatch.setattr(module, "time", fake_time)
    resolver = sys.modules.get("app.clients.chat_dns")
    if resolver:
        monkeypatch.setattr(resolver, "time", fake_time)
    monkeypatch.setattr(socket, "getaddrinfo", resolving)
    monkeypatch.setattr(subprocess, "Popen", spawning)
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: FakeSocket(*args, **kwargs, live=live)
    )
    monkeypatch.setattr(
        module, "select", SimpleNamespace(select=selecting), raising=False
    )

    class TLS(FakeSocket):
        def do_handshake(self):
            raise ssl.SSLWantReadError()

    class Context:
        def wrap_socket(
            self, plain, server_hostname=None, do_handshake_on_connect=True
        ):
            if do_handshake_on_connect:
                clock[0] += 0.25
            plain.close()
            return TLS(live=live)

    connection = module._ChatHTTPSConnection(
        "127.0.0.1", 12345, deadline=_AttemptDeadline(30)
    )
    connection._context = Context()
    try:
        with pytest.raises(TimeoutError):
            connection.connect()
        assert clock[0] - base <= 5.1, "DNS or TLS renewed the five-second budget"
        assert not live, "Expired TLS left an open socket"
    finally:
        connection.close()
        for sock in list(live):
            sock.close()


@pytest.mark.parametrize(
    "fault",
    [
        "truncated",
        "oversized",
        "wrong_pid",
        "duplicate",
        "unknown",
        "nonzero",
        "extra",
        "invalid_utf8",
        "empty",
        "seventeen",
        "nonnumeric",
        "wrong_port",
        "wrong_family",
        "wrong_protocol",
        "bool_port",
        "ipv6_flow",
        "ipv6_scope",
        "zone",
        "error",
        "bad_error",
    ],
)
def test_invalid_resolver_protocol_never_creates_a_socket_and_reaps_its_child(
    monkeypatch, fault
):
    import json

    live = set()
    children = []
    launches = []
    original_popen = subprocess.Popen
    script = """import os,sys,json,struct
sys.stdin.buffer.read()
fault=sys.argv[1]
ready={'kind':'ready','pid':os.getpid()}
address=[2,1,6,'',['127.0.0.1',12345]]
result={'kind':'result','addresses':[address]}
if fault=='wrong_pid':ready['pid']+=1
if fault=='unknown':result['extra']=True
if fault=='empty':result['addresses']=[]
if fault=='seventeen':result['addresses']=[address]*17
if fault=='nonnumeric':address[4][0]='example.invalid'
if fault=='wrong_port':address[4][1]=80
if fault=='wrong_family':address[0]=999
if fault=='wrong_protocol':address[2]=17
if fault=='bool_port':address[4][1]=True
if fault in ('ipv6_flow','ipv6_scope','zone'):
 address[0]=10;address[4]=['::1',12345,0,0]
 if fault=='ipv6_flow':address[4][2]=1048576
 if fault=='ipv6_scope':address[4][3]=-1
 if fault=='zone':address[4][0]='fe80::1%eth0'
if fault in ('error','bad_error'):result={'kind':'error','code':'resolution' if fault=='error' else 'private-secret'}
def frame(value):
 raw=json.dumps(value,separators=(',',':')).encode()
 return struct.pack('!I',len(raw))+raw
output=frame(ready)+frame(result)
if fault=='truncated':output=output[:-1]
if fault=='oversized':output=frame(ready)+struct.pack('!I',8193)+b' '*8193
if fault=='duplicate':
 raw=b'{"kind":"result","kind":"result","addresses":[[2,1,6,"",["127.0.0.1",12345]]]}'
 output=frame(ready)+struct.pack('!I',len(raw))+raw
if fault=='invalid_utf8':output=frame(ready)+struct.pack('!I',1)+b'\\xff'
if fault=='extra':output+=b'X'
sys.stdout.buffer.write(output);sys.stdout.buffer.flush()
sys.exit(1 if fault=='nonzero' else 0)
"""

    def launch(command, *args, **kwargs):
        launches.append((command, kwargs))
        child = original_popen(
            [sys.executable, "-I", "-S", "-c", script, fault], *args, **kwargs
        )
        children.append(child)
        return child

    monkeypatch.setenv("PRIVATE_SYNTHETIC_SECRET", "never-inherit")
    monkeypatch.setattr(subprocess, "Popen", launch)
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: FakeSocket(*args, **kwargs, live=live)
    )
    connection = module._ChatHTTPConnection("127.0.0.1", deadline=_AttemptDeadline(2))
    try:
        with pytest.raises((ValueError, OSError)):
            connection._connect_socket(("127.0.0.1", 12345), 2, None)
        assert not live and len(children) == 1 and children[0].poll() is not None
        assert children[0].stdin.closed and children[0].stdout.closed
        command, options = launches[0]
        assert command[1:4] == ["-I", "-S", "-B"] and command[-1].endswith(
            "chat_dns_child.py"
        )
        assert options["shell"] is False and options["close_fds"] is True
        assert (
            options["stderr"] == subprocess.DEVNULL
            and "PRIVATE_SYNTHETIC_SECRET" not in options["env"]
        )
    finally:
        connection.close()
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)
        for sock in list(live):
            sock.close()


def test_cancel_during_tls_handshake_closes_owned_socket_and_finishes_worker(
    monkeypatch,
):
    live = set()
    entered = threading.Event()
    cancelled = threading.Event()
    errors = []
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: FakeSocket(*args, **kwargs, live=live)
    )

    def selecting(*args):
        entered.set()
        time.sleep(min(0.01, args[-1]))
        return [], [], []

    monkeypatch.setattr(module, "select", SimpleNamespace(select=selecting))

    class TLS(FakeSocket):
        def do_handshake(self):
            raise ssl.SSLWantReadError()

    class Context:
        def wrap_socket(
            self, plain, server_hostname=None, do_handshake_on_connect=True
        ):
            assert do_handshake_on_connect is False
            plain.close()
            return TLS(live=live)

    connection = module._ChatHTTPSConnection(
        "127.0.0.1", 12345, deadline=_AttemptDeadline(30), cancelled=cancelled
    )
    connection._context = Context()

    def connect():
        try:
            connection.connect()
        except BaseException as failure:
            errors.append(failure)

    worker = threading.Thread(target=connect)
    worker.start()
    try:
        assert entered.wait(1), "TLS handshake did not start"
        cancelled.set()
        worker.join(0.3)
        assert not worker.is_alive() and not live and connection.sock is None
        assert len(errors) == 1 and isinstance(errors[0], TimeoutError)
    finally:
        cancelled.set()
        worker.join(6)
        connection.close()
        for sock in list(live):
            sock.close()
