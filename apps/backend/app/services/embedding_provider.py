import errno
import hashlib
import io
import json
import math
import socket
import time
from functools import partial
from http.client import HTTPConnection, HTTPException, HTTPResponse, HTTPSConnection, RemoteDisconnected
from urllib import error, request

from app.core.llm_metrics import observe_provider_call

PROVIDER_ERROR_CATEGORIES = frozenset({
    "timeout", "connection", "transport", "authentication", "request",
    "redirect", "rate_limit", "upstream", "invalid_response",
})
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class ProviderError(RuntimeError):
    """A terminal provider failure that is safe to report: it carries a category and nothing else."""

    def __init__(self, category: str):
        self.category = category if category in PROVIDER_ERROR_CATEGORIES else "transport"
        super().__init__(f"Embedding provider failed: {self.category}")


class _RejectRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, response, code, msg, headers, newurl):
        return None


class _AttemptDeadline:
    """One monotonic budget for a whole attempt: connection, request, headers and body."""

    def __init__(self, timeout: float):
        self.expires = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.expires - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Gateway attempt deadline exceeded")
        return remaining


class _DeadlineReader(io.RawIOBase):
    def __init__(self, sock, deadline):
        self.sock = sock
        self.deadline = deadline
        self.raw = sock.makefile("rb", buffering=0)

    def readable(self):
        return True

    def readinto(self, buffer):
        self.sock.settimeout(self.deadline.remaining())
        count = self.raw.readinto(buffer)
        self.deadline.remaining()
        return count

    def close(self):
        try:
            self.raw.close()
        finally:
            super().close()


class _ResponseSocket:
    def __init__(self, sock, deadline):
        self.sock = sock
        self.deadline = deadline

    def makefile(self, mode):
        # Buffer above the deadline-aware raw reader, never below it: each recv in read/readline
        # (status line and headers included) must use the remaining attempt budget.
        return io.BufferedReader(_DeadlineReader(self.sock, self.deadline))


class _DeadlineResponse(HTTPResponse):
    def __init__(self, sock, *args, deadline, **kwargs):
        super().__init__(_ResponseSocket(sock, deadline), *args, **kwargs)


class _DeadlineHTTPConnection(HTTPConnection):
    def __init__(self, *args, deadline, **kwargs):
        super().__init__(*args, **kwargs)
        self.deadline = deadline
        self.response_class = partial(_DeadlineResponse, deadline=deadline)
        self._create_connection = self._connect_socket

    def _connect_socket(self, address, timeout, source_address):
        host, port = address
        # Synchronous system DNS is outside the cancelable transport budget.
        addresses = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        last_error = OSError("No gateway addresses")
        for family, socktype, proto, _, sockaddr in addresses:
            self.deadline.remaining()
            sock = socket.socket(family, socktype, proto)
            try:
                sock.settimeout(self.deadline.remaining())
                if source_address:
                    sock.bind(source_address)
                sock.connect(sockaddr)
                self.deadline.remaining()
                return sock
            except OSError as exc:
                last_error = exc
                sock.close()
            except BaseException:
                sock.close()
                raise
        self.deadline.remaining()
        raise last_error

    def send(self, data):
        if self.sock is None:
            self.connect()
        self.sock.settimeout(self.deadline.remaining())
        super().send(data)
        self.deadline.remaining()


class _DeadlineHTTPSConnection(_DeadlineHTTPConnection, HTTPSConnection):
    def connect(self):
        HTTPConnection.connect(self)
        self.sock.settimeout(self.deadline.remaining())
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self._tunnel_host or self.host)
        self.deadline.remaining()


class _DeadlineHandler:
    def do_open(self, http_class, req, **kwargs):
        connection = _DeadlineHTTPSConnection if http_class is HTTPSConnection else _DeadlineHTTPConnection
        return super().do_open(partial(connection, deadline=req._attempt_deadline), req, **kwargs)


class _DeadlineHTTPHandler(_DeadlineHandler, request.HTTPHandler):
    pass


