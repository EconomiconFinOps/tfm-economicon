"""Scoped durable admission barrier. All mutations use the conversation lock."""

from copy import deepcopy
from uuid import uuid4
from sqlalchemy import text
from app.db import chat_history
from app.db.chat_summary import digest

STATES = {"pending", "running", "reconciling", "failed"}
REASONS = {
    "queued",
    "running",
    "remote_uncertain",
    "failed",
    "retry_requested",
    "capacity_deferred",
    "descriptor_mismatch",
    "pending_pair_too_large",
}


class CompactionRepository:
    def __init__(self, repository):
        self.repository = repository

    def read(self, c, scope):
        from app.db.chat_repository import ChatError

        raw = c.execute(
            text(
                "SELECT CAST(dialogue_compaction AS TEXT) FROM conversations "
                "WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id"
            ),
            scope,
        ).scalar_one()
        if raw is None:
            return None
        try:
            value = chat_history.loads(raw)
            if (
                value["v"] != 1
                or value["state"] not in STATES
                or not isinstance(value["generation"], str)
                or type(value["revision"]) is not int
                or value["revision"] < 0
            ):
                raise ValueError()
            return value
        except (ValueError, TypeError, KeyError):
            raise ChatError(503, "compaction_integrity") from None

    def get(self, scope):
        return self.repository._transaction(scope, lambda c: self.read(c, scope))

    def fence_in(self, c, scope):
        document = chat_history.read(c, scope)
        raw = c.execute(
            text(
                "SELECT CAST(dialogue_summary AS TEXT) FROM conversations "
                "WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id"
            ),
            scope,
        ).scalar_one()
        return {
            "history_revision": document["revision"],
            "parent_hash": None if raw is None else digest(chat_history.loads(raw)),
        }

    def fence(self, scope):
        return self.repository._transaction(scope, lambda c: self.fence_in(c, scope))

    def admit(self, c, scope, expected=None):
        from app.db.chat_repository import ChatError

        if self.read(c, scope) is not None:
            raise ChatError(409, "conversation_compacting")
        if expected is not None and expected != self.fence_in(c, scope):
            raise ChatError(409, "context_stale")

    def ensure_idle(self, scope):
        return self.repository._transaction(scope, lambda c: self.admit(c, scope))

    def _write(self, c, scope, value):
        c.execute(
            text(
                "UPDATE conversations SET dialogue_compaction=:control WHERE "
                "id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id"
            ),
            {**scope, "control": None if value is None else chat_history.dumps(value)},
        )

    def pending(self, c, scope, context=None):
        from app.db.chat_repository import ChatError

        if self.read(c, scope) is not None:
            raise ChatError(409, "conversation_compacting")
        from app.core.context_budget import budget

        manifest = context.get("manifest", {}) if isinstance(context, dict) else {}
        tokens = manifest.get("variable_tokens", 0)
        contract = manifest.get("context_budget", budget("chat"))
        limit = contract.get("context_tokens", budget("chat")["context_tokens"])
        pressure = type(tokens) is int and type(limit) is int and tokens >= limit * 0.75
        value = {
            "v": 1,
            "state": "pending",
            "generation": str(uuid4()),
            "revision": 0,
            **self.fence_in(c, scope),
            "owner": None,
            "lease_until": None,
            "job": None,
            "reason": "queued",
            "full_context_pressure": pressure,
        }
        self._write(c, scope, value)
        return value

    def claim(self, scope, owner, explicit=False):
        from app.core.config import get_settings

        def action(c):
            value = self.read(c, scope)
            if value is None or (value["state"] == "failed" and not explicit):
                return None
            if (
                value.get("owner")
                and (value.get("lease_until") or 0) > self.repository.clock()
            ):
                return None
            value["owner"] = owner
            value["lease_until"] = (
                self.repository.clock() + get_settings().summary_timeout_seconds + 15
            )
            value["revision"] += 1
            if value.get("job") is not None:
                value.update(state="reconciling", reason="remote_uncertain")
            else:
                value.update(
                    state="pending",
                    reason=(
                        "retry_requested"
                        if value.get("reason") == "retry_requested"
                        else "queued"
                    ),
                )
            self._write(c, scope, value)
            return value

        return self.repository._transaction(scope, action)

    def transition_in(self, c, scope, expected, *, clear=False, **changes):
        from app.db.chat_repository import ChatError

        current = self.read(c, scope)
        if current is None or any(
            current.get(k) != expected.get(k)
            for k in ("generation", "revision", "owner")
        ):
            raise ChatError(409, "compaction_changed")
        if clear:
            self._write(c, scope, None)
            return None
        value = deepcopy(current)
        value.update(changes)
        value["revision"] += 1
        self._write(c, scope, value)
        return value

    def transition(self, scope, expected, **changes):
        return self.repository._transaction(
            scope, lambda c: self.transition_in(c, scope, expected, **changes)
        )

    def retry(self, scope):
        from app.db.chat_repository import ChatError

        def action(c):
            value = self.read(c, scope)
            if value is None:
                return None
            if value["state"] not in ("failed", "reconciling"):
                raise ChatError(409, "compaction_not_retryable")
            if (
                value.get("owner")
                and (value.get("lease_until") or 0) > self.repository.clock()
            ):
                return value
            return self.transition_in(
                c,
                scope,
                value,
                state="reconciling" if value.get("job") else "pending",
                reason="remote_uncertain" if value.get("job") else "retry_requested",
                owner=None,
                lease_until=None,
            )

        return self.repository._transaction(scope, action)

    def recoverable(self):
        with self.repository.engine.connect() as c:
            rows = c.execute(
                text(
                    "SELECT tenant_id,user_id,id AS conversation_id,"
                    "CAST(dialogue_compaction AS TEXT) AS control FROM conversations "
                    "WHERE dialogue_compaction IS NOT NULL ORDER BY id"
                )
            ).mappings()
            return [
                dict((k, row[k]) for k in ("tenant_id", "user_id", "conversation_id"))
                for row in rows
                if chat_history.loads(row["control"]).get("state") != "failed"
            ]

    def public(self, scope):
        value = self.get(scope)
        if value is None:
            return {
                "reason": "cold",
                "state": "idle",
                "active": False,
                "pending": False,
                "blocked": False,
                "retryable": False,
            }
        state = value["state"]
        return {
            "reason": value["reason"] if value.get("reason") in REASONS else "failed",
            "state": state,
            "active": state == "running",
            "pending": state in ("pending", "reconciling"),
            "blocked": True,
            "retryable": state in ("failed", "reconciling"),
        }
