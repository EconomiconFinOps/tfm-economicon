"""Durable extraction and execution claims independent of the inference pipeline."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy import create_engine, text
from app.documents.document_processor import DocumentProcessor
from app.documents.document_checkpoint import load_checkpoint, save_checkpoint
from app.db.database import Database
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask


@pytest.fixture
def case(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'checkpoint.db'))
    path=Path(__file__).resolve().parents[2]/'backend/app/db/migrations/006_document_ingestion.py'
    spec=importlib.util.spec_from_file_location('document_schema_fixture',path)
    migration=importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    initial_spec=importlib.util.spec_from_file_location('initial_schema_fixture',path.with_name('001_initial.py'))
    initial=importlib.util.module_from_spec(initial_spec); initial_spec.loader.exec_module(initial)
    data=b'Cloud budget 42 USD'
    job,upload=str(uuid.uuid4()),str(uuid.uuid4())
    final=f'confirmed/tenant/user/{upload}'
    now=datetime.now(timezone.utc)
    with engine.begin() as c:
        initial.upgrade(c)
        for sql in migration.schema_steps(): c.execute(text(sql))
        c.execute(text("INSERT INTO users VALUES('user','fixture@example.com','unused','Fixture','member',:now)"),{'now':now})
        c.execute(text("INSERT INTO user_tenants VALUES('user','tenant','member',:now)"),{'now':now})
        c.execute(text('''INSERT INTO document_uploads(id,tenant_id,user_id,filename,format,expected_size,content_hash,
            source,staging_key,final_key,status,job_id,force_reprocess,created_at,expires_at,outbox_sent,outbox_next,cleanup_done,terminal_failure)
            VALUES(:upload,'tenant','user','budget.txt','txt',:size,:hash,'document','staging/fixture',:final,'confirmed',:job,
            false,:now,:expiry,true,:now,false,false)'''),{'upload':upload,'size':len(data),'hash':hashlib.sha256(data).hexdigest(),
            'final':final,'job':job,'now':now,'expiry':now+timedelta(minutes=3)})
    storage=SimpleNamespace(config=SimpleNamespace(bucket='fixture'),read=lambda *_:data,delete=lambda *_:None)
    stored={'id':job,'tenant_id':'tenant','created_by':'user','source':'document','artifact_uri':'s3://fixture/'+final}
    stored['payload']={'tenant_id':'tenant','source':'document','artifact_uri':stored['artifact_uri'],'upload_id':upload,'metadata':{}}
    with engine.begin() as c:
        c.execute(text('''INSERT INTO jobs(id,tenant_id,created_by,source,artifact_uri,payload,status,result,created_at,updated_at)
            VALUES(:id,:tenant_id,:created_by,:source,:artifact_uri,:payload,'queued',NULL,:now,:now)'''),
            {**stored,'payload':json.dumps(stored['payload']),'now':now})
    yield engine,storage,stored,{'upload_id':upload}
    engine.dispose()


def test_claim_excludes_second_worker_and_lost_owner_cannot_complete_or_release_other(case):
    engine,storage,stored,payload=case
    first,second=DocumentProcessor(engine,storage),DocumentProcessor(engine,storage)
    first.claim(stored,payload)
    try:
        with pytest.raises(RuntimeError,match='execution_busy'): second.claim(stored,payload)
        with engine.begin() as c:
            c.execute(text('UPDATE document_execution_claims SET expires_at=:past'),{'past':datetime.now(timezone.utc)-timedelta(seconds=1)})
        second.claim(stored,payload)
        with pytest.raises(RuntimeError,match='lease_lost'): first.assert_owned(stored,payload)
        first.release(stored)
        second.assert_owned(stored,payload)
    finally:
        first.release(stored); second.release(stored)


def test_durable_checkpoint_reused_after_new_worker_without_read_or_reextract(case,monkeypatch):
    engine,storage,stored,payload=case
    extracted={'text':'Cloud budget 42 USD','blocks':[{'kind':'text','text':'Cloud budget 42 USD'}],
               'file_metadata':{},'warnings':[],'extraction_method':'fixture','result':'extracted'}
    calls=[]
    monkeypatch.setattr('app.documents.document_processor.extract_local',lambda *_:calls.append(True) or extracted)
    first=DocumentProcessor(engine,storage); first.claim(stored,payload)
    document=first.prepare(stored,payload); first.release(stored)
    storage.read=lambda *_:pytest.fail('Checkpoint reuse must not download the original')
    monkeypatch.setattr('app.documents.document_processor.extract_local',lambda *_:pytest.fail('Must not reextract'))
    second=DocumentProcessor(engine,storage); second.claim(stored,payload)
    try:
        assert second.prepare(stored,payload)==document
        assert len(calls)==1 and document['tenant_id']=='tenant' and document['schema_version']==1
        foreign={**stored,'tenant_id':'another-tenant'}
        with pytest.raises(RuntimeError,match='lease_lost'): second.prepare(foreign,payload)
    finally: second.release(stored)


def test_manual_text_uses_same_versioned_contract_without_file_claim(case):
    engine,storage,stored,_=case
    processor=DocumentProcessor(engine,storage)
    document=processor.prepare(stored,{'text_content':'Manual cloud budget 42 USD'})
    assert document['original_format']=='manual-text' and document['extraction_method']=='manual-text'
    assert document['text']=='Manual cloud budget 42 USD' and document['blocks']==[]
    with engine.connect() as c:
        assert json.loads(c.execute(text('SELECT document FROM extracted_documents')).scalar_one())==document


def test_large_unicode_checkpoint_roundtrips_bounded_parts_and_rejects_missing_part(case):
    engine,_,stored,_=case
    document={'schema_version':1,'tenant_id':'tenant','text':'Presupuesto € 漢字 🙂\n'*40_000,'blocks':[]}
    save_checkpoint(engine,stored['id'],'tenant',document)
    with engine.connect() as c:
        assert load_checkpoint(c,stored['id'],'tenant')==document
        assert load_checkpoint(c,stored['id'],'foreign') is None
        parts=c.execute(text('SELECT content FROM extracted_document_parts')).scalars().all()
        assert len(parts)>1 and all(len(part.encode('utf-8'))<=256_000 for part in parts)
    with engine.begin() as c: c.execute(text('DELETE FROM extracted_document_parts WHERE part_index=1'))
    with engine.connect() as c:
        with pytest.raises(RuntimeError,match='checkpoint_incomplete'): load_checkpoint(c,stored['id'],'tenant')


def test_interrupted_large_write_never_replaces_previous_published_checkpoint(case,monkeypatch):
    from sqlalchemy import event
    engine,_,stored,_=case
    previous={'schema_version':1,'tenant_id':'tenant','text':'Previous usable document','blocks':[]}
    save_checkpoint(engine,stored['id'],'tenant',previous)
    def interrupt(_connection,_cursor,sql,_parameters,_context,_many):
        if sql.startswith('INSERT INTO extracted_documents'): raise RuntimeError('synthetic publication interruption')
    event.listen(engine,'before_cursor_execute',interrupt)
    try:
        with pytest.raises(RuntimeError,match='synthetic publication interruption'):
            save_checkpoint(engine,stored['id'],'tenant',{**previous,'text':'budget € '*80_000})
    finally: event.remove(engine,'before_cursor_execute',interrupt)
    with engine.connect() as c: assert load_checkpoint(c,stored['id'],'tenant')==previous


def test_file_completion_keeps_large_content_out_of_job_result_and_redelivery_reuses_it(case,monkeypatch):
    engine,storage,stored,payload=case
    value='Cloud budget 42 USD '*30_000
    monkeypatch.setattr('app.documents.document_processor.extract_local',lambda *_:{'text':value,'blocks':[],
        'file_metadata':{},'warnings':[],'extraction_method':'fixture','result':'extracted'})
    calls=[]
    def pipeline(data):
        calls.append(data)
        return {**data,'chunks':[value],'summary':'Completed fixture','embedding_result':{'chunk_count':1}}
    database=Database.__new__(Database); database.engine=engine
    task=IngestTask(JobRepository(database),SimpleNamespace(run=pipeline),DocumentProcessor(engine,storage))
    result=task.execute(stored)
    assert 'text_content' not in result and 'chunks' not in result and result['document_id']==stored['id']
    assert calls[0]['text_content']==value
    with engine.connect() as c:
        status,saved=c.execute(text('SELECT status,result FROM jobs')).one()
        assert status=='completed' and len(saved)<2000 and json.loads(saved)==result
        assert load_checkpoint(c,stored['id'],'tenant')['text']==value
    assert task.execute(stored)==result and len(calls)==1


def test_completion_sql_rejects_wrong_or_expired_owner_atomically(case):
    engine,storage,stored,payload=case
    processor=DocumentProcessor(engine,storage); processor.claim(stored,payload)
    database=Database.__new__(Database); database.engine=engine
    scope={'tenant_id':'tenant','created_by':'user'}
    try:
        with pytest.raises(PermissionError): database.update_job_status(stored['id'],'completed',{},document_owner='wrong',**scope)
        with engine.begin() as c:
            c.execute(text('UPDATE document_execution_claims SET expires_at=:past'),{'past':datetime.now(timezone.utc)-timedelta(seconds=1)})
        with pytest.raises(PermissionError): database.update_job_status(stored['id'],'completed',{},document_owner=processor.owner,**scope)
        with engine.connect() as c: assert c.execute(text('SELECT status FROM jobs')).scalar_one()=='queued'
    finally: processor.release(stored)
