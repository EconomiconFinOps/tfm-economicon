import json
import logging
import threading
import time
from dataclasses import dataclass, field

import pika
from pika.adapters.select_connection import IOLoop, SelectConnection
from pika.adapters.utils.nbio_interface import AbstractStreamProtocol
from pika.adapters.utils.selector_ioloop_adapter import SelectorIOServicesAdapter

from app.core.runtime_secrets import StartupError
from app.services.managed_resolver import get_resolver


CAPACITY = 16
TICKET_TIMEOUT = 10.0
CONFIRM_TIMEOUT = 5.0
SETUP_TIMEOUT = 5.0
TICK = 0.1
SHUTDOWN_TIMEOUT = 5.0
BACKOFF = (1.0, 2.0, 4.0, 5.0)


@dataclass(frozen=True)
class PublishResult:
    outcome: str
    code: str

    def __bool__(self):
        raise TypeError("Inspect the explicit publication outcome.")


@dataclass(eq=False)
class _Ticket:
    deadline: float
    event: threading.Event = field(default_factory=threading.Event)
    phase: str = "RESERVED"
    body: str | None = field(default=None, repr=False)
    result: PublishResult | None = None
    setups: int = 0
    generation: int = 0
    sequence: int = 0
    confirm_deadline: float = 0.0


class _PikaLogFilter(logging.Filter):
    def filter(self, record):
        # Pika diagnostics may embed broker text, frames, URLs and cause chains.
        record.msg = "rabbitmq_dependency_event"
        record.args = ()
        record.exc_info = record.exc_text = record.stack_info = None
        return True


_log_filter = _PikaLogFilter()
_log_lock = threading.Lock()


def _sanitize_pika_logs():
    with _log_lock:
        for name in tuple(logging.Logger.manager.loggerDict):
            if name == "pika" or name.startswith("pika."):
                logging.getLogger(name).addFilter(_log_filter)


def _parameters(url):
    parameters = pika.URLParameters(url)
    parameters.heartbeat = 30
    parameters.socket_timeout = 3
    parameters.stack_timeout = 5
    parameters.blocked_connection_timeout = 3
    parameters.connection_attempts = 1
    return parameters


class _AbortProtocol(AbstractStreamProtocol):
    def __init__(self, original, services):
        self.original = original
        self.services = services
        self.transport = None
        self.external_abort = False

    def connection_made(self, transport):
        # Capture before forwarding: even a failing callback must be cleanable.
        self.transport = transport
        self.services.streams.add(self)
        result = self.original.connection_made(transport)
        if self.services.stopping:
            self.external_abort = True
            transport.abort()
        return result

    def data_received(self, data):
        return self.original.data_received(data)

    def eof_received(self):
        return self.original.eof_received()

    def connection_lost(self, error):
        if self.external_abort and error is None:
            error = ConnectionAbortedError("Publisher transport stopped")
        try:
            return self.original.connection_lost(error)
        finally:
            self.services.streams.discard(self)
            self.transport = None


class _CapturingAdapter(SelectorIOServicesAdapter):
    def __init__(self, loop, resolver, dns_deadline, cleanup_deadline, probe_lease=None):
        super().__init__(loop)
        self.streams = set()
        self.stopping = False
        self.resolver = resolver
        self.dns_deadline = dns_deadline
        self.cleanup_deadline = cleanup_deadline
        self.probe_lease = probe_lease
        self.references = set()

    def getaddrinfo(self, host, port, on_done, family=0, socktype=0, proto=0, flags=0):
        # This internal Pika override is the approved, version-tested boundary.
        def completed(result):
            if not self.stopping and self.resolver.available:
                on_done(result)

        reference = self.resolver.resolve(
            host, port, family, socktype, proto, flags, on_done=completed,
            lane="probe" if self.probe_lease is not None else "publisher",
            probe_lease=self.probe_lease, deadline=self.dns_deadline,
            cleanup_deadline=self.cleanup_deadline,
        )
        self.references.add(reference)
        return reference

    def poll(self):
        for reference in tuple(self.references):
            if self.stopping:
                reference.cancel()
            else:
                reference.dispatch()
            if reference.done.is_set():
                self.references.discard(reference)

    def create_streaming_connection(self, protocol_factory, sock, on_done,
                                    ssl_context=None, server_hostname=None):
        def completed(result):
            if isinstance(result, BaseException):
                on_done(result)
            else:
                transport, delegate = result
                on_done((transport, delegate.original))

        return super().create_streaming_connection(
            lambda: _AbortProtocol(protocol_factory(), self), sock, completed,
            ssl_context=ssl_context, server_hostname=server_hostname,
        )


