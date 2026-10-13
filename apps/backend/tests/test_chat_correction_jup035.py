"""Bounded recovery uses the existing operation and durable attempt budget."""

import asyncio
import copy
import pytest

from test_chat_operations_jup035 import api, body, headers, path, ANSWER
from app.services.chat_operations import service


def test_rejected_draft_is_never_published(api):
    asyncio.run(check_draft(api))


async def check_draft(api):
    app, _, processor, _ = api
    processor.release = asyncio.Event()
    manager = service(app)
    scope = {"tenant_id": "t", "user_id": "alice", "conversation_id": "alice-chat"}
    row, _ = await manager.open(scope, body())
    await asyncio.sleep(.08)
    buffer = manager.buffers[row["operation_id"]]
    assert buffer["partial"] == ""
    assert not any("event: delta" in frame for frame in buffer["events"])
    processor.release.set()
    await asyncio.gather(*list(manager.tasks.values()))
    final = await manager.get(scope, row["operation_id"])
    assert final["state"] == "completed"
    assert any("event: final" in frame for frame in buffer["events"])
    await manager.close()


def test_correction_cache_is_bound_and_authenticated():
    from app.core.chat_correction import seal_cache, verify_cache
    identity = {"tenant_id": "t", "user_id": "u", "conversation_id": "c",
                "operation_id": "o", "input_hash": "hash"}
    cache = seal_cache(identity, {"content": "source"}, {"messages": []}, b"k" * 32)
    assert verify_cache(cache, identity, b"k" * 32)
    for field in identity:
        foreign = {**identity, field: "foreign"}
        with pytest.raises(ValueError):
            verify_cache(cache, foreign, b"k" * 32)
    altered = copy.deepcopy(cache)
    altered["effective"]["messages"] = ["altered"]
    with pytest.raises(ValueError):
        verify_cache(altered, identity, b"k" * 32)


def test_one_correction_uses_existing_attempt_and_original_deadline(api):
    from app.core.chat_correction import seal_cache
    app, _, _, clock = api
    manager = service(app)
    repo = manager.repository
    scope = {"tenant_id": "t", "user_id": "alice", "conversation_id": "alice-chat"}
    row, _ = repo.reserve(scope, body(), {"prompt_version": "synthetic-v2"})
    row, won = repo.claim(scope, row["operation_id"], "synthetic-boot")
    assert won
    original = row["attempt_deadline"]
    cache = seal_cache(row, {}, {}, b"k" * 32)
    row = repo.cache_recovery(scope, row["operation_id"], row["current_attempt_id"], cache)
    clock.advance(25)
    row = repo.correct(scope, row["operation_id"], row["current_attempt_id"],
                       "unused_documentary_evidence", {"completion_tokens": 12}, b"k" * 32)
    assert row["state"] == "waiting"
    # A new repository instance simulates losing all process-local retry state.
    from app.db.chat_repository import ChatRepository
    repo = ChatRepository(api[1], clock)
    row, won = repo.claim(scope, row["operation_id"], "synthetic-boot")
    assert won and row["attempt_count"] == 2
    assert row["attempt_deadline"] == original
    assert row["attempts"][0]["usage"]["completion_tokens"] == 12
    row = repo.correct(scope, row["operation_id"], row["current_attempt_id"],
                       "unused_documentary_evidence", None, b"k" * 32)
    assert row["state"] == "active"
    row = repo.close_attempt(scope, row["operation_id"], row["current_attempt_id"], transient=True)
    assert row["state"] == "failed"


