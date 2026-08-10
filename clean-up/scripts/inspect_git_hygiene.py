#!/usr/bin/env python3
"""Inspect exact local branches and linked worktrees for safe Git cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from discover_repository import PROTECTED_BRANCHES, markdown_cell, parse_worktrees
from inspect_repository import decode_path, is_junction, run_git


OUTPUT_SCHEMA = "clean-up-git-inspection/v1"
ID_PATTERN = re.compile(r"^GC-[A-F0-9]{12}$")


def stable_id(surface: str, target: str, candidate_kind: str | None, action: str, evidence: dict[str, Any]) -> str:
    material = json.dumps(
        {
            "schema": OUTPUT_SCHEMA,
            "surface": surface,
            "target": target,
            "candidate_kind": candidate_kind,
            "action": action,
            "evidence": evidence,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8", errors="surrogateescape")
    return "GC-" + hashlib.sha256(material).hexdigest()[:12].upper()


def git_text(root: Path, arguments: list[str]) -> tuple[str | None, str | None]:
    completed = run_git(root, arguments)
    if completed.returncode != 0:
        detail = decode_path(completed.stderr).strip() or f"git {' '.join(arguments)} failed"
        return None, detail
    return decode_path(completed.stdout).strip(), None


def git_bytes(root: Path, arguments: list[str]) -> tuple[bytes | None, str | None]:
    completed = run_git(root, arguments)
    if completed.returncode != 0:
        detail = decode_path(completed.stderr).strip() or f"git {' '.join(arguments)} failed"
        return None, detail
    return completed.stdout, None


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve(strict=False))) == os.path.normcase(str(right.resolve(strict=False)))


def repository_root(workspace: Path) -> Path:
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Workspace root must be a directory")
    value, error = git_text(root, ["rev-parse", "--show-toplevel"])
    if error or value is None:
        raise ValueError(error or "Workspace is not a Git repository")
    reported = Path(value).resolve(strict=True)
    if not same_path(root, reported):
        raise ValueError("Workspace must be the exact Git worktree root")
    return root


def integration_ref(root: Path) -> dict[str, str] | None:
    symbolic, _ = git_text(root, ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    candidates = [symbolic] if symbolic else []
    candidates.extend(f"refs/heads/{name}" for name in ("main", "master", "trunk", "develop", "development"))
    seen: set[str] = set()
    for name in candidates:
        if not name or name in seen:
            continue
        seen.add(name)
        commit, error = git_text(root, ["rev-parse", "--verify", f"{name}^{{commit}}"])
        if not error and commit:
            return {"ref": name, "commit": commit}
    return None


def worktree_inventory(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    worktrees, error = parse_worktrees(root)
    if error:
        return [], [{"code": "worktree-scan-failed", "message": error}]
    return worktrees, []


def checked_out_branches(worktrees: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in worktrees:
        branch = item.get("branch")
        path = item.get("worktree")
        if isinstance(branch, str) and branch.startswith("refs/heads/") and isinstance(path, str):
            result[branch.removeprefix("refs/heads/")] = path
    return result


def branch_tracking(root: Path, name: str) -> dict[str, str]:
    value, error = git_text(root, [
        "for-each-ref", "--format=%(upstream:short)|%(upstream:track)", f"refs/heads/{name}",
    ])
    if error or value is None:
        return {"upstream": "", "track": ""}
    upstream, _, track = value.partition("|")
    return {"upstream": upstream, "track": track}


def inspect_branch(
    root: Path, name: str, worktrees: list[dict[str, Any]], integration: dict[str, str] | None,
) -> dict[str, Any]:
    tip, error = git_text(root, ["rev-parse", "--verify", f"refs/heads/{name}^{{commit}}"])
    if error or not tip:
        evidence = {"exists": False, "error": error or "Local branch does not exist"}
        return {
            "id": stable_id("branch", name, None, "none", evidence),
            "surface": "branch", "target": name, "classification": "review",
            "candidate_kind": None, "proposed_action": "none", "reason": "The exact local branch does not exist.",
            "evidence": evidence,
        }

    checked_out = checked_out_branches(worktrees).get(name)
    protected = name in PROTECTED_BRANCHES
    merged = False
    unique_commits: int | None = None
    if integration:
        ancestor = run_git(root, ["merge-base", "--is-ancestor", tip, integration["commit"]])
        merged = ancestor.returncode == 0
        count, count_error = git_text(root, ["rev-list", "--count", f"{integration['commit']}..{tip}"])
        if not count_error and count is not None and count.isdigit():
            unique_commits = int(count)
    tracking = branch_tracking(root, name)
    evidence: dict[str, Any] = {
        "exists": True,
        "ref": f"refs/heads/{name}",
        "tip": tip,
        "protected": protected,
        "checked_out_at": checked_out,
        "integration": integration,
        "fully_merged": merged,
        "unique_commits": unique_commits,
        **tracking,
    }
    candidate = bool(integration and merged and unique_commits == 0 and not protected and not checked_out)
    if candidate:
        reason = f"The local branch is fully contained in {integration['ref']}, has no unique commits, and is not checked out."
        candidate_kind = "merged-local-branch"
        action = "delete-local-branch"
    elif protected:
        reason = "Protected integration branches are never cleanup candidates."
        candidate_kind = None
        action = "none"
    elif checked_out:
        reason = f"The branch is checked out in linked worktree {checked_out}; review or remove that worktree first."
        candidate_kind = None
        action = "none"
    elif not integration:
        reason = "No trusted local or origin default integration ref could be resolved."
        candidate_kind = None
        action = "none"
    elif not merged or unique_commits != 0:
        reason = "The branch is not fully contained in the integration ref and may contain unique work."
        candidate_kind = None
        action = "none"
    else:
        reason = "Current evidence does not prove that deleting this branch is safe."
        candidate_kind = None
        action = "none"
    return {
        "id": stable_id("branch", name, candidate_kind, action, evidence),
        "surface": "branch", "target": name,
        "classification": "candidate" if candidate else "review",
        "candidate_kind": candidate_kind, "proposed_action": action,
        "reason": reason, "evidence": evidence,
    }


def nul_values(value: bytes) -> list[str]:
    return [decode_path(item) for item in value.split(b"\0") if item]


def record_summary(values: list[str], raw: bytes | None = None, sample_limit: int = 10) -> dict[str, Any]:
    material = raw if raw is not None else "\0".join(values).encode("utf-8", errors="surrogateescape")
    return {
        "count": len(values),
        "sha256": hashlib.sha256(material).hexdigest(),
        "sample": values[:sample_limit],
        "sample_truncated": len(values) > sample_limit,
    }


def metadata_file(root: Path, worktree: Path, name: str) -> dict[str, Any]:
    value, error = git_text(root, ["-C", str(worktree), "rev-parse", "--git-path", name])
    if error or not value:
        return {"path": None, "exists": False, "error": error}
    path = Path(value)
    if not path.is_absolute():
        path = worktree / path
    try:
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
    except OSError as exc:
        return {"path": str(path), "exists": False, "error": str(exc)}
    return {"path": str(path), "exists": exists, "size": size}


def inspect_worktree(root: Path, target: str, worktrees: list[dict[str, Any]]) -> dict[str, Any]:
    requested = Path(target).resolve(strict=False)
    record = next(
        (item for item in worktrees if isinstance(item.get("worktree"), str) and same_path(Path(item["worktree"]), requested)),
        None,
    )
    if record is None:
        evidence = {"registered": False}
        return {
            "id": stable_id("worktree", str(requested), None, "none", evidence),
            "surface": "worktree", "target": str(requested), "classification": "review",
            "candidate_kind": None, "proposed_action": "none",
            "reason": "The exact path is not a currently registered linked worktree.", "evidence": evidence,
        }

    exact_target = str(Path(str(record["worktree"])).resolve(strict=False))
    current = same_path(requested, root)
    exists = requested.exists()
    plain_directory = bool(exists and requested.is_dir() and not requested.is_symlink() and not is_junction(requested))
    branch_ref = record.get("branch") if isinstance(record.get("branch"), str) else None
    branch = branch_ref.removeprefix("refs/heads/") if branch_ref and branch_ref.startswith("refs/heads/") else None
    status_bytes, status_error = git_bytes(root, ["-C", str(requested), "status", "--porcelain=v2", "-z", "--untracked-files=all"]) if plain_directory else (None, None)
    ignored_bytes, ignored_error = git_bytes(root, ["-C", str(requested), "ls-files", "--others", "--ignored", "--exclude-standard", "-z"]) if plain_directory else (None, None)
    stage_bytes, stage_error = git_bytes(root, ["-C", str(requested), "ls-files", "--stage", "-z"]) if plain_directory else (None, None)
    status_values = nul_values(status_bytes or b"")
    ignored_values = nul_values(ignored_bytes or b"")
    submodule_values = [value for value in nul_values(stage_bytes or b"") if value.startswith("160000 ")]
    status = record_summary(status_values, status_bytes or b"")
    ignored = record_summary(ignored_values, ignored_bytes or b"")
    submodules = record_summary(submodule_values)
    config = metadata_file(root, requested, "config.worktree") if plain_directory else {"exists": False}
    sparse = metadata_file(root, requested, "info/sparse-checkout") if plain_directory else {"exists": False}
    head = str(record.get("HEAD") or "")
    branch_tip, branch_error = git_text(root, ["rev-parse", "--verify", f"{branch_ref}^{{commit}}"] ) if branch_ref else (None, None)
    branch_recovery = bool(branch and branch_tip and not branch_error and branch_tip == head)
    errors = list(dict.fromkeys(
        value for value in (status_error, ignored_error, stage_error, config.get("error"), sparse.get("error"))
        if value
    ))
    evidence: dict[str, Any] = {
        "registered": True,
        "path": exact_target,
        "head": head,
        "branch_ref": branch_ref,
        "branch": branch,
        "branch_tip": branch_tip,
        "branch_recovery": branch_recovery,
        "current": current,
        "exists": exists,
        "plain_directory": plain_directory,
        "locked": record.get("locked", False),
        "prunable": record.get("prunable", False),
        "detached": bool(record.get("detached") or not branch),
        "status": status,
        "ignored": ignored,
        "submodules": submodules,
        "worktree_config": config,
        "sparse_checkout": sparse,
        "errors": errors,
    }
    candidate = bool(
        not errors and not current and plain_directory and not record.get("locked")
        and not record.get("prunable") and branch_recovery
        and status["count"] == 0 and ignored["count"] == 0 and submodules["count"] == 0
        and not config.get("exists") and not sparse.get("exists")
    )
    if candidate:
        reason = "The linked worktree is clean, branch-backed, reproducible, and has no ignored data, submodules, sparse state, or worktree-specific config."
        candidate_kind = "clean-linked-worktree"
        action = "remove-linked-worktree"
    elif current:
        reason = "The active workspace worktree is never a cleanup candidate."
        candidate_kind = None
        action = "none"
    elif record.get("locked"):
        reason = "The linked worktree is locked and must be preserved."
        candidate_kind = None
        action = "none"
    elif not exists or record.get("prunable"):
        reason = "The registered worktree is missing or prunable; broad metadata pruning is not authorized by this exact cleanup contract."
        candidate_kind = None
        action = "none"
    elif not plain_directory:
        reason = "The worktree path is not a plain directory."
        candidate_kind = None
        action = "none"
    elif not branch_recovery:
        reason = "The worktree is detached or its exact HEAD is not recoverable from its local branch."
        candidate_kind = None
        action = "none"
    elif status["count"] or ignored["count"]:
        reason = "The worktree contains changed, untracked, or ignored content and may hold unique local data."
        candidate_kind = None
        action = "none"
    elif submodules["count"] or config.get("exists") or sparse.get("exists"):
        reason = "The worktree has submodule, sparse-checkout, or worktree-specific configuration state that simple recreation may not preserve."
        candidate_kind = None
        action = "none"
    else:
        reason = "Current evidence does not prove that removing this worktree is safe."
        candidate_kind = None
        action = "none"
    return {
        "id": stable_id("worktree", exact_target, candidate_kind, action, evidence),
        "surface": "worktree", "target": exact_target,
        "classification": "candidate" if candidate else "review",
        "candidate_kind": candidate_kind, "proposed_action": action,
        "reason": reason, "evidence": evidence,
    }


def inspect_git_hygiene(workspace: Path, branches: list[str], worktree_paths: list[str]) -> dict[str, Any]:
    root = repository_root(workspace)
    refusals: list[dict[str, str]] = []
    if len(branches) != len(set(branches)):
        refusals.append({"code": "duplicate-branch", "message": "Branch selections must be unique"})
    normalized_worktrees = [os.path.normcase(str(Path(value).resolve(strict=False))) for value in worktree_paths]
    if len(normalized_worktrees) != len(set(normalized_worktrees)):
        refusals.append({"code": "duplicate-worktree", "message": "Worktree selections must be unique"})
    worktrees, inventory_refusals = worktree_inventory(root)
    refusals.extend(inventory_refusals)
    integration = integration_ref(root)
    items = [inspect_branch(root, name, worktrees, integration) for name in branches]
    items.extend(inspect_worktree(root, path, worktrees) for path in worktree_paths)
    candidates = [item["id"] for item in items if item["classification"] == "candidate"]
    return {
        "schema": OUTPUT_SCHEMA,
        "mode": "inspect-git-hygiene",
        "mutations_performed": False,
        "workspace": str(root),
        "integration": integration,
        "scope": {"branches": list(branches), "worktrees": list(worktree_paths)},
        "items": items,
        "proposed_authorization_set": candidates,
        "apply_supported": bool(candidates) and not refusals,
        "refusals": refusals,
        "review_required": True,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Clean Up Git hygiene inspection", "", f"Workspace: `{markdown_cell(result['workspace'])}`",
        "Mutations: `none`", "",
        "| ID | Surface | Exact target | Action | Decision | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for item in result["items"]:
        evidence = item["evidence"]
        if item["surface"] == "branch":
            summary = f"tip {str(evidence.get('tip', 'unknown'))[:12]}; merged {evidence.get('fully_merged', False)}"
        else:
            summary = (
                f"branch {evidence.get('branch') or 'detached'}; "
                f"status {evidence.get('status', {}).get('count', 0)}; "
                f"ignored {evidence.get('ignored', {}).get('count', 0)}"
            )
        lines.append(
            f"| `{item['id']}` | `{item['surface']}` | `{markdown_cell(item['target'])}` | "
            f"`{item['proposed_action']}` | `{item['classification']}` | {markdown_cell(summary)} |"
        )
    if not result["items"]:
        lines.append("| - | - | - | - | - | No exact Git hygiene selections were inspected. |")
    lines.extend([
        "", "Git hygiene inspection made no filesystem or Git mutations.",
        "Discovery PD IDs and path-cleanup PC IDs cannot authorize Git cleanup.",
        "Apply requires separate explicit approval of exact GC IDs and fresh state verification.",
    ])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Exact Git worktree root")
    parser.add_argument("--branch", action="append", default=[], help="Exact local branch name; repeat as needed")
    parser.add_argument("--worktree", action="append", default=[], help="Exact linked worktree path; repeat as needed")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.branch and not args.worktree:
        print(json.dumps({"schema": OUTPUT_SCHEMA, "error": "At least one exact branch or worktree is required"}, indent=2))
        return 1
    try:
        result = inspect_git_hygiene(Path(args.workspace), list(args.branch), list(args.worktree))
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
