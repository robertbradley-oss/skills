from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "clean-up" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_cleanup as apply_module
import inspect_repository as inspect_module


class ApplyCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.workspace, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.workspace, check=True)
        (self.workspace / "sentinel.txt").write_text("keep\n", encoding="utf-8")
        self.path = self.workspace / "tmp" / "debug.log"
        self.path.parent.mkdir()
        self.path.write_text("debug\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect(self) -> dict:
        return inspect_module.inspect(self.workspace, ["tmp/debug.log"], None)

    def candidate_id(self) -> str:
        return self.inspect()["provisional_authorization_set"][0]

    def validation(self, code: str = "raise SystemExit(0)") -> str:
        return json.dumps([sys.executable, "-B", "-c", code])

    def apply(self, item_id: str, validation: str | None = None, report: str | None = None) -> tuple[dict, int]:
        args = argparse.Namespace(
            workspace=str(self.workspace), path=["tmp/debug.log"], git_base=None,
            approve=[item_id], validate_command=[validation or self.validation()],
            validation_timeout=30, report=report,
        )
        return apply_module.apply_cleanup(args)

    def test_success_removes_exact_path_without_default_report(self) -> None:
        result, exit_code = self.apply(self.candidate_id())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["schema"], "clean-up-apply/v2")
        self.assertEqual(result["status"], "completed")
        self.assertFalse(self.path.exists())
        self.assertIsNone(result["report"])
        self.assertFalse((self.workspace / ".clean-up").exists())
        self.assertEqual(result["recovery"]["status"], "discarded")

    def test_optional_report_is_non_overwriting_and_outside_gameplan(self) -> None:
        report = ".clean-up/reports/run.json"
        result, exit_code = self.apply(self.candidate_id(), report=report)
        self.assertEqual(exit_code, 0)
        document = json.loads((self.workspace / report).read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], "clean-up-report/v2")
        self.assertEqual(document["recovery"]["status"], "discarded")
        self.assertFalse((self.workspace / ".gameplan").exists())
        self.assertEqual(result["report"], report)

    def test_stale_id_refuses_without_mutation(self) -> None:
        item_id = self.candidate_id()
        self.path.write_text("changed\n", encoding="utf-8")
        result, exit_code = self.apply(item_id)
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue(self.path.is_file())
        self.assertIn("approval-not-current", {item["code"] for item in result["refusals"]})

    def test_baseline_side_effect_invalidates_approval(self) -> None:
        validation = self.validation(
            "from pathlib import Path; Path('tmp/debug.log').write_text('changed\\n'); raise SystemExit(0)"
        )
        result, exit_code = self.apply(self.candidate_id(), validation)
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(self.path.read_text(), "changed\n")
        self.assertFalse(result["cleanup_mutations_performed"])

    def test_post_validation_failure_restores_original(self) -> None:
        validation = self.validation(
            "from pathlib import Path; raise SystemExit(0 if Path('tmp/debug.log').is_file() else 1)"
        )
        result, exit_code = self.apply(self.candidate_id(), validation)
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual(self.path.read_text(), "debug\n")
        self.assertEqual(result["recovery"]["status"], "discarded")

    def test_tracked_modified_path_cannot_enter_apply(self) -> None:
        subprocess.run(["git", "add", "tmp/debug.log"], cwd=self.workspace, check=True)
        subprocess.run(["git", "commit", "-qm", "track"], cwd=self.workspace, check=True)
        old_id = self.candidate_id() if self.inspect()["provisional_authorization_set"] else "PC-0123456789AB"
        self.path.write_text("modified\n", encoding="utf-8")
        result, exit_code = self.apply(old_id)
        self.assertEqual(exit_code, 2)
        self.assertTrue(self.path.exists())
        self.assertIn("approval-not-current", {item["code"] for item in result["refusals"]})


if __name__ == "__main__":
    unittest.main()
