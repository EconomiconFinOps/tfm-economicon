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


def test_private_records_project_exact_ids_without_changing_public_contract():
    value=candidate();original=copy.deepcopy(value)
    rendered=render_response(value,[],quantities={})
    result=assemble_chat_response(rendered,None,authorized_evidence=SOURCES)
    assert value==original
    assert result['recommendations'][0]['evidence_ids']==['policy-b']
    assert 'evidence' not in result['recommendations'][0]
    assert [item['id'] for item in result['evidence']]==['policy-a','policy-b']
    assert all('support_quote' not in item for item in result['evidence'])
    public=FinOpsResponse.model_json_schema()['$defs']['Recommendation']
    private=chat_provider_schema(authorized_evidence=SOURCES)['$defs']['Recommendation']
    assert 'evidence_ids' in public['required'] and 'evidence' not in public['properties']
    assert 'evidence' in private['required'] and 'evidence_ids' not in private['properties']
    assert private['properties']['evidence']['items']=={'$ref':'#/$defs/Evidence'}


@pytest.mark.parametrize('width',[1,7,8192])
def test_recommendation_projection_preserves_streamed_answer(width):
    value=candidate();raw=json.dumps(value,ensure_ascii=True)
    parser=SegmentAnswerJSON([],quantities={})
    streamed=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    projected=assemble_chat_response(render_response(value,[],quantities={}),None,authorized_evidence=SOURCES)
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
