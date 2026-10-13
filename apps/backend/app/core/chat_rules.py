"""Closed documentary interval grammar; no inferred financial authority.

Only explicit percentage formulas and complete interval partitions qualify.
Source ranges come from the original Markdown parser, never model headings.
"""
import hashlib
import json
import re
import unicodedata
from decimal import Decimal


class QuantityCatalog(dict):
    rules = ()
    rule_sources = ()
    classification_requested = False


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def classification_request(question):
    """Conservative lexical routing of the current request, never retrieved text.

    Only the first paragraph is a request candidate; subsequent supplied context
    cannot force a response variant. Ambiguous/conceptual/negated wording retains
    narrative capability. This is routing, not inferred financial authority.
    """
    request = normalized(question.split('\n\n', 1)[0])
    if re.search(r'\b(?:sin\s+(?:un\s+)?semaforo|no\s+(?:lo\s+)?clasifi\w*|without\s+(?:a\s+)?traffic|do\s+not\s+classif\w*)', request):
        return False
    if re.search(r'\b(?:significa|significado|definicion|define|meaning|definition|what\s+is|que\s+es|como\s+funciona)\b', request):
        return False
    return bool(re.search(r'(?:^|[¿?!.]\s*)(?:por\s+favor[, ]+)?(?:clasifica\b|classify\b)', request)
                or re.search(r'\b(?:que|cual|what|which)\b[^?!.]{0,100}\b(?:semaforo|clasificacion|classification|traffic[- ]light)\b', request))


def applicable_rules(catalog):
    return [rule for rule in getattr(catalog, 'rules', ()) if any(
        len(entry.get('concept_anchors', [])) == 1
        and tuple(entry['concept_anchors'][0]) == tuple(rule['anchor'])
        for entry in catalog.values())]


def required_classification(catalog):
    if not getattr(catalog, 'classification_requested', False):return False
    rules=applicable_rules(catalog)
    if len(rules)!=1:return False
    return sum(len(entry.get('concept_anchors', [])) == 1
        and tuple(entry['concept_anchors'][0]) == tuple(rules[0]['anchor'])
        and any(origin.get('kind')=='user' for origin in entry.get('provenance', []))
        for entry in catalog.values()) == 1


def concept(value):
    # This is lexical identity, not a synonym/translation or inferred KPI.
    words = re.findall(r'[a-z]+', normalized(value))
    return tuple(w for w in words if w not in {'cost', 'coste', 'costo', 'percentage', 'porcentaje', 'of', 'de', 'the', 'el'})


def validate_provenance(source):
    provenance = source.get('provenance')
    if provenance is None:
        return []  # Historical fixtures have no authoritative section spans.
    if not isinstance(provenance, dict) or set(provenance) != {'document_id', 'chunk_index', 'sections'}:
        raise ValueError('Invalid documentary provenance.')
    if not isinstance(provenance['document_id'], str) or not provenance['document_id'] or type(provenance['chunk_index']) is not int or provenance['chunk_index'] < 0:
        raise ValueError('Invalid documentary provenance.')
    sections = provenance['sections']
    if not isinstance(sections, list) or len(sections) > 64:
        raise ValueError('Invalid documentary sections.')
    end = 0
    for span in sections:
        if not isinstance(span, dict) or set(span) != {'start', 'end', 'section', 'document_start', 'section_start'}:
            raise ValueError('Invalid documentary section.')
        if type(span['start']) is not int or type(span['end']) is not int or span['start'] != end or not end < span['end'] <= len(source['content']):
            raise ValueError('Invalid documentary section range.')
        if span['section'] is not None and (not isinstance(span['section'], str) or not 1 <= len(span['section']) <= 500):
            raise ValueError('Invalid documentary section title.')
        if type(span['document_start']) is not int or span['document_start'] < span['start']:
            raise ValueError('Invalid documentary absolute range.')
        if span['section'] is None:
            if span['section_start'] is not None:raise ValueError('Invalid documentary heading identity.')
        elif type(span['section_start']) is not int or not 0 <= span['section_start'] <= span['document_start']:
            raise ValueError('Invalid documentary heading identity.')
        if sections and span['document_start']-span['start'] != sections[0]['document_start']:
            raise ValueError('Inconsistent documentary absolute range.')
        end = span['end']
    if sections and end != len(source['content']):
        raise ValueError('Incomplete documentary section ranges.')
    return sections


FORMULA = re.compile(r'KPI:\s*(?:```(?:text)?\s*)?([^=;`]{1,100})\s*=\s*([^/;`]{1,100})\s*/\s*([^*;`]{1,100})\s*\*\s*100\b', re.I)
LABEL = re.compile(r'(?:^|\s)-\s+([\wáéíóúñ -]{1,40}):\s*([^;]*?)(?=;|\.(?:\s|$)|\s+-\s+[\wáéíóúñ -]{1,40}:|$)', re.I)
BOUND = re.compile(r'(menor o igual a|mayor o igual a|menor que|mayor que|less than or equal to|greater than or equal to|less than|greater than|<=|>=|≤|≥|<|>)\s*(-?\d+(?:[.,]\d+)?)\s*(%)', re.I)


