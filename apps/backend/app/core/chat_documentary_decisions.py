"""Literal definitions and qualified advice over explicit three-valued premises.

Complete positional sections supply all documentary wording. The provider never
upgrades a qualifier or supplies a premise. Unsupported requests/policies keep
the ordinary route; these compilers do not establish general semantic entailment.
"""
import copy
import hashlib
import json
import re

from app.core.chat_policy_sections import complete_sections
from app.core.chat_premises import Premise, evaluate
from app.core.chat_rules import normalized


def _section(catalog, heading):
    sources = list(getattr(catalog, 'rule_sources', ()))
    known = {source['id']: source for source in getattr(catalog, 'authorized_sources', ())}
    if any(known.get(source['id']) != source for source in sources):
        raise ValueError('Documentary decision source is not authorized.')
    sections = complete_sections(sources, heading)
    return sections[0] if len(sections) == 1 else None


def _selections(section, clauses):
    selected, records = [], {}
    for clause in clauses:
        if not clause or len(clause) > 220:
            return None
        matches = [source for source in section['sources'] if clause in source['content']]
        if not matches:
            return None
        source = min(matches, key=lambda s: (s['provenance']['chunk_index'], s['id']))
        if not isinstance(source.get('title'), str) or not 1 <= len(source['title']) <= 256:
            return None
        selected.append({'source_id': source['id'], 'passage': clause})
        records[source['id']] = source
    return selected, list(records.values())


def _quotations(selected, records):
    known = {record['id']: record for record in records}
    return ''.join('\nFuente: ' + known[item['source_id']]['title'] + ' — «' + item['passage'] + '»\n'
                   for item in selected)


def _cost_basis(catalog, question):
    parts = question.split('\n\n')
    if len(parts) > 2 or (len(parts) == 2 and not re.fullmatch(
            r'(?:contexto del escenario:\s*)?consulta conceptual, sin importes ni contratos de cliente[.]?', normalized(parts[1]))):
        return None
    request = normalized(parts[0])
    first = r'(?:coste actual|actual cost)'
    second = r'(?:(?:coste )?amortizado|amortized cost)'
    if not re.fullmatch(
            rf'¿?(?:uso {first} o {second} para repartir el coste de (?:una reserva|un savings plan)'
            rf'|que diferencia hay entre {first} y {second}'
            rf'|compara {first} (?:con|y) {second})[?.]?', request):
        return None
    section = _section(catalog, 'Conceptos FinOps Basicos')
    if section is None:
        return None
    # A definition block ends at the next definition, not its first period:
    # retaining subsequent qualifications avoids dropping a limiting sentence.
    body = section['body']
    markers = list(re.finditer(r'(?:^|(?<=[.!?])\s+)(?P<start>(?:(?:El|La|Un|Una) )?\*\*(?P<label>[^*]{1,80})\*\*)', body))
    definitions = {}
    for index, marker in enumerate(markers):
        label = normalized(marker['label'])
        if label not in ('actual cost', 'amortized cost'):
            continue
        if label in definitions:
            return None
        end = markers[index+1].start('start') if index+1 < len(markers) else len(body)
        clause = body[marker.start('start'):end].strip()
        if not clause.endswith('.'):
            return None
        definitions[label] = clause
    if set(definitions) != {'actual cost', 'amortized cost'}:
        return None
    chosen = _selections(section, [definitions['actual cost'], definitions['amortized cost']])
    if chosen is None:
        return None
    selected, records = chosen
    answer = ('Comparación documental de coste actual y amortizado. '
              'Para decidir entre ambas vistas, estas son sus definiciones completas en la fuente:\n'
              + _quotations(selected, records)
              + '\nLa aplicabilidad a un contrato o reparto concreto no se ha evaluado en esta consulta conceptual.')
    return {'topic': 'cost_basis', 'section': section, 'selections': selected, 'sources': records,
            'public_fields': {'answer': answer, 'status': 'ok', 'next_actions': []}}


