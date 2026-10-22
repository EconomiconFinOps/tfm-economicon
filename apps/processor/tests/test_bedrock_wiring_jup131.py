import json
import asyncio
import threading
import time
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.bedrock import TITAN_MODEL
from app.clients.bedrock import BedrockTransport
from app.agents.providers import get_provider


def settings(**changes):
    values = dict(llm_provider='bedrock',llm_model='economicon-chat',bedrock_region='eu-south-2',
        bedrock_chat_model_id='eu.amazon.nova-micro-v1:0',embedding_provider='bedrock',
        embedding_model=TITAN_MODEL,embedding_dimension=1024,ai_execution_mode='evaluation')
    values.update(changes)
    return Settings(**values,_env_file=None)


def test_chat_and_summary_factories_use_native_transport_without_gateway_keys(monkeypatch):
    from app.core import config
    from app.clients.chat_gateway import configured_gateway
    from app.clients.summary_gateway import configured_gateway as summary_gateway
    s = settings()
    assert s.litellm_api_key is None
    monkeypatch.setattr(config,'get_settings',lambda: s)
    monkeypatch.setattr(config,'Settings',lambda: s)
    monkeypatch.setenv('SUMMARY_ENABLED','true')
    chat, summary = configured_gateway(),summary_gateway()
    assert isinstance(chat.client.transport,BedrockTransport)
    assert isinstance(summary.client.transport,BedrockTransport)
    assert chat.client.transport.model_id == summary.client.transport.model_id == 'eu.amazon.nova-micro-v1:0'


def test_legacy_agent_factory_uses_converse_and_validates_json_schema():
    provider = get_provider('bedrock',settings=settings())
    sdk = Mock()
    sdk.converse.return_value={'output':{'message':{'content':[{'toolUse':{'name':'FinOpsResponse',
        'input':{'response':{'answer':'Respuesta'}}}}]}},'stopReason':'tool_use',
        'usage':{'inputTokens':4,'outputTokens':2,'totalTokens':6}}
    provider.runtime._client=sdk
    result=provider.invoke('Pregunta',response_format={'type':'json_schema','json_schema':{
        'name':'FinOpsResponse','schema':{'type':'object','properties':{'answer':{'type':'string'}},'required':['answer']}}})
    assert json.loads(result)=={'answer':'Respuesta'}
    assert sdk.converse.call_count==1


@pytest.mark.parametrize('value',[None,'global.amazon.nova-micro-v1:0','us.amazon.nova-micro-v1:0','unreviewed-model'])
def test_model_choice_requires_an_explicit_supported_eu_profile(value):
    with pytest.raises(ValidationError): settings(bedrock_chat_model_id=value)


def test_native_chat_preserves_private_review_and_only_emits_validated_final_output():
    from app.clients.chat_gateway import ChatGateway
    from test_chat_review_flow_jup035 import PLAN,FINAL,CONTEXT,Resources,execute
    from test_bedrock_transport_jup131 import Events,events
    gateway=ChatGateway(settings())
    gateway.resources=Resources()
    sdk=Mock();streams=[];calls=[]
    def generate(**parameters):
        if streams: assert streams[-1].closed
        calls.append(parameters)
        name=parameters['toolConfig']['tools'][0]['toolSpec']['name']
        values=events()
        values[1]['contentBlockStart']['start']['toolUse']['name']=name
        values[2]['contentBlockDelta']['delta']['toolUse']['input']=json.dumps({'response': PLAN if name=='PrivateAnswerPlan' else FINAL})
        stream=Events(values);streams.append(stream)
        return {'stream':stream}
    sdk.converse_stream.side_effect=generate
    gateway.client.transport.runtime._client=sdk
    result=execute(gateway)
    assert sdk.converse_stream.call_count==2
    assert [p['inferenceConfig']['maxTokens'] for p in calls]==[1000,2200]
    assert ''.join(x['text'] for x in result if x['type']=='delta')=='Hola 😀'
    assert not any(x['type']=='draft' for x in result)
    assert result[-1]['type']=='candidate'
    assert result[-1]['usage_report']['observed']['total_tokens']==32
    assert result[-1]['usage_report']['complete'] is False  # price is not supplied by Converse
    assert result[-1]['usage'] == {'prompt_tokens':24,'completion_tokens':8,'total_tokens':32}
    assert all(s.closed for s in streams)


def test_native_summary_uses_the_existing_payload_validator_without_a_separate_api_key():
    from app.clients.summary_gateway import SummaryGateway
    from test_summary_sizes_jup035 import current
    resources=current()
    output=dict(v=2,topics=[],facts=[],limitations=['Sin datos adicionales.'])
    gateway=SummaryGateway(settings())
    sdk=Mock()
    sdk.converse.return_value={'output':{'message':{'role':'assistant','content':[{'toolUse':{
        'name':'SummaryResponse','input':{'response':output}}}]}},'stopReason':'tool_use',
        'usage':{'inputTokens':12,'outputTokens':4,'totalTokens':16}}
    gateway.client.transport.runtime._client=sdk
    result=gateway._post([{'role':'system','content':'Reglas'},{'role':'user','content':'Resumen'}],
        resources,time.time()+30,{},threading.Event())
    assert result['output']==output and result['usage']['total_tokens']==16
    assert result['cost'] is None and result['observed_model'] is None


def test_cancel_interrupts_the_owned_native_stream_and_does_not_dispatch_final():
    from app.clients.chat_gateway import ChatGateway
    from test_chat_review_flow_jup035 import CONTEXT,Resources
    from test_bedrock_transport_jup131 import Events,events
    started,released=threading.Event(),threading.Event()
    class Blocking(Events):
        def __iter__(self):
            values=events()
            values[1]['contentBlockStart']['start']['toolUse']['name']='PrivateAnswerPlan'
            yield from values[:2]
            started.set()
            assert released.wait(5)
            yield from values[2:]
        def close(self):
            super().close();released.set()
    stream=Blocking([])
    gateway=ChatGateway(settings());gateway.resources=Resources()
    sdk=Mock();sdk.converse_stream.return_value={'stream':stream}
    gateway.client.transport.runtime._client=sdk
    async def run():
        async def consume(): return [x async for x in gateway(CONTEXT,time.time()+120)]
        task=asyncio.create_task(consume())
        assert await asyncio.to_thread(started.wait,3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    try: asyncio.run(run())
    finally: stream.close()
    assert stream.closed and released.is_set() and sdk.converse_stream.call_count==1
