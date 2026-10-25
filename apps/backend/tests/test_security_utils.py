from datetime import datetime, timezone

import jwt

from app.core import security
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from conftest import SYNTHETIC_ENV


def test_password_hash_roundtrip():
    password_hash = hash_password("secret")

    assert verify_password("secret", password_hash) is True
    assert verify_password("invalid", password_hash) is False


def test_access_token_roundtrip():
    token = create_access_token(
        user_id="user-finops-admin",
        secret_key="test-secret",
        expires_minutes=30,
    )

    payload = decode_access_token(token, "test-secret")

    assert payload["sub"] == "user-finops-admin"


def test_access_token_issues_integer_claims_from_one_clock_read(monkeypatch):
    class AdvancingClock(datetime):
        calls = 0

        @classmethod
        def now(cls, tz=None):
            instant = datetime.fromtimestamp(1_800_000_000 + cls.calls, timezone.utc)
            cls.calls += 1
            return instant if tz is None else instant.astimezone(tz)

    monkeypatch.setattr(security, "datetime", AdvancingClock)
    key = SYNTHETIC_ENV["AUTH_SECRET_KEY"]
    token = create_access_token("jup085-issued-user", key, expires_minutes=17)

    # Decode with the library independently of the product's claim validator.
    monkeypatch.setattr(jwt.api_jwt, "datetime", AdvancingClock)
    issuance_reads = AdvancingClock.calls
    payload = jwt.decode(token, key, algorithms=["HS256"])

    assert payload.get("iat") == 1_800_000_000
    assert type(payload["iat"]) is int and type(payload["exp"]) is int
    assert payload["sub"] == "jup085-issued-user"
    assert payload["exp"] == payload["iat"] + 17 * 60
    assert issuance_reads == 1
