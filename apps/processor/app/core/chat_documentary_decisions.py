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
    bound = (_allocation(catalog, question) or _cost_basis(catalog, question) or _commitment(catalog, question)
             or _rightsizing(catalog, question) or _investigation(catalog, question))
    if bound is None or len(bound['public_fields']['answer']) > 4000:
        return None
    bound['id'] = hashlib.sha256(json.dumps({'question': question, 'binding': bound},
        ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return bound


def _allocation(catalog, question):
    """Separate tag presence, policy compliance and allocation sufficiency.

    Only a closed, affirmative user scenario establishes a hypothetical mapping.
    A missing/negated/ambiguous mapping is unknown, never unallocated by default.
    Unknown source policy cannot establish even the documentary classification.
    This is not a general natural-language rule extractor or a tenant lookup.
    """
    parts = question.split('\n\n')
    key = r'[a-z][a-z0-9_-]{0,39}'
    request = re.fullmatch(
        rf'¿?(?:un|este) recurso sin (?:el tag |la etiqueta )?(?P<tag>{key}) '
        r'es (?:necesariamente|siempre) (?:coste no asignado|unallocated)[?.]?',
        normalized(parts[0]))
    if request is None:
        return None
    tag = request['tag']
    # Reserved words cannot stand for a tag or mapping key in this grammar.
    reserved = {'no', 'sin', 'ninguno', 'nadie', 'desconocido', 'ninguna', 'null'}
    if tag in reserved:
        return None
    scenario = None
    if len(parts) == 2:
        # A quoted multiword name is an opaque identifier; unquoted prose,
        # conjunctions, appended conditions and instructions are not names.
        name = r'(?:[a-z0-9][a-z0-9_-]{0,59}|`[a-z0-9][a-z0-9 _-]{0,59}`)'
        scenario = re.fullmatch(
            rf'(?:contexto del escenario:\s*)?(?:escenario sintetico:\s*)?'
            rf'(?:falta el tag|falta la etiqueta|no existe el tag) (?P<tag>{key}), '
            r'pero una regla documentada asigna inequivocamente (?:el|este) recurso '
            rf'(?P<unit>al equipo|a la aplicacion|al cost center|a la unidad responsable) (?P<name>{name}) '
            rf'(?:mediante|a traves de) (?P<via>{key})[.]?', normalized(parts[1]))
    mapped = bool(scenario and scenario['tag'] == tag and scenario['via'] != tag
                  and scenario['via'] not in reserved and scenario['name'].strip('`') not in reserved
                  and not any(s.get('kind') != 'corpus' for s in getattr(catalog, 'authorized_sources', ())))
    section = _section(catalog, 'Coste No Asignado Y Coste Compartido')
    selected, records = [], []
    if section is not None:
        # Recognize the WHOLE supported policy, including shared/excluded;
        # accepting only a matching allocated bullet could drop an exception.
        grammar = (
            r'El (?P<definition>coste no asignado es coste que no puede asociarse con informacion suficiente '
            r'a un owner, aplicacion, cost center u otra unidad responsable[.]) '
            r'No debe confundirse con coste compartido[.] '
            r'Un coste puede ser compartido y estar identificado; unallocated significa que falta informacion suficiente[.] '
            r'Estados recomendados: (?P<allocated>- `allocated`: responsable conocido;) '
            r'- `shared`: coste compartido conocido; - `unallocated`: sin informacion suficiente; '
            r'- `excluded`: excluido por regla documentada[.]')
        policy = re.fullmatch(grammar, section['body'])
        chosen = _selections(section, [policy['definition'], policy['allocated']]) if policy else None
        if chosen is not None:
            selected, records = chosen
    policy_known = bool(selected)
    allocated = mapped and policy_known
    answer = ('La presencia de una etiqueta, el cumplimiento de la política de tagging y la capacidad '
              'de asignar un coste son cuestiones distintas. No se ha evaluado si la clave ' + tag
              + ' es obligatoria ni si cumple la política de etiquetado.\n')
    if policy_known:
        answer += ('No necesariamente: la definición documental se refiere a información suficiente '
                   'para identificar al responsable, no sólo a la presencia de esa etiqueta.\n'
                   + _quotations(selected, records))
    else:
        answer += ('No se dispone de una sección documental completa, inequívoca y compatible '
                   'para establecer el estado de asignación.\n')
    actions = []
    if allocated:
        answer += ('Escenario hipotético aportado (declaración del usuario): «' + parts[1] + '»\n'
                   'Bajo esas premisas, corresponde allocated '
                   '(responsable conocido). Es una conclusión sobre el escenario declarado, '
                   'sin verificación del recurso, del tenant ni de la ejecución de la regla.\n')
    else:
        answer += ('No se establece allocated, shared, excluded ni unallocated para el recurso concreto: '
                   'la ausencia de la etiqueta no demuestra por sí sola falta de información suficiente, '
                   'y no se ha establecido una regla inequívoca aplicable a este escenario.\n')
        actions = ['Aportar la política completa y la regla aplicable que identifique inequívocamente al responsable; '
                   'aclarar condiciones, contradicciones o alternativas pendientes.']
    answer += ('Una preferencia sobre el tipo de valor de owner (equipo o persona) no establece '
               'que la clave sea opcional, obligatoria o preferida frente a otros mecanismos de asignación.')
    return {'topic': 'allocation_sufficiency', 'section': section, 'selections': selected, 'sources': records,
            'premises': {'tag_absent': True if scenario and scenario['tag'] == tag else None,
                         'tag_compliance': None, 'documentary_policy': policy_known,
                         'declared_unambiguous_mapping': True if mapped else None},
            'allocation': 'allocated' if allocated else None,
            'public_fields': {'answer': answer, 'status': 'ok' if allocated else 'insufficient_data',
                              'next_actions': actions}}


def _rightsizing(catalog, question):
    parts = normalized(question).split('\n\n')
    if len(parts) != 2 or not re.fullmatch(
            r'¿?(?:reducimos ya el tamano de esta vm para ahorrar'
            r'|conviene reducir (?:esta|la) vm'
            r'|podemos hacer rightsizing (?:ahora|ya))[?.]?', parts[0]):
        return None
    scenario = re.fullmatch(
        r'(?:contexto del escenario:\s*)?escenario sintetico: cpu media (?P<cpu>[0-9]{1,3}(?:[.,][0-9]{1,6})?)\s*%, '
        r'sin datos de memoria, i/o, picos ni sla; coste [0-9]{1,12}(?:[.,][0-9]{1,6})? '
        r'(?:eur|usd|gbp|chf|cad|aud|jpy)/mes[.] '
        r'no existe recomendacion validada ni medicion de ahorro[.]?', parts[1])
    if scenario is None or float(scenario['cpu'].replace(',', '.')) > 100:
        return None
    if any(s.get('kind') != 'corpus' for s in getattr(catalog, 'authorized_sources', ())):
        return None
    section = _section(catalog, 'Azure Advisor, Rightsizing Y Commitments')
    if section is None:
        return None
    sentences = re.split(r'(?<=[.!?])\s+', section['body'])
    # A changed policy or an extra exception must be reviewed rather than
    # silently selecting one convenient sentence from it.
    expected = [
        r'Azure Advisor puede ser una fuente de seniales, pero no una orden automatica[.]',
        r'Antes de aplicar rightsizing hay que validar CPU, memoria, I/O, picos, SLA, crecimiento esperado y restricciones de negocio[.]',
        r'Un commitment es un compromiso financiero a cambio de descuento, como Reservations o Savings Plans[.]',
        r'Antes de comprar commitments conviene aplicar rightsizing y confirmar una base de uso estable[.]',
    ]
    if len(sentences) != len(expected) or any(not re.fullmatch(pattern, sentence)
                                                            for pattern, sentence in zip(expected, sentences)):
        return None
    chosen = _selections(section, sentences[:2])
    if chosen is None:
        return None
    selected, records = chosen
    actions = ['Obtener memoria, I/O, picos, SLA, crecimiento esperado y restricciones de negocio; contrastarlos con la CPU media aportada.',
               'Validar la hipótesis de dimensionamiento y su impacto en rendimiento y servicio antes de actuar, con revisión humana.']
    answer = ('Escenario hipotético aportado; no verificado financieramente. '
              'La CPU media aislada no valida reducir la VM: rightsizing es una hipótesis de adecuación de capacidad, '
              'no equivale siempre a reducir tamaño.\n'
              'La política documental exige estas comprobaciones:\n'+_quotations(selected, records)
              +'\nInterpretación para el escenario: al faltar memoria, I/O, picos y SLA, reducir capacidad podría '
              'degradar el rendimiento o el servicio y comprometer el SLA. Es un riesgo condicional, '
              'no una degradación observada ni una consecuencia garantizada. Hay que validar antes de actuar. '
              'No existe una recomendación validada ni una medición de ahorro; no se garantiza ni se cuantifica ahorro. '
              'No se ejecuta ningún cambio.\n'+'\n'.join(actions))
    return {'topic': 'rightsizing', 'section': section, 'selections': selected, 'sources': records,
            'public_fields': {'answer': answer, 'status': 'insufficient_data', 'next_actions': actions}}


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
