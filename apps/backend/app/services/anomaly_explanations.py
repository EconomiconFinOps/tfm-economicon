"""Explain observed rule matches deterministically; never infer a root cause."""
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from importlib import import_module

from pydantic import ValidationError

from app.schemas.anomaly_explanations import (
    AnomalyExplanation, DetectionSnapshot, ExplainAnomalyRequest,
)
from app.schemas.billing import BillingSummary


class DetectorUnavailable(Exception):
    pass


class InvalidSelection(Exception):
    pass


class InvalidDetectionEvidence(Exception):
    pass


class AnomalyNotFound(Exception):
    pass


class EvidenceChanged(Exception):
    pass


class BillingAnomalyProvider:
    """Adapter to JUP-030; no replacement detector or demo fallback."""

    def __init__(self, database):
        self.database = database

    def evaluate(self, tenant_id: str, selection: dict) -> dict:
        try:
            definition_type = import_module("app.schemas.anomalies").AnomalyDefinition
            evaluate = import_module("app.services.anomalies").evaluate_anomalies
        except (ImportError, AttributeError):
            raise DetectorUnavailable() from None
        try:
            definition = definition_type.model_validate(selection)
        except ValidationError:
            raise InvalidSelection() from None

        def read(start, end):
            return BillingSummary.model_validate(self.database.fetch_billing_summary(
                tenant_id, start_date=start, end_date=end,
                group_by=definition.group_by, tag_key=None,
            ))

        current = read(definition.start_date, definition.end_date)
        period = definition.baseline_period
        baseline = read(period.start_date, period.end_date) if period is not None else None
        return evaluate(definition, current, baseline, tenant_id=tenant_id).model_dump(mode="json")


def _verify(snapshot: DetectionSnapshot, alert, request: ExplainAnomalyRequest):
    """Reject inconsistent upstream evidence; arithmetic checks are not a detector."""
    if snapshot.definition != request.definition or snapshot.evaluation_status == "unavailable":
        raise InvalidDetectionEvidence()
    definition = snapshot.definition
    start, end = date.fromisoformat(definition.start_date), date.fromisoformat(definition.end_date)
    if start >= end or (snapshot.current_period.start_date, snapshot.current_period.end_date) != (start, end):
        raise InvalidDetectionEvidence()
    if alert.currency != definition.currency or not alert.trigger_reasons:
        raise InvalidDetectionEvidence()
    expected_reasons = []
    with localcontext() as context:
        context.prec = max(80, len(alert.current_cost) + len(alert.baseline_cost or "") + 40)
        cost = Decimal(alert.current_cost)
        threshold = definition.absolute_threshold
        expected_absolute = "disabled" if threshold is None else "triggered" if cost >= Decimal(threshold) else "below"
        if alert.threshold_status != expected_absolute:
            raise InvalidDetectionEvidence()
        if expected_absolute == "triggered":
            expected_reasons.append("absolute_threshold")
        if definition.deviation_threshold_percent is None:
            if snapshot.baseline_period is not None or snapshot.baseline_quality is not None:
                raise InvalidDetectionEvidence()
            if any(value is not None for value in (alert.baseline_cost, alert.delta_amount, alert.deviation_percent, alert.baseline_record_count)):
                raise InvalidDetectionEvidence()
            expected_deviation = "disabled"
        else:
            period = snapshot.baseline_period
            if period is None or snapshot.baseline_quality is None or (period.start_date, period.end_date) != (start - (end - start), start):
                raise InvalidDetectionEvidence()
            if alert.baseline_cost is None:
                expected_deviation = "baseline_missing"
                if any(value is not None for value in (alert.delta_amount, alert.deviation_percent, alert.baseline_record_count)):
                    raise InvalidDetectionEvidence()
            else:
                if not alert.baseline_record_count:
                    raise InvalidDetectionEvidence()
                previous = Decimal(alert.baseline_cost)
                delta = cost - previous
                if alert.delta_amount is None or Decimal(alert.delta_amount) != delta:
                    raise InvalidDetectionEvidence()
                if previous <= 0:
                    expected_deviation = "baseline_nonpositive"
                    if alert.deviation_percent is not None:
                        raise InvalidDetectionEvidence()
                else:
                    percent = (delta * 100 / previous).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if alert.deviation_percent is None or Decimal(alert.deviation_percent) != percent:
                        raise InvalidDetectionEvidence()
                    triggered = (delta >= Decimal(definition.min_absolute_increase)
                                 and delta * 100 >= previous * Decimal(definition.deviation_threshold_percent))
                    expected_deviation = "triggered" if triggered else "below"
        if alert.deviation_status != expected_deviation:
            raise InvalidDetectionEvidence()
        if expected_deviation == "triggered":
            expected_reasons.append("period_increase")
    if alert.trigger_reasons != expected_reasons:
        raise InvalidDetectionEvidence()
    provisional = (snapshot.current_quality.data_status == "partial"
                   or (snapshot.baseline_quality and snapshot.baseline_quality.data_status == "partial")
                   or alert.deviation_status in {"baseline_missing", "baseline_nonpositive"})
    if snapshot.current_quality.data_status == "empty" or (provisional and snapshot.evaluation_status != "provisional"):
        raise InvalidDetectionEvidence()


