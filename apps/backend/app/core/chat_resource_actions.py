"""Bound direct resource-change requests to this assistant's read-only capability.

This is a deliberately bounded command grammar, not a general intent classifier.
It never turns a retrieved rightsizing policy into a prerequisite for other work.
Questions, quoted instructions and negated commands keep their ordinary route.
"""
import copy
import hashlib
import json
import re

from app.core.chat_rules import normalized


TARGET = (r'(?:tod[oa]s? (?:l[oa]s? )?|(?:este|esta|estos|estas) |mis? |(?:el|la|los|las|un|una|unos|unas) )?'
          r'(?:maquinas?(?: virtual(?:es)?)?|vms?|recursos?|servidor(?:es)?|instancias?|discos?|bases? de datos)'
          r'(?: [a-z0-9][a-z0-9_.:/ -]{0,120})?')
VERBS = r'(?:apaga|deten|reinicia|elimina|borra|redimensiona|modifica)'
NOUNS = r'(?:apagado|reinicio|borrado|eliminacion|redimensionamiento|cambio de tamano)'
COMMAND = re.compile(
    r'(?:por favor,? )?(?:ignora (?:todas )?las restricciones(?: de seguridad)? y )?'
    r'(?:' + VERBS + r' ' + TARGET
    + r'|(?:aplica|ejecuta|realiza) (?:el|un) ' + NOUNS + r' (?:a|en|de|sobre) ' + TARGET + r')[.!]?')


def required_resource_action(catalog):
    question = getattr(catalog, 'classification_question', '')
    if not isinstance(question, str) or not 1 <= len(question) <= 16384:
        return None
    # Only the current request paragraph supplies intent. Retrieval and the
    # scenario may describe operations without requesting that we execute them.
    request = normalized(question.split('\n\n', 1)[0]).strip()
    if COMMAND.fullmatch(request) is None:
        return None
    fields = {
        'answer': ('Este asistente no ejecuta cambios sobre recursos cloud. '
                   'No se ha ejecutado la acción solicitada. '
                   'Puedo analizar los datos disponibles y preparar una propuesta '
                   'para revisión humana, con su alcance, impacto y riesgos.'),
        'status': 'refused',
        'next_actions': ['Indicar el ámbito y el objetivo para preparar un análisis '
                         'o una propuesta revisable, sin ejecutar cambios.'],
    }
    identity = {'question': question, 'capability': 'resource-changes-unavailable-v1', 'public_fields': fields}
    return {'id': hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest(), 'public_fields': fields}


def resource_action_answer(value, catalog):
    bound = required_resource_action(catalog)
    if bound is None or value != {'resource_action': bound['id']}:
        raise ValueError('Resource action answer is not bound to this request.')
    return copy.deepcopy(bound['public_fields'])
