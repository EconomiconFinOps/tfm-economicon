"""Deterministic proposals; no persistence, provider calls or cloud mutations."""
from decimal import Decimal
from hashlib import sha256
import json

from app.schemas.billing import BillingGroup, BillingSummary
from app.schemas.recommendations import (
    NotEvaluatedAction,
    ObservedCost,
    Recommendation,
    RecommendationEvidence,
    RecommendationPeriod,
    RecommendationQuery,
    RecommendationReport,
    RecommendationScope,
    RuleId,
)


MAX_CANDIDATES = 50


def _identifier(prefix: str, payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{prefix}:sha256:{sha256(serialized.encode('utf-8')).hexdigest()}"


def _group_key(group: BillingGroup) -> tuple[str, bool, str]:
    return group.currency, group.value is not None, group.value or ""


def _candidate(
    group: BillingGroup, rule_id: RuleId, query: RecommendationQuery,
    tenant_id: str, source_data: dict,
) -> tuple[Recommendation, RecommendationEvidence]:
    scope = RecommendationScope(value=group.value)
    observed = ObservedCost(amount=group.cost, currency=group.currency, record_count=group.record_count)
    identity = {
        "tenant_id": tenant_id, "query": query.model_dump(mode="json"),
        "rule_id": rule_id, "rule_version": 1, "scope": scope.model_dump(),
        "currency": group.currency,
    }
    evidence = RecommendationEvidence(
        id=_identifier("cost-query", {**identity, "source_data": source_data}),
        query=query, rule_id=rule_id, scope=scope, observed_cost=observed,
    )
    if rule_id == "missing_project":
        category, qualification, confidence = "tagging", "supported", "high"
        action = "Revisar con el equipo de negocio y proponer un proyecto o aplicacion para los registros sin proyecto."
        rationale = (
            "Hay registros de coste sin proyecto ni tag project utilizable. Asignar contexto de negocio "
            "permite revisar la imputacion; el coste observado no representa ahorro."
        )
    else:
        category, qualification, confidence = "investigation", "investigation_candidate", "low"
        action = "Revisar el consumo del proyecto con su equipo y reunir datos de utilizacion y requisitos de negocio."
        rationale = (
            "Es el mayor coste neto positivo entre los proyectos identificados de esta moneda y periodo. "
            "La regla selecciona un punto de investigacion; no demuestra desperdicio ni justifica reducir recursos."
        )
    recommendation = Recommendation(
        id=_identifier("recommendation", identity), rule_id=rule_id,
        category=category, qualification=qualification, action=action, rationale=rationale,
        scope=scope, observed_cost=observed, confidence=confidence, risk="low", difficulty="unknown",
        evidence_ids=[evidence.id],
    )
    return recommendation, evidence


def generate_recommendations(summary: BillingSummary, *, tenant_id: str) -> RecommendationReport:
    """Use one tenant-authorized project summary, preserving its exact net costs.

    IDs are content-derived references, not persisted records or database snapshots.
    The evidence ID covers every project group, so changes to the comparison set
    invalidate evidence for the largest-project rule as well as changed amounts.
    """
    if not tenant_id or not tenant_id.strip():
        raise ValueError("An authorized tenant is required")
    if summary.group_by != "project" or summary.tag_key is not None:
        raise ValueError("Recommendations require a project billing summary")
    period = RecommendationPeriod(**summary.period.model_dump())
    query = RecommendationQuery(period=period)
    groups = sorted(summary.groups, key=_group_key)
    keys = [(group.currency, group.value) for group in groups]
    if len(keys) != len(set(keys)):
        raise ValueError("Project groups must be unique within each currency")
    if any(group.subscription_id is not None for group in groups):
        raise ValueError("Project groups aggregate across authorized tenant subscriptions")
    if any(group.record_count <= 0 or (group.value is not None and not group.value.strip()) for group in groups):
        raise ValueError("Project groups require records and canonical project values")
    if summary.data_status == "empty" and groups:
        raise ValueError("Empty billing data cannot contain project groups")
    source_data = {
        "groups": [group.model_dump() for group in groups],
        "data_status": summary.data_status,
        "missing_dimension_count": summary.missing_dimension_count,
        "excluded_undated_count": summary.excluded_undated_count,
    }

    selections: list[tuple[BillingGroup, RuleId]] = []
    largest: dict[str, BillingGroup] = {}
    for group in groups:
        if group.value is None:
            selections.append((group, "missing_project"))
        elif Decimal(group.cost) > 0:
            current = largest.get(group.currency)
            # Iteration is lexicographic by project: retain the first exact tie.
            if current is None or Decimal(group.cost) > Decimal(current.cost):
                largest[group.currency] = group
    selections.extend((group, "largest_project_cost") for group in largest.values())
    # This presentation order does not compare currencies or assign savings priority.
    selections.sort(key=lambda item: (item[0].currency, item[1], item[0].value or ""))
    total_candidates = len(selections)
    results = [_candidate(group, rule, query, tenant_id, source_data)
               for group, rule in selections[:MAX_CANDIDATES]]

    limitations = [
        "Solo se analizan costes ingeridos del entorno simulado; no se acredita ahorro potencial ni realizado.",
        "Los importes son costes netos: los creditos y ajustes pueden compensar cargos positivos.",
        "No hay telemetria de utilizacion, tarifas alternativas ni una fuente de ownership o requisitos de negocio.",
        "La dificultad es desconocida; el riesgo bajo se refiere a la revision propuesta, no a modificar recursos.",
        "La consulta agrega por proyecto dentro del tenant; no identifica recursos ni atribuye una suscripcion al candidato.",
        "Los identificadores no implican persistencia, historial, una instantanea conservada ni un workflow de aprobacion.",
        "No se ejecutan cambios cloud. Cada propuesta requiere revision y aprobacion humana antes de cualquier accion.",
    ]
    if summary.missing_dimension_count:
        limitations.append("Hay registros del periodo sin proyecto; la cobertura de contexto de negocio es parcial.")
    if summary.excluded_undated_count:
        limitations.append(
            "Se excluyen registros sin fecha de las ingestas completadas del tenant; "
            "no puede atribuirse su coste al periodo solicitado."
        )
    if not groups:
        limitations.append("No hay grupos de coste fechados en el periodo para generar recomendaciones.")
    if total_candidates > MAX_CANDIDATES:
        limitations.append("Se muestran los primeros 50 candidatos en orden lexicografico; no es un ranking de ahorro.")

    return RecommendationReport(
        period=period, data_status=summary.data_status,
        status="available" if groups else "insufficient_data",
        recommendations=[item[0] for item in results], evidence=[item[1] for item in results],
        total_candidates=total_candidates, truncated=total_candidates > MAX_CANDIDATES,
        missing_dimension_count=summary.missing_dimension_count,
        excluded_undated_count=summary.excluded_undated_count,
        assumptions=[
            "El intervalo de consulta es UTC, incluye start_date y excluye end_date.",
            "Proyecto usa la columna normalizada project y, si falta, el tag project; blancos se consideran ausentes.",
            "Los valores de proyecto conservan mayusculas y minusculas; un valor literal Unknown no se considera ausente.",
            "Cada moneda se evalua por separado; no se convierte ni se compara con otras monedas.",
            "Un empate de coste positivo se resuelve por orden lexicografico del nombre de proyecto.",
        ],
        limitations=limitations,
        not_evaluated=[
            NotEvaluatedAction(action="rightsizing", missing_inputs=["CPU, memoria, I/O, picos y SLA"]),
            NotEvaluatedAction(action="scheduling", missing_inputs=["Horarios de uso y restricciones operativas"]),
            NotEvaluatedAction(action="orphan_cleanup", missing_inputs=["Inventario, dependencias y ownership verificados"]),
            NotEvaluatedAction(action="rate_optimization", missing_inputs=["Tarifas y recomendaciones de compromisos verificadas"]),
            NotEvaluatedAction(action="savings_impact", missing_inputs=["Baseline comparable y supuestos de impacto versionados"]),
        ],
    )
