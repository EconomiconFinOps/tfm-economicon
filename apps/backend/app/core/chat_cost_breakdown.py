"""Compute complete user-declared service and monthly comparisons with scope.

Only a closed, fully consumed declaration of a period, subscription, currency,
cost basis and service amounts qualifies. Service names and amounts are input
data, not a fixed example. This never verifies ingestion or billing authority.
"""
import hashlib
import json
import re
from decimal import Decimal, localcontext
from fractions import Fraction

from app.core.chat_missing_spend import MONTH
from app.core.chat_rules import normalized


AMOUNT = r'-?[0-9]{1,12}(?:[.,][0-9]{1,12})?'
DECLARATION = re.compile(
    rf'(?:Contexto del escenario:\s*)?Escenario sint[eé]tico completo de '
    rf'(?P<month>{MONTH}) de (?P<year>[0-9]{{4}}), suscripci[oó]n '
    r'(?P<subscription>[A-Za-z0-9][A-Za-z0-9_-]{0,63}), moneda '
    r'(?P<currency>EUR|USD|GBP|CHF|CAD|AUD|JPY), coste '
    r'(?P<basis>actual|amortizado): (?P<items>[^\n]+)[.] No hay otras l[ií]neas[.]?', re.I)
ITEM = re.compile(rf'(?P<service>[^;:<>"`\n]{{1,80}}?)\s+(?P<value>{AMOUNT})')


def required_monthly_comparison(catalog):
    """Bind explicit full months and comparable amounts, not arbitrary prose."""
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2 or any(s.get('kind') != 'corpus'
                             for s in getattr(catalog, 'authorized_sources', ())):
        return None
    request = re.fullmatch(
        r'¿?(?:(?:cuanto subio|como cambio) el gasto|calcula la variacion del gasto) entre '
        rf'(?P<baseline>{MONTH}) y (?P<current>{MONTH})[?.]?', normalized(parts[0]))
    number = r'[0-9]{1,12}(?:[.,][0-9]{1,12})?'
    currency = r'EUR|USD|GBP|CHF|CAD|AUD|JPY'
    declaration = re.fullmatch(
        r'(?:Contexto del escenario:\s*)?Escenario sint[eé]tico, mismo alcance '
        r'(?P<scope>[A-Za-z0-9][A-Za-z0-9_-]{0,63}) y meses completos de (?P<year>[0-9]{4}): '
        rf'(?P<first_month>{MONTH}) (?P<first>{number}) (?P<first_currency>{currency}); '
        rf'(?P<second_month>{MONTH}) (?P<second>{number}) (?P<second_currency>{currency}) '
        r'de coste (?P<basis>actual|amortizado)[.]?', parts[1], re.I)
    if request is None or declaration is None or not 1900 <= int(declaration['year']) <= 2200:
        return None
    baseline,current=request['baseline'],request['current']
    first,second=normalized(declaration['first_month']),normalized(declaration['second_month'])
    if (baseline==current or first==second or {baseline,current}!={first,second}
            or declaration['first_currency'].upper()!=declaration['second_currency'].upper()):
        return None
    amounts={first:Decimal(declaration['first'].replace(',','.')),
             second:Decimal(declaration['second'].replace(',','.'))}
    if any(v>Decimal('1e12') for v in amounts.values()):
        return None
    with localcontext() as precision:
        precision.prec=80
        difference=amounts[current]-amounts[baseline]
        relative=difference/amounts[baseline]*100 if amounts[baseline] else None
    identity=hashlib.sha256(json.dumps({'question':question},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'id':identity,'baseline_month':baseline,'current_month':current,
            'baseline':amounts[baseline],'current':amounts[current],
            'difference':difference,'relative':relative,'year':int(declaration['year']),
            'scope':declaration['scope'],'basis':declaration['basis'].lower(),
            'currency':declaration['first_currency'].upper()}


def monthly_comparison_answer(value,catalog):
    bound=required_monthly_comparison(catalog)
    if bound is None or value!={'monthly_comparison':bound['id']}:
        raise ValueError('Monthly comparison is not grounded.')
    from app.core.chat_expressions import display
    def exact(number):
        text=format(number,'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    baseline,current,delta=(exact(bound[k]) for k in ('baseline','current','difference'))
    unit=bound['currency']
    answer=('Escenario hipotético aportado; no verificado financieramente.\n'
        f'Ámbito aportado: {bound["scope"]}; meses completos de {bound["year"]}; coste {bound["basis"]}.\n'
        f'Baseline de {bound["baseline_month"]}: {baseline} {unit}. '
        f'Gasto de {bound["current_month"]}: {current} {unit}.\n'
        f'Variación absoluta ({bound["current_month"]} menos {bound["baseline_month"]}): '
        f'{current} − {baseline} = {delta} {unit}.\n')
    if bound['relative'] is None:
        answer+='Variación relativa indefinida: el baseline es cero; no se inventa un porcentaje de crecimiento.\n'
    else:
        with localcontext() as precision:
            precision.prec=80
            shown=display(bound['relative'])
        equality='=' if Fraction(Decimal(shown))*Fraction(bound['baseline'])==Fraction(bound['difference'])*100 else '≈'
        answer+=(f'Variación relativa sobre {bound["baseline_month"]}: '
                 f'({delta} / {baseline}) × 100 {equality} {shown} %.\n')
    trend='aumentó' if bound['difference']>0 else 'disminuyó' if bound['difference']<0 else 'no varió'
    return answer+(f'El gasto declarado {trend}; el cálculo no confirma una causa, '
                   'severidad ni facturación real.')


def required_cost_breakdown(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2:
        return None
    request = re.fullmatch(
        r'¿?(?:cuanto gastamos|cual es el gasto total)(?: en (' + MONTH + r')(?: de ([0-9]{4}))?)? '
        r'y (?:que|cual) servicio (?:concentra mas coste|cuesta mas|tiene mayor coste)[?.]?', normalized(parts[0]))
    declaration = DECLARATION.fullmatch(parts[1])
    if request is None or declaration is None:
        return None
    if any(source.get('kind') != 'corpus' for source in getattr(catalog, 'authorized_sources', ())):
        return None  # A server cost query is not replaceable by a user assertion.
    month, year = normalized(declaration['month']), declaration['year']
    if (not 1900 <= int(year) <= 2200 or request[1] is not None and request[1] != month
            or request[2] is not None and request[2] != year):
        return None
    fields = declaration['items'].split('; ')
    if not 1 <= len(fields) <= 12:
        return None
    items = []
    for field in fields:
        match = ITEM.fullmatch(field)
        if match is None:
            return None
        service = match['service']
        # Labels are data, not prose instructions, formulas, extra scope or
        # executable identifiers. Preserve spelling but reject empty/odd labels.
        if (service != service.strip() or not re.fullmatch(r'[\w][\w /&+().-]{0,79}', service)
                or re.search(r'\b(?:no|sin|excepto|ignora\w*|incluy\w*|excluy\w*|periodo|moneda|total)\b', normalized(service))):
            return None
        value = Decimal(match['value'].replace(',', '.'))
        if abs(value) > Decimal('1e12'):
            return None
        items.append({'service': service, 'value': value, 'source_span': match.group()})
    # Duplicate labels might represent separate lines or overlapping aggregates.
    # Do not infer which; preserve the ordinary route for clarification.
    if len({normalized(item['service']) for item in items}) != len(items):
        return None
    with localcontext() as precision:
        precision.prec = 40
        total = sum((item['value'] for item in items), Decimal(0))
        greatest = max(item['value'] for item in items)
        leaders = [item['service'] for item in items if item['value'] == greatest]
        # Signed adjustments are legitimate totals; a positive expenditure
        # share is not meaningful for a zero or negative net denominator.
        share = greatest / total * 100 if total > 0 and greatest >= 0 else None
    data = {'question': question, 'source_spans': [item['source_span'] for item in items]}
    identity = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':')).encode()).hexdigest()
    return {'id': identity, 'month': month, 'year': year, 'subscription': declaration['subscription'],
            'currency': declaration['currency'].upper(), 'basis': normalized(declaration['basis']),
            'items': items, 'total': total, 'greatest': greatest, 'leaders': leaders, 'share': share}


