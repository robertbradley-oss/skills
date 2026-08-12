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
from triage_repository import (  # noqa: E402
    decision_for_inspection, keep_git_hygiene_item, path_role_keep_reason,
    render_markdown, triage,
)


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
        (root / "tracked.data").write_text("tracked\n", encoding="ascii")
        tracked_paths = [".gitignore", "tracked.data"]
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

            self.assertEqual(result["schema"], "clean-up-triage/v6")
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
            git_candidate = next(
                item for item in result["git_hygiene_candidates"]
                if item["target"] == "merged-topic"
            )
            self.assertEqual(git_candidate["candidate_kind"], "merged-local-branch")
            self.assertTrue(git_candidate["candidate_id"].startswith("GC-"))
            self.assertEqual(result["proposed_git_authorization_set"], [git_candidate["candidate_id"]])

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

    def test_node_next_and_typescript_are_covered_in_one_broad_triage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            (root / ".gitignore").write_text(
                "node_modules/\n.next/\nnext-env.d.ts\n", encoding="ascii",
            )
            (root / "package.json").write_text(
                '{"name":"fixture","private":true,"dependencies":{"next":"15.0.0"}}\n',
                encoding="ascii",
            )
            (root / "package-lock.json").write_text(
                '{"name":"fixture","lockfileVersion":3}\n', encoding="ascii",
            )
            source = root / "src" / "helper.tsx"
            source.parent.mkdir()
            source.write_text(
                "function unusedHelper() { return <span />; }\n", encoding="ascii",
            )
            self.git(
                root, "add", ".gitignore", "package.json", "package-lock.json", "src/helper.tsx",
            )
            self.git(root, "commit", "-qm", "add next fixture")
            for directory in ("node_modules", ".next"):
                output = root / directory
                output.mkdir()
                (output / "generated.bin").write_bytes(b"generated")
            (root / "next-env.d.ts").write_text(
                '/// <reference types="next" />\n', encoding="ascii",
            )

            result = triage(root, None, 50)
            candidates = {item["path"]: item for item in result["safe_to_remove"]}

            self.assertEqual(result["verdict"], "cleanup-recommended")
            self.assertEqual(set(candidates), {"node_modules", ".next", "next-env.d.ts"})
            self.assertTrue(all(
                item["candidate_kind"] == "ignored-generated" for item in candidates.values()
            ))
            self.assertEqual([item["symbol"] for item in result["tracked_code"]], ["unusedHelper"])
            self.assertEqual(result["tracked_code_coverage"], [])
            self.assertEqual(result["summary"]["tracked_code_coverage_gap_count"], 0)

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

    def test_unpublished_legacy_release_is_kept_as_the_only_verified_copy(self) -> None:
        lead = {"id": "PD-0123456789AB", "reason": "release review"}
        item = {
            "classification": "review", "candidate_kind": None,
            "proposed_action": "none",
            "reason": "No single published stable GitHub release matches the manifest Version",
            "evidence": {
                "release_retention": {
                    "eligible": False,
                    "reason": "No single published stable GitHub release matches the manifest Version",
                },
            },
        }

        decision = decision_for_inspection(lead, item)

        self.assertEqual(decision["decision"], "keep")
        self.assertIn("remote recovery is not proven", decision["reason"])

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

    def test_structured_artifacts_references_and_installer_source_are_concrete_keeps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            (root / ".gitignore").write_text("**/bin/\nartifacts/\n", encoding="ascii")
            self.git(root, "add", ".gitignore")
            self.git(root, "commit", "-qm", "ignore evidence archive")
            for name in ("phase-1", "config-redesign"):
                bundle = root / "artifacts" / name
                bundle.mkdir(parents=True)
                (bundle / "evidence.json").write_text(
                    '{"bundle":"' + name + '"}\n', encoding="ascii",
                )
            (root / "references").mkdir()
            (root / "references" / "mockup.png").write_bytes(b"reference-image")
            (root / "installer").mkdir()
            (root / "installer" / "setup.iss").write_text("[Setup]\n", encoding="ascii")

            result = triage(root, None, 50)
            kept = {item["path"]: item["reason"] for item in result["keep"]}

            self.assertEqual(result["unresolved"], [], result["unresolved"])
            self.assertEqual(result["verdict"], "clean")
            self.assertIn("artifacts", kept)
            self.assertIn("structured", kept["artifacts"])
            self.assertIn("references", kept)
            self.assertIn("installer", kept)
            self.assertEqual(result["unresolved"], [])

    def test_phase_documentation_duplicates_are_kept_by_semantic_path_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            for phase in ("phase-1", "phase-2"):
                evidence = root / "docs" / phase / "evidence"
                evidence.mkdir(parents=True)
                (evidence / "selected.png").write_bytes(b"same-pixels")
            self.git(root, "add", "docs")
            self.git(root, "commit", "-qm", "add phase evidence")

            result = triage(root, None, 50)

            duplicate_keeps = [item for item in result["keep"] if item["surface"] == "duplicate-set"]
            self.assertEqual(len(duplicate_keeps), 1)
            self.assertIn("documentation meaning", duplicate_keeps[0]["reason"])
            self.assertEqual(result["unresolved"], [])
            self.assertEqual(result["verdict"], "clean")

    def test_versioned_release_root_is_kept_as_a_container_not_a_cleanup_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for version in ("1.0.0", "1.1.0"):
                release = root / "release" / f"setup-{version}"
                release.mkdir(parents=True)
                (release / "release-manifest.json").write_text(
                    '{"Version":"' + version + '"}\n', encoding="ascii",
                )
            lead = {"target": "release", "evidence": {"git": "untracked"}}

            reason = path_role_keep_reason(root, lead)

            self.assertIsNotNone(reason)
            self.assertIn("child releases are triaged independently", reason)

    def test_tracked_dead_code_and_language_gaps_prevent_false_clean_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            source = root / "src" / "Sample.cs"
            source.parent.mkdir()
            source.write_text(
                "class Sample\n{\n    private void Unused() { }\n}\n", encoding="ascii",
            )
            tools = root / "tools"
            tools.mkdir()
            (tools / "build.mjs").write_text(
                "function invokeBuild() { return 1; }\n", encoding="ascii",
            )
            self.git(root, "add", "src/Sample.cs", "tools/build.mjs")
            self.git(root, "commit", "-qm", "add tracked code")

            result = triage(root, None, 50)
            markdown = render_markdown(result)

            self.assertEqual(result["verdict"], "review-remains")
            self.assertEqual([item["symbol"] for item in result["tracked_code"]], ["Unused"])
            self.assertTrue(result["tracked_code"][0]["id"].startswith("DC-"))
            self.assertEqual(result["proposed_authorization_set"], [])
            self.assertEqual(result["proposed_git_authorization_set"], [])
            self.assertIn("unsupported-source-languages", {
                item["code"] for item in result["tracked_code_coverage"]
            })
            extension_gap = next(
                item for item in result["tracked_code_coverage"]
                if item["code"] == "unsupported-source-languages"
            )
            self.assertEqual(extension_gap["extensions"], {".mjs": 1})
            self.assertIn("## Tracked code", markdown)
            self.assertIn("DC-...` IDs are review handles only", markdown)

    def test_javascript_dead_code_is_review_only_with_complete_triage_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            source = root / "src" / "helper.jsx"
            source.parent.mkdir()
            source.write_text(
                "function unusedHelper() { return <span />; }\n", encoding="ascii",
            )
            self.git(root, "add", "src/helper.jsx")
            self.git(root, "commit", "-qm", "add JavaScript source")

            result = triage(root, None, 50)

            self.assertEqual(result["verdict"], "clean")
            self.assertEqual([item["symbol"] for item in result["tracked_code"]], ["unusedHelper"])
            finding = result["tracked_code"][0]
            self.assertEqual(finding["evidence"]["language"], "javascript")
            self.assertEqual(finding["classification"], "review")
            self.assertEqual(finding["proposed_action"], "none")
            self.assertEqual(result["tracked_code_coverage"], [])
            self.assertEqual(result["proposed_authorization_set"], [])
            self.assertEqual(result["proposed_git_authorization_set"], [])
            self.assertEqual(result["summary"]["tracked_code_coverage_gap_count"], 0)
            self.assertEqual(result["summary"]["unresolved_count"], 0)
            self.assertIn("tracked-code review lead(s) remain report-only", result["headline"])

    def test_file_organization_opportunity_is_decided_without_user_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide\n", encoding="ascii")
            self.git(root, "add", "docs/guide.md")
            self.git(root, "commit", "-qm", "add docs convention")
            (root / "notes.md").write_text("loose notes\n", encoding="ascii")

            result = triage(root, None, 50)
            markdown = render_markdown(result)

            self.assertEqual(result["verdict"], "organization-recommended")
            organization = next(
                item for item in result["file_organization"] if item["path"] == "notes.md"
            )
            self.assertTrue(organization["id"].startswith("FO-"))
            self.assertEqual(organization["suggested_destination"], "docs/notes.md")
            self.assertEqual(organization["classification"], "move-recommended")
            self.assertIn(organization, result["file_organization_moves"])
            self.assertNotIn(organization["id"], result["proposed_authorization_set"])
            self.assertNotIn(organization["id"], result["proposed_git_authorization_set"])
            self.assertIn("## File organization", markdown)
            self.assertIn("destinations already decided", result["headline"])
            self.assertIn("FO-...` IDs record decisions", markdown)

    def test_triage_analyzes_modified_supported_code_without_a_changed_file_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), outputs=0)
            source = root / "src" / "Sample.cs"
            source.parent.mkdir()
            source.write_text("class Sample { }\n", encoding="ascii")
            self.git(root, "add", "src/Sample.cs")
            self.git(root, "commit", "-qm", "add source")
            source.write_text(
                "class Sample\n{\n    private void WorkInProgress() { }\n}\n",
                encoding="ascii",
            )

            result = triage(root, None, 50)

            finding = next(
                item for item in result["tracked_code"] if item["symbol"] == "WorkInProgress"
            )
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertEqual(finding["classification"], "review")
            self.assertNotIn(
                "changed-supported-files",
                {item["code"] for item in result["tracked_code_coverage"]},
            )

    def test_dirty_linked_worktree_is_preserved_automatically_without_user_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.repository(parent, outputs=0)
            linked = parent / "dirty-linked"
            self.git(root, "worktree", "add", "-qb", "dirty-topic", str(linked), "main")
            (linked / "tracked.data").write_text("changed\n", encoding="ascii")

            result = triage(root, None, 50)

            kept = [item for item in result["git_hygiene_keep"] if item["surface"] == "worktree"]
            self.assertEqual(len(kept), 1)
            self.assertIn("unique local data", kept[0]["reason"])
            self.assertEqual(result["git_hygiene"], [])
            self.assertEqual(result["summary"]["git_hygiene_review_count"], 0)
            self.assertGreaterEqual(result["summary"]["git_hygiene_kept_count"], 1)
            self.assertEqual(result["verdict"], "clean")

    def test_git_inspection_error_defaults_to_preserve_instead_of_user_review(self) -> None:
        lead = {
            "id": "PD-0123456789AB", "surface": "worktree", "target": "C:/old/worktree",
        }
        item = {
            "surface": "worktree", "target": "C:/old/worktree",
            "classification": "review", "evidence": {"errors": ["ownership check failed"]},
        }

        kept = keep_git_hygiene_item(lead, item)

        self.assertIsNotNone(kept)
        self.assertEqual(kept["decision"], "keep")
        self.assertIn("safety default keeps", kept["reason"])


if __name__ == "__main__":
    unittest.main()
