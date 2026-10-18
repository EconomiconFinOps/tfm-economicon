"""Frozen old/new retrieval comparison using cached real embeddings and real pgvector."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from sqlalchemy import create_engine,text
from app.vector_store.pgvector_store import PgVectorStore
from app.embeddings.normalized import parent_metadata

root=Path('/evidence')
inputs=json.loads((root/'comparison-inputs-v1.json').read_text())
password=os.environ['POSTGRES_PASSWORD']
base='postgresql+psycopg://postgres:'+password+'@postgres-pgvector:5432/'
admin=create_engine(base+'embeddings',isolation_level='AUTOCOMMIT')
names={'old':'rag2_t800_comparison_old','new':'rag2_t800_comparison_new'}
for name in names.values():
    with admin.connect() as connection: connection.execute(text('CREATE DATABASE "'+name+'"'))
admin.dispose()

def vector(cache_key):
    item=json.loads((root/'embedding-cache'/(cache_key+'.json')).read_text())
    assert item['dimensions']==1536 and item['upstream_model']=='openrouter/openai/text-embedding-3-small'
    return item['embedding']

stores={kind:PgVectorStore(base+name,1536) for kind,name in names.items()}
try:
    for store in stores.values(): store.initialize()
    for case in inputs['cases']:
        doc=case['document']
        common={'job_id':doc['document_id'],'tenant_id':doc['tenant_id'],'source':'synthetic-evaluation',
                'artifact_uri':None,'text_content':doc['text'],'provider_name':'litellm'}
        stores['old'].store_document(**common,chunks=[row['content'] for row in case['old']],
            embeddings=[vector(row['cache_key']) for row in case['old']])
        stores['new'].store_document(**common,chunks=case['new']['chunks'],
            embeddings=[vector(row['cache_key']) for row in case['new']['chunks']],
            document_metadata=parent_metadata(doc,case['new']['manifest']),expected_publication=None)
finally:
    for store in stores.values(): store.close()

backend='''
import json,os,time
from pathlib import Path
from app.services.vector_store import PgVectorQueryStore
from app.services.citations import resolve_citations
root=Path('/evidence')
inputs=json.loads((root/'comparison-inputs-v1.json').read_text())
base='postgresql+psycopg://postgres:'+os.environ['POSTGRES_PASSWORD']+'@postgres-pgvector:5432/'
output={}
for kind in ('old','new'):
    store=PgVectorQueryStore(base+'rag2_t800_comparison_'+kind)
    records=[]
    try:
        for case in inputs['cases']:
            for number,question in enumerate(case['questions']):
                cached=json.loads((root/'embedding-cache'/(question['cache_key']+'.json')).read_text())
                started=time.perf_counter()
                rows=store.search_chunks(case['document']['tenant_id'],cached['embedding'],20,provider='litellm')
                elapsed=time.perf_counter()-started
                expected=' '.join(question['evidence'].split())
                rank=next((index+1 for index,row in enumerate(rows) if row['document_id']==question['document_id']
                           and expected in ' '.join(row['content'].split())),None)
                cited=resolve_citations([rows[rank-1]['chunk_id']],rows,case['document']['tenant_id'])[0] if rank else None
                records.append({'case':case['name'],'question_index':number,'query':question['query'],
                    'expected_document':question['document_id'],'expected_normalized_span':question['normalized_span'],
                    'expected_page':question['page'],'rank':rank,'retrieval_seconds':elapsed,
                    'top_5_documents':[row['document_id'] for row in rows[:5]],
                    'citation':cited,'page_provenance_matches':cited.get('page')==question['page'] if cited and question['page'] is not None else None})
    finally: store.close()
    output[kind]={'recall':{str(k):sum(row['rank'] is not None and row['rank']<=k for row in records)/len(records) for k in (1,3,5,10)},
                  'questions':len(records),'records':records}
print(json.dumps(output))
'''
completed=subprocess.run([sys.executable,'-B','-c',backend],env={**os.environ,'PYTHONPATH':'/backend'},
                         cwd='/backend',capture_output=True,text=True)
if completed.returncode:
    print(completed.stderr,file=sys.stderr)
    raise RuntimeError('Real retrieval comparison failed')
result=json.loads(completed.stdout)
result['method']={'same_frozen_corpus_sha256':inputs['summary']['corpus_sha256'],
    'same_model':'openrouter/openai/text-embedding-3-small','same_dimensions':1536,
    'same_cosine_distance_and_ranking':True,'same_provider_filter':'litellm','same_tenant_filter':True,
    'hit_definition':'same document and full ground-truth evidence after whitespace normalization within one retrieved chunk',
    'real_pgvector':True,'vectors_reused_from_cache':True,'extra_inference_calls':0,
    'database_names':names,'limitations':'6 synthetic normalized documents, 12 questions; exploratory sample, not representative production quality'}
with (root/'comparison-real-pgvector-v1.json').open('x') as output: json.dump(result,output,ensure_ascii=False,indent=2)
print(json.dumps({'old':result['old']['recall'],'new':result['new']['recall'],'method':result['method']},indent=2))
