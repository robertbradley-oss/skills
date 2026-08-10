from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from analyze_file_organization import analyze_file_organization, render_markdown  # noqa: E402


class FileOrganizationAnalysisTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, text=True,
            stdin=subprocess.DEVNULL, capture_output=True,
        )

    def repository(self, parent: Path, files: dict[str, bytes]) -> Path:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Clean Up Test")
        self.git(root, "config", "user.email", "clean-up@example.invalid")
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "fixture")
        return root

    def test_loose_untracked_image_gets_exact_review_only_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"references/keep.txt": b"keep\n"})
            loose = root / "mockup.png"
            loose.write_bytes(b"image-bytes")
            before = loose.read_bytes()

            result = analyze_file_organization(root)

            self.assertEqual(result["schema"], "clean-up-file-organization/v2")
            self.assertFalse(result["mutations_performed"])
            self.assertFalse(result["apply_supported"])
            self.assertEqual(len(result["findings"]), 1)
            finding = result["findings"][0]
            self.assertTrue(finding["id"].startswith("FO-"))
            self.assertEqual(finding["path"], "mockup.png")
            self.assertEqual(finding["suggested_destination"], "references/mockup.png")
            self.assertEqual(finding["git_state"], "untracked")
            self.assertEqual(finding["classification"], "move-recommended")
            self.assertEqual(finding["proposed_action"], "move-file-with-reference-updates")
            self.assertEqual(finding["references"]["match_count"], 0)
            self.assertEqual(result["proposed_authorization_set"], [])
            self.assertEqual(loose.read_bytes(), before)
            self.assertFalse((root / "references" / "mockup.png").exists())

    def test_changed_tracked_document_is_labeled_without_being_moved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "docs/guide.md": b"guide\n",
                "notes.md": b"old notes\n",
            })
            (root / "notes.md").write_bytes(b"changed notes\n")

            result = analyze_file_organization(root)

            finding = next(item for item in result["findings"] if item["path"] == "notes.md")
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertEqual(finding["suggested_destination"], "docs/notes.md")
            self.assertEqual(finding["classification"], "keep")
            self.assertIn("changed", finding["reason"])
            self.assertTrue((root / "notes.md").exists())

    def test_multiple_established_destinations_remain_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "assets/keep.txt": b"keep\n",
                "references/keep.txt": b"keep\n",
            })
            (root / "diagram.svg").write_bytes(b"<svg/>\n")

            result = analyze_file_organization(root)

            finding = result["findings"][0]
            self.assertIsNone(finding["suggested_destination"])
            self.assertEqual(finding["candidate_directories"], ["assets", "references"])
            self.assertEqual(finding["classification"], "keep")
            self.assertIn("no unique destination is proven", finding["reason"])

    def test_root_control_and_entrypoint_files_are_never_organization_leads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "docs/guide.md": b"guide\n",
                "scripts/helper.ps1": b"Write-Output helper\n",
                "README.md": b"readme\n",
                "GAMEPLAN.md": b"plan\n",
                "build.ps1": b"Write-Output build\n",
                ".notes.md": b"hidden\n",
            })

            result = analyze_file_organization(root)

            self.assertEqual(result["findings"], [])
            self.assertTrue(result["summary"]["coverage_complete"])

    def test_file_budget_exhaustion_is_reported_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"references/keep.txt": b"keep\n"})
            (root / "mockup.png").write_bytes(b"image-bytes")

            result = analyze_file_organization(root, max_bytes=1)

            self.assertEqual(result["findings"], [])
            self.assertTrue(result["summary"]["scan_truncated"])
            self.assertFalse(result["summary"]["coverage_complete"])
            self.assertIn(
                "file-organization-budget-exhausted",
                {item["code"] for item in result["coverage_gaps"]},
            )

    def test_markdown_states_review_only_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"docs/guide.md": b"guide\n"})
            (root / "notes.md").write_bytes(b"notes\n")

            markdown = render_markdown(analyze_file_organization(root))

            self.assertIn("FO-", markdown)
            self.assertIn("Mutations: `none`", markdown)
            self.assertIn("FO IDs record automatic move-or-keep decisions", markdown)

    def test_referenced_file_is_still_decided_with_exact_updates_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "docs/guide.md": b"See notes.md for details.\n",
                "notes.md": b"notes\n",
            })

            result = analyze_file_organization(root)

            finding = next(item for item in result["findings"] if item["path"] == "notes.md")
            self.assertEqual(finding["classification"], "move-recommended")
            self.assertEqual(finding["references"]["match_count"], 1)
            self.assertIn("Update 1 repository path reference", finding["reason"])


if __name__ == "__main__":
    unittest.main()
