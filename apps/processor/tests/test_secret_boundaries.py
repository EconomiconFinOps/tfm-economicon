"""JUP-053: imports, startup, bounded diagnostics and HTTP failure boundaries."""
import asyncio
import importlib
import json
import logging
import sys
import traceback
from contextlib import ExitStack
from unittest.mock import MagicMock, patch
from urllib.parse import quote

import httpx
import pytest
import structlog
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import configure_logging
from conftest import RUNTIME_KEYS, SYNTHETIC_ENV

SERVICE = "processor"
RESOURCE_TARGETS = ["app.db.database.Database","app.clients.rabbitmq_queue.RabbitMQQueue","app.vector_store.pgvector_store.PgVectorStore"]
ENTRYPOINTS = ["app.run_api","app.run_worker","app.run_all","app.run_azure_cost_ingestion"]
SENTINEL = "jup053-only-synthetic/Sensitive+Value?"
ENCODED = quote(SENTINEL, safe="")


@pytest.mark.parametrize("encoding", ["raw", "quote", "quote_plus"])
def test_rf053_002_active_secrets_in_nested_mapping_keys_are_redacted(monkeypatch, capsys, encoding):
    from urllib.parse import quote_plus

    active = "jup053 nested/key + sentinel"
    forms = {"raw": active, "quote": quote(active, safe=""), "quote_plus": quote_plus(active, safe="")}
    monkeypatch.setenv("RABBITMQ_URL", f"amqp://unit:{forms['quote']}@localhost:5672/%2F")
    get_settings.cache_clear()
    get_settings()
    configure_logging()
    structlog.contextvars.bind_contextvars(request_id="jup053-mapping-key")
    field_only = "jup053-sensitive-field-value"
    structlog.get_logger("mapping-key-boundary").info(
        "mapping metadata",
        safe_count=7,
        payload={"items": [{"prefix-" + forms[encoding] + "-suffix": {
            "safe_number": 23, "PassWord": field_only, "Authorization": field_only,
        }}]},
    )
    captured = capsys.readouterr()
    row = json.loads(captured.out)
    assert row["safe_count"] == 7
    assert row["service"] == SERVICE and row["logger"] == "mapping-key-boundary"
    assert row["level"] == "info" and row["timestamp"]
    assert row["request_id"] == "jup053-mapping-key"
    nested = next(iter(row["payload"]["items"][0].values()))
    assert nested["safe_number"] == 23
    assert field_only not in captured.out + captured.err
    for secret in forms.values():
        assert secret not in captured.out + captured.err



@pytest.fixture
def resource_mocks():
    with ExitStack() as stack:
        yield [stack.enter_context(patch(target)) for target in RESOURCE_TARGETS]


@pytest.fixture
def main_module(monkeypatch, resource_mocks):
    monkeypatch.delitem(sys.modules, "app.main", raising=False)
    return importlib.import_module("app.main")


@pytest.fixture(autouse=True)
def restore_logging():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers, root.level = handlers, level
    structlog.contextvars.clear_contextvars()


def rendered_failure(call):
    try:
        result = call()
    except (Exception, SystemExit) as exc:
        return True, "".join(traceback.format_exception(exc))
    return isinstance(result, int) and result != 0, ""


def test_import_without_secrets_does_not_load_settings_or_construct_resources(monkeypatch, resource_mocks):
    for name in RUNTIME_KEYS:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    monkeypatch.delitem(sys.modules, "app.main", raising=False)
    with patch("app.core.config.get_settings", wraps=get_settings) as loader:
        module = importlib.import_module("app.main")
    assert module.app is not None
    assert loader.call_count == 0, "Import must not require runtime settings"
    assert all(mock.call_count == 0 for mock in resource_mocks), "Import constructed service resources"


