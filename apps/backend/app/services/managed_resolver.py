"""Process-wide, two-lane DNS supervisor. Only this thread owns child I/O."""

from collections import deque
import os
from pathlib import Path
import socket
import struct
import subprocess
from subprocess import Popen
import sys
import threading
import time

from pika.adapters.utils.nbio_interface import AbstractIOReference

from app.core.runtime_secrets import StartupError
from .dns_resolver_child import (
    ERROR_CODES, READY_LIMIT, REQUEST_LIMIT, RESULT_LIMIT, decode, encode,
    integer, validate_request, validate_result,
)


_registry_lock = threading.Lock()
_active_service = None
_registered_service = None
_CHILD = Path(__file__).with_name("dns_resolver_child.py").resolve()


def build_child_command():
    try:
        if os.name == "nt":
            interpreter = Path(sys.base_exec_prefix) / "python.exe"
        elif sys.platform.startswith("linux"):
            interpreter = Path(sys.executable).resolve(strict=True)
        else:
            raise ValueError()
        if not interpreter.is_absolute() or not interpreter.is_file() or not _CHILD.is_file():
            raise ValueError()
        return [str(interpreter), "-I", "-S", "-B", str(_CHILD)]
    except Exception:
        raise StartupError("DNS resolver interpreter unavailable.") from None


def _environment():
    if os.name != "nt":
        return {}
    root = os.environ.get("SystemRoot", "")
    if not root or not Path(root).is_absolute() or not (Path(root) / "System32").is_dir():
        raise StartupError("DNS resolver environment unavailable.") from None
    return {"SystemRoot": root}


def _error(code="EAI_FAIL"):
    return socket.gaierror(ERROR_CODES.get(code, socket.EAI_FAIL), "DNS resolution unavailable.")


class _Reference(AbstractIOReference):
    def __init__(self, service, callback, lane, wire, deadline, cleanup_deadline):
        self.service = service
        self.callback = callback
        self.lane = lane
        self.wire = wire
        self.deadline = deadline
        self.cleanup_deadline = cleanup_deadline
        self.state = "WAITING"
        self.cancelled = self.delivered = False
        self.done = threading.Event()
        self.result = None
        self.process = None
        self.launch_deadline = 0.0
        self.ready = self.eof = self.terminating = self.ownership_failed = False
        self.terminate_at = 0.0
        self.exit_deadline = 0.0
        self.offset = 0
        self.buffer = bytearray()
        self.response = None
        self.failure = None

    def cancel(self):
        with self.service.lock:
            if self.cancelled or self.delivered:
                return False
            self.cancelled = True
            self.callback = None
        self.service.wake.set()
        return True

    def dispatch(self):
        with self.service.lock:
            self.service._check_locked()
            if not self.done.is_set() or self.cancelled or self.delivered or self.service.stopping:
                return
            self.delivered = True
            callback, self.callback = self.callback, None
            result, self.result = self.result, None
        callback(result)


class _ProbeLease:
    def __init__(self, service, deadline):
        self.service = service
        self.deadline = deadline
        self.ready = threading.Event()
        self.active = self.released = self.attached = False
        self.started_at = 0.0

    def wait(self):
        self.ready.wait(max(0, self.deadline - time.monotonic()))
        with self.service.lock:
            self.service._check_locked()
            valid = self.active and not self.released and not self.service.stopping and time.monotonic() < self.deadline
        if not valid:
            self.service.release_probe(self)
        return valid


