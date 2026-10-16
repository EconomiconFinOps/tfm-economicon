from app.schemas.assistant import SourceCitation
from app.services.citations import structured_location, resolve_citations


def metadata(spans,path=None):
    return {'source_spans':spans,'primary_spans':[{'normalized_range':[0,6],'content_range':[0,6]}],
            'section_path':path}


def span(start,end,page=None,path=None):
    return {'normalized_range':[start,end],'block_ref':None,'original':{'page':page} if page else {},
            'section_path':path or [],'heading_level':None}


def test_single_page_is_published_only_when_it_covers_all_meaningful_primary_text():
    parent={'chunking':{'position_contract':{'normalized_text':'unicode_codepoints:0-based:end-exclusive'}}}
    result=structured_location(metadata([span(0,3,7),span(3,6)],['Guide','Costs']),parent,'abc \n ')
    assert result['page']==7 and result['section']=='Guide / Costs'
    result=structured_location(metadata([span(0,3,7),span(3,6)]),parent,'abcdef')
    assert result['page'] is None


def test_multiple_pages_and_unknown_sections_are_preserved_without_false_single_location():
    result=structured_location(metadata([span(0,3,1),span(3,6,2)]),{},'abcdef')
    assert result['page'] is None and result['section'] is None
    assert [item['original']['page'] for item in result['source_spans']]==[1,2]


def test_structural_citation_roundtrips_source_positions_and_units():
    location=structured_location(metadata([span(0,6,7)],['Guide']),
        {'chunking':{'position_contract':{'original_pages':'1-based'}}},'abcdef')
    record={'chunk_id':'versioned-evidence','document_id':'document','tenant_id':'tenant','chunk_index':0,
            'title':'Guide','source':'guide.pdf','content':'abcdef',**location}
    [citation]=resolve_citations(['versioned-evidence'],[record],'tenant')
    assert citation['evidence_id']=='versioned-evidence' and citation['page']==7
    assert citation['position_contract']=={'original_pages':'1-based'}
    assert SourceCitation.model_validate(citation).source_spans==location['source_spans']


def test_new_declared_unknown_location_is_not_guessed_from_markdown_text():
    result=structured_location(metadata([span(0,6)]),{},'# Fake')
    assert result['section'] is None and result['page'] is None


def test_revalidating_a_legacy_citation_preserves_its_serialized_shape():
    legacy={'evidence_id':'legacy','kind':'corpus','document_id':'document','title':'Guide',
            'source':'guide','reference':'document:document/chunk:0','section':None,'page':None,'excerpt':'text'}
    assert SourceCitation.model_validate(legacy).model_dump()==legacy
