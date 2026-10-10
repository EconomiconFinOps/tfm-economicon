"""Faults, interruptions and concurrency boundaries of the locked CD agent."""
import io
import contextlib
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import types
import unittest
import urllib.error
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
import deploy


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        deploy.init(self.root, 19252)
        self.old, self.new = "a" * 40, "b" * 40
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "docker-compose.yml").write_text("services: {}")

    def fixture(self, sha, slot):
        path = self.root / "releases" / sha
        path.mkdir(parents=True)
        deploy.atomic_json(path / "release.json", {"sha": sha, "slot": slot,
                          "api_port": 19257 + slot * 100, "frontend_port": 19260 + slot * 100})
        return path

    def state(self, current, slot, previous=None, **extra):
        deploy.atomic_json(self.root / "state.json", {"current": current, "slot": slot,
                          "previous": previous, **extra})

    def read(self, name):
        return json.loads((self.root / name).read_text())

    def github(self, path):
        if path == "git/ref/heads/develop":
            return {"object": {"sha": self.new}}
        self.assertEqual(path, "actions/workflows/cd.yml/runs?branch=develop&per_page=1")
        return {"workflow_runs": [{"id": 42, "head_sha": self.new, "head_branch": "develop",
                "event": "push", "status": "completed", "conclusion": "success",
                "head_repository": {"full_name": deploy.REPOSITORY}}]}

    def git(self, args, **kwargs):
        if "rev-parse" in args:
            return self.new
        if "archive" in args:
            archive = Path(args[args.index("--output") + 1])
            with tarfile.open(archive, "w") as tar:
                value = b"services: {}"
                member = tarfile.TarInfo("docker-compose.yml")
                member.size = len(value)
                tar.addfile(member, io.BytesIO(value))
        return ""

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_down_failure_after_promotion_is_retried_on_unchanged_poll(self, compose, smoke):
        old = self.fixture(self.old, 0)
        new = self.fixture(self.new, 1)
        self.state(self.old, 0)
        deploy.atomic_json(self.root / "failure.json", {"sha": self.new, "retry_allowed": True})
        deploy.atomic_json(self.root / "recovery.json", {"phase": "current", "error_type": "OldError"})
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if release == old else None
        with self.assertRaises(deploy.CleanupError):
            deploy.deploy(self.root, new)
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.assertIn("resolved_at", self.read("failure.json"))
        self.assertEqual(self.read("recovery.json")["errors"], [{"phase": "cleanup",
            "error_type": "CleanupError", "releases": [{"release": self.old, "error_type": "OSError"}]}])
        resolved = self.read("failure.json")["resolved_at"]
        compose.reset_mock(side_effect=True)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run") as run:
            deploy.poll(self.root)
        compose.assert_any_call(old, "down", "--remove-orphans")
        run.assert_not_called()  # Current == head, no fetch/rebuild.
        self.assertFalse((self.root / "recovery.json").exists())
        self.assertEqual(self.read("failure.json")["resolved_at"], resolved)

    @patch.object(deploy, "compose")
    def test_registration_errors_never_replace_build_cause_or_prevent_down(self, compose):
        release = self.fixture(self.new, 1)
        original = RuntimeError("private build cause")
        for failure_write in (False, True):
            for cleanup_fails in (False, True):
                with self.subTest(failure_write=failure_write, cleanup_fails=cleanup_fails):
                    # Real FileExistsError creating events/, not only mocked telemetry.
                    if not (self.root / "events").exists():
                        (self.root / "events").write_text("blocked")
                    compose.reset_mock()
                    compose.side_effect = [original, OSError("private down cause") if cleanup_fails else None]
                    actual_write = deploy.atomic_json
                    def write(path, value):
                        if path.name == "failure.json" and failure_write:
                            raise OSError("private disk error")
                        actual_write(path, value)
                    with patch.object(deploy, "atomic_json", side_effect=write), \
                         contextlib.redirect_stderr(io.StringIO()) as stderr:
                        with self.assertRaises(RuntimeError) as caught:
                            deploy.deploy(self.root, release)
                    self.assertIs(caught.exception, original)
                    self.assertEqual([c.args[1] for c in compose.call_args_list], ["build", "down"])
                    self.assertIn("Evidence unavailable", stderr.getvalue())
                    self.assertNotIn("private", stderr.getvalue())

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_registration_error_preserves_api_cause_and_still_stops_candidate(self, smoke, compose):
        release = self.fixture(self.new, 1)
        original = urllib.error.URLError("private network")
        with patch.object(deploy, "api", side_effect=original), \
             patch.object(deploy, "event", side_effect=PermissionError("private disk")):
            with self.assertRaises(urllib.error.URLError) as caught:
                deploy.deploy(self.root, release, expected_head=self.new)
        self.assertIs(caught.exception, original)
        compose.assert_any_call(release, "down", "--remove-orphans")
        self.assertFalse((self.root / "failure.json").exists())

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_promoted_failure_resolution_write_is_retried_without_rebuilding(self, smoke, compose):
        self.fixture(self.old, 0)
        release = self.fixture(self.new, 1)
        self.state(self.old, 0)
        deploy.atomic_json(self.root / "failure.json", {"sha": self.new})
        actual_write = deploy.atomic_json
        def write(path, value):
            if path.name == "failure.json":
                raise OSError()
            actual_write(path, value)
        with patch.object(deploy, "atomic_json", side_effect=write):
            deploy.deploy(self.root, release)
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.assertNotIn("resolved_at", self.read("failure.json"))
        compose.reset_mock()
        with patch.object(deploy, "api", side_effect=urllib.error.URLError("offline")):
            with self.assertRaises(urllib.error.URLError):
                deploy.poll(self.root)
        self.assertIn("resolved_at", self.read("failure.json"))
        self.assertFalse(any(c.args[1] == "build" for c in compose.call_args_list))

    @patch.object(deploy, "compose")
    def test_already_deployed_repairs_resolution_without_erasing_pending_cleanup(self, compose):
        release = self.fixture(self.new, 1)
        self.state(self.new, 1)
        deploy.atomic_json(self.root / "failure.json", {"sha": self.new})
        pending = {"phase": "cleanup", "error_type": "CleanupError"}
        deploy.atomic_json(self.root / "recovery.json", pending)
        deploy.deploy(self.root, release)
        self.assertIn("resolved_at", self.read("failure.json"))
        self.assertEqual(self.read("recovery.json"), pending)
        compose.assert_not_called()

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_repeated_rollback_retries_cleanup_without_returning_to_retired_release(self, compose, smoke):
        old = self.fixture(self.old, 0)
        new = self.fixture(self.new, 1)
        self.state(self.new, 1, self.old)
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if release == new else None
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(deploy.CleanupError):
                deploy.rollback(self.root)
        self.assertIn("State already changed", stderr.getvalue())
        committed = self.read("state.json")
        self.assertEqual(self.read("recovery.json")["releases"], [{"release": self.new, "error_type": "OSError"}])
        compose.reset_mock(side_effect=True)
        deploy.rollback(self.root)
        self.assertEqual(self.read("state.json"), committed)
        self.assertEqual(committed["current"], self.old)
        self.assertTrue(committed["manual_rollback"])
        compose.assert_any_call(new, "down", "--remove-orphans")
        self.assertFalse(any(c.args[0] == new and c.args[1] == "up" for c in compose.call_args_list))
        self.assertEqual(smoke.call_args.args, (old,))
        self.assertFalse((self.root / "recovery.json").exists())

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke", side_effect=ValueError("current not healthy"))
    def test_repeated_rollback_failure_keeps_current_and_does_not_stop_it(self, smoke, compose):
        old = self.fixture(self.old, 0)
        self.fixture(self.new, 1)
        self.state(self.old, 0, self.new, manual_rollback=True)
        with self.assertRaises(ValueError):
            deploy.rollback(self.root)
        self.assertEqual(self.read("state.json")["current"], self.old)
        self.assertFalse(any(c.args[1] == "down" for c in compose.call_args_list))
        self.assertEqual(self.read("recovery.json")["phase"], "current")

    @patch.object(deploy, "compose", side_effect=OSError())
    def test_reconcile_reports_every_failure(self, compose):
        a = self.fixture(self.old, 0)
        b = self.fixture(self.new, 1)
        with self.assertRaises(deploy.CleanupError) as caught:
            deploy.reconcile(self.root, None)
        self.assertEqual(caught.exception.failures, [
            {"release": a.name, "error_type": "OSError"}, {"release": b.name, "error_type": "OSError"}])

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_cleanup_cause_survives_recovery_and_event_write_errors(self, compose, smoke):
        old = self.fixture(self.old, 0)
        new = self.fixture(self.new, 1)
        self.state(self.old, 0)
        original = OSError("private cleanup")
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(original) if release == old else None
        actual_write = deploy.atomic_json
        def write(path, value):
            if path.name == "recovery.json":
                raise PermissionError()
            actual_write(path, value)
        with patch.object(deploy, "atomic_json", side_effect=write), \
             patch.object(deploy, "event", side_effect=PermissionError()):
            with self.assertRaises(deploy.CleanupError) as caught:
                deploy.deploy(self.root, new)
        self.assertEqual(caught.exception.failures, [{"release": self.old, "error_type": "OSError"}])
        self.assertEqual(self.read("state.json")["current"], self.new)

    def test_second_cleanup_success_removes_old_cleanup_without_hiding_current_error(self):
        self.fixture(self.old, 0)
        self.state(self.old, 0)
        with patch.object(deploy, "reconcile", side_effect=[deploy.CleanupError([]), None]), \
             patch.object(deploy, "compose", side_effect=OSError()), \
             patch.object(deploy, "api", side_effect=self.github), \
             patch.object(deploy, "prepare"), patch.object(deploy, "deploy"), \
             patch.object(deploy, "run", side_effect=self.git):
            deploy.poll(self.root)
        self.assertEqual(self.read("recovery.json")["errors"], [{"phase": "current", "error_type": "OSError"}])

    def test_validate_source_cannot_prepare_or_promote_with_pending_cleanup(self):
        with patch.object(deploy, "lock", side_effect=lambda root: contextlib.nullcontext()), \
             patch.object(sys, "argv", ["deploy", "--root", str(self.root), "validate-source",
                         "--source", str(self.source), "--sha", self.new]), \
             patch.object(deploy, "reconcile", side_effect=deploy.CleanupError([])), \
             patch.object(deploy, "prepare") as prepare, patch.object(deploy, "deploy") as start:
            with self.assertRaises(deploy.CleanupError):
                deploy.main()
        prepare.assert_not_called()
        start.assert_not_called()

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_next_sha_can_reuse_slot_after_interrupted_promotion_cleanup(self, compose, smoke):
        old = self.fixture(self.old, 0)
        new = self.fixture(self.new, 1)
        self.state(self.old, 0)
        active = {self.old: 0}
        fail_down = True
        def docker(release, *args):
            nonlocal fail_down
            if args[0] == "down":
                if release == old and fail_down:
                    fail_down = False
                    raise OSError("interrupted cleanup")
                active.pop(release.name, None)
            elif args[0] == "up":
                slot = json.loads((release / "release.json").read_text())["slot"]
                self.assertFalse(any(key != release.name and value == slot for key, value in active.items()))
                active[release.name] = slot
        compose.side_effect = docker
        with self.assertRaises(deploy.CleanupError):
            deploy.deploy(self.root, new)
        self.assertEqual(len(active), 2)
        self.new = "c" * 40
        def command(args, **kwargs):
            return '{"services": {}}' if args[0] == "docker" else self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run", side_effect=command):
            deploy.poll(self.root)
        self.assertEqual(active, {self.new: 0})
        self.assertEqual(self.read("state.json")["slot"], 0)

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_down_failure_after_rollback_is_retried_while_paused(self, compose, smoke):
        old = self.fixture(self.old, 0)
        new = self.fixture(self.new, 1)
        self.state(self.new, 1, self.old)
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if release == new else None
        with self.assertRaises(deploy.CleanupError):
            deploy.rollback(self.root)
        self.assertTrue(self.read("state.json")["manual_rollback"])
        compose.reset_mock(side_effect=True)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run") as run:
            deploy.poll(self.root)
        compose.assert_any_call(new, "down", "--remove-orphans")
        run.assert_not_called()

    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_original_build_error_and_failure_survive_failed_down(self, compose, smoke):
        release = self.fixture(self.new, 1)
        original = RuntimeError("build cause")
        compose.side_effect = [original, OSError("cleanup cause")]
        with self.assertRaises(RuntimeError) as caught:
            deploy.deploy(self.root, release, 42)
        self.assertIs(caught.exception, original)
        failure = self.read("failure.json")
        self.assertEqual((failure["error_type"], failure["cleanup_error_type"]), ("RuntimeError", "OSError"))
        self.assertEqual(failure["run_id"], 42)
        self.assertNotIn("cause", (self.root / "failure.json").read_text())
        smoke.assert_not_called()

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_stale_preparing_is_removed_and_dotenv_variants_never_copied(self, run):
        stale = self.root / "releases" / (self.new + ".preparing")
        stale.mkdir(parents=True)
        (stale / "stale").write_text("interrupted")
        (self.source / ".env.private").write_text("SECRET")
        (self.source / "nested").mkdir()
        (self.source / "nested" / ".env.production").write_text("SECRET")
        with patch.object(deploy.os, "chmod", wraps=os.chmod) as chmod:
            release = deploy.prepare(self.root, self.source, self.new, 0)
        chmod.assert_any_call(stale / ".env", 0o600)
        chmod.assert_any_call(stale / "compose.json", 0o600)
        self.assertFalse((release / "stale").exists())
        self.assertFalse((release / ".env.private").exists())
        self.assertFalse((release / "nested" / ".env.production").exists())
        if os.name == "posix":
            self.assertEqual((release / ".env").stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(os.name == "posix", "Requires POSIX directory modes")
    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_private_archive_source_is_traversable_inside_nonroot_images(self, run):
        package = self.source / "apps" / "backend" / "app" / "core"
        package.mkdir(parents=True)
        (package / "config.py").write_text("VALUE = 1\n")
        for path in (self.source, *self.source.rglob("*")):
            if path.is_dir():
                os.chmod(path, 0o700)
        release = deploy.prepare(self.root, self.source, self.new, 0)
        for path in release.rglob("*"):
            if path.is_dir():
                self.assertEqual(path.stat().st_mode & 0o777, 0o755)
        self.assertEqual(release.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        self.assertEqual((release / ".env").stat().st_mode & 0o777, 0o600)
        self.assertEqual((release / "compose.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual((release / "apps/backend/app/core/config.py").read_text(), "VALUE = 1\n")

    def test_short_uppercase_and_traversal_sha_are_rejected(self):
        for sha in ("a" * 4, "a" * 39, "a" * 41, "A" * 40, "../" + "a" * 40):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                deploy.prepare(self.root, self.source, sha, 0)
        self.assertFalse((self.root / "releases").exists())

    @patch.object(deploy, "compose")
    def test_complete_poll_can_replace_current_when_recovery_fails(self, compose):
        old = self.fixture(self.old, 0)
        self.state(self.old, 0)
        def fail_recovery(release, *args):
            if release == old and args[0] == "up":
                raise OSError("broken current")
        compose.side_effect = fail_recovery
        original_git = self.git
        def command(args, **kwargs):
            if args[0] == "docker":
                return '{"services": {}}'
            return original_git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github) as api, \
             patch.object(deploy, "run", side_effect=command) as run, \
             patch.object(deploy, "smoke") as smoke:
            deploy.poll(self.root)
        state = self.read("state.json")
        self.assertEqual((state["current"], state["slot"], state["run_id"]), (self.new, 1, 42))
        self.assertFalse((self.root / "recovery.json").exists())  # Healthy replacement resolved it.
        self.assertEqual(api.call_count, 4)  # Eligibility, after fetch and before promotion.
        self.assertTrue(any("fetch" in c.args[0] for c in run.call_args_list))
        smoke.assert_called_once()

    @patch.object(deploy, "compose")
    def test_fetch_race_and_prepare_race_never_deploy(self, compose):
        for phase in ("fetch", "prepare"):
            with self.subTest(phase=phase), patch.object(deploy, "deploy") as start, \
                 patch.object(deploy, "prepare") as prepare:
                count = 0
                def api(path):
                    nonlocal count
                    if path == "git/ref/heads/develop":
                        count += 1
                        if phase == "prepare" and count == 2:
                            return {"object": {"sha": "c" * 40}}
                    return self.github(path)
                def git(args, **kwargs):
                    if "rev-parse" in args and phase == "fetch":
                        return "c" * 40
                    return self.git(args, **kwargs)
                with patch.object(deploy, "api", side_effect=api), patch.object(deploy, "run", side_effect=git):
                    deploy.poll(self.root)
                start.assert_not_called()
                self.assertEqual(prepare.call_count, 0 if phase == "fetch" else 1)

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_head_change_after_smoke_preserves_current(self, smoke, compose):
        release = self.fixture(self.new, 1)
        self.state(self.old, 0)
        prior = {"sha": "d" * 40, "error_type": "ValueError"}
        deploy.atomic_json(self.root / "failure.json", prior)
        with patch.object(deploy, "api", return_value={"object": {"sha": "c" * 40}}):
            deploy.deploy(self.root, release, expected_head=self.new)
        self.assertEqual(self.read("state.json")["current"], self.old)
        self.assertTrue(all(c.args[0] == release for c in compose.call_args_list))
        self.assertEqual(self.read("failure.json"), prior)
        self.assertEqual(json.loads(next((self.root / "events").glob("*.json")).read_text())["reason"], "superseded")

    @patch.object(deploy, "compose")
    def test_reconcile_attempts_all_and_preserves_unknown_preparing(self, compose):
        a = self.fixture("a" * 40, 0)
        b = self.fixture("b" * 40, 1)
        self.fixture("c" * 40, 0)
        valid = self.root / "releases" / ("d" * 40 + ".preparing")
        invalid = self.root / "releases" / "not-a-sha.preparing"
        valid.mkdir()
        invalid.mkdir()
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if release == a else None
        with self.assertRaises(deploy.CleanupError) as caught:
            deploy.reconcile(self.root, "c" * 40)
        self.assertEqual([c.args[0] for c in compose.call_args_list], [a, b])
        self.assertEqual(caught.exception.failures, [{"release": a.name, "error_type": "OSError"}])
        self.assertFalse(valid.exists())
        self.assertTrue(invalid.exists())

    def test_second_reconcile_failure_blocks_fetch_and_deploy(self):
        with patch.object(deploy, "reconcile", side_effect=deploy.CleanupError([])) as clean, \
             patch.object(deploy, "api", side_effect=self.github) as api, \
             patch.object(deploy, "run") as run, patch.object(deploy, "deploy") as start:
            with self.assertRaises(deploy.CleanupError):
                deploy.poll(self.root)
        self.assertEqual(clean.call_count, 2)
        self.assertEqual(api.call_count, 2)  # Still evaluates eligibility.
        run.assert_not_called()
        start.assert_not_called()
        self.assertEqual(self.read("recovery.json")["phase"], "cleanup")

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_failure_of_other_sha_does_not_pause_new_candidate(self, smoke, compose):
        deploy.atomic_json(self.root / "failure.json", {"sha": self.old, "error_type": "ValueError"})
        def command(args, **kwargs):
            return '{"services": {}}' if args[0] == "docker" else self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run", side_effect=command):
            deploy.poll(self.root)
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.assertEqual(self.read("failure.json")["sha"], self.old)

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_transient_check_error_survives_failed_cleanup_without_quarantine(self, smoke, compose):
        release = self.fixture(self.new, 1)
        self.state(self.old, 0)
        error = urllib.error.URLError("offline")
        compose.side_effect = [None, None, OSError("cleanup")]
        with patch.object(deploy, "api", side_effect=error):
            with self.assertRaises(urllib.error.URLError) as caught:
                deploy.deploy(self.root, release, expected_head=self.new)
        self.assertIs(caught.exception, error)
        self.assertFalse((self.root / "failure.json").exists())
        events = [json.loads(p.read_text()) for p in (self.root / "events").glob("*.json")]
        self.assertTrue(any(e.get("cleanup_error_type") == "OSError" for e in events))

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_network_error_after_smoke_keeps_prior_failure_and_allows_retry(self, smoke, compose):
        release = self.fixture(self.new, 1)
        self.fixture(self.old, 0)
        self.state(self.old, 0)
        prior = {"sha": "c" * 40, "error_type": "ValueError"}
        deploy.atomic_json(self.root / "failure.json", prior)
        for error in (urllib.error.URLError("offline"), urllib.error.HTTPError("url", 403, "rate", {}, None),
                      urllib.error.HTTPError("url", 503, "busy", {}, None)):
            if hasattr(error, "close"):
                self.addCleanup(error.close)
            with self.subTest(error=type(error).__name__), patch.object(deploy, "api", side_effect=error):
                with self.assertRaises(type(error)):
                    deploy.deploy(self.root, release, 42, expected_head=self.new)
            self.assertEqual(self.read("state.json")["current"], self.old)
            self.assertEqual(self.read("failure.json"), prior)
        events = [json.loads(p.read_text()) for p in (self.root / "events").glob("*.json")]
        self.assertTrue(all(e["reason"] == "eligibility-unavailable" for e in events))
        # The next poll can fetch and promote this same SHA without resume.
        def command(args, **kwargs):
            return '{"services": {}}' if args[0] == "docker" else self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run", side_effect=command):
            deploy.poll(self.root)
        self.assertEqual(self.read("state.json")["current"], self.new)

    @patch.object(deploy, "compose")
    def test_recovery_status_clears_only_when_cleanup_and_current_recover(self, compose):
        self.fixture(self.old, 0)
        self.state(self.old, 0)
        with patch.object(deploy, "api", side_effect=lambda path: {"object": {"sha": self.old}}
                          if path == "git/ref/heads/develop" else {"workflow_runs": []}), \
             patch.object(deploy, "eligible_run", return_value=None):
            compose.side_effect = OSError()
            deploy.poll(self.root)
            self.assertEqual(self.read("recovery.json")["phase"], "current")
            compose.side_effect = None
            deploy.poll(self.root)
        self.assertFalse((self.root / "recovery.json").exists())

    @patch.object(deploy, "compose")
    def test_cleanup_recovery_does_not_clear_still_broken_current(self, compose):
        self.fixture(self.old, 0)
        self.state(self.old, 0)
        def command(args, **kwargs):
            return '{"services": {}}' if args[0] == "docker" else self.git(args, **kwargs)
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if args[0] == "up" else None
        with patch.object(deploy, "api", side_effect=self.github), \
             patch.object(deploy, "run", side_effect=command), patch.object(deploy, "deploy"):
            deploy.poll(self.root)
        self.assertEqual(self.read("recovery.json")["phase"], "current")

    @patch.object(deploy, "run", return_value='{"services": {}}')
    def test_project_names_isolate_same_sha_across_roots(self, run):
        other = self.root / "other"
        deploy.init(other, 19452)
        a = deploy.prepare(self.root, self.source, self.new, 0)
        b = deploy.prepare(other, self.source, self.new, 0)
        name = lambda path: next(l for l in (path / ".env").read_text().splitlines() if l.startswith("COMPOSE_PROJECT_NAME="))
        self.assertNotEqual(name(a), name(b))

    def test_nonblocking_lock_rejects_contention_without_entering_body(self):
        fcntl = types.SimpleNamespace(LOCK_EX=2, LOCK_NB=4, flock=Mock(side_effect=BlockingIOError))
        with patch.dict(sys.modules, {"fcntl": fcntl}):
            with self.assertRaisesRegex(RuntimeError, "Another deployment"):
                with deploy.lock(self.root):
                    self.fail("contended lock entered")
        self.assertEqual(fcntl.flock.call_args.args[1], 6)

    @patch.object(deploy, "compose")
    def test_failed_sha_is_paused_until_resume_even_without_current(self, compose):
        deploy.atomic_json(self.root / "failure.json", {"sha": self.new})
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run") as run:
            deploy.poll(self.root)
        run.assert_not_called()
        with patch.object(sys, "argv", ["deploy", "--root", str(self.root), "resume"]), \
             patch.object(deploy, "lock", side_effect=lambda root: contextlib.nullcontext()):
            deploy.main()
        self.assertTrue(self.read("failure.json")["retry_allowed"])
        self.assertEqual(self.read("failure.json")["sha"], self.new)
        def command(args, **kwargs):
            return '{"services": {}}' if args[0] == "docker" else self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), \
             patch.object(deploy, "run", side_effect=command), patch.object(deploy, "smoke"):
            deploy.poll(self.root)
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.assertIn("resolved_at", self.read("failure.json"))

    @patch.object(deploy, "compose")
    @patch.object(deploy, "smoke")
    def test_happy_poll_archives_verified_sha_and_promotes_initial_slot(self, smoke, compose):
        def command(args, **kwargs):
            if args[0] == "docker":
                return '{"services": {}}'
            if "archive" in args:
                self.assertEqual(args[-1], self.new)
            return self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run", side_effect=command):
            deploy.poll(self.root)
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.assertEqual(self.read("state.json")["slot"], 0)
        self.assertEqual(self.read("state.json")["run_id"], 42)
        smoke.assert_called_once_with(self.root / "releases" / self.new)

    @unittest.skipUnless(os.name == "posix", "Linux host lock")
    def test_real_lock_rejects_second_handle(self):
        with deploy.lock(self.root):
            with self.assertRaisesRegex(RuntimeError, "Another deployment"):
                with deploy.lock(self.root):
                    self.fail("second lock entered")

    def test_resume_clears_manual_pause_and_validate_source_rejects_existing_sha(self):
        self.fixture(self.old, 0)
        self.state(self.old, 0, manual_rollback=True)
        with patch.object(deploy, "lock", side_effect=lambda root: contextlib.nullcontext()):
            with patch.object(sys, "argv", ["deploy", "--root", str(self.root), "resume"]):
                deploy.main()
            self.assertNotIn("manual_rollback", self.read("state.json"))
            with patch.object(sys, "argv", ["deploy", "--root", str(self.root), "validate-source",
                     "--source", str(self.source), "--sha", self.old]), patch.object(deploy, "compose") as compose:
                with self.assertRaises(ValueError):
                    deploy.main()
                compose.assert_not_called()

    @patch.object(deploy, "run", return_value='{"services": {}}')
    @patch.object(deploy, "smoke")
    @patch.object(deploy, "compose")
    def test_validate_source_uses_supplied_source_and_respects_pause(self, compose, smoke, run):
        (self.source / "marker").write_text("operator source")
        argv = ["deploy", "--root", str(self.root), "validate-source", "--source", str(self.source), "--sha", self.new]
        with patch.object(deploy, "lock", side_effect=lambda root: contextlib.nullcontext()), \
             patch.object(sys, "argv", argv):
            deploy.main()
        release = self.root / "releases" / self.new
        self.assertEqual((release / "marker").read_text(), "operator source")
        self.assertEqual(self.read("state.json")["current"], self.new)
        self.state(self.new, 0, manual_rollback=True)
        argv[-1] = "c" * 40
        compose.reset_mock()
        with patch.object(deploy, "lock", side_effect=lambda root: contextlib.nullcontext()), \
             patch.object(sys, "argv", argv), self.assertRaises(ValueError):
            deploy.main()
        compose.assert_not_called()

    @patch.object(deploy, "compose")
    def test_archive_symlink_escape_is_rejected(self, compose):
        original_extract = tarfile.TarFile.extractall
        def checked_extract(tar, *args, **kwargs):
            self.assertEqual(kwargs.get("filter"), "data")
            return original_extract(tar, *args, **kwargs)
        def malicious_git(args, **kwargs):
            if "archive" in args:
                with tarfile.open(args[args.index("--output") + 1], "w") as tar:
                    member = tarfile.TarInfo("escape")
                    member.type = tarfile.SYMTYPE
                    member.linkname = str(self.root.parent / "outside")
                    tar.addfile(member)
                return ""
            return self.git(args, **kwargs)
        with patch.object(deploy, "api", side_effect=self.github), \
             patch.object(deploy, "run", side_effect=malicious_git), patch.object(deploy, "deploy") as start, \
             patch.object(tarfile.TarFile, "extractall", checked_extract):
            with self.assertRaises(tarfile.FilterError):
                deploy.poll(self.root)
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
