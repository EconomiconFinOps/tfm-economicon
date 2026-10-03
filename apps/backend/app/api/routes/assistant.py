from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_active_tenant,
    get_assistant_service,
    get_current_user,
    get_embedding_provider,
    get_vector_store,
    get_database,
)
from app.schemas.billing import AmbiguousCostSource
from app.services.azure_cost_questions import AzureCostQuestionService
from app.core.metrics import assistant_queries_total
from app.schemas.assistant import (
    AssistantReply,
    ConversationCollection,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationRecord,
    MessageCreateRequest,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/conversations", response_model=ConversationCollection)
def list_conversations(
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> ConversationCollection:
    return ConversationCollection(
        items=[
            ConversationRecord(**item)
            for item in database.fetch_conversations(tenant_id, current_user["id"])
        ]
    )


@router.post(
    "/conversations",
    response_model=ConversationRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> ConversationRecord:
    return ConversationRecord(
        **database.create_conversation(tenant_id, current_user["id"], payload.title)
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> ConversationDetail:
    conversation = database.fetch_conversation(conversation_id, tenant_id, current_user["id"])
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return ConversationDetail(
        conversation=ConversationRecord(**conversation),
        messages=database.fetch_messages(conversation_id, tenant_id, current_user["id"]),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AssistantReply,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider),
    assistant_service=Depends(get_assistant_service),
) -> AssistantReply:
    conversation = database.fetch_conversation(conversation_id, tenant_id, current_user["id"])
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if payload.cost_query is not None:
        try:
            assistant_output = AzureCostQuestionService().answer(database, tenant_id, payload.cost_query)
        except AmbiguousCostSource:
            raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
        retrieved_chunks = []
    else:
        query_embedding = embedding_provider.embed(payload.content)
        retrieved_chunks = vector_store.search_chunks(tenant_id, query_embedding)
        assistant_output = assistant_service.answer(payload.content, retrieved_chunks)

    user_message = database.append_message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=current_user["id"],
        requester_id=current_user["id"],
        role="user",
        content=payload.content,
        metadata={"cost_query": assistant_output["cost_evidence"]["selection"]} if payload.cost_query else {},
    )
    assistant_message = database.append_message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=None,
        requester_id=current_user["id"],
        role="assistant",
        content=assistant_output["content"],
        metadata={key: value for key, value in assistant_output.items() if key != "content"},
    )

    assistant_queries_total.inc()

    return AssistantReply(
        conversation=ConversationRecord(**conversation),
        user_message=user_message,
        assistant_message=assistant_message,
        retrieved_context=retrieved_chunks,
    )
