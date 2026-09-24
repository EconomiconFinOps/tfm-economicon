import hashlib
import secrets
from datetime import datetime, timezone

import jwt


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        100_000,
    ).hex()
    return f"{salt_value}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, expected = password_hash.split("$", maxsplit=1)
    candidate = hash_password(password, salt=salt)
    return secrets.compare_digest(candidate.split("$", maxsplit=1)[1], expected)


def create_access_token(user_id: str, secret_key: str, expires_minutes: int) -> str:
    issued_at = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "sub": user_id,
        "iat": issued_at,
        "exp": issued_at + expires_minutes * 60,
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict:
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        leeway=5,
        options={"require": ["sub", "iat", "exp"]},
    )
    # PyJWT checks signature and clock bounds but may coerce time claim types.
    if (
        not isinstance(payload["sub"], str)
        or not payload["sub"]
        or type(payload["iat"]) is not int
        or type(payload["exp"]) is not int
        or payload["iat"] < 0
        or payload["exp"] <= payload["iat"]
    ):
        raise jwt.InvalidTokenError("Invalid access token.")
    return payload
