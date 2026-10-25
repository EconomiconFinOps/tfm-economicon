"""Exact recovery from chunks alone, with the normalized document only as oracle."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.embeddings.contracts import ChunkingConfig
from app.embeddings.structural_chunker import StructuredChunker, reconstruct_normalized_text
from app.embeddings.tokenization import EmbeddingTokenCounter

FIXTURES=Path(__file__).parent/'fixtures/normalized_documents'


def assert_frozen_source_trace(source, chunks):
    """Contrast emitted pointers and locations with the frozen normalized source."""
    import re
    for chunk in chunks:
        assert chunk['document_id']==source['document_id']
        tracked=chunk['metadata']['primary_spans']+chunk['metadata']['repetitions']
        for span in chunk['metadata']['source_spans']:
            start,end=span['normalized_range']
            actual=source['text'][start:end]
            carriers=[item for item in tracked
                      if item['normalized_range'][0]<=start<end<=item['normalized_range'][1]]
            assert carriers
            for carrier in carriers:
                offset=carrier['content_range'][0]+start-carrier['normalized_range'][0]
                assert chunk['content'][offset:offset+end-start]==actual
            ref=span['block_ref']
            if ref is None:
                continue
            value=source; ancestors=[]
            for component in ref.split('/'):
                ancestors.append(value)
                value=value[int(component)] if isinstance(value,list) else value[component]
            owners=[item for item in ancestors+[value] if isinstance(item,dict)]
            location=span['original']
            for key in ('page','bbox','coordinate_system','method'):
                if key in location:
                    assert any(item.get(key)==location[key] for item in owners)
            if 'source_lines' in location:
                first,last=location['source_lines']
                assert any(item.get('source_lines') and item['source_lines'][0]<=first<=last<=item['source_lines'][1]
                           for item in owners)
                # Markdown uses CommonMark CR/LF lines; TXT uses its extractor's line contract.
                lines=source['text'].split('\n') if source['original_format']=='md' else source['text'].splitlines()
                assert actual.rstrip('\r\n') in '\n'.join(lines[first-1:last])
            def word_block(block):
                if block.get('kind')=='table':
                    return '\n'.join('\t'.join('\n'.join(word_block(item) for item in cell)
                                               for cell in row) for row in block['rows'])
                return block.get('text','')
            if isinstance(value,dict) and 'text' in value:
                referenced=value['text']
            elif isinstance(value,dict) and value.get('kind')=='table':
                referenced=(word_block(value) if source['original_format'] in {'doc','docx'} else '\n'.join(' '.join(str(cell) for cell in row if cell is not None) for row in value['rows']))
            elif isinstance(value,list) and '/rows/' in ref:
                depth=len(ref.split('/rows/',1)[1].split('/'))
                if source['original_format'] in {'doc','docx'}:
                    referenced=('\t'.join('\n'.join(word_block(item) for item in cell) for cell in value)
                                if depth==1 else '\n'.join(word_block(item) for item in value))
                else:
                    referenced=' '.join(str(item) for item in value if item is not None)
            else:
                raise AssertionError('Unknown referenced block shape')
            assert re.sub(r'\s+',' ',actual).strip() in re.sub(r'\s+',' ',referenced).strip()


@pytest.fixture(scope='module')
def chunker():
    return StructuredChunker(ChunkingConfig(32,48,0.1),EmbeddingTokenCounter())


def document(text,fmt='md'):
    return {'schema_version':1,'document_id':'exact-reconstruction','tenant_id':'synthetic',
            'original_format':fmt,'text':text,'blocks':[],'file_metadata':{}}


@pytest.mark.parametrize('name',sorted(path.name for path in FIXTURES.glob('*.json')))
def test_reconstruction_of_each_real_extracted_format_uses_only_chunk_substrings(chunker,name):
    source=json.loads((FIXTURES/name).read_text(encoding='utf-8'))
    chunks=chunker.chunk_document(source)['chunks']
    # The reconstruction call cannot see source or the chunking manifest.
    actual=reconstruct_normalized_text(list(reversed(deepcopy(chunks))))
    assert actual==source['text']
    assert_frozen_source_trace(source,chunks)


@pytest.mark.parametrize('value',[
    'Plain text\n\t \n', '  \t\r\n',
    '# One\n\nAlpha 漢字🙂\n\n\n# Two\n\nBeta café\n\t ',
    '| Resource | Cost |\n|---|---|\n'+''.join(f'| Service {i} | {i} EUR |\n' for i in range(80)),
    '- Parent\n'+''.join(f'  - Child {i} retains its source condition.\n' for i in range(100)),
    '```python\n'+('print("漢🙂")\n'*100)+'```\n',
])
def test_overlap_headers_whitespace_and_unicode_are_recovered_exactly(chunker,value):
    source=document(value)
    result=chunker.chunk_document(source)
    assert reconstruct_normalized_text(result['chunks'])==value
    assert all(chunk['metadata']['token_count']<=48 for chunk in result['chunks'])
    assert_frozen_source_trace(source,result['chunks'])


def test_large_omitted_whitespace_remains_metadata_and_is_not_embedded_as_empty_chunks(chunker):
    value='Evidence.'+' \t\n'*10_000
    result=chunker.chunk_document(document(value,'txt'))
    assert len(result['chunks'])==1
    assert result['chunks'][0]['content']=='Evidence.'
    assert reconstruct_normalized_text(result['chunks'])==value


@pytest.mark.parametrize('mutation',['first','middle','last','duplicate','mixed','content','range','repetition','descriptor','fragments','huge-fragment-count'])
def test_incomplete_or_incoherent_sets_fail_without_an_original_document(chunker,mutation):
    value='| Item | Value |\n|---|---|\n'+''.join(f'| Resource {i} | {i} EUR |\n' for i in range(60))
    chunks=deepcopy(chunker.chunk_document(document(value))['chunks'])
    assert len(chunks)>3
    if mutation in {'first','middle','last'}:
        del chunks[{'first':0,'middle':len(chunks)//2,'last':len(chunks)-1}[mutation]]
    elif mutation=='duplicate': chunks.append(deepcopy(chunks[-1]))
    elif mutation=='mixed': chunks[-1]['document_id']='another-document'
    elif mutation=='content': chunks[-1]['content']+='corruption'
    elif mutation=='range': chunks[-1]['metadata']['primary_spans'][0]['normalized_range'][0]+=1
    elif mutation=='repetition': chunks[1]['metadata']['repetitions'][0]['normalized_range']=[1,1+len(chunks[1]['content'].splitlines()[0])]
    elif mutation=='descriptor': chunks[0]['metadata']['reconstruction']['document_text_sha256']='0'*64
    elif mutation=='fragments': chunks[-1]['metadata']['fragments'][0]['fragment_count']+=1
    elif mutation=='huge-fragment-count':
        for chunk in chunks:
            for fragment in chunk['metadata']['fragments']: fragment['fragment_count']=10**12
    with pytest.raises(ValueError): reconstruct_normalized_text(chunks)


def test_empty_and_legacy_sets_have_an_explicit_unsupported_result():
    with pytest.raises(ValueError,match='No chunks'): reconstruct_normalized_text([])
    with pytest.raises(ValueError,match='unavailable'):
        reconstruct_normalized_text([{'chunk_index':0,'metadata':{}}])


@pytest.mark.parametrize('separator',[' '*200_000,'\t'*20_000,'\u00a0'*20_000],ids=['spaces','tabs','unicode-spaces'])
@pytest.mark.parametrize('config',[ChunkingConfig(600,800,0.1),ChunkingConfig(32,48,0)],ids=['default-overlap','small-no-overlap'])
def test_interior_whitespace_omissions_keep_complete_persisted_fragment_groups(separator,config):
    value='Before.'+separator+'After.'
    result=StructuredChunker(config,EmbeddingTokenCounter()).chunk_document(document(value,'txt'))
    chunks=result['chunks']
    assert reconstruct_normalized_text(deepcopy(chunks))==value
    assert all(chunk['content'].strip() for chunk in chunks)
    assert all(chunk['metadata']['token_count']<=config.max_tokens for chunk in chunks)
    assert any(0<span['normalized_range'][0]<span['normalized_range'][1]<len(value)
               for span in chunks[0]['metadata']['reconstruction']['omitted_spans'])
    fragments=[fragment for chunk in chunks for fragment in chunk['metadata']['fragments']]
    assert len(fragments)>1
    assert len({fragment['fragment_group_id'] for fragment in fragments})==1
    assert [fragment['fragment_index'] for fragment in fragments]==list(range(1,len(fragments)+1))
    assert all(fragment['fragment_count']==len(fragments) for fragment in fragments)


@pytest.mark.parametrize('mutation',['missing-fragment','duplicate-fragment-index'])
def test_actual_fragment_corruption_still_fails_with_intentional_whitespace_omissions(mutation):
    value='Before.'+' '*200_000+'After.'
    chunks=deepcopy(StructuredChunker(ChunkingConfig(),EmbeddingTokenCounter()).chunk_document(document(value,'txt'))['chunks'])
    records=[fragment for chunk in chunks for fragment in chunk['metadata']['fragments']]
    assert len(records)>1
    if mutation=='missing-fragment':
        chunks[-1]['metadata']['fragments'].pop()
    else:
        records[-1]['fragment_index']=records[0]['fragment_index']
    with pytest.raises(ValueError,match='fragment'):
        reconstruct_normalized_text(chunks)
