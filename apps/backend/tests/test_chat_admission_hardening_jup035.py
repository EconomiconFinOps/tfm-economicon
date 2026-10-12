import copy
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.db.chat_repository import ChatError
from app.db.migration_runner import MigrationRunner
from app.schemas.chat import ResponseValidationError, validate_response
from app.services.chat_context import ChatContext, response_subscriptions
from test_chat_operations_jup035 import ANSWER, api, body, headers, path, run
from test_chat_screen_jup035 import demo_dataset, no_operation


def test_context_wait_timeout_is_a_sanitized_503(api, monkeypatch):
    resources = SimpleNamespace(verify_descriptor=lambda descriptor: None)
    builder = ChatContext(api[0], resources)
    monkeypatch.setattr(ChatContext, "build", lambda *args: {})

    async def expired(*args, **kwargs):
        raise asyncio.TimeoutError("PRIVATE CONTEXT")

    monkeypatch.setattr(asyncio, "wait_for", expired)
    with pytest.raises(ChatError) as failure:
        asyncio.run(builder({}, {}, {}))
    assert failure.value.status == 503
    assert failure.value.code == "context_timeout"
    assert "PRIVATE" not in str(failure.value)


@pytest.mark.parametrize("selection", [
    {"start_date": 1780272000, "end_date": 1782864000},
    {"period": {"start_date": 1780272000, "end_date": 1782864000, "timezone": "UTC"}},
])
def test_numeric_capture_dates_return_422_before_reservation(api, selection):
    async def scenario(client):
        payload = body()
        payload["screen_context"]["selection"] = selection
        response = await client.post(path(), json=payload, headers=headers())
        assert response.status_code == 422
        no_operation(api)
    run(scenario, api)


def test_dataset_limit_is_checked_before_billing(api, monkeypatch):
    builder = ChatContext(api[0], None)
    payload = body()
    payload["screen_context"]["datasets"] = [demo_dataset()] * 21
    calls = []
    monkeypatch.setattr(builder, "billing", lambda *args: calls.append(args))
    with pytest.raises(ChatError) as failure:
        builder.build(dict(tenant_id="t", user_id="alice", conversation_id="alice-chat"), payload)
    assert failure.value.status == 413
    assert calls == []


def test_subscription_selection_rejects_control_characters():
    with pytest.raises(ChatError) as failure:
        response_subscriptions({"selection": {"filters": {"subscriptions": ["subscription\u0000"]}}})
    assert failure.value.status == 422


@pytest.mark.parametrize("field", ["kind", "source", "title"])
def test_evidence_identity_cannot_hide_forged_provenance(field):
    authorized = {"id": "doc:1", "kind": "corpus", "source": "manual", "title": "Manual"}
    response = copy.deepcopy(ANSWER)
    response["status"] = "partial"
    response["evidence"] = [{**authorized, field: "cost_query" if field == "kind" else "Forged"}]
    with pytest.raises(ResponseValidationError) as failure:
        validate_response(response, [authorized])
    assert failure.value.rule_code == "evidence_provenance"


def test_corrupt_history_does_not_block_schema_startup_or_other_conversations(api):
    with api[1].engine.begin() as connection:
        connection.execute(text("UPDATE conversations SET dialogue_history='{}' WHERE id='alice-chat'"))
    import app.db.migrations
    MigrationRunner(api[1].engine, "app.db.migrations", Path(app.db.migrations.__file__).parent).verify()
    assert api[1].fetch_messages("bob-chat", "t", "bob") == []
    with pytest.raises(ChatError):
        api[1].fetch_messages("alice-chat", "t", "alice")
