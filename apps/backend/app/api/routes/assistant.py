import math
from datetime import datetime, timezone
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
from app.services.anomaly_explanations import ExplanationUnavailable, explain_episode
from app.services.citations import InvalidCitation, resolve_citations, validate_context
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES, ProviderError
from app.services.azure_cost_questions import AzureCostQuestionService
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

    try:
        database.assert_conversation_idle(conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"])
    except ChatError as exc:
        raise HTTPException(exc.status, exc.code) from None

    if payload.anomaly_query is not None:
        # Orden de la decisión 8 del diseño: leer, explicar y SOLO ENTONCES guardar. Si el episodio no existe
        # (404) o no se puede explicar (409) no queda ni el mensaje del usuario: un historial con preguntas
        # sin respuesta sería ruido y, en el 404, delataría un identificador de otro cliente.
        # El cliente sale SIEMPRE de la sesión (`tenant_id`), nunca del cuerpo: el identificador del episodio
        # es una selección, no una autorización, y el episodio ajeno es indistinguible del inexistente.
        try:
            snapshot = database.fetch_anomaly_episode_snapshot(tenant_id, payload.anomaly_query.episode_id)
        except ArithmeticError:
            # Las columnas de operandos del episodio son `DECIMAL` sin precisión: la base admite NaN, infinitos
            # y valores enormes que el redondeo de la lectura (`money()`/`severity()`) no sabe representar y que
            # lanza `decimal.InvalidOperation` antes de que el explicador vea los datos. Una fila ilegible es
            # «no se puede explicar» (409), igual que los datos incoherentes que rechaza el explicador, y no un
            # error del servidor. Se captura SOLO la lectura (no toda la rama) para no ocultar otros fallos, y
            # `from None` evita propagar valores del cliente en la cadena de excepciones.
            raise HTTPException(status_code=409, detail={"code": "anomaly_explanation_unavailable"}) from None
        if snapshot is None:
            raise HTTPException(status_code=404, detail={"code": "anomaly_episode_not_found"})
        try:
            explanation = explain_episode(snapshot, tenant_id=tenant_id, explained_at=datetime.now(timezone.utc))
        except ExplanationUnavailable:
            raise HTTPException(status_code=409, detail={"code": "anomaly_explanation_unavailable"}) from None
        # Misma forma de guardado que la rama de propiedad. No se registra (`logger`) nada del episodio ni de
        # la explicación: el nombre del servicio y el motivo de cierre son datos del cliente.
        user_message = database.prepare_message(
            conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"],
            requester_id=current_user["id"], role="user", content=payload.content,
            metadata={"anomaly_query": {"episode_id": payload.anomaly_query.episode_id}},
        )
        assistant_message = database.prepare_message(
            conversation_id=conversation_id, tenant_id=tenant_id, user_id=None,
            requester_id=current_user["id"], role="assistant", content=explanation["content"],
            metadata={"citations": [], "anomaly_evidence": explanation["anomaly_evidence"],
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

    if payload.cost_query is not None:
        try:
            output = AzureCostQuestionService().answer(database, tenant_id, payload.cost_query)
        except AmbiguousCostSource:
            raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
        user_message = database.prepare_message(
            conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"],
            requester_id=current_user["id"], role="user", content=payload.content,
            metadata={"cost_query": output["cost_evidence"]["selection"]},
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

    user_message = database.prepare_message(
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
    try:
        validate_context(retrieved_chunks, tenant_id)
    except InvalidCitation:
        raise HTTPException(status_code=502, detail="Invalid response evidence.") from None
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
    try:
        assistant_output = assistant_service.answer(payload.content, retrieved_chunks)
        source_citations = resolve_citations(assistant_output["citations"], retrieved_chunks, tenant_id)
    except InvalidCitation:
        raise HTTPException(status_code=502, detail="Invalid response evidence.") from None

    assistant_message = database.prepare_message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=None,
        requester_id=current_user["id"],
        role="assistant",
        content=assistant_output["content"],
        metadata={"citations": assistant_output["citations"], "source_citations": source_citations,
            "generation": {"question_message_id": user_message["id"]}},
    )

    try:
        user_message, assistant_message = database.append_pair(question=user_message, assistant=assistant_message)
    except ChatError as exc:
        raise HTTPException(exc.status, exc.code) from None

    assistant_queries_total.inc()

    reply = AssistantReply(
        conversation=ConversationRecord(**conversation),
        user_message=user_message,
        assistant_message=assistant_message,
        retrieved_context=retrieved_chunks,
    )
    return chat_history.http_response(reply.model_dump(mode='python'), status_code=201)


def _retrieval_failed(category: str, trace: dict, started: float) -> None:
    category = category if category in FAILURE_CATEGORIES else "transport"
    retrieval_failures_total.labels(category=category).inc()
    logger.warning(
        "retrieval_failed", **trace, category=category,
        duration_ms=round((perf_counter() - started) * 1000, 2),
    )
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=RETRIEVAL_UNAVAILABLE) from None
