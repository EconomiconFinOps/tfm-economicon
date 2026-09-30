import pytest

from app.services.assistant import AssistantService
from app.services.citations import InvalidCitation, heading, resolve_citations, section_for_chunk


def chunk(identifier="chunk-1", **overrides):
    return dict(chunk_id=identifier, tenant_id="tenant-a", document_id="doc-1",
                title="Guía Azure", source="FinOps", chunk_index=0,
                content="# Costes\nEvidencia observada.", section="Costes", **overrides)


def test_citations_preserve_evidence_identity_and_location():
    [citation] = resolve_citations(["chunk-1"], [chunk(page=7)], "tenant-a")
    assert citation == dict(evidence_id="chunk-1", kind="corpus", document_id="doc-1",
                           title="Guía Azure", source="FinOps", reference="document:doc-1/chunk:0",
                           section="Costes", page=7, excerpt="# Costes\nEvidencia observada.")


@pytest.mark.parametrize("references,records,tenant", [
    (["missing"], [chunk()], "tenant-a"),
    (["chunk-1", "chunk-1"], [chunk()], "tenant-a"),
    (["chunk-1"], [chunk(), chunk()], "tenant-a"),
    (["chunk-1"], [chunk()], "tenant-b"),
    (["chunk-1"], [chunk()], ""),
    ([{}], [chunk()], "tenant-a"),
    (["chunk-1"], [{k: v for k, v in chunk().items() if k != "tenant_id"}], "tenant-a"),
])
def test_invalid_evidence_fails_closed_without_identifiers(references, records, tenant):
    with pytest.raises(InvalidCitation, match="^Invalid response evidence.$"):
        resolve_citations(references, records, tenant)


def test_only_used_chunks_are_cited_in_passage_order():
    records = [chunk(f"chunk-{i}") for i in range(4)]
    answer = AssistantService().answer("Consulta", records)
    assert answer["citations"] == ["chunk-0", "chunk-1", "chunk-2"]
    assert "[3]" in answer["content"]
    assert "[4]" not in answer["content"]
    assert [item["evidence_id"] for item in resolve_citations(answer["citations"], records, "tenant-a")] == answer["citations"]


def test_missing_location_is_not_invented():
    record = chunk()
    record.pop("section")
    [citation] = resolve_citations(["chunk-1"], [record], "tenant-a")
    assert citation["page"] is None and citation["section"] is None
    assert heading("# Guía Azure\n\n## Costes\nObservados") == "Guía Azure"
    assert heading("Sin encabezado") is None


def test_section_recovery_uses_original_document_not_flattened_chunk():
    document = "# Guía Azure\n\n## Costes\nLos costes observados.\n\n## Ahorro\nRevisar recursos."
    assert section_for_chunk(document, "Los costes observados.") == "Costes"
    assert section_for_chunk(document, "## Costes Los costes observados.") == "Costes"
    assert section_for_chunk(document, "Revisar recursos.") == "Ahorro"
    assert section_for_chunk("Introducción\n## Costes\nTexto", "Introducción") is None
    assert section_for_chunk("## A\nRepetido\n## B\nRepetido", "Repetido") is None
    assert section_for_chunk(document, "No existe") is None
