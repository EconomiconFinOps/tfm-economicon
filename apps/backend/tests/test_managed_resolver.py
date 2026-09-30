"""DNS addendum contract tests; tentative internal API is documented in handoff."""
from contextlib import contextmanager
import importlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading
import time

from pika.adapters.utils.nbio_interface import AbstractIOReference
import pytest

from app.core.runtime_secrets import StartupError


CHILD = Path(__file__).parents[1] / "app/services/dns_resolver_child.py"
FIXTURE = Path(__file__).parent / "fixtures/dns_child_fixture.py"
MODULE = "app.services.managed_resolver"
REQUEST = {"host": "127.0.0.1", "port": 5672, "family": socket.AF_UNSPEC,
           "socktype": socket.SOCK_STREAM, "proto": socket.IPPROTO_TCP,
           "flags": socket.AI_NUMERICHOST}


def managed_module():
    if importlib.util.find_spec(MODULE) is None:
        pytest.fail("FUTURE_ENTRYPOINT_ABSENT: managed_resolver; not semantic Red", pytrace=False)
    module = importlib.import_module(MODULE)
    missing = [name for name in ("ResolverSupervisor", "get_resolver", "build_child_command", "Popen")
               if not hasattr(module, name)]
    assert not missing, "FUTURE_ENTRYPOINT_ABSENT: " + ", ".join(missing)
    return module


