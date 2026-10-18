"""Metric-bound comparisons for two explicitly comparable hypothetical periods.

Only a complete cost/count declaration and an explicit unit-cost definition are
compiled. Dates, partial periods, ambiguous units or financial authority are not
inferred. Each caption and its operands are rendered together by the server.
"""
import hashlib
import json
import re
from decimal import Decimal, localcontext
from fractions import Fraction

from app.core.chat_rules import normalized


def required_unit_cost(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = normalized(question).split('\n\n')
    if len(parts) != 2 or not re.fullmatch(
            r'¿?(?:el incremento de gasto significa que somos menos eficientes'
            r'|compara (?:el )?coste unitario(?: entre (?:ambos|los dos) periodos)?'
            r'|calcula (?:la )?variacion del coste unitario'
            r'|ha (?:mejorado|empeorado) (?:la )?eficiencia)[?.]?', parts[0]):
        return None
    if any(s.get('kind') != 'corpus' for s in getattr(catalog, 'authorized_sources', ())):
        return None
    number = r'[0-9]{1,12}(?:[.,][0-9]{1,12})?'
    unit = r'pedidos|operaciones|transacciones|usuarios|unidades'
    period = (r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
              r'(?: [12][0-9]{3})?|periodo [ab]')
    pair = rf'(?P<period>{period}) (?P<cost>{number}) (?P<currency>eur|usd|gbp|chf|cad|aud|jpy) y (?P<count>{number}) (?P<unit>{unit})'
    scenario = re.fullmatch(
        r'(?:contexto del escenario:\s*)?escenario sintetico con periodos completos y comparables: '
        rf'(?P<first>[^;\n]+); (?P<second>[^;\n]+)[.] '
        rf'(?:definir|definicion de) coste unitario = gasto / (?P<definition>{unit})[.]?', parts[1])
    if scenario is None:
        return None
    rows = [re.fullmatch(pair, scenario[key]) for key in ('first', 'second')]
    if any(row is None for row in rows):
        return None
    first, second = rows
    if (first['period'] == second['period'] or first['currency'] != second['currency']
            or first['unit'] != second['unit'] or first['unit'] != scenario['definition']):
        return None
    data = [{'period': row['period'], 'cost': Decimal(row['cost'].replace(',', '.')),
             'count': Decimal(row['count'].replace(',', '.'))} for row in rows]
    if any(value > Decimal('1e12') for row in data for value in (row['cost'], row['count'])):
        return None
    return {'id': hashlib.sha256(json.dumps({'question': question, 'spans': scenario.groupdict()},
                    sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            'periods': data, 'currency': first['currency'].upper(), 'unit': first['unit']}


def unit_cost_answer(value, catalog):
    bound = required_unit_cost(catalog)
    if bound is None or value != {'unit_cost': bound['id']}:
        raise ValueError('Unit-cost comparison is not grounded.')
    from app.core.chat_expressions import display

    def shown(value):
        with localcontext() as precision:
            precision.prec = 80
            text = display(Decimal(value.numerator) / Decimal(value.denominator))
        return ('=' if Fraction(Decimal(text)) == value else '≈') + ' ' + text

    a, b = bound['periods']
    cost_a, cost_b, count_a, count_b = (Fraction(x) for x in (a['cost'], b['cost'], a['count'], b['count']))
    currency, unit = bound['currency'], bound['unit']
    answer = ('Escenario hipotético aportado; no verificado financieramente. '
              'La comparación toma como base el primer período declarado y usa la definición gasto / '+unit+'.\n')
    for row in (a, b):
        cost, count = Fraction(row['cost']), Fraction(row['count'])
        answer += f"{row['period']}: gasto {format(row['cost'], 'f')} {currency}; volumen {format(row['count'], 'f')} {unit}. "
        if not count:
            answer += 'Coste unitario indefinido: el volumen es cero.\n'
        else:
            answer += f'Coste unitario {shown(cost / count)} {currency}/{unit}.\n'
    answer += f'Variación absoluta del gasto total (segundo menos primero) {shown(cost_b-cost_a)} {currency}.\n'
    answer += ('Variación relativa del gasto total sobre el primer período '+shown((cost_b-cost_a)/cost_a*100)+' %.\n'
               if cost_a else 'Variación relativa del gasto total indefinida: el gasto inicial es cero.\n')
    if not count_a or not count_b:
        return answer + 'No se calcula la variación del coste unitario ni se concluye sobre eficiencia con un volumen nulo.'
    first, second = cost_a/count_a, cost_b/count_b
    delta = second-first
    answer += f'Variación absoluta del coste unitario (segundo menos primero) {shown(delta)} {currency}/{unit}.\n'
    answer += ('Variación relativa del coste unitario sobre el primer período '+shown(delta/first*100)+' %.\n'
               if first else 'Variación relativa del coste unitario indefinida: el coste unitario inicial es cero.\n')
    relation = 'disminuye' if delta < 0 else 'aumenta' if delta > 0 else 'se mantiene'
    return answer + ('El coste por unidad '+relation+'. El gasto total por sí solo no determina la eficiencia. '
                     'Esta comparación solo evalúa coste por unidad; no acredita calidad de servicio, beneficio ni ahorro realizado.')
