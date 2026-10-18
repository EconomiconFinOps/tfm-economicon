"""Preserve a declared shared cost when no approved allocation rule is supplied.

No source is chosen by chunk identity or topical similarity. The decision uses
only the complete hypothetical user declaration; documentary claims, real
financial observations and illustrative allocations stay on the general route.
"""
import hashlib
import json
import re
from decimal import Decimal

from app.core.chat_rules import normalized

AMOUNT = r'[0-9]{1,12}(?:[.,][0-9]{1,12})?'
MONEY = rf'(?P<amount>{AMOUNT}) (?P<currency>EUR|USD|GBP|CHF|CAD|AUD|JPY)'
LABEL = r'[\w][\w -]{0,59}'
REQUEST = re.compile(rf'¿?Cu[aá]nto (?:cargamos|imputamos|asignamos) a cada equipo por los '
                     rf'{MONEY} de (?P<asset>{LABEL}) compartid[oa][?]?', re.I)
SCENARIO = re.compile(rf'(?:Contexto del escenario:\s*)?Escenario sint[eé]tico: '
                      rf'(?P<asset>{LABEL}) shared de {MONEY}, usad[oa] por equipos '
                      r'(?P<teams>[^.;\n]+)[.] No existe regla de reparto aprobada '
                      r'ni consumo por equipo[.]?', re.I)


def required_shared_allocation(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = question.split('\n\n')
    if len(parts) != 2:
        return None
    request, scenario = REQUEST.fullmatch(parts[0]), SCENARIO.fullmatch(parts[1])
    if request is None or scenario is None:
        return None
    if any(source.get('kind') != 'corpus' for source in getattr(catalog, 'authorized_sources', ())):
        return None
    if (request['currency'].upper() != scenario['currency'].upper()
            or normalized(request['asset']) != normalized(scenario['asset'])
            or Decimal(request['amount'].replace(',', '.')) != Decimal(scenario['amount'].replace(',', '.'))):
        return None
    amount = Decimal(scenario['amount'].replace(',', '.'))
    if not 0 < amount <= Decimal('1e12'):
        return None
    teams = re.split(r', | y ', scenario['teams'])
    if (not 2 <= len(teams) <= 8 or len({normalized(team) for team in teams}) != len(teams)
            or any(not re.fullmatch(LABEL, team) or team != team.strip() for team in teams)
            or re.search(r'\b(?:no|sin|excepto|ignora\w*|incluy\w*|excluy\w*)\b',
                         normalized(scenario['asset'] + ' ' + scenario['teams']))):
        return None
    payload = {'question': question, 'source_spans': [request.group(), scenario.group()]}
    identity = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':')).encode()).hexdigest()
    return {'id': identity, 'amount': amount, 'currency': scenario['currency'].upper(),
            'asset': scenario['asset'], 'teams': teams,
            'approved_rule': False, 'consumption_by_team': None}


def shared_allocation_answer(value, catalog):
    bound = required_shared_allocation(catalog)
    if bound is None or value != {'shared_allocation': bound['id']}:
        raise ValueError('Shared allocation decision is not grounded.')
    number = format(bound['amount'], 'f')
    number = number.rstrip('0').rstrip('.') if '.' in number else number
    return ('Escenario hipotético aportado; no verificado financieramente.\n'
            f'El importe aportado de {bound["asset"]} es {number} {bound["currency"]}, '
            'identificado como shared en el escenario y utilizado por los equipos '
            + ', '.join(bound['teams']) + '. Se mantiene como coste compartido identificado; '
            'la ausencia de una regla de reparto no borra esa identificación.\n'
            'El escenario declara que no existe una regla de reparto aprobada ni consumo por equipo. '
            'No se puede determinar cuánto corresponde a cada equipo: no se asignan importes '
            'iguales ni porcentajes por defecto.\n'
            'Hace falta definir o aportar la regla aprobada, su base de reparto y los datos '
            'por equipo que esa regla requiera, para el mismo período y ámbito. '
            'Esta respuesta no imputa cargos ni acredita un reparto aprobado. '
            'Los documentos generales recuperados no sustituyen la regla de este escenario.')
