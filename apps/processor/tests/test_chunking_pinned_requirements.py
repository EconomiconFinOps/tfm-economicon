"""Negative/boundary tests for requirements that no current test pins."""
import hashlib
import threading

import pytest
from sqlalchemy import event

from app.embeddings.contracts import ChunkingConfig
from app.embeddings.normalized import manual_document, parent_metadata
from app.embeddings.providers import MockEmbeddingProvider
from app.embeddings.structural_chunker import StructuredChunker, reconstruct_normalized_text
from app.embeddings.tokenization import EmbeddingTokenCounter
from app.vector_store.pgvector_store import StalePublication
from test_tenant_isolation_vector import vector_store  # noqa: F401  (disposable real pgvector fixture)

COUNTER = EmbeddingTokenCounter()


def document(text, fmt='txt'):
    return {'schema_version': 1, 'document_id': 'doc', 'tenant_id': 'tenant', 'original_format': fmt, 'text': text,
            'blocks': [], 'file_metadata': {}}


def paragraph(prefix, tokens):
    words = []
    while COUNTER.count(' '.join(words)) < tokens:
        words.append(f'{prefix}{len(words)}')
    return ' '.join(words)


def test_packed_paragraphs_stop_at_the_target_not_at_the_maximum():
    config = ChunkingConfig(100, 160, 0.1)
    text = '\n\n'.join(paragraph(f'p{index}w', 40) for index in range(12)) + '\n'
    chunks = StructuredChunker(config).chunk_document(document(text))['chunks']
    assert len(chunks) > 3
    assert max(chunk['metadata']['token_count'] for chunk in chunks) <= config.target_tokens + config.overlap_tokens


def test_heading_is_not_left_alone_when_the_next_paragraph_exceeds_the_target_but_fits_the_maximum():
    config = ChunkingConfig(100, 160, 0.1)
    body = '\n\n'.join(paragraph(f'q{index}w', 120) for index in range(2))
    chunks = StructuredChunker(config).chunk_document(document('## Regla\n\n' + body + '\n', 'md'))['chunks']
    assert all(chunk['content'].strip() != '## Regla' for chunk in chunks)
    assert chunks[0]['content'].startswith('## Regla') and 'q0w' in chunks[0]['content']


def multi_chunk_result():
    config = ChunkingConfig(100, 160, 0.1)
    text = '\n\n'.join(paragraph(f'r{index}w', 40) for index in range(12)) + '\n'
    return text, StructuredChunker(config).chunk_document(document(text))['chunks']


def reseal(chunk):
    chunk['metadata']['chunk_hash'] = hashlib.sha256(chunk['content'].encode('utf-8')).hexdigest()


def test_reconstruction_rejects_repeated_context_that_differs_from_its_source():
    _, chunks = multi_chunk_result()
    target = next(chunk for chunk in chunks if chunk['metadata']['repetitions'])
    left, right = target['metadata']['repetitions'][0]['content_range']
    content = target['content']
    target['content'] = content[:left] + ('X' if content[left] != 'X' else 'Y') + content[left + 1:]
    reseal(target)  # hash and every range stay coherent: only the repeated text lies about its source
    with pytest.raises(ValueError):
        reconstruct_normalized_text(chunks)


def test_reconstruction_does_not_accept_a_missing_chunk_hidden_as_omitted_text():
    text, chunks = multi_chunk_result()
    last = chunks.pop()
    spans = [item['normalized_range'] for item in last['metadata']['primary_spans']]
    start, end = min(item[0] for item in spans), max(item[1] for item in spans)
    descriptor = chunks[0]['metadata']['reconstruction']
    descriptor['chunk_count'] -= 1
    descriptor['omitted_spans'].append({'normalized_range': [start, end], 'text': text[start:end]})
    with pytest.raises(ValueError):
        reconstruct_normalized_text(chunks)


