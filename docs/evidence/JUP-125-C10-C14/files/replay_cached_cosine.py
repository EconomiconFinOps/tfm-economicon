"""New mathematical replay of preserved vectors; no SQL, tokenizer, network or provider."""
import json
import math
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def cosine(a,b):
    return math.fsum(x*y for x,y in zip(a,b)) / math.sqrt(math.fsum(x*x for x in a)*math.fsum(x*x for x in b))

def main():
    data = load("C14/stages/final-1.0.1/inputs.json")
    historical = load("C14/stages/final-1.0.1/sql-results.json")
    vectors = {r["cache_key"]:load("C14/vector-cache/"+r["cache_key"]+".json")["embedding"] for r in data["requests"]}
    result = {"kind":"NEW mathematical float64 cosine replay of frozen final inputs; NOT SQL execution",
              "provider_calls":0, "retokenization":False, "historical_latency_remeasured":False,
              "current_candidate_validated":False}
    for mode in ("old","new"):
        chunks = [c for case in data["cases"] for c in (case["old"] if mode=="old" else case["new"]["chunks"])]
        records = []
        for case in data["cases"]:
            for qi, q in enumerate(case["questions"]):
                scores = [(cosine(vectors[q["cache_key"]], vectors[c["cache_key"]]), i, c) for i,c in enumerate(chunks)]
                scores.sort(key=lambda row: (-row[0], row[1]))
                hits = [(rank,c) for rank,(_,_,c) in enumerate(scores[:20],1)
                        if c["document_id"]==q["document_id"] and
                        " ".join(q["evidence"].split()) in " ".join(c["content"].split())]
                rank = hits[0][0] if hits else None
                original = next(r for r in historical[mode]["records"] if r["case"]==case["name"] and r["question_index"]==qi)
                records.append({"case":case["name"],"question_index":qi,"query":q["query"],"expected_evidence":q["evidence"],
                                "expected_normalized_span":q["normalized_span"],"expected_page":q["page"],
                                "cosine_evidence_rank":rank,"historical_sql_rank":original["rank"],
                                "rank_matches_historical":rank==original["rank"],
                                "historical_citation_page":original["citation"].get("page"),
                                "historical_page_provenance_matches":original["page_provenance_matches"]})
        result[mode] = {"records":records,"recall":{str(k):sum(r["cosine_evidence_rank"] is not None and
                       r["cosine_evidence_rank"]<=k for r in records)/len(records) for k in (1,3,5,10)}}
    result["all_evidence_ranks_match_historical"] = all(r["rank_matches_historical"] for mode in ("old","new") for r in result[mode]["records"])
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["all_evidence_ranks_match_historical"] else 1

if __name__=="__main__":
    sys.exit(main())
