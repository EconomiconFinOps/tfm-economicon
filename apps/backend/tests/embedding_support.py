"""Local doubles for the embedding provider tests: a fake gateway and a deterministic word-based provider."""
import hashlib
import json
import math
import re
import time
import socket
import threading
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeGateway:
    """Answers the queued responses in order and records what it received (never the key itself)."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                gateway.requests.append({
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                    "body": json.loads(body) if body else None,
                })
                status, payload, headers, delay = gateway.next_response()
                if delay:
                    threading.Event().wait(delay)
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                try:
                    self.send_response(status)
                    for name, value in headers.items():
                        self.send_header(name, value)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def next_response(self):
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        status, payload = item[0], item[1]
        headers = item[2] if len(item) > 2 else {}
        delay = item[3] if len(item) > 3 else 0
        return status, payload, headers, delay

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}/v1"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def vector_payload(*vectors):
    return {"data": [{"embedding": vector} for vector in vectors]}


class WordEmbeddingProvider:
    """One pseudo-random vector per normalized word, summed and normalized: shared words mean closeness."""

    name = "words"

    def __init__(self, dimension=64):
        self.dimension = dimension

    def _word(self, word):
        values, counter = [], 0
        while len(values) < self.dimension:
            values.extend((byte - 127.5) / 127.5 for byte in hashlib.sha256(f"{word}:{counter}".encode()).digest())
            counter += 1
        return values[: self.dimension]

    def embed(self, text):
        folded = unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode()
        total = [0.0] * self.dimension
        for word in re.findall(r"[a-z0-9]{3,}", folded):
            for index, value in enumerate(self._word(word)):
                total[index] += value
        norm = math.sqrt(sum(value * value for value in total))
        return [value / norm for value in total] if norm else [1.0] + [0.0] * (self.dimension - 1)


class RawServer:
    """A bare TCP server: the behaviour receives each accepted connection after the request was read."""

    def __init__(self, behaviour):
        self.behaviour, self.hits = behaviour, 0
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.listener.settimeout(0.2)
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.listener.getsockname()[1]}/v1"

    def _loop(self):
        while not self.stopping.is_set():
            try:
                connection, _ = self.listener.accept()
            except OSError:
                continue
            threading.Thread(target=self._handle, args=(connection,), daemon=True).start()

    def _handle(self, connection):
        try:
            connection.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = connection.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, _, rest = data.partition(b"\r\n\r\n")
            length = 0
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    length = int(line.split(b":")[1])
            while len(rest) < length:
                rest += connection.recv(65536)
            self.hits += 1
            self.behaviour(connection)
        except OSError:
            pass
        finally:
            try:
                connection.close()
            except OSError:
                pass

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stopping.set()
        self.listener.close()


def trickle(data, gap):
    def run(connection):
        for index in range(len(data)):
            connection.sendall(data[index:index + 1])
            time.sleep(gap)
    return run


def headers_trickling(connection):
    # The status line and the start of a header arrive at once, then one byte every 30 ms.
    connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nX-Trickle: ")
    for _ in range(80):
        connection.sendall(b"x")
        time.sleep(0.03)
    connection.sendall(b"\r\n\r\n{}")
