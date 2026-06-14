from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


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