def _commitment(catalog, question):
    parts = normalized(question).split('\n\n')
    if len(parts) != 2 or not re.fullmatch(
            r'¿?(?:compramos|conviene comprar|es recomendable comprar) (?:una reserva|un commitment|un savings plan) '
            r'(?:de inmediato|ahora)(?: para una (?:vm|maquina virtual)(?: que pronto migraremos)?)?[?]?', parts[0]):
        return None
    scenario = re.fullmatch(
        r'(?:contexto del escenario:\s*)?escenario sintetico: migracion prevista '
        r'(?P<when>el proximo mes|dentro de [1-9][0-9]{0,2} (?:dias|semanas|meses)), '
        r'demanda futura (?P<demand>desconocida|estable|inestable) y rightsizing '
        r'(?P<sizing>pendiente|completado)[.] No se aportan precios ni terminos de contratacion[.]?', parts[1], re.I)
    if scenario is None or any(source.get('kind') != 'corpus'
                               for source in getattr(catalog, 'authorized_sources', ())):
        return None
    section = _section(catalog, 'Azure Advisor, Rightsizing Y Commitments')
    if section is None:
        return None
    sentences = re.split(r'(?<=[.!?])\s+', section['body'])
    advice = [sentence for sentence in sentences if re.fullmatch(
        r'Antes de comprar commitments (?:conviene|se recomienda|se aconseja) aplicar rightsizing '
        r'y confirmar una base de uso estable[.]', sentence)]
    definition = [sentence for sentence in sentences if re.fullmatch(
        r'Un commitment es un compromiso financiero a cambio de descuento, como Reservations o Savings Plans[.]', sentence)]
    # Compile this complete policy grammar, not two sentences cherry-picked
    # from a policy that might add an exception or reverse their application.
    if (len(advice) != 1 or len(definition) != 1 or len(sentences) != 4
            or not re.fullmatch(r'Azure Advisor puede ser una fuente de seniales(?:, pero no una orden automatica)?[.]', sentences[0])
            or not re.fullmatch(r'Antes de aplicar rightsizing hay que validar [^.!?;]{1,170}[.]', sentences[1])
            or sentences[2] != definition[0] or sentences[3] != advice[0]):
        return None
    chosen = _selections(section, [sentences[1], definition[0], advice[0]])
    if chosen is None:
        return None
    selected, records = chosen
    ref = 'user:' + hashlib.sha256(question.encode()).hexdigest()
    stable = {'desconocida': None, 'estable': True, 'inestable': False}[scenario['demand']]
    complete = scenario['sizing'] == 'completado'
    premises = {'stable_future_demand': Premise(stable, () if stable is None else (ref,)),
                'rightsizing_complete': Premise(complete, (ref,))}
    readiness = evaluate({'all': [{'premise': key} for key in premises]}, premises)
    answer = ('Escenario hipotético aportado; no verificado financieramente.\n'
              'La fuente ofrece esta definición y recomendación, conservadas literalmente:\n'
              + _quotations(selected, records)
              + '\nMigración declarada: ' + scenario['when'] + '. Rightsizing declarado: ' + scenario['sizing'] + '.\n')
    if stable is None:
        answer += ('La demanda futura es desconocida. No se concluye que la base de uso sea estable '
                   'ni que sea inestable o inexistente.\n')
    else:
        answer += 'La demanda futura se declara ' + scenario['demand'] + ' en el escenario; no se ha verificado.\n'
    actions = []
    if not complete:
        actions.append('Completar el rightsizing pendiente y revisar su efecto en la demanda antes de valorar el compromiso.')
    if stable is not True:
        actions.append('Confirmar una base de uso estable para el recurso o capacidad que podría consumir el compromiso tras la migración.')
    actions.append('Obtener precios y términos de contratación, y evaluar la utilización esperada y el ahorro antes de decidir la compra.')
    answer += ('Recomendación para este escenario: aplazar la compra inmediata y resolver los puntos pendientes. '
               'La recomendación documental no se convierte en una obligación adicional.\n'
               'Riesgo condicional: si la capacidad comprometida no se consume, puede haber infrautilización '
               'y gasto sin uso. La migración prevista no demuestra que la VM desaparezca ni que toda '
               'la capacidad vaya a quedar sin uso. No se aportan precios ni términos: no se cuantifica '
               'descuento, plazo óptimo, retorno ni ahorro. No se realiza ninguna compra.\n'
               + '\n'.join(actions))
    return {'topic': 'commitment', 'section': section, 'selections': selected, 'sources': records,
            'premises': {key: premise.value for key, premise in readiness.premises.items()},
            'readiness': readiness.value,
            'public_fields': {'answer': answer, 'status': 'insufficient_data', 'next_actions': actions}}


def required_documentary_answer(catalog):
    question = getattr(catalog, 'classification_question', '')
    bound = _cost_basis(catalog, question) or _commitment(catalog, question) or _investigation(catalog, question)
    if bound is None or len(bound['public_fields']['answer']) > 4000:
        return None
    bound['id'] = hashlib.sha256(json.dumps({'question': question, 'binding': bound},
        ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return bound


def _investigation(catalog, question):
    from app.core.chat_policy_sections import policy_topic
    if policy_topic(question) != 'cost_investigation':
        return None
    if any(source.get('kind') != 'corpus' for source in getattr(catalog, 'authorized_sources', ())):
        return None
    if any(any(p.get('kind') == 'user' for p in item.get('provenance', ())) for item in catalog.values()):
        return None  # Numeric scenarios need their own analysis, not a missing-data answer.
    section = _section(catalog, 'Cost Management Y Cost Analysis')
    if section is None:
        return None
    match = re.search(r'Metodo basico para investigar un aumento de costes:\s*(.+)$', section['body'])
    if match is None:
        return None
    steps = re.split(r'\s+(?=[1-9][0-9]?[.]\s)', match[1])
    if not 1 <= len(steps) <= 12:
        return None
    clauses = []
    for index, step in enumerate(steps, 1):
        parsed = re.fullmatch(str(index)+r'[.]\s+([^;]{1,210}[.])', step)
        if parsed is None:
            return None
        clauses.append(parsed[1])
    chosen = _selections(section, clauses)
    if chosen is None:
        return None
    selected, records = chosen
    actions = ['Indicar período, suscripción o ámbito, moneda, baseline y desglose de costes para investigar el aumento.']
    answer = ('No se ha establecido la causa del aumento. Para contrastarlo, indique período, '
              'suscripción o ámbito, moneda, baseline y desglose de costes.\n'
              'Método de investigación documentado:\n' + _quotations(selected, records)
              + '\nEstos pasos orientan la investigación; no prueban una causa concreta ni convierten '
              'los campos de un modelo conceptual en requisitos previos para empezar a investigar.')
    return {'topic': 'cost_investigation', 'section': section, 'selections': selected,
            'sources': records, 'public_fields': {'answer': answer, 'status': 'insufficient_data', 'next_actions': actions}}


def documentary_answer(value, catalog):
    bound = required_documentary_answer(catalog)
    if bound is None or value != {'documentary_answer': bound['id']}:
        raise ValueError('Documentary answer is not grounded.')
    return copy.deepcopy(bound['public_fields']), copy.deepcopy(bound['sources'])
