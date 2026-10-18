"""Closed reporting-scenario grammar backed by complete documentary definitions.

This route classifies an explicitly described accounting treatment. It never
infers allocation quality or authorizes a financial transfer. Unsupported prose
retains the ordinary response route rather than being coerced into a fact.
"""
import hashlib
import json
import re

from app.core.chat_premises import Premise, evaluate
from app.core.chat_rules import normalized, validate_provenance


SHOWBACK = '**Showback** muestra costes asignados a equipos o unidades sin repercusion contable formal.'
CHARGEBACK = '**Chargeback** repercute el coste formalmente a una unidad responsable.'
RATIONALE = 'Es apropiado para el MVP porque mejora visibilidad y accountability sin requerir procesos financieros estrictos.'
QUALITY = 'Debe esperar a que la calidad de allocation sea suficiente.'


def required_reporting(catalog):
    question = getattr(catalog, 'classification_question', '')
    parts = normalized(question).split('\n\n')
    if len(parts) != 2:
        return None
    request, scenario = parts
    if not re.fullmatch(r'[¿]?(?:podemos presentar (?:este|el) reparto como (?:chargeback|showback)'
                        r'|(?:este|el) reparto es (?:showback o chargeback|chargeback o showback))[?]?', request):
        return None
    # Bind an entire supported statement, not a phrase buried in a negation,
    # quotation, counterfactual, multiple scenarios or additional instructions.
    match = re.fullmatch(
        r'(?:contexto del escenario:\s*)?(?:escenario sintetico\s+)?(?:con\s+)?'
        r'costes (?:mostrados|asignados) (?:por|a) (?:equipos?|unidades)'
        r'(?: para dar visibilidad)?,\s*(sin|con) repercusion contable formal[.]?', scenario)
    if not match:
        return None
    candidates = []
    for source in getattr(catalog, 'rule_sources', ()):
        if (source.get('kind') != 'corpus' or not isinstance(source.get('title'), str)
                or not 1 <= len(source['title']) <= 256):
            continue
        for span in validate_provenance(source):
            if normalized(span['section'] or '') != 'showback y chargeback':
                continue
            text = source['content'][span['start']:span['end']].strip()
            # Compile only the complete supported definition block. An edited,
            # negated, incomplete or extended policy is not silently interpreted.
            expected = '## Showback Y Chargeback ' + SHOWBACK + ' ' + RATIONALE + ' ' + CHARGEBACK + ' ' + QUALITY
            if normalized(text) == normalized(expected):
                candidates.append(source)
    if len(candidates) != 1:
        return None
    source = candidates[0]
    formal = match.group(1) == 'con'
    identity = hashlib.sha256(json.dumps({'question': question, 'source': source},
        ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'id': identity, 'formal_transfer': formal, 'source': source}


def reporting_answer(value, catalog):
    bound = required_reporting(catalog)
    if bound is None or value != {'reporting_basis': bound['id']}:
        raise ValueError('Reporting decision is not grounded.')
    facts = {'formal_transfer': Premise(bound['formal_transfer'], ('user:' + bound['id'],)),
             'allocation_quality_sufficient': Premise(None)}
    decision = evaluate({'premise': 'formal_transfer'}, facts)
    label = 'chargeback' if decision.value else 'showback'
    text = ('Según el escenario hipotético aportado, el reparto corresponde a ' + label + '. '
            + ('Se declara repercusión contable formal.' if decision.value else
               'Se muestran costes sin repercusión contable formal; no debe presentarse como chargeback.')
            + '\nNo se ha evaluado la calidad de allocation en esta clasificación: '
              'no se concluye que sea suficiente ni insuficiente. Para plantear chargeback, '
              'esa calidad debe verificarse; esta respuesta no autoriza una repercusión contable.')
    content = bound['source']['content']
    definition = re.search(r'\*\*' + label + r'\*\*[^.]+[.]', content, re.I).group()
    quality = re.search(r'Debe esperar[^.]+[.]', content, re.I).group()
    for quote in (definition, quality):
        text += '\nFuente: ' + bound['source']['title'] + ' — «' + quote + '»'
    return text, [bound['source']]
