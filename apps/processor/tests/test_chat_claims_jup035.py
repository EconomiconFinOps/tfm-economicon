import copy
import json
import pytest
from app.core.chat_claims import passages,render_documentary
from app.core.chat_rules import QuantityCatalog
from app.core.chat_segments import render_response,ServerRenderedResponse
from app.agents.schemas import chat_provider_schema,assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON

SOURCE={'id':'guide','kind':'corpus','title':'Guide','source':'guide.md','content':'Costs are observations. Confirm the scope before comparison.'}

def catalog():
    value=QuantityCatalog({});value.authorized_sources=[copy.deepcopy(SOURCE)];value.rule_sources=[copy.deepcopy(SOURCE)]
    return value

def candidate():
    return {'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
        'basis':'authorized_evidence','status':'ok',
        'answer':[{'documentary':{'source_id':'guide','passage':'Costs are observations.'}},
                  {'inference':'Conviene comprobar el alcance del escenario.'}],
        'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}

@pytest.mark.parametrize('width',[1,7,8192])
@pytest.mark.parametrize('basis_first',[True,False])
def test_literal_support_stream_final_and_projection(width,basis_first):
    value=candidate()
    if not basis_first:value['basis']=value.pop('basis')
    raw=json.dumps(value,ensure_ascii=True);parser=SegmentAnswerJSON([],quantities=catalog())
    stream=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    result=render_response(value,[],quantities=catalog())
    assert stream==parser.finish()==result['answer']
    assert 'Interpretación:' not in stream
    # The explanation comes first and the literal excerpt is listed after it.
    assert stream.index('Conviene comprobar')<stream.index('Fuente: Guide')
    assert type(result) is ServerRenderedResponse
    final=assemble_chat_response(result,None,authorized_evidence=[SOURCE])
    assert final['answer']==stream and final['evidence']==[{key:SOURCE[key] for key in ('id','kind','title','source')}]

@pytest.mark.parametrize('patch',[
    {'source_id':'foreign'}, {'passage':'Unsupported assertion.'},{'title':'Injected'},
])
def test_invalid_selection_rejected_before_any_emission(patch):
    value=candidate();value['answer'][0]['documentary'].update(patch)
    parser=SegmentAnswerJSON([],quantities=catalog())
    with pytest.raises(ValueError):parser.feed(json.dumps(value))
    assert parser.text==''
    with pytest.raises(ValueError):render_response(value,[],quantities=catalog())


def test_unused_top_level_evidence_is_rejected():
    value=candidate();value['evidence']=[SOURCE]
    with pytest.raises(ValueError,match='derived'):render_response(value,[],quantities=catalog())


def test_free_documentary_paraphrase_has_no_legacy_text_escape():
    value=candidate();value['answer']=[{'text':'A purported documentary policy.'}]
    with pytest.raises(ValueError):render_response(value,[],quantities=catalog())


def test_empty_support_is_not_an_authorized_narrative():
    value=candidate();value['answer']=[{'inference':'A tentative interpretation.'}]
    with pytest.raises(ValueError,match='selected evidence'):render_response(value,[],quantities=catalog())


def test_quote_markers_are_not_selectable_support():
    assert passages('## Heading\n1.\n2.\nA useful definition.')==['A useful definition.']


def test_split_free_equation_in_inferences_is_rejected():
    value=candidate();value['answer']=[{'inference':'7 + '},{'inference':'2 = 100'}]
    with pytest.raises(ValueError):render_response(value,[],quantities=catalog())
    with pytest.raises(ValueError):SegmentAnswerJSON([],quantities=catalog()).feed(json.dumps(value))


def test_private_schema_has_no_root_citation_admission():
    schema=chat_provider_schema(authorized_evidence=[SOURCE],quantities=catalog())
    assert all(branch['properties']['evidence']['maxItems']==0 for branch in schema.get('anyOf',[schema]))


@pytest.mark.parametrize('basis,status',[('user_scenario','insufficient_data'),('greeting','no_data')])
@pytest.mark.parametrize('field',['assumptions','limitations','next_actions'])
def test_non_documentary_modes_never_offer_unrenderable_auxiliary_citations(basis,status,field):
    schema=chat_provider_schema(authorized_evidence=[SOURCE],quantities=catalog())
    branch=next(b for b in schema['anyOf'] if b['properties']['basis']['const']==basis)
    item=branch['properties'][field]['items']['items']
    assert set(item['properties'])=={'inference'}
    assert item['additionalProperties'] is False
    value=candidate();value.update(basis=basis,status=status,evidence=[])
    value['answer']=[{'inference':'Escenario aportado.'}] if basis=='user_scenario' else [{'text':'Hola.'}]
    value[field]=[[{'inference':'Confirma el alcance.'}]]
    assert 'Confirma el alcance.' in render_response(value,[],quantities=catalog())[field][0]
    value[field]=[[{'documentary':{'source_id':'guide','passage':'Costs are observations.'}}]]
    with pytest.raises(ValueError,match='cannot grant authority'):
        render_response(value,[],quantities=catalog())

@pytest.mark.parametrize('basis_first',[True,False])
def test_plain_text_cannot_be_emitted_before_final_rejection(basis_first):
    value=candidate();value['answer']=[{'text':'An unsupported purported policy.'}]
    if not basis_first:value['basis']=value.pop('basis')
    parser=SegmentAnswerJSON([],quantities=catalog())
    with pytest.raises(ValueError):parser.feed(json.dumps(value))
    assert parser.text==''


def test_many_adjacent_interpretations_count_only_actual_rendered_prefix():
    value=candidate();value['basis']='user_scenario';value['status']='insufficient_data'
    value['answer']=[{'inference':'a'*30} for _ in range(100)]
    raw=json.dumps(value);parser=SegmentAnswerJSON([],quantities=catalog())
    stream=''.join(parser.feed(raw[i:i+7]) for i in range(0,len(raw),7))
    assert stream==parser.finish()==render_response(value,[],quantities=catalog())['answer']


def test_recommendation_projects_only_its_own_visible_support():
    value=candidate();value['recommendations']=[{'id':'r1','category':'other',
        'action':[{'inference':'Revisar el alcance.'}],
        'rationale':[{'documentary':{'source_id':'guide','passage':'Confirm the scope before comparison.'}}],
        'estimated_savings':None,'currency':None}]
    result=render_response(value,[],quantities=catalog())
    assert result['recommendations'][0]['evidence_ids']==['guide']
    assert 'Fuente: Guide' in result['recommendations'][0]['rationale']
    assert len(result['evidence'])==1
    value['recommendations'][0]['rationale']=[{'inference':'Just a speculative justification.'}]
    with pytest.raises(ValueError,match='requires visible'):render_response(value,[],quantities=catalog())


def test_json_round_trip_does_not_forge_the_in_process_provenance_marker():
    rendered=render_response(candidate(),[],quantities=catalog())
    with pytest.raises(ValueError,match='grounded'):
        assemble_chat_response(json.loads(json.dumps(rendered)),None,authorized_evidence=[SOURCE])


def test_financial_sources_are_used_only_by_authorized_metric_references():
    source={'id':'cost','kind':'cost_query','title':'Verified query','source':'query-1'}
    q=catalog();q.authorized_sources.append(source)
    value=candidate();value['answer']=[{'inference':'Lectura de la consulta autorizada.'}]
    value['metrics']=[{'name':'total','value':'37','unit':'EUR','evidence_ids':['cost']}]
    result=render_response(value,[],quantities=q)
    assert result['evidence']==[source]
    value['basis']='missing_data';value['status']='insufficient_data'
    value['next_actions']=[[{'inference':'Confirma el alcance.'}]]
    with pytest.raises(ValueError):render_response(value,[],quantities=q)


def test_source_metadata_changed_after_render_is_rejected_by_assembler():
    result=render_response(candidate(),[],quantities=catalog())
    with pytest.raises(ValueError,match='mismatch'):
        assemble_chat_response(result,None,authorized_evidence=[{**SOURCE,'title':'Changed'}])


@pytest.mark.parametrize('message,code',[
    ('Documentary selection source unavailable.','documentary_selection_source'),
    ('Documentary selection passage mismatch.','documentary_selection_passage'),
    ('Response evidence is derived from used support.','evidence_projection_only'),
    ('Documentary selection passage mismatch. SECRET',None),
])
def test_documentary_failures_emit_closed_codes_without_content(message,code,caplog):
    from app.clients.chat_gateway import _record_diagnostic
    _record_diagnostic('provisional_answer',ValueError(message),'0'*64,None)
    event=json.loads(caplog.records[-1].message)
    assert event.get('rule_code')==code
    assert 'SECRET' not in caplog.text and message not in caplog.text


@pytest.mark.parametrize('replacement',[None,{},'missing'])
def test_recommendation_projection_never_repairs_a_missing_or_invalid_collection(replacement):
    value=candidate()
    if replacement=='missing':value.pop('recommendations')
    else:value['recommendations']=replacement
    with pytest.raises(ValueError,match='Invalid recommendation collection'):
        render_response(value,[],quantities=catalog())


@pytest.mark.parametrize('field',['metrics','assumptions','limitations','next_actions'])
def test_required_public_collections_are_never_repaired(field):
    value=candidate();value.pop(field)
    with pytest.raises(ValueError):
        rendered=render_response(value,[],quantities=catalog())
        assemble_chat_response(rendered,None,authorized_evidence=[SOURCE])


def test_omitted_basis_cannot_release_an_unattributed_provisional_answer():
    value=candidate();value.pop('basis');value['answer']=[{'text':'Unattributed purported policy.'}]
    parser=SegmentAnswerJSON([],quantities=catalog())
    with pytest.raises(ValueError,match='basis'):parser.feed(json.dumps(value))
    assert parser.text==''



def test_flattened_table_offers_complete_literal_rows_without_rewriting():
    from app.core.chat_claims import passages, table_rows
    table = ('Other paragraph. ## Tags | Tag | Example | Use | | --- | --- | --- | '
             '| `owner` | `team` | Responsible | | `environment` | `prod` | Context | More prose.')
    expected = ['| `owner` | `team` | Responsible |', '| `environment` | `prod` | Context |']
    assert table_rows(table) == expected
    assert all(row in table and row in passages(table) for row in expected)
    assert not any('---' in quote for quote in passages(table))


def test_table_partial_row_and_wrong_column_count_are_not_offered():
    from app.core.chat_claims import table_rows
    prefix = '| A | B | C | | --- | --- | --- | '
    assert table_rows(prefix + '| first | second | cut') == []
    assert table_rows(prefix + '| first | second |') == []
    assert table_rows('| first | second | third |') == []


def test_long_table_row_is_not_truncated_into_a_quote():
    from app.core.chat_claims import passages
    content = '| A | B | | --- | --- | | ' + 'x' * 230 + ' | value |'
    assert not any('value' in quote for quote in passages(content))


def test_excerpts_are_listed_together_after_the_explanation():
    # Explanation and literal excerpts no longer alternate: prose first, then every excerpt.
    value=candidate()
    value['answer']=[{'inference':'Primera idea.'},{'documentary':{'source_id':'guide','passage':'Costs are observations.'}},
                     {'inference':'Segunda idea.'},{'documentary':{'source_id':'guide','passage':'Confirm the scope before comparison.'}}]
    raw=json.dumps(value,ensure_ascii=True);parser=SegmentAnswerJSON([],quantities=catalog())
    stream=''.join(parser.feed(raw[i:i+7]) for i in range(0,len(raw),7))
    answer=render_response(value,[],quantities=catalog())['answer']
    assert stream==parser.finish()==answer
    assert 'Interpretación' not in answer
    assert answer.index('Segunda idea.')<answer.index('Fuente: Guide — «Costs are observations.»')
    assert answer.count('Fuente: Guide')==2
