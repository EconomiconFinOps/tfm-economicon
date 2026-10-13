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
            {'start':0,'end':len(content),'section':'Waste 😀','document_start':12,'section_start':0}]}}
    context={'authorized_evidence':[source],'messages':[
        {'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'waste: 8 EUR; remaining: 92 EUR.'})},
        {'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[source]})}]}
    catalog=context_quantities(context)
    leaf=lambda key:{'quantity':key+' EUR'}
    classification={'operation':'classify','rule_id':catalog.rules[0]['id'],'value':{
        'operation':'percentage','numerator':leaf('8'),
        'denominator':{'operation':'sum','left':leaf('8'),'right':leaf('92')}}}
    response={'answer':{'calculations':[],'classification':classification},
        'assumptions':[],'limitations':[],'next_actions':[],'recommendations':[],'metrics':[],
        'evidence':[]}
    return context,catalog,response


@pytest.mark.parametrize('width',[1,7,8192])
def test_classification_stream_equals_final_with_split_json_unicode(width):
    _,catalog,response=fixture()
    raw=json.dumps(response,ensure_ascii=True)
    parser=SegmentAnswerJSON([],quantities=catalog)
    streamed=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    assert streamed==parser.finish()==render_response(response,[],quantities=catalog)['answer']
    assert '): middle.' in streamed and '8 % <= 8 %' in streamed
    assert 'Waste 😀' in streamed


@pytest.mark.parametrize('field',['answer','limitations','recommendations'])
def test_contradictory_conclusion_cannot_hide_in_other_public_fields(field):
    _,catalog,response=fixture()
    text='La clasificación es high.'
    if field=='answer':response[field]['conclusion']=text
    elif field=='recommendations':response[field]=[{'action':text,'rationale':'Review'}]
    else:response[field]=[[{'text':text}]]
    with pytest.raises(ValueError,match='Invalid classified'):
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
    ('Documentary calculation citation missing.','documentary_calculation_citation_missing'),
    ('Invalid canonical subscriptions.','invalid_canonical_subscriptions'),
    ('Invalid authorized evidence.','invalid_authorized_evidence'),
    ('Unverified documentary classification prose. SECRET',None),
])
def test_interval_diagnostics_are_exact_closed_codes_without_rejected_text(message,code,caplog):
    from app.clients.chat_gateway import _record_diagnostic
    _record_diagnostic('provisional_answer',ValueError(message),'0'*64,None)
    event=json.loads(caplog.records[-1].message)
    assert event.get('rule_code')==code
    assert 'SECRET' not in caplog.text and message not in caplog.text


def test_classified_duplicate_and_truncated_object_never_finishes():
    _,catalog,response=fixture()
    raw=json.dumps({'answer':response['answer']})
    duplicate=raw.replace('"calculations": []','"calculations": [], "calculations": []')
    with pytest.raises(ValueError,match='Duplicate'):
        SegmentAnswerJSON([],quantities=catalog).feed(duplicate)
    parser=SegmentAnswerJSON([],quantities=catalog)
    parser.feed(raw[:-2])
    with pytest.raises(ValueError,match='Incomplete'):parser.finish()


def test_classified_calculations_and_terminal_share_operation_budget():
    _,catalog,response=fixture()
    leaf={'quantity':'8 EUR'}
    node={'operation':'sum','left':{'operation':'sum','left':leaf,'right':leaf},
          'right':{'operation':'sum','left':leaf,'right':leaf}}
    response['answer']['calculations']=[node]*4
    assert render_response(response,[],quantities=catalog)['answer']
    # Four distinct depth-three trees plus terminal bounds exceed twelve
    # real evaluations, even though their leaves and some children repeat.
    def binary(operation,a,b):
        keys=('left','right') if operation=='sum' else ('current','baseline')
        return {'operation':operation,keys[0]:a,keys[1]:b}
    response['answer']['calculations']=[
        binary(outer,binary(inner,binary('sum',leaf,leaf),leaf),{'quantity':'92 EUR'})
        for outer in ('sum','difference') for inner in ('sum','difference')]
    with pytest.raises(ValueError,match='operation limit'):
        render_response(response,[],quantities=catalog)
    with pytest.raises(ValueError,match='operation limit'):
        SegmentAnswerJSON([],quantities=catalog).feed(json.dumps(response))


@pytest.mark.parametrize('field',['before','after'])
def test_classified_object_rejects_prose_in_either_position(field):
    _,catalog,response=fixture()
    response['answer']={field:'La clasificación es high.',**response['answer']}
    with pytest.raises(ValueError,match='Invalid classified answer'):
        SegmentAnswerJSON([],quantities=catalog).feed(json.dumps(response))


def test_all_classified_notes_are_closed_server_wording_not_new_assertions():
    from app.core.chat_segments import CLASSIFIED_NOTES
    _,catalog,response=fixture()
    response['assumptions']=[[{'text':note}] for note in CLASSIFIED_NOTES]
    response['limitations']=[[{'text':note}] for note in CLASSIFIED_NOTES]
    rendered=render_response(response,[],quantities=catalog)
    assert rendered['assumptions']==rendered['limitations']==list(CLASSIFIED_NOTES)


def test_server_citations_require_exact_authenticated_records_and_are_not_json_flags():
    from app.agents.schemas import assemble_chat_response
    from app.core.chat_segments import ServerRenderedResponse
    from test_chat_server_period_jup035 import provider_answer
    context,catalog,response=fixture()
    response={**provider_answer(),**response,'status':'ok'}
    rendered=render_response(response,[],quantities=catalog)
    assert type(rendered) is ServerRenderedResponse
    source=context['authorized_evidence'][0]
    expected={key:source[key] for key in ('id','kind','title','source')}
    assert rendered['evidence']==[expected]
    assert 'support_quote' not in rendered['evidence'][0]
    result=assemble_chat_response(rendered,None,authorized_evidence=[source])
    assert result['evidence']==[expected]
    for authorized in [[],[{**source,'id':'other-tenant'}],[{**source,'title':'changed'}],[{**source,'content':source['content']+' altered'}]]:
        with pytest.raises(ValueError,match='Derived documentary evidence mismatch'):
            assemble_chat_response(rendered,None,authorized_evidence=authorized)
    changed=copy.deepcopy(rendered);changed['evidence'][0]['extra']='untrusted'
    with pytest.raises(ValueError,match='Derived documentary evidence mismatch'):
        assemble_chat_response(changed,None,authorized_evidence=[source])
    serialized=json.loads(json.dumps(rendered))
    with pytest.raises(ValueError,match='Citation passage is not grounded'):
        assemble_chat_response(serialized,None,authorized_evidence=[source])
    serialized['server_derived']=True
    with pytest.raises(ValueError):assemble_chat_response(serialized,None,authorized_evidence=[source])
    for evidence in [[expected],[{**expected,'support_quote':source['content']}],None]:
        with pytest.raises(ValueError,match='Classified evidence is server-owned'):
            render_response({**response,'evidence':evidence},[],quantities=catalog)


def test_server_citations_do_not_include_unused_rules_or_user_quantities():
    context,catalog,response=fixture()
    source=context['authorized_evidence'][0]
    unused={**source,'id':'unused-source','content':'Unrelated reference 17 EUR.'}
    catalog.rule_sources=[*catalog.rule_sources,unused]
    rendered=render_response(response,[],quantities=catalog)
    assert [item['id'] for item in rendered['evidence']]==[source['id']]
    catalog.rule_sources=[]
    with pytest.raises(ValueError,match='Derived documentary source unavailable'):
        render_response(response,[],quantities=catalog)


def test_long_source_server_citation_does_not_fabricate_a_first_window_quote():
    from app.agents.schemas import assemble_chat_response
    from test_chat_server_period_jup035 import provider_answer
    context,catalog,response=fixture()
    original=context['authorized_evidence'][0]
    source={**original,'content':'x'*3000+' '+original['content']}
    # The catalog retains the exact authenticated source used during rendering;
    # no model quotation or arbitrary 2048-character prefix is manufactured.
    source['provenance']=copy.deepcopy(original['provenance'])
    source['provenance']['sections'][0]['end']=len(source['content'])
    context['authorized_evidence']=[source]
    context['messages'][-1]['content']='UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[source]})
    catalog=context_quantities(context)
    assert len(catalog.rules)==1
    response={**provider_answer(),**response,'status':'ok'}
    rendered=render_response(response,[],quantities=catalog)
    result=assemble_chat_response(rendered,None,authorized_evidence=[source])
    assert result['evidence'][0]['id']==source['id']
    assert all('support_quote' not in item for item in rendered['evidence'])


def test_additional_documentary_operand_adds_only_its_authenticated_source():
    context,catalog,response=fixture()
    extra={'id':'operand-source','kind':'corpus','title':'Operand','source':'manual','content':'Coste observado: 23 EUR.'}
    records=[*context['authorized_evidence'],extra]
    context['authorized_evidence']=records
    context['messages'][-1]['content']='UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':records})
    catalog=context_quantities(context)
    key=next(key for key in catalog if key.startswith('document:operand-source:'))
    response['answer']['calculations']=[{'operation':'sum','left':{'quantity':key},'right':{'quantity':'92 EUR'}}]
    rendered=render_response(response,[],quantities=catalog)
    assert {item['id'] for item in rendered['evidence']}=={'operand-source','synthetic:rule'}


