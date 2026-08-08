#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/processor"))

from app.clients.azure_cost import (  # noqa: E402
    AzureCostClient,
    AzureCostEmptyPageError,
    AzureCostHttpError,
    AzureCostResponseError,
    AzureCostTimeoutError,
    HttpResponse,
    UrllibTransport,
)
from app.core.config import Settings  # noqa: E402


CASES_PATH = ROOT / "docs/api/azure-cost-query-contract-cases.json"


class OneShotScenarioTransport:
    def __init__(self, scenario: str):
        self.scenario = scenario
        self.delegate = UrllibTransport()
        self.calls = 0

    def post(
        self,
        url: str,
        *,
        body: bytes,
        headers: Mapping[str, str],
        timeout: float,
    ) -> HttpResponse:
        self.calls += 1
        request_headers = dict(headers)
        if self.calls == 1:
            request_headers["X-Fake-Azure-Scenario"] = self.scenario
        return self.delegate.post(
            url,
            body=body,
            headers=request_headers,
            timeout=timeout,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the Azure cost ingestion client")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", default="jupiter-local-token")
    parser.add_argument("--subscription-id")
    return parser.parse_args()


def make_settings(args: argparse.Namespace, **updates) -> Settings:
    values = {
        "azure_cost_api_base_url": args.base_url,
        "azure_cost_api_token": args.token,
        "azure_cost_api_timeout_seconds": 5,
        "azure_cost_api_max_retries": 2,
        "azure_cost_api_retry_backoff_seconds": 0.05,
    }
    values.update(updates)
    return Settings(**values)


def load_request(args: argparse.Namespace) -> tuple[str, dict]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    definition = next(
        case["request"]
        for case in cases["cases"]
        if case["id"] == "daily-cost-by-resource-group"
    )
    return args.subscription_id or cases["knownSubscriptionId"], definition


def expect_error(callable_, error_type, message: str | None = None):
    try:
        callable_()
    except error_type as exc:
        if message is not None:
            assert message in str(exc), str(exc)
        return exc
    raise AssertionError(f"Expected {error_type.__name__}")


def main() -> None:
    args = parse_args()
    subscription_id, definition = load_request(args)

    normal = AzureCostClient(make_settings(args)).query_all(subscription_id, definition)
    assert len(normal.rows) == 30
    assert normal.page_count == 3
    assert normal.retry_count == 0

    unauthorized = AzureCostClient(
        make_settings(args, azure_cost_api_token="wrong-token")
    )
    error = expect_error(
        lambda: unauthorized.query_all(subscription_id, definition),
        AzureCostHttpError,
    )
    assert error.status_code == 401

    rate_limit_sleeps = []

    def rate_limit_sleep(delay: float) -> None:
        rate_limit_sleeps.append(delay)
        time.sleep(delay)

    rate_limited = AzureCostClient(
        make_settings(args),
        transport=OneShotScenarioTransport("rate-limit"),
        sleeper=rate_limit_sleep,
    ).query_all(subscription_id, definition)
    assert rate_limited.retry_count == 1
    assert rate_limit_sleeps == [1.0]

    server_error_sleeps = []
    server_error = AzureCostClient(
        make_settings(args),
        transport=OneShotScenarioTransport("server-error"),
        sleeper=server_error_sleeps.append,
    ).query_all(subscription_id, definition)
    assert server_error.retry_count == 1
    assert server_error_sleeps == [0.05]

    expect_error(
        lambda: AzureCostClient(
            make_settings(args),
            transport=OneShotScenarioTransport("empty-page"),
        ).query_all(subscription_id, definition),
        AzureCostEmptyPageError,
        "empty intermediate page",
    )
    expect_error(
        lambda: AzureCostClient(
            make_settings(args),
            transport=OneShotScenarioTransport("invalid-data"),
        ).query_all(subscription_id, definition),
        AzureCostResponseError,
        "non-numeric PreTaxCost",
    )
    expect_error(
        lambda: AzureCostClient(
            make_settings(args, azure_cost_api_timeout_seconds=0.2),
            transport=OneShotScenarioTransport("timeout"),
        ).query_all(subscription_id, definition),
        AzureCostTimeoutError,
        "timed out",
    )

    print(
        json.dumps(
            {
                "baseUrl": args.base_url,
                "rows": len(normal.rows),
                "pages": normal.page_count,
                "auth401": True,
                "rateLimitRetry": rate_limited.retry_count,
                "retryAfterSeconds": rate_limit_sleeps[0],
                "serverErrorRetry": server_error.retry_count,
                "timeoutDetected": True,
                "emptyPageDetected": True,
                "invalidDataDetected": True,
                "status": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
