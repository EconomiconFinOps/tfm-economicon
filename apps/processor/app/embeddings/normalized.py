"""Parent document facts stay separate from per-chunk metadata."""
import hashlib
import re


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
        if title and document.get('original_format') == 'md':
            # The Markdown extractor keeps the raw ATX line; a title is the heading text.
            title = re.sub(r'^[ ]{0,3}#{1,6}[ \t]+|[ \t]+#+[ \t]*$', '', title).strip() or None
    return {'schema_version':1, 'original_format':document['original_format'],
            'title':title, 'content_hash':hashlib.sha256(document['text'].encode('utf-8')).hexdigest(),
            'origin':document.get('origin', {}), 'file_metadata':document.get('file_metadata', {}),
            'extraction_method':document.get('extraction_method'),
            'extraction_result':document.get('result'), 'extraction_warnings':document.get('warnings', []),
            'chunking':manifest}
