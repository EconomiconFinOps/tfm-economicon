"""JUP-085: real auth routes with synthetic configuration and a fake user store."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest

from app.core import security
from app.core.logging import configure_logging
from app.core.security import hash_password
from conftest import SYNTHETIC_ENV
from test_secret_boundaries import (
    main_module,
    request as asgi_request,
    resource_mocks,
    restore_logging,
)

NOW = 1_800_000_000
PASSWORD = "jup085-password-sentinel"
KEY = SYNTHETIC_ENV["AUTH_SECRET_KEY"]
INVALID_TOKEN = {"detail": "Invalid access token."}
INVALID_BEARER = {"detail": "Missing or invalid bearer token."}
MISSING = object()


@pytest.fixture
def auth_clock(monkeypatch):
    class Clock(datetime):
        second = NOW

        @classmethod
        def now(cls, tz=None):
            instant = datetime.fromtimestamp(cls.second, timezone.utc)
            return instant if tz is None else instant.astimezone(tz)

    monkeypatch.setattr(security, "datetime", Clock)
    monkeypatch.setattr(jwt.api_jwt, "datetime", Clock)
    return Clock


@pytest.fixture
def auth_api(main_module, auth_clock, monkeypatch):
    user = {
        "id": "jup085-subject-sentinel",
        "email": "operator@example.com",
        "full_name": "Synthetic Operator",
        "role": "admin",
        "password_hash": hash_password(PASSWORD, salt="jup085-synthetic-salt"),
    }
    database = MagicMock(spec=["fetch_user_by_email", "fetch_user_by_id"])
    database.fetch_user_by_email.side_effect = lambda email: user if email == user["email"] else None
    database.fetch_user_by_id.side_effect = lambda subject: user if subject == user["id"] else None
    monkeypatch.setattr(main_module.app.state, "database", database, raising=False)
    return SimpleNamespace(app=main_module.app, database=database, user=user)


def request(api, method, path, **kwargs):
    # Bind diagnostics to this request's capture stream, as in JUP-053.
    configure_logging()
    return asgi_request(api.app, method, path, **kwargs)


def profile(user):
    return {field: user[field] for field in ("id", "email", "full_name", "role")}


def claims(api, **changes):
    return {"sub": api.user["id"], "iat": NOW, "exp": NOW + 60, **changes}


def assert_private(api, response, capsys, caplog, *sentinels):
    captured = capsys.readouterr()
    rendered = response.text + captured.out + captured.err + caplog.text
    for sentinel in (PASSWORD, KEY, api.user["password_hash"], api.user["id"], *sentinels):
        assert sentinel not in rendered


def test_login_returns_wrapper_and_token_with_configured_ttl(auth_api, monkeypatch, capsys, caplog):
    monkeypatch.setenv("AUTH_TOKEN_TTL_MINUTES", "17")
    response = request(auth_api, "POST", "/auth/login", json={
        "email": auth_api.user["email"], "password": PASSWORD,
    })

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user"}
    assert body["token_type"] == "bearer"
    assert body["user"] == profile(auth_api.user)
    assert isinstance(body["access_token"], str) and body["access_token"]
    auth_api.database.fetch_user_by_email.assert_called_once_with(auth_api.user["email"])
    captured = capsys.readouterr()
    diagnostics = captured.out + captured.err + caplog.text
    for sentinel in (PASSWORD, KEY, auth_api.user["password_hash"]):
        assert sentinel not in response.text + diagnostics
    assert body["access_token"] not in diagnostics
    assert auth_api.user["id"] not in diagnostics
    payload = jwt.decode(body["access_token"], KEY, algorithms=["HS256"])
    assert payload.get("iat") == NOW
    assert type(payload["iat"]) is int and type(payload["exp"]) is int
    assert payload["sub"] == auth_api.user["id"]
    assert payload["exp"] == NOW + 17 * 60


@pytest.mark.parametrize("password", ["  literal password  ", "   "], ids=["padded", "spaces"])
def test_login_compares_nonempty_password_literally(auth_api, password):
    auth_api.user["password_hash"] = hash_password(password, salt="jup085-literal-salt")
    response = request(auth_api, "POST", "/auth/login", json={
        "email": auth_api.user["email"], "password": password,
    })

    assert response.status_code == 200
    assert response.json()["user"] == profile(auth_api.user)
    if password.strip():
        trimmed = request(auth_api, "POST", "/auth/login", json={
            "email": auth_api.user["email"], "password": password.strip(),
        })
        assert trimmed.status_code == 401
        assert trimmed.json() == {"detail": "Invalid email or password."}


@pytest.mark.parametrize("email,password", [
    pytest.param("unknown@example.com", PASSWORD, id="unknown-email"),
    pytest.param("operator@example.com", "jup085-wrong-password", id="wrong-password"),
])
def test_login_invalid_credentials_are_generic(auth_api, capsys, caplog, email, password):
    response = request(auth_api, "POST", "/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}
    auth_api.database.fetch_user_by_email.assert_called_once_with(email)
    assert_private(auth_api, response, capsys, caplog, email, password)


@pytest.mark.parametrize("field,value", [
    pytest.param("email", MISSING, id="missing-email"),
    pytest.param("email", None, id="null-email"),
    pytest.param("email", 123, id="nonstring-email"),
    pytest.param("email", "jup085-invalid-email", id="invalid-email"),
    pytest.param("password", MISSING, id="missing-password"),
    pytest.param("password", None, id="null-password"),
    pytest.param("password", {"private": PASSWORD}, id="nonstring-password"),
    pytest.param("password", "", id="empty-password"),
])
def test_login_invalid_input_is_sanitized_422(auth_api, capsys, caplog, field, value):
    body = {"email": auth_api.user["email"], "password": PASSWORD}
    if value is MISSING:
        body.pop(field)
    else:
        body[field] = value
    response = request(auth_api, "POST", "/auth/login", json=body)

    assert response.status_code == 422
    assert response.json() == {"detail": [{"type": "validation_error", "msg": "Invalid request value"}]}
    auth_api.database.fetch_user_by_email.assert_not_called()
    assert_private(auth_api, response, capsys, caplog, auth_api.user["email"], "jup085-invalid-email")


def test_me_returns_current_direct_profile_without_tenant_header(auth_api):
    login = request(auth_api, "POST", "/auth/login", json={
        "email": auth_api.user["email"], "password": PASSWORD,
    })
    assert login.status_code == 200
    auth_api.user.update(email="updated@example.com", full_name="Current Operator", role="viewer")
    response = request(auth_api, "GET", "/me", headers={
        "Authorization": "Bearer " + login.json()["access_token"],
    })

    assert response.status_code == 200
    assert response.json() == profile(auth_api.user)
    assert response.json() != login.json()["user"]
    auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])


def test_me_accepts_case_insensitive_bearer(auth_api):
    token = jwt.encode(claims(auth_api), KEY, algorithm="HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"bEaReR {token}"})

    assert response.status_code == 200
    assert response.json() == profile(auth_api.user)
    auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])


@pytest.mark.parametrize("case", ["missing", "duplicate", "wrong-scheme", "empty", "extra-segment"])
def test_me_rejects_malformed_bearer_before_lookup(auth_api, capsys, caplog, case):
    token = jwt.encode(claims(auth_api), KEY, algorithm="HS256")
    headers = {
        "missing": [],
        "duplicate": [("Authorization", f"Bearer {token}"), ("authorization", f"Bearer {token}")],
        "wrong-scheme": [("Authorization", f"Basic {token}")],
        "empty": [("Authorization", "Bearer ")],
        "extra-segment": [("Authorization", f"Bearer {token} extra")],
    }[case]
    response = request(auth_api, "GET", "/me", headers=headers)

    assert (response.status_code, response.json(), auth_api.database.fetch_user_by_id.call_args_list) == (
        401, INVALID_BEARER, [],
    )
    assert_private(auth_api, response, capsys, caplog, token)


@pytest.mark.parametrize("case", ["corrupt", "unsigned", "wrong-key", "wrong-algorithm"])
def test_me_rejects_invalid_signature_or_algorithm_before_lookup(auth_api, capsys, caplog, case):
    wrong_key = "jup085-wrong-key-0123456789abcdef0123456789abcdef0123456789abcdef"
    if case == "corrupt":
        token = "jup085-corrupt-token-sentinel"
    elif case == "unsigned":
        token = jwt.encode(claims(auth_api), "", algorithm="none")
    else:
        token = jwt.encode(claims(auth_api), wrong_key if case == "wrong-key" else KEY,
                           algorithm="HS384" if case == "wrong-algorithm" else "HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert (response.status_code, response.json(), auth_api.database.fetch_user_by_id.call_args_list) == (
        401, INVALID_TOKEN, [],
    )
    assert_private(auth_api, response, capsys, caplog, token, wrong_key)


@pytest.mark.parametrize("field,value", [
    pytest.param("sub", MISSING, id="missing-sub"),
    pytest.param("sub", None, id="null-sub"),
    pytest.param("sub", "", id="empty-sub"),
    pytest.param("sub", 123, id="nonstring-sub"),
    pytest.param("iat", MISSING, id="legacy-without-iat"),
    pytest.param("iat", None, id="null-iat"),
    pytest.param("iat", True, id="boolean-iat"),
    pytest.param("iat", str(NOW), id="string-iat"),
    pytest.param("iat", NOW - 0.5, id="fractional-iat"),
    pytest.param("iat", -1, id="negative-iat"),
    pytest.param("iat", NOW + 6, id="future-iat"),
    pytest.param("exp", MISSING, id="missing-exp"),
    pytest.param("exp", None, id="null-exp"),
    pytest.param("exp", True, id="boolean-exp"),
    pytest.param("exp", str(NOW + 60), id="string-exp"),
    pytest.param("exp", NOW + 60.5, id="fractional-exp"),
    pytest.param("exp", -1, id="negative-exp"),
    pytest.param("exp", NOW, id="exp-equals-iat"),
    pytest.param("exp", NOW - 1, id="exp-before-iat"),
])
def test_me_rejects_missing_or_malformed_claims_before_lookup(
    auth_api, auth_clock, capsys, caplog, field, value,
):
    payload = claims(auth_api)
    if value is MISSING:
        payload.pop(field)
    else:
        payload[field] = value
    if field == "exp" and (value is True or value == -1):
        # Near the epoch, native leeway cannot mask strict type/order rejection.
        auth_clock.second = 0
        payload["iat"] = 0
    token = jwt.encode(payload, KEY, algorithm="HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert (response.status_code, response.json(), auth_api.database.fetch_user_by_id.call_args_list) == (
        401, INVALID_TOKEN, [],
    )
    assert_private(auth_api, response, capsys, caplog, token)


@pytest.mark.parametrize("field,value,clock_offset,status", [
    pytest.param("iat", NOW + 5, 0, 200, id="iat-exact-five"),
    pytest.param("iat", NOW + 5, -0.001, 401, id="iat-just-outside-five"),
    pytest.param("iat", NOW + 5, 0.001, 200, id="iat-just-inside-five"),
    pytest.param("nbf", NOW + 5, 0, 200, id="nbf-exact-five"),
    pytest.param("nbf", NOW + 6, 0, 401, id="nbf-six"),
    pytest.param("nbf", NOW + 5, -0.001, 401, id="nbf-just-outside-five"),
    pytest.param("nbf", NOW + 5, 0.001, 200, id="nbf-just-inside-five"),
])
def test_me_future_time_uses_five_second_leeway(
    auth_api, auth_clock, capsys, caplog, field, value, clock_offset, status,
):
    auth_clock.second = NOW + clock_offset
    payload = claims(auth_api, iat=NOW - 60)
    payload[field] = value
    token = jwt.encode(payload, KEY, algorithm="HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status
    if status == 200:
        assert response.json() == profile(auth_api.user)
        auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])
    else:
        assert response.json() == INVALID_TOKEN
        auth_api.database.fetch_user_by_id.assert_not_called()
        assert_private(auth_api, response, capsys, caplog, token)


@pytest.mark.parametrize("elapsed,status", [
    pytest.param(0, 200, id="exact-expiration"),
    pytest.param(4, 200, id="four-seconds-expired"),
    pytest.param(4.999, 200, id="just-before-grace-boundary"),
    pytest.param(5, 401, id="exact-grace-boundary"),
    pytest.param(5.001, 401, id="just-after-grace-boundary"),
])
def test_me_expiration_uses_exclusive_five_second_leeway(
    auth_api, auth_clock, capsys, caplog, elapsed, status,
):
    auth_clock.second = NOW + elapsed
    token = jwt.encode(claims(auth_api, iat=NOW - 60, exp=NOW), KEY, algorithm="HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status
    if status == 200:
        assert response.json() == profile(auth_api.user)
        auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])
    else:
        assert response.json() == INVALID_TOKEN
        auth_api.database.fetch_user_by_id.assert_not_called()
        assert_private(auth_api, response, capsys, caplog, token)


@pytest.mark.parametrize("expiration", [
    pytest.param(NOW - 4, id="reversed-within-leeway"),
    pytest.param(NOW + 4, id="equal-within-leeway"),
])
def test_me_rejects_time_order_even_inside_leeway(auth_api, capsys, caplog, expiration):
    token = jwt.encode(claims(auth_api, iat=NOW + 4, exp=expiration), KEY, algorithm="HS256")
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN
    auth_api.database.fetch_user_by_id.assert_not_called()
    assert_private(auth_api, response, capsys, caplog, token)


def test_me_removed_user_returns_generic_invalid_token(auth_api, capsys, caplog):
    token = jwt.encode(claims(auth_api), KEY, algorithm="HS256")
    auth_api.database.fetch_user_by_id.side_effect = None
    auth_api.database.fetch_user_by_id.return_value = None
    response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN
    auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])
    assert_private(auth_api, response, capsys, caplog, token)


@pytest.mark.parametrize("endpoint", ["login", "me"])
def test_user_store_failure_is_sanitized_500_not_401(auth_api, capsys, caplog, endpoint):
    token = jwt.encode(claims(auth_api), KEY, algorithm="HS256")
    message = " ".join((PASSWORD, KEY, token, auth_api.user["password_hash"], auth_api.user["id"]))
    if endpoint == "login":
        auth_api.database.fetch_user_by_email.side_effect = RuntimeError(message)
        response = request(auth_api, "POST", "/auth/login", json={
            "email": auth_api.user["email"], "password": PASSWORD,
        })
        auth_api.database.fetch_user_by_email.assert_called_once_with(auth_api.user["email"])
    else:
        auth_api.database.fetch_user_by_id.side_effect = RuntimeError(message)
        response = request(auth_api, "GET", "/me", headers={"Authorization": f"Bearer {token}"})
        auth_api.database.fetch_user_by_id.assert_called_once_with(auth_api.user["id"])

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert_private(auth_api, response, capsys, caplog, token)
