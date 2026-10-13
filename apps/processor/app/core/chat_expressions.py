"""Bounded, source-grounded hypothetical expressions, never billing authority.

Quantities bind value and observed unit together. Expressions are evaluated at
the point where they are rendered, with no generated result IDs or executable
code. Keep this module byte-identical in backend and processor.
"""
import copy
import json
import re
from decimal import Decimal, DecimalException, localcontext
from app.core.chat_rules import QuantityCatalog, documentary_rules, concept, numerator_matches, check_classification_prose, classification_request

MAX_OPERATIONS = 12
MAX_DEPTH = 4
MAX_QUANTITIES = 128
CARDINALS = dict(zip(
    ('cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte').split(),range(21)))
CARDINALS.update(dict(zip(('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty').split(),range(21))))


def context_question(context):
    for message in context.get('messages',[]):
        content=message.get('content','')
        if content.startswith('UNTRUSTED_CURRENT_CONTEXT\n'):
            value=json.loads(content.split('\n',1)[1]).get('question')
            if isinstance(value,str) and value.strip():return value
    raise ValueError('Expression input unavailable.')


def context_quantities(context):
    if not any(message.get('content','').startswith('UNTRUSTED_CURRENT_CONTEXT\n') for message in context.get('messages',[])):
        return {}
    catalog=QuantityCatalog(quantities(context_question(context)))
    rule_sources=[]
    for entry in catalog.values():
        entry['provenance']=[{'kind':'user','source':entry['source']}]
    authorized={item['id']:item for item in context.get('authorized_evidence',[]) if item.get('kind')=='corpus'}
    for message in context.get('messages',[]):
        content=message.get('content','')
        if not content.startswith('UNTRUSTED_RETRIEVAL_CONTEXT\n'):continue
        for source in json.loads(content.split('\n',1)[1]).get('evidence',[]):
            if source.get('kind')!='corpus' or authorized.get(source.get('id'))!=source:
                raise ValueError('Documentary quantity source not authorized.')
            rule_sources.append(source)
            for key,entry in quantities(source['content'],explicit_only=True).items():
                provenance={'kind':'corpus','id':source['id'],'source':entry['source']}
                # Numeric equality is not provenance equality: user operands and
                # documentary rules remain distinct, even at the same value.
                qualified='document:'+source['id']+':'+key
                if qualified in catalog:
                    if provenance not in catalog[qualified]['provenance']:
                        catalog[qualified]['provenance'].append(provenance)
                elif len(catalog)<MAX_QUANTITIES:
                    catalog[qualified]={**entry,'display':key,'provenance':[provenance]}
    catalog.classification_requested=classification_request(context_question(context))
    catalog.rules=documentary_rules(rule_sources)
    catalog.rule_sources=rule_sources
    return catalog
NUMERIC = r'(?<![\w.,-])[-−]?[0-9]+(?:[.,][0-9]+)?(?![\w-]|[.,][0-9])'
CURRENCIES = ('EUR','USD','GBP','JPY','CHF','CAD','AUD','CNY','INR','€','$','£','¥')
# A closed dimensional vocabulary, not arbitrary words from the question.
COUNTS = ('recursos','recurso','resources','resource','pedidos','pedido','orders','order',
          'operaciones','operacion','operación','operations','operation',
          'transacciones','transaccion','transacción','transactions','transaction',
          'usuarios','usuario','users','user','unidades','unidad','units','unit')
MEASURES = ('GB','GiB','TB','TiB','MB','MiB','CPU','vCPU','horas','hora','hours','hour',
            'días','día','dias','dia','days','day','meses','mes','months','month')
UNIT_PATTERN = r'(?:'+ '|'.join(re.escape(x) for x in sorted(CURRENCIES+COUNTS+MEASURES+('%',),key=len,reverse=True))+r')(?:/(?:día|dia|day|hora|hour|mes|month))?'
UNIT_RE = re.compile(UNIT_PATTERN+r'(?![\w/])',re.IGNORECASE)
COUNT_RE = re.compile(r'\b(?:'+'|'.join(re.escape(x) for x in COUNTS)+r')\b',re.IGNORECASE)
DATE_RE = re.compile(r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|año|year|periodo|período)\b',re.IGNORECASE)


