import pytest
from time import perf_counter

from app.services.assistant import AssistantService
from app.services.citations import DocumentCitations, InvalidCitation, heading, resolve_citations, section_for_chunk


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


def test_excerpt_of_a_real_sized_chunk_is_the_quoted_passage():
    record = chunk()
    record["content"] = " ".join(f"palabra-{i}" for i in range(60))
    assert len(record["content"]) > 140
    answer = AssistantService().answer("Consulta", [record])
    [citation] = resolve_citations(answer["citations"], [record], "tenant-a")
    assert citation["excerpt"] == record["content"][:140]
    assert f"- [1] {citation['source']}: {citation['excerpt']}" in answer["content"].split("\n")


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


@pytest.mark.parametrize("document", ["# \r\nTexto\r\n", "#  \nTexto", "#\nTexto", "# ###\nTexto"])
def test_empty_headings_have_no_title_or_location(document):
    assert heading(document) is None
    assert section_for_chunk(document, "Texto") is None


@pytest.mark.parametrize("prefix", [
    "```bash\n# instalar dependencias\n```\n",
    "~~~yaml\n# comentario\n~~~\n",
    "````bash\n```\n# sigue dentro\n````\n",
    "---\n# comentario YAML\ntitle: metadatos\n---\n",
    "---\n# comentario YAML\n...\n",
    "    # codigo indentado\n",
    "\t# codigo indentado\n",
])
def test_non_heading_contexts_do_not_invent_titles_or_sections(prefix):
    document = prefix + "Introduccion\n## Guia de C# ##\nCoste observado"
    assert heading(document) == "Guia de C#"
    assert section_for_chunk(document, "Introduccion") is None
    assert section_for_chunk(document, "Coste observado") == "Guia de C#"


def test_unclosed_fences_and_front_matter_are_conservatively_ignored():
    for document in ["```\n# Texto", "---\n# Texto"]:
        assert heading(document) is None


def test_code_heading_does_not_replace_real_section():
    document = "## Costes\n```bash\n# falso\n```\nEvidencia final"
    assert section_for_chunk(document, "Evidencia final") == "Costes"


def test_large_document_locations_complete_within_interactive_budget():
    document = "".join(f"## Seccion {i}\n" + "coste " * 63 + f"fin-{i}\n" for i in range(1000))
    start = perf_counter()
    locations = DocumentCitations(document)
    assert [locations.section(f"fin-{i}") for i in range(996, 1000)] == [f"Seccion {i}" for i in range(996, 1000)]
    # Generous for CI: old implementation took >7 s for these four passages.
    assert perf_counter() - start < 1.5


def test_padded_source_matches_the_cited_passage():
    record = chunk()
    record["source"] = "  guia.md \t"
    record["content"] = "Costes observados"
    answer = AssistantService().answer("Consulta", [record])
    [citation] = resolve_citations(answer["citations"], [record], "tenant-a")
    assert f"- [1] {citation['source']}: {citation['excerpt']}" in answer["content"]
