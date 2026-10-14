import copy
import json

import pytest
from app.core.chat_expressions import context_quantities, ExpressionRenderer
from app.core.chat_boolean_rules import render_boolean
from app.core.chat_segments import render_response, render_classified_answer, ServerRenderedResponse
from app.schemas.chat import provider_response_schema
from app.services.citations import DocumentCitations


def catalog(question, document=None):
    sources=[]
    if document:
        index=DocumentCitations(document)
        sources=[{'id':'doc:0','kind':'corpus','title':'Policy','source':'manual','content':index.normalized,
                  'provenance':{'document_id':'doc','chunk_index':0,'sections':index.section_spans(index.normalized)}}]
    return context_quantities({'authorized_evidence':sources,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':sources})}]})


def request(current=96,baseline=80,operator='>',combinator='AND'):
    return f'¿Se cumple la regla?\n\nBaseline {baseline} EUR/día; observado {current} EUR/día. Regla: delta relativo {operator}20 % {combinator} delta absoluto >12 EUR/día.'


def answer(q):
    rule=q.boolean_rules[0]
    return {'boolean':{'rule_id':rule['id'],'baseline':rule['baseline'],'current':rule['current']}}


def response(q):
    return {'answer':answer(q),'status':'ok' if q.boolean_rules[0]['source_ids'] else 'insufficient_data',
            'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('operator,combinator,expected',[('>','AND','no se cumple'),('>=','AND','se cumple'),('>','OR','se cumple')])
def test_server_evaluates_both_operands_limits_and_terminal(operator,combinator,expected):
    q=catalog(request(operator=operator,combinator=combinator));value=response(q)
    result=render_response(value,[],quantities=q)
    assert f'Resultado {combinator}: la regla {expected}.' in result['answer']
    assert '16 EUR/día' in result['answer'] and '20 %' in result['answer']
    assert result['evidence']==[] and type(result) is dict
    schema=provider_response_schema(financial_metrics_allowed=False,authorized_evidence=[],quantities=q)
    assert schema['properties']['answer']['type']=='object'
    assert schema['properties']['status']['enum']==['insufficient_data']
    bad={**value,'answer':[{'text':'La regla sí se cumple.'}]}
    with pytest.raises(ValueError,match='requires typed'):render_response(bad,[],quantities=q)


@pytest.mark.parametrize('combinator,result',[('AND','no se puede determinar'),('OR','se cumple')])
def test_undefined_relative_delta_is_not_a_number(combinator,result):
    q=catalog(request(current=30,baseline=0,combinator=combinator))
    text=render_response(response(q),[],quantities=q)['answer']
    assert 'base es cero' in text and f'la regla {result}' in text


@pytest.mark.parametrize('change',[
    lambda s:s.replace('observado 96 EUR/día','observado 96 USD/día'),
    lambda s:s+' Baseline 70 EUR/día.',
    lambda s:s.replace('Regla:','No se aplica'),
    lambda s:s.replace('Regla:','No aplicar'),
    lambda s:s.replace('12 EUR/día.','12 EUR/día AND absolute_delta <99 EUR/día.'),
    lambda s:s+' Otra regla: delta relativo >21 % AND absoluto >12 EUR/día.',
])
def test_ambiguous_incompatible_or_negated_rule_never_authorizes_terminal(change):
    assert catalog(change(request())).boolean_rules==[]


def test_unknown_or_manipulated_rule_operand_or_operator_rejected():
    q=catalog(request());value=answer(q)
    for mutation in ({'rule_id':'other'},{'baseline':'96 EUR/día'},{'combinator':'OR'}):
        wrong={'boolean':{**value['boolean'],**mutation}}
        with pytest.raises(ValueError):render_classified_answer(wrong,ExpressionRenderer(q))


def test_document_rule_propagates_exact_source_and_identical_user_rule_needs_no_artificial_cite():
    document='# Policy\n## Changes\nrelative_delta >20 % AND absolute_delta >12 EUR/day'
    question='¿Se cumple la regla?\n\nBaseline 80 EUR/día; observado 96 EUR/día.'
    q=catalog(question,document)
    result=render_response(response(q),[],quantities=q)
    assert type(result) is ServerRenderedResponse and [s['id'] for s in result.documentary_records]==['doc:0']
    q=catalog(request(),document)
    assert len(q.boolean_rules)==1 and q.boolean_rules[0]['origin']=='user'
    assert type(render_response(response(q),[],quantities=q)) is dict
    conflicting=catalog(request(),document.replace('>20','>21'))
    assert conflicting.boolean_rules==[]


def test_declaring_rule_does_not_force_unrelated_or_conceptual_request():
    for question in ('Explica qué significa esta regla.','Describe los datos sin evaluar la regla.'):
        q=catalog(request().replace('¿Se cumple la regla?',question))
        assert not q.boolean_requested


def test_same_catalog_does_not_allow_swapping_quantity_or_condition():
    q=catalog(request());renderer=ExpressionRenderer(q)
    rendered=render_classified_answer(answer(q),renderer)
    assert renderer.operations==5 and 'Resultado AND' in rendered
    wrong=copy.deepcopy(answer(q));wrong['boolean']['current']='80 EUR/día'
    with pytest.raises(ValueError):render_classified_answer(wrong,ExpressionRenderer(q))


def test_rule_split_across_authenticated_spans_is_not_guessed():
    question='¿Se cumple la regla?\n\nBaseline 80 EUR/día; observado 96 EUR/día.'
    document='# Policy\n## Relative\nrelative_delta >20 % AND\n## Absolute\nabsolute_delta >12 EUR/day'
    assert catalog(question,document).boolean_rules==[]


@pytest.mark.parametrize('combinator,result', [('AND', 'no se cumple'), ('OR', 'no se puede determinar')])
def test_false_absolute_condition_does_not_change_unknown_relative_condition(combinator, result):
    q = catalog(request(current=6, baseline=0, combinator=combinator))
    rendered = render_response(response(q), [], quantities=q)
    assert 'base es cero' in rendered['answer']
    assert '6 EUR/día > 12 EUR/día → falso' in rendered['answer']
    assert f'Resultado {combinator}: la regla {result}.' in rendered['answer']
    assert rendered['evidence'] == []