class ResolverSupervisor:
    def __init__(self):
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.thread = None
        self.stopping = self.cleanup_failed = self.closed = False
        self.close_deadline = float("inf")
        self.lanes = {"publisher": None, "probe": None}
        self.probe = None
        self.waiters = deque()
        self.publisher = None
        self.next_lane = "publisher"
        self.environment = None

    def start(self):
        global _active_service
        # Validation precedes admission; this does not resolve or launch anything.
        build_child_command()
        environment = _environment()
        with _registry_lock:
            if _active_service is not None and _active_service is not self:
                raise StartupError("DNS resolver already started.") from None
            with self.lock:
                if self.stopping or self.closed:
                    raise StartupError("DNS resolver is stopped.") from None
                if self.thread is not None:
                    if not self.thread.is_alive():
                        self._fail_locked()
                        raise StartupError("DNS resolver cleanup failed.") from None
                    return
                self.environment = environment
                self.thread = threading.Thread(target=self._run, name="rabbitmq-dns-supervisor", daemon=False)
                _active_service = self
                try:
                    self.thread.start()
                except Exception:
                    self._fail_locked()
                    raise StartupError("DNS resolver could not start.") from None

    def register_publisher(self, owner):
        with self.lock:
            self._check_locked()
            if self.stopping or self.closed or (self.publisher is not None and self.publisher is not owner):
                raise StartupError("RabbitMQ publisher already registered or unavailable.") from None
            self.publisher = owner

    @property
    def retired(self):
        with self.lock:
            return (self.closed and (self.thread is None or not self.thread.is_alive())
                    and (self.publisher is None or self.publisher.publisher_stopped))

    @property
    def available(self):
        with self.lock:
            self._check_locked()
            return self.thread is not None and self.thread.is_alive() and not self.stopping

    def _fail_locked(self):
        self.cleanup_failed = self.stopping = True
        for lease in self.waiters:
            lease.released = True
            lease.ready.set()
        self.waiters.clear()
        for ref in self.lanes.values():
            if ref is not None:
                ref.cancelled = True
                ref.callback = None
        self.wake.set()

    def _check_locked(self):
        now = time.monotonic()
        for ref in self.lanes.values():
            if ref is not None and ((ref.state == "STARTING" and now >= ref.launch_deadline)
                                    or now >= ref.cleanup_deadline):
                self._fail_locked()
                break
        if self.thread is not None and self.thread.ident is not None and not self.thread.is_alive() and not self.closed:
            self._fail_locked()

    def request_probe(self, *, deadline):
        with self.lock:
            self._check_locked()
            self._promote_locked()
            if self.thread is None or self.stopping or deadline <= time.monotonic() or len(self.waiters) >= 4:
                return None
            lease = _ProbeLease(self, deadline)
            self.waiters.append(lease)
            self._promote_locked()
        self.wake.set()
        return lease

    def _promote_locked(self):
        now = time.monotonic()
        retained = deque()
        for lease in self.waiters:
            if lease.released or now >= lease.deadline or self.stopping:
                lease.released = True
                lease.ready.set()
            else:
                retained.append(lease)
        self.waiters = retained
        if self.probe is not None and self.probe.released and self.lanes["probe"] is None:
            self.probe = None
        if not self.stopping and self.probe is None and self.waiters:
            self.probe = self.waiters.popleft()
            self.probe.active = True
            self.probe.started_at = now
            self.probe.ready.set()

    def attach_probe(self, lease):
        with self.lock:
            if self.stopping or lease is not self.probe or lease.released or time.monotonic() >= lease.deadline:
                return False
            lease.attached = True
            return True

    def release_probe(self, lease):
        with self.lock:
            lease.released = True
            lease.attached = False
            lease.ready.set()
            if lease is self.probe and self.lanes["probe"] is not None:
                ref = self.lanes["probe"]
                ref.cancelled = True
                ref.callback = None
            self._promote_locked()
        self.wake.set()

    def resolve(self, host, port, family=0, socktype=0, proto=0, flags=0, *, on_done,
                lane="publisher", probe_lease=None, deadline, cleanup_deadline):
        wire = None
        try:
            query = validate_request(dict(host=host, port=port, family=family, socktype=socktype, proto=proto, flags=flags))
            wire = encode(query, REQUEST_LIMIT)
        except Exception:
            pass
        with self.lock:
            self._check_locked()
            if self.thread is None or self.stopping:
                raise StartupError("DNS resolver cleanup failed or unavailable.") from None
            ref = _Reference(self, on_done, lane, wire, deadline, cleanup_deadline)
            if (wire is None or lane not in self.lanes or self.lanes[lane] is not None
                    or (lane == "probe" and (probe_lease is not self.probe or probe_lease is None
                                            or probe_lease.released))):
                ref.result = _error()
                ref.state = "DONE"
                ref.done.set()
            elif time.monotonic() >= deadline:
                ref.result = _error("EAI_AGAIN")
                ref.state = "DONE"
                ref.done.set()
            else:
                self.lanes[lane] = ref
        self.wake.set()
        return ref

    def stop(self, *, deadline):
        with self.lock:
            self.stopping = True
            self.close_deadline = min(self.close_deadline, deadline)
            for ref in self.lanes.values():
                if ref is not None:
                    ref.cancelled = True
                    ref.callback = None
                    ref.cleanup_deadline = min(ref.cleanup_deadline, self.close_deadline)
            if self.probe is not None and not self.probe.attached:
                self.probe.released = True
            self._promote_locked()
        self.wake.set()

    def close(self, *, deadline):
        self.stop(deadline=deadline)
        thread = self.thread
        if thread is not None and thread.ident is not None and thread is not threading.current_thread():
            # A later caller may observe overdue cleanup completing. It cannot
            # renew any resource deadline or reopen admission after a failure.
            thread.join(max(0, deadline - time.monotonic()))
        with self.lock:
            if (thread is not None and thread.is_alive()) or any(self.lanes.values()) or self.probe is not None:
                self._fail_locked()
                raise StartupError("DNS resolver cleanup failed.") from None
            self.closed = True
        self._unregister()

    def _unregister(self):
        global _active_service
        with _registry_lock:
            if _active_service is self and self.retired:
                _active_service = None

    def _finish(self, ref, result):
        with self.lock:
            ref.state = "DONE"
            ref.result = result
            ref.process = None
            ref.wire = None
            ref.buffer.clear()
            ref.done.set()
            self.lanes[ref.lane] = None
            self._promote_locked()

    def _spawn(self, ref):
        options = dict(shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, bufsize=0, close_fds=True,
                       cwd=str(_CHILD.parent), env=self.environment)
        if os.name == "nt":
            # NO_WINDOW alone still allocates a hidden conhost on Windows.
            # Detached stdio pipes avoid that extra, unowned process entirely.
            options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        try:
            process = Popen(build_child_command(), **options)
            ref.process = process
            with self.lock:
                if time.monotonic() >= ref.launch_deadline:
                    self._fail_locked()
                ref.state = "RUNNING"
            os.set_blocking(process.stdin.fileno(), False)
            os.set_blocking(process.stdout.fileno(), False)
        except Exception:
            if ref.process is None:
                self._finish(ref, _error())
            else:
                ref.failure = "EAI_FAIL"

    def _read(self, ref):
        data = os.read(ref.process.stdout.fileno(), 8192)
        if not data:
            ref.eof = True
            if ref.buffer or ref.response is None:
                raise ValueError()
            ref.exit_deadline = min(time.monotonic() + 0.1, ref.cleanup_deadline - 0.1)
            return
        ref.buffer.extend(data)
        while len(ref.buffer) >= 4:
            limit = RESULT_LIMIT if ref.ready else READY_LIMIT
            size = struct.unpack("!I", ref.buffer[:4])[0]
            if not 0 < size <= limit or ref.response is not None:
                raise ValueError()
            if len(ref.buffer) < size + 4:
                return
            value = decode(bytes(ref.buffer[4:size + 4]))
            del ref.buffer[:size + 4]
            if not ref.ready:
                if not isinstance(value, dict) or set(value) != {"kind", "pid"} or value["kind"] != "ready" or not integer(value["pid"], 1, 2**32 - 1):
                    raise ValueError()
                if value["pid"] != ref.process.pid:
                    ref.ownership_failed = True
                    with self.lock:
                        self._fail_locked()
                    raise ValueError()
                ref.ready = True
            else:
                if ref.offset != len(ref.wire):
                    raise ValueError()
                ref.response = validate_result(value)
        if ref.response is not None and ref.buffer:
            raise ValueError()

    def _cleanup(self, ref, now):
        process = ref.process
        ref.state = "REAPING"
        try:
            status = process.poll()
            if status is None:
                if (ref.eof and not ref.cancelled and not self.stopping and not ref.failure
                        and now < ref.exit_deadline):
                    return
                if not ref.failure and not ref.cancelled and not self.stopping:
                    ref.failure = "EAI_FAIL"
                if not ref.terminating:
                    ref.terminating = True
                    ref.terminate_at = now
                    process.terminate()
                elif now - ref.terminate_at >= 0.1:
                    process.kill()
                return
            process.wait(timeout=0)
            for pipe in (process.stdin, process.stdout):
                if not pipe.closed:
                    pipe.close()
            if ref.ownership_failed:
                return
            result = _error(ref.failure or "EAI_FAIL")
            if not ref.failure and not ref.cancelled and ref.eof and status == 0 and ref.response is not None:
                response = ref.response
                result = response["answers"] if response["kind"] == "ok" else _error(response["code"])
            self._finish(ref, result)
        except Exception:
            with self.lock:
                self._fail_locked()

    def _service(self, ref, now):
        if ref.state == "WAITING":
            if ref.cancelled or self.stopping or now >= ref.deadline:
                self._finish(ref, _error("EAI_AGAIN"))
            return
        if ref.process is None:
            return
        if (not ref.failure and not ref.eof
                and (now >= ref.deadline or (not ref.ready and now >= ref.launch_deadline))):
            ref.failure = "EAI_AGAIN"
        if ref.cancelled or self.stopping or ref.failure or ref.state == "REAPING":
            self._cleanup(ref, now)
            return
        try:
            if not ref.eof:
                try:
                    self._read(ref)
                except BlockingIOError:
                    pass
            # Recheck cancellation after reading ready, before sending any data.
            if ref.ready and not ref.cancelled and not self.stopping and ref.offset < len(ref.wire):
                try:
                    written = os.write(ref.process.stdin.fileno(), ref.wire[ref.offset:ref.offset + 2048])
                    if written <= 0:
                        raise ValueError()
                    ref.offset += written
                    if ref.offset == len(ref.wire):
                        ref.process.stdin.close()
                except BlockingIOError:
                    pass
            if ref.eof:
                self._cleanup(ref, now)
        except Exception:
            ref.failure = "EAI_FAIL"
            self._cleanup(ref, now)

    def _run(self):
        try:
            while True:
                with self.lock:
                    self._check_locked()
                    self._promote_locked()
                    refs = tuple(ref for ref in self.lanes.values() if ref is not None)
                    if self.stopping and not refs and (self.probe is None or not self.probe.attached):
                        self.probe = None
                        self.closed = True
                        return
                # Cleanup always precedes consideration of another spawn.
                for ref in sorted(refs, key=lambda item: not (item.cancelled or item.state == "REAPING" or item.failure)):
                    self._service(ref, time.monotonic())
                with self.lock:
                    self._check_locked()
                    chosen = None
                    if not self.stopping and not any(ref is not None and ref.state == "REAPING"
                                                     for ref in self.lanes.values()):
                        order = (self.next_lane, "probe" if self.next_lane == "publisher" else "publisher")
                        for lane in order:
                            ref = self.lanes[lane]
                            if ref is not None and ref.state == "WAITING" and not ref.cancelled:
                                chosen = ref
                                ref.state = "STARTING"
                                ref.launch_deadline = min(time.monotonic() + 0.5, ref.deadline)
                                self.next_lane = "probe" if lane == "publisher" else "publisher"
                                break
                if chosen is not None:
                    self._spawn(chosen)
                self.wake.wait(0.02)
                self.wake.clear()
        except BaseException:
            with self.lock:
                self._fail_locked()
            # Retain this owner and its records; never replace it after a fault.
            while True:
                for ref in tuple(self.lanes.values()):
                    if ref is not None:
                        self._service(ref, time.monotonic())
                with self.lock:
                    self._promote_locked()
                    if not any(self.lanes.values()) and (self.probe is None or not self.probe.attached):
                        self.probe = None
                        self.closed = True
                        return
                self.wake.wait(0.02)
                self.wake.clear()


def get_resolver():
    global _active_service, _registered_service
    with _registry_lock:
        if _active_service is not None and _active_service.retired:
            _active_service = None
        if _active_service is not None:
            return _active_service
        if _registered_service is None or _registered_service.retired:
            _registered_service = ResolverSupervisor()
        return _registered_service
