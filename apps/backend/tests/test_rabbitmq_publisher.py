"""RF-086-003 public Pika boundary doubles with a real scheduled IOLoop."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import ast
import json
import inspect
import importlib.util
import logging
import socket
import ssl
import subprocess
import sys
import threading
import time
import textwrap
from pathlib import Path
from queue import Empty, Queue
from types import SimpleNamespace

import pika
from pika import frame, spec
from pika.adapters.select_connection import SelectConnection, IOLoop
from pika.adapters.utils.nbio_interface import AbstractStreamProtocol, AbstractStreamTransport
from pika.adapters.utils.selector_ioloop_adapter import SelectorIOServicesAdapter
import pytest

from app.services import rabbitmq_queue as publisher


URL = "amqp://unit:synthetic@127.0.0.1:5672/%2F"
JOB = {"id": "own-job", "tenant_id": "tenant-a", "created_by": "alice", "status": "queued",
       "source": "test", "artifact_uri": None,
       "payload": {"tenant_id": "tenant-a", "source": "test", "text_content": "private-body-marker"}}






def require(queue, *methods):
    missing = [name for name in methods if not callable(getattr(queue, name, None))]
    assert not missing, "Contract entrypoints absent: " + ", ".join(missing)


def start_if_supported(queue):
    if callable(getattr(queue, "start", None)):
        queue.start()


def publish_compatible(queue, job=JOB):
    if callable(getattr(queue, "reserve", None)):
        token = queue.reserve()
        if getattr(token, "outcome", None) == "not_sent":
            return token
        return queue.publish(job, reservation=token)
    return queue.publish(job)


def outcome(result, expected, code=None):
    assert getattr(result, "outcome", None) == expected, f"Expected explicit {expected}, got {result!r}"
    if code is not None:
        assert result.code == code


@pytest.mark.parametrize("registry_origin", ["cached", "active"])
def test_owner_registration_survives_failed_close_after_dns_thread_exits(monkeypatch, record_property, registry_origin):
    from app.core.runtime_secrets import StartupError

    assert publisher.SHUTDOWN_TIMEOUT == 5.0
    source, first_line = inspect.getsourcelines(publisher.RabbitMQQueue._send)
    calls = [node for node in ast.walk(ast.parse(textwrap.dedent("".join(source))))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == "basic_publish"]
    assert len(calls) == 1, "Locate the actual basic_publish send boundary unambiguously"
    send_line = first_line + calls[0].lineno - 1
    send_code = publisher.RabbitMQQueue._send.__code__
    entered, release = threading.Event(), threading.Event()
    previous_trace = threading.gettrace()
    existing = set(threading.enumerate())
    queues, results, waiter_errors = [], [], []
    observations = {}
    first = waiter = active_service = None

    def trace(frame, event, arg):
        if (event == "line" and frame.f_code is send_code and frame.f_lineno == send_line
                and frame.f_locals.get("self") is first and not entered.is_set()):
            entered.set()
            if not release.wait(10):
                raise RuntimeError("Test owner scheduling barrier expired")
        return trace

    def publish():
        try:
            results.append(first.publish(JOB, reservation=ticket))
        except BaseException as error:
            waiter_errors.append(error)

    threading.settrace(trace)
    try:
        if registry_origin == "active":
            from app.services.managed_resolver import ResolverSupervisor
            active_service = ResolverSupervisor()
            active_service.start()
        first_driver = PikaDriver(monkeypatch)
        first = publisher.RabbitMQQueue(URL, "owner-retention-first")
        queues.append(first)
        first.start()
        assert first_driver.ready.wait(2)
        ticket = first.reserve()
        waiter = threading.Thread(target=publish, name="owner-retention-waiter")
        waiter.start()
        assert entered.wait(2)
        assert ticket.phase == "IN_FLIGHT" and first_driver.sent == []
        started = time.monotonic()
        with pytest.raises(StartupError):
            first.close()
        observations["close_seconds"] = time.monotonic() - started
        assert observations["close_seconds"] <= 5.5
        assert first._thread.is_alive()
        first._resolver.thread.join(0.5)
        assert not first._resolver.thread.is_alive(), "Exercise registry retention after DNS owner exit"
        waiter.join(1)
        assert not waiter.is_alive() and waiter_errors == [] and len(results) == 1
        terminal = results[0]
        outcome(terminal, "unknown", "shutdown_in_flight")

        replacement_driver = PikaDriver(monkeypatch)
        replacement = publisher.RabbitMQQueue(URL, "owner-retention-rejected")
        queues.append(replacement)
        try:
            replacement.start()
        except StartupError:
            observations["replacement_rejected"] = True
        else:
            observations["replacement_rejected"] = False
        observations["owners_alive_at_attempt"] = sum(
            queue._thread is not None and queue._thread.is_alive() for queue in (first, replacement))
        observations["dns_thread_dead_at_attempt"] = not first._resolver.thread.is_alive()
        replacement.close()

        release.set()
        first._thread.join(2)
        assert not first._thread.is_alive() and first._loop is None
        assert all(connection.is_closed for connection in first_driver.connections)
        assert not first_driver.io.streams and not first._resolver.thread.is_alive()
        observations["late_old_sends"] = len(first_driver.sent)
        observations["old_resources_verified_closed"] = True
        assert ticket.result is terminal and len(first_driver.sent) <= 1
        # An earlier failure may remain reported; admission still requires verified cleanup.
        try:
            first.close()
        except StartupError:
            observations["late_close_error"] = "StartupError"
        else:
            observations["late_close_error"] = None

        recovered_driver = PikaDriver(monkeypatch)
        recovered = publisher.RabbitMQQueue(URL, "owner-retention-recovered")
        queues.append(recovered)
        recovered.start()
        assert recovered_driver.ready.wait(2)
        recovered.start()
        assert len(recovered_driver.connections) == 1
        outcome(recovered.publish(JOB, reservation=recovered.reserve()), "confirmed")
        recovered.close()
        recovered.close()
        observations["start_after_verified_cleanup"] = True
    finally:
        release.set()
        if waiter is not None:
            waiter.join(2)
        for queue in reversed(queues):
            try:
                queue.close()
            except StartupError:
                pass
            if queue._thread is not None:
                queue._thread.join(2)
        threading.settrace(previous_trace)
        if active_service is not None:
            active_service.close(deadline=time.monotonic() + 5)
        observations["remaining_owned_threads"] = [thread.name for thread in threading.enumerate()
                                                    if thread not in existing]
        record_property("owner_retention_observations", json.dumps(observations))
        assert observations["remaining_owned_threads"] == []

    assert observations["replacement_rejected"], (
        "Replacement admitted while the prior publisher could still send, despite DNS cleanup: "
        + json.dumps(observations))
    assert observations["owners_alive_at_attempt"] == 1


def test_owner_thread_must_exit_after_pika_cleanup_proof_before_replacement(monkeypatch):
    from app.core.runtime_secrets import StartupError

    entered, release = threading.Event(), threading.Event()
    existing, previous_trace = set(threading.enumerate()), threading.gettrace()
    owner = None
    queues = []

    def trace(frame, event, arg):
        if event == "return" and frame.f_code is publisher.RabbitMQQueue._run.__code__ and frame.f_locals.get("self") is owner:
            entered.set()
            if not release.wait(8):
                raise RuntimeError("Test owner return barrier expired")
        return trace

    threading.settrace(trace)
    try:
        driver = PikaDriver(monkeypatch)
        owner = publisher.RabbitMQQueue(URL, "owner-return-boundary")
        queues.append(owner)
        owner.start()
        assert driver.ready.wait(2)
        started = time.monotonic()
        with pytest.raises(StartupError):
            owner.close()
        assert time.monotonic() - started <= 5.5 and publisher.SHUTDOWN_TIMEOUT == 5.0
        assert entered.is_set() and owner._thread.is_alive()
        assert owner._pika_cleanup_complete.is_set() and owner._loop is None
        assert all(connection.is_closed for connection in driver.connections)
        assert not owner._resolver.thread.is_alive()
        contender = publisher.RabbitMQQueue(URL, "owner-return-rejected")
        queues.append(contender)
        with pytest.raises(StartupError):
            contender.start()
        release.set()
        owner._thread.join(2)
        assert not owner._thread.is_alive()
        owner.close()
        next_driver = PikaDriver(monkeypatch)
        next_owner = publisher.RabbitMQQueue(URL, "owner-return-clean")
        queues.append(next_owner)
        next_owner.start()
        assert next_driver.ready.wait(2)
    finally:
        release.set()
        for queue in reversed(queues):
            try:
                queue.close()
            except StartupError:
                pass
            if queue._thread is not None:
                queue._thread.join(2)
        threading.settrace(previous_trace)
        assert set(threading.enumerate()) <= existing


@pytest.mark.parametrize("other_kind", ["new", "probe"])
def test_non_owner_close_cannot_release_registration_and_clean_restart_is_allowed(monkeypatch, other_kind):
    from app.core.runtime_secrets import StartupError

    queues = []
    existing = set(threading.enumerate())
    try:
        driver = PikaDriver(monkeypatch)
        owner = publisher.RabbitMQQueue(URL, "registered-owner")
        queues.append(owner)
        owner.start()
        assert driver.ready.wait(2)
        original_thread, original_io = owner._thread, driver.io
        owner.start()
        other = publisher.RabbitMQQueue(URL, "non-owner")
        queues.append(other)
        if other_kind == "probe":
            try:
                assert other.ping() is True
            finally:
                # The double selects a scheduler per connection; real Pika loops are independent.
                driver.io = original_io
        other.close()
        other.close()
        assert owner._thread is original_thread and original_thread.is_alive()
        contender = publisher.RabbitMQQueue(URL, "still-rejected")
        queues.append(contender)
        with pytest.raises(StartupError):
            contender.start()
        contender.close()
        outcome(owner.publish(JOB, reservation=owner.reserve()), "confirmed")
        owner.close()
        owner.close()
        assert not original_thread.is_alive() and all(connection.is_closed for connection in driver.connections)

        next_driver = PikaDriver(monkeypatch)
        next_owner = publisher.RabbitMQQueue(URL, "next-clean-owner")
        queues.append(next_owner)
        next_owner.start()
        assert next_driver.ready.wait(2)
        outcome(next_owner.publish(JOB, reservation=next_owner.reserve()), "confirmed")
    finally:
        for queue in reversed(queues):
            try:
                queue.close()
            except StartupError:
                pass
            if queue._thread is not None:
                queue._thread.join(2)
        assert set(threading.enumerate()) <= existing


def unverified_owner_scenario(mode):
    """Keep an intentionally unprovable registry inside a disposable test host."""
    from app.core.runtime_secrets import StartupError
    from app.services.managed_resolver import get_resolver

    patch = pytest.MonkeyPatch()
    queues = []
    existing = set(threading.enumerate())
    try:
        driver = PikaDriver(patch)
        if mode == "loop-close":
            class UnverifiedLoop(IOLoop):
                def close(self):
                    super().close()
                    raise OSError("synthetic cleanup proof failure")
            patch.setattr(publisher, "IOLoop", UnverifiedLoop)
        else:
            assert mode == "connection-close"
            patch.setattr(PikaDriver.Connection, "lost", lambda self, error: None)
        owner = publisher.RabbitMQQueue(URL, "unverified-owner")
        queues.append(owner)
        owner.start()
        assert driver.ready.wait(2)
        resolver = owner._resolver
        with pytest.raises(StartupError):
            owner.close()
        owner._thread.join(2)
        assert not owner._thread.is_alive() and not resolver.thread.is_alive()
        assert not owner.publisher_stopped and not resolver.retired
        assert get_resolver() is resolver
        contender = publisher.RabbitMQQueue(URL, "unverified-replacement")
        queues.append(contender)
        with pytest.raises(StartupError):
            contender.start()
        publisher.RabbitMQQueue(URL, "unregistered-object").close()
        assert get_resolver() is resolver
        with pytest.raises(StartupError):
            contender.start()
        assert owner._session is not None, "Unverified Pika references were discarded"
        if mode == "loop-close":
            assert owner._loop is not None, "Failed loop close must retain its reference"
        print("DEAD_OWNER_WITHOUT_PROOF_REMAINS_REGISTERED", flush=True)
    finally:
        for queue in reversed(queues):
            try:
                queue.close()
            except StartupError:
                pass
            if queue._thread is not None:
                queue._thread.join(2)
        patch.undo()
        assert set(threading.enumerate()) <= existing


@pytest.mark.parametrize("mode", ["loop-close", "connection-close"])
def test_dead_owner_without_cleanup_proof_cannot_release_registry(mode):
    command = (
        "import runpy,sys; from pathlib import Path; "
        "sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[1])); "
        "runpy.run_path(sys.argv[1])['unverified_owner_scenario'](sys.argv[2])"
    )
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS} if sys.platform == "win32" else {}
    result = subprocess.run([sys.executable, "-B", "-c", command, str(Path(__file__).resolve()), mode],
                            capture_output=True, text=True, timeout=22, **options)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEAD_OWNER_WITHOUT_PROOF_REMAINS_REGISTERED" in result.stdout


class PikaDriver:
    """Behavioral constructor double; real runtime feasibility has separate tests."""

    def __init__(self, monkeypatch):
        self.calls = []
        self.sent = []
        self.parameters = []
        self.connections = []
        self.sent_event = threading.Event()
        self.aborted = threading.Event()
        self.ready = threading.Event()
        self.auto_confirm = True
        self.send_error = None
        self.setup_pending = False
        self.declaration_pending = False
        self.confirm_pending = False
        self.io = None
        monkeypatch.setattr(pika, "BlockingConnection", self.blocking)
        monkeypatch.setattr(pika, "SelectConnection", self.select)
        monkeypatch.setattr(pika.adapters.select_connection, "SelectConnection", self.select)
        if hasattr(publisher, "SelectConnection"):
            monkeypatch.setattr(publisher, "SelectConnection", self.select)
        monkeypatch.setattr(SelectorIOServicesAdapter, "create_streaming_connection",
                            lambda services, *args, **kwargs: self.stream(*args, **kwargs))

    def record(self, name):
        self.calls.append((name, threading.get_ident()))

    def stream(self, protocol_factory, sock, on_done, **kwargs):
        protocol = protocol_factory()
        driver = self

        class Transport(AbstractStreamTransport):
            aborted = False

            def get_protocol(self):
                return protocol

            def write(self, data):
                if not data:
                    raise ValueError("Empty transport write")
                driver.record("transport.write")

            def get_write_buffer_size(self):
                return 0

            def abort(self):
                driver.record("transport.abort")
                driver.aborted.set()
                if not self.aborted:
                    self.aborted = True
                    driver.schedule(lambda: protocol.connection_lost(None))

        transport = Transport()
        protocol.connection_made(transport)
        on_done((transport, protocol))
        return SimpleNamespace(cancel=lambda: None)

    def schedule(self, callback):
        if self.io is None:
            callback()
        else:
            self.io.add_callback_threadsafe(callback)

    def blocking(self, parameters):
        self.record("BlockingConnection")
        self.parameters.append(parameters)
        connection = self.Connection(self, parameters, legacy=True)
        self.connections.append(connection)
        return connection

    def select(self, parameters=None, on_open_callback=None, on_open_error_callback=None,
               on_close_callback=None, custom_ioloop=None, internal_connection_workflow=True):
        self.record("SelectConnection.__init__")
        assert internal_connection_workflow is True
        assert isinstance(custom_ioloop, SelectorIOServicesAdapter)
        self.parameters.append(parameters)
        self.io = custom_ioloop
        connection = self.Connection(self, parameters)
        connection.callbacks.update(open=on_open_callback, open_error=on_open_error_callback,
                                    close=on_close_callback)
        self.connections.append(connection)

        def begin_stream():
            if connection.is_closed or connection.is_closing or self.setup_pending:
                return
            original_protocol = self.Protocol(connection)
            def completed(result):
                if isinstance(result, BaseException):
                    connection.lost(result)
                    return
                transport, original = result
                assert original is original_protocol, "Workflow must receive its original protocol"
                assert transport is connection.transport, "Workflow must receive the unchanged transport"
                self.schedule(connection.opened)
            custom_ioloop.create_streaming_connection(lambda: original_protocol, None, completed)

        self.schedule(begin_stream)
        return connection

    class Protocol(AbstractStreamProtocol):
        def __init__(self, connection):
            self.connection = connection

        def connection_made(self, transport):
            self.connection.driver.record("protocol.connection_made")
            self.connection.transport = transport

        def data_received(self, data):
            self.connection.driver.record("protocol.data_received")

        def eof_received(self):
            self.connection.driver.record("protocol.eof_received")
            return False

        def connection_lost(self, error):
            self.connection.driver.record("protocol.connection_lost")
            assert error is not None, "External abort requires the approved delegate's error translation"
            self.connection.lost(error)

    class Connection:
        def __init__(self, driver, parameters, legacy=False):
            self.driver = driver
            self.params = parameters
            self.legacy = legacy
            self.is_closed = False
            self.is_closing = False
            self.is_open = legacy
            self.ever_opened = legacy
            self.transport = None
            self.callbacks = {}
            self.channels = []

        def opened(self):
            if self.is_closed or self.is_closing:
                return
            self.is_open = self.ever_opened = True
            callback = self.callbacks.get("open")
            if callback is not None:
                callback(self)

        def channel(self, on_open_callback=None, **kwargs):
            self.driver.record("channel")
            assert self.is_open
            channel = PikaDriver.Channel(self)
            self.channels.append(channel)
            if on_open_callback:
                self.driver.schedule(lambda: on_open_callback(channel))
            return channel

        def add_on_close_callback(self, callback):
            self.callbacks["close"] = callback

        def add_on_connection_blocked_callback(self, callback):
            self.callbacks["blocked"] = callback

        def add_on_connection_unblocked_callback(self, callback):
            self.callbacks["unblocked"] = callback

        def lost(self, error):
            if self.is_closed:
                return
            self.is_open, self.is_closing, self.is_closed = False, False, True
            kind = "close" if self.ever_opened else "open_error"
            self.driver.record("callback." + kind)
            callback = self.callbacks.get(kind)
            if callback is not None:
                callback(self, error)

        def close(self, *args, **kwargs):
            self.driver.record("connection.close")
            if self.legacy:
                self.lost(pika.exceptions.ConnectionClosedByClient(200, "test probe closed"))
                return
            assert not self.is_closed and not self.is_closing
            self.is_closing = True
            if self.transport is None:
                self.driver.schedule(lambda: self.lost(pika.exceptions.ConnectionOpenAborted("setup stopped")))
            else:
                # No synthetic CloseOk: established teardown needs captured abort.
                assert self.ever_opened, "Opening stream must use flagged transport.abort, not close"

    class Channel:
        def __init__(self, connection):
            self.connection = connection
            self.driver = connection.driver
            self.is_closed = False
            self.is_open = True
            self.confirm = None
            self.returned = None
            self.closed = None
            self.sequence = 0

        def queue_declare(self, queue, durable, callback=None, **kwargs):
            self.driver.record("queue_declare")
            assert durable is True
            if callback and not self.driver.declaration_pending:
                self.driver.schedule(lambda: callback(SimpleNamespace(method=pika.spec.Queue.DeclareOk(queue=queue))))

        def confirm_delivery(self, ack_nack_callback, callback=None):
            self.driver.record("confirm_delivery")
            self.confirm = ack_nack_callback
            if callback and not self.driver.confirm_pending:
                def selected():
                    callback(SimpleNamespace(method=pika.spec.Confirm.SelectOk()))
                    self.driver.ready.set()
                self.driver.schedule(selected)

        def add_on_return_callback(self, callback):
            self.returned = callback

        def add_on_close_callback(self, callback):
            self.closed = callback

        def basic_publish(self, **kwargs):
            self.driver.record("basic_publish")
            self.sequence += 1
            self.driver.sent.append((self, kwargs))
            self.driver.sent_event.set()
            if self.driver.send_error:
                raise self.driver.send_error
            if self.confirm and self.driver.auto_confirm:
                self.ack(self.sequence)

        def ack(self, tag, multiple=False):
            self.driver.schedule(lambda: self.confirm(SimpleNamespace(method=pika.spec.Basic.Ack(delivery_tag=tag, multiple=multiple))))

        def nack(self, tag):
            self.driver.schedule(lambda: self.confirm(SimpleNamespace(method=pika.spec.Basic.Nack(delivery_tag=tag))))

        def return_message(self):
            self.driver.schedule(lambda: self.returned(self, pika.spec.Basic.Return(reply_code=312, reply_text="private-broker-marker"), pika.BasicProperties(), b"private-body-marker"))

        def close(self, *args, **kwargs):
            self.driver.record("channel.close")
            self.is_open, self.is_closed = False, True
            if self.closed:
                self.closed(self, RuntimeError("channel closed"))


@pytest.fixture
def driver(monkeypatch):
    return PikaDriver(monkeypatch)


@pytest.fixture
def queue(driver):
    instance = publisher.RabbitMQQueue(URL, "jup086-unit")
    try:
        yield instance
    finally:
        instance.close()






@pytest.fixture
def runtime_handshake_holder():
    """Owned, single-connection peer using Pika's public frame serialization."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(0.1)
    peer = SimpleNamespace(port=listener.getsockname()[1], wire=bytearray(),
                           header=threading.Event(), eof=threading.Event(),
                           stop=threading.Event(), errors=[], complete_handshake=False,
                           methods=[], product=False, hold=None, reply="ack",
                           reached=threading.Event(), delivered=threading.Event(),
                           deliveries=[], heartbeats=0, tls_context=None,
                           tls_established=threading.Event(), tls_errors=[], tls_version=None,
                           terminal_reason=None, controls=Queue())

    def serve():
        try:
            while not peer.stop.is_set():
                try:
                    stream, _ = listener.accept()
                except socket.timeout:
                    continue
                with ExitStack() as resources:
                    resources.enter_context(stream)
                    if peer.tls_context is not None:
                        stream.settimeout(2)
                        try:
                            stream = resources.enter_context(peer.tls_context.wrap_socket(stream, server_side=True))
                        except ssl.SSLError as error:
                            peer.tls_errors.append(error.reason)
                            peer.eof.set()
                            return
                        peer.tls_version = stream.version()
                        peer.tls_established.set()
                    stream.settimeout(0.1)
                    pending = bytearray()
                    handshake = "header"
                    content = None
                    last_heartbeat = time.monotonic()
                    while not peer.stop.is_set():
                        if peer.product and handshake == "opened":
                            try:
                                control, sent = peer.controls.get_nowait()
                            except Empty:
                                pass
                            else:
                                stream.sendall(frame.Method(0, control).marshal())
                                sent.set()
                        if (peer.product and handshake == "opened"
                                and time.monotonic() - last_heartbeat >= 0.1):
                            stream.sendall(frame.Heartbeat().marshal())
                            peer.heartbeats += 1
                            last_heartbeat = time.monotonic()
                        try:
                            data = stream.recv(4096)
                        except socket.timeout:
                            continue
                        if not data:
                            peer.terminal_reason = "eof"
                            peer.eof.set()
                            return
                        peer.wire.extend(data)
                        if len(peer.wire) >= 8:
                            peer.header.set()
                        if not peer.complete_handshake:
                            continue
                        pending.extend(data)
                        if handshake == "header" and len(pending) >= 8:
                            assert pending[:8] == b"AMQP\x00\x00\x09\x01"
                            del pending[:8]
                            properties = {"capabilities": {"publisher_confirms": True,
                                                           "basic.nack": True,
                                                           "connection.blocked": True}}
                            stream.sendall(frame.Method(0, spec.Connection.Start(server_properties=properties)).marshal())
                            handshake = "start_ok"
                        while pending and handshake != "header":
                            consumed, message = frame.decode_frame(bytes(pending))
                            if not consumed:
                                break
                            del pending[:consumed]
                            if isinstance(message, frame.Method):
                                peer.methods.append(type(message.method).__name__)
                            if peer.product and handshake == "opened":
                                if isinstance(message, frame.Heartbeat):
                                    continue
                                if isinstance(message, frame.Method):
                                    method = message.method
                                    replies = ((spec.Channel.Open, "channel", spec.Channel.OpenOk()),
                                               (spec.Queue.Declare, "declare", spec.Queue.DeclareOk(
                                                   queue="jup086-runtime", message_count=0, consumer_count=0)),
                                               (spec.Confirm.Select, "confirm", spec.Confirm.SelectOk()))
                                    for kind, stage, response in replies:
                                        if isinstance(method, kind):
                                            if peer.hold == stage:
                                                peer.reached.set()
                                            else:
                                                stream.sendall(frame.Method(message.channel_number, response).marshal())
                                            break
                                    else:
                                        assert isinstance(method, spec.Basic.Publish), type(method)
                                        content = {"method": method, "channel": message.channel_number,
                                                   "body": bytearray()}
                                elif isinstance(message, frame.Header):
                                    assert content is not None
                                    content.update(size=message.body_size, properties=message.properties)
                                else:
                                    assert isinstance(message, frame.Body) and content is not None
                                    content["body"].extend(message.fragment)
                                    if len(content["body"]) == content["size"]:
                                        peer.deliveries.append(content)
                                        peer.delivered.set()
                                        channel = content["channel"]
                                        tag = len(peer.deliveries)
                                        if peer.reply == "return":
                                            stream.sendall(frame.Method(channel, spec.Basic.Return(
                                                reply_code=312, reply_text="private-broker-marker",
                                                exchange="", routing_key="jup086-runtime")).marshal()
                                                + frame.Header(channel, content["size"], content["properties"]).marshal()
                                                + frame.Body(channel, bytes(content["body"])).marshal())
                                        if peer.reply in {"ack", "return", "nack"}:
                                            reply = spec.Basic.Nack if peer.reply == "nack" else spec.Basic.Ack
                                            stream.sendall(frame.Method(channel, reply(delivery_tag=tag)).marshal())
                                        content = None
                                continue
                            assert isinstance(message, frame.Method)
                            if handshake == "start_ok":
                                assert isinstance(message.method, spec.Connection.StartOk)
                                stream.sendall(frame.Method(0, spec.Connection.Tune(
                                    channel_max=16, frame_max=131072, heartbeat=30)).marshal())
                                handshake = "tune_ok"
                            elif handshake == "tune_ok":
                                assert isinstance(message.method, spec.Connection.TuneOk)
                                handshake = "open"
                            elif handshake == "open":
                                assert isinstance(message.method, spec.Connection.Open)
                                stream.sendall(frame.Method(0, spec.Connection.OpenOk()).marshal())
                                handshake = "opened"
                            else:
                                raise AssertionError("Unexpected frame after OpenOk")
                return
        except ConnectionResetError:
            peer.terminal_reason = "reset"
            peer.eof.set()
        except ConnectionAbortedError as error:
            if sys.platform == "win32" and getattr(error, "winerror", None) == 10053:
                peer.terminal_reason = "windows-aborted-10053"
                peer.eof.set()
            else:
                peer.errors.append(error)
        except Exception as error:
            peer.errors.append(error)
        finally:
            listener.close()

    server = threading.Thread(target=serve, name="jup086-runtime-handshake-peer")
    server.start()
    try:
        yield peer
    finally:
        peer.stop.set()
        server.join(timeout=2)
        assert not server.is_alive(), "Owned loopback peer did not terminate"
        assert peer.errors == []




