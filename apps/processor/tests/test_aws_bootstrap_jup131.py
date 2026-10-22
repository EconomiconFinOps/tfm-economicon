from unittest.mock import Mock

import pytest


def test_processor_prepares_operational_then_vector_schema(monkeypatch):
    from app import aws_bootstrap as module
    engines = {'operational': Mock(), 'vectors': Mock()}
    context = Mock()
    context.inputs = {'embedding': {'dimension': 1024}}
    context.admin_engine.side_effect = lambda database: engines[database]
    events = []
    def runner(engine, package, directory, **options):
        value = Mock()
        value.run.side_effect = lambda: events.append(package)
        return value
    monkeypatch.setattr(module, 'MigrationRunner', runner)
    monkeypatch.setattr(module, 'grant_application_roles', lambda *args: events.append('grant'))
    module.execute(context, 'database')
    assert events == ['app.db.migrations', 'grant', 'app.vector_store.migrations', 'grant']
    assert all(engine.dispose.call_count == 1 for engine in engines.values())


def test_invalid_dimension_does_not_open_database(monkeypatch):
    from app import aws_bootstrap as module
    context = Mock()
    context.inputs = {'embedding': {'dimension': 1536}}
    with pytest.raises(RuntimeError):
        module.execute(context, 'database')
    context.admin_engine.assert_not_called()


def test_local_entrypoint_does_not_construct_sdk_clients(monkeypatch):
    from app import aws_bootstrap as module
    import boto3
    monkeypatch.delenv('ECONOMICON_BOOTSTRAP', raising=False)
    client = Mock(side_effect=AssertionError('AWS forbidden'))
    monkeypatch.setattr(boto3, 'client', client)
    assert module.main() == 1
    client.assert_not_called()


def test_fixture_phase_keeps_costs_before_native_corpus_and_closes_engines(monkeypatch):
    from app import aws_bootstrap as module
    from app import aws_bootstrap_fixtures as fixtures
    from app.embeddings import providers
    from app.vector_store import pgvector_store
    context = Mock()
    context.inputs = {'embedding': {'dimension': 1024}, 'region': 'eu-west-1'}
    engines = {'operational': Mock(), 'vectors': Mock()}
    context.admin_engine.side_effect = lambda database: engines[database]
    events = []
    monkeypatch.setattr(fixtures, 'seed_costs', lambda *args: events.append('costs'))
    monkeypatch.setattr(fixtures, 'seed_corpus', lambda *args: events.append('corpus'))
    monkeypatch.setattr(providers, 'BedrockEmbeddingProvider', Mock())
    store = Mock()
    monkeypatch.setattr(pgvector_store, 'PgVectorStore', Mock(return_value=store))
    module.execute(context, 'fixtures')
    assert events == ['costs', 'corpus']
    store.initialize.assert_called_once()
    assert all(engine.dispose.call_count == 1 for engine in engines.values())
