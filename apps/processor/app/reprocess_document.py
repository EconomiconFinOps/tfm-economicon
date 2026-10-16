"""Run only on explicit operator request; never called on startup or job replay."""
import argparse
import json
from app.core.config import get_settings
from app.db.database import Database
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.providers import get_embedding_provider
from app.embeddings.structural_chunker import StructuredChunker
from app.repositories.jobs import JobRepository
from app.tasks.reprocess import DocumentReprocessor
from app.vector_store.pgvector_store import PgVectorStore


def main():
    parser = argparse.ArgumentParser(description='Reindex one completed document from its normalized checkpoint')
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--tenant-id', required=True)
    parser.add_argument('--created-by', required=True, help='Existing job owner; membership is verified')
    args = parser.parse_args()
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)
    try:
        # Deployment preparation owns migrations; this command never upgrades schema.
        chunker = StructuredChunker(ChunkingConfig(settings.embedding_chunk_target_tokens,
            settings.embedding_chunk_max_tokens, settings.embedding_chunk_overlap_ratio))
        operation = DocumentReprocessor(JobRepository(database), database.engine, chunker,
            get_embedding_provider(settings.embedding_provider, settings.embedding_dimension, settings=settings), store)
        result = operation.execute(document_id=args.document_id, tenant_id=args.tenant_id, created_by=args.created_by)
        print(json.dumps(result, sort_keys=True))
    finally:
        store.close()
        database.dispose()


if __name__ == '__main__':
    main()
