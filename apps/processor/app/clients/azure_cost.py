from __future__ import annotations

import json
import logging
import math
import socket
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

from app.core.config import Settings


logger = logging.getLogger(__name__)


class AzureCostClientError(RuntimeError):
    """Base class for safe, actionable Azure cost ingestion failures."""


class AzureCostHttpError(AzureCostClientError):
    def __init__(self, status_code: int, error_code: str):
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(f"Azure Cost API returned HTTP {status_code} ({error_code})")


class AzureCostTimeoutError(AzureCostClientError):
    pass


class AzureCostResponseError(AzureCostClientError):
    pass


class AzureCostEmptyPageError(AzureCostResponseError):
    pass


class AzureCostNextLinkError(AzureCostResponseError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class HttpTransport(Protocol):
    def post(
        self,
        url: str,
        *,
        body: bytes,
        headers: Mapping[str, str],
        timeout: float,
    ) -> HttpResponse: ...


class UrllibTransport:
    def post(
        self,
        url: str,
        *,
        body: bytes,
        headers: Mapping[str, str],
        timeout: float,
    ) -> HttpResponse:
        request = Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                return HttpResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=response.read(),
                )
        except HTTPError as exc:
            return HttpResponse(
                status_code=exc.code,
                headers=dict(exc.headers),
                body=exc.read(),
            )
        except (TimeoutError, socket.timeout) as exc:
            raise AzureCostTimeoutError("Azure Cost API request timed out") from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise AzureCostTimeoutError("Azure Cost API request timed out") from exc
            raise AzureCostClientError("Azure Cost API connection failed") from exc


@dataclass(frozen=True)
class CostColumn:
    name: str
    type: str


@dataclass(frozen=True)
class AzureCostQueryResult:
    columns: tuple[CostColumn, ...]
    rows: tuple[dict[str, int | float | str], ...]
    page_count: int
    retry_count: int


@dataclass(frozen=True)
class _ValidatedPage:
    columns: tuple[CostColumn, ...]
    rows: tuple[dict[str, int | float | str], ...]
    next_link: str | None


class AzureCostClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: HttpTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.base_url = settings.azure_cost_api_base_url
        self.api_version = settings.azure_cost_api_version
        self.token = settings.azure_cost_api_token.get_secret_value()
        self.timeout = settings.azure_cost_api_timeout_seconds
        self.max_retries = settings.azure_cost_api_max_retries
        self.retry_backoff = settings.azure_cost_api_retry_backoff_seconds
        self.max_retry_after = settings.azure_cost_api_max_retry_after_seconds
        self.max_pages = settings.azure_cost_api_max_pages
        self.transport = transport or UrllibTransport()
        self.sleeper = sleeper
        self._origin = _origin(self.base_url)

    def query_all(self, subscription_id: str, definition: Mapping) -> AzureCostQueryResult:
        body = json.dumps(definition, separators=(",", ":")).encode("utf-8")
        next_link: str | None = self._query_url(subscription_id)
        expected_columns: tuple[CostColumn, ...] | None = None
        rows: list[dict[str, int | float | str]] = []
        visited: set[str] = set()
        page_count = 0
        retry_count = 0

        while next_link is not None:
            if page_count >= self.max_pages:
                raise AzureCostResponseError("Azure Cost API exceeded the configured page limit")
            request_url = self._safe_next_link(next_link)
            if request_url in visited:
                raise AzureCostResponseError("Azure Cost API returned a pagination cycle")
            visited.add(request_url)
            page_count += 1

            _log("azure_cost_request", attempt=1, page=page_count, path=urlsplit(request_url).path)
            response, retries = self._post_with_retries(request_url, body, page_count)
            retry_count += retries
            page = self._validate_page(response.body)

            if expected_columns is None:
                expected_columns = page.columns
            elif page.columns != expected_columns:
                raise AzureCostResponseError("Azure Cost API columns changed between pages")
            if not page.rows and page.next_link is not None:
                raise AzureCostEmptyPageError(
                    "Azure Cost API returned an empty intermediate page"
                )

            rows.extend(page.rows)
            _log(
                "azure_cost_page_received",
                page=page_count,
                row_count=len(page.rows),
                has_next_link=page.next_link is not None,
            )
            next_link = page.next_link

        assert expected_columns is not None
        _log(
            "azure_cost_ingestion_completed",
            page_count=page_count,
            retry_count=retry_count,
            row_count=len(rows),
        )
        return AzureCostQueryResult(
            columns=expected_columns,
            rows=tuple(rows),
            page_count=page_count,
            retry_count=retry_count,
        )

    def _query_url(self, subscription_id: str) -> str:
        scope = quote(subscription_id, safe="")
        return (
            f"{self.base_url}/subscriptions/{scope}/providers/"
            f"Microsoft.CostManagement/query?api-version={quote(self.api_version, safe='')}"
        )

    def _safe_next_link(self, value: str) -> str:
        resolved = urljoin(f"{self.base_url}/", value)
        if _origin(resolved) != self._origin:
            raise AzureCostNextLinkError("Azure Cost API nextLink changed origin")
        return resolved

    def _post_with_retries(
        self,
        url: str,
        body: bytes,
        page: int,
    ) -> tuple[HttpResponse, int]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        retries = 0
        while True:
            response = self.transport.post(
                url,
                body=body,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response, retries
            if response.status_code not in {429, 500} or retries >= self.max_retries:
                raise AzureCostHttpError(
                    response.status_code,
                    _error_code(response.body),
                )

            delay = self._retry_delay(response, retries)
            retries += 1
            _log(
                "azure_cost_retry",
                attempt=retries + 1,
                delay_seconds=delay,
                page=page,
                status_code=response.status_code,
            )
            self.sleeper(delay)

    def _retry_delay(self, response: HttpResponse, retry_index: int) -> float:
        if response.status_code == 429:
            retry_after = _header(response.headers, "Retry-After")
            if retry_after is not None:
                try:
                    return min(max(float(retry_after), 0.0), self.max_retry_after)
                except ValueError:
                    pass
        return self.retry_backoff * (2**retry_index)

    @staticmethod
    def _validate_page(body: bytes) -> _ValidatedPage:
        try:
            payload = json.loads(body)
            properties = payload["properties"]
            raw_columns = properties["columns"]
            raw_rows = properties["rows"]
            next_link = properties.get("nextLink")
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise AzureCostResponseError("Azure Cost API returned malformed JSON") from exc

        if not isinstance(raw_columns, list) or not raw_columns:
            raise AzureCostResponseError("Azure Cost API returned no columns")
        columns: list[CostColumn] = []
        for raw_column in raw_columns:
            if not isinstance(raw_column, dict):
                raise AzureCostResponseError("Azure Cost API returned an invalid column")
            name = raw_column.get("name")
            column_type = raw_column.get("type")
            if not isinstance(name, str) or not name or column_type not in {"Number", "String"}:
                raise AzureCostResponseError("Azure Cost API returned an invalid column")
            columns.append(CostColumn(name=name, type=column_type))
        names = [column.name for column in columns]
        if len(names) != len(set(names)):
            raise AzureCostResponseError("Azure Cost API returned duplicate columns")
        if "PreTaxCost" not in names or "Currency" not in names:
            raise AzureCostResponseError("Azure Cost API omitted required cost columns")

        if not isinstance(raw_rows, list):
            raise AzureCostResponseError("Azure Cost API rows must be an array")
        validated_rows = []
        for raw_row in raw_rows:
            if not isinstance(raw_row, list) or len(raw_row) != len(columns):
                raise AzureCostResponseError("Azure Cost API row does not match columns")
            values: dict[str, int | float | str] = {}
            for column, value in zip(columns, raw_row, strict=True):
                _validate_cell(column, value)
                values[column.name] = value
            validated_rows.append(values)

        if next_link is not None and (not isinstance(next_link, str) or not next_link):
            raise AzureCostResponseError("Azure Cost API returned an invalid nextLink")
        return _ValidatedPage(
            columns=tuple(columns),
            rows=tuple(validated_rows),
            next_link=next_link,
        )


def _validate_cell(column: CostColumn, value: object) -> None:
    if column.type == "Number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AzureCostResponseError(
                f"Azure Cost API returned a non-numeric {column.name} value"
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise AzureCostResponseError(
                f"Azure Cost API returned a non-finite {column.name} value"
            )
    elif not isinstance(value, str):
        raise AzureCostResponseError(
            f"Azure Cost API returned a non-string {column.name} value"
        )


def _origin(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    return parsed.scheme.casefold(), parsed.netloc.casefold()


def _header(headers: Mapping[str, str], name: str) -> str | None:
    expected = name.casefold()
    return next((value for key, value in headers.items() if key.casefold() == expected), None)


def _error_code(body: bytes) -> str:
    try:
        code = json.loads(body).get("error", {}).get("code")
        return code if isinstance(code, str) and code else "UnknownError"
    except (AttributeError, json.JSONDecodeError):
        return "UnknownError"


def _log(event: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, **fields}, sort_keys=True))
