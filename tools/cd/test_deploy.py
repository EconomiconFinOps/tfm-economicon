import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import deploy
import smoke


class GateTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.run = {"id": 10, "run_attempt": 1, "head_sha": self.sha,
                    "head_branch": "develop", "event": "push", "status": "completed",
                    "conclusion": "success", "head_repository": {"full_name": deploy.REPOSITORY}}

    def test_accepts_current_success_and_manual_develop_rerun(self):
        self.assertEqual(deploy.eligible_run([self.run], self.sha), self.run)
        self.run["event"] = "workflow_dispatch"
        self.assertEqual(deploy.eligible_run([self.run], self.sha), self.run)

    def test_rejects_missing_stale_failed_cancelled_pending_fork_or_branch_runs(self):
        self.assertIsNone(deploy.eligible_run([], self.sha))
        for key, value in [("head_sha", "b" * 40), ("head_branch", "main"),
                           ("event", "pull_request"), ("status", "in_progress"),
                           ("conclusion", "failure"), ("conclusion", "cancelled"),
                           ("head_repository", None),
                           ("head_repository", {"full_name": "fork/repo"})]:
            with self.subTest(key=key, value=value):
                changed = {**self.run, key: value}
                self.assertIsNone(deploy.eligible_run([changed], self.sha))

    def test_failed_latest_run_or_attempt_blocks_older_success(self):
        self.assertIsNone(deploy.eligible_run([self.run, {**self.run, "id": 11, "conclusion": "failure"}], self.sha))
        self.assertIsNone(deploy.eligible_run([self.run, {**self.run, "run_attempt": 2, "conclusion": "failure"}], self.sha))

    @patch.object(deploy, "run")
    @patch.object(deploy, "api")
    def test_poll_does_not_touch_docker_or_git_without_success(self, api, run):
        api.side_effect = [{"object": {"sha": self.sha}}, {"workflow_runs": []}]
        deploy.poll(Path("unused"))
        run.assert_not_called()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        deploy.init(self.root, 19252)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "docker-compose.yml").write_text("services: {}")
        (self.source / ".env").write_text("SECRET=do-not-copy")
        self.old = "a" * 40
        self.new = "b" * 40

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, sha, slot):
        release = self.root / "releases" / sha
        release.mkdir(parents=True)
        deploy.atomic_json(release / "release.json", {"sha": sha, "slot": slot, "api_port": 19257 + 100 * slot,
                                                       "frontend_port": 19260 + 100 * slot})
        return release

    def state(self, current=None, previous=None):
        if current:
            deploy.atomic_json(self.root / "state.json", {"current": current, "previous": previous, "slot": 0})

    def test_init_generates_secrets_and_refuses_to_overwrite(self):
        content = (self.root / "secrets.json").read_text()
        with self.assertRaises(ValueError):
            deploy.init(self.root, 19252)
        self.assertEqual(content, (self.root / "secrets.json").read_text())
        secrets = json.loads(content)
        self.assertGreaterEqual(len(secrets["AUTH_SECRET_KEY"]), 32)
        self.assertNotEqual(secrets["POSTGRES_PASSWORD"], secrets["DEMO_PASSWORD"])
        self.assertTrue(secrets["DATABASE_URL"].startswith("cockroachdb+psycopg://"))
        self.assertTrue(secrets["VECTOR_DATABASE_URL"].startswith("postgresql+psycopg://"))

    def test_evaluation_password_is_added_once_and_preserves_configured_values(self):
        name = "GRAFANA_EVALUATION_DB_PASSWORD"
        path = self.root / "secrets.json"
        initial = json.loads(path.read_text())
        self.assertTrue(name in initial)
        self.assertIsInstance(initial[name], str)
        self.assertGreaterEqual(len(initial[name]), 32)

        legacy = {key: value for key, value in initial.items() if key != name}
        deploy.atomic_json(path, legacy)
        upgraded = deploy.document_secrets(self.root)
        self.assertTrue(all(upgraded[key] == value for key, value in legacy.items()))
        self.assertGreaterEqual(len(upgraded[name]), 32)
        after_upgrade = path.read_bytes()
        deploy.document_secrets(self.root)
        self.assertTrue(path.read_bytes() == after_upgrade)

        configured = dict(upgraded, **{name: "synthetic-existing-evaluation-password"})
        deploy.atomic_json(path, configured)
        before = path.read_bytes()
        for _ in range(2):
            self.assertTrue(deploy.document_secrets(self.root) == configured)
            self.assertTrue(path.read_bytes() == before)

    def test_invalid_port_base_rejected_before_creating_files(self):
        for port in (0, 1023, 65424, 65425, 65535):
            with self.assertRaises(ValueError):
                deploy.init(self.root / "invalid", port)
        self.assertFalse((self.root / "invalid").exists())

    def test_init_provisions_distinct_document_credentials(self):
        values = json.loads((self.root / "secrets.json").read_text())
        names = ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD",
                 "DOCUMENT_S3_ACCESS_KEY", "DOCUMENT_S3_SECRET_KEY")
        self.assertEqual(len({values[name] for name in names}), len(names))
        self.assertEqual(values["DOCUMENT_S3_BUCKET"], "document-ingestion")
        self.assertEqual(values["DOCUMENT_S3_REGION"], "us-east-1")

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_prepare_upgrades_legacy_document_secrets_once_without_rotation(self, run):
        path = self.root / "secrets.json"
        original = json.loads(path.read_text())
        for name in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "DOCUMENT_S3_SECRET_KEY",
                     "DOCUMENT_S3_BUCKET", "DOCUMENT_S3_REGION"):
            original.pop(name, None)
        original.update(DOCUMENT_S3_ACCESS_KEY="existing-document-user", DOCUMENT_S3_BUCKET="existing-bucket")
        deploy.atomic_json(path, original)
        hmac = (self.root / "private" / "chat-hmac").read_bytes()
        first = deploy.prepare(self.root, self.source, self.old, 0)
        upgraded = path.read_bytes()
        values = json.loads(upgraded)
        for name, value in original.items():
            self.assertEqual(values[name], value)
        for name in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "DOCUMENT_S3_SECRET_KEY"):
            self.assertTrue(values[name])
        second = deploy.prepare(self.root, self.source, self.new, 1)
        self.assertEqual(path.read_bytes(), upgraded)
        self.assertEqual((self.root / "private" / "chat-hmac").read_bytes(), hmac)
        for release in (first, second):
            self.assertIn("DOCUMENT_S3_BUCKET='existing-bucket'", (release / ".env").read_text())

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_document_ports_endpoints_and_origins_follow_each_slot(self, run):
        ports = []
        for sha, slot in ((self.old, 0), (self.new, 1)):
            release = deploy.prepare(self.root, self.source, sha, slot)
            values = dict(line.split("=", 1) for line in (release / ".env").read_text().splitlines())
            base = 19252 + slot * 100
            self.assertEqual(values["LANDING_HOST_PORT"], f"'{base + 12}'")
            self.assertEqual(values["MINIO_HOST_PORT"], f"'{base + 11}'")
            self.assertEqual(values["DOCUMENT_S3_ENDPOINT"], "'http://minio:9000'")
            self.assertEqual(values["DOCUMENT_S3_PUBLIC_ENDPOINT"], f"'http://127.0.0.1:{base + 11}'")
            self.assertEqual(values["DOCUMENT_CORS_ORIGINS"],
                             f"'http://127.0.0.1:{base + 8},http://localhost:{base + 8}'")
            ports.append({int(values[name].strip("'")) for name in deploy.PORTS})
        self.assertTrue(ports[0].isdisjoint(ports[1]))

    def test_chat_hmac_initialization_reuse_and_legacy_root(self):
        path = self.root / 'private' / 'chat-hmac'
        original = path.read_bytes()
        self.assertEqual(len(original), 64)
        self.assertEqual(deploy.chat_hmac_file(self.root), path.resolve())
        self.assertEqual(path.read_bytes(), original)
        legacy = self.root / 'legacy'
        legacy.mkdir()
        self.assertEqual(len(deploy.chat_hmac_file(legacy).read_bytes()), 64)
        path.chmod(0o600)
        path.write_bytes(b'invalid')
        with self.assertRaisesRegex(ValueError, 'refusing to rotate'):
            deploy.chat_hmac_file(self.root)
        self.assertEqual(path.read_bytes(), b'invalid')

    @patch.object(deploy, "run")
    def test_prepare_private_ports_absolute_paths_and_shell_dollars(self, run):
        def render(*args, **kwargs):
            staging = self.root / "releases" / (self.new + ".preparing")
            return json.dumps({"services": {"backend": {"ports": [{"published": "19257", "target": 8000}],
                  "build": {"context": str(staging / "apps/backend")},
                  "entrypoint": ["sh", "-ec", 'echo "$$RUNTIME_ENVIRONMENT"; exec "$$@"'],
                  "volumes": [{"type": "bind", "source": str(staging / "file")}]}}, "name": "test"})
        run.side_effect = render
        release = deploy.prepare(self.root, self.source, self.new, 1)
        config = json.loads((release / "compose.json").read_text())
        backend = config["services"]["backend"]
        self.assertEqual(backend["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(backend["build"]["context"], str(release / "apps/backend"))
        self.assertEqual(backend["volumes"][0]["source"], str(release / "file"))
        self.assertIn("$$RUNTIME_ENVIRONMENT", backend["entrypoint"][2])
        self.assertNotIn("$$$$", backend["entrypoint"][2])
        self.assertNotIn("do-not-copy", (release / ".env").read_text())
        self.assertIn("API_HOST_PORT='19357'", (release / ".env").read_text())
        self.assertIn("CHAT_HMAC_FILE='" + str((self.root / 'private' / 'chat-hmac').resolve()) + "'", (release / '.env').read_text())
        self.assertFalse((release / 'private' / 'chat-hmac').exists())
        with self.assertRaises(ValueError):
            deploy.prepare(self.root, self.source, self.new, 0)

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_prepare_gives_each_slot_its_own_chat_private_network(self, run):
        environments = []
        original_hmac = (self.root / "private" / "chat-hmac").read_bytes()
        for sha, slot in ((self.old, 0), (self.new, 1)):
            release = deploy.prepare(self.root, self.source, sha, slot)
            environments.append(dict(
                line.split("=", 1) for line in (release / ".env").read_text().splitlines()
            ))
        self.assertEqual(environments[0]["CHAT_PRIVATE_SUBNET"], "'172.30.35.0/24'")
        self.assertEqual(environments[1]["CHAT_PRIVATE_SUBNET"], "'172.30.36.0/24'")
        self.assertEqual(environments[0]["PROCESSOR_CHAT_PRIVATE_IP"], "'172.30.35.3'")
        self.assertEqual(environments[1]["PROCESSOR_CHAT_PRIVATE_IP"], "'172.30.36.3'")
        self.assertEqual(environments[0]["CHAT_HMAC_FILE"], environments[1]["CHAT_HMAC_FILE"])
        self.assertEqual((self.root / "private" / "chat-hmac").read_bytes(), original_hmac)

    def test_invalid_sha_never_copies_source(self):
        with self.assertRaises(ValueError):
            deploy.prepare(self.root, self.source, "../../outside", 0)

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_prepare_excludes_root_and_nested_secrets_and_preserves_hmac(self, run):
        secret = self.root / "private" / "chat-hmac"
        original = secret.read_bytes()
        for parent in (self.source, self.source / "apps" / "processor"):
            directory = parent / ".secrets"
            directory.mkdir(parents=True)
            (directory / "application-key").write_text("synthetic-never-copy")
        (self.source / "ordinary.txt").write_text("keep-source")
        release = deploy.prepare(self.root, self.source, self.new, 0)
        self.assertFalse((release / ".secrets").exists())
        self.assertFalse((release / "apps" / "processor" / ".secrets").exists())
        self.assertEqual((release / "ordinary.txt").read_text(), "keep-source")
        self.assertEqual(secret.read_bytes(), original)

    def test_chat_hmac_rejects_symlink_file_or_directory(self):
        for link_directory in (False, True):
            with self.subTest(directory=link_directory):
                root = self.root / ("directory-link" if link_directory else "file-link")
                root.mkdir()
                target = self.root / ("target-dir" if link_directory else "target-key")
                if link_directory:
                    target.mkdir()
                    link = root / "private"
                else:
                    target.write_bytes(b"s" * 64)
                    (root / "private").mkdir()
                    link = root / "private" / "chat-hmac"
                try:
                    link.symlink_to(target, target_is_directory=link_directory)
                except OSError as error:
                    if getattr(error, "winerror", None) != 1314:
                        raise
                    # Windows without link privilege still exercises both guards.
                    # Linux/CI exercises real filesystem links without this path.
                    with patch.object(Path, "is_symlink", lambda candidate: candidate == link):
                        with self.assertRaisesRegex(ValueError, "symlink"):
                            deploy.chat_hmac_file(root)
                    continue
                with self.assertRaisesRegex(ValueError, "symlink"):
                    deploy.chat_hmac_file(root)

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_success_switches_only_after_smoke_and_preserves_volumes(self, compose, smoke):
        release = self.fixture(self.new, 1)
        self.fixture(self.old, 0)
        self.state(self.old)
        def check(release):
            self.assertEqual(json.loads((self.root / "state.json").read_text())["current"], self.old)
        smoke.side_effect = check
        deploy.deploy(self.root, release, 123)
        state = json.loads((self.root / "state.json").read_text())
        self.assertEqual((state["current"], state["previous"], state["run_id"]), (self.new, self.old, 123))
        self.assertEqual(compose.call_args.args, (self.root / "releases" / self.old, "down", "--remove-orphans"))
        self.assertNotIn("-v", str(compose.call_args_list))

    @patch.object(deploy, "smoke", side_effect=RuntimeError("bad smoke"))
    @patch.object(deploy, "compose")
    def test_failed_smoke_keeps_previous_running_and_pointer(self, compose, smoke):
        release = self.fixture(self.new, 1)
        self.state(self.old)
        with self.assertRaises(RuntimeError):
            deploy.deploy(self.root, release)
        self.assertEqual(json.loads((self.root / "state.json").read_text())["current"], self.old)
        self.assertTrue((self.root / "failure.json").exists())
        self.assertTrue(all(call.args[0] == release for call in compose.call_args_list))

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_failed_build_does_not_start_candidate(self, compose, smoke):
        release = self.fixture(self.new, 1)
        compose.side_effect = [RuntimeError("build failed"), None]
        with self.assertRaises(RuntimeError):
            deploy.deploy(self.root, release)
        self.assertEqual([call.args[1] for call in compose.call_args_list], ["build", "down"])
        smoke.assert_not_called()
        self.assertFalse((self.root / "state.json").exists())

    @patch.object(deploy, "compose")
    def test_idempotent_deploy_never_recreates_current(self, compose):
        release = self.fixture(self.new, 0)
        self.state(self.new)
        deploy.deploy(self.root, release)
        compose.assert_not_called()

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_verified_rollback_pauses_poll_to_avoid_immediate_redeployment(self, compose, smoke):
        self.fixture(self.old, 1)
        self.state(self.new, self.old)
        deploy.rollback(self.root)
        state = json.loads((self.root / "state.json").read_text())
        self.assertEqual(state["current"], self.old)
        self.assertTrue(state["manual_rollback"])
        with patch.object(deploy, "api", side_effect=[{"object": {"sha": self.new}},
                   {"workflow_runs": [{"id": 1, "head_sha": self.new, "head_branch": "develop", "event": "push",
                    "status": "completed", "conclusion": "success", "head_repository": {"full_name": deploy.REPOSITORY}}]}]), patch.object(deploy, "run") as run:
            deploy.poll(self.root)
            run.assert_not_called()

    @patch.object(deploy, "smoke", side_effect=RuntimeError("unhealthy rollback"))
    @patch.object(deploy, "compose")
    def test_failed_rollback_does_not_stop_current(self, compose, smoke):
        self.fixture(self.old, 1)
        self.state(self.new, self.old)
        with self.assertRaises(RuntimeError):
            deploy.rollback(self.root)
        self.assertEqual(json.loads((self.root / "state.json").read_text())["current"], self.new)
        self.assertEqual(compose.call_count, 2)
        self.assertTrue(all(call.args[0] == self.root / "releases" / self.old for call in compose.call_args_list))

    @patch.object(deploy, "api", side_effect=OSError("offline"))
    @patch.object(deploy, "compose")
    def test_restarts_verified_current_before_offline_github_check(self, compose, api):
        self.state(self.old)
        with self.assertRaises(OSError):
            deploy.poll(self.root)
        self.assertEqual(compose.call_args.args[0], self.root / "releases" / self.old)
        self.assertIn("--no-build", compose.call_args.args)


@unittest.skipUnless(os.getenv("CD_COMPOSE_INTEGRATION") == "true", "requires explicit local Docker Compose check")
class ComposeIntegrationTests(unittest.TestCase):
    def test_real_prepare_renders_current_compose_for_both_slots(self):
        source = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="economicon-cd-compose-") as directory:
            for legacy in (False, True):
                with self.subTest(legacy=legacy):
                    root = Path(directory) / str(legacy)
                    deploy.init(root, 19252)
                    if legacy:
                        values = json.loads((root / "secrets.json").read_text())
                        for key in tuple(values):
                            if key.startswith(("MINIO_", "DOCUMENT_")) or key == "GRAFANA_EVALUATION_DB_PASSWORD":
                                del values[key]
                        deploy.atomic_json(root / "secrets.json", values)
                    # Environment must not hide missing generated values or override the slot.
                    clean = {key: value for key, value in os.environ.items()
                             if not key.startswith(("MINIO_", "DOCUMENT_", "COMPOSE_"))
                             and key not in deploy.PORTS and key not in {"CHAT_HMAC_FILE", "CORS_ALLOWED_ORIGINS", "GRAFANA_EVALUATION_DB_PASSWORD"}}
                    ports = []
                    with patch.dict(os.environ, clean, clear=True):
                        for sha, slot in (("a" * 40, 0), ("b" * 40, 1)):
                            release = deploy.prepare(root, source, sha, slot)
                            config = json.loads((release / "compose.json").read_text())
                            services = config["services"]
                            for flag in ['RAG_VERIFIED_ENABLED', 'RAG_CONTEXTUAL_ENABLED', 'RAG_HYBRID_ENABLED']:
                                self.assertEqual(str(services['backend']['environment'][flag]).lower(), 'false')
                            self.assertEqual(services['backend']['environment']['EMBEDDING_MAPPING_SHA256'], '')
                            self.assertEqual(services['processor']['environment']['EMBEDDING_MAPPING_SHA256'], '')
                            stored = json.loads((root / "secrets.json").read_text())
                            self.assertTrue(services["grafana"]["environment"]["GRAFANA_EVALUATION_DB_PASSWORD"]
                                            == stored["GRAFANA_EVALUATION_DB_PASSWORD"])
                            secret_bytes = (root / "secrets.json").read_bytes()
                            self.assertEqual(deploy.prepare(root, source, sha, slot), release)
                            self.assertTrue((root / "secrets.json").read_bytes() == secret_bytes)
                            port = str(19252 + slot * 100 + 11)
                            self.assertEqual(str(services["minio"]["ports"][0]["published"]), port)
                            self.assertEqual(services["backend"]["environment"]["DOCUMENT_S3_PUBLIC_ENDPOINT"],
                                             f"http://127.0.0.1:{port}")
                            self.assertEqual(services["minio"]["environment"]["MINIO_API_CORS_ALLOW_ORIGIN"],
                                             f"http://127.0.0.1:{19260 + slot * 100},http://localhost:{19260 + slot * 100}")
                            self.assertNotIn("MINIO_ROOT_PASSWORD", services["backend"]["environment"])
                            self.assertEqual(services["backend"]["environment"]["DOCUMENT_S3_ACCESS_KEY"],
                                             services["minio-init"]["environment"]["DOCUMENT_S3_ACCESS_KEY"])
                            ports.append({(item["host_ip"], str(item["published"]))
                                          for service in services.values() for item in service.get("ports", [])})
                    self.assertTrue(ports[0].isdisjoint(ports[1]))


if __name__ == "__main__":
    unittest.main()
