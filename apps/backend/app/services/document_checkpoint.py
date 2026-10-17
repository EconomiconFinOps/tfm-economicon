"""Versioned document checkpoints with bounded SQL messages.

Identical in backend and processor, which are independent Python deployments.
Small legacy JSON checkpoints remain readable; large checkpoints publish a manifest
only after all generation-scoped parts are durable.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import text

PART_CHARACTERS = 64_000  # at most256KB in UTF-8; well below Cockroach wire/row limits
MAX_BYTES = 160_000_000
MAX_PARTS = 2500


def load_checkpoint(connection, job_id, tenant_id):
    row=connection.execute(text('SELECT document FROM extracted_documents WHERE job_id=:id AND tenant_id=:tenant'),
                           {'id':job_id,'tenant':tenant_id}).first()
    if row is None: return None
    value=json.loads(row[0]) if isinstance(row[0],str) else row[0]
    if not isinstance(value,dict): raise RuntimeError('document_checkpoint_invalid')
    if value.get('checkpoint_storage')!='sql-parts-v1': return value
    count=value.get('part_count')
    if type(count) is not int or not 1<=count<=MAX_PARTS: raise RuntimeError('document_checkpoint_invalid')
    rows=connection.execute(text('''SELECT part_index,content FROM extracted_document_parts
        WHERE job_id=:id AND tenant_id=:tenant AND generation=:generation ORDER BY part_index'''),
        {'id':job_id,'tenant':tenant_id,'generation':value.get('generation')}).all()
    if len(rows)!=count or any(row.part_index!=index for index,row in enumerate(rows)):
        raise RuntimeError('document_checkpoint_incomplete')
    raw=''.join(row.content for row in rows).encode('utf-8')
    if len(raw)>MAX_BYTES or len(raw)!=value.get('byte_count') or hashlib.sha256(raw).hexdigest()!=value.get('sha256'):
        raise RuntimeError('document_checkpoint_integrity_rejected')
    return json.loads(raw)


def save_checkpoint(engine, job_id, tenant_id, document, *, owner=None):
    value=json.dumps(document,ensure_ascii=False,separators=(',',':'))
    raw=value.encode('utf-8')
    if len(raw)>MAX_BYTES: raise RuntimeError('document_checkpoint_limit')
    generation=str(uuid.uuid4())
    if len(raw)>256_000:
        parts=[value[index:index+PART_CHARACTERS] for index in range(0,len(value),PART_CHARACTERS)]
        if len(parts)>MAX_PARTS: raise RuntimeError('document_checkpoint_limit')
        for index,content in enumerate(parts):
            with engine.begin() as connection:
                connection.execute(text('''INSERT INTO extracted_document_parts(job_id,tenant_id,generation,part_index,content)
                    VALUES(:id,:tenant,:generation,:index,:content)'''),
                    {'id':job_id,'tenant':tenant_id,'generation':generation,'index':index,'content':content})
        value=json.dumps({'checkpoint_storage':'sql-parts-v1','generation':generation,'part_count':len(parts),
                          'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    # A file worker may publish only while its lease still belongs to it.
    fence=''' WHERE EXISTS (SELECT 1 FROM document_execution_claims
        WHERE job_id=:id AND tenant_id=:tenant AND owner=:owner AND expires_at>:now)''' if owner else ''
    with engine.begin() as connection:
        saved=connection.execute(text('''INSERT INTO extracted_documents(job_id,tenant_id,document,created_at)
            SELECT :id,:tenant,:document,:now'''+fence+''' ON CONFLICT(job_id) DO UPDATE SET document=excluded.document
            WHERE extracted_documents.tenant_id=excluded.tenant_id'''),
            {'id':job_id,'tenant':tenant_id,'document':value,'owner':owner,'now':datetime.now(timezone.utc)}).rowcount
        if saved!=1: raise RuntimeError('document_checkpoint_publication_rejected')
    # Never delete another in-flight generation here. The backend sweeps unreferenced
    # parts only after the job is completed or its failed retention is terminal.
