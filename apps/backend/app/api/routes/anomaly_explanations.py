"""Structured assistant capability, independent of free-text routing JUP-035/036."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_active_tenant, get_current_user, get_database
from app.core.metrics import assistant_queries_total
from app.schemas.anomaly_explanations import ExplainAnomalyRequest
from app.schemas.assistant import AssistantReply
from app.schemas.billing import AmbiguousCostSource
from app.services.anomaly_explanations import (
    AnomalyNotFound, BillingAnomalyProvider, DetectorUnavailable, EvidenceChanged,
    InvalidDetectionEvidence, InvalidSelection, explain_anomaly,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])


def get_anomaly_provider(database=Depends(get_database)):
    return BillingAnomalyProvider(database)


@router.post("/conversations/{conversation_id}/anomaly-explanations",
             response_model=AssistantReply, status_code=status.HTTP_201_CREATED)
def explain_detected_anomaly(
    conversation_id: str,
    payload: ExplainAnomalyRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    provider=Depends(get_anomaly_provider),
) -> AssistantReply:
    conversation = database.fetch_conversation(conversation_id, tenant_id, current_user["id"])
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    try:
        result = provider.evaluate(tenant_id, payload.definition.model_dump())
        explanation = explain_anomaly(result, payload)
    except InvalidSelection:
        raise HTTPException(status_code=422, detail="Invalid anomaly selection.") from None
    except AnomalyNotFound:
        raise HTTPException(status_code=404, detail="Anomaly not found in this evaluation.") from None
    except EvidenceChanged:
        raise HTTPException(status_code=409, detail="Anomaly evidence changed. Refresh the evaluation.") from None
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    except InvalidDetectionEvidence:
        raise HTTPException(status_code=502, detail="Invalid anomaly evidence.") from None
    except Exception:
        # No upstream exception or SQL content reaches the client or persisted chat.
        raise HTTPException(status_code=503, detail="Anomaly detection is unavailable.") from None

    metadata = {"capability": "anomaly_explanation", "anomaly_explanation": explanation.model_dump(mode="json")}
    user_message = database.append_message(
        conversation_id=conversation_id, tenant_id=tenant_id, user_id=current_user["id"],
        requester_id=current_user["id"], role="user", content=f"Explica la anomalía {payload.anomaly_id}.",
        metadata={"anomaly_id": payload.anomaly_id, "evidence_id": payload.evidence_id},
    )
    assistant_message = database.append_message(
        conversation_id=conversation_id, tenant_id=tenant_id, user_id=None,
        requester_id=current_user["id"], role="assistant", content=explanation.content, metadata=metadata,
    )
    assistant_queries_total.inc()
    return AssistantReply(conversation=conversation, user_message=user_message,
                          assistant_message=assistant_message, retrieved_context=[])
