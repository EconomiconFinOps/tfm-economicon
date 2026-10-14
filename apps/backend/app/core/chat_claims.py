"""Literal documentary excerpts, separately labelled interpretations, and provenance.

Selection makes support inspectable; it does not establish semantic entailment.
"""
import copy
import re

PASSAGE_LIMIT=220
PASSAGE_COUNT=96


def table_rows(content):
    """Recover complete literal rows from whitespace-flattened Markdown tables.

    A separator establishes the column count. Partial rows and rows with a
    different width are not offered; labels/values are never reconstructed.
    """
    parts = re.split(r'(?<=\|)\s+(?=\|)', content)
    width = None
    rows = []
    for part in parts:
        if not part.startswith('|'):
            width = None
            continue
        end = part.rfind('|')
        if end == 0:
            width = None
            continue
        cells = part[1:end].split('|')
        if len(cells) >= 2 and all(re.fullmatch(r'\s*:?-{3,}:?\s*', cell) for cell in cells):
            width = len(cells)
            continue
        if width is None:
            continue
        if len(cells) != width or any(not cell.strip() for cell in cells):
            width = None
            continue
        rows.append(part[:end+1])
        if part[end+1:].strip():
            width = None
    return rows


def passages(content):
    if not isinstance(content,str) or not content.strip():return []
    # Preserve exact bytes/characters of each selected contiguous span. Long
    # sentences are not silently cut into assertions; the model may select
    # another bounded sentence, otherwise this fragment offers no short quote.
    spans=re.split(r'(?<=[.!?;])(?=\s)|\n+',content)
    result=[]
    for span in spans:
        value=span.strip()
        if (value and len(value)<=PASSAGE_LIMIT and value not in result
                and not re.fullmatch(r'[\W\d_]+',value) and not value.startswith('#')):
            result.append(value)
    for row in table_rows(content):
        if len(row) <= PASSAGE_LIMIT and row not in result:
            result.append(row)
    return result[:PASSAGE_COUNT]


def documentary_schema(sources):
    choices=[]
    for source in sources:
        if source.get('kind')!='corpus':continue
        quotes=passages(source.get('content'))
        if quotes:
            choices.append({'type':'object','properties':{
                'source_id':{'type':'string','const':source['id']},
                'passage':{'type':'string','enum':quotes,'maxLength':PASSAGE_LIMIT}},
                'required':['source_id','passage'],'additionalProperties':False})
    if not choices:return None
    inner=choices[0] if len(choices)==1 else {'anyOf':choices}
    return {'type':'object','properties':{'documentary':inner},
            'required':['documentary'],'additionalProperties':False}


def render_documentary(selection,sources):
    if not isinstance(selection,dict) or set(selection)!={'source_id','passage'}:
        raise ValueError('Documentary selection shape invalid.')
    if not isinstance(selection['source_id'],str) or not isinstance(selection['passage'],str):
        raise ValueError('Documentary selection shape invalid.')
    matches=[source for source in sources if source.get('id')==selection['source_id']]
    if len(matches)!=1 or matches[0].get('kind')!='corpus':
        raise ValueError('Documentary selection source unavailable.')
    source=matches[0]
    if selection['passage'] not in passages(source.get('content')):
        raise ValueError('Documentary selection passage mismatch.')
    # Source identity is server-owned. No model supplied title/URL is rendered.
    label=source.get('title')
    if not isinstance(label,str) or not label.strip() or len(label)>256:
        raise ValueError('Documentary selection source unavailable.')
    text='\nFuente: '+label+' — «'+selection['passage']+'»\n'
    if len(text)>500:raise ValueError('Documentary excerpt output limit.')
    return text,copy.deepcopy(source)
