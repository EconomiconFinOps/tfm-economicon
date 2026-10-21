"""Manual CodeBuild entrypoint. No AWS activity occurs at import time.

AWS mutations require CodeBuild plus a content-addressed configuration, pinned
source, matching account and lease. Use prepare.py for offline rehearsal setup.
"""
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

from control import (require, validate_config, validate_recipe, validate_recipe_files, state_key, lock_key,
                     bind_plan, verify_binding, cleanup_inventory, check_destroy_plan, check_unlock_plan,
                     application_digest, source_files, source_sha256, resources)

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".work/aws-demo"
APPLICATIONS = ("backend", "processor", "azure-cost-api")


def run(args, env=None, data=None):
    result = subprocess.run(args, cwd=ROOT, env=env, input=data, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        # Terraform/CLI diagnostics can contain DSNs/passwords. No raw diagnostics
        # in CloudWatch; preserve in restricted S3 through the caller.
        (WORK / "last-error.private.txt").write_text(result.stdout + result.stderr)
        raise RuntimeError(f"{args[0]} failed (exit {result.returncode}); private diagnostic retained")
    return result.stdout


class Runner:
    def __init__(self):
        require(os.environ.get("CODEBUILD_BUILD_ID"), "Run cloud phases only inside CodeBuild")
        self.bucket = os.environ["CONTROL_BUCKET"]
        self.control_region = os.environ["CONTROL_REGION"]
        self.table = os.environ["LEASE_TABLE"]
        WORK.mkdir(parents=True, exist_ok=True)
        os.chmod(WORK, 0o700)
        self.control_env = dict(os.environ, AWS_DEFAULT_REGION=self.control_region, AWS_REGION=self.control_region,
                                AWS_PAGER="", TF_IN_AUTOMATION="1", TF_INPUT="0")
        key = os.environ["CONFIG_KEY"]
        require(key.startswith("configs/") and ".." not in key, "Invalid configuration key")
        raw = self.aws("s3", "cp", f"s3://{self.bucket}/{key}", "-", raw=True).encode()
        require(key == f"configs/{hashlib.sha256(raw).hexdigest()}.json", "Configuration must be immutable/content addressed")
        self.config = validate_config(json.loads(raw), os.environ["SOURCE_SHA"])
        require(self.config["account_id"] == os.environ["EXPECTED_ACCOUNT"], "Bootstrap account mismatch")
        identity = self.aws("sts", "get-caller-identity")
        require(identity["Account"] == self.config["account_id"], "AWS credentials belong to another account")
        self.config_key = key
        self.prefix = f'cycles/{self.config["cycle_id"]}/{self.config["source_sha"]}'
        assumed = self.aws("sts", "assume-role", "--role-arn", os.environ["DEPLOY_ROLE_ARN"],
                           "--role-session-name", "economicon-demo", "--duration-seconds", "3600")["Credentials"]
        self.deploy_env = dict(self.control_env, AWS_ACCESS_KEY_ID=assumed["AccessKeyId"],
                               AWS_SECRET_ACCESS_KEY=assumed["SecretAccessKey"], AWS_SESSION_TOKEN=assumed["SessionToken"],
                               AWS_REGION=self.config["region"], AWS_DEFAULT_REGION=self.config["region"],
                               TF_VAR_mq_admin_password=os.environ["MQ_ADMIN_PASSWORD"])
        self.vars = self.base_vars()

    def aws(self, *args, raw=False, deploy=False, payload=None):
        command = ["aws", *args]
        if not raw:
            command += ["--output", "json"]
        if payload is not None:
            request = WORK / "request.private.json"
            request.write_text(json.dumps(payload))
            command += ["--cli-input-json", "file://" + str(request)]
        output = run(command, self.deploy_env if deploy else self.control_env)
        return output if raw else (json.loads(output) if output.strip() else {})

    def base_vars(self):
        c = self.config
        return {"project": "economicon", "environment": c["cycle_id"], "region": c["region"],
                "availability_zones": c["availability_zones"], "route53_zone_id": c["route53_zone_id"],
                "frontend_domain": c["frontend_domain"], "origin_domain": c["origin_domain"],
                "postgres_version": c["postgres_version"], "postgres_parameter_family": "postgres" + c["postgres_version"].split(".")[0],
                "rabbitmq_version": c["rabbitmq_version"], "permissions_boundary_arn": os.environ["BOUNDARY_ARN"],
                "final_snapshot_suffix": c["cycle_id"] + "-" + c["source_sha"][:8],
                "deploy_applications": False, "application_adaptations_verified": False}

    def tf(self, *args):
        varfile = WORK / "cycle.tfvars.json"
        varfile.write_text(json.dumps(self.vars))
        command = ["terraform", "-chdir=infra/aws-reference", *args]
        if args[0] in ("plan", "apply") and not (args[0] == "apply" and args[-1].endswith(".tfplan")):
            command.append("-var-file=" + str(varfile))
        return run(command, self.deploy_env)

    def init(self):
        # State permissions belong to the control role, resource APIs to deploy.
        # Backend assumes control credentials directly; provider explicitly
        # assumes deploy role via generated override (never committed).
        override = ROOT / "infra/aws-reference/cicd_override.tf.json"
        override.write_text(json.dumps({"provider": {"aws": [
            {"region": self.config["region"], "allowed_account_ids": [self.config["account_id"]],
             "assume_role": [{"role_arn": os.environ["DEPLOY_ROLE_ARN"]}]},
            {"alias": "edge", "region": "us-east-1", "allowed_account_ids": [self.config["account_id"]],
             "assume_role": [{"role_arn": os.environ["DEPLOY_ROLE_ARN"]}]}]}}))
        self.deploy_env = dict(self.control_env, TF_VAR_mq_admin_password=os.environ["MQ_ADMIN_PASSWORD"])
        self.tf("init", "-reconfigure", "-input=false", "-lockfile=readonly",
                "-backend-config=bucket=" + self.bucket, "-backend-config=region=" + self.control_region,
                "-backend-config=key=" + state_key(self.config), "-backend-config=encrypt=true", "-backend-config=use_lockfile=true")

    def download(self, name):
        destination = WORK / name
        self.aws("s3", "cp", f"s3://{self.bucket}/{self.prefix}/{name}", str(destination), raw=True)
        return destination

    def upload(self, name):
        self.aws("s3", "cp", str(WORK / name), f"s3://{self.bucket}/{self.prefix}/{name}", raw=True)

    def lease(self, status=None, acquire=False):
        key = {"domain": {"S": lock_key(self.config)}}
        if acquire:
            self.aws("dynamodb", "put-item", payload={"TableName": self.table,
                "Item": dict(key, cycle={"S": self.config["cycle_id"]}, sha={"S": self.config["source_sha"]},
                             config_key={"S": self.config_key}, phase={"S": "PLANNED"}),
                "ConditionExpression": "attribute_not_exists(#d)", "ExpressionAttributeNames": {"#d": "domain"}})
        item = self.aws("dynamodb", "get-item", payload={"TableName": self.table, "Key": key, "ConsistentRead": True}).get("Item", {})
        require(item.get("cycle", {}).get("S") == self.config["cycle_id"] and item.get("sha", {}).get("S") == self.config["source_sha"] and item.get("config_key", {}).get("S") == self.config_key, "Domain leased by another cycle/config/SHA")
        if status:
            self.aws("dynamodb", "update-item", payload={"TableName": self.table, "Key": key,
                "UpdateExpression": "SET phase = :phase", "ConditionExpression": "cycle = :cycle AND sha = :sha",
                "ExpressionAttributeValues": {":phase": {"S": status}, ":cycle": {"S": self.config["cycle_id"]}, ":sha": {"S": self.config["source_sha"]}}})
        return item["phase"]["S"]

    def recipe(self):
        path = ROOT / self.config["release_recipe"]
        recipe = validate_recipe(json.loads(path.read_text()))
        return validate_recipe_files(recipe, ROOT)

    def validate(self):
        expiry = datetime.fromisoformat(self.config["expires_at"].replace("Z", "+00:00"))
        require(0 < (expiry - datetime.now(timezone.utc)).total_seconds() <= 8 * 3600, "Cycle must expire within eight hours of launch")
        self.recipe()  # Fail BEFORE provisioning if application adaptation is absent.
        token = os.environ["GITHUB_TOKEN"]
        request = urllib.request.Request(f'https://api.github.com/repos/EconomiconFinOps/tfm-economicon/actions/runs/{self.config["ci_run_id"]}',
            headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            ci = json.load(response)
        require(ci["head_sha"] == self.config["source_sha"] and ci["conclusion"] == "success" and ci["path"] == ".github/workflows/ci.yml", "CI for exact source SHA must pass")
        regions = self.aws("ec2", "describe-regions", "--all-regions", "--region", "eu-south-2", deploy=True)["Regions"]
        require(any(r["RegionName"] == "eu-south-2" and r["OptInStatus"] in ("opt-in-not-required", "opted-in") for r in regions), "Spain region not enabled")
        zone = self.aws("route53", "get-hosted-zone", "--id", self.config["route53_zone_id"], deploy=True)["HostedZone"]
        require(not zone["Config"]["PrivateZone"] and any(self.config["frontend_domain"] == zone["Name"].rstrip(".") or self.config["frontend_domain"].endswith("." + zone["Name"].rstrip(".")) for _ in [0]), "Wrong public DNS zone")
        for domain in (self.config["frontend_domain"], self.config["origin_domain"]):
            records = self.aws("route53", "list-resource-record-sets", "--hosted-zone-id", self.config["route53_zone_id"], deploy=True)["ResourceRecordSets"]
            require(not any(r["Name"].rstrip(".") == domain and r["Type"] in ("A", "AAAA", "CNAME") for r in records), "Existing DNS record must not be overwritten: " + domain)
        run(["python", "-m", "unittest", "discover", "-s", "tools/aws_demo", "-p", "test_*.py"], self.control_env)
        self.tf("init", "-backend=false", "-input=false", "-lockfile=readonly")
        self.tf("validate")
        self.tf("test")

    def build(self):
        for name in APPLICATIONS:
            context = "." if name == "backend" else "apps/" + name
            image = f'economicon-local/{name}:{self.config["source_sha"]}'
            run(["docker", "build", "--platform", "linux/amd64", "-f", f"apps/{name}/Dockerfile", "-t", image, context], self.control_env)
            run(["docker", "save", "-o", str(WORK / (name + ".tar")), image], self.control_env)
            self.upload(name + ".tar")
        bundle = WORK / "source.zip"
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in source_files(ROOT):
                archive.write(path, path.relative_to(ROOT).as_posix())
        self.upload("source.zip")

    def plan(self):
        self.validate()
        self.lease(acquire=True)
        self.schedule_expiry()
        self.init()
        self.make_plan("infra")

    def make_plan(self, name, destroy=False):
        path = WORK / (name + ".tfplan")
        args = ["plan", "-input=false", "-lock-timeout=120s", "-out=" + str(path)]
        if destroy:
            args.append("-destroy")
        self.tf(*args)
        if destroy:
            check_destroy_plan(json.loads(self.tf("show", "-json", str(path))), self.config["cycle_id"])
        (WORK / (name + ".binding.json")).write_text(json.dumps(bind_plan(path, self.config)))
        self.upload(name + ".tfplan")
        self.upload(name + ".binding.json")

    def apply_saved(self, name):
        plan = self.download(name + ".tfplan")
        binding = json.loads(self.download(name + ".binding.json").read_text())
        verify_binding(plan, binding, self.config)
        self.tf("apply", "-input=false", "-lock-timeout=120s", str(plan))

    def apply(self):
        require(datetime.now(timezone.utc) < datetime.fromisoformat(self.config["expires_at"].replace("Z", "+00:00")), "Cycle expired before approval/apply")
        require(self.lease() == "PLANNED", "Up plan has been superseded or torn down")
        self.lease("APPLYING")
        self.init()
        self.apply_saved("infra")
        self.lease("INFRA_READY")

    def outputs(self):
        return {k: v["value"] for k, v in json.loads(self.tf("output", "-json")).items()}

    def release(self):
        require(datetime.now(timezone.utc) < datetime.fromisoformat(self.config["expires_at"].replace("Z", "+00:00")), "Cycle expired before release")
        require(self.lease() == "INFRA_READY", "Infrastructure not ready")
        self.init()
        outputs = self.outputs()
        (WORK / "outputs.json").write_text(json.dumps(outputs))
        # Private recipe scripts use CONTROL outputs and AWS role via SDK/CLI;
        # they must register/run/wait ECS bootstrap tasks and populate secrets.
        recipe = self.recipe()
        images = {}
        with self.resource_credentials():
            registry = f'{self.config["account_id"]}.dkr.ecr.eu-south-2.amazonaws.com'
            password = self.aws("ecr", "get-login-password", "--region", "eu-south-2", deploy=True, raw=True)
            run(["docker", "login", "--username", "AWS", "--password-stdin", registry], self.deploy_env, password)
            for name in APPLICATIONS:
                archive = self.download(name + ".tar")
                run(["docker", "load", "-i", str(archive)], self.deploy_env)
                local_image = f'economicon-local/{name}:{self.config["source_sha"]}'
                tagged = outputs["ecr_repositories"][name] + ":" + self.config["source_sha"]
                run(["docker", "tag", local_image, tagged], self.deploy_env)
                run(["docker", "push", tagged], self.deploy_env)
                detail = self.aws("ecr", "describe-images", "--repository-name", outputs["ecr_repositories"][name].split("/", 1)[1], "--image-ids", "imageTag=" + self.config["source_sha"], deploy=True)
                images[name] = outputs["ecr_repositories"][name] + "@" + detail["imageDetails"][0]["imageDigest"]
            (WORK / "images.json").write_text(json.dumps(images))
            for command in recipe["bootstrap"]:
                run(command, dict(self.deploy_env, DEMO_OUTPUTS=str(WORK / "outputs.json"), DEMO_IMAGES=str(WORK / "images.json")))
        self.vars.update(deploy_applications=True, application_adaptations_verified=True, container_images=images)
        # Recipe supplies only public runtime configuration; secret values are
        # written to Secrets Manager by the controlled bootstrap task.
        self.vars["application_environment"] = recipe.get("application_environment", {})
        self.vars["bedrock_model_arns"] = recipe.get("bedrock_model_arns", [])
        self.make_plan("applications")
        self.apply_saved("applications")
        # Persist full non-secret variables so teardown never turns apps off
        # accidentally or replans from different inputs.
        self.upload("cycle.tfvars.json")
        self.upload("images.json")
        run(["corepack", "pnpm", "install", "--frozen-lockfile"], self.control_env)
        run(["corepack", "pnpm", "--filter", "@finops/frontend", "build"], dict(self.control_env,
            VITE_API_BASE_URL="/api", VITE_COGNITO_CLIENT_ID=outputs["cognito"]["client_id"], VITE_COGNITO_ISSUER=outputs["cognito"]["issuer"]))
        with self.resource_credentials():
            self.aws("s3", "sync", "apps/frontend/dist", "s3://" + outputs["buckets"]["frontend"], "--delete", raw=True, deploy=True)
            for command in recipe["checks"]:
                run(command, dict(self.deploy_env, DEMO_OUTPUTS=str(WORK / "outputs.json")))
        (WORK / "ready.json").write_text(json.dumps({"source_sha": self.config["source_sha"], "url": outputs["frontend_url"], "ready_at": datetime.now(timezone.utc).isoformat()}))
        self.upload("ready.json")
        self.lease("READY")

    @contextlib.contextmanager
    def resource_credentials(self):
        previous = self.deploy_env
        credentials = self.aws("sts", "assume-role", "--role-arn", os.environ["DEPLOY_ROLE_ARN"], "--role-session-name", "economicon-release")["Credentials"]
        self.deploy_env = dict(previous, AWS_ACCESS_KEY_ID=credentials["AccessKeyId"], AWS_SECRET_ACCESS_KEY=credentials["SecretAccessKey"], AWS_SESSION_TOKEN=credentials["SessionToken"], AWS_DEFAULT_REGION=self.config["region"], AWS_REGION=self.config["region"])
        try:
            yield
        finally:
            self.deploy_env = previous

    def plan_down(self):
        self.lease("TEARDOWN")  # Invalidates any stale, still-approved up plan.
        self.init()
        # Read actual state; a failed release may already have application tasks.
        state = json.loads(self.tf("show", "-json"))
        # Existing application instances are destroyed from state. Never
        # synthesize missing tasks or require a full image manifest for cleanup.
        self.vars["rehearsal_teardown"] = True
        # Only protection changes: do not apply a whole release configuration
        # reconstructed from incomplete outputs. Scoped targets avoid migrations.
        targets = [r["address"] for r in resources(state) if r["type"] in ("aws_db_instance", "aws_lb", "aws_cognito_user_pool")]
        if targets:
            path = WORK / "unlock.tfplan"
            self.tf("plan", "-input=false", "-out=" + str(path), *["-target=" + address for address in targets])
            check_unlock_plan(json.loads(self.tf("show", "-json", str(path))))
            self.tf("apply", "-input=false", str(path))
        self.make_plan("destroy", destroy=True)
        self.upload("cycle.tfvars.json")

    def stop_writers(self, state):
        for resource in resources(state):
            if resource["type"] == "aws_ecs_service":
                service = resource["values"]
                self.aws("ecs", "update-service", "--cluster", service["cluster"], "--service", service["name"], "--desired-count", "0", deploy=True)
                self.aws("ecs", "wait", "services-stable", "--cluster", service["cluster"], "--services", service["name"], deploy=True)
        for resource in resources(state):
            if resource["address"] == "aws_ecs_cluster.main":
                cluster = resource["values"]["id"]
                tasks = self.aws("ecs", "list-tasks", "--cluster", cluster, deploy=True).get("taskArns", [])
                for task in tasks:
                    self.aws("ecs", "stop-task", "--cluster", cluster, "--task", task, "--reason", "Disposable demo teardown", deploy=True)
                for start in range(0, len(tasks), 100):
                    self.aws("ecs", "wait", "tasks-stopped", "--cluster", cluster, "--tasks", *tasks[start:start + 100], deploy=True)

    def destroy(self):
        require(self.lease() == "TEARDOWN", "Down plan required")
        self.init()
        saved = self.download("destroy.tfplan")
        verify_binding(saved, json.loads(self.download("destroy.binding.json").read_text()), self.config)
        plan = json.loads(self.tf("show", "-json", str(saved)))
        check_destroy_plan(plan, self.config["cycle_id"])
        state = json.loads(self.tf("show", "-json"))
        planned_ids = {r["address"]: (r["change"].get("before") or {}).get("id") for r in plan.get("resource_changes", []) if r.get("mode", "managed") == "managed"}
        actual_ids = {r["address"]: r["values"].get("id") for r in resources(state) if r.get("mode", "managed") == "managed"}
        require(planned_ids == actual_ids, "State resource inventory changed after down plan; replan before cleaning")
        inventory = cleanup_inventory(state)
        with self.resource_credentials():
            self.stop_writers(state)
            for bucket in inventory["buckets"]:
                # CLI pagination automatically collects all versions; delete in
                # bounded API batches, checking per-object failures explicitly.
                result = self.aws("s3api", "list-object-versions", "--bucket", bucket, deploy=True)
                objects = [{"Key": o["Key"], "VersionId": o["VersionId"]} for o in result.get("Versions", []) + result.get("DeleteMarkers", [])]
                for start in range(0, len(objects), 1000):
                    deleted = self.aws("s3api", "delete-objects", deploy=True, payload={"Bucket": bucket, "Delete": {"Objects": objects[start:start + 1000], "Quiet": True}})
                    require(not deleted.get("Errors"), "S3 object deletion failed")
            for repository in inventory["repositories"]:
                images = self.aws("ecr", "list-images", "--repository-name", repository, deploy=True).get("imageIds", [])
                for start in range(0, len(images), 100):
                    result = self.aws("ecr", "batch-delete-image", deploy=True, payload={"repositoryName": repository, "imageIds": images[start:start + 100]})
                    require(not result.get("failures"), "ECR image deletion failed")
        self.apply_saved("destroy")
        remaining = [r for r in resources(json.loads(self.tf("show", "-json"))) if r.get("mode", "managed") == "managed"]
        require(not remaining, "Terraform state still contains managed resources")
        with self.resource_credentials():
            residuals = self.inspect_residuals()
        report = {"cycle_id": self.config["cycle_id"], "terraform_managed_resources": 0, "residual_inventory": residuals,
                  "cost_zero_verified": False, "pending": ["KMS scheduled deletion (30d)", "Secrets Manager recovery (30d)",
                    "RDS retained automated backups, snapshots and exported logs must be inventoried", "Bootstrap/state/artifacts remain in Paris"],
                  "destroyed_at": datetime.now(timezone.utc).isoformat()}
        (WORK / "retirement.json").write_text(json.dumps(report))
        self.upload("retirement.json")
        require(not residuals["active"], "Active residual AWS resources remain; inspect retirement.json and retain lease")
        try:
            self.aws("scheduler", "delete-schedule", "--name", "economicon-" + self.config["cycle_id"])
        except RuntimeError:
            diagnostic = WORK / "last-error.private.txt"
            if not diagnostic.exists() or "ResourceNotFoundException" not in diagnostic.read_text():
                raise
        self.aws("dynamodb", "delete-item", payload={"TableName": self.table, "Key": {"domain": {"S": lock_key(self.config)}},
            "ConditionExpression": "cycle = :cycle AND sha = :sha", "ExpressionAttributeValues": {":cycle": {"S": self.config["cycle_id"]}, ":sha": {"S": self.config["source_sha"]}}})

    def schedule_expiry(self):
        target = {"ProjectName": os.environ["RUNNER_NAME"], "SourceTypeOverride": "S3",
                  "SourceLocationOverride": f"{self.bucket}/{self.prefix}/source.zip", "ArtifactsOverride": {"Type": "NO_ARTIFACTS"},
                  "EnvironmentVariablesOverride": [{"Name": key, "Value": value, "Type": "PLAINTEXT"} for key, value in
                    {"PHASE": "expire", "CONFIG_KEY": self.config_key, "SOURCE_SHA": self.config["source_sha"], "EXECUTION_ID": "expiry"}.items()]}
        self.aws("scheduler", "create-schedule", payload={"Name": "economicon-" + self.config["cycle_id"],
            "ScheduleExpression": "at(" + self.config["expires_at"].removesuffix("Z") + ")", "ScheduleExpressionTimezone": "UTC",
            "FlexibleTimeWindow": {"Mode": "OFF"}, "ActionAfterCompletion": "DELETE",
            "Target": {"Arn": "arn:aws:scheduler:::aws-sdk:codebuild:startBuild", "RoleArn": os.environ["EXPIRY_ROLE_ARN"],
                       "Input": json.dumps(target), "DeadLetterConfig": {"Arn": os.environ["EXPIRY_DLQ_ARN"]},
                       "RetryPolicy": {"MaximumRetryAttempts": 3, "MaximumEventAgeInSeconds": 3600}}})

    def inspect_residuals(self):
        result = {"active": [], "pending_deletion": [], "regions": ["eu-south-2", "us-east-1"]}
        for region in result["regions"]:
            inventory = self.aws("resourcegroupstaggingapi", "get-resources", "--region", region, "--tag-filters",
                "Key=Project,Values=economicon", "Key=Environment,Values=" + self.config["cycle_id"], deploy=True)
            for resource in inventory.get("ResourceTagMappingList", []):
                arn = resource["ResourceARN"]
                if ":kms:" in arn:
                    details = self.aws("kms", "describe-key", "--key-id", arn, "--region", region, deploy=True)["KeyMetadata"]
                    pending = details.get("KeyState") == "PendingDeletion"
                elif ":secretsmanager:" in arn:
                    details = self.aws("secretsmanager", "describe-secret", "--secret-id", arn, "--region", region, deploy=True)
                    pending = bool(details.get("DeletedDate"))
                else:
                    pending = False
                result["pending_deletion" if pending else "active"].append(arn)
        return result


def main():
    runner = None
    try:
        runner = Runner()
        phase = os.environ["PHASE"]
        methods = {"validate": runner.validate, "build": runner.build, "plan": runner.plan,
                   "apply": runner.apply, "release": runner.release, "plan-down": runner.plan_down,
                   "destroy": runner.destroy, "expire": lambda: (runner.plan_down(), runner.destroy())}
        require(phase in methods, "Unknown phase")
        methods[phase]()
        print(json.dumps({"phase": phase, "cycle": runner.config["cycle_id"], "result": "SUCCESS"}))
    except Exception as error:
        if runner and (WORK / "last-error.private.txt").exists():
            runner.upload("last-error.private.txt")
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
