"""Arithmetic coverage for explicitly adjacent hypothetical forecast/budget fields.

This is not a forecast generator or a natural-language financial fact extractor.
Ambiguous roles, periods interposed between fields, mixed currencies and server
financial evidence keep the general response path unchanged.
"""
import hashlib
import re
import json
from decimal import Decimal, localcontext


def required_budget_variance(catalog):
    """Bind only a complete, explicitly labelled hypothetical actual/budget pair."""
    from app.core.chat_rules import normalized
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2 or not re.fullmatch(
            r'¿?(?:en cuanto superamos el presupuesto(?: de [a-z]+)?'
            r'|calcula (?:la )?desviacion (?:del|de) presupuesto'
            r'|cual es la desviacion (?:del|de) presupuesto)[?.]?', normalized(parts[0])):
        return None
    if any(source.get('kind') != 'corpus' for source in getattr(catalog, 'authorized_sources', ())):
        return None
    number = r'[0-9]{1,12}(?:[.,][0-9]{1,12})?'
    currency = r'(?:EUR|USD|GBP|CHF|CAD|AUD|JPY)'
    field = rf'(?P<role>coste actual(?: final)?|budget|presupuesto) (?P<amount>{number}) (?P<currency>{currency})'
    declaration = re.fullmatch(
        r'(?:Contexto del escenario:\s*)?Escenario sint[eé]tico'
        r'(?: (?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        r' [12][0-9]{3} [a-zA-Z0-9][a-zA-Z0-9-]{0,63})?: (?P<fields>[^\n]+)[.] '
        r'Variaci[oó]n definida como coste menos presupuesto; porcentaje sobre presupuesto[.]?', parts[1])
    if declaration is None:
        return None
    fields = re.split(r' y |; ', declaration['fields'])
    if len(fields) != 2:
        return None
    amounts, units, spans = {}, set(), {}
    for raw in fields:
        match = re.fullmatch(field, raw, re.I)
        if match is None:
            return None
        role = 'actual' if normalized(match['role']).startswith('coste actual') else 'budget'
        amount = Decimal(match['amount'].replace(',', '.'))
        if role in amounts or amount > Decimal('1e12'):
            return None
        amounts[role] = amount; units.add(match['currency'].upper()); spans[role] = raw
    if set(amounts) != {'actual', 'budget'} or len(units) != 1:
        return None
    with localcontext() as precision:
        precision.prec = 40
        delta = amounts['actual'] - amounts['budget']
        relative = delta / amounts['budget'] * 100 if amounts['budget'] else None
    payload = {'question': question, 'source_spans': spans}
    identity = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {'id': identity, 'amounts': amounts, 'currency': units.pop(), 'difference': delta, 'relative': relative}


def budget_variance_answer(value, catalog):
    bound = required_budget_variance(catalog)
    if bound is None or value != {'budget_variance': bound['id']}:
        raise ValueError('Budget variance is not grounded.')
    from app.core.chat_expressions import display
    a, b, d = (display(bound['amounts']['actual']), display(bound['amounts']['budget']), display(bound['difference']))
    unit = bound['currency']
    relation = ('exceso positivo sobre el presupuesto' if bound['difference'] > 0 else
                'gasto inferior al presupuesto' if bound['difference'] < 0 else 'gasto igual al presupuesto')
    answer = ('Escenario hipotético aportado; no verificado financieramente.\n'
              f'Coste actual final: {a} {unit}. Presupuesto: {b} {unit}.\n'
              f'Desviación (coste menos presupuesto): {a} − {b} = {d} {unit}; {relation}.\n')
    if bound['relative'] is None:
        answer += 'Porcentaje indefinido: el presupuesto es cero; no se inventa una desviación relativa.\n'
    else:
        from fractions import Fraction
        with localcontext() as precision:
            precision.prec = 80
            shown = display(bound['relative'])
        equality = '=' if Fraction(Decimal(shown))*Fraction(bound['amounts']['budget']) == Fraction(bound['difference'])*100 else '≈'
        answer += f'Desviación relativa sobre presupuesto: ({d} / {b}) × 100 {equality} {shown} %.\n'
    return answer + 'Se compara el coste actual final declarado, no un forecast ni una causa probada.'

FIELD = re.compile(
    r'\b(?P<role>forecast(?: al cierre)?|budget(?: mensual)?|presupuesto(?: mensual)?)'
    r'[ \t]*[:=]?[ \t]*(?P<value>[+-]?[0-9]{1,15}(?:[.,][0-9]{1,12})?)'
    r'[ \t]+(?P<currency>EUR|USD|GBP|CHF|CAD|AUD|JPY)\b', re.I)


def explicit_comparison(catalog):
    question = getattr(catalog, 'classification_question', '')
    request = question.split('\n\n', 1)[0]
    if not re.search(r'\b(?:budget|presupuesto)\b', request, re.I):
        return None
    if any(s.get('kind') != 'corpus' for s in getattr(catalog, 'authorized_sources', ())):
        return None
    fields = list(FIELD.finditer(question))
    if len(fields) != 2 or not re.fullmatch(r'\s*;\s*', question[fields[0].end():fields[1].start()]):
        return None
    after = question[fields[1].end():]
    if after and not re.match(r'\s*(?:[.;?\n]|$)', after):
        return None  # Do not discard a time unit or a different scope qualifier.
    # Match whole explicit fields, never a label embedded in a negation or an
    # explanatory sentence. No dates/scopes may occur between the two operands.
    before = question[:fields[0].start()].rstrip(' \t')
    if before and before[-1] not in ';:\n':
        return None
    roles = {}
    for field in fields:
        role = 'forecast' if field['role'].lower().startswith('forecast') else 'budget'
        if role in roles:
            return None
        roles[role] = field
    if set(roles) != {'forecast', 'budget'}:
        return None
    forecast, budget = roles['forecast'], roles['budget']
    if forecast['currency'].upper() != budget['currency'].upper():
        return None
    f, b = (Decimal(v['value'].replace(',', '.')) for v in (forecast, budget))
    if b <= 0 or any(abs(v) > Decimal('1e12') for v in (f, b)):
        return None
    with localcontext() as precision:
        precision.prec = 40
        difference, relative = f - b, (f - b) / b * 100
    if abs(relative) > Decimal('1e18'):
        return None
    return {'forecast': f, 'budget': b, 'difference': difference, 'relative': relative,
            'currency': forecast['currency'].upper(),
            'source_spans': [v.group() for v in (forecast, budget)],
            'question_sha256': hashlib.sha256(question.encode()).hexdigest()}


def comparison_text(catalog):
    bound = explicit_comparison(catalog)
    if bound is None:
        return ''
    def shown(value):
        result = format(value, 'f')
        return result.rstrip('0').rstrip('.') if '.' in result else result
    f, b, d, r = (shown(bound[key]) for key in ('forecast', 'budget', 'difference', 'relative'))
    unit = bound['currency']
    return (f'Comparación aritmética hipotética de los datos aportados: forecast {f} {unit}; '
            f'presupuesto {b} {unit}. Desviación (forecast menos presupuesto): {d} {unit}; '
            f'desviación relativa respecto al presupuesto: {r} %. '
            'El forecast es una proyección, no gasto realizado ni un resultado garantizado.\n')
