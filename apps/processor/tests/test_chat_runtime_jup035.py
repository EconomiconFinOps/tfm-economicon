"""Two supervised listener apps retain one initialized ingestion resource owner."""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.core.runtime_secrets import StartupError


def test_health_lifespan_borrows_initialized_resources_and_does_not_close_them(monkeypatch):
    from app import main
    shared=SimpleNamespace(database=MagicMock(),queue=MagicMock(),vector_store=MagicMock())
    monkeypatch.setattr(main.app.state,'runtime_resources',shared,raising=False)
    database=MagicMock();queue=MagicMock();vector=MagicMock()
    constructors=[MagicMock(return_value=database),MagicMock(return_value=queue),MagicMock(return_value=vector)]
    for name,mock in zip(['Database','RabbitMQQueue','PgVectorStore'],constructors):
        monkeypatch.setattr(main,name,mock)
    async def exercise():
        async with main.lifespan(main.app):
            assert main.app.state.database is shared.database
            assert main.app.state.queue is shared.queue
            assert main.app.state.vector_store is shared.vector_store
    asyncio.run(exercise())
    assert all(mock.call_count==0 for mock in constructors)
    shared.database.dispose.assert_not_called()
    shared.queue.close.assert_not_called()
    shared.vector_store.close.assert_not_called()


@pytest.fixture
def combined(monkeypatch,tmp_path):
    from app import run_all
    from app import main
    monkeypatch.setenv('CHAT_ENABLED','true')
    monkeypatch.setenv('PROCESSOR_CHAT_BIND_HOST','172.31.35.3')
    monkeypatch.setenv('PROCESSOR_CHAT_PORT','8003')
    key=tmp_path/'synthetic.key';key.write_bytes(b'jup035-only-synthetic-signing-key-at-least32')
    monkeypatch.setenv('CHAT_SIGNING_KEY_FILE',str(key))
    monkeypatch.setenv('CHAT_RESOURCE_DIRECTORY','/workspace/apps/processor/app/agents/prompt_resources/jup035/chat/v2')
    worker=MagicMock()
    worker_factory=MagicMock(return_value=worker)
    monkeypatch.setattr(run_all,'ProcessorWorker',worker_factory)
    monkeypatch.setattr(run_all,'get_settings',lambda:Settings(_env_file=None))
    monkeypatch.setattr(run_all,'configure_logging',lambda:None)
    monkeypatch.setattr(run_all.threading,'Thread',MagicMock())
    calls=[]
    def legacy(*args,**kwargs):
        calls.append({'app':args[0] if args else kwargs.get('app'),'host':kwargs['host'],'port':kwargs['port']})
    monkeypatch.setattr(run_all.uvicorn,'run',legacy)
    class Server:
        def __init__(self,config):
            self.config=config;self.should_exit=False
        async def serve(self,sockets=None):
            calls.append({'app':self.config.app,'host':self.config.host,'port':self.config.port})
            await asyncio.sleep(0)
    monkeypatch.setattr(run_all.uvicorn,'Server',Server)
    bound=[]
    class Socket:
        def setsockopt(self,*args): pass
        def bind(self,address): bound.append(address)
        def listen(self,*args): pass
        def setblocking(self,*args): pass
        def close(self): pass
        def fileno(self): return 123
    import socket
    fake_socket=SimpleNamespace(socket=lambda *args,**kwargs:Socket(),
        AF_INET=socket.AF_INET,SOCK_STREAM=socket.SOCK_STREAM,
        SOL_SOCKET=socket.SOL_SOCKET,SO_REUSEADDR=socket.SO_REUSEADDR)
    # Replace only the entrypoint adapter; asyncio's own socketpair stays native.
    monkeypatch.setattr(run_all,'socket',fake_socket,raising=False)
    return run_all,main,worker_factory,worker,calls,bound


def test_combined_enabled_runtime_has_two_apps_with_private_specific_bind(combined):
    run_all,main,factory,worker,calls,bound=combined
    run_all.main()
    assert len(calls)==2,calls
    private=[call for call in calls if call['app'] is main.chat_app]
    public=[call for call in calls if call['app'] is main.app]
    assert len(private)==len(public)==1
    assert private[0]['host']=='172.31.35.3' and private[0]['port']==8003
    assert public[0]['host']=='0.0.0.0'
    assert ('172.31.35.3',8003) in bound
    assert factory.call_count==1
    assert main.app.state.runtime_resources is worker
    assert main.chat_app.state.chat_database is worker.database
    worker.close.assert_called_once()


@pytest.mark.parametrize('host',['0.0.0.0','127.0.0.1','not-an-ip'])
def test_unsafe_private_bind_fails_before_worker_or_any_listener(combined,monkeypatch,host):
    run_all,main,factory,worker,calls,bound=combined
    monkeypatch.setenv('PROCESSOR_CHAT_BIND_HOST',host)
    with pytest.raises(StartupError):
        run_all.main()
    assert factory.call_count==0 and calls==[] and bound==[]


def test_private_bind_collision_has_no_wildcard_or_port_fallback(combined,monkeypatch):
    run_all,main,factory,worker,calls,bound=combined
    class Collision:
        def setsockopt(self,*args): pass
        def bind(self,address):
            bound.append(address)
            raise OSError('Synthetic owned-port collision')
        def close(self): pass
    monkeypatch.setattr(run_all.socket,'socket',lambda *args,**kwargs:Collision())
    with pytest.raises(StartupError):
        run_all.main()
    assert bound==[('172.31.35.3',8003)]
    assert factory.call_count==0 and calls==[]


def test_private_runtime_keeps_exact_server_key_from_its_synthetic_file(combined):
    import os
    from pathlib import Path
    run_all,main,factory,worker,calls,bound=combined
    run_all.main()
    expected=Path(os.environ['CHAT_SIGNING_KEY_FILE']).read_bytes()
    assert getattr(main.chat_app.state,'chat_signing_key',None)==expected
    assert main.chat_app.state.chat_database is worker.database
