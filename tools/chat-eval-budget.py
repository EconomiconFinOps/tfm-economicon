"""Conservative operation admission; caller must persist reservations before POST.

This module does not fetch accounting or authorize a runtime. An unknown outcome
keeps its full reservation until a provider accounting reconciliation proves cost.
"""
from decimal import Decimal, InvalidOperation
import math
from datetime import datetime
import hashlib
import json

CAP = Decimal('2.00')
HISTORICAL_FLOOR = Decimal('0.957927619')


def accounting_snapshot(upstream, keys, now):
    """Derive a conservative cap from actual read-only accounting responses.

    Caller fetches all responses together and supplies their observation time.
    Upstream account usage may include other work: it is an upper bound, never
    asserted to be the exact task spend. No secret-bearing raw response is kept.
    """
    if set(keys) != {'backend', 'processor'}:
        raise ValueError('Both validation keys must be accounted for')
    usage = money(str(upstream['usage']))
    gateway_spend = Decimal(0)
    safe_keys = {}
    for service, info in keys.items():
        expiry = datetime.fromisoformat(info['expires'].replace('Z', '+00:00'))
        if expiry.tzinfo is None or expiry.timestamp() <= now:
            raise ValueError('Validation credentials expired; renewal requires preserved accounting')
        spend = money(str(info['spend']))
        maximum = money(str(info['max_budget']))
        if spend >= maximum:
            raise ValueError('Validation key budget exhausted')
        gateway_spend += spend
        safe_keys[service] = {'spend': str(spend), 'max_budget': str(maximum),
                              'expires': info['expires']}
    # Upper bounds cannot be added: upstream already includes gateway charges.
    # This assumes all authorized inference goes through this OpenRouter account;
    # a runner must verify that constraint and halt on any other route.
    conservative = max(usage, gateway_spend, HISTORICAL_FLOOR)
    evidence = {'upstream_usage': str(usage), 'keys': safe_keys, 'observed_at': now}
    evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
    return {'scope': 'jup035-cumulative-all-providers', 'observed_at': now,
            'cumulative_usd': str(conservative), 'evidence_sha256': evidence_hash,
            'accounting_basis': 'conservative OpenRouter account upper bound; not exact task attribution',
            'evidence': evidence}


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
