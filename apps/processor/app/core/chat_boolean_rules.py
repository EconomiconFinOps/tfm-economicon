"""Closed, grounded two-condition change rules; no model-authored conclusions."""
import hashlib
import json
import re
from decimal import Decimal
from app.core.chat_rules import normalized, validate_provenance, explicit_quantity_roles, scenario_clauses, scenario_request

_NUMBER = r"-?\d+(?:[.,]\d+)?"
_UNIT = r"(?:%|[A-Za-z€£$¥]{1,8}(?:/(?:día|dia|day|hora|hour|mes|month))?)(?![\w/])"
_METRIC = r"(?:relative_delta|absolute_delta|delta\s+relativo|delta\s+absoluto|relativo|absoluto)"
_CONDITION = rf"({_METRIC})\s*(>=|<=|>|<|==|=|≥|≤)\s*({_NUMBER})\s*({_UNIT})"
_RULE = re.compile(_CONDITION + r"\s+(AND|OR|Y|O)\s+" + _CONDITION, re.I)
_ROLE = re.compile(r"\b(baseline|base|observado|observada|observed|current)\b(?:\s+(?:diario|diaria|daily))?(?:\s+el\s+\d{4}-\d{2}-\d{2})?\s*[:=]?\s*("+_NUMBER+r")\s*("+_UNIT+r")", re.I)


def _parse(text, *, complete=False):
    from app.core.chat_expressions import normalized_unit, canonical_decimal
    result=[]; offset=0
    for clause in scenario_clauses(text):
        start=text.index(clause, offset); offset=start+len(clause)
        literal = re.sub(r'(?i)^\s*(?:(?:regla(?:\s+MVP)?|aplicar|rule)\s*:?\s*)?', '', clause)
        match = _RULE.fullmatch(literal)
        if match is None:
            if complete:return []
            continue
        groups=match.groups(); conditions=[]
        for metric,operator,value,unit in (groups[:4],groups[5:]):
            metric='relative_change' if normalized(metric) in ('relative_delta','delta relativo','relativo') else 'difference'
            unit=normalized_unit(unit)
            if (metric=='relative_change') != (unit=='%'):break
            try:value=canonical_decimal(value)
            except ValueError:break
            conditions.append({'metric':metric,'relation':{'=':'eq','==':'eq','>':'gt','<':'lt','>=':'gte','<=':'lte','≥':'gte','≤':'lte'}[operator],'value':value,'unit':unit})
        if len(conditions)!=2 or {c['metric'] for c in conditions}!={'relative_change','difference'}:
            if complete:return []
            continue
        conditions.sort(key=lambda item:item['metric'])
        left=start+len(clause)-len(literal)
        result.append({'conditions':conditions,'combinator':'AND' if groups[4].upper() in ('AND','Y') else 'OR','literal':match.group(),'start':left,'end':left+len(literal)})
    return result


