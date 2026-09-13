#!/usr/bin/env python3
"""Exercise authenticated HTTP ingestion and verify both databases.

Run against an explicitly selected disposable stack. This creates one job per
--tenant (default: tenant-core), using the document supplied with --document.
Requires the backend's SQLAlchemy/psycopg dependencies and DATABASE_URL,
VECTOR_DATABASE_URL, and the password environment variable selected below.
The output contains identifiers and checks, never credentials or document text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.request

from sqlalchemy import create_engine, text


def emit(event: str, **values) -> None:
    print(json.dumps({"event": event, **values}, default=str), flush=True)


def post(base_url: str, path: str, payload: dict, *, token=None, tenant=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Tenant-Id"] = tenant
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, json.load(response)


def verify_document(connection, *, job_id, tenant, content, source, artifact_uri, result,
                    provider, dimension, chunk_size, chunk_overlap):
    document = connection.execute(
        text("SELECT * FROM knowledge_documents WHERE job_id = :job_id"),
        {"job_id": job_id},
    ).mappings().one()
    assert document["id"] == document["job_id"] == job_id
    assert document["tenant_id"] == tenant
    assert document["text_content"] == content
    assert document["source"] == source.strip().lower()
    assert document["artifact_uri"] == artifact_uri
    chunks = connection.execute(
        text("""
            SELECT c.id, c.document_id, c.chunk_index, c.content, c.char_count,
                   e.id AS embedding_id, e.chunk_id, e.dimension, e.provider,
                   vector_dims(e.embedding) AS stored_dimension
            FROM document_chunks c
            LEFT JOIN chunk_embeddings e ON e.chunk_id = c.id
            WHERE c.document_id = :job_id ORDER BY c.chunk_index
        """),
        {"job_id": job_id},
    ).mappings().all()
    assert len(chunks) > 0
    assert len(chunks) == document["chunk_count"] == result["embedding_result"]["chunk_count"]
    assert len(chunks) == result["embedding_result"]["embedding_count"]
    normalized = " ".join(content.split())
    step = chunk_size - chunk_overlap
    expected_count = 1 + math.ceil(max(0, len(normalized) - chunk_size) / step)
    expected_chunks = [normalized[index * step:index * step + chunk_size].strip()
                       for index in range(expected_count)]
    expected_chunks = [chunk for chunk in expected_chunks if chunk]
    assert [chunk["content"] for chunk in chunks] == expected_chunks
    assert result["chunks"] == expected_chunks
    for index, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == index
        assert chunk["id"] == chunk["chunk_id"] == f"{job_id}:chunk:{index}"
        assert chunk["embedding_id"] == f"{job_id}:chunk:{index}:embedding"
        assert chunk["document_id"] == job_id
        assert chunk["content"] and chunk["content"] in normalized
        assert chunk["char_count"] == len(chunk["content"])
        assert chunk["dimension"] == chunk["stored_dimension"] == dimension
        assert chunk["provider"] == provider
    assert result["embedding_result"]["document_id"] == job_id
    emit("persistence_verified", job_id=job_id, tenant_id=tenant,
         document_id=document["id"], chunk_count=len(chunks), embedding_count=len(chunks),
         dimension=chunks[0]["dimension"], provider=provider,
         metadata_preserved_in_job_result=True,
         content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--tenant", action="append", dest="tenants")
    parser.add_argument("--email", default="operator@example.com")
    parser.add_argument("--password-env", default="DEMO_PASSWORD")
    parser.add_argument("--source", default="assistant-corpus")
    parser.add_argument("--artifact-uri", default="docs/assistant-corpus/finops/azure-finops-mvp.md")
    parser.add_argument("--expected-provider", default="mock")
    parser.add_argument("--expected-dimension", type=int, default=8)
    parser.add_argument("--expected-chunk-size", type=int, default=500)
    parser.add_argument("--expected-chunk-overlap", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.expected_dimension <= 0:
        parser.error("--expected-dimension must be positive")
    if not 0 <= args.expected_chunk_overlap < args.expected_chunk_size:
        parser.error("expected chunk overlap must be nonnegative and less than chunk size")
    content = args.document.read_text(encoding="utf-8").strip()
    if not content:
        parser.error("document must contain non-whitespace text")
    status, login = post(args.base_url, "/auth/login", {
        "email": args.email, "password": os.environ[args.password_env],
    })
    assert status == 200
    emit("login", status=status)
    database = create_engine(os.environ["DATABASE_URL"])
    vectors = create_engine(os.environ["VECTOR_DATABASE_URL"])
    jobs = []
    try:
        for tenant in args.tenants or ["tenant-core"]:
            metadata = {"validation": "JUP-020", "document_name": args.document.name,
                        "tenant_marker": tenant}
            payload = {"tenant_id": tenant, "source": args.source,
                       "text_content": content, "artifact_uri": args.artifact_uri,
                       "metadata": metadata}
            status, response = post(args.base_url, "/jobs/ingest", payload,
                                    token=login["access_token"], tenant=tenant)
            assert status == 202 and response["status"] == "queued"
            job_id = response["job_id"]
            jobs.append(job_id)
            emit("http_ingest_accepted", status=status, job_id=job_id, tenant_id=tenant)
            deadline = time.monotonic() + args.timeout
            while True:
                with database.connect() as connection:
                    job = connection.execute(
                        text("SELECT tenant_id, status, payload, result FROM jobs WHERE id = :id"),
                        {"id": job_id},
                    ).mappings().one()
                if job["status"] == "completed":
                    break
                if job["status"] == "failed":
                    emit("ingestion_failed", job_id=job_id, status=job["status"],
                         error_code="ingestion_failed")
                    raise AssertionError(f"HTTP ingestion failed for job {job_id}")
                if time.monotonic() >= deadline:
                    raise AssertionError(f"Timed out waiting for job {job_id}; status={job['status']}")
                time.sleep(0.25)
            result = job["result"]
            if isinstance(result, str):
                result = json.loads(result)
            stored_payload = job["payload"]
            if isinstance(stored_payload, str):
                stored_payload = json.loads(stored_payload)
            assert job["tenant_id"] == tenant
            assert stored_payload == payload
            assert result["job_id"] == job_id and result["tenant_id"] == tenant
            assert result["metadata"] == metadata
            with vectors.connect() as connection:
                verify_document(connection, job_id=job_id, tenant=tenant, content=content,
                                source=args.source, artifact_uri=args.artifact_uri,
                                result=result, provider=args.expected_provider,
                                dimension=args.expected_dimension,
                                chunk_size=args.expected_chunk_size,
                                chunk_overlap=args.expected_chunk_overlap)
        emit("smoke_passed", job_ids=jobs, provider=args.expected_provider,
             scope="HTTP, RabbitMQ worker, CockroachDB and pgvector persistence")
    finally:
        database.dispose()
        vectors.dispose()


if __name__ == "__main__":
    main()
