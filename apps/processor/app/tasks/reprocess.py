"""Explicit operator reindexing from a completed job's durable normalized input."""
from app.documents.document_checkpoint import load_checkpoint
from app.embeddings.normalized import parent_metadata


class UnsupportedReprocessing(RuntimeError):
    pass


class DocumentReprocessor:
    def __init__(self, repository, checkpoint_engine, chunker, embedding_provider, vector_store):
        self.repository = repository
        self.checkpoint_engine = checkpoint_engine
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def execute(self, *, document_id: str, tenant_id: str, created_by: str) -> dict:
        stored = self.repository.fetch_authorized_job(document_id, tenant_id=tenant_id, created_by=created_by)
        if stored is None:
            raise PermissionError('Document reprocessing rejected')
        if stored['status'] != 'completed':
            raise UnsupportedReprocessing('Only a completed document can be explicitly reprocessed')
        expected = self.vector_store.publication(document_id, tenant_id)
        if expected is None:
            raise UnsupportedReprocessing('No existing vector document to reprocess')
        with self.checkpoint_engine.connect() as connection:
            document = load_checkpoint(connection, document_id, tenant_id)
        if document is None:
            raise UnsupportedReprocessing('Normalized checkpoint is absent; existing search is unchanged')
        if document.get('document_id') != document_id or document.get('tenant_id') != tenant_id:
            raise ValueError('Normalized checkpoint identity mismatch')
        result = self.chunker.chunk_document(document)
        # All remote work finishes before the replacement transaction begins.
        embeddings = [self.embedding_provider.embed(chunk['content']) for chunk in result['chunks']]
        # Recheck the existing authorization after a potentially slow provider call.
        current = self.repository.fetch_authorized_job(document_id, tenant_id=tenant_id, created_by=created_by)
        if current is None or current['status'] != 'completed':
            raise PermissionError('Document reprocessing rejected')
        publication = self.vector_store.store_document(
            job_id=document_id, tenant_id=tenant_id, source=stored['source'].strip().lower(),
            artifact_uri=stored.get('artifact_uri'), text_content=document['text'], chunks=result['chunks'],
            embeddings=embeddings, provider_name=self.embedding_provider.name,
            document_metadata=parent_metadata(document, result['manifest']), expected_publication=expected)
        return {**publication, 'chunking_fingerprint':result['manifest']['fingerprint'],
                'operation':'explicit-reprocess', 'job_status':'completed'}