def test_publication_check_is_serialized_by_a_row_lock(vector_store):  # noqa: F811
    """B must not read the old publication while A is between its read and its commit."""
    def prepare(value):
        doc = manual_document({'job_id': 'fixed', 'tenant_id': 'tenant-a', 'source': 's', 'text_content': value})
        result = StructuredChunker().chunk_document(doc)
        return {'job_id': 'fixed', 'tenant_id': 'tenant-a', 'source': 's', 'artifact_uri': None, 'text_content': value,
                'chunks': result['chunks'], 'embeddings': [MockEmbeddingProvider(8).embed(c['content']) for c in result['chunks']],
                'provider_name': 'mock', 'document_metadata': parent_metadata(doc, result['manifest'])}
    original = vector_store.store_document(**prepare('Original evidence.'), expected_publication=None)
    a_read, b_reached = threading.Event(), threading.Event()
    marker = 'tenant_id, job_id, metadata FROM knowledge_documents'
    def before(connection, cursor, statement, parameters, context, executemany):
        if marker in statement and threading.current_thread().name == 'publisher-b':
            b_reached.set()
    def after(connection, cursor, statement, parameters, context, executemany):
        if marker in statement and threading.current_thread().name == 'publisher-a':
            a_read.set()
            b_reached.wait(3)  # B reaches its own read: it blocks on the lock, or reads the old row without one
    event.listen(vector_store.engine, 'before_cursor_execute', before)
    event.listen(vector_store.engine, 'after_cursor_execute', after)
    outcomes = {}
    def publish(name, value):
        if name == 'publisher-b':
            a_read.wait(5)
        try:
            outcomes[name] = vector_store.store_document(**prepare(value), expected_publication=original['publication_id'])
        except StalePublication:
            outcomes[name] = None
    threads = [threading.Thread(target=publish, args=(name, value), name=name)
               for name, value in (('publisher-a', 'First new evidence.'), ('publisher-b', 'Second new evidence.'))]
    try:
        [thread.start() for thread in threads]
        [thread.join(30) for thread in threads]
    finally:
        event.remove(vector_store.engine, 'before_cursor_execute', before)
        event.remove(vector_store.engine, 'after_cursor_execute', after)
    assert outcomes['publisher-a'] is not None and outcomes['publisher-b'] is None


# --- explicit reprocess: authority and preconditions that no current test pins -----------------
from sqlalchemy import text as sql  # noqa: E402
from test_document_checkpoint import case  # noqa: E402,F401
from test_reprocess_document import setup as reprocess_setup  # noqa: E402
from app.tasks.reprocess import UnsupportedReprocessing  # noqa: E402


def test_reprocess_needs_an_existing_vector_document(case, monkeypatch):  # noqa: F811
    operation, scope, provider, store, _ = reprocess_setup(case, monkeypatch)
    store.publication = lambda *_: None
    with pytest.raises(UnsupportedReprocessing, match='No existing vector document'):
        operation.execute(**scope)
    assert not provider.calls and store.saved is None


def test_reprocess_rechecks_authority_after_the_slow_embedding_calls(case, monkeypatch):  # noqa: F811
    operation, scope, provider, store, _ = reprocess_setup(case, monkeypatch)
    original = provider.embed
    def embed_and_lose_authority(value):
        with case[0].begin() as connection:
            connection.execute(sql("UPDATE jobs SET status='running'"))
        return original(value)
    provider.embed = embed_and_lose_authority
    with pytest.raises(PermissionError):
        operation.execute(**scope)
    assert store.saved is None and store.marker == 'previous'


# --- a chunk never claims a more specific section than all of its text shares --------------------
def test_chunk_spanning_sibling_subsections_keeps_only_their_common_section():
    config = ChunkingConfig(100, 160, 0)  # no overlap: the chunk starts exactly at the first subsection
    text = ('## A\n\n' + paragraph('a', 100) + '\n\n' + paragraph('b', 100)
            + '\n\n### B1\n\nFirst detail.\n\n### B2\n\nSecond detail.\n')
    chunks = StructuredChunker(config).chunk_document(document(text, 'md'))['chunks']
    both = [chunk for chunk in chunks if 'First detail' in chunk['content'] and 'Second detail' in chunk['content']]
    assert len(both) == 1
    assert both[0]['metadata']['section_path'] == ['A']


def test_chunk_with_text_before_any_heading_claims_no_section():
    text = 'Preface without a heading.\n\n### A\n\nBody of the section.\n'
    result = StructuredChunker().chunk_document(document(text, 'md'))
    assert len(result['chunks']) == 1
    assert result['chunks'][0]['metadata']['section_path'] is None
