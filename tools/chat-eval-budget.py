"""Conservative operation admission; caller must persist reservations before POST.

This module does not fetch accounting or authorize a runtime. An unknown outcome
keeps its full reservation until a provider accounting reconciliation proves cost.
"""
from decimal import Decimal, InvalidOperation
import math

CAP = Decimal('2.00')
HISTORICAL_FLOOR = Decimal('0.957927619')


def money(value):
    if not isinstance(value, str):
        raise ValueError('Costs must be decimal strings')
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError('Invalid cost') from None
    if not result.is_finite() or result < 0:
        raise ValueError('Invalid cost')
    return result


def operation_bound(*, input_tokens_per_attempt, input_price_per_million,
                    output_price_per_million, auxiliary_bound_usd):
    # Repository limit: four attempts, each draft1000 + final2200 output tokens.
    # Input includes BOTH messages/schema payloads, not just the user question.
    if type(input_tokens_per_attempt) is not int or input_tokens_per_attempt <= 0:
        raise ValueError('Require a verified input-token upper bound')
    return (Decimal(4) * (Decimal(input_tokens_per_attempt) * money(input_price_per_million)
                         + Decimal(3200) * money(output_price_per_million)) / Decimal(1000000)
            + money(auxiliary_bound_usd))


def admit(snapshot, reservations, operation_id, bound, now):
    if (not isinstance(now, (int, float)) or not math.isfinite(now)
            or type(snapshot.get('observed_at')) not in (int, float)
            or not math.isfinite(snapshot['observed_at'])
            or not 0 <= now - snapshot['observed_at'] <= 30):
        raise ValueError('Live accounting is stale or invalid')
    if snapshot.get('scope') != 'jup035-cumulative-all-providers' or not snapshot.get('evidence_sha256'):
        raise ValueError('Accounting scope/evidence not verified')
    spent = money(snapshot['cumulative_usd'])
    if spent < HISTORICAL_FLOOR:
        raise ValueError('Accounting below confirmed historical spend')
    if not operation_id or operation_id in reservations:
        raise ValueError('Operation already reserved or unidentified')
    if not isinstance(bound, Decimal) or not bound.is_finite() or bound <= 0:
        raise ValueError('Require a positive bounded operation cost')
    outstanding = sum((money(value['reserved_usd']) for value in reservations.values()), Decimal(0))
    if spent + outstanding + bound > CAP:
        raise ValueError('Insufficient budget for worst-case operation')
    return {**reservations, operation_id: {'reserved_usd': str(bound),
                                         'accounting_evidence_sha256': snapshot['evidence_sha256'],
                                         'admitted_at': now, 'state': 'RESERVED'}}
