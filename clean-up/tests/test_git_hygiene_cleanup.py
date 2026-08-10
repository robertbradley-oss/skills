from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from apply_git_hygiene import apply_git_hygiene, preflight  # noqa: E402
from inspect_git_hygiene import inspect_git_hygiene  # noqa: E402


class GitHygieneCleanupTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=check, text=True,
            stdin=subprocess.DEVNULL, capture_output=True,
        )

    def repository(self, parent: Path) -> Path:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Clean Up Test")
        self.git(root, "config", "user.email", "clean-up@example.invalid")
        (root / ".gitignore").write_text("*.cache\n", encoding="ascii")
        (root / "tracked.txt").write_text("tracked\n", encoding="ascii")
        self.git(root, "add", ".gitignore", "tracked.txt")
        self.git(root, "commit", "-qm", "fixture")
        return root

    def linked_worktree(self, root: Path, path: Path, branch: str = "linked-topic") -> None:
        self.git(root, "worktree", "add", "-q", "-b", branch, str(path), "main")

    def args(
        self, root: Path, *, branches: list[str] | None = None,
        worktrees: list[str] | None = None, approvals: list[str] | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            workspace=str(root), branch=branches or [], worktree=worktrees or [],
            approve=approvals or [],
        )

    def test_inspect_proves_only_clean_recoverable_git_hygiene_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent)
            linked = parent / "linked"
            self.linked_worktree(root, linked)
            self.git(root, "branch", "merged-topic")
            self.git(root, "branch", "stable")

            result = inspect_git_hygiene(root, ["main", "stable", "merged-topic", "linked-topic"], [str(linked)])
            items = {(item["surface"], item["target"]): item for item in result["items"]}

            self.assertEqual(result["schema"], "clean-up-git-inspection/v1")
            self.assertFalse(result["mutations_performed"])
            self.assertEqual(items[("branch", "main")]["classification"], "review")
            self.assertEqual(items[("branch", "stable")]["classification"], "review")
            self.assertEqual(items[("branch", "merged-topic")]["classification"], "candidate")
            self.assertEqual(items[("branch", "merged-topic")]["candidate_kind"], "merged-local-branch")
            self.assertEqual(items[("branch", "linked-topic")]["classification"], "review")
            worktree = next(item for item in result["items"] if item["surface"] == "worktree")
            self.assertEqual(worktree["classification"], "candidate")
            self.assertEqual(worktree["candidate_kind"], "clean-linked-worktree")
            self.assertTrue(all(value.startswith("GC-") for value in result["proposed_authorization_set"]))

    def test_dirty_ignored_locked_and_detached_worktrees_remain_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent)
            dirty = parent / "dirty"
            ignored = parent / "ignored"
            locked = parent / "locked"
            detached = parent / "detached"
            self.linked_worktree(root, dirty, "dirty-topic")
            self.linked_worktree(root, ignored, "ignored-topic")
            self.linked_worktree(root, locked, "locked-topic")
            self.git(root, "worktree", "add", "-q", "--detach", str(detached), "main")
            (dirty / "tracked.txt").write_text("changed\n", encoding="ascii")
            (ignored / "private.cache").write_text("keep\n", encoding="ascii")
            self.git(root, "worktree", "lock", str(locked))

            result = inspect_git_hygiene(root, [], [str(dirty), str(ignored), str(locked), str(detached)])

            self.assertEqual(result["proposed_authorization_set"], [])
            self.assertTrue(all(item["classification"] == "review" for item in result["items"]))
            ignored_item = next(item for item in result["items"] if item["target"] == str(ignored.resolve()))
            self.assertEqual(ignored_item["evidence"]["ignored"]["count"], 1)
            self.assertIn("sha256", ignored_item["evidence"]["ignored"])
            reasons = " ".join(item["reason"] for item in result["items"])
            self.assertIn("unique local data", reasons)
            self.assertIn("locked", reasons)
            self.assertIn("detached", reasons)

    def test_discovery_and_path_ids_cannot_authorize_git_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.git(root, "branch", "merged-topic")
            inspection = inspect_git_hygiene(root, ["merged-topic"], [])

            for wrong_id in (
                "PD-0123456789AB", "PC-0123456789AB", "DC-0123456789AB",
                "FO-0123456789AB",
            ):
                selected, refusals = preflight(inspection, [wrong_id])
                self.assertEqual(selected, [])
                self.assertTrue(any(item["code"] == "approval-format-invalid" for item in refusals))
                self.assertTrue(any(item["code"] == "approval-not-current" for item in refusals))

    def test_large_ignored_sets_are_digest_bound_without_dumping_every_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent)
            linked = parent / "linked"
            self.linked_worktree(root, linked)
            for index in range(500):
                (linked / f"private-{index:04d}.cache").write_text("keep\n", encoding="ascii")

            result = inspect_git_hygiene(root, [], [str(linked)])
            ignored = result["items"][0]["evidence"]["ignored"]

            self.assertEqual(ignored["count"], 500)
            self.assertEqual(len(ignored["sample"]), 10)
            self.assertTrue(ignored["sample_truncated"])
            self.assertLess(len(json.dumps(result)), 20_000)

    def test_apply_deletes_only_the_approved_fully_merged_local_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.git(root, "branch", "merged-topic")
            inspection = inspect_git_hygiene(root, ["merged-topic"], [])
            candidate = inspection["items"][0]

            result, exit_code = apply_git_hygiene(self.args(
                root, branches=["merged-topic"], approvals=[candidate["id"]],
            ))

            self.assertEqual(exit_code, 0, result)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(self.git(root, "branch", "--list", "merged-topic").stdout.strip(), "")
            self.assertEqual(self.git(root, "branch", "--show-current").stdout.strip(), "main")
            self.assertEqual(result["recovery"]["status"], "discarded")

    def test_apply_removes_clean_worktree_but_preserves_its_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent)
            linked = parent / "linked"
            self.linked_worktree(root, linked)
            inspection = inspect_git_hygiene(root, [], [str(linked)])
            candidate = inspection["items"][0]

            result, exit_code = apply_git_hygiene(self.args(
                root, worktrees=[str(linked)], approvals=[candidate["id"]],
            ))

            self.assertEqual(exit_code, 0, result)
            self.assertEqual(result["status"], "completed")
            self.assertFalse(linked.exists())
            self.assertIn("linked-topic", self.git(root, "branch", "--list", "linked-topic").stdout)
            self.assertNotIn(str(linked), self.git(root, "worktree", "list", "--porcelain").stdout)

    def test_stale_worktree_approval_is_refused_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent)
            linked = parent / "linked"
            self.linked_worktree(root, linked)
            inspection = inspect_git_hygiene(root, [], [str(linked)])
            candidate = inspection["items"][0]
            (linked / "new.txt").write_text("new\n", encoding="ascii")

            result, exit_code = apply_git_hygiene(self.args(
                root, worktrees=[str(linked)], approvals=[candidate["id"]],
            ))

            self.assertEqual(exit_code, 2)
            self.assertEqual(result["status"], "refused")
            self.assertTrue(linked.exists())
            self.assertTrue((linked / "new.txt").exists())
            self.assertFalse(result["git_mutations_performed"])

    def test_unique_branch_remains_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.git(root, "switch", "-qc", "unique-topic")
            (root / "unique.txt").write_text("unique\n", encoding="ascii")
            self.git(root, "add", "unique.txt")
            self.git(root, "commit", "-qm", "unique")
            self.git(root, "switch", "-q", "main")

            result = inspect_git_hygiene(root, ["unique-topic"], [])

            self.assertEqual(result["items"][0]["classification"], "review")
            self.assertIn("unique work", result["items"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
