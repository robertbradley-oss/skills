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

            self.assertEqual(result["schema"], "clean-up-tracked-code/v4")
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

    def test_typescript_and_tsx_emit_only_conservative_unreferenced_leads(self) -> None:
        source = """function usedHelper() { return 1; }
function unusedHelper() { return 2; }
const UsedComponent = () => <span>{usedHelper()}</span>;
const unusedValue = 3;
export function exportedHandler() { return 4; }

class Worker {
    private usedMethod() { return 1; }
    private unusedMethod() { return 2; }
    #unusedSecret = 3;
    @frameworkManaged()
    private decoratedOnly() { return 4; }
    run() { return this.usedMethod(); }
}

export const worker = new Worker();
export default function Page() { return <UsedComponent />; }
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/page.tsx": source})

            result = analyze_tracked_code(root)
            findings = {item["symbol"]: item for item in result["findings"]}

            self.assertEqual(set(findings), {"unusedHelper", "unusedValue", "unusedMethod", "unusedSecret"})
            self.assertEqual(result["summary"]["supported_languages"], {"typescript": 1})
            self.assertEqual(result["summary"]["unsupported_extensions"], {})
            self.assertTrue(result["summary"]["coverage_complete"])
            self.assertTrue(all(item["confidence"] == "weak" for item in findings.values()))
            self.assertTrue(all(item["classification"] == "review" for item in findings.values()))
            self.assertEqual(findings["unusedMethod"]["signal"], "unreferenced-private-member")
            self.assertEqual(
                findings["unusedHelper"]["signal"], "unreferenced-typescript-declaration",
            )

    def test_typescript_references_cross_ts_and_js_and_generated_declarations_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "src/helper.ts": "function sharedHelper() { return 1; }\n",
                "src/use.js": "console.log(sharedHelper());\n",
                "next-env.d.ts": "declare function generatedOnly(): void;\n",
            })

            result = analyze_tracked_code(root)

            self.assertNotIn("sharedHelper", {item["symbol"] for item in result["findings"]})
            self.assertNotIn("generatedOnly", {item["symbol"] for item in result["findings"]})
            self.assertEqual(
                result["summary"]["supported_languages"], {"javascript": 1, "typescript": 2},
            )
            self.assertEqual(result["summary"]["unsupported_extensions"], {})

    def test_javascript_and_jsx_emit_only_conservative_unreferenced_leads(self) -> None:
        source = """function usedHelper() { return 1; }
function unusedHelper() { return 2; }
const UsedComponent = () => <span>{usedHelper()}</span>;
const unusedValue = 3;
var unusedLegacy = 4;
export function exportedHandler() { return 5; }

class Worker {
    #usedMethod() { return 1; }
    static #unusedMethod() { return 2; }
    #unusedSecret = 3;
    @frameworkManaged()
    #decoratedOnly() { return 4; }
    run() { return this.#usedMethod(); }
}

export const worker = new Worker();
export default function Page() { return <UsedComponent />; }
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/page.jsx": source})

            result = analyze_tracked_code(root)
            findings = {item["symbol"]: item for item in result["findings"]}

            self.assertEqual(
                set(findings),
                {"unusedHelper", "unusedValue", "unusedLegacy", "unusedMethod", "unusedSecret"},
            )
            self.assertEqual(result["summary"]["supported_languages"], {"javascript": 1})
            self.assertEqual(result["summary"]["unsupported_extensions"], {})
            self.assertTrue(result["summary"]["coverage_complete"])
            self.assertTrue(all(item["confidence"] == "weak" for item in findings.values()))
            self.assertTrue(all(item["classification"] == "review" for item in findings.values()))
            self.assertEqual(findings["unusedMethod"]["signal"], "unreferenced-private-member")
            self.assertEqual(
                findings["unusedHelper"]["signal"], "unreferenced-javascript-declaration",
            )

    def test_javascript_references_cross_jsx_and_typescript_and_generated_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {
                "src/helper.js": "function sharedHelper() { return 1; }\n",
                "src/use.tsx": "export const value = sharedHelper();\n",
                "src/component.jsx": "export const View = () => <span>{sharedHelper()}</span>;\n",
                "src/generated.generated.js": "function generatedOnly() { return 1; }\n",
            })

            result = analyze_tracked_code(root)

            symbols = {item["symbol"] for item in result["findings"]}
            self.assertNotIn("sharedHelper", symbols)
            self.assertNotIn("generatedOnly", symbols)
            self.assertEqual(
                result["summary"]["supported_languages"], {"javascript": 3, "typescript": 1},
            )

    def test_javascript_commonjs_dynamic_and_string_references_suppress_leads(self) -> None:
        source = """function commonJsHandler() { return 1; }
function stringNamed() { return 2; }
function dynamicNamed() { return 3; }
function* unusedGenerator() { yield 4; }
module.exports = { commonJsHandler };
console.log("stringNamed");
registry["dynamicNamed"]();
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/helper.js": source})

            result = analyze_tracked_code(root)

            self.assertEqual([item["symbol"] for item in result["findings"]], ["unusedGenerator"])

    def test_modified_javascript_is_analyzed_and_state_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/helper.js": "export const value = 1;\n"})
            (root / "src" / "helper.js").write_text(
                "function unfinishedHelper() { return 1; }\n", encoding="ascii",
            )

            changed = analyze_tracked_code(root)
            finding = changed["findings"][0]

            self.assertEqual(finding["symbol"], "unfinishedHelper")
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertTrue(finding["evidence"]["changed_file"])
            self.assertIn("modified worktree content", finding["reason"])
            changed_id = finding["id"]

            self.git(root, "add", "src/helper.js")
            self.git(root, "commit", "-qm", "accept helper")
            clean = analyze_tracked_code(root)

            self.assertEqual(clean["findings"][0]["git_state"], "tracked-clean")
            self.assertNotEqual(changed_id, clean["findings"][0]["id"])

    def test_modified_typescript_is_analyzed_and_state_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary), {"src/helper.ts": "export const value = 1;\n"})
            (root / "src" / "helper.ts").write_text(
                "function unfinishedHelper() { return 1; }\n", encoding="ascii",
            )

            changed = analyze_tracked_code(root)
            finding = changed["findings"][0]

            self.assertEqual(finding["symbol"], "unfinishedHelper")
            self.assertEqual(finding["git_state"], "tracked-changed")
            self.assertTrue(finding["evidence"]["changed_file"])
            self.assertIn("modified worktree content", finding["reason"])
            changed_id = finding["id"]

            self.git(root, "add", "src/helper.ts")
            self.git(root, "commit", "-qm", "accept helper")
            clean = analyze_tracked_code(root)

            self.assertEqual(clean["findings"][0]["git_state"], "tracked-clean")
            self.assertNotEqual(changed_id, clean["findings"][0]["id"])

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
