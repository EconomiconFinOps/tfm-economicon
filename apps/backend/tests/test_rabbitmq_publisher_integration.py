"""Opt-in disposable RabbitMQ; frame faults use only stdlib and owned sockets.

Run with JUP086_RABBITMQ_TEST_URL supplied by the orchestrator. This module
never starts/restarts Docker, changes policies, purges queues or uses defaults.
Run the idle test with a process timeout >=90 seconds. SQL CAS on CockroachDB
is separately parameterized in test_job_publication.py.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
import socket
import ssl
import struct
import threading
import time
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import pika
import pytest

from app.services.rabbitmq_queue import RabbitMQQueue
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_job_publication import BODY, post
from test_rabbitmq_publisher import JOB, outcome, publish_compatible, start_if_supported
from test_rabbitmq_publisher import runtime_handshake_holder
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api


def test_dns_tls_handoff_preserves_original_hostname_and_certificate_checks(monkeypatch, tmp_path, runtime_handshake_holder):
    """Inspect actual Pika's TLS handoff; not a server-certificate acceptance test."""
    from pika.adapters.utils.selector_ioloop_adapter import SelectorIOServicesAdapter
    from test_managed_resolver import ChildHarness, managed_module

    children = ChildHarness(managed_module(), monkeypatch, tmp_path, "answers")
    observed, reached = [], threading.Event()
    def inspect_tls(services, protocol_factory, sock, on_done, ssl_context=None, server_hostname=None):
        observed.append((server_hostname, ssl_context.verify_mode, ssl_context.check_hostname))
        reached.set()
        sock.close()
        raise OSError("Owned TLS handoff inspection complete")
    monkeypatch.setattr(SelectorIOServicesAdapter, "create_streaming_connection", inspect_tls)
    peer = runtime_handshake_holder
    queue = RabbitMQQueue(f"amqps://unit:synthetic@original-host.example:{peer.port}/%2F", "jup086-tls")
    try:
        queue.start()
        assert reached.wait(3)
        assert observed == [("original-host.example", ssl.CERT_REQUIRED, True)]
        assert children.markers()[0]["args"][0] == "original-host.example"
        queue.close()
    finally:
        try:
            queue.close()
        finally:
            children.cleanup()


class FrameProxy:
    """Forward complete AMQP frames; optionally withhold confirms and CloseOk.

    The client's actual TuneOk is observed, so idle is measured against the
    negotiated value. Nothing changes the broker's configuration or clock.
    """

    def __init__(self, url, *, lose_ack=False, lose_delivery=False):
        self.target = urlsplit(url)
        self.lose_ack = lose_ack
        self.lose_delivery = lose_delivery
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.sockets = []
        self.threads = []
        self.errors = []
        self.dropped_acks = 0
        self.dropped_close_ok = 0
        self.heartbeats = 0
        self.heartbeat_times = []
        self.first_publish_at = None
        self.negotiated_heartbeat = None
        self.confirms_selected = threading.Event()
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen()
        self.listener.settimeout(0.2)
        credentials = self.target.netloc.rsplit("@", 1)[0]
        self.url = urlunsplit(("amqp", credentials + "@127.0.0.1:" + str(self.listener.getsockname()[1]),
                              self.target.path, "", ""))

    @staticmethod
    def receive(stream, size):
        data = bytearray()
        while len(data) < size:
            part = stream.recv(size - len(data))
            if not part:
                raise EOFError
            data.extend(part)
        return bytes(data)

    def transform(self, packet, *, from_broker):
        frame_type, channel, size = struct.unpack(">BHI", packet[:7])
        assert packet[-1:] == b"\xce" and len(packet) == size + 8
        payload = packet[7:-1]
        method = struct.unpack(">HH", payload[:4]) if frame_type == 1 else None
        with self.lock:
            if from_broker and frame_type == 8:
                self.heartbeats += 1
                self.heartbeat_times.append(time.monotonic())
            if not from_broker and method == (60, 40) and self.first_publish_at is None:
                self.first_publish_at = time.monotonic()
            if not from_broker and method == (10, 31):
                self.negotiated_heartbeat = struct.unpack(">H", payload[-2:])[0]
            if not from_broker and method == (85, 10):
                self.confirms_selected.set()
            if from_broker and self.lose_ack and method == (60, 80):
                self.dropped_acks += 1
                return b""
            if from_broker and self.lose_ack and method in {(10, 51), (20, 41)}:
                self.dropped_close_ok += 1
                return b""
            if not from_broker and self.lose_delivery and (method == (60, 40) or frame_type in {2, 3}):
                return b""
        return packet

    def pump(self, source, target, from_broker):
        try:
            if not from_broker:
                preamble = self.receive(source, 8)
                assert preamble == b"AMQP\x00\x00\x09\x01"
                target.sendall(preamble)
            while not self.stop.is_set():
                header = self.receive(source, 7)
                size = struct.unpack(">I", header[3:])[0]
                assert size <= 16 * 1024 * 1024
                packet = self.transform(header + self.receive(source, size + 1), from_broker=from_broker)
                if packet:
                    target.sendall(packet)
        except (EOFError, ConnectionError, OSError):
            pass
        except Exception as error:
            self.errors.append(type(error).__name__)
        finally:
            for stream in (source, target):
                try:
                    stream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def accept(self):
        while not self.stop.is_set():
            try:
                client, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                server = socket.create_connection((self.target.hostname, self.target.port), timeout=3)
                server.settimeout(None)
            except OSError:
                client.close()
                continue
            with self.lock:
                self.sockets.extend((client, server))
            for source, target, direction in ((client, server, False), (server, client, True)):
                thread = threading.Thread(target=self.pump, args=(source, target, direction))
                self.threads.append(thread)
                thread.start()

    def __enter__(self):
        self.acceptor = threading.Thread(target=self.accept)
        self.acceptor.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.listener.close()
        self.acceptor.join(timeout=4)
        for stream in self.sockets:
            try:
                stream.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            stream.close()
        for thread in self.threads:
            thread.join(timeout=2)
        assert not self.acceptor.is_alive() and not any(thread.is_alive() for thread in self.threads)
        assert self.errors == []


