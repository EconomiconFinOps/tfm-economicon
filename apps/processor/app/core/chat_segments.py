"""Private, bounded response segments; public response fields remain strings."""
import copy

from app.core.chat_calculations import render_text
from app.core.chat_rules import required_classification
from app.core.chat_boolean_rules import boolean_definition, render_boolean
from app.core.chat_expressions import ExpressionRenderer, expression_definitions
from app.core.chat_response_modes import bind_modes, response_prefix, BASIS_STATUSES, DOCUMENTARY_BASES

class ServerRenderedResponse(dict):
    """In-process provenance, never a JSON flag accepted from a provider."""
    def __init__(self, value, records):
        super().__init__(value)
        self.documentary_records=tuple(copy.deepcopy(records))


def server_evidence(records):
    return [{key:record[key] for key in ('id','kind','title','source')} for record in records]


def project_recommendation_citations(value,authorized_evidence):
    """Project explicit private selections, never infer a supporting source.

    Every selected record is checked before union/deduplication, including a
    record already present in top-level evidence with a different quotation.
    This does not verify entailment of a recommendation's prose.
    """
    recommendations=value.get('recommendations')
    if recommendations==[]:return value
    if not isinstance(recommendations,list) or len(recommendations)>20:
        raise ValueError('Invalid recommendation collection.')
    known={source['id']:source for source in authorized_evidence}
    evidence=value.get('evidence')
    if not isinstance(evidence,list):raise ValueError('Invalid evidence collection.')

    def checked(items):
        if not isinstance(items,list) or len(items)>20:raise ValueError('Invalid recommendation citations.')
        result=[];seen=set()
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str):
                raise ValueError('Recommendation citation shape invalid.')
            identifier=item['id'];source=known.get(identifier)
            if source is None:raise ValueError('Recommendation citation source unknown.')
            if identifier in seen:raise ValueError('Recommendation citation duplicated.')
            fields={'id','kind','title','source'}
            if source.get('kind')=='corpus':fields.add('support_quote')
            if set(item)!=fields or any(item.get(key)!=source.get(key) for key in ('id','kind','title','source')):
                raise ValueError('Recommendation citation metadata mismatch.')
            if source.get('kind')=='corpus' and item['support_quote'] not in quote_choices(source.get('content')):
                raise ValueError('Citation passage is not grounded.')
            seen.add(identifier);result.append(copy.deepcopy(item))
        return result

    combined=checked(evidence);seen={item['id'] for item in combined};projected=[]
    for recommendation in recommendations:
        if not isinstance(recommendation,dict) or 'evidence_ids' in recommendation or 'evidence' not in recommendation:
            raise ValueError('Recommendation citations must be explicit records.')
        chosen=checked(recommendation['evidence'])
        if not chosen:raise ValueError('Invalid recommendation citations.')
        projected.append({**{key:item for key,item in recommendation.items() if key!='evidence'},
            'evidence_ids':[item['id'] for item in chosen]})
        for item in chosen:
            if item['id'] not in seen:combined.append(item);seen.add(item['id'])
    if len(combined)>20:raise ValueError('Invalid recommendation citations.')
    return {**value,'recommendations':projected,'evidence':combined}


CLASSIFIED_NOTES=(
    'Las cantidades proceden del escenario aportado; no son mÃ©tricas financieras verificadas.',
    'La clasificaciÃ³n aplica Ãºnicamente al KPI y a la secciÃ³n documental indicados.',
    'El denominador es el mostrado en la fÃ³rmula; debe corresponder a los conceptos elegibles del escenario.',
)


BOOLEAN_NOTES=('Las cantidades y la regla se aplican Ãºnicamente al escenario indicado.',
    'Una condiciÃ³n indefinida no se convierte en un resultado numÃ©rico inventado.',)
CLASSIFICATION_ABSTENTIONS=('No puedo clasificar de forma fundada: necesito identificar los componentes del coste elegible y el numerador del KPI.',
    'No puedo clasificar de forma fundada: necesito una regla completa y aplicable al KPI solicitado.',)


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
        if required_classification(quantities):
            for branch in branches:
                if 'ok' not in branch['properties']['status'].get('enum',[]):
                    branch['properties']['answer']={'type':'array','minItems':1,'maxItems':1,'items':{'type':'object','properties':{'text':{'type':'string','enum':list(CLASSIFICATION_ABSTENTIONS)}},'required':['text'],'additionalProperties':False}}
                    for field in ('assumptions','limitations','next_actions','recommendations','metrics','evidence'):
                        branch['properties'][field]['maxItems']=0
        retained=[branch for branch in branches if not (required_classification(quantities)
            and 'ok' in branch['properties']['status'].get('enum',[]))]
        schema['anyOf']=classified+retained if required_classification(quantities) else retained+classified
    rules=getattr(quantities,'boolean_rules',())
    if rules:
        # Rule/operator/operands are all grounded before generation. The model
        # selects a typed terminal, never the condition or its conclusion.
        base=copy.deepcopy(branches[-1]);props=base['properties']
        props['answer']={'type':'object','properties':{'boolean':boolean_definition(rules)},'required':['boolean'],'additionalProperties':False}
        props['status']={'type':'string','enum':['ok'] if rules[0]['source_ids'] else ['insufficient_data']}
        props['evidence']['minItems']=0;props['evidence']['maxItems']=0
        for field in ('next_actions','recommendations','metrics'):props[field]['maxItems']=0
        for field in ('assumptions','limitations'):
            props[field]['items']={'type':'array','minItems':1,'maxItems':1,'items':{'type':'object','properties':{'text':{'type':'string','enum':list(BOOLEAN_NOTES)}},'required':['text'],'additionalProperties':False}}
        if getattr(quantities,'boolean_requested',False):
            return {**base,'$defs':schema['$defs']}
        if 'anyOf' in schema:schema['anyOf'].append(base)
        else:schema={'type':'object','anyOf':[{k:v for k,v in schema.items() if k!='$defs'},base],'$defs':schema['$defs']}
    return schema if required_classification(quantities) else bind_modes(schema,quantities)



