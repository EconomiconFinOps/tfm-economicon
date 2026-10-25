"""Opt-in real PostgreSQL checks for coherent replacement, rollback and concurrent CAS."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.normalized import manual_document, parent_metadata
from app.embeddings.providers import MockEmbeddingProvider
from app.embeddings.structural_chunker import StructuredChunker
from app.vector_store.pgvector_store import StalePublication
from test_tenant_isolation_vector import vector_store


def prepare(value,config=None):
    document=manual_document({'job_id':'fixed-document','tenant_id':'tenant-a','source':'synthetic','text_content':value})
    result=StructuredChunker(config).chunk_document(document)
    return {'job_id':document['document_id'],'tenant_id':document['tenant_id'],'source':'synthetic','artifact_uri':None,
            'text_content':value,'chunks':result['chunks'],
            'embeddings':[MockEmbeddingProvider(8).embed(chunk['content']) for chunk in result['chunks']],
            'provider_name':'mock','document_metadata':parent_metadata(document,result['manifest'])}


def rows(store):
    with store.engine.connect() as connection:
        return connection.execute(text('SELECT dc.id,dc.content,dc.metadata AS chunk_metadata,ce.embedding::text,kd.metadata AS parent_metadata FROM document_chunks dc JOIN knowledge_documents kd ON kd.id=dc.document_id JOIN chunk_embeddings ce ON ce.chunk_id=dc.id ORDER BY dc.chunk_index')).all()


def test_replacement_has_only_new_generation_with_stable_deterministic_ids(vector_store):
    old=prepare('Useful paragraph. '*150,ChunkingConfig(32,48,0.1))
    first=vector_store.store_document(**old,expected_publication=None)
    original_ids=[row.id for row in rows(vector_store)]
    new=prepare(old['text_content'],ChunkingConfig(48,64,0.1))
    vector_store.store_document(**new,expected_publication=first['publication_id'])
    actual=rows(vector_store)
    assert [row.id for row in actual]==[row['chunk_id'] for row in new['chunks']]
    assert set(original_ids).isdisjoint(row.id for row in actual)
    assert len({row.chunk_metadata['chunking_fingerprint'] for row in actual})==1
    assert len(actual)==len(new['embeddings'])


def test_sql_failure_after_delete_rolls_back_parent_chunks_and_vectors(vector_store):
    original=vector_store.store_document(**prepare('Original evidence.'),expected_publication=None)
    before=rows(vector_store)
    with vector_store.engine.begin() as connection:
        connection.execute(text("ALTER TABLE document_chunks ADD CONSTRAINT injected_failure CHECK(content NOT LIKE '%FORCED_FAILURE%')"))
    with pytest.raises(IntegrityError):
        vector_store.store_document(**prepare('FORCED_FAILURE'),expected_publication=original['publication_id'])
    assert rows(vector_store)==before
    assert vector_store.publication('fixed-document','tenant-a')==original['publication_id']


def test_concurrent_operations_cannot_overwrite_each_other_after_preparation(vector_store):
    original=vector_store.store_document(**prepare('Original evidence.'),expected_publication=None)
    barrier=Barrier(2)
    def publish(value):
        candidate=prepare(value)
        barrier.wait(timeout=10)
        try:
            return vector_store.store_document(**candidate,expected_publication=original['publication_id'])
        except StalePublication:
            return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes=list(executor.map(publish,['First new evidence.','Second new evidence.']))
    assert sum(value is not None for value in outcomes)==1
    actual=rows(vector_store)
    assert len(actual)==1 and actual[0].content in {'First new evidence.','Second new evidence.'}


def test_simultaneous_first_publications_only_one_wins(vector_store):
    barrier=Barrier(2)
    def publish(value):
        candidate=prepare(value); barrier.wait(timeout=10)
        try: return vector_store.store_document(**candidate,expected_publication=None)
        except StalePublication: return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes=list(executor.map(publish,['First.','Second.']))
    assert sum(value is not None for value in outcomes)==1
    assert len(rows(vector_store))==1


def test_new_metadata_does_not_change_legacy_content_ids_or_vectors(vector_store):
    vector_store.store_document(job_id='legacy',tenant_id='tenant-a',source='synthetic',artifact_uri=None,
        text_content='Legacy evidence',chunks=['Legacy evidence'],embeddings=[[1.0]+[0.0]*7],provider_name='mock')
    [row]=rows(vector_store)
    assert row.id=='legacy:chunk:0' and row.content=='Legacy evidence' and row.chunk_metadata=={}


def test_wrong_tenant_cannot_read_or_replace_publication(vector_store):
    first=vector_store.store_document(**prepare('Tenant evidence.'),expected_publication=None)
    before=rows(vector_store)
    with pytest.raises(PermissionError): vector_store.publication('fixed-document','foreign')
    candidate=prepare('Foreign evidence.'); candidate['tenant_id']='foreign'
    with pytest.raises(PermissionError): vector_store.store_document(**candidate,expected_publication=first['publication_id'])
    assert rows(vector_store)==before
