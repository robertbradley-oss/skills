#!/usr/bin/env python3
"""Read-only Clean Up inspection from explicit paths and current Git evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from release_retention import analyze_release_directory


OUTPUT_SCHEMA = "clean-up-inspection/v2"
RESERVED_EXACT_PATHS = {".clean-up", ".git", ".gameplan", ".post-clean", "GAMEPLAN.md"}
AMBIGUOUS_EMPTY_NAMES = {
    "artifacts", "cache", "data", "fixture", "fixtures", "output", "release",
    "runtime", "seed", "seeds", "storage", "testdata", "uploads", "vendor",
}


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
        file_stat = path.stat()
        return {"type": "file", "size": file_stat.st_size, "sha256": sha256_file(path)}
    if path.is_dir():
        directory_stat = path.stat()
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
                    file_stat = child.stat()
                    entries.append({
                        "path": relative, "type": "file", "size": file_stat.st_size,
                        "sha256": sha256_file(child),
                    })
                else:
                    entries.append({"path": relative, "type": "other"})

        scan(path)
        manifest = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
        return {
            "type": "directory", "entries": entries, "entry_count": len(entries),
            "sha256": sha256_bytes(manifest),
            "metadata": {
                "mode": stat.S_IMODE(directory_stat.st_mode),
                "mtime_ns": directory_stat.st_mtime_ns,
            },
        }
    return {"type": "other"}


def fingerprint_token(fingerprint: dict[str, Any]) -> str:
    encoded = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(encoded)


def is_reserved_path(path: str) -> bool:
    return any(path == item or path.startswith(item + "/") for item in RESERVED_EXACT_PATHS)


def run_git(
    root: Path, arguments: list[str], input_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    input_options = {"input": input_data} if input_data is not None else {"stdin": subprocess.DEVNULL}
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *arguments], cwd=root, shell=False,
        capture_output=True, check=False, **input_options,
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


def tracked_descendants(root: Path, path: str) -> tuple[list[str], str | None]:
    completed = run_git(root, ["ls-files", "-z", "--", path])
    if completed.returncode != 0:
        return [], decode_path(completed.stderr).strip() or "git ls-files failed"
    return sorted(decode_path(item) for item in completed.stdout.split(b"\0") if item), None


def ignored_tree_evidence(root: Path, path: str, current: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    checked = [path]
    if current.get("type") == "directory":
        checked.extend(f"{path}/{entry['path']}" for entry in current.get("entries", []))
    payload = b"\0".join(item.encode("utf-8", errors="surrogateescape") for item in checked) + b"\0"
    completed = run_git(
        root,
        ["check-ignore", "--no-index", "--verbose", "--non-matching", "-z", "--stdin"],
        payload,
    )
    if completed.returncode not in {0, 1}:
        return {}, decode_path(completed.stderr).strip() or "git check-ignore failed"
    fields = completed.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 4 != 0:
        return {}, "git check-ignore returned malformed evidence"
    records: dict[str, dict[str, Any]] = {}
    for index in range(0, len(fields), 4):
        source, line_number, pattern, matched_path = fields[index:index + 4]
        normalized = decode_path(matched_path)
        records[normalized] = {
            "ignored": bool(pattern),
            "source": decode_path(source) if source else None,
            "line": decode_path(line_number) if line_number else None,
            "pattern": decode_path(pattern) if pattern else None,
        }
    unmatched = [item for item in checked if not records.get(item, {}).get("ignored")]
    return {
        "root_ignored": bool(records.get(path, {}).get("ignored")),
        "complete_tree_ignored": not unmatched,
        "checked_paths": len(checked),
        "unmatched_paths": unmatched,
        "root_rule": records.get(path),
    }, None


def has_dotnet_project_root(path: Path) -> bool:
    try:
        if path.stat().st_size > 1024 * 1024:
            return False
        with path.open("rb") as handle:
            text = handle.read(64 * 1024).decode("utf-8-sig", errors="replace")
    except OSError:
        return False
    cursor = 0
    length = len(text)
    while cursor < length and text[cursor].isspace():
        cursor += 1
    if text.startswith("<?xml", cursor):
        end = text.find("?>", cursor + 5)
        if end < 0:
            return False
        cursor = end + 2
    while True:
        while cursor < length and text[cursor].isspace():
            cursor += 1
        if not text.startswith("<!--", cursor):
            break
        end = text.find("-->", cursor + 4)
        if end < 0:
            return False
        cursor = end + 3
    if not text.startswith("<Project", cursor):
        return False
    boundary = cursor + len("<Project")
    return boundary < length and (text[boundary].isspace() or text[boundary] in {">", "/"})


def dotnet_generated_context(root: Path, path: str, absolute: Path) -> dict[str, Any] | None:
    output_name = PurePosixPath(path).name.lower()
    if output_name not in {"bin", "obj"} or not absolute.is_dir():
        return None
    projects: list[str] = []
    try:
        neighbors = sorted(absolute.parent.iterdir(), key=lambda item: item.name.lower())
    except OSError:
        return None
    for project in neighbors:
        if project.suffix.lower() != ".csproj" or project.is_symlink() or is_junction(project):
            continue
        if not project.is_file() or target_outside_workspace(root, project):
            continue
        relative = project.relative_to(root).as_posix()
        tracked = run_git(root, ["ls-files", "--error-unmatch", "--", relative])
        if tracked.returncode != 0:
            continue
        if has_dotnet_project_root(project):
            projects.append(relative)
    if not projects:
        return None
    return {
        "kind": "dotnet-conventional-output",
        "output_name": output_name,
        "tracked_projects": projects,
    }


def repository_reference_evidence(root: Path, path: str) -> tuple[dict[str, Any], str | None]:
    queries = [path]
    windows_path = path.replace("/", "\\")
    if windows_path != path:
        queries.append(windows_path)
    arguments = ["grep", "--untracked", "--full-name", "-I", "-i", "-n", "-F"]
    for query in queries:
        arguments.extend(["-e", query])
    arguments.extend([
        "--", ".",
        ":(exclude)GAMEPLAN.md",
        ":(exclude).gameplan/**",
        ":(exclude).clean-up/**",
        ":(exclude).post-clean/**",
    ])
    completed = run_git(root, arguments)
    if completed.returncode not in {0, 1}:
        return {}, decode_path(completed.stderr).strip() or "git grep failed"
    reference_pattern = re.compile(
        rf"(?<![A-Za-z0-9_.-]){re.escape(path)}(?![A-Za-z0-9_.-])",
        flags=re.IGNORECASE,
    )
    matches = []
    for raw_line in completed.stdout.splitlines():
        line = decode_path(raw_line)
        fields = line.split(":", 2)
        source = fields[0]
        if PurePosixPath(source).name == ".gitignore":
            continue
        if len(fields) < 3 or reference_pattern.search(fields[2]):
            matches.append(line)
    return {
        "query": path,
        "match_semantics": "path-token",
        "matches": matches[:20],
        "match_count": len(matches),
        "truncated": len(matches) > 20,
    }, None


def classify_git(
    root: Path, path: str, absolute: Path, current: dict[str, Any], git: dict[str, Any],
) -> tuple[str, str, dict[str, Any], str | None]:
    status = descendant_evidence(path, git["status"])
    base_changes = descendant_evidence(path, git["base_changes"])
    detail = {"worktree": status, "base": base_changes}
    if not git["available"]:
        return "review", "Git evidence is unavailable", detail, None
    if current.get("type") == "absent":
        return "preserve", "Path is absent; no cleanup is needed", detail, None
    if current.get("type") in {"symlink", "junction", "link", "other"} or current.get("error"):
        return "review", "Links, junctions, special, or unreadable paths are not cleanup candidates", detail, None
    if current.get("external_target") or any(
        entry.get("type") in {"symlink", "junction", "link", "other"}
        or entry.get("external_target") or entry.get("error")
        for entry in current.get("entries", [])
    ):
        return "review", "Path contains a link, junction, special, or unreadable descendant", detail, None

    tracked, tracked_error = tracked_descendants(root, path)
    ignored, ignored_error = ignored_tree_evidence(root, path, current)
    detail["tracked_paths"] = tracked
    detail["ignored"] = ignored
    if tracked_error or ignored_error:
        detail["evidence_error"] = tracked_error or ignored_error
        return "review", "Git could not establish complete tracked and ignored state", detail, None

    if current.get("type") == "directory":
        files = [entry["path"] for entry in current.get("entries", []) if entry.get("type") != "directory"]
        if ignored.get("root_ignored"):
            if not ignored.get("complete_tree_ignored"):
                return "review", "The selected root is ignored, but its complete tree is not ignored", detail, None
            if tracked or status or base_changes:
                return "review", "Ignored root contains tracked, staged, modified, added, or mixed-state descendants", detail, None
            generated_context = dotnet_generated_context(root, path, absolute)
            detail["generated_context"] = generated_context
            if generated_context is not None:
                references, reference_error = repository_reference_evidence(root, path)
                detail["references"] = references
                if reference_error:
                    detail["evidence_error"] = reference_error
                    return "review", "Repository references could not be checked", detail, None
                if references.get("match_count"):
                    return "review", "Repository content references the ignored generated root", detail, None
                return (
                    "candidate",
                    "The exact ignored tree is conventional .NET build output beside a tracked project",
                    detail,
                    "ignored-generated",
                )
        expected_untracked = {path + "/" + child for child in files}
        fully_untracked = bool(expected_untracked) and set(status) == expected_untracked and all(
            item.get("code") == "??" for item in status.values()
        )
        release_retention = analyze_release_directory(path, absolute)
        detail["release_retention"] = release_retention
        if release_retention is not None:
            if ignored.get("root_ignored") and ignored.get("complete_tree_ignored") and not status:
                local_git_state = "ignored"
            elif fully_untracked and not tracked and not base_changes:
                local_git_state = "untracked"
            else:
                local_git_state = "unsafe"
            release_retention = {**release_retention, "local_git_state": local_git_state}
            detail["release_retention"] = release_retention
            if tracked or base_changes or local_git_state == "unsafe":
                return "review", "Release directory has tracked, staged, modified, or mixed Git state", detail, None
            references, reference_error = repository_reference_evidence(root, path)
            detail["references"] = references
            if reference_error:
                detail["evidence_error"] = reference_error
                return "review", "Repository references could not be checked", detail, None
            if release_retention.get("eligible") is True:
                return (
                    "candidate",
                    "The exact release is fully backed by published SHA-256 assets and superseded",
                    detail,
                    "remote-backed-release",
                )
            return "review", str(release_retention.get("reason") or "Release retention is unresolved"), detail, None
        if current.get("entry_count") == 0:
            if tracked or status or base_changes:
                return "review", "Empty directory has tracked or changed Git state", detail, None
            references, reference_error = repository_reference_evidence(root, path)
            detail["references"] = references
            if reference_error:
                detail["evidence_error"] = reference_error
                return "review", "Repository references could not be checked", detail, None
            if PurePosixPath(path).name.lower() in AMBIGUOUS_EMPTY_NAMES:
                return "review", "Empty directory name may denote retained, fixture, runtime, or cache content", detail, None
            if references.get("match_count"):
                return "review", "Repository content references the empty directory", detail, None
            return (
                "candidate",
                "The exact directory is empty, metadata-bound, and unreferenced by repository content",
                detail,
                "empty-directory",
            )
        if ignored.get("root_ignored"):
            return "review", "Ignored status alone does not establish generated context or disposability", detail, None
        if not files:
            return "review", "Directory contains only empty descendants and lacks safe whole-path evidence", detail, None
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
            return "candidate", "Every file is untracked or added relative to the explicit Git base", detail, "git-new"
        return "review", "Directory contains tracked, modified, ignored, or otherwise unexplained content", detail, None

    worktree_code = git["status"].get(path, {}).get("code")
    base_code = git["base_changes"].get(path, {}).get("code", "")
    if worktree_code == "??":
        return "candidate", "Path is explicitly named and currently untracked", detail, "git-new"
    if worktree_code and "A" in worktree_code:
        return "candidate", "Path is explicitly named and added in the current index/worktree", detail, "git-new"
    if base_code.startswith("A"):
        return "candidate", "Path is explicitly named and added relative to the explicit Git base", detail, "git-new"
    if worktree_code or base_code:
        return "review", "Git shows a modification, deletion, rename, copy, or mixed state - not safe whole-path provenance", detail, None
    return "review", "Path is tracked with no evidence that the current task or branch introduced it", detail, None


def stable_id(
    scope_token: str, path: str, action: str, candidate_kind: str | None,
    current: dict[str, Any], evidence: dict[str, Any],
) -> str:
    material = json.dumps(
        {
            "scope": scope_token, "path": path, "action": action,
            "candidate_kind": candidate_kind, "current": current, "evidence": evidence,
        },
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
        candidate_kind: str | None = None
        if error or absolute is None:
            classification, reason, evidence = "review", error or "Path could not be resolved", {}
        else:
            try:
                current = fingerprint_path(root, absolute)
            except OSError as exc:
                current = {"type": "unreadable", "error": str(exc)}
            if is_reserved_path(path):
                classification, reason, evidence = "preserve", "Clean Up control and planning paths are reserved", {}
            elif target_outside_workspace(root, absolute) or has_link_ancestor(root, absolute):
                classification, reason, evidence = "review", "Path uses a link/junction or resolves outside the workspace", {}
            else:
                classification, reason, evidence, candidate_kind = classify_git(root, path, absolute, current, git)
        action = "remove-whole-path" if classification == "candidate" else "none"
        item_id = stable_id(scope_token, path, action, candidate_kind, current, evidence)
        item = {
            "id": item_id, "path": path, "classification": classification,
            "proposed_action": action, "candidate_kind": candidate_kind,
            "reason": reason, "current": current,
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
        "# Clean Up inspection", "", f"Paths: `{', '.join(result['scope']['paths']) or 'none'}`",
        f"Git base: `{result['git'].get('base_commit') or 'none'}`", "Mutations: `none`", "",
        "| ID | Path | Decision | Candidate kind | Action | Fingerprint | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in result["items"]:
        reason = str(item["reason"]).replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{item['path']}` | `{item['classification']}` | "
            f"`{item['candidate_kind'] or 'none'}` | `{item['proposed_action']}` | "
            f"`{fingerprint_summary(item['current'])}` | {reason} |"
        )
    if not result["items"]:
        lines.append("| - | - | - | - | - | - | No inspectable paths. |")
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
