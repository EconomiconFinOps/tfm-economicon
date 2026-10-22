"""A separate-key, non-streaming summary request with owned cancellable transport."""
import asyncio
import hashlib
from functools import partial
from http.client import HTTPSConnection,HTTPResponse
import io
import json
import os
from pathlib import Path
import socket
import threading
import time
from urllib import request,error
from types import SimpleNamespace
from app.core.bedrock import BedrockError
from app.clients.bedrock import BedrockTransport
from pydantic import SecretStr
from app.clients.chat_gateway import _ChatHTTPConnection,_ChatHTTPSConnection,interrupt
from app.clients.chat_stream_parser import complete_json
from app.clients.litellm import _AttemptDeadline,_DeadlineReader,_RejectRedirectHandler,_usage_metadata,LiteLLMClient
from app.core.chat_resources import canonical

class SummaryGatewayError(Exception):
    def __init__(self,status,code):
        self.status,self.code=status,code
        super().__init__(code)

class _SummaryReader(_DeadlineReader):
    def __init__(self,sock,deadline,cancelled):
        super().__init__(sock,deadline)
        self.cancelled=cancelled

    def readinto(self,buffer):
        # shutdown from another thread need not wake a timed Windows recv.
        # Poll the owned socket, not SocketIO: a timeout poisons SocketIO's
        # subsequent reads. Keep its file reference solely for socket lifetime.
        while True:
            if self.cancelled.is_set():raise SummaryGatewayError(503,'summary_cancelled')
            self.sock.settimeout(min(.1,self.deadline.remaining()))
            try:
                count=self.sock.recv_into(buffer)
            except socket.timeout:
                continue
            self.deadline.remaining()
            if self.cancelled.is_set():raise SummaryGatewayError(503,'summary_cancelled')
            return count

class _SummarySocket:
    def __init__(self,sock,deadline,cancelled):
        self.sock,self.deadline,self.cancelled=sock,deadline,cancelled

    def makefile(self,mode):
        return io.BufferedReader(_SummaryReader(self.sock,self.deadline,self.cancelled))

class _SummaryResponse(HTTPResponse):
    def __init__(self,sock,*args,deadline,cancelled,**kwargs):
        super().__init__(_SummarySocket(sock,deadline,cancelled),*args,**kwargs)

class _OwnedConnection:
    def __init__(self,*args,holder,**kwargs):
        super().__init__(*args,**kwargs)
        self.response_class=partial(_SummaryResponse,deadline=self.deadline,cancelled=self.cancelled)
        holder['connection']=self

class _HTTP(_OwnedConnection,_ChatHTTPConnection):pass
class _HTTPS(_OwnedConnection,_ChatHTTPSConnection):pass

class _Handler:
    def do_open(self,http_class,req,**kwargs):
        connection=_HTTPS if http_class is HTTPSConnection else _HTTP
        return super().do_open(partial(connection,holder=req._summary_holder,deadline=req._attempt_deadline,cancelled=req._chat_cancelled),req,**kwargs)
class _HTTPHandler(_Handler,request.HTTPHandler):pass
class _HTTPSHandler(_Handler,request.HTTPSHandler):pass

