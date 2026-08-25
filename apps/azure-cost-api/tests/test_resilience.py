import time
from copy import deepcopy
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from test_query_api import CASES_BY_ID, QUERY_PATH


QUERY_URL = f"{QUERY_PATH}?api-version=2025-03-01"
BODY = CASES_BY_ID["daily-cost-by-resource-group"]["request"]


def post(client, *, body=BODY, headers=None, url=QUERY_URL):
    return client.post(url, json=body, headers=headers or {})


def test_missing_token_returns_401_with_challenge(secure_client):
    response = post(secure_client)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "AuthenticationFailed"


def test_operational_endpoints_do_not_require_authentication(secure_client):
    assert secure_client.get("/health").status_code == 200
    assert secure_client.get("/openapi.json").status_code == 200


def test_invalid_token_never_leaks_configured_value(secure_client):
    response = post(secure_client, headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401
    assert "test-valid-token" not in response.text


def test_forbidden_identity_returns_403(secure_client):
    response = post(
        secure_client,
        headers={"Authorization": "Bearer test-forbidden-token"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AuthorizationFailed"


def test_valid_token_allows_query(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()["properties"]["rows"]) == 2


def test_bearer_scheme_is_case_insensitive(secure_client):
    response = post(
        secure_client,
        headers={"Authorization": "bEaReR test-valid-token"},
    )

    assert response.status_code == 200


def test_pagination_collects_every_row_without_duplicates(secure_client, auth_headers):
    rows = []
    next_link = QUERY_URL

    while next_link:
        response = post(secure_client, headers=auth_headers, url=next_link)
        assert response.status_code == 200
        properties = response.json()["properties"]
        assert len(properties["rows"]) <= 2
        rows.extend(properties["rows"])
        next_link = properties["nextLink"]

    assert len(rows) == 30
    assert len({tuple(row) for row in rows}) == 30


def test_next_link_preserves_version_and_uses_opaque_token(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)
    next_link = response.json()["properties"]["nextLink"]
    query = parse_qs(urlsplit(next_link).query)

    assert query["api-version"] == ["2025-03-01"]
    assert len(query["$skiptoken"][0].split(".")) == 2


def test_tampered_skip_token_is_rejected(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)
    next_link = response.json()["properties"]["nextLink"]
    parts = urlsplit(next_link)
    query = parse_qs(parts.query)
    query["$skiptoken"] = [query["$skiptoken"][0] + "tampered"]
    tampered = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment)
    )

    response = post(secure_client, headers=auth_headers, url=tampered)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


@pytest.mark.parametrize("token", ["", "opaque", "invalid.signature", "a.b.c"])
def test_malformed_skip_token_is_rejected(secure_client, auth_headers, token):
    url = f"{QUERY_URL}&{urlencode({'$skiptoken': token})}"

    response = post(secure_client, headers=auth_headers, url=url)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


def test_skip_token_is_bound_to_request_body(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)
    next_link = response.json()["properties"]["nextLink"]
    changed_body = deepcopy(BODY)
    changed_body["dataset"]["granularity"] = "None"

    response = post(
        secure_client,
        body=changed_body,
        headers=auth_headers,
        url=next_link,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


def test_skip_token_is_bound_to_subscription(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)
    next_link = response.json()["properties"]["nextLink"]
    current_subscription = QUERY_PATH.split("/")[2]
    other_subscription = next(
        item
        for item in secure_client.app.state.repository.subscription_ids
        if item.casefold() != current_subscription.casefold()
    )
    changed_subscription_url = next_link.replace(current_subscription, other_subscription)

    response = post(secure_client, headers=auth_headers, url=changed_subscription_url)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


def test_skip_token_is_invalidated_when_signing_secret_changes(
    secure_client,
    secure_settings,
    auth_headers,
):
    next_link = post(secure_client, headers=auth_headers).json()["properties"]["nextLink"]
    rotated = secure_settings.model_copy(
        update={"azure_cost_skiptoken_secret": "rotated-unit-test-secret"}
    )

    with TestClient(create_app(rotated)) as rotated_client:
        response = post(rotated_client, headers=auth_headers, url=next_link)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


def test_skip_token_is_invalidated_by_dataset_change(secure_client, auth_headers):
    response = post(secure_client, headers=auth_headers)
    next_link = response.json()["properties"]["nextLink"]
    secure_client.app.state.repository.dataset_checksum = "changed-checksum"

    response = post(secure_client, headers=auth_headers, url=next_link)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"


def test_rate_limit_scenario_returns_retry_after(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "rate-limit"}
    response = post(secure_client, headers=headers)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "3"
    assert response.json()["error"]["code"] == "TooManyRequests"


def test_server_error_scenario_returns_500(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "server-error"}
    response = post(secure_client, headers=headers)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "InternalServerError"


def test_timeout_scenario_delays_then_returns_data(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "timeout"}
    started = time.perf_counter()
    response = post(secure_client, headers=headers)
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert elapsed >= 0.008


def test_empty_page_scenario_preserves_continuation(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "empty-page"}
    response = post(secure_client, headers=headers)
    properties = response.json()["properties"]

    assert response.status_code == 200
    assert properties["rows"] == []
    assert properties["nextLink"] is not None


def test_invalid_data_scenario_corrupts_numeric_cell(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "invalid-data"}
    response = post(secure_client, headers=headers)

    assert response.status_code == 200
    assert response.json()["properties"]["rows"][0][0] == "INVALID_COST"


def test_unsupported_scenario_returns_400(secure_client, auth_headers):
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "surprise"}
    response = post(secure_client, headers=headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BadRequest"


def test_default_scenario_is_configurable(secure_settings, auth_headers):
    configured = secure_settings.model_copy(
        update={"azure_cost_default_scenario": "server-error"}
    )
    with TestClient(create_app(configured)) as client:
        response = post(client, headers=auth_headers)

    assert response.status_code == 500


def test_request_scenario_overrides_configured_default(secure_settings, auth_headers):
    configured = secure_settings.model_copy(
        update={"azure_cost_default_scenario": "server-error"}
    )
    headers = {**auth_headers, "X-Fake-Azure-Scenario": "normal"}

    with TestClient(create_app(configured)) as client:
        response = post(client, headers=headers)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "overrides",
    [
        {"azure_cost_page_size": 0},
        {"azure_cost_page_size": 1001},
        {"azure_cost_fake_timeout_seconds": 31},
        {"azure_cost_retry_after_seconds": -1},
        {"azure_cost_skiptoken_secret": "too-short"},
        {"azure_cost_default_scenario": "unexpected"},
        {"azure_cost_auth_enabled": True, "azure_cost_valid_tokens": "  "},
        {
            "azure_cost_valid_tokens": "shared-identity",
            "azure_cost_forbidden_tokens": "shared-identity",
        },
    ],
)
def test_unsafe_or_unsupported_settings_are_rejected(secure_settings, overrides):
    with pytest.raises(ValidationError):
        Settings(**(secure_settings.model_dump() | overrides))