@pytest.mark.parametrize("second_error", [False, True, "cancel"])
def test_full_correction_reuses_retrieval_and_persists_once(api, second_error):
    async def scenario():
        app, db, processor, _ = api
        original_builder = app.state.chat_context_builder
        searches = []
        async def builder(scope, payload, descriptor):
            context = await original_builder(scope, payload, descriptor)
            return {**context, "tool_protocol": "server-documentation-v4"}
        async def extension(scope, context, control, deadline):
            searches.append(control)
            return {"content": "{}"}, context
        builder.tool_extension = extension
        app.state.chat_context_builder = builder
        processor.key = b"k" * 32
        correction_started = asyncio.Event()
        release_correction = asyncio.Event()
        async def tool_result(claim, result):
            assert result == {"content": "{}"}
        processor.tool_result = tool_result
        async def stream(claim):
            processor.claims.append(copy.deepcopy(claim))
            if "correction" not in claim:
                yield {"type": "tool_call", "assistant": {"action": "search"}}
            elif second_error == "cancel":
                correction_started.set()
                await release_correction.wait()
            yield {"type": "delta", "text": "REJECTED_DRAFT" if len(processor.claims) == 1 else "OK"}
            if len(processor.claims) == 1 or second_error:
                yield {"type": "error", "category": "invalid_response", "status": 422,
                       "rule_code": "unused_documentary_evidence",
                       "usage": {"completion_tokens": 7, "cost_usd": "0.001"}}
            else:
                yield {"type": "candidate", "result": ANSWER, "finish_reason": "stop",
                       "usage": {"completion_tokens": 11, "cost_usd": "0.002"}}
        processor.stream = stream
        manager = service(app, active=True)
        scope = {"tenant_id": "t", "user_id": "alice", "conversation_id": "alice-chat"}
        try:
            row, _ = await manager.open(scope, body())
            if second_error == "cancel":
                await asyncio.wait_for(correction_started.wait(), 5)
                await manager.stop(scope, row["operation_id"])
                release_correction.set()
            async def terminal():
                while True:
                    current = await manager.get(scope, row["operation_id"])
                    if current["state"] in ("completed", "failed", "cancelled"):
                        return current
                    await asyncio.sleep(.005)
            final = await asyncio.wait_for(terminal(), 5)
            expected = "cancelled" if second_error == "cancel" else "failed" if second_error else "completed"
            assert final["state"] == expected
            assert len(searches) == 1 and len(processor.claims) == 2
            assert processor.claims[0]["context"] == processor.claims[1]["context"]
            assert processor.claims[0]["deadline"] == processor.claims[1]["deadline"]
            history = db.fetch_messages("alice-chat", "t", "alice")
            assert len(history) == (0 if second_error else 2)
            if not second_error:
                result = manager.repository.result(scope, final)
                assert result["content"] == ANSWER["answer"]
                assert result["metadata"]["generation"]["usage"] == {
                    "completion_tokens": 18, "cost_usd": "0.003"}
            assert "REJECTED_DRAFT" not in str(final["attempts"])
        finally:
            await manager.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["deadline", "limit", "cancel", "security"])
def test_correction_admission_rejects_exhausted_or_unsafe_work(api, mode):
    from app.core.chat_correction import seal_cache
    app, _, _, clock = api
    repo = service(app).repository
    scope = {"tenant_id": "t", "user_id": "alice", "conversation_id": "alice-chat"}
    row, _ = repo.reserve(scope, body(), {"prompt_version": "synthetic-v2"})
    for number in range(4 if mode == "limit" else 1):
        row, _ = repo.claim(scope, row["operation_id"], "synthetic-boot")
        if mode == "limit" and number < 3:
            row = repo.close_attempt(scope, row["operation_id"], row["current_attempt_id"], transient=True)
    row = repo.cache_recovery(scope, row["operation_id"], row["current_attempt_id"],
                             seal_cache(row, {}, {}, b"k" * 32))
    if mode == "deadline":
        clock.advance(116)
    if mode == "cancel":
        row = repo.stop(scope, row["operation_id"])
    result = repo.correct(scope, row["operation_id"], row["current_attempt_id"],
                          "evidence_provenance" if mode == "security" else "unused_documentary_evidence",
                          None, b"k" * 32)
    assert "correction" not in result["private_control"]
    assert result["state"] == ("cancelled" if mode == "cancel" else "active")


def test_truncated_candidate_preserves_reported_consumption(api):
    async def scenario():
        app, _, processor, _ = api

        async def stream(claim):
            yield {"type": "candidate", "result": ANSWER, "finish_reason": "length",
                   "usage": {"completion_tokens": 6400, "cost_usd": "0.004"}}

        processor.stream = stream
        manager = service(app)
        scope = {"tenant_id": "t", "user_id": "alice", "conversation_id": "alice-chat"}
        row, _ = await manager.open(scope, body())
        await asyncio.gather(*list(manager.tasks.values()))
        row = manager.repository.get(scope, row["operation_id"])
        assert row["attempts"][0]["usage"] == {
            "completion_tokens": 6400, "cost_usd": "0.004"}
        await manager.close()

    asyncio.run(scenario())