def normalized_unit(unit):
    aliases={
        **dict.fromkeys(('recursos','recurso','resources','resource'),'recurso'),
        **dict.fromkeys(('pedidos','pedido','orders','order'),'pedido'),
        **dict.fromkeys(('operaciones','operacion','operación','operations','operation'),'operación'),
        **dict.fromkeys(('transacciones','transaccion','transacción','transactions','transaction'),'transacción'),
        **dict.fromkeys(('usuarios','usuario','users','user'),'usuario'),
        **dict.fromkeys(('unidades','unidad','units','unit'),'unidad'),
        **dict.fromkeys(('horas','hora','hours','hour'),'hora'),
        **dict.fromkeys(('días','día','dias','dia','days','day'),'día'),
        **dict.fromkeys(('meses','mes','months','month'),'mes')}
    return '/'.join('EUR' if part=='€' else part.upper() if part.upper() in CURRENCIES else aliases.get(part.casefold(),part)
                    for part in unit.split('/'))


def canonical_decimal(value):
    value=Decimal(value.replace('−','-').replace(',','.'))
    if not value.is_finite() or abs(value)>Decimal('1e12'):
        raise ValueError('Expression source magnitude.')
    raw=format(value,'f')
    if '.' in raw:raw=raw.rstrip('0').rstrip('.')
    return '0' if raw in ('','-0') else raw


def quantities(question, *, explicit_only=False):
    """Return deterministic indivisible options with their original source span.

    A unique currency may scope bare monetary entries, but never dates, count
    clauses or explicit percent/threshold clauses. Ambiguity is retained as
    dimensionless; no model-supplied unit is accepted later.
    """
    if not isinstance(question,str):raise ValueError('Expression input type.')
    currency_hits={normalized_unit(m.group()) for m in re.finditer(
        r'(?<!\w)(?:'+'|'.join(re.escape(x) for x in CURRENCIES)+r')(?!\w)',question,re.IGNORECASE)}
    result={}
    numeric_or_word=NUMERIC+r'|\b(?:'+'|'.join(CARDINALS)+r')\b'
    for match in re.finditer(numeric_or_word,question,re.IGNORECASE):
        raw=match.group();before=question[:match.start()];after=question[match.end():]
        word=raw.casefold() in CARDINALS
        try:value=canonical_decimal(str(CARDINALS[raw.casefold()]) if word else raw)
        except (ValueError,DecimalException):continue
        if len(value)>26 or ('.' in value and len(value.split('.')[1])>12):continue
        suffix=re.match(r'\s*('+UNIT_PATTERN+r')(?![\w/])',after,re.IGNORECASE)
        prefix=re.search(r'(?<!\w)('+UNIT_PATTERN+r')\s*[:=]?\s*$',before,re.IGNORECASE)
        unit='';kind='bare';span=raw
        if suffix:
            unit=suffix.group(1);kind='adjacent';span=raw+suffix.group()
        elif prefix:
            unit=prefix.group(1);kind='adjacent';span=prefix.group()+raw
        else:
            # Scope exclusions use the local entry, not an arbitrary distant
            # currency. A count near a bare number cannot become money.
            clause=re.split(r'[;\n]',before)[-1][-80:]+raw+re.split(r'[;\n]',after)[0][:80]
            date=((len(raw)==4 and raw.isdecimal() and 1900<=int(raw)<=2200 and DATE_RE.search(clause))
                  or re.search(r'\b(?:fecha|date|día|dia|day)\s*$',before,re.IGNORECASE)
                  or re.match(r'\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b',after,re.IGNORECASE))
            count=COUNT_RE.search(clause)
            threshold=re.search(r'%|porcent|umbral|threshold',clause,re.IGNORECASE)
            monetary=r'\b(?:costes?|costos?|gastos?|costs?|spend|budget|presupuesto|forecast|allocated|shared|unallocated|excluded)\b'
            local_before=re.split(r'[;\n.!?]',before)[-1][-80:]
            sentence=re.split(r'[.!?\n]',before)[-1]
            heading=sentence.rsplit(':',1)[0] if ':' in sentence else ''
            monetary_scope=(re.search(monetary+r'\s*(?:actual|mensual|diario|total|de\s+\w+)?\s*[:=]?\s*$',local_before,re.IGNORECASE)
                            or (heading and re.search(monetary,heading,re.IGNORECASE)
                                and not re.search(r'[.\n]',sentence.rsplit(':',1)[1])))
            if len(currency_hits)==1 and monetary_scope and not (date or count or threshold):
                unit=next(iter(currency_hits));kind='context_currency'
            # Written cardinals in an explicitly counted population may refer
            # back to its unique dimension (e.g. ten users; nine comply).
            # Ordinals denote positions, so they are deliberately not counts.
            if word and not unit:
                paragraph=before.rsplit('\n',1)[-1]
                population_text=' '.join(re.split(r'[.!?]',paragraph)[-2:])
                population={normalized_unit(m.group()) for m in COUNT_RE.finditer(population_text)}
                if len(population)==1:
                    unit=next(iter(population));kind='context_count'
        if explicit_only and kind!='adjacent':continue
        unit=normalized_unit(unit)
        # Time dimensions scope an entry. Only an explicitly named observed
        # value may inherit the immediately preceding daily baseline's rate;
        # a budget elsewhere in the question is a different quantity.
        entries=re.split(r'[;\n]',before)
        local=entries[-1]
        daily=re.search(r'\b(?:diari[oa]s?|daily|por día|por dia|per day)\b',local,re.IGNORECASE)
        if not daily and len(entries)>1 and re.search(r'\b(?:observad[oa]|observed|actual)\b',local,re.IGNORECASE):
            prior=entries[-2]
            if re.search(r'\b(?:baseline|base)\b',prior,re.IGNORECASE):
                daily=re.search(r'\b(?:diari[oa]s?|daily|por día|por dia|per day)\b',prior,re.IGNORECASE)
        mixed=re.search(r'\b(?:total|mensual|monthly|horari[oa]|hourly|semanal|weekly)\b',local,re.IGNORECASE)
        if not explicit_only and unit in CURRENCIES and daily and not mixed:
            unit+='/día';kind='context_daily_rate'
        key=value+(' '+unit if unit else '')
        entry=result.setdefault(key,{'value':value,'unit':unit,'source':span,'binding':kind})
        if not explicit_only:
            left=before[:prefix.start()] if prefix else before
            right=after[suffix.end():] if suffix else after
            anchors=[]
            left_match=re.search(r'(?:^|[;:\n])\s*([A-Za-zÁÉÍÓÚáéíóúÑñ_][A-Za-zÁÉÍÓÚáéíóúÑñ_ -]{0,50})\s*[:=]?\s*$',left)
            right_match=re.match(r'\s+([A-Za-zÁÉÍÓÚáéíóúÑñ_][A-Za-zÁÉÍÓÚáéíóúÑñ_ -]{0,50})\s*(?=;|[.!?](?:\s|$)|$)',right)
            for match_anchor in (left_match,right_match):
                if match_anchor and concept(match_anchor.group(1)):
                    anchors.append(list(concept(match_anchor.group(1))))
            existing=entry.setdefault('concept_anchors',[])
            for anchor in anchors:
                if anchor not in existing:existing.append(anchor)
        if len(result)>MAX_QUANTITIES:return {}
    return result


