"""One resource owner, ingestion thread and two supervised listener apps."""
import asyncio
import ipaddress
import os
import signal
import socket
import threading
from contextlib import contextmanager
from pathlib import Path

import uvicorn

from app.core.config import get_settings
from app.core.runtime_secrets import StartupError, startup_boundary
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


def private_listener():
    if os.getenv('CHAT_ENABLED','false').lower()!='true':
        return None,None,None
    try:
        host=os.environ['PROCESSOR_CHAT_BIND_HOST']
        address=ipaddress.IPv4Address(host)
        if str(address)!=host or not address.is_private or address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified:
            raise ValueError()
        port=int(os.getenv('PROCESSOR_CHAT_PORT','8003'))
        if not 1<=port<=65535:
            raise ValueError()
        key_file=Path(os.environ['CHAT_SIGNING_KEY_FILE'])
        if not 32<=key_file.stat().st_size<=4096:
            raise ValueError()
        key=key_file.read_bytes()
        if not 32<=len(key)<=4096:
            raise ValueError()
    except Exception:
        raise StartupError('Private chat configuration is invalid.') from None
    bound=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        bound.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        bound.bind((host,port))
        bound.listen(128)
        bound.setblocking(False)
        return bound,(host,port),key
    except Exception:
        bound.close()
        raise StartupError('Private chat address is unavailable; startup cannot continue.') from None


async def serve_dual(settings,health,chat,bound,address):
    class SupervisedServer(uvicorn.Server):
        @contextmanager
        def capture_signals(self):
            # The shared supervisor owns signals so either listener stops both.
            yield

    common={'access_log':False,'log_config':None,'reload':False,
            'workers':1,'lifespan':'on','timeout_graceful_shutdown':5}
    servers=[SupervisedServer(uvicorn.Config(health,host='0.0.0.0',port=settings.processor_port,**common)),
             SupervisedServer(uvicorn.Config(chat,host=address[0],port=address[1],**common))]
    stopped=asyncio.Event()
    loop=asyncio.get_running_loop()
    previous={}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGINT,signal.SIGTERM):
            previous[sig]=signal.getsignal(sig)
            signal.signal(sig,lambda *_:loop.call_soon_threadsafe(stopped.set))
    tasks=[asyncio.create_task(servers[0].serve()),asyncio.create_task(servers[1].serve(sockets=[bound]))]
    stop_task=asyncio.create_task(stopped.wait())
    try:
        done,_=await asyncio.wait([*tasks,stop_task],return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task is not stop_task:
                task.result()
    finally:
        for server in servers:
            server.should_exit=True
        stop_task.cancel()
        await asyncio.gather(stop_task,return_exceptions=True)
        try:
            await asyncio.wait_for(asyncio.gather(*tasks,return_exceptions=True),10)
        except TimeoutError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
        for sig,handler in previous.items():
            signal.signal(sig,handler)


@startup_boundary
def main() -> None:
    from app.aws_runtime import prepare_runtime
    prepare_runtime('processor')
    settings=get_settings()
    configure_logging()
    capacity=None
    if os.getenv('CHAT_ENABLED','false').lower()=='true':
        from app.chat import configured_capacity
        capacity=configured_capacity()
    bound,address,key=private_listener()
    worker=None
    thread=None
    try:
        worker=ProcessorWorker(settings)
        from app.main import app,chat_app
        app.state.runtime_resources=worker
        if bound is not None:
            chat_app.state.chat_database=worker.database
            chat_app.state.chat_signing_key=key
            chat_app.state.chat_capacity=capacity
        thread=threading.Thread(target=worker.run_forever,daemon=True,name='processor-worker')
        thread.start()
        if bound is None:
            uvicorn.run('app.main:app',host='0.0.0.0',port=settings.processor_port,
                        reload=False,access_log=False,log_config=None)
        else:
            asyncio.run(serve_dual(settings,app,chat_app,bound,address))
    finally:
        try:
            try:
                if worker is not None:
                    worker.stop()
            finally:
                if thread is not None and thread.ident is not None:
                    thread.join()
        finally:
            try:
                if worker is not None:
                    worker.close()
            finally:
                if bound is not None:
                    bound.close()


if __name__=='__main__':
    main()
