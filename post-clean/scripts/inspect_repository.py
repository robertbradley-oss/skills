#!/usr/bin/env python3
"""Read-only Post Clean inspection from explicit paths and current Git evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


OUTPUT_SCHEMA = "post-clean-inspection/v2"
RESERVED_EXACT_PATHS = {".git", ".gameplan", ".post-clean", "GAMEPLAN.md"}
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_relative_path(raw: str) -> tuple[str | None, str | None]:
    value = raw.strip()
    if not value:
        return None, "path is empty"
    if "\\" in value:
        return None, "path must use / separators"
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return None, "path must be workspace-relative"
    if any(char in value for char in "*?[]{}"):
        return None, "wildcards are not allowed"
    path = PurePosixPath(value)
    if value == "." or any(part in {"", ".", ".."} for part in path.parts):
        return None, "path traversal or workspace-root targets are not allowed"
    return path.as_posix(), None


def lexical_path(root: Path, relative: str) -> tuple[Path | None, str | None]:
    candidate = Path(os.path.abspath(root.joinpath(*PurePosixPath(relative).parts)))
    try:
        if os.path.commonpath([str(root), str(candidate)]) != str(root):
            return None, "resolved path is outside the workspace"
    except ValueError:
        return None, "resolved path is on a different filesystem root"
    return candidate, None


def is_junction(path: Path) -> bool:
    check = getattr(path, "is_junction", None)
    return bool(check and check())


def target_outside_workspace(root: Path, path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
        return os.path.commonpath([str(root), str(resolved)]) != str(root)
    except (OSError, ValueError):
        return True


def has_link_ancestor(root: Path, path: Path) -> bool:
    """Return true when any component from the workspace root through path is a link."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if os.path.lexists(cursor) and (cursor.is_symlink() or is_junction(cursor)):
            return True
    return False


def fingerprint_path(root: Path, path: Path) -> dict[str, Any]:
    if not os.path.lexists(path):
        return {"type": "absent"}
    if path.is_symlink() or is_junction(path):
        try:
            target = os.readlink(path) if path.is_symlink() else str(path.resolve(strict=False))
        except OSError as exc:
            return {"type": "link", "error": str(exc)}
        return {
            "type": "junction" if is_junction(path) else "symlink",
            "target": target,
            "external_target": target_outside_workspace(root, path),
        }
    if path.is_file():
        stat = path.stat()
        return {"type": "file", "size": stat.st_size, "sha256": sha256_file(path)}
    if path.is_dir():
        entries: list[dict[str, Any]] = []

        def scan(directory: Path) -> None:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda entry: entry.name)
            for entry in children:
                child = Path(entry.path)
                relative = child.relative_to(path).as_posix()
                if entry.is_symlink() or is_junction(child):
                    entries.append({"path": relative, **fingerprint_path(root, child)})
                elif entry.is_dir(follow_symlinks=False):
                    entries.append({"path": relative, "type": "directory"})
                    scan(child)
                elif entry.is_file(follow_symlinks=False):
                    stat = child.stat()
                    entries.append({
                        "path": relative, "type": "file", "size": stat.st_size,
                        "sha256": sha256_file(child),
                    })
                else:
                    entries.append({"path": relative, "type": "other"})

        scan(path)
        manifest = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
        return {
            "type": "directory", "entries": entries, "entry_count": len(entries),
            "sha256": sha256_bytes(manifest),
        }
    return {"type": "other"}


def fingerprint_token(fingerprint: dict[str, Any]) -> str:
    encoded = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(encoded)


def is_reserved_path(path: str) -> bool:
    return any(path == item or path.startswith(item + "/") for item in RESERVED_EXACT_PATHS)


def run_git(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *arguments], cwd=root, shell=False,
        stdin=subprocess.DEVNULL, capture_output=True, check=False,
    )


def decode_path(value: bytes) -> str:
    return value.decode("utf-8", errors="surrogateescape").replace("\\", "/")