class _Session:
    """Connection and captured transports, accessed only by their loop owner."""

    def __init__(self, loop, on_open, on_end, resolver, dns_deadline, cleanup_deadline,
                 probe_lease=None):
        self.services = _CapturingAdapter(loop, resolver, dns_deadline, cleanup_deadline, probe_lease)
        self.connection = None
        self.on_open = on_open
        self.on_end = on_end
        self.ended = False

    def start(self, parameters):
        self.connection = SelectConnection(
            parameters, custom_ioloop=self.services,
            on_open_callback=self.on_open,
            on_open_error_callback=self._ended,
            on_close_callback=self._ended,
        )

    def _ended(self, connection, error):
        if not self.ended:
            self.ended = True
            self.on_end()

    @property
    def pika_closed(self):
        return (not self.services.streams
                and (self.connection is None or self.connection.is_closed))

    @property
    def finished(self):
        return (self.pika_closed
                and all(reference.done.is_set() for reference in self.services.references))

    def abort(self):
        self.services.stopping = True
        for reference in tuple(self.services.references):
            reference.cancel()
        streams = tuple(self.services.streams)
        for delegate in streams:
            if not delegate.external_abort:
                delegate.external_abort = True
                delegate.transport.abort()
        connection = self.connection
        if not streams and connection is not None and not connection.is_closed and not connection.is_closing:
            connection.close()


def _drain(loop, session, deadline):
    """Allow public close/lost callbacks to finish before disposing the loop."""
    if session.finished:
        return True
    session.abort()

    def check():
        session.services.poll()
        if session.finished or time.monotonic() >= deadline:
            loop.stop()
        else:
            loop.call_later(0.01, check)

    loop.call_later(0, check)
    loop.start()
    return session.finished


