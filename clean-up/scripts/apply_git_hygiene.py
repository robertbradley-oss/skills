#!/usr/bin/env python3
"""Apply explicitly approved Clean Up Git hygiene candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inspect_git_hygiene import ID_PATTERN, inspect_git_hygiene
from inspect_repository import decode_path, run_git


OUTPUT_SCHEMA = "clean-up-git-apply/v1"
ZERO_OID = "0" * 40


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_failure(root: Path, arguments: list[str]) -> str | None:
    completed = run_git(root, arguments)
    if completed.returncode == 0:
        return None
    return decode_path(completed.stderr).strip() or f"git {' '.join(arguments)} failed"


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    for arguments in (
        ["show-ref", "--head"],
        ["worktree", "list", "--porcelain"],
        ["fsck", "--connectivity-only", "--no-dangling"],
    ):
        error = git_failure(root, arguments)
        if error:
            errors.append(error)
    return errors


def candidate_contract(item: dict[str, Any]) -> str | None:
    evidence = item.get("evidence", {})
    if item.get("surface") == "branch" and item.get("candidate_kind") == "merged-local-branch":
        if not (
            item.get("proposed_action") == "delete-local-branch"
            and evidence.get("exists") is True
            and isinstance(evidence.get("tip"), str)
            and evidence.get("fully_merged") is True
            and evidence.get("unique_commits") == 0
            and evidence.get("protected") is False
            and not evidence.get("checked_out_at")
            and isinstance(evidence.get("integration"), dict)
            and isinstance(evidence["integration"].get("commit"), str)
        ):
            return f"Merged-branch evidence is incomplete for {item.get('target')}"
        return None
    if item.get("surface") == "worktree" and item.get("candidate_kind") == "clean-linked-worktree":
        if not (
            item.get("proposed_action") == "remove-linked-worktree"
            and evidence.get("registered") is True
            and evidence.get("current") is False
            and evidence.get("plain_directory") is True
            and evidence.get("branch_recovery") is True
            and isinstance(evidence.get("branch"), str)
            and isinstance(evidence.get("head"), str)
            and not evidence.get("locked")
            and not evidence.get("prunable")
            and evidence.get("status", {}).get("count") == 0
            and evidence.get("ignored", {}).get("count") == 0
            and evidence.get("submodules", {}).get("count") == 0
            and not evidence.get("errors")
            and not evidence.get("worktree_config", {}).get("exists")
            and not evidence.get("sparse_checkout", {}).get("exists")
        ):
            return f"Clean-worktree evidence is incomplete for {item.get('target')}"
        return None
    return f"Unsupported candidate contract for {item.get('target')}"


def preflight(inspection: dict[str, Any], approved_ids: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    refusals = list(inspection.get("refusals", []))
    if not approved_ids:
        refusals.append({"code": "approval-required", "message": "At least one exact GC candidate ID is required"})
    if len(approved_ids) != len(set(approved_ids)):
        refusals.append({"code": "duplicate-approval", "message": "Approved IDs must be unique"})
    for item_id in approved_ids:
        if not ID_PATTERN.fullmatch(item_id):
            refusals.append({"code": "approval-format-invalid", "message": f"Invalid Git cleanup candidate ID: {item_id}"})
    candidates = {
        item["id"]: item for item in inspection.get("items", [])
        if item.get("classification") == "candidate"
    }
    unknown = sorted(set(approved_ids) - set(candidates))
    if unknown:
        refusals.append({
            "code": "approval-not-current",
            "message": "Approved IDs are stale or not current Git cleanup candidates: " + ", ".join(unknown),
        })
    selected = [candidates[item_id] for item_id in approved_ids if item_id in candidates]
    for item in selected:
        error = candidate_contract(item)
        if error:
            refusals.append({"code": "candidate-contract-invalid", "message": error})
    return selected, refusals


def backup_ref(run_key: str, item_id: str) -> str:
    safe_run = re.sub(r"[^A-Za-z0-9-]", "-", run_key)
    return f"refs/clean-up-recovery/{safe_run}/{item_id.lower()}"


def apply_git_hygiene(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_key = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    root = Path(args.workspace).resolve(strict=True)
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "mode": "apply-git-hygiene",
        "run_key": run_key,
        "started": utc_now(),
        "completed": None,
        "status": "starting",
        "scope": {"branches": list(args.branch), "worktrees": list(args.worktree)},
        "approved_ids": list(args.approve),
        "actions": [],
        "validation": [],
        "git_mutations_performed": False,
        "refusals": [],
        "recovery": {"status": "not-created", "detail": None},
    }

    inspection = inspect_git_hygiene(root, list(args.branch), list(args.worktree))
    selected, refusals = preflight(inspection, list(args.approve))
    result["refusals"].extend(refusals)
    if refusals:
        result["status"] = "refused"
        result["completed"] = utc_now()
        return result, 2

    baseline_errors = validate_repository(root)
    result["validation"].append({"phase": "baseline", "outcome": "passed" if not baseline_errors else "failed", "errors": baseline_errors})
    if baseline_errors:
        result["status"] = "refused"
        result["refusals"].append({"code": "baseline-validation-failed", "message": "; ".join(baseline_errors)})
        result["completed"] = utc_now()
        return result, 2

    refreshed = inspect_git_hygiene(root, list(args.branch), list(args.worktree))
    refreshed_selected, refreshed_refusals = preflight(refreshed, list(args.approve))
    if refreshed_refusals or [item["id"] for item in refreshed_selected] != [item["id"] for item in selected]:
        result["status"] = "refused"
        result["refusals"].extend(refreshed_refusals or [{
            "code": "approval-not-current", "message": "Git state changed during baseline validation",
        }])
        result["completed"] = utc_now()
        return result, 2
    selected = refreshed_selected

    branch_recovery: list[dict[str, str]] = []
    worktree_recovery: list[dict[str, str]] = []
    try:
        for item in selected:
            if item["surface"] == "worktree":
                original = Path(item["target"])
                quarantine = original.parent / f".{original.name}.clean-up-{secrets.token_hex(6)}"
                if os.path.lexists(quarantine):
                    raise RuntimeError(f"Recovery worktree path already exists: {quarantine}")
                error = git_failure(root, ["worktree", "move", str(original), str(quarantine)])
                if error:
                    raise RuntimeError(error)
                worktree_recovery.append({
                    "id": item["id"], "original": str(original), "quarantine": str(quarantine),
                    "branch": item["evidence"]["branch"], "head": item["evidence"]["head"], "state": "quarantined",
                })
                result["actions"].append({
                    "id": item["id"], "surface": "worktree", "target": item["target"],
                    "outcome": "quarantined", "detail": "Moved as a registered worktree pending validation.",
                })
            else:
                recovery_ref = backup_ref(run_key, item["id"])
                tip = item["evidence"]["tip"]
                branch_ref = item["evidence"]["ref"]
                error = git_failure(root, ["update-ref", recovery_ref, tip, ZERO_OID])
                if error:
                    raise RuntimeError(error)
                branch_recovery.append({
                    "id": item["id"], "branch_ref": branch_ref, "tip": tip,
                    "recovery_ref": recovery_ref, "state": "backed-up",
                })
                error = git_failure(root, ["update-ref", "-d", branch_ref, tip])
                if error:
                    raise RuntimeError(error)
                branch_recovery[-1]["state"] = "deleted"
                result["actions"].append({
                    "id": item["id"], "surface": "branch", "target": item["target"],
                    "outcome": "quarantined", "detail": "Deleted behind an exact temporary recovery ref pending validation.",
                })
        result["git_mutations_performed"] = bool(selected)
        result["recovery"] = {"status": "available", "detail": "Exact branch refs and registered worktrees remain recoverable pending validation."}

        post_errors = validate_repository(root)
        result["validation"].append({"phase": "after-quarantine", "outcome": "passed" if not post_errors else "failed", "errors": post_errors})
        if post_errors:
            raise RuntimeError("After-quarantine validation failed: " + "; ".join(post_errors))

        for mapping in worktree_recovery:
            error = git_failure(root, ["worktree", "remove", mapping["quarantine"]])
            if error:
                raise RuntimeError(error)
            mapping["state"] = "removed"
        final_errors = validate_repository(root)
        result["validation"].append({"phase": "after-cleanup", "outcome": "passed" if not final_errors else "failed", "errors": final_errors})
        if final_errors:
            raise RuntimeError("After-cleanup validation failed: " + "; ".join(final_errors))

        for mapping in branch_recovery:
            error = git_failure(root, ["update-ref", "-d", mapping["recovery_ref"], mapping["tip"]])
            if error:
                raise RuntimeError(error)
            mapping["state"] = "discarded"
        discard_errors = validate_repository(root)
        result["validation"].append({
            "phase": "after-recovery-discard",
            "outcome": "passed" if not discard_errors else "failed",
            "errors": discard_errors,
        })
        if discard_errors:
            raise RuntimeError("After-recovery-discard validation failed: " + "; ".join(discard_errors))
        result["status"] = "completed"
        result["recovery"] = {"status": "discarded", "detail": "Temporary recovery state was discarded after successful validation."}
        for action in result["actions"]:
            action["outcome"] = "removed"
        result["completed"] = utc_now()
        return result, 0
    except BaseException as exc:
        recovery_errors: list[str] = []
        result["refusals"].append({"code": "apply-failed", "message": str(exc)})
        for mapping in reversed(worktree_recovery):
            if mapping["state"] == "quarantined":
                error = git_failure(root, ["worktree", "move", mapping["quarantine"], mapping["original"]])
            elif mapping["state"] == "removed":
                error = git_failure(root, ["worktree", "add", mapping["original"], mapping["branch"]])
            else:
                error = None
            if error:
                recovery_errors.append(error)
            else:
                mapping["state"] = "restored"
        for mapping in reversed(branch_recovery):
            if mapping["state"] in {"deleted", "discarded"}:
                error = git_failure(root, ["update-ref", mapping["branch_ref"], mapping["tip"], ZERO_OID])
                if error:
                    recovery_errors.append(error)
                else:
                    mapping["state"] = "restored"
            cleanup_error = git_failure(root, ["update-ref", "-d", mapping["recovery_ref"], mapping["tip"]])
            if cleanup_error:
                recovery_errors.append(cleanup_error)
        if recovery_errors:
            result["status"] = "recovery-required"
            result["recovery"] = {"status": "retained", "detail": "; ".join(recovery_errors)}
            exit_code = 3
        else:
            result["status"] = "restored"
            result["recovery"] = {"status": "discarded", "detail": "All Git cleanup mutations were restored."}
            for action in result["actions"]:
                action["outcome"] = "restored"
            exit_code = 2
        result["completed"] = utc_now()
        return result, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Exact Git worktree root")
    parser.add_argument("--branch", action="append", default=[], help="Frozen exact local branch name")
    parser.add_argument("--worktree", action="append", default=[], help="Frozen exact linked worktree path")
    parser.add_argument("--approve", action="append", required=True, help="Approved GC candidate ID")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.branch and not args.worktree:
        result = {"schema": OUTPUT_SCHEMA, "mode": "apply-git-hygiene", "status": "failed", "error": "At least one exact branch or worktree is required"}
        exit_code = 3
    else:
        try:
            result, exit_code = apply_git_hygiene(args)
        except (OSError, ValueError) as exc:
            result = {"schema": OUTPUT_SCHEMA, "mode": "apply-git-hygiene", "status": "failed", "error": str(exc)}
            exit_code = 3
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
