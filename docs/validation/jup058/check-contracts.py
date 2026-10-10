"""Read-only JUP-058 fixture check against the in-progress JUP-033/034 code.

Run with Python >=3.11, Pydantic 2, Node and the frontend's installed TypeScript:
  python contract-check.py
Optional --frontend/--jup033/--jup034 arguments select repository roots.
Writes JSON evidence to stdout only; imports never write bytecode caches.
This is local contract/service compatibility, not HTTP or deployed integration.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import platform
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def differences(expected, actual, path="$") -> list[dict]:
    if type(expected) is not type(actual):
        return [{"path": path, "fixture": expected, "service": actual}]
    if isinstance(expected, dict):
        result = []
        for key in sorted(expected.keys() | actual.keys()):
            if key not in expected or key not in actual:
                result.append({"path": f"{path}.{key}", "fixture": expected.get(key), "service": actual.get(key)})
            else:
                result.extend(differences(expected[key], actual[key], f"{path}.{key}"))
        return result
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [{"path": path, "fixture": expected, "service": actual}]
        return [item for index, (left, right) in enumerate(zip(expected, actual))
                for item in differences(left, right, f"{path}[{index}]")]
    return [] if expected == actual else [{"path": path, "fixture": expected, "service": actual}]


NODE_EXPORT = r"""
const fs = require('node:fs');
const ts = require(process.argv[2]);
function loadTypescript(filename) {
  const result = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
    fileName: filename,
    reportDiagnostics: true,
  });
  const errors = (result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error);
  if (errors.length) throw new Error(ts.formatDiagnosticsWithColorAndContext(errors, {
    getCurrentDirectory: () => process.cwd(), getCanonicalFileName: x => x, getNewLine: () => '\n'
  }));
  const module = {exports: {}};
  new Function('exports', 'module', 'require', result.outputText)(module.exports, module, name => {
    throw new Error('Unexpected runtime dependency: ' + name);
  });
  return module.exports;
}
const fixture = loadTypescript(process.argv[1]);
const guards = loadTypescript(process.argv[3]);
const serialized = JSON.parse(JSON.stringify({
  recommendations: fixture.demoRecommendationReport,
  impact: fixture.demoImpactReport,
}));
process.stdout.write(JSON.stringify({
  ...serialized,
  typescript_version: ts.version,
  frontend_recommendation_guard: guards.isRecommendationReport(serialized.recommendations),
}));
"""


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend", type=Path, default=root)
    parser.add_argument("--jup033", type=Path, default=root)
    parser.add_argument("--jup034", type=Path, default=root)
    args = parser.parse_args()
    files = {
        "recommendation_schema": args.jup033 / "apps/backend/app/schemas/recommendations.py",
        "billing_schema_dependency": args.jup033 / "apps/backend/app/schemas/billing.py",
        "impact_schema": args.jup034 / "apps/backend/app/schemas/recommendation_impact.py",
        "impact_service": args.jup034 / "apps/backend/app/services/recommendation_impact.py",
        "fixture": args.frontend / "apps/frontend/src/data/demo/recommendationsPanel.ts",
        "frontend_contract": args.frontend / "apps/frontend/src/services/recommendations.ts",
    }
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Local serialized fixtures and actual proposed Pydantic models/service; no HTTP, database or deployment",
        "sources": {key: {"path": str(path.resolve()), "sha256": digest(path)} for key, path in files.items()},
        "checks": [],
        "limitations": [
            "Other chats own these dependency checkouts; source hashes identify the observed versions.",
            "JUP-058 data is explicitly authored demonstration data, not output observed from the JUP-033 engine.",
            "No validation of real tenant authorization, database contents, endpoint availability or human acceptance.",
        ],
    }
    import pydantic
    report["versions"] = {"python": platform.python_version(), "pydantic": pydantic.__version__}
    sys.path.insert(0, str((args.jup033 / "apps/backend").resolve()))
    recommendation_module = importlib.import_module("app.schemas.recommendations")
    impact_module = load_file("app.schemas.recommendation_impact", files["impact_schema"])
    impact_service = load_file("app.services.recommendation_impact", files["impact_service"])
    frontend = args.frontend / "apps/frontend"
    process = subprocess.run([
        "node", "-e", NODE_EXPORT, str(files["fixture"].resolve()),
        str((frontend / "node_modules/typescript").resolve()),
        str(files["frontend_contract"].resolve()),
    ], cwd=frontend, capture_output=True, text=True, encoding="utf-8", check=True)
    fixtures = json.loads(process.stdout)
    report["versions"]["typescript"] = fixtures.pop("typescript_version")
    report["versions"]["node"] = subprocess.check_output(["node", "--version"], text=True).strip()
    report["checks"].append({"name": "frontend guard accepts serialized recommendation fixture", "passed": fixtures.pop("frontend_recommendation_guard")})

    for key, model in (("recommendations", recommendation_module.RecommendationReport),
                       ("impact", impact_module.ImpactReport)):
        validated = model.model_validate(fixtures[key])
        serialized = validated.model_dump(mode="json")
        report["checks"].append({"name": f"{key}: Pydantic accepts fixture and JSON round-trip is identical", "passed": serialized == fixtures[key]})
        encoded_schema = json.dumps(model.model_json_schema(), sort_keys=True, separators=(",", ":")).encode()
        report["sources"]["recommendation_schema" if key == "recommendations" else "impact_schema"]["resolved_json_schema_sha256"] = hashlib.sha256(encoded_schema).hexdigest()

    request = impact_module.ImpactRequest.model_validate({
        "schema_version": fixtures["impact"]["schema_version"],
        "baseline_month": fixtures["impact"]["baseline_month"],
        "scenarios": [item["scenario"] for item in fixtures["impact"]["recommendations"]],
    })
    report["checks"].append({"name": "ImpactRequest validates the fixture scenarios together", "passed": True})
    actual = impact_service.evaluate_recommendation_impact(request, fixtures["impact"]["tenant_id"]).model_dump(mode="json")
    # The demonstration has authored explanatory prose. Financial fields,
    # selection membership and exclusions must match the real service exactly.
    expected = {key: value for key, value in fixtures["impact"].items() if key not in {"assumptions", "limitations"}}
    computed = {key: value for key, value in actual.items() if key not in {"assumptions", "limitations"}}
    delta = differences(expected, computed)
    report["checks"].append({"name": "impact financial fields, membership and exclusions match the actual JUP-034 service", "passed": not delta, "differences": delta})

    invalid_approval = copy.deepcopy(fixtures["recommendations"])
    invalid_approval["recommendations"][0]["requires_human_approval"] = False
    invalid_evidence = copy.deepcopy(fixtures["recommendations"])
    invalid_evidence["recommendations"][0]["evidence_ids"] = ["cost-query:sha256:" + "f" * 64]
    invalid_pair = copy.deepcopy(fixtures["impact"])
    invalid_pair["recommendations"][0]["scenario"]["target_monthly_cost"] = None
    for name, model, value in (
        ("rejects false human approval requirement", recommendation_module.RecommendationReport, invalid_approval),
        ("rejects broken evidence references", recommendation_module.RecommendationReport, invalid_evidence),
        ("rejects unpaired baseline/target costs", impact_module.ImpactReport, invalid_pair),
    ):
        try:
            model.model_validate(value)
            passed = False
        except pydantic.ValidationError:
            passed = True
        report["checks"].append({"name": name, "passed": passed})

    changed = [key for key, path in files.items() if digest(path) != report["sources"][key]["sha256"]]
    report["checks"].append({"name": "source hashes stable during the run", "passed": not changed, "changed": changed})
    report["passed"] = all(check["passed"] for check in report["checks"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
