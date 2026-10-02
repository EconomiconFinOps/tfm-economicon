"""Bounded gateway transport with content-free diagnostics."""

import errno
from http.client import HTTPException, RemoteDisconnected
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
        self.transport = request.build_opener(_RejectRedirectHandler())

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
            try:
                with self.transport.open(req, timeout=self.settings.llm_timeout_seconds) as response:
                    status_code = response.status
                    body = json.loads(response.read().decode("utf-8"))
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
