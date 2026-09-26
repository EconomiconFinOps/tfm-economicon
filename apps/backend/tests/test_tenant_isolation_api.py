"""Real bearer/session/membership and repositories; doubles only at external sinks."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.logging import configure_logging
from app.core.security import create_access_token
from app.services.assistant import AssistantService
from app.services.rabbitmq_queue import PublishResult
from conftest import SYNTHETIC_ENV
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, request, resource_mocks, restore_logging


@pytest.fixture
def api(main_module, populated_database, monkeypatch):
    db = populated_database
    spies = {}
    for name in ("user_has_tenant", "fetch_conversations", "fetch_conversation", "fetch_messages", "fetch_billing_summary", "create_job", "create_conversation", "append_message"):
        spies[name] = MagicMock(wraps=getattr(db, name))
        monkeypatch.setattr(db, name, spies[name])
    queue = MagicMock(spec_set=["queue_name", "reserve", "publish", "cancel"], queue_name="jup086-test")
    queue.reserve.return_value = object()
    queue.publish.return_value = PublishResult("confirmed", "confirmed")
    vector = MagicMock()
    vector.search_chunks.return_value = []
    embedding = MagicMock()
    embedding.embed.return_value = [1.0] + [0.0] * 7
    for name, value in {"database": db, "queue": queue, "vector_store": vector, "embedding_provider": embedding, "assistant_service": AssistantService()}.items():
        monkeypatch.setattr(main_module.app.state, name, value, raising=False)
    return SimpleNamespace(app=main_module.app, db=db, spies=spies, queue=queue, vector=vector, embedding=embedding)


def headers(user="alice", tenant="tenant-a"):
    token = create_access_token(user, SYNTHETIC_ENV["AUTH_SECRET_KEY"], 5)
    return [("Authorization", "Bearer " + token)] + ([] if tenant is None else [("X-Tenant-Id", tenant)])


def call(api, method, path, **kwargs):
    configure_logging()
    return request(api.app, method, path, **kwargs)


def no_effects(api, *, resource_reads=True):
    for name in ("create_job", "create_conversation", "append_message"):
        api.spies[name].assert_not_called()
    if resource_reads:
        for name in ("fetch_conversations", "fetch_conversation", "fetch_messages", "fetch_billing_summary"):
            api.spies[name].assert_not_called()
    api.queue.publish.assert_not_called()
    api.queue.reserve.assert_not_called()
    api.vector.search_chunks.assert_not_called()
    api.embedding.embed.assert_not_called()




@pytest.mark.parametrize(
    'tenant_database,auth,tenant,body,expected',
    [
        pytest.param('sqlite', True, 'tenant-b', {}, 403, id='sqlite-True-tenant-b-body3-403'),
        pytest.param('sqlite', True, 'tenant-a', {'tenant_id': 'tenant-b', 'source': 'test', 'text_content': 'ok'}, 400, id='sqlite-True-tenant-a-body7-400'),
    ],
    indirect=['tenant_database'],
)
def test_ingest_error_precedence_without_effects(api, auth, tenant, body, expected):
    response = call(api, "POST", "/jobs/ingest", headers=headers(tenant=tenant) if auth else [], json=body)
    assert response.status_code == expected
    no_effects(api)






@pytest.mark.parametrize(
    'tenant_database,method,body,status',
    [
        pytest.param('sqlite', 'GET', None, 404, id='sqlite-GET-None-404'),
        pytest.param('sqlite', 'POST', {'content': 'hello'}, 404, id='sqlite-POST-body1-404'),
    ],
    indirect=['tenant_database'],
)
def test_foreign_other_owner_and_missing_ids_are_indistinguishable(api, method, body, status, capsys, caplog):
    responses = []
    for identifier in ("foreign-marker", "other-owner", "nonexistent"):
        path = "/assistant/conversations/" + identifier + ("/messages" if method == "POST" else "")
        responses.append(call(api, method, path, headers=headers(), **({"json": body} if body is not None else {})))
    assert [response.status_code for response in responses] == [status] * 3
    assert responses[0].json() == responses[1].json() == responses[2].json()
    no_effects(api, resource_reads=status == 422)
    captured = capsys.readouterr()
    assert "foreign-marker" not in captured.out + captured.err + caplog.text + responses[0].text


@pytest.mark.parametrize(
    'tenant_database,path,body,field,value',
    [
        pytest.param('sqlite', '/assistant/conversations', {'title': 'new'}, 'user_id', 'bob', id='sqlite-/assistant/conversations-body0-user_id-bob'),
        pytest.param('sqlite', '/assistant/conversations/own/messages', {'content': 'hello'}, 'tenant_id', 'tenant-b', id='sqlite-/assistant/conversations/own/messages-body1-tenant_id-tenant-b'),
    ],
    indirect=['tenant_database'],
)
def test_authority_fields_are_forbidden_not_ignored(api, field, value, path, body):
    response = call(api, "POST", path, headers=headers(), json={**body, field: value})
    assert response.status_code == 422
    assert response.json() == {"detail": [{"type": "validation_error", "msg": "Invalid request value"}]}
    no_effects(api)


@pytest.mark.parametrize(
    'tenant_database,user,tenant,expected',
    [
        pytest.param('cockroach', 'multi', 'tenant-a', [], id='cockroach-multi-tenant-a-expected1'),
    ],
    indirect=['tenant_database'],
)
def test_conversation_list_is_private_even_for_multitenant_user(api, user, tenant, expected):
    response = call(api, "GET", "/assistant/conversations", headers=headers(user, tenant))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == expected




@pytest.mark.parametrize(
    'tenant_database',
    [
        pytest.param('cockroach', id='cockroach'),
    ],
    indirect=['tenant_database'],
)
def test_billing_counts_only_selected_tenant_and_preserves_placeholder_contract(api):
    for tenant, creator in (("tenant-a", "alice"), ("tenant-b", "bob"), ("tenant-b", "bob")):
        api.db.create_job({"tenant_id": tenant, "source": "test", "text_content": "test"}, creator)
    response = call(api, "GET", "/billing/summary", headers=headers())
    assert response.status_code == 200
    assert response.json()["open_ingestions"] == 1










@pytest.mark.parametrize(
    'tenant_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['tenant_database'],
)
def test_resource_dependency_failure_never_leaks_business_markers(api, capsys, caplog):
    def fail(*args):
        raise RuntimeError("foreign-query-marker SELECT private FROM foreign-tenant-marker")
    api.spies["fetch_conversations"].side_effect = fail
    response = call(api, "GET", "/assistant/conversations", headers=headers())
    assert response.status_code == 500
    captured = capsys.readouterr()
    rendered = response.text + captured.out + captured.err + caplog.text
    for marker in ("foreign-query-marker", "foreign-tenant-marker", "SELECT private"):
        assert marker not in rendered
