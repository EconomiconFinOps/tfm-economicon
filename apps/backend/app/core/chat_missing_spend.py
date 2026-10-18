"""Explicit hypothetical empty-query/incomplete-ingestion decision.

This is a closed statement grammar, not a coverage verifier. Real billing
authority remains with the server's scoped queries. Unknown/ambiguous language
does not enter this terminal.
"""
import hashlib
import re

from app.core.chat_premises import Premise, evaluate
from app.core.chat_rules import normalized


MONTHS = ('enero febrero marzo abril mayo junio julio agosto septiembre octubre '
          'noviembre diciembre').split()
MONTH = '(?:' + '|'.join(MONTHS) + ')'


def required_missing_spend(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = normalized(question).split('\n\n')
    if len(parts) != 2:
        return None
    request = re.fullmatch(r'[¿]?el gasto de (' + MONTH + r')(?: de ([0-9]{4}))? es (?:cero|0)[?]?', parts[0])
    scenario = re.fullmatch(
        r'(?:contexto del escenario:\s*)?(?:escenario sintetico:\s*)?'
        r'la consulta de (' + MONTH + r') de ([0-9]{4}) devuelve (?:cero|0) registros, '
        r'pero la ingesta (?:del mes|de ese periodo) (?:todavia |aun )?no se ha completado[.]?', parts[1])
    if (request is None or scenario is None or request.group(1) != scenario.group(1)
            or request.group(2) is not None and request.group(2) != scenario.group(2)):
        return None
    # A server financial observation is a different source of authority. Do not
    # discard it merely because a hypothetical sentence also appears in input.
    if any(source.get('kind') != 'corpus' for source in getattr(catalog, 'authorized_sources', ())):
        return None
    return {'id': hashlib.sha256(question.encode()).hexdigest(),
            'period': scenario.group(1) + ' de ' + scenario.group(2)}


def missing_spend_answer(value, catalog):
    bound = required_missing_spend(catalog)
    if bound is None or value != {'missing_spend': bound['id']}:
        raise ValueError('Missing-spend decision is not grounded.')
    facts = {'query_has_rows': Premise(False, ('user:' + bound['id'],)),
             'period_coverage_complete': Premise(False, ('user:' + bound['id'],)),
             'period_spend_is_zero': Premise(None)}
    decision = evaluate({'premise': 'period_spend_is_zero'}, facts)
    if decision.value is not None:
        raise ValueError('Empty query cannot establish a period total.')
    return ('Escenario hipotético aportado; no verificado financieramente.\n'
            'No se puede concluir que el gasto de ' + bound['period'] + ' sea cero. '
            'La consulta sin registros y la ingesta incompleta descritas no acreditan '
            'el gasto total del periodo; tampoco demuestran que exista un gasto positivo. '
            'Es necesario completar o verificar la cobertura de la ingesta y obtener una '
            'consulta de costes autorizada para el mismo ámbito, periodo y moneda antes '
            'de atribuir un importe.')
