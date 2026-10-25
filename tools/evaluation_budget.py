"""Local campaign reservations. Receipts and mutable state stay outside Git.

The ledger never turns missing usage into zero or a final-attempt receipt into
an all-attempt bill. An operator reconciles unknowns with authoritative receipts.
"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import tempfile


class BudgetError(RuntimeError):
    pass


def amount(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0: raise ValueError()
        return result
    except (InvalidOperation, ValueError):
        raise BudgetError('Invalid campaign amount') from None


class BudgetLedger:
    def __init__(self, path, *, alert=None):
        self.path = Path(path)
        self.alert = alert or (lambda message: print(message, file=__import__('sys').stderr))

    @contextmanager
    def locked(self):
        lock = self.path.with_suffix(self.path.suffix + '.lock')
        with lock.open('a+b') as handle:
            handle.seek(0, 2)
            if handle.tell() == 0: handle.write(b'0'); handle.flush()
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == 'nt': msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else: fcntl.flock(handle, fcntl.LOCK_UN)

    def _write(self, value):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=self.path.parent, delete=False) as handle:
                temporary = handle.name
                json.dump(value, handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary and os.path.exists(temporary): os.unlink(temporary)

    def initialize(self, *, budget_id, limit, alert_at, authorization):
        limit, alert_at = amount(limit), amount(alert_at)
        if not budget_id or not authorization or not 0 < alert_at < limit:
            raise BudgetError('Explicit authorization and valid campaign limits are required')
        with self.locked():
            if self.path.exists(): raise BudgetError('Preserve the existing campaign ledger')
            self._write({'version': 1, 'budget_id': budget_id, 'authorization': authorization,
                         'limit_usd': str(limit), 'alert_at_usd': str(alert_at), 'alerts': [], 'operations': {}})

    def _read(self):
        value = json.loads(self.path.read_text(encoding='utf-8'))
        if value.get('version') != 1 or not isinstance(value.get('operations'), dict):
            raise BudgetError('Invalid campaign ledger')
        return value

    @staticmethod
    def committed(value):
        return sum((amount(item['cost_usd']) if item['state'] == 'settled' else amount(item['reserved_usd'])
                    for item in value['operations'].values()), Decimal(0))

    def reserve(self, identifier, reserve, *, kind):
        reserve = amount(reserve)
        if kind not in {'chat', 'index', 'auxiliary'} or reserve <= 0 or (kind == 'chat' and reserve < Decimal('6.50')):
            raise BudgetError('Invalid operation reservation')
        with self.locked():
            value = self._read()
            if identifier in value['operations']: raise BudgetError('An operation cannot be reserved twice')
            if any(item['state'] in {'reserved', 'unknown'} for item in value['operations'].values()):
                raise BudgetError('An operation is in flight or unresolved; reconcile its cost and finish before new admission')
            total = self.committed(value) + reserve
            if total > amount(value['limit_usd']): raise BudgetError('Campaign budget would be exceeded')
            if total >= amount(value['alert_at_usd']) and not value['alerts']:
                self.alert('Campaign reservation reaches the 75% alert boundary before the operation starts')
                value['alerts'].append({'before_operation': identifier, 'committed_usd': str(total)})
            value['operations'][identifier] = {'kind': kind, 'state': 'reserved', 'reserved_usd': str(reserve),
                                               'cost_usd': None, 'receipt': None}
            self._write(value)

    def finish(self, identifier, receipt=None):
        with self.locked():
            value = self._read()
            operation = value['operations'][identifier]
            if operation['state'] == 'settled': raise BudgetError('Never count an operation twice')
            if receipt is None:
                operation['state'] = 'unknown'
            else:
                if (receipt.get('operation_id') != identifier or receipt.get('all_requests_accounted') is not True
                        or receipt.get('operation_finished') is not True
                        or not isinstance(receipt.get('reference'), str) or not receipt['reference']):
                    raise BudgetError('An authoritative all-request receipt is required')
                cost = amount(receipt.get('cost_usd'))
                operation.update(state='settled', cost_usd=str(cost), receipt=receipt)
            self._write(value)
            if self.committed(value) > amount(value['limit_usd']):
                raise BudgetError('Recorded actual cost exceeds the campaign limit; stop all operations')