class SummaryGateway:
    def __init__(self,settings):
        self.native = getattr(settings,'llm_provider','litellm') == 'bedrock'
        if settings.llm_model!='economicon-chat' or (not self.native and settings.litellm_api_key is None):
            raise ValueError('Summary configuration.')
        self.settings=settings
        if self.native:
            self.client=SimpleNamespace(transport=BedrockTransport(settings))
        else:
            self.client=LiteLLMClient(settings)
            self.client.transport=request.build_opener(request.ProxyHandler({}),_RejectRedirectHandler(),_HTTPHandler(),_HTTPSHandler())
        self.jobs={}

    def _post(self,messages,resources,deadline,holder,cancelled):
        # Leave time inside the lot deadline for validation and installation.
        remaining=deadline-time.time()-5
        if remaining<=0 or cancelled.is_set():raise SummaryGatewayError(504,'summary_deadline')
        payload={'model':'economicon-chat','messages':messages,'stream':False,'max_tokens':resources.context_budget['output_tokens'],
            'num_retries':0,'timeout':remaining,'reasoning':{'enabled':False},
            'provider':{'order':['deepinfra/fp4'],'allow_fallbacks':False,'require_parameters':True},
            'response_format':{'type':'json_schema','json_schema':{'name':'SummaryResponse','strict':True,'schema':resources.provider_response_schema}}}
        if self.native:
            payload.pop('provider');payload.pop('reasoning')
            payload['native_model_id']=self.client.transport.model_id
            req=SimpleNamespace(data=canonical(payload))
        else:
            req=request.Request(self.client.base_url+'/chat/completions',data=canonical(payload),
                headers={'Authorization':'Bearer '+self.settings.litellm_api_key.get_secret_value(),'Content-Type':'application/json'},method='POST')
        req._attempt_deadline=_AttemptDeadline(max(.001,deadline-time.time()-5))
        req._chat_cancelled=cancelled
        req._summary_holder=holder
        try:
            with self.client.transport.open(req,timeout=min(5,remaining)) as response:
                holder['response']=response
                if not response.headers.get('Content-Type','').startswith('application/json'):
                    raise ValueError('Summary provider format.')
                raw=response.read(1048577)
                req._attempt_deadline.remaining()
                if cancelled.is_set():raise SummaryGatewayError(503,'summary_cancelled')
                if len(raw)>1048576:raise ValueError('Summary provider limit.')
                body=complete_json(raw.decode('utf-8'))
                if not isinstance(body,dict):raise ValueError('Summary provider envelope.')
                choices=body.get('choices')
                if not isinstance(choices,list) or len(choices)!=1:
                    raise ValueError('Summary provider choices.')
                choice=choices[0]
                if not isinstance(choice,dict) or choice.get('index',0)!=0 or choice.get('finish_reason')!='stop':
                    raise ValueError('Summary provider completion.')
                message=choice.get('message')
                if not isinstance(message,dict) or not isinstance(message.get('content'),str):
                    raise ValueError('Summary provider content.')
                output=resources.validate_payload(complete_json(message['content']))
                usage=_usage_metadata(body,response.headers.get('x-litellm-response-cost')) or None
                return {'output':output,'usage':usage,'cost':None if usage is None else usage.get('cost_usd'),
                    'observed_model':body.get('model') if isinstance(body.get('model'),str) and len(body['model'])<=256 else None}
        except SummaryGatewayError:raise
        except BedrockError as failure:
            raise SummaryGatewayError(504 if failure.category=='timeout' else 502,'summary_native_provider') from None
        except error.HTTPError as failure:
            failure.close()
            raise SummaryGatewayError(503 if failure.code==429 else 502,'summary_provider_rejected') from None
        except (TimeoutError,socket.timeout):
            raise SummaryGatewayError(504,'summary_deadline') from None
        except error.URLError as failure:
            if isinstance(failure.reason,TimeoutError):raise SummaryGatewayError(504,'summary_deadline') from None
            raise SummaryGatewayError(502,'summary_transport') from None
        except ValueError:raise SummaryGatewayError(422,'summary_invalid_response') from None
        except Exception:raise SummaryGatewayError(502,'summary_transport') from None

    def cancel(self,job_id):
        job=self.jobs.get(job_id)
        if job is None:return
        holder,cancelled,worker=job
        cancelled.set()
        response=holder.get('response')
        if response is not None:interrupt(response)
        connection=holder.get('connection');sock=getattr(connection,'sock',None)
        if sock is not None:
            try:sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass

    async def dispatch(self,job_id,messages,resources,deadline):
        if job_id in self.jobs:raise SummaryGatewayError(409,'summary_job_replayed')
        holder={};cancelled=threading.Event()
        worker=asyncio.create_task(asyncio.to_thread(self._post,messages,resources,deadline,holder,cancelled))
        self.jobs[job_id]=(holder,cancelled,worker)
        try:
            return await asyncio.shield(worker)
        except asyncio.CancelledError:
            self.cancel(job_id)
            # Cancelling an asyncio waiter does not stop its thread. Keep the
            # strong reference until the owned worker has actually settled.
            raise
        finally:
            def finish(task):
                self.jobs.pop(job_id,None)
                if not task.cancelled():task.exception()
            if worker.done():finish(worker)
            else:worker.add_done_callback(finish)

    async def close(self):
        for job in list(self.jobs):self.cancel(job)
        await asyncio.gather(*(x[2] for x in list(self.jobs.values())),return_exceptions=True)

def configured_gateway():
    if os.getenv('SUMMARY_ENABLED','false').lower()!='true':return None
    from app.core.config import Settings
    from app.core.runtime_secrets import register_secrets
    try:
        settings=Settings()
        if settings.llm_provider=='mock':
            from app.clients.mock_chat import MockSummaryGateway,require_local_mock
            require_local_mock(settings)
            return MockSummaryGateway()
        if settings.llm_provider=='bedrock':return SummaryGateway(settings)
        if settings.llm_provider!='litellm' or settings.llm_model!='economicon-chat':return None
        path=Path(os.environ['SUMMARY_API_KEY_FILE'])
        if path.is_symlink() or not path.is_file() or not 16<=path.stat().st_size<=512:return None
        key=path.read_text(encoding='utf-8').strip()
        main=settings.litellm_api_key
        if not 16<=len(key)<=512 or any(c.isspace() for c in key) or key.startswith('sk-or-') or (main and key==main.get_secret_value()):
            return None
        class Secrets:
            model_fields=(*type(settings).model_fields,'summary_api_key')
            summary_api_key=SecretStr(key)
            def __getattr__(self,name):return getattr(settings,name)
        register_secrets(Secrets())
        return SummaryGateway(settings.model_copy(update={'litellm_api_key':SecretStr(key)}))
    except Exception:return None
