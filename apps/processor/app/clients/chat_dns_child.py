"""Fixed, isolated resolver entry point. No application configuration is loaded."""

import ipaddress
import json
import os
import socket
import struct
import sys

LIMIT = 8192


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def send(value, limit=LIMIT):
    payload = json.dumps(value, allow_nan=False, separators=(",", ":")).encode()
    if len(payload) > limit:
        raise ValueError("Frame limit")
    sys.stdout.buffer.write(struct.pack("!I", len(payload)) + payload)
    sys.stdout.buffer.flush()


def run():
    send({"kind": "ready", "pid": os.getpid()}, 128)
    header = sys.stdin.buffer.read(4)
    if len(header) != 4:
        raise ValueError("Header")
    length = struct.unpack("!I", header)[0]
    if not 0 < length <= 2048:
        raise ValueError("Request limit")
    payload = sys.stdin.buffer.read(length)
    if len(payload) != length or sys.stdin.buffer.read(1):
        raise ValueError("Request framing")
    request = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    if not isinstance(request, dict) or set(request) != {"host", "port"}:
        raise ValueError("Request shape")
    host, port = request["host"], request["port"]
    if (
        not isinstance(host, str)
        or not host
        or "\x00" in host
        or len(host.encode()) > 1024
    ):
        raise ValueError("Host")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Port")
    addresses = socket.getaddrinfo(
        host, port, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP
    )
    if not 0 < len(addresses) <= 16:
        raise ValueError("Address count")
    result = []
    for family, kind, protocol, _, location in addresses:
        if (
            family not in (socket.AF_INET, socket.AF_INET6)
            or kind != socket.SOCK_STREAM
            or protocol != socket.IPPROTO_TCP
        ):
            raise ValueError("Address type")
        if len(location) != (2 if family == socket.AF_INET else 4):
            raise ValueError("Address shape")
        parsed = ipaddress.ip_address(location[0])
        if (
            "%" in location[0]
            or parsed.version != (4 if family == socket.AF_INET else 6)
            or location[1] != port
        ):
            raise ValueError("Numeric address")
        if family == socket.AF_INET6 and (
            type(location[2]) is not int
            or not 0 <= location[2] <= 1048575
            or type(location[3]) is not int
            or not 0 <= location[3] <= 4294967295
        ):
            raise ValueError("IPv6 address")
        result.append([family, kind, protocol, "", list(location)])
    send({"kind": "result", "addresses": result})


if __name__ == "__main__":
    try:
        run()
    except socket.gaierror:
        send({"kind": "error", "code": "resolution"})
    except Exception:
        send({"kind": "error", "code": "invalid"})
