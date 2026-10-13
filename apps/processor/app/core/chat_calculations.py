"""Bounded hypothetical arithmetic. Never executes code or grants billing authority.

The model chooses semantics/units; source literals and dimensional compatibility
are checked here. Decimal evaluates the selected operations. Semantic relevance
of that selection and surrounding prose still require acceptance evaluation.
Keep the processor copy byte-identical (separate service images).
"""
import copy
import json
import re
from decimal import Decimal, DecimalException, localcontext



CALCULATION_RULES = {'Currency conversion unsupported.': 'calculation_currency_conversion_unsupported', 'Calculation derived unit limit.': 'calculation_derived_unit_limit', 'Calculation plan limit.': 'calculation_plan_limit', 'Calculation step shape.': 'calculation_step_shape', 'Calculation operand.': 'calculation_operand', 'Calculation forward reference.': 'calculation_forward_reference', 'Calculation unit.': 'calculation_unit', 'Calculation input unavailable.': 'calculation_input_unavailable', 'Calculation reference unit.': 'calculation_reference_unit', 'Calculation literal absent from question.': 'calculation_literal_absent_from_question', 'Calculation unit absent from question.': 'calculation_unit_absent_from_question', 'Incompatible calculation units.': 'calculation_incompatible_calculation_units', 'Dimensioned multiplication unsupported.': 'calculation_dimensioned_multiplication_unsupported', 'Calculation denominator zero.': 'calculation_denominator_zero', 'Calculation magnitude limit.': 'calculation_magnitude_limit', 'Calculation precision limit.': 'calculation_precision_limit', 'Calculation text type.': 'calculation_text_type', 'Free numeric equation forbidden.': 'calculation_free_numeric_equation_forbidden', 'Unknown calculation slot.': 'calculation_unknown_calculation_slot', 'Incomplete calculation slot.': 'calculation_incomplete_calculation_slot', 'Calculation stream limit.': 'calculation_stream_limit'}


class CalculationError(ValueError):
    def __init__(self, message):
        self.rule_code = CALCULATION_RULES.get(message, 'calculation_invalid')
        super().__init__(message)


NUMERIC_OPERATORS = ('add','subtract','multiply','divide','percentage')
COMPARISON_OPERATORS = ('gt','gte','lt','lte','eq')
OPERATORS = NUMERIC_OPERATORS + COMPARISON_OPERATORS
OPERAND = r'^-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,12})?$'
OPERAND_SCHEMA = {'anyOf':[
    {'type':'object','properties':{'literal':{'type':'string','pattern':OPERAND,'maxLength':26},
        'unit':{'type':'string','maxLength':32}},'required':['literal','unit'],'additionalProperties':False},
    {'type':'object','properties':{'ref':{'type':'integer','minimum':0,'maximum':11}},
        'required':['ref'],'additionalProperties':False}]}
PLAN_SCHEMA = {'type':'array','maxItems':12,'items':{'type':'object','properties':{
    'left':OPERAND_SCHEMA,'right':OPERAND_SCHEMA,
    'operator':{'type':'string','enum':list(NUMERIC_OPERATORS)}},
    'required':['left','right','operator'],'additionalProperties':False}}
COMPARISON_SCHEMA = copy.deepcopy(PLAN_SCHEMA)
COMPARISON_SCHEMA['items']['properties']['operator']['enum'] = list(COMPARISON_OPERATORS)
FIELDS={'left','right','operator'}
MONETARY_UNITS={'EUR','USD','GBP','JPY','CHF','CAD','AUD','CNY','INR','€','$','£','¥'}


def quotient_unit(left, right):
    if left==right: return ''
    if not right: return left
    # A dimensioned ratio is not an exchange-rate authorization. Currency
    # conversion is deliberately absent; retain ordinary cost/count dimensions.
    lm={part for part in re.split(r'[/ *]',left.upper()) if part in MONETARY_UNITS}
    rm={part for part in re.split(r'[/ *]',right.upper()) if part in MONETARY_UNITS}
    if lm and rm and lm!=rm: raise CalculationError('Currency conversion unsupported.')
    unit=(left or '1')+'/'+right
    if len(unit)>32: raise CalculationError('Calculation derived unit limit.')
    return unit


