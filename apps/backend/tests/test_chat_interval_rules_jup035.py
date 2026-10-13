import copy
import json
from pathlib import Path

import pytest

from app.core.chat_expressions import context_quantities, ExpressionRenderer, expression_definitions
from app.core.chat_rules import documentary_rules
from app.core.chat_segments import render_response
from app.services.citations import DocumentCitations


DOCUMENT = """# Report
## Rework
KPI: Rework Cost % = Rework Cost / Eligible Cost * 100
- calm: menor o igual a 7 %;
- watch: mayor que 7 % y menor o igual a 13 %;
- alert: mayor que 13 %.
## Budget
Budget variance is cost minus budget. No traffic-light rule is defined here.
"""


def sources(document=DOCUMENT, *, size=180, overlap=40):
    index = DocumentCitations(document)
    chunks = []
    for number, start in enumerate(range(0, len(index.normalized), size-overlap)):
        content = index.normalized[start:start+size]
        # Production chunks are whitespace-normalized and never retain edge whitespace.
        content = content.strip()
        chunks.append({'id':f'doc:{number}', 'kind':'corpus','title':'Report','source':'manual','content':content,
            'provenance':{'document_id':'doc','chunk_index':number,'sections':index.section_spans(content)}})
    return chunks


def catalog(question='rework 7 EUR; remaining 93 EUR.', records=None):
    records = sources() if records is None else records
    return context_quantities({'authorized_evidence':records,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':records})}]})


def percent(numerator, remaining):
    leaf = lambda key: {'quantity':key+' EUR'}
    return {'operation':'percentage','numerator':leaf(numerator),
        'denominator':{'operation':'sum','left':leaf(numerator),'right':leaf(remaining)}}


@pytest.mark.parametrize('value,label', [('6','calm'),('7','calm'),('8','watch'),('13','watch'),('14','alert')])
def test_literal_intervals_use_exact_inclusive_boundaries(value,label):
    remainder = str(100-int(value))
    quantities = catalog(f'rework {value} EUR; remaining {remainder} EUR.')
    assert len(quantities.rules) == 1
    rule = quantities.rules[0]
    node = {'operation':'classify','rule_id':rule['id'],'value':percent(value,remainder)}
    result = ExpressionRenderer(quantities).render(node)
    assert f'): {label}.' in result
    assert rule['metric'] == 'Rework Cost %'
    assert rule['section'] == 'Rework'


@pytest.mark.parametrize('question', ['budget 7 EUR; remaining 93 EUR.', 'rework 7 EUR; budget 7 EUR; remaining 93 EUR.'])
def test_budget_or_ambiguous_numeric_alias_cannot_use_other_kpi(question):
    quantities = catalog(question)
    with pytest.raises(ValueError,match='KPI value mismatch'):
        ExpressionRenderer(quantities).render({'operation':'classify','rule_id':quantities.rules[0]['id'],'value':percent('7','93')})


@pytest.mark.parametrize('question',['7 EUR rework; 93 EUR remaining.','rework: 7 EUR; remaining: 93 EUR.','rework = 7 EUR; remaining = 93 EUR.'])
def test_label_after_value_is_bound_without_semantic_translation(question):
    quantities = catalog(question)
    result = ExpressionRenderer(quantities).render({'operation':'classify','rule_id':quantities.rules[0]['id'],'value':percent('7','93')})
    assert '): calm.' in result


@pytest.mark.parametrize('replace', [
    ('mayor que 7 %','mayor o igual a 7 %'),
    ('mayor que 7 %','mayor que 8 %'),
    ('- alert: mayor que 13 %.','- alert: mayor que 13 %. - extra: aproximadamente 9 %.'),
    ('- alert: mayor que 13 %.','- alert: mayor que 13 EUR.'),
])
def test_overlap_gap_unsupported_row_or_mixed_units_fail_closed(replace):
    assert documentary_rules(sources(DOCUMENT.replace(*replace))) == []


def test_same_heading_text_does_not_join_distinct_section_occurrences():
    document = DOCUMENT.replace('## Budget','## Rework')
    records = sources(document)
    rules = documentary_rules(records)
    assert len(rules) == 1
    assert all('Budget' not in rule['metric'] for rule in rules)
    assert len({span['section_start'] for source in records for span in source['provenance']['sections'] if span['section']=='Rework'}) == 2


def test_missing_contiguous_chunk_or_changed_overlap_does_not_reconstruct_rule():
    records = sources(size=100, overlap=10)
    assert documentary_rules(records[::2]) == []
    tampered = copy.deepcopy(sources())
    tampered[1]['content'] = 'X' + tampered[1]['content'][1:]
    assert documentary_rules(tampered) == []


@pytest.mark.parametrize('text', [
    'Como supera el límite, el semáforo correspondiente es alert.',
    'La clasificación es calm.',
    'La superación calculada entra en la franja alert.',
])
def test_unverified_conclusion_is_rejected_even_without_classify(text):
    renderer = ExpressionRenderer(catalog())
    with pytest.raises(ValueError,match='Unverified documentary classification'):
        renderer.check_prose(text)
    renderer.check_prose('El coste es alto y la latencia baja; investigar antes de actuar.')


def test_sections_are_positioned_by_original_markdown_not_chunk_initial_label():
    original = DocumentCitations(DOCUMENT)
    spans = original.section_spans(original.normalized)
    assert [span['section'] for span in spans] == ['Report','Rework','Budget']
    assert original.normalized[spans[-1]['start']:].startswith('## Budget')


def test_repository_document_rule_and_full_response_fit_twelve_operations():
    root = Path(__file__).resolve().parents[3]
    document = (root/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8')
    records = sources(document,size=500,overlap=50)
    quantities = catalog('EUR: allocated 700; shared 200; unallocated 100; excluded 50.',records)
    assert len(quantities.rules) == 1
    rule = quantities.rules[0]
    leaf = lambda key:{'quantity':key+' EUR'}
    total={'operation':'sum','left':leaf('700'),'right':{'operation':'sum','left':leaf('200'),'right':leaf('100')}}
    percentage={'operation':'percentage','numerator':leaf('100'),'denominator':total}
    value={'answer':{'calculations':[total,percentage],
        'classification':{'operation':'classify','rule_id':rule['id'],'value':percentage}},
        'assumptions':[],'limitations':[],'next_actions':[],'recommendations':[],'metrics':[],
        'evidence':[]}
    result=render_response(value,[],quantities=quantities)
    assert '): amarillo.' in result['answer']
    assert '10 % <= 10 %' in result['answer']
    schema=expression_definitions(quantities)
    assert rule['id'] in json.dumps(schema)
    assert {entry['id'] for entry in result['evidence']}==set(rule['source_ids'])
    with pytest.raises(ValueError,match='Classified evidence is server-owned'):
        render_response({**value,'evidence':[{'id':'untrusted'}]},[],quantities=quantities)


def test_near_boundary_does_not_render_false_rounded_inequality():
    quantities=catalog('rework 7.0000001 EUR; remaining 92.9999999 EUR.')
    result=ExpressionRenderer(quantities).render({'operation':'classify','rule_id':quantities.rules[0]['id'],
        'value':percent('7.0000001','92.9999999')})
    assert '): watch.' in result and '7.000000100 > 7' not in result
    assert '7 % > 7 %' not in result
    assert '≈ 7 %' in result


def test_schema_does_not_offer_classification_to_budget_only_quantities():
    definitions=expression_definitions(catalog('budget 7 EUR; remaining 93 EUR.'))
    assert 'classify' not in json.dumps(definitions)


@pytest.mark.parametrize('value,label', [('50','verde'),('101','rojo')])
def test_documented_boundaries_with_postfixed_amount_label_and_leaf_denominator(value,label):
    document=(Path(__file__).resolve().parents[3]/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8')
    quantities=catalog(f'¿Se incluye el 5 %? Escenario sintético con 1000 EUR elegibles y {value} EUR unallocated; aplicar las reglas MVP.',sources(document,size=500,overlap=50))
    rule=quantities.rules[0]
    result=ExpressionRenderer(quantities).render({'operation':'classify','rule_id':rule['id'],'value':{
        'operation':'percentage','numerator':{'quantity':value+' EUR'},'denominator':{'quantity':'1000 EUR'}}})
    assert f'): {label}.' in result


@pytest.mark.parametrize('conclusion', [
    # Exact rejected conclusions from the synthetic expression17 provider receipt.
    'Como el resultado hipotético supera el 10 %, el semáforo correspondiente es rojo.',
    'La superación calculada entra en la franja roja (> 10 %), por lo que el presupuesto está excedido de forma significativa.',
])
def test_previous_provider_conclusions_cannot_bypass_interval_evaluation(conclusion):
    document=(Path(__file__).resolve().parents[3]/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8')
    quantities=catalog('EUR: allocated 700; shared 200; unallocated 100; excluded 50.',sources(document,size=500,overlap=50))
    with pytest.raises(ValueError,match='Unverified documentary classification'):
        render_response({'basis':'user_scenario','status':'insufficient_data','answer':[{'text':conclusion}],
            'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]},[],quantities=quantities)


@pytest.mark.parametrize('change',[{'rule_id':'unknown'},{'label':'alert'}])
def test_unknown_rule_or_model_supplied_label_is_not_repaired(change):
    quantities=catalog()
    node={'operation':'classify','rule_id':quantities.rules[0]['id'],'value':percent('7','93'),**change}
    with pytest.raises(ValueError):ExpressionRenderer(quantities).render(node)


@pytest.mark.parametrize('status',['ok','partial'])
def test_private_schema_separates_narrative_and_terminal_classification(status):
    from app.schemas.chat import _validate,provider_response_schema
    from test_chat_operations_jup035 import ANSWER
    records=sources();quantities=catalog(records=records)
    schema=provider_response_schema(authorized_evidence=records,quantities=quantities)
    node={'operation':'classify','rule_id':quantities.rules[0]['id'],'value':percent('7','93')}
    value=copy.deepcopy(ANSWER)
    value['scope'].pop('period');value['scope'].pop('subscription_ids')
    value.update(status=status,answer={'calculations':[],'classification':node},
        evidence=[],assumptions=[],limitations=[],next_actions=[],recommendations=[],metrics=[])
    _validate(value,schema,schema)
    for field in ('before','after'):
        changed=copy.deepcopy(value);changed['answer'][field]='La clasificación es alert.'
        with pytest.raises(ValueError):_validate(changed,schema,schema)
    changed=copy.deepcopy(value);changed['answer']=[{'expression':node}]
    with pytest.raises(ValueError):_validate(changed,schema,schema)
    changed=copy.deepcopy(value);changed['limitations']=[[{'text':'La clasificación es alert.'}]]
    with pytest.raises(ValueError):_validate(changed,schema,schema)
    changed=copy.deepcopy(value);changed['next_actions']=[[{'text':'Investigate.'}]]
    with pytest.raises(ValueError):_validate(changed,schema,schema)


@pytest.mark.parametrize('question,required', [
    ('¿Qué semáforo corresponde?',True),
    ('¿Qué clasificación corresponde?',True),
    ('Clasifica el coste rework.',True),
    ('Which traffic light applies?',True),
    ('Explica el reparto.',False),
    ('Explica el reparto sin semáforo.',False),
    ('No clasifiques el coste; explica el reparto.',False),
    ('Explica qué significa clasificación.',False),
    ('¿Qué es el semáforo?',False),
    ('Explica el reparto.\n\nContexto: ¿Qué semáforo corresponde?',False),
])
def test_explicit_classification_routing_preserves_other_requests(question,required):
    from app.core.chat_rules import required_classification
    from app.schemas.chat import _validate,provider_response_schema
    from test_chat_operations_jup035 import ANSWER
    records=sources()
    q=catalog(question+'\n\nDatos: rework 7 EUR; remaining 93 EUR.',records)
    assert required_classification(q) is required
    schema=provider_response_schema(authorized_evidence=records,quantities=q)
    value=copy.deepcopy(ANSWER)
    value['scope'].pop('period');value['scope'].pop('subscription_ids')
    value.update(status='ok',answer=[{'text':'El escenario contiene dos conceptos de coste.'}],
        evidence=[{key:records[0][key] for key in ('id','kind','title','source')}|{'support_quote':records[0]['content']}],
        assumptions=[],limitations=[],next_actions=[],recommendations=[],metrics=[])
    if required:
        with pytest.raises(ValueError):_validate(value,schema,schema)
        with pytest.raises(ValueError,match='Explicit classification requires typed answer'):
            render_response(value,[],quantities=q)
        classified=copy.deepcopy(value)
        classified['answer']={'calculations':[],'classification':{'operation':'classify','rule_id':q.rules[0]['id'],'value':percent('7','93')}}
        classified['evidence']=[]
        _validate(classified,schema,schema)
        assert '): calm.' in render_response(classified,[],quantities=q)['answer']
        value['status']='insufficient_data'
        # Status cannot reopen free classification prose. Only a neutral,
        # explicit request for the missing inputs remains representable.
        with pytest.raises(ValueError):_validate(value,schema,schema)
        with pytest.raises(ValueError):render_response(value,[],quantities=q)
        from app.core.chat_segments import CLASSIFICATION_ABSTENTIONS
        value['answer']=[{'text':CLASSIFICATION_ABSTENTIONS[0]}]
        value['evidence']=[]
        _validate(value,schema,schema)
        render_response(value,[],quantities=q)
    else:
        value['basis']='authorized_evidence'
        _validate(value,schema,schema)
        render_response(value,[],quantities=q)


def test_ambiguous_rules_or_unanchored_quantity_do_not_force_classification():
    from app.core.chat_rules import required_classification
    q=catalog('¿Qué semáforo corresponde?\n\nDatos: budget 7 EUR; remaining 93 EUR.')
    assert not required_classification(q)
    q=catalog('¿Qué semáforo corresponde?\n\nDatos: rework 7 EUR; remaining 93 EUR.')
    q.rules=[*q.rules,{**q.rules[0],'id':'another-rule'}]
    assert not required_classification(q)


def test_history_and_retrieval_do_not_force_current_narrative_request():
    from app.core.chat_rules import required_classification
    records=sources()
    context={'authorized_evidence':records,'messages':[
        {'content':'UNTRUSTED_DIALOGUE_SUMMARY\n'+json.dumps({'text':'Clasifica el coste rework.'})},
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'Explica el reparto.\n\nDatos: rework 7 EUR; remaining 93 EUR.'})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':records})}]}
    assert not required_classification(context_quantities(context))


def test_multiple_period_numerators_keep_narrative_comparison_available():
    from app.core.chat_rules import required_classification
    q=catalog('¿Qué semáforo corresponde a cada periodo?\n\nEnero: rework 7 EUR. Febrero: rework 8 EUR. Remaining 92 EUR.')
    eligible=[entry for entry in q.values() if entry.get('concept_anchors')==[['rework']]]
    assert len(eligible)==2
    assert not required_classification(q)


def test_partial_documentary_intervals_guard_does_not_authorize_other_kpi():
    from app.core.chat_rules import check_classification_prose
    document=(Path(__file__).resolve().parents[3]/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8')
    records=sources(document,size=500,overlap=50)
    partial=[record for record in records if 'rojo: mayor que 10 %' in record['content']]
    assert len(partial)==1
    q=catalog('budget 1000 EUR; actual 1200 EUR.',partial)
    assert q.rules==[]
    assert 'DocumentaryClassification' not in expression_definitions(q)
    with pytest.raises(ValueError,match='Unverified documentary classification'):
        check_classification_prose('La desviación presupuestaria corresponde al intervalo rojo.',q.rules,q.rule_sources)
    assert check_classification_prose('El coste es alto y necesita investigación.',q.rules,q.rule_sources)==set()
    assert check_classification_prose('El recurso rojo corresponde al equipo de pruebas.',q.rules,q.rule_sources)==set()
    # No classification authority is created by malformed or absent provenance.
    bad=copy.deepcopy(partial);bad[0]['provenance']['sections'][0]['start']=999
    with pytest.raises(ValueError):check_classification_prose('El semáforo es rojo.',[],bad)


def test_comparison_displays_evaluated_operands_without_rounding_its_truth():
    q=catalog('baseline 400 EUR; actual 550 EUR; umbral 100 EUR; tasa 20 %.')
    result=ExpressionRenderer(q).render({'operation':'compare',
        'left':{'operation':'difference','current':{'quantity':'550 EUR'},'baseline':{'quantity':'400 EUR'}},
        'right':{'quantity':'100 EUR'},'relation':'gt'})
    assert 'valores evaluados: 150 EUR > 100 EUR → verdadero' in result
    relative=ExpressionRenderer(q).render({'operation':'compare',
        'left':{'operation':'relative_change','current':{'quantity':'550 EUR'},'baseline':{'quantity':'400 EUR'}},
        'right':{'quantity':'20 %'},'relation':'gt'})
    assert 'valores evaluados: 37.5 % > 20 % → verdadero' in relative
    tiny=catalog('0.0000004 EUR y 0.0000003 EUR.')
    shown=ExpressionRenderer(tiny).render({'operation':'compare','left':{'quantity':'0.0000004 EUR'},'right':{'quantity':'0.0000003 EUR'},'relation':'gt'})
    assert 'valores evaluados: 0.0000004 EUR > 0.0000003 EUR' in shown
