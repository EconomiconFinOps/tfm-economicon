"""JUP-131: pure validation shared by local preparation and the AWS runner.

Importing this module never reads credentials or contacts AWS.
"""
import hashlib
import ast
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_config(config, actual_sha):
    require(re.fullmatch(r"(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})", config.get("cycle_id", "")), "Invalid cycle_id")
    require(re.fullmatch(r"[0-9]{12}", config.get("account_id", "")), "Set the real account_id")
    require(re.fullmatch(r"[a-f0-9]{40}", config.get("source_sha", "")), "Set the reviewed full SHA")
    require(config["source_sha"] == actual_sha, "Source SHA differs from approved config")
    require(config.get("region") == "eu-west-1", "Demo must use Ireland")
    require(config.get("control_region") == "eu-west-3", "Control must use Paris")
    zones = config.get("availability_zones", [])
    require(len(zones) == 3 and len(set(zones)) == 3 and all(re.fullmatch(r"eu-west-1[a-z]", z) for z in zones), "Three Ireland AZs required")
    require(config.get("frontend_domain") == "economicon.danteinferno.es", "Unexpected frontend domain")
    require(config.get("origin_domain") == "origin.economicon.danteinferno.es", "Unexpected origin domain")
    require(re.fullmatch(r"Z[A-Z0-9]{5,}", config.get("route53_zone_id", "")), "Set verified public zone ID")
    for key in ("postgres_version", "rabbitmq_version"):
        require(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", config.get(key, "")), "Set verified " + key)
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", config.get("expires_at", "")), "Use UTC expiry YYYY-MM-DDTHH:MM:SSZ")
    stamp = datetime.fromisoformat(config["expires_at"].replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0, "expires_at must be UTC")
    for key in ("budget_eur", "estimated_cycle_eur", "available_credit_eur"):
        require(type(config.get(key)) in (int, float) and config[key] > 0, "Set verified " + key)
    require(config["estimated_cycle_eur"] <= min(config["budget_eur"], config["available_credit_eur"]) <= 60, "Cycle exceeds available budget")
    require(re.fullmatch(r"\d+", config.get("ci_run_id", "")), "CI run required")
    recipe = PurePosixPath(config.get("release_recipe", ""))
    require(not recipe.is_absolute() and ".." not in recipe.parts and str(recipe).startswith("infra/aws-cicd/"), "Recipe must be versioned under infra/aws-cicd")
    return config


def validate_recipe(recipe):
    require(re.fullmatch(r"[a-f0-9]{64}", recipe.get("application_sha256", "")), "Accepted application tree hash required")
    evidence = recipe.get("evidence", {})
    for key in ("postgresql", "cognito", "bedrock", "demo_data"):
        require(bool(re.fullmatch(r"[a-f0-9]{64}", evidence.get(key, {}).get("sha256", ""))), "Acceptance evidence missing: " + key)
        path = PurePosixPath(evidence[key].get("path", ""))
        require(not path.is_absolute() and ".." not in path.parts and str(path).startswith("docs/evidence/"), "Evidence must be versioned")
    for phase in ("bootstrap", "checks"):
        commands = recipe.get(phase, [])
        require(bool(commands), "Recipe needs " + phase)
        for command in commands:
            require(isinstance(command, list) and len(command) >= 2 and command[0] == "python", "Recipe commands must be Python argument arrays")
            path = PurePosixPath(command[1])
            require(str(path).startswith("tools/aws_demo/") and ".." not in path.parts and path.suffix == ".py", "Recipe script must be versioned in tools/aws_demo")
    for environment in recipe.get("application_environment", {}).values():
        for key in environment:
            require(not re.search(r"PASSWORD|SECRET|TOKEN|DATABASE_URL|RABBITMQ_URL|API_KEY|ACCESS_KEY|HMAC|PRIVATE_KEY|CREDENTIAL", key, re.I), "Secret-like field in public application_environment")
    models = recipe.get("bedrock_model_arns", [])
    require(isinstance(models, list) and all(
        model == "arn:aws:bedrock:eu-west-1::foundation-model/amazon.titan-embed-text-v2:0" for model in models
    ), "Only the reviewed regional Titan embedding model may enter this release")
    profile = recipe.get("bedrock_chat_profile_id")
    require(profile is None or profile in ("eu.amazon.nova-micro-v1:0", "eu.amazon.nova-lite-v1:0"),
            "Unreviewed Bedrock chat profile")
    return recipe


def validate_recipe_files(recipe, root):
    root = Path(root).resolve()
    require(recipe["application_sha256"] == application_digest(root), "Release evidence application tree differs")
    for entry in recipe["evidence"].values():
        path = root / entry["path"]
        require(path.resolve().is_relative_to(root) and path.is_file(), "Evidence file missing or outside source")
        require(source_sha256(path) == entry["sha256"], "Evidence hash mismatch")
    for phase in ("bootstrap", "checks"):
        for command in recipe[phase]:
            path = root / command[1]
            require(path.resolve().is_relative_to(root) and path.is_file(), "Release script missing or outside source")
            ast.parse(path.read_text(encoding="utf-8"))
    return recipe


def application_digest(root):
    """Bind acceptance to application bytes without a self-referential Git SHA."""
    digest = hashlib.sha256()
    for path in source_files(root):
        if path.relative_to(root).parts[0] == "apps":
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + bytes.fromhex(source_sha256(path)))
    return digest.hexdigest()


