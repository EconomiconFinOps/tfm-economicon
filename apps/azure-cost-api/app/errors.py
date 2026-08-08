from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    headers: Mapping[str, str] | None = None


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
