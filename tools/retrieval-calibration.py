"""Calibration of the JUP-022 retrieval contract with the JUP-069 question bank.

The script measures, with the standard library only, whether the fragments that
a question would retrieve belong to the documents and sections that the bank and
the labels file declare. It chunks the corpus with the ingestion chunker, embeds
fragments and questions with the chosen provider and computes the cosine distance
itself, so it never opens a database connection or writes to a vector store.

Real runs are explicit: they need a virtual key, they plan their number of
provider calls before the first one and they stop when it exceeds the allowed
maximum. Outputs contain identifiers, headings and distances, never credentials
or fragment text.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = "docs/validation/JUP-069-questions.json"
LABELS_PATH = "docs/validation/JUP-022-retrieval-labels.json"
CHUNKER_PATH = "apps/processor/app/embeddings/chunker.py"
CONFIG_PATH = "apps/processor/app/core/config.py"
DEFAULT_TOP_KS = [1, 2, 3, 4, 6, 8]
DEFAULT_MAX_DISTANCES: list[float | None] = [None, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
NON_ANSWER = ("clarify", "abstain")
LISTED_FRAGMENTS = 8


class CalibrationError(RuntimeError):
    """A condition that stops the run with a message that carries no secret."""


def digest(text: str) -> str:
    # Same line-ending normalization as the question bank validator.
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def load_ingestion_chunker(repo_root: Path = ROOT):
    path = repo_root / CHUNKER_PATH
    spec = importlib.util.spec_from_file_location("economicon_ingestion_chunker", path)
    if spec is None or spec.loader is None:
        raise CalibrationError("No se puede cargar el troceador de la ingesta.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TextChunker


def ingestion_chunk_defaults(repo_root: Path = ROOT) -> tuple[int, int]:
    text = (repo_root / CONFIG_PATH).read_text(encoding="utf-8")
    size = re.search(r"embedding_chunk_size:\s*int\s*=\s*(\d+)", text)
    overlap = re.search(r"embedding_chunk_overlap:\s*int\s*=\s*(\d+)", text)
    if not size or not overlap:
        raise CalibrationError("No se encuentran los valores de troceado de la ingesta.")
    return int(size.group(1)), int(overlap.group(1))


def normalize(text: str) -> str:
    return " ".join(text.split())


def chunk_spans(text: str, size: int, overlap: int, repo_root: Path = ROOT) -> list[tuple[str, int, int]]:
    """Chunks of the ingestion pipeline with their offsets in the normalized text."""
    normalized = normalize(text)
    step = size - overlap
    spans: list[tuple[str, int, int]] = []
    start = 0
    while normalized and start < len(normalized):
        end = min(len(normalized), start + size)
        raw = normalized[start:end]
        chunk = raw.strip()
        if chunk:
            first = start + (len(raw) - len(raw.lstrip()))
            spans.append((chunk, first, first + len(chunk)))
        if end >= len(normalized):
            break
        start += step
    if [chunk for chunk, _, _ in spans] != load_ingestion_chunker(repo_root)(size, overlap).split(text):
        raise CalibrationError("El troceado de la calibracion ya no coincide con el de la ingesta.")
    return spans


def section_spans(text: str) -> list[tuple[str, int, int]]:
    """Sections as (heading, start, end) in normalized coordinates; text belongs to the nearest heading above it."""
    marks: list[tuple[str, int]] = []
    length = 0
    fence: str | None = None
    for line in text.replace("\r\n", "\n").split("\n"):
        marker = re.match(r" {0,3}(`{3,}|~{3,})", line)
        in_code = False
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif marker.group(1)[0] == fence:
                fence = None
            in_code = True
        elif fence is not None:
            in_code = True
        tokens = line.split()
        if not tokens:
            continue
        offset = length + (1 if length else 0)
        heading = None if in_code else re.match(r" {0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", line)
        if heading:
            marks.append((heading.group(1).strip(), offset))
        length = offset + len(" ".join(tokens))
    return [(name, start, marks[index + 1][1] if index + 1 < len(marks) else length) for index, (name, start) in enumerate(marks)]


def primary_section(sections: list[tuple[str, int, int]], start: int, end: int) -> str | None:
    best, best_overlap = None, 0
    for name, section_start, section_end in sections:
        overlap = min(end, section_end) - max(start, section_start)
        if overlap > best_overlap:
            best, best_overlap = name, overlap
    return best


def cosine_distance(left: Iterable[float], right: Iterable[float]) -> float:
    a, b = list(left), list(right)
    if len(a) != len(b):
        raise ValueError("Los vectores tienen longitudes distintas.")
    norm_a, norm_b = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("Un vector de norma cero no tiene distancia coseno.")
    similarity = sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)
    return min(2.0, max(0.0, 1.0 - similarity))


def retrieve(items: list[tuple], top_k: int, max_distance: float | None) -> list[tuple]:
    """Items are (identifier, distance, payload); order is distance then identifier."""
    ranked = sorted(items, key=lambda item: (item[1], item[0]))
    if max_distance is not None:
        ranked = [item for item in ranked if item[1] <= max_distance]
    return ranked[:top_k]


class BagOfWordsProvider:
    """Deterministic, offline provider: texts that share words end up close to each other."""

    name = "simulated"

    def __init__(self, dimension: int = 256):
        self.dimension = dimension
        self.alias = "simulated-bag-of-words"

    def _word_vector(self, word: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self.dimension:
            block = hashlib.sha256(f"{word}:{counter}".encode("utf-8")).digest()
            values.extend((byte - 127.5) / 127.5 for byte in block)
            counter += 1
        return values[: self.dimension]

    def embed(self, text: str) -> list[float]:
        folded = unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode()
        words = re.findall(r"[a-z0-9]{3,}", folded)
        total = [0.0] * self.dimension
        for word in words:
            for index, value in enumerate(self._word_vector(word)):
                total[index] += value
        return total if any(total) else [0.0] * (self.dimension - 1) + [1e-9]


class _Secret:
    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "<secret>"


def load_litellm_provider(env: dict[str, str] | None = None, repo_root: Path = ROOT):
    env = os.environ if env is None else env
    for name in ("LITELLM_API_KEY", "LITELLM_BASE_URL"):
        if not (env.get(name) or "").strip():
            raise CalibrationError(f"Falta {name}: la calibracion real necesita el gateway y una clave virtual propia.")
    alias = env.get("EMBEDDING_MODEL") or "economicon-embedding"
    try:
        dimension = int(env.get("EMBEDDING_DIMENSION") or 1536)
    except ValueError:
        raise CalibrationError("EMBEDDING_DIMENSION debe ser un numero entero.") from None
    sys.path.insert(0, str(repo_root / "apps" / "processor"))
    try:
        from app.embeddings.providers import LiteLLMEmbeddingProvider  # type: ignore  # noqa: PLC0415
    except (ImportError, AttributeError):
        raise CalibrationError("Esta rama no incluye el proveedor LiteLLM del processor (JUP-023): integrarla antes de la ejecucion real.") from None
    settings = SimpleNamespace(
        litellm_base_url=env["LITELLM_BASE_URL"], litellm_api_key=_Secret(env["LITELLM_API_KEY"]),
        llm_max_retries=2, llm_timeout_seconds=30, embedding_model=alias,
    )
    provider = LiteLLMEmbeddingProvider(dimension, settings)
    provider.alias = alias
    return provider


def node_validator(repo_root: Path = ROOT) -> Callable[[], list[str]]:
    def validate() -> list[str]:
        try:
            result = subprocess.run(["node", "tools/retrieval-labels.mjs", "validate"], cwd=repo_root, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            return ["Node no esta disponible para validar las etiquetas."]
        return [] if result.returncode == 0 else [line for line in (result.stderr or result.stdout).splitlines() if line.strip()]
    return validate


def run(
    *, repo_root: Path, suite_path: str, labels_path: str, provider, chunk_size: int, chunk_overlap: int,
    top_ks: list[int], max_distances: list[float | None], max_calls: int, min_hit_ratio: float,
    validate_labels: Callable[[], list[str]] | None, now: str | None = None, corpus_documents: list[str] | None = None,
) -> dict:
    if validate_labels is not None:
        errors = validate_labels()
        if errors:
            raise CalibrationError("Etiquetas invalidas, no se hace ninguna llamada:\n" + "\n".join(errors))
    suite = json.loads((repo_root / suite_path).read_text(encoding="utf-8"))
    labels = {entry["case"]: entry for entry in json.loads((repo_root / labels_path).read_text(encoding="utf-8"))["labels"]}
    source_by_path = {source["path"]: source_id for source_id, source in suite["sources"].items()}
    paths = list(dict.fromkeys([source["path"] for source in suite["sources"].values()] + list(corpus_documents or [])))

    documents: dict[str, dict] = {}
    for relative in paths:
        text = (repo_root / relative).read_text(encoding="utf-8")
        source_id = source_by_path.get(relative, Path(relative).stem)
        declared = suite["sources"].get(source_id, {}).get("sha256")
        if declared and digest(text) != declared:
            raise CalibrationError(f"Fuente {source_id}: contenido cambiado; revisar las etiquetas y el banco.")
        documents[source_id] = {"path": relative, "sha256": digest(text), "chunks": chunk_spans(text, chunk_size, chunk_overlap), "sections": section_spans(text)}

    chunks = [(source_id, index, chunk, start, end) for source_id, doc in documents.items() for index, (chunk, start, end) in enumerate(doc["chunks"])]
    planned = len(chunks) + len(suite["cases"])
    if planned > max_calls:
        raise CalibrationError(f"Las llamadas previstas ({planned}) superan el maximo permitido ({max_calls}); no se hace ninguna llamada.")

    vectors = [_embed(provider, chunk) for _, _, chunk, _, _ in chunks]
    order = {source_id: position for position, source_id in enumerate(documents)}
    cases, ranked_by_case = [], {}
    for case in suite["cases"]:
        question_vector = _embed(provider, case["question"])
        items = []
        for (source_id, index, _, start, end), vector in zip(chunks, vectors):
            section = primary_section(documents[source_id]["sections"], start, end)
            items.append(((order[source_id], index), cosine_distance(question_vector, vector), (source_id, section)))
        ranked_by_case[case["id"]] = sorted(items, key=lambda item: (item[1], item[0]))

    def hits(case, retrieved):
        label = labels[case["id"]]
        expected = {(item["source"], item["heading"]) for item in label.get("expect", [])}
        document = any(payload[0] in case["sources"] for _, _, payload in retrieved)
        section = any(payload in expected for _, _, payload in retrieved) if expected else None
        return document, section

    points = []
    for top_k in top_ks:
        for max_distance in max_distances:
            groups = {"answer": [], "non_answer": []}
            for case in suite["cases"]:
                retrieved = retrieve(ranked_by_case[case["id"]], top_k, max_distance)
                document, section = hits(case, retrieved)
                groups["non_answer" if case["behavior"] in NON_ANSWER else "answer"].append((case, bool(retrieved), document, section))

            def summarize(rows, with_sections):
                block = {"cases": len(rows), "document_hit_rate": _rate(sum(1 for r in rows if r[2]), len(rows)), "empty_rate": _rate(sum(1 for r in rows if not r[1]), len(rows))}
                if with_sections:
                    scored = [r for r in rows if r[3] is not None]
                    block["section_cases"] = len(scored)
                    block["section_hit_rate"] = _rate(sum(1 for r in scored if r[3]), len(scored))
                return block

            point = {"top_k": top_k, "max_distance": max_distance, "answer": summarize(groups["answer"], True), "non_answer": summarize(groups["non_answer"], False)}
            point["by_category"] = {
                category: _rate(sum(1 for r in groups["answer"] if r[0]["category"] == category and r[2]), sum(1 for r in groups["answer"] if r[0]["category"] == category))
                for category in sorted({r[0]["category"] for r in groups["answer"]})
            }
            points.append(point)

    for case in suite["cases"]:
        label = labels[case["id"]]
        expected = {(item["source"], item["heading"]) for item in label.get("expect", [])}
        ranked = ranked_by_case[case["id"]]
        in_expected = [d for _, d, payload in ranked if payload in expected]
        outside = [d for _, d, payload in ranked if payload not in expected]
        cases.append({
            "id": case["id"], "behavior": case["behavior"], "category": case["category"], "coverage": label["coverage"],
            "best_expected_distance": round(min(in_expected), 4) if in_expected else None,
            "best_other_distance": round(min(outside), 4) if outside else None,
            "retrieved": [{"source": payload[0], "section": payload[1], "distance": round(distance, 4)} for _, distance, payload in ranked[:LISTED_FRAGMENTS]],
        })

    rule = (f"Para cada top_k, la menor distancia maxima del barrido que conserva al menos {min_hit_ratio:.0%} del acierto por seccion "
            "de los casos 'answer' obtenido sin umbral; no usa los casos clarify ni abstain.")
    candidates = []
    for top_k in top_ks:
        row = [p for p in points if p["top_k"] == top_k]
        base = next((p for p in row if p["max_distance"] is None), None)
        baseline = (base or row[-1])["answer"]["section_hit_rate"] or 0.0
        eligible = [p for p in row if p["max_distance"] is not None and (p["answer"]["section_hit_rate"] or 0.0) >= min_hit_ratio * baseline]
        chosen = min(eligible, key=lambda p: p["max_distance"]) if eligible and baseline > 0 else (base or row[-1])
        candidates.append({"top_k": top_k, "max_distance": chosen["max_distance"], "section_hit_rate": chosen["answer"]["section_hit_rate"], "empty_rate": chosen["answer"]["empty_rate"]})

    return {
        "schema_version": 1, "jup": "JUP-022", "generated_at": now or datetime.now(timezone.utc).isoformat(),
        "provider": {"name": provider.name, "alias": getattr(provider, "alias", provider.name), "dimension": provider.dimension},
        "corpus": {source_id: {"path": doc["path"], "sha256": doc["sha256"]} for source_id, doc in documents.items()},
        "bank": {"path": suite_path, "suite_version": suite["suite_version"]},
        "labels": {"path": labels_path, "cases": len(labels), "coverage": {c: sum(1 for l in labels.values() if l["coverage"] == c) for c in ("direct", "partial", "none")}},
        "chunking": {"size": chunk_size, "overlap": chunk_overlap, "chunks": len(chunks)},
        "planned_calls": planned, "sweep": {"top_k": top_ks, "max_distance": max_distances},
        "points": points, "cases": cases, "gaps": sorted(case_id for case_id, label in labels.items() if label["coverage"] == "none"),
        "selection": {"rule": rule, "min_hit_ratio": min_hit_ratio, "candidates": candidates},
        "limits": [
            "Hay pocos documentos y pocas preguntas: es una calibracion inicial y el umbral puede sobreajustarse a este corpus.",
            "El tope de llamadas cuenta las llamadas previstas; si el proveedor reintenta ante fallos transitorios, el gasto real puede ser hasta (reintentos + 1) veces mayor.",
            "Las distancias son de un solo modelo y alias; un cambio de modelo exige repetir la medicion.",
            "Cada fragmento se asigna a la seccion que cubre mas de su texto: una seccion mas corta que un fragmento puede no ser la principal de ninguno y quedar sin acierto por seccion aunque su contenido se recupere (el acierto por documento no tiene este efecto).",
            "Los casos sin cobertura son huecos del corpus: se listan aparte y no cuentan en el acierto por seccion.",
            "Los casos clarify y abstain se miden aparte y no intervienen en la seleccion del umbral.",
            "La medicion es en memoria; el orden y el filtro SQL reales se cubren con los tests contra pgvector.",
        ],
    }


def _embed(provider, text: str):
    try:
        return provider.embed(text)
    except Exception as exc:
        category = getattr(exc, "category", None)
        detail = f" (categoria {category})" if isinstance(category, str) else ""
        raise CalibrationError(f"El proveedor fallo durante la calibracion{detail}; se detiene sin mostrar su respuesta.") from None


def _rate(hits: int, total: int) -> float | None:
    return round(hits / total, 4) if total else None


def render_report(result: dict) -> str:
    fmt = lambda value: "n/d" if value is None else f"{value:.0%}"  # noqa: E731
    lines = [
        "# Calibracion de la recuperacion (JUP-022)", "",
        f"Generado: {result['generated_at']}. Proveedor: `{result['provider']['name']}`, alias `{result['provider']['alias']}`, dimension {result['provider']['dimension']}.",
        f"Banco: {result['bank']['path']} v{result['bank']['suite_version']}. Troceado: {result['chunking']['size']} caracteres con solape {result['chunking']['overlap']} ({result['chunking']['chunks']} fragmentos). Llamadas previstas: {result['planned_calls']}.", "",
        "## Regla de seleccion", "", result["selection"]["rule"], "", "## Candidatos", "",
        "| top_k | Distancia maxima | Acierto por seccion | Resultados vacios |", "| --- | --- | --- | --- |",
    ]
    for item in result["selection"]["candidates"]:
        lines.append(f"| {item['top_k']} | {item['max_distance'] if item['max_distance'] is not None else 'sin umbral'} | {fmt(item['section_hit_rate'])} | {fmt(item['empty_rate'])} |")
    lines += ["", "## Barrido (casos answer)", "", "| top_k | Distancia maxima | Acierto por documento | Acierto por seccion | Vacios | Casos clarify/abstain: documento | Casos clarify/abstain: vacios |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for point in result["points"]:
        lines.append(f"| {point['top_k']} | {point['max_distance'] if point['max_distance'] is not None else 'sin umbral'} | {fmt(point['answer']['document_hit_rate'])} | {fmt(point['answer']['section_hit_rate'])} | {fmt(point['answer']['empty_rate'])} | {fmt(point['non_answer']['document_hit_rate'])} | {fmt(point['non_answer']['empty_rate'])} |")
    lines += ["", "## Huecos del corpus (sin cobertura)", ""]
    lines += [f"- {case_id}" for case_id in result["gaps"]] or ["- Ninguno."]
    lines += ["", "## Separacion por caso (mejor fragmento esperado frente al mejor de los demas)", "", "| Caso | Tipo | Cobertura | Esperado | Otros |", "| --- | --- | --- | --- | --- |"]
    for case in result["cases"]:
        lines.append(f"| {case['id']} | {case['behavior']} | {case['coverage']} | {case['best_expected_distance']} | {case['best_other_distance']} |")
    lines += ["", "## Limites", ""] + [f"- {limit}" for limit in result["limits"]]
    return "\n".join(lines) + "\n"


def parse_distance(value: str) -> float | None:
    return None if value.lower() in {"none", "ninguna", "sin"} else float(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibracion de la recuperacion de JUP-022.")
    parser.add_argument("--provider", choices=["litellm", "simulated"], default="simulated")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--max-calls", type=int, default=400)
    parser.add_argument("--top-k", type=int, nargs="+", default=DEFAULT_TOP_KS)
    parser.add_argument("--max-distance", type=parse_distance, nargs="+", default=DEFAULT_MAX_DISTANCES)
    parser.add_argument("--min-hit-ratio", type=float, default=0.9)
    parser.add_argument("--chunk-size", type=int)
    parser.add_argument("--chunk-overlap", type=int)
    args = parser.parse_args(argv)
    try:
        provider = load_litellm_provider() if args.provider == "litellm" else BagOfWordsProvider()
        size, overlap = ingestion_chunk_defaults()
        corpus = sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / "docs/assistant-corpus").rglob("*.md") if path.name != "README.md")
        result = run(
            repo_root=ROOT, suite_path=SUITE_PATH, labels_path=LABELS_PATH, provider=provider,
            chunk_size=args.chunk_size or size, chunk_overlap=args.chunk_overlap if args.chunk_overlap is not None else overlap,
            top_ks=args.top_k, max_distances=args.max_distance, max_calls=args.max_calls, min_hit_ratio=args.min_hit_ratio,
            validate_labels=node_validator(), corpus_documents=corpus,
        )
    except CalibrationError as error:
        print(str(error), file=sys.stderr)
        return 1
    report = render_report(result)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    print(f"[OK] {len(result['cases'])} casos, {result['chunking']['chunks']} fragmentos, {result['planned_calls']} llamadas con el proveedor {result['provider']['name']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