class RabbitMQQueue:
    def __init__(self, rabbitmq_url: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self._lock = threading.Lock()
        self._tickets = {}
        self._started = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._closing = False
        self._failed = False
        self._cleanup_failed = False
        self._generation = 0
        self._connecting = False
        self._ready = False
        self._retiring = False
        self._inflight = None
        self._loop = None
        self._session = None
        self._channel = None
        self._sequence = 0
        self._blocked_at = None
        self._backoff = 0
        self._resolver = None
        self._owns_resolver = False
        self._close_deadline = float("inf")
        self._pika_cleanup_complete = threading.Event()
        self._pika_cleanup_complete.set()

    @property
    def publisher_stopped(self):
        # Registry readers use owner-recorded cleanup proof, never Pika state.
        return (self._closing and (self._thread is None or not self._thread.is_alive())
                and self._pika_cleanup_complete.is_set())

    def start(self) -> None:
        with self._lock:
            if self._closing:
                raise StartupError("RabbitMQ publisher is stopped.")
            if self._thread is None:
                resolver = get_resolver()
                resolver.register_publisher(self)
                self._resolver = resolver
                self._owns_resolver = True
                resolver.start()
                self._thread = threading.Thread(target=self._run, name="rabbitmq-publisher", daemon=False)
                try:
                    self._thread.start()
                except Exception:
                    self._failed = True
                    raise StartupError("RabbitMQ publisher could not start.") from None
        if not self._started.wait(1) or self._failed or not self._thread.is_alive():
            with self._lock:
                self._closing = True
            self._wake.set()
            raise StartupError("RabbitMQ publisher could not start.") from None

    def _finish(self, ticket, outcome, code):
        # All ticket state and completion paths share _lock.
        if ticket.result is None:
            ticket.result = PublishResult(outcome, code)
            ticket.body = None
            self._tickets.pop(ticket, None)
            ticket.event.set()

    def _expire(self, now):
        for ticket in tuple(self._tickets):
            if ticket.phase == "IN_FLIGHT":
                if now >= ticket.confirm_deadline:
                    self._finish(ticket, "unknown", "confirm_timeout")
            elif now >= ticket.deadline:
                self._finish(ticket, "not_sent", "deadline_before_send")

    def _unavailable(self):
        for ticket in tuple(self._tickets):
            sent = ticket.phase == "IN_FLIGHT"
            self._finish(ticket, "unknown" if sent else "not_sent",
                         "connection_lost" if sent else "owner_unavailable")

    def reserve(self):
        with self._lock:
            self._expire(time.monotonic())
            if self._closing:
                return PublishResult("not_sent", "stopping")
            if (self._failed or self._thread is None or not self._thread.is_alive()
                    or not self._resolver.available):
                self._unavailable()
                return PublishResult("not_sent", "owner_unavailable")
            if len(self._tickets) >= CAPACITY:
                return PublishResult("not_sent", "capacity")
            ticket = _Ticket(time.monotonic() + TICKET_TIMEOUT)
            ticket.setups = int(self._connecting)
            self._tickets[ticket] = None
            return ticket

    def cancel(self, reservation) -> None:
        with self._lock:
            if reservation in self._tickets:
                sent = reservation.phase == "IN_FLIGHT"
                self._finish(reservation, "unknown" if sent else "not_sent",
                             "cancelled_in_flight" if sent else "deadline_before_send")
        self._wake.set()

    def publish(self, payload: dict, *, reservation) -> PublishResult:
        with self._lock:
            if not isinstance(reservation, _Ticket):
                return PublishResult("not_sent", "owner_unavailable")
            if reservation.result is not None:
                return reservation.result
            if reservation not in self._tickets or reservation.phase != "RESERVED":
                raise ValueError("Invalid publisher reservation.")
            reservation.phase = "SERIALIZING"
        try:
            body = json.dumps(payload)
        except Exception:
            with self._lock:
                self._finish(reservation, "not_sent", "serialization_failed")
                return reservation.result
        with self._lock:
            self._expire(time.monotonic())
            if reservation.result is None:
                reservation.body = body
                reservation.phase = "READY_TO_SEND"
        del body
        self._wake.set()
        while not reservation.event.wait(TICK):
            with self._lock:
                self._expire(time.monotonic())
                if self._failed or not self._thread.is_alive():
                    self._unavailable()
        return reservation.result

    def close(self) -> None:
        with self._lock:
            self._close_deadline = min(self._close_deadline, time.monotonic() + SHUTDOWN_TIMEOUT)
            deadline = self._close_deadline
            self._closing = True
            for ticket in tuple(self._tickets):
                sent = ticket.phase == "IN_FLIGHT"
                self._finish(ticket, "unknown" if sent else "not_sent",
                             "shutdown_in_flight" if sent else "stopping")
            thread = self._thread
        if self._owns_resolver:
            self._resolver.stop(deadline=deadline)
        self._wake.set()
        if thread is not None and thread.ident is not None and thread is not threading.current_thread():
            thread.join(max(0, deadline - time.monotonic()))
        if self._owns_resolver:
            self._resolver.close(deadline=deadline)
        if (self._owns_resolver and not self.publisher_stopped) or self._cleanup_failed:
            raise StartupError("RabbitMQ publisher cleanup failed.") from None

    def _active(self, generation):
        return generation == self._generation and not self._retiring and not self._closing

    def _callback(self, generation, function, *args):
        if self._active(generation):
            try:
                function(generation, *args)
            except Exception:
                self._retire()

    def _opened(self, generation, connection):
        connection.add_on_connection_blocked_callback(
            lambda *args: self._callback(generation, self._blocked, True))
        connection.add_on_connection_unblocked_callback(
            lambda *args: self._callback(generation, self._blocked, False))
        connection.channel(on_open_callback=lambda channel: self._callback(generation, self._channel_opened, channel))

    def _channel_opened(self, generation, channel):
        self._channel = channel
        channel.add_on_close_callback(lambda *args: self._callback(generation, self._channel_closed))
        channel.add_on_return_callback(lambda *args: self._callback(generation, self._returned))
        channel.queue_declare(queue=self.queue_name, durable=True,
                              callback=lambda frame: self._callback(generation, self._declared))

    def _channel_closed(self, generation):
        self._retire()

    def _declared(self, generation):
        self._channel.confirm_delivery(
            lambda frame: self._callback(generation, self._confirmed, frame),
            callback=lambda frame: self._callback(generation, self._selected),
        )

    def _selected(self, generation):
        if time.monotonic() >= self._setup_deadline:
            self._retire()
            return
        with self._lock:
            self._ready = True
            self._connecting = False
        self._backoff = 0

    def _blocked(self, generation, blocked):
        self._blocked_at = time.monotonic() if blocked else None

    def _confirmed(self, generation, frame):
        method = frame.method
        with self._lock:
            self._expire(time.monotonic())
            ticket = self._inflight
            if ticket is None or ticket.result is not None or ticket.generation != generation:
                return
            tag = method.delivery_tag
            matches = tag == ticket.sequence or (
                method.multiple and (tag == 0 or ticket.sequence <= tag <= self._sequence))
            if not matches:
                return
            if isinstance(method, pika.spec.Basic.Ack):
                self._finish(ticket, "confirmed", "confirmed")
                self._inflight = None
            elif isinstance(method, pika.spec.Basic.Nack):
                self._finish(ticket, "rejected", "broker_nack")
        if isinstance(method, pika.spec.Basic.Nack):
            self._retire()

    def _returned(self, generation):
        with self._lock:
            self._expire(time.monotonic())
            if self._inflight is not None and self._inflight.generation == generation:
                self._finish(self._inflight, "rejected", "unroutable")
        self._retire()

    def _retire(self):
        if self._retiring:
            return
        self._retiring = True
        self._retire_deadline = min(self._close_deadline,
                                    time.monotonic() + 4 if self._ready else self._setup_deadline)
        with self._lock:
            self._ready = self._connecting = False
            if self._inflight is not None:
                self._finish(self._inflight, "unknown", "connection_lost")
            for ticket in tuple(self._tickets):
                if ticket.phase != "IN_FLIGHT" and ticket.setups >= 2:
                    self._finish(ticket, "not_sent", "connect_failed")
        self._session.abort()

    def _send(self):
        with self._lock:
            now = time.monotonic()
            self._expire(now)
            if self._closing or self._inflight is not None:
                return
            ticket = next((item for item in self._tickets if item.phase == "READY_TO_SEND"), None)
            if ticket is None:
                return
            # This is the send boundary; every subsequent uncertain failure is unknown.
            ticket.phase = "IN_FLIGHT"
            ticket.generation = self._generation
            self._sequence += 1
            ticket.sequence = self._sequence
            ticket.confirm_deadline = min(ticket.deadline, now + CONFIRM_TIMEOUT)
            self._inflight = ticket
            body, ticket.body = ticket.body, None
        try:
            self._channel.basic_publish(
                exchange="", routing_key=self.queue_name, body=body,
                properties=pika.BasicProperties(delivery_mode=2), mandatory=True,
            )
        except Exception:
            self._retire()

    def _tick(self):
        self._session.services.poll()
        now = time.monotonic()
        with self._lock:
            self._expire(now)
            terminal_send = self._inflight is not None and self._inflight.result is not None
        if (self._closing or not self._resolver.available or terminal_send
                or (not self._ready and now >= self._setup_deadline - 0.5)
                or (self._blocked_at is not None and now - self._blocked_at >= 3)):
            self._retire()
        if self._retiring:
            self._retire_deadline = min(self._retire_deadline, self._close_deadline)
            if self._session.finished or now >= self._retire_deadline:
                if not self._session.finished:
                    self._cleanup_failed = True
                self._loop.stop()
                return
        elif self._ready and self._blocked_at is None:
            self._send()
        delay = TICK
        with self._lock:
            for ticket in self._tickets:
                due = ticket.confirm_deadline if ticket.phase == "IN_FLIGHT" else ticket.deadline
                delay = min(delay, max(0, due - time.monotonic()))
        if not self._ready and not self._retiring:
            delay = min(delay, max(0, self._setup_deadline - 0.5 - time.monotonic()))
        self._loop.call_later(delay, self._tick)

    def _run(self):
        try:
            _sanitize_pika_logs()
            parameters = _parameters(self.rabbitmq_url)
            while not self._closing and self._resolver.available:
                self._pika_cleanup_complete.clear()
                self._loop = IOLoop()
                self._started.set()
                with self._lock:
                    self._generation += 1
                    self._connecting = True
                    for ticket in self._tickets:
                        ticket.setups += 1
                    self._inflight = None
                generation = self._generation
                self._retiring = self._ready = False
                self._blocked_at = self._channel = None
                self._sequence = 0
                self._setup_deadline = time.monotonic() + SETUP_TIMEOUT
                self._session = _Session(
                    self._loop, lambda connection: self._callback(generation, self._opened, connection),
                    self._retire, self._resolver, self._setup_deadline - 2.5,
                    self._setup_deadline - 2,
                )
                try:
                    try:
                        self._session.start(parameters)
                    except Exception:
                        self._retire()
                    self._loop.call_later(0, self._tick)
                    self._loop.start()
                finally:
                    drain_deadline = time.monotonic() + 4
                    try:
                        self._retire()
                        drain_deadline = min(drain_deadline, self._retire_deadline, self._close_deadline)
                        if not _drain(self._loop, self._session, drain_deadline):
                            self._cleanup_failed = True
                    except BaseException:
                        self._cleanup_failed = True
                        raise
                    finally:
                        try:
                            self._loop.close()
                            self._loop = None
                            if self._session.pika_closed:
                                self._pika_cleanup_complete.set()
                        except BaseException:
                            self._cleanup_failed = True
                            raise
                if self._cleanup_failed:
                    raise RuntimeError()
                until = time.monotonic() + BACKOFF[self._backoff]
                self._backoff = min(self._backoff + 1, len(BACKOFF) - 1)
                while not self._closing and self._resolver.available and time.monotonic() < until:
                    with self._lock:
                        self._expire(time.monotonic())
                    self._wake.wait(min(TICK, max(0, until - time.monotonic())))
                    self._wake.clear()
        except BaseException:
            with self._lock:
                self._failed = True
                self._unavailable()
        finally:
            with self._lock:
                self._connecting = self._ready = False
                self._unavailable()
                self._inflight = None
            if self._pika_cleanup_complete.is_set():
                self._session = self._channel = None
            self._started.set()

    def ping(self) -> bool:
        # A probe owns its own connection and loop entirely on this calling thread.
        deadline = time.monotonic() + SETUP_TIMEOUT
        if self._closing:
            return False
        resolver = get_resolver()
        lease = resolver.request_probe(deadline=deadline)
        if lease is None or not lease.wait():
            return False
        if not resolver.attach_probe(lease):
            resolver.release_probe(lease)
            return False
        loop = session = None
        loop_clean = True
        healthy = False
        done = False
        try:
            _sanitize_pika_logs()
            parameters = _parameters(self.rabbitmq_url)
            loop = IOLoop()
            dns_deadline = min(lease.started_at + 2.5, deadline - 1)

            def declared(frame):
                nonlocal healthy, done
                healthy = time.monotonic() < deadline - 0.5 and resolver.available
                done = True

            def channel_opened(channel):
                channel.queue_declare(queue=self.queue_name, durable=True, callback=declared)

            def opened(connection):
                connection.channel(on_open_callback=channel_opened)

            def ended():
                nonlocal done
                done = True

            session = _Session(loop, opened, ended, resolver, dns_deadline,
                               min(dns_deadline + 0.5, deadline - 0.5), lease)

            def tick():
                nonlocal healthy
                session.services.poll()
                now = time.monotonic()
                limit = min(deadline, resolver.close_deadline)
                if now >= limit:
                    healthy = False
                    loop.stop()
                    return
                if done or self._closing or not resolver.available or now >= limit - 0.5:
                    if not done or self._closing or not resolver.available:
                        healthy = False
                    session.abort()
                    if session.finished:
                        loop.stop()
                        return
                loop.call_later(min(TICK, max(0, limit - now)), tick)

            if time.monotonic() >= dns_deadline or not resolver.available:
                return False
            session.start(parameters)
            loop.call_later(0, tick)
            loop.start()
        except Exception:
            healthy = False
        finally:
            if loop is not None:
                try:
                    if session is not None and not _drain(loop, session, min(deadline, resolver.close_deadline)):
                        healthy = False
                except Exception:
                    healthy = False
                finally:
                    try:
                        loop.close()
                    except Exception:
                        loop_clean = False
                        healthy = False
            if (not loop_clean or (session is not None and (session.services.streams
                    or (session.connection is not None and not session.connection.is_closed)))):
                with resolver.lock:
                    resolver._fail_locked()
            else:
                resolver.release_probe(lease)
        return healthy
