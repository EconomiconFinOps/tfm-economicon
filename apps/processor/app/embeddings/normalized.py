"""Parent document facts stay separate from per-chunk metadata."""
import hashlib


def manual_document(state):
    text = state['text_content']
    return {'schema_version':1, 'document_id':state['job_id'], 'tenant_id':state['tenant_id'],
            'original_format':'manual-text', 'text':text, 'blocks':[], 'file_metadata':{},
            'warnings':[], 'extraction_method':'manual-text', 'result':'extracted',
            'origin':{'source':state['source'], 'artifact_uri':state.get('artifact_uri'),
                      'content_hash':hashlib.sha256(text.encode('utf-8')).hexdigest()}}


def parent_metadata(document, manifest):
    title = document.get('file_metadata', {}).get('title')
    if not title:
        title = next((block.get('text') for block in document['blocks']
                      if block.get('kind') == 'heading' and block.get('text')), None)
    return {'schema_version':1, 'original_format':document['original_format'],
            'title':title, 'content_hash':hashlib.sha256(document['text'].encode('utf-8')).hexdigest(),
            'origin':document.get('origin', {}), 'file_metadata':document.get('file_metadata', {}),
            'extraction_method':document.get('extraction_method'),
            'extraction_result':document.get('result'), 'extraction_warnings':document.get('warnings', []),
            'chunking':manifest}
