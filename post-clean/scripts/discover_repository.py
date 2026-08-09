#!/usr/bin/env python3
"""Read-only discovery of possible folder and repository cleanup leads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from inspect_repository import (
    decode_path,
    is_junction,
    is_reserved_path,
    repository_evidence,
    run_git,
)


OUTPUT_SCHEMA = "post-clean-discovery/v2"
PROTECTED_BRANCHES = {"main", "master", "develop", "development", "trunk"}
CONTROL_NAMES = {".git", ".gameplan", ".hg", ".post-clean", ".svn"}
GENERATED_COMPONENTS = {
    ".cache", ".gradle", ".mypy_cache", ".next", ".nuxt", ".parcel-cache",
    ".pytest_cache", ".ruff_cache", ".tox", ".turbo", ".venv", "__pycache__",
    "artifacts", "bin", "build", "coverage", "dist", "node_modules", "obj",
    "out", "release", "target", "temp", "tmp", "vendor",
}
TEMPORARY_SUFFIXES = {
    ".bak", ".cache", ".dmp", ".log", ".old", ".orig", ".rej", ".swp", ".temp", ".tmp",
}
TEMPORARY_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TEMPORARY_NAMES_LOWER = {name.lower() for name in TEMPORARY_NAMES}


def stable_id(surface: str, target: str, signal: str, evidence: dict[str, Any]) -> str:
    material = json.dumps(
        {"surface": surface, "target": target, "signal": signal, "evidence": evidence},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8", errors="surrogateescape")
    return "PD-" + hashlib.sha256(material).hexdigest()[:12].upper()


def warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def markdown_cell(value: Any) -> str:
    return (
        str(value)
        .replace("`", "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "\\|")
    )


def run_git_values(root: Path, arguments: list[str]) -> tuple[list[str], str | None]:
    completed = run_git(root, arguments)
    if completed.returncode != 0:
        detail = decode_path(completed.stderr).strip() or f"git {' '.join(arguments)} failed"
        return [], detail
    return [decode_path(value) for value in completed.stdout.split(b"\0") if value], None


def normalize_git_path(value: str) -> str:
    return value.rstrip("/").replace("\\", "/")


def discover_git_paths(root: Path, ignored: bool) -> tuple[list[str], str | None]:
    arguments = ["ls-files", "--others"]
    if ignored:
        arguments.append("--ignored")
    arguments.extend(["--exclude-standard", "--directory", "--no-empty-directory", "-z"])
    values, error = run_git_values(root, arguments)
    paths = sorted({normalize_git_path(value) for value in values if normalize_git_path(value)})
    return paths, error


def summarize_path(root: Path, relative: str, limit: int = 5000) -> dict[str, Any]:
    path = root.joinpath(*PurePosixPath(relative).parts)
    if not os.path.lexists(path):
        return {"type": "absent"}
    if path.is_symlink() or is_junction(path):
        return {"type": "link", "scan": "not-followed"}
    if path.is_file():
        try:
            return {"type": "file", "files": 1, "directories": 0, "bytes": path.stat().st_size, "truncated": False}
        except OSError as exc:
            return {"type": "file", "error": str(exc)}
    if not path.is_dir():
        return {"type": "other"}

    files = 0
    directories = 0
    total_bytes = 0
    scanned = 0
    errors: list[str] = []
    stack = [path]
    while stack and scanned < limit:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                children = list(iterator)
        except OSError as exc:
            errors.append(str(exc))
            continue
        for entry in children:
            if scanned >= limit:
                break
            scanned += 1
            child = Path(entry.path)
            if entry.is_symlink() or is_junction(child):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    directories += 1
                    stack.append(child)
                elif entry.is_file(follow_symlinks=False):
                    files += 1
                    total_bytes += entry.stat(follow_symlinks=False).st_size
            except OSError as exc:
                errors.append(str(exc))
    result: dict[str, Any] = {
        "type": "directory", "files": files, "directories": directories,
        "bytes": total_bytes, "truncated": bool(stack) or scanned >= limit,
    }
    if errors:
        result["errors"] = errors[:3]
    return result


def path_signal(path: str, ignored: bool) -> tuple[str, str, str]:
    parts = [part.lower() for part in PurePosixPath(path).parts]
    name = PurePosixPath(path).name
    suffix = PurePosixPath(path).suffix.lower()
    generated = any(part in GENERATED_COMPONENTS for part in parts)
    temporary = name.lower() in TEMPORARY_NAMES_LOWER or suffix in TEMPORARY_SUFFIXES
    if generated:
        return (
            "generated-residue",
            "strong" if ignored else "moderate",
            "The path name matches a common generated, build, cache, package, or release-output location.",
        )
    if temporary:
        return (
            "temporary-file",
            "strong" if ignored else "moderate",
            "The filename matches a common temporary, backup, log, dump, or editor-residue pattern.",
        )
    if ignored:
        return (
            "ignored-content", "moderate",
            "Git ignores this path, but ignored content can still be an intentional local input or cache seed.",
        )
    return (
        "untracked-content", "weak",
        "The path is untracked. Git cannot establish why it exists or whether it is disposable.",
    )


def add_lead(
    leads: list[dict[str, Any]], surface: str, target: str, signal: str,
    confidence: str, reason: str, evidence: dict[str, Any],
) -> None:
    if any(
        item["surface"] == surface
        and item["target"] == target
        and item["signal"] == signal
        for item in leads
    ):
        return
    leads.append({
        "id": stable_id(surface, target, signal, evidence),
        "surface": surface,
        "target": target,
        "signal": signal,
        "confidence": confidence,
        "classification": "review",
        "proposed_action": "none",
        "reason": reason,
        "evidence": evidence,
        "provenance_claim": "Discovery evidence only; task provenance and disposability are not established.",
    })


def sha256_path(path: Path, expected_size: int) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        if os.fstat(handle.fileno()).st_size != expected_size:
            raise OSError("file size changed before hashing")
        remaining = expected_size
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                raise OSError("file became shorter while hashing")
            digest.update(chunk)
            remaining -= len(chunk)
        if os.fstat(handle.fileno()).st_size != expected_size:
            raise OSError("file size changed while hashing")
    return digest.hexdigest()


def discover_filesystem_leads(
    root: Path, leads: list[dict[str, Any]], warnings: list[dict[str, str]],
    max_files: int, max_hash_bytes: int,
) -> dict[str, Any]:
    files_by_size: dict[int, list[str]] = {}
    directories = 0
    files = 0
    links_skipped = 0
    control_paths_skipped = 0
    generated_roots = 0
    temporary_files = 0
    scan_truncated = False
    stack = [root]

    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            warnings.append(warning("filesystem-scan-failed", f"{directory}: {exc}"))
            continue

        child_directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            if entry.name.lower() in CONTROL_NAMES:
                control_paths_skipped += 1
                continue
            if entry.is_symlink() or is_junction(path):
                links_skipped += 1
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    directories += 1
                    if entry.name.lower() in GENERATED_COMPONENTS:
                        generated_roots += 1
                        add_lead(
                            leads, "path", relative, "generated-residue", "moderate",
                            "The directory name matches a common generated, build, cache, package, or release-output location.",
                            {"source": "filesystem", "footprint": summarize_path(root, relative)},
                        )
                    else:
                        child_directories.append(path)
                elif entry.is_file(follow_symlinks=False):
                    if files >= max_files:
                        scan_truncated = True
                        break
                    files += 1
                    stat = entry.stat(follow_symlinks=False)
                    name = entry.name
                    suffix = Path(name).suffix.lower()
                    if name.lower() in TEMPORARY_NAMES_LOWER or suffix in TEMPORARY_SUFFIXES:
                        temporary_files += 1
                        add_lead(
                            leads, "path", relative, "temporary-file", "moderate",
                            "The filename matches a common temporary, backup, log, dump, or editor-residue pattern.",
                            {
                                "source": "filesystem",
                                "footprint": {
                                    "type": "file", "files": 1, "directories": 0,
                                    "bytes": stat.st_size, "truncated": False,
                                },
                            },
                        )
                    elif stat.st_size > 0:
                        files_by_size.setdefault(stat.st_size, []).append(relative)
            except OSError as exc:
                warnings.append(warning("filesystem-entry-failed", f"{relative}: {exc}"))
        if scan_truncated:
            break
        stack.extend(reversed(child_directories))

    hashed_bytes = 0
    hash_budget_exhausted = False
    duplicate_sets = 0
    duplicate_files = 0
    for size, paths in sorted(files_by_size.items()):
        if len(paths) < 2:
            continue
        by_digest: dict[str, list[str]] = {}
        for relative in sorted(paths):
            if hashed_bytes + size > max_hash_bytes:
                hash_budget_exhausted = True
                continue
            path = root.joinpath(*PurePosixPath(relative).parts)
            try:
                digest = sha256_path(path, size)
            except OSError as exc:
                warnings.append(warning("duplicate-hash-failed", f"{relative}: {exc}"))
                continue
            hashed_bytes += size
            by_digest.setdefault(digest, []).append(relative)
        for digest, duplicates in sorted(by_digest.items()):
            if len(duplicates) < 2:
                continue
            ordered = sorted(duplicates)
            duplicate_sets += 1
            duplicate_files += len(ordered)
            add_lead(
                leads,
                "duplicate-set",
                f"{len(ordered)} files with SHA-256 {digest[:12]}",
                "exact-duplicate",
                "strong",
                "These files are byte-identical. Their locations, references, and intent must be reviewed before choosing any path for inspection.",
                {
                    "sha256": digest,
                    "bytes_each": size,
                    "total_bytes": size * len(ordered),
                    "paths": ordered,
                },
            )

    return {
        "filesystem_directories": directories,
        "filesystem_files": files,
        "filesystem_links_skipped": links_skipped,
        "filesystem_control_paths_skipped": control_paths_skipped,
        "filesystem_generated_roots": generated_roots,
        "filesystem_temporary_files": temporary_files,
        "filesystem_scan_truncated": scan_truncated,
        "duplicate_sets": duplicate_sets,
        "duplicate_files": duplicate_files,
        "duplicate_hashed_bytes": hashed_bytes,
        "duplicate_hash_budget_exhausted": hash_budget_exhausted,
    }


def discover_path_leads(
    root: Path, leads: list[dict[str, Any]], warnings: list[dict[str, str]], max_leads: int,
) -> dict[str, int]:
    untracked, untracked_error = discover_git_paths(root, ignored=False)
    ignored, ignored_error = discover_git_paths(root, ignored=True)
    if untracked_error:
        warnings.append(warning("untracked-scan-failed", untracked_error))
    if ignored_error:
        warnings.append(warning("ignored-scan-failed", ignored_error))

    ignored_set = set(ignored)
    combined = [(path, False) for path in untracked if path not in ignored_set]
    combined.extend((path, True) for path in ignored)
    for path, is_ignored in combined:
        if len(leads) >= max_leads:
            break
        if is_reserved_path(path):
            continue
        signal, confidence, reason = path_signal(path, is_ignored)
        add_lead(
            leads, "path", path, signal, confidence, reason,
            {"git": "ignored" if is_ignored else "untracked", "footprint": summarize_path(root, path)},
        )
    return {"untracked_roots": len(untracked), "ignored_roots": len(ignored)}


def branch_rows(root: Path) -> tuple[list[dict[str, str]], str | None]:
    completed = run_git(root, [
        "for-each-ref",
        "--format=%(refname:short)|%(upstream:short)|%(upstream:track)|%(objectname)",
        "refs/heads",
    ])
    if completed.returncode != 0:
        return [], decode_path(completed.stderr).strip()
    rows: list[dict[str, str]] = []
    for line in decode_path(completed.stdout).splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            rows.append({"name": parts[0], "upstream": parts[1], "track": parts[2], "object": parts[3]})
    return rows, None


def current_branch(root: Path) -> str | None:
    completed = run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    return decode_path(completed.stdout).strip() if completed.returncode == 0 else None


def merged_branches(root: Path) -> tuple[set[str], str | None]:
    completed = run_git(root, ["branch", "--merged", "HEAD", "--format=%(refname:short)"])
    if completed.returncode != 0:
        return set(), decode_path(completed.stderr).strip()
    return set(decode_path(completed.stdout).splitlines()), None


def discover_branch_leads(
    root: Path, leads: list[dict[str, Any]], warnings: list[dict[str, str]], max_leads: int,
) -> dict[str, int]:
    rows, rows_error = branch_rows(root)
    merged, merged_error = merged_branches(root)
    if rows_error:
        warnings.append(warning("branch-scan-failed", rows_error))
    if merged_error:
        warnings.append(warning("merged-branch-scan-failed", merged_error))
    active = current_branch(root)
    stale = 0
    merged_review = 0
    for row in rows:
        name = row["name"]
        evidence = {"head": row["object"], "upstream": row["upstream"], "track": row["track"], "current": name == active}
        if "gone" in row["track"]:
            stale += 1
            add_lead(
                leads, "branch", name, "stale-upstream", "moderate",
                "The local branch tracks an upstream that no longer exists. Preserve it until unique commits and worktree use are checked.",
                evidence,
            )
        if name in merged and name != active and name not in PROTECTED_BRANCHES:
            merged_review += 1
            add_lead(
                leads, "branch", name, "merged-local-branch", "moderate",
                "The branch tip is reachable from HEAD. Confirm it is not used by another worktree or retained intentionally before deletion.",
                evidence,
            )
    return {"local_branches": len(rows), "stale_upstreams": stale, "merged_review_branches": merged_review}


def parse_worktrees(root: Path) -> tuple[list[dict[str, Any]], str | None]:
    completed = run_git(root, ["worktree", "list", "--porcelain"])
    if completed.returncode != 0:
        return [], decode_path(completed.stderr).strip()
    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in decode_path(completed.stdout).splitlines() + [""]:
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"detached", "bare"}:
            current[key] = True
        elif key == "locked":
            current[key] = value or True
        elif key == "prunable":
            current[key] = value or True
        else:
            current[key] = value
    return worktrees, None


def discover_worktree_leads(
    root: Path, leads: list[dict[str, Any]], warnings: list[dict[str, str]], max_leads: int,
) -> dict[str, int]:
    worktrees, error = parse_worktrees(root)
    if error:
        warnings.append(warning("worktree-scan-failed", error))
    additional = 0
    prunable = 0
    for item in worktrees:
        path = item.get("worktree")
        if not path:
            continue
        try:
            same = Path(path).resolve(strict=False) == root
        except OSError:
            same = False
        if same:
            continue
        additional += 1
        signal = "prunable-worktree" if item.get("prunable") else "additional-worktree"
        if item.get("prunable"):
            prunable += 1
        add_lead(
            leads, "worktree", path, signal, "strong" if item.get("prunable") else "weak",
            "Git marks this worktree prunable." if item.get("prunable") else
            "Another linked worktree exists. Its branch and uncommitted state must be inspected before removal.",
            item,
        )
    return {"linked_worktrees": len(worktrees), "additional_worktrees": additional, "prunable_worktrees": prunable}


def discover_integrity_lead(root: Path, leads: list[dict[str, Any]], max_leads: int) -> int:
    completed = run_git(root, ["show-ref", "--head"])
    if completed.returncode == 0:
        return 0
    detail = decode_path(completed.stderr).strip()
    evidence = {"exit_code": completed.returncode, "error": detail[:1000]}
    add_lead(
        leads, "repository", "Git references", "git-reference-error", "strong",
        "Git could not enumerate references cleanly. Repair metadata separately after backing it up; path cleanup cannot fix this.",
        evidence,
    )
    return 1


def discover(
    workspace: Path, git_base: str | None, max_leads: int,
    max_files: int = 50000, max_hash_bytes: int = 1024 * 1024 * 1024,
) -> dict[str, Any]:
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Workspace root must be a directory")
    if max_leads <= 0:
        raise ValueError("max-leads must be positive")
    if max_files <= 0:
        raise ValueError("max-files must be positive")
    if max_hash_bytes <= 0:
        raise ValueError("max-hash-bytes must be positive")

    git, refusals = repository_evidence(root, git_base)
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "mode": "discover",
        "mutations_performed": False,
        "apply_supported": False,
        "workspace": str(root),
        "scope_type": "git-repository" if git.get("available") else "folder",
        "git": git,
        "summary": {},
        "leads": [],
        "provisional_authorization_set": [],
        "warnings": list(refusals),
        "review_required": True,
    }
    leads: list[dict[str, Any]] = result["leads"]
    summary: dict[str, Any] = result["summary"]
    if git.get("available"):
        summary.update(discover_path_leads(root, leads, result["warnings"], max_leads))
        summary.update(discover_branch_leads(root, leads, result["warnings"], max_leads))
        summary.update(discover_worktree_leads(root, leads, result["warnings"], max_leads))
        summary["git_reference_errors"] = discover_integrity_lead(root, leads, max_leads)
        summary["tracked_worktree_changes"] = sum(
            1 for item in git.get("status", {}).values() if item.get("code") != "??"
        )
    else:
        summary.update({
            "untracked_roots": 0, "ignored_roots": 0, "local_branches": 0,
            "stale_upstreams": 0, "merged_review_branches": 0, "linked_worktrees": 0,
            "additional_worktrees": 0, "prunable_worktrees": 0,
            "git_reference_errors": 0, "tracked_worktree_changes": 0,
        })
    summary.update(discover_filesystem_leads(
        root, leads, result["warnings"], max_files, max_hash_bytes,
    ))
    priority = {"repository": 0, "worktree": 1, "branch": 2, "path": 3, "duplicate-set": 4}
    leads.sort(key=lambda item: (priority.get(item["surface"], 9), item["signal"], item["target"]))
    summary["lead_count_total"] = len(leads)
    if len(leads) > max_leads:
        del leads[max_leads:]
    summary["lead_count"] = len(leads)
    summary["truncated"] = summary["lead_count_total"] > len(leads)
    return result


def footprint_text(value: dict[str, Any]) -> str:
    if value.get("type") == "file":
        return f"{value.get('bytes', 0)} bytes"
    if value.get("type") == "directory":
        suffix = "+" if value.get("truncated") else ""
        return f"{value.get('files', 0)}{suffix} files, {value.get('bytes', 0)}{suffix} bytes"
    return value.get("type", "unknown")


def evidence_text(lead: dict[str, Any]) -> str:
    evidence = lead["evidence"]
    if lead["surface"] == "path":
        return footprint_text(evidence.get("footprint", {}))
    if lead["surface"] == "branch":
        upstream = evidence.get("upstream") or "none"
        track = evidence.get("track") or "no tracking delta"
        return f"upstream {upstream}; {track}"
    if lead["surface"] == "worktree":
        branch = str(evidence.get("branch", "detached")).removeprefix("refs/heads/")
        return f"branch {branch}"
    if lead["surface"] == "repository":
        return f"git exit {evidence.get('exit_code', 'unknown')}"
    if lead["surface"] == "duplicate-set":
        return f"{len(evidence.get('paths', []))} files; {evidence.get('bytes_each', 0)} bytes each"
    return "unknown"


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Post Clean discovery", "", f"Workspace: `{result['workspace']}`", "Mutations: `none`",
        "Apply supported from discovery: `no`", "",
        "| ID | Surface | Target | Signal | Confidence | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for lead in result["leads"]:
        target = markdown_cell(lead["target"])
        footprint = markdown_cell(evidence_text(lead))
        lines.append(
            f"| `{lead['id']}` | `{markdown_cell(lead['surface'])}` | `{target}` | "
            f"`{markdown_cell(lead['signal'])}` | `{markdown_cell(lead['confidence'])}` | {footprint} |"
        )
    if not result["leads"]:
        lines.append("| - | - | - | - | - | No cleanup leads found. |")
    lines.extend([
        "", "Discovery leads are review prompts, not cleanup candidates or authorization.",
        "Select exact Git-root path leads for a separate Inspect pass. Folder-only, duplicate-set, branch, worktree, and repository leads remain review-only.",
    ])
    if result["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(
            f"- {markdown_cell(item['code'])}: {markdown_cell(item['message'])}"
            for item in result["warnings"]
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Folder, workspace, or Git repository root")
    parser.add_argument("--git-base", help="Optional explicit commit, tag, or branch for context")
    parser.add_argument("--max-leads", type=int, default=200, help="Bound the number of discovery leads")
    parser.add_argument("--max-files", type=int, default=50000, help="Bound filesystem files examined")
    parser.add_argument(
        "--max-hash-bytes", type=int, default=1024 * 1024 * 1024,
        help="Bound total bytes read for exact-duplicate hashing",
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = discover(
            Path(args.workspace), args.git_base, args.max_leads,
            args.max_files, args.max_hash_bytes,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"schema": OUTPUT_SCHEMA, "error": str(exc)}, indent=2))
        return 1
    if args.format == "markdown":
        sys.stdout.write(render_markdown(result))
    else:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
