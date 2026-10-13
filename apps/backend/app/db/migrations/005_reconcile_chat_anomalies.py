"""Reconciliation marker for the two historically published 002 schemas.

The exclusive runner completes both resumable 002 schemas before history
migration 003. Existing ledger rows and application data are never rewritten.
"""
from importlib import import_module


def verify(connection):
    for name in ('002_chat_operations', '002_anomaly_episodes',
                 '003_dialogue_history', '004_dialogue_compaction'):
        import_module('app.db.migrations.' + name).verify(connection)


def upgrade(connection):
    verify(connection)