def render_classified_answer(value,expressions):
    if isinstance(value,dict) and set(value)=={'boolean'}:
        if expressions is None:raise ValueError('Boolean rule not grounded.')
        from decimal import localcontext
        with localcontext() as precision:
            precision.prec=40
            result=render_boolean(value['boolean'],expressions)
        if len(result)>4000:raise ValueError('Rendered text limit.')
        return result
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
    basis=value.get('basis')
    classified=isinstance(value['answer'],dict)
    boolean=classified and set(value['answer'])=={'boolean'}
    if getattr(quantities,'boolean_rules',()) and getattr(quantities,'boolean_requested',False) and not boolean:
        raise ValueError('Explicit boolean rule requires typed answer.')
    if classified:
        if 'basis' in value:raise ValueError('Terminal response cannot override basis.')
    elif not required_classification(quantities):
        response_prefix(basis)
        if basis=='authorized_evidence':
            if not value.get('evidence'):raise ValueError('Narrative requires selected evidence.')
        else:
            if basis not in BASIS_STATUSES:raise ValueError('Invalid response basis.')
            if value.get('status') not in BASIS_STATUSES[basis]:raise ValueError('Response basis status mismatch.')
            restricted=('metrics','recommendations') if basis in DOCUMENTARY_BASES else ('evidence','metrics','recommendations')
            if any(value.get(field)!=[] for field in restricted):
                raise ValueError('Response basis cannot grant authority.')
            if basis in ('missing_data','clarification','refusal') and not value.get('next_actions'):
                raise ValueError('Response basis requires useful next action.')

    if required_classification(quantities) and not classified:
        if value['answer'] not in [[{'text':note}] for note in CLASSIFICATION_ABSTENTIONS]:
            raise ValueError('Explicit classification requires typed answer.')
        if any(value.get(field)!=[] for field in ('assumptions','limitations','next_actions','recommendations','metrics','evidence')):
            raise ValueError('Invalid classified auxiliary fields.')
    if required_classification(quantities) and value.get('status') in ('ok','partial') and not classified:
        raise ValueError('Explicit classification requires typed answer.')
    if classified:
        if value.get('evidence')!=[]:raise ValueError('Classified evidence is server-owned.')
        for field in ('next_actions','recommendations','metrics'):
            if value.get(field)!=[]:raise ValueError('Invalid classified auxiliary fields.')
        for field in ('assumptions','limitations'):
            items=value.get(field)
            if not isinstance(items,list) or any(item not in [[{'text':note}] for note in (BOOLEAN_NOTES if boolean else CLASSIFIED_NOTES)] for item in items):
                raise ValueError('Invalid classified auxiliary fields.')
    result={**value,'answer':render_classified_answer(value['answer'],expressions) if isinstance(value['answer'],dict) else render_segments(value['answer'],records,expressions=expressions)}
    for field in ('assumptions','limitations','next_actions'):
        if field not in value or not isinstance(value[field],list) or len(value[field])>10:
            raise ValueError('Invalid calculation collection.')
        for item in value[field]:
            if (not isinstance(item,list) or len(item)!=1 or
                    not isinstance(item[0],dict) or set(item[0])!={'text'}):
                raise ValueError('Invalid short prose item.')
        result[field]=[render_segments(item,[],limit=500,expressions=None if classified else expressions) for item in value[field]]
    result.pop('basis',None)
    if not classified:
        result['answer']=response_prefix(basis)+result['answer']
        if len(result['answer'])>4000:raise ValueError('Rendered text limit.')
        if basis in BASIS_STATUSES and expressions is not None:
            used=expressions.documentary_operand_sources if basis in DOCUMENTARY_BASES else expressions.documentary_sources
            if used:raise ValueError('Response basis contains documentary operands.')
    if expressions is not None:
        for recommendation in value.get('recommendations',[]):
            if isinstance(recommendation,dict):
                for field in ('action','rationale'):
                    if isinstance(recommendation.get(field),str):expressions.check_prose(recommendation[field])
    if classified:
        known={record['id']:record for record in getattr(quantities,'rule_sources',())}
        if boolean and not expressions.documentary_sources:
            if value.get('status')!='insufficient_data':raise ValueError('User rule status requires no financial authority.')
            return result
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
        # Recommendation selections will be individually authenticated by the
        # assembler before projection. Their IDs alone never confer authority.
        for recommendation in value.get('recommendations',[]):
            if isinstance(recommendation,dict) and isinstance(recommendation.get('evidence'),list):
                cited.update(item.get('id') for item in recommendation['evidence'] if isinstance(item,dict) and item.get('kind')=='corpus')
        if not expressions.documentary_sources<=cited:
            raise ValueError('Documentary calculation citation missing.')
    return result
