"""Local factual guards over QA; these checks do not prove semantic entailment."""

import re
import unicodedata

ENTITY = re.compile(
    r"https?://[^\s<>\"']+|\b[A-Z]{2,}(?:[-_]\w+)?\b|\b[A-Z]-\d+\b|\b\d+(?:[.,]\d+)*\b|[€$£%]"
)
NAMES = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+\b")
NEGATION = re.compile(
    r"\b(?:no|sin|nunca|jam[aá]s|not|never|cannot|unknown|inciert\w*|desconocid\w*)\b"
)
STEMS = (
    "autor",
    "confirm",
    "elimin",
    "borr",
    "permit",
    "acredit",
    "verific",
    "convert",
    "disminu",
    "aument",
)
QUALIFIED = re.compile(
    r"\b(?:contradic\w*|inciert\w*|desconocid\w*|pregunt\w*|solicit\w*|intenci[oó]n|hip[oó]tesis)\b"
)


def folded(value):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value.casefold())
        if not unicodedata.combining(c)
    )


def factual_text(value, original):
    # Entities must be literal, even when surrounding qualitative prose differs.
    for match in list(ENTITY.finditer(value)) + list(NAMES.finditer(value)):
        token = match.group().rstrip(".,;")
        if token not in original:
            raise ValueError("Summary invents an entity.")
    if QUALIFIED.search(value.casefold()):
        return
    output = folded(value)
    for clause in re.split(r"[.;!?\n]", original):
        source = folded(clause)
        if (
            NEGATION.search(source)
            and any(stem in source and stem in output for stem in STEMS)
            and not NEGATION.search(output)
        ):
            raise ValueError("Summary removes negation or flattens contradictory QA.")


def validate_sources(value, sources):
    if not isinstance(sources, dict) or any(
        not isinstance(k, str) or not isinstance(v, str) for k, v in sources.items()
    ):
        raise ValueError("Summary sources are invalid.")
    for topic in value["topics"]:
        refs = topic["question_refs"] + topic["answer_refs"]
        if not refs or any(ref not in sources for ref in refs):
            raise ValueError("Summary topic references are invalid.")
        factual_text(topic["text"], "\n".join(sources[ref] for ref in refs))
    for fact in value["facts"]:
        if (
            fact["source_ref"] not in sources
            or fact["quote"] not in sources[fact["source_ref"]]
        ):
            raise ValueError("Summary fact is not literal.")
    original = "\n".join(sources.values())
    for limitation in value["limitations"]:
        factual_text(limitation, original)
    return value


def validate_output(value, sources, resources):
    return validate_sources(resources.validate_payload(value), sources)