@pytest.mark.parametrize('width',[1,7,8192])
def test_observed_quantity_segments_preserve_two_currencies_without_operations(width):
    context={'messages':[{'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'Importes: 100 EUR y 100 USD.'})}]}
    catalog=context_quantities(context)
    value={'answer':{'scenario':{'quantities':['100 EUR','100 USD'],'calculations':[]}},'status':'insufficient_data',
        'assumptions':[],'limitations':[],'next_actions':[],'recommendations':[],'metrics':[],'evidence':[]}
    raw=json.dumps(value,ensure_ascii=True);parser=SegmentAnswerJSON([],quantities=catalog)
    streamed=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    rendered=render_response(value,[],quantities=catalog)
    assert streamed==parser.finish()==rendered['answer']
    assert 'Dato aportado: 100 EUR.' in streamed and 'Dato aportado: 100 USD.' in streamed
    assert 'moneda de destino' in streamed and '200' not in streamed
    assert rendered['evidence']==[]
    with pytest.raises(ValueError,match='Unknown source quantity'):
        render_response({**value,'answer':{'scenario':{'quantities':['200 EUR'],'calculations':[]}}},[],quantities=catalog)


def test_documentary_quantity_display_requires_citation_and_cannot_gain_server_marker():
    from app.core.chat_segments import ServerRenderedResponse
    context,catalog,_=fixture()
    key=next(key for key in catalog if key.startswith('document:'))
    value={'answer':[{'quantity':key}],'assumptions':[],'limitations':[],
        'next_actions':[],'recommendations':[],'metrics':[],'evidence':[]}
    with pytest.raises(ValueError,match='Narrative requires selected evidence'):
        render_response(value,[],quantities=catalog)
    source=context['authorized_evidence'][0]
    value['evidence']=[{key:source[key] for key in ('id','kind','title','source')}]
    rendered=render_response(value,[],quantities=catalog)
    assert type(rendered) is dict and not isinstance(rendered,ServerRenderedResponse)
    assert 'Dato documental:' in rendered['answer']
