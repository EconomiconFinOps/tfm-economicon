"""Three review interleavings, simulated remote boundary and real SQL repository."""
import asyncio
from uuid import uuid4
import pytest
from app.db.chat_repository import ChatError
from test_chat_operations_jup035 import api, body, ANSWER
from test_chat_summary_lifecycle_jup035 import summary_resources53
from test_chat_summary_scheduler_jup035 import packet, runtime, source, context, idle, SCOPE


def test_live_worker_releases_own_reservation_after_other_worker_settles(packet):
    first, a = runtime(packet)
    second, b = runtime(packet)
    source(packet, count=5, long=False)
    remote = packet[3]
    remote.mode = 'uncertain'
    async def exercise():
        try:
            a.on_completed(SCOPE, context(8192), str(uuid4()))
            await idle(a)
            assert a.reserved and first.occupied == 1 and len(remote.calls) == 1
            await b.recover(); await idle(b)
            assert a.reserved and b.reserved and len(remote.calls) == 1
            await a.recover(); await idle(a)
            assert a.reserved and first.occupied == 1 and len(remote.calls) == 1
            remote.confirmed = True
            await b.recover(); await idle(b)
            assert first.repository.compactions.get(SCOPE)['state'] == 'failed'
            assert second.occupied == 0
            await a.recover(); await idle(a)
            assert not a.reserved and first.occupied == 0, 'settlement by B stranded reservation in live A'
            assert len(remote.calls) == 1
            with pytest.raises(ChatError):
                await first.open(SCOPE, body())
            remote.mode = 'valid'
            other = {**SCOPE, 'user_id': 'bob', 'conversation_id': 'bob-chat'}
            source(packet, count=5, long=False, scope=other)
            a.on_completed(other, context(8192), str(uuid4()))
            await idle(a)
            assert len(remote.calls) == 2 and not a.reserved
        finally:
            await first.close(); await second.close()
    asyncio.run(exercise())


def test_complete_context_pressure_survives_reload_without_ram_record(packet):
    first, a = runtime(packet)
    source(packet, count=5, long=False)
    repo = first.repository
    ctx = {'prompt_version': 'synthetic', 'messages': [], 'manifest': {'variable_tokens': 8192}}
    row, _ = repo.reserve(SCOPE, body(), ctx)
    row, won = repo.claim(SCOPE, row['operation_id'], 'synthetic-boot')
    assert won
    repo.complete(SCOPE, row['operation_id'], row['current_attempt_id'], ANSWER,
        {'generation': {'v':2,'state':'completed','question_message_id': row['question_message_id']}}, str(uuid4()))
    second, b = runtime(packet)
    async def exercise():
        try:
            assert not a.records and not b.records
            assert repo.compactions.get(SCOPE)['state'] == 'pending'
            await b.recover(); await idle(b)
            assert len(packet[3].calls) == 1, 'lost committed full-context pressure after reload'
            assert repo.compactions.get(SCOPE) is None
            assert packet[3].calls[0]['selected_pairs'] == 2
        finally:
            await first.close(); await second.close()
    asyncio.run(exercise())
