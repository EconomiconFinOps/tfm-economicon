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


class ClassificationProseError(ValueError):
    """No rejected prose is retained; only a closed public-field location."""
    def __init__(self, field=None, index=None):
        super().__init__('Unverified documentary classification prose.')
        self.field = field if field in {'answer','assumptions','limitations','next_actions','recommendations.action','recommendations.rationale'} else None
        self.index = index if type(index) is int and 0 <= index < 24 else None


def check_classification_prose(text, rules, sources):
    """Reject explicit free-form classification conclusions, not generic words.

    Literal documentary excerpts are allowed and require their source citation.
    This is a bounded conclusion guard, not universal natural-language entailment.
    """
    cited = set()
    labels = {row['label'] for rule in rules for row in rule['intervals']}
    # Partial authenticated interval rows can forbid an unsupported prose claim;
    # they never become executable rules without the complete formula/partition.
    for source in sources:
        for span in validate_provenance(source):
            labels.update(row['label'] for row in intervals(source['content'][span['start']:span['end']]))
    for sentence in re.split(r'(?<=[.!?])\s+|\n', text):
        if not re.search(r'\b(?:semaforo|clasific\w*|franja|intervalo|nivel|rango|categoria)\b', normalized(sentence)):
            continue
        variants={normalized(label) for label in labels}
        variants.update(value[:-1]+'a' for value in list(variants) if value.endswith('o'))
        if not any(re.search(r'(?<!\w)' + re.escape(label) + r'(?!\w)', normalized(sentence)) for label in variants):
            continue
        matches = [source['id'] for source in sources if sentence.strip() and sentence.strip() in source['content']]
        if not matches:
            raise ClassificationProseError()
        cited.update(matches)
    return cited


def allocation_denominator(catalog, users, rule):
    """Bind a closed allocation partition only with an explicit exclusion policy.

    Status names identify operands, never thresholds. All amounts must have one
    currency and distinct, unambiguous provenance. The trailing policy must
    explicitly exclude the stated amount and declare the remainder eligible.
    Unsupported prose or extra financial quantities retain the unresolved path.
    """
    if tuple(rule['anchor']) != ('unallocated',):
        return None
    statuses = ('allocated', 'shared', 'unallocated', 'excluded')
    money = {key: entry for key, entry in users.items() if entry['unit']}
    if len(money) != 4 or len({entry['unit'] for entry in money.values()}) != 1:
        return None
    bound = {}
    for status in statuses:
        matches = [(key, entry) for key, entry in money.items()
                   if entry.get('concept_anchors') == [[status]]]
        if len(matches) != 1 or Decimal(matches[0][1]['value']) < 0:
            return None
        bound[status] = matches[0]
    question = normalized(getattr(catalog, 'classification_question', ''))
    spans = []
    for status, (key, entry) in bound.items():
        # Match labelled entries, not a number mentioned elsewhere in prose.
        source = re.escape(normalized(entry['source']))
        currency = re.escape(normalized(entry['unit']))
        matches = list(re.finditer(r'(?<![\w-])' + status + r'\s*[:=]?\s+' + source
            + r'(?:\s+' + currency + r')?(?=\s*(?:;|[.!?]|$))', question))
        if len(matches) != 1:
            return None
        spans.append(matches[0])
    spans.sort(key=lambda match: match.start())
    # Only separators may occur between the four entries. A second scenario,
    # qualification, or an intervening instruction cannot become a partition.
    if any(question[a.end():b.start()].strip() != ';' for a, b in zip(spans, spans[1:])):
        return None
    tail = question[spans[-1].end():].strip()
    excluded = bound['excluded'][1]
    amount = re.escape(normalized(excluded['source']))
    unit = re.escape(normalized(excluded['unit']))
    policy = (r'[.;]\s*(?:(?:la regla(?: del escenario)? )?excluye (?:esos )?'
        + amount + r'(?:\s+' + unit + r')? del coste elegible;\s*el resto es elegible'
        + r'|excluded is excluded from eligible cost;\s*the remainder is eligible)[.]?')
    if not re.fullmatch(policy, tail):
        return None
    if sum(Decimal(bound[name][1]['value']) for name in statuses[:3]) <= 0:
        return None
    leaf = lambda name: {'quantity': bound[name][0]}
    return {'operation': 'sum', 'left': leaf('allocated'), 'right': {
        'operation': 'sum', 'left': leaf('shared'), 'right': leaf('unallocated')}}


