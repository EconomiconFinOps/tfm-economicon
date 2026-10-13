"""Private, bounded response segments; public response fields remain strings."""
import copy

from app.core.chat_calculations import render_text
from app.core.chat_rules import required_classification
from app.core.chat_expressions import ExpressionRenderer, expression_definitions

class ServerRenderedResponse(dict):
    """In-process provenance, never a JSON flag accepted from a provider."""
    def __init__(self, value, records):
        super().__init__(value)
        self.documentary_records=tuple(copy.deepcopy(records))


def server_evidence(records):
    return [{key:record[key] for key in ('id','kind','title','source')} for record in records]


CLASSIFIED_NOTES=(
    'Las cantidades proceden del escenario aportado; no son métricas financieras verificadas.',
    'La clasificación aplica únicamente al KPI y a la sección documental indicados.',
    'El denominador es el mostrado en la fórmula; debe corresponder a los conceptos elegibles del escenario.',
)


def quote_choices(content):
    if not isinstance(content,str) or not content.strip():
        raise ValueError('Invalid corpus quotation source.')
    # Every choice is a literal passage. The context budget accounts for all of
    # them; no generated paraphrase or automatic citation is introduced.
    return [content[i:i+2048] for i in range(0,len(content),2048) if content[i:i+2048].strip()]


def segment_schema(records=None, *, limit=4000, quantities=None):
    choices=[{'type':'object','properties':{'text':{'type':'string','maxLength':limit}},
              'required':['text'],'additionalProperties':False}]
    if quantities:
        choices.append({'$ref':'#/$defs/SourceQuantity'})
        choices.append({'type':'object','properties':{'expression':{'$ref':'#/$defs/RenderedExpression'}},
                        'required':['expression'],'additionalProperties':False})
    elif records:
        choices.append({'type':'object','properties':{'calculation_id':{
            'type':'string','enum':[record['id'] for record in records]}},
            'required':['calculation_id'],'additionalProperties':False})
    return {'type':'array','minItems':1,'maxItems':128,'items':choices[0] if len(choices)==1 else {'anyOf':choices}}


def bind_segments(schema, records=None, quantities=None):
    schema=copy.deepcopy(schema)
    if quantities:schema.setdefault('$defs',{}).update(expression_definitions(quantities))
    branches=schema.get('anyOf',[schema])
    classified=[]
    for branch in branches:
        properties=branch['properties']
        properties['answer']=segment_schema(records, quantities=quantities)
        for field in ('assumptions','limitations','next_actions'):
            # One bounded prose segment per short public item. Arithmetic lives
            # in answer; allowing128 short segments advertised values that the
            # unchanged500-character public contract necessarily rejects.
            item=segment_schema(limit=500)
            item['maxItems']=1
            properties[field]['items']=item
        if 'DocumentaryClassification' in schema.get('$defs',{}) and 'ok' in properties['status'].get('enum',[]):
            variant=copy.deepcopy(branch)
            props=variant['properties']
            props['answer']={'type':'object','properties':{
                'calculations':{'type':'array','maxItems':4,'items':{'$ref':'#/$defs/NumericRenderedExpression'}},
                'classification':{'$ref':'#/$defs/DocumentaryClassification'}},
                'required':['calculations','classification'],'additionalProperties':False}
            for field in ('assumptions','limitations'):
                props[field]['items']={'type':'array','minItems':1,'maxItems':1,'items':{
                    'type':'object','properties':{'text':{'type':'string','enum':list(CLASSIFIED_NOTES)}},
                    'required':['text'],'additionalProperties':False}}
            for field in ('next_actions','recommendations','metrics'):props[field]['maxItems']=0
            props['evidence']['minItems']=0
            props['evidence']['maxItems']=0
            classified.append(variant)
    if classified:
        retained=[branch for branch in branches if not (required_classification(quantities)
            and 'ok' in branch['properties']['status'].get('enum',[]))]
        schema['anyOf']=classified+retained if required_classification(quantities) else retained+classified
    return schema


def render_classified_answer(value,expressions):
    if (not isinstance(value,dict) or set(value)!={'calculations','classification'}
            or expressions is None or not isinstance(value['calculations'],list)
            or len(value['calculations'])>4):raise ValueError('Invalid classified answer.')
    parts=[]
    for node in value['calculations']:
        if not isinstance(node,dict) or node.get('operation') in (None,'classify','compare'):
            raise ValueError('Invalid classified calculation.')
        parts.append(expressions.render(node))
    node=value['classification']
    if not isinstance(node,dict) or node.get('operation')!='classify':raise ValueError('Invalid classified answer.')
    parts.append(expressions.render(node))
    text=''.join(parts).strip()
    if len(text)>4000:raise ValueError('Rendered text limit.')
    return text


