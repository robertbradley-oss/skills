#!/usr/bin/env python3
"""Read-only, bounded analysis of loose workspace files that may need organization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from discover_repository import markdown_cell
from inspect_repository import (
    decode_path, is_reserved_path, repository_reference_evidence, run_git,
)


OUTPUT_SCHEMA = "clean-up-file-organization/v2"
ROLE_DESTINATIONS = {
    "documentation": ("docs",),
    "image": ("assets", "images", "references"),
    "script": ("scripts", "tools"),
    "test": ("tests",),
    "example": ("examples", "samples"),
}
DOCUMENTATION_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
SCRIPT_EXTENSIONS = {".bat", ".cmd", ".ps1", ".py", ".sh"}
PROJECT_EXTENSIONS = {
    ".csproj", ".fsproj", ".props", ".sln", ".targets", ".vbproj",
}
PROTECTED_ROOT_NAMES = {
    "agents.md", "authors", "authors.md", "changelog", "changelog.md",
    "citation.cff", "code_of_conduct.md", "contributing", "contributing.md",
    "copying", "dockerfile", "gameplan.md", "go.mod", "go.sum", "justfile",
    "license", "license.md", "license.txt", "makefile", "notice", "notice.md",
    "package-lock.json", "package.json", "pnpm-lock.yaml", "poetry.lock",
    "pyproject.toml", "readme", "readme.md", "readme.txt", "requirements.txt",
    "security.md", "setup.cfg", "setup.py", "taskfile.yml", "tsconfig.json",
    "uv.lock", "yarn.lock",
}
PROTECTED_ROOT_STEMS = {
    "bootstrap", "build", "configure", "install", "run", "setup", "start",
}
TEST_NAME_RE = re.compile(r"^(?:test[_-].+|.+(?:\.|_)(?:test|tests))\.[^.]+$", re.IGNORECASE)
EXAMPLE_NAME_RE = re.compile(r"(?:^|[._-])(?:example|sample)(?:[._-]|$)", re.IGNORECASE)


def normalized_git_path(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def git_values(root: Path, arguments: list[str]) -> tuple[list[str], str | None]:
    completed = run_git(root, arguments)
    if completed.returncode != 0:
        return [], decode_path(completed.stderr).strip() or f"git {' '.join(arguments)} failed"
    return [decode_path(value) for value in completed.stdout.split(b"\0") if value], None


def scope(root: Path) -> tuple[str, dict[str, set[str]], list[dict[str, str]]]:
    probe = run_git(root, ["rev-parse", "--show-toplevel"])
    if probe.returncode != 0:
        return "folder", {}, []
    try:
        reported = Path(decode_path(probe.stdout).strip()).resolve(strict=True)
    except OSError:
        return "folder", {}, []
    if os.path.normcase(str(root)) != os.path.normcase(str(reported)):
        return "folder", {}, []
    warnings: list[dict[str, str]] = []
    commands = {
        "tracked": ["ls-files", "-z"],
        "changed": ["diff", "--name-only", "-z", "HEAD", "--"],
        "untracked": ["ls-files", "--others", "--exclude-standard", "-z"],
        "ignored": ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
    }
    states: dict[str, set[str]] = {}
    for name, arguments in commands.items():
        values, error = git_values(root, arguments)
        states[name] = {normalized_git_path(value) for value in values}
        if error:
            warnings.append({"code": f"organization-{name}-failed", "message": error})
    return "git-repository", states, warnings


def protected_root_file(name: str) -> bool:
    lowered = name.casefold()
    pure = PurePosixPath(name)
    return bool(
        name.startswith(".")
        or lowered in PROTECTED_ROOT_NAMES
        or pure.suffix.casefold() in PROJECT_EXTENSIONS
        or pure.stem.casefold() in PROTECTED_ROOT_STEMS
        or lowered.endswith((".lock", ".lock.json"))
    )


def role_for(name: str) -> str | None:
    pure = PurePosixPath(name)
    lowered = name.casefold()
    suffix = pure.suffix.casefold()
    if TEST_NAME_RE.match(name):
        return "test"
    if EXAMPLE_NAME_RE.search(lowered):
        return "example"
    if suffix in DOCUMENTATION_EXTENSIONS:
        return "documentation"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in SCRIPT_EXTENSIONS:
        return "script"
    return None


def file_state(relative: str, scope_type: str, states: dict[str, set[str]]) -> str:
    if scope_type != "git-repository":
        return "not-applicable"
    if relative in states.get("tracked", set()):
        return "tracked-changed" if relative in states.get("changed", set()) else "tracked-clean"
    if relative in states.get("ignored", set()):
        return "ignored"
    if relative in states.get("untracked", set()):
        return "untracked"
    return "unknown"


def stable_id(
    path: str, role: str, destinations: list[str], sha256: str, git_state: str,
    references: dict[str, Any] | None,
) -> str:
    material = json.dumps(
        {
            "schema": OUTPUT_SCHEMA,
            "path": path,
            "role": role,
            "destinations": destinations,
            "sha256": sha256,
            "git_state": git_state,
            "references": references,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return "FO-" + hashlib.sha256(material).hexdigest()[:12].upper()


def analyze_file_organization(
    workspace: Path, max_files: int = 1000, max_bytes: int = 64 * 1024 * 1024,
) -> dict[str, Any]:
    if max_files <= 0:
        raise ValueError("max-files must be positive")
    if max_bytes <= 0:
        raise ValueError("max-bytes must be positive")
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Workspace must be a directory")
    scope_type, states, warnings = scope(root)
    destinations = {
        entry.name.casefold(): entry.name
        for entry in os.scandir(root)
        if entry.is_dir(follow_symlinks=False) and not entry.is_symlink()
    }
    try:
        root_files = sorted(
            (entry for entry in os.scandir(root) if entry.is_file(follow_symlinks=False)),
            key=lambda entry: entry.name.casefold(),
        )
    except OSError as exc:
        raise ValueError(f"Could not enumerate workspace root: {exc}") from exc

    findings: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, Any]] = []
    scanned_files = 0
    scanned_bytes = 0
    truncated = False
    unreadable: list[str] = []
    for entry in root_files:
        if scanned_files >= max_files:
            truncated = True
            break
        relative = entry.name.replace("\\", "/")
        if is_reserved_path(relative) or protected_root_file(entry.name):
            continue
        role = role_for(entry.name)
        if role is None:
            continue
        candidate_directories = [
            destinations[name] for name in ROLE_DESTINATIONS[role] if name in destinations
        ]
        if not candidate_directories:
            continue
        path = Path(entry.path)
        try:
            size = path.stat().st_size
            if scanned_bytes + size > max_bytes:
                truncated = True
                break
            data = path.read_bytes()
            if len(data) != size:
                raise OSError("file size changed while reading")
        except OSError as exc:
            unreadable.append(relative)
            warnings.append({
                "code": "organization-file-read-failed", "message": f"{relative}: {exc}",
            })
            continue
        scanned_files += 1
        scanned_bytes += len(data)
        digest = hashlib.sha256(data).hexdigest()
        state = file_state(relative, scope_type, states)
        suggested_directory = candidate_directories[0] if len(candidate_directories) == 1 else None
        suggested_path = (
            f"{suggested_directory}/{relative}" if suggested_directory is not None else None
        )
        collision = bool(suggested_path and (root / suggested_path).exists())
        references: dict[str, Any] | None = None
        reference_error: str | None = None
        if scope_type == "git-repository" and suggested_path is not None:
            references, reference_error = repository_reference_evidence(root, relative)
        if reference_error:
            warnings.append({
                "code": "organization-reference-check-failed",
                "message": f"{relative}: {reference_error}",
            })
        if suggested_directory is None:
            classification = "keep"
            proposed_action = "none"
            reason = (
                f"Keep at the current location: the loose root {role} file matches multiple "
                f"established directories ({', '.join(candidate_directories)}), so no unique "
                "destination is proven."
            )
        elif collision:
            classification = "keep"
            proposed_action = "none"
            reason = (
                f"Keep at the current location: {suggested_path} already exists, so an automatic "
                "move could overwrite or conflate distinct content."
            )
        elif state not in {"tracked-clean", "untracked"}:
            classification = "keep"
            proposed_action = "none"
            reason = (
                f"Keep at the current location: the file is {state}, and organization must not "
                "relocate changed, ignored, unknown, or non-Git content automatically."
            )
        elif reference_error:
            classification = "keep"
            proposed_action = "none"
            reason = (
                "Keep at the current location: repository references could not be checked reliably."
            )
        else:
            classification = "move-recommended"
            proposed_action = "move-file-with-reference-updates"
            reference_count = int((references or {}).get("match_count", 0))
            reference_note = (
                f" Update {reference_count} repository path reference(s) as part of the move."
                if reference_count else " No repository path references require updates."
            )
            reason = (
                f"Move to {suggested_path}: this is a cleanly classifiable loose root {role} file, "
                f"the repository has one established {suggested_directory}/ destination, and no "
                f"destination collision exists.{reference_note}"
            )
        findings.append({
            "id": stable_id(relative, role, candidate_directories, digest, state, references),
            "surface": "file-organization",
            "path": relative,
            "role": role,
            "git_state": state,
            "bytes": len(data),
            "sha256": digest,
            "candidate_directories": candidate_directories,
            "suggested_destination": suggested_path,
            "destination_collision": collision,
            "references": references,
            "signal": "loose-root-file",
            "confidence": "strong" if classification == "move-recommended" else "moderate",
            "classification": classification,
            "proposed_action": proposed_action,
            "reason": reason,
        })

    if truncated:
        coverage_gaps.append({
            "code": "file-organization-budget-exhausted",
            "message": "The loose-root file scan exceeded the configured file or byte budget.",
        })
    if unreadable:
        coverage_gaps.append({
            "code": "file-organization-unreadable",
            "message": "One or more loose root files could not be fingerprinted safely.",
            "count": len(unreadable),
            "sample": unreadable[:10],
            "sample_truncated": len(unreadable) > 10,
        })
    findings.sort(key=lambda item: item["path"].casefold())
    return {
        "schema": OUTPUT_SCHEMA,
        "mode": "analyze-file-organization",
        "mutations_performed": False,
        "apply_supported": False,
        "workspace": str(root),
        "scope_type": scope_type,
        "findings": findings,
        "coverage_gaps": coverage_gaps,
        "warnings": warnings,
        "summary": {
            "root_files_seen": len(root_files),
            "eligible_files_scanned": scanned_files,
            "eligible_bytes_scanned": scanned_bytes,
            "finding_count": len(findings),
            "move_recommended_count": sum(
                item["classification"] == "move-recommended" for item in findings
            ),
            "kept_count": sum(item["classification"] == "keep" for item in findings),
            "scan_truncated": truncated,
            "unreadable_files": len(unreadable),
            "coverage_complete": not coverage_gaps and not warnings,
        },
        "review_required": bool(
            any(item["classification"] == "move-recommended" for item in findings)
            or coverage_gaps or warnings
        ),
        "proposed_authorization_set": [],
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Clean Up file-organization analysis", "",
        f"Workspace: `{markdown_cell(result['workspace'])}`",
        "Mutations: `none`", "Apply supported: `no`", "",
        "| ID | Loose file | Decision | Git state | Destination |",
        "|---|---|---|---|---|",
    ]
    for item in result["findings"]:
        destination = item["suggested_destination"] or "review destination options"
        lines.append(
            f"| `{item['id']}` | `{markdown_cell(item['path'])}` | `{item['classification']}` | "
            f"`{item['git_state']}` | `{markdown_cell(destination)}` |"
        )
    if not result["findings"]:
        lines.append("| - | - | - | - | No evidence-backed file-organization opportunities found. |")
    if result["coverage_gaps"]:
        lines.extend(["", "Coverage gaps:"])
        lines.extend(
            f"- {markdown_cell(item['code'])}: {markdown_cell(item['message'])}"
            for item in result["coverage_gaps"]
        )
    lines.extend([
        "", "File-organization analysis made no filesystem or Git mutations.",
        "FO IDs record automatic move-or-keep decisions but cannot authorize path or Git Apply.",
        "A recommended move requires only an explicit edit request and relevant validation; the user is not asked to decide organization intent.",
    ])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Folder, workspace, or exact Git worktree root")
    parser.add_argument("--max-files", type=int, default=1000, help="Bound loose root files read")
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024, help="Bound loose root bytes read")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze_file_organization(Path(args.workspace), args.max_files, args.max_bytes)
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
