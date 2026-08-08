from __future__ import annotations

import secrets

from app.config import Settings
from app.errors import ApiError


def authenticate(authorization: str | None, settings: Settings) -> None:
    if not settings.azure_cost_auth_enabled:
        return

    scheme, separator, token = (authorization or "").partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise _authentication_failed()

    if _contains(token, settings.forbidden_tokens):
        raise ApiError(
            403,
            "AuthorizationFailed",
            "The simulated identity is not allowed to query this subscription.",
        )
    if not _contains(token, settings.valid_tokens):
        raise _authentication_failed()


def _contains(candidate: str, configured: frozenset[str]) -> bool:
    return any(secrets.compare_digest(candidate, expected) for expected in configured)


def _authentication_failed() -> ApiError:
    return ApiError(
        401,
        "AuthenticationFailed",
        "A valid simulated bearer token is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