class _DeadlineHTTPSHandler(_DeadlineHandler, request.HTTPSHandler):
    pass


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _transport_failure(exc: BaseException) -> tuple[str, bool]:
    if isinstance(exc, TimeoutError):
        return "timeout", True
    if isinstance(exc, (ConnectionError, RemoteDisconnected)):
        return "connection", True
    if isinstance(exc, socket.gaierror):
        return "connection", exc.errno == socket.EAI_AGAIN
    if isinstance(exc, OSError) and exc.errno in {
        errno.ECONNRESET, errno.ECONNREFUSED, errno.ECONNABORTED,
        errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH, errno.EPIPE,
    }:
        return "connection", True
    return "transport", False


def _read_body(response, deadline: float) -> bytes:
    # A per-read timeout never fires on a body that trickles in, so the whole read has a deadline.
    chunks, size = [], 0
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError()
        chunk = response.read1(65536)
        if not chunk:
            return b"".join(chunks)
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError("response too large")
        chunks.append(chunk)


class MockEmbeddingProvider:
    name = "mock"

    def __init__(self, dimension: int):
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        vector: list[float] = []
        for index in range(self.dimension):
            digest = hashlib.sha256(f"{index}:{text}".encode("utf-8")).digest()
            raw_value = int.from_bytes(digest[:8], byteorder="big", signed=False)
            normalized = (raw_value / ((1 << 64) - 1)) * 2 - 1
            vector.append(round(normalized, 6))
        return vector


class LiteLLMEmbeddingProvider:
    """Embeds the question through the LiteLLM gateway with the virtual key of the backend."""

    def __init__(self, settings):
        self.name = "litellm"
        self.dimension = settings.embedding_dimension
        self.alias = settings.embedding_model
        base = settings.litellm_base_url.rstrip("/")
        self._url = (base if base.endswith("/v1") else f"{base}/v1") + "/embeddings"
        self._key = settings.litellm_api_key
        self._timeout = settings.embedding_timeout_seconds
        self._retries = settings.embedding_max_retries
        # The gateway is an internal service: never route the key through proxies taken from the environment.
        self._transport = request.build_opener(
            request.ProxyHandler({}), _RejectRedirectHandler(), _DeadlineHTTPHandler(), _DeadlineHTTPSHandler(),
        )

    def __repr__(self) -> str:
        return f"LiteLLMEmbeddingProvider(alias={self.alias!r}, dimension={self.dimension})"

    def embed(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.alias, "input": text, "dimensions": self.dimension}, allow_nan=False).encode("utf-8")
        with observe_provider_call("embedding", ProviderError):
            for attempt in range(self._retries + 1):
                category, retryable = self._attempt(payload)
                if isinstance(category, list):
                    return category
                if not retryable or attempt == self._retries:
                    raise ProviderError(category)
                _sleep(min(0.25 * (2 ** attempt), 1.0))
            raise ProviderError("transport")

    def _attempt(self, payload: bytes):
        req = request.Request(
            self._url, data=payload, method="POST",
            headers={"Authorization": f"Bearer {self._key.get_secret_value()}", "Content-Type": "application/json"},
        )
        try:
            req._attempt_deadline = _AttemptDeadline(self._timeout)
            with self._transport.open(req, timeout=self._timeout) as response:
                body = json.loads(_read_body(response, req._attempt_deadline.expires).decode("utf-8"), parse_constant=_reject_constant)
        except error.HTTPError as exc:
            status = exc.code
            exc.close()
            if 300 <= status < 400:
                return "redirect", False
            if status in {401, 403}:
                return "authentication", False
            if status == 429:
                return "rate_limit", True
            if 500 <= status < 600:
                return "upstream", True
            return "request", False
        except error.URLError as exc:
            return _transport_failure(exc.reason)
        except (OSError, HTTPException) as exc:
            return _transport_failure(exc)
        except (ValueError, UnicodeError):
            return "invalid_response", False
        return self._vector(body), False

    def _vector(self, body):
        try:
            data = body["data"]
            vector = data[0]["embedding"]
            if (
                isinstance(data, list) and len(data) == 1
                and isinstance(vector, list) and len(vector) == self.dimension
                and all(type(value) in {int, float} and math.isfinite(value) for value in vector)
            ):
                return [float(value) for value in vector]
        except (KeyError, IndexError, TypeError, OverflowError):
            pass
        return "invalid_response"


def _reject_constant(name: str):
    raise ValueError("non-finite number")