def test_lifespan_delivers_unwrapped_external_dsn_to_clients(main_module, resource_mocks):
    async def start():
        async with main_module.app.router.lifespan_context(main_module.app):
            assert main_module.app.state.database is not None
    asyncio.run(start())
    for constructor, name in zip(resource_mocks, ["DATABASE_URL", "RABBITMQ_URL", "VECTOR_DATABASE_URL"]):
        assert constructor.call_args.args[0] == SYNTHETIC_ENV[name]


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_missing_settings_stop_every_entrypoint_before_work(monkeypatch, entrypoint):
    module = importlib.import_module(entrypoint)
    for name in ("DATABASE_URL", "RABBITMQ_URL", "VECTOR_DATABASE_URL", "AUTH_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    monkeypatch.setattr(sys, "argv", [entrypoint, "--tenant-id", "tenant-unit", "--subscription-id", "sub-unit"])
    with ExitStack() as stack:
        starts = [stack.enter_context(patch("uvicorn.run")), stack.enter_context(patch("threading.Thread"))]
        if hasattr(module, "ProcessorWorker"):
            starts.append(stack.enter_context(patch.object(module, "ProcessorWorker")))
        if hasattr(module, "Database"):
            starts.append(stack.enter_context(patch.object(module, "Database")))
        if hasattr(module, "AzureCostClient"):
            starts.append(stack.enter_context(patch.object(module, "AzureCostClient")))
            starts.append(stack.enter_context(patch.object(module, "AzureCostIngestionService")))
        stopped, _ = rendered_failure(module.main)
    assert all(mock.call_count == 0 for mock in starts), "Work started before required credentials validated"
    assert stopped, "Invalid configuration reached successful startup"


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_validation_errors_at_entrypoints_omit_raw_input(monkeypatch, capsys, entrypoint):
    module = importlib.import_module(entrypoint)
    port = "API_PORT" if SERVICE == "backend" else "PROCESSOR_PORT"
    monkeypatch.setenv(port, SENTINEL)
    get_settings.cache_clear()
    monkeypatch.setattr(sys, "argv", [entrypoint, "--tenant-id", "tenant-unit", "--subscription-id", "sub-unit"])
    stopped, diagnostic = rendered_failure(module.main)
    captured = capsys.readouterr()
    assert stopped
    assert SENTINEL not in diagnostic + captured.out + captured.err


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_dependency_exception_chain_at_entrypoints_is_safe(monkeypatch, capsys, entrypoint):
    module = importlib.import_module(entrypoint)
    monkeypatch.setenv("RABBITMQ_URL", f"amqp://unit:{ENCODED}@127.0.0.1:5672/%2F")
    get_settings.cache_clear()
    monkeypatch.setattr(sys, "argv", [entrypoint, "--tenant-id", "tenant-unit", "--subscription-id", "sub-unit"])

    def fail(*args, **kwargs):
        try:
            raise ValueError(f"dependency cause {SENTINEL}")
        except ValueError as exc:
            raise RuntimeError(f"dependency initialization {ENCODED}") from exc

    with ExitStack() as stack:
        if hasattr(module, "ProcessorWorker"):
            stack.enter_context(patch.object(module, "ProcessorWorker", side_effect=fail))
        elif hasattr(module, "Database"):
            constructor = stack.enter_context(patch.object(module, "Database"))
            constructor.return_value.initialize.side_effect = fail
        else:
            stack.enter_context(patch("uvicorn.run", side_effect=fail))
        stopped, diagnostic = rendered_failure(module.main)
    captured = capsys.readouterr()
    assert stopped
    assert SENTINEL not in diagnostic + captured.out + captured.err
    assert ENCODED not in diagnostic + captured.out + captured.err


@pytest.mark.parametrize("standard", [False, True], ids=["structlog", "stdlib"])
def test_logs_redact_active_values_after_interpolation_and_exception_formatting(monkeypatch, capsys, standard):
    monkeypatch.setenv("RABBITMQ_URL", f"amqp://unit:{ENCODED}@127.0.0.1:5672/%2F")
    get_settings.cache_clear()
    get_settings()
    configure_logging()
    structlog.contextvars.bind_contextvars(request_id="jup053-request")
    logger = logging.getLogger("secret-boundary") if standard else structlog.get_logger("secret-boundary")
    logger.info("dependency %s %s", SENTINEL, ENCODED)
    try:
        try:
            raise ValueError(f"cause {SENTINEL}")
        except ValueError as exc:
            raise RuntimeError(f"storage operation failed {ENCODED}") from exc
    except RuntimeError:
        logger.exception("storage failure")
    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines() if line.strip()]
    assert len(rows) == 2
    for row in rows:
        assert row["service"] == SERVICE
        assert row["logger"] == "secret-boundary"
        assert row["request_id"] == "jup053-request"
        assert row["timestamp"] and row["level"]
    assert "RuntimeError" in json.dumps(rows[-1]) and "storage" in json.dumps(rows[-1])
    assert SENTINEL not in captured.out + captured.err
    assert ENCODED not in captured.out + captured.err


