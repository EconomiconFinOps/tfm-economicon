"""Authorize and checkpoint document extraction before the existing RAG pipeline."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import uuid

from sqlalchemy import text
import structlog

from app.agents.guardrails import AgentInputError
from app.documents.document_storage import InvalidDocument
from app.documents.document_checkpoint import load_checkpoint, save_checkpoint


def json_value(value):
    return json.loads(value) if isinstance(value, str) else value


def limits():
    values = {
        'max_pages': int(os.getenv('DOCUMENT_MAX_PAGES', '100')),
        'seconds': int(os.getenv('DOCUMENT_EXTRACTION_SECONDS', '180')),
        'page_seconds': int(os.getenv('DOCUMENT_OCR_PAGE_SECONDS', '30')),
        'memory_mb': int(os.getenv('DOCUMENT_EXTRACTION_MEMORY_MB', '1536')),
        'max_pixels': int(os.getenv('DOCUMENT_OCR_MAX_PIXELS', '16000000')),
        'max_text_chars': 20_000_000, 'max_blocks': 50_000,
        'lease_seconds': int(os.getenv('DOCUMENT_EXECUTION_LEASE_SECONDS', '300')),
    }
    if not (1 <= values['max_pages'] <= 1000 and 10 <= values['seconds'] <= 600
            and 1 <= values['page_seconds'] <= 120 and 256 <= values['memory_mb'] <= 4096
            and 1_000_000 <= values['max_pixels'] <= 32_000_000 and 15 <= values['lease_seconds'] <= 900):
        raise ValueError('Invalid extraction limits')
    return values


def extract_local(data, extension):
    settings = limits()
    with tempfile.TemporaryDirectory(prefix='document-extract-') as name:
        directory = Path(name)
        (directory / 'input').write_bytes(data)
        (directory / 'limits.json').write_text(json.dumps(settings))
        # No service credentials or inherited descriptors are passed to the extractor.
        environment = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'LANG': 'C.UTF-8',
                       'HOME': name, 'TMPDIR': name, 'OMP_THREAD_LIMIT': '1', 'OPENBLAS_NUM_THREADS': '1',
                       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(Path(__file__).resolve().parents[2])}
        process = subprocess.Popen([sys.executable, '-B', '-m', 'app.documents.extract_worker', name, extension],
                                   env=environment, cwd=name, close_fds=True, start_new_session=True,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            process.wait(timeout=settings['seconds'] + 5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise AgentInputError('document_extraction_limit') from None
        finally:
            # Also reap an OCR/conversion descendant left behind by a failed extractor.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        output = directory / 'output.json'
        if process.returncode != 0 or not output.is_file() or output.stat().st_size > 80_000_000:
            raise AgentInputError('document_extraction_failed')
        result = json.loads(output.read_text(encoding='utf-8'))
        if not result.get('ok'):
            if result.get('error') == 'document_extraction_environment_unavailable':
                raise RuntimeError('document_extraction_environment_unavailable')
            raise AgentInputError('document_extraction_failed')
        return result['document']


class DocumentProcessor:
    def __init__(self, engine, storage):
        self.engine, self.storage = engine, storage
        self.owner = str(uuid.uuid4())
        self._heartbeat_stop = None
        self._heartbeat_thread = None
        self._lease_lost = threading.Event()

    def claim(self, stored, payload):
        if 'upload_id' not in payload:
            return
        self._lease_lost = threading.Event()
        now = datetime.now(timezone.utc)
        params = {'id': stored['id'], 'tenant': stored['tenant_id'], 'owner': self.owner,
                  'now': now, 'expiry': now + timedelta(seconds=limits()['lease_seconds'])}
        with self.engine.begin() as connection:
            connection.execute(text('''INSERT INTO document_execution_claims(job_id,tenant_id,owner,expires_at)
                VALUES(:id,:tenant,:owner,:now) ON CONFLICT(job_id) DO NOTHING'''), params)
            claimed = connection.execute(text('''UPDATE document_execution_claims SET owner=:owner,expires_at=:expiry
                WHERE job_id=:id AND tenant_id=:tenant AND expires_at<=:now'''), params).rowcount
            if claimed != 1:
                raise RuntimeError('document_execution_busy')
        stop = threading.Event()
        lease_lost = self._lease_lost
        self._heartbeat_stop = stop
        def heartbeat():
            # A delayed renewal must never start waiting on the next job's Event.
            while not stop.wait(limits()['lease_seconds'] / 3):
                try:
                    with self.engine.begin() as connection:
                        renewed_at = datetime.now(timezone.utc)
                        changed = connection.execute(text('''UPDATE document_execution_claims SET expires_at=:expiry
                            WHERE job_id=:id AND tenant_id=:tenant AND owner=:owner AND expires_at>:renewed_at'''),
                            {**params, 'renewed_at': renewed_at,
                             'expiry': renewed_at + timedelta(seconds=limits()['lease_seconds'])}).rowcount
                        if changed != 1:
                            lease_lost.set()
                            return
                except Exception:
                    structlog.get_logger(__name__).warning('document_execution_lease_renewal_failed')
        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True, name='document-execution-heartbeat')
        self._heartbeat_thread.start()

    def assert_owned(self, stored, payload):
        if 'upload_id' not in payload:
            return
        if self._lease_lost.is_set():
            raise RuntimeError('document_execution_lease_lost')
        with self.engine.connect() as connection:
            owned = connection.execute(text('''SELECT 1 FROM document_execution_claims
                WHERE job_id=:id AND tenant_id=:tenant AND owner=:owner AND expires_at>:now'''),
                {'id': stored['id'], 'tenant': stored['tenant_id'], 'owner': self.owner,
                 'now': datetime.now(timezone.utc)}).first()
        if owned is None:
            self._lease_lost.set()
            raise RuntimeError('document_execution_lease_lost')

    def release(self, stored):
        if self._heartbeat_stop is not None:
            self._heartbeat_stop.set()
            self._heartbeat_thread.join(timeout=10)
            self._heartbeat_stop = None
            self._heartbeat_thread = None
        with self.engine.begin() as connection:
            connection.execute(text('DELETE FROM document_execution_claims WHERE job_id=:id AND tenant_id=:tenant AND owner=:owner'),
                               {'id': stored['id'], 'tenant': stored['tenant_id'], 'owner': self.owner})

    def is_terminal(self, stored, payload):
        return 'upload_id' in payload and bool(self.upload(stored, payload['upload_id'])['terminal_failure'])

    def _matching_file(self, job, incoming=None):
        if not isinstance(job, dict) or not all(isinstance(job.get(key), str) for key in ('id', 'tenant_id', 'created_by')):
            return None
        with self.engine.connect() as connection:
            row = connection.execute(text('''SELECT j.* FROM jobs j
                JOIN document_uploads u ON u.job_id=j.id AND u.tenant_id=j.tenant_id AND u.user_id=j.created_by
                WHERE j.id=:id AND j.tenant_id=:tenant AND j.created_by=:user AND u.status='confirmed' '''),
                {'id': job['id'], 'tenant': job['tenant_id'], 'user': job['created_by']}).mappings().first()
        if row is None:
            return None
        stored = dict(row)
        try:
            payload = json_value(stored['payload'])
            provided = json_value(job.get('payload')) if incoming is None else incoming
        except (TypeError, ValueError):
            return None
        if not isinstance(payload, dict) or not isinstance(provided, dict) or 'upload_id' not in payload:
            return None
        payload = {'artifact_uri': None, 'metadata': {}, **payload}
        provided = {'artifact_uri': None, 'metadata': {}, **provided}
        if (provided != payload or job.get('job_id', job['id']) != job['id']
                or any(job.get(key) != stored.get(key) for key in ('source', 'artifact_uri'))):
            return None
        # Verify the confirmed object's canonical owner/path before any transition.
        self.upload(stored, payload['upload_id'])
        return stored, payload

    def _terminal(self, connection, stored, *, revoked=False):
        now = datetime.now(timezone.utc)
        params = {'id': stored['id'], 'tenant': stored['tenant_id'], 'user': stored['created_by'],
                  'owner': self.owner, 'now': now}
        fence = '''EXISTS (SELECT 1 FROM document_execution_claims c WHERE c.job_id=:id
            AND c.tenant_id=:tenant AND c.owner=:owner AND c.expires_at>:now)'''
        if revoked:
            # Recheck in the same transaction: restored membership must retry authorization.
            member = connection.execute(text('SELECT 1 FROM user_tenants WHERE user_id=:user AND tenant_id=:tenant'), params).first()
            if member is not None:
                raise RuntimeError('document_authorization_changed')
            changed = connection.execute(text('''UPDATE jobs SET status='failed',result=:result,updated_at=:now
                WHERE id=:id AND tenant_id=:tenant AND created_by=:user AND status<>'completed' AND ''' + fence),
                {**params, 'result': json.dumps({'error': 'document_authorization_rejected'})}).rowcount
            if changed != 1:
                raise RuntimeError('document_execution_lease_lost')
        changed = connection.execute(text('''UPDATE document_uploads SET terminal_failure=true
            WHERE job_id=:id AND tenant_id=:tenant AND user_id=:user AND status='confirmed'
              AND EXISTS (SELECT 1 FROM jobs j WHERE j.id=:id AND j.tenant_id=:tenant AND j.status='failed')
              AND ''' + fence), params).rowcount
        if changed != 1:
            raise RuntimeError('document_terminal_transition_rejected')
        connection.execute(text('DELETE FROM document_content_claims WHERE job_id=:id AND tenant_id=:tenant'), params)

    def reject_unauthorized(self, job, incoming):
        matched = self._matching_file(job, incoming)
        if matched is None:
            return
        stored, payload = matched
        if stored['status'] == 'completed' or self.is_terminal(stored, payload):
            return
        self.claim(stored, payload)
        try:
            with self.engine.begin() as connection:
                self._terminal(connection, stored, revoked=True)
        finally:
            self.release(stored)

    def terminal_failure(self, job):
        matched = self._matching_file(job)
        if matched is None:
            return
        stored, payload = matched
        if stored['status'] != 'failed' or self.is_terminal(stored, payload):
            return
        # Task.execute releases its claim before the worker decides whether a
        # delivery is terminal. Reacquire rather than writing without a fence.
        self.claim(stored, payload)
        try:
            with self.engine.begin() as connection:
                self._terminal(connection, stored)
        finally:
            self.release(stored)

    def upload(self, stored, upload_id):
        with self.engine.connect() as connection:
            row = connection.execute(text('''SELECT * FROM document_uploads WHERE id=:upload AND job_id=:job
                AND tenant_id=:tenant AND user_id=:user AND status='confirmed' '''),
                {'upload': upload_id, 'job': stored['id'], 'tenant': stored['tenant_id'], 'user': stored['created_by']}).mappings().first()
        if row is None:
            raise AgentInputError('document_reference_rejected')
        expected = f'confirmed/{stored["tenant_id"]}/{stored["created_by"]}/{upload_id}'
        if row['final_key'] != expected or stored['artifact_uri'] != f's3://{self.storage.config.bucket}/{expected}':
            raise AgentInputError('document_reference_rejected')
        return dict(row)

    def prepare(self, stored, payload):
        self.assert_owned(stored, payload)
        upload = self.upload(stored, payload['upload_id']) if 'upload_id' in payload else None
        with self.engine.connect() as connection:
            prior = load_checkpoint(connection, stored['id'], stored['tenant_id'])
        if prior is not None:
            return prior
        origin = {'source': stored['source'], 'artifact_uri': stored.get('artifact_uri'),
                  'uploaded_by': stored['created_by'], 'tenant_id': stored['tenant_id']}
        if upload is not None:
            try:
                raw = self.storage.read(upload['final_key'], upload['expected_size'], upload['content_hash'])
            except InvalidDocument:
                raise AgentInputError('document_integrity_rejected') from None
            extracted = extract_local(raw, upload['format'])
            origin.update(filename=upload['filename'], file_size=upload['expected_size'],
                          content_hash=upload['content_hash'], uploaded_at=str(upload['created_at']),
                          content_type={'md': 'text/markdown', 'txt': 'text/plain', 'pdf': 'application/pdf',
                                        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                        'doc': 'application/msword'}[upload['format']])
            original_format = upload['format']
        else:
            value = payload['text_content']
            extracted = {'text': value, 'blocks': [], 'file_metadata': {}, 'warnings': [],
                         'extraction_method': 'manual-text', 'result': 'extracted'}
            origin.update(content_hash=hashlib.sha256(value.encode('utf-8')).hexdigest())
            original_format = 'manual-text'
        document = {'schema_version': 1, 'document_id': stored['id'], 'tenant_id': stored['tenant_id'],
                    'original_format': original_format, 'origin': origin, **extracted}
        self.assert_owned(stored, payload)
        save_checkpoint(self.engine, stored['id'], stored['tenant_id'], document,
                        owner=self.owner if 'upload_id' in payload else None)
        return document

    def completed(self, stored, payload):
        if 'upload_id' not in payload:
            return
        upload = self.upload(stored, payload['upload_id'])
        # SQL completed is already durable. Failure here schedules cleanup, never reverses it.
        try:
            self.storage.delete(upload['final_key'])
            self.storage.delete(upload['staging_key'])
        except Exception:
            structlog.get_logger(__name__).warning('document_cleanup_retry_pending')