def await_publisher_state(predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert predicate(), "Publisher did not reach the expected state within its observation budget"


def peer_blocked(peer, queue, blocked):
    sent = threading.Event()
    method = spec.Connection.Blocked(reason="owned-test") if blocked else spec.Connection.Unblocked()
    peer.controls.put((method, sent))
    assert sent.wait(1)
    await_publisher_state(lambda: (queue._blocked_at is not None) == blocked)


def assert_publisher_clean(queue, peer, threads):
    assert peer.eof.wait(1)
    assert queue.publisher_stopped and queue._loop is None and queue._session is None
    assert not queue._resolver.thread.is_alive()
    assert set(threading.enumerate()) <= threads


def test_actual_pika_blocked_unblocked_resumes_once_and_close_is_terminal(runtime_handshake_holder, record_property):
    peer = runtime_handshake_holder
    peer.product = peer.complete_handshake = True
    queue = publisher.RabbitMQQueue(f"amqp://unit:synthetic@127.0.0.1:{peer.port}/%2F", "jup086-runtime")
    threads = set(threading.enumerate())
    try:
        queue.start()
        await_publisher_state(lambda: queue._ready)
        assert publisher._parameters(queue.rabbitmq_url).heartbeat == 30
        assert publisher.CONFIRM_TIMEOUT == publisher.SHUTDOWN_TIMEOUT == 5
        with ThreadPoolExecutor(max_workers=1) as pool:
            peer_blocked(peer, queue, True)
            token = queue.reserve()
            waiter = pool.submit(queue.publish, JOB, reservation=token)
            await_publisher_state(lambda: token.phase == "READY_TO_SEND")
            time.sleep(0.35)
            assert not waiter.done() and peer.deliveries == [], "Blocked publisher sent before Unblocked"
            peer_blocked(peer, queue, False)
            confirmed = waiter.result(timeout=2)
            outcome(confirmed, "confirmed")
            assert [json.loads(item["body"]) for item in peer.deliveries] == [JOB]
            peer_blocked(peer, queue, True)
            pending = queue.reserve()
            waiter = pool.submit(queue.publish, {**JOB, "id": "never-send"}, reservation=pending)
            await_publisher_state(lambda: pending.phase == "READY_TO_SEND")
            started = time.monotonic()
            queue.close()
            elapsed = time.monotonic() - started
            assert elapsed <= 5.5
            stopped = waiter.result(timeout=1)
            outcome(stopped, "not_sent", "stopping")
            assert queue.publish(JOB, reservation=token) is confirmed
            assert queue.publish(JOB, reservation=pending) is stopped
            with pytest.raises(FrozenInstanceError):
                stopped.outcome = "confirmed"
            assert len(peer.deliveries) == 1, "Terminal ticket replayed"
            record_property("blocked_close_seconds", elapsed)
    finally:
        queue.close()
    assert_publisher_clean(queue, peer, threads)


def test_actual_pika_blocked_expiry_retires_inflight_without_replay(runtime_handshake_holder, record_property):
    peer = runtime_handshake_holder
    peer.product = peer.complete_handshake = True
    peer.reply = "hold"
    queue = publisher.RabbitMQQueue(f"amqp://unit:synthetic@127.0.0.1:{peer.port}/%2F", "jup086-runtime")
    threads = set(threading.enumerate())
    try:
        queue.start()
        assert publisher._parameters(queue.rabbitmq_url).blocked_connection_timeout == 3
        assert publisher.CONFIRM_TIMEOUT == 5 and publisher.TICKET_TIMEOUT == 10
        with ThreadPoolExecutor(max_workers=2) as pool:
            token = queue.reserve()
            waiter = pool.submit(queue.publish, JOB, reservation=token)
            assert peer.delivered.wait(2)
            peer_blocked(peer, queue, True)
            blocked_at = queue._blocked_at
            pending = queue.reserve()
            queued = pool.submit(queue.publish, {**JOB, "id": "never-send"}, reservation=pending)
            await_publisher_state(lambda: pending.phase == "READY_TO_SEND")
            result = waiter.result(timeout=4)
            elapsed = time.monotonic() - blocked_at
            outcome(result, "unknown", "connection_lost")
            assert 2.8 <= elapsed <= 3.6, "Blocked expiry must precede the five-second confirm deadline"
            assert peer.eof.wait(0.5) and len(peer.deliveries) == 1
            started = time.monotonic()
            queue.close()
            assert time.monotonic() - started <= 5.5
            stopped = queued.result(timeout=1)
            outcome(stopped, "not_sent", "stopping")
            assert queue.publish(JOB, reservation=token) is result
            assert queue.publish(JOB, reservation=pending) is stopped
            with pytest.raises(FrozenInstanceError):
                result.outcome = "confirmed"
            assert len(peer.deliveries) == 1 and "Close" not in peer.methods
            record_property("blocked_expiry_seconds", elapsed)
    finally:
        queue.close()
    assert_publisher_clean(queue, peer, threads)


class RuntimeAbortDelegate(AbstractStreamProtocol):
    """Test-only public protocol candidate; no access to Pika's private state."""

    def __init__(self, original, observe=lambda name: None):
        self.original = original
        self.observe = observe
        self.external_abort = False

    def connection_made(self, transport):
        self.observe("connection_made")
        return self.original.connection_made(transport)

    def data_received(self, data):
        self.observe("data_received")
        return self.original.data_received(data)

    def eof_received(self):
        self.observe("eof_received")
        return self.original.eof_received()

    def connection_lost(self, error):
        self.observe("connection_lost")
        if self.external_abort and error is None:
            error = ConnectionAbortedError("Publisher transport stopped")
        return self.original.connection_lost(error)












@pytest.mark.parametrize("reply,expected,code", [
    ("ack", "confirmed", "confirmed"), ("nack", "rejected", "broker_nack"),
    ("return", "rejected", "unroutable"), ("cancel", "unknown", "cancelled_in_flight"),
    ("stop", "unknown", "shutdown_in_flight"), ("hold", "unknown", "confirm_timeout"),
])
def test_product_real_pika_delivery_and_abort_without_closeok(runtime_handshake_holder, reply, expected, code, record_property):
    peer = runtime_handshake_holder
    peer.product = peer.complete_handshake = True
    peer.reply = reply
    queue = publisher.RabbitMQQueue(f"amqp://unit:synthetic@127.0.0.1:{peer.port}/%2F", "jup086-runtime")
    before_threads = {thread.ident for thread in threading.enumerate()}
    try:
        queue.start()
        token = queue.reserve()
        with ThreadPoolExecutor(max_workers=1) as pool:
            started = time.monotonic()
            waiter = pool.submit(queue.publish, JOB, reservation=token)
            assert peer.delivered.wait(3)
            if reply == "cancel":
                queue.cancel(token)
            elif reply == "stop":
                queue.close()
            result = waiter.result(timeout=6)
            elapsed = time.monotonic() - started
            outcome(result, expected, code)
            assert elapsed <= 6.5
            if reply == "hold":
                assert elapsed >= 4.8 and peer.heartbeats >= 20
            queue.close()
            assert queue.publish(JOB, reservation=token) == result
        assert peer.eof.wait(1), "Real product did not abort its captured stream"
        assert queue.publisher_stopped and queue._loop is None and queue._session is None
        assert len(peer.deliveries) == 1
        delivered = peer.deliveries[0]
        assert json.loads(delivered["body"]) == JOB
        assert delivered["properties"].delivery_mode == 2
        assert (delivered["method"].exchange, delivered["method"].routing_key,
                delivered["method"].mandatory) == ("", "jup086-runtime", True)
        assert peer.methods.count("Select") == 1 and "Close" not in peer.methods
        assert {thread.ident for thread in threading.enumerate()} <= before_threads
        record_property("actual_product_pika_version", pika.__version__)
        record_property("heartbeat_frames_sent", peer.heartbeats)
        record_property("wire_deliveries", len(peer.deliveries))
        record_property("public_result", result.outcome + ":" + result.code)
        record_property("peer_terminal_reason", peer.terminal_reason)
    finally:
        queue.close()




def assert_spawned_dns_cleanup(monkeypatch, tmp_path, phase, record_property):
    from test_managed_resolver import ChildHarness, managed_module, wait_until

    module = managed_module()
    existing = set(threading.enumerate())
    queue = publisher.RabbitMQQueue("amqp://unit:synthetic@rf003-dns.invalid:5672/%2F", "jup086-stalled-dns")
    parent_calls = []
    with monkeypatch.context() as patch:
        children = ChildHarness(module, patch, tmp_path, "block")
        def forbidden_parent_dns(*args, **kwargs):
            parent_calls.append(threading.get_ident())
            raise socket.gaierror(socket.EAI_FAIL, "DNS must run only in the child")
        patch.setattr(socket, "getaddrinfo", forbidden_parent_dns)
        try:
            started = time.monotonic()
            queue.start()
            assert time.monotonic() - started <= 1.2
            wait_until(lambda: bool(children.markers()), timeout=3)
            if phase == "setup-expiry-retry-close":
                wait_until(lambda: len(children.markers()) >= 2, timeout=8)
                assert children.launches[1]["previous_unreaped"] == [], "New generation preceded previous DNS reap"
            started = time.monotonic()
            queue.close()
            assert time.monotonic() - started <= 5.5
            assert parent_calls == [], "Pika's non-terminable parent resolver was still used"
            assert not (tmp_path / "release").exists()
            assert all(p.returncode is not None and p.stdin.closed and p.stdout.closed for p in children.processes)
            assert {item["pid"] for item in children.markers()} <= {p.pid for p in children.processes}
            assert set(threading.enumerate()) <= existing
            record_property("dns_boundary", "real spawned child; product runpy entrypoint")
            record_property("dns_children_reaped_before_fixture_release", len(children.processes))
        finally:
            try:
                queue.close()
            finally:
                children.cleanup()


@pytest.mark.parametrize("phase", ["immediate-close", "setup-expiry-retry-close"])
def test_product_real_pika_stalled_dns_leaves_no_helpers_or_overlapping_resolvers(monkeypatch, tmp_path, phase, record_property):
    """Exercise Pika's real resolver lifetime, before any TCP stream exists."""
    if importlib.util.find_spec("app.services.managed_resolver") is not None:
        assert_spawned_dns_cleanup(monkeypatch, tmp_path, phase, record_property)
        return
    record_property("dns_boundary", "legacy parent resolver; child entrypoint absent, not child evidence")
    release, entered, overlap = (threading.Event() for _ in range(3))
    lock = threading.Lock()
    resolvers, active, guard_timeouts = [], set(), []
    observations = {"max_active_resolvers": 0}
    original_getaddrinfo = socket.getaddrinfo
    existing_threads = set(threading.enumerate())
    queue = publisher.RabbitMQQueue(
        "amqp://unit:synthetic@rf003-dns.invalid:5672/%2F", "jup086-stalled-dns")

    def held_dns(*args, **kwargs):
        resolver = threading.current_thread()
        with lock:
            resolvers.append(resolver)
            active.add(resolver)
            observations["max_active_resolvers"] = max(observations["max_active_resolvers"], len(active))
            entered.set()
            if len(active) > 1:
                overlap.set()
        try:
            if not release.wait(20):
                guard_timeouts.append(resolver.name)
            # Never return an address: even exceptional cleanup cannot connect.
            raise socket.gaierror(socket.EAI_AGAIN, "Synthetic resolver released")
        finally:
            with lock:
                active.discard(resolver)

    with monkeypatch.context() as patch:
        patch.setattr(socket, "getaddrinfo", held_dns)
        try:
            started = time.monotonic()
            queue.start()
            assert entered.wait(3), "Real Pika did not reach the controlled public DNS boundary"
            if phase == "setup-expiry-retry-close":
                # Observe the real 5 s setup + 1 s backoff without demanding a
                # second resolver: a corrected implementation must not overlap.
                overlap.wait(7.5)
            observations["before_close_seconds"] = time.monotonic() - started
            before_close = time.monotonic()
            close_error = None
            try:
                queue.close()
            except Exception as error:
                close_error = type(error).__name__
            observations["close_seconds"] = time.monotonic() - before_close
            observations["close_error"] = close_error
            with lock:
                observations["resolver_entries"] = len(resolvers)
                observations["resolvers_after_close"] = [
                    {"name": thread.name, "daemon": thread.daemon}
                    for thread in resolvers if thread.is_alive()]
            observations["threads_after_close"] = [
                {"name": thread.name, "daemon": thread.daemon}
                for thread in threading.enumerate() if thread not in existing_threads]
            observations["release_set_at_close"] = release.is_set()
        finally:
            release.set()
            try:
                queue.close()
            finally:
                with lock:
                    owned = set(resolvers)
                owned.update(thread for thread in threading.enumerate() if thread not in existing_threads)
                deadline = time.monotonic() + 5
                for thread in owned:
                    thread.join(max(0, deadline - time.monotonic()))
                cleanup_alive = [thread.name for thread in owned if thread.is_alive()]
                record_property("dns_cleanup_alive", json.dumps(cleanup_alive))
                assert not cleanup_alive, "Test cleanup left resolver or owner threads alive"
                assert not guard_timeouts, "Controlled DNS release guard expired"

    assert socket.getaddrinfo is original_getaddrinfo
    record_property("public_getaddrinfo_restored", True)
    record_property("actual_pika_version", pika.__version__)
    for name, value in observations.items():
        record_property("dns_" + name, json.dumps(value))
    assert not observations["release_set_at_close"]
    assert observations["close_error"] is None and observations["close_seconds"] <= 5.5
    if phase == "setup-expiry-retry-close":
        assert observations["max_active_resolvers"] <= 1, (
            "Setup retry started another resolver while abandoned DNS work was still blocked: "
            + json.dumps(observations))
    assert observations["resolvers_after_close"] == [], (
        "Public close returned with live Pika DNS resolvers: " + json.dumps(observations))
    assert observations["threads_after_close"] == [], "Successful close must leave no owner or helper threads"










def test_pika_log_sanitization_removes_arguments_body_and_exception_chain(queue, driver, caplog):
    logger = logging.getLogger("pika.adapters.select_connection")
    queue.start()
    assert driver.ready.wait(2)
    with caplog.at_level(logging.ERROR):
        try:
            try:
                raise ValueError("private-cause-marker")
            except ValueError as cause:
                raise RuntimeError("private-broker-marker") from cause
        except RuntimeError:
            logger.exception("URL %s body %s", URL, "private-body-marker", stack_info=True)
    records = [record for record in caplog.records if record.name == logger.name]
    assert records and records[-1].getMessage() == "rabbitmq_dependency_event"
    assert records[-1].exc_info is None and records[-1].exc_text is None and records[-1].stack_info is None
    assert all(marker not in caplog.text for marker in (URL, "private-cause-marker", "private-broker-marker", "private-body-marker"))






def test_loss_after_entering_send_is_unknown_and_never_replayed(queue, driver):
    driver.send_error = pika.exceptions.StreamLostError("synthetic post-send loss")
    start_if_supported(queue)
    result = publish_compatible(queue)
    assert len(driver.sent) == 1
    outcome(result, "unknown", "connection_lost")
    time.sleep(1.2)
    assert len(driver.sent) == 1










def test_capacity_is_16_including_reserved_tokens_and_cancel_releases_once(queue):
    require(queue, "start", "reserve", "cancel")
    queue.start()
    barrier = threading.Barrier(21)
    def reserve():
        barrier.wait(timeout=3)
        return queue.reserve()
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(reserve) for _ in range(20)]
        before = time.monotonic()
        barrier.wait(timeout=3)
        results = [future.result(timeout=2) for future in futures]
    assert time.monotonic() - before < 1
    admitted = [value for value in results if getattr(value, "outcome", None) != "not_sent"]
    rejected = [value for value in results if getattr(value, "outcome", None) == "not_sent"]
    assert len(admitted) == 16 and len(rejected) == 4
    assert all(value.code == "capacity" for value in rejected)
    for token in admitted:
        queue.cancel(token)
        queue.cancel(token)
    more = [queue.reserve() for _ in range(17)]
    assert sum(getattr(value, "outcome", None) != "not_sent" for value in more) == 16
    for token in more:
        if getattr(token, "outcome", None) != "not_sent":
            queue.cancel(token)


