from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth import authenticate
from app.config import Settings, get_settings
from app.errors import ApiError, error_payload
from app.models import QueryDefinition, QueryResult
from app.pagination import Paginator, query_fingerprint
from app.query_engine import QueryEngine
from app.repository import CostRepository
from app.scenarios import (
    SCENARIO_HEADER,
    apply_after_query,
    apply_before_query,
    resolve_scenario,
)


API_VERSION = "2025-03-01"
QUERY_NAMESPACE = uuid.UUID("0b9c5cc2-f7b1-41bd-a05c-627123f3b2bf")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    paginator = Paginator(
        page_size=resolved_settings.azure_cost_page_size,
        secret=resolved_settings.azure_cost_skiptoken_secret,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = CostRepository(
            resolved_settings.azure_cost_dataset_path,
            resolved_settings.azure_cost_mapping_path,
        )
        app.state.repository = repository
        app.state.query_engine = QueryEngine(repository)
        yield

    app = FastAPI(
        title="Economicon Azure Cost API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
        openapi_url=None,
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        messages = [error["msg"] for error in exc.errors()]
        return JSONResponse(
            status_code=400,
            content=error_payload("BadRequest", "; ".join(messages)),
        )

    @app.get("/health", tags=["operations"])
    def health(request: Request) -> dict:
        repository: CostRepository = request.app.state.repository
        return {
            "status": "ok",
            "dataset": repository.dataset_path.name,
            "rows": len(repository.records),
            "subscriptions": len(repository.subscription_ids),
        }

    @app.get("/openapi.json", include_in_schema=False)
    def contractual_openapi() -> dict:
        return json.loads(resolved_settings.azure_cost_openapi_path.read_text(encoding="utf-8"))

    @app.post(
        "/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query",
        response_model=QueryResult,
        response_model_by_alias=True,
        tags=["cost-management"],
    )
    async def query_subscription_usage(
        request: Request,
        definition: QueryDefinition,
        subscription_id: Annotated[str, Path(min_length=1)],
        api_version: Annotated[str, Query(alias="api-version")],
        skip_token: Annotated[str | None, Query(alias="$skiptoken")] = None,
    ) -> QueryResult:
        authenticate(request.headers.get("Authorization"), resolved_settings)
        if api_version != API_VERSION:
            raise ApiError(400, "BadRequest", f"Only api-version={API_VERSION} is supported.")

        scenario = resolve_scenario(
            request.headers.get(SCENARIO_HEADER),
            resolved_settings.azure_cost_default_scenario,
        )
        await apply_before_query(scenario, resolved_settings)

        engine: QueryEngine = request.app.state.query_engine
        properties = engine.execute(subscription_id, definition)
        fingerprint = query_fingerprint(
            subscription_id,
            definition,
            request.app.state.repository.dataset_checksum,
        )
        offset = paginator.decode_offset(skip_token, fingerprint)
        properties = paginator.paginate(
            properties,
            offset=offset,
            fingerprint=fingerprint,
            request_url=str(request.url),
        )
        properties = apply_after_query(scenario, properties)
        canonical = json.dumps(
            {
                "subscriptionId": subscription_id.casefold(),
                "definition": definition.model_dump(mode="json", by_alias=True),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        query_id = str(uuid.uuid5(QUERY_NAMESPACE, canonical))
        return QueryResult(
            id=(
                f"/subscriptions/{subscription_id}/providers/"
                f"Microsoft.CostManagement/Query/{query_id}"
            ),
            name=query_id,
            type="microsoft.costmanagement/Query",
            properties=properties,
        )

    return app


app = create_app()
