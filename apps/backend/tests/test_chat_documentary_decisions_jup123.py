"""Actual original corpus, independent backend grammar and used-source firewall."""
import json
from pathlib import Path

import pytest

from app.core.chat_documentary_decisions import required_documentary_answer
from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema, validate_response
from app.services.citations import DocumentCitations


@pytest.mark.parametrize('question,context,expected,status',[
    ('¿Uso coste actual o amortizado para repartir el coste de una reserva?',
     'Consulta conceptual, sin importes ni contratos de cliente.',
     ('se aproxima','suele ser mas util','amortized cost'),'ok'),
    ('¿Compramos una reserva de inmediato para una VM que pronto migraremos?',
     'Escenario sintético: migración prevista el próximo mes, demanda futura desconocida '
     'y rightsizing pendiente. No se aportan precios ni términos de contratación.',
     ('conviene aplicar','No se concluye que la base de uso sea estable','Riesgo condicional'),'insufficient_data'),
])
def test_full_original_corpus_preserves_qualification_and_unknown_premises(question,context,expected,status):
    root=Path(__file__).resolve().parents[3]
    doc=DocumentCitations((root/'docs/assistant-corpus/finops/azure-finops-mvp.md').read_text(encoding='utf-8'))
    sources=[]
    for index,left in enumerate(range(0,len(doc.normalized),450)):
        # Ingestion strips chunk boundary whitespace. Unstripped slices have no
        # authoritative ranges and must not be used as successful fixtures.
        content=doc.normalized[left:left+500].strip()
        spans=doc.section_spans(content)
        assert spans
        sources.append({'id':f'finops:{index}','kind':'corpus','title':doc.title,'source':'finops','content':content,
                        'provenance':{'document_id':'finops','chunk_index':index,'sections':spans}})
    q=context_quantities({'authorized_evidence':sources,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question+'\n\nContexto del escenario: '+context})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':sources})}]})
    bound=required_documentary_answer(q);assert bound is not None
    answer={'documentary_answer':bound['id']}
    assert provider_response_schema(quantities=q,authorized_evidence=sources)['properties']['answer']=={'const':answer}
    value={'schema_version':'1.0','status':status,'answer':answer,
           'scope':{'cloud':'azure','data_environment':'simulated','period':None,'subscription_ids':[]},
           'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
    public=render_response(value,[],quantities=q)
    assert validate_response(json.loads(json.dumps(public)),sources,expected_period=None,expected_subscriptions=[])==public
    assert all(word in public['answer'] for word in expected)
    assert 'exige' not in public['answer'] and public['metrics']==public['recommendations']==[]
