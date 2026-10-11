"""Owner-scoped operation API, with history separate from pending requests."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.dependencies import get_active_tenant,get_current_user,get_database
from app.db.chat_repository import ChatError
from app.db import chat_history
from app.schemas.chat import GenerationRequest
from app.schemas.chat_screen import read_generation
from app.services.chat_operations import service


router=APIRouter(prefix='/assistant',tags=['assistant'])


def scope(conversation_id,user,tenant):
    return {'conversation_id':conversation_id,'user_id':user['id'],'tenant_id':tenant}


def failure(error):
    raise HTTPException(status_code=error.status,detail=error.code) from None


@router.get('/requests')
async def requests(request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        return await service(request.app).requests({'tenant_id':tenant,'user_id':user['id']})
    except ChatError as error: failure(error)


@router.post('/conversations/{conversation_id}/generations')
async def generate(conversation_id:str,request:Request,
                   user=Depends(get_current_user),tenant=Depends(get_active_tenant),database=Depends(get_database)):
    owned=scope(conversation_id,user,tenant)
    if await __import__('asyncio').to_thread(database.fetch_conversation,conversation_id,tenant,user['id']) is None:
        raise HTTPException(404,'not_found')
    payload=await read_generation(request,GenerationRequest)
    screen=payload.screen_context
    if screen.get('identity')!={'tenant_id':tenant,'user_id':user['id']}:
        raise HTTPException(422,'screen_identity_invalid')
    try:
        runtime=service(request.app,active=True)
        frozen=payload.model_dump(mode='json')
        if frozen['retry_of_operation_id'] is None:
            del frozen['retry_of_operation_id']
        row,created=await runtime.open(owned,frozen)
        if not created: return JSONResponse(runtime.public(row,'existing'))
        return StreamingResponse(runtime.events(owned,row['operation_id'],initial=True),media_type='text/event-stream',
            headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    except ChatError as error: failure(error)


@router.get('/conversations/{conversation_id}/generations/{operation_id}')
async def status(conversation_id:str,operation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        runtime=service(request.app)
        return runtime.public(await runtime.get(scope(conversation_id,user,tenant),operation_id))
    except ChatError as error: failure(error)


@router.get('/conversations/{conversation_id}/generations/{operation_id}/events')
async def events(conversation_id:str,operation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        runtime=service(request.app)
        owned=scope(conversation_id,user,tenant)
        row=await runtime.get(owned,operation_id)
        return StreamingResponse(runtime.events(owned,operation_id),media_type='text/event-stream',
            status_code=202 if row['state'] not in ('completed','failed','cancelled') and operation_id not in runtime.buffers else 200,
            headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    except ChatError as error: failure(error)


@router.post('/conversations/{conversation_id}/generations/{operation_id}/stop')
async def stop(conversation_id:str,operation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        runtime=service(request.app)
        return runtime.public(await runtime.stop(scope(conversation_id,user,tenant),operation_id))
    except ChatError as error: failure(error)


@router.post('/conversations/{conversation_id}/generations/{operation_id}/resume')
async def resume(conversation_id:str,operation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        runtime=service(request.app)
        runtime.start()
        return runtime.public(await runtime.resume(scope(conversation_id,user,tenant),operation_id))
    except ChatError as error: failure(error)


@router.get('/conversations/{conversation_id}/generations/{operation_id}/{resource}')
async def resource(conversation_id:str,operation_id:str,resource:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    if resource not in ['result','context','evidence']: raise HTTPException(404,'not_found')
    try:
        runtime=service(request.app)
        owned=scope(conversation_id,user,tenant)
        row=await runtime.get(owned,operation_id)
        if resource=='result':
            return chat_history.http_response(await runtime._db(runtime.repository.result,owned,row))
        if resource=='context':
            context=row['canonical_input']['context']
            return {'screen_context':row['canonical_input']['request']['screen_context'],
                    'manifest':context.get('manifest',{}),'prompt_version':context['prompt_version']}
        return {'items':row['canonical_input']['context'].get('authorized_evidence',[])}
    except ChatError as error: failure(error)


@router.get('/conversations/{conversation_id}/summary')
async def summary(conversation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    # Cold metadata read: no operation scheduler, inference or derived writes.
    from app.services.chat_context import ChatContext
    try:
        builder=ChatContext(request.app,getattr(request.app.state,'chat_resources',None))
        owned=scope(conversation_id,user,tenant)
        _,_,_,value=await __import__('asyncio').to_thread(builder.memory,owned)
        from app.db.chat_repository import ChatRepository
        repository=ChatRepository(request.app.state.database)
        value['queue']=await __import__('asyncio').to_thread(repository.compactions.public,owned)
        return value
    except ChatError as error:failure(error)


@router.post('/conversations/{conversation_id}/summary/retry')
async def retry_summary(conversation_id:str,request:Request,user=Depends(get_current_user),tenant=Depends(get_active_tenant)):
    try:
        runtime=service(request.app,active=True)
        owned=scope(conversation_id,user,tenant)
        await runtime.summary.retry(owned)
        return await runtime._db(runtime.repository.compactions.public,owned)
    except ChatError as error:failure(error)
