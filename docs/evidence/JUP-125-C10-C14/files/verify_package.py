"""Read-only evidence-package verification. Python 3.10+, standard library only."""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CORPUS_SHA = "1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b"
STAGES = ("initial-1.0.0", "initial-enriched-1.0.0", "r1-1.0.0", "final-1.0.1", "r2-1.0.1")

def need(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def reconstruct(chunks):
    """Assemble recorded payload spans only; no expected text/document argument."""
    descriptors = [c["metadata"]["reconstruction"] for c in chunks if "reconstruction" in c["metadata"]]
    need(len(descriptors) == 1, "Expected one recorded reconstruction descriptor")
    descriptor = descriptors[0]
    need(len(chunks) == descriptor["chunk_count"], "Recorded chunk count")
    need(sorted(c["chunk_index"] for c in chunks) == list(range(len(chunks))), "Chunk indices")
    parts = [None] * descriptor["document_characters"]
    for c in chunks:
        content, meta = c["content"], c["metadata"]
        need(sha(content.encode()) == meta["chunk_hash"], "Chunk content hash")
        for span in meta["primary_spans"]:
            a, b = span["normalized_range"]
            x, y = span["content_range"]
            text = content[x:y]
            need(0 <= a < b <= len(parts) and b-a == len(text), "Primary span lengths")
            for i, char in enumerate(text, a):
                need(parts[i] is None or parts[i] == char, "Primary span conflict")
                parts[i] = char
    for span in descriptor["omitted_spans"]:
        a, b = span["normalized_range"]
        text = span["text"]
        need(0 <= a < b <= len(parts) and len(text) == b-a and text.isspace(), "Omitted whitespace")
        for i, char in enumerate(text, a):
            need(parts[i] is None or parts[i] == char, "Omitted span conflict")
            parts[i] = char
    need(all(char is not None for char in parts), "Incomplete reconstruction")
    recovered = "".join(parts)
    need(sha(recovered.encode()) == descriptor["document_text_sha256"], "Reconstructed text hash")
    for c in chunks:
        meta = c["metadata"]
        for span in meta["primary_spans"] + meta["repetitions"]:
            a, b = span["normalized_range"]
            x, y = span["content_range"]
            need(c["content"][x:y] == recovered[a:b], "Carrier text differs")
        for span in meta["source_spans"]:
            a, b = span["normalized_range"]
            carriers = [s for s in meta["primary_spans"] + meta["repetitions"]
                        if s["normalized_range"][0] <= a < b <= s["normalized_range"][1]]
            need(carriers, "Source span has no text carrier")
            for carrier in carriers:
                offset = carrier["content_range"][0] + a-carrier["normalized_range"][0]
                need(c["content"][offset:offset+b-a] == recovered[a:b], "Source span text")
    return recovered

def verify():
    manifest = load("MANIFEST.json")
    expected = {item["path"] for item in manifest["files"]}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    need(actual == expected | {"MANIFEST.json"}, "Package path set differs from manifest")
    for item in manifest["files"]:
        path = ROOT / item["path"]
        need(path.resolve().is_relative_to(ROOT.resolve()) and not path.is_symlink(), "Unsafe package path")
        raw = path.read_bytes()
        need(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "Hash/size: " + item["path"])

    inventory = load("C10/inventory.json")["documents"]
    need(len(inventory) == 9, "Nine original formats required")
    for item in inventory:
        name = item["filename"]
        raw = (ROOT / "C10/originals" / name).read_bytes()
        normalized = (ROOT / "C10/normalized" / (name + ".json")).read_bytes()
        fixture = (ROOT / "C10/historical-fixtures" / (name + ".json")).read_bytes()
        doc = json.loads(normalized)
        need(sha(raw) == item["sha256"] == doc["origin"]["content_hash"], "C10 original hash")
        need(sha(normalized) == item["normalized_sha256"] and normalized == fixture, "C10 fixture hash")
        need(doc["origin"]["filename"] == name and doc["origin"]["file_size"] == len(raw), "C10 original identity")
        need(doc["document_id"] == item["document_id"], "C10 document identity")
        need(doc["extraction_method"] == item["method"] and len(doc["text"]) == item["characters"], "C10 extraction")
        need(len(doc["blocks"]) == item["blocks"] and doc["origin"]["artifact_uri"] is None, "C10 blocks/origin")
    flow = load("C10/receipts/principal-sql-flow.json")
    need(flow == load("C10/receipts/independent-sql-flow.json"), "C10 historical receipts differ")
    need({d["format"] for d in flow["fixtures"]} == {d["filename"] for d in inventory}, "C10 receipt format coverage")
    need({d["format"] for d in flow["retrieval"]["all_real_normalized_formats"]} ==
         {d["filename"] for d in inventory}, "C10 citation receipt format coverage")

    corpus_raw = (ROOT / "C14/corpus/evaluation-corpus-frozen-v2.json").read_bytes()
    need(sha(corpus_raw) == CORPUS_SHA, "Frozen corpus hash")
    corpus = json.loads(corpus_raw)
    need(len(corpus["cases"]) == 6 and sum(len(c["questions"]) for c in corpus["cases"]) == 12, "Corpus counts")
    final = load("C14/stages/final-1.0.1/inputs.json")
    requests = {r["cache_key"]: r for r in final["requests"]}
    need(len(requests) == 46 and len(final["requests"]) == 46, "Unique requests")
    cache_names = {p.stem for p in (ROOT / "C14/vector-cache").glob("*.json")}
    need(cache_names == set(requests), "Exact cache coverage")
    receipt = load("C14/receipts/final-r2-post-cleanup-original.json")
    need(len(receipt["cache_files"]) == 46, "Historical cache inventory")
    for item in receipt["cache_files"]:
        raw = (ROOT / "C14/vector-cache" / item["path"]).read_bytes()
        need(sha(raw) == item["sha256"] and len(raw) == item["bytes"], "Historical cache inventory hash")
    for key, request in requests.items():
        need(sha(("economicon-embedding\0" + request["input"]).encode()) == key, "Input/cache key")
        need(request["model"] == "economicon-embedding" and request["dimensions"] == 1536, "Input model")
        cache = load("C14/vector-cache/" + key + ".json")
        need(cache["cache_key"] == key and cache["model_alias"] == request["model"], "Vector association")
        need(cache["upstream_model"] == "openrouter/openai/text-embedding-3-small", "Effective vector model")
        vector = cache["embedding"]
        need(cache["dimensions"] == 1536 and len(vector) == 1536 and
             all(isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x) for x in vector),
             "Vector dimensions/numbers")
        need(sum(x*x for x in vector) > 0, "Zero vector")
    need(sum(r["tokens"] for r in requests.values()) == 5839, "Recorded token sum; not retokenization")
    reconstructed = 0
    for stage in STAGES:
        data = load("C14/stages/" + stage + "/inputs.json")
        need(data["summary"]["corpus_sha256"] == CORPUS_SHA, "Stage declared corpus")
        need(data["requests"] == final["requests"], "Stage exact inputs differ: " + stage)
        refs = []
        for case, frozen in zip(data["cases"], corpus["cases"]):
            need(case["name"] == frozen["name"] and case["document"] == frozen["document"], "Corpus document relation")
            doc = case["document"]
            need([{k:v for k,v in q.items() if k != "cache_key"} for q in case["questions"]] ==
                 frozen["questions"], "Frozen questions relation")
            for q in case["questions"]:
                a,b = q["normalized_span"]
                need(doc["text"][a:b] == q["evidence"] and q["document_id"] == doc["document_id"], "Question reference span")
                refs.append((q["cache_key"], q["query"]))
            normalized = " ".join(doc["text"].split())
            legacy = []
            start = 0
            while start < len(normalized):
                end = min(len(normalized), start+500)
                chunk = normalized[start:end].strip()
                if chunk:
                    legacy.append(chunk)
                if end >= len(normalized):
                    break
                start += 450
            need(legacy == [c["content"] for c in case["old"]], "Legacy 500/50 baseline")
            for chunk in case["old"] + case["new"]["chunks"]:
                refs.append((chunk["cache_key"], chunk["content"]))
            version = "1.0.1" if stage in ("final-1.0.1", "r2-1.0.1") else "1.0.0"
            need(case["new"]["manifest"]["chunking_version"] == version, "Stage version")
            need(case["new"]["manifest"]["configuration"] == {"target_tokens":600,"max_tokens":800,"overlap_ratio":0.1},
                 "Structural configuration")
            if version == "1.0.1":
                recovered = reconstruct(case["new"]["chunks"])
                need(recovered == doc["text"], "Reconstructed corpus differs")
                reconstructed += 1
        need(len(refs) == 46 and len(set(k for k,_ in refs)) == 46, "25 old + 9 new + 12 query references")
        for key, text in refs:
            need(requests[key]["input"] == text, "Exact input reference")
    r2 = load("C14/stages/r2-1.0.1/inputs.json")
    need([c["new"] for c in final["cases"]] == [c["new"] for c in r2["cases"]], "Final/R2 full new chunk equivalence")
    need((ROOT / "C14/stages/r1-1.0.0/EMPTY-corpus-original.json").stat().st_size == 0, "Preserved R1 anomaly")
    return {"package_integrity":"verified", "manifest_files":len(expected), "C10_originals":9,
            "C10_original_normalized_fixture_hashes":27, "C14_corpus_sha256":CORPUS_SHA,
            "documents":6, "questions":12, "exact_inputs":46, "real_cached_vectors":46,
            "dimensions":1536, "stages":list(STAGES), "recorded_final_and_r2_reconstructions":reconstructed,
            "R1_empty_corpus_preserved":True, "provider_calls":0,
            "scope":"Historical bytes and recorded data relations only; no current-candidate acceptance or SQL replay"}

if __name__ == "__main__":
    try:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"verification_error":str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
