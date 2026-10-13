"""Bounded positional neighbors share the retrieval tenant/provider snapshot."""
from types import SimpleNamespace
import pytest
from app.services.vector_store import PgVectorQueryStore


class Rows(list):
    def all(self):return self


class Connection:
    def __init__(self,seeds,neighbors):self.seeds=seeds;self.neighbors=neighbors;self.calls=[]
    def connect(self):return self
    def execution_options(self,**kw):self.options=kw;return self
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,statement,params):
        sql=str(statement);self.calls.append((sql,params))
        if 'text_content' in sql:return [SimpleNamespace(id=doc,text_content='# Manual\ncontent') for doc in params['document_ids']]
        if 'neighbor_limit' in params:return Rows(self.neighbors)
        return Rows(self.seeds)


def row(index,document='doc'):
    return SimpleNamespace(chunk_id=f'{document}:{index}',document_id=document,tenant_id='tenant-a',chunk_index=index,source='manual',content='content',distance=.12)


def store(seeds,neighbors):
    instance=PgVectorQueryStore.__new__(PgVectorQueryStore);instance.engine=Connection(seeds,neighbors);return instance


def test_neighbor_outside_vector_pool_is_loaded_by_exact_scoped_position():
    instance=store([row(4),row(9)], [row(3),row(5)])
    result=instance.search_chunks('tenant-a',[1.,0.],top_k=4,provider='p',neighbor_seed_count=1)
    assert [r['chunk_id'] for r in result]==['doc:4','doc:3','doc:5','doc:9']
    assert instance.engine.options=={'isolation_level':'REPEATABLE READ'}
    sql,params=instance.engine.calls[1]
    assert 'kd.tenant_id = :tenant_id' in sql and 'ce.provider = :provider' in sql
    assert params['tenant_id']=='tenant-a' and params['provider']=='p'
    assert {(params['document_0'],params['index_0']),(params['document_1'],params['index_1'])}=={('doc',3),('doc',5)}
    assert params['neighbor_limit']==2 and 'LIMIT :neighbor_limit' in sql
    assert result[1]['distance']==.12


def test_expansion_preserves_top_k_bound_and_does_not_expand_recursively():
    instance=store([row(4),row(9)],[row(3),row(5),row(2)])
    result=instance.search_chunks('tenant-a',[1.],top_k=2,neighbor_seed_count=1)
    assert [r['chunk_id'] for r in result]==['doc:4','doc:3']
    assert len(instance.engine.calls)==3
    assert all(r['chunk_id']!='doc:2' for r in result)


def test_neighbors_from_other_document_or_position_are_not_selected():
    instance=store([row(4)], [row(3,'other'),row(99)])
    result=instance.search_chunks('tenant-a',[1.],top_k=3,neighbor_seed_count=1)
    assert [r['chunk_id'] for r in result]==['doc:4']


@pytest.mark.parametrize('count',[-1,True,21,'1'])
def test_bad_neighbor_budget_rejected_before_query(count):
    instance=store([],[])
    with pytest.raises(ValueError):instance.search_chunks('tenant-a',[1.],top_k=20,neighbor_seed_count=count)
    assert instance.engine.calls==[]


def test_default_contract_does_not_add_positional_lookup():
    instance=store([row(4)],[row(3)])
    assert [r['chunk_id'] for r in instance.search_chunks('tenant-a',[1.])]==['doc:4']
    assert len(instance.engine.calls)==2
