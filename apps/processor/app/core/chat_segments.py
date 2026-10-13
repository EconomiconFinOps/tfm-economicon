"""Private, bounded response segments; public response fields remain strings."""

import copy

from app.core.chat_calculations import render_text
from app.core.chat_expressions import ExpressionRenderer, expression_definitions


def quote_choices(content):
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Invalid corpus quotation source.")
    # Every choice is a literal passage. The context budget accounts for all of
    # them; no generated paraphrase or automatic citation is introduced.
    return [
        content[i : i + 2048]
        for i in range(0, len(content), 2048)
        if content[i : i + 2048].strip()
    ]


def segment_schema(records=None, *, limit=4000, quantities=None, rules=None, evidence=None):
    choices = [
        {
            "type": "object",
            "properties": {"text": {"type": "string", "maxLength": limit}},
            "required": ["text"],
            "additionalProperties": False,
        }
    ]
    if evidence is not None:
        ids = [item["id"] for item in evidence if item.get("kind") == "corpus"]
        prose = choices[0]
        prose["properties"].update(
            basis={"type": "string", "enum": ["non_documentary"]},
            evidence_ids={"type": "array", "maxItems": 0, "items": {"type": "string"}},
        )
        prose["required"] += ["basis", "evidence_ids"]
        if ids:
            documentary = copy.deepcopy(prose)
            documentary["properties"]["basis"] = {"const": "documentary", "type": "string"}
            documentary["properties"]["evidence_ids"] = {
                "type": "array", "minItems": 1, "maxItems": 20,
                "items": {"type": "string", "enum": ids},
            }
            choices.append(documentary)
    if quantities:
        choices.append(
            {
                "type": "object",
                "properties": {"expression": {"$ref": "#/$defs/RenderedExpression"}},
                "required": ["expression"],
                "additionalProperties": False,
            }
        )
    if quantities and rules:
        from app.core.chat_rules import classification_schema

        choices.append(
            {
                "type": "object",
                "properties": {"classification": classification_schema(rules)},
                "required": ["classification"],
                "additionalProperties": False,
            }
        )
    return {
        "type": "array",
        "minItems": 1,
        "maxItems": 128,
        "items": choices[0] if len(choices) == 1 else {"anyOf": choices},
    }


def bind_segments(schema, records=None, quantities=None, rules=None, evidence=None):
    schema = copy.deepcopy(schema)
    if quantities:
        schema.setdefault("$defs", {}).update(expression_definitions(quantities))
    for branch in schema.get("anyOf", [schema]):
        properties = branch["properties"]
        properties["answer"] = segment_schema(
            records, quantities=quantities, rules=rules, evidence=evidence
        )
        for field in ("assumptions", "limitations", "next_actions"):
            # One bounded prose segment per short public item. Arithmetic lives
            # in answer; allowing128 short segments advertised values that the
            # unchanged500-character public contract necessarily rejects.
            item = segment_schema(limit=500, evidence=evidence)
            item["maxItems"] = 1
            properties[field]["items"] = item
    return schema


def render_segment(segment, records, expressions=None):
    if not isinstance(segment, dict):
        raise ValueError("Invalid response segment.")
    if set(segment) in ({"text"}, {"text", "basis", "evidence_ids"}):
        text = segment["text"]
        if not isinstance(text, str) or "[[calc:" in text:
            raise ValueError("Invalid segment text.")
        # Slots and raw equations cannot bypass the typed reference branch.
        return render_text(text, [])
    if set(segment) == {"expression"} and expressions is not None:
        return expressions.render(segment["expression"])
    if set(segment) == {"classification"} and expressions is not None:
        return expressions.classify(segment["classification"])
    raise ValueError("Invalid response segment.")


