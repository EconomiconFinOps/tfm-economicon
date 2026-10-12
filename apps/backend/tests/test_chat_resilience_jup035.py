"""Recovery and memory lifetime, using controlled operations without model calls."""
import asyncio

import pytest
from sqlalchemy.exc import OperationalError

from test_chat_operations_jup035 import api, body
from app.services.chat_operations import service


@pytest.mark.parametrize("component", ["operations", "summaries"])
def test_scheduler_survives_database_outage_and_completes_waiting_operation(api, monkeypatch, caplog, component):
    async def scenario():
        runtime = service(api[0])
        runtime.occupied = runtime.capacity
        scope = dict(tenant_id="t", user_id="alice", conversation_id="alice-chat")
        row, _ = await runtime.open(scope, body())
        assert row["state"] == "waiting"
        runtime.occupied = 0
        failed = asyncio.Event()
        if component == "operations":
            original = runtime.repository.recoverable
            def recover():
                if not failed.is_set():
                    failed.set()
                    raise OperationalError("PRIVATE SQL", {}, Exception("PRIVATE DETAIL"))
                return original()
            monkeypatch.setattr(runtime.repository, "recoverable", recover)
        else:
            original = runtime.summary.recover
            async def recover():
                if not failed.is_set():
                    failed.set()
                    raise OperationalError("PRIVATE SQL", {}, Exception("PRIVATE DETAIL"))
                return await original()
            monkeypatch.setattr(runtime.summary, "recover", recover)
        runtime.start()
        try:
            await asyncio.wait_for(failed.wait(), 2)
            async def completed():
                while True:
                    current = await runtime.get(scope, row["operation_id"])
                    if current["state"] == "completed":
                        return current
                    await asyncio.sleep(.01)
            await asyncio.wait_for(completed(), 3)
            assert len(api[2].claims) == 1
            assert not runtime.scheduler.done()
        finally:
            await runtime.close()
        assert "chat_scheduler_diagnostic" in caplog.text
        assert "PRIVATE SQL" not in caplog.text and "PRIVATE DETAIL" not in caplog.text
    asyncio.run(scenario())


def test_start_replaces_finished_scheduler_but_close_prevents_restart(api):
    async def scenario():
        runtime = service(api[0])
        runtime.scheduler = asyncio.create_task(asyncio.sleep(0))
        previous = runtime.scheduler
        await previous
        runtime.start()
        assert runtime.scheduler is not previous
        await runtime.close()
        runtime.start()
        assert runtime.scheduler.done()
    asyncio.run(scenario())


def test_completed_operation_releases_unobserved_buffer(api):
    async def scenario():
        runtime = service(api[0])
        scope = dict(tenant_id="t", user_id="alice", conversation_id="alice-chat")
        row, _ = await runtime.open(scope, body())
        producer = runtime.tasks[row["operation_id"]]
        await producer
        async def released():
            while row["operation_id"] in runtime.buffers:
                await asyncio.sleep(.01)
        await asyncio.wait_for(released(), 2)
        frames = [frame async for frame in runtime.events(scope, row["operation_id"])]
        assert any(frame.startswith("event: final") for frame in frames)
        await runtime.close()
    asyncio.run(scenario())
