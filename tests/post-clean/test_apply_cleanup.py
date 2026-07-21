from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSPECT_SCRIPT = ROOT / "post-clean" / "scripts" / "inspect_footprint.py"
APPLY_SCRIPT = ROOT / "post-clean" / "scripts" / "apply_cleanup.py"


def footprint_text(task_rows: list[str], obligation_rows: list[str] | None = None) -> str:
    obligations = "\n".join(obligation_rows or [])
    return f"""# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Apply fixture`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-19`
Finalized: `2026-07-19`
Baseline: `clean fixture`
Coverage: `workspace paths only`

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
{"\n".join(task_rows)}

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
{obligations}
"""


class ApplyCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.footprint = self.workspace / ".gameplan" / "footprints" / "source.md"
        self.footprint.parent.mkdir(parents=True)
        (self.workspace / "tmp").mkdir()
        (self.workspace / "sentinel.txt").write_text("keep\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def footprint_relative(self) -> str:
        return self.footprint.relative_to(self.workspace).as_posix()

    def write_file_fixture(self, content: str = "debug\n") -> None:
        (self.workspace / "tmp" / "debug.log").write_text(content, encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/debug.log` | `created` | `temporary` | `remove` | Disposable debug output. |"
                ],
                ["| `tmp/debug.log` | `remove` | `open` | Remove after completion. |"],
            ),
            encoding="utf-8",
        )

    def run_json(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def inspect(self) -> dict:
        completed = self.run_json(
            [
                sys.executable,
                "-B",
                str(INSPECT_SCRIPT),
                "--workspace",
                str(self.workspace),
                "--footprint",
                self.footprint_relative,
                "--format",
                "json",
            ]
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def validation(self, code: str) -> str:
        return json.dumps([sys.executable, "-B", "-c", code])

    def apply(self, approved: list[str], validation: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            "-B",
            str(APPLY_SCRIPT),
            "--workspace",
            str(self.workspace),
            "--footprint",
            self.footprint_relative,
        ]
        for item_id in approved:
            command.extend(["--approve", item_id])
        command.extend(["--validate-command", validation, "--validation-timeout", "30"])
        completed = self.run_json(command)
        return completed, json.loads(completed.stdout)

    def candidate_id(self, result: dict, path: str = "tmp/debug.log") -> str:
        return next(
            item["id"]
            for item in result["items"]
            if item["path"] == path and item["classification"] == "candidate"
        )

    def test_success_removes_exact_path_updates_obligation_and_reports(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id(self.inspect())
        validation = self.validation(
            "from pathlib import Path; raise SystemExit(0 if Path('sentinel.txt').is_file() else 1)"
        )

        completed, result = self.apply([item_id], validation)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["status"], "completed")
        self.assertFalse((self.workspace / "tmp" / "debug.log").exists())
        self.assertEqual(result["obligations_updated"], 1)
        self.assertIn("| `tmp/debug.log` | `remove` | `done` |", self.footprint.read_text())
        self.assertEqual(result["recovery"]["status"], "discarded")
        report = self.workspace / result["report"]
        self.assertTrue(report.is_file())
        self.assertIn("Status: `completed`", report.read_text())

    def test_stale_id_refuses_without_removing_target(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id(self.inspect())
        (self.workspace / "tmp" / "debug.log").write_text("changed\n", encoding="utf-8")
        validation = self.validation("raise SystemExit(0)")

        completed, result = self.apply([item_id], validation)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue((self.workspace / "tmp" / "debug.log").is_file())
        self.assertIn("approval-not-current", {item["code"] for item in result["refusals"]})
        self.assertTrue((self.workspace / result["report"]).is_file())

    def test_post_clean_validation_failure_restores_original(self) -> None:
        self.write_file_fixture("restore-me\n")
        item_id = self.candidate_id(self.inspect())
        validation = self.validation(
            "from pathlib import Path; raise SystemExit(0 if Path('tmp/debug.log').is_file() else 1)"
        )

        completed, result = self.apply([item_id], validation)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "restore-me\n")
        self.assertIn("| `tmp/debug.log` | `remove` | `open` |", self.footprint.read_text())
        self.assertEqual(result["recovery"]["status"], "discarded")
        self.assertIn("Status: `restored`", (self.workspace / result["report"]).read_text())

    def test_baseline_validation_failure_refuses_before_cleanup(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id(self.inspect())

        completed, result = self.apply([item_id], self.validation("raise SystemExit(9)"))

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue((self.workspace / "tmp" / "debug.log").is_file())
        self.assertFalse(result["cleanup_mutations_performed"])
        self.assertIn(
            "baseline-validation-failed", {item["code"] for item in result["refusals"]}
        )

    def test_baseline_validation_state_change_invalidates_approval(self) -> None:
        self.write_file_fixture("before\n")
        item_id = self.candidate_id(self.inspect())
        validation = self.validation(
            "from pathlib import Path; Path('tmp/debug.log').write_text('changed-by-validation\\n'); raise SystemExit(0)"
        )

        completed, result = self.apply([item_id], validation)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(
            (self.workspace / "tmp" / "debug.log").read_text(), "changed-by-validation\n"
        )
        self.assertFalse(result["cleanup_mutations_performed"])
        self.assertIn("approval-not-current", {item["code"] for item in result["refusals"]})

    def test_directory_requires_every_descendant_id(self) -> None:
        bundle = self.workspace / "tmp" / "bundle"
        bundle.mkdir()
        (bundle / "data.txt").write_text("data\n", encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/bundle` | `created` | `scaffold` | `remove` | Disposable scaffold. |",
                    "| `tmp/bundle/data.txt` | `created` | `temporary` | `remove` | Scaffold data. |",
                ]
            ),
            encoding="utf-8",
        )
        inspected = self.inspect()
        directory_id = self.candidate_id(inspected, "tmp/bundle")

        completed, result = self.apply([directory_id], self.validation("raise SystemExit(0)"))

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue((bundle / "data.txt").is_file())
        self.assertIn(
            "directory-authorization-incomplete", {item["code"] for item in result["refusals"]}
        )

    def test_directory_with_every_descendant_approved_is_removed(self) -> None:
        bundle = self.workspace / "tmp" / "bundle"
        bundle.mkdir()
        (bundle / "data.txt").write_text("data\n", encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/bundle` | `created` | `scaffold` | `remove` | Disposable scaffold. |",
                    "| `tmp/bundle/data.txt` | `created` | `temporary` | `remove` | Scaffold data. |",
                ]
            ),
            encoding="utf-8",
        )
        inspected = self.inspect()
        approved = [
            item["id"] for item in inspected["items"] if item["classification"] == "candidate"
        ]

        completed, result = self.apply(approved, self.validation("raise SystemExit(0)"))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(bundle.exists())
        self.assertEqual({item["outcome"] for item in result["actions"]}, {"removed"})
        self.assertEqual(result["recovery"]["status"], "discarded")

    def test_targeted_edit_item_cannot_enter_apply(self) -> None:
        source = self.workspace / "src.txt"
        source.write_text("keep plus debug\n", encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `src.txt` | `pre-existing` | `deliverable` | `keep` | Intentional source. |"
                ],
                ["| `src.txt` | `remove` | `open` | Remove only the debug addition. |"],
            ),
            encoding="utf-8",
        )
        inspected = self.inspect()
        review_id = next(
            item["id"]
            for item in inspected["items"]
            if item["source"] == "cleanup-obligation"
        )

        completed, result = self.apply([review_id], self.validation("raise SystemExit(0)"))

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(source.read_text(), "keep plus debug\n")
        self.assertIn("approval-not-current", {item["code"] for item in result["refusals"]})


if __name__ == "__main__":
    unittest.main()
