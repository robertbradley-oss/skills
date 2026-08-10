from __future__ import annotations

import argparse
import json
import os
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


class IgnoredGeneratedFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.external_temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.external = Path(self.external_temporary.name)
        self.created_links: list[Path] = []
        self.git("init", "-q")
        self.git("config", "user.email", "clean-up@example.invalid")
        self.git("config", "user.name", "Clean Up Tests")
        (self.workspace / ".gitignore").write_text(
            "**/bin/\n**/obj/\n.next/\nnode_modules/\nnext-env.d.ts\nartifacts/\nscratch-cache/\n",
            encoding="utf-8",
        )
        project = self.workspace / "src" / "App" / "App.csproj"
        project.parent.mkdir(parents=True)
        project.write_text("<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8")
        (self.workspace / "README.md").write_text(
            "The artifacts/build-manifest.json file is a retained reproducibility deliverable.\n",
            encoding="utf-8",
        )
        self.commit_all()

    def tearDown(self) -> None:
        for link in reversed(self.created_links):
            if os.path.lexists(link):
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)
        self.temporary.cleanup()
        self.external_temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=self.workspace, check=True,
            capture_output=True, text=True,
        )

    def commit_all(self, message: str = "fixture") -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def create_project(self, name: str) -> Path:
        project = self.workspace / "src" / name / f"{name}.csproj"
        project.parent.mkdir(parents=True, exist_ok=True)
        project.write_text("<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8")
        self.git("add", project.relative_to(self.workspace).as_posix())
        self.git("commit", "-qm", f"add {name} project")
        return project

    def create_output(self, relative: str, content: bytes = b"generated") -> Path:
        output = self.workspace.joinpath(*relative.split("/"))
        output.mkdir(parents=True, exist_ok=True)
        (output / "generated.bin").write_bytes(content)
        return output

    def create_node_project(self, nextjs: bool = True, lockfile: bool = True) -> None:
        dependencies = ', "dependencies": {"next": "15.0.0"}' if nextjs else ""
        (self.workspace / "package.json").write_text(
            '{"name": "fixture", "private": true' + dependencies + "}\n",
            encoding="utf-8",
        )
        paths = ["package.json"]
        if lockfile:
            (self.workspace / "package-lock.json").write_text(
                '{"name":"fixture","lockfileVersion":3,"packages":{"node_modules/next":{}}}\n',
                encoding="utf-8",
            )
            paths.append("package-lock.json")
        self.git("add", *paths)
        self.git("commit", "-qm", "add node project")

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

    def inspect(self, paths: list[str]) -> dict:
        return inspect_module.inspect(self.workspace, paths, None)

    def validation(self, code: str = "raise SystemExit(0)") -> str:
        return json.dumps([sys.executable, "-B", "-c", code])

    def apply(
        self, paths: list[str], approved: list[str], validation: str | None = None,
        report: str | None = None,
    ) -> tuple[dict, int]:
        return apply_module.apply_cleanup(argparse.Namespace(
            workspace=str(self.workspace), path=paths, git_base=None,
            approve=approved, validate_command=[validation or self.validation()],
            validation_timeout=30, report=report,
        ))


