import asyncio

import httpx
from fastapi import FastAPI

from app.core.metrics import MetricsMiddleware, metrics_router


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)
    app.include_router(metrics_router)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return app


def _call(app: FastAPI, method: str, path: str) -> httpx.Response:
    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.request(method, path)

    return asyncio.run(call())


def test_metrics_endpoint_returns_prometheus_text():
    app = _build_app()

    response = _call(app, "GET", "/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_successful_request_increments_http_requests_counter():
    app = _build_app()

    _call(app, "GET", "/ping")
    metrics_response = _call(app, "GET", "/metrics")

    body = metrics_response.text
    assert 'backend_http_requests_total{method="GET",path="/ping",status_code="200"}' in body
