"""One-time real phase1 extraction for chunking fixtures; no providers or product writes."""
import hashlib
import json
from pathlib import Path
import uuid
from app.documents.document_processor import extract_local

root=Path('/datasets')
target=root/'normalized'
target.mkdir(exist_ok=True)
inventory=[]
for source in sorted((root/'fixtures').iterdir()):
    raw=source.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    extracted=extract_local(raw,source.suffix[1:])
    document={'schema_version':1,'document_id':str(uuid.uuid5(uuid.NAMESPACE_URL,'rag2-fixture:'+digest)),
        'tenant_id':'tenant-rag2-fixture','original_format':source.suffix[1:],
        'origin':{'source':'document','artifact_uri':None,'uploaded_by':'synthetic-fixture-operator','tenant_id':'tenant-rag2-fixture',
            'filename':source.name,'file_size':len(raw),'content_hash':digest},**extracted}
    encoded=json.dumps(document,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
    output=target/(source.name+'.json')
    assert not output.exists(),'Never replace frozen normalization'
    output.write_bytes(encoded)
    inventory.append({'filename':source.name,'sha256':digest,'normalized_sha256':hashlib.sha256(encoded).hexdigest(),
        'characters':len(document['text']),'blocks':len(document['blocks']),'method':document['extraction_method'],'document_id':document['document_id']})
    print(json.dumps({'filename':source.name,'result':'normalized','characters':len(document['text']),'blocks':len(document['blocks'])}),flush=True)
(target/'inventory.json').write_text(json.dumps({'source':'real accepted phase1 extract_local once; synthetic files only; immutable fixtures reused for chunker unit/integration tests','documents':inventory},indent=2),encoding='utf-8')
