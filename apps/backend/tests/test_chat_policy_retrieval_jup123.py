"""Exact policy expansion stays bounded and uses the same retrieval transaction."""
from types import SimpleNamespace

import pytest

from app.services.citations import DocumentCitations
from app.services.vector_store import PgVectorQueryStore


POLICY = ('# Manual\n## Budgets Y Forecast\nUn budget es una expectativa.\n'
          'Reglas de interpretacion:\n- superar un umbral requiere investigacion, no apagado automatico;\n'
          '- no confundir forecast y presupuesto.\n## Otra Seccion\nFin.')


class Rows(list):
    def all(self): return self


class Connection:
    def __init__(self, document=POLICY, doc_count=1, width=150, step=100):
        self.calls = []; self.document = document
        self.documents = Rows(SimpleNamespace(id=f'policy-{i}', text_content=document, metadata={}) for i in range(doc_count))
        self.location = DocumentCitations(document or '')
        self.rows = Rows(SimpleNamespace(chunk_id=f'policy:{i}', document_id='policy-0',
            tenant_id='tenant-a', chunk_index=i, source='manual', content=self.location.normalized[left:left+width], distance=.9, metadata={})
            for i,left in enumerate(range(0,len(self.location.normalized),step)))

    def connect(self): return self
    def execution_options(self, **options): self.options=options; return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        if 'policy_heading' in params: return self.documents
        if 'policy_chunk_limit' in params: return self.rows
        if 'document_ids' in params: return [SimpleNamespace(id=x,text_content=self.document,metadata={}) for x in params['document_ids']]
        return Rows()


def store(connection):
    result=PgVectorQueryStore.__new__(PgVectorQueryStore);result.engine=connection;return result


def search(connection, **kwargs):
    return store(connection).search_chunks('tenant-a',[1.,0.],top_k=20,provider='mock',
        max_distance=.01,policy_section='Budgets Y Forecast',**kwargs)


def test_exact_policy_can_complete_empty_semantic_results_without_faking_distance():
    c=Connection();result=search(c)
    assert result and all(x['policy_priority'] for x in result)
    assert all(x['distance']==.9 for x in result)
    assert c.options=={'isolation_level':'REPEATABLE READ'}
    lookup=[(sql,p) for sql,p in c.calls if 'policy_heading' in p][0]
    chunks=[(sql,p) for sql,p in c.calls if 'policy_chunk_limit' in p][0]
    for sql,p in (lookup,chunks):
        assert 'kd.tenant_id = :tenant_id' in sql and 'ce.provider = :provider' in sql
        assert p['tenant_id']=='tenant-a' and p['provider']=='mock'
    assert 'LIMIT 2' in lookup[0] and 'CASE WHEN octet_length' in lookup[0]
    assert chunks[1]['policy_chunk_limit']==7
    assert 'LIMIT :policy_chunk_limit' in chunks[0]
    assert 'position(dc.content in :policy_normalized)' in chunks[0]


@pytest.mark.parametrize('damage', ['ambiguous', 'too_large', 'gap', 'too_many_chunks', 'wrong_tenant', 'wrong_document', 'last_section'])
def test_partial_ambiguous_or_over_budget_policy_does_not_gain_priority(damage):
    c=Connection(doc_count=2 if damage=='ambiguous' else 1)
    if damage=='too_large': c.documents[0].text_content=None
    if damage=='gap': c.rows=Rows([c.rows[0],c.rows[-1]])
    if damage=='too_many_chunks': c.rows=Rows(c.rows*3)
    if damage=='wrong_tenant': c.rows[0].tenant_id='other'
    if damage=='wrong_document': c.rows[0].document_id='other'
    if damage=='last_section':
        c.documents[0].text_content=POLICY.split('## Otra Seccion')[0]
    assert search(c)==[]


def test_every_additional_query_reuses_deadline_check_and_never_opens_connection():
    c=Connection();checks=[]
    result=store(c)._policy_rows(c,'tenant-a','mock','[1,0]','Budgets Y Forecast',lambda:checks.append(True))
    assert result and len(checks)==2
    def expired(): raise TimeoutError('Retrieval deadline.')
    with pytest.raises(TimeoutError): store(c)._policy_rows(c,'tenant-a','mock','[1,0]','Budgets Y Forecast',expired)


@pytest.mark.parametrize('section,provider', [('secret','mock'),('Budgets Y Forecast',None),('Budgets Y Forecast','')])
def test_unknown_section_or_unscoped_provider_is_rejected_before_sql(section,provider):
    c=Connection()
    with pytest.raises(ValueError): store(c).search_chunks('tenant-a',[1,0],provider=provider,policy_section=section)
    assert c.calls==[]


@pytest.mark.parametrize('limit,expected',[(20,6),(2,2)])
def test_context_preserves_all_policy_chunks_above_semantic_top_k(limit,expected):
    from app.services.chat_context import ChatContext
    # Six exact section fragments must not be cut to the ordinary four hits.
    c=Connection(width=100,step=35)
    c.rows=c.rows[:6]
    calls=[]
    instance=store(c)
    def search_chunks(tenant,vector,**kwargs):
        calls.append(kwargs)
        return [{'chunk_id':f'policy:{i}','document_id':'policy-0','tenant_id':tenant,'chunk_index':i,
                 'title':'Manual','source':'manual','content':row.content,'distance':.9,
                 'section_spans':c.location.section_spans(row.content),'policy_priority':True}
                for i,row in enumerate(c.rows)]
    instance.search_chunks=search_chunks
    class Embedding:
        name='mock'
        def embed(self,question): self.calls=getattr(self,'calls',0)+1;return [1.,0.]
    provider=Embedding()
    app=SimpleNamespace(state=SimpleNamespace(embedding_provider=provider,vector_store=instance))
    evidence,_,omission=ChatContext(app,None).retrieve({'tenant_id':'tenant-a'},'¿Un presupuesto apaga recursos?',evidence_limit=limit)
    assert len(evidence)==expected and provider.calls==1
    assert omission['omitted_policy_chunks']==6-expected
    assert calls[0]['policy_section']=='Budgets Y Forecast'
    assert calls[0]['top_k']==20
