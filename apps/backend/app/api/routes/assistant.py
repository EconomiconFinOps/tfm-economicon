import math
from time import perf_counter

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    get_active_tenant,
    get_assistant_service,
    get_current_user,
    get_embedding_provider,
    get_vector_store,
    get_database,
)
from app.core.config import get_settings
from app.db.chat_repository import ChatError, ChatRepository
from app.db import chat_history
from app.core.metrics import assistant_queries_total, retrieval_empty_total, retrieval_failures_total
from app.services.citations import InvalidCitation, resolve_citations, validate_context
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES, ProviderError
from app.schemas.billing import AmbiguousCostSource
from app.services.ownership_questions import OwnershipQuestionService, OwnershipResultTooLarge
from app.schemas.assistant import (
    AssistantReply,
    ConversationCollection,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationRecord,
    ConversationRenameRequest,
    MessageCreateRequest,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])
logger = structlog.get_logger("assistant")

RETRIEVAL_UNAVAILABLE = "The assistant cannot retrieve context right now. Try again later."
FAILURE_CATEGORIES = frozenset(PROVIDER_ERROR_CATEGORIES) | {"vector_store"}


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


@router.patch("/conversations/{conversation_id}", response_model=ConversationRecord)
def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> ConversationRecord:
    conversation = database.rename_conversation(conversation_id, tenant_id, current_user["id"], payload.title)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return ConversationRecord(**conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> Response:
    try:
        ChatRepository(database).delete_conversation({"conversation_id": conversation_id,
            "tenant_id": tenant_id, "user_id": current_user["id"]})
    except ChatError as exc:
        raise HTTPException(exc.status, exc.code) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    try:
        detail = ConversationDetail(
            conversation=ConversationRecord(**conversation),
            messages=database.fetch_messages(conversation_id, tenant_id, current_user["id"]),
        )
        return chat_history.http_response(detail.model_dump(mode='python'))
    except ChatError as exc:
        raise HTTPException(exc.status, exc.code) from None


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

    if payload.ownership_query is None:
        raise HTTPException(status_code=410, detail="legacy_chat_retired")

    try:
        database.assert_conversation_idle(conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"])
    except ChatError as exc:
        raise HTTPException(exc.status, exc.code) from None

    if payload.ownership_query is not None:
        try:
            output = OwnershipQuestionService().answer(database, tenant_id, payload.ownership_query)
        except AmbiguousCostSource:
            raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
        except OwnershipResultTooLarge:
            raise HTTPException(status_code=422, detail={"code": "ownership_result_too_large"}) from None
        user_message = database.prepare_message(
            conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"],
            requester_id=current_user["id"], role="user", content=payload.content,
            metadata={"ownership_query": output["cost_evidence"]["selection"]},
        )
        assistant_message = database.prepare_message(
            conversation_id=conversation_id, tenant_id=tenant_id, user_id=None,
            requester_id=current_user["id"], role="assistant", content=output["content"],
            metadata={"citations": [], "cost_evidence": output["cost_evidence"],
                "generation": {"question_message_id": user_message["id"]}},
        )
        try:
            user_message, assistant_message = database.append_pair(question=user_message, assistant=assistant_message)
        except ChatError as exc:
            raise HTTPException(exc.status, exc.code) from None
        assistant_queries_total.inc()
        reply = AssistantReply(
            conversation=ConversationRecord(**conversation), user_message=user_message,
            assistant_message=assistant_message, retrieved_context=[],
        )
        return chat_history.http_response(reply.model_dump(mode='python'), status_code=201)