def validate_plan(plan, comparisons=None):
    comparisons=[] if comparisons is None else comparisons
    if (not isinstance(plan,list) or not isinstance(comparisons,list)
            or len(plan)+len(comparisons)>12): raise CalculationError('Calculation plan limit.')
    for index, step in enumerate(plan+comparisons):
        numeric=index<len(plan)
        allowed=NUMERIC_OPERATORS if numeric else COMPARISON_OPERATORS
        if not isinstance(step,dict) or set(step)!=FIELDS or step['operator'] not in allowed:
            raise CalculationError('Calculation step shape.')
        for side in ('left','right'):
            operand=step[side]
            if not isinstance(operand,dict): raise CalculationError('Calculation operand.')
            if set(operand)=={'ref'}:
                limit=index if numeric else len(plan)
                if type(operand['ref']) is not int or not 0<=operand['ref']<limit:
                    raise CalculationError('Calculation forward reference.')
            elif set(operand)=={'literal','unit'}:
                value=operand['literal'];unit=operand['unit']
                if not isinstance(value,str) or re.fullmatch(OPERAND,value) is None:
                    raise CalculationError('Calculation operand.')
                if (not isinstance(unit,str) or len(unit)>32 or unit!=unit.strip()
                        or any(ord(char)<32 for char in unit)):
                    raise CalculationError('Calculation unit.')
            else: raise CalculationError('Calculation operand.')
    return plan


def question_text(context):
    for message in reversed(context['messages']):
        text=message.get('content','')
        if text.startswith('UNTRUSTED_CURRENT_CONTEXT\n'):
            value=json.loads(text.split('\n',1)[1]).get('question')
            if isinstance(value,str): return value
    raise CalculationError('Calculation input unavailable.')


def _literals(text):
    # Decimal comma is accepted. Ambiguous grouped numbers are not silently
    # interpreted as thousands, nor are numeric fragments taken from identifiers.
    found=re.findall(r'(?<![\w.,-])[-−]?[0-9]+(?:[.,][0-9]+)?(?![\w-]|[.,][0-9])',text)
    return {Decimal(item.replace('−','-').replace(',','.')) for item in found}



def source_choices(context):
    try: question=question_text(context)
    except CalculationError: return [],['']
    numbers=set()
    for value in _literals(question):
        text=format(value,'f')
        if '.' in text:text=text.rstrip('0').rstrip('.')
        if re.fullmatch(OPERAND,text):numbers.add(text)
    units={''}
    units.update(token for token in re.findall(r'[A-Za-zÀ-ÿ€$£¥%]+(?:/[A-Za-zÀ-ÿ€$£¥%]+)*',question)
                 if len(token)<=32)
    if len(numbers)>128 or len(units)>128:return [],['']
    return sorted(numbers),sorted(units)



def validate_contextual_plan(context, plan, comparisons=None):
    comparisons=[] if comparisons is None else comparisons
    validate_plan(plan,comparisons)
    if not plan and not comparisons:return plan
    numbers,units=source_choices(context)
    if not numbers:raise CalculationError('Calculation literal absent from question.')
    for step in plan+comparisons:
        for operand in (step['left'],step['right']):
            if 'literal' in operand:
                if operand['literal'] not in numbers:raise CalculationError('Calculation literal absent from question.')
                if operand['unit'] not in units:raise CalculationError('Calculation unit absent from question.')
    return plan


def contextual_decision_schema(context, base):
    import copy
    schema=copy.deepcopy(base)
    numbers,units=source_choices(context)
    for field,template in (('calculations',PLAN_SCHEMA),('comparisons',COMPARISON_SCHEMA)):
        plan=copy.deepcopy(template)
        if not numbers:
            plan['maxItems']=0
        else:
            for side in ('left','right'):
                literal=plan['items']['properties'][side]['anyOf'][0]['properties']
                literal['literal']['enum']=numbers
                literal['unit']['enum']=units
        schema['properties'][field]=plan
        for branch in schema.get('anyOf',[]):branch['properties'][field]=copy.deepcopy(plan)
    return schema


