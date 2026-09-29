"""Bounded, stdlib-only wire protocol for the isolated DNS process."""

import ipaddress
import json
import os
import socket
import struct


REQUEST_LIMIT = 2048
RESULT_LIMIT = 65536
READY_LIMIT = 128
ERROR_CODES = {
    name: getattr(socket, name)
    for name in (
        "EAI_AGAIN", "EAI_NONAME", "EAI_NODATA", "EAI_FAIL", "EAI_FAMILY",
        "EAI_ADDRFAMILY", "EAI_SOCKTYPE", "EAI_SERVICE", "EAI_BADFLAGS",
        "EAI_MEMORY", "EAI_SYSTEM", "EAI_OVERFLOW",
    ) if hasattr(socket, name)
}
FLAG_MASK = 0
for _flag in socket.AddressInfo:
    FLAG_MASK |= int(_flag)


def integer(value, low, high):
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def bounded_text(value):
    return isinstance(value, str) and "\x00" not in value and len(value.encode("utf-8")) <= 1024


def validate_request(value):
    if not isinstance(value, dict) or set(value) != {"host", "port", "family", "socktype", "proto", "flags"}:
        raise ValueError()
    if not bounded_text(value["host"]) or not integer(value["port"], 0, 65535):
        raise ValueError()
    for key, choices in (
        ("family", (socket.AF_UNSPEC, socket.AF_INET, socket.AF_INET6)),
        ("socktype", (0, socket.SOCK_STREAM, socket.SOCK_DGRAM)),
        ("proto", (0, socket.IPPROTO_TCP, socket.IPPROTO_UDP)),
    ):
        item = value[key]
        if not integer(item, 0, 65535) or item not in choices:
            raise ValueError()
    if not integer(value["flags"], 0, FLAG_MASK) or value["flags"] & ~FLAG_MASK:
        raise ValueError()
    return value


def validate_result(value):
    if not isinstance(value, dict):
        raise ValueError()
    if value.get("kind") == "error":
        if set(value) != {"kind", "code"} or not isinstance(value["code"], str):
            raise ValueError()
        if value["code"] not in ERROR_CODES and value["code"] not in ("INVALID_REQUEST", "RESOLVER_FAILURE"):
            raise ValueError()
        return value
    if set(value) != {"kind", "answers"} or value["kind"] != "ok":
        raise ValueError()
    answers = value["answers"]
    if not isinstance(answers, (list, tuple)) or not 1 <= len(answers) <= 64:
        raise ValueError()
    checked = []
    for answer in answers:
        if not isinstance(answer, (list, tuple)) or len(answer) != 5:
            raise ValueError()
        family, kind, proto, canonical, address = answer
        if (not integer(family, 0, 65535) or family not in (socket.AF_INET, socket.AF_INET6)
                or not integer(kind, 0, 65535) or kind not in (0, socket.SOCK_STREAM, socket.SOCK_DGRAM)
                or not integer(proto, 0, 65535) or proto not in (0, socket.IPPROTO_TCP, socket.IPPROTO_UDP)
                or not bounded_text(canonical) or not isinstance(address, (list, tuple))
                or len(address) != (2 if family == socket.AF_INET else 4)):
            raise ValueError()
        if not bounded_text(address[0]) or not integer(address[1], 0, 65535):
            raise ValueError()
        # Scope is carried separately; accepting a zone string would change it.
        if "%" in address[0] or ipaddress.ip_address(address[0]).version != (4 if family == socket.AF_INET else 6):
            raise ValueError()
        if family == socket.AF_INET6 and (not integer(address[2], 0, 1048575)
                                         or not integer(address[3], 0, 4294967295)):
            raise ValueError()
        checked.append((family, kind, proto, canonical, tuple(address)))
    return {"kind": "ok", "answers": checked}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError()


def decode(raw):
    return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_pairs,
                      parse_constant=_invalid_constant)


def encode(value, limit):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > limit:
        raise ValueError()
    return struct.pack("!I", len(raw)) + raw


def _read_exact(size):
    data = bytearray()
    while len(data) < size:
        part = os.read(0, size - len(data))
        if not part:
            raise ValueError()
        data.extend(part)
    return bytes(data)


def _send(value, limit):
    wire = encode(value, limit)
    offset = 0
    while offset < len(wire):
        written = os.write(1, wire[offset:])
        if written <= 0:
            raise ValueError()
        offset += written


def main():
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(0, os.O_BINARY)
        msvcrt.setmode(1, os.O_BINARY)
    _send({"kind": "ready", "pid": os.getpid()}, READY_LIMIT)
    try:
        size = struct.unpack("!I", _read_exact(4))[0]
        if not 0 < size <= REQUEST_LIMIT:
            raise ValueError()
        request = validate_request(decode(_read_exact(size)))
        if os.read(0, 1):
            raise ValueError()
    except Exception:
        _send({"kind": "error", "code": "INVALID_REQUEST"}, RESULT_LIMIT)
        return
    try:
        answers = socket.getaddrinfo(request["host"], request["port"], request["family"],
                                     request["socktype"], request["proto"], request["flags"])
        result = validate_result({"kind": "ok", "answers": answers})
        encode(result, RESULT_LIMIT)
    except socket.gaierror as error:
        code = next((name for name, number in ERROR_CODES.items() if number == error.errno), "RESOLVER_FAILURE")
        result = {"kind": "error", "code": code}
    except Exception:
        result = {"kind": "error", "code": "RESOLVER_FAILURE"}
    _send(result, RESULT_LIMIT)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        # Never emit resolver, request or OS exception details on either pipe.
        raise SystemExit(1) from None
