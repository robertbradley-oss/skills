from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from analyze_tracked_code import analyze_tracked_code  # noqa: E402


class TrackedCodeAnalysisTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, text=True,
            stdin=subprocess.DEVNULL, capture_output=True,
        )

    def repository(self, parent: Path, files: dict[str, str]) -> Path:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Clean Up Test")
        self.git(root, "config", "user.email", "clean-up@example.invalid")
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="ascii")
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "fixture")
        return root

    def test_reports_only_unreferenced_unattributed_private_csharp_members(self) -> None:
        source = """using System;
class Sample
{
    private int usedField;
    private int unusedField;
    private void Used() { usedField++; }
    private void Unused() { }
    private void OnFrameworkCallback() { }
    [Obsolete]
    private void Attributed() { }
    private void NamedByString() { }
    public void Run() { Used(); Console.WriteLine(\"NamedByString\"); }
}
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/Sample.cs": source})

            result = analyze_tracked_code(root)
            findings = {item["symbol"]: item for item in result["findings"]}

            self.assertEqual(result["schema"], "clean-up-tracked-code/v2")
            self.assertFalse(result["mutations_performed"])
            self.assertFalse(result["apply_supported"])
            self.assertEqual(set(findings), {"unusedField", "Unused"})
            self.assertTrue(all(item["id"].startswith("DC-") for item in findings.values()))
            self.assertTrue(all(item["classification"] == "review" for item in findings.values()))
            self.assertEqual(result["proposed_authorization_set"], [])
            self.assertTrue(result["summary"]["coverage_complete"])

    def test_new_reference_removes_lead_and_changes_corpus_state(self) -> None:
        source = """class Sample
{
    private void MaybeUnused() { }
}
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/Sample.cs": source})
            first = analyze_tracked_code(root)
            (root / "src" / "Use.cs").write_text(
                "class Use { string Name = \"MaybeUnused\"; }\n", encoding="ascii",
            )
            self.git(root, "add", "src/Use.cs")
            self.git(root, "commit", "-qm", "add reflection reference")

            second = analyze_tracked_code(root)

            self.assertEqual([item["symbol"] for item in first["findings"]], ["MaybeUnused"])
            self.assertNotIn("MaybeUnused", {item["symbol"] for item in second["findings"]})

    def test_changed_supported_files_are_analyzed_and_clearly_labeled_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/Sample.cs": "class Sample { }\n"})
            (root / "src" / "Sample.cs").write_text(
                "class Sample\n{\n    private void NewUnused() { }\n}\n", encoding="ascii",
            )

            result = analyze_tracked_code(root)

            self.assertEqual([item["symbol"] for item in result["findings"]], ["NewUnused"])
            finding = result["findings"][0]
            self.assertTrue(finding["evidence"]["changed_file"])
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertEqual(finding["confidence"], "weak")
            self.assertEqual(finding["classification"], "review")
            self.assertIn("modified worktree content", finding["reason"])
            self.assertEqual(result["summary"]["changed_supported_files"], 1)
            self.assertEqual(result["summary"]["changed_supported_files_analyzed"], 1)
            self.assertTrue(result["summary"]["coverage_complete"])
            self.assertNotIn("changed-supported-files", {item["code"] for item in result["coverage_gaps"]})

            changed_id = finding["id"]
            self.git(root, "add", "src/Sample.cs")
            self.git(root, "commit", "-qm", "accept source change")
            clean_result = analyze_tracked_code(root)

            self.assertFalse(clean_result["findings"][0]["evidence"]["changed_file"])
            self.assertEqual(clean_result["findings"][0]["git_state"], "tracked-clean")
            self.assertNotEqual(changed_id, clean_result["findings"][0]["id"])

    def test_unsupported_languages_are_reported_without_false_clean_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "src/Sample.cs": "class Sample { }\n",
                "tools/build.py": "def invoke_unused():\n    pass\n",
            })

            result = analyze_tracked_code(root)

            self.assertEqual(result["summary"]["unsupported_extensions"], {".py": 1})
            self.assertFalse(result["summary"]["coverage_complete"])
            self.assertIn("unsupported-source-languages", {item["code"] for item in result["coverage_gaps"]})

    def test_powershell_functions_are_case_insensitive_review_leads_only(self) -> None:
        script = """function Invoke-Used {
    Write-Output used
}

function Invoke-Unused {
    Write-Output unused
}

invoke-used
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"tools/build.ps1": script})

            result = analyze_tracked_code(root)

            self.assertEqual([item["symbol"] for item in result["findings"]], ["Invoke-Unused"])
            finding = result["findings"][0]
            self.assertEqual(finding["signal"], "unreferenced-script-function")
            self.assertEqual(finding["confidence"], "weak")
            self.assertEqual(finding["classification"], "review")
            self.assertEqual(result["summary"]["supported_languages"], {"powershell": 1})
            self.assertTrue(result["summary"]["coverage_complete"])

    def test_modified_powershell_function_is_analyzed_and_labeled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "tools/build.ps1": "Write-Output initial\n",
            })
            (root / "tools" / "build.ps1").write_text(
                "function Invoke-NewUnused {\n    Write-Output unused\n}\n",
                encoding="ascii",
            )

            result = analyze_tracked_code(root)

            self.assertEqual([item["symbol"] for item in result["findings"]], ["Invoke-NewUnused"])
            finding = result["findings"][0]
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertTrue(finding["evidence"]["changed_file"])
            self.assertEqual(finding["classification"], "review")
            self.assertTrue(result["summary"]["coverage_complete"])

    def test_control_files_and_generated_csharp_are_not_declaration_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "GAMEPLAN.md": "private void Phantom() { }\n",
                ".gameplan/state.cs": "class Hidden\n{\n    private void HiddenUnused() { }\n}\n",
                "src/Generated.g.cs": "class Generated\n{\n    private void GeneratedUnused() { }\n}\n",
                "src/Real.cs": "class Real\n{\n    private void RealUnused() { }\n}\n",
            })

            result = analyze_tracked_code(root)
            symbols = {item["symbol"] for item in result["findings"]}

            self.assertEqual(symbols, {"RealUnused"})
            self.assertEqual(result["summary"]["supported_source_files"], 2)

    def test_exhausted_budget_suppresses_findings_and_marks_scan_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "src/Sample.cs": "class Sample { private void Unused() { } }\n",
            })

            result = analyze_tracked_code(root, max_bytes=1)

            self.assertEqual(result["findings"], [])
            self.assertTrue(result["summary"]["scan_truncated"])
            self.assertFalse(result["summary"]["coverage_complete"])
            self.assertIn("tracked-code-budget-exhausted", {item["code"] for item in result["coverage_gaps"]})


if __name__ == "__main__":
    unittest.main()
