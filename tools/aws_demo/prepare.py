"""Prepare rehearsal files locally. Never imports boto, reads AWS keys or runs AWS."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from control import validate_config, validate_recipe, validate_recipe_files, application_digest, state_key, master_budget_waiver

ROOT = Path(__file__).resolve().parents[2]


def prepare(config, output, actual_sha):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    blockers = []
    try:
        validate_config(config, actual_sha)
    except (ValueError, KeyError, TypeError) as error:
        blockers.append(str(error))
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("REPLACE"):
            blockers.append("Provide verified " + key)
    recipe_name = config.get("release_recipe")
    recipe_path = ROOT / recipe_name if isinstance(recipe_name, str) else ROOT
    if (not recipe_path.resolve().is_relative_to(ROOT.resolve())
            or not isinstance(recipe_name, str) or not recipe_path.is_file()):
        blockers.append("Application adaptation evidence and release recipe not supplied")
    else:
        try:
            recipe = validate_recipe(json.loads(recipe_path.read_text()))
            validate_recipe_files(recipe, ROOT)
        except (ValueError, OSError, KeyError) as error:
            blockers.append("Release evidence: " + str(error))
    raw = (json.dumps(config, sort_keys=True, indent=2) + "\n").encode()
    key = "configs/" + hashlib.sha256(raw).hexdigest() + ".json"
    (output / "config.json").write_bytes(raw)
    for direction in ("up", "down"):
        request = {"name": "economicon-defensa-" + direction,
            "sourceRevisions": [{"actionName": "Source", "revisionType": "COMMIT_ID", "revisionValue": config["source_sha"]}],
            "variables": [{"name": "ConfigKey", "value": key}]}
        (output / ("start-" + direction + ".json")).write_text(json.dumps(request, indent=2) + "\n")
    cost_check = "regional estimate; master budget requirement waived, organization limit unverified" if master_budget_waiver(config) else "remaining project budget and regional estimate"
    report = {"local_preparation": "COMPLETE", "aws_deployable": not blockers,
              "aws_preflight_executed": False, "aws_resources_created": False,
              "config_key": key, "state_key": state_key(config) if isinstance(config.get("cycle_id"), str) else None,
              "blockers": sorted(set(blockers)),
              "application_sha256": application_digest(ROOT),
              "required_cloud_checks": ["account/IAM", cost_check, "Ireland AZs and quotas",
                "RDS/MQ versions/classes", "DNS ownership and delegation", "model access", "exact-SHA develop push CI and ancestry"]}
    (output / "readiness.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="infra/aws-cicd/ensayo1.example.json")
    parser.add_argument("--output", default=".work/ensayo1")
    parser.add_argument("--allow-incomplete", action="store_true", help="Prepare blocked files successfully without claiming deployability")
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = prepare(json.loads(Path(args.config).read_text()), args.output, sha)
    print(json.dumps(report, indent=2))
    return 0 if report["aws_deployable"] or args.allow_incomplete else 2


if __name__ == "__main__":
    raise SystemExit(main())