def explain_anomaly(raw: dict, request: ExplainAnomalyRequest) -> AnomalyExplanation:
    try:
        snapshot = DetectionSnapshot.model_validate(raw)
        matches = [item for item in snapshot.alerts if item.id == request.anomaly_id]
        if not matches:
            raise AnomalyNotFound()
        if len(matches) != 1:
            raise InvalidDetectionEvidence()
        alert = matches[0]
        if alert.evidence_id != request.evidence_id:
            raise EvidenceChanged()
        _verify(snapshot, alert, request)
    except (ValueError, TypeError, ArithmeticError):
        raise InvalidDetectionEvidence() from None

    definition = snapshot.definition
    group = json.dumps(alert.group_value, ensure_ascii=False) if alert.group_value is not None else "sin dimensión informada"
    subscription = (f" Suscripción: {json.dumps(alert.subscription_id, ensure_ascii=False)}."
                    if alert.subscription_id is not None else "")
    lines = [
        f"La anomalía {alert.id} fue marcada para {definition.group_by} {group}.{subscription}",
        f"Periodo UTC [{definition.start_date}, {definition.end_date}), fin excluido. "
        f"Coste observado: {alert.current_cost} {alert.currency}; registros: {alert.current_record_count}.",
    ]
    if "absolute_threshold" in alert.trigger_reasons:
        lines.append(f"El coste alcanza o supera el umbral absoluto de {definition.absolute_threshold} {alert.currency} (>=).")
    if "period_increase" in alert.trigger_reasons:
        period = snapshot.baseline_period
        lines.append(
            f"Frente al periodo UTC [{period.start_date}, {period.end_date}), "
            f"con {alert.baseline_cost} {alert.currency} y {alert.baseline_record_count} registros, "
            f"el incremento es {alert.delta_amount} {alert.currency} ({alert.deviation_percent}%). "
            f"Cumple el umbral de {definition.deviation_threshold_percent}% y el incremento mínimo "
            f"de {definition.min_absolute_increase} {alert.currency}. La decisión precede al redondeo del porcentaje."
        )
    elif alert.deviation_status in {"baseline_missing", "baseline_nonpositive"}:
        reason = "no hay observaciones comparables" if alert.baseline_cost is None else f"la base es {alert.baseline_cost} {alert.currency}, no positiva"
        lines.append(f"La regla de incremento no se puede evaluar: {reason}. No se interpreta como incremento cero.")
    elif alert.deviation_status == "below":
        lines.append("La regla de incremento no se activó; no cumplió simultáneamente el porcentaje y el incremento mínimo configurados.")

    limitations = [
        "El marcado identifica una coincidencia con reglas; no demuestra una causa ni un ahorro realizable.",
        "La cobertura temporal completa y la frescura de las fuentes no están verificadas.",
        "Los importes están redondeados a céntimos; no se convierten ni se suman monedas distintas.",
        "Los periodos se consultan por separado; una ingesta posterior puede cambiar la evaluación.",
    ]
    if snapshot.evaluation_status == "provisional":
        limitations.append("Evaluación provisional: hay datos parciales o comparaciones no evaluables.")
    quality = snapshot.current_quality
    lines.append(f"Calidad actual: {quality.data_status}; dimensiones ausentes: {quality.missing_dimension_count}; "
                 f"registros sin fecha excluidos: {quality.excluded_undated_count}.")
    checks = [
        "Contrastar la cobertura y las ingestas de ambos periodos antes de tomar decisiones.",
        "Revisar los recursos y consumos del grupo con su responsable; son comprobaciones pendientes, no causas confirmadas.",
    ]
    evidence = snapshot.model_dump(mode="json", exclude={"alerts", "assessments"})
    evidence["anomaly"] = alert.model_dump(mode="json")
    return AnomalyExplanation(
        content="\n".join(lines + limitations + ["Comprobaciones sugeridas:"] + checks),
        evidence=evidence, limitations=limitations, suggested_checks=checks,
    )