def wait_until(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        threading.Event().wait(0.01)
    assert predicate(), "Bounded observation deadline expired"


def frame(value):
    raw = json.dumps(value).encode("utf-8")
    return struct.pack("!I", len(raw)) + raw


def frames(wire):
    values = []
    while wire:
        assert len(wire) >= 4
        size = struct.unpack("!I", wire[:4])[0]
        assert size <= 65536 and len(wire) >= size + 4
        values.append(json.loads(wire[4:4 + size]))
        wire = wire[4 + size:]
    return values


def child_environment():
    return {"SystemRoot": os.environ["SystemRoot"]} if os.name == "nt" else {}


def environment_keys(environment):
    return sorted(key.upper() if os.name == "nt" else key for key in environment)


def base_interpreter():
    return Path(sys.base_exec_prefix) / "python.exe" if os.name == "nt" else Path(sys.executable).resolve(strict=True)


def process_parents():
    """Read-only OS census, not a claim based only on the child's ready frame."""
    if os.name != "nt":
        result = {}
        for path in Path("/proc").glob("[0-9]*/stat"):
            try:
                result[int(path.parent.name)] = int(path.read_text().rpartition(")")[2].split()[1])
            except (FileNotFoundError, ProcessLookupError):
                pass
        return result
    import ctypes
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD), ("pid", wintypes.DWORD),
                    ("heap", ctypes.c_size_t), ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                    ("parent", wintypes.DWORD), ("priority", wintypes.LONG), ("flags", wintypes.DWORD),
                    ("exe", wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        function = getattr(kernel, name)
        function.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
        function.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    assert snapshot != ctypes.c_void_p(-1).value
    try:
        entry = Entry(size=ctypes.sizeof(Entry))
        result = {}
        valid = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while valid:
            result[int(entry.pid)] = int(entry.parent)
            valid = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        return result
    finally:
        kernel.CloseHandle(snapshot)


class ChildHarness:
    """Real OS children; only command selection and explicit OS faults are doubled."""
    def __init__(self, module, monkeypatch, directory, mode):
        self.processes, self.launches = [], []
        self.directory = directory
        directory.mkdir(exist_ok=True)
        original = module.build_child_command
        real_popen = subprocess.Popen

        def command():
            argv = list(original())
            assert Path(argv[-1]).resolve() == CHILD.resolve()
            return argv[:-1] + [str(FIXTURE.resolve()), str(CHILD.resolve()), mode, str(directory)]

        def popen(argv, **kwargs):
            previous = [p.pid for p in self.processes if p.returncode is None
                        or not p.stdin.closed or not p.stdout.closed]
            process = real_popen(argv, **kwargs)
            self.processes.append(process)
            self.launches.append({"argv": argv, "options": kwargs, "previous_unreaped": previous,
                                  "thread": threading.current_thread()})
            return process

        monkeypatch.setattr(module, "build_child_command", command)
        monkeypatch.setattr(module, "Popen", popen)

    def markers(self):
        records = []
        for path in self.directory.glob("*.json"):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return records

    def cleanup(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            else:
                process.wait(timeout=0)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        assert all(p.returncode is not None for p in self.processes)


@contextmanager
def resolver_runtime(monkeypatch, tmp_path, mode="answers"):
    module = managed_module()
    existing = set(threading.enumerate())
    with monkeypatch.context() as patch:
        children = ChildHarness(module, patch, tmp_path, mode)
        service = module.ResolverSupervisor()
        service.start()
        try:
            yield module, service, children
        finally:
            try:
                service.close(deadline=time.monotonic() + 5)
            finally:
                children.cleanup()
            assert set(threading.enumerate()) <= existing, "Supervisor/helper survived test cleanup"


def resolve(service, callback, lane="publisher", lease=None, **changes):
    query = {**REQUEST, **changes}
    now = time.monotonic()
    return service.resolve(**query, on_done=callback, lane=lane, probe_lease=lease,
                           deadline=now + 2.5, cleanup_deadline=now + 3)


def deliver(reference, values, timeout=3.5):
    def dispatch():
        reference.dispatch()
        return bool(values)
    wait_until(dispatch, timeout)








def test_real_blocked_child_has_expected_os_pid_no_descendants_and_shared_close_budget(monkeypatch, tmp_path):
    with resolver_runtime(monkeypatch, tmp_path, "block") as (_, service, children):
        lease = service.request_probe(deadline=time.monotonic() + 5)
        assert lease.wait()
        refs = [resolve(service, lambda result: None),
                resolve(service, lambda result: None, lane="probe", lease=lease)]
        wait_until(lambda: len(children.markers()) == 2)
        parents = process_parents()
        child_pids = {process.pid for process in children.processes}
        assert {record["pid"] for record in children.markers()} == child_pids
        assert all(parents[pid] == os.getpid() for pid in child_pids)
        assert not any(parent in child_pids for parent in parents.values())
        started = time.monotonic()
        service.close(deadline=started + 5)
        assert time.monotonic() - started <= 5.5
        assert not child_pids.intersection(process_parents())
        assert all(process.returncode is not None and process.stdin.closed and process.stdout.closed
                   for process in children.processes)
        assert not (tmp_path / "release").exists()
        for reference in refs:
            reference.dispatch()


def test_real_child_order_ipv4_ipv6_pid_environment_and_owner_callback(monkeypatch, tmp_path):
    monkeypatch.setenv("DNS_TEST_SECRET", "dns-private-marker")
    with resolver_runtime(monkeypatch, tmp_path) as (_, service, children):
        values, callers = [], []
        reference = resolve(service, lambda result: (values.append(result), callers.append(threading.get_ident())))
        assert isinstance(reference, AbstractIOReference)
        deliver(reference, values)
        process = children.processes[0]
        assert values == [[(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "v4.example", ("127.0.0.1", 5672)),
                           (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "v6.example", ("::1", 5672, 7, 3))]]
        assert callers == [threading.get_ident()]
        assert process.returncode == 0 and process.stdin.closed and process.stdout.closed
        marker = children.markers()[0]
        assert marker["pid"] == process.pid and marker["ppid"] == os.getpid()
        assert marker["app_modules"] == [] and not marker["secret_in_env"]
        runtime_keys = environment_keys(marker["env_keys"])
        if os.name == "posix" and "LC_CTYPE" in runtime_keys:
            # CPython may coerce the Unix C locale after the empty-env spawn.
            assert marker["lc_ctype"] in {"C.UTF-8", "C.utf8", "UTF-8"}
            runtime_keys.remove("LC_CTYPE")
        assert runtime_keys == environment_keys(child_environment())
        options = children.launches[0]["options"]
        assert environment_keys(options["env"]) == environment_keys(child_environment())
        assert list(options["env"].values()) == list(child_environment().values())
        assert options["shell"] is False
        assert options["close_fds"] is True and options["bufsize"] == 0
        assert options["stdin"] == subprocess.PIPE and options["stdout"] == subprocess.PIPE
        assert options["stderr"] == subprocess.DEVNULL
        if os.name == "nt":
            assert options["creationflags"] & subprocess.CREATE_NO_WINDOW
        assert "dns-private-marker" not in repr(children.launches)
        assert len({item["thread"] for item in children.launches}) == 1
        assert not children.launches[0]["thread"].daemon
        reference.dispatch()
        assert len(values) == 1 and reference.cancel() is False




@pytest.mark.parametrize(
    'mode',
    [
        pytest.param('malformed', id='malformed'),
        pytest.param('unknown-error', id='unknown-error'),
        pytest.param('oversize', id='oversize'),
    ],
)
def test_invalid_child_output_is_reaped_and_only_fixed_gaierror_delivered(monkeypatch, tmp_path, caplog, mode):
    with resolver_runtime(monkeypatch, tmp_path, mode) as (_, service, children):
        values = []
        reference = resolve(service, values.append)
        deliver(reference, values)
        assert len(values) == 1 and isinstance(values[0], socket.gaierror)
        assert values[0].errno == socket.EAI_FAIL
        assert "dns-private-marker" not in str(values[0]) + caplog.text
        assert values[0].__cause__ is None and values[0].__context__ is None
        assert all(p.returncode is not None and p.stdin.closed and p.stdout.closed for p in children.processes)




def test_two_lanes_fifo_four_waiters_and_one_supervisor(monkeypatch, tmp_path):
    with resolver_runtime(monkeypatch, tmp_path, "block") as (_, service, children):
        active = service.request_probe(deadline=time.monotonic() + 5)
        assert active is not None and active.wait() is True
        waiting = [service.request_probe(deadline=time.monotonic() + 5) for _ in range(4)]
        assert all(lease is not None for lease in waiting)
        before = time.monotonic()
        assert service.request_probe(deadline=time.monotonic() + 5) is None
        assert time.monotonic() - before < 0.1
        calls = []
        pub = resolve(service, calls.append)
        probe = resolve(service, calls.append, lane="probe", lease=active)
        wait_until(lambda: len(children.markers()) == 2)
        assert len(children.processes) == 2 and len({item["thread"] for item in children.launches}) == 1
        assert all(not item.ready.is_set() for item in waiting)
        assert pub.cancel() is True and probe.cancel() is True
        wait_until(lambda: all(p.returncode is not None and p.stdout.closed for p in children.processes))
        service.release_probe(active)
        for index, lease in enumerate(waiting):
            assert lease.wait() is True
            assert all(not later.ready.is_set() for later in waiting[index + 1:])
            service.release_probe(lease)
        pub.dispatch()
        probe.dispatch()
        assert calls == [] and pub.cancel() is False


@pytest.mark.parametrize(
    'phase',
    [
        pytest.param('result-ready', id='result-ready'),
    ],
)
def test_cancel_wins_before_delivery_without_late_callback_or_early_slot_reuse(monkeypatch, tmp_path, phase):
    with resolver_runtime(monkeypatch, tmp_path, "block" if phase == "running" else "answers") as (_, service, children):
        values = []
        reference = resolve(service, values.append)
        wait_until(lambda: bool(children.markers()))
        if phase == "result-ready":
            wait_until(lambda: children.processes[0].returncode is not None and children.processes[0].stdout.closed)
        assert reference.cancel() is True and reference.cancel() is False
        wait_until(lambda: children.processes[0].returncode is not None and children.processes[0].stdout.closed)
        reference.dispatch()
        assert values == []
        assert reference.done.wait(1), "Reaped lookup did not finish releasing its lane"
        replacement = resolve(service, values.append)
        wait_until(lambda: len(children.launches) == 2)
        assert children.launches[1]["previous_unreaped"] == []
        replacement.cancel()


def test_timeout_reaps_before_eai_again_and_waiting_probe_deadline_is_not_reset(monkeypatch, tmp_path):
    with resolver_runtime(monkeypatch, tmp_path, "block") as (_, service, children):
        active = service.request_probe(deadline=time.monotonic() + 5)
        assert active.wait()
        queued = service.request_probe(deadline=time.monotonic() + 0.15)
        started = time.monotonic()
        assert queued.wait() is False and time.monotonic() - started < 0.5
        values = []
        reference = resolve(service, values.append)
        deliver(reference, values, timeout=3.3)
        assert isinstance(values[0], socket.gaierror) and values[0].errno == socket.EAI_AGAIN
        assert children.processes[0].returncode is not None and children.processes[0].stdout.closed
        service.release_probe(active)


def test_stalled_popen_retains_supervisor_and_slot_until_late_return_is_reaped(monkeypatch, tmp_path):
    with resolver_runtime(monkeypatch, tmp_path, "block") as (module, service, children):
        entered, release = threading.Event(), threading.Event()
        real_launch = module.Popen
        def stalled(*args, **kwargs):
            entered.set()
            assert release.wait(3), "Test launch barrier timed out"
            return real_launch(*args, **kwargs)
        with monkeypatch.context() as fault:
            fault.setattr(module, "Popen", stalled)
            values = []
            reference = resolve(service, values.append)
            try:
                assert entered.wait(1)
                assert reference.cancel() is True
                with pytest.raises(StartupError, match="cleanup") as error:
                    service.close(deadline=time.monotonic() + 0.2)
                assert error.value.__cause__ is None
                with pytest.raises(StartupError):
                    resolve(service, values.append)
                assert children.processes == []
            finally:
                release.set()
        wait_until(lambda: len(children.processes) == 1 and children.processes[0].returncode is not None)
        reference.dispatch()
        assert values == [] and children.markers() == []


@pytest.mark.parametrize(
    'fault_name',
    [
        pytest.param('reap', id='reap'),
    ],
)
def test_os_cleanup_failure_is_retained_and_never_claims_success(monkeypatch, tmp_path, fault_name):
    with resolver_runtime(monkeypatch, tmp_path, "block") as (_, service, children):
        reference = resolve(service, lambda result: pytest.fail("Cancelled DNS delivered a callback"))
        wait_until(lambda: bool(children.markers()))
        process = children.processes[0]
        with monkeypatch.context() as fault:
            if fault_name == "kill":
                fault.setattr(process, "terminate", lambda: None)
                def fail_kill():
                    raise OSError("dns-private-marker")
                fault.setattr(process, "kill", fail_kill)
            else:
                real_wait = process.wait
                def fail_reap(timeout=None):
                    if timeout == 0:
                        raise subprocess.TimeoutExpired("dns-private-marker", timeout)
                    return real_wait(timeout=timeout)
                fault.setattr(process, "wait", fail_reap)
            assert reference.cancel()
            with pytest.raises(StartupError, match="cleanup") as failure:
                service.close(deadline=time.monotonic() + 0.4)
            assert "dns-private-marker" not in str(failure.value) and failure.value.__cause__ is None
            with pytest.raises(StartupError):
                resolve(service, lambda result: None)
            assert len(children.processes) == 1




@pytest.mark.parametrize("cancel_lane", ["publisher"])
def test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane(monkeypatch, tmp_path, cancel_lane):
    with resolver_runtime(monkeypatch, tmp_path) as (module, service, children):
        entered, release = threading.Event(), threading.Event()
        launch = module.Popen
        calls = []

        def held_launch(*args, **kwargs):
            entered.set()
            assert release.wait(2), "Test launch barrier timed out"
            return launch(*args, **kwargs)

        with monkeypatch.context() as fault:
            fault.setattr(module, "Popen", held_launch)
            publisher = resolve(service, lambda value: calls.append(("publisher", value)))
            try:
                assert entered.wait(1)
                lease = service.request_probe(deadline=time.monotonic() + 5)
                assert lease.wait()
                probe = resolve(service, lambda value: calls.append(("probe", value)), lane="probe", lease=lease)
                cancelled = publisher if cancel_lane == "publisher" else probe
                assert cancelled.cancel() is True
            finally:
                release.set()
            assert publisher.done.wait(3) and probe.done.wait(3)
        publisher.dispatch()
        probe.dispatch()
        assert [lane for lane, result in calls] == ["probe" if cancel_lane == "publisher" else "publisher"]
        assert isinstance(calls[0][1], list)
        assert cancelled.cancel() is False
        if cancel_lane == "probe":
            assert len(children.processes) == 1, "Cancelled WAITING work launched a child"
        else:
            assert len(children.processes) == 2
            assert children.launches[1]["previous_unreaped"] == [], "Spawn overtook pending cleanup"
        assert len(children.markers()) == 1, "Cancelled work sent a DNS query"
        service.release_probe(lease)


def test_adversarial_launch_error_is_sanitized_and_does_not_poison_empty_slot(monkeypatch, tmp_path, caplog):
    with resolver_runtime(monkeypatch, tmp_path) as (module, service, children):
        def fail_launch(*args, **kwargs):
            raise OSError("dns-private-marker")

        with monkeypatch.context() as fault:
            fault.setattr(module, "Popen", fail_launch)
            values = []
            reference = resolve(service, values.append)
            deliver(reference, values)
            assert isinstance(values[0], socket.gaierror) and values[0].errno == socket.EAI_FAIL
            assert "dns-private-marker" not in str(values[0]) + caplog.text
            assert reference.done.is_set() and children.processes == [] and service.available
        values = []
        replacement = resolve(service, values.append)
        deliver(replacement, values)
        assert isinstance(values[0], list) and len(children.processes) == 1


def test_adversarial_partial_pipe_io_and_would_block_keep_offsets_and_budgets(monkeypatch, tmp_path):
    with resolver_runtime(monkeypatch, tmp_path) as (module, service, children):
        read, write = os.read, os.write
        sizes = {"read": [], "write": []}
        callers = set()

        def owned(fd, name):
            return any(not getattr(process, name).closed and getattr(process, name).fileno() == fd
                       for process in children.processes)

        def partial_read(fd, size):
            if owned(fd, "stdout"):
                sizes["read"].append(size)
                callers.add(threading.current_thread())
                assert size <= 8192
                if len(sizes["read"]) == 1:
                    raise BlockingIOError()
                size = min(size, 11)
            return read(fd, size)

        def partial_write(fd, data):
            if owned(fd, "stdin"):
                sizes["write"].append(len(data))
                callers.add(threading.current_thread())
                assert len(data) <= 2048
                if len(sizes["write"]) == 2:
                    raise BlockingIOError()
                data = data[:7]
            return write(fd, data)

        with monkeypatch.context() as fault:
            fault.setattr(module.os, "read", partial_read)
            fault.setattr(module.os, "write", partial_write)
            values = []
            reference = resolve(service, values.append)
            deliver(reference, values)
        assert len(values[0]) == 2 and values[0][1][4] == ("::1", 5672, 7, 3)
        assert len(sizes["read"]) > 2 and len(sizes["write"]) > 2
        assert callers == {service.thread} and not service.thread.daemon
        assert children.markers()[0]["args"] == list(REQUEST.values())






def wrong_pid_scenario(directory):
    """Isolated runner exits only after its real child is reaped; retained owner is intentional."""
    patch = pytest.MonkeyPatch()
    children = None
    exit_code = 1
    try:
        module = managed_module()
        children = ChildHarness(module, patch, Path(directory), "wrong-pid")
        service = module.ResolverSupervisor()
        service.start()
        values = []
        reference = resolve(service, values.append)
        wait_until(lambda: bool(children.processes) and children.processes[0].returncode is not None
                   and children.processes[0].stdout.closed)
        assert not reference.done.is_set() and not service.available
        with pytest.raises(StartupError, match="cleanup"):
            service.close(deadline=time.monotonic() + 0.1)
        with pytest.raises(StartupError):
            resolve(service, values.append)
        with pytest.raises(StartupError):
            module.ResolverSupervisor().start()
        assert service.request_probe(deadline=time.monotonic() + 1) is None
        reference.dispatch()
        assert values == [] and children.markers() == [] and len(children.processes) == 1
        assert service.thread.is_alive() and not service.thread.daemon
        children.cleanup()
        assert children.processes[0].pid not in process_parents()
        print("OWNERSHIP_RETAINED_CHILD_REAPED", flush=True)
        exit_code = 0
    except BaseException:
        import traceback
        traceback.print_exc()
    finally:
        if children is not None:
            children.cleanup()
        patch.undo()
        # Do not change product state to release a deliberately unprovable owner.
        os._exit(exit_code)


def test_adversarial_wrong_pid_retains_admission_in_isolated_process(tmp_path):
    command = (
        "import runpy,sys; from pathlib import Path; "
        "sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[1])); "
        "runpy.run_path(sys.argv[1])['wrong_pid_scenario'](sys.argv[2])"
    )
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS} if os.name == "nt" else {}
    result = subprocess.run([sys.executable, "-B", "-c", command, str(Path(__file__).resolve()), str(tmp_path)],
                            capture_output=True, text=True, timeout=12, **options)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OWNERSHIP_RETAINED_CHILD_REAPED" in result.stdout
