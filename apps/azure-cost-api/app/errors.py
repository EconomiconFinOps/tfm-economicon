from dataclasses import dataclass


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