def test_sensitive_named_fields_are_redacted_recursively(capsys):
    get_settings()
    configure_logging()
    structlog.get_logger("nested").info(
        "safe event",
        payload={"items": [{"password": SENTINEL, "Authorization": f"Bearer {SENTINEL}",
                            "cookie": SENTINEL, "api_key": SENTINEL}], "safe_count": 3},
    )
    output = capsys.readouterr().out
    row = json.loads(output)
    assert row["payload"]["safe_count"] == 3
    assert SENTINEL not in output


def request(app, method, path, **kwargs):
    async def call():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://unit",
        ) as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(call())


def test_http_422_omits_validation_input_and_context(main_module, capsys):
    class SensitiveRequest(BaseModel):
        password: int

    @main_module.app.post("/secret-validation")
    def validate(payload: SensitiveRequest):
        return {"ok": True}

    response = request(main_module.app, "POST", "/secret-validation", json={"password": SENTINEL})
    assert response.status_code == 422
    body = response.json()
    assert body.get("detail")
    assert SENTINEL not in response.text
    assert all("input" not in item and "ctx" not in item for item in body["detail"])
    captured = capsys.readouterr()
    assert SENTINEL not in captured.out + captured.err


def test_http_500_has_safe_diagnostic_and_no_body_header_leak(main_module, capsys):
    @main_module.app.post("/secret-failure")
    def fail():
        raise RuntimeError(SENTINEL)

    response = request(
        main_module.app, "POST", "/secret-failure",
        json={"password": SENTINEL}, headers={"Authorization": f"Bearer {SENTINEL}", "Cookie": SENTINEL},
    )
    assert response.status_code == 500
    assert response.text
    captured = capsys.readouterr()
    assert SENTINEL not in response.text + captured.out + captured.err


def test_access_log_uses_route_template_or_unknown_marker(main_module, capsys):
    # Bind the handler to this test's capture stream, not fixture setup capture.
    configure_logging()

    @main_module.app.get("/resource/{resource_id}")
    def resource(resource_id: str):
        return {"ok": True}

    private_path = "jup053-private-path-segment"
    request(main_module.app, "GET", f"/resource/{private_path}")
    request(main_module.app, "GET", f"/unknown/{private_path}")
    output = capsys.readouterr().out
    access = [json.loads(line) for line in output.splitlines() if '"http_request"' in line]
    assert len(access) == 2
    assert access[0]["path"] == "/resource/{resource_id}"
    assert private_path not in json.dumps(access)


def test_lifespan_failure_is_sanitized_and_never_yields_readiness(main_module, resource_mocks, capsys):
    resource_mocks[0].return_value.initialize.side_effect = RuntimeError(SYNTHETIC_ENV["DATABASE_URL"])
    reached = []

    async def start():
        async with main_module.app.router.lifespan_context(main_module.app):
            reached.append(True)

    stopped, diagnostic = rendered_failure(lambda: asyncio.run(start()))
    captured = capsys.readouterr()
    assert stopped and not reached
    assert SYNTHETIC_ENV["DATABASE_URL"] not in diagnostic + captured.out + captured.err


def test_persisted_job_failure_uses_stable_code_not_exception_text():
    from app.tasks.ingest import IngestTask

    repository = MagicMock()
    pipeline = MagicMock()
    pipeline.run.side_effect = RuntimeError(SENTINEL)
    task = IngestTask(repository, pipeline)
    with pytest.raises(Exception):
        task.execute({
            "id": "jup053-job", "tenant_id": "tenant-core", "source": "azure-cost",
            "artifact_uri": None, "payload": {"text_content": "test document", "metadata": {}},
        })
    repository.mark_running.assert_called_once_with("jup053-job")
    repository.mark_completed.assert_not_called()
    repository.mark_failed.assert_called_once()
    job_id, diagnostic = repository.mark_failed.call_args.args
    assert job_id == "jup053-job"
    assert diagnostic and SENTINEL not in diagnostic
    pipeline.run.side_effect = RuntimeError("different synthetic failure")
    with pytest.raises(Exception):
        task.execute({
            "id": "jup053-job", "tenant_id": "tenant-core", "source": "azure-cost",
            "artifact_uri": None, "payload": {"text_content": "test document", "metadata": {}},
        })
    assert repository.mark_failed.call_args.args[1] == diagnostic


