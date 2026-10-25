from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import get_database, get_queue, get_vector_store
from app.schemas.health import HealthResponse


UTC = timezone.utc
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    database=Depends(get_database),
    queue=Depends(get_queue),
    vector_store=Depends(get_vector_store),
) -> HealthResponse:
    database_status = "ok" if database.ping() else "failed"
    rabbitmq_status = "ok" if queue.ping() else "failed"
    vector_store_status = "ok" if vector_store.ping() else "failed"
    status = (
        "ok"
        if database_status == "ok" and rabbitmq_status == "ok" and vector_store_status == "ok"
        else "degraded"
    )
    return HealthResponse(
        status=status,
        services={
            "database": database_status,
            "rabbitmq": rabbitmq_status,
            "vector_store": vector_store_status,
        },
        checked_at=datetime.now(UTC),
    )

# Operational diagnostics are separately authenticated; legacy /health above
# retains its public dependency/timestamp contract.
import hashlib
from functools import partial
from urllib.parse import urlsplit, urlunsplit

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.api.dependencies import get_active_tenant
from app.core.config import get_settings
from app.schemas.health import ProviderCheckRequest, SystemHealthResponse
from app.services.system_health import IDS, aggregate_status, run_probes, unavailable_summary
from app.services.system_health_runtime import database_probe, http_probe, litellm_liveliness_probe, provider_service, queue_probe, vector_probe


def _provider(request, settings):
    return getattr(request.app.state, "health_provider_check", None) or provider_service(settings)


@router.get("/health/status", response_model=SystemHealthResponse)
def operational_health(
    request: Request, response: Response, tenant=Depends(get_active_tenant),
    database=Depends(get_database), queue=Depends(get_queue), vector_store=Depends(get_vector_store),
):
    settings = get_settings()
    checked = datetime.now(UTC)
    parsed = urlsplit(settings.litellm_base_url)
    gateway_url = urlunsplit((parsed.scheme, parsed.netloc, "/health/liveliness", "", ""))
    probes = {
        "database": partial(database_probe, database, tenant, checked),
        "rabbitmq": partial(queue_probe, queue, settings),
        "vector_store": partial(vector_probe, vector_store),
        "processor": partial(http_probe, settings.processor_health_base_url),
        "azure_cost_api": partial(http_probe, settings.azure_cost_health_base_url),
        "litellm": partial(litellm_liveliness_probe, gateway_url if settings.health_gateway_probe_enabled else None),
    }
    results = run_probes(probes, probe_seconds=settings.health_probe_timeout_seconds, overall_seconds=18)
    jobs, ingestion = unavailable_summary(), unavailable_summary(ingestion=True)
    components = [{"id": "backend", "status": "ok", "reason_code": "none", "source_kind": "live", "checked_at": checked, "latency_ms": 0}]
    for item in results:
        if item["id"] == "database":
            jobs = item.pop("jobs", jobs)
            ingestion = item.pop("ingestion", ingestion)
        item.setdefault("source_kind", "simulated" if item["id"] == "azure_cost_api" else "live")
        item.setdefault("checked_at", checked)
        item.setdefault("latency_ms", None)
        if item["id"] == "processor":
            item["worker_status"] = "unknown"
        components.append(item)
    components.append(_provider(request, settings).observation())
    components.sort(key=lambda component: IDS.index(component["id"]))
    state = aggregate_status(components)
    activity_attention = any(item.get("failed_last_24h") for item in (jobs, ingestion)) or bool((jobs.get("counts") or {}).get("publish_unknown"))
    if state == "ok" and (activity_attention or any(item["data_status"] == "unavailable" for item in (jobs, ingestion))):
        state = "degraded"
    response.headers["Cache-Control"] = "no-store"
    from datetime import timedelta
    return {"tenant_id": tenant, "status": state, "checked_at": checked,
            "window": {"start": checked - timedelta(hours=24), "end": checked},
            "components": components, "jobs": jobs, "ingestion": ingestion}


@router.post("/health/provider-check")
def provider_check(payload: ProviderCheckRequest, request: Request, tenant=Depends(get_active_tenant)):
    # Scope-bound idempotency uses a one-way session fingerprint, never a token
    # or user/tenant value in the fixed inference payload or diagnostic logs.
    session = hashlib.sha256(request.headers["authorization"].encode("utf-8")).hexdigest()
    result = _provider(request, get_settings()).check(session_id=session, tenant_id=tenant, idempotency_key=payload.idempotency_key)
    result = dict(result)
    status_code = result.pop("http_status")
    headers = {"Cache-Control": "no-store"}
    if "retry_after" in result:
        headers["Retry-After"] = str(result["retry_after"])
    return JSONResponse(status_code=status_code, content=jsonable_encoder(result), headers=headers)
