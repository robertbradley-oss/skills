from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "clean-up" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_cleanup as apply_module  # noqa: E402
import inspect_repository as inspect_module  # noqa: E402
import triage_repository as triage_module  # noqa: E402


class TemporaryResidueCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "clean-up@example.invalid")
        self.git("config", "user.name", "Clean Up Tests")
        (self.workspace / ".gitignore").write_text("*.bak\n", encoding="ascii")
        (self.workspace / "README.md").write_text("fixture\n", encoding="ascii")
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=self.workspace, check=True,
            capture_output=True, text=True,
        )

    def inspect(self, path: str) -> dict:
        return inspect_module.inspect(self.workspace, [path], None)

    def apply(self, path: str, item_id: str) -> tuple[dict, int]:
        validation = json.dumps([sys.executable, "-B", "-c", "raise SystemExit(0)"])
        return apply_module.apply_cleanup(argparse.Namespace(
            workspace=str(self.workspace), path=[path], git_base=None,
            approve=[item_id], validate_command=[validation],
            validation_timeout=30, report=None,
        ))

    def test_untracked_and_ignored_strict_temporary_files_are_typed_candidates(self) -> None:
        (self.workspace / "scratch.tmp").write_text("temporary\n", encoding="ascii")
        (self.workspace / "backup.bak").write_text("backup\n", encoding="ascii")

        for path in ("scratch.tmp", "backup.bak"):
            with self.subTest(path=path):
                item = self.inspect(path)["items"][0]
                self.assertEqual(item["classification"], "candidate")
                self.assertEqual(item["candidate_kind"], "temporary-residue")
                self.assertEqual(item["evidence"]["references"]["match_count"], 0)

    def test_logs_and_referenced_temporary_names_remain_unresolved(self) -> None:
        (self.workspace / "application.log").write_text("important log\n", encoding="ascii")
        (self.workspace / "config.txt").write_text("input=referenced.tmp\n", encoding="ascii")
        self.git("add", "config.txt")
        self.git("commit", "-qm", "reference temporary input")
        (self.workspace / "referenced.tmp").write_text("required\n", encoding="ascii")

        log_item = self.inspect("application.log")["items"][0]
        referenced = self.inspect("referenced.tmp")["items"][0]
        triage = triage_module.triage(self.workspace, None, 50)

        self.assertEqual(log_item["candidate_kind"], "git-new")
        self.assertEqual(referenced["classification"], "review")
        self.assertIn("references", referenced["reason"])
        self.assertIn("application.log", {item["target"] for item in triage["unresolved"]})
        self.assertNotIn("application.log", {item["path"] for item in triage["safe_to_remove"]})

    def test_approved_temporary_residue_applies_through_quarantine(self) -> None:
        path = "scratch.tmp"
        target = self.workspace / path
        target.write_text("temporary\n", encoding="ascii")
        item = self.inspect(path)["items"][0]

        result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(target.exists())
        self.assertEqual(self.git("status", "--short").stdout, "")


if __name__ == "__main__":
    unittest.main()
