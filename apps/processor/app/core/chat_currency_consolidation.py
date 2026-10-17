"""Closed hypothetical multi-currency input requiring conversion parameters.

This does not infer a conversion rate or parse arbitrary financial prose. The
whole request and declaration must match; ambiguous or authoritative financial
inputs remain on the ordinary route. No corpus policy is inferred from an
explicit absence of user-supplied conversion data.
"""
import hashlib
import re
from decimal import Decimal, localcontext

from app.core.chat_missing_spend import MONTH
from app.core.chat_rules import normalized


def required_currency_consolidation(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2 or any(source.get('kind') != 'corpus'
                             for source in getattr(catalog, 'authorized_sources', ())):
        return None
    request = re.fullmatch(
        r'¿?(?:puedes )?(?:sumar|consolidar) los costes de las '
        r'(?P<count>dos|tres|cuatro|[2-9]|1[0-9]|20) suscripciones[?.]?', normalized(parts[0]))
    if request is None:
        return None
    scenario = re.fullmatch(
        rf'(?:Contexto del escenario:\s*)?Escenario sint[eé]tico (?P<month>{MONTH}) '
        r'(?P<year>[0-9]{4}): (?P<entries>[^\n]+)\. '
        r'No se suministra tipo de cambio ni fecha de conversi[oó]n[.]?', parts[1], re.I)
    if scenario is None or not 1900 <= int(scenario['year']) <= 2200:
        return None
    count = {'dos': 2, 'tres': 3, 'cuatro': 4}.get(request['count'])
    if count is None:
        count = int(request['count'])
    entries = scenario['entries'].split('; ')
    if len(entries) != count:
        return None
    costs = []
    names = set()
    for entry in entries:
        match = re.fullmatch(
            r'(?P<scope>[A-Za-z0-9][A-Za-z0-9_-]{0,63}) '
            r'(?P<amount>[0-9]{1,12}(?:[.,][0-9]{1,12})?) '
            r'(?P<currency>EUR|USD|GBP|CHF|CAD|AUD|JPY)', entry, re.I)
        if match is None or match['scope'].casefold() in names:
            return None
        amount = Decimal(match['amount'].replace(',', '.'))
        if amount > Decimal('1e12'):
            return None
        names.add(match['scope'].casefold())
        costs.append((match['scope'], amount, match['currency'].upper()))
    if len({unit for _, _, unit in costs}) < 2:
        return None
    return {'id': hashlib.sha256(question.encode()).hexdigest(), 'costs': costs,
            'period': normalized(scenario['month']) + ' de ' + scenario['year']}


def currency_consolidation_answer(value, catalog):
    bound = required_currency_consolidation(catalog)
    if bound is None or value != {'currency_consolidation': bound['id']}:
        raise ValueError('Currency consolidation is not grounded.')

    def exact(amount):
        text = format(amount, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text

    totals = {}
    with localcontext() as precision:
        precision.prec = 80
        for _, amount, unit in bound['costs']:
            totals[unit] = totals.get(unit, Decimal(0)) + amount
    lines = ['Escenario hipotético aportado; no verificado financieramente.',
             'Período aportado: ' + bound['period'] + '.',
             'Importes aportados por suscripción:']
    lines += [f'{scope}: {exact(amount)} {unit}.' for scope, amount, unit in bound['costs']]
    lines += ['Totales separados por moneda: ' + '; '.join(
        exact(total) + ' ' + unit for unit, total in totals.items()) + '.',
        'No se consolida un total entre monedas ni se inventa una conversión. '
        'Para consolidar, indica la moneda destino, el tipo de cambio autorizado '
        '(incluida su dirección entre cada moneda de origen y la moneda destino) '
        'y la fecha de cambio aplicable.']
    return '\n'.join(lines)
