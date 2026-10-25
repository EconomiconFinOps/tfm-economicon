import asyncio
from types import SimpleNamespace

import httpx
from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.health import router as health_router
from app.db.database import Database


def _app(database, *, rabbitmq=True, vector_store=True) -> FastAPI:
    app = FastAPI()
    app.include_router(health_router)
    app.state.database = database
    app.state.queue = SimpleNamespace(ping=lambda: rabbitmq)
    app.state.vector_store = SimpleNamespace(ping=lambda: vector_store)
    return app


def _get_health(app: FastAPI) -> httpx.Response:
    async def call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/health")

    return asyncio.run(call())


def _database(tmp_path, *, backend_schema: bool) -> Database:
    database = Database(f"sqlite:///{tmp_path / 'processor.db'}")
    if backend_schema:
        with database.engine.begin() as connection:
            connection.execute(text("CREATE TABLE jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL)"))
            connection.execute(text(
                "INSERT INTO jobs VALUES ('a', 'queued'), ('b', 'completed'), ('c', 'completed')"
            ))
    return database


def test_health_is_ok_before_backend_schema_exists(tmp_path):
    database = _database(tmp_path, backend_schema=False)

    response = _get_health(_app(database))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["services"] == {"database": "ok", "rabbitmq": "ok", "vector_store": "ok"}
    assert "jobs" not in body
    database.dispose()


def test_health_is_unchanged_once_backend_schema_exists(tmp_path):
    database = _database(tmp_path, backend_schema=True)

    response = _get_health(_app(database))

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "jobs" not in response.json()
    database.dispose()


def test_health_combines_missing_backend_schema_with_failed_broker(tmp_path):
    database = _database(tmp_path, backend_schema=False)

    response = _get_health(_app(database, rabbitmq=False))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["services"] == {"database": "ok", "rabbitmq": "failed", "vector_store": "ok"}
    database.dispose()


def test_health_reports_an_unreachable_database_as_failed():
    database = Database("postgresql+psycopg://user@127.0.0.1:1/db?connect_timeout=1")

    response = _get_health(_app(database))

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["services"]["database"] == "failed"
    database.dispose()
