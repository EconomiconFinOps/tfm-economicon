"""Approved private cancel route, bounded nonce admission and SQL watchdog."""
import asyncio
import json
import time
from uuid import uuid4

from sqlalchemy import text
from test_chat_private_jup035 import private,claim,run,signed


def test_full_nonce_cache_rejects_new_request_with503_without_evicting_live_nonce(private,monkeypatch):
    nonces={str(uuid4()):time.time()+180 for _ in range(4096)}
    original=nonces.copy()
    monkeypatch.setattr(private[0].state,'chat_nonces',nonces)
    async def scenario(c):
        response=await c.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
        assert response.status_code==503,response.text
        assert nonces==original and private[3]==[]
    run(private[0],scenario)


def test_cancel_route_requires_confirmed_sql_stop_and_exact_control(private):
    async def scenario(c):
        endpoint='/internal/chat/v2/attempts/attempt/cancel'
        payload=claim();raw=json.dumps(payload,separators=(',',':')).encode()
        active=await c.post(endpoint,content=raw,headers=signed('POST',endpoint,raw))
        assert active.status_code==404
        with private[2].begin() as connection: connection.execute(text("UPDATE chat_operations SET state='cancelled' WHERE operation_id='op'"))
        stopped=await c.post(endpoint,content=raw,headers=signed('POST',endpoint,raw))
        assert stopped.status_code==200 and stopped.json()['cancelled'] is True
        changed=json.dumps(claim(capability='wrong'),separators=(',',':')).encode()
        assert (await c.post(endpoint,content=changed,headers=signed('POST',endpoint,changed))).status_code==404
        assert private[3]==[]
    run(private[0],scenario)


def test_sql_stop_ends_silent_gateway_without_waiting_for_next_fragment(private,monkeypatch):
    async def scenario(c):
        entered=asyncio.Event();closed=asyncio.Event()
        async def silent(context,deadline):
            private[3].append(context)
            try:
                yield {'type':'delta','text':'Provisional'}
                entered.set()
                await asyncio.Event().wait()
            finally: closed.set()
        monkeypatch.setattr(private[0].state,'chat_gateway',silent)
        raw=json.dumps(claim(),separators=(',',':')).encode()
        task=asyncio.create_task(c.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw)))
        await asyncio.wait_for(entered.wait(),2)
        with private[2].begin() as connection: connection.execute(text("UPDATE chat_operations SET state='cancelled' WHERE operation_id='op'"))
        try:
            response=await asyncio.wait_for(asyncio.shield(task),1.2)
            assert response.status_code==200 and '"candidate_end"' not in response.text
            assert closed.is_set() and len(private[3])==1
        finally:
            if not task.done(): task.cancel()
            await asyncio.gather(task,return_exceptions=True)
    run(private[0],scenario)
