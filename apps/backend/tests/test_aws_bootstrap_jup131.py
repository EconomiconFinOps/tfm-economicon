from unittest.mock import Mock

import pytest


def test_backend_migrates_before_granting_application_roles(monkeypatch):
    from app import aws_bootstrap as module
    context = Mock()
    engine = context.admin_engine.return_value
    events = []
    migration = Mock()
    migration.run.side_effect = lambda: events.append('migration')
    monkeypatch.setattr(module, 'MigrationRunner', Mock(return_value=migration))
    monkeypatch.setattr(module, 'grant_application_roles', lambda *args: events.append('grant'))
    module.execute(context, 'database')
    assert events == ['migration', 'grant']
    context.admin_engine.assert_called_once_with('operational')
    engine.dispose.assert_called_once()


def test_migration_failure_releases_engine_without_grants(monkeypatch):
    from app import aws_bootstrap as module
    context = Mock()
    migration = Mock()
    migration.run.side_effect = RuntimeError('synthetic-private-db-error')
    monkeypatch.setattr(module, 'MigrationRunner', Mock(return_value=migration))
    grant = Mock()
    monkeypatch.setattr(module, 'grant_application_roles', grant)
    with pytest.raises(RuntimeError):
        module.execute(context, 'database')
    context.admin_engine.return_value.dispose.assert_called_once()
    grant.assert_not_called()


def test_entrypoint_rejects_local_execution_without_sdk_access(monkeypatch, capsys):
    from app import aws_bootstrap as module
    import boto3
    monkeypatch.delenv('ECONOMICON_BOOTSTRAP', raising=False)
    client = Mock(side_effect=AssertionError('AWS forbidden'))
    monkeypatch.setattr(boto3, 'client', client)
    assert module.main() == 1
    client.assert_not_called()
    assert 'Private application bootstrap failed' in capsys.readouterr().err
