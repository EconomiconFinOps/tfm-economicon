from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.agents.schemas import FinOpsResponse


SUPPORTED_AZURE_SOURCES = frozenset(
    {
        "azure",
        "azure-cost",
        "azure-cost-api",
        "azure-cost-management",
        "azure-cost-simulator",
    }
)
SENSITIVE_KEY = re.compile(
    r"(?:authorization|api[_-]?key|credential|password|secret|token)",
    re.IGNORECASE,
)
SAFE_STATUS = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
SAFE_SOURCE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
NUMERIC_CLAIM = re.compile(
    r"(?<!\w)-?\d+(?:[.,]\d+)?\s*(?:EUR|USD|euros?|€|%)(?!\w)",
    re.IGNORECASE,
)
MAX_METADATA_DEPTH = 4
MAX_METADATA_ITEMS = 50
MAX_METADATA_STRING = 500
MAX_METADATA_JSON = 4000


class AgentGuardrailError(RuntimeError):
    """Raised when agent input or output violates the local safety contract."""


class AgentResponseError(AgentGuardrailError):
    """Raised when provider output cannot be accepted as a FinOps response."""


@dataclass(frozen=True)
class PreparedAgentInput:
    source: str
    status: str
    metadata_json: str


def normalize_source(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentGuardrailError("source must be a non-empty string")
    source = value.strip().lower()
    if not SAFE_SOURCE.fullmatch(source):
        raise AgentGuardrailError("source must be a safe provider identifier")
    return source


def prepare_agent_input(job_payload: dict, status: str) -> PreparedAgentInput:
    if not isinstance(job_payload, dict):
        raise AgentGuardrailError("job payload must be an object")
    if not isinstance(job_payload.get("tenant_id"), str) or not job_payload[
        "tenant_id"
    ].strip():
        raise AgentGuardrailError("tenant context is required")
    if not isinstance(status, str) or not SAFE_STATUS.fullmatch(status):
        raise AgentGuardrailError("status contains unsupported characters")

    metadata = job_payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise AgentGuardrailError("metadata must be an object")

    return PreparedAgentInput(
        source=normalize_source(job_payload.get("source")),
        status=status,
        metadata_json=sanitize_metadata(metadata),
    )


def source_is_supported(source: str) -> bool:
    return source in SUPPORTED_AZURE_SOURCES


def sanitize_metadata(metadata: dict) -> str:
    sanitized = _sanitize_value(metadata, depth=0)
    rendered = json.dumps(
        sanitized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(rendered) <= MAX_METADATA_JSON:
        return rendered
    return json.dumps(
        {
            "notice": "metadata_truncated",
            "preview": rendered[: MAX_METADATA_JSON - 100],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sanitize_value(value: Any, depth: int) -> Any:
    if depth >= MAX_METADATA_DEPTH:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        result = {}
        for key in sorted(value, key=lambda item: str(item))[:MAX_METADATA_ITEMS]:
            normalized_key = str(key)[:100]
            result[normalized_key] = (
                "[REDACTED]"
                if SENSITIVE_KEY.search(normalized_key)
                else _sanitize_value(value[key], depth + 1)
            )
        return result
    if isinstance(value, (list, tuple)):
        return [
            _sanitize_value(item, depth + 1)
            for item in value[:MAX_METADATA_ITEMS]
        ]
    if isinstance(value, str):
        return value[:MAX_METADATA_STRING]
    if isinstance(value, float) and not math.isfinite(value):
        return "[NON_FINITE_NUMBER]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:MAX_METADATA_STRING]


def parse_and_validate_response(raw_response: str) -> FinOpsResponse:
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise AgentResponseError("provider returned an empty response")
    error_message: str | None = None
    try:
        response = FinOpsResponse.model_validate_json(raw_response)
    except ValidationError:
        error_message = (
            "provider response does not match the FinOps response schema"
        )
    except ValueError:
        error_message = "provider response is not valid JSON"

    if error_message is not None:
        # Raise outside the handler so the provider payload is not retained in
        # an exception cause/context that standard traceback logging would emit.
        raise AgentResponseError(error_message)

    if not response.evidence and NUMERIC_CLAIM.search(response.answer):
        raise AgentResponseError(
            "response contains a numeric claim without structured evidence"
        )
    return response
