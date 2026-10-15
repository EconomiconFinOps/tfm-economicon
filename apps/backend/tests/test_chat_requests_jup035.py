"""Private requests are recoverable without becoming canonical messages."""
import asyncio
import json
from datetime import datetime,timezone

from sqlalchemy import event,text

from app.api.dependencies import get_current_user
from app.db.chat_repository import ChatRepository
from test_chat_operations_jup035 import api,body,headers,messages,run

def scope(owner='alice',tenant='t',conversation=None):
    return {'tenant_id':tenant,'user_id':owner,'conversation_id':conversation or owner+'-chat'}

def reserve(api,owned,question):
    payload=body(owned['user_id'],question)
    payload['screen_context']['identity']={'tenant_id':owned['tenant_id'],'user_id':owned['user_id']}
    return ChatRepository(api[1],api[3]).reserve(owned,payload,{
        'prompt_version':'synthetic-v2','messages':[{'role':'system','content':'synthetic-system-secret'}],
        'authorized_evidence':[]})[0]

def other_tenant(api):
    owned=scope(tenant='other',conversation='alice-other')
    now=datetime.now(timezone.utc)
    history={'schema_version':1,'identity':owned,'revision':0,'next_ordinal':0,'messages':[]}
    with api[1].engine.begin() as connection:
        connection.execute(text("INSERT INTO tenants VALUES ('other','Other','other','test')"))
        connection.execute(text("INSERT INTO user_tenants VALUES ('alice','other','member',:now)"),{'now':now})
        connection.execute(text("INSERT INTO conversations(id,tenant_id,user_id,title,created_at,updated_at,dialogue_history) "
            "VALUES ('alice-other','other','alice','Other',:now,:now,:history)"),{'now':now,'history':json.dumps(history)})
    return owned

def test_private_pending_and_terminal_questions_are_recoverable_without_history_or_dispatch(api):
    alice=reserve(api,scope(),'Pregunta pendiente propia')
    bob=reserve(api,scope('bob'),'Pregunta de Bob privada')
    other=reserve(api,other_tenant(api),'Pregunta de otro cliente')
    ChatRepository(api[1],api[3]).stop(scope('bob'),bob['operation_id'])
    async def scenario(client):
        response=await client.get('/assistant/requests',headers=headers())
        assert response.status_code==200,response.text
        items=response.json()['items']
        assert len(items)==1 and items[0]['question']=='Pregunta pendiente propia'
        assert items[0]['conversation_id']=='alice-chat'
        assert items[0]['tenant_id']=='t' and items[0]['user_id']=='alice'
        assert items[0]['operation']['operation_id']==alice['operation_id']
        assert items[0]['operation']['state']=='waiting' and items[0]['operation']['attempt_count']==0
        raw=response.text
        for forbidden in ('Pregunta de Bob privada','Pregunta de otro cliente','private_control',
                          'canonical_input','capability','synthetic-system-secret','screen_context'):
            assert forbidden not in raw
        await asyncio.sleep(.03)
        assert api[2].claims==[] and messages(api[1])==[]
        own_bob=await client.get('/assistant/requests',headers=headers('bob'))
        assert own_bob.json()['items'][0]['operation']['state']=='cancelled'
        assert own_bob.json()['items'][0]['question']=='Pregunta de Bob privada'
        other_response=await client.get('/assistant/requests',headers={**headers(),'X-Tenant-Id':'other'})
        assert {item['operation']['operation_id'] for item in other_response.json()['items']}=={other['operation_id']}
    run(scenario,api)

def test_requests_projection_is_read_only_and_never_renews_wait_budget(api):
    row=reserve(api,scope(),'Pregunta conservada')
    api[3].advance(5)
    observed=[]
    def inspect(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','CREATE','ALTER','DROP'):
            observed.append(statement)
    event.listen(api[1].engine,'before_cursor_execute',inspect)
    async def scenario(client):
        first=await client.get('/assistant/requests',headers=headers())
        assert first.status_code==200,first.text
        item=first.json()['items'][0]
        assert item['operation']['wait_info']['local_remaining_ms']==115000
        assert item['operation']['attempt_count']==0
        second=await client.get('/assistant/requests',headers=headers())
        assert second.json()==first.json()
        assert api[2].claims==[] and observed==[] and messages(api[1])==[]
        retained=ChatRepository(api[1],api[3]).get(scope(),row['operation_id'])
        assert retained['revision']==row['revision'] and retained['private_control']==row['private_control']
    try: run(scenario,api)
    finally: event.remove(api[1].engine,'before_cursor_execute',inspect)

def test_requests_join_checks_conversation_owner_not_just_operation_columns(api):
    row=reserve(api,scope('bob'),'Must not become Alice data')
    with api[1].engine.begin() as connection:
        connection.execute(text("UPDATE chat_operations SET user_id='alice' WHERE operation_id=:id"),{'id':row['operation_id']})
    async def scenario(client):
        response=await client.get('/assistant/requests',headers=headers())
        assert response.status_code==200,response.text
        assert response.json()=={'items':[]}
        assert 'Must not become Alice data' not in response.text and api[2].claims==[]
    run(scenario,api)

def test_requests_require_authenticated_membership_and_exactly_one_tenant_selector(api):
    async def scenario(client):
        for options,expected in [({'X-Test-User':'bob','X-Tenant-Id':'other'},403),
                                 ({'X-Test-User':'alice'},400),
                                 ({'X-Test-User':'alice','X-Tenant-Id':'t,other'},400)]:
            response=await client.get('/assistant/requests',headers=options)
            assert response.status_code==expected,response.text
        assert api[2].claims==[] and messages(api[1])==[]
    run(scenario,api)

def test_requests_without_bearer_are401_even_when_empty(api):
    saved=api[0].dependency_overrides.pop(get_current_user)
    async def scenario(client):
        response=await client.get('/assistant/requests',headers={'X-Tenant-Id':'t'})
        assert response.status_code==401,response.text
        assert api[2].claims==[] and messages(api[1])==[]
    try: run(scenario,api)
    finally: api[0].dependency_overrides[get_current_user]=saved
