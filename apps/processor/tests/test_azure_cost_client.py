import json
import logging

import pytest
from pydantic import ValidationError

from app.clients.azure_cost import (
    AzureCostClient,
    AzureCostEmptyPageError,
    AzureCostHttpError,
    AzureCostNextLinkError,
    AzureCostResponseError,
    AzureCostTimeoutError,
    HttpResponse,
)
from app.core.config import Settings


BASE_URL = "http://fake-azure.local:8002"
SUBSCRIPTION_ID = "64e355d7-997c-491d-b0c1-8414dccfcf42"
DEFINITION = {
    "type": "ActualCost",
    "timeframe": "MonthToDate",
    "dataset": {
        "granularity": "None",
        "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
    },
}
COLUMNS = [
    {"name": "PreTaxCost", "type": "Number"},
    {"name": "Currency", "type": "String"},
]


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def post(self, url, *, body, headers, timeout):
        self.requests.append(
            {"url": url, "body": body, "headers": dict(headers), "timeout": timeout}
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def settings(**updates) -> Settings:
    values = {
        "azure_cost_api_base_url": BASE_URL,
        "azure_cost_api_token": "super-secret-token",
        "azure_cost_api_timeout_seconds": 7.5,
        "azure_cost_api_max_retries": 3,
        "azure_cost_api_retry_backoff_seconds": 0.25,
        "azure_cost_api_max_retry_after_seconds": 30,
    }
    values.update(updates)
    return Settings(**values)


def response(
    rows,
    *,
    columns=COLUMNS,
    next_link=None,
    status=200,
    headers=None,
    error_code=None,
) -> HttpResponse:
    payload = (
        {"error": {"code": error_code, "message": "simulated"}}
        if status != 200
        else {
            "id": "query-id",
            "name": "query-name",
            "type": "microsoft.costmanagement/Query",
            "properties": {
                "columns": columns,
                "rows": rows,
                "nextLink": next_link,
            },
        }
    )
    return HttpResponse(
        status_code=status,
        headers=headers or {},
        body=json.dumps(payload).encode("utf-8"),
    )


def test_configurable_bearer_timeout_and_request_body_are_used():
    transport = FakeTransport([response([[12.5, "USD"]])])
    client = AzureCostClient(settings(), transport=transport)

    result = client.query_all(SUBSCRIPTION_ID, DEFINITION)

    request = transport.requests[0]
    assert request["headers"]["Authorization"] == "Bearer super-secret-token"
    assert request["timeout"] == 7.5
    assert json.loads(request["body"]) == DEFINITION
    assert result.rows == ({"PreTaxCost": 12.5, "Currency": "USD"},)


def test_all_pages_are_followed_and_combined():
    next_link = f"{BASE_URL}/next?api-version=2025-03-01&$skiptoken=opaque"
    transport = FakeTransport(
        [
            response([[1, "USD"]], next_link=next_link),
            response([[2, "USD"]]),
        ]
    )
    client = AzureCostClient(settings(), transport=transport)

    result = client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert [row["PreTaxCost"] for row in result.rows] == [1, 2]
    assert result.page_count == 2
    assert result.retry_count == 0
    assert transport.requests[1]["url"] == next_link


def test_429_respects_retry_after():
    transport = FakeTransport(
        [
            response([], status=429, headers={"Retry-After": "2"}, error_code="TooManyRequests"),
            response([[1, "USD"]]),
        ]
    )
    sleeps = []
    client = AzureCostClient(settings(), transport=transport, sleeper=sleeps.append)

    result = client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert sleeps == [2.0]
    assert result.retry_count == 1


def test_500_uses_exponential_backoff():
    transport = FakeTransport(
        [
            response([], status=500, error_code="InternalServerError"),
            response([], status=500, error_code="InternalServerError"),
            response([[1, "USD"]]),
        ]
    )
    sleeps = []
    client = AzureCostClient(settings(), transport=transport, sleeper=sleeps.append)

    result = client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert sleeps == [0.25, 0.5]
    assert result.retry_count == 2


def test_retry_after_is_bounded_by_configuration():
    transport = FakeTransport(
        [
            response([], status=429, headers={"Retry-After": "600"}, error_code="TooManyRequests"),
            response([[1, "USD"]]),
        ]
    )
    sleeps = []
    client = AzureCostClient(
        settings(azure_cost_api_max_retry_after_seconds=4),
        transport=transport,
        sleeper=sleeps.append,
    )

    client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert sleeps == [4.0]


def test_exhausted_retries_raise_safe_http_error():
    transport = FakeTransport(
        [
            response([], status=500, error_code="InternalServerError"),
            response([], status=500, error_code="InternalServerError"),
        ]
    )
    client = AzureCostClient(
        settings(azure_cost_api_max_retries=1),
        transport=transport,
        sleeper=lambda _delay: None,
    )

    with pytest.raises(AzureCostHttpError) as exc_info:
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "InternalServerError"


def test_401_is_not_retried():
    transport = FakeTransport(
        [response([], status=401, error_code="AuthenticationFailed")]
    )
    client = AzureCostClient(settings(), transport=transport)

    with pytest.raises(AzureCostHttpError) as exc_info:
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert exc_info.value.status_code == 401
    assert len(transport.requests) == 1


def test_timeout_is_reported_without_credentials():
    transport = FakeTransport([AzureCostTimeoutError("request timed out")])
    client = AzureCostClient(settings(), transport=transport)

    with pytest.raises(AzureCostTimeoutError, match="timed out") as exc_info:
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert "super-secret-token" not in str(exc_info.value)


def test_empty_intermediate_page_is_detected():
    transport = FakeTransport([response([], next_link=f"{BASE_URL}/next")])
    client = AzureCostClient(settings(), transport=transport)

    with pytest.raises(AzureCostEmptyPageError, match="empty intermediate page"):
        client.query_all(SUBSCRIPTION_ID, DEFINITION)


def test_empty_final_result_is_valid():
    transport = FakeTransport([response([])])
    client = AzureCostClient(settings(), transport=transport)

    result = client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert result.rows == ()
    assert result.page_count == 1


@pytest.mark.parametrize(
    "invalid_response, message",
    [
        (HttpResponse(200, {}, b"not-json"), "malformed JSON"),
        (response([[1]], columns=COLUMNS), "row does not match"),
        (response([["INVALID_COST", "USD"]]), "non-numeric PreTaxCost"),
        (response([[True, "USD"]]), "non-numeric PreTaxCost"),
        (response([[1, 2]]), "non-string Currency"),
        (
            response([[1, 2]], columns=[COLUMNS[0], COLUMNS[0]]),
            "duplicate columns",
        ),
        (
            response([[1]], columns=[{"name": "PreTaxCost", "type": "Number"}]),
            "omitted required cost columns",
        ),
    ],
)
def test_invalid_columns_and_rows_are_rejected(invalid_response, message):
    client = AzureCostClient(settings(), transport=FakeTransport([invalid_response]))

    with pytest.raises(AzureCostResponseError, match=message):
        client.query_all(SUBSCRIPTION_ID, DEFINITION)


def test_columns_must_be_stable_between_pages():
    transport = FakeTransport(
        [
            response([[1, "USD"]], next_link=f"{BASE_URL}/next"),
            response(
                [["USD", 2]],
                columns=[COLUMNS[1], COLUMNS[0]],
            ),
        ]
    )
    client = AzureCostClient(settings(), transport=transport)

    with pytest.raises(AzureCostResponseError, match="columns changed"):
        client.query_all(SUBSCRIPTION_ID, DEFINITION)


def test_cross_origin_next_link_is_rejected_before_sending_token():
    transport = FakeTransport(
        [response([[1, "USD"]], next_link="https://attacker.invalid/next")]
    )
    client = AzureCostClient(settings(), transport=transport)

    with pytest.raises(AzureCostNextLinkError, match="changed origin"):
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert len(transport.requests) == 1


def test_pagination_cycles_and_page_limit_are_detected():
    first_url = (
        f"{BASE_URL}/subscriptions/{SUBSCRIPTION_ID}/providers/"
        "Microsoft.CostManagement/query?api-version=2025-03-01"
    )
    cycle_transport = FakeTransport([response([[1, "USD"]], next_link=first_url)])

    with pytest.raises(AzureCostResponseError, match="pagination cycle"):
        AzureCostClient(settings(), transport=cycle_transport).query_all(
            SUBSCRIPTION_ID,
            DEFINITION,
        )

    limit_transport = FakeTransport([response([[1, "USD"]], next_link=f"{BASE_URL}/next")])
    with pytest.raises(AzureCostResponseError, match="page limit"):
        AzureCostClient(
            settings(azure_cost_api_max_pages=1),
            transport=limit_transport,
        ).query_all(SUBSCRIPTION_ID, DEFINITION)


def test_logs_are_json_and_do_not_contain_token_or_body(caplog):
    transport = FakeTransport([response([[1, "USD"]])])
    client = AzureCostClient(settings(), transport=transport)

    with caplog.at_level(logging.INFO, logger="app.clients.azure_cost"):
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    events = [json.loads(record.message) for record in caplog.records]
    assert {event["event"] for event in events} == {
        "azure_cost_request",
        "azure_cost_page_received",
        "azure_cost_ingestion_completed",
    }
    assert "super-secret-token" not in caplog.text
    assert "PreTaxCost" not in caplog.text


def test_settings_reject_credentials_in_url_and_invalid_timeout():
    with pytest.raises(ValidationError):
        settings(azure_cost_api_base_url="https://user:password@example.test")
    with pytest.raises(ValidationError):
        settings(azure_cost_api_timeout_seconds=0)
