"""Cost run scope, conflicts, cleanup, rowcounts and transactional rollback."""
from contextlib import contextmanager
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.repositories.azure_cost import SqlAzureCostRepository
from app.tasks.azure_cost_ingest import AzureCostIngestionService
from tenant_isolation_support import cockroach_isolation_database, isolation_database, required_scope, snapshot
from test_azure_cost_cockroach_integration import database_factory
from test_azure_cost_normalized_schema import normalized_record


@pytest.fixture
def costs(isolation_database):
    repository = SqlAzureCostRepository(isolation_database)
    for run, tenant, subscription in (("run-a", "tenant-a", "shared-subscription"), ("run-b", "tenant-b", "shared-subscription"), ("run-other-sub", "tenant-a", "other-subscription")):
        repository.start_run(run, tenant, subscription, {"fixture": True})
        repository.complete_run(run, tenant, subscription, (normalized_record(),), page_count=2, retry_count=1)
    return SimpleNamespace(db=isolation_database, repository=repository)


def state(costs):
    return snapshot(costs.db, "azure_cost_ingestion_runs", "azure_cost_records")


def denial(action):
    try:
        return action()
    except (PermissionError, LookupError, ValueError, RuntimeError):
        return None


@pytest.mark.parametrize(
    'isolation_database,target',
    [
        pytest.param('cockroach', 'run-b', id='cockroach-run-b'),
        pytest.param('cockroach', 'run-other-sub', id='cockroach-run-other-sub'),
    ],
    indirect=['isolation_database'],
)
def test_start_conflict_cannot_reset_foreign_run(costs, target):
    before = state(costs)
    denial(lambda: costs.repository.start_run(target, "tenant-a", "shared-subscription", {"attempt": "foreign"}))
    assert state(costs) == before


@pytest.mark.parametrize(
    'isolation_database,target',
    [
        pytest.param('sqlite', 'run-b', id='sqlite-run-b'),
        pytest.param('sqlite', 'run-other-sub', id='sqlite-run-other-sub'),
    ],
    indirect=['isolation_database'],
)
def test_complete_foreign_parent_cannot_insert_cross_scope_records(costs, target):
    before = state(costs)
    attacker_record = replace(normalized_record(), source_row_hash="b" * 64, resource_name="attempted-replacement")
    denial(lambda: costs.repository.complete_run(target, "tenant-a", "shared-subscription", (attacker_record,), page_count=9, retry_count=0))
    assert state(costs) == before


@pytest.mark.parametrize(
    'isolation_database,target,operation',
    [
        pytest.param('sqlite', 'run-b', 'fail_run', id='sqlite-run-b-fail_run'),
        pytest.param('sqlite', 'run-b', 'fetch_run', id='sqlite-run-b-fetch_run'),
        pytest.param('sqlite', 'run-b', 'fetch_records', id='sqlite-run-b-fetch_records'),
        pytest.param('sqlite', 'run-other-sub', 'fail_run', id='sqlite-run-other-sub-fail_run'),
        pytest.param('sqlite', 'run-other-sub', 'fetch_run', id='sqlite-run-other-sub-fetch_run'),
        pytest.param('sqlite', 'run-other-sub', 'fetch_records', id='sqlite-run-other-sub-fetch_records'),
    ],
    indirect=['isolation_database'],
)
def test_scoped_failure_cleanup_and_lookup_contract(costs, operation, target):
    method = getattr(costs.repository, operation)
    scope = required_scope(method, tenant_id="tenant-a", subscription_id="shared-subscription")
    before = state(costs)
    result = denial(lambda: method(target, "SyntheticFailure", **scope) if operation == "fail_run" else method(target, **scope))
    assert result in (None, [])
    assert state(costs) == before






class ReportZeroUpdatedRows:
    """Keep real writes/rollback but simulate the driver's unexpected rowcount."""
    def __init__(self, engine, stage):
        self.engine = engine
        self.stage = stage
        self.intercepted = []

    @contextmanager
    def begin(self):
        proxy_engine = self
        with self.engine.begin() as connection:
            class Proxy:
                def execute(self, statement, parameters=None):
                    result = connection.execute(statement, parameters)
                    if " ".join(str(statement).upper().split()).startswith(proxy_engine.stage):
                        proxy_engine.intercepted.append(proxy_engine.stage)
                        return SimpleNamespace(rowcount=0)
                    return result
            yield Proxy()




@pytest.mark.parametrize(
    'isolation_database,operation,field,value',
    [
        pytest.param('sqlite', 'complete', 'tenant_id', 'tenant-b', id='sqlite-complete-tenant_id-tenant-b'),
        pytest.param('sqlite', 'fail', 'subscription_id', 'other-subscription', id='sqlite-fail-subscription_id-other-subscription'),
    ],
    indirect=['isolation_database'],
)
def test_cleanup_preserves_inconsistent_cross_scope_children(costs, field, value, operation):
    with costs.db.engine.begin() as connection:
        connection.execute(text(f"UPDATE azure_cost_records SET {field}=:value WHERE ingestion_id='run-a'"), {"value": value})
    legacy = [row for row in state(costs)[1] if row["ingestion_id"] == "run-a"]
    assert len(legacy) == 1
    if operation == "complete":
        costs.repository.complete_run("run-a", "tenant-a", "shared-subscription", (replace(normalized_record(), source_row_hash="d" * 64),), page_count=1, retry_count=0)
    else:
        costs.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id="shared-subscription")
    assert all(row in state(costs)[1] for row in legacy)
    own = costs.repository.fetch_records("run-a", tenant_id="tenant-a", subscription_id="shared-subscription")
    assert len(own) == (1 if operation == "complete" else 0)


@pytest.mark.parametrize(
    'isolation_database,field,value',
    [
        pytest.param('sqlite', 'tenant_id', 'tenant-b', id='sqlite-tenant_id-tenant-b'),
    ],
    indirect=['isolation_database'],
)
def test_record_lookup_requires_matching_parent_even_when_child_scope_matches(costs, field, value):
    with costs.db.engine.begin() as connection:
        connection.execute(text(f"UPDATE azure_cost_ingestion_runs SET {field}=:value WHERE id='run-a'"), {"value": value})
    assert costs.repository.fetch_records("run-a", tenant_id="tenant-a", subscription_id="shared-subscription") == []


@pytest.mark.parametrize(
    'isolation_database',
    [
        pytest.param('cockroach', id='cockroach'),
    ],
    indirect=['isolation_database'],
)
def test_insert_failure_rolls_back_prior_deletion(costs):
    before = state(costs)
    invalid = replace(normalized_record(), currency=None)
    with pytest.raises(IntegrityError):
        costs.repository.complete_run("run-a", "tenant-a", "shared-subscription", (invalid,), page_count=1, retry_count=0)
    assert state(costs) == before
