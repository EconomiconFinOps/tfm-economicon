"""Contract invariants independent of tokenizer/dependency or splitting implementation."""
from copy import deepcopy
import json
import pytest
from app.embeddings.contracts import (
    ChunkingConfig, chunk_identity, document_identity, fingerprint, generation_identity,
)


def document():
    return {'schema_version':1,'document_id':'fixed-document','tenant_id':'tenant-a',
        'original_format':'md','text':'# Guía\n\nPresupuesto € 漢字 🙂\n','blocks':[
            {'kind':'heading','level':1,'text':'Guía','source_lines':[1,1]}],
        'origin':{'uploaded_at':'2026-10-15','uploaded_by':'operator'},'file_metadata':{}}


def test_defaults_and_overlap_are_based_on_configured_target():
    assert ChunkingConfig().identity()=={'target_tokens':600,'max_tokens':800,'overlap_ratio':0.1}
    assert ChunkingConfig().overlap_tokens==60
    assert ChunkingConfig(target_tokens=320).overlap_tokens==32
    assert ChunkingConfig(overlap_ratio=0).overlap_tokens==0


@pytest.mark.parametrize('values',[
    {'target_tokens':True},{'max_tokens':False},{'target_tokens':0},
    {'target_tokens':801},{'max_tokens':801},{'target_tokens':700,'max_tokens':600},
    {'overlap_ratio':True},{'overlap_ratio':-0.1},{'overlap_ratio':1},
    {'overlap_ratio':float('nan')},{'overlap_ratio':float('inf')},
])
def test_invalid_configuration_fails_before_processing(values):
    with pytest.raises(ValueError): ChunkingConfig(**values)


def test_generation_is_stable_and_separates_operational_and_structural_data():
    original=document()
    reference=generation_identity(original,ChunkingConfig(),'fixed-tokenizer-sha256')
    assert reference==generation_identity(deepcopy(original),ChunkingConfig(),'fixed-tokenizer-sha256')
    changed=deepcopy(original); changed['origin']['uploaded_at']='2030-01-01'
    assert reference==generation_identity(changed,ChunkingConfig(),'fixed-tokenizer-sha256')
    for mutation in ('blocks','text','document_id','tenant_id'):
        changed=deepcopy(original)
        if mutation=='blocks': changed['blocks'][0]['source_lines']=[2,2]
        else: changed[mutation]+=' different'
        assert fingerprint(reference)!=fingerprint(generation_identity(changed,ChunkingConfig(),'fixed-tokenizer-sha256'))
    assert reference!=generation_identity(original,ChunkingConfig(target_tokens=320),'fixed-tokenizer-sha256')
    assert reference!=generation_identity(original,ChunkingConfig(),'other-tokenizer')
    assert json.loads(json.dumps(reference,ensure_ascii=False))==reference


def test_identifiers_are_stable_versioned_and_ordered_without_claiming_job_equality():
    first=fingerprint(generation_identity(document(),ChunkingConfig(),'tokenizer'))
    second=fingerprint(generation_identity(document(),ChunkingConfig(target_tokens=320),'tokenizer'))
    assert chunk_identity('fixed-document',first,0)==chunk_identity('fixed-document',first,0)
    assert len({chunk_identity('fixed-document',first,0),chunk_identity('fixed-document',first,1),
        chunk_identity('other-document',first,0),chunk_identity('fixed-document',second,0)})==4
    with pytest.raises(ValueError): chunk_identity('fixed-document',first,True)


def test_unicode_and_incomplete_locations_remain_original_data():
    value=document(); value['blocks']=[]
    assert document_identity(value)['text']==value['text']
    assert document_identity(value)['blocks']==[]
    assert 'page' not in document_identity(value)
    invalid=deepcopy(value); invalid['text']='invalid\ud800'
    with pytest.raises(UnicodeEncodeError): document_identity(invalid)
