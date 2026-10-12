"""Bounded hypothetical arithmetic. Never executes code or grants billing authority.

The model chooses semantics/units; source literals and dimensional compatibility
are checked here. Decimal evaluates the selected operations. Semantic relevance
of that selection and surrounding prose still require acceptance evaluation.
Keep the processor copy byte-identical (separate service images).
"""
import json
import re
from decimal import Decimal, DecimalException, localcontext

OPERATORS = ('add','subtract','multiply','divide','percentage','gt','gte','lt','lte','eq')
OPERAND = r'^(?:-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,12})?|@[0-9]{1,2})$'
PLAN_SCHEMA = {'type':'array','maxItems':12,'items':{'type':'object','properties':{
    'left':{'type':'string','pattern':OPERAND,'maxLength':26},
    'right':{'type':'string','pattern':OPERAND,'maxLength':26},
    'left_unit':{'type':'string','maxLength':32},
    'right_unit':{'type':'string','maxLength':32},
    'operator':{'type':'string','enum':list(OPERATORS)}},
    'required':['left','right','left_unit','right_unit','operator'],'additionalProperties':False}}
FIELDS={'left','right','left_unit','right_unit','operator'}
MONETARY_UNITS={'EUR','USD','GBP','JPY','CHF','CAD','AUD','CNY','INR','€','$','£','¥'}


def quotient_unit(left, right):
    if left==right: return ''
    if not right: return left
    # A dimensioned ratio is not an exchange-rate authorization. Currency
    # conversion is deliberately absent; retain ordinary cost/count dimensions.
    lm={part for part in re.split(r'[/ *]',left.upper()) if part in MONETARY_UNITS}
    rm={part for part in re.split(r'[/ *]',right.upper()) if part in MONETARY_UNITS}
    if lm and rm and lm!=rm: raise ValueError('Currency conversion unsupported.')
    unit=(left or '1')+'/'+right
    if len(unit)>32: raise ValueError('Calculation derived unit limit.')
    return unit


def validate_plan(plan):
    if not isinstance(plan,list) or len(plan)>12: raise ValueError('Calculation plan limit.')
    for index, step in enumerate(plan):
        if not isinstance(step,dict) or set(step)!=FIELDS or step['operator'] not in OPERATORS:
            raise ValueError('Calculation step shape.')
        for side in ('left','right'):
            value=step[side];unit=step[side+'_unit']
            if not isinstance(value,str) or re.fullmatch(OPERAND,value) is None:
                raise ValueError('Calculation operand.')
            if value.startswith('@') and int(value[1:])>=index: raise ValueError('Calculation forward reference.')
            if (not isinstance(unit,str) or len(unit)>32 or unit!=unit.strip()
                    or any(ord(char)<32 for char in unit)):
                raise ValueError('Calculation unit.')
    return plan


def question_text(context):
    for message in reversed(context['messages']):
        text=message.get('content','')
        if text.startswith('UNTRUSTED_CURRENT_CONTEXT\n'):
            value=json.loads(text.split('\n',1)[1]).get('question')
            if isinstance(value,str): return value
    raise ValueError('Calculation input unavailable.')


def _literals(text):
    # Decimal comma is accepted. Ambiguous grouped numbers are not silently
    # interpreted as thousands, nor are numeric fragments taken from identifiers.
    found=re.findall(r'(?<![\w.,])[-−]?[0-9]+(?:[.,][0-9]+)?(?![\w.,])',text)
    return {Decimal(item.replace('−','-').replace(',','.')) for item in found}


def _display(value):
    rounded=value.quantize(Decimal('0.000001'))
    raw=format(rounded,'f').rstrip('0').rstrip('.') if '.' in format(rounded,'f') else format(rounded,'f')
    return '0' if raw in ('','-0') else raw


