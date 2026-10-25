"""Test-only DNS faults; product code receives no test flags or environment."""
import json
import os
from pathlib import Path
import runpy
import socket
import struct
import sys
import threading


def packet(value):
    body = json.dumps(value, allow_nan=False).encode("utf-8")
    return struct.pack("!I", len(body)) + body


def read_exact(size):
    data = bytearray()
    while len(data) < size:
        part = os.read(0, size - len(data))
        if not part:
            raise EOFError("Fixture request incomplete")
        data.extend(part)
    return bytes(data)


def answers(port):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "v4.example", ("127.0.0.1", port)),
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "v6.example", ("::1", port, 7, 3))]


def main():
    product, mode, directory = sys.argv[1:]
    directory = Path(directory)
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(0, os.O_BINARY)
        msvcrt.setmode(1, os.O_BINARY)

    def observe(args):
        record = {"pid": os.getpid(), "ppid": os.getppid(), "args": args,
                  "env_keys": sorted(os.environ),
                  "lc_ctype": os.environ.get("LC_CTYPE"),
                  "secret_in_env": any("dns-private-marker" in value for value in os.environ.values()),
                  "app_modules": [name for name in sys.modules if name == "app" or name.startswith("app.")]}
        (directory / (str(os.getpid()) + ".json")).write_text(json.dumps(record), encoding="utf-8")

    if mode in {"block", "answers", "negative"}:
        def resolver(host, port, family=0, type=0, proto=0, flags=0):
            observe([host, port, family, type, proto, flags])
            if mode == "block":
                # Parent must terminate/reap before creating this release file.
                for _ in range(600):
                    if (directory / "release").exists():
                        break
                    threading.Event().wait(0.05)
                raise socket.gaierror(socket.EAI_AGAIN, "dns-private-marker")
            if mode == "negative":
                raise socket.gaierror(socket.EAI_NONAME, "dns-private-marker")
            return answers(port)
        socket.getaddrinfo = resolver
        sys.argv = [product]
        runpy.run_path(product, run_name="__main__")
        return

    pid = os.getpid() + (1 if mode == "wrong-pid" else 0)
    ready_faults = {
        "ready-oversize": struct.pack("!I", 129) + json.dumps({"kind": "ready", "pid": pid}).encode().ljust(129, b" "),
        "ready-zero": struct.pack("!I", 0),
        "ready-partial": struct.pack("!I", 50) + b"{}",
        "ready-extra": packet({"kind": "ready", "pid": pid, "extra": "dns-private-marker"}),
        "ready-bool": packet({"kind": "ready", "pid": True}),
        "ready-kind": packet({"kind": "other", "pid": pid}),
    }
    if mode in ready_faults:
        os.write(1, ready_faults[mode])
        if mode != "ready-oversize":
            return
    else:
        os.write(1, packet({"kind": "ready", "pid": pid}))
    size = struct.unpack("!I", read_exact(4))[0]
    if size > 2048:
        raise ValueError("Fixture request exceeds contract")
    request = json.loads(read_exact(size))
    observe(request)
    valid = {"kind": "ok", "answers": answers(request["port"])}
    raw = {
        "duplicate": b'{"kind":"error","kind":"ok","answers":' + json.dumps(answers(request["port"])).encode() + b'}',
        "nan": b'{"kind":"ok","answers":NaN}',
        "malformed": b'{dns-private-marker',
        "unknown-error": b'{"kind":"error","code":"dns-private-marker"}',
        "extra-key": b'{"kind":"error","code":"EAI_FAIL","secret":"dns-private-marker"}',
        "bool-port": json.dumps({"kind": "ok", "answers": [[2, 1, 6, "", ["127.0.0.1", True]]]}).encode(),
        "nonnumeric-ip": json.dumps({"kind": "ok", "answers": [[2, 1, 6, "", ["dns.invalid", 5672]]]}).encode(),
        "too-many": json.dumps({"kind": "ok", "answers": [answers(5672)[0]] * 65}).encode(),
        "flow-overflow": json.dumps({"kind": "ok", "answers": [[socket.AF_INET6, 1, 6, "", ["::1", 5672, 1048576, 0]]]}).encode(),
    }
    if mode in raw:
        body = raw[mode]
        wire = struct.pack("!I", len(body)) + body
    elif mode == "oversize":
        wire = struct.pack("!I", 65537)
    elif mode == "partial-header":
        wire = b"\x00\x00"
    elif mode == "partial-body":
        wire = struct.pack("!I", 100) + b"{}"
    elif mode == "extra-frame":
        wire = packet(valid) + packet(valid)
    else:
        wire = packet(valid)
    if mode == "partial-valid":
        for byte in wire:
            os.write(1, bytes([byte]))
            threading.Event().wait(0.001)
    else:
        os.write(1, wire)
    if mode == "nonzero-exit":
        raise SystemExit(7)


if __name__ == "__main__":
    main()