def intervals(text):
    result = []
    for match in LABEL.finditer(text):
        label, clause = match.groups()
        pieces = re.split(r'\s+(?:y|and)\s+', clause.strip(), flags=re.I)
        bounds = []
        for piece in pieces:
            parsed = BOUND.fullmatch(piece.strip())
            if not parsed:
                bounds = []; break
            operator, number, unit = parsed.groups()
            value = Decimal(number.replace(',', '.'))
            if abs(value) > Decimal('1e12') or len(number) > 26:
                bounds = []; break
            operator = normalized(operator)
            lower = operator.startswith(('mayor', 'greater')) or operator in ('>', '>=', '≥')
            inclusive = 'igual' in operator or 'equal' in operator or operator in ('<=', '>=', '≤', '≥')
            bounds.append({'side': 'lower' if lower else 'upper', 'value': str(value), 'inclusive': inclusive})
        if not 1 <= len(bounds) <= 2 or len({b['side'] for b in bounds}) != len(bounds):
            continue
        result.append({'label': label.strip(), 'bounds': bounds, 'literal': match.group().strip()})
    return result


def partition(rows):
    if not 2 <= len(rows) <= 8 or len({row['label'].casefold() for row in rows}) != len(rows):
        return None
    def bound(row, side):
        return next((b for b in row['bounds'] if b['side'] == side), None)
    rows = sorted(rows, key=lambda r: Decimal(bound(r, 'lower')['value']) if bound(r, 'lower') else Decimal('-Infinity'))
    if bound(rows[0], 'lower') or bound(rows[-1], 'upper'):
        return None
    for row in rows:
        lo, hi = bound(row, 'lower'), bound(row, 'upper')
        if lo and hi and Decimal(lo['value']) >= Decimal(hi['value']):
            return None
    for left, right in zip(rows, rows[1:]):
        hi, lo = bound(left, 'upper'), bound(right, 'lower')
        if not hi or not lo or Decimal(hi['value']) != Decimal(lo['value']) or hi['inclusive'] == lo['inclusive']:
            return None
    return rows


def documentary_rules(sources):
    groups = {}
    for source in sources:
        for span in validate_provenance(source):
            if span['section'] is None:continue
            key = (source['provenance']['document_id'], span['section_start'])
            groups.setdefault(key, []).append({'source_id':source['id'],'section':span['section'],
                'start':span['document_start'],'text':source['content'][span['start']:span['end']]})
    rules = []
    for (document, section_start), parts in groups.items():
        parts.sort(key=lambda p:p['start'])
        if len({p['section'] for p in parts})!=1:continue
        start=parts[0]['start'];joined='';valid=True
        for part in parts:
            relative=part['start']-start
            if relative>len(joined):valid=False;break
            overlap=min(len(joined)-relative,len(part['text']))
            if joined[relative:relative+overlap]!=part['text'][:overlap]:valid=False;break
            joined+=part['text'][overlap:]
        if not valid:continue
        formulas=list(FORMULA.finditer(joined))
        if len(formulas)!=1 or len(re.findall(r'\bKPI\s*:',joined,re.I))!=1:continue
        formula=formulas[0]
        metric,numerator,denominator=(v.strip() for v in formula.groups())
        if '%' not in metric or not concept(numerator):continue
        candidates=list(LABEL.finditer(joined))
        # Unsupported/truncated rows in this list cannot be silently discarded.
        rows=intervals(joined)
        if len(rows)!=len(candidates) or len(candidates)!=len(re.findall(r'(?:^|\s)-\s+',joined)):continue
        rows=partition(rows)
        if rows is None:continue
        source_ids=set()
        for match in [formula,*candidates]:
            left,right=start+match.start(),start+match.end()
            containing=[p for p in parts if p['start']<=left and p['start']+len(p['text'])>=right]
            if containing:source_ids.add(containing[0]['source_id'])
            else:source_ids.update(p['source_id'] for p in parts if p['start']<right and p['start']+len(p['text'])>left)
        section=parts[0]['section']
        identity=json.dumps([document,section_start,metric,rows],sort_keys=True,ensure_ascii=False)
        rules.append({'id':'interval:'+hashlib.sha256(identity.encode()).hexdigest()[:24],
            'metric':metric,'section':section,'section_start':section_start,
            'numerator':numerator,'denominator':denominator,'anchor':concept(numerator),
            'unit':'%','intervals':rows,'source_ids':sorted(source_ids)})
    return rules[:16]


def numerator_matches(node, catalog, rule):
    if not isinstance(node, dict) or node.get('operation') != 'percentage':
        return False
    numerator = node.get('numerator')
    if not isinstance(numerator, dict) or set(numerator) != {'quantity'}:
        return False
    if not isinstance(numerator['quantity'],str):return False
    entry = catalog.get(numerator['quantity'], {})
    anchors = entry.get('concept_anchors', [])
    return len(anchors) == 1 and tuple(anchors[0]) == tuple(rule['anchor'])


def check_classification_prose(text, rules, sources):
    """Reject explicit free-form classification conclusions, not generic words.

    Literal documentary excerpts are allowed and require their source citation.
    This is a bounded conclusion guard, not universal natural-language entailment.
    """
    cited = set()
    for sentence in re.split(r'(?<=[.!?])\s+|\n', text):
        if not re.search(r'\b(?:semaforo|clasific\w*|franja|nivel|rango|categoria)\b', normalized(sentence)):
            continue
        labels = {row['label'] for rule in rules for row in rule['intervals']}
        variants={normalized(label) for label in labels}
        variants.update(value[:-1]+'a' for value in list(variants) if value.endswith('o'))
        if not any(re.search(r'(?<!\w)' + re.escape(label) + r'(?!\w)', normalized(sentence)) for label in variants):
            continue
        matches = [source['id'] for source in sources if sentence.strip() and sentence.strip() in source['content']]
        if not matches:
            raise ValueError('Unverified documentary classification prose.')
        cited.update(matches)
    return cited