def calculate(context, plan):
    validate_plan(plan)
    if not plan: return []
    question=question_text(context)
    literals=_literals(question)
    records=[];values=[]
    def operand(step,side):
        raw=step[side];unit=step[side+'_unit']
        if raw.startswith('@'):
            index=int(raw[1:])
            value,expected=values[index]
            if isinstance(value,bool) or expected!=unit: raise ValueError('Calculation reference unit.')
        else:
            value=Decimal(raw)
            if value not in literals: raise ValueError('Calculation literal absent from question.')
            if unit and unit.casefold() not in question.casefold(): raise ValueError('Calculation unit absent from question.')
        return value,unit
    try:
        with localcontext() as precision:
            precision.prec=40
            for index,step in enumerate(plan):
                left,lu=operand(step,'left');right,ru=operand(step,'right');op=step['operator']
                if op in ('add','subtract','percentage','gt','gte','lt','lte','eq') and lu!=ru:
                    raise ValueError('Incompatible calculation units.')
                if op=='add': value=left+right;unit=lu;symbol='+'
                elif op=='subtract': value=left-right;unit=lu;symbol='−'
                elif op=='multiply':
                    if lu and ru: raise ValueError('Dimensioned multiplication unsupported.')
                    value=left*right;unit=lu or ru;symbol='×'
                elif op in ('divide','percentage'):
                    if right==0: raise ValueError('Calculation denominator zero.')
                    value=left/right*(100 if op=='percentage' else 1)
                    unit='%' if op=='percentage' else quotient_unit(lu,ru);symbol='/'
                else:
                    value={'gt':left>right,'gte':left>=right,'lt':left<right,'lte':left<=right,'eq':left==right}[op]
                    unit='';symbol={'gt':'>','gte':'>=','lt':'<','lte':'<=','eq':'=='}[op]
                if not isinstance(value,bool) and (not value.is_finite() or abs(value)>Decimal('1e18')):
                    raise ValueError('Calculation magnitude limit.')
                values.append((value,unit))
                shown='verdadero' if value is True else 'falso' if value is False else _display(value)
                # Never round the operands: doing so could turn a correct
                # calculation into a visibly false displayed expression.
                def term(number,dimension):
                    raw=format(number,'f')
                    if '.' in raw: raw=raw.rstrip('0').rstrip('.')
                    return raw+((' '+dimension) if dimension else '')
                lhs=term(left,lu)+' '+symbol+' '+term(right,ru)
                if op=='percentage': lhs='('+lhs+') × 100'
                relation='=' if isinstance(value,bool) or Decimal(shown)==value else '≈'
                equation=lhs+' '+relation+' '+shown+((' '+unit) if unit else '')
                records.append({'id':str(index),'value':shown,'unit':unit,'equation':equation,'hypothetical':True})
    except DecimalException as failure:
        raise ValueError('Calculation precision limit.') from failure
    return records


_NUMBER=r'-?[0-9]+(?:[.,][0-9]+)?'
_UNIT=r'(?:\s*[A-Za-zÀ-ÿ€$%][A-Za-zÀ-ÿ€$%/ ]{0,31})?'
_FREE_EQUATION=re.compile(_NUMBER+_UNIT+r'\s*(?:[+×*/xX÷]|-(?!>)|>=?|<=?|==)\s*'+
    _NUMBER+_UNIT+r'[^\n]{0,64}?(?:=|≈|→|->)\s*(?:'+_NUMBER+r'|verdadero|falso|true|false)',re.IGNORECASE)


def render_text(text, records):
    if not isinstance(text,str): raise ValueError('Calculation text type.')
    normalized=text.replace('−','-').replace('**','').replace('__','').replace('`','')
    if _FREE_EQUATION.search(normalized): raise ValueError('Free numeric equation forbidden.')
    def replace(match):
        identifier=match.group(1)
        if not identifier.isdecimal() or int(identifier)>=len(records): raise ValueError('Unknown calculation slot.')
        return records[int(identifier)]['equation']
    result=re.sub(r'\[\[calc:([^\]]*)\]\]',replace,text)
    if '[[calc:' in result: raise ValueError('Incomplete calculation slot.')
    return result


class CalculationStream:
    """Hold private slots across arbitrary token/UTF-8 boundaries, never leak them.

    Buffer each sentence until it can be checked for free numeric equations;
    validated sentences still stream before the provider finishes its JSON.
    """
    def __init__(self, records):
        self.records=records;self.pending=''

    def feed(self, text, final=False):
        self.pending+=text
        if len(self.pending)>16384: raise ValueError('Calculation stream limit.')
        if final:
            result=render_text(self.pending,self.records);self.pending='';return result
        # Decimal points and punctuation inside a slot cannot terminate a unit.
        boundaries=list(re.finditer(r'[.!?;\n]\s',self.pending))
        end=0
        for boundary in boundaries:
            candidate=self.pending[:boundary.end()]
            if candidate.count('[[calc:')==candidate.count(']]'): end=boundary.end()
        if not end:return ''
        complete,self.pending=self.pending[:end],self.pending[end:]
        return render_text(complete,self.records)