def repository_evidence(root: Path, base: str | None) -> tuple[dict[str, Any], list[dict[str, str]]]:
    evidence: dict[str, Any] = {
        "available": False, "root": None, "head": None, "base_requested": base,
        "base_commit": None, "status": {}, "base_changes": {},
    }
    refusals: list[dict[str, str]] = []
    probe = run_git(root, ["rev-parse", "--show-toplevel"])
    if probe.returncode != 0:
        refusals.append({"code": "git-unavailable", "message": "Workspace is not a Git worktree"})
        return evidence, refusals
    repository_root = Path(decode_path(probe.stdout).strip()).resolve()
    if repository_root != root:
        refusals.append({
            "code": "workspace-not-git-root",
            "message": f"Workspace must be the Git root; detected {repository_root}",
        })
        return evidence, refusals
    evidence["available"] = True
    evidence["root"] = str(repository_root)
    head = run_git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    if head.returncode == 0:
        evidence["head"] = decode_path(head.stdout).strip()

    status = run_git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    if status.returncode != 0:
        refusals.append({"code": "git-status-failed", "message": decode_path(status.stderr).strip()})
        evidence["available"] = False
        return evidence, refusals
    records = status.stdout.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        text = decode_path(record)
        if len(text) < 4:
            continue
        code, path = text[:2], text[3:]
        if code[0] in {"R", "C"} and index < len(records):
            old_path = decode_path(records[index])
            index += 1
            evidence["status"][path] = {"code": code, "old_path": old_path}
        else:
            evidence["status"][path] = {"code": code}

    if base:
        resolved = run_git(root, ["rev-parse", "--verify", f"{base}^{{commit}}"])
        if resolved.returncode != 0:
            refusals.append({
                "code": "git-base-invalid", "message": f"Git base does not resolve to a commit: {base}",
            })
            return evidence, refusals
        evidence["base_commit"] = decode_path(resolved.stdout).strip()
        diff = run_git(root, [
            "diff", "--name-status", "-z", "--find-renames", evidence["base_commit"], "--",
        ])
        if diff.returncode != 0:
            refusals.append({"code": "git-base-diff-failed", "message": decode_path(diff.stderr).strip()})
            return evidence, refusals
        parts = diff.stdout.split(b"\0")
        cursor = 0
        while cursor < len(parts):
            raw_status = parts[cursor]
            cursor += 1
            if not raw_status:
                continue
            change = decode_path(raw_status)
            if change.startswith(("R", "C")):
                if cursor + 1 >= len(parts):
                    break
                old_path = decode_path(parts[cursor]); new_path = decode_path(parts[cursor + 1])
                cursor += 2
                evidence["base_changes"][new_path] = {"code": change, "old_path": old_path}
            else:
                if cursor >= len(parts):
                    break
                path = decode_path(parts[cursor]); cursor += 1
                evidence["base_changes"][path] = {"code": change}
    return evidence, refusals


def descendant_evidence(path: str, mapping: dict[str, Any]) -> dict[str, Any]:
    prefix = path + "/"
    return {key: value for key, value in mapping.items() if key == path or key.startswith(prefix)}


