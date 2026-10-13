"""Durable chat transitions under the conversation lock and revision fence."""

import json
import random
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text

from app.schemas.chat import canonical
from app.db import chat_history


OPEN = ("active", "waiting", "paused")
TERMINAL = ("completed", "failed", "cancelled")
JSON_FIELDS = ("canonical_input", "attempts", "private_control")


class ChatError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def timestamp(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def instant(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def durable_deadline(seconds):
    # The private claim and ledger carry exactly the microsecond SQL fence.
    # Rounding upward would extend the authorized attempt, so round down.
    value = instant(seconds)
    if value.timestamp() > seconds:
        value -= timedelta(microseconds=1)
    return value.timestamp()


def decode(row):
    if row is None:
        return None
    value = dict(row)
    for key in JSON_FIELDS:
        if isinstance(value[key], str):
            value[key] = json.loads(value[key])
    for key in ("attempt_deadline", "retry_at", "created_at", "updated_at"):
        value[key] = timestamp(value[key])
    return value


class ChatRepository:
    def __init__(self, database, clock=time.time):
        self.engine, self.clock = database.engine, clock
        from app.db.chat_summary_repository import SummaryRepository

        self.summaries = SummaryRepository(self)
        from app.db.chat_compaction import CompactionRepository

        self.compactions = CompactionRepository(self)

    def _transaction(self, scope, action, on_unique=None):
        for attempt in range(5):
            try:
                with self.engine.connect().execution_options(
                    isolation_level="SERIALIZABLE"
                ) as c:
                    with c.begin():
                        lock = (
                            ""
                            if self.engine.dialect.name == "sqlite"
                            else " FOR UPDATE"
                        )
                        parent = c.execute(
                            text(
                                "SELECT id FROM conversations WHERE id=:conversation_id "
                                "AND tenant_id=:tenant_id AND user_id=:user_id" + lock
                            ),
                            scope,
                        ).first()
                        if parent is None:
                            raise ChatError(404, "not_found")
                        chat_history.read(c, scope)
                        return action(c)
            except ChatError as error:
                if (
                    error.code in ("operation_changed", "history_changed")
                    and attempt < 4
                ):
                    time.sleep(random.uniform(0.02, 0.05))
                    continue
                raise
            except Exception as error:
                original = getattr(error, "orig", None)
                code = getattr(original, "sqlstate", None)
                # Resolve only the reservation's expected UNIQUE arbitration,
                # after rollback. Other constraints and genuine storage errors
                # retain their safe503; no generic retry of failed inserts.
                unique = code == "23505" or (
                    self.engine.dialect.name == "sqlite"
                    and getattr(original, "sqlite_errorcode", None) == 2067
                )
                if unique and on_unique is not None:
                    return self._transaction(scope, on_unique)
                sqlite_busy = self.engine.dialect.name == "sqlite" and getattr(
                    original, "sqlite_errorcode", None
                ) in (5, 517)
                if (code == "40001" or sqlite_busy) and attempt < 4:
                    time.sleep(random.uniform(0.02, 0.2))
                    continue
                # Caller resolves ambiguous commits by stable operation/result IDs.
                raise ChatError(
                    503, "commit_unknown" if code == "40003" else "storage_unavailable"
                ) from None

    def delete_conversation(self, scope):
        def remove(c):
            # Check every child of the locked parent before removing any data.
            inconsistent = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations "
                    "WHERE conversation_id=:conversation_id AND (tenant_id<>:tenant_id OR user_id<>:user_id) "
                    "LIMIT 1"
                ),
                scope,
            ).first()
            legacy_inconsistent = c.execute(
                text(
                    "SELECT id FROM messages WHERE conversation_id=:conversation_id "
                    "AND (tenant_id<>:tenant_id OR (user_id IS NOT NULL AND user_id<>:user_id)) LIMIT 1"
                ),
                scope,
            ).first()
            if inconsistent or legacy_inconsistent:
                raise ChatError(503, "conversation_integrity")
            opened = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE conversation_id=:conversation_id "
                    "AND tenant_id=:tenant_id AND user_id=:user_id AND state IN ('active','waiting','paused') LIMIT 1"
                ),
                scope,
            ).first()
            if opened:
                raise ChatError(409, "conversation_busy")
            control = self.compactions.read(c, scope)
            if control is not None and (
                control["state"] != "failed"
                or control.get("job") is not None
                or control.get("owner") is not None
            ):
                raise ChatError(409, "conversation_compacting")
            c.execute(
                text(
                    "DELETE FROM chat_operations WHERE conversation_id=:conversation_id "
                    "AND tenant_id=:tenant_id AND user_id=:user_id AND state IN ('completed','failed','cancelled')"
                ),
                scope,
            )
            c.execute(
                text(
                    "DELETE FROM messages WHERE conversation_id=:conversation_id "
                    "AND tenant_id=:tenant_id AND (user_id=:user_id OR user_id IS NULL)"
                ),
                scope,
            )
            deleted = c.execute(
                text(
                    "DELETE FROM conversations WHERE id=:conversation_id "
                    "AND tenant_id=:tenant_id AND user_id=:user_id"
                ),
                scope,
            )
            if deleted.rowcount != 1:
                raise ChatError(503, "conversation_integrity")

        return self._transaction(scope, remove)

    def _row(self, c, scope, operation_id):
        row = (
            c.execute(
                text(
                    "SELECT o.* FROM chat_operations o JOIN conversations c ON "
                    "c.id=o.conversation_id AND c.tenant_id=o.tenant_id AND c.user_id=o.user_id "
                    "WHERE o.operation_id=:operation_id AND o.conversation_id=:conversation_id "
                    "AND o.tenant_id=:tenant_id AND o.user_id=:user_id"
                ),
                {**scope, "operation_id": operation_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise ChatError(404, "not_found")
        return decode(row)

    def get(self, scope, operation_id):
        return self._transaction(scope, lambda c: self._row(c, scope, operation_id))

    def owned_requests(self, scope):
        with self.engine.connect() as connection:
            return [
                decode(row)
                for row in connection.execute(
                    text(
                        "SELECT o.* FROM chat_operations o JOIN conversations c "
                        "ON c.id=o.conversation_id AND c.tenant_id=o.tenant_id AND c.user_id=o.user_id "
                        "WHERE o.tenant_id=:tenant_id AND o.user_id=:user_id "
                        "ORDER BY o.created_at DESC,o.operation_id"
                    ),
                    scope,
                ).mappings()
            ]

    def existing(self, scope, request_id):
        def find(c):
            row = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant_id "
                    "AND user_id=:user_id AND conversation_id=:conversation_id AND client_request_id=:request_id"
                ),
                {**scope, "request_id": request_id},
            ).first()
            return self._row(c, scope, row[0]) if row else None

        return self._transaction(scope, find)

    def reserve(self, scope, payload, context):
        import hashlib

        operation_id, question_id = str(uuid4()), str(uuid4())
        frozen = {"request": payload, "context": context}
        serialized = canonical(frozen)
        digest = hashlib.sha256(serialized.encode()).hexdigest()

        def create(c):
            prior = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant_id "
                    "AND user_id=:user_id AND conversation_id=:conversation_id AND client_request_id=:request_id"
                ),
                {**scope, "request_id": payload["request_id"]},
            ).first()
            if prior:
                row = self._row(c, scope, prior[0])
                if canonical(row["canonical_input"]["request"]) != canonical(payload):
                    raise ChatError(409, "intent_conflict")
                return row, False
            self.compactions.admit(c, scope, context.get("memory_fence"))
            busy = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant_id "
                    "AND conversation_id=:conversation_id AND state IN ('active','waiting','paused')"
                ),
                scope,
            ).first()
            if busy:
                raise ChatError(409, "conversation_busy")
            target_question_id = question_id
            retry = payload.get("retry_of_operation_id")
            if retry is not None:
                source = self._row(c, scope, retry)
                if source["state"] not in TERMINAL:
                    raise ChatError(409, "retry_not_terminal")
                if source["question_content"] != payload["content"]:
                    raise ChatError(409, "question_integrity")
                if source["state"] == "completed":
                    chat_history.completed_result(c, scope, source)
                target_question_id = source["question_message_id"]
                document = chat_history.read(c, scope)
                prior_question = next(
                    (m for m in document["messages"] if m["id"] == target_question_id),
                    None,
                )
                if prior_question is not None and (
                    prior_question["role"] != "user"
                    or prior_question["content"] != payload["content"]
                ):
                    raise ChatError(409, "question_integrity")
            now = self.clock()
            control = {
                "wait": {
                    "local_used_ms": 0,
                    "provider_used_ms": 0,
                    "reason": "local_capacity",
                    "started": now,
                    "until": now + 120,
                },
                "pause_reason": None,
            }
            c.execute(
                text(
                    "INSERT INTO chat_operations (operation_id,tenant_id,user_id,conversation_id,"
                    "client_request_id,question_message_id,question_content,canonical_input,input_hash,state,revision,"
                    "attempt_count,attempts,private_control,created_at,updated_at) VALUES (:operation_id,:tenant_id,"
                    ":user_id,:conversation_id,:request_id,:question_id,:content,:input,:hash,'waiting',0,0,"
                    ":attempts,:control,:now,:now)"
                ),
                {
                    **scope,
                    "operation_id": operation_id,
                    "request_id": payload["request_id"],
                    "question_id": target_question_id,
                    "content": payload["content"],
                    "input": serialized,
                    "hash": digest,
                    "attempts": "[]",
                    "control": canonical(control),
                    "now": instant(now),
                },
            )
            return self._row(c, scope, operation_id), True

        def resolve_unique(c):
            prior = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant_id "
                    "AND user_id=:user_id AND conversation_id=:conversation_id AND client_request_id=:request_id"
                ),
                {**scope, "request_id": payload["request_id"]},
            ).first()
            if prior:
                row = self._row(c, scope, prior[0])
                if canonical(row["canonical_input"]["request"]) != canonical(payload):
                    raise ChatError(409, "intent_conflict")
                return row, False
            busy = c.execute(
                text(
                    "SELECT operation_id FROM chat_operations WHERE tenant_id=:tenant_id "
                    "AND conversation_id=:conversation_id AND state IN ('active','waiting','paused')"
                ),
                scope,
            ).first()
            if busy:
                raise ChatError(409, "conversation_busy")
            raise ChatError(503, "storage_unavailable")

        return self._transaction(scope, create, on_unique=resolve_unique)

    def _write(self, c, scope, row):
        previous = row["revision"]
        row["revision"] += 1
        row["updated_at"] = self.clock()
        fields = [
            "state",
            "revision",
            "attempt_count",
            "current_attempt_id",
            "attempt_deadline",
            "retry_at",
            "attempts",
            "private_control",
            "result_message_id",
            "updated_at",
        ]
        params = {
            key: (
                canonical(row[key])
                if key in JSON_FIELDS
                else (
                    instant(row[key])
                    if key in ("attempt_deadline", "retry_at", "updated_at")
                    and row[key] is not None
                    else row[key]
                )
            )
            for key in fields
        }
        result = c.execute(
            text(
                "UPDATE chat_operations SET "
                + ",".join(f"{key}=:{key}" for key in fields)
                + " WHERE operation_id=:operation_id AND revision=:previous AND tenant_id=:tenant_id "
                "AND user_id=:user_id AND conversation_id=:conversation_id"
            ),
            {
                **scope,
                **params,
                "operation_id": row["operation_id"],
                "previous": previous,
            },
        )
        if result.rowcount != 1:
            raise ChatError(409, "operation_changed")
        return row

    def _settle(self, row):
        wait = row["private_control"]["wait"]
        reason = wait.get("reason")
        if reason is None:
            return
        now = self.clock()
        start, until = wait["started"], wait["until"]
        if (
            not isinstance(start, (int, float))
            or not isinstance(until, (int, float))
            or until < start
            or now < start
        ):
            row["state"] = "paused"
            row["private_control"]["pause_reason"] = "wait_integrity"
            wait["reason"] = None
            return
        key = "local_used_ms" if reason == "local_capacity" else "provider_used_ms"
        wait[key] = min(
            120000, wait[key] + max(0, round((min(now, until) - start) * 1000))
        )
        wait["started"] = min(now, until)
        if reason == "local_capacity" and wait[key] >= 120000:
            row["state"] = "paused"
            row["private_control"]["pause_reason"] = "local_budget_exhausted"
            wait["reason"] = None
        elif reason == "provider_delay" and now >= until:
            # One exclusive provider->local boundary, including delayed recovery.
            remaining = max(0, 120000 - wait["local_used_ms"]) / 1000
            wait.update(reason="local_capacity", started=until, until=until + remaining)
            self._settle(row)

    def reconcile(self, scope, operation_id):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] == "waiting":
                before = canonical(row)
                self._settle(row)
                return self._write(c, scope, row) if canonical(row) != before else row
            return row

        return self._transaction(scope, transition)

    def claim(self, scope, operation_id, boot_id, explicit=False):
        attempt_id, capability = str(uuid4()), str(uuid4())

        def transition(c):
            row = self._row(c, scope, operation_id)
            before = canonical(row)
            if row["state"] == "waiting":
                self._settle(row)
            if explicit:
                if row["state"] != "paused":
                    raise ChatError(409, "not_paused")
                if row["retry_at"] is not None and self.clock() < row["retry_at"]:
                    raise ChatError(409, "provider_not_ready")
            elif (
                row["state"] != "waiting"
                or row["private_control"]["wait"]["reason"] == "provider_delay"
            ):
                return (
                    self._write(c, scope, row) if canonical(row) != before else row
                ), False
            if row["attempt_count"] >= 4:
                row["state"] = "failed"
                row["private_control"]["pause_reason"] = "attempts_exhausted"
                return self._write(c, scope, row), False
            correction = row["private_control"].get("correction")
            if correction and (correction.get("claimed") or self.clock() >= correction["deadline"] - 5):
                row["state"] = "failed"
                row["private_control"]["pause_reason"] = "correction_exhausted"
                return self._write(c, scope, row), False
            row["private_control"]["wait"]["reason"] = None
            row["private_control"]["pause_reason"] = None
            row["private_control"].update(boot_id=boot_id, capability=capability)
            row.update(
                state="active",
                attempt_count=row["attempt_count"] + 1,
                current_attempt_id=attempt_id,
                attempt_deadline=correction["deadline"] if correction else durable_deadline(self.clock() + 120),
                retry_at=None,
            )
            row["attempts"].append(
                {
                    "attempt_id": attempt_id,
                    "number": row["attempt_count"],
                    "deadline": row["attempt_deadline"],
                    "outcome": "active",
                }
            )
            if correction:
                correction.update(claimed=True, attempt_id=attempt_id, number=row["attempt_count"])
            return self._write(c, scope, row), True

        return self._transaction(scope, transition)

    def pause_or_resume_wait(self, scope, operation_id):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] != "paused":
                raise ChatError(409, "not_paused")
            if row["retry_at"] is not None and self.clock() < row["retry_at"]:
                raise ChatError(409, "provider_not_ready")
            wait = row["private_control"]["wait"]
            remaining = max(0, 120000 - wait["local_used_ms"]) / 1000
            if remaining:
                row["state"] = "waiting"
                row["private_control"]["pause_reason"] = None
                wait.update(
                    reason="local_capacity",
                    started=self.clock(),
                    until=self.clock() + remaining,
                )
                return self._write(c, scope, row)
            return row

        return self._transaction(scope, transition)

    def close_attempt(
        self,
        scope,
        operation_id,
        attempt_id,
        *,
        transient,
        delay=0,
        reason="provider_error",
        partial="",
        usage=None,
    ):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] != "active" or row["current_attempt_id"] != attempt_id:
                return row
            from app.schemas.chat import reported_usage
            row["attempts"][-1].update(outcome=reason, partial=partial[:4000],
                                      usage=reported_usage(usage))
            row["current_attempt_id"] = None
            row["attempt_deadline"] = None
            wait = row["private_control"]["wait"]
            wait["reason"] = None
            if not transient or row["attempt_count"] >= 4 or row["private_control"].get("correction"):
                row["state"] = "failed"
                row["private_control"]["pause_reason"] = reason
            else:
                now = self.clock()
                row["retry_at"] = now + delay
                remaining = max(0, 120000 - wait["provider_used_ms"]) / 1000
                if delay > remaining:
                    row["state"] = "paused"
                    row["private_control"][
                        "pause_reason"
                    ] = "provider_budget_insufficient"
                elif delay > 0:
                    row["state"] = "waiting"
                    wait.update(reason="provider_delay", started=now, until=now + delay)
                else:
                    row["state"] = "waiting"
                    remaining = max(0, 120000 - wait["local_used_ms"]) / 1000
                    wait.update(
                        reason="local_capacity", started=now, until=now + remaining
                    )
            return self._write(c, scope, row)

        return self._transaction(scope, transition)

    def cache_recovery(self, scope, operation_id, attempt_id, cache):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] != "active" or row["current_attempt_id"] != attempt_id:
                raise ChatError(409, "attempt_not_current")
            row["private_control"]["recovery"] = cache
            return self._write(c, scope, row)
        return self._transaction(scope, transition)

    def correct(self, scope, operation_id, attempt_id, code, usage, key):
        from app.core.chat_correction import INSTRUCTIONS, verify_cache
        from app.schemas.chat import reported_usage

        def transition(c):
            row = self._row(c, scope, operation_id)
            control = row["private_control"]
            if (row["state"] != "active" or row["current_attempt_id"] != attempt_id
                or code not in INSTRUCTIONS or control.get("correction")
                or row["attempt_count"] >= 4 or self.clock() >= row["attempt_deadline"] - 5
                or not control.get("recovery")):
                return row
            verify_cache(control["recovery"], row, key)
            control["correction"] = {"code": code, "deadline": row["attempt_deadline"],
                                     "source_attempt": attempt_id, "claimed": False}
            row["attempts"][-1].update(outcome=code, usage=reported_usage(usage))
            row.update(state="waiting", current_attempt_id=None, attempt_deadline=None, retry_at=None)
            control["wait"].update(reason="local_capacity", started=self.clock(),
                                   until=control["correction"]["deadline"] - 5)
            return self._write(c, scope, row)
        return self._transaction(scope, transition)

    def stop(self, scope, operation_id):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] in TERMINAL:
                return row
            if row["state"] == "waiting":
                self._settle(row)
            row["state"] = "cancelled"
            row["private_control"]["wait"]["reason"] = None
            row["private_control"]["pause_reason"] = "user_stop"
            return self._write(c, scope, row)

        return self._transaction(scope, transition)

    def complete(self, scope, operation_id, attempt_id, result, metadata, result_id):
        def transition(c):
            row = self._row(c, scope, operation_id)
            if row["state"] == "completed" and row["result_message_id"] == result_id:
                chat_history.completed_result(c, scope, row)
                return row
            if (
                row["state"] != "active"
                or row["current_attempt_id"] != attempt_id
                or self.clock() >= row["attempt_deadline"]
            ):
                raise ChatError(409, "attempt_not_current")
            now = instant(self.clock())
            question = {
                "id": row["question_message_id"],
                "content": row["question_content"],
                "metadata": {},
                "created_at": now,
            }
            assistant = {
                "id": result_id,
                "content": result["answer"],
                "metadata": metadata,
                "created_at": now,
            }
            chat_history.append_final(c, scope, question, assistant)
            import os

            if os.getenv("SUMMARY_ENABLED", "false") == "true":
                self.compactions.pending(c, scope, row["canonical_input"]["context"])
            row.update(state="completed", result_message_id=result_id)
            row["attempts"][-1]["outcome"] = "completed"
            return self._write(c, scope, row)

        return self._transaction(scope, transition)

    def producer_state(self, scope, operation_id):
        # A stream fragment needs its fence, not a parent lock or JSON history.
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT operation_id,state,current_attempt_id,attempt_count,revision FROM chat_operations "
                        "WHERE operation_id=:operation_id AND tenant_id=:tenant_id AND user_id=:user_id "
                        "AND conversation_id=:conversation_id"
                    ),
                    {**scope, "operation_id": operation_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise ChatError(404, "not_found")
            return dict(row)

    def recoverable(self):
        with self.engine.connect() as c:
            return [
                dict(x)
                for x in c.execute(
                    text(
                        "SELECT operation_id,tenant_id,user_id,conversation_id "
                        "FROM chat_operations WHERE state IN ('active','waiting') ORDER BY retry_at,created_at"
                    )
                ).mappings()
            ]

    def result(self, scope, operation):
        def read(c):
            row = self._row(c, scope, operation["operation_id"])
            if row["state"] != "completed":
                raise ChatError(409, "result_not_ready")
            return chat_history.completed_result(c, scope, row)

        return self._transaction(scope, read)
