import copy
import json

import pytest

from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from app.core.chat_rules import validate_provenance


def fixture():
    content = ('KPI: Waste Cost % = Waste Cost / Eligible Cost * 100 '
        '- low: <= 3 %; - middle: > 3 % and <= 8 %; - high: > 8 %.')
    source={'id':'synthetic:rule','kind':'corpus','title':'Synthetic','source':'manual','content':content,
        'provenance':{'document_id':'synthetic','chunk_index':0,'sections':[
            {'start':0,'end':len(content),'section':'Waste','document_start':12,'section_start':0}]}}
    context={'authorized_evidence':[source],'messages':[
        {'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'waste: 8 EUR; remaining: 92 EUR.'})},
        {'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[source]})}]}
    catalog=context_quantities(context)
    leaf=lambda key:{'quantity':key+' EUR'}
    classification={'operation':'classify','rule_id':catalog.rules[0]['id'],'value':{
        'operation':'percentage','numerator':leaf('8'),
        'denominator':{'operation':'sum','left':leaf('8'),'right':leaf('92')}}}
    response={'answer':[{'text':'Escenario "😀": '},{'expression':classification}],
        'assumptions':[],'limitations':[],'next_actions':[],'recommendations':[],
        'evidence':[{'id':source['id'],'kind':'corpus'}]}
    return context,catalog,response


@pytest.mark.parametrize('width',[1,7,8192])
def test_classification_stream_equals_final_with_split_json_unicode(width):
    _,catalog,response=fixture()
    raw=json.dumps(response,ensure_ascii=True)
    parser=SegmentAnswerJSON([],quantities=catalog)
    streamed=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    assert streamed==parser.finish()==render_response(response,[],quantities=catalog)['answer']
    assert '): middle.' in streamed and '8 % <= 8 %' in streamed


@pytest.mark.parametrize('field',['answer','limitations','recommendations'])
def test_contradictory_conclusion_cannot_hide_in_other_public_fields(field):
    _,catalog,response=fixture()
    text='La clasificación es high.'
    if field=='answer':response[field]+=[{'text':text}]
    elif field=='recommendations':response[field]=[{'action':text,'rationale':'Review'}]
    else:response[field]=[[{'text':text}]]
    with pytest.raises(ValueError,match='Unverified documentary classification'):
        render_response(response,[],quantities=catalog)


def test_classification_prose_split_across_segments_is_rejected_before_publication():
    _,catalog,_=fixture()
    raw=json.dumps({'answer':[{'text':'La clasifi'},{'text':'cación es high.'}]})
    with pytest.raises(ValueError,match='Unverified documentary classification'):
        SegmentAnswerJSON([],quantities=catalog).feed(raw)


@pytest.mark.parametrize('mutation',['section','range','source_id'])
def test_documentary_provenance_changes_fail_exact_context_authorization(mutation):
    context,_,_=fixture()
    changed=copy.deepcopy(context['authorized_evidence'][0])
    if mutation=='section':changed['provenance']['sections'][0]['section']='Budget'
    elif mutation=='range':changed['provenance']['sections'][0]['document_start']+=1
    else:changed['id']='other-tenant:rule'
    context['messages'][1]['content']='UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[changed]})
    with pytest.raises(ValueError,match='not authorized'):context_quantities(context)


def test_non_partitioned_section_metadata_is_rejected():
    context,_,_=fixture()
    source=context['authorized_evidence'][0]
    source['provenance']['sections'][0]['end']-=1
    with pytest.raises(ValueError,match='Incomplete'):validate_provenance(source)


@pytest.mark.parametrize('message,code',[
    ('Classification shape.','classification_shape'),
    ('Unknown documentary interval rule.','classification_unknown_rule'),
    ('Documentary KPI value mismatch.','classification_kpi_mismatch'),
    ('Documentary interval unit mismatch.','classification_unit_mismatch'),
    ('Ambiguous documentary interval.','classification_ambiguous_interval'),
    ('Unverified documentary classification prose.','classification_unverified_prose'),
    ('Unverified documentary classification prose. SECRET',None),
])
def test_interval_diagnostics_are_exact_closed_codes_without_rejected_text(message,code,caplog):
    from app.clients.chat_gateway import _record_diagnostic
    _record_diagnostic('provisional_answer',ValueError(message),'0'*64,None)
    event=json.loads(caplog.records[-1].message)
    assert event.get('rule_code')==code
    assert 'SECRET' not in caplog.text and message not in caplog.text
