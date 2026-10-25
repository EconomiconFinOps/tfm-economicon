import json
from types import SimpleNamespace
import pytest
from sqlalchemy import text
from app.db.database import Database
from app.documents.document_checkpoint import save_checkpoint
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.normalized import manual_document
from app.embeddings.structural_chunker import StructuredChunker
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.reprocess import DocumentReprocessor, UnsupportedReprocessing
from test_document_checkpoint import case


class Store:
    def __init__(self):
        self.marker='previous'; self.saved=None
    def publication(self,*_): return self.marker
    def store_document(self,**kwargs):
        assert kwargs['expected_publication']==self.marker
        self.saved=kwargs
        return {'document_id':kwargs['job_id'],'chunk_count':len(kwargs['chunks'])}


class Provider:
    name='mock'
    def __init__(self): self.calls=[]
    def embed(self,value): self.calls.append(value); return [1.0,0.0]


def setup(case,monkeypatch,checkpoint=True):
    engine,storage,stored,_=case
    with engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status='completed'"))
    document=manual_document({'job_id':stored['id'],'tenant_id':stored['tenant_id'],
        'source':stored['source'],'text_content':'# A\n\nRetained normalized evidence.'})
    document['original_format']='md'
    if checkpoint: save_checkpoint(engine,stored['id'],stored['tenant_id'],document)
    monkeypatch.setattr('app.documents.document_processor.extract_local',lambda *_:pytest.fail('Reprocessing must not reextract'))
    storage.read=lambda *_:pytest.fail('Original is unavailable after successful ingestion')
    database=Database.__new__(Database); database.engine=engine
    provider,store=Provider(),Store()
    operation=DocumentReprocessor(JobRepository(database),engine,StructuredChunker(),provider,store)
    scope={'document_id':stored['id'],'tenant_id':stored['tenant_id'],'created_by':stored['created_by']}
    return operation,scope,provider,store,document


def test_explicit_reprocess_reads_checkpoint_without_original_and_keeps_job_completed(case,monkeypatch):
    operation,scope,provider,store,document=setup(case,monkeypatch)
    result=operation.execute(**scope)
    assert result['document_id']==document['document_id'] and result['job_status']=='completed'
    assert provider.calls==[chunk['content'] for chunk in store.saved['chunks']]
    assert store.saved['document_metadata']['original_format']=='md'
    with case[0].connect() as connection:
        assert connection.execute(text('SELECT status FROM jobs')).scalar_one()=='completed'


def test_legacy_without_checkpoint_remains_untouched(case,monkeypatch):
    operation,scope,provider,store,_=setup(case,monkeypatch,False)
    with pytest.raises(UnsupportedReprocessing,match='checkpoint is absent'): operation.execute(**scope)
    assert not provider.calls and store.saved is None and store.marker=='previous'


@pytest.mark.parametrize('changed',[{'tenant_id':'foreign'},{'created_by':'foreign'}])
def test_reprocess_requires_existing_job_owner_and_tenant(case,monkeypatch,changed):
    operation,scope,provider,store,_=setup(case,monkeypatch)
    with pytest.raises(PermissionError): operation.execute(**{**scope,**changed})
    assert not provider.calls and store.saved is None


def test_provider_failure_never_replaces_existing_version(case,monkeypatch):
    operation,scope,provider,store,_=setup(case,monkeypatch)
    def fail(_): raise RuntimeError('synthetic provider failure')
    provider.embed=fail
    with pytest.raises(RuntimeError,match='synthetic'): operation.execute(**scope)
    assert store.saved is None and store.marker=='previous'


def test_non_completed_job_cannot_reprocess(case,monkeypatch):
    operation,scope,provider,store,_=setup(case,monkeypatch)
    with case[0].begin() as connection: connection.execute(text("UPDATE jobs SET status='running'"))
    with pytest.raises(UnsupportedReprocessing,match='completed'): operation.execute(**scope)
    assert not provider.calls and store.saved is None


def test_reprocess_needs_an_existing_vector_document(case, monkeypatch):
    operation, scope, provider, store, _ = setup(case, monkeypatch)
    store.publication = lambda *_: None
    with pytest.raises(UnsupportedReprocessing, match='No existing vector document'):
        operation.execute(**scope)
    assert not provider.calls and store.saved is None


def test_reprocess_rechecks_authority_after_the_slow_embedding_calls(case, monkeypatch):
    operation, scope, provider, store, _ = setup(case, monkeypatch)
    original = provider.embed
    def embed_and_lose_authority(value):
        with case[0].begin() as connection:
            connection.execute(text("UPDATE jobs SET status='running'"))
        return original(value)
    provider.embed = embed_and_lose_authority
    with pytest.raises(PermissionError):
        operation.execute(**scope)
    assert store.saved is None and store.marker == 'previous'


def test_structured_pipeline_embeds_only_content_and_accepts_manual_input():
    store,provider=Store(),Provider()
    agent=SimpleNamespace(invoke=lambda *_args,**_kwargs:{'provider':'mock'})
    result=PipelineRunner(agent,StructuredChunker(),provider,store).run({
        'job_id':'manual','tenant_id':'tenant','source':' Manual ','text_content':'Useful text.'})
    assert provider.calls==['Useful text.']
    assert result['normalized_document']['original_format']=='manual-text'
    assert store.saved['document_metadata']['chunking']['chunk_count']==1


def test_structured_pipeline_rejects_foreign_checkpoint_before_provider():
    store,provider=Store(),Provider()
    payload={'job_id':'manual','tenant_id':'tenant','source':'manual','text_content':'Useful text.'}
    document=manual_document(payload); document['tenant_id']='foreign'
    runner=PipelineRunner(SimpleNamespace(invoke=lambda *_:None),StructuredChunker(),provider,store)
    with pytest.raises(ValueError,match='identity'): runner.run({**payload,'normalized_document':document})
    assert not provider.calls and store.saved is None


def test_token_configuration_is_configurable_from_environment(monkeypatch):
    from app.core.config import Settings
    monkeypatch.setenv('EMBEDDING_CHUNK_TARGET_TOKENS','48')
    monkeypatch.setenv('EMBEDDING_CHUNK_MAX_TOKENS','64')
    monkeypatch.setenv('EMBEDDING_CHUNK_OVERLAP_RATIO','0.2')
    settings=Settings()
    assert settings.embedding_chunk_target_tokens==48 and settings.embedding_chunk_overlap_ratio==0.2


@pytest.mark.parametrize('options',[{'embedding_chunk_target_tokens':801},
    {'embedding_chunk_target_tokens':64,'embedding_chunk_max_tokens':48},
    {'embedding_chunk_overlap_ratio':float('nan')},{'embedding_chunk_overlap_ratio':1}])
def test_invalid_token_configuration_fails_startup(options):
    from app.core.config import Settings
    with pytest.raises(ValueError): Settings(**options)
