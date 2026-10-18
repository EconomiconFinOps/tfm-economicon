"""Behavioral chunking regressions: integrity, structures, Unicode, provenance and budgets."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.embeddings.contracts import ChunkingConfig, chunk_identity
from app.embeddings.structural_chunker import StructuredChunker
from app.embeddings.tokenization import EmbeddingTokenCounter

FIXTURES=Path(__file__).parent/'fixtures/normalized_documents'


def document(text,fmt='manual-text',blocks=None):
    return {'schema_version':1,'document_id':'fixed-document','tenant_id':'tenant-a',
            'original_format':fmt,'text':text,'blocks':blocks or [],'file_metadata':{}}


@pytest.fixture(scope='module')
def counter(): return EmbeddingTokenCounter()


@pytest.mark.parametrize('name',['digital.pdf','hybrid.pdf','mixed.pdf','plain.txt','scanned.pdf',
                                'structure.doc','structure.docx','structure.md','table.pdf'])
@pytest.mark.parametrize('settings',[(32,48,0.1),(600,800,0.1)])
def test_actual_normalized_formats_are_deterministic_integral_and_bounded(name,settings,counter):
    source=json.loads((FIXTURES/(name+'.json')).read_text())
    chunker=StructuredChunker(ChunkingConfig(*settings),counter)
    first=chunker.chunk_document(source)
    assert first==chunker.chunk_document(deepcopy(source))
    assert first['chunks']
    assert all(counter.count(chunk['content'])<=settings[1] for chunk in first['chunks'])
    assert json.loads(json.dumps(first,ensure_ascii=False))==first
    if name.endswith(('.doc','.docx')):
        assert all('page' not in span['original'] and 'source_lines' not in span['original']
                   for chunk in first['chunks'] for span in chunk['metadata']['source_spans'])


@pytest.mark.parametrize('text',['','Only one short paragraph.','x'*12000,'漢字🙂 café '*800,
                               'Repeat this useful paragraph.\n\n'*160])
@pytest.mark.parametrize('overlap',[0,0.1,0.9])
def test_empty_small_long_repeated_unicode_and_extreme_overlap(text,overlap,counter):
    source=document(text)
    chunker=StructuredChunker(ChunkingConfig(48,64,overlap),counter)
    result=chunker.chunk_document(source)
    assert bool(result['chunks'])==bool(text.strip())
    chunker.validate(source,result)
    assert result==chunker.chunk_document(source)
    assert all('\ufffd' not in chunk['content'] for chunk in result['chunks'])


def test_business_condition_and_strict_threshold_clarification_use_general_section_grouping(counter):
    root=Path(__file__).resolve().parents[3]
    text=(root/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text()
    result=StructuredChunker(counter=counter).chunk_document(document(text,'md'))
    containing=[chunk for chunk in result['chunks'] if 'relative_delta > 20' in chunk['content']]
    assert len(containing)==1
    assert 'absolute_delta > 100 EUR/day' in containing[0]['content']
    assert 'estrict' in containing[0]['content'].lower()
    # The same structural relation must work without that literal business sentence.
    generic='# Parent\n\n## Condition\n\nA condition applies to all objects.\n\n```text\nx > y AND z > w\n```\n\nEquality does not satisfy either comparison.\n'
    result=StructuredChunker(counter=counter).chunk_document(document(generic,'md'))
    assert any('x > y' in chunk['content'] and 'Equality does not satisfy' in chunk['content'] for chunk in result['chunks'])


@pytest.mark.parametrize('body',['\n'.join(f'| Resource {i} | {i} EUR |' for i in range(80)),
                                '| '+('漢🙂'*500)+' | value |'])
def test_large_table_and_cell_keep_headers_order_and_explicit_fragments(body,counter):
    text='| Resource | Cost |\n|---|---|\n'+body+'\n'
    source=document(text,'md')
    chunker=StructuredChunker(ChunkingConfig(48,64,0.1),counter)
    result=chunker.chunk_document(source)
    assert len(result['chunks'])>1
    fragments=[fragment for chunk in result['chunks'] for fragment in chunk['metadata']['fragments']]
    assert len({item['fragment_group_id'] for item in fragments})==1
    assert [item['fragment_index'] for item in fragments]==list(range(1,len(fragments)+1))
    assert all(item['fragment_count']==len(fragments) for item in fragments)
    assert any(item['reason'].startswith('table_header') for chunk in result['chunks'] for item in chunk['metadata']['repetitions'])
    assert all(chunk['metadata']['content_type']=='table' for chunk in result['chunks'])


def test_code_lines_and_oversize_line_preserve_exact_unicode_content(counter):
    text='```python\n'+''.join(f'print("presupuesto {i}")\n' for i in range(80))+'value="'+('漢🙂'*300)+'"\n```\n'
    source=document(text,'md')
    result=StructuredChunker(ChunkingConfig(48,64,0.1),counter).chunk_document(source)
    assert len(result['chunks'])>2
    assert all(chunk['metadata']['content_type']=='code' for chunk in result['chunks'])
    assert any(item['split_reason'].startswith('code_') for chunk in result['chunks'] for item in chunk['metadata']['fragments'])
    assert all(any(span.get('language')=='python' for span in chunk['metadata']['source_spans']) for chunk in result['chunks'])


def test_nested_list_preserves_parent_relationship_and_txt_keeps_item_boundaries(counter):
    source=document('- Parent\n  - Child\n  - Second child\n- Other parent\n','md')
    result=StructuredChunker(counter=counter).chunk_document(source)
    children=[span for chunk in result['chunks'] for span in chunk['metadata']['source_spans'] if span.get('list_depth')==1]
    assert children and all(span['parent_normalized_range'] for span in children)
    source=document('Introductory context.\n\n'+''.join(f'- Item {i} preserves a complete operation.\n' for i in range(100)),'txt')
    result=StructuredChunker(ChunkingConfig(48,64,0),counter).chunk_document(source)
    assert any(fragment['split_reason']=='list_items' for chunk in result['chunks'] for fragment in chunk['metadata']['fragments'])


def test_independent_sections_never_overlap_and_multiple_subsections_keep_all_provenance(counter):
    text='# Root\n\n## Independent A\n\nAlpha details.\n\n### A child\n\nChild details.\n\n## Independent B\n\nBeta details.\n'
    source=document(text,'md')
    result=StructuredChunker(counter=counter).chunk_document(source)
    assert len(result['chunks'])==2
    assert all(not chunk['metadata']['repetitions'] for chunk in result['chunks'])
    first=result['chunks'][0]
    assert any(span['section_path']==['Root','Independent A','A child'] for span in first['metadata']['source_spans'])
    assert all('Beta details' not in chunk['content'] for chunk in result['chunks'][:1])


def test_effective_overlap_is_recorded_and_not_claimed_to_be_exactly_the_configured_target(counter):
    source=document('Long sentence with useful cost context. '*200)
    result=StructuredChunker(ChunkingConfig(48,64,0.1),counter).chunk_document(source)
    assert any(chunk['metadata']['effective_overlap_tokens']>0 for chunk in result['chunks'][1:])
    assert all(chunk['metadata']['effective_overlap_tokens']<=4 for chunk in result['chunks'])


def test_explicit_trailing_whitespace_is_not_sent_as_thousands_of_empty_chunks(counter):
    source=document('Boundary evidence.'+' '*200_000)
    result=StructuredChunker(counter=counter).chunk_document(source)
    assert len(result['chunks'])==1
    assert result['manifest']['ignored_whitespace_ranges']==[[len('Boundary evidence.'),len(source['text'])]]


def test_packed_related_paragraphs_have_measured_overlap(counter):
    source=document('\n\n'.join('Related paragraph number '+str(i)+' explains a useful operational detail.' for i in range(60)))
    result=StructuredChunker(ChunkingConfig(48,64,0.1),counter).chunk_document(source)
    assert len(result['chunks'])>2
    assert all(0<chunk['metadata']['effective_overlap_tokens']<=4 for chunk in result['chunks'][1:])


def test_table_rows_and_word_cells_have_real_grid_locations(counter):
    source=json.loads((FIXTURES/'structure.docx.json').read_text())
    result=StructuredChunker(counter=counter).chunk_document(source)
    locations=[span['original'] for chunk in result['chunks'] for span in chunk['metadata']['source_spans']]
    assert any(location.get('column_range')==[1,2] and location.get('row_range')==[1,2] for location in locations)


def test_all_unannotated_ranges_are_explicit_even_when_other_spans_exist(counter):
    source=document('## A\n\nBody.\n\n## B\n\nMore body.','md')
    result=StructuredChunker(counter=counter).chunk_document(source)
    for chunk in result['chunks']:
        for primary in chunk['metadata']['primary_spans']:
            start,end=primary['normalized_range']
            spans=chunk['metadata']['source_spans']
            assert all(any(left<=point<right for left,right in (item['normalized_range'] for item in spans))
                       for point in range(start,end))


def test_prepublication_validation_rejects_corruption_missing_refs_reordering_and_lost_content(counter):
    source=document('A useful repeated sentence. '*160)
    chunker=StructuredChunker(ChunkingConfig(48,64,0.1),counter)
    original=chunker.chunk_document(source)
    assert len(original['chunks'])>1
    corrupt=deepcopy(original); corrupt['chunks'][0]['content']+='injected'
    with pytest.raises(ValueError): chunker.validate(source,corrupt)
    corrupt=deepcopy(original); corrupt['chunks'][0]['metadata']['source_spans'][0]['block_ref']='blocks/999'
    with pytest.raises(ValueError): chunker.validate(source,corrupt)
    corrupt=deepcopy(original); corrupt['chunks'].pop()
    with pytest.raises(ValueError): chunker.validate(source,corrupt)
    corrupt=deepcopy(original); corrupt['chunks'][0],corrupt['chunks'][1]=corrupt['chunks'][1],corrupt['chunks'][0]
    for i,chunk in enumerate(corrupt['chunks']):
        chunk['chunk_index']=i; chunk['chunk_id']=chunk_identity(source['document_id'],corrupt['manifest']['fingerprint'],i)
    with pytest.raises(ValueError): chunker.validate(source,corrupt)


@pytest.mark.parametrize('indent',['  ','\t'])
@pytest.mark.parametrize('overlap',[0,0.1])
def test_fragmented_txt_nested_children_keep_their_actual_parent(indent,overlap,counter):
    from app.embeddings.structure import structure
    first='- Project Alpha has the restricted operating budget.\n'
    second='- Project Beta permits a different operating budget.\n'
    text=first+''.join(f'{indent}- Alpha resource {i} retains its own cost condition.\n' for i in range(100))
    second_start=len(text)
    text+=second+''.join(f'{indent}- Beta resource {i} retains its own cost condition.\n' for i in range(100))
    parents=[[0,second_start],[second_start,len(text)]]
    source=document(text,'txt',[{'kind':'text','text':text,'source_lines':[1,202]}])
    structured=structure(source)
    assert [unit.breaks for unit in structured.units if unit.kind=='list']==[(second_start,len(text))]
    chunker=StructuredChunker(ChunkingConfig(48,64,overlap),counter)
    result=chunker.chunk_document(source)
    chunker.validate(source,result)
    assert result==chunker.chunk_document(deepcopy(source))
    assert all(chunk['metadata']['token_count']<=64 for chunk in result['chunks'])
    assert ''.join(text[a:b] for chunk in result['chunks']
                   for a,b in (span['normalized_range'] for span in chunk['metadata']['primary_spans']))==text
    separated=set()
    for chunk in result['chunks']:
        child_spans=[span for span in chunk['metadata']['source_spans'] if span.get('list_depth')==1]
        for span in child_spans:
            parent_index=int(span['normalized_range'][0]>=second_start)
            assert span['parent_normalized_range']==parents[parent_index]
            if (first if parent_index==0 else second).strip() not in chunk['content']:
                separated.add(parent_index)
    assert separated=={0,1},'Both parents must have independently traceable children in later chunks'


def test_plain_list_indentation_has_stable_nested_parent_ranges_and_no_fictional_origin():
    from app.embeddings.structure import structure
    text='Intro\n\n  1. Root\n    - Child\n      + Grandchild\n    - Sibling\n  2. Next root\n\nOutro'
    result=structure(document(text,'manual-text'))
    items=[item for item in result.annotations if item.kind=='list_item']
    assert [item.list_depth for item in items]==[0,1,2,1,0]
    assert items[1].parent_normalized_range==(items[0].start,items[0].end)
    assert items[2].parent_normalized_range==(items[1].start,items[1].end)
    assert items[3].parent_normalized_range==(items[0].start,items[0].end)
    assert items[4].parent_normalized_range is None
    assert all(item.original=={} and item.block_ref is None for item in items)
    assert ''.join(text[unit.start:unit.end] for unit in result.units)==text
