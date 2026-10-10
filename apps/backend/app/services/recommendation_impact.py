"""Deterministic gross, steady-state savings; no provider prices or execution."""
from decimal import Decimal, ROUND_HALF_UP, localcontext

from app.schemas.recommendation_impact import (
    CurrencyImpact, ImpactReport, ImpactRequest, RecommendationImpact,
)


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def evaluate_recommendation_impact(request: ImpactRequest, tenant_id: str) -> ImpactReport:
    with localcontext() as context:
        # Bounded 18 integer + 6 fractional digits, 100 scenarios, annual x12.
        context.prec = 40
        impacts = []
        amounts: dict[str, Decimal] = {}
        for scenario in request.scenarios:
            amount = None
            if scenario.baseline_monthly_cost is not None:
                amount = max(Decimal("0"), Decimal(scenario.baseline_monthly_cost)
                             - Decimal(scenario.target_monthly_cost))
                amounts[scenario.recommendation_id] = amount
            impacts.append(RecommendationImpact(
                scenario=scenario,
                status="insufficient_data" if amount is None else "estimated" if amount > 0 else "no_savings",
                potential_monthly_savings=None if amount is None else _money(amount),
                potential_annual_savings=None if amount is None else _money(amount * 12),
            ))

        # Keep a feasible scenario, not the naive sum nor a claimed optimal portfolio.
        selected: list[RecommendationImpact] = []
        estimated = [item for item in impacts if item.scenario.recommendation_id in amounts]
        for item in sorted(estimated, key=lambda value: (
            -amounts[value.scenario.recommendation_id], value.scenario.recommendation_id,
        )):
            scopes = set(item.scenario.cost_scope_ids)
            item.excluded_by = [other.scenario.recommendation_id for other in selected
                                if scopes.intersection(other.scenario.cost_scope_ids)]
            if not item.excluded_by:
                item.included_in_total = True
                selected.append(item)

        totals = []
        for currency in sorted({item.currency for item in request.scenarios}):
            included = [item.scenario.recommendation_id for item in selected if item.scenario.currency == currency]
            amount = sum((amounts[identifier] for identifier in included), Decimal("0"))
            totals.append(CurrencyImpact(
                currency=currency,
                potential_monthly_savings=_money(amount) if included else None,
                potential_annual_savings=_money(amount * 12) if included else None,
                included_recommendation_ids=included,
                unestimated_recommendation_ids=sorted(item.scenario.recommendation_id for item in impacts
                    if item.scenario.currency == currency and item.status == "insufficient_data"),
            ))

        return ImpactReport(
            tenant_id=tenant_id, baseline_month=request.baseline_month,
            recommendations=impacts, totals=totals,
            assumptions=[
                "Baseline and target cover the same complete calendar month, scope, usage and price basis.",
                "Monthly potential is max(baseline minus target, 0); annual potential repeats that month 12 times.",
                "Annualization assumes immediate full adoption and unchanged usage and prices for 12 months.",
            ],
            limitations=[
                "Caller-supplied hypothetical inputs and evidence references are not verified billing or provider prices.",
                "Gross potential excludes implementation costs, adoption delays, seasonality and realised savings.",
                "Overlapping atomic cost scopes are alternatives; greedy selection is feasible, not necessarily optimal.",
                "Scope completeness and equivalence must be checked by the caller; unknown estimates remain null.",
                "Currencies are not converted; totals use unrounded amounts and display two decimal places.",
            ],
        )
