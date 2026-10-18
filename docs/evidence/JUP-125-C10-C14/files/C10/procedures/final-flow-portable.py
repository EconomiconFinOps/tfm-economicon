"""Early real SQL contract probe; synthetic vectors never measure semantic quality."""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.embeddings.structural_chunker import StructuredChunker, reconstruct_normalized_text
from app.embeddings.normalized import parent_metadata
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.vector_store.pgvector_store import PgVectorStore, StalePublication

url=os.environ['FINAL_FLOW_DATABASE_URL']
from sqlalchemy.engine import make_url
target_url=make_url(url)
assert target_url.host in {'127.0.0.1','localhost'} and target_url.port not in {None,5432,26257}
assert target_url.database.startswith('rag2_') and target_url.password and not target_url.query
store=PgVectorStore(url,8)
store.initialize()
counter=StructuredChunker()
provider=MockEmbeddingProvider(8)
class Agent:
    def invoke(self,*args,**kwargs): return {'provider':'mock','purpose':'contract-only'}
runner=PipelineRunner(Agent(),counter,provider,store)
report={'quality_claim':False,'fixtures':[]}
for path in sorted(Path('/source/tests/fixtures/normalized_documents').glob('*.json')):
    document=json.loads(path.read_text())
    document.update(document_id='early-'+path.stem,tenant_id='early-tenant')
    result=runner.run({'job_id':document['document_id'],'tenant_id':document['tenant_id'],
        'source':'synthetic-'+path.stem,'text_content':document['text'],
        'normalized_document':document,'metadata':{}})
    assert result['embedding_result']['chunk_count'] == len(result['chunks'])
    with store.engine.connect() as connection:
        rows=connection.execute(text('SELECT id,document_id,chunk_index,content,metadata FROM document_chunks WHERE document_id=:id ORDER BY chunk_index'),
                                {'id':document['document_id']}).all()
    assert [row.content for row in rows] == [chunk['content'] for chunk in result['chunks']]
    assert [row.metadata for row in rows] == [chunk['metadata'] for chunk in result['chunks']]
    persisted_chunks=[{'chunk_id':row.id,'document_id':row.document_id,'chunk_index':row.chunk_index,'content':row.content,'metadata':row.metadata} for row in rows]
    assert reconstruct_normalized_text(persisted_chunks)==document['text']
    report['fixtures'].append({'format':path.stem,'chunks':len(rows),'persisted_metadata':True,'reconstructed_from_sql_chunks_only':True})

def snapshot(doc_id):
    with store.engine.connect() as connection:
        return [list(row) for row in connection.execute(text('SELECT dc.id,dc.content,dc.metadata,ce.embedding::text,kd.metadata FROM knowledge_documents kd JOIN document_chunks dc ON dc.document_id=kd.id JOIN chunk_embeddings ce ON ce.chunk_id=dc.id WHERE kd.id=:id ORDER BY dc.chunk_index'),{'id':doc_id})]

document={'schema_version':1,'document_id':'early-atomic-'+uuid4().hex,'tenant_id':'early-tenant','original_format':'txt',
          'text':'Original durable evidence','blocks':[],'extraction_method':'manual-text','file_metadata':{}}
def publish(doc,expected):
    value=counter.chunk_document(doc)
    return store.store_document(job_id=doc['document_id'],tenant_id=doc['tenant_id'],source='synthetic',
        artifact_uri=None,text_content=doc['text'],chunks=value['chunks'],
        embeddings=[provider.embed(chunk['content']) for chunk in value['chunks']],provider_name='mock',
        document_metadata=parent_metadata(doc,value['manifest']),expected_publication=expected)
original=publish(document,None)
before=snapshot(document['document_id'])
with store.engine.begin() as connection:
    connection.execute(text("ALTER TABLE document_chunks ADD CONSTRAINT early_forced_failure CHECK (content NOT LIKE '%forced-rollback%')"))
try:
    publish({**document,'text':'forced-rollback evidence'},original['publication_id'])
    raise AssertionError('SQL failure was not injected')
except IntegrityError:
    assert snapshot(document['document_id']) == before
finally:
    with store.engine.begin() as connection:
        connection.execute(text('ALTER TABLE document_chunks DROP CONSTRAINT early_forced_failure'))
