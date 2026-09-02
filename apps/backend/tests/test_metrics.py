import asyncio
from unittest.mock import patch

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

    @app.get("/timed")
    async def timed():
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    return app


def _call(
    app: FastAPI,
    method: str,
    path: str,
    *,
    raise_app_exceptions: bool = True,
) -> httpx.Response:
    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=app,
                raise_app_exceptions=raise_app_exceptions,
            ),
            base_url="http://test",
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


def test_request_duration_uses_seconds_for_prometheus_buckets():
    app = _build_app()

    with patch("app.core.metrics.perf_counter", side_effect=[100.0, 100.25]):
        _call(app, "GET", "/timed")

    body = _call(app, "GET", "/metrics").text
    assert (
        'backend_http_request_duration_seconds_bucket{le="0.25",method="GET",path="/timed"} 1.0'
        in body
    )
    assert (
        'backend_http_request_duration_seconds_bucket{le="0.1",method="GET",path="/timed"} 0.0'
        in body
    )


def test_unhandled_exception_is_recorded_as_500():
    app = _build_app()

    response = _call(app, "GET", "/boom", raise_app_exceptions=False)

    assert response.status_code == 500
    body = _call(app, "GET", "/metrics").text
    assert (
        'backend_http_requests_total{method="GET",path="/boom",status_code="500"}' in body
    )


def test_unmatched_paths_share_a_bounded_label():
    app = _build_app()

    _call(app, "GET", "/missing-1")
    _call(app, "GET", "/missing-2")

    body = _call(app, "GET", "/metrics").text
    assert (
        'backend_http_requests_total{method="GET",path="__unmatched__",status_code="404"}'
        in body
    )
    assert 'path="/missing-1"' not in body
    assert 'path="/missing-2"' not in body
