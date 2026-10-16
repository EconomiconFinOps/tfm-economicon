"""Admission and durable lifecycle tests; real MinIO coverage is opt-in integration."""
from datetime import timedelta
import hashlib
from importlib import import_module
import io
import json
import struct
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from app.api.routes.documents import UploadRequest
from app.services.document_storage import InvalidDocument, S3Storage, StorageConfig, StorageUnavailable
from app.services.document_uploads import DocumentUploads, UploadError, utc_timestamp


class MemoryStorage:
    def __init__(self):
        self.config=SimpleNamespace(max_bytes=20_000_000,url_seconds=180,bucket='fixture-private')
        self.objects={}
        self.fail_delete=False

    def presign(self,key,size):
        return 'https://storage.invalid/staging'

    def read(self,key,size,digest):
        raw=self.objects.get(key)
        if raw is None or len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:
            raise InvalidDocument('document_integrity_mismatch')
        return raw

    def finalize(self,key,raw,digest):
        self.objects.setdefault(key,raw)

    def delete(self,key):
        if self.fail_delete:
            raise StorageUnavailable('document_storage_unavailable')
        self.objects.pop(key,None)


class Queue:
    queue_name='fixture:documents'
    def __init__(self):
        self.messages=[]
        self.outcome='confirmed'
    def reserve(self):
        return SimpleNamespace(outcome=None)
    def publish(self,job,**kwargs):
        self.messages.append(job)
        return SimpleNamespace(outcome=self.outcome)
    def cancel(self,reservation):
        pass


@pytest.fixture
def service(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'documents.db'))
    with engine.begin() as connection:
        import_module('app.db.migrations.001_initial').upgrade(connection)
        for statement in import_module('app.db.migrations.006_document_ingestion').schema_steps():
            connection.execute(text(statement))
        for user,tenant in [('one','alpha'),('one','beta'),('two','alpha'),('three','beta')]:
            connection.execute(text('INSERT INTO user_tenants(user_id,tenant_id,role,created_at) VALUES(:user,:tenant,\'member\',:now)'),
                               {'user':user,'tenant':tenant,'now':utc_timestamp()})
    value=DocumentUploads(SimpleNamespace(engine=engine),Queue(),MemoryStorage())
    yield value
    engine.dispose()


def begin(service,*,user='one',tenant='alpha',raw=b'Synthetic cloud budget 42 USD',force=False,filename='budget.txt'):
    request=UploadRequest(filename=filename,file_size=len(raw),content_hash=hashlib.sha256(raw).hexdigest(),force_reprocess=force)
    result=service.begin(tenant,user,request)
    row=service.owned(result['upload_id'],tenant,user)
    service.storage.objects[row['staging_key']]=raw
    return row


def test_user_slot_spans_sessions_and_tenants_but_not_other_users(service):
    begin(service)
    for tenant in ('alpha','beta'):
        with pytest.raises(UploadError,match='user_upload_active'):
            begin(service,tenant=tenant)
    assert begin(service,user='two')['tenant_id']=='alpha'


def test_confirm_checks_owner_tenant_missing_object_and_hash(service):
    row=begin(service)
    for tenant,user in [('beta','one'),('alpha','two')]:
        with pytest.raises(UploadError,match='upload_not_found'):
            service.confirm(row['id'],tenant,user)
    service.storage.objects.pop(row['staging_key'])
    with pytest.raises(UploadError):
        service.confirm(row['id'],'alpha','one')
    service.storage.objects[row['staging_key']]=b'corrupt'
    with pytest.raises(UploadError):
        service.confirm(row['id'],'alpha','one')
    with service.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM jobs')).scalar_one()==0


def test_confirmation_is_idempotent_and_staging_cannot_replace_final(service):
    row=begin(service)
    first=service.confirm(row['id'],'alpha','one')
    service.storage.objects[row['staging_key']]=b'overwritten staging'
    second=service.confirm(row['id'],'alpha','one')
    assert first['job_id']==second['job_id'] and len(service.queue.messages)==1
    assert service.storage.objects[row['final_key']]==b'Synthetic cloud budget 42 USD'
    assert service.queue.messages[0]['payload']['upload_id']==row['id']
    assert 'text_content' not in service.queue.messages[0]['payload']
    assert service.status(row['id'],'alpha','one')['job_status']=='queued'
    assert begin(service)['id']!=row['id']  # Confirm releases only that user's transfer slot.


