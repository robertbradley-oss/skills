from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "post-clean" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_cleanup as apply_module
import inspect_footprint as inspect_module


def footprint_text(
    task_rows: list[str],
    obligation_rows: list[str] | None = None,
    protected_rows: list[str] | None = None,
) -> str:
    return f"""# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Adversarial fixture`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-19`
Finalized: `2026-07-19`
Baseline: `isolated fixture`
Coverage: `workspace paths only`

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
{chr(10).join(protected_rows or [])}

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
{chr(10).join(task_rows)}

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
{chr(10).join(obligation_rows or [])}
"""


class AdversarialFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.external_temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.external = Path(self.external_temporary.name)
        self.footprint = self.workspace / ".gameplan" / "footprints" / "source.md"
        self.footprint.parent.mkdir(parents=True)
        (self.workspace / "tmp").mkdir()
        (self.workspace / "sentinel.txt").write_text("keep\n", encoding="utf-8")
        self.retained_recovery: set[Path] = set()
        self.created_links: list[Path] = []

    def tearDown(self) -> None:
        for link in reversed(self.created_links):
            if os.path.lexists(link):
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)
        temp_root = Path(tempfile.gettempdir()).resolve()
        for recovery in self.retained_recovery:
            if recovery.exists():
                resolved = recovery.resolve()
                if resolved.parent != temp_root or not resolved.name.startswith("post-clean-"):
                    raise AssertionError(f"Unexpected recovery cleanup target: {resolved}")
                shutil.rmtree(resolved)
        self.temporary.cleanup()
        self.external_temporary.cleanup()

    def create_directory_link(self, link: Path, target: Path) -> None:
        if os.name != "nt":
            os.symlink(target, link, target_is_directory=True)
        else:
            command = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& { param([string]$Link,[string]$Target) "
                "$ErrorActionPreference='Stop'; "
                "New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null }",
                str(link),
                str(target),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                self.skipTest(f"Directory link creation unavailable: {completed.stderr.strip()}")
        self.created_links.append(link)

    @property
    def footprint_relative(self) -> str:
        return self.footprint.relative_to(self.workspace).as_posix()

    def write_file_fixture(self, content: str = "original\n") -> None:
        (self.workspace / "tmp" / "debug.log").write_text(content, encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/debug.log` | `created` | `temporary` | `remove` | Disposable output. |"
                ],
                ["| `tmp/debug.log` | `remove` | `open` | Remove after completion. |"],
            ),
            encoding="utf-8",
        )

    def inspect(self) -> dict:
        return inspect_module.inspect(self.workspace, self.footprint_relative)

    def candidate_id(self, path: str = "tmp/debug.log") -> str:
        return next(
            item["id"]
            for item in self.inspect()["items"]
            if item["path"] == path and item["classification"] == "candidate"
        )

    def validation(self, code: str = "raise SystemExit(0)") -> str:
        return json.dumps([sys.executable, "-B", "-c", code])

    def apply(self, approved: list[str], validation: str | None = None) -> tuple[dict, int]:
        args = argparse.Namespace(
            workspace=str(self.workspace),
            footprint=self.footprint_relative,
            approve=approved,
            validate_command=[validation or self.validation()],
            validation_timeout=30,
        )
        return apply_module.apply_cleanup(args)

    def retain_for_cleanup(self, result: dict) -> Path:
        location = result["recovery"].get("location")
        self.assertIsNotNone(location)
        recovery = Path(location)
        self.assertTrue(recovery.is_dir())
        self.retained_recovery.add(recovery)
        return recovery


class AdversarialInspectTests(AdversarialFixture):
    def test_traversal_and_duplicate_provenance_refuse_authorization(self) -> None:
        outside = self.external / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `../outside.txt` | `created` | `temporary` | `remove` | Escape attempt. |",
                    "| `tmp/duplicate.log` | `created` | `temporary` | `remove` | First row. |",
                    "| `tmp/duplicate.log` | `created` | `temporary` | `remove` | Duplicate row. |",
                ]
            ),
            encoding="utf-8",
        )

        result = self.inspect()

        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertIn("malformed-footprint", {item["code"] for item in result["refusals"]})
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_reserved_protected_and_unknown_rows_never_become_candidates(self) -> None:
        (self.workspace / ".gameplan" / "scratch.tmp").write_text("control\n", encoding="utf-8")
        (self.workspace / "tmp" / "protected.log").write_text("protected\n", encoding="utf-8")
        (self.workspace / "tmp" / "unknown.log").write_text("unknown\n", encoding="utf-8")
        self.footprint.write_text(
            footprint_text(
                [
                    "| `.gameplan/scratch.tmp` | `created` | `temporary` | `remove` | Reserved. |",
                    "| `tmp/protected.log` | `created` | `temporary` | `remove` | Protected. |",
                    "| `tmp/unknown.log` | `created` | `mystery` | `remove` | Unknown enum. |",
                ],
                protected_rows=[
                    "| `tmp/protected.log` | `untracked` | Preserve fixture. |"
                ],
            ),
            encoding="utf-8",
        )

        result = self.inspect()

        self.assertEqual(result["provisional_authorization_set"], [])
        classifications = {item["path"]: item["classification"] for item in result["items"]}
        self.assertEqual(classifications[".gameplan/scratch.tmp"], "preserve")
        self.assertEqual(classifications["tmp/protected.log"], "preserve")
        self.assertEqual(classifications["tmp/unknown.log"], "review")

    def test_link_ancestor_escape_is_review_only(self) -> None:
        outside = self.external / "outside.log"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.workspace / "tmp" / "escape"
        self.create_directory_link(link, self.external)
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/escape/outside.log` | `created` | `temporary` | `remove` | Escaping path. |"
                ]
            ),
            encoding="utf-8",
        )

        result = self.inspect()
        item = next(item for item in result["items"] if item["path"] == "tmp/escape/outside.log")

        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertEqual(item["classification"], "review")
        self.assertTrue(item["current"]["external_target"])
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_junction_fingerprint_is_review_only(self) -> None:
        candidate = self.workspace / "tmp" / "junction-like"
        candidate.mkdir()
        self.footprint.write_text(
            footprint_text(
                [
                    "| `tmp/junction-like` | `created` | `temporary` | `remove` | Junction fixture. |"
                ]
            ),
            encoding="utf-8",
        )
        real_is_junction = inspect_module.is_junction

        def simulated_junction(path: Path) -> bool:
            return path == candidate or real_is_junction(path)

        with mock.patch.object(inspect_module, "is_junction", side_effect=simulated_junction):
            result = self.inspect()

        item = next(item for item in result["items"] if item["path"] == "tmp/junction-like")
        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertEqual(item["classification"], "review")
        self.assertEqual(item["current"]["type"], "junction")

    def test_source_footprint_junction_escape_is_refused_before_read(self) -> None:
        shutil.rmtree(self.footprint.parent)
        external_footprints = self.external / "footprints"
        external_footprints.mkdir()
        (external_footprints / "source.md").write_text(
            footprint_text(
                [
                    "| `tmp/debug.log` | `created` | `temporary` | `remove` | External source. |"
                ]
            ),
            encoding="utf-8",
        )
        self.create_directory_link(self.footprint.parent, external_footprints)

        result = self.inspect()

        self.assertEqual(result["items"], [])
        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertIn("source-link-escape", {item["code"] for item in result["refusals"]})


