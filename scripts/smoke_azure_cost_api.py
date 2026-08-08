#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "docs/api/azure-cost-query-contract-cases.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test for the simulated Azure Cost API")
    parser.add_argument("--base-url", required=True, help="Example: http://dockerserver:18003")
    parser.add_argument("--token", default="jupiter-local-token")
    parser.add_argument("--forbidden-token", default="jupiter-forbidden-token")
    parser.add_argument("--expected-page-size", type=int, default=10)
    parser.add_argument("--expected-delay", type=float, default=2.0)
    return parser.parse_args()


def send(
    url: str,
    body: dict,
    *,
    token: str | None,
    scenario: str | None = None,
) -> tuple[int, dict, dict[str, str], float]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if scenario is not None:
        headers["X-Fake-Azure-Scenario"] = scenario
    request = Request(
        url,
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
            return response.status, payload, dict(response.headers), time.perf_counter() - started
    except HTTPError as exc:
        payload = json.load(exc)
        return exc.code, payload, dict(exc.headers), time.perf_counter() - started


def expect_error(result: tuple, status: int, code: str) -> None:
    actual_status, payload, _headers, _elapsed = result
    assert actual_status == status, (actual_status, payload)
    assert payload["error"]["code"] == code, payload


def header_value(headers: dict[str, str], name: str) -> str | None:
    expected = name.casefold()
    return next((value for key, value in headers.items() if key.casefold() == expected), None)


def main() -> None:
    args = parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    body = next(
        case["request"]
        for case in cases["cases"]
        if case["id"] == "daily-cost-by-resource-group"
    )
    query_url = (
        f"{args.base_url.rstrip('/')}/subscriptions/{cases['knownSubscriptionId']}"
        "/providers/Microsoft.CostManagement/query?api-version=2025-03-01"
    )

    expect_error(send(query_url, body, token=None), 401, "AuthenticationFailed")
    expect_error(send(query_url, body, token="wrong-token"), 401, "AuthenticationFailed")
    expect_error(
        send(query_url, body, token=args.forbidden_token),
        403,
        "AuthorizationFailed",
    )

    all_rows: list[list] = []
    page_count = 0
    next_link: str | None = query_url
    first_next_link: str | None = None
    while next_link:
        status, payload, _headers, _elapsed = send(next_link, body, token=args.token)
        assert status == 200, payload
        properties = payload["properties"]
        assert len(properties["rows"]) <= args.expected_page_size
        all_rows.extend(properties["rows"])
        page_count += 1
        next_link = properties["nextLink"]
        if first_next_link is None:
            first_next_link = next_link

    assert len(all_rows) == 30, len(all_rows)
    assert len({json.dumps(row, sort_keys=True) for row in all_rows}) == 30
    assert first_next_link is not None
    expect_error(
        send(first_next_link + "tampered", body, token=args.token),
        400,
        "InvalidSkipToken",
    )

    rate_limit = send(query_url, body, token=args.token, scenario="rate-limit")
    expect_error(rate_limit, 429, "TooManyRequests")
    assert header_value(rate_limit[2], "Retry-After") == "1"
    expect_error(
        send(query_url, body, token=args.token, scenario="server-error"),
        500,
        "InternalServerError",
    )

    timeout_result = send(query_url, body, token=args.token, scenario="timeout")
    assert timeout_result[0] == 200, timeout_result[1]
    assert timeout_result[3] >= args.expected_delay * 0.8, timeout_result[3]

    empty_page = send(query_url, body, token=args.token, scenario="empty-page")
    assert empty_page[0] == 200, empty_page[1]
    assert empty_page[1]["properties"]["rows"] == []
    assert empty_page[1]["properties"]["nextLink"] is not None

    invalid_data = send(query_url, body, token=args.token, scenario="invalid-data")
    assert invalid_data[0] == 200, invalid_data[1]
    assert invalid_data[1]["properties"]["rows"][0][0] == "INVALID_COST"

    print(
        json.dumps(
            {
                "baseUrl": args.base_url,
                "rows": len(all_rows),
                "pages": page_count,
                "pageSize": args.expected_page_size,
                "auth": [401, 403],
                "errors": [429, 500],
                "timeoutSeconds": round(timeout_result[3], 3),
                "emptyPage": True,
                "invalidData": True,
                "status": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
