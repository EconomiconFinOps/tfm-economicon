import errno
import hashlib
import json
import math
import socket
import time
from http.client import HTTPException, RemoteDisconnected
from urllib import error, request

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
        self._transport = request.build_opener(_RejectRedirectHandler())

    def __repr__(self) -> str:
        return f"LiteLLMEmbeddingProvider(alias={self.alias!r}, dimension={self.dimension})"

    def embed(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.alias, "input": text, "dimensions": self.dimension}, allow_nan=False).encode("utf-8")
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
            deadline = time.monotonic() + self._timeout
            with self._transport.open(req, timeout=self._timeout) as response:
                body = json.loads(_read_body(response, deadline).decode("utf-8"), parse_constant=_reject_constant)
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
