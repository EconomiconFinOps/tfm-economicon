"""Direct repository boundaries, including legacy inconsistent children."""
from datetime import datetime, timezone
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from tenant_isolation_support import required_scope, populated_database, rows, tenant_database, tenant_cockroach_database


@pytest.mark.parametrize(
    'tenant_database,parent,tenant,author',
    [
        pytest.param('sqlite', 'other-owner', 'tenant-a', 'alice', id='sqlite-other-owner-tenant-a-alice'),
        pytest.param('sqlite', 'own', 'tenant-b', 'alice', id='sqlite-own-tenant-b-alice'),
    ],
    indirect=['tenant_database'],
)
def test_rejected_message_changes_neither_child_nor_parent(populated_database, parent, tenant, author):
    db = populated_database
    before = (rows(db, "conversations"), rows(db, "messages"))
    try:
        db.append_message(conversation_id=parent, tenant_id=tenant, user_id=author, requester_id=author, role="user", content="attempt")
    except (ValueError, PermissionError, LookupError):
        pass
    assert (rows(db, "conversations"), rows(db, "messages")) == before


@pytest.mark.parametrize(
    'tenant_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['tenant_database'],
)
def test_scoped_fetch_does_not_disclose_legacy_inconsistent_child(populated_database):
    db = populated_database
    with db.engine.begin() as connection:
        connection.execute(text("INSERT INTO messages VALUES ('bad-child', 'own', 'tenant-b', 'bob', 'user', 'foreign-secret-marker', NULL, :now)"), {"now": datetime.now(timezone.utc)})
    result = db.fetch_messages("own", tenant_id="tenant-a", user_id="alice")
    assert result == []


@pytest.mark.parametrize(
    'tenant_database,parent',
    [
        pytest.param('sqlite', 'foreign-marker', id='sqlite-foreign-marker'),
        pytest.param('sqlite', 'other-owner', id='sqlite-other-owner'),
    ],
    indirect=['tenant_database'],
)
def test_scoped_child_read_contract(populated_database, parent):
    db = populated_database
    scope = required_scope(db.fetch_messages, tenant_id="tenant-a", user_id="alice")
    db.append_message(conversation_id="own", tenant_id="tenant-a", user_id="alice", requester_id="alice", role="user", content="allowed")
    for identifier, tenant, owner in (("foreign-marker", "tenant-b", "bob"), ("other-owner", "tenant-a", "other-a")):
        db.append_message(conversation_id=identifier, tenant_id=tenant, user_id=owner, requester_id=owner, role="user", content="foreign-private-message")
    result = db.fetch_messages(parent, **scope)
    assert [item["content"] for item in result] == (["allowed"] if parent == "own" else [])


@pytest.mark.parametrize(
    'tenant_database,parent',
    [
        pytest.param('sqlite', 'other-owner', id='sqlite-other-owner'),
    ],
    indirect=['tenant_database'],
)
def test_nullable_assistant_author_requires_requester_contract(populated_database, parent):
    db = populated_database
    scope = required_scope(db.append_message, requester_id="alice")
    before = (rows(db, "conversations"), rows(db, "messages"))
    try:
        db.append_message(conversation_id=parent, tenant_id="tenant-a", user_id=None, role="assistant", content="attempt", **scope)
    except (ValueError, PermissionError, LookupError):
        pass
    assert (rows(db, "conversations"), rows(db, "messages")) == before


@pytest.mark.parametrize(
    'tenant_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['tenant_database'],
)
def test_requester_cannot_attribute_a_message_to_another_user(populated_database):
    db = populated_database
    before = (rows(db, "conversations"), rows(db, "messages"))
    with pytest.raises(PermissionError):
        db.append_message(conversation_id="own", tenant_id="tenant-a", user_id="bob", requester_id="alice", role="user", content="forged author")
    assert (rows(db, "conversations"), rows(db, "messages")) == before


@pytest.mark.parametrize(
    'tenant_database,stage',
    [
        pytest.param('cockroach', 'UPDATE CONVERSATIONS', id='cockroach-UPDATE CONVERSATIONS'),
    ],
    indirect=['tenant_database'],
)
def test_message_rowcount_rejection_rolls_back_both_writes(populated_database, monkeypatch, stage):
    db = populated_database
    engine = db.engine
    before = (rows(db, "conversations"), rows(db, "messages"))
    intercepted = []

    class Engine:
        def __getattr__(self, name):
            return getattr(engine, name)

        def connect(self):
            return engine.connect()

        @contextmanager
        def begin(self):
            with engine.begin() as connection:
                class Connection:
                    def execute(self, statement, parameters=None):
                        result = connection.execute(statement, parameters)
                        if " ".join(str(statement).upper().split()).startswith(stage):
                            intercepted.append(stage)
                            return SimpleNamespace(rowcount=0)
                        return result
                yield Connection()

    with monkeypatch.context() as patch:
        patch.setattr(db, "engine", Engine())
        with pytest.raises(PermissionError):
            db.append_message(conversation_id="own", tenant_id="tenant-a", user_id=None, requester_id="alice", role="assistant", content="must roll back")
    assert intercepted == [stage]
    assert (rows(db, "conversations"), rows(db, "messages")) == before
