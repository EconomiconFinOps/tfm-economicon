"""Versioned internal rules activated only by effective authenticated passages."""

import hashlib
import json
import re

FORMULA = "Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100"
BANDS = (
    "- verde: menor o igual a 5 %; "
    "- amarillo: mayor que 5 % y menor o igual a 10 %; "
    "- rojo: mayor que 10 %."
)
RULE_ID = "unallocated-cost-v1"
RULE_SOURCE = "business-rules.economicon-mvp"
RULE_CATALOG = {
    "version": 1,
    "id": RULE_ID,
    "source": RULE_SOURCE,
    "formula": FORMULA,
    "bands_passage": BANDS,
    "bands": [
        {"upper": "5", "inclusive": True, "color": "verde", "interval": "<= 5 %"},
        {
            "upper": "10",
            "inclusive": True,
            "color": "amarillo",
            "interval": "> 5 % y <= 10 %",
        },
        {"upper": None, "inclusive": False, "color": "rojo", "interval": "> 10 %"},
    ],
}
RULE_CATALOG_SHA256 = hashlib.sha256(
    json.dumps(
        RULE_CATALOG, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
).hexdigest()


def normalized(text):
    return " ".join(text.split())


def context_rules(context):
    authorized = {
        item["id"]: item
        for item in context.get("authorized_evidence", [])
        if item.get("kind") == "corpus"
    }
    effective = []
    for message in context.get("messages", []):
        content = message.get("content", "")
        if not content.startswith("UNTRUSTED_RETRIEVAL_CONTEXT\n"):
            continue
        for item in json.loads(content.split("\n", 1)[1]).get("evidence", []):
            if item.get("kind") != "corpus" or authorized.get(item.get("id")) != item:
                raise ValueError("Rule source not authorized.")
            effective.append(item)
    groups = {}
    for item in effective:
        # Formula and bands can cross chunk boundaries, but not document IDs.
        match = re.fullmatch(r"(.+):chunk:[0-9]+", item["id"])
        if item.get("source") != RULE_SOURCE or not match:
            continue
        groups.setdefault(match.group(1), []).append(item)
    for sources in groups.values():
        supports = []
        for passage in (FORMULA, BANDS):
            selected = next(
                (
                    item
                    for item in sources
                    if normalized(passage) in normalized(item["content"])
                ),
                None,
            )
            if selected is None:
                break
            supports.append({"source": selected, "passage": passage})
        if len(supports) == 2:
            return {
                RULE_ID: {"catalog_sha256": RULE_CATALOG_SHA256, "supports": supports}
            }
    return {}


def classification_schema(rules):
    return {
        "type": "object",
        "properties": {
            "rule_id": {"type": "string", "enum": list(rules)},
            "expression": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "const": "percentage"},
                    "numerator": {"$ref": "#/$defs/NumericExpression3"},
                    "denominator": {"$ref": "#/$defs/NumericExpression3"},
                },
                "required": ["operation", "numerator", "denominator"],
                "additionalProperties": False,
            },
        },
        "required": ["rule_id", "expression"],
        "additionalProperties": False,
    }


def validate_classification_citations(required, evidence):
    if not isinstance(evidence, list):
        raise ValueError("Missing classification citation.")
    selected = {item.get("id"): item for item in evidence if isinstance(item, dict)}
    for support in required:
        source, passage = support["source"], support["passage"]
        item = selected.get(source["id"], {})
        quote = item.get("support_quote")
        if (
            any(
                item.get(key) != source[key]
                for key in ("id", "kind", "title", "source")
            )
            or not isinstance(quote, str)
            or quote not in source["content"]
            or normalized(passage) not in normalized(quote)
        ):
            raise ValueError("Invalid classification citation.")


def project_classification_citations(required, evidence):
    """Publish the server-applied rule's own citations; never repair supplied ones."""
    from app.core.chat_segments import quote_choices

    if not isinstance(evidence, list) or any(
        not isinstance(item, dict) for item in evidence
    ):
        raise ValueError("Invalid classification citation.")
    selected = list(evidence)
    identifiers = [item.get("id") for item in selected]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Invalid classification citation.")
    grouped = {}
    for support in required:
        grouped.setdefault(support["source"]["id"], []).append(support)
    for identifier, supports in grouped.items():
        provided = next(
            (item for item in selected if item.get("id") == identifier), None
        )
        if provided is not None:
            validate_classification_citations(supports, [provided])
            continue
        source = supports[0]["source"]
        quote = next(
            (
                part
                for part in quote_choices(source["content"])
                if all(normalized(s["passage"]) in normalized(part) for s in supports)
            ),
            None,
        )
        if quote is None:
            raise ValueError("Invalid classification citation.")
        selected.append(
            {
                **{key: source[key] for key in ("id", "kind", "title", "source")},
                "support_quote": quote,
            }
        )
    if len(selected) > 20:
        raise ValueError("Invalid classification citation.")
    return selected
