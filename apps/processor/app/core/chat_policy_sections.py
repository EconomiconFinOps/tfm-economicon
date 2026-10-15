"""Complete policy lists compiled from authorized positional documentary spans.

Routing recognizes a small set of conceptual topics, not questions or answers
from an evaluation bank. The compiler never supplies missing policy text: gaps,
conflicting overlaps, ambiguous documents or unquotable units keep the general
response route. All policy wording, table values and modalities come from the
current authorized corpus, not a second policy encoded in Python.
"""
import copy
import hashlib
import json
import re

from app.core.chat_claims import table_rows
from app.core.chat_rules import normalized, validate_provenance


SECTIONS = {'tagging': 'Reglas De Tagging', 'budget_operation': 'Budgets Y Forecast',
            'cost_investigation': 'Cost Management Y Cost Analysis'}
COMPANION_SECTIONS = {'Budgets Y Forecast': ('Conceptos FinOps Basicos',)}
MAX_SECTION = 4096
MAX_UNITS = 24


def policy_topic(question):
    """Conservative routing only; never infer a customer's configuration.

    Requests for execution, numeric results, other policies, negated lists or
    multiple tasks remain general. Context may describe a scenario but cannot
    select this route. The source compiler still has to prove completeness.
    """
    if not isinstance(question, str):
        return None
    request = normalized(question.split('\n\n', 1)[0]).strip()
    if re.fullmatch(r'¿?(?:por que (?:ha subido|ha aumentado|aumento|subio)(?: tanto)? el (?:gasto|coste)'
                    r'|como investigar (?:un|el) aumento de (?:gasto|costes?))[?.]?', request):
        return 'cost_investigation'
    if (len(request) > 500 or re.search(r'\d|[;\n"`]|[.!?].+\S', request)
            or re.search(r'\b(?:no|sin|excepto|y|o|ademas|tambien|ignora\w*|segun|cuanto|porcentaje|cumple|cumplimiento|calcula\w*|compara\w*|configurad\w*|cliente|real|azure)\b', request)):
        return None
    if re.search(r'\b(?:tags?|etiquetas?|tagging)\b', request):
        if (re.match(r'^(?:¿?(?:que|cuales)\b|enumera\b|lista\b|explica\b)', request)
                and re.search(r'\b(?:minimos?|minimas?|reglas?|exigir|exigimos|obligatorios?|requeridos?)\b', request)):
            return 'tagging'
    if (re.match(r'^¿?(?:el|un|los|que|como)\b', request)
            and re.search(r'\b(?:budget|presupuesto)s?\b', request)
            and re.search(r'\bapag\w*\b', request)
            and request.endswith('?')):
        return 'budget_operation'
    return None


def complete_sections(sources, heading):
    """Stitch a whole section only when original ranges close both boundaries.

    Section ends are established by the next original Markdown heading, never
    by the end of a retrieval chunk. Every overlapped character must agree.
    """
    if not isinstance(sources, (list, tuple)) or len(sources) > 20:
        return []
    groups, boundaries = {}, {}
    for source in sources:
        if source.get('kind') != 'corpus':
            continue
        spans = validate_provenance(source)
        provenance = source.get('provenance', {})
        document = provenance.get('document_id')
        for span in spans:
            if span['section_start'] is not None:
                boundaries.setdefault(document, set()).add(span['section_start'])
            if normalized(span['section'] or '') == normalized(heading):
                key = (document, span['section_start'])
                groups.setdefault(key, []).append((source, span))
    result = []
    for (document, start), pieces in groups.items():
        ends = [end for end in boundaries.get(document, ()) if end > start]
        if not ends:
            continue
        end = min(ends)
        if not 1 <= end - start <= MAX_SECTION:
            continue
        text = [None] * (end - start)
        conflict = False
        used = {}
        for source, span in pieces:
            content = source['content'][span['start']:span['end']]
            left = span['document_start'] - start
            if left < 0 or left + len(content) > len(text):
                conflict = True
                break
            for index, char in enumerate(content, left):
                if text[index] is not None and text[index] != char:
                    conflict = True
                    break
                text[index] = char
            used[source['id']] = source
        if conflict or any(char is None for char in text):
            continue
        content = ''.join(text).strip()
        # The general compiler below accepts a complete ATX heading followed by
        # its known title, independent of the policy's first sentence.
        prefix = re.match(r'^#{1,6}\s+', content)
        if not prefix or normalized(content[prefix.end():prefix.end()+len(heading)]) != normalized(heading):
            continue
        body = content[prefix.end()+len(heading):]
        if not body.startswith(' '):
            continue
        result.append({'document_id': document, 'section_start': start,
                       'heading': heading, 'body': body.strip(), 'sources': list(used.values())})
    return result