def cost_breakdown_answer(value, catalog):
    bound = required_cost_breakdown(catalog)
    if bound is None or value != {'cost_breakdown': bound['id']}:
        raise ValueError('Cost breakdown is not grounded.')

    def shown(number):
        text = format(number, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text

    currency = bound['currency']
    text = ('Escenario hipotético aportado; no verificado financieramente.\n'
            f'Período aportado: {bound["month"]} de {bound["year"]}; '
            f'suscripción aportada: {bound["subscription"]}; moneda: {currency}; '
            f'vista de coste declarada: coste {bound["basis"]}.\n'
            'Se conserva la declaración de que no hay otras líneas; no se ha verificado esa cobertura.\n')
    text += '\n'.join(item['service'] + ': ' + shown(item['value']) + ' ' + currency
                      for item in bound['items']) + '\n'
    text += ('Suma de las líneas: ' + ' + '.join('(' + shown(item['value']) + ')' for item in bound['items'])
             + ' = ' + shown(bound['total']) + ' ' + currency + '.\n')
    text += ('Servicio con mayor importe' if len(bound['leaders']) == 1 else 'Servicios empatados en el mayor importe')
    text += ': ' + ', '.join(bound['leaders']) + '; ' + shown(bound['greatest']) + ' ' + currency + '.\n'
    if bound['share'] is not None:
        from app.core.chat_expressions import display
        with localcontext() as precision:
            precision.prec = 80
            percentage = display(bound['share'])
        relation = '=' if Fraction(Decimal(percentage)) * Fraction(bound['total']) == Fraction(bound['greatest']) * 100 else '≈'
        text += ('Participación de cada servicio indicado sobre el total neto: '
                 + shown(bound['greatest']) + ' / ' + shown(bound['total'])
                 + ' × 100 ' + relation + ' ' + percentage + ' %.\n')
        if any(item['value'] < 0 for item in bound['items']):
            text += 'Hay ajustes negativos: una participación sobre el total neto puede superar el 100 %.\n'
    else:
        text += 'No se interpreta una participación del gasto con total neto cero o negativo.\n'
    text += ('Estos datos no son una factura real ni una consulta de costes autorizada. '
             'Para contrastarlos hay que verificar la misma suscripción, período, moneda y vista de coste.')
    return text
