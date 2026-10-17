"""Durable admission and at-most-once dispatch for the local evaluation runner.

All campaigns in the authorized spend scope MUST share this database. Recording
DISPATCHING precedes the network call: a crash requires read-only reconciliation,
never an automatic POST retry. Provider reconciliation is deliberately separate.
"""
import importlib.util
import json
import hashlib
from pathlib import Path
import sqlite3
from contextlib import contextmanager
from uuid import uuid4

spec = importlib.util.spec_from_file_location('budget', Path(__file__).with_name('chat-eval-budget.py'))
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class Ledger:
    def __init__(self, path):
        self.path = Path(path).resolve()
        root = Path(__file__).resolve().parents[1]
        if self.path == root or root in self.path.parents:
            raise ValueError('Ledger must be outside the checkout')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS attempts ('
                       'request_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, sample_id TEXT NOT NULL, '
                       'reservation TEXT NOT NULL, state TEXT NOT NULL, conversation_id TEXT, '
                       'operation_id TEXT, UNIQUE(plan_hash,sample_id))')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, plan_hash, sample_id, snapshot, bound, now, *, authorized_cap_usd=None):
        if not plan_hash or not sample_id:
            raise ValueError('Plan and sample identity required')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM attempts WHERE plan_hash=? AND sample_id=?',
                          (plan_hash, sample_id)).fetchone():
                raise ValueError('Sample already reserved; reconcile existing handle')
            pending = {r['request_id']: json.loads(r['reservation'])
                       for r in db.execute('SELECT * FROM attempts')}
            request_id = str(uuid4())
            reservation = budget.admit(snapshot, pending, request_id, bound, now,
                                       authorized_cap_usd=authorized_cap_usd)[request_id]
            db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
                       (request_id, plan_hash, sample_id, json.dumps(reservation), 'RESERVED', None, None))
        return request_id

    def attach_conversation(self, request_id, conversation_id):
        if not conversation_id:
            raise ValueError('Conversation identity required')
        with self.connect() as db:
            count = db.execute('UPDATE attempts SET conversation_id=? WHERE request_id=? '
                               "AND state='RESERVED' AND conversation_id IS NULL",
                               (conversation_id, request_id)).rowcount
            if count != 1:
                raise ValueError('Conversation already set or request not reserved')

    def dispatch(self, request_id, send):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM attempts WHERE request_id=?', (request_id,)).fetchone()
            if row is None or row['state'] != 'RESERVED' or not row['conversation_id']:
                raise ValueError('Do not resend: reconcile existing operation')
            db.execute("UPDATE attempts SET state='DISPATCHING' WHERE request_id=?", (request_id,))
        # Commit/fsync happens before side effects. Neither exceptions nor missing
        # response IDs release money or reset dispatch state.
        operation_id = send(row['conversation_id'], request_id)
        if not isinstance(operation_id, str) or not operation_id:
            raise ValueError('Missing operation handle; read-only reconciliation required')
        self.observe_handle(request_id, operation_id)
        return operation_id

    def observe_handle(self, request_id, operation_id):
        if not isinstance(operation_id, str) or not operation_id:
            raise ValueError('Operation identity required')
        with self.connect() as db:
            count = db.execute("UPDATE attempts SET operation_id=?, state='OBSERVING' WHERE request_id=? "
                               "AND state IN ('DISPATCHING','OBSERVING') "
                               'AND (operation_id IS NULL OR operation_id=?)',
                               (operation_id, request_id, operation_id)).rowcount
            if count != 1:
                raise ValueError('Operation identity changed or request not dispatched')

    def pending(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM attempts ORDER BY rowid')]


    def retain_failed_cost(self, request_id, receipt):
        """Keep the entire bound for a proved terminal failure with unknown cost."""
        operation = receipt.get('operation', {})
        checks = receipt.get('verification', {})
        if (operation.get('state') != 'failed'
                or receipt.get('collection_state') != 'VERIFIED_PUBLIC_SNAPSHOT'
                or checks.get('input_matches_bank') is not True
                or checks.get('stable_snapshot') is not True
                or not receipt.get('durable_input_supplement')):
            raise ValueError('Verified durable terminal failure required')
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        self._retain_unknown_cost(request_id, receipt, digest, 'terminal_failure')

    def retain_completed_cost(self, request_id, receipt):
        """Record a verified completed response while keeping its ENTIRE maximum."""
        operation = receipt.get('operation', {})
        checks = receipt.get('verification', {})
        result = receipt.get('result')
        resources = receipt.get('resources')
        if (operation.get('state') != 'completed'
                or receipt.get('collection_state') != 'VERIFIED_PUBLIC_SNAPSHOT'
                or any(checks.get(key) is not True for key in
                       ('input_matches_bank', 'stable_snapshot', 'public_history_parity', 'citation_ids_known'))
                or not isinstance(result, dict) or not isinstance(result.get('content'), str)
                or not result['content'].strip()
                or not isinstance(resources, dict)):
            raise ValueError('Verified completed public receipt required')
        if (resources.get('operation') != operation or resources.get('operation_after') != operation
                or resources.get('result') != result
                or resources.get('history') != receipt.get('history')
                or not isinstance(resources.get('history'), dict)):
            raise ValueError('Completed receipt public snapshot mismatch')
        resources_digest = hashlib.sha256(json.dumps(receipt['resources'], sort_keys=True,
            ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if resources_digest != receipt.get('resources_sha256'):
            raise ValueError('Completed receipt resources mismatch')
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        self._retain_unknown_cost(request_id, receipt, digest, 'terminal_completed')

    def _retain_unknown_cost(self, request_id, receipt, digest, proof_key):
        operation = receipt['operation']
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM attempts WHERE request_id=?', (request_id,)).fetchone()
            if (row is None or row['state'] != 'OBSERVING'
                    or row['operation_id'] != operation.get('operation_id')
                    or receipt.get('conversation_id') != row['conversation_id']):
                raise ValueError('Terminal receipt does not match observed operation')
            reservation = json.loads(row['reservation'])
            if reservation['state'] != 'RESERVED':
                raise ValueError('Only an untouched full reservation can be retained')
            reservation.update(state='COST_UNKNOWN_RESERVED',
                maximum_reserved_usd=reservation['reserved_usd'],
                **{proof_key: {'operation_id': row['operation_id'], 'state': operation['state'],
                               'receipt_sha256': digest}})
            db.execute('UPDATE attempts SET reservation=? WHERE request_id=?',
                (json.dumps(reservation), request_id))

    def reconcile_cost(self, request_id, operation, reports, auxiliary_cost_usd):
        cost = budget.completed_attempt_cost(operation, reports) + budget.money(auxiliary_cost_usd)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM attempts WHERE request_id=?', (request_id,)).fetchone()
            if row is None or row['state'] != 'OBSERVING' or row['operation_id'] != operation['operation_id']:
                raise ValueError('Accounting does not match observed operation')
            reservation = json.loads(row['reservation'])
            if cost > budget.money(reservation['reserved_usd']):
                raise ValueError('Observed cost exceeded reservation; halt campaign')
            # Retain actual cost in outstanding totals even after provider counters
            # include it. This deliberately double-counts rather than releasing
            # money based on asynchronous upstream counter timing.
            reservation['maximum_reserved_usd'] = reservation['reserved_usd']
            reservation['reserved_usd'] = str(cost)
            reservation['state'] = 'COST_OBSERVED'
            reservation['attempt_reports'] = reports
            reservation['auxiliary_cost_usd'] = auxiliary_cost_usd
            db.execute('UPDATE attempts SET reservation=? WHERE request_id=?',
                       (json.dumps(reservation), request_id))
