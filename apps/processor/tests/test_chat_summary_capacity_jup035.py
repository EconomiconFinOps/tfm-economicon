"""Shared admission through existing signed ASGI routes and counted local HTTP.

The summary provider is a scripted loopback HTTP server; main producer is a
controlled async fixture. Neither constitutes remote model fidelity evidence.
"""
import asyncio,json,time
from pathlib import Path
from sqlalchemy import text
import pytest
from app.agents.schemas import FinOpsResponse
from test_chat_private_jup035 import private,signed,claim
from test_chat_resources_jup035 import resources
from test_chat_summary_resources_jup035 import summary_bundle
from test_chat_summary_gateway_jup035 import summary_session,envelope,exercise,request,ROUTE,SCOPE,canonical

MAIN='/internal/chat/v2/attempts'
POLICY='jup-035.summary-one-reserve-five.v2'

def main_context(application):
    r=application.state.chat_resources;m=json.loads(r.manifest_bytes)
    messages=[{'role':'system','content':r.system},{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n{}'}]
    count=r.check_messages(messages,FinOpsResponse.model_json_schema())
    return {'prompt_version':r.prompt_version,'messages':messages,
        'financial_metrics_allowed':False,'tool_protocol':'structured-documentation-v3','manifest':{
        'prompt_version':r.prompt_version,'tokenizer_sha256':r.tokenizer_sha256,'response_schema_sha256':r.response_schema_sha256,
        'input_contract_sha256':m['input_contract_sha256'],'assembler_sha256':m['assembler_sha256'],'variable_tokens':count,
        'context_budget':r.context_budget}}

def claims(session,application,count):
    values=[]
    with session[0][0][2].begin() as c:
        for i in range(count):
            op='shared-op-'+str(i);attempt='shared-attempt-'+str(i)
            c.execute(text("INSERT INTO chat_operations SELECT :op,tenant_id,user_id,conversation_id,state,:attempt,attempt_count,attempt_deadline,private_control,input_hash FROM chat_operations WHERE operation_id='op'"),{'op':op,'attempt':attempt})
            values.append(claim(operation_id=op,attempt_id=attempt,context=main_context(application)))
    return values

async def post_main(client,value):return await request(client,'POST',MAIN,value)
async def wait_entered(entered,count):
    for _ in range(200):
        if len(entered)==count:return
        await asyncio.sleep(.005)
    pytest.fail('Expected actual controlled producer admission was not observed')
async def wait_summary(session):
    for _ in range(200):
        if session[2]:return
        await asyncio.sleep(.005)
    pytest.fail('Expected counted local summary HTTP dispatch was not observed')

@pytest.mark.parametrize('capacity,main_count,admit',[(5,0,False),(6,0,True),(6,1,False),(7,1,True),(7,2,False),(8,2,True),(8,3,False)])
def test_private_summary_shared_capacity_requires_five_main_slots_free(summary_session,monkeypatch,capacity,main_count,admit):
    monkeypatch.setattr(summary_session[0][0][0].state,'chat_capacity',capacity,raising=False)
    async def run(client,application):
        release=asyncio.Event();entered=[];tasks=[]
        async def gateway(context,deadline):
            entered.append(context);yield {'type':'delta','text':'Provisional'}
            await release.wait();yield {'type':'candidate','result':{'synthetic':'main'},'finish_reason':'stop','usage':None}
        monkeypatch.setattr(application.state,'chat_gateway',gateway)
        try:
            for body in claims(summary_session,application,main_count):tasks.append(asyncio.create_task(post_main(client,body)))
            await wait_entered(entered,main_count)
            body=envelope(summary_session)
            response=await request(client,'POST',ROUTE,body)
            assert response.status_code==(200 if admit else 503),response.text
            assert len(summary_session[2])==(1 if admit else 0)
            assert len(entered)==main_count and all(not t.done() for t in tasks)
            if not admit:
                release.set();await asyncio.gather(*tasks)
                if capacity>5:
                    response=await request(client,'POST',ROUTE,body)
                    assert response.status_code==200 and len(summary_session[2])==1
        finally:
            release.set();await asyncio.gather(*tasks,return_exceptions=True)
    exercise(summary_session,run)

@pytest.mark.parametrize('capacity',[6,7,8])
def test_summary_and_main_share_total_capacity_and_release_only_after_owned_job_closes(summary_session,monkeypatch,capacity):
    monkeypatch.setattr(summary_session[0][0][0].state,'chat_capacity',capacity,raising=False)
    summary_session[1].behavior='stall'
    async def run(client,application):
        release=asyncio.Event();entered=[];tasks=[];summary=None
        async def gateway(context,deadline):
            entered.append(context);yield {'type':'delta','text':'Provisional'}
            await release.wait();yield {'type':'candidate','result':{'synthetic':'main'},'finish_reason':'stop','usage':None}
        monkeypatch.setattr(application.state,'chat_gateway',gateway)
        try:
            body=envelope(summary_session);summary=asyncio.create_task(request(client,'POST',ROUTE,body));await wait_summary(summary_session)
            values=claims(summary_session,application,capacity)
            for value in values[:-1]:tasks.append(asyncio.create_task(post_main(client,value)))
            await wait_entered(entered,capacity-1)
            excess_task=asyncio.create_task(post_main(client,values[-1]));tasks.append(excess_task)
            for _ in range(200):
                if excess_task.done() or len(entered)>=capacity:break
                await asyncio.sleep(.005)
            live_summaries=len([job for job in application.state.summary_jobs.values() if not job.settled])
            assert live_summaries==1 and len(entered)+live_summaries<=capacity, 'Observed upstream main plus summary exceeds shared capacity'
            assert excess_task.done(), 'Excess main must be refused before upstream admission'
            excess=await excess_task
            assert excess.status_code==503 and excess.json()['code']=='capacity_unavailable',excess.text
            assert len(entered)==capacity-1 and len(summary_session[2])==1
            duplicate=await request(client,'POST',ROUTE,envelope(summary_session))
            assert duplicate.status_code==503 and len(summary_session[2])==1
            control={'v':2,'scope':SCOPE,'boot_id':body['boot_id'],'input_hash':body['input_hash']}
            cancelled=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
            assert cancelled.status_code in [200,202]
            await asyncio.wait_for(summary,2)
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.json()['settled'] is True
            task=asyncio.create_task(post_main(client,values[-1]));tasks.append(task)
            await wait_entered(entered,capacity)
            assert len(summary_session[2])==1
        finally:
            release.set();summary_session[4].set()
            await asyncio.gather(*tasks,*([summary] if summary is not None else []),return_exceptions=True)
    exercise(summary_session,run)

@pytest.mark.parametrize('flag',['false','TRUE','1','yes',''])
def test_summary_flag_is_strict_off_by_default_and_main_remains_ready(summary_session,monkeypatch,flag):
    if flag=='':monkeypatch.delenv('SUMMARY_ENABLED')
    else:monkeypatch.setenv('SUMMARY_ENABLED',flag)
    async def run(client,application):
        body=envelope(summary_session)
        response=await request(client,'POST',ROUTE,body)
        assert response.status_code==503 and summary_session[2]==[],response.text
        main=await client.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
        assert main.status_code==200
    exercise(summary_session,run)

@pytest.mark.parametrize('capacity',[5,6,7,8])
def test_summary_descriptor_reports_frozen_boot_capacity_and_policy_before_admission_without_provider(summary_session,monkeypatch,capacity):
    monkeypatch.setattr(summary_session[0][0][0].state,'chat_capacity',capacity,raising=False)
    async def run(client,application):
        monkeypatch.setenv('CHAT_MAX_ACTIVE',str(5 if capacity!=5 else 8))
        path='/internal/chat/v2/summary/descriptor'
        response=await client.get(path,headers=signed('GET',path));assert response.status_code==200,response.text
        value=response.json()
        assert value.get('capacity')==capacity and value.get('admission_policy')==POLICY and value.get('summary_ready') is True
        assert value['boot_id']==application.state.chat_boot_id and summary_session[2]==[]
        assert application.state.summary_jobs=={}
    exercise(summary_session,run)

def test_compose_summary_is_server_only_same_strict_optional_flag_and_separate_key_path():
    root=Path(__file__).resolve().parents[3]
    source=(root/'docker-compose.yml').read_text()
    ai=(root/'infra/litellm/compose.ai.yml').read_text()
    services={};current=None
    for line in source.splitlines():
        if line.startswith('  ') and not line.startswith('   ') and line.endswith(':'):
            current=line.strip()[:-1];services[current]={}
        elif current and line.startswith('      ') and ':' in line:
            key,value=line.strip().split(':',1);services[current][key]=value.strip()
    assert services['backend'].get('SUMMARY_ENABLED')=='${SUMMARY_ENABLED:-true}'
    assert services['processor'].get('SUMMARY_ENABLED')==services['backend']['SUMMARY_ENABLED']
    assert services['backend'].get('SUMMARY_RESOURCE_DIRECTORY')=='/opt/economicon/summary/v3'
    assert services['processor'].get('SUMMARY_RESOURCE_DIRECTORY')=='/app/app/agents/prompt_resources/jup035/summary/v3'
    assert 'SUMMARY_API_KEY_FILE' not in source
    assert 'SUMMARY_API_KEY_FILE: /run/secrets/summary-api-key' in ai
    assert '- summary-api-key' in ai
    assert 'file: ${SUMMARY_API_KEY_FILE:?required separate summary virtual-key file}' in ai

def test_private_second_summary_at_eight_and_zero_main_is_rejected_by_max_one_not_total_capacity(summary_session,monkeypatch):
    application=summary_session[0][0][0]
    monkeypatch.setattr(application.state,'chat_capacity',8,raising=False)
    summary_session[1].behavior='stall'
    async def run(client,application):
        first=second=None
        try:
            first=asyncio.create_task(request(client,'POST',ROUTE,envelope(summary_session)))
            await wait_summary(summary_session)
            assert len(summary_session[2])==1 and application.state.chat_attempts=={}
            active=[job for job in application.state.summary_jobs.values() if not job.settled]
            assert len(active)==1 and active[0].task is not None
            second=asyncio.create_task(request(client,'POST',ROUTE,envelope(summary_session)))
            for _ in range(200):
                if second.done() or len(summary_session[2])>=2:break
                await asyncio.sleep(.005)
            assert len(summary_session[2])==1,'Second counted upstream dispatch violates max-one despite six free slots'
            assert second.done(),'Second job should be refused before dispatch, not wait on a second worker'
            response=await second
            assert response.status_code==503 and response.json()['code']=='summary_capacity',response.text
            assert len([job for job in application.state.summary_jobs.values() if not job.settled])==1
            summary_session[4].set();response=await asyncio.wait_for(first,2)
            assert response.status_code==200 and response.json()['settled'] is True and len(summary_session[2])==1
        finally:
            summary_session[4].set()
            await asyncio.gather(*(t for t in (first,second) if t is not None),return_exceptions=True)
    exercise(summary_session,run)