def render_segments(segments, records, *, limit=4000, expressions=None):
    if not isinstance(segments, list) or not 1 <= len(segments) <= 128:
        raise ValueError("Invalid segment collection.")
    parts = []
    pending = []
    for segment in segments:
        # Validate shape before grouping adjacent text. Group validation closes
        # bypasses where an equation or a slot is split across text segments.
        rendered = render_segment(segment, records, expressions)
        if "text" in segment:
            pending.append(rendered)
        else:
            if pending:
                parts.append(render_segment({"text": "".join(pending)}, records))
                pending = []
            parts.append(rendered)
    if pending:
        parts.append(render_segment({"text": "".join(pending)}, records))
    result = "".join(parts)
    if len(result) > limit:
        raise ValueError("Rendered text limit.")
    result = result.strip()
    if not result:
        raise ValueError("Empty rendered text.")
    return result


def render_response(value, records, *, quantities=None, rules=None, require_grounding=False):
    if not isinstance(value, dict) or "answer" not in value:
        raise ValueError("Invalid calculation response.")
    expressions = (
        ExpressionRenderer(quantities, rules=rules) if quantities is not None else None
    )
    result = {
        **value,
        "answer": render_segments(value["answer"], records, expressions=expressions),
    }
    for field in ("assumptions", "limitations", "next_actions"):
        if (
            field not in value
            or not isinstance(value[field], list)
            or len(value[field]) > 10
        ):
            raise ValueError("Invalid calculation collection.")
        for item in value[field]:
            if (
                not isinstance(item, list)
                or len(item) != 1
                or not isinstance(item[0], dict)
                or set(item[0]) not in ({"text"}, {"text", "basis", "evidence_ids"})
            ):
                raise ValueError("Invalid short prose item.")
        result[field] = [render_segments(item, [], limit=500) for item in value[field]]
    if expressions is not None and expressions.classification_used:
        from app.core.chat_rules import project_classification_citations

        result["evidence"] = project_classification_citations(
            expressions.classification_supports, value.get("evidence")
        )
    if expressions is not None and expressions.documentary_sources:
        evidence = result.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(item, dict) for item in evidence
        ):
            raise ValueError("Documentary calculation citation missing.")
        cited = {item.get("id") for item in evidence if item.get("kind") == "corpus"}
        if not expressions.documentary_sources <= cited:
            raise ValueError("Documentary calculation citation missing.")
    if require_grounding:
        validate_grounding(value, result, records, expressions)
    return result


def validate_grounding(value, result, records, expressions):
    known = {item["id"]: item for item in records if item.get("kind") == "corpus"}
    selected = {}
    for item in result.get("evidence", []):
        if item.get("kind") != "corpus":
            continue
        identifier = item.get("id")
        source = known.get(identifier)
        quote = item.get("support_quote")
        if identifier in selected or source is None or any(
            item.get(key) != source.get(key) for key in ("kind", "title", "source")
        ):
            raise ValueError("Invalid documentary provenance.")
        if not isinstance(quote, str) or not quote.strip() or quote not in source.get("content", ""):
            raise ValueError("Invalid documentary passage.")
        selected[identifier] = item
    used = set()
    segments = list(value["answer"])
    for field in ("assumptions", "limitations", "next_actions"):
        segments.extend(segment for item in value[field] for segment in item)
    for segment in segments:
        if "text" not in segment:
            continue
        if set(segment) != {"text", "basis", "evidence_ids"}:
            raise ValueError("Documentary support missing.")
        ids = segment["evidence_ids"]
        if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)):
            raise ValueError("Invalid documentary provenance.")
        if segment["basis"] == "non_documentary" and not ids:
            continue
        if segment["basis"] != "documentary" or not ids:
            raise ValueError("Documentary support missing.")
        if not set(ids) <= known.keys():
            raise ValueError("Invalid documentary provenance.")
        if not set(ids) <= selected.keys():
            raise ValueError("Documentary support missing.")
        used.update(ids)
    if expressions is not None:
        used.update(expressions.documentary_sources)
        if expressions.classification_used:
            used.update(item["source"]["id"] for item in expressions.classification_supports)
    for field in ("metrics", "recommendations"):
        for item in value.get(field, []):
            used.update(set(item.get("evidence_ids", [])) & known.keys())
    if selected.keys() - used:
        raise ValueError("Unused documentary evidence.")
