"""Durable upload admission, immutable finalization and file-only outbox recovery."""
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import uuid

from sqlalchemy import exc, text

from app.services.document_formats import FormatError, filename_format, validate_format
from app.services.document_storage import InvalidDocument
from app.services.document_checkpoint import load_checkpoint

logger = logging.getLogger(__name__)


class UploadError(ValueError):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)


def utc_timestamp():
    return datetime.now(timezone.utc)


def as_utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def json_value(value):
    return json.loads(value) if isinstance(value, str) else value


class DocumentUploads:
    def __init__(self, database, queue, storage):
        self.database, self.engine, self.queue, self.storage = database, database.engine, queue, storage
        self.failed_retention_days = int(os.getenv('DOCUMENT_FAILED_RETENTION_DAYS', '7'))
        if not 1 <= self.failed_retention_days <= 90:
            raise ValueError('Invalid failed document retention')

    def transaction(self, operation):
        for attempt in range(4):
            try:
                with self.engine.begin() as connection:
                    return operation(connection)
            except (exc.OperationalError, exc.IntegrityError) as error:
                state = getattr(error.orig, 'sqlstate', None)
                if state not in {'40001', '23505'} or attempt == 3:
                    raise
        raise UploadError('upload_conflict')

    def begin(self, tenant, user, request):
        try:
            extension = filename_format(request.filename)
        except FormatError as error:
            raise UploadError(str(error), 422) from None
        if not 0 < request.file_size <= self.storage.config.max_bytes:
            raise UploadError('document_size_limit', 413)
        now = utc_timestamp()
        upload_id = str(uuid.uuid4())
        # The random session namespace is selected by the server, never a user filename.
        namespace = f'{tenant}/{user}/{upload_id}'
        row = dict(id=upload_id, tenant_id=tenant, user_id=user, filename=request.filename,
                   format=extension, expected_size=request.file_size, content_hash=request.content_hash,
                   source='document-upload', staging_key=f'staging/{namespace}', final_key=f'confirmed/{namespace}',
                   force_reprocess=request.force_reprocess, status='uploading', created_at=now,
                   expires_at=now + timedelta(seconds=self.storage.config.url_seconds), outbox_next=now)
        url = self.storage.presign(row['staging_key'], row['expected_size'])

        def reserve(connection):
            connection.execute(text('DELETE FROM document_upload_slots WHERE user_id=:user AND expires_at<=:now'),
                               {'user': user, 'now': now})
            inserted = connection.execute(text('''INSERT INTO document_upload_slots(user_id,upload_id,expires_at)
                VALUES(:user_id,:id,:expires_at) ON CONFLICT(user_id) DO NOTHING'''), row).rowcount
            if inserted != 1:
                raise UploadError('user_upload_active')
            connection.execute(text('''INSERT INTO document_uploads
                (id,tenant_id,user_id,filename,format,expected_size,content_hash,source,staging_key,final_key,
                 force_reprocess,status,created_at,expires_at,outbox_next)
                VALUES(:id,:tenant_id,:user_id,:filename,:format,:expected_size,:content_hash,:source,:staging_key,
                       :final_key,:force_reprocess,:status,:created_at,:expires_at,:outbox_next)'''), row)
        self.transaction(reserve)
        return {'upload_id': upload_id, 'upload_url': url, 'headers': {'Content-Type': 'application/octet-stream'},
                'expires_at': row['expires_at'].isoformat(), 'max_file_bytes': self.storage.config.max_bytes}

    def owned(self, upload_id, tenant, user):
        with self.engine.connect() as connection:
            row = connection.execute(text('''SELECT * FROM document_uploads
                WHERE id=:id AND tenant_id=:tenant AND user_id=:user'''),
                {'id': upload_id, 'tenant': tenant, 'user': user}).mappings().first()
        if row is None:
            raise UploadError('upload_not_found', 404)
        return dict(row)

    def confirm(self, upload_id, tenant, user):
        row = self.owned(upload_id, tenant, user)
        if row['status'] in {'confirmed', 'duplicate'}:
            self.publish_pending(row['id'])
            return self.status(upload_id, tenant, user)
        if row['status'] != 'uploading' or as_utc(row['expires_at']) <= utc_timestamp():
            raise UploadError('upload_expired')
        try:
            data = self.storage.read(row['staging_key'], row['expected_size'], row['content_hash'])
            validate_format(data, row['format'])
            # Upload body and final body are the same verified bytes, avoiding copy/read TOCTOU.
            self.storage.finalize(row['final_key'], data, row['content_hash'])
        except (FormatError, InvalidDocument) as error:
            # Missing/partial object is recoverable while the upload authorization remains valid.
            raise UploadError(str(error), 422) from None
        now, new_job = utc_timestamp(), str(uuid.uuid4())

        def finish(connection):
            current = connection.execute(text('SELECT * FROM document_uploads WHERE id=:id'),
                                         {'id': upload_id}).mappings().one()
            if current['status'] in {'confirmed', 'duplicate'}:
                return
            if current['status'] != 'uploading' or as_utc(current['expires_at']) <= now:
                raise UploadError('upload_expired')
            # Membership is checked again in the atomic transition, not only before the S3 call.
            member = connection.execute(text('SELECT 1 FROM user_tenants WHERE user_id=:user AND tenant_id=:tenant'),
                                        {'user': user, 'tenant': tenant}).first()
            if member is None:
                raise UploadError('upload_not_found', 404)
            connection.execute(text('''INSERT INTO document_content_claims(tenant_id,content_hash,job_id)
                VALUES(:tenant,:hash,:job) ON CONFLICT(tenant_id,content_hash) DO NOTHING'''),
                {'tenant': tenant, 'hash': row['content_hash'], 'job': new_job})
            prior = connection.execute(text('''SELECT job_id FROM document_content_claims
                WHERE tenant_id=:tenant AND content_hash=:hash'''),
                {'tenant': tenant, 'hash': row['content_hash']}).scalar_one()
            if prior != new_job:
                terminal = connection.execute(text('''SELECT 1 FROM jobs j
                    JOIN document_uploads u ON u.job_id=j.id AND u.tenant_id=j.tenant_id
                    WHERE j.id=:job AND j.tenant_id=:tenant AND j.status='failed'
                      AND u.status='confirmed' AND u.terminal_failure=true'''),
                    {'job': prior, 'tenant': tenant}).first()
                if terminal is not None:
                    # Recover claims left by an older worker without redirecting
                    # healthy, completed or retryable jobs belonging to the tenant.
                    connection.execute(text('''UPDATE document_content_claims SET job_id=:job
                        WHERE tenant_id=:tenant AND content_hash=:hash AND job_id=:prior'''),
                        {'job': new_job, 'tenant': tenant, 'hash': row['content_hash'], 'prior': prior})
                    prior = new_job
            duplicate = prior != new_job and not row['force_reprocess']
            job_id = prior if duplicate else new_job
            if not duplicate:
                if prior != new_job:
                    connection.execute(text('''UPDATE document_content_claims SET job_id=:job
                        WHERE tenant_id=:tenant AND content_hash=:hash'''),
                        {'job': job_id, 'tenant': tenant, 'hash': row['content_hash']})
                uri = f's3://{self.storage.config.bucket}/{row["final_key"]}'
                payload = {'tenant_id': tenant, 'source': row['source'], 'artifact_uri': uri,
                           'upload_id': upload_id, 'metadata': {}}
                connection.execute(text('''INSERT INTO jobs
                    (id,tenant_id,created_by,source,artifact_uri,payload,status,result,created_at,updated_at)
                    VALUES(:id,:tenant,:user,:source,:uri,:payload,'publish_pending',NULL,:now,:now)'''),
                    {'id': job_id, 'tenant': tenant, 'user': user, 'source': row['source'], 'uri': uri,
                     'payload': json.dumps(payload), 'now': now})
            connection.execute(text('''UPDATE document_uploads SET status=:status,job_id=:job,
                outbox_sent=:sent WHERE id=:id AND status='uploading' '''),
                {'status': 'duplicate' if duplicate else 'confirmed', 'job': job_id, 'id': upload_id, 'sent': duplicate})
            connection.execute(text('DELETE FROM document_upload_slots WHERE user_id=:user AND upload_id=:id'),
                               {'user': user, 'id': upload_id})
        self.transaction(finish)
        # A database/broker failure leaves the durable outbox pending for HTTP retry/maintenance.
        self.publish_pending(upload_id)
        return self.status(upload_id, tenant, user)

    def publish_pending(self, upload_id):
        now = utc_timestamp()
        def claim(connection):
            changed = connection.execute(text('''UPDATE document_uploads SET outbox_next=:next
                WHERE id=:id AND status='confirmed' AND outbox_sent=false AND outbox_next<=:now'''),
                {'id': upload_id, 'now': now, 'next': now + timedelta(seconds=15)}).rowcount
            if changed != 1:
                return None
            row = connection.execute(text('''SELECT j.* FROM jobs j JOIN document_uploads u
                ON u.job_id=j.id AND u.tenant_id=j.tenant_id AND u.user_id=j.created_by WHERE u.id=:id'''),
                {'id': upload_id}).mappings().one()
            return dict(row)
        job = self.transaction(claim)
        if job is None:
            return
        job['payload'] = json_value(job['payload'])
        envelope = {key: job[key] for key in ('id', 'tenant_id', 'created_by', 'source', 'artifact_uri', 'payload')}
        reservation = self.queue.reserve()
        try:
            if getattr(reservation, 'outcome', None) == 'not_sent':
                return
            published = self.queue.publish(envelope, reservation=reservation)
            if published.outcome != 'confirmed':
                return
            def acknowledge(connection):
                connection.execute(text('UPDATE document_uploads SET outbox_sent=true WHERE id=:id'), {'id': upload_id})
                connection.execute(text("UPDATE jobs SET status='queued',updated_at=:now WHERE id=:id AND status='publish_pending'"),
                                   {'id': job['id'], 'now': utc_timestamp()})
            self.transaction(acknowledge)
        finally:
            self.queue.cancel(reservation)

    def cancel(self, upload_id, tenant, user):
        self.owned(upload_id, tenant, user)
        def cancel_row(connection):
            connection.execute(text("UPDATE document_uploads SET status='cancelled' WHERE id=:id AND status='uploading'"), {'id': upload_id})
            connection.execute(text('DELETE FROM document_upload_slots WHERE user_id=:user AND upload_id=:id'),
                               {'user': user, 'id': upload_id})
        self.transaction(cancel_row)
        return self.status(upload_id, tenant, user)

    def status(self, upload_id, tenant, user):
        row = self.owned(upload_id, tenant, user)
        job = None
        if row['job_id']:
            with self.engine.connect() as connection:
                job = connection.execute(text('''SELECT j.id,j.status,j.result,COALESCE(u.terminal_failure,false) AS terminal_failure
                    FROM jobs j LEFT JOIN document_uploads u ON u.job_id=j.id AND u.tenant_id=j.tenant_id AND u.status='confirmed'
                    WHERE j.id=:id AND j.tenant_id=:tenant'''),
                                         {'id': row['job_id'], 'tenant': tenant}).mappings().first()
        status = row['status']
        if status == 'uploading' and as_utc(row['expires_at']) <= utc_timestamp():
            status = 'expired'
        return {'upload_id': row['id'], 'filename': row['filename'], 'file_size': row['expected_size'],
                'status': status, 'job_id': row['job_id'], 'job_status': job['status'] if job else None,
                'duplicate': row['status'] == 'duplicate', 'cleanup_done': row['cleanup_done'],
                'retry_pending': bool(job and job['status']=='failed' and not job['terminal_failure'])}

    def extracted(self, job_id, tenant):
        with self.engine.connect() as connection:
            document = load_checkpoint(connection, job_id, tenant)
        if document is None:
            raise UploadError('document_not_found', 404)
        return document

    def maintain(self):
        now = utc_timestamp()
        with self.engine.begin() as connection:
            connection.execute(text("UPDATE document_uploads SET status='expired' WHERE status='uploading' AND expires_at<=:now"), {'now': now})
            connection.execute(text('DELETE FROM document_upload_slots WHERE expires_at<=:now'), {'now': now})
            pending = connection.execute(text("SELECT id FROM document_uploads WHERE status='confirmed' AND outbox_sent=false AND outbox_next<=:now LIMIT 50"), {'now': now}).scalars().all()
            stale = connection.execute(text('''SELECT u.* FROM document_uploads u LEFT JOIN jobs j
                ON j.id=u.job_id AND j.tenant_id=u.tenant_id
                WHERE u.cleanup_done=false AND (
                  (u.status IN ('cancelled','expired','duplicate') AND u.expires_at<=:now)
                  OR (u.status='confirmed' AND j.status='completed')
                  OR (u.status='confirmed' AND u.terminal_failure=true AND j.status='failed' AND j.updated_at<=:retention)) LIMIT 50'''),
                  {'now': now, 'retention': now - timedelta(days=self.failed_retention_days)}).mappings().all()
        for upload_id in pending:
            try:
                self.publish_pending(upload_id)
            except Exception:
                # One unavailable item must not prevent recovery of the other uploads.
                logger.warning('document_outbox_retry_pending', extra={'upload_id': upload_id})
        for row in stale:
            # Final only belongs to this upload, never to another tenant or deduplicated job.
            try:
                self.storage.delete(row['final_key'])
                self.storage.delete(row['staging_key'])
                if as_utc(row['expires_at']) <= now:
                    with self.engine.begin() as connection:
                        connection.execute(text('UPDATE document_uploads SET cleanup_done=true WHERE id=:id'), {'id': row['id']})
            except Exception:
                logger.warning('document_cleanup_retry_pending', extra={'upload_id': row['id']})
        with self.engine.begin() as connection:
            connection.execute(text('''DELETE FROM extracted_document_parts AS p
                WHERE EXISTS (SELECT 1 FROM jobs j WHERE j.id=p.job_id AND j.tenant_id=p.tenant_id AND (
                    j.status='completed' OR (j.status='failed' AND j.updated_at<=:retention AND EXISTS (
                        SELECT 1 FROM document_uploads u WHERE u.job_id=j.id AND u.tenant_id=j.tenant_id AND u.terminal_failure=true))))
                AND NOT EXISTS (SELECT 1 FROM extracted_documents d WHERE d.job_id=p.job_id AND d.tenant_id=p.tenant_id
                    AND d.document->>'checkpoint_storage'='sql-parts-v1' AND d.document->>'generation'=p.generation)'''),
                {'retention': now-timedelta(days=self.failed_retention_days)})
