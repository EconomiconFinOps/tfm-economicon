"""Resolve evidence only against the current tenant's retrieved records."""
import re

from app.schemas.assistant import SourceCitation


class InvalidCitation(ValueError):
    def __init__(self):
        super().__init__("Invalid response evidence.")


def validate_context(chunks: list[dict], tenant_id: str) -> None:
    ids = [chunk.get("chunk_id") for chunk in chunks]
    if (not tenant_id or any(not isinstance(item, str) or not item for item in ids)
            or len(ids) != len(set(ids))
            or any(chunk.get("tenant_id") != tenant_id for chunk in chunks)):
        raise InvalidCitation()


def heading(text: str) -> str | None:
    match = re.search(r"^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", text, re.MULTILINE)
    return match.group(1)[:500] if match else None


def section_for_chunk(document: str, content: str) -> str | None:
    # JUP-020 collapses whitespace. Recover location only for an unambiguous
    # match in the original document; never treat the flattened chunk as a heading.
    normalized = " ".join(document.split())
    fragment = " ".join(content.split())
    start = normalized.find(fragment) if fragment else -1
    if start < 0 or normalized.find(fragment, start + 1) >= 0:
        return None
    section = None
    for match in re.finditer(r"^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", document, re.MULTILINE):
        prefix = " ".join(document[:match.start()].split())
        offset = len(prefix) + bool(prefix)
        if offset > start:
            break
        section = match.group(1)[:500]
    return section


def resolve_citations(references: list[str], chunks: list[dict], tenant_id: str) -> list[dict]:
    validate_context(chunks, tenant_id)
    if any(not isinstance(item, str) for item in references) or len(references) != len(set(references)):
        raise InvalidCitation()
    records = {chunk["chunk_id"]: chunk for chunk in chunks}
    if any(ref not in records for ref in references):
        raise InvalidCitation()
    citations = []
    for ref in references:
        chunk = records[ref]
        citations.append(SourceCitation(
            evidence_id=ref,
            kind="corpus",
            document_id=chunk["document_id"],
            title=chunk["title"],
            source=chunk["source"],
            reference=f"document:{chunk['document_id']}/chunk:{chunk['chunk_index']}",
            section=chunk.get("section"),
            page=chunk.get("page"),
            excerpt=chunk["content"][:140],
        ).model_dump())
    return citations
