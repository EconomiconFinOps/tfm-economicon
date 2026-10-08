"""Bounded gateway transport with content-free diagnostics."""

import errno
from functools import partial
from http.client import HTTPConnection, HTTPSConnection, HTTPException, HTTPResponse, RemoteDisconnected
import io
import json
import math
import socket
import time
from urllib import error, request

import structlog

from app.core.config import Settings


logger = structlog.get_logger(__name__)


class ProviderError(RuntimeError):
    """A terminal provider failure safe to report without upstream details."""

    def __init__(self, category: str):
        self.category = category if category in {
            "timeout", "connection", "transport", "authentication", "request",
            "redirect", "rate_limit", "upstream", "invalid_response",
        } else "transport"
        super().__init__(f"LiteLLM provider failed: {self.category}")


class _RejectRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, response, code, msg, headers, newurl):
        return None


class _AttemptDeadline:
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
        # Buffer above the deadline-aware raw reader, never below it: each recv
        # in read/readline must use the remaining attempt budget.
        return io.BufferedReader(_DeadlineReader(self.sock, self.deadline))


class _DeadlineResponse(HTTPResponse):
    def __init__(self, sock, *args, deadline, **kwargs):
        super().__init__(_ResponseSocket(sock, deadline), *args, **kwargs)


class _DeadlineHTTPConnection(HTTPConnection):
    def __init__(self, *args, deadline, **kwargs):
        super().__init__(*args, **kwargs)
        self.deadline = deadline
        self.response_class = partial(_DeadlineResponse, deadline=deadline)
        # HTTPConnection's per-instance factory also preserves its tunnel setup.
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
        self.sock = self._context.wrap_socket(
            self.sock, server_hostname=self._tunnel_host or self.host,
        )
        self.deadline.remaining()


class _DeadlineHandler:
    def do_open(self, http_class, req, **kwargs):
        connection = (
            _DeadlineHTTPSConnection if http_class is HTTPSConnection
            else _DeadlineHTTPConnection
        )
        return super().do_open(
            partial(connection, deadline=req._attempt_deadline), req, **kwargs,
        )


class _DeadlineHTTPHandler(_DeadlineHandler, request.HTTPHandler):
    pass


class _DeadlineHTTPSHandler(_DeadlineHandler, request.HTTPSHandler):
    pass


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


def _safe_cost(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        cost = float(value)
    except (ValueError, OverflowError):
        return None
    return cost if math.isfinite(cost) and cost >= 0 else None


def _usage_metadata(payload: dict, cost_header: str | None) -> dict:
    metadata = {}
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        usage = {}
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(field)
        if type(value) is int and value >= 0:
            metadata[field] = value
    for candidate in (cost_header, usage.get("cost"), payload.get("response_cost")):
        cost = _safe_cost(candidate)
        if cost is not None:
            metadata["cost_usd"] = cost
            break
    return metadata


class LiteLLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        base = settings.litellm_base_url.rstrip("/")
        self.base_url = base if base.endswith("/v1") else f"{base}/v1"
        self.transport = request.build_opener(
            _RejectRedirectHandler(), _DeadlineHTTPHandler(), _DeadlineHTTPSHandler(),
        )

    def post(self, endpoint: str, payload: dict) -> dict:
        req = request.Request(
            f"{self.base_url}/{endpoint}",
            data=json.dumps(payload, allow_nan=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.litellm_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.perf_counter()
        for attempt in range(self.settings.llm_max_retries + 1):
            retryable = False
            status_code = None
            req._attempt_deadline = _AttemptDeadline(self.settings.llm_timeout_seconds)
            try:
                with self.transport.open(req, timeout=self.settings.llm_timeout_seconds) as response:
                    status_code = response.status
                    raw_body = response.read()
                    req._attempt_deadline.remaining()
                    body = json.loads(raw_body.decode("utf-8"))
                    cost_header = response.headers.get("x-litellm-response-cost")
                if not isinstance(body, dict):
                    raise ValueError("Invalid gateway response")
            except error.HTTPError as exc:
                status_code = exc.code
                exc.close()
                if 300 <= status_code < 400:
                    category = "redirect"
                elif status_code in {401, 403}:
                    category = "authentication"
                elif status_code == 429:
                    category, retryable = "rate_limit", True
                elif 500 <= status_code < 600:
                    category, retryable = "upstream", True
                else:
                    category = "request"
            except error.URLError as exc:
                category, retryable = _transport_failure(exc.reason)
            except (OSError, HTTPException) as exc:
                category, retryable = _transport_failure(exc)
            except (ValueError, UnicodeError):
                category = "invalid_response"
            else:
                logger.info(
                    "litellm_response", alias=payload["model"], status_code=status_code,
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    **_usage_metadata(body, cost_header),
                )
                return body

            # Leave the handler before raising so no upstream exception is retained.
            logger.warning(
                "litellm_failure", alias=payload["model"], category=category,
                status_code=status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            if not retryable or attempt == self.settings.llm_max_retries:
                raise ProviderError(category)
            time.sleep(min(0.25 * (2 ** attempt), 1.0))