def boolean_catalog(question,sources,catalog):
    """Only explicit named deltas and explicitly labelled baseline/current pairs.

    Unsupported/ambiguous rules do not authorize a classification. A documentary
    rule must fit a verified section span; neighboring unrelated text is not its
    provenance. Identical semantics deduplicate; conflicting semantics disable
    the terminal rather than selecting a convenient rule.
    """
    from app.core.chat_expressions import normalized_unit, canonical_decimal
    if not boolean_request(question):
        return []
    candidates=[]
    for rule in _parse(question):candidates.append({**rule,'origin':'user','source_ids':[]})
    from app.core.chat_policy_sections import complete_sections
    headings={span['section'] for source in sources for span in validate_provenance(source)
              if span['section'] and re.fullmatch(
                  r'(?:Changes|Cambios|Rules?|Reglas?(?: MVP)?(?: de anomal[ií]as)?|Anomalies|Anomal[ií]as(?: de coste)?)',
                  span['section'], re.I)}
    for heading in headings:
        for section in complete_sections(sources, heading):
            for rule in _parse(section['body'], complete=True):
                candidates.append({**rule,'origin':'corpus',
                    'source_ids':[source['id'] for source in section['sources']]})
    grouped={}
    for candidate in candidates:
        identity=json.dumps([candidate['conditions'],candidate['combinator']],sort_keys=True)
        if identity not in grouped:grouped[identity]=candidate
        elif candidate['origin']=='user':grouped[identity]=candidate
        # A user-stated rule is sufficient; do not manufacture a documentary
        # citation to duplicate it. Identical corpus overlaps retain one source.
    if len(grouped)!=1:return []
    roles={'baseline':set(),'current':set()}
    matches = explicit_quantity_roles(question, _ROLE, extra_clause=lambda clause: bool(_parse(clause, complete=True)))
    for match in matches:
        role='baseline' if match[1].casefold() in ('baseline','base') else 'current'
        try:value=canonical_decimal(match[2])
        except ValueError:continue
        unit=normalized_unit(match[3])
        keys=[key for key,entry in catalog.items() if entry['value']==value
            and (entry['unit']==unit or (entry.get('binding')=='context_daily_rate' and entry['unit']==unit+'/día'))
            and any(p.get('kind')=='user' for p in entry.get('provenance',[]))]
        if len(keys)!=1:return []
        roles[role].add(keys[0])
    if any(len(values)!=1 for values in roles.values()):return []
    baseline=next(iter(roles['baseline']));current=next(iter(roles['current']))
    candidate=next(iter(grouped.values()))
    absolute=next(c for c in candidate['conditions'] if c['metric']=='difference')
    if catalog[baseline]['unit']!=catalog[current]['unit'] or catalog[current]['unit']!=absolute['unit']:return []
    identity=next(iter(grouped))
    return [{**candidate,'id':'boolean:'+hashlib.sha256(identity.encode()).hexdigest()[:24],
             'baseline':baseline,'current':current}]


def boolean_request(question):
    return scenario_request(question, 'boolean')


def boolean_definition(rules):
    variants=[]
    for rule in rules:
        props={name:{'type':'string','const':rule[name]} for name in ('baseline','current')}
        props['rule_id']={'type':'string','const':rule['id'],'description':json.dumps(rule,ensure_ascii=False)}
        variants.append({'type':'object','properties':props,'required':list(props),'additionalProperties':False})
    return variants[0] if len(variants)==1 else {'anyOf':variants}


def render_boolean(value,renderer):
    if not isinstance(value,dict) or set(value)!={'rule_id','baseline','current'}:raise ValueError('Boolean rule answer shape.')
    matches=[rule for rule in getattr(renderer.catalog,'boolean_rules',())
             if rule['id']==value['rule_id'] and all(rule[key]==value[key] for key in ('baseline','current'))]
    if len(matches)!=1:raise ValueError('Boolean rule not grounded.')
    rule=matches[0];renderer.documentary_sources.update(rule['source_ids'])
    pieces=[];outcomes=[]
    symbols={'gt':'>','gte':'>=','lt':'<','lte':'<=','eq':'=='}
    for condition in rule['conditions']:
        node={'operation':condition['metric'],'baseline':{'quantity':rule['baseline']},'current':{'quantity':rule['current']}}
        number,unit,formula,reason=renderer._numeric(node)
        renderer._count()
        label='Delta absoluto' if condition['metric']=='difference' else 'Delta relativo'
        if reason:
            pieces.append(label+': '+reason+'.');outcomes.append(None);continue
        if unit!=condition['unit']:raise ValueError('Boolean rule unit mismatch.')
        bound=Decimal(condition['value']);relation=condition['relation']
        valid={'gt':number>bound,'gte':number>=bound,'lt':number<bound,'lte':number<=bound,'eq':number==bound}[relation]
        exact=format(number,'f');exact=exact.rstrip('0').rstrip('.') if '.' in exact else exact
        pieces.append(label+': '+formula+' = '+exact+' '+unit+'. Condición: '+exact+' '+unit+' '+symbols[relation]+' '+condition['value']+' '+unit+' → '+('verdadero' if valid else 'falso')+'.')
        outcomes.append(valid)
    renderer._count()
    # Values enter the premise evaluator only after the grounded numeric
    # expressions above have been evaluated by the server. These references
    # identify comparisons, not extra documentary citations.
    from app.core.chat_premises import Premise, evaluate
    premises = {str(index): Premise(outcome, () if outcome is None else
                (rule['id'] + ':condition:' + str(index),))
                for index, outcome in enumerate(outcomes)}
    decision = evaluate({'all' if rule['combinator'] == 'AND' else 'any':
                         [{'premise': key} for key in premises]}, premises)
    result = decision.value
    conclusion='no se puede determinar' if result is None else 'se cumple' if result else 'no se cumple'
    pieces.append('Resultado '+rule['combinator']+': la regla '+conclusion+'.')
    pieces.append('Regla aportada por el usuario; escenario hipotético.' if rule['origin']=='user' else 'Regla documental aplicada al escenario hipotético.')
    if result is True:
        pieces.append('El resultado no demuestra una causa: investigue el cambio y confirme si era esperado.')
    elif result is None:
        pieces.append('Se necesita una base comparable con datos aplicables; investigue si el recurso o el consumo son nuevos.')
    return '\n'.join(pieces)



