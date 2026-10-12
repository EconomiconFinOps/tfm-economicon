"""One bounded resolver child per admitted chat connection, owned by its caller."""

import ipaddress
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time

LIMIT = 8192


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Resolver protocol")
        result[key] = value
    return result


def _decode(payload):
    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )


def _addresses(value, port):
    if not isinstance(value, dict):
        raise ValueError("Resolver protocol")
    if (
        value.get("kind") == "error"
        and set(value) == {"kind", "code"}
        and value["code"] in ("resolution", "invalid")
    ):
        raise OSError("Gateway name resolution failed")
    if set(value) != {"kind", "addresses"} or value["kind"] != "result":
        raise ValueError("Resolver protocol")
    records = value["addresses"]
    if not isinstance(records, list) or not 0 < len(records) <= 16:
        raise ValueError("Resolver address count")
    result = []
    for record in records:
        if not isinstance(record, list) or len(record) != 5:
            raise ValueError("Resolver address")
        family, kind, protocol, canonical, location = record
        if (
            any(type(number) is not int for number in (family, kind, protocol))
            or family not in (socket.AF_INET, socket.AF_INET6)
            or kind != socket.SOCK_STREAM
            or protocol != socket.IPPROTO_TCP
            or canonical != ""
        ):
            raise ValueError("Resolver address type")
        if not isinstance(location, list) or len(location) != (
            2 if family == socket.AF_INET else 4
        ):
            raise ValueError("Resolver address shape")
        host = location[0]
        if (
            not isinstance(host, str)
            or "%" in host
            or len(host) > 64
            or ipaddress.ip_address(host).version
            != (4 if family == socket.AF_INET else 6)
        ):
            raise ValueError("Resolver numeric address")
        if type(location[1]) is not int or location[1] != port:
            raise ValueError("Resolver address port")
        if family == socket.AF_INET6 and (
            type(location[2]) is not int
            or not 0 <= location[2] <= 1048575
            or type(location[3]) is not int
            or not 0 <= location[3] <= 4294967295
        ):
            raise ValueError("Resolver IPv6 address")
        result.append((family, kind, protocol, "", tuple(location)))
    return result


def _environment():
    if os.name == "posix":
        return {}, 0
    if os.name == "nt":
        root = Path(os.environ.get("SystemRoot", ""))
        if not root.is_absolute() or not (root / "System32").is_dir():
            raise OSError("Resolver environment unavailable")
        return {
            "SystemRoot": str(root)
        }, subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    raise OSError("Resolver platform unsupported")


def resolve(host, port, remaining, cancelled):
    if (
        not isinstance(host, str)
        or not host
        or "\x00" in host
        or len(host.encode()) > 1024
        or type(port) is not int
        or not 1 <= port <= 65535
    ):
        raise ValueError("Gateway address")
    remaining()
    if cancelled.is_set():
        raise TimeoutError("Gateway connection cancelled")
    child_path = Path(__file__).with_name("chat_dns_child.py").resolve(strict=True)
    executable = Path(sys.executable).resolve(strict=True)
    environment, flags = _environment()
    payload = json.dumps(
        {"host": host, "port": port}, allow_nan=False, separators=(",", ":")
    ).encode()
    packet = struct.pack("!I", len(payload)) + payload
    child = subprocess.Popen(
        [str(executable), "-I", "-S", "-B", str(child_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=environment,
        cwd=str(child_path.parent),
        shell=False,
        close_fds=True,
        bufsize=0,
        creationflags=flags,
    )
    received = bytearray()
    sent = 0
    try:
        os.set_blocking(child.stdin.fileno(), False)
        os.set_blocking(child.stdout.fileno(), False)
        while True:
            budget = remaining()
            if cancelled.is_set():
                raise TimeoutError("Gateway connection cancelled")
            if sent < len(packet):
                try:
                    written = os.write(child.stdin.fileno(), packet[sent:])
                    if written <= 0:
                        raise OSError("Resolver input closed")
                    sent += written
                except BlockingIOError:
                    pass
                if sent == len(packet):
                    child.stdin.close()
            try:
                chunk = os.read(child.stdout.fileno(), LIMIT + 137 - len(received))
            except BlockingIOError:
                chunk = None
            if chunk:
                received.extend(chunk)
                if len(received) > LIMIT + 136:
                    raise ValueError("Resolver output limit")
            if chunk == b"":
                remaining()
                if cancelled.is_set():
                    raise TimeoutError("Gateway connection cancelled")
                if child.poll() is None:
                    cancelled.wait(min(0.01, budget))
                    continue
                if child.returncode != 0 or sent != len(packet):
                    raise OSError("Resolver exited unsuccessfully")
                offset, frames = 0, []
                for limit in (128, LIMIT):
                    if len(received) < offset + 4:
                        raise ValueError("Resolver truncated output")
                    length = struct.unpack("!I", received[offset : offset + 4])[0]
                    offset += 4
                    if not 0 < length <= limit or len(received) < offset + length:
                        raise ValueError("Resolver frame limit")
                    frames.append(_decode(received[offset : offset + length]))
                    offset += length
                if (
                    offset != len(received)
                    or frames[0] != {"kind": "ready", "pid": child.pid}
                    or type(frames[0].get("pid")) is not int
                ):
                    raise ValueError("Resolver ownership protocol")
                return _addresses(frames[1], port)
            cancelled.wait(min(0.01, budget))
    finally:
        try:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=0.25)
        finally:
            child.stdin.close()
            child.stdout.close()
