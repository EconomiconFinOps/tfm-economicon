from __future__ import annotations

import base64
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.errors import ApiError
from app.models import QueryDefinition, QueryProperties


def query_fingerprint(
    subscription_id: str,
    definition: QueryDefinition,
    dataset_checksum: str,
) -> str:
    canonical = json.dumps(
        {
            "dataset": dataset_checksum,
            "definition": definition.model_dump(mode="json", by_alias=True),
            "subscriptionId": subscription_id.casefold(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Paginator:
    def __init__(self, page_size: int, secret: str):
        self.page_size = page_size
        self.secret = secret.encode("utf-8")

    def decode_offset(self, token: str | None, expected_fingerprint: str) -> int:
        if token is None:
            return 0
        try:
            encoded_payload, encoded_signature = token.split(".", maxsplit=1)
            payload_bytes = _decode(encoded_payload)
            signature = _decode(encoded_signature)
            expected_signature = hmac.digest(self.secret, payload_bytes, "sha256")
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError
            payload = json.loads(payload_bytes)
            offset = payload["offset"]
            if (
                payload.get("version") != 1
                or payload.get("query") != expected_fingerprint
                or not isinstance(offset, int)
                or isinstance(offset, bool)
                or offset < 0
            ):
                raise ValueError
            return offset
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise ApiError(
                400,
                "InvalidSkipToken",
                "The $skiptoken is invalid for this query or dataset.",
            ) from None

    def paginate(
        self,
        properties: QueryProperties,
        *,
        offset: int,
        fingerprint: str,
        request_url: str,
    ) -> QueryProperties:
        end = min(offset + self.page_size, len(properties.rows))
        rows = properties.rows[offset:end]
        next_link = None
        if end < len(properties.rows):
            next_link = _replace_skip_token(request_url, self._encode(end, fingerprint))
        return QueryProperties(columns=properties.columns, rows=rows, next_link=next_link)

    def _encode(self, offset: int, fingerprint: str) -> str:
        payload = json.dumps(
            {"offset": offset, "query": fingerprint, "version": 1},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hmac.digest(self.secret, payload, "sha256")
        return f"{_encode(payload)}.{_encode(signature)}"


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _replace_skip_token(request_url: str, token: str) -> str:
    parts = urlsplit(request_url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key != "$skiptoken"]
    query.append(("$skiptoken", token))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
