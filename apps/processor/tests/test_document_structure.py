"""Canonical coverage and trustworthy annotations on fixed phase1 normalizations."""
import json
from pathlib import Path
import pytest
from app.embeddings.structure import structure

FIXTURES=Path(__file__).parent/'fixtures/normalized_documents'


def normalized(text,fmt='md',blocks=None):
    return {'schema_version':1,'document_id':'structure-fixture','tenant_id':'tenant-a','original_format':fmt,
            'text':text,'blocks':blocks or [],'file_metadata':{}}


@pytest.mark.parametrize('name',['digital.pdf','hybrid.pdf','mixed.pdf','plain.txt','scanned.pdf',
                                'structure.doc','structure.docx','structure.md','table.pdf'])
def test_real_frozen_phase1_documents_have_exact_ordered_coverage_without_reextraction(name):
    document=json.loads((FIXTURES/(name+'.json')).read_text())
    result=structure(document)
    assert ''.join(result.text[unit.start:unit.end] for unit in result.units)==document['text']
    assert all(left.end==right.start for left,right in zip(result.units,result.units[1:]))
    assert all(0<=item.start<=item.end<=len(document['text']) for item in result.annotations)
    assert structure(document)==result
    if name in {'structure.doc','structure.docx','structure.md','table.pdf'}:
        assert any(unit.kind=='table' for unit in result.units)
    if name.endswith(('.doc','.docx')):
        assert all('page' not in item.original and 'source_lines' not in item.original for item in result.annotations)


def test_markdown_frontmatter_fences_nested_lists_and_hierarchy_are_not_flat_text_guesses():
    text='---\n# metadata, not a section\ntitle: Test\n---\n# Parent\n\n## Child\n\n- First\n  - Nested\n- Second\n\n```python\n# code, not a section\nprint(42)\n```\n'
    result=structure(normalized(text))
    headings=[item.title for item in result.annotations if item.kind=='heading']
    assert headings==['Parent','Child']
    assert any(unit.kind=='code' for unit in result.units)
    assert any(unit.kind=='list' and len(unit.breaks)==2 for unit in result.units)
    assert {item.list_depth for item in result.annotations if item.kind=='list_item'}=={0,1}
    assert any(unit.section_path==('Parent','Child') for unit in result.units if unit.kind=='code')
    assert ''.join(text[x.start:x.end] for x in result.units)==text


def test_plain_text_does_not_invent_headings_or_original_locations():
    result=structure(normalized('# Literal text\n\nParagraph',fmt='manual-text'))
    assert not result.annotations
    assert all(not unit.section_path for unit in result.units)


def test_ambiguous_pdf_alignment_is_a_warning_not_an_extra_copy_or_fictional_page():
    document=normalized('Repeated\nRepeated\nUnmapped','pdf',[{'kind':'text','text':'Repeated','page':3}])
    result=structure(document)
    assert result.warnings==['pdf_source_block_not_aligned']
    assert not result.annotations
    assert ''.join(result.text[x.start:x.end] for x in result.units)==document['text']


def test_pdf_recognized_headings_are_used_but_not_inferred_from_ocr():
    document=normalized('Heading\nBody','pdf',[{'kind':'heading','text':'Heading','level':2,'page':1},
        {'kind':'text','text':'Body','page':1,'method':'ocr'}])
    result=structure(document)
    assert result.units[-1].section_path==('Heading',)
    assert len([x for x in result.annotations if x.kind=='heading'])==1


def test_word_consecutive_list_items_preserve_order_without_fabricating_depth():
    blocks=[{'kind':'heading','text':'Deep heading','level':7},
            {'kind':'list_item','text':'First'},{'kind':'list_item','text':'Second'}]
    result=structure(normalized('Deep heading\nFirst\nSecond','docx',blocks))
    lists=[unit for unit in result.units if unit.kind=='list']
    assert len(lists)==1 and len(lists[0].breaks)==2
    assert all(item.list_depth is None for item in result.annotations)
    assert result.units[-1].section_path==('Deep heading',)


@pytest.mark.parametrize('location',[{'page':0},{'page':True},{'source_lines':[2,1]},
    {'bbox':[2,0,1,2],'coordinate_system':'pdf_points'}])
def test_invalid_available_original_ranges_are_errors(location):
    with pytest.raises(ValueError): structure(normalized('Value','pdf',[{'kind':'text','text':'Value',**location}]))