def source_sha256(path):
    data = Path(path).read_bytes()
    try:
        data.decode("utf-8")
        data = data.replace(b"\r\n", b"\n")
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(data).hexdigest()


def source_files(root):
    root = Path(root)
    excluded = {".git", ".work", ".superpowers", ".codex", ".agents", ".terraform", "node_modules", "__pycache__", ".venv", ".pytest_cache", ".turbo", "dist", "build", ".secrets"}
    generated_tokenizers = {
        f"apps/processor/app/agents/prompt_resources/jup035/chat/{version}/tokenizer.json"
        for version in ("v2", "v4")
    }
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in excluded and not (Path(directory) / name).is_symlink() and not getattr(Path(directory) / name, "is_junction", lambda: False)())
        for name in sorted(names):
            path = Path(directory) / name
            # Hash the versioned builder/manifests, not ignored build outputs.
            # CodePipeline's source archive contains neither generated tokenizer.
            if path.relative_to(root).as_posix() in generated_tokenizers:
                continue
            if name in excluded or path.is_symlink() or name.startswith(".env"):
                continue
            if name.endswith((".tfstate", ".tfstate.backup", ".tfplan", ".tfvars", ".tfvars.json", ".pyc", ".private.txt", "_override.tf.json")):
                continue
            yield path


def check_unlock_plan(plan):
    protections = {"deletion_protection", "enable_deletion_protection", "skip_final_snapshot"}
    for resource in plan.get("resource_changes", []):
        actions = resource["change"]["actions"]
        if resource.get("mode") == "data" or actions == ["no-op"]:
            continue
        require(actions == ["update"], "Unlock must not create, replace or delete resources")
        require(resource["address"] in ("aws_lb.api", "aws_cognito_user_pool.main",
                    'aws_db_instance.main["operational"]', 'aws_db_instance.main["vectors"]'), "Unexpected unlock target")
        before = resource["change"]["before"]
        after = resource["change"]["after"]
        changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
        require(changed <= protections, "Unlock would change non-protection fields: " + ",".join(sorted(changed)))


def state_key(config):
    return "economicon/defensa/" + config["cycle_id"] + "/terraform.tfstate"


def lock_key(config):
    return config["frontend_domain"]


def bind_plan(path, config):
    return {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "config_sha256": hashlib.sha256(__import__("json").dumps(config, sort_keys=True).encode()).hexdigest(),
            "source_sha": config["source_sha"], "cycle_id": config["cycle_id"], "state_key": state_key(config)}


def verify_binding(path, binding, config):
    require(binding == bind_plan(path, config), "Saved plan/config/source binding mismatch")


def resources(state):
    def walk(module):
        yield from module.get("resources", [])
        for child in module.get("child_modules", []):
            yield from walk(child)
    return list(walk(state.get("values", {}).get("root_module", {})))


def cleanup_inventory(state):
    buckets, repos = [], []
    for resource in resources(state):
        address = resource["address"]
        if address in ('aws_s3_bucket.main["frontend"]', 'aws_s3_bucket.main["documents"]'):
            buckets.append(resource["values"]["id"])
        if address in [f'aws_ecr_repository.application["{name}"]' for name in ("backend", "processor", "azure-cost-api")]:
            repos.append(resource["values"]["name"])
    return {"buckets": buckets, "repositories": repos}


def check_destroy_plan(plan, cycle):
    # All deletions must be exact addresses in the fixed application root module.
    # Untagged child resources are accepted only when their address/type belongs
    # to this reviewed template. No modules, imports or bootstrap resources.
    root = Path(__file__).resolve().parents[2] / "infra/aws-reference"
    allowed = set()
    for path in root.glob("*.tf"):
        allowed.update(re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', path.read_text()))
    addresses = []
    for resource in plan.get("resource_changes", []):
        if resource.get("mode") == "data" or resource["change"]["actions"] == ["no-op"]:
            continue
        address = resource["address"]
        match = re.fullmatch(r'(aws_[a-z0-9_]+)\.([a-z0-9_]+)(?:\[(?:"[^"\n]+"|0|[1-9][0-9]*)\])?', address)
        require(match is not None and match.groups() in allowed, "Destroy outside application template: " + address)
        require(resource["change"]["actions"] == ["delete"], "Destroy plan contains a non-delete action")
        before = resource["change"].get("before") or {}
        tags = before.get("tags_all") or before.get("tags") or {}
        if tags:
            require(tags.get("Project") == "economicon" and tags.get("Environment") == cycle, "Foreign resource tags")
        addresses.append(address)
    return addresses
