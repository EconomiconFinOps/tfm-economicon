"""Regressions for parser coordinates and recursive subsection preservation."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.documents.extractors import markdown
from app.documents.document_formats import FormatError
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.structure import structure
from app.embeddings.structural_chunker import StructuredChunker
from app.embeddings.tokenization import EmbeddingTokenCounter

CASES=Path(__file__).parent/'fixtures/chunking_cases'


@pytest.fixture(scope='module')
def counter():
    return EmbeddingTokenCounter()


def document(text):
    return {'schema_version':1,'document_id':'coordinate-regression','tenant_id':'synthetic',
            'original_format':'md','text':text,'blocks':[],'file_metadata':{}}


@pytest.mark.parametrize('separator',['\u2028','\u2029','\u0085','\v','\f','\x1c','\x1d','\x1e'])
@pytest.mark.parametrize('newline',['\n','\r\n','\r'])
def test_unicode_content_does_not_change_markdown_parser_line_coordinates(separator,newline,counter):
    text=newline.join(['# Alpha','','Alpha line'+separator+'Still Alpha'+separator+'Only Alpha',
                       '','# Beta','','Beta body',''])
    source=document(text)
    parsed=structure(source)
    beta=next(item for item in parsed.annotations if item.kind=='heading' and item.title=='Beta')
    expected=text.index('# Beta')
    assert (beta.start,beta.end)==(expected,expected+len('# Beta'+newline))
    assert text[beta.start:beta.end]=='# Beta'+newline
    chunker=StructuredChunker(counter=counter)
    result=chunker.chunk_document(source)
    assert result==chunker.chunk_document(deepcopy(source))
    assert any(separator in chunk['content'] for chunk in result['chunks'])
    for chunk in result['chunks']:
        for span in chunk['metadata']['source_spans']:
            if span['section_path']==['Beta']:
                assert span['normalized_range'][0]>=expected
    alpha=next(chunk for chunk in result['chunks'] if 'Only Alpha' in chunk['content'])
    assert all('Beta' not in span['section_path'] for span in alpha['metadata']['source_spans'])


@pytest.mark.parametrize('separator',['\u2028','\u2029','\u0085','\v','\f','\x1c','\x1d','\x1e'])
def test_real_markdown_extractor_block_text_and_chunk_reference_agree_after_unicode(separator,counter):
    raw=('# Alpha\n\nAlpha'+separator+'continued\n\n# Beta\n\nBeta body\n').encode('utf-8')
    if separator in {'\v','\x1c','\x1d','\x1e'}:
        with pytest.raises(FormatError,match='empty_or_binary_document'):
            markdown(raw)
        return
    text,blocks,metadata,warnings,method=markdown(raw)
    source={**document(text),'blocks':blocks,'file_metadata':metadata,'warnings':warnings,
            'extraction_method':method}
    heading=next(block for block in blocks if block['kind']=='heading' and block['source_lines']==[5,5])
    assert heading['text']=='# Beta'
    result=StructuredChunker(counter=counter).chunk_document(source)
    annotations=[span for chunk in result['chunks'] for span in chunk['metadata']['source_spans']
                 if span['heading_level']==1 and span['section_path']==['Beta']]
    assert annotations
    for span in annotations:
        assert text[slice(*span['normalized_range'])].rstrip('\r\n')=='# Beta'
        assert span['original']['source_lines']==[5,5]
        assert blocks[int(span['block_ref'].split('/')[1])]['text']=='# Beta'


@pytest.mark.parametrize('level',[3,4,5,6])
def test_fitting_subsection_keeps_condition_and_exception_inside_large_parent(level,counter):
    control=json.loads((CASES/'subsection-control.json').read_text(encoding='utf-8'))
    parent=json.loads((CASES/'subsection-large-parent.json').read_text(encoding='utf-8'))
    for value in (control,parent):
        value['text']=value['text'].replace('### Conditional rule','#'*level+' Conditional rule')
    assert parent['text'].endswith(control['text'])
    assert 600<counter.count(control['text'])<=800
    condition='When resource consumption exceeds both strict limits, escalate the account.'
    exception='Equality at either limit does not qualify; both comparisons are strict.'
    chunker=StructuredChunker(ChunkingConfig(),counter)
    for source in (control,parent):
        result=chunker.chunk_document(source)
        preserved=[chunk for chunk in result['chunks'] if condition in chunk['content'] and exception in chunk['content']]
        assert len(preserved)==1
        assert control['text'].rstrip() in preserved[0]['content']
        assert all(chunk['metadata']['token_count']<=800 for chunk in result['chunks'])
        assert result==chunker.chunk_document(deepcopy(source))


@pytest.mark.parametrize('newline',['\n','\r\n','\r'])
def test_frontmatter_mask_keeps_parser_line_endings_and_unicode_content(newline):
    text=newline.join(['---','title: Metadata\u2028literal','---','# Alpha','','Only Alpha\u2028continued','','# Beta','Body'])
    parsed=structure(document(text))
    headings=[item for item in parsed.annotations if item.kind=='heading']
    assert [item.title for item in headings]==['Alpha','Beta']
    assert headings[-1].start==text.index('# Beta')


def test_old_checkpoint_with_misaligned_markdown_block_has_explicit_unknown_reference(counter):
    text,blocks,metadata,warnings,method=markdown(b'# Alpha\n\nOnly Alpha\xe2\x80\xa8continued\n\n# Beta\n\nBeta body\n')
    beta=next(block for block in blocks if block['kind']=='heading' and block['source_lines']==[5,5])
    beta['text']='Only Alpha'  # A persisted checkpoint produced by the former line-domain bug.
    source={**document(text),'blocks':blocks,'file_metadata':metadata,'extraction_method':method}
    result=StructuredChunker(counter=counter).chunk_document(source)
    assert 'markdown_source_block_not_aligned' in result['manifest']['warnings']
    spans=[span for chunk in result['chunks'] for span in chunk['metadata']['source_spans']
           if span['heading_level']==1 and span['section_path']==['Beta']]
    assert spans and all(span['block_ref'] is None for span in spans)
    assert all(text[slice(*span['normalized_range'])].rstrip()=='# Beta' for span in spans)
    assert all(span['original']['source_lines']==[5,5] for span in spans)