class AdversarialApplyTests(AdversarialFixture):
    def test_recovery_creation_failure_refuses_without_mutation_and_reports(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()

        with mock.patch.object(
            apply_module, "create_recovery_root", side_effect=OSError("induced recovery failure")
        ):
            result, exit_code = self.apply([item_id])

        self.assertEqual(exit_code, 3)
        self.assertEqual(result["status"], "failed")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "original\n")
        self.assertFalse(result["cleanup_mutations_performed"])
        self.assertIn("recovery-create-failed", {item["code"] for item in result["refusals"]})
        self.assertTrue((self.workspace / result["report"]).is_file())

    def test_initial_report_failure_discards_empty_recovery_and_preserves_target(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        original_write = apply_module.atomic_write_text

        def fail_report(path: Path, content: str) -> None:
            if "cleanups" in path.parts:
                raise OSError("induced report failure")
            original_write(path, content)

        with mock.patch.object(apply_module, "atomic_write_text", side_effect=fail_report):
            result, exit_code = self.apply([item_id])

        self.assertEqual(exit_code, 3)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["recovery"]["status"], "discarded")
        self.assertIsNone(result["recovery"]["location"])
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "original\n")
        self.assertFalse(result["cleanup_mutations_performed"])
        self.assertIn("report-write-failed", {item["code"] for item in result["refusals"]})

    def test_completion_report_failure_restores_target_and_writes_final_record(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        original_write = apply_module.atomic_write_text
        report_writes = 0

        def fail_second_report(path: Path, content: str) -> None:
            nonlocal report_writes
            if "cleanups" in path.parts:
                report_writes += 1
                if report_writes == 2:
                    raise OSError("induced completion report failure")
            original_write(path, content)

        with mock.patch.object(apply_module, "atomic_write_text", side_effect=fail_second_report):
            result, exit_code = self.apply([item_id])

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "original\n")
        self.assertIn("| `tmp/debug.log` | `remove` | `open` |", self.footprint.read_text())
        report = self.workspace / result["report"]
        self.assertIn("Status: `restored`", report.read_text(encoding="utf-8"))

    def test_final_report_update_failure_surfaces_without_reversing_valid_cleanup(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        original_write = apply_module.atomic_write_text
        report_writes = 0

        def fail_third_report(path: Path, content: str) -> None:
            nonlocal report_writes
            if "cleanups" in path.parts:
                report_writes += 1
                if report_writes == 3:
                    raise OSError("induced final report update failure")
            original_write(path, content)

        with mock.patch.object(apply_module, "atomic_write_text", side_effect=fail_third_report):
            result, exit_code = self.apply([item_id])

        self.assertEqual(exit_code, 3)
        self.assertEqual(result["status"], "completed-report-update-failed")
        self.assertFalse((self.workspace / "tmp" / "debug.log").exists())
        self.assertEqual(result["recovery"]["status"], "discarded")
        self.assertIn("report-update-failed", {item["code"] for item in result["refusals"]})
        self.assertIn(
            "Status: `completed`",
            (self.workspace / result["report"]).read_text(encoding="utf-8"),
        )

    def test_discard_failure_retains_recovery_and_reports_completed_cleanup(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()

        with mock.patch.object(
            apply_module, "discard_recovery", return_value=(False, "induced discard failure")
        ):
            result, exit_code = self.apply([item_id])

        recovery = self.retain_for_cleanup(result)
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed-recovery-retained")
        self.assertEqual(result["recovery"]["status"], "retained")
        self.assertTrue((recovery / "recovery-map.json").is_file())
        self.assertTrue((recovery / "item-0001").is_file())
        self.assertFalse((self.workspace / "tmp" / "debug.log").exists())
        self.assertIn("| `tmp/debug.log` | `remove` | `done` |", self.footprint.read_text())

    def test_concurrent_target_reappearance_requires_manual_recovery(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        validation = self.validation(
            "from pathlib import Path; p=Path('tmp/debug.log'); "
            "p.write_text('concurrent\\n') if not p.exists() else None; raise SystemExit(0)"
        )

        result, exit_code = self.apply([item_id], validation)

        recovery = self.retain_for_cleanup(result)
        self.assertEqual(exit_code, 3)
        self.assertEqual(result["status"], "recovery-required")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "concurrent\n")
        self.assertEqual((recovery / "item-0001").read_text(), "original\n")
        self.assertTrue((recovery / "recovery-map.json").is_file())
        self.assertIn("| `tmp/debug.log` | `remove` | `open` |", self.footprint.read_text())
        self.assertIn("Status: `recovery-required`", (self.workspace / result["report"]).read_text())

    def test_recovery_identity_change_blocks_restoration(self) -> None:
        recovery, identity = apply_module.create_recovery_root(self.workspace, "identity-test")
        self.retained_recovery.add(recovery)

        with mock.patch.object(
            apply_module,
            "recovery_identity",
            return_value=(identity[0], identity[1] + 1),
        ):
            restored, errors = apply_module.restore_targets(
                self.workspace, recovery, identity, []
            )

        self.assertFalse(restored)
        self.assertIn("identity changed", errors[0])
        self.assertTrue(recovery.is_dir())

    def test_concurrent_source_change_restores_target_and_records_observed_digest(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        validation = self.validation(
            "from pathlib import Path; target=Path('tmp/debug.log'); "
            "source=Path('.gameplan/footprints/source.md'); "
            "source.write_text(source.read_text()+'\\n<!-- concurrent -->\\n') "
            "if not target.exists() else None; raise SystemExit(0)"
        )

        result, exit_code = self.apply([item_id], validation)

        source_text = self.footprint.read_text(encoding="utf-8")
        expected_digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "original\n")
        self.assertIn("<!-- concurrent -->", source_text)
        self.assertEqual(result["source_sha256_after"], expected_digest)
        self.assertIn("| `tmp/debug.log` | `remove` | `open` |", source_text)

    def test_obligation_update_failure_restores_target_and_leaves_source_open(self) -> None:
        self.write_file_fixture()
        item_id = self.candidate_id()
        original_write = apply_module.atomic_write_text

        def fail_obligation_update(path: Path, content: str) -> None:
            if path == self.footprint and "| `done` |" in content:
                raise OSError("induced source update failure")
            original_write(path, content)

        with mock.patch.object(apply_module, "atomic_write_text", side_effect=fail_obligation_update):
            result, exit_code = self.apply([item_id])

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "original\n")
        self.assertIn("| `tmp/debug.log` | `remove` | `open` |", self.footprint.read_text())
        self.assertEqual(result["obligations_updated"], 0)


if __name__ == "__main__":
    unittest.main()
