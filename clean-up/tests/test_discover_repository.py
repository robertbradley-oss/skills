from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from discover_repository import discover, markdown_cell  # noqa: E402
from inspect_repository import inspect  # noqa: E402
from apply_cleanup import preflight  # noqa: E402


class DiscoverRepositoryTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, text=True,
            stdin=subprocess.DEVNULL, capture_output=True,
        )

    def repository(self, parent: Path) -> Path:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Clean Up Test")
        self.git(root, "config", "user.email", "clean-up@example.invalid")
        (root / ".gitignore").write_text("bin/\n", encoding="utf-8")
        (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
        self.git(root, "add", ".gitignore", "tracked.txt")
        self.git(root, "commit", "-m", "fixture")
        return root

    def test_discovery_finds_leads_without_authorizing_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            (root / "bin").mkdir()
            (root / "bin" / "output.dll").write_bytes(b"generated")
            (root / "scratch.txt").write_text("unknown\n", encoding="utf-8")
            (root / "tracked.txt").write_text("modified\n", encoding="utf-8")
            self.git(root, "branch", "merged-topic")

            result = discover(root, None, 50)
            targets = {(lead["surface"], lead["target"]): lead for lead in result["leads"]}

            self.assertEqual(result["schema"], "clean-up-discovery/v2")
            self.assertFalse(result["mutations_performed"])
            self.assertFalse(result["apply_supported"])
            self.assertEqual(result["provisional_authorization_set"], [])
            self.assertEqual(targets[("path", "bin")]["signal"], "generated-residue")
            self.assertEqual(targets[("path", "scratch.txt")]["signal"], "untracked-content")
            self.assertEqual(targets[("branch", "merged-topic")]["signal"], "merged-local-branch")
            self.assertNotIn(("path", "tracked.txt"), targets)
            self.assertTrue(all(lead["classification"] == "review" for lead in result["leads"]))
            self.assertTrue(all(lead["proposed_action"] == "none" for lead in result["leads"]))
            self.assertTrue(all(lead["id"].startswith("PD-") for lead in result["leads"]))

            inspected = inspect(root, ["scratch.txt"], None)
            self.assertEqual(inspected["items"][0]["classification"], "candidate")
            self.assertTrue(inspected["items"][0]["id"].startswith("PC-"))

            discovery_id = targets[("path", "scratch.txt")]["id"]
            selected, refusals = preflight(inspected, [discovery_id])
            self.assertEqual(selected, [])
            self.assertTrue(any(item["code"] == "approval-format-invalid" for item in refusals))
            self.assertTrue(any(item["code"] == "approval-not-current" for item in refusals))

            selected, refusals = preflight(inspected, ["DC-0123456789AB"])
            self.assertEqual(selected, [])
            self.assertTrue(any(item["code"] == "approval-format-invalid" for item in refusals))
            self.assertTrue(any(item["code"] == "approval-not-current" for item in refusals))

    def test_repository_integrity_lead_is_not_starved_by_result_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            (root / "scratch.txt").write_text("unknown\n", encoding="utf-8")
            broken = root / ".git" / "refs" / "heads" / "broken"
            broken.write_text("0000000000000000000000000000000000000000\n", encoding="ascii")

            result = discover(root, None, 1)

            self.assertEqual(len(result["leads"]), 1)
            self.assertEqual(result["leads"][0]["surface"], "repository")
            self.assertEqual(result["leads"][0]["signal"], "git-reference-error")
            self.assertTrue(result["summary"]["truncated"])

    def test_non_git_folder_finds_residue_and_exact_duplicates_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src" / "first.py").write_bytes(b"print('same')\n")
            (root / "src" / "second.py").write_bytes(b"print('same')\n")
            (root / "notes.log").write_text("temporary\n", encoding="utf-8")
            (root / "build").mkdir()
            (root / "build" / "output.bin").write_bytes(b"generated")
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

            result = discover(root, None, 50)
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            targets = {(lead["surface"], lead["target"]): lead for lead in result["leads"]}
            duplicate = next(
                lead for lead in result["leads"] if lead["signal"] == "exact-duplicate"
            )

            self.assertEqual(after, before)
            self.assertEqual(result["scope_type"], "folder")
            self.assertFalse(result["mutations_performed"])
            self.assertFalse(result["apply_supported"])
            self.assertEqual(targets[("path", "build")]["signal"], "generated-residue")
            self.assertEqual(targets[("path", "notes.log")]["signal"], "temporary-file")
            self.assertEqual(
                duplicate["evidence"]["paths"], ["src/first.py", "src/second.py"]
            )
            self.assertEqual(duplicate["classification"], "review")
            self.assertEqual(duplicate["proposed_action"], "none")
            self.assertTrue(duplicate["id"].startswith("PD-"))

    def test_filesystem_scan_skips_control_and_generated_subtrees(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git" / "objects").mkdir(parents=True)
            (root / ".clean-up" / "reports").mkdir(parents=True)
            (root / ".post-clean" / "reports").mkdir(parents=True)
            (root / "node_modules" / "package").mkdir(parents=True)
            (root / "visible.txt").write_bytes(b"duplicate")
            (root / ".git" / "objects" / "hidden.txt").write_bytes(b"duplicate")
            (root / ".clean-up" / "reports" / "current.json").write_bytes(b"duplicate")
            (root / ".post-clean" / "reports" / "legacy.json").write_bytes(b"duplicate")
            (root / "node_modules" / "package" / "vendored.txt").write_bytes(b"duplicate")

            result = discover(root, None, 50)
            duplicate_paths = {
                path
                for lead in result["leads"] if lead["signal"] == "exact-duplicate"
                for path in lead["evidence"]["paths"]
            }

            self.assertEqual(duplicate_paths, set())
            self.assertIn(
                ("path", "node_modules"),
                {(lead["surface"], lead["target"]) for lead in result["leads"]},
            )
            self.assertGreaterEqual(result["summary"]["filesystem_control_paths_skipped"], 3)

    def test_filesystem_and_hash_budgets_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(4):
                (root / f"file-{index}.txt").write_bytes(b"same")

            file_limited = discover(root, None, 50, max_files=2, max_hash_bytes=100)
            hash_limited = discover(root, None, 50, max_files=10, max_hash_bytes=4)

            self.assertTrue(file_limited["summary"]["filesystem_scan_truncated"])
            self.assertEqual(file_limited["summary"]["filesystem_files"], 2)
            self.assertTrue(hash_limited["summary"]["duplicate_hash_budget_exhausted"])
            self.assertLessEqual(hash_limited["summary"]["duplicate_hashed_bytes"], 4)
            self.assertFalse(any(
                lead["signal"] == "exact-duplicate" for lead in hash_limited["leads"]
            ))

    def test_markdown_cell_neutralizes_untrusted_path_markup(self) -> None:
        self.assertEqual(
            markdown_cell("`path|name\r\nnext`"),
            "'path\\|name  next'",
        )


if __name__ == "__main__":
    unittest.main()
