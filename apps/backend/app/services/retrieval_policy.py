"""Conservative literal eligibility, frozen independently of measured outcomes.

No formula evaluation or equivalence inference. FTS proposes candidates; this
policy can only admit complete textual anchors with short contextual support.
"""
import re

STOP = frozenset('a al algo ante aquí como con cual cuáles cuando de del desde donde el ella en entre es esa ese esta este esto hay la las lo los me mi o para por que qué se si sin sobre su sus un una unas unos y how what which when where why is are the a an of for from in on to with and or this that show explain'.split())
TOKENS = re.compile(r'>=|<=|!=|==|>|<|=|[\w]+(?:[-./][\w]+)*|[^\w\s]', re.UNICODE)


def literal_tokens(value):
    return TOKENS.findall(' '.join(value.split()))


def contains_literal(content, anchor):
    haystack, needle = literal_tokens(content), literal_tokens(anchor)
    return bool(needle) and any(haystack[index:index + len(needle)] == needle
                               for index in range(len(haystack) - len(needle) + 1))


def query_policy(question):
    if not isinstance(question, str) or len(question.encode('utf-8')) > 8192:
        raise ValueError('Invalid retrieval query')
    quoted = re.findall(r'`([^`\n]+)`|"([^"\n]+)"|“([^”\n]+)”', question)
    phrases = [next(value for value in match if value) for match in quoted]
    anchors = list(phrases)
    # Complete technical identifiers; a lone number/common word is never an anchor.
    anchors += [value for value in re.findall(r'(?<![\w./-])[A-Za-z0-9]+(?:[-_./][A-Za-z0-9]+)+(?![\w./-])', question)
                if not re.fullmatch(r'[0-9]+\.[0-9]+', value)]
    expressions = re.findall(r'\b[\w]+\s*(?:>=|<=|!=|==|>|<|=)\s*[0-9]+(?:[.,][0-9]+)?(?:\s*(?:%|(?:USD|EUR|GiB|GB|ms|s)\b))?', question)
    anchors += expressions
    anchors = list(dict.fromkeys(' '.join(value.split()) for value in anchors))
    supported = len(anchors) <= 4 and all(len(value) <= 128 for value in anchors)
    # Unsupported comparative/alternative syntax cannot rescue a lexical hit.
    supported = supported and not re.search(r'\b(?:versus|vs|frente|alternativamente|either)\b', question, re.I)
    remaining = question
    for anchor in sorted(anchors, key=len, reverse=True):
        remaining = remaining.replace(anchor, ' ')
    terms = list(dict.fromkeys(value.casefold() for value in re.findall(r'\b\w{3,}\b', remaining)
                               if value.casefold() not in STOP))
    return {'anchors': anchors, 'phrases': phrases[:4], 'terms': terms, 'rescue': bool(anchors) and supported and len(terms) <= 12}


def anchors_match(content, policy):
    return all(contains_literal(content, anchor) for anchor in policy['anchors'])


def lexical_eligible(content, policy):
    words = set(value.casefold() for value in re.findall(r'\b\w+\b', content))
    return policy['rescue'] and anchors_match(content, policy) and set(policy['terms']) <= words


def fuse(dense, lexical, *, limit=20, k=60):
    combined = {}
    for lane, rows in [('dense', dense), ('lexical', lexical)]:
        for rank, item in enumerate(rows[:20], 1):
            key = (item['revision_id'], item['chunk_id'])
            result = combined.setdefault(key, {**item, 'rrf_score': 0., 'dense_rank': None, 'lexical_rank': None})
            result[lane + '_rank'] = rank
            result['rrf_score'] += 1. / (k + rank)
            if lane == 'lexical': result['lexical_score'] = item['lexical_score']
    return sorted(combined.values(), key=lambda item: (-item['rrf_score'], item['chunk_id']))[:limit]
