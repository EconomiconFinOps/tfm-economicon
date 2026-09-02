import asyncio
import json

import httpx
import structlog
from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.request_context import RequestIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping():
        logger = structlog.get_logger("ping")
        logger.info("first")
        logger.info("second")
        context = structlog.contextvars.get_contextvars()
        return {"request_id": context.get("request_id")}

    return app


def test_all_logs_within_a_request_share_the_same_request_id(capsys):
    configure_logging()
    app = _build_app()

    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get("/ping")

    response = asyncio.run(call())
    response_request_id = response.json()["request_id"]

    captured_lines = [
        json.loads(line)
        for line in capsys.readouterr().out.strip().splitlines()
        if line.strip()
    ]
    captured_lines = [line for line in captured_lines if line["logger"] == "ping"]

    assert len(captured_lines) == 2
    for line in captured_lines:
        assert line["request_id"] == response_request_id


def test_concurrent_requests_do_not_share_request_id():
    app = _build_app()

    async def call() -> str:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/ping")
            return response.json()["request_id"]

    async def run_concurrently() -> tuple[str, str]:
        return await asyncio.gather(call(), call())

    first_request_id, second_request_id = asyncio.run(run_concurrently())

    assert first_request_id != second_request_id


def test_main_app_registers_request_id_middleware():
    from app.core.request_context import RequestIdMiddleware
    from app.main import app as main_app

    middleware_classes = [m.cls for m in main_app.user_middleware]
    assert RequestIdMiddleware in middleware_classes


def test_middleware_logs_http_access_line(capsys):
    configure_logging()
    app = _build_app()

    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get("/ping")

    asyncio.run(call())

    captured_lines = [
        json.loads(line)
        for line in capsys.readouterr().out.strip().splitlines()
        if line.strip()
    ]
    access_lines = [line for line in captured_lines if line["event"] == "http_request"]

    assert len(access_lines) == 1
    access_line = access_lines[0]
    assert access_line["method"] == "GET"
    assert access_line["path"] == "/ping"
    assert access_line["status_code"] == 200
    assert "duration_ms" in access_line
