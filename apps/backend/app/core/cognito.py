"""Cognito access-token verification. Tenant authority stays in the database."""
import re
from threading import RLock
from time import monotonic

import jwt


class BoundedJWKClient(jwt.PyJWKClient):
    """One HTTP attempt per issuer/client per 30s, including failed attempts.

    No per-kid negative cache: attacker-controlled IDs consume constant memory.
    Key rotation may take up to 30s to discover. The normal JWKS TTL stays 300s.
    This also covers supported PyJWT versions without a native cooldown.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fetch_lock = RLock()
        self._attempt_at = float('-inf')
        self._success_at = float('-inf')
        self._payload = None

    def fetch_data(self):
        with self._fetch_lock:
            now = monotonic()
            if now - self._attempt_at < 30:
                if self._payload is None or now - self._success_at >= 300:
                    raise jwt.PyJWKClientError('JWKS refresh temporarily unavailable')
                return self._payload
            self._attempt_at = now  # Also throttle timeouts, outages and invalid JWKS.
            payload = super().fetch_data()
            jwt.PyJWKSet.from_dict(payload)  # Do not retain malformed remote data.
            self._payload, self._success_at = payload, monotonic()
            return payload

    def get_signing_key(self, kid):
        # Do not depend on version-specific PyJWT unknown-kid refresh behavior.
        # Serialise cache lookup + refresh, not only concurrent HTTP requests.
        with self._fetch_lock:
            for refresh in (False, True):
                keys = self.get_signing_keys(refresh=refresh)
                for key in keys:
                    if key.key_id == kid:
                        return key
        raise jwt.PyJWKClientError('Unknown signing key')


def validate_issuer(issuer: str) -> str:
    if not re.fullmatch(
        r"https://cognito-idp\.(?P<region>[a-z]{2}-[a-z]+-[0-9])\.amazonaws\.com/(?P=region)_[A-Za-z0-9]+",
        issuer,
    ):
        raise ValueError("An exact Cognito user-pool issuer is required")
    return issuer


class CognitoVerifier:
    def __init__(self, issuer: str, client_id: str):
        self.issuer = validate_issuer(issuer)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", client_id):
            raise ValueError("An explicit Cognito app client is required")
        self.client_id = client_id
        self.keys = BoundedJWKClient(
            f"{self.issuer}/.well-known/jwks.json",
            cache_jwk_set=True, lifespan=300, timeout=5,
        )

    def verify(self, token: str) -> dict:
        try:
            if not isinstance(token, str) or not 1 <= len(token) <= 16384:
                raise jwt.InvalidTokenError()
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str) or not 1 <= len(header["kid"]) <= 256:
                raise jwt.InvalidTokenError()
            key = self.keys.get_signing_key_from_jwt(token).key
            payload = jwt.decode(token, key, algorithms=["RS256"], issuer=self.issuer,
                options={"verify_aud": False,
                         "require": ["iss", "sub", "iat", "exp", "token_use", "client_id"]})
            # Cognito access tokens identify the app with client_id; ID tokens
            # use aud and are deliberately not accepted as API credentials.
            if (payload["token_use"] != "access" or payload["client_id"] != self.client_id
                    or not isinstance(payload["sub"], str) or not payload["sub"]
                    or type(payload["iat"]) is not int or type(payload["exp"]) is not int
                    or payload["iat"] < 0 or payload["exp"] <= payload["iat"]):
                raise jwt.InvalidTokenError()
            return payload
        except Exception:
            # Never propagate token content, remote response bodies or SDK
            # errors. Key rotation uses the bounded JWKS refresh above.
            raise jwt.InvalidTokenError("Invalid Cognito access token.") from None
