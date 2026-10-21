"""Fallo de inventario/retirada no equivale a contenedor ausente (PR141).

Ejecuta el main real y su finally; únicamente el proceso Docker se simula porque
estas pruebas no deben acceder a un daemon ni crear recursos. El arranque falla
de forma controlada antes de SQL para aislar el contrato observable de limpieza.
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("evaluation_cleanup_runner", ROOT / "scripts/tests/check_evaluation_paired_postgres.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
NAME = "economicon-jup121-paired-test-012345abcdef"


def result(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout, stderr=stderr)


class CleanupReportTests(unittest.TestCase):
    def exercise(self, inventories, *, ownership=None, removal=None, old_final=None):
        inventory = list(inventories)
        calls = []
        deletions = []
        ownership = ownership if ownership is not None else result(stdout=NAME + "\n")
        removal = removal if removal is not None else result(stdout=NAME + "\n")
        old_final = old_final if old_final is not None else result(1, stderr="Error: No such container: " + NAME)

        def external(command, **kwargs):
            calls.append(command)
            if command[:3] == ["docker", "image", "inspect"]:
                return result(1, stderr="controlled setup failure before container creation")
            if command[:3] == ["docker", "container", "ls"]:
                # Exact name and all states are required: a stopped container is
                # still a resource, and a prefix must not match a foreign name.
                self.assertIn("--all", command)
                self.assertIn("name=^/" + NAME + "$", command)
                answer = inventory.pop(0) if len(inventory) > 1 else inventory[0]
            elif command[:3] == ["docker", "inspect", "--format"]:
                answer = ownership
            elif command[:3] == ["docker", "container", "inspect"]:
                answer = old_final  # Characterizes the previous ambiguous check.
            elif command[:4] == ["docker", "rm", "-f", "-v"]:
                self.assertEqual(command[4:], [NAME])
                deletions.append(command[-1])
                answer = removal
            else:
                raise AssertionError(f"Unexpected external operation: {command}")
            if isinstance(answer, BaseException):
                raise answer
            return answer

        stdout = io.StringIO()
        with mock.patch.object(runner.subprocess, "run", side_effect=external), redirect_stdout(stdout):
            with self.assertRaises(AssertionError):
                runner.main(NAME)
        output = stdout.getvalue().strip()
        self.assertTrue(output, "Even unknown cleanup must publish its truthful summary")
        return json.loads(output), deletions

    def test_daemon_failure_is_not_absence(self):
        failure = result(1, stderr="Cannot connect to the Docker daemon")
        report, deletions = self.exercise([failure], ownership=failure, old_final=failure)
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])

    def test_permission_failure_is_not_absence(self):
        failure = result(1, stderr="permission denied while connecting")
        report, deletions = self.exercise([failure], ownership=failure, old_final=failure)
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])

    def test_successful_empty_inventory_confirms_already_absent(self):
        report, deletions = self.exercise([result()], ownership=result(1, stderr="No such object"))
        self.assertIs(report["container_removed"], True)
        self.assertEqual(report.get("cleanup_status"), "already_absent")
        self.assertEqual(deletions, [])

    def test_owned_container_removed_only_after_successful_recheck(self):
        report, deletions = self.exercise([result(stdout=NAME + "\n"), result()])
        self.assertIs(report["container_removed"], True)
        self.assertEqual(report.get("cleanup_status"), "removed")
        self.assertEqual(deletions, [NAME])

    def test_failed_rm_cannot_report_success_even_if_later_inspect_fails(self):
        report, _ = self.exercise([result(stdout=NAME + "\n"), result()],
                                  removal=result(1, stderr="removal failed"))
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "failed")
        self.assertNotEqual(report.get("status"), "PASS")

    def test_ownership_mismatch_does_not_remove_a_foreign_resource(self):
        report, deletions = self.exercise([result(stdout=NAME + "\n")],
                                          ownership=result(stdout="different-owner\n"), old_final=result())
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "ownership_mismatch")
        self.assertEqual(deletions, [])

    def test_ownership_inspect_error_keeps_cleanup_unknown(self):
        report, deletions = self.exercise([result(stdout=NAME + "\n")], ownership=result(1, stderr="daemon error"))
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])

    def test_post_removal_daemon_failure_is_not_proof_of_absence(self):
        report, deletions = self.exercise([result(stdout=NAME + "\n"), result(1, stderr="daemon unavailable")])
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [NAME])

    def test_container_still_present_after_rm_is_failure(self):
        report, _ = self.exercise([result(stdout=NAME + "\n")], old_final=result(stdout="[]"))
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "failed")

    def test_inventory_timeout_reports_unknown_and_does_not_delete(self):
        report, deletions = self.exercise([subprocess.TimeoutExpired(["docker"], 45)])
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])

    def test_inventory_oserror_reports_unknown_and_does_not_delete(self):
        report, deletions = self.exercise([OSError("daemon binary unavailable")])
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])

    def test_unexpected_inventory_output_is_not_absence_or_ownership(self):
        report, deletions = self.exercise([result(stdout="another-container\n")])
        self.assertIs(report["container_removed"], False)
        self.assertEqual(report.get("cleanup_status"), "unknown")
        self.assertEqual(deletions, [])


if __name__ == "__main__":
    unittest.main()