def classify_git(path: str, current: dict[str, Any], git: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    status = descendant_evidence(path, git["status"])
    base_changes = descendant_evidence(path, git["base_changes"])
    detail = {"worktree": status, "base": base_changes}
    if not git["available"]:
        return "review", "Git evidence is unavailable", detail
    if current.get("type") == "absent":
        return "preserve", "Path is absent; no cleanup is needed", detail
    if current.get("type") in {"symlink", "junction", "link", "other"} or current.get("error"):
        return "review", "Links, junctions, special, or unreadable paths are not cleanup candidates", detail
    if current.get("external_target") or any(
        entry.get("type") in {"symlink", "junction", "link"} or entry.get("external_target")
        for entry in current.get("entries", [])
    ):
        return "review", "Path contains a link or junction", detail

    if current.get("type") == "directory":
        files = [entry["path"] for entry in current.get("entries", []) if entry.get("type") != "directory"]
        if not files:
            return "review", "Empty directories have no Git evidence of when or why they were created", detail
        states = []
        for child in files:
            full = path + "/" + child
            worktree_code = git["status"].get(full, {}).get("code")
            base_code = git["base_changes"].get(full, {}).get("code", "")
            if worktree_code == "??" or base_code.startswith("A"):
                states.append("added")
            else:
                states.append("other")
        if all(state == "added" for state in states):
            return "candidate", "Every file is untracked or added relative to the explicit Git base", detail
        return "review", "Directory contains tracked, modified, ignored, or otherwise unexplained content", detail

    worktree_code = git["status"].get(path, {}).get("code")
    base_code = git["base_changes"].get(path, {}).get("code", "")
    if worktree_code == "??":
        return "candidate", "Path is explicitly named and currently untracked", detail
    if worktree_code and "A" in worktree_code:
        return "candidate", "Path is explicitly named and added in the current index/worktree", detail
    if base_code.startswith("A"):
        return "candidate", "Path is explicitly named and added relative to the explicit Git base", detail
    if worktree_code or base_code:
        return "review", "Git shows a modification, deletion, rename, copy, or mixed state—not safe whole-path provenance", detail
    return "review", "Path is tracked with no evidence that the current task or branch introduced it", detail


def stable_id(scope_token: str, path: str, action: str, current: dict[str, Any], evidence: dict[str, Any]) -> str:
    material = json.dumps(
        {"scope": scope_token, "path": path, "action": action, "current": current, "evidence": evidence},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8", errors="surrogateescape")
    return "PC-" + sha256_bytes(material)[:12].upper()


def inspect(workspace: Path, requested_paths: list[str], git_base: str | None) -> dict[str, Any]:
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Workspace root must be a directory")
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA, "mode": "inspect", "mutations_performed": False,
        "apply_supported": True, "workspace": str(root), "scope": {"paths": [], "git_base": git_base},
        "git": {}, "items": [], "provisional_authorization_set": [], "refusals": [],
        "review_required": True,
    }
    if not requested_paths:
        result["refusals"].append({"code": "scope-empty", "message": "At least one explicit --path is required"})
        result["apply_supported"] = False
        return result
    normalized_paths: list[str] = []
    for raw in requested_paths:
        normalized, error = normalize_relative_path(raw)
        if error or normalized is None:
            result["refusals"].append({"code": "scope-path-invalid", "message": f"{raw!r}: {error}"})
        elif normalized in normalized_paths:
            result["refusals"].append({"code": "scope-path-duplicate", "message": f"Duplicate path: {normalized}"})
        else:
            normalized_paths.append(normalized)
    for index, first in enumerate(normalized_paths):
        for second in normalized_paths[index + 1:]:
            if first.startswith(second + "/") or second.startswith(first + "/"):
                result["refusals"].append({
                    "code": "scope-path-overlap",
                    "message": f"Overlapping scopes are not allowed: {first}, {second}",
                })
    result["scope"]["paths"] = normalized_paths
    git, git_refusals = repository_evidence(root, git_base)
    result["git"] = git
    result["refusals"].extend(git_refusals)
    if any(item["code"] in {"scope-path-invalid", "scope-path-duplicate", "scope-path-overlap", "git-base-invalid", "git-base-diff-failed", "workspace-not-git-root"} for item in result["refusals"]):
        result["apply_supported"] = False

    scope_token = sha256_bytes(json.dumps({
        "workspace": str(root), "paths": normalized_paths, "head": git.get("head"),
        "base_requested": git_base, "base_commit": git.get("base_commit"),
    }, sort_keys=True, separators=(",", ":")).encode())
    for path in normalized_paths:
        absolute, error = lexical_path(root, path)
        current: dict[str, Any] = {"type": "unresolved"}
        if error or absolute is None:
            classification, reason, evidence = "review", error or "Path could not be resolved", {}
        else:
            try:
                current = fingerprint_path(root, absolute)
            except OSError as exc:
                current = {"type": "unreadable", "error": str(exc)}
            if is_reserved_path(path):
                classification, reason, evidence = "preserve", "Post Clean control and planning paths are reserved", {}
            elif target_outside_workspace(root, absolute) or has_link_ancestor(root, absolute):
                classification, reason, evidence = "review", "Path uses a link/junction or resolves outside the workspace", {}
            else:
                classification, reason, evidence = classify_git(path, current, git)
        action = "remove-whole-path" if classification == "candidate" else "none"
        item_id = stable_id(scope_token, path, action, current, evidence)
        item = {
            "id": item_id, "path": path, "classification": classification,
            "proposed_action": action, "reason": reason, "current": current,
            "evidence": evidence,
            "provenance_claim": "Current repository evidence only; task provenance is not established.",
        }
        result["items"].append(item)
        if classification == "candidate" and result["apply_supported"]:
            result["provisional_authorization_set"].append(item_id)
    result["provisional_authorization_set"].sort()
    return result


def fingerprint_summary(current: dict[str, Any]) -> str:
    kind = current.get("type", "unknown")
    digest = current.get("sha256")
    return f"{kind}:{digest[:12]}" if digest else kind


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Post Clean inspection", "", f"Paths: `{', '.join(result['scope']['paths']) or 'none'}`",
        f"Git base: `{result['git'].get('base_commit') or 'none'}`", "Mutations: `none`", "",
        "| ID | Path | Decision | Action | Fingerprint | Reason |", "|---|---|---|---|---|---|",
    ]
    for item in result["items"]:
        reason = str(item["reason"]).replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{item['path']}` | `{item['classification']}` | "
            f"`{item['proposed_action']}` | `{fingerprint_summary(item['current'])}` | {reason} |"
        )
    if not result["items"]:
        lines.append("| - | - | - | - | - | No inspectable paths. |")
    authorization = ", ".join(f"`{item}`" for item in result["provisional_authorization_set"]) or "empty"
    lines.extend(["", f"Provisional authorization set: {authorization}", "", "Task provenance is not established; reference and context review is still required."])
    if result["refusals"]:
        lines.extend(["", "Refusals:"])
        lines.extend(f"- {item['code']}: {item['message']}" for item in result["refusals"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Workspace Git root")
    parser.add_argument("--path", action="append", required=True, help="Explicit workspace-relative path; repeat as needed")
    parser.add_argument("--git-base", help="Optional explicit commit, tag, or branch to diff against")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect(Path(args.workspace), args.path, args.git_base)
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
