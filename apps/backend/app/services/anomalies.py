"""Deterministic rules over observed billing aggregates, not causal diagnosis."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json

from app.schemas.anomalies import (
    AnomalyAssessment, AnomalyDefinition, AnomalyEvaluation, AnomalyQuality, CostAnomaly,
)
from app.schemas.billing import BillingGroup, BillingPeriod, BillingSummary


def _money(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if rounded == 0 else format(rounded, "f")


def _key(group: BillingGroup, group_by: str) -> tuple:
    value = group.value
    if group_by == "resource_group" and value is not None:
        value = value.lower()  # Matches billing SQL lower(value), within subscription.
    return group.currency, group.subscription_id, value


def _groups(summary: BillingSummary, definition: AnomalyDefinition, period: BillingPeriod) -> dict:
    if summary.period != period or summary.group_by != definition.group_by or summary.tag_key is not None:
        raise ValueError("Billing selection does not match anomaly definition")
    if len({total.currency for total in summary.totals}) != len(summary.totals):
        raise ValueError("Billing currencies must be unique")
    result = {}
    for group in summary.groups:
        key = _key(group, definition.group_by)
        if key in result:
            raise ValueError("Billing groups must be unique")
        if group.record_count <= 0:
            raise ValueError("Billing groups must contain observed records")
        result[key] = group
    if summary.data_status == "empty" and (summary.totals or summary.groups):
        raise ValueError("Empty billing summary contains observations")
    return {key: group for key, group in result.items() if group.currency == definition.currency}


def _quality(summary: BillingSummary, currency: str) -> AnomalyQuality:
    return AnomalyQuality(
        data_status=summary.data_status,
        record_count=sum(total.record_count for total in summary.totals if total.currency == currency),
        missing_dimension_count=summary.missing_dimension_count,
        excluded_undated_count=summary.excluded_undated_count,
    )


def evaluate_anomalies(
    definition: AnomalyDefinition, current: BillingSummary, baseline: BillingSummary | None = None,
    *, tenant_id: str,
) -> AnomalyEvaluation:
    period = BillingPeriod(start_date=definition.start_date, end_date=definition.end_date)
    prior_period = definition.baseline_period
    groups = _groups(current, definition, period)
    if (baseline is None) != (prior_period is None):
        raise ValueError("Baseline presence does not match enabled rules")
    prior = _groups(baseline, definition, prior_period) if baseline is not None else {}
    current_quality = _quality(current, definition.currency)
    baseline_quality = _quality(baseline, definition.currency) if baseline is not None else None
    assessments, alerts = [], []
    for key, group in sorted(groups.items(), key=lambda pair: tuple(part or "" for part in pair[0])):
        previous = prior.get(key)
        with localcontext() as context:
            # String money and high precision preserve cents beyond IEEE-754 and local context.
            context.prec = max(80, len(group.cost) + (len(previous.cost) if previous else 0) + 40)
            cost = Decimal(group.cost)
            previous_cost = Decimal(previous.cost) if previous else None
            delta = cost - previous_cost if previous_cost is not None else None
            percent = delta * 100 / previous_cost if previous_cost is not None and previous_cost > 0 else None
            threshold_status = "disabled"
            deviation_status = "disabled"
            reasons = []
            if definition.absolute_threshold is not None:
                threshold_status = "triggered" if cost >= Decimal(definition.absolute_threshold) else "below"
                if threshold_status == "triggered":
                    reasons.append("absolute_threshold")
            if prior_period is not None:
                if previous_cost is None:
                    deviation_status = "baseline_missing"
                elif previous_cost <= 0:
                    deviation_status = "baseline_nonpositive"
                else:
                    # Compare before display rounding, using cross multiplication.
                    triggered = (delta >= Decimal(definition.min_absolute_increase)
                                 and delta * 100 >= previous_cost * Decimal(definition.deviation_threshold_percent))
                    deviation_status = "triggered" if triggered else "below"
                    if triggered:
                        reasons.append("period_increase")
            assessment = AnomalyAssessment(
                group_value=group.value, subscription_id=group.subscription_id, currency=group.currency,
                current_cost=group.cost, baseline_cost=previous.cost if previous else None,
                current_record_count=group.record_count,
                baseline_record_count=previous.record_count if previous else None,
                delta_amount=_money(delta) if delta is not None else None,
                deviation_percent=_money(percent) if percent is not None else None,
                threshold_status=threshold_status, deviation_status=deviation_status, trigger_reasons=reasons,
            )
        assessments.append(assessment)
        if reasons:
            identity = json.dumps([1, tenant_id, definition.model_dump(mode="json"), key],
                                  sort_keys=True, ensure_ascii=True, separators=(",", ":"))
            evidence = json.dumps([identity, assessment.model_dump(), current_quality.model_dump(),
                                   baseline_quality.model_dump() if baseline_quality else None],
                                  sort_keys=True, ensure_ascii=True, separators=(",", ":"))
            alerts.append(CostAnomaly(id="cost-" + hashlib.sha256(identity.encode()).hexdigest(),
                                      evidence_id="evidence-" + hashlib.sha256(evidence.encode()).hexdigest(),
                                      **assessment.model_dump()))
    partial = current.data_status == "partial" or (baseline is not None and baseline.data_status == "partial")
    # A missing/nonpositive comparison cannot silently become a clean bill of health.
    incomplete = any(item.deviation_status in {"baseline_missing", "baseline_nonpositive"} for item in assessments)
    return AnomalyEvaluation(
        definition=definition, current_period=period, baseline_period=prior_period,
        current_quality=current_quality, baseline_quality=baseline_quality,
        evaluation_status="unavailable" if not groups else "provisional" if partial or incomplete else "evaluated",
        alerts=alerts, assessments=assessments,
    )