def expression_definitions(catalog):
    """Finite DAG of schema definitions: no duplicated recursive intersections."""
    leaf={'type':'object','properties':{'quantity':{'type':'string','enum':list(catalog)}},
          'required':['quantity'],'additionalProperties':False}
    definitions={'SourceQuantity':leaf}
    for depth in range(MAX_DEPTH+1):
        alternatives=[{'$ref':'#/$defs/SourceQuantity'}]
        if depth:
            ref={'$ref':f'#/$defs/NumericExpression{depth-1}'}
            for operator,names in (
                ('sum',('left','right')),('difference',('current','baseline')),
                ('ratio',('numerator','denominator')),('percentage',('numerator','denominator')),
                ('relative_change',('current','baseline'))):
                properties={'operation':{'type':'string','const':operator},**{name:ref for name in names}}
                alternatives.append({'type':'object','properties':properties,
                    'required':list(properties),'additionalProperties':False})
        definitions[f'NumericExpression{depth}']=alternatives[0] if len(alternatives)==1 else {'anyOf':alternatives}
    ref={'$ref':f'#/$defs/NumericExpression{MAX_DEPTH-1}'}
    comparison={'type':'object','properties':{'operation':{'type':'string','const':'compare'},
        'left':ref,'right':ref,'relation':{'type':'string','enum':['gt','gte','lt','lte','eq']}},
        'required':['operation','left','right','relation'],'additionalProperties':False}
    # A displayed calculation must actually calculate. Source quantities are
    # operands, not degenerate answers that can substitute a threshold for a
    # computed variation while satisfying the structured schema.
    numeric=definitions[f'NumericExpression{MAX_DEPTH}']['anyOf'][1:]
    definitions['NumericRenderedExpression']={'anyOf':numeric}
    alternatives=[*numeric,comparison]
    classifications=[]
    rules=getattr(catalog,'rules',())
    for rule in rules:
        eligible=[key for key,entry in catalog.items() if len(entry.get('concept_anchors',[]))==1
                  and tuple(entry['concept_anchors'][0])==tuple(rule['anchor'])]
        if not eligible:continue
        numerator={'type':'object','properties':{'quantity':{'type':'string','enum':eligible}},
                   'required':['quantity'],'additionalProperties':False}
        value={'type':'object','properties':{'operation':{'type':'string','const':'percentage'},
            'numerator':numerator,'denominator':{'$ref':f'#/$defs/NumericExpression{MAX_DEPTH-2}'}},
            'required':['operation','numerator','denominator'],'additionalProperties':False}
        classifications.append({'type':'object','properties':{
            'operation':{'type':'string','const':'classify'},
            'rule_id':{'type':'string','const':rule['id'],'description':json.dumps(rule,ensure_ascii=False)},
            'value':value},'required':['operation','rule_id','value'],'additionalProperties':False})
    definitions['RenderedExpression']={'anyOf':alternatives}
    if classifications:
        definitions['DocumentaryClassification']=classifications[0] if len(classifications)==1 else {'anyOf':classifications}
    return definitions


