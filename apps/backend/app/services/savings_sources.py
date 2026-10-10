"""Explicit consumer of JUP-033/034 v1 reports, supplied by server-side loaders.

These private consumer schemas intentionally do not import unmerged producer code.
No loader is installed here and no caller-submitted report is accepted by the API.
Impact scenarios remain hypothetical; their original reports are retained intact.
"""
from collections.abc import Callable
from datetime import date, datetime, timezone
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.savings import Currency, Money, SavingsSelection, SavingsSnapshot
from app.services.savings_summary import InvalidSavingsEvidence


_Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
_Reference = Annotated[str, StringConstraints(min_length=1, max_length=256)]
_Id = Annotated[str, StringConstraints(pattern=r"^[a-z-]+:sha256:[0-9a-f]{64}$")]
_RawMoney = Annotated[str, StringConstraints(pattern=r"^(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,6})?$")]
_NetMoney = Annotated[str, StringConstraints(pattern=r"^-?(0|[1-9][0-9]*)\.[0-9]{2}$")]
_Rule = Literal["missing_project", "largest_project_cost"]
_Level = Literal["low", "medium", "high"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Period(_Strict):
    start_date: date
    end_date: date
    timezone: Literal["UTC"]


class _Scope(_Strict):
    dimension: Literal["project"]
    value: str | None


class _Cost(_Strict):
    amount: _NetMoney
    currency: Currency
    record_count: int = Field(gt=0)


class _Query(_Strict):
    period: _Period
    group_by: Literal["project"]
    tag_key: None


class _Evidence(_Strict):
    id: _Id
    kind: Literal["cost_query"]
    source: Literal["azure_cost_records"]
    query: _Query
    rule_id: _Rule
    rule_version: Literal[1]
    scope: _Scope
    observed_cost: _Cost


class _Recommendation(_Strict):
    id: _Id
    rule_id: _Rule
    rule_version: Literal[1]
    category: Literal["tagging", "investigation"]
    qualification: Literal["supported", "investigation_candidate"]
    action: _Text
    rationale: _Text
    scope: _Scope
    observed_cost: _Cost
    estimated_savings: None
    currency: None
    confidence: _Level
    risk: _Level
    difficulty: Literal["low", "medium", "high", "unknown"]
    evidence_ids: list[_Id] = Field(min_length=1, max_length=1)
    requires_human_approval: Literal[True]


class _NotEvaluated(_Strict):
    action: Literal["rightsizing", "scheduling", "orphan_cleanup", "rate_optimization", "savings_impact"]
    missing_inputs: list[_Text] = Field(min_length=1)


class _RecommendationReport(_Strict):
    contract_version: Literal[1]
    period: _Period
    source: Literal["azure_cost_records"]
    cloud: Literal["azure"]
    data_environment: Literal["simulated"]
    data_status: Literal["available", "partial", "empty"]
    status: Literal["available", "insufficient_data"]
    recommendations: list[_Recommendation] = Field(max_length=50)
    evidence: list[_Evidence] = Field(max_length=50)
    total_candidates: int = Field(ge=0)
    truncated: bool
    assumptions: list[_Text]
    limitations: list[_Text]
    not_evaluated: list[_NotEvaluated]
    missing_dimension_count: int = Field(ge=0)
    excluded_undated_count: int = Field(ge=0)


class _Scenario(_Strict):
    recommendation_id: _Reference
    cost_scope_ids: list[_Reference] = Field(min_length=1, max_length=100)
    currency: Currency
    baseline_monthly_cost: _RawMoney | None
    target_monthly_cost: _RawMoney | None
    evidence_ids: list[_Reference] = Field(min_length=1, max_length=20)
    assumptions: list[_Text] = Field(min_length=1, max_length=20)


class _Impact(_Strict):
    scenario: _Scenario
    status: Literal["estimated", "no_savings", "insufficient_data"]
    potential_monthly_savings: Money | None
    potential_annual_savings: Money | None
    observed_savings: None
    included_in_total: bool
    excluded_by: list[_Reference]


class _CurrencyImpact(_Strict):
    currency: Currency
    potential_monthly_savings: Money | None
    potential_annual_savings: Money | None
    included_recommendation_ids: list[_Reference]
    unestimated_recommendation_ids: list[_Reference]
    observed_savings: None


class _ImpactReport(_Strict):
    schema_version: Literal["1.0"]
    tenant_id: _Reference
    baseline_month: date
    basis: Literal["caller_supplied_scenario"]
    aggregation_method: Literal["descending_savings_disjoint_scopes"]
    recommendations: list[_Impact] = Field(max_length=100)
    totals: list[_CurrencyImpact]
    assumptions: list[_Text]
    limitations: list[_Text]


NO_IMPACT = "Impacto JUP-034 no disponible para esta recomendacion; el coste observado no es ahorro."
HYPOTHETICAL = "Impacto hipotetico de un escenario suministrado; sus supuestos y referencias no acreditan ahorro verificado."
NON_ADDITIVE = "Las estimaciones individuales no se suman; los totales originales JUP-034 se conservan en upstream_reports."


def _decode(raw, model):
    if isinstance(raw, BaseModel):
        raw = raw.model_dump(mode="json")
    # Copy the supplied snapshot and reject NaN, Infinity and non-JSON objects.
    serialized = json.dumps(raw, ensure_ascii=False, allow_nan=False)
    return model.model_validate_json(serialized), json.loads(serialized)


def _unique(values):
    if len(values) != len(set(values)):
        raise InvalidSavingsEvidence()
    return set(values)


def _validate_recommendations(report, selection):
    if (report.period.start_date, report.period.end_date) != (selection.start_date, selection.end_date):
        raise InvalidSavingsEvidence()
    _unique([item.id for item in report.recommendations])
    _unique([item.id for item in report.evidence])
    if (report.total_candidates < len(report.recommendations)
            or report.truncated != (report.total_candidates > len(report.recommendations))
            or (report.status == "insufficient_data" and (report.total_candidates or report.evidence))
            or (report.data_status == "empty" and (report.total_candidates or report.evidence))):
        raise InvalidSavingsEvidence()
    evidence = {item.id: item for item in report.evidence}
    referenced = set()
    for item in report.recommendations:
        expected = ("tagging", "supported") if item.rule_id == "missing_project" else ("investigation", "investigation_candidate")
        if ((item.category, item.qualification) != expected
                or (item.scope.value is None) != (item.rule_id == "missing_project")):
            raise InvalidSavingsEvidence()
        for identifier in item.evidence_ids:
            source = evidence.get(identifier)
            if (source is None or source.query.period != report.period
                    or (source.rule_id, source.rule_version, source.scope, source.observed_cost)
                    != (item.rule_id, item.rule_version, item.scope, item.observed_cost)):
                raise InvalidSavingsEvidence()
            referenced.add(identifier)
    if referenced != set(evidence):
        raise InvalidSavingsEvidence()


def _validate_impact(report, recommendations, tenant_id, selection):
    month = selection.start_date
    next_month = date(month.year + 1, 1, 1) if month.month == 12 else date(month.year, month.month + 1, 1)
    if (report.tenant_id != tenant_id or month.day != 1 or report.baseline_month != month
            or selection.end_date != next_month):
        raise InvalidSavingsEvidence()
    known = {item.id: item for item in recommendations.recommendations}
    _unique([item.scenario.recommendation_id for item in report.recommendations])
    impacts = {item.scenario.recommendation_id: item for item in report.recommendations}
    currencies = {}
    for identifier, item in impacts.items():
        scenario = item.scenario
        scopes = [value.casefold().rstrip("/") for value in scenario.cost_scope_ids]
        _unique(scopes)
        references = _unique(scenario.evidence_ids)
        if (identifier not in known or scenario.currency != known[identifier].observed_cost.currency
                or not references.issubset(known[identifier].evidence_ids)
                or not all(scopes) or (scenario.baseline_monthly_cost is None) != (scenario.target_monthly_cost is None)
                or (item.potential_monthly_savings is None) != (item.potential_annual_savings is None)
                or (item.status == "insufficient_data") != (item.potential_monthly_savings is None)
                or (scenario.baseline_monthly_cost is None) != (item.status == "insufficient_data")
                or (item.status == "no_savings" and (item.potential_monthly_savings, item.potential_annual_savings) != ("0.00", "0.00"))):
            raise InvalidSavingsEvidence()
        for scope in scopes:
            if scope in currencies and currencies[scope] != scenario.currency:
                raise InvalidSavingsEvidence()
            currencies[scope] = scenario.currency
        exclusions = _unique(item.excluded_by)
        if (not exclusions.issubset(impacts) or identifier in exclusions
                or (item.included_in_total and (exclusions or item.status == "insufficient_data"))):
            raise InvalidSavingsEvidence()
    for identifier, item in impacts.items():
        scopes = {value.casefold().rstrip("/") for value in item.scenario.cost_scope_ids}
        overlaps = {other_id for other_id, other in impacts.items()
                    if other_id != identifier and other.included_in_total
                    and scopes.intersection(value.casefold().rstrip("/") for value in other.scenario.cost_scope_ids)}
        if (item.included_in_total and overlaps
                or item.status != "insufficient_data" and not item.included_in_total and set(item.excluded_by) != overlaps
                or item.status != "insufficient_data" and not item.included_in_total and not overlaps
                or item.status == "insufficient_data" and item.excluded_by):
            raise InvalidSavingsEvidence()
    total_currencies = _unique([item.currency for item in report.totals])
    if total_currencies != {item.scenario.currency for item in impacts.values()}:
        raise InvalidSavingsEvidence()
    for total in report.totals:
        included = _unique(total.included_recommendation_ids)
        unknown = _unique(total.unestimated_recommendation_ids)
        if (included != {key for key, item in impacts.items() if item.scenario.currency == total.currency and item.included_in_total}
                or unknown != {key for key, item in impacts.items() if item.scenario.currency == total.currency and item.status == "insufficient_data"}
                or (total.potential_monthly_savings is None) != (total.potential_annual_savings is None)
                or bool(included) != (total.potential_monthly_savings is not None)):
            raise InvalidSavingsEvidence()
    return impacts


class RecommendationSavingsProvider:
    """Adapter enabled only by explicitly installing trusted server-side loaders."""

    def __init__(self, recommendation_loader: Callable, impact_loader: Callable | None = None):
        self.recommendation_loader = recommendation_loader
        self.impact_loader = impact_loader

    def load_snapshot(self, tenant_id: str, selection: SavingsSelection) -> dict:
        # JUP-033 aggregates projects across the authorized tenant's subscriptions.
        if not tenant_id.strip() or selection.subscription_id is not None:
            raise InvalidSavingsEvidence()
        raw_recommendations = self.recommendation_loader(tenant_id, selection)
        raw_impact = self.impact_loader(tenant_id, selection) if self.impact_loader else None
        try:
            report, original = _decode(raw_recommendations, _RecommendationReport)
            _validate_recommendations(report, selection)
            upstream = {"JUP-033": original}
            impacts = {}
            impact_report = None
            if raw_impact is not None:
                impact_report, original_impact = _decode(raw_impact, _ImpactReport)
                impacts = _validate_impact(impact_report, report, tenant_id, selection)
                upstream["JUP-034"] = original_impact
            limitations = list(report.limitations)
            limitations.append(NON_ADDITIVE if impact_report else NO_IMPACT)
            if report.truncated:
                limitations.append(f"JUP-033 devuelve {len(report.recommendations)} de {report.total_candidates} candidatos; cobertura truncada.")
            if impact_report:
                limitations.extend([HYPOTHETICAL, *impact_report.limitations])
            opportunities = []
            for item in report.recommendations:
                impact = impacts.get(item.id)
                assumptions = list(report.assumptions)
                item_limitations = list(report.limitations)
                if impact:
                    assumptions.extend([*impact_report.assumptions, *impact.scenario.assumptions])
                    item_limitations.extend([HYPOTHETICAL, NON_ADDITIVE, *impact_report.limitations])
                    if impact.excluded_by:
                        item_limitations.append("Escenario excluido del total JUP-034 por alternativas solapadas: " + ", ".join(impact.excluded_by))
                if impact is None or impact.status == "insufficient_data":
                    item_limitations.append(NO_IMPACT)
                opportunities.append(dict(
                    recommendation_id=item.id, tenant_id=tenant_id, subscription_id=None,
                    title=item.action, action=item.action, state="proposed",
                    currency=item.observed_cost.currency,
                    monthly_estimate=impact.potential_monthly_savings if impact else None,
                    annual_estimate=impact.potential_annual_savings if impact else None,
                    independent_cost_basis=None, risk=item.risk, confidence=item.confidence,
                    assumptions=assumptions or ["Se conserva el contexto y las reglas del informe JUP-033."],
                    limitations=list(dict.fromkeys(item_limitations)),
                    sources=[dict(evidence_id=identifier, title="Coste observado Azure simulado; no es ahorro",
                                  reference=f"azure_cost_records; project={item.scope.value!r}; [{selection.start_date}, {selection.end_date}) UTC")
                             for identifier in item.evidence_ids],
                ))
            snapshot = SavingsSnapshot(
                contract_version="savings-input.v1", tenant_id=tenant_id,
                start_date=selection.start_date, end_date=selection.end_date, subscription_id=None,
                generated_at=datetime.now(timezone.utc),
                data_status="empty" if not opportunities else "partial" if report.truncated or report.data_status == "partial" else "available",
                opportunities=opportunities, limitations=list(dict.fromkeys(limitations)),
                upstream_reports=upstream,
            )
            return snapshot.model_dump(mode="json")
        except (ValueError, TypeError, KeyError):
            raise InvalidSavingsEvidence() from None
