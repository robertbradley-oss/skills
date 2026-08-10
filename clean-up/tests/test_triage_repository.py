from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from apply_cleanup import preflight  # noqa: E402
from inspect_repository import inspect  # noqa: E402
from triage_repository import decision_for_inspection, render_markdown, triage  # noqa: E402


class TriageRepositoryTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, text=True,
            stdin=subprocess.DEVNULL, capture_output=True,
        )

    def repository(self, parent: Path, outputs: int = 1) -> Path:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Clean Up Test")
        self.git(root, "config", "user.email", "clean-up@example.invalid")
        (root / ".gitignore").write_text("**/bin/\n", encoding="ascii")
        for index in range(outputs):
            project = root / "src" / f"App{index}"
            project.mkdir(parents=True)
            (project / f"App{index}.csproj").write_text(
                '<Project Sdk="Microsoft.NET.Sdk"></Project>\n', encoding="ascii",
            )
        (root / "tracked.txt").write_text("tracked\n", encoding="ascii")
        tracked_paths = [".gitignore", "tracked.txt"]
        if outputs:
            tracked_paths.append("src")
        self.git(root, "add", *tracked_paths)
        self.git(root, "commit", "-qm", "fixture")
        for index in range(outputs):
            output = root / "src" / f"App{index}" / "bin"
            output.mkdir()
            (output / "output.dll").write_bytes(f"generated-{index}".encode("ascii"))
        return root

    def test_broad_triage_auto_inspects_strict_paths_without_promoting_git_new(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            (root / "scratch.txt").write_text("unknown\n", encoding="ascii")
            self.git(root, "branch", "merged-topic")

            result = triage(root, None, 50)

            self.assertEqual(result["schema"], "clean-up-triage/v1")
            self.assertFalse(result["mutations_performed"])
            self.assertEqual(result["verdict"], "cleanup-recommended")
            self.assertIn("prevent a fully clean verdict", result["headline"])
            self.assertEqual(result["summary"]["safe_to_remove_count"], 1)
            candidate = result["safe_to_remove"][0]
            self.assertEqual(candidate["path"], "src/App0/bin")
            self.assertEqual(candidate["candidate_kind"], "ignored-generated")
            self.assertTrue(candidate["candidate_id"].startswith("PC-"))
            self.assertEqual(result["proposed_authorization_set"], [candidate["candidate_id"]])
            self.assertTrue(all(not value.startswith("PD-") for value in result["proposed_authorization_set"]))
            self.assertIn("scratch.txt", {item["target"] for item in result["unresolved"]})
            self.assertIn("merged-topic", {item["target"] for item in result["git_hygiene"]})

            fresh = inspect(root, [candidate["path"]], None)
            selected, refusals = preflight(fresh, result["proposed_authorization_set"])
            self.assertEqual(len(selected), 1)
            self.assertEqual(refusals, [])

    def test_generic_untracked_content_never_becomes_an_automatic_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            (root / "important-draft.txt").write_text("keep me\n", encoding="ascii")

            result = triage(root, None, 50)

            self.assertEqual(result["safe_to_remove"], [])
            self.assertEqual(result["proposed_authorization_set"], [])
            draft = next(item for item in result["unresolved"] if item["target"] == "important-draft.txt")
            self.assertIn("preserved", draft["reason"])

    def test_newest_remote_release_is_kept_from_synthetic_inspection_evidence(self) -> None:
        lead = {"id": "PD-0123456789AB", "reason": "release review"}
        item = {
            "classification": "review",
            "candidate_kind": None,
            "proposed_action": "none",
            "reason": "Release is current or within the two newest stable releases",
            "evidence": {
                "release_retention": {
                    "reason": "Release is current or within the two newest stable releases",
                },
            },
        }

        decision = decision_for_inspection(lead, item)

        self.assertEqual(decision["decision"], "keep")
        self.assertIn("newest two", decision["reason"])

    def test_candidate_shaped_discovery_id_cannot_enter_safe_to_remove(self) -> None:
        lead = {"id": "PD-0123456789AB", "reason": "generated review"}
        item = {
            "id": "PD-0123456789AB",
            "classification": "candidate",
            "candidate_kind": "ignored-generated",
            "proposed_action": "remove-whole-path",
            "reason": "synthetic candidate",
            "evidence": {},
        }

        decision = decision_for_inspection(lead, item)

        self.assertEqual(decision["decision"], "unresolved")

    def test_markdown_leads_with_verdict_and_does_not_dump_all_unresolved_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            for index in range(4):
                (root / f"draft-{index}.txt").write_text("intentional\n", encoding="ascii")

            result = triage(root, None, 50)
            markdown = render_markdown(result, details_limit=2)

            self.assertIn("## Bottom line", markdown)
            self.assertIn("Repository verdict:", markdown)
            self.assertIn("additional unresolved lead(s)", markdown)
            self.assertIn("Discovery `PD-...` IDs never authorize removal.", markdown)

    def test_inspection_budget_exhaustion_forces_incomplete_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=2)

            result = triage(root, None, 50, max_inspections=1)

            self.assertTrue(result["summary"]["auto_inspect_truncated"])
            self.assertEqual(result["verdict"], "incomplete")
            self.assertIn("incomplete", result["headline"])

    def test_non_git_folder_is_reviewable_without_treating_git_absence_as_scan_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "build").mkdir()
            (root / "build" / "output.bin").write_bytes(b"generated")

            result = triage(root, None, 50)

            self.assertEqual(result["scope_type"], "folder")
            self.assertEqual(result["verdict"], "review-remains")
            self.assertFalse(any(item["code"] == "git-unavailable" for item in result["warnings"]))
            self.assertEqual(result["safe_to_remove"], [])


if __name__ == "__main__":
    unittest.main()
