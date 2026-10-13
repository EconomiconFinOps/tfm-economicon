"""Evaluate observed billing totals; no persistence, forecast or notification."""
from decimal import Decimal, ROUND_HALF_UP, localcontext

from app.schemas.billing import BillingSummary
from app.schemas.budget import BudgetDefinition, BudgetEvaluation


def _display(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if rounded == 0 else format(rounded, "f")


def evaluate_budget(budget: BudgetDefinition, summary: BillingSummary) -> BudgetEvaluation:
    if (summary.period.start_date, summary.period.end_date) != (budget.start_date, budget.end_date):
        raise ValueError("Billing period does not match budget")
    currencies = [total.currency for total in summary.totals]
    if len(currencies) != len(set(currencies)):
        raise ValueError("Billing currencies must be unique")
    matching = next((total for total in summary.totals if total.currency == budget.currency), None)
    result = BudgetEvaluation(
        budget=budget, data_status=summary.data_status, evaluation_status="unavailable",
        record_count=matching.record_count if matching else 0,
        missing_dimension_count=summary.missing_dimension_count,
        excluded_undated_count=summary.excluded_undated_count,
    )
    if matching is None or matching.record_count <= 0 or summary.data_status == "empty":
        return result
    with localcontext() as context:
        # Enough headroom for products, ratios, subtraction and final quantization;
        # independent of process-wide Decimal context and amounts above JS precision.
        context.prec = max(80, len(matching.cost) + len(budget.amount) + 20)
        spend, amount = Decimal(matching.cost), Decimal(budget.amount)
        reached = [threshold for threshold in budget.thresholds_percent
                   if spend * 100 >= amount * Decimal(threshold)]
        return result.model_copy(update={
            "evaluation_status": "provisional" if summary.data_status == "partial" else "evaluated",
            "observed_spend": _display(spend),
            "consumption_percent": _display(spend * 100 / amount),
            "remaining_amount": _display(amount - spend),
            "deviation_amount": _display(spend - amount),
            "deviation_percent": _display((spend - amount) * 100 / amount),
            "reached_thresholds_percent": reached,
            "highest_reached_threshold_percent": reached[-1] if reached else None,
        })
