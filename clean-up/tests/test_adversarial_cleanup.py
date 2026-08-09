from __future__ import annotations

import argparse
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
SCRIPTS = ROOT / "clean-up" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_cleanup as apply_module
import inspect_repository as inspect_module


class AdversarialFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.external_temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.external = Path(self.external_temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.workspace, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.workspace, check=True)
        (self.workspace / "tmp").mkdir()
        self.target = self.workspace / "tmp" / "debug.log"
        self.target.write_text("original\n", encoding="utf-8")
        self.retained_recovery: set[Path] = set()
        self.created_links: list[Path] = []

    def tearDown(self) -> None:
        for link in reversed(self.created_links):
            if os.path.lexists(link):
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)
        for recovery in self.retained_recovery:
            if recovery.exists():
                resolved = recovery.resolve()
                self.assertEqual(resolved.parent, self.workspace.parent.resolve())
                self.assertTrue(resolved.name.startswith(".clean-up-"))
                shutil.rmtree(resolved)
        self.temporary.cleanup()
        self.external_temporary.cleanup()

    def create_directory_link(self, link: Path, target: Path) -> None:
        if os.name != "nt":
            os.symlink(target, link, target_is_directory=True)
        else:
            completed = subprocess.run([
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                "& { param([string]$Link,[string]$Target) $ErrorActionPreference='Stop'; "
                "New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null }",
                str(link), str(target),
            ], capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                self.skipTest(f"Directory link creation unavailable: {completed.stderr.strip()}")
        self.created_links.append(link)

    def inspect(self, paths: list[str] | None = None) -> dict:
        return inspect_module.inspect(self.workspace, paths or ["tmp/debug.log"], None)

    def candidate_id(self) -> str:
        return self.inspect()["provisional_authorization_set"][0]

    def validation(self, code: str = "raise SystemExit(0)") -> str:
        return json.dumps([sys.executable, "-B", "-c", code])

    def apply(self, item_id: str, validation: str | None = None, report: str | None = None) -> tuple[dict, int]:
        return apply_module.apply_cleanup(argparse.Namespace(
            workspace=str(self.workspace), path=["tmp/debug.log"], git_base=None,
            approve=[item_id], validate_command=[validation or self.validation()],
            validation_timeout=30, report=report,
        ))

    def retain(self, result: dict) -> Path:
        recovery = Path(result["recovery"]["location"])
        self.assertTrue(recovery.is_dir())
        self.retained_recovery.add(recovery)
        return recovery


class AdversarialInspectTests(AdversarialFixture):
    def test_traversal_duplicate_and_overlap_refuse_authorization(self) -> None:
        result = self.inspect(["../outside.txt", "tmp", "tmp/debug.log", "tmp/debug.log"])
        codes = {item["code"] for item in result["refusals"]}
        self.assertIn("scope-path-invalid", codes)
        self.assertIn("scope-path-duplicate", codes)
        self.assertIn("scope-path-overlap", codes)
        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertFalse(result["apply_supported"])

    def test_link_ancestor_escape_is_review_only(self) -> None:
        outside = self.external / "outside.log"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.workspace / "tmp" / "escape"
        self.create_directory_link(link, self.external)
        result = self.inspect(["tmp/escape/outside.log"])
        item = result["items"][0]
        self.assertEqual(item["classification"], "review")
        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertEqual(outside.read_text(), "outside\n")

    def test_directory_containing_external_link_is_review_only(self) -> None:
        bundle = self.workspace / "bundle"
        bundle.mkdir()
        (bundle / "file.txt").write_text("new\n", encoding="utf-8")
        self.create_directory_link(bundle / "escape", self.external)
        result = self.inspect(["bundle"])
        self.assertEqual(result["items"][0]["classification"], "review")
        self.assertIn("link", result["items"][0]["reason"])

    def test_simulated_junction_target_is_never_candidate(self) -> None:
        real = inspect_module.is_junction

        def junction(path: Path) -> bool:
            return path.resolve() == self.target.resolve() or real(path)

        with mock.patch.object(inspect_module, "is_junction", side_effect=junction):
            result = self.inspect()
        self.assertEqual(result["items"][0]["classification"], "review")
        self.assertEqual(result["items"][0]["current"]["type"], "junction")


class AdversarialApplyTests(AdversarialFixture):
    def test_recovery_creation_failure_preserves_target(self) -> None:
        with mock.patch.object(apply_module, "create_recovery_root", side_effect=OSError("induced")):
            result, exit_code = self.apply(self.candidate_id())
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(self.target.read_text(), "original\n")
        self.assertFalse(result["cleanup_mutations_performed"])

    def test_requested_report_failure_restores_target(self) -> None:
        with mock.patch.object(apply_module, "atomic_write_json", side_effect=OSError("induced")):
            result, exit_code = self.apply(
                self.candidate_id(), report=".clean-up/reports/run.json"
            )
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual(self.target.read_text(), "original\n")

    def test_concurrent_target_reappearance_requires_manual_recovery(self) -> None:
        validation = self.validation(
            "from pathlib import Path; p=Path('tmp/debug.log'); "
            "p.write_text('concurrent\\n') if not p.exists() else None; raise SystemExit(0)"
        )
        result, exit_code = self.apply(self.candidate_id(), validation)
        recovery = self.retain(result)
        self.assertEqual(exit_code, 3)
        self.assertEqual(result["status"], "recovery-required")
        self.assertEqual(self.target.read_text(), "concurrent\n")
        self.assertEqual((recovery / "item-0001").read_text(), "original\n")

    def test_recovery_identity_change_blocks_restoration(self) -> None:
        recovery, identity = apply_module.create_recovery_root(self.workspace, "identity-test")
        self.retained_recovery.add(recovery)
        with mock.patch.object(apply_module, "recovery_identity", return_value=(identity[0], identity[1] + 1)):
            restored, errors = apply_module.restore_targets(self.workspace, recovery, identity, [])
        self.assertFalse(restored)
        self.assertIn("identity changed", errors[0])

    def test_post_validation_head_change_restores_target(self) -> None:
        validation = self.validation(
            "from pathlib import Path; import subprocess; "
            "subprocess.run(['git','commit','--allow-empty','-qm','concurrent'],check=True) "
            "if not Path('tmp/debug.log').exists() else None"
        )
        result, exit_code = self.apply(self.candidate_id(), validation)
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual(self.target.read_text(), "original\n")
        self.assertIn("explicit Git base changed", result["refusals"][-1]["message"])

    def test_discard_failure_retains_same_filesystem_recovery(self) -> None:
        with mock.patch.object(apply_module, "discard_recovery", return_value=(False, "induced")):
            result, exit_code = self.apply(self.candidate_id())
        recovery = self.retain(result)
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed-recovery-retained")
        self.assertEqual(os.stat(self.workspace).st_dev, os.stat(recovery).st_dev)
        self.assertTrue((recovery / "recovery-map.json").is_file())


if __name__ == "__main__":
    unittest.main()
