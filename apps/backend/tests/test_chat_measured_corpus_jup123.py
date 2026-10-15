"""The current corpus and ingestion-sized fragments cover the measured questions."""
import json
from pathlib import Path

import pytest

from app.services.citations import DocumentCitations
from app.core.chat_expressions import context_quantities
from app.core.chat_policy_sections import required_policy
from app.core.chat_documentary_decisions import required_documentary_answer
from app.core.chat_budget_comparison import required_budget_variance


@pytest.mark.parametrize('case,headings',[
    ('015',{'Budgets Y Forecast','Conceptos FinOps Basicos'}),
    ('003',{'Cost Management Y Cost Analysis'}),('013',set())])
def test_original_question_uses_complete_actual_corpus_with_positional_provenance(case,headings):
    root=Path(__file__).resolve().parents[3]
    bank=json.loads((root/'docs/validation/JUP-069-questions.json').read_text(encoding='utf-8'))
    question=next(c for c in bank['cases'] if c['id']=='JUP-069-'+case)
    records=[]
    for source in bank['sources'].values():
        path=root/source['path'];parsed=DocumentCitations(path.read_text(encoding='utf-8'))
        all_rows=[]
        for index,left in enumerate(range(0,len(parsed.normalized),450)):
            content=parsed.normalized[left:left+500].strip()
            all_rows.append({'id':path.stem+':'+str(index),'kind':'corpus','source':path.stem,
                'title':parsed.title,'content':content,'provenance':{'document_id':path.stem,
                'chunk_index':index,'sections':parsed.section_spans(content)}})
        selected={i for i,r in enumerate(all_rows) if any(s['section'] in headings for s in r['provenance']['sections'])}
        for index in list(selected):
            if index+1<len(all_rows):selected.add(index+1)
        records.extend(all_rows[i] for i in sorted(selected))
    q=context_quantities({'authorized_evidence':records,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question['question']+'\n\nContexto del escenario: '+question['context']})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':records})}]})
    if case=='015':
        bound=required_policy(q)
        assert bound is not None
        assert all(word in bound['text'] for word in ('seguimiento','alertas','investigacion','no apaga'))
    elif case=='003':
        bound=required_documentary_answer(q)
        assert bound is not None and 'Agrupar por servicio.' in bound['public_fields']['answer']
    else:
        bound=required_budget_variance(q)
        assert bound is not None and bound['difference']==200 and bound['relative']==20
