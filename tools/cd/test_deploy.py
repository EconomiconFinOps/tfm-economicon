import copy
import json
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

    def test_invalid_port_base_rejected_before_creating_files(self):
        for port in (0, 1023, 65425, 65535):
            with self.assertRaises(ValueError):
                deploy.init(self.root / "invalid", port)
        self.assertFalse((self.root / "invalid").exists())

    @patch.object(deploy, "run")
    def test_prepare_private_ports_absolute_paths_and_shell_dollars(self, run):
        def render(*args, **kwargs):
            staging = self.root / "releases" / (self.new + ".preparing")
            return json.dumps({"services": {"backend": {"ports": [{"published": "19257", "target": 8000}],
                  "build": {"context": str(staging / "apps/backend")},
                  "entrypoint": ["sh", "-ec", 'echo "$RUNTIME_ENVIRONMENT"; exec "$@"'],
                  "volumes": [{"type": "bind", "source": str(staging / "file")}]}}, "name": "test"})
        run.side_effect = render
        release = deploy.prepare(self.root, self.source, self.new, 1)
        config = json.loads((release / "compose.json").read_text())
        backend = config["services"]["backend"]
        self.assertEqual(backend["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(backend["build"]["context"], str(release / "apps/backend"))
        self.assertEqual(backend["volumes"][0]["source"], str(release / "file"))
        self.assertIn("$$RUNTIME_ENVIRONMENT", backend["entrypoint"][2])
        self.assertNotIn("do-not-copy", (release / ".env").read_text())
        self.assertIn("API_HOST_PORT='19357'", (release / ".env").read_text())
        with self.assertRaises(ValueError):
            deploy.prepare(self.root, self.source, self.new, 0)

    def test_invalid_sha_never_copies_source(self):
        with self.assertRaises(ValueError):
            deploy.prepare(self.root, self.source, "../../outside", 0)

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_success_switches_only_after_smoke_and_preserves_volumes(self, compose, smoke):
        release = self.fixture(self.new, 1)
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
        self.assertEqual(compose.call_count, 1)


if __name__ == "__main__":
    unittest.main()