def _display(value):
    rounded=value.quantize(Decimal('0.000001'))
    raw=format(rounded,'f').rstrip('0').rstrip('.') if '.' in format(rounded,'f') else format(rounded,'f')
    return '0' if raw in ('','-0') else raw


def calculate(context, plan, comparisons=None):
    comparisons=[] if comparisons is None else comparisons
    validate_contextual_plan(context,plan,comparisons)
    if not plan and not comparisons: return []
    question=question_text(context)
    literals=_literals(question)
    records=[];values=[]
    def operand(step,side):
        operand=step[side]
        if 'ref' in operand:
            value,unit=values[operand['ref']]
            if isinstance(value,bool): raise CalculationError('Calculation reference unit.')
        else:
            value=Decimal(operand['literal']);unit=operand['unit']
            if value not in literals: raise CalculationError('Calculation literal absent from question.')
            if unit and unit.casefold() not in question.casefold(): raise CalculationError('Calculation unit absent from question.')
        return value,unit
    try:
        with localcontext() as precision:
            precision.prec=40
            for index,step in enumerate(plan+comparisons):
                left,lu=operand(step,'left');right,ru=operand(step,'right');op=step['operator']
                if op in ('add','subtract','percentage','gt','gte','lt','lte','eq') and lu!=ru:
                    raise CalculationError('Incompatible calculation units.')
                if op=='add': value=left+right;unit=lu;symbol='+'
                elif op=='subtract': value=left-right;unit=lu;symbol='−'
                elif op=='multiply':
                    if lu and ru: raise CalculationError('Dimensioned multiplication unsupported.')
                    value=left*right;unit=lu or ru;symbol='×'
                elif op in ('divide','percentage'):
                    if right==0: raise CalculationError('Calculation denominator zero.')
                    value=left/right*(100 if op=='percentage' else 1)
                    unit='%' if op=='percentage' else quotient_unit(lu,ru);symbol='/'
                else:
                    value={'gt':left>right,'gte':left>=right,'lt':left<right,'lte':left<=right,'eq':left==right}[op]
                    unit='';symbol={'gt':'>','gte':'>=','lt':'<','lte':'<=','eq':'=='}[op]
                if not isinstance(value,bool) and (not value.is_finite() or abs(value)>Decimal('1e18')):
                    raise CalculationError('Calculation magnitude limit.')
                if index<len(plan):values.append((value,unit))
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
                identifier='n:'+str(index) if index<len(plan) else 'c:'+str(index-len(plan))
                records.append({'id':identifier,'value':shown,'unit':unit,'equation':equation,'hypothetical':True})
    except DecimalException as failure:
        raise CalculationError('Calculation precision limit.') from failure
    return records


_NUMBER=r'-?[0-9]+(?:[.,][0-9]+)?'
_UNIT=r'(?:\s*[A-Za-zÀ-ÿ€$%][A-Za-zÀ-ÿ€$%/ ]{0,31})?'
_FREE_EQUATION=re.compile(_NUMBER+_UNIT+r'\s*(?:[+×*/xX÷]|-(?!>)|>=?|<=?|==)\s*'+
    _NUMBER+_UNIT+r'[^\n]{0,64}?(?:=|≈|→|->)\s*(?:'+_NUMBER+r'|verdadero|falso|true|false)',re.IGNORECASE)


def render_text(text, records):
    if not isinstance(text,str): raise CalculationError('Calculation text type.')
    normalized=text.replace('−','-').replace('**','').replace('__','').replace('`','')
    if _FREE_EQUATION.search(normalized): raise CalculationError('Free numeric equation forbidden.')
    def replace(match):
        identifier=match.group(1)
        if not identifier.isdecimal() or int(identifier)>=len(records): raise CalculationError('Unknown calculation slot.')
        return records[int(identifier)]['equation']
    result=re.sub(r'\[\[calc:([^\]]*)\]\]',replace,text)
    if '[[calc:' in result: raise CalculationError('Incomplete calculation slot.')
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
        if len(self.pending)>16384: raise CalculationError('Calculation stream limit.')
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
