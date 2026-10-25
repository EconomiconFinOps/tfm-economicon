from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    headers: Mapping[str, str] | None = None


class ConfigurationError(RuntimeError):
    """Raised when the versioned API contract cannot configure the service."""


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
