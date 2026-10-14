import copy
import json

import pytest

from app.agents.schemas import FinOpsResponse, assemble_chat_response, chat_provider_schema
from app.core.chat_segments import render_response, project_recommendation_citations
from app.clients.chat_stream_parser import SegmentAnswerJSON
from test_chat_gateway_jup035 import ANSWER


SOURCES=[{'id':'policy-a','kind':'corpus','title':'Guide A','source':'guide-a',
          'content':'Confirm stable demand before committing.'},
         {'id':'policy-b','kind':'corpus','title':'Guide B','source':'guide-b',
          'content':'Compare resource size with observed demand.'}]


def selected(index=0):
    source=SOURCES[index]
    return {**{key:source[key] for key in ('id','kind','title','source')},'support_quote':source['content']}


def candidate():
    value=copy.deepcopy(ANSWER)
    for key in ('period','subscription_ids'):value['scope'].pop(key)
    value.update(basis='authorized_evidence',status='ok',answer=[{'text':'Compare the current size with demand.'}],
        assumptions=[],limitations=[],next_actions=[],evidence=[selected(0)],
        recommendations=[{'category':'investigation','action':'Review resource sizing.',
            'rationale':'Observed demand is needed to assess the size.',
            'estimated_savings':None,'currency':None,'confidence':'medium','risk':'low',
            'requires_human_approval':True,'evidence':[selected(1)]}])
    return value


def visible_candidate():
    value=candidate();value['evidence']=[]
    value['answer']=[{'documentary':{'source_id':SOURCES[0]['id'],'passage':SOURCES[0]['content']}},
                     {'inference':'Compare the current size with demand.'}]
    rec=value['recommendations'][0]
    rec.pop('evidence');rec['action']=[{'inference':rec['action']}]
    rec['rationale']=[{'documentary':{'source_id':SOURCES[1]['id'],'passage':SOURCES[1]['content']}}]
    return value


def visible_catalog():
    from app.core.chat_rules import QuantityCatalog
    value=QuantityCatalog({});value.authorized_sources=copy.deepcopy(SOURCES);return value


def test_private_records_project_exact_ids_without_changing_public_contract():
    value=visible_candidate();original=copy.deepcopy(value)
    rendered=render_response(value,[],quantities=visible_catalog())
    result=assemble_chat_response(rendered,None,authorized_evidence=SOURCES)
    assert value==original
    assert result['recommendations'][0]['evidence_ids']==['policy-b']
    assert 'evidence' not in result['recommendations'][0]
    assert [item['id'] for item in result['evidence']]==['policy-a','policy-b']
    assert all('support_quote' not in item for item in result['evidence'])
    public=FinOpsResponse.model_json_schema()['$defs']['Recommendation']
    private=chat_provider_schema(authorized_evidence=SOURCES)['$defs']['Recommendation']
    assert 'evidence_ids' in public['required'] and 'evidence' not in public['properties']
    assert 'evidence' not in private['properties'] and 'evidence_ids' not in private['properties']
    assert private['properties']['rationale']['type']=='array'


def test_advertised_recommendation_rationale_renders_its_own_support():
    schema=chat_provider_schema(authorized_evidence=SOURCES,quantities=visible_catalog())
    rationale=schema['$defs']['Recommendation']['properties']['rationale']
    assert rationale['minItems']==rationale['maxItems']==1
    selections=rationale['items']['properties']['documentary']['anyOf']
    for selection in selections:
        value=visible_candidate()
        source=selection['properties']['source_id']['const']
        passage=selection['properties']['passage']['enum'][0]
        value['recommendations'][0]['rationale']=[{
            'documentary':{'source_id':source,'passage':passage}}]
        result=render_response(value,[],quantities=visible_catalog())
        rec=result['recommendations'][0]
        assert rec['evidence_ids']==[source]
        assert passage in rec['rationale'] and len(rec['rationale'])<=500
        assert 'inference' not in rationale['items']['properties']


def test_recommendations_are_not_offered_without_selectable_documentary_support():
    schema=chat_provider_schema(authorized_evidence=[])
    assert all(branch['properties']['recommendations']['maxItems']==0
               for branch in schema.get('anyOf',[schema]))


@pytest.mark.parametrize('width',[1,7,8192])
def test_recommendation_projection_preserves_streamed_answer(width):
    value=visible_candidate();raw=json.dumps(value,ensure_ascii=True)
    parser=SegmentAnswerJSON([],quantities=visible_catalog())
    streamed=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    projected=assemble_chat_response(render_response(value,[],quantities=visible_catalog()),None,authorized_evidence=SOURCES)
    assert streamed==parser.finish()==projected['answer']
    assert projected['recommendations'][0]['evidence_ids']==['policy-b']


@pytest.mark.parametrize('field,replacement',[
    ('id','foreign-tenant'),('title','altered'),('source','different'),
    ('kind','user_input'),('support_quote','Invented support'),('support_quote',None)])
def test_nested_selection_cannot_fabricate_source_or_passage(field,replacement):
    value=candidate();value['recommendations'][0]['evidence'][0][field]=replacement
    with pytest.raises(ValueError):project_recommendation_citations(value,SOURCES)


def test_invalid_duplicate_selection_cannot_hide_behind_valid_top_level_quote():
    value=candidate();value['evidence'].append(selected(1))
    value['recommendations'][0]['evidence'][0]['support_quote']='invented'
    with pytest.raises(ValueError,match='grounded'):project_recommendation_citations(value,SOURCES)


def test_union_reuses_only_explicitly_selected_records_and_rejects_duplicates_in_each_list():
    value=candidate();value['evidence'].append(selected(1))
    projected=project_recommendation_citations(value,SOURCES)
    assert len(projected['evidence'])==2
    assert len(project_recommendation_citations(candidate(),SOURCES+[{'id':'unused'}])['evidence'])==2
    value['recommendations'][0]['evidence'].append(selected(1))
    with pytest.raises(ValueError):project_recommendation_citations(value,SOURCES)


@pytest.mark.parametrize('mutation',['ids','empty','extra','omitted_source'])
def test_old_reference_shortcut_empty_selection_and_extra_fields_are_rejected(mutation):
    value=candidate();sources=SOURCES
    if mutation=='ids':value['recommendations'][0]['evidence_ids']=['policy-b']
    elif mutation=='empty':value['recommendations'][0]['evidence']=[]
    elif mutation=='extra':value['recommendations'][0]['evidence'][0]['tenant']='other'
    else:sources=SOURCES[:1]
    with pytest.raises(ValueError):project_recommendation_citations(value,sources)


@pytest.mark.parametrize('case,message',[
    ('shape','Recommendation citation shape invalid.'),
    ('unknown','Recommendation citation source unknown.'),
    ('duplicate','Recommendation citation duplicated.'),
    ('metadata','Recommendation citation metadata mismatch.'),
])
def test_rejected_citations_have_closed_distinct_diagnostics(case,message):
    value=candidate();project_recommendation_citations(value,SOURCES)
    entries=value['recommendations'][0]['evidence']
    if case=='shape':entries[0]='not-a-record'
    elif case=='unknown':entries[0]['id']='outside-current-context'
    elif case=='duplicate':entries.append(copy.deepcopy(entries[0]))
    else:entries[0]['title']='altered metadata'
    with pytest.raises(ValueError) as caught:project_recommendation_citations(value,SOURCES)
    assert str(caught.value)==message
