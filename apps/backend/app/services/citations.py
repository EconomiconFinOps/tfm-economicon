"""Resolve evidence only against the current tenant's retrieved records."""
import re
from bisect import bisect_right

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


class DocumentCitations:
    """Request-local Markdown locations over the same normalization as ingestion.

    Parse each document once in linear time. Only ATX headings outside fenced
    code, indented code and initial YAML front matter are eligible locations.
    """
    def __init__(self, document: str):
        parts = []
        self.offsets: list[int] = []
        self.sections: list[str] = []
        length = 0
        fence = None
        front_matter = False
        for line_number, line in enumerate(document.splitlines()):
            normalized = " ".join(line.split())
            offset = length + bool(parts)
            if normalized:
                parts.append(normalized)
                length = offset + len(normalized)
            stripped = line.strip()
            if line_number == 0 and stripped.lstrip("\ufeff") == "---":
                front_matter = True
                continue
            if front_matter:
                if stripped in {"---", "..."}:
                    front_matter = False
                continue
            if fence:
                if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}[ \t]*", line):
                    fence = None
                continue
            opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if opening and (opening[1][0] != "`" or "`" not in opening[2]):
                fence = (opening[1][0], len(opening[1]))
                continue
            match = re.match(r"^ {0,3}#{1,6}(?:[ \t]+(.*)|$)", line)
            if match:
                title = (match[1] or "").strip()
                without_closing = title.rstrip("#")
                if not without_closing or without_closing[-1] in " \t":
                    title = without_closing.rstrip()
                if title:
                    self.offsets.append(offset)
                    self.sections.append(title[:500])
        self.normalized = " ".join(parts)
        self.title = self.sections[0] if self.sections else None

    def section(self, content: str) -> str | None:
        fragment = " ".join(content.split())
        start = self.normalized.find(fragment) if fragment else -1
        if start < 0 or self.normalized.find(fragment, start + 1) >= 0:
            return None
        index = bisect_right(self.offsets, start) - 1
        return self.sections[index] if index >= 0 else None


def heading(text: str) -> str | None:
    return DocumentCitations(text).title


def section_for_chunk(document: str, content: str) -> str | None:
    return DocumentCitations(document).section(content)


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
