"""Complete count and cost coverage from two explicitly supplied disjoint groups.

This is a closed scenario grammar, not a general extractor or a tagging policy.
The user declares which resources comply and that all the cost is taggable.
Both denominators and both results are server-owned; unsupported, incomplete or
contradictory scenarios keep the general response route. No billing authority.
"""
import hashlib
import json
import re
from decimal import Decimal, localcontext
from fractions import Fraction

from app.core.chat_rules import normalized

NUMBER = r'[0-9]{1,12}(?:[.,][0-9]{1,12})?'
COUNT = r'(?:[0-9]{1,9}|[a-z]+)'
CURRENCY = r'(?:EUR|USD|GBP|CHF|CAD|AUD|JPY)'
# An ordinal may identify the sole remaining resource, but is never used to
# infer an arbitrary missing group size. Validate it against the declared total.
ORDINALS = dict(zip(('primero segundo tercero cuarto quinto sexto septimo octavo '
                    'noveno decimo undecimo duodecimo').split(), range(1, 13)))
SCENARIO = re.compile(
    rf'(?P<total>{COUNT}) recursos etiquetables[.] '
    rf'(?P<compliant>{COUNT})(?: recursos)? cumplen todos los (?:tags minimos|requisitos de etiquetado) '
    rf'y (?:suman|cuestan) (?P<yes_cost>{NUMBER}) (?P<yes_unit>{CURRENCY}); '
    rf'(?:(?P<noncompliant>{COUNT}) recursos incumplen|el (?P<ordinal>[a-z]+) incumple) '
    rf'y (?:suman|cuestan|cuesta) (?P<no_cost>{NUMBER}) (?P<no_unit>{CURRENCY})[.] '
    r'todo el coste es etiquetable[.]?', re.I)


def required_weighted_coverage(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2:
        return None
    request, scenario = map(normalized, parts)
    # Whole requests only: negations, multiple questions and other weightings
    # cannot be turned into a demand for this particular metric.
    if not re.fullmatch(
            r'¿?(?:cual es (?:el|la)|calcula (?:el|la)|muestra (?:el|la)) '
            r'(?:cumplimiento|cobertura) de (?:tagging|etiquetado) '
            r'(?:por coste|ponderad[ao] por coste)[?.]?', request):
        return None
    if any(source.get('kind') != 'corpus'
           for source in getattr(catalog, 'authorized_sources', ())):
        return None
    scenario = re.sub(r'^contexto del escenario:\s*', '', scenario)
    scenario = re.sub(r'^escenario sintetico:\s*', '', scenario)
    match = SCENARIO.fullmatch(scenario)
    if match is None:
        return None
    from app.core.chat_expressions import CARDINALS
    words = {normalized(key): value for key, value in CARDINALS.items()}

    def count(raw):
        return int(raw) if raw.isascii() and raw.isdigit() else words.get(raw)

    total, compliant = count(match['total']), count(match['compliant'])
    noncompliant = count(match['noncompliant']) if match['noncompliant'] else 1
    if (total is None or compliant is None or noncompliant is None
            or not 0 < total <= 10**9 or min(compliant, noncompliant) < 0
            or compliant + noncompliant != total
            or (match['ordinal'] and ORDINALS.get(match['ordinal']) != total)):
        return None
    if match['yes_unit'].upper() != match['no_unit'].upper():
        return None
    yes, no = (Decimal(match[key].replace(',', '.')) for key in ('yes_cost', 'no_cost'))
    if (max(yes, no) > Decimal('1e12') or (not compliant and yes != 0)
            or (not noncompliant and no != 0)):
        return None
    with localcontext() as precision:
        precision.prec = 40
        cost_total = yes + no
        by_cost = yes / cost_total * 100 if cost_total else None
        by_count = Decimal(compliant) / Decimal(total) * 100
    spans = {key: match[key] for key in (
        'total', 'compliant', 'noncompliant', 'ordinal', 'yes_cost', 'no_cost', 'yes_unit', 'no_unit')}
    identity = hashlib.sha256(json.dumps({'question': question, 'spans': spans},
        ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'id': identity, 'total': total, 'compliant': compliant, 'noncompliant': noncompliant,
            'yes_cost': yes, 'no_cost': no, 'cost_total': cost_total,
            'by_cost': by_cost, 'by_count': by_count, 'currency': match['yes_unit'].upper(),
            'source_spans': spans}


def weighted_coverage_answer(value, catalog):
    bound = required_weighted_coverage(catalog)
    if bound is None or value != {'weighted_coverage': bound['id']}:
        raise ValueError('Weighted coverage is not grounded.')

    def show(number):
        text = format(number, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text

    yes, no, total = (show(bound[key]) for key in ('yes_cost', 'no_cost', 'cost_total'))
    def percentage(value, numerator, denominator):
        from app.core.chat_expressions import display
        with localcontext() as precision:
            precision.prec = 80
            shown = display(value)
        relation = '=' if Fraction(Decimal(shown)) * Fraction(denominator) == Fraction(numerator) * 100 else '≈'
        return relation + ' ' + shown

    unit = bound['currency']
    count = percentage(bound['by_count'], bound['compliant'], bound['total'])
    text = ('Escenario hipotético aportado; no verificado financieramente.\n'
            'Se toma del escenario la declaración de qué recursos cumplen todos los tags '
            'y de que todo el coste es etiquetable; no se ha auditado el etiquetado.\n'
            f'Coste que cumple: {yes} {unit}; coste que incumple: {no} {unit}. '
            f'Coste etiquetable total: {yes} + {no} = {total} {unit}.\n')
    if bound['by_cost'] is None:
        text += ('Cumplimiento por coste indefinido: el denominador es cero; '
                 'no se convierte en un cumplimiento del 0 % ni del 100 %.\n')
    else:
        result = percentage(bound['by_cost'], bound['yes_cost'], bound['cost_total'])
        text += (f'Cumplimiento de tagging por coste: {yes} / {total} × 100 {result} %.\n')
    text += (f'Por número de recursos: {bound["compliant"]} / {bound["total"]} × 100 {count} %. '
             'Este porcentaje cuenta recursos; no sustituye al resultado ponderado por coste. '
             'Para una medición real deben verificarse coste, etiquetas, período y ámbito.')
    return text
