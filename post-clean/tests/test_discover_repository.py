from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from discover_repository import discover  # noqa: E402
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
        self.git(root, "config", "user.name", "Post Clean Test")
        self.git(root, "config", "user.email", "post-clean@example.invalid")
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


if __name__ == "__main__":
    unittest.main()
