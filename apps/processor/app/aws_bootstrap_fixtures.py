"""Versioned synthetic costs and native-vector corpus for a disposable cycle."""
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from sqlalchemy import text

from app.aws_bootstrap_common import require
from app.core.bedrock import TITAN_MODEL, embedding_fingerprint
from app.embeddings.context import prepare_embedding
from app.embeddings.space import EmbeddingSpace, canonical
from app.embeddings.tokenization import EmbeddingTokenCounter
from app.vector_store.generations import GenerationStore


def load_fixture():
    path = Path(__file__).parent / 'resources/rehearsal-v1.json'
    require(path.stat().st_size <= 16384)
    value = json.loads(path.read_text(encoding='utf-8'))
    require(value['version'] == 'aws-defense-v1' and value['synthetic'] is True)
    require([item['tenant_id'] for item in value['tenants']] == ['tenant-core', 'tenant-growth'])
    return value


def _identity(config, fixture):
    require(re.fullmatch(r'(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})', config['cycle_id'])
            and re.fullmatch(r'[a-f0-9]{40}', config['source_sha']))
    return {'synthetic': True, 'fixture': fixture['version'], 'cycle_id': config['cycle_id'],
            'source_sha': config['source_sha'], 'fixture_sha256': hashlib.sha256(canonical(fixture).encode()).hexdigest()}


def seed_costs(engine, config, fixture):
    identity = _identity(config, fixture)
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        for item in fixture['tenants']:
            identifier = item['document_id'] + '-cost'
            request = dict(identity)
            expected_run = {'tenant_id': item['tenant_id'], 'subscription_id': item['subscription_id'],
                            'request': request, 'status': 'completed', 'row_count': 1}
            current = connection.execute(text('''SELECT tenant_id,subscription_id,request,status,row_count
                FROM azure_cost_ingestion_runs WHERE id=:id'''), {'id': identifier}).mappings().first()
            require(current is None or dict(current) == expected_run)
            connection.execute(text('''INSERT INTO azure_cost_ingestion_runs
                (id,tenant_id,subscription_id,request,status,row_count,page_count,started_at,completed_at)
                VALUES(:id,:tenant_id,:subscription_id,CAST(:request AS jsonb),'completed',1,1,:now,:now)
                ON CONFLICT DO NOTHING'''), dict(expected_run, id=identifier, request=canonical(request), now=now))
            expected = {'id': identifier, 'ingestion_id': identifier, 'tenant_id': item['tenant_id'],
                        'subscription_id': item['subscription_id'], 'usage_date': date.fromisoformat(fixture['period']['start_date']),
                        'pretax_cost': Decimal(item['cost_eur']), 'currency': 'EUR',
                        'dimensions': {'synthetic': True}, 'service_name': item['service_name'],
                        'source_row_hash': hashlib.sha256(canonical(item).encode()).hexdigest()}
            columns = ','.join(expected)
            current_rows = connection.execute(text('SELECT ' + columns + ' FROM azure_cost_records WHERE id=:id OR ingestion_id=:id'),
                                              {'id': identifier}).mappings().all()
            require(not current_rows or len(current_rows) == 1 and dict(current_rows[0]) == expected)
            connection.execute(text('''INSERT INTO azure_cost_records
                (id,ingestion_id,tenant_id,subscription_id,usage_date,pretax_cost,currency,dimensions,source_row_hash,created_at,service_name)
                VALUES(:id,:ingestion_id,:tenant_id,:subscription_id,:usage_date,:pretax_cost,:currency,CAST(:dimensions AS jsonb),:source_row_hash,:now,:service_name)
                ON CONFLICT DO NOTHING'''), dict(expected, dimensions=canonical(expected['dimensions']), now=now))


def seed_corpus(store, config, fixture, provider):
    identity = _identity(config, fixture)
    dimension = config['embedding']['dimension']
    require(config['region'] == 'eu-west-1' and dimension == 1024
            and provider.name == 'bedrock' and provider.model == TITAN_MODEL and provider.dimension == dimension
            and provider.mapping_sha256 == embedding_fingerprint('eu-west-1', dimension)
            and store.embedding_dimension == dimension)
    counter = EmbeddingTokenCounter()
    space = EmbeddingSpace('bedrock', TITAN_MODEL, provider.mapping_sha256, counter.identity, dimension=dimension)
    generations = GenerationStore(store.engine, counter)
    source = 'synthetic:' + ':'.join(identity[key] for key in ('fixture', 'cycle_id', 'source_sha', 'fixture_sha256'))
    # Inspect all existing owned IDs before inference or modifying the corpus.
    existing = {}
    with store.engine.connect() as connection:
        for item in fixture['tenants']:
            row = connection.execute(text('SELECT tenant_id,job_id,source,text_content,chunk_count FROM knowledge_documents WHERE id=:id'),
                                     {'id': item['document_id']}).mappings().first()
            if row is not None:
                require(dict(row) == {'tenant_id': item['tenant_id'], 'job_id': item['document_id'], 'source': source,
                                     'text_content': item['text'], 'chunk_count': 1})
                chunks = connection.execute(text('''SELECT c.content,e.provider,e.dimension FROM document_chunks c
                    JOIN chunk_embeddings e ON e.chunk_id=c.id WHERE c.document_id=:id'''), {'id': item['document_id']}).all()
                require(chunks == [(item['text'], 'bedrock', dimension)])
            plan = generations.active_plan(item['tenant_id'])
            require(plan.get('generation_id') is None or row is not None and plan['descriptor'] == space.descriptor())
            existing[item['document_id']] = row is not None
    result = {}
    for item in fixture['tenants']:
        tenant = item['tenant_id']
        if not existing[item['document_id']]:
            prepared = prepare_embedding({'content': item['text']}, {}, space, counter)
            vector = generations.cache_embeddings(tenant, space, [prepared], provider)[prepared.text_hash]
            store.store_document(job_id=item['document_id'], tenant_id=tenant, source=source, artifact_uri=None,
                                 text_content=item['text'], chunks=[item['text']], embeddings=[vector], provider_name='bedrock',
                                 expected_publication=None)
        plan = generations.active_plan(tenant)
        if plan.get('generation_id') is None:
            generation = generations.build(tenant, space, provider)
            plan = generations.activate(tenant, generation, expected_head=None, expected_version=plan['version'])
        require(plan['descriptor'] == space.descriptor())
        result[tenant] = plan['generation_id']
    return result