def display(value):
    text=format(value.quantize(Decimal('0.000001')),'f').rstrip('0').rstrip('.')
    return '0' if text in ('','-0') else text


class ExpressionRenderer:
    def __init__(self,catalog):
        self.catalog=copy.deepcopy(catalog)
        self.operations=0
        self.documentary_sources=set()

    def check_prose(self,text):
        self.documentary_sources.update(check_classification_prose(text,
            getattr(self.catalog,'rules',()),getattr(self.catalog,'rule_sources',())))

    def _classify(self,node):
        if set(node)!={'operation','rule_id','value'}:raise ValueError('Classification shape.')
        rules=[rule for rule in getattr(self.catalog,'rules',()) if rule['id']==node['rule_id']]
        if len(rules)!=1:raise ValueError('Unknown documentary interval rule.')
        rule=rules[0]
        if not numerator_matches(node['value'],self.catalog,rule):
            raise ValueError('Documentary KPI value mismatch.')
        value,unit,formula,reason=self._numeric(node['value'],1)
        self.documentary_sources.update(rule['source_ids'])
        if reason:return '\nClasificación no definida: '+reason+'.\n'
        if unit!=rule['unit']:raise ValueError('Documentary interval unit mismatch.')
        matches=[]
        for interval in rule['intervals']:
            valid=True
            for bound in interval['bounds']:
                self._count()
                limit=Decimal(bound['value'])
                valid=valid and ((value>=limit if bound['inclusive'] else value>limit) if bound['side']=='lower' else (value<=limit if bound['inclusive'] else value<limit))
            if valid:matches.append(interval)
        if len(matches)!=1:raise ValueError('Ambiguous documentary interval.')
        interval=matches[0]
        exact=format(value,'f')
        if '.' in exact:exact=exact.rstrip('0').rstrip('.')
        conditions=[]
        for bound in interval['bounds']:
            symbol=('>=' if bound['inclusive'] else '>') if bound['side']=='lower' else ('<=' if bound['inclusive'] else '<')
            conditions.append(exact+' '+unit+' '+symbol+' '+bound['value']+' '+unit)
        shown=display(value);equality='=' if Decimal(shown)==value else '≈'
        return '\nClasificación según la regla ('+rule['metric']+'; '+rule['section']+'): '+interval['label']+'. '+formula+' '+equality+' '+shown+' '+unit+'. Intervalo: '+' y '.join(conditions)+'.\n'

    def _count(self):
        self.operations+=1
        if self.operations>MAX_OPERATIONS:raise ValueError('Expression operation limit.')

    def _numeric(self,node,depth=0):
        if not isinstance(node,dict) or depth>MAX_DEPTH:raise ValueError('Expression shape or depth.')
        if set(node)=={'quantity'}:
            key=node['quantity']
            if not isinstance(key,str) or key not in self.catalog:raise ValueError('Unknown source quantity.')
            entry=self.catalog[key]
            self.documentary_sources.update(origin['id'] for origin in entry.get('provenance',[]) if origin['kind']=='corpus')
            return Decimal(entry['value']),entry['unit'],entry.get('display',key),None
        operator=node.get('operation')
        if not isinstance(operator,str):raise ValueError('Expression operation shape.')
        names={'sum':('left','right'),'difference':('current','baseline'),
               'ratio':('numerator','denominator'),'percentage':('numerator','denominator'),
               'relative_change':('current','baseline')}.get(operator)
        if names is None or set(node)!={'operation',*names}:raise ValueError('Expression operation shape.')
        self._count()
        a,au,at,ae=self._numeric(node[names[0]],depth+1)
        b,bu,bt,be=self._numeric(node[names[1]],depth+1)
        if ae or be:return None,'',f'({at}; {bt})',ae or be
        if operator in ('sum','difference','percentage','relative_change') and au!=bu:
            # Only well-grounded distinct currencies have a meaningful domain
            # result; arbitrary incompatible dimensions remain invalid output.
            if operator in ('sum','difference') and au.upper() in CURRENCIES and bu.upper() in CURRENCIES:
                return None,'',f'{at} y {bt}','no agregable sin una conversión de divisa autorizada'
            raise ValueError('Incompatible expression units.')
        if operator=='sum':value=a+b;unit=au;formula=f'({at} + {bt})'
        elif operator=='difference':value=a-b;unit=au;formula=f'({at} − {bt})'
        elif operator=='relative_change':
            formula=f'(({at} − {bt}) / {bt}) × 100'
            if b==0:return None,'%',formula,'variación relativa indefinida porque la base es cero'
            value=(a-b)/b*100;unit='%'
        else:
            formula=f'({at} / {bt})'+(' × 100' if operator=='percentage' else '')
            if b==0:return None,'',formula,'cociente indefinido porque el denominador es cero'
            if operator=='percentage':value=a/b*100;unit='%'
            else:
                ac={part.upper() for part in au.split('/') if part.upper() in CURRENCIES}
                bc={part.upper() for part in bu.split('/') if part.upper() in CURRENCIES}
                if ac and bc and ac!=bc:
                    return None,'',formula,'conversión entre divisas no autorizada'
                value=a/b;unit='' if au==bu else au if not bu else (au or '1')+'/'+bu
        if not value.is_finite() or abs(value)>Decimal('1e18') or len(unit)>32:
            raise ValueError('Expression magnitude or unit limit.')
        return value,unit,formula,None

    def render(self,node):
        if not isinstance(node,dict) or 'operation' not in node:
            raise ValueError('Rendered expression requires an operation.')
        try:
            with localcontext() as precision:
                precision.prec=40
                if node.get('operation')=='classify':return self._classify(node)
                if isinstance(node,dict) and node.get('operation')=='compare':
                    if set(node)!={'operation','left','right','relation'} or node['relation'] not in ('gt','gte','lt','lte','eq'):
                        raise ValueError('Comparison expression shape.')
                    self._count()
                    a,au,at,ae=self._numeric(node['left'],1);b,bu,bt,be=self._numeric(node['right'],1)
                    if ae or be:return '\nComparación no definida: '+(ae or be)+'.\n'
                    if au!=bu:raise ValueError('Incompatible expression units.')
                    relation=node['relation'];symbol={'gt':'>','gte':'>=','lt':'<','lte':'<=','eq':'=='}[relation]
                    valid={'gt':a>b,'gte':a>=b,'lt':a<b,'lte':a<=b,'eq':a==b}[relation]
                    return '\nComparación: '+at+' '+symbol+' '+bt+' → '+('verdadero' if valid else 'falso')+'.\n'
                value,unit,formula,reason=self._numeric(node)
                if reason:return '\n'+formula+': '+reason+'.\n'
                shown=display(value);symbol='=' if Decimal(shown)==value else '≈'
                if node.get('operation')=='difference' and unit=='%':unit='puntos porcentuales'
                return '\nCálculo: '+formula+' '+symbol+' '+shown+(' '+unit if unit else '')+'.\n'
        except DecimalException as error:
            raise ValueError('Expression precision limit.') from error
