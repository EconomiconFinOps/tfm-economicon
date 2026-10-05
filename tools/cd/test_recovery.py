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
        compose.side_effect = lambda release, *args: (_ for _ in ()).throw(OSError()) if release == old else None
        with self.assertRaises(OSError):
            deploy.deploy(self.root, new)
        self.assertEqual(self.read("state.json")["current"], self.new)
        compose.reset_mock(side_effect=True)
        with patch.object(deploy, "api", side_effect=self.github), patch.object(deploy, "run") as run:
            deploy.poll(self.root)
        compose.assert_any_call(old, "down", "--remove-orphans")
        run.assert_not_called()  # Current == head, no fetch/rebuild.

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
        with self.assertRaises(OSError):
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
        with self.assertRaises(OSError):
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
        self.assertEqual(self.read("recovery.json")["phase"], "current")
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
        with patch.object(deploy, "api", return_value={"object": {"sha": "c" * 40}}), self.assertRaises(RuntimeError):
            deploy.deploy(self.root, release, expected_head=self.new)
        self.assertEqual(self.read("state.json")["current"], self.old)
        self.assertTrue(all(c.args[0] == release for c in compose.call_args_list))

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