report['rollback_after_delete_preserves_all_rows']=True
new=publish({**document,'text':'New durable evidence'},original['publication_id'])
try:
    publish({**document,'text':'Stale result'},original['publication_id'])
    raise AssertionError('Stale publication was accepted')
except StalePublication:
    assert store.publication(document['document_id'],document['tenant_id'])==new['publication_id']
report['stale_publication_rejected']=True
store.store_document(job_id='early-legacy',tenant_id='early-tenant',source='legacy',artifact_uri=None,
    text_content='# Legacy\n## Section\nUnique old evidence',chunks=['Unique old evidence'],
    embeddings=[provider.embed('Unique old evidence')],provider_name='mock')
store.store_document(job_id='early-foreign',tenant_id='foreign-tenant',source='foreign',artifact_uri=None,
    text_content='foreign secret',chunks=['foreign secret'],embeddings=[provider.embed('Unique old evidence')],provider_name='mock')
store.close()

# Separate Python deployment: importing backend app cannot reuse processor app.
backend='''
import json,os
from app.services.vector_store import PgVectorQueryStore
from app.services.citations import resolve_citations
from sqlalchemy import text
url=os.environ['FINAL_FLOW_DATABASE_URL']
store=PgVectorQueryStore(url)
with store.engine.connect() as connection:
    vector=connection.execute(text("SELECT embedding::text FROM chunk_embeddings WHERE chunk_id='early-legacy:chunk:0'")).scalar_one()
records=store.search_chunks('early-tenant',json.loads(vector),20,provider='mock')
assert all(record['tenant_id']=='early-tenant' for record in records)
legacy=next(record for record in records if record['document_id']=='early-legacy')
assert legacy['section']=='Section' and legacy['title']=='Legacy'
pdf=next(record for record in records if record['document_id']=='early-table.pdf')
assert pdf['page']==1 and pdf['source_spans'] and pdf['position_contract']
citations=resolve_citations([legacy['chunk_id'],pdf['chunk_id']],records,'early-tenant')
assert citations[1]['page']==1 and citations[1]['source_spans']
assert 'source_spans' not in citations[0]
assert store.search_chunks('empty-tenant',json.loads(vector),4,provider='mock')==[]
from pathlib import Path
verified=[]
for filename in sorted(Path('/source/tests/fixtures/normalized_documents').glob('*.json')):
    oracle=json.loads(filename.read_text(encoding='utf-8'))
    expected_id='early-'+filename.stem
    recovered=[record for record in records if record['document_id']==expected_id]
    assert recovered,expected_id
    for record in recovered:
        metadata=record['chunk_metadata']
        with store.engine.connect() as connection:
            persisted=connection.execute(text('SELECT metadata FROM document_chunks WHERE id=:id'),{'id':record['chunk_id']}).scalar_one()
        assert metadata==persisted
        for span in metadata['source_spans']:
            start,end=span['normalized_range']
            carriers=[item for item in metadata['primary_spans']+metadata['repetitions']
                      if item['normalized_range'][0]<=start<end<=item['normalized_range'][1]]
            assert carriers
            for carrier in carriers:
                offset=carrier['content_range'][0]+start-carrier['normalized_range'][0]
                assert record['content'][offset:offset+end-start]==oracle['text'][start:end]
        [citation]=resolve_citations([record['chunk_id']],[record],'early-tenant')
        assert citation['document_id']==expected_id
        assert citation['source_spans']==metadata['source_spans']
        assert citation['excerpt']==record['content'][:280]
    verified.append({'format':filename.stem,'retrieved_chunks':len(recovered),'text_and_citation_provenance_contrasted':True})
print(json.dumps({'tenant_isolation':True,'legacy_search_and_citations':True,
                  'new_pdf_citation_provenance':True,'all_real_normalized_formats':verified}))
store.close()
'''
completed=subprocess.run([sys.executable,'-B','-c',backend],env={**os.environ,'PYTHONPATH':'/backend'},
                         cwd='/backend',capture_output=True,text=True)
if completed.returncode:
    print(completed.stderr,file=sys.stderr)
    raise RuntimeError('Backend contract probe failed')
report['retrieval']=json.loads(completed.stdout)
with Path('/evidence/early-integration-result.json').open('x',encoding='utf-8') as result_file: json.dump(report,result_file,indent=2)
print(json.dumps(report,indent=2))
