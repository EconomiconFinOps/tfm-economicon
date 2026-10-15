"""Exercise the real document HTTP/storage/processor flow with an operator-supplied file.

Use only a disposable local stack configured with the existing mock providers.
Credentials come from DOCUMENT_SMOKE_EMAIL / DOCUMENT_SMOKE_PASSWORD, never CLI arguments.
Output contains technical metadata only, never credentials, signed URLs or extracted text.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://localhost:8000')
    parser.add_argument('--tenant',required=True)
    parser.add_argument('--file',required=True,type=Path)
    parser.add_argument('--timeout',type=int,default=300)
    args=parser.parse_args()
    if not 1<=args.timeout<=1800: parser.error('timeout must be1..1800 seconds')
    raw=args.file.read_bytes()
    if not 0<len(raw)<=20_000_000: parser.error('file must be1..20,000,000 bytes')
    headers={'Content-Type':'application/json'}
    def request(path,body=None,*,method=None,custom_headers=None,raw_body=None):
        target=path if path.startswith('http') else args.base_url.rstrip('/')+path
        data=json.dumps(body).encode() if body is not None else raw_body
        try:
            with urlopen(Request(target,data,headers if custom_headers is None else custom_headers,method=method),timeout=90) as response:
                value=response.read()
                return json.loads(value) if value and 'json' in response.headers.get('Content-Type','') else None
        except HTTPError as error:
            code=error.code; error.close()
            raise RuntimeError('HTTP request failed with status '+str(code)) from None
    auth=request('/auth/login',{'email':os.environ['DOCUMENT_SMOKE_EMAIL'],'password':os.environ['DOCUMENT_SMOKE_PASSWORD']})
    headers.update(Authorization='Bearer '+auth['access_token'],**{'X-Tenant-Id':args.tenant})
    digest=hashlib.sha256(raw).hexdigest()
    ticket=request('/jobs/uploads',{'filename':args.file.name,'file_size':len(raw),'content_hash':digest})
    request(ticket['upload_url'],method='PUT',custom_headers=ticket['headers'],raw_body=raw)
    accepted=request('/jobs/uploads/'+ticket['upload_id']+'/confirm',method='POST')
    repeated=request('/jobs/uploads/'+ticket['upload_id']+'/confirm',method='POST')
    assert repeated['job_id']==accepted['job_id'],'Confirmation is not idempotent'
    deadline=time.monotonic()+args.timeout
    while time.monotonic()<deadline:
        status=request('/jobs/uploads/'+ticket['upload_id'])
        if status['job_status']=='failed' and not status['retry_pending']:
            raise RuntimeError('Document processing failed')
        if status['job_status']=='completed': break
        time.sleep(1)
    else: raise RuntimeError('Document processing timed out')
    document=request('/jobs/documents/'+status['job_id'])
    assert document['schema_version']==1 and document['tenant_id']==args.tenant
    assert document['origin']['content_hash']==digest and document['text'].strip()
    assert isinstance(document['blocks'],list) and isinstance(document['warnings'],list)
    print(json.dumps({'result':'passed','upload_id':ticket['upload_id'],'job_id':status['job_id'],
        'duplicate':status['duplicate'],'format':document['original_format'],'text_characters':len(document['text']),
        'blocks':len(document['blocks']),'method':document['extraction_method'],'cleanup_done':status['cleanup_done']}))


if __name__=='__main__':
    try: main()
    except Exception as error:
        # Network exceptions may carry a signed URL. Never print their text or traceback.
        print(json.dumps({'result':'failed','error_type':type(error).__name__}))
        raise SystemExit(1)
