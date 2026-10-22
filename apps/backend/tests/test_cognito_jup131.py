"""Real RSA signatures and untrusted claims; no AWS or network calls."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import URLError

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import pytest

from app.core.cognito import CognitoVerifier

ISSUER = "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_TestPool123"
CLIENT = "synthetic-app-client"


@pytest.fixture(scope="module")
def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def claims(**changes):
    now = int(datetime.now(timezone.utc).timestamp())
    return dict(sub="subject-123", iss=ISSUER, client_id=CLIENT, token_use="access",
                iat=now-10, exp=now+60, scope="openid email", **changes)


def verifier(key):
    v = CognitoVerifier(ISSUER, CLIENT)
    v.keys = Mock(get_signing_key_from_jwt=Mock(return_value=SimpleNamespace(key=key.public_key())))
    return v


def token(key, payload):
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": "test-key"})


def test_accepts_signed_access_token(key):
    assert verifier(key).verify(token(key, claims()))["sub"] == "subject-123"


@pytest.mark.parametrize("change", [
    {"iss": "https://attacker.example.invalid"}, {"client_id": "other-client"},
    {"token_use": "id", "aud": CLIENT}, {"exp": 1}, {"iat": 9999999999},
    {"sub": ""}, {"sub": 123}, {"iat": True}, {"exp": "9999999999"},
])
def test_rejects_invalid_claims(key, change):
    payload = claims()
    payload.update(change)
    with pytest.raises(jwt.InvalidTokenError):
        verifier(key).verify(token(key, payload))


@pytest.mark.parametrize("name", ["iss", "client_id", "token_use", "iat", "exp", "sub"])
def test_requires_security_claims(key, name):
    payload = claims()
    del payload[name]
    with pytest.raises(jwt.InvalidTokenError):
        verifier(key).verify(token(key, payload))


def test_rejects_forged_signature(key):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(jwt.InvalidTokenError):
        verifier(key).verify(token(other, claims()))


def test_rejects_hmac_algorithm_without_key_lookup(key):
    v = verifier(key)
    with pytest.raises(jwt.InvalidTokenError):
        v.verify(jwt.encode(claims(), "synthetic-hmac-key-0123456789abcdef", algorithm="HS256", headers={"kid": "test-key"}))
    v.keys.get_signing_key_from_jwt.assert_not_called()


def test_real_jwks_selects_rotated_key_and_ignores_untrusted_discovery_url(key):
    v = CognitoVerifier(ISSUER, CLIENT)
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    v.keys.fetch_data = Mock(return_value={"keys": [{**public, "kid": "rotated-key", "use": "sig", "alg": "RS256"}]})
    signed = jwt.encode(claims(), key, algorithm="RS256",
        headers={"kid": "rotated-key", "jku": "https://attacker.example.invalid/keys"})
    assert v.verify(signed)["sub"] == "subject-123"
    assert v.keys.uri == f"{ISSUER}/.well-known/jwks.json"
    v.keys.fetch_data.assert_called_once()


def test_unknown_kid_burst_bounds_network_and_allows_rotation_after_cooldown(key):
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    initial = {'keys': [{**public, 'kid': 'test-key', 'use': 'sig', 'alg': 'RS256'}]}
    rotated = {'keys': initial['keys'] + [{**public, 'kid': 'rotated', 'use': 'sig', 'alg': 'RS256'}]}
    # Exercise the real PyJWT parser/cache; replace only its HTTP transport.
    transport = Mock(open=Mock(side_effect=[io.StringIO(json.dumps(initial)), io.StringIO(json.dumps(rotated))]))
    with patch('app.core.cognito.monotonic', return_value=100) as clock, \
            patch('jwt.jwks_client.urllib.request.build_opener', return_value=transport):
        v = CognitoVerifier(ISSUER, CLIENT)
        for n in range(20):
            signed = jwt.encode(claims(), key, algorithm='RS256', headers={'kid': f'unknown-{n}'})
            with pytest.raises(jwt.InvalidTokenError):
                v.verify(signed)
        assert transport.open.call_count == 1
        assert v.verify(token(key, claims()))['sub'] == 'subject-123'
        clock.return_value = 131
        signed = jwt.encode(claims(), key, algorithm='RS256', headers={'kid': 'rotated'})
        assert v.verify(signed)['sub'] == 'subject-123'
        assert transport.open.call_count == 2


def test_jwks_failure_burst_is_throttled_and_later_retry_succeeds(key):
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    data = {'keys': [{**public, 'kid': 'test-key', 'use': 'sig', 'alg': 'RS256'}]}
    transport = Mock(open=Mock(side_effect=[URLError('offline'), io.StringIO(json.dumps(data))]))
    with patch('app.core.cognito.monotonic', return_value=100) as clock, \
            patch('jwt.jwks_client.urllib.request.build_opener', return_value=transport):
        v = CognitoVerifier(ISSUER, CLIENT)
        for _ in range(20):
            with pytest.raises(jwt.InvalidTokenError):
                v.verify(token(key, claims()))
        assert transport.open.call_count == 1
        clock.return_value = 131
        assert v.verify(token(key, claims()))['sub'] == 'subject-123'
        assert transport.open.call_count == 2


def test_concurrent_unknown_kids_share_one_http_attempt(key):
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    data = {'keys': [{**public, 'kid': 'test-key', 'use': 'sig', 'alg': 'RS256'}]}
    transport = Mock(open=Mock(side_effect=lambda *args, **kwargs: io.StringIO(json.dumps(data))))
    with patch('jwt.jwks_client.urllib.request.build_opener', return_value=transport):
        v = CognitoVerifier(ISSUER, CLIENT)
        def invalid(n):
            signed = jwt.encode(claims(), key, algorithm='RS256', headers={'kid': f'unknown-{n}'})
            with pytest.raises(jwt.InvalidTokenError):
                v.verify(signed)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(invalid, range(40)))
        assert transport.open.call_count == 1


@pytest.mark.parametrize("issuer", ["http://localhost/pool", "https://attacker.example.invalid/pool",
    ISSUER+"/", ISSUER+"?key=evil", "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-3_Other"])
def test_issuer_cannot_redirect_key_discovery(issuer):
    with pytest.raises(ValueError):
        CognitoVerifier(issuer, CLIENT)


def test_key_retrieval_failure_denies_access(key):
    v = verifier(key)
    v.keys.get_signing_key_from_jwt.side_effect = RuntimeError("unavailable")
    with pytest.raises(jwt.InvalidTokenError):
        v.verify(token(key, claims()))


def test_cognito_configuration_does_not_require_local_signing_key(monkeypatch):
    from app.core.config import Settings
    monkeypatch.delenv("AUTH_SECRET_KEY")
    s = Settings(auth_provider="cognito", cognito_issuer=ISSUER, cognito_client_id=CLIENT, _env_file=None)
    assert s.auth_secret_key is None


@pytest.mark.parametrize("field", ["cognito_issuer", "cognito_client_id"])
def test_cognito_requires_explicit_pool_and_client(field):
    from app.core.config import Settings
    from pydantic import ValidationError
    values = dict(auth_provider="cognito", cognito_issuer=ISSUER, cognito_client_id=CLIENT)
    values[field] = ""
    with pytest.raises(ValidationError):
        Settings(**values, _env_file=None)


def test_local_password_login_is_disabled_in_cognito_mode(monkeypatch):
    from app.api.routes import auth
    from app.schemas.auth import LoginRequest
    from fastapi import HTTPException
    monkeypatch.setattr(auth, "get_settings", lambda: SimpleNamespace(auth_provider="cognito"))
    database = Mock()
    with pytest.raises(HTTPException) as exc:
        auth.login(LoginRequest(email="operator@example.com", password="synthetic-password"), database)
    assert exc.value.status_code == 403
    database.fetch_user_by_email.assert_not_called()


@pytest.mark.parametrize("known", [True, False])
def test_access_token_subject_requires_existing_local_identity(monkeypatch, known):
    from app.api import dependencies
    from fastapi import HTTPException
    database = Mock()
    database.fetch_user_by_id.return_value = {"id": "subject-123"} if known else None
    settings = SimpleNamespace(auth_provider="cognito", cognito_issuer=ISSUER)
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    verifier = Mock(verify=Mock(return_value={"sub": "subject-123", "email": "operator@example.com"}))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=database, cognito_verifier=verifier)))
    if known:
        assert dependencies.get_current_user(request, ["Bearer synthetic-token"])["id"] == "subject-123"
    else:
        with pytest.raises(HTTPException) as exc:
            dependencies.get_current_user(request, ["Bearer synthetic-token"])
        assert exc.value.status_code == 401
    database.fetch_user_by_id.assert_called_once_with("subject-123")
    database.fetch_user_by_email.assert_not_called()