def render_segment(segment, records, expressions=None):
    if not isinstance(segment,dict):raise ValueError('Invalid response segment.')
    if set(segment)=={'text'}:
        text=segment['text']
        if not isinstance(text,str) or '[[calc:' in text:
            raise ValueError('Invalid segment text.')
        # Slots and raw equations cannot bypass the typed reference branch.
        if expressions is not None:expressions.check_prose(text)
        return render_text(text,[])
    if set(segment)=={'calculation_id'}:
        if expressions is not None:raise ValueError('Invalid segment reference.')
        identifier=segment['calculation_id']
        if not isinstance(identifier,str):raise ValueError('Invalid segment reference.')
        matches=[record for record in records if record['id']==identifier]
        if len(matches)!=1:raise ValueError('Invalid segment reference.')
        return matches[0]['equation']
    if set(segment)=={'quantity'} and expressions is not None:
        return expressions.render_quantity(segment['quantity'])
    if set(segment)=={'expression'} and expressions is not None:
        if isinstance(segment['expression'],dict) and segment['expression'].get('operation')=='classify':
            raise ValueError('Classification requires typed answer.')
        return expressions.render(segment['expression'])
    raise ValueError('Invalid response segment.')


def render_segments(segments, records, *, limit=4000, expressions=None):
    if not isinstance(segments,list) or not 1<=len(segments)<=128:
        raise ValueError('Invalid segment collection.')
    parts=[];pending=[]
    for segment in segments:
        # Validate shape before grouping adjacent text. Group validation closes
        # bypasses where an equation or a slot is split across text segments.
        rendered=render_segment(segment,records,expressions)
        if 'text' in segment:pending.append(rendered)
        else:
            if pending:parts.append(render_segment({'text':''.join(pending)},records,expressions));pending=[]
            parts.append(rendered)
    if pending:parts.append(render_segment({'text':''.join(pending)},records,expressions))
    result=''.join(parts)
    if len(result)>limit:raise ValueError('Rendered text limit.')
    result=result.strip()
    if not result:raise ValueError('Empty rendered text.')
    return result


def render_response(value, records, *, quantities=None):
    if not isinstance(value,dict) or 'answer' not in value:
        raise ValueError('Invalid calculation response.')
    expressions=ExpressionRenderer(quantities) if quantities is not None else None
    classified=isinstance(value['answer'],dict)
    if required_classification(quantities) and value.get('status') in ('ok','partial') and not classified:
        raise ValueError('Explicit classification requires typed answer.')
    if classified:
        if value.get('evidence')!=[]:raise ValueError('Classified evidence is server-owned.')
        for field in ('next_actions','recommendations','metrics'):
            if value.get(field)!=[]:raise ValueError('Invalid classified auxiliary fields.')
        for field in ('assumptions','limitations'):
            items=value.get(field)
            if not isinstance(items,list) or any(item not in [[{'text':note}] for note in CLASSIFIED_NOTES] for item in items):
                raise ValueError('Invalid classified auxiliary fields.')
    result={**value,'answer':render_classified_answer(value['answer'],expressions) if classified else render_segments(value['answer'],records,expressions=expressions)}
    for field in ('assumptions','limitations','next_actions'):
        if field not in value or not isinstance(value[field],list) or len(value[field])>10:
            raise ValueError('Invalid calculation collection.')
        for item in value[field]:
            if (not isinstance(item,list) or len(item)!=1 or
                    not isinstance(item[0],dict) or set(item[0])!={'text'}):
                raise ValueError('Invalid short prose item.')
        result[field]=[render_segments(item,[],limit=500,expressions=None if classified else expressions) for item in value[field]]
    if expressions is not None:
        for recommendation in value.get('recommendations',[]):
            if isinstance(recommendation,dict):
                for field in ('action','rationale'):
                    if isinstance(recommendation.get(field),str):expressions.check_prose(recommendation[field])
    if classified:
        known={record['id']:record for record in getattr(quantities,'rule_sources',())}
        if not expressions.documentary_sources or not expressions.documentary_sources<=known.keys():
            raise ValueError('Derived documentary source unavailable.')
        records=[known[identifier] for identifier in sorted(expressions.documentary_sources)]
        if len(records)>20 or any(record.get('kind')!='corpus' for record in records):
            raise ValueError('Derived documentary source unavailable.')
        result['evidence']=server_evidence(records)
        return ServerRenderedResponse(result,records)
    if expressions is not None and expressions.documentary_sources:
        evidence=value.get('evidence')
        if not isinstance(evidence,list) or any(not isinstance(item,dict) for item in evidence):
            raise ValueError('Documentary calculation citation missing.')
        cited={item.get('id') for item in evidence if item.get('kind')=='corpus'}
        if not expressions.documentary_sources<=cited:
            raise ValueError('Documentary calculation citation missing.')
    return result
