from dataclasses import replace
import hashlib
from copy import deepcopy
import pytest
from app.embeddings.context import prepare_embedding
from app.embeddings.space import EmbeddingSpace
from app.embeddings.tokenization import EmbeddingTokenCounter


@pytest.fixture(scope='module')
def counter():
    return EmbeddingTokenCounter()


def space(counter, preparation='contextual_embedding_v1'):
    return EmbeddingSpace('mock', 'mock/sha256_v1', 'a' * 64, counter.identity, preparation)


def test_context_is_deterministic_preserves_citation_content_and_omits_operational_values(counter):
    chunk = {'content': 'Threshold > 20%; equality does not qualify.\n漢字🙂',
             'metadata': {'content_type': 'paragraph', 'source_spans': [{'section_path': ['Rules', 'Strict limits']}]}}
    before = deepcopy(chunk)
    first = prepare_embedding(chunk, {'title': 'FinOps\nGuide', 'tenant_id': 'PRIVATE_TENANT'}, space(counter), counter)
    assert first == prepare_embedding(deepcopy(chunk), {'title': 'FinOps\nGuide'}, space(counter), counter)
    assert first.text.endswith('\n\n' + chunk['content']) and 'Sección: Rules > Strict limits' in first.text
    assert first.text_hash == hashlib.sha256(first.text.encode()).hexdigest()
    assert 'PRIVATE_TENANT' not in first.text and chunk == before
    assert first.text_hash != prepare_embedding(chunk, {}, space(counter, 'plain_v1'), counter).text_hash


def test_unknown_or_mixed_sections_never_get_one_false_heading(counter):
    chunk = {'content': 'Evidence.', 'metadata': {'source_spans': [{'section_path': ['Alpha']}, {'section_path': ['Beta']}]}}
    assert prepare_embedding(chunk, {}, space(counter), counter).text == chunk['content']
    chunk['metadata']['source_spans'][1]['section_path'] = []
    assert prepare_embedding(chunk, {}, space(counter), counter).text == chunk['content']
    chunk['metadata'] = {}
    assert prepare_embedding(chunk, {}, space(counter), counter).text == chunk['content']


def test_long_context_is_bounded_without_cutting_original_content(counter):
    chunk = {'content': 'Useful canonical evidence. ' * 100, 'metadata': {}}
    prepared = prepare_embedding(chunk, {'title': '漢字🙂' * 500}, replace(space(counter), context_tokens=16), counter)
    assert prepared.text.endswith(chunk['content'])
    assert prepared.token_count <= 1024 and 'embedding_context_truncated' in prepared.warnings
    with pytest.raises(ValueError, match='not truncated'):
        prepare_embedding({'content': 'x ' * 10000}, {}, space(counter), counter)


def test_character_caps_report_truncation_even_when_token_budget_fits(counter):
    chunk = {'content': 'Evidence.', 'metadata': {}}
    prepared = prepare_embedding(chunk, {'title': 'a' * 600}, space(counter), counter)
    assert prepared.text == 'Documento: ' + 'a' * 512 + '\n\nEvidence.'
    assert prepared.warnings == ('embedding_context_truncated',)
    assert prepare_embedding(chunk, {'title': 'a' * 512}, space(counter), counter).warnings == ()
    chunk['metadata'] = {'source_spans': [{'section_path': ['b' * 600]}]}
    assert prepare_embedding(chunk, {}, space(counter), counter).warnings == ('embedding_context_truncated',)
    chunk['metadata']['source_spans'].append({'section_path': ['b' * 512 + 'different']})
    assert prepare_embedding(chunk, {}, space(counter), counter).text == 'Evidence.'
    assert prepare_embedding(chunk, {'title': 'a' * 600}, space(counter, 'plain_v1'), counter).warnings == ()


def test_identity_contains_recipe_but_not_tenant_or_generation(counter):
    original = space(counter)
    assert original == EmbeddingSpace.from_descriptor(original.descriptor())
    assert original.id != replace(original, preparation='plain_v1').id
    assert original.id != replace(original, mapping_sha256='b' * 64).id
    assert 'tenant' not in original.descriptor() and 'generation' not in original.descriptor()
    with pytest.raises(ValueError):
        replace(original, model_id='unverified-model-with-1536-dimensions')


def test_markdown_title_cleaning_changes_only_contextual_input(counter):
    from app.documents.extractors import markdown
    from app.embeddings.normalized import parent_metadata
    from app.embeddings.structural_chunker import StructuredChunker
    value, blocks, metadata, warnings, method = markdown(b'# FinOps guide ###\n\nCanonical evidence.\n')
    document = {'schema_version': 1, 'document_id': 'synthetic', 'tenant_id': 'a',
        'original_format': 'md', 'text': value, 'blocks': blocks, 'file_metadata': metadata}
    before = deepcopy(document)
    result = StructuredChunker(counter=counter).chunk_document(document)
    parent = parent_metadata(document, result['manifest'])
    assert parent['title'] == 'FinOps guide'
    assert document == before and parent['content_hash'] == hashlib.sha256(value.encode()).hexdigest()
    chunk = result['chunks'][0]
    old = {**parent, 'title': blocks[0]['text']}
    contextual = prepare_embedding(chunk, parent, space(counter), counter)
    previous = prepare_embedding(chunk, old, space(counter), counter)
    assert contextual.text.startswith('Documento: FinOps guide\n')
    assert contextual.text.endswith(chunk['content']) and contextual.text != previous.text
    assert contextual.text_hash == hashlib.sha256(contextual.text.encode()).hexdigest()
    assert contextual.text_hash != previous.text_hash
    assert contextual.token_count == counter.count(contextual.text)
    assert prepare_embedding(chunk, parent, space(counter, 'plain_v1'), counter) == prepare_embedding(
        chunk, old, space(counter, 'plain_v1'), counter)
