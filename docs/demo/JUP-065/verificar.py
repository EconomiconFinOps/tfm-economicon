"""Comprueba integridad/reproducción y referencias offline; no prueba el MVP."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from preparar import prepare


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(repo, root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="jup065-check-") as tmp:
        regenerated = Path(tmp)
        expected = prepare(repo, regenerated)
        originals = root / "generado"
        paths = sorted(p.relative_to(regenerated) for p in regenerated.rglob("*") if p.is_file())
        actual_paths = sorted(p.relative_to(originals) for p in originals.rglob("*") if p.is_file())
        if paths != actual_paths:
            raise ValueError("Inventario generado distinto de la reproducción")
        for path in paths:
            if (regenerated / path).read_bytes() != (originals / path).read_bytes():
                raise ValueError(f"Archivo no reproducible: {path}")
        require(expected["csv_rows_selected"] == 40, "Referencia o separación de entradas inválida")
        require(expected["persisted_record_count"] == 38, "Referencia o separación de entradas inválida")
        require(expected["totals"] == [{"currency": "USD", "exact_csv_sum": "0.060113199075769", "cost": "0.06", "record_count": 38}], "Referencia o separación de entradas inválida")
        require(len(expected["groups"]) == 8, "Referencia o separación de entradas inválida")
        require(sum(g["record_count"] for g in expected["groups"]) == 38, "Referencia o separación de entradas inválida")
        require(next(g for g in expected["groups"] if g["value"] == "DevTestLab")["record_count"] == 8, "Referencia o separación de entradas inválida")
        prompts = json.loads((originals / "prompts.json").read_text(encoding="utf-8"))["cases"]
        require(len(prompts) == 5 and all(set(c) == {"id", "prompt"} for c in prompts), "Referencia o separación de entradas inválida")
        private = json.loads((originals / "rubricas-privadas.json").read_text(encoding="utf-8"))["cases"]
        require({c["id"] for c in prompts} == {c["id"] for c in private}, "Referencia o separación de entradas inválida")
        require({c["behavior"] for c in private} == {"answer", "clarify", "abstain"}, "Referencia o separación de entradas inválida")
        return {"offline_status": "pass", "reproduced_files": len(paths),
                "runtime_status": "not_run", "llm_status": "not_run",
                "files_sha256": {str(p).replace("\\", "/"): hashlib.sha256((originals / p).read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.repo), indent=2))