@pytest.mark.parametrize('compression', [zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA])
def test_corrupt_docx_compression_is_rejected_without_publishing(service, compression):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=compression) as archive:
        archive.writestr('[Content_Types].xml', b'wordprocessingml.document.main+xml')
        archive.writestr('word/document.xml',
                         b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
    raw = bytearray(stream.getvalue())
    offset = 30 + struct.unpack_from('<H', raw, 26)[0] + struct.unpack_from('<H', raw, 28)[0]
    if compression == zipfile.ZIP_DEFLATED:
        raw[offset] |= 6  # Reserved DEFLATE block type, retaining the ZIP headers.
    elif compression == zipfile.ZIP_BZIP2:
        raw[offset] = 0  # Invalid BZip2 signature.
    else:
        raw[offset + 4] = 255  # Invalid LZMA filter properties.
    row = begin(service, raw=bytes(raw), filename='corrupt.docx')
    with pytest.raises(UploadError, match='invalid_docx_document') as caught:
        service.confirm(row['id'], 'alpha', 'one')
    assert caught.value.status == 422
    assert service.status(row['id'], 'alpha', 'one')['job_id'] is None
    assert service.queue.messages == []
    assert row['final_key'] not in service.storage.objects
    with service.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM jobs')).scalar_one() == 0
    service.cancel(row['id'], 'alpha', 'one')


def test_dedup_is_explicit_tenant_scoped_and_force_reprocess_supported(service):
    first=begin(service)
    initial=service.confirm(first['id'],'alpha','one')
    duplicate=begin(service,user='two')
    repeated=service.confirm(duplicate['id'],'alpha','two')
    assert repeated['duplicate'] and repeated['job_id']==initial['job_id']
    independent=begin(service,user='three',tenant='beta')
    other=service.confirm(independent['id'],'beta','three')
    assert not other['duplicate'] and other['job_id']!=initial['job_id']
    deliberate=begin(service,force=True)
    fresh=service.confirm(deliberate['id'],'alpha','one')
    assert not fresh['duplicate'] and fresh['job_id']!=initial['job_id']


def test_outbox_recovers_unknown_publication_without_new_job(service):
    service.queue.outcome='unknown'
    row=begin(service)
    initial=service.confirm(row['id'],'alpha','one')
    assert initial['job_status']=='publish_pending'
    service.queue.outcome='confirmed'
    with service.engine.begin() as connection:
        connection.execute(text('UPDATE document_uploads SET outbox_next=:past'),{'past':utc_timestamp()-timedelta(seconds=30)})
    service.maintain()
    assert service.status(row['id'],'alpha','one')['job_status']=='queued'
    with service.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM jobs')).scalar_one()==1


def test_cleanup_waits_for_success_and_retries_failed_delete(service):
    row=begin(service)
    confirmed=service.confirm(row['id'],'alpha','one')
    service.maintain()
    assert row['final_key'] in service.storage.objects
    with service.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status='completed' WHERE id=:id"),{'id':confirmed['job_id']})
        connection.execute(text('UPDATE document_uploads SET expires_at=:past'),{'past':utc_timestamp()-timedelta(seconds=1)})
    service.storage.fail_delete=True
    service.maintain()  # A failed deletion stays pending without stopping the sweep.
    assert not service.owned(row['id'],'alpha','one')['cleanup_done']
    service.storage.fail_delete=False
    service.maintain()
    assert row['final_key'] not in service.storage.objects and row['staging_key'] not in service.storage.objects
    assert service.owned(row['id'],'alpha','one')['cleanup_done']
    service.maintain()  # Idempotent.


def test_failed_job_keeps_original_until_retry_is_terminal(service):
    row=begin(service)
    service.confirm(row['id'],'alpha','one')
    with service.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status='failed',updated_at=:past"),{'past':utc_timestamp()-timedelta(days=8)})
    service.maintain()
    assert row['final_key'] in service.storage.objects
    with service.engine.begin() as connection:
        connection.execute(text('UPDATE document_uploads SET terminal_failure=true,expires_at=:past'),{'past':utc_timestamp()-timedelta(days=8)})
    service.maintain()
    assert row['final_key'] not in service.storage.objects


def test_abandoned_upload_expires_without_affecting_other_users(service):
    first=begin(service)
    other=begin(service,user='two')
    with service.engine.begin() as connection:
        connection.execute(text('UPDATE document_uploads SET expires_at=:past WHERE id=:id'),{'past':utc_timestamp()-timedelta(seconds=1),'id':first['id']})
        connection.execute(text('UPDATE document_upload_slots SET expires_at=:past WHERE user_id=\'one\''),{'past':utc_timestamp()-timedelta(seconds=1)})
    service.maintain()
    assert first['staging_key'] not in service.storage.objects
    assert other['staging_key'] in service.storage.objects
    assert begin(service)['id']!=first['id']


def test_actual_storage_reader_bounds_size_and_validates_hash():
    config=StorageConfig('fixture-private','http://internal.invalid','http://browser.invalid','us-east-1','synthetic','synthetic')
    reader=S3Storage.__new__(S3Storage)
    reader.config=config
    data=b'synthetic bytes'
    class Internal:
        def get_object(self,**kwargs):
            return {'ContentLength':len(data),'Body':io.BytesIO(data)}
    reader.internal=Internal()
    assert reader.read('server-key',len(data),hashlib.sha256(data).hexdigest())==data
    with pytest.raises(InvalidDocument):
        reader.read('server-key',len(data),'0'*64)
    with pytest.raises(InvalidDocument):
        reader.read('server-key',len(data)+1,hashlib.sha256(data).hexdigest())


@pytest.mark.parametrize('size',[0,20_000_001])
def test_declared_size_limit_creates_no_upload(service,size):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UploadRequest(filename='file.txt',file_size=size,content_hash='0'*64)


def test_exact_size_boundary_is_admitted_by_request_contract():
    assert UploadRequest(filename='file.txt',file_size=20_000_000,content_hash='0'*64).file_size==20_000_000


def test_membership_revoked_during_s3_verification_creates_no_processable_job(service):
    row=begin(service)
    original=service.storage.finalize
    def revoke(*args):
        original(*args)
        with service.engine.begin() as c: c.execute(text("DELETE FROM user_tenants WHERE user_id='one' AND tenant_id='alpha'"))
    service.storage.finalize=revoke
    with pytest.raises(UploadError,match='upload_not_found'): service.confirm(row['id'],'alpha','one')
    with service.engine.connect() as c: assert c.execute(text('SELECT count(*) FROM jobs')).scalar_one()==0


def test_retry_status_and_duplicate_use_the_original_jobs_terminal_state(service):
    row=begin(service); accepted=service.confirm(row['id'],'alpha','one')
    with service.engine.begin() as c: c.execute(text("UPDATE jobs SET status='failed'"))
    assert service.status(row['id'],'alpha','one')['retry_pending']
    duplicate=begin(service,user='two'); status=service.confirm(duplicate['id'],'alpha','two')
    assert status['duplicate'] and status['retry_pending'] and status['job_id']==accepted['job_id']
    with service.engine.begin() as c: c.execute(text('UPDATE document_uploads SET terminal_failure=true WHERE id=:id'),{'id':row['id']})
    assert not service.status(duplicate['id'],'alpha','two')['retry_pending']


def test_failed_cleanup_does_not_starve_other_completed_upload(service):
    first=begin(service); service.confirm(first['id'],'alpha','one')
    second=begin(service,user='two',raw=b'Independent budget 73 USD'); service.confirm(second['id'],'alpha','two')
    with service.engine.begin() as c:
        c.execute(text("UPDATE jobs SET status='completed'"))
        c.execute(text('UPDATE document_uploads SET expires_at=:past'),{'past':utc_timestamp()-timedelta(seconds=1)})
    original=service.storage.delete
    def delete(key):
        if key==first['final_key']: raise StorageUnavailable('synthetic failure')
        return original(key)
    service.storage.delete=delete; service.maintain()
    assert not service.owned(first['id'],'alpha','one')['cleanup_done']
    assert service.owned(second['id'],'alpha','two')['cleanup_done']


def test_sweep_preserves_published_checkpoint_and_active_parts(service):
    from app.services.document_checkpoint import load_checkpoint, save_checkpoint
    row=begin(service); accepted=service.confirm(row['id'],'alpha','one'); job=accepted['job_id']
    document={'schema_version':1,'text':'Cloud budget42 USD '*20_000,'blocks':[]}
    save_checkpoint(service.engine,job,'alpha',document)
    with service.engine.begin() as c:
        c.execute(text("INSERT INTO extracted_document_parts VALUES(:job,'alpha','abandoned-generation',0,'unfinished')"),{'job':job})
    service.maintain()
    with service.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM extracted_document_parts WHERE generation='abandoned-generation'")).scalar_one()==1
    with service.engine.begin() as c: c.execute(text("UPDATE jobs SET status='completed'"))
    service.maintain()
    with service.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM extracted_document_parts WHERE generation='abandoned-generation'")).scalar_one()==0
        assert load_checkpoint(c,job,'alpha')==document


def test_incompatible_partial_document_schema_is_rejected(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'partial.db'))
    migration=import_module('app.db.migrations.006_document_ingestion')
    with engine.begin() as c:
        c.execute(text('CREATE TABLE document_uploads(id STRING PRIMARY KEY)'))
        for statement in migration.schema_steps(): c.execute(text(statement))
        with pytest.raises(RuntimeError,match='schema is incomplete'): migration.verify(c)
    engine.dispose()


def test_shared_admission_storage_and_checkpoint_contracts_remain_identical():
    root=Path(__file__).resolve().parents[3]
    for name in ('document_storage.py','document_formats.py','document_checkpoint.py'):
        assert (root/'apps/backend/app/services'/name).read_bytes()==(root/'apps/processor/app/documents'/name).read_bytes()
    config=StorageConfig('private','http://internal.invalid','http://browser.invalid','us-east-1','sensitive-access','sensitive-secret')
    assert 'sensitive-access' not in repr(config) and 'sensitive-secret' not in repr(config)