def test_combined_entrypoint_leaves_no_worker_after_server_initialization_failure(monkeypatch):
    import app.run_all as module

    stopped = []

    class Worker:
        def __init__(self, settings):
            pass

        def run_forever(self):
            pass

        def close(self):
            stopped.append("close")

        def stop(self):
            stopped.append("stop")

    thread = MagicMock()
    with (
        patch.object(module, "ProcessorWorker", Worker),
        patch.object(module.threading, "Thread", return_value=thread),
        patch.object(module.uvicorn, "run", side_effect=RuntimeError("initialization failed")),
    ):
        rendered_failure(module.main)
    assert not thread.start.called or (stopped and thread.join.called), "Started worker was not stopped and joined"


@pytest.mark.parametrize("failure_point", ["none", "thread_constructor", "stop", "join"])
def test_combined_entrypoint_closes_initialized_worker_despite_lifecycle_failure(failure_point):
    import app.run_all as module

    worker = MagicMock(spec=["run_forever", "stop", "close"])
    thread = MagicMock(spec=["start", "join", "ident"])
    thread.ident = None

    def start():
        thread.ident = 1

    thread.start.side_effect = start
    if failure_point == "stop":
        worker.stop.side_effect = RuntimeError("synthetic stop failure")
    elif failure_point == "join":
        thread.join.side_effect = RuntimeError("synthetic join failure")

    with (
        patch.object(module, "ProcessorWorker", return_value=worker) as constructor,
        patch.object(module.threading, "Thread", return_value=thread) as thread_constructor,
        patch.object(module.uvicorn, "run") as server,
    ):
        if failure_point == "thread_constructor":
            thread_constructor.side_effect = RuntimeError("synthetic thread construction failure")
        failed, _ = rendered_failure(module.main)

    constructor.assert_called_once()
    thread_constructor.assert_called_once()
    assert failed == (failure_point != "none")
    if failure_point == "thread_constructor":
        server.assert_not_called()
        thread.start.assert_not_called()
    else:
        thread.start.assert_called_once()
        server.assert_called_once()
    worker.close.assert_called_once()
    if thread.ident is not None:
        thread.join.assert_called_once()


def test_rf053_003_task_to_worker_preserves_sanitized_root_diagnostics(monkeypatch, capsys):
    from app.clients.rabbitmq_queue import QueueMessage
    from app.tasks.ingest import IngestTask
    from app.workers.runner import ProcessorWorker

    monkeypatch.setenv("RABBITMQ_URL", f"amqp://unit:{ENCODED}@localhost:5672/%2F")
    get_settings.cache_clear()
    settings = get_settings()
    configure_logging()
    job = {
        "id": "jup053-error-job", "request_id": "jup053-worker-failure",
        "tenant_id": "tenant-core", "source": "azure-cost", "artifact_uri": None,
        "payload": {"text_content": "test document", "metadata": {}},
    }
    structlog.contextvars.bind_contextvars(request_id=job["request_id"])
    repository = MagicMock()
    pipeline = MagicMock()
    harmless_message = "synthetic input parse failure"
    dsn = SYNTHETIC_ENV["VECTOR_DATABASE_URL"]
    pipeline.run.side_effect = ValueError(f"{harmless_message}: {SENTINEL}; {dsn}")
    # Exercise the real loop/task/acknowledgement path without allocating clients.
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.settings = settings
    worker.task = IngestTask(repository, pipeline)
    worker.queue = MagicMock()
    worker.queue.blocking_pop.return_value = QueueMessage(job, 42)
    worker._stopping = MagicMock()
    worker._stopping.is_set.side_effect = [False, True]

    worker.run_forever()

    repository.mark_running.assert_called_once_with("jup053-error-job")
    repository.mark_failed.assert_called_once_with("jup053-error-job", "ingestion_failed")
    repository.mark_completed.assert_not_called()
    worker.queue.ack.assert_not_called()
    worker.queue.nack.assert_called_once_with(42, requeue=True)
    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines() if line.strip()]
    assert rows and any(row["level"] == "error" for row in rows)
    assert all(row["service"] == "processor" and row["timestamp"] and row["logger"] for row in rows)
    assert all(row["request_id"] == job["request_id"] for row in rows)
    diagnostics = json.dumps(rows)
    assert SENTINEL not in captured.out + captured.err
    assert ENCODED not in captured.out + captured.err
    assert dsn not in captured.out + captured.err
    assert "vector-fixture-pass" not in captured.out + captured.err
    assert "ValueError" in diagnostics, "Original exception type was lost before rendered logging"
    assert harmless_message in diagnostics, "Useful sanitized root message was lost"
