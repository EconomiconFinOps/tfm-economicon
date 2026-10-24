from dataclasses import dataclass
from typing import Mapping


@dataclass
class ApiError(Exception):
    """API failure whose traceback remains writable for exception handlers."""

    status_code: int
    code: str
    message: str
    headers: Mapping[str, str] | None = None


class ConfigurationError(RuntimeError):
    """Raised when the versioned API contract cannot configure the service."""


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