def required_zero_change(catalog):
    """Resolve an explicit baseline/current pair for a relative-change request.

    This terminal supplies the defined absolute difference even when division
    by the user's zero baseline is undefined. It does not infer a baseline,
    borrow documentary values, or decide whether an anomaly rule is satisfied.
    """
    from app.core.chat_expressions import normalized_unit, canonical_decimal
    question = getattr(catalog, 'classification_question', '')
    if not scenario_request(question, 'zero_change'):
        return None
    request = normalized(question.split('\n\n', 1)[0])
    if getattr(catalog, 'boolean_requested', False) or getattr(catalog, 'classification_requested', False):
        return None
    if not re.fullmatch(r'[¿]?[^?!.;\n]+[?!.]?', request) or re.search(r'\b(?:y|and|ademas|also)\b', request):
        return None
    if not (re.search(r'\b(?:porcentaje|percentage|percent|relativ[oa]s?|relative)\b', request)
            and re.search(r'\b(?:aument\w*|increment\w*|variacion|cambio|increase|change|growth)\b', request)):
        return None
    if re.search(r'\b(?:no|not|sin|without|define|definicion|significa|meaning)\b', request):
        return None
    users = {key: entry for key, entry in catalog.items()
             if any(p.get('kind') == 'user' for p in entry.get('provenance', []))}
    matches = explicit_quantity_roles(question, _ROLE,
        extra_clause=lambda clause: normalized(clause) in ('sin historial previo', 'no hay historial previo'))
    if len(matches) != 2:
        return None
    roles = {}
    for match in matches:
        role = 'baseline' if match[1].casefold() in ('baseline', 'base') else 'current'
        if role in roles:
            return None
        value = canonical_decimal(match[2]); unit = normalized_unit(match[3])
        keys = [key for key, entry in users.items() if entry['value'] == value
                and (entry['unit'] == unit or (entry.get('binding') == 'context_daily_rate'
                     and entry['unit'] == unit + '/día'))]
        if len(keys) != 1:
            return None
        roles[role] = keys[0]
    if set(roles) != {'baseline', 'current'}:
        return None
    baseline, current = users[roles['baseline']], users[roles['current']]
    if Decimal(baseline['value']) != 0 or not baseline['unit'] or baseline['unit'] != current['unit']:
        return None
    if {key for key, entry in users.items() if entry['unit']} != set(roles.values()):
        return None
    return {'operation': 'relative_change', 'baseline': {'quantity': roles['baseline']},
            'current': {'quantity': roles['current']}}
