"""Conservative operation admission; caller must persist reservations before POST.

This module does not fetch accounting or authorize a runtime. An unknown outcome
keeps its full reservation until a provider accounting reconciliation proves cost.
"""
from decimal import Decimal, InvalidOperation
import math
from datetime import datetime
import hashlib
import json
import re

# User raised the cumulative limit to USD5 on 2026-10-14; prior spend remains.
CAP = Decimal('5.00')
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


def completed_attempt_cost(operation, reports):
    """Cost from complete observed reports for EVERY attempt, including failures.

    Caller must retrieve reports from the authenticated processor logs for the
    verified runtime. An unreported attempt cannot be treated as a free call.
    """
    count = operation.get('attempt_count')
    if (operation.get('state') not in ('completed', 'failed', 'cancelled')
            or type(count) is not int or not 1 <= count <= 4 or len(reports) != count):
        raise ValueError('Terminal operation with all attempt reports required')
    seen, total = set(), Decimal(0)
    for report in reports:
        attempt = report.get('attempt_id')
        legs = report.get('attempted_legs')
        if (not attempt or attempt in seen or report.get('operation_id') != operation.get('operation_id')
                or report.get('event') != 'chat_review_usage' or report.get('complete') is not True
                or type(legs) is not int or legs not in (1, 2) or report.get('reported_legs') != legs
                or len(report.get('requests', [])) != legs):
            raise ValueError('Incomplete or mismatched attempt accounting')
        seen.add(attempt)
        total += money(str(report['observed']['cost_usd']))
    if operation.get('current_attempt_id') not in seen:
        raise ValueError('Terminal attempt is missing')
    return total


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
    coverage = snapshot.get('complete_ledger_history')
    if coverage is not None:
        # Explicit opt-in only after the operator has audited that the historical
        # floor covers all prior work and this ledger covers every later charge.
        # Keep independent upper bounds: upstream may lag, while its global
        # counter may also include unrelated work. Never delete settled costs.
        identity = hashlib.sha256(json.dumps(sorted(reservations)).encode()).hexdigest()
        if (coverage.get('historical_floor_usd') != str(HISTORICAL_FLOOR)
                or coverage.get('request_ids_sha256') != identity):
            raise ValueError('Incomplete or mismatched ledger history')
        settled = sum((money(value['reserved_usd']) for value in reservations.values()
                       if value.get('state') == 'COST_OBSERVED'), Decimal(0))
        outstanding -= settled
        spent = max(spent, HISTORICAL_FLOOR + settled)
    if spent + outstanding + bound > CAP:
        raise ValueError('Insufficient budget for worst-case operation')
    return {**reservations, operation_id: {'reserved_usd': str(bound),
                                         'accounting_evidence_sha256': snapshot['evidence_sha256'],
                                         'admitted_at': now, 'state': 'RESERVED'}}


def retained_failure(reservation, operation_id, receipt=None):
    """Verify identity/full bound; this NEVER establishes or releases actual cost."""
    proof = reservation.get('terminal_failure', {})
    if (reservation.get('state') != 'COST_UNKNOWN_RESERVED'
            or money(reservation.get('reserved_usd')) <= 0
            or reservation.get('reserved_usd') != reservation.get('maximum_reserved_usd')
            or proof.get('state') != 'failed' or proof.get('operation_id') != operation_id
            or not re.fullmatch('[a-f0-9]{64}', str(proof.get('receipt_sha256', '')))):
        raise ValueError('Invalid retained terminal failure')
    if receipt is not None:
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if (receipt.get('operation', {}).get('state') != 'failed'
                or receipt.get('operation', {}).get('operation_id') != operation_id
                or receipt.get('collection_state') != 'VERIFIED_PUBLIC_SNAPSHOT'
                or digest != proof['receipt_sha256']):
            raise ValueError('Retained failure receipt mismatch')
    return True
