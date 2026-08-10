from __future__ import annotations

import argparse
import hashlib
import json
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
import release_retention as retention_module


class ReleaseRetentionFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "clean-up@example.invalid")
        self.git("config", "user.name", "Clean Up Tests")
        (self.workspace / ".gitignore").write_text("release/\n", encoding="utf-8")
        (self.workspace / "README.md").write_text("Release fixtures.\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=self.workspace, check=True,
            capture_output=True, text=True,
        )

    def create_release(self, version: str = "1.0.0") -> Path:
        release = self.workspace / "release" / f"setup-{version}"
        release.mkdir(parents=True)
        manifest = {
            "Schema": "fixture-release/v1",
            "Version": version,
            "AutomaticUpdates": {
                "Feed": "https://github.com/example/releases/releases/latest/download/release-manifest.json",
            },
        }
        (release / "release-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
        )
        (release / f"Fixture-{version}.bin").write_bytes(f"release-{version}".encode())
        (release / "SHA256SUMS.txt").write_text("fixture checksums\n", encoding="utf-8")
        return release

    def remove_product_feed(self, release: Path) -> None:
        manifest_path = release / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("AutomaticUpdates", None)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def release_metadata(
        self, release: Path, version: str = "1.0.0", newer: int = 2,
        mutate_asset: str | None = None, missing_digest: str | None = None,
        missing_url: str | None = None,
        draft: bool = False, prerelease: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        assets = []
        for path in sorted(release.iterdir()):
            digest = self.digest(path)
            if path.name == mutate_asset:
                digest = "0" * 64
            asset = {
                "name": path.name,
                "size": path.stat().st_size,
                "digest": None if path.name == missing_digest else f"sha256:{digest}",
                "browser_download_url": None if path.name == missing_url else f"https://github.com/example/releases/releases/download/v{version}/{path.name}",
            }
            assets.append(asset)
        releases = []
        for index in range(newer, 0, -1):
            releases.append({
                "tag_name": f"v9.0.{index}", "name": f"Newer {index}",
                "draft": False, "prerelease": False,
                "published_at": f"2026-02-{index + 1:02d}T00:00:00Z", "assets": [],
            })
        releases.append({
            "tag_name": f"v{version}", "name": f"Fixture {version}",
            "html_url": f"https://github.com/example/releases/releases/tag/v{version}",
            "draft": draft, "prerelease": prerelease,
            "published_at": "2026-01-01T00:00:00Z", "assets": assets,
        })
        return subprocess.CompletedProcess(
            ["gh", "api"], 0, stdout=json.dumps(releases).encode(), stderr=b"",
        )

    def inspect(self, path: str = "release/setup-1.0.0") -> dict:
        return inspect_module.inspect(self.workspace, [path], None)

    @staticmethod
    def validation() -> str:
        return json.dumps([sys.executable, "-B", "-c", "raise SystemExit(0)"])

    def apply(self, path: str, item_id: str) -> tuple[dict, int]:
        return apply_module.apply_cleanup(argparse.Namespace(
            workspace=str(self.workspace), path=[path], git_base=None,
            approve=[item_id], validate_command=[self.validation()],
            validation_timeout=30, report=None,
        ))


class ReleaseRetentionInspectTests(ReleaseRetentionFixture):
    def test_exact_remote_backing_and_two_newer_releases_create_candidate(self) -> None:
        release = self.create_release()
        response = self.release_metadata(release)

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect()["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "remote-backed-release")
        evidence = item["evidence"]["release_retention"]
        self.assertTrue(evidence["eligible"])
        self.assertEqual(evidence["repository"], "example/releases")
        self.assertEqual(evidence["newer_stable_count"], 2)
        self.assertEqual(len(evidence["asset_matches"]), 3)
        self.assertEqual(evidence["unmatched_files"], [])
        self.assertEqual(evidence["repository_source"], "manifest-feed")

    def test_two_newer_sibling_feeds_can_establish_legacy_release_repository(self) -> None:
        release = self.create_release("1.0.0")
        self.remove_product_feed(release)
        self.create_release("1.1.0")
        self.create_release("1.2.0")
        response = self.release_metadata(release, "1.0.0")

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect()["items"][0]

        self.assertEqual(item["classification"], "candidate")
        evidence = item["evidence"]["release_retention"]
        self.assertEqual(evidence["repository_source"], "sibling-manifest-consensus")
        self.assertEqual(len(evidence["repository_sources"]), 2)
        self.assertEqual({source["repository"] for source in evidence["repository_sources"]}, {"example/releases"})

    def test_single_or_conflicting_sibling_feed_cannot_establish_repository(self) -> None:
        for case in ("single", "conflicting"):
            with self.subTest(case=case):
                release = self.create_release(f"1.0.{0 if case == 'single' else 1}")
                self.remove_product_feed(release)
                self.create_release(f"1.1.{0 if case == 'single' else 1}")
                if case == "conflicting":
                    sibling = self.create_release("1.2.1")
                    manifest_path = sibling / "release-manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["AutomaticUpdates"]["Feed"] = (
                        "https://github.com/other/releases/releases/latest/download/release-manifest.json"
                    )
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                path = release.relative_to(self.workspace).as_posix()
                with mock.patch.object(retention_module, "run_gh") as run_gh:
                    item = self.inspect(path)["items"][0]
                self.assertEqual(item["classification"], "review")
                run_gh.assert_not_called()

    def test_fully_untracked_remote_backed_release_creates_typed_candidate(self) -> None:
        (self.workspace / ".gitignore").write_text("", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "do not ignore releases")
        release = self.create_release()
        response = self.release_metadata(release)

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect()["items"][0]

        self.assertEqual(item["classification"], "candidate")
        self.assertEqual(item["candidate_kind"], "remote-backed-release")
        self.assertEqual(item["evidence"]["release_retention"]["local_git_state"], "untracked")
        self.assertTrue(item["evidence"]["worktree"])

    def test_current_and_previous_stable_releases_remain_review(self) -> None:
        for newer in (0, 1):
            with self.subTest(newer=newer):
                release = self.create_release(version=f"1.0.{newer}")
                response = self.release_metadata(release, version=f"1.0.{newer}", newer=newer)
                path = f"release/setup-1.0.{newer}"
                with mock.patch.object(retention_module, "run_gh", return_value=response):
                    item = self.inspect(path)["items"][0]
                self.assertEqual(item["classification"], "review")
                self.assertIn("two newest", item["reason"])

    def test_mismatch_missing_digest_and_extra_file_remain_review(self) -> None:
        cases = ("mismatch", "missing-digest", "missing-url", "extra-file")
        for case in cases:
            with self.subTest(case=case):
                release = self.create_release(version={
                    "mismatch": "1.0.1", "missing-digest": "1.0.2",
                    "missing-url": "1.0.3", "extra-file": "1.0.4",
                }[case])
                response = self.release_metadata(
                    release, version=release.name.removeprefix("setup-"),
                    mutate_asset=next(path.name for path in release.iterdir() if path.suffix == ".bin") if case == "mismatch" else None,
                    missing_digest="SHA256SUMS.txt" if case == "missing-digest" else None,
                    missing_url="SHA256SUMS.txt" if case == "missing-url" else None,
                )
                if case == "extra-file":
                    (release / "local-only.txt").write_text("not remote\n", encoding="utf-8")
                path = release.relative_to(self.workspace).as_posix()
                with mock.patch.object(retention_module, "run_gh", return_value=response):
                    item = self.inspect(path)["items"][0]
                self.assertEqual(item["classification"], "review")
                self.assertIsNone(item["candidate_kind"])
                self.assertTrue(item["evidence"]["release_retention"]["unmatched_files"])

    def test_draft_prerelease_and_api_failure_remain_review(self) -> None:
        release = self.create_release()
        responses = (
            self.release_metadata(release, draft=True),
            self.release_metadata(release, prerelease=True),
            subprocess.CompletedProcess(["gh", "api"], 1, stdout=b"", stderr=b"offline"),
        )
        for response in responses:
            with self.subTest(returncode=response.returncode, stderr=response.stderr):
                with mock.patch.object(retention_module, "run_gh", return_value=response):
                    item = self.inspect()["items"][0]
                self.assertEqual(item["classification"], "review")
                self.assertIsNone(item["candidate_kind"])

    def test_toolchain_release_url_without_product_feed_does_not_query_github(self) -> None:
        release = self.create_release()
        manifest_path = release / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("AutomaticUpdates")
        manifest["Toolchain"] = {
            "Source": "https://github.com/vendor/compiler/releases/download/v1/compiler.exe",
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch.object(retention_module, "run_gh") as run_gh:
            item = self.inspect()["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIn("Fewer than two newer sibling manifests", item["reason"])
        run_gh.assert_not_called()

    def test_nested_and_multiple_repository_evidence_remain_review(self) -> None:
        release = self.create_release()
        (release / "nested").mkdir()
        with mock.patch.object(retention_module, "run_gh") as run_gh:
            item = self.inspect()["items"][0]
        self.assertEqual(item["classification"], "review")
        run_gh.assert_not_called()

        nested = release / "nested"
        nested.rmdir()
        manifest_path = release / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["BackupFeed"] = "https://github.com/other/releases/releases/latest"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with mock.patch.object(retention_module, "run_gh") as run_gh:
            item = self.inspect()["items"][0]
        self.assertEqual(item["classification"], "review")
        run_gh.assert_not_called()

    def test_non_versioned_or_unrelated_directory_remains_review(self) -> None:
        release = self.create_release()
        unrelated = self.workspace / "cache" / "current"
        unrelated.parent.mkdir()
        release.rename(unrelated)
        (self.workspace / ".gitignore").write_text("release/\ncache/\n", encoding="utf-8")

        with mock.patch.object(retention_module, "run_gh") as run_gh:
            item = self.inspect("cache/current")["items"][0]

        self.assertEqual(item["classification"], "review")
        self.assertIsNone(item["candidate_kind"])
        run_gh.assert_not_called()


class ReleaseRetentionApplyTests(ReleaseRetentionFixture):
    def test_approved_legacy_release_with_sibling_consensus_applies(self) -> None:
        release = self.create_release("1.0.0")
        self.remove_product_feed(release)
        self.create_release("1.1.0")
        self.create_release("1.2.0")
        response = self.release_metadata(release, "1.0.0")
        path = release.relative_to(self.workspace).as_posix()

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect(path)["items"][0]
            result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(release.exists())

    def test_changed_sibling_consensus_invalidates_approval_before_mutation(self) -> None:
        release = self.create_release("1.0.0")
        self.remove_product_feed(release)
        self.create_release("1.1.0")
        sibling = self.create_release("1.2.0")
        response = self.release_metadata(release, "1.0.0")
        path = release.relative_to(self.workspace).as_posix()

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect(path)["items"][0]
        self.remove_product_feed(sibling)
        with mock.patch.object(retention_module, "run_gh", return_value=response):
            result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue(release.is_dir())

    def test_approved_remote_backed_release_applies_through_quarantine(self) -> None:
        release = self.create_release()
        response = self.release_metadata(release)
        path = release.relative_to(self.workspace).as_posix()

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect(path)["items"][0]
            result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(release.exists())
        self.assertEqual(self.git("status", "--short").stdout, "")

    def test_approved_fully_untracked_release_applies_without_git_change(self) -> None:
        (self.workspace / ".gitignore").write_text("", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "do not ignore releases")
        release = self.create_release()
        response = self.release_metadata(release)
        path = release.relative_to(self.workspace).as_posix()

        with mock.patch.object(retention_module, "run_gh", return_value=response):
            item = self.inspect(path)["items"][0]
            result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(release.exists())
        self.assertEqual(self.git("status", "--short").stdout, "")

    def test_changed_remote_evidence_invalidates_approval_before_mutation(self) -> None:
        release = self.create_release()
        good = self.release_metadata(release)
        bad = self.release_metadata(
            release, mutate_asset=next(path.name for path in release.iterdir() if path.suffix == ".bin"),
        )
        path = release.relative_to(self.workspace).as_posix()

        with mock.patch.object(retention_module, "run_gh", return_value=good):
            item = self.inspect(path)["items"][0]
        with mock.patch.object(retention_module, "run_gh", return_value=bad):
            result, exit_code = self.apply(path, item["id"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(result["status"], "refused")
        self.assertTrue(release.is_dir())
