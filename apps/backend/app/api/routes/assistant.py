import math
from time import perf_counter

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_active_tenant,
    get_assistant_service,
    get_current_user,
    get_embedding_provider,
    get_vector_store,
    get_database,
)
from app.core.config import get_settings
from app.core.metrics import assistant_queries_total, retrieval_empty_total, retrieval_failures_total
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES, ProviderError
from app.schemas.assistant import (
    AssistantReply,
    ConversationCollection,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationRecord,
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

    user_message = database.append_message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=current_user["id"],
        requester_id=current_user["id"],
        role="user",
        content=payload.content,
    )
    settings = get_settings()
    provider_name = embedding_provider.name
    alias = getattr(embedding_provider, "alias", provider_name)
    trace = {"tenant_id": tenant_id, "user_message_id": user_message["id"], "provider": provider_name, "alias": alias}
    started = perf_counter()
    try:
        query_embedding = embedding_provider.embed(payload.content)
        if (
            len(query_embedding) != embedding_provider.dimension
            or not all(math.isfinite(value) for value in query_embedding)
            or not any(abs(value) >= 5e-7 for value in query_embedding)
        ):
            raise ProviderError("invalid_response")
    except ProviderError as exc:
        _retrieval_failed(exc.category, trace, started)
    except Exception:
        _retrieval_failed("transport", trace, started)
    try:
        retrieved_chunks = vector_store.search_chunks(
            tenant_id, query_embedding, top_k=settings.retrieval_top_k,
            max_distance=settings.retrieval_max_distance, provider=embedding_provider.name,
        )
    except Exception:
        _retrieval_failed("vector_store", trace, started)
    logger.info(
        "retrieval", **trace,
        chunk_ids=[item["chunk_id"] for item in retrieved_chunks],
        document_ids=[item.get("document_id") for item in retrieved_chunks],
        distances=[round(item["distance"], 4) for item in retrieved_chunks],
        top_k=settings.retrieval_top_k, max_distance=settings.retrieval_max_distance,
        results=len(retrieved_chunks), duration_ms=round((perf_counter() - started) * 1000, 2),
    )
    if not retrieved_chunks:
        retrieval_empty_total.inc()
    assistant_output = assistant_service.answer(payload.content, retrieved_chunks)
    assistant_message = database.append_message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=None,
        requester_id=current_user["id"],
        role="assistant",
        content=assistant_output["content"],
        metadata={"citations": assistant_output["citations"]},
    )

    assistant_queries_total.inc()

    return AssistantReply(
        conversation=ConversationRecord(**conversation),
        user_message=user_message,
        assistant_message=assistant_message,
        retrieved_context=retrieved_chunks,
    )


def _retrieval_failed(category: str, trace: dict, started: float) -> None:
    category = category if category in FAILURE_CATEGORIES else "transport"
    retrieval_failures_total.labels(category=category).inc()
    logger.warning(
        "retrieval_failed", **trace, category=category,
        duration_ms=round((perf_counter() - started) * 1000, 2),
    )
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=RETRIEVAL_UNAVAILABLE) from None
