"""Run only on explicit operator request; never called on startup or job replay."""
import argparse
import json
from pathlib import Path
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
    parser.add_argument('--action', choices=['document', 'build', 'inspect', 'activate', 'rollback', 'prune'], default='document')
    parser.add_argument('--document-id')
    parser.add_argument('--tenant-id', required=True)
    parser.add_argument('--created-by', required=True, help='Existing document owner, or current tenant member for index service operations')
    parser.add_argument('--space-file', help='Verified non-secret embedding descriptor JSON (build only)')
    parser.add_argument('--retrieval-mode', choices=['dense', 'hybrid'], default='dense')
    parser.add_argument('--rrf-k', type=int, default=60, help='Immutable generation ranking constant, 1..1000')
    parser.add_argument('--generation-id')
    parser.add_argument('--resume-generation')
    parser.add_argument('--expected-head', help='Exact active generation, or legacy for the initial activation')
    parser.add_argument('--expected-version', type=int)
    parser.add_argument('--rebuild', action='store_true', help='Explicitly permit rebuilding the prior space over the current catalog')
    parser.add_argument('--keep-generation', action='append', default=[], help='Protect evaluation/recovery generations during pruning')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    if args.action == 'document' and not args.document_id:
        parser.error('--document-id is required for document reprocessing')
    if args.action == 'build' and not args.space_file and not args.resume_generation:
        parser.error('build requires --space-file or --resume-generation')
    if args.action in {'activate', 'rollback'} and (args.expected_head is None or args.expected_version is None):
        parser.error('activation/rollback require --expected-head and --expected-version')
    if args.action == 'activate' and not args.generation_id:
        parser.error('activate requires --generation-id')
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)
    try:
        # Deployment preparation owns migrations; this command never upgrades schema.
        if args.action != 'document':
            result = index_operation(args, settings, database, store)
            print(json.dumps(result, sort_keys=True, default=str))
            return
        chunker = StructuredChunker(ChunkingConfig(settings.embedding_chunk_target_tokens,
            settings.embedding_chunk_max_tokens, settings.embedding_chunk_overlap_ratio))
        operation = DocumentReprocessor(JobRepository(database), database.engine, chunker,
            get_embedding_provider(settings.embedding_provider, settings.embedding_dimension, settings=settings), store)
        result = operation.execute(document_id=args.document_id, tenant_id=args.tenant_id, created_by=args.created_by)
        print(json.dumps(result, sort_keys=True))
    finally:
        store.close()
        database.dispose()


def index_operation(args, settings, database, store):
    from app.embeddings.space import EmbeddingSpace
    from app.embeddings.tokenization import EmbeddingTokenCounter
    from app.vector_store.generations import GenerationStore
    from app.vector_store.operator import catalog_authorizer
    authorize = catalog_authorizer(database, store, args.tenant_id, args.created_by)
    authorize()
    generations = GenerationStore(store.engine)
    scope = args.tenant_id
    if args.action == 'inspect':
        return generations.inspect(scope, args.generation_id)
    if args.action == 'prune':
        return generations.prune(scope, keep=args.keep_generation, limit=args.limit, authorize=authorize)
    if args.action == 'activate':
        return generations.activate(scope, args.generation_id, expected_head=None if args.expected_head == 'legacy' else args.expected_head,
            expected_version=args.expected_version, authorize=authorize)
    if args.action == 'rollback' and not args.rebuild:
        return generations.rollback(scope, expected_head=args.expected_head, expected_version=args.expected_version, authorize=authorize)
    generations.counter = EmbeddingTokenCounter()
    provider = get_embedding_provider(settings.embedding_provider, settings.embedding_dimension, settings=settings)
    if args.action == 'rollback':
        return generations.rebuild_previous(scope, provider, expected_head=args.expected_head,
            expected_version=args.expected_version, authorize=authorize)
    if args.resume_generation:
        identifier = generations.resume(scope, args.resume_generation, provider, authorize=authorize)
    else:
        path = Path(args.space_file)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
            raise ValueError('Invalid space descriptor file')
        space = EmbeddingSpace.from_descriptor(json.loads(path.read_text(encoding='utf-8')))
        identifier = generations.build(scope, space, provider, retrieval_mode=args.retrieval_mode,
                                       rrf_k=getattr(args, 'rrf_k', 60), authorize=authorize)
    return generations.inspect(scope, identifier)


if __name__ == '__main__':
    main()