def parameters(url):
    value = pika.URLParameters(url)
    value.socket_timeout, value.stack_timeout = 3, 5
    value.blocked_connection_timeout, value.connection_attempts = 3, 1
    return value


@pytest.fixture
def isolated_rabbit():
    raw = os.environ.get("JUP086_RABBITMQ_TEST_URL")
    if not raw:
        pytest.skip("NOTRUN: orchestrator has not provisioned JUP086_RABBITMQ_TEST_URL")
    parsed = urlsplit(raw)
    assert parsed.scheme == "amqp" and parsed.hostname in {"localhost", "127.0.0.1"}
    assert parsed.port not in {None, 5672} and not parsed.query
    queue_name = "jup086.rf086003." + uuid4().hex
    with pika.BlockingConnection(parameters(raw)) as connection:
        connection.channel().queue_declare(queue=queue_name, durable=True)
    try:
        yield raw, queue_name
    finally:
        with pika.BlockingConnection(parameters(raw)) as connection:
            connection.channel().queue_delete(queue=queue_name)


@contextmanager
def publisher(raw, queue_name):
    queue = RabbitMQQueue(raw, queue_name)
    try:
        start_if_supported(queue)
        yield queue
    finally:
        started = time.monotonic()
        queue.close()
        assert time.monotonic() - started <= 5.5


def take(raw, queue_name):
    with pika.BlockingConnection(parameters(raw)) as connection:
        method, _, body = connection.channel().basic_get(queue=queue_name, auto_ack=True)
        return json.loads(body) if method is not None else None




@pytest.mark.parametrize(
    'tenant_database',
    [
        pytest.param('cockroach', id='cockroach'),
    ],
    indirect=['tenant_database'],
)
def test_same_backend_first_post_idle_request_and_persisted_orphan(api, isolated_rabbit, record_property):
    raw, name = isolated_rabbit
    with FrameProxy(raw) as proxy, publisher(proxy.url, name) as queue:
        api.app.state.queue = queue
        process_id = os.getpid()
        first = post(api)
        assert first.status_code == 202
        assert take(raw, name)["id"] == first.json()["job_id"]
        assert proxy.negotiated_heartbeat == 30
        idle_started = time.monotonic()
        time.sleep(2 * proxy.negotiated_heartbeat + 2)
        idle_seconds = time.monotonic() - idle_started
        assert idle_seconds > 2 * proxy.negotiated_heartbeat
        record_property("negotiated_heartbeat", proxy.negotiated_heartbeat)
        record_property("idle_seconds", idle_seconds)
        # This independent probe can be green while the retained publisher is stale.
        assert queue.ping() is True
        second = post(api)
        saved = rows(api.db, "jobs")
        second_rows = [row for row in saved if row["id"] != first.json()["job_id"]]
        record_property("post_idle_status", second.status_code)
        record_property("post_idle_persisted_status", second_rows[0]["status"] if second_rows else "no-row")
        record_property("broker_heartbeats_forwarded", proxy.heartbeats)
        assert os.getpid() == process_id
        assert second.status_code == 202, "First post-idle request failed despite healthy independent probe; inspect persisted status in JUnit"
        assert take(raw, name)["id"] == second.json()["job_id"]
        assert len(saved) == 2 and all(row["status"] == "queued" for row in saved)


