"""Prepared capture admission is bounded/closed; rejection persists nothing."""
import json

import pytest
from sqlalchemy import text
from test_chat_operations_jup035 import api,body,existing,headers,messages,path,run


def no_operation(api):
    with api[1].engine.connect() as connection:
        assert connection.execute(text('SELECT COUNT(*) FROM chat_operations')).scalar_one()==0
    assert messages(api[1])==[] and api[2].claims==[]


@pytest.mark.parametrize('field',['bearer_token','headers','profile','system_prompt'])
def test_unapproved_screen_fields_are_rejected_before_any_reservation(api,field):
    async def scenario(c):
        payload=body();payload['screen_context'][field]='synthetic-not-for-context'
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==422,response.text
        assert 'synthetic-not-for-context' not in response.text
        no_operation(api)
    run(scenario,api)


@pytest.mark.parametrize('change',[{'schema_version':'999'},{'captured_at':'not-a-time'},
                                  {'route':'https://untrusted.invalid/private'},{'datasets':'not-an-array'}])
def test_capture_version_route_timestamp_and_dataset_shape_are_validated(api,change):
    async def scenario(c):
        payload=body();payload['screen_context'].update(change)
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==422,response.text
        no_operation(api)
    run(scenario,api)


def demo_dataset(groups=None):
    return {'source':'demo','load_state':'loaded','loaded_at':'2026-10-09T22:00:00Z',
            'selection':{},'data_environment':'demo','completeness':{'status':'complete','missing_dimensions':[]},
            'totals':[{'currency':'EUR','amount':'0.00'}], 'groups':groups or [],'series':[],
            'counts':{'records':len(groups or []),'groups':len(groups or [])}}


def test_demo_capture_is_preserved_complete_without_promoting_it_to_evidence(api):
    async def scenario(c):
        payload=body();payload['screen_context']['datasets']=[demo_dataset([
            {'label':'Compute','currency':'EUR','amount':'-12.3400'}])]
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==200,response.text
        op=await existing(c,payload)
        context=await c.get(op['status_url']+'/context',headers=headers())
        assert context.json()['screen_context']==payload['screen_context']
        evidence=await c.get(op['status_url']+'/evidence',headers=headers())
        assert evidence.json()['items']==[]
    run(scenario,api)


def test_undeclared_provenance_is_admitted_and_preserved_without_renaming_it(api):
    async def scenario(c):
        payload=body()
        dataset=demo_dataset([{'label':'Compute','currency':'EUR','amount':'-12.3400'}])
        dataset.update(source='billing-summary-v2',data_environment='unknown')
        payload['screen_context']['datasets']=[dataset]
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==200,response.text
        op=await existing(c,payload)
        context=await c.get(op['status_url']+'/context',headers=headers())
        assert context.json()['screen_context']==payload['screen_context']
        assert context.json()['screen_context']['datasets'][0]['data_environment']=='unknown'
        assert (await c.get(op['status_url']+'/context',headers=headers('bob'))).status_code==404
    run(scenario,api)


@pytest.mark.parametrize('environment',['live','real','production'])
def test_undeclared_provenance_does_not_expand_to_other_client_claims(api,environment):
    async def scenario(c):
        payload=body()
        dataset=demo_dataset()
        dataset.update(source='billing-summary-v2',data_environment=environment)
        payload['screen_context']['datasets']=[dataset]
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==422,response.text
        no_operation(api)
    run(scenario,api)


def test_capture_over1mib_is413_without_reservation_or_silent_truncation(api):
    async def scenario(c):
        payload=body();payload['screen_context']['datasets']=[demo_dataset([
            {'label':'a'*256,'currency':'EUR','amount':'1.00'} for _ in range(3600)])]
        assert len(json.dumps(payload['screen_context'],ensure_ascii=False,separators=(',',':')).encode())>1048576
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==413,response.text
        no_operation(api)
    run(scenario,api)


def test_large_valid_capture_remains_complete_in_scoped_get_not_sse_frame(api):
    async def scenario(c):
        payload=body();payload['screen_context']['datasets']=[demo_dataset([
            {'label':'a'*256,'currency':'EUR','amount':'1.00'} for _ in range(2000)])]
        size=len(json.dumps(payload['screen_context'],ensure_ascii=False,separators=(',',':')).encode())
        assert 524288<size<1048576
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==200 and 'event: final' in response.text
        assert 'a'*256 not in response.text
        op=await existing(c,payload)
        resource=await c.get(op['status_url']+'/context',headers=headers())
        assert resource.json()['screen_context']==payload['screen_context']
        assert (await c.get(op['status_url']+'/context',headers=headers('bob'))).status_code==404
    run(scenario,api)


def test_public_body_over2mib_and_question_over16kib_are413_before_model(api):
    async def scenario(c):
        for size in [16385,2097153]:
            payload=body(content='a'*size)
            response=await c.post(path(),json=payload,headers=headers())
            assert response.status_code==413,response.text
            no_operation(api)
    run(scenario,api)


def test_depth_over32_is_rejected_before_normalizing_or_reserving(api):
    async def scenario(c):
        value='synthetic'
        for _ in range(33): value={'nested':value}
        payload=body();payload['screen_context']['selection']={'filters':{'tags':[value]}}
        response=await c.post(path(),json=payload,headers=headers())
        assert response.status_code==413,response.text
        no_operation(api)
    run(scenario,api)


def test_raw_body_size_includes_whitespace_even_when_capture_and_question_fit(api):
    async def scenario(c):
        raw=json.dumps(body()).encode()+b' '*2097153
        response=await c.post(path(),content=raw,headers={**headers(),'Content-Type':'application/json'})
        assert response.status_code==413,response.text
        no_operation(api)
    run(scenario,api)


def test_foreign_owner_is_rejected_before_reading_large_generation_body(api):
    async def scenario(c):
        response=await c.post(path(),content=b' '*2097153,headers=headers('bob'))
        assert response.status_code==404,response.text
        no_operation(api)
    run(scenario,api)