def resolved_classification(catalog):
    """Bind an explicit eligible total before removing the abstention branch.

    Accept an explicitly labelled eligible total or a closed allocation
    partition with an explicit exclusion policy. Ambiguity retains the fallback.
    """
    if not required_classification(catalog):
        return None
    rule = applicable_rules(catalog)[0]
    if normalized(rule['denominator']).strip() not in {
        'eligible cost', 'total eligible cost', 'coste elegible', 'coste total elegible',
    }:
        return None
    question = getattr(catalog, 'classification_question', '')
    users = {key: entry for key, entry in catalog.items()
             if any(p.get('kind') == 'user' for p in entry.get('provenance', []))}
    numerators = [(key, entry) for key, entry in users.items()
                  if entry.get('concept_anchors') == [list(rule['anchor'])]]
    if len(numerators) != 1:
        return None
    numerator, n = numerators[0]
    if n['unit'] not in {'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR'}:
        return None
    money = {key: entry for key, entry in users.items()
             if entry['unit'] and entry['unit'] != '%'}
    if len(money) != 2:
        denominator = allocation_denominator(catalog, users, rule)
        if denominator is None:
            return None
        return {'operation': 'classify', 'rule_id': rule['id'], 'value': {
            'operation': 'percentage', 'numerator': {'quantity': numerator},
            'denominator': denominator}}
    denominator, d = next((key, entry) for key, entry in money.items() if key != numerator)
    if d['unit'] != n['unit'] or not Decimal('0') <= Decimal(n['value']) <= Decimal(d['value']) or Decimal(d['value']) <= 0:
        return None
    # Duplicate amounts can denote distinct periods/entities; deduplication in
    # the quantity catalog must not turn them into a unique scenario.
    spans = {}
    for key, entry in ((numerator, n), (denominator, d)):
        matches = list(re.finditer(r'(?<![\w.,])' + re.escape(entry['source']) + r'(?!\w)', question, re.I))
        if len(matches) != 1:
            return None
        spans[key] = matches[0]
    suffix = normalized(question[spans[denominator].end():])
    if not re.match(r'\s+(?:elegibles|de coste (?:total )?elegible|(?:total )?eligible cost)\s*(?=y\b|and\b|[;.!?]|$)', suffix):
        return None
    return {'operation': 'classify', 'rule_id': rule['id'], 'value': {
        'operation': 'percentage', 'numerator': {'quantity': numerator},
        'denominator': {'quantity': denominator}}}



def required_zero_percentage(catalog):
    """Closed unallocated/eligible ratio with a verified formula and zero total.

    A complete percentage formula is enough to explain undefined division; no
    interval classification is inferred from a missing/truncated threshold list.
    """
    from app.core.chat_expressions import canonical_decimal, normalized_unit
    question = getattr(catalog, 'classification_question', '')
    request = normalized(question.split('\n\n', 1)[0])
    if not re.fullmatch(r'[¿]?[^?!.;\n]+[?!.]?', request):
        return None
    if re.search(r'\b(?:y|and|ademas|also|not|define|definicion|significa|no\s+(?:calcules|quiero))\b', request):
        return None
    if not (re.search(r'\b(?:porcentaje|percentage|percent)\b', request)
            and re.search(r'\b(?:sin asignar|no asignado|unallocated)\b', request)):
        return None
    if getattr(catalog, 'classification_requested', False) or getattr(catalog, 'boolean_requested', False):
        return None
    source_ids = []
    for source in getattr(catalog, 'rule_sources', ()):
        for span in validate_provenance(source):
            if span['section'] is None:
                continue
            text = source['content'][span['start']:span['end']]
            for formula in FORMULA.finditer(text):
                metric, numerator, denominator = (normalized(v.strip()) for v in formula.groups())
                if concept(numerator) != ('unallocated',):
                    continue
                if '%' not in metric or denominator not in ('eligible cost', 'total eligible cost', 'coste elegible', 'coste total elegible'):
                    return None
                if source['id'] not in source_ids:
                    source_ids.append(source['id'])
    if not source_ids:
        return None
    pattern = re.compile(r'\b(total elegible|coste total elegible|total eligible cost|eligible cost|unallocated)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*(EUR|USD|GBP|JPY|CHF|CAD|AUD|CNY|INR)\b', re.I)
    matches = list(pattern.finditer(question))
    if len(matches) != 2:
        return None
    users = {key: entry for key, entry in catalog.items()
             if any(p.get('kind') == 'user' for p in entry.get('provenance', []))}
    roles = {}
    for match in matches:
        if re.search(r'\b(?:no|non|not|sin)\s*$', normalized(question[:match.start()])):
            return None
        role = 'numerator' if normalized(match[1]) == 'unallocated' else 'denominator'
        if role in roles:
            return None
        value = canonical_decimal(match[2]); unit = normalized_unit(match[3])
        keys = [key for key, entry in users.items() if entry['value'] == value and entry['unit'] == unit]
        if len(keys) != 1:
            return None
        roles[role] = keys[0]
    if set(roles) != {'numerator', 'denominator'}:
        return None
    n, d = users[roles['numerator']], users[roles['denominator']]
    if Decimal(d['value']) != 0 or Decimal(n['value']) < 0 or n['unit'] != d['unit']:
        return None
    if {key for key, entry in users.items() if entry['unit']} != set(roles.values()):
        return None
    return {'expression': {'operation': 'percentage', **{key: {'quantity': value} for key, value in roles.items()}},
            'source_ids': source_ids[:1]}
