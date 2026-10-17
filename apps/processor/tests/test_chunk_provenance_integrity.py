"""Pre-publication validation rejects well-formed provenance that does not match the document."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.structural_chunker import StructuredChunker
from app.embeddings.tokenization import EmbeddingTokenCounter

FIXTURES = Path(__file__).parent/'fixtures/normalized_documents'
NAMES = ['digital.pdf', 'hybrid.pdf', 'mixed.pdf', 'plain.txt', 'scanned.pdf',
         'structure.doc', 'structure.docx', 'structure.md', 'table.pdf']


@pytest.fixture(scope='module')
def counter(): return EmbeddingTokenCounter()


def two_page_pdf():
    text = 'First evidence.\nSecond evidence.'
    return {'schema_version':1, 'document_id':'two-pages', 'tenant_id':'tenant-a', 'original_format':'pdf',
            'text':text, 'file_metadata':{}, 'blocks':[
                {'kind':'text', 'text':'First evidence.', 'page':1, 'bbox':[40.0, 40.0, 180.0, 55.0],
                 'coordinate_system':'pdf_points'},
                {'kind':'text', 'text':'Second evidence.', 'page':2, 'bbox':[40.0, 40.0, 190.0, 55.0],
                 'coordinate_system':'pdf_points'}]}


def spans(result):
    return [span for chunk in result['chunks'] for span in chunk['metadata']['source_spans']]


def test_existing_but_wrong_block_and_page_are_rejected(counter):
    source = two_page_pdf()
    chunker = StructuredChunker(ChunkingConfig(600, 800, 0.1), counter)
    result = chunker.chunk_document(source)
    first = next(span for span in spans(result) if span['block_ref'] == 'blocks/0')
    assert first['original']['page'] == 1
    corrupt = deepcopy(result)
    span = next(span for span in spans(corrupt) if span['block_ref'] == 'blocks/0')
    span['block_ref'] = 'blocks/1'
    span['original']['page'] = 999
    with pytest.raises(ValueError, match='Source annotations'):
        chunker.validate(source, corrupt)
    for change in ({'block_ref':'blocks/1'}, {'original':{**first['original'], 'page':999}}):
        corrupt = deepcopy(result)
        next(span for span in spans(corrupt) if span['block_ref'] == 'blocks/0').update(change)
        with pytest.raises(ValueError, match='Source annotations'):
            chunker.validate(source, corrupt)


@pytest.mark.parametrize('name', NAMES)
def test_actual_formats_validate_after_a_json_round_trip(name, counter):
    source = json.loads((FIXTURES/(name+'.json')).read_text())
    chunker = StructuredChunker(ChunkingConfig(32, 48, 0.1), counter)
    result = json.loads(json.dumps(chunker.chunk_document(source), ensure_ascii=False))
    chunker.validate(source, result)


@pytest.mark.parametrize('name', NAMES)
def test_invented_section_or_parent_range_is_rejected(name, counter):
    source = json.loads((FIXTURES/(name+'.json')).read_text())
    chunker = StructuredChunker(ChunkingConfig(32, 48, 0.1), counter)
    result = chunker.chunk_document(source)
    tampered = 0
    for key, value in (('section_path', ['Invented section']), ('parent_normalized_range', [0, 999]),
                       ('heading_level', 7), ('content_type', 'code')):
        corrupt = deepcopy(result)
        span = next((span for span in spans(corrupt) if span['block_ref'] is not None and key in span), None)
        if span is None or span[key] == value:
            continue
        span[key] = value
        with pytest.raises(ValueError, match='Source annotations'):
            chunker.validate(source, corrupt)
        tampered += 1
    assert tampered
    corrupt = deepcopy(result)
    corrupt['chunks'][0]['metadata']['section_path'] = ['Invented section']
    with pytest.raises(ValueError, match='section path'):
        chunker.validate(source, corrupt)