class IgnoredGeneratedInspectTests(IgnoredGeneratedFixture):
    def test_ignored_dotnet_bin_and_obj_are_typed_candidates(self) -> None:
        self.create_output("src/App/bin")
        self.create_output("src/App/obj")

        result = self.inspect(["src/App/bin", "src/App/obj"])

        self.assertEqual(len(result["provisional_authorization_set"]), 2)
        for item in result["items"]:
            self.assertEqual(item["classification"], "candidate")
            self.assertEqual(item["candidate_kind"], "ignored-generated")
            self.assertTrue(item["evidence"]["ignored"]["root_ignored"])
            self.assertTrue(item["evidence"]["ignored"]["complete_tree_ignored"])
            self.assertEqual(
                item["evidence"]["generated_context"]["kind"],
                "dotnet-conventional-output",
            )
            self.assertEqual(
                item["evidence"]["generated_context"]["tracked_projects"],
                ["src/App/App.csproj"],
            )

    def test_retained_artifacts_and_arbitrary_ignored_root_stay_review_only(self) -> None:
        artifacts = self.workspace / "artifacts"
        artifacts.mkdir()
        (artifacts / "build-manifest.json").write_text("{}\n", encoding="utf-8")
        arbitrary = self.workspace / "scratch-cache"
        arbitrary.mkdir()
        (arbitrary / "entry.bin").write_bytes(b"cache")

        result = self.inspect(["artifacts", "scratch-cache"])

        for item in result["items"]:
            self.assertEqual(item["classification"], "review")
            self.assertIsNone(item["candidate_kind"])
            self.assertIn("Ignored status alone", item["reason"])
        self.assertEqual(result["provisional_authorization_set"], [])

    def test_ignored_node_and_next_outputs_are_typed_candidates_with_lockfile_proof(self) -> None:
        self.create_node_project()
        (self.workspace / "tsconfig.json").write_text(
            '{"include":["next-env.d.ts",".next/types/**/*.ts"],"exclude":["node_modules"]}\n',
            encoding="utf-8",
        )
        (self.workspace / "eslint.config.mjs").write_text(
            'export default [{ ignores: [".next/**", "next-env.d.ts"] }];\n',
            encoding="utf-8",
        )
        self.git("add", "tsconfig.json", "eslint.config.mjs")
        self.git("commit", "-qm", "add next configuration")
        self.create_output("node_modules")
        self.create_output(".next")
        (self.workspace / "next-env.d.ts").write_text(
            '/// <reference types="next" />\n', encoding="utf-8",
        )

        result = self.inspect(["node_modules", ".next", "next-env.d.ts"])
        decisions = {item["path"]: item for item in result["items"]}

        self.assertEqual(len(result["provisional_authorization_set"]), 3)
        for path, item in decisions.items():
            self.assertEqual(item["classification"], "candidate", path)
            self.assertEqual(item["candidate_kind"], "ignored-generated")
            context = item["evidence"]["generated_context"]
            self.assertEqual(context["tracked_package"]["path"], "package.json")
            self.assertEqual(
                [lockfile["path"] for lockfile in context["tracked_lockfiles"]],
                ["package-lock.json"],
            )
            self.assertGreater(
                item["evidence"]["references"]["generated_metadata_match_count"], 0,
            )
        self.assertEqual(
            decisions["node_modules"]["evidence"]["generated_context"]["kind"],
            "node-dependency-install",
        )
        self.assertEqual(
            decisions[".next"]["evidence"]["generated_context"]["kind"],
            "nextjs-generated-output",
        )

    def test_node_output_requires_tracked_package_and_lockfile_evidence(self) -> None:
        self.create_node_project(lockfile=False)
        self.create_output("node_modules")

        item = self.inspect(["node_modules"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["candidate_kind"])
        self.assertIsNone(item["evidence"]["generated_context"])

    def test_next_output_requires_a_tracked_next_dependency(self) -> None:
        self.create_node_project(nextjs=False)
        self.create_output(".next")

        item = self.inspect([".next"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["candidate_kind"])
        self.assertIsNone(item["evidence"]["generated_context"])

    def test_referenced_node_output_stays_review_only(self) -> None:
        self.create_node_project()
        self.create_output("node_modules")
        (self.workspace / "README.md").write_text(
            "Keep node_modules for the offline demo.\n", encoding="utf-8",
        )
        self.git("add", "README.md")
        self.git("commit", "-qm", "retain offline dependencies")

        item = self.inspect(["node_modules"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertGreater(item["evidence"]["references"]["match_count"], 0)

    def test_ignored_generated_root_with_tracked_modified_descendant_is_review(self) -> None:
        self.create_project("Mixed")
        output = self.create_output("src/Mixed/bin")
        tracked = output / "generated.bin"
        self.git("add", "-f", "src/Mixed/bin/generated.bin")
        self.git("commit", "-qm", "track retained binary")
        tracked.write_bytes(b"modified")

        item = self.inspect(["src/Mixed/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIn("tracked", item["reason"].lower())
        self.assertEqual(item["evidence"]["tracked_paths"], ["src/Mixed/bin/generated.bin"])

    def test_referenced_dotnet_output_stays_review_only(self) -> None:
        self.create_output("src/App/bin")
        (self.workspace / "retention.md").write_text(
            "Retain src/App/bin for the offline support bundle.\n", encoding="utf-8",
        )
        self.git("add", "retention.md")
        self.git("commit", "-qm", "document retained output")

        item = self.inspect(["src/App/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIn("references", item["reason"])
        self.assertGreater(item["evidence"]["references"]["match_count"], 0)

    def test_csproj_extension_without_project_xml_is_insufficient_context(self) -> None:
        fake = self.workspace / "src" / "Fake" / "Fake.csproj"
        fake.parent.mkdir(parents=True)
        fake.write_text("not a project\n", encoding="utf-8")
        self.git("add", "src/Fake/Fake.csproj")
        self.git("commit", "-qm", "add misleading project filename")
        self.create_output("src/Fake/bin")

        item = self.inspect(["src/Fake/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["evidence"]["generated_context"])

    def test_ignored_directory_link_and_escape_are_review_only(self) -> None:
        self.create_project("Linked")
        (self.external / "outside.bin").write_bytes(b"outside")
        link = self.workspace / "src" / "Linked" / "bin"
        self.create_directory_link(link, self.external)

        item = self.inspect(["src/Linked/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIn(item["current"]["type"], {"junction", "symlink"})
        self.assertEqual((self.external / "outside.bin").read_bytes(), b"outside")

    def test_special_descendant_evidence_is_review_only(self) -> None:
        output = self.workspace / "src" / "App" / "bin"
        output.mkdir(parents=True)
        current = inspect_module.fingerprint_path(self.workspace, output)
        current["entries"] = [{"path": "device", "type": "other"}]
        current["entry_count"] = 1

        with mock.patch.object(inspect_module, "fingerprint_path", return_value=current):
            item = self.inspect(["src/App/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIn("special", item["reason"])

    def test_changed_ignored_directory_invalidates_candidate_id(self) -> None:
        output = self.create_output("src/App/bin", b"first")
        first = self.inspect(["src/App/bin"])["items"][0]
        (output / "generated.bin").write_bytes(b"second")
        second = self.inspect(["src/App/bin"])["items"][0]

        self.assertNotEqual(first["id"], second["id"])
        result, exit_code = self.apply(["src/App/bin"], [first["id"]])
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue(output.is_dir())

    def test_unreferenced_empty_tmp_is_metadata_bound_candidate(self) -> None:
        (self.workspace / "tmp").mkdir()

        item = self.inspect(["tmp"])["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "empty-directory")
        self.assertEqual(item["current"]["entry_count"], 0)
        self.assertIsInstance(item["current"]["metadata"]["mtime_ns"], int)
        self.assertEqual(item["evidence"]["references"]["match_count"], 0)

    def test_extension_and_partial_name_hits_do_not_reference_empty_tmp(self) -> None:
        (self.workspace / "notes.md").write_text(
            "report.tmp attempt tmp-cache tmp_data tmp.json tmpfile\n",
            encoding="utf-8",
        )
        self.git("add", "notes.md")
        self.git("commit", "-qm", "document unrelated tmp tokens")
        (self.workspace / "tmp").mkdir()

        item = self.inspect(["tmp"])["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "empty-directory")
        self.assertEqual(item["evidence"]["references"]["match_semantics"], "path-token")
        self.assertEqual(item["evidence"]["references"]["match_count"], 0)

    def test_gameplan_references_are_not_read_or_used_by_inspect(self) -> None:
        (self.workspace / "GAMEPLAN.md").write_text(
            "Retain the top-level tmp directory.\n", encoding="utf-8",
        )
        (self.workspace / ".gameplan" / "footprints").mkdir(parents=True)
        (self.workspace / ".gameplan" / "footprints" / "current.md").write_text(
            "The tmp directory was retained.\n", encoding="utf-8",
        )
        self.git("add", "GAMEPLAN.md", ".gameplan/footprints/current.md")
        self.git("commit", "-qm", "add planning controls")
        (self.workspace / "tmp").mkdir()

        item = self.inspect(["tmp"])["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "empty-directory")
        self.assertEqual(item["evidence"]["references"]["match_count"], 0)

    def test_exact_and_descendant_path_hits_reference_empty_tmp(self) -> None:
        (self.workspace / "config.json").write_text(
            '{"requiredDirectory":"tmp","cachePath":"tmp\\\\session"}\n',
            encoding="utf-8",
        )
        self.git("add", "config.json")
        self.git("commit", "-qm", "declare tmp directory")
        (self.workspace / "tmp").mkdir()

        item = self.inspect(["tmp"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["candidate_kind"])
        self.assertGreater(item["evidence"]["references"]["match_count"], 0)

    def test_partial_repo_path_does_not_reference_generated_output(self) -> None:
        self.create_output("src/App/bin")
        (self.workspace / "notes.md").write_text(
            "old-src/App/bin-copy is an unrelated label.\n",
            encoding="utf-8",
        )
        self.git("add", "notes.md")
        self.git("commit", "-qm", "document unrelated output label")

        item = self.inspect(["src/App/bin"])["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "ignored-generated")
        self.assertEqual(item["evidence"]["references"]["match_count"], 0)

    def test_windows_style_repo_path_references_generated_output(self) -> None:
        self.create_output("src/App/bin")
        (self.workspace / "retention.md").write_text(
            "Retain src\\App\\bin\\generated.bin for offline support.\n",
            encoding="utf-8",
        )
        self.git("add", "retention.md")
        self.git("commit", "-qm", "document windows output path")

        item = self.inspect(["src/App/bin"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertGreater(item["evidence"]["references"]["match_count"], 0)

    def test_directory_with_only_empty_descendants_is_not_an_empty_candidate(self) -> None:
        (self.workspace / "tmp" / "nested").mkdir(parents=True)

        item = self.inspect(["tmp"])["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["candidate_kind"])
        self.assertIn("empty descendants", item["reason"])

    def test_referenced_or_ambiguous_empty_directory_stays_review_only(self) -> None:
        (self.workspace / "config.json").write_text(
            '{"requiredDirectory":"runtime-empty"}\n', encoding="utf-8",
        )
        self.git("add", "config.json")
        self.git("commit", "-qm", "declare runtime directory")
        (self.workspace / "runtime-empty").mkdir()
        (self.workspace / "fixtures").mkdir()

        result = self.inspect(["runtime-empty", "fixtures"])
        decisions = {item["path"]: item for item in result["items"]}

        self.assertEqual(decisions["runtime-empty"]["classification"], "review")
        self.assertGreater(decisions["runtime-empty"]["evidence"]["references"]["match_count"], 0)
        self.assertEqual(decisions["fixtures"]["classification"], "review")
        self.assertIn("retained", decisions["fixtures"]["reason"])

    def test_invalid_and_overlapping_scopes_never_authorize(self) -> None:
        (self.workspace / "tmp").mkdir()
        (self.workspace / "tmp" / "child").mkdir()
        absolute = str((self.workspace / "tmp").resolve())

        result = self.inspect([
            ".", "../outside", "tmp/*", absolute, "tmp", "tmp/child",
        ])
        codes = {item["code"] for item in result["refusals"]}

        self.assertIn("scope-path-invalid", codes)
        self.assertIn("scope-path-overlap", codes)
        self.assertFalse(result["apply_supported"])
        self.assertEqual(result["provisional_authorization_set"], [])


class IgnoredGeneratedApplyTests(IgnoredGeneratedFixture):
    def test_exact_ignored_candidates_apply_through_quarantine(self) -> None:
        bin_path = self.create_output("src/App/bin")
        obj_path = self.create_output("src/App/obj")
        paths = ["src/App/bin", "src/App/obj"]
        inspection = self.inspect(paths)

        result, exit_code = self.apply(paths, inspection["provisional_authorization_set"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(bin_path.exists())
        self.assertFalse(obj_path.exists())
        self.assertEqual(result["recovery"]["status"], "discarded")

    def test_node_and_next_candidates_apply_through_the_same_guarded_lane(self) -> None:
        self.create_node_project()
        node_modules = self.create_output("node_modules")
        next_output = self.create_output(".next")
        next_env = self.workspace / "next-env.d.ts"
        next_env.write_text('/// <reference types="next" />\n', encoding="utf-8")
        paths = ["node_modules", ".next", "next-env.d.ts"]
        inspection = self.inspect(paths)

        result, exit_code = self.apply(paths, inspection["provisional_authorization_set"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(node_modules.exists())
        self.assertFalse(next_output.exists())
        self.assertFalse(next_env.exists())
        self.assertEqual(result["recovery"]["status"], "discarded")

    def test_changed_node_lockfile_invalidates_approved_candidate(self) -> None:
        self.create_node_project()
        node_modules = self.create_output("node_modules")
        item = self.inspect(["node_modules"])["items"][0]
        (self.workspace / "package-lock.json").write_text(
            '{"name":"fixture","lockfileVersion":3,"changed":true}\n',
            encoding="utf-8",
        )

        result, exit_code = self.apply(["node_modules"], [item["id"]])

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue(node_modules.is_dir())
        self.assertIn("approval-not-current", {refusal["code"] for refusal in result["refusals"]})

    def test_empty_directory_can_apply_and_nonempty_change_refuses(self) -> None:
        empty = self.workspace / "tmp"
        empty.mkdir()
        item = self.inspect(["tmp"])["items"][0]
        (empty / "late.txt").write_text("late\n", encoding="utf-8")

        refused, refused_code = self.apply(["tmp"], [item["id"]])
        self.assertEqual(refused_code, 2)
        self.assertEqual(refused["status"], "refused")
        self.assertTrue((empty / "late.txt").is_file())

        (empty / "late.txt").unlink()
        refreshed = self.inspect(["tmp"])["items"][0]
        completed, completed_code = self.apply(["tmp"], [refreshed["id"]])
        self.assertEqual(completed_code, 0)
        self.assertEqual(completed["status"], "completed")
        self.assertFalse(empty.exists())

    def test_validation_failure_restores_ignored_output_exactly(self) -> None:
        output = self.create_output("src/App/bin", b"restore-me")
        item = self.inspect(["src/App/bin"])["items"][0]
        validation = self.validation(
            "from pathlib import Path; "
            "raise SystemExit(0 if Path('src/App/bin').is_dir() else 1)"
        )

        result, exit_code = self.apply(["src/App/bin"], [item["id"]], validation)

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((output / "generated.bin").read_bytes(), b"restore-me")

    def test_report_failure_restores_ignored_output(self) -> None:
        output = self.create_output("src/App/obj", b"restore-report")
        item = self.inspect(["src/App/obj"])["items"][0]

        with mock.patch.object(apply_module, "try_write_report", return_value=False):
            result, exit_code = self.apply(
                ["src/App/obj"], [item["id"]], report=".clean-up/reports/run.json",
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "restored")
        self.assertEqual((output / "generated.bin").read_bytes(), b"restore-report")

    def test_manual_and_cross_inspection_ids_are_refused(self) -> None:
        self.create_output("src/App/bin")
        obj_path = self.create_output("src/App/obj")
        arbitrary = self.workspace / "scratch-cache"
        arbitrary.mkdir()
        (arbitrary / "entry.bin").write_bytes(b"cache")
        bin_id = self.inspect(["src/App/bin"])["items"][0]["id"]

        cross, cross_code = self.apply(["src/App/obj"], [bin_id])
        manual, manual_code = self.apply(["scratch-cache"], ["PC-000000000000"])

        self.assertEqual(cross_code, 2)
        self.assertEqual(manual_code, 2)
        self.assertIn("approval-not-current", {item["code"] for item in cross["refusals"]})
        self.assertIn("approval-not-current", {item["code"] for item in manual["refusals"]})
        self.assertTrue(obj_path.is_dir())
        self.assertTrue(arbitrary.is_dir())


if __name__ == "__main__":
    unittest.main()
