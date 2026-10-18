"""Interactions of JUP-125 metadata with incoming positional/policy retrieval."""
import json
from datetime import datetime, timezone
from threading import Event
import time

import pytest
from sqlalchemy import text

from app.services.citations import resolve_citations
from test_tenant_isolation_vector import retrieval  # noqa: F401
from test_vector_metadata_migration_order import selector_loop_on_windows  # noqa: F401
import test_new_document_citation_titles as title_cases


def seed_structured(store, monkeypatch, body):
    monkeypatch.setattr(title_cases, "BODY", body)
    generated = title_cases.generate("md")
    now = datetime.now(timezone.utc)
    with store.engine.begin() as connection:
        connection.execute(text("""INSERT INTO knowledge_documents
            (id,job_id,tenant_id,source,artifact_uri,text_content,chunk_count,created_at,updated_at,metadata)
            VALUES ('new-md','new-md','tenant-a','guide.md',NULL,:body,:count,:now,:now,CAST(:metadata AS jsonb))"""),
            {"body":body,"count":len(generated["result"]["chunks"]),"now":now,
             "metadata":json.dumps(generated["parent"])})
        for chunk in generated["result"]["chunks"]:
            params={"id":chunk["chunk_id"],"index":chunk["chunk_index"],"content":chunk["content"],
                    "metadata":json.dumps(chunk["metadata"]),"now":now}
            connection.execute(text("""INSERT INTO document_chunks
                (id,document_id,chunk_index,content,char_count,created_at,metadata)
                VALUES (:id,'new-md',:index,:content,1,:now,CAST(:metadata AS jsonb))"""),params)
            connection.execute(text("""INSERT INTO chunk_embeddings VALUES
                (:id,:id,'[0,1,0,0,0,0,0,0]'::vector,8,'mock',:now)"""),params)
    return generated


@pytest.mark.parametrize("bounded", [False, True])
def test_positional_neighbors_keep_structured_metadata_and_literal_citations(retrieval, monkeypatch, bounded):
    body = "# Integration C#\n\n" + "".join(f"## Section {i}\n\n" + (f"Evidence {i}. " * 120) + "\n\n" for i in range(3))
    generated=seed_structured(retrieval,monkeypatch,body)
    chunks=generated["result"]["chunks"]
    assert len(chunks)>=3
    center=chunks[1]["chunk_id"]
    with retrieval.engine.begin() as connection:
        connection.execute(text("UPDATE chunk_embeddings SET embedding='[1,0,0,0,0,0,0,0]'::vector WHERE chunk_id=:id"),{"id":center})
    options={}
    if bounded:
        assert retrieval.ping()
        options={"deadline":time.time()+10,"cancelled":Event()}
    rows=retrieval.search_chunks("tenant-a",[1.]+[0.]*7,provider="mock",top_k=3,
        max_distance=.01,neighbor_seed_count=1,**options)
    assert rows[0]["chunk_id"]==center and len(rows)==3
    expected={chunk["chunk_id"]:chunk for chunk in chunks}
    assert {row["chunk_index"] for row in rows}=={0,1,2}
    for row in rows:
        assert row["content"]==expected[row["chunk_id"]]["content"]
        assert row["chunk_metadata"]==expected[row["chunk_id"]]["metadata"]
        assert row["title"]=="Integration C#" and row["source_spans"]
    citations=resolve_citations([row["chunk_id"] for row in rows],rows,"tenant-a")
    assert all(citation["title"]=="Integration C#" and citation["source_spans"] for citation in citations)


@pytest.mark.parametrize("bounded", [False, True])
def test_policy_lookup_of_actual_structured_markdown_preserves_raw_chunks(retrieval,monkeypatch,bounded):
    body=("# Integration C#\n## Budgets Y Forecast\nUn budget es una expectativa.\n"
          "Reglas de interpretacion:\n- superar un umbral requiere investigacion;\n"
          "- no confundir forecast y presupuesto.\n## Next Section\nEnd.\n")
    generated=seed_structured(retrieval,monkeypatch,body)
    options={}
    if bounded:
        assert retrieval.ping()
        options={"deadline":time.time()+10,"cancelled":Event()}
    rows=retrieval.search_chunks("tenant-a",[1.]+[0.]*7,top_k=20,max_distance=.01,
        provider="mock",policy_section="Budgets Y Forecast",**options)
    assert rows and all(row.get("policy_priority") for row in rows)
    expected={chunk["chunk_id"]:chunk for chunk in generated["result"]["chunks"]}
    assert all(row["content"]==expected[row["chunk_id"]]["content"] for row in rows)
    assert all(row["chunk_metadata"]==expected[row["chunk_id"]]["metadata"] for row in rows)
    from app.core.chat_policy_sections import complete_sections, policy_units
    sources=[{"id":row["chunk_id"],"kind":"corpus","content":row["content"],
              "provenance":{"document_id":row["document_id"],"chunk_index":row["chunk_index"],
                            "sections":row["section_spans"]}} for row in rows]
    sections=complete_sections(sources,"Budgets Y Forecast")
    assert len(sections)==1 and policy_units(sections[0]["body"]) is not None


@pytest.mark.parametrize("bounded", [False, True])
@pytest.mark.parametrize("missing", [("document_chunks",), ("knowledge_documents",), ("document_chunks","knowledge_documents")])
def test_policy_lookup_survives_003_fallback_and_then_same_store_uses_metadata(retrieval,bounded,missing):
    from test_chat_policy_retrieval_pgvector_jup123 import add_policy
    from test_vector_metadata_migration_order import drop_chunking_metadata, apply_chunking_metadata
    add_policy(retrieval,"migration-policy")
    drop_chunking_metadata(retrieval,missing)
    if bounded:
        assert retrieval.ping()
    def search():
        options={"deadline":time.time()+10,"cancelled":Event()} if bounded else {}
        return retrieval.search_chunks("tenant-a",[1.]+[0.]*7,top_k=20,max_distance=.01,
            provider="mock",policy_section="Reglas De Tagging",**options)
    before=search()
    assert before and all(row.get("policy_priority") and row["section_spans"] for row in before)
    assert all("chunk_metadata" not in row for row in before)
    drop_chunking_metadata(retrieval,tuple(table for table in ("document_chunks","knowledge_documents") if table not in missing))
    apply_chunking_metadata(retrieval)
    with retrieval.engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET metadata=CAST(:value AS jsonb) WHERE id='migration-policy'"),
            {"value":json.dumps({"title":"Preserved policy C#"})})
    after=search()
    assert [row["chunk_id"] for row in after]==[row["chunk_id"] for row in before]
    assert all(row["title"]=="Preserved policy C#" and row["section_spans"] for row in after)
