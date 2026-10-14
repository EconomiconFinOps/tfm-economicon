"""Opt-in actual SQL/pgvector proof, using the existing disposable DB fixture."""
from datetime import datetime,timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.chat_expressions import context_quantities
from app.core.chat_policy_sections import required_policy
from app.services.citations import DocumentCitations
from test_tenant_isolation_vector import retrieval  # noqa: F401


def add_policy(store,document,tenant='tenant-a',provider='mock',body=None):
    body=body or (Path(__file__).resolve().parents[3]/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8')
    parsed=DocumentCitations(body);now=datetime.now(timezone.utc)
    with store.engine.begin() as c:
        c.execute(text('INSERT INTO knowledge_documents VALUES (:id,:id,:tenant,:body,NULL,:body,1,:now,:now)'),
                  {'id':document,'tenant':tenant,'body':body,'now':now})
        for i,left in enumerate(range(0,len(parsed.normalized),450)):
            p={'id':f'{document}:{i}','doc':document,'index':i,'body':parsed.normalized[left:left+500],'now':now,'provider':provider}
            c.execute(text('INSERT INTO document_chunks VALUES (:id,:doc,:index,:body,500,:now)'),p)
            c.execute(text("INSERT INTO chunk_embeddings VALUES (:id,:id,'[0,1,0,0,0,0,0,0]'::vector,8,:provider,:now)"),p)


@pytest.mark.parametrize('section,question,required', [
    ('Budgets Y Forecast','¿Un presupuesto apaga recursos?','investigacion, no apagado automatico'),
    ('Reglas De Tagging','Enumera los tags minimos.','las claves se normalizan en minusculas'),
])
def test_exact_section_outside_similarity_threshold_is_complete_and_tenant_provider_scoped(retrieval,section,question,required):
    import json
    add_policy(retrieval,'rules')
    add_policy(retrieval,'foreign-rules','tenant-b')
    add_policy(retrieval,'other-provider',provider='inactive')
    rows=retrieval.search_chunks('tenant-a',[1.,0,0,0,0,0,0,0],top_k=20,max_distance=.01,
                                 provider='mock',policy_section=section)
    assert rows and len(rows)<=6
    assert {x['document_id'] for x in rows}=={'rules'}
    assert all(x['policy_priority'] and x['tenant_id']=='tenant-a' and x['distance']>.01 for x in rows)
    sources=[{'id':x['chunk_id'],'kind':'corpus','title':x['title'],'source':x['source'],'content':x['content'],
              'provenance':{'document_id':x['document_id'],'chunk_index':x['chunk_index'],'sections':x['section_spans']}}
             for x in rows]
    catalog=context_quantities({'authorized_evidence':sources,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':sources})}]})
    bound=required_policy(catalog)
    assert bound is not None and required in bound['text']


def test_two_active_policy_documents_are_not_arbitrarily_reduced_to_one(retrieval):
    add_policy(retrieval,'rules-a');add_policy(retrieval,'rules-b')
    rows=retrieval.search_chunks('tenant-a',[1.,0,0,0,0,0,0,0],top_k=20,max_distance=.01,
                                 provider='mock',policy_section='Budgets Y Forecast')
    assert rows==[]
