"""Offline count and immutable real-embedding input set; no provider calls."""
import hashlib
import json
from pathlib import Path
import statistics
import time
from app.embeddings.chunker import TextChunker
from app.embeddings.structural_chunker import StructuredChunker

root=Path('/evidence')
path=root/'evaluation-corpus-frozen-v2.json'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b'
corpus=json.loads(path.read_text())
chunker=StructuredChunker()
legacy=TextChunker(500,50)
cases=[]
unique={}
def key(text): return hashlib.sha256(('economicon-embedding\0'+text).encode()).hexdigest()
def register(text):
    identity=key(text)
    unique[identity]={'cache_key':identity,'model':'economicon-embedding','dimensions':1536,
                     'input':text,'tokens':chunker.counter.count(text)}
    return identity

for case in corpus['cases']:
    document=case['document']
    started=time.perf_counter(); old=legacy.split(document['text']); old_seconds=time.perf_counter()-started
    started=time.perf_counter(); new=chunker.chunk_document(document); new_seconds=time.perf_counter()-started
    old_records=[]
    cursor=0
    for i,content in enumerate(old):
        # Legacy normalizes all whitespace. Its evidence match is measured against
        # normalized reference text, never its old chunk ID.
        old_records.append({'document_id':document['document_id'],'chunk_index':i,
            'content':content,'cache_key':register(content),'token_count':chunker.counter.count(content)})
    for chunk in new['chunks']:
        chunk['cache_key']=register(chunk['content'])
    for question in case['questions']:
        question['cache_key']=register(question['query'])
    cases.append({'name':case['name'],'document':document,'questions':case['questions'],
                  'old':old_records,'new':new,'timing_seconds':{'old':old_seconds,'new':new_seconds}})

all_old=[row for case in cases for row in case['old']]
all_new=[row for case in cases for row in case['new']['chunks']]
queries=[row for case in cases for row in case['questions']]
total=sum(row['tokens'] for row in unique.values())
summary={'corpus_sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'documents':len(cases),
         'queries':len(queries),'old_chunks':len(all_old),'new_chunks':len(all_new),
         'tokenizer_id':chunker.counter.identity,
         'old_chunk_tokens':[row['token_count'] for row in all_old],
         'new_chunk_tokens':[row['metadata']['token_count'] for row in all_new],
         'new_effective_overlap_tokens':sum(row['metadata']['effective_overlap_tokens'] for row in all_new),
         'new_repeated_context_tokens':sum(rep['token_count'] for row in all_new for rep in row['metadata']['repetitions']),
         'deduplicated_inputs':len(unique), 'deduplicated_tokens':total,
         'maximum_attempts_per_input':3,'maximum_billable_tokens':total*3,
         'price_usd_per_million_tokens':'0.02','maximum_estimated_cost_usd':total*3*0.02/1_000_000,
         'first_lot_cap_usd':0.01,'total_cap_eur':0.10,'budget_pool':'rag-phase2-tests-20261015',
         'provider_calls':0,'quality_claim':False}
assert summary['maximum_estimated_cost_usd']<0.01
result={'summary':summary,'cases':cases,'requests':list(unique.values())}
output=root/'comparison-inputs-v1.json'
assert not output.exists(),'Freeze a new numbered candidate rather than overwrite an input lot'
output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
(root/'comparison-offline-count-v1.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
