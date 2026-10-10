"""Deterministic executive summary of potential savings, without a model call."""
from collections import Counter
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import Protocol

from pydantic import ValidationError

from app.schemas.savings import SavingsSelection, SavingsSnapshot


class SavingsProvider(Protocol):
    """Adapter supplied by JUP-033/034; filters the complete snapshot server-side."""

    def load_snapshot(self, tenant_id: str, selection: SavingsSelection) -> dict: ...


class InvalidSavingsEvidence(ValueError):
    def __init__(self):
        super().__init__("Invalid savings evidence.")


def summarize_savings(raw_snapshot: dict, tenant_id: str, selection: SavingsSelection) -> dict:
    try:
        snapshot = SavingsSnapshot.model_validate(raw_snapshot)
    except (ValidationError, TypeError, ValueError):
        raise InvalidSavingsEvidence() from None
    if (
        snapshot.tenant_id != tenant_id
        or snapshot.start_date != selection.start_date
        or snapshot.end_date != selection.end_date
        or snapshot.subscription_id != selection.subscription_id
    ):
        raise InvalidSavingsEvidence()
    seen_ids = set()
    evidence = {}
    for item in snapshot.opportunities:
        if (
            item.tenant_id != tenant_id
            or (selection.subscription_id is not None and item.subscription_id != selection.subscription_id)
            or item.recommendation_id in seen_ids
        ):
            raise InvalidSavingsEvidence()
        seen_ids.add(item.recommendation_id)
        for source in item.sources:
            value = source.model_dump()
            if source.evidence_id in evidence and evidence[source.evidence_id] != value:
                raise InvalidSavingsEvidence()
            evidence[source.evidence_id] = value

    active = [item for item in snapshot.opportunities if item.state in {"proposed", "accepted"}]
    groups = []
    # Never rank or convert across currencies. top_n only limits presentation.
    for currency in sorted({item.currency for item in active}):
        items = [item for item in active if item.currency == currency]
        quantified = [item for item in items if item.monthly_estimate is not None]
        basis = [item.independent_cost_basis for item in quantified]
        additive = bool(quantified) and None not in basis and len(set(basis)) == len(basis)
        with localcontext() as context:
            context.prec = 40  # 200 bounded 26-digit amounts plus cents.
            monthly = format(sum((Decimal(item.monthly_estimate) for item in quantified), Decimal(0)), ".2f") if additive else None
            annual = format(sum((Decimal(item.annual_estimate) for item in quantified), Decimal(0)), ".2f") if additive else None
        total_status = (
            "unavailable" if not quantified else "non_additive" if not additive
            else "partial" if len(quantified) < len(items) or snapshot.data_status == "partial"
            else "estimated"
        )
        ranked = sorted(items, key=lambda item: (
            item.monthly_estimate is None,
            -Decimal(item.monthly_estimate or "0.00"), item.recommendation_id,
        ))
        groups.append(dict(
            currency=currency, opportunity_count=len(items), quantified_count=len(quantified),
            unquantified_count=len(items) - len(quantified), total_status=total_status,
            monthly_estimate=monthly, annual_estimate=annual,
            shown_count=min(selection.top_n, len(items)),
            opportunities=[item.model_dump(mode="json") for item in ranked[:selection.top_n]],
        ))
    try:
        snapshot_json = snapshot.model_dump(mode="json")
        canonical = json.dumps(snapshot_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = sha256(canonical.encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        raise InvalidSavingsEvidence() from None
    result = dict(
        contract_version="savings-summary.v1", selection=selection.model_dump(mode="json"),
        generated_at=snapshot_json["generated_at"], data_status=snapshot.data_status,
        benefit_kind="potential_estimate", realized_savings=None,
        opportunity_count=len(active), excluded_count=len(snapshot.opportunities) - len(active),
        excluded_states=dict(Counter(item.state for item in snapshot.opportunities if item not in active)),
        groups=groups, limitations=snapshot.limitations,
        snapshot_sha256=digest,
        # Complete evidence survives top_n truncation and conversation reload.
        source_snapshot=snapshot_json,
    )
    return {"content": render_summary(result), "evidence": result}


def render_summary(result: dict) -> str:
    selection = result["selection"]
    lines = [
        "Resumen ejecutivo de oportunidades de ahorro",
        "Ahorro potencial estimado; no es ahorro realizado. Ahorro realizado: no verificado.",
        f"Periodo de las fuentes: {selection['start_date']} a {selection['end_date']} (fin exclusivo, UTC).",
        f"Suscripcion: {selection['subscription_id'] or 'todas las del tenant activo'}.",
        f"Snapshot: {result['generated_at']}. Cobertura: {result['data_status']}.",
        f"Oportunidades activas: {result['opportunity_count']}; excluidas por estado: {result['excluded_count']}.",
    ]
    if not result["groups"]:
        lines.append("No hay oportunidades activas en las fuentes consultadas; esto no acredita ahorro cero.")
    for group in result["groups"]:
        lines.append(f"\n{group['currency']}: {group['opportunity_count']} oportunidades; se muestran {group['shown_count']} por estimacion mensual.")
        if group["total_status"] == "non_additive":
            lines.append("Total no calculable: hay solapamientos posibles o independencia sin verificar. No sumar las estimaciones individuales.")
        elif group["total_status"] == "unavailable":
            lines.append("Ahorro potencial sin cuantificar; no se sustituye por cero.")
        else:
            qualifier = "Subtotal parcial conocido" if group["total_status"] == "partial" else "Total potencial estimado"
            lines.append(f"{qualifier}: {group['monthly_estimate']} {group['currency']}/mes; {group['annual_estimate']} {group['currency']}/año.")
        lines.append(f"Sin cuantificar: {group['unquantified_count']}. Monedas separadas, sin conversion.")
        for item in group["opportunities"]:
            amount = "sin cuantificar" if item["monthly_estimate"] is None else f"{item['monthly_estimate']} {item['currency']}/mes; {item['annual_estimate']} {item['currency']}/año"
            lines.extend([
                f"- {item['recommendation_id']}: {item['title']} — {amount} (estimado).",
                f"  Accion propuesta: {item['action']}. Riesgo: {item['risk']}; confianza: {item['confidence']}.",
                "  Supuestos: " + "; ".join(item["assumptions"]),
                "  Fuentes: " + "; ".join(f"{source['evidence_id']} — {source['title']} ({source['reference']})" for source in item["sources"]),
            ])
            lines.extend("  Limitacion: " + value for value in item["limitations"])
    lines.extend("Limitacion de cobertura: " + value for value in result["limitations"])
    lines.append("Las estimaciones mensual y anual proceden del proveedor; requieren validar supuestos y riesgo antes de actuar.")
    return "\n".join(lines)