def test_cancel_before_send_prevents_every_later_send(queue, driver):
    require(queue, "start", "reserve", "cancel")
    queue.start()
    token = queue.reserve()
    queue.cancel(token)
    result = queue.publish(JOB, reservation=token)
    outcome(result, "not_sent")
    assert driver.sent == []










def test_confirm_deadline_retires_generation_and_late_ack_cannot_complete_next(queue, driver):
    require(queue, "start", "reserve")
    driver.auto_confirm = False
    queue.start()
    first = queue.reserve()
    before = time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(queue.publish, JOB, reservation=first)
        assert driver.sent_event.wait(3)
        old = driver.sent[0][0]
        outcome(future.result(timeout=6), "unknown", "confirm_timeout")
        assert time.monotonic() - before <= 6.5
        # Completion wakes the caller before the owner necessarily finishes the
        # same tick. Allow one 100 ms tick plus bounded scheduler tolerance.
        assert driver.aborted.wait(0.3), "Timed-out generation was not promptly aborted"
        driver.sent_event.clear()
        second = queue.reserve()
        future = pool.submit(queue.publish, {**JOB, "id": "second"}, reservation=second)
        assert driver.sent_event.wait(5)
        new = driver.sent[-1][0]
        assert new is not old
        names = [name for name, _ in driver.calls]
        assert names.index("transport.abort") < names.index("SelectConnection.__init__", 1)
        old.ack(1)
        old.nack(1)
        old.return_message()
        time.sleep(0.15)
        assert not future.done(), "Old generation ack completed the new ticket"
        new.ack(1)
        outcome(future.result(timeout=2), "confirmed")
    assert [json.loads(item["body"])["id"] for _, item in driver.sent] == ["own-job", "second"]
