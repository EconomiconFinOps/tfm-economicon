"""Arithmetic coverage for explicitly adjacent hypothetical forecast/budget fields.

This is not a forecast generator or a natural-language financial fact extractor.
Ambiguous roles, periods interposed between fields, mixed currencies and server
financial evidence keep the general response path unchanged.
"""
import hashlib
import re
from decimal import Decimal, localcontext

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
