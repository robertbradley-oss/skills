#!/usr/bin/env python3
"""Read-only proof for locally cached GitHub release asset sets."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


KEEP_NEWEST_STABLE = 2
MAX_MANIFEST_BYTES = 1024 * 1024
GITHUB_RELEASE_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/releases(?:/|$)",
    flags=re.IGNORECASE,
)
SHA256_DIGEST = re.compile(r"^sha256:([A-Fa-f0-9]{64})$")
VERSION = re.compile(r"^v?(\d+(?:\.\d+){1,3})$", flags=re.IGNORECASE)
VERSION_IN_NAME = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_gh(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["gh", *arguments], stdin=subprocess.DEVNULL, capture_output=True,
        check=False, timeout=30,
    )


def normalized_version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = VERSION.fullmatch(value.strip())
    return match.group(1) if match else None


def manifest_feed_strings(value: Any, remaining: list[int]) -> list[str]:
    if remaining[0] <= 0:
        return []
    remaining[0] -= 1
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if isinstance(item, str) and "feed" in str(key).lower():
                values.append(item)
            values.extend(manifest_feed_strings(item, remaining))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(manifest_feed_strings(item, remaining))
        return values
    return []


def release_repository(manifest: dict[str, Any]) -> tuple[str | None, str | None]:
    repositories: set[str] = set()
    remaining = [10_000]
    feed_values = manifest_feed_strings(manifest, remaining)
    if remaining[0] <= 0:
        return None, "Release manifest exceeds the bounded evidence traversal limit"
    if not feed_values:
        return None, "Release manifest has no explicit GitHub Releases feed URL"
    for value in feed_values:
        for match in GITHUB_RELEASE_URL.finditer(value):
            owner, repository = match.group(1), match.group(2).removesuffix(".git")
            repositories.add(f"{owner}/{repository}")
    if remaining[0] <= 0:
        return None, "Release manifest exceeds the bounded evidence traversal limit"
    if not repositories:
        return None, "Release manifest has no GitHub Releases URL"
    if len(repositories) != 1:
        return None, "Release manifest names multiple GitHub release repositories"
    return next(iter(repositories)), None


def top_level_version(manifest: dict[str, Any]) -> str | None:
    versions = {
        value for key, raw in manifest.items()
        if str(key).lower() == "version"
        for value in [normalized_version(raw)] if value is not None
    }
    return next(iter(versions)) if len(versions) == 1 else None


def review(reason: str, **evidence: Any) -> dict[str, Any]:
    return {
        "kind": "github-release-asset-set", "eligible": False,
        "reason": reason, "keep_newest_stable": KEEP_NEWEST_STABLE, **evidence,
    }


def analyze_release_directory(path: str, absolute: Path) -> dict[str, Any] | None:
    if not absolute.is_dir():
        return None
    try:
        children = sorted(absolute.iterdir(), key=lambda item: item.name.lower())
    except OSError as exc:
        return review(f"Release directory could not be listed: {exc}")
    manifests = [item for item in children if item.name.lower() == "release-manifest.json"]
    if not manifests:
        return None
    if len(manifests) != 1 or not manifests[0].is_file() or manifests[0].is_symlink():
        return review("Release directory does not contain one plain release-manifest.json file")
    if any(not item.is_file() or item.is_symlink() for item in children):
        return review("Release directory contains nested, linked, or special entries")
    if len(children) < 2:
        return review("Release directory does not contain a complete asset set")

    manifest_path = manifests[0]
    try:
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            return review("Release manifest exceeds the bounded one MiB evidence limit")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return review(f"Release manifest could not be read as JSON: {exc}")
    if not isinstance(manifest, dict):
        return review("Release manifest JSON root is not an object")

    version = top_level_version(manifest)
    if version is None:
        return review("Release manifest has no single top-level semantic Version")
    path_parts = [part.lower() for part in Path(path).parts]
    if not any(part in {"artifacts", "release", "releases"} for part in path_parts[:-1]):
        return review("Release asset set is not inside an artifacts or release container", version=version)
    if version not in VERSION_IN_NAME.findall(path_parts[-1]):
        return review("Release directory name does not contain the manifest Version", version=version)
    repository, repository_error = release_repository(manifest)
    if repository_error or repository is None:
        return review(repository_error or "Release repository could not be resolved", version=version)

    try:
        completed = run_gh(["api", f"repos/{repository}/releases?per_page=100"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return review(
            f"GitHub release metadata could not be queried: {exc}",
            version=version, repository=repository,
        )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()[:500]
        return review(
            "GitHub release metadata query failed" + (f": {detail}" if detail else ""),
            version=version, repository=repository,
        )
    try:
        releases = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return review(
            f"GitHub release metadata was invalid JSON: {exc}",
            version=version, repository=repository,
        )
    if not isinstance(releases, list):
        return review("GitHub release metadata root is not a list", version=version, repository=repository)

    stable = [
        item for item in releases
        if isinstance(item, dict)
        and item.get("draft") is False
        and item.get("prerelease") is False
        and isinstance(item.get("published_at"), str)
    ]
    matching = [item for item in stable if normalized_version(item.get("tag_name")) == version]
    if len(matching) != 1:
        return review(
            "No single published stable GitHub release matches the manifest Version",
            version=version, repository=repository,
        )
    release = matching[0]
    published_at = release["published_at"]
    newer = sorted(
        [item for item in stable if item["published_at"] > published_at],
        key=lambda item: item["published_at"], reverse=True,
    )

    remote_by_name: dict[str, dict[str, Any]] = {}
    duplicate_names: set[str] = set()
    release_assets = release.get("assets", [])
    if not isinstance(release_assets, list):
        return review(
            "Published release assets are not a list",
            version=version, repository=repository, release_tag=release.get("tag_name"),
        )
    for asset in release_assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
            continue
        name = asset["name"]
        if name in remote_by_name:
            duplicate_names.add(name)
        remote_by_name[name] = asset
    if duplicate_names:
        return review(
            "Published release contains duplicate asset names",
            version=version, repository=repository, release_tag=release.get("tag_name"),
        )

    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for local in children:
        try:
            size = local.stat().st_size
            digest = sha256_file(local)
        except OSError as exc:
            return review(
                f"Local release asset could not be fingerprinted: {exc}",
                version=version, repository=repository, release_tag=release.get("tag_name"),
            )
        remote = remote_by_name.get(local.name)
        remote_digest = SHA256_DIGEST.fullmatch(str(remote.get("digest", ""))) if remote else None
        remote_url = remote.get("browser_download_url") if remote else None
        expected_url_prefix = f"https://github.com/{repository}/releases/download/"
        exact = bool(
            remote and remote_digest
            and remote.get("size") == size
            and remote_digest.group(1).lower() == digest
            and isinstance(remote_url, str)
            and remote_url.startswith(expected_url_prefix)
        )
        item = {
            "name": local.name, "size": size, "sha256": digest,
            "remote_digest": remote.get("digest") if remote else None,
            "remote_url": remote_url,
        }
        (matches if exact else unmatched).append(item)

    common = {
        "version": version,
        "repository": repository,
        "release_tag": release.get("tag_name"),
        "release_name": release.get("name"),
        "release_url": release.get("html_url"),
        "published_at": published_at,
        "newer_stable_count": len(newer),
        "newer_stable_tags": [item.get("tag_name") for item in newer[:20]],
        "asset_matches": matches,
        "unmatched_files": unmatched,
        "local_path": path,
    }
    if unmatched:
        return review("Not every local file has an exact published SHA-256 match", **common)
    if len(newer) < KEEP_NEWEST_STABLE:
        return review("Release is current or within the two newest stable releases", **common)
    return {
        "kind": "github-release-asset-set",
        "eligible": True,
        "reason": "Every local file exactly matches a published GitHub release and two newer stable releases exist",
        "keep_newest_stable": KEEP_NEWEST_STABLE,
        **common,
    }