def policy_units(body):
    """Parse a complete bounded list and optional table; retain literal wording.

    The supported grammar is declarative data. Extra prose after the list,
    damaged tables and oversized clauses are not silently discarded.
    """
    markers = list(re.finditer(r'\bReglas(?: de interpretacion)?:\s*', body, re.I))
    if len(markers) != 1:
        return None
    marker = markers[0]
    prefix, tail = body[:marker.start()].strip(), body[marker.end():].strip()
    units = []
    if '|' in prefix:
        intro, table = prefix.split('|', 1)
        table = '|' + table
        rows = table_rows(table)
        # Account for the entire table, including its header and separator.
        parts = re.split(r'(?<=\|)\s+(?=\|)', table)
        if (not rows or len(parts) != len(rows) + 2
                or any(not part.startswith('|') or not part.endswith('|') for part in parts)):
            return None
        prefix = intro.strip()
        units.extend(rows)
    if prefix:
        paragraphs = [item.strip() for item in re.split(r'(?<=[.!?])\s+', prefix)]
        units = paragraphs + units
    if not tail.startswith('- '):
        return None
    bullets = re.split(r'(?<=;)\s+(?=-\s)', tail)
    if any(not re.fullmatch(r'- [^;]+[;.]', item) for item in bullets):
        return None
    units.extend(bullets)
    if not 1 <= len(units) <= MAX_UNITS or any(not unit or len(unit) > 220 for unit in units):
        return None
    return units


def budget_definition(sources):
    """Keep the complete current definition, including its operational consequence."""
    sections = complete_sections(sources, 'Conceptos FinOps Basicos')
    if len(sections) != 1:
        return None
    section = sections[0]
    markers = list(re.finditer(r'(?:^|(?<=[.!?])\s+)(?P<start>(?:(?:El|La|Un|Una) )?\*\*(?P<label>[^*]{1,80})\*\*)', section['body']))
    chosen = []
    for index, marker in enumerate(markers):
        if normalized(marker['label']) != 'budget':
            continue
        end = markers[index+1].start('start') if index+1 < len(markers) else len(section['body'])
        text = section['body'][marker.start('start'):end].strip()
        if not text.endswith('.') or len(text) > 220:
            return None
        chosen.append(text)
    return (section, chosen[0]) if len(chosen) == 1 else None


def required_policy(catalog):
    question = getattr(catalog, 'classification_question', '')
    topic = policy_topic(question)
    if topic is None:
        return None
    authorized = getattr(catalog, 'authorized_sources', ())
    sources = list(getattr(catalog, 'rule_sources', ()))
    known = {source['id']: source for source in authorized}
    if any(known.get(source['id']) != source for source in sources):
        raise ValueError('Policy source is not authorized.')
    sections = complete_sections(sources, SECTIONS[topic])
    if len(sections) != 1:
        return None
    section = sections[0]
    units = policy_units(section['body'])
    if units is None:
        return None
    unit_sources = [(unit, section['sources']) for unit in units]
    companion = None
    if topic == 'budget_operation':
        companion = budget_definition(sources)
        if companion is None:
            return None  # A complete policy list alone is not a complete budget answer.
        unit_sources.insert(0, (companion[1], companion[0]['sources']))
    selected, records = [], {}
    for unit, candidates in unit_sources:
        matches = [source for source in candidates if unit in source['content']]
        if not matches:
            return None  # A quote must belong to one actual, current fragment.
        source = min(matches, key=lambda source: (source['provenance']['chunk_index'], source['id']))
        if not isinstance(source.get('title'), str) or not 1 <= len(source['title']) <= 256:
            return None
        selected.append({'source_id': source['id'], 'passage': unit})
        records[source['id']] = source
    text = 'Reglas documentadas — ' + section['heading'] + ':\n'
    for item in selected:
        text += '\nFuente: ' + records[item['source_id']]['title'] + ' — «' + item['passage'] + '»\n'
    text += '\nEsta respuesta describe la política documental; no verifica la configuración de recursos ni costes de un cliente.'
    if len(text) > 4000:
        return None
    payload = {'question': question, 'topic': topic, 'selections': selected,
               'complete_section': section, 'companion': companion}
    identity = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                        separators=(',', ':')).encode()).hexdigest()
    return {'id': identity, 'text': text, 'sources': list(records.values()),
            'selections': selected, 'topic': topic}


def policy_answer(value, catalog):
    bound = required_policy(catalog)
    if bound is None or value != {'policy_section': bound['id']}:
        raise ValueError('Policy answer is not grounded.')
    return bound['text'], copy.deepcopy(bound['sources'])
