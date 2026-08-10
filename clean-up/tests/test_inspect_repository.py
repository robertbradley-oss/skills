from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "clean-up" / "scripts" / "inspect_repository.py"


class GitWorkspace(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "clean-up@example.invalid")
        self.git("config", "user.name", "Clean Up Tests")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.workspace, check=True, capture_output=True, text=True)

    def commit_all(self, message: str = "baseline") -> str:
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def inspect(self, paths: list[str], base: str | None = None) -> dict:
        command = [sys.executable, "-B", str(SCRIPT), "--workspace", str(self.workspace)]
        for path in paths:
            command.extend(["--path", path])
        if base:
            command.extend(["--git-base", base])
        command.extend(["--format", "json"])
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(command, check=True, capture_output=True, text=True, env=environment)
        return json.loads(completed.stdout)


class InspectRepositoryTests(GitWorkspace):
    def test_untracked_path_emits_stable_state_bound_candidate(self) -> None:
        path = self.workspace / "tmp" / "debug.log"
        path.parent.mkdir()
        path.write_text("debug\n", encoding="utf-8")

        first = self.inspect(["tmp/debug.log"])
        second = self.inspect(["tmp/debug.log"])

        self.assertEqual(first["schema"], "clean-up-inspection/v3")
        self.assertFalse(first["mutations_performed"])
        self.assertEqual(first["provisional_authorization_set"], second["provisional_authorization_set"])
        item = first["items"][0]
        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "git-new")
        self.assertEqual(item["evidence"]["worktree"]["tmp/debug.log"]["code"], "??")
        self.assertIn("not established", item["provenance_claim"])
        path.write_text("changed\n", encoding="utf-8")
        self.assertNotEqual(first["items"][0]["id"], self.inspect(["tmp/debug.log"])["items"][0]["id"])

    def test_tracked_clean_and_modified_paths_are_review(self) -> None:
        tracked = self.workspace / "tracked.txt"
        tracked.write_text("baseline\n", encoding="utf-8")
        self.commit_all()
        clean = self.inspect(["tracked.txt"])["items"][0]
        tracked.write_text("modified\n", encoding="utf-8")
        modified = self.inspect(["tracked.txt"])["items"][0]
        self.assertEqual(clean["classification"], "review")
        self.assertEqual(modified["classification"], "review")
        self.assertIn("modification", modified["reason"])

    def test_explicit_base_identifies_branch_added_file_and_binds_commit(self) -> None:
        (self.workspace / "baseline.txt").write_text("base\n", encoding="utf-8")
        base = self.commit_all()
        (self.workspace / "artifact.txt").write_text("branch artifact\n", encoding="utf-8")
        self.commit_all("branch work")

        result = self.inspect(["artifact.txt"], base)

        self.assertEqual(result["git"]["base_commit"], base)
        self.assertEqual(result["items"][0]["classification"], "candidate")
        self.assertEqual(result["items"][0]["evidence"]["base"]["artifact.txt"]["code"], "A")

    def test_invalid_base_and_overlapping_scope_disable_apply(self) -> None:
        (self.workspace / "tmp").mkdir()
        (self.workspace / "tmp" / "a.txt").write_text("a\n", encoding="utf-8")
        result = self.inspect(["tmp", "tmp/a.txt"], "does-not-exist")
        codes = {item["code"] for item in result["refusals"]}
        self.assertIn("scope-path-overlap", codes)
        self.assertIn("git-base-invalid", codes)
        self.assertFalse(result["apply_supported"])
        self.assertEqual(result["provisional_authorization_set"], [])

    def test_reserved_and_absent_paths_stay_out_while_unreferenced_empty_directory_is_candidate(self) -> None:
        (self.workspace / ".gameplan").mkdir()
        (self.workspace / ".gameplan" / "old.md").write_text("old\n", encoding="utf-8")
        (self.workspace / ".clean-up").mkdir()
        (self.workspace / ".clean-up" / "current.json").write_text("{}\n", encoding="utf-8")
        (self.workspace / ".post-clean").mkdir()
        (self.workspace / ".post-clean" / "legacy.json").write_text("{}\n", encoding="utf-8")
        (self.workspace / "empty").mkdir()
        result = self.inspect([
            ".gameplan/old.md", ".clean-up/current.json", ".post-clean/legacy.json",
            "missing.txt", "empty",
        ])
        decisions = {item["path"]: item["classification"] for item in result["items"]}
        self.assertEqual(decisions[".gameplan/old.md"], "preserve")
        self.assertEqual(decisions[".clean-up/current.json"], "preserve")
        self.assertEqual(decisions[".post-clean/legacy.json"], "preserve")
        self.assertEqual(decisions["missing.txt"], "preserve")
        self.assertEqual(decisions["empty"], "candidate")
        empty = next(item for item in result["items"] if item["path"] == "empty")
        self.assertEqual(empty["candidate_kind"], "empty-directory")
        self.assertEqual(result["provisional_authorization_set"], [empty["id"]])


if __name__ == "__main__":
    unittest.main()