@pytest.mark.parametrize(
    'delivered',
    [
        pytest.param(True, id='True'),
    ],
)
def test_ack_withheld_while_heartbeat_alive_is_bounded_unknown_and_not_replayed(isolated_rabbit, delivered, monkeypatch):
    """Accelerated heartbeat fault; production-default idle coverage is separate."""
    from app.services import rabbitmq_queue as publisher_module

    raw, name = isolated_rabbit
    original_parameters = publisher_module._parameters
    assert original_parameters(raw).heartbeat == 30
    assert publisher_module.CONFIRM_TIMEOUT == 5
    with FrameProxy(raw, lose_ack=True, lose_delivery=not delivered) as proxy, monkeypatch.context() as patch:
        def accelerated_parameters(url):
            value = original_parameters(url)
            assert value.heartbeat == 30
            if url == proxy.url:
                value.heartbeat = 2
            return value

        patch.setattr(publisher_module, "_parameters", accelerated_parameters)
        with publisher(proxy.url, name) as queue:
            started = time.monotonic()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(publish_compatible, queue)
                result = future.result(timeout=12)
            finished = time.monotonic()
            outcome(result, "unknown", "confirm_timeout")
            assert finished - started <= 11
            assert proxy.negotiated_heartbeat == 2
            assert proxy.confirms_selected.is_set() and proxy.heartbeats > 0
            with proxy.lock:
                assert proxy.first_publish_at is not None
                assert any(proxy.first_publish_at <= at <= finished for at in proxy.heartbeat_times)
            assert (proxy.dropped_acks > 0) is delivered
            actual = take(raw, name)
            assert (actual is not None) is delivered
            if delivered:
                assert actual == JOB
            proxy.lose_ack = False
            proxy.lose_delivery = False
            result = publish_compatible(queue, {**JOB, "id": "next-generation"})
            outcome(result, "confirmed")
            assert take(raw, name)["id"] == "next-generation"
            assert take(raw, name) is None, "Unknown delivery was replayed after reconnect"
    assert publisher_module._parameters is original_parameters


def test_real_mandatory_return_beats_ack(isolated_rabbit):
    raw, name = isolated_rabbit
    with publisher(raw, name) as queue:
        outcome(publish_compatible(queue), "confirmed")
        assert take(raw, name) == JOB
        with pika.BlockingConnection(parameters(raw)) as connection:
            connection.channel().queue_delete(queue=name)
        result = publish_compatible(queue, {**JOB, "id": "unroutable"})
        outcome(result, "rejected", "unroutable")


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_same_backend_real_owned_restart_next_http_confirmed_no_replay(api, isolated_rabbit, request, record_property):
    restart = getattr(request.config, "jup086_owned_rabbit_restart", None)
    if restart is None:
        pytest.skip("NOTRUN: orchestrator must supply an audited owned-Rabbit restart hook")
    raw, name = isolated_rabbit
    threads = set(threading.enumerate())
    process_id, app_id = os.getpid(), id(api.app)
    with FrameProxy(raw) as proxy, publisher(proxy.url, name) as queue:
        api.app.state.queue = queue
        owner = queue._thread
        first = post(api)
        assert first.status_code == 202
        first_id = first.json()["job_id"]
        assert take(raw, name)["id"] == first_id
        assert proxy.negotiated_heartbeat == 30
        proxy.lose_ack = True
        uncertain = post(api)
        assert uncertain.status_code == 503
        unknown = next(row for row in rows(api.db, "jobs") if row["id"] != first_id)
        assert unknown["status"] == "publish_unknown" and proxy.dropped_acks == 1
        assert take(raw, name)["id"] == unknown["id"]
        proxy.lose_ack = False
        old_generation = queue._generation
        proof = restart(raw)
        assert proof["container_id"] and proof["before_started_at"] != proof["after_started_at"]
        assert os.getpid() == process_id and id(api.app) == app_id
        assert api.app.state.queue is queue and queue._thread is owner and owner.is_alive()
        next_response = post(api)
        assert next_response.status_code == 202
        next_id = next_response.json()["job_id"]
        delivered = take(raw, name)
        assert (delivered["id"], delivered["tenant_id"], delivered["created_by"]) == (next_id, "tenant-a", "alice")
        assert take(raw, name) is None, "Prior publication replayed after real broker restart"
        saved = rows(api.db, "jobs")
        assert len(saved) == 3
        assert {row["id"]: row["status"] for row in saved} == {
            first_id: "queued", unknown["id"]: "publish_unknown", next_id: "queued"}
        assert all((row["tenant_id"], row["created_by"]) == ("tenant-a", "alice") for row in saved)
        assert queue._generation > old_generation
        record_property("restart_proof", json.dumps(proof))
        record_property("same_backend_pid", process_id)
        record_property("scoped_sql", json.dumps({row["id"]: row["status"] for row in saved}))
    assert queue.publisher_stopped and queue._loop is None and queue._session is None
    assert not queue._resolver.thread.is_alive()
    assert set(threading.enumerate()) <= threads
