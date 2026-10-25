from __future__ import annotations

import asyncio
from enum import Enum

from app.config import Settings
from app.errors import ApiError
from app.models import QueryProperties


SCENARIO_HEADER = "X-Fake-Azure-Scenario"


class Scenario(str, Enum):
    normal = "normal"
    rate_limit = "rate-limit"
    server_error = "server-error"
    timeout = "timeout"
    empty_page = "empty-page"
    invalid_data = "invalid-data"


def resolve_scenario(requested: str | None, default: str) -> Scenario:
    try:
        return Scenario(requested or default)
    except ValueError:
        supported = ", ".join(item.value for item in Scenario)
        raise ApiError(
            400,
            "BadRequest",
            f"Unsupported fake scenario. Use one of: {supported}.",
        ) from None


async def apply_before_query(scenario: Scenario, settings: Settings) -> None:
    if scenario is Scenario.rate_limit:
        raise ApiError(
            429,
            "TooManyRequests",
            "The simulated Azure endpoint is throttling requests.",
            headers={"Retry-After": str(settings.azure_cost_retry_after_seconds)},
        )
    if scenario is Scenario.server_error:
        raise ApiError(
            500,
            "InternalServerError",
            "The simulated Azure endpoint encountered an internal error.",
        )
    if scenario is Scenario.timeout:
        await asyncio.sleep(settings.azure_cost_fake_timeout_seconds)


def apply_after_query(scenario: Scenario, properties: QueryProperties) -> QueryProperties:
    if scenario is Scenario.empty_page:
        return properties.model_copy(update={"rows": []})
    if scenario is Scenario.invalid_data:
        invalid_rows = [list(row) for row in properties.rows]
        if invalid_rows:
            invalid_rows[0][0] = "INVALID_COST"
        else:
            invalid_rows = [["INVALID_COST"]]
        return properties.model_copy(update={"rows": invalid_rows})
    return properties
