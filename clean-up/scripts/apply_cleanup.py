#!/usr/bin/env python3
"""Apply explicitly approved Clean Up v2 whole-path candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from inspect_repository import (
    fingerprint_path,
    fingerprint_token,
    has_link_ancestor,
    inspect,
    is_junction,
    is_reserved_path,
    lexical_path,
    normalize_relative_path,
    target_outside_workspace,
)


APPLY_SCHEMA = "clean-up-apply/v2"
REPORT_SCHEMA = "clean-up-report/v2"
ID_PATTERN = re.compile(r"^PC-[A-F0-9]{12}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".clean-up-", suffix=".tmp", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def parse_validation_commands(values: list[str]) -> tuple[list[list[str]], list[dict[str, str]]]:
    commands: list[list[str]] = []
    refusals: list[dict[str, str]] = []
    for index, value in enumerate(values, start=1):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            refusals.append({"code": "validation-command-invalid", "message": f"Command {index}: {exc}"})
            continue
        if not isinstance(parsed, list) or not parsed or not all(
            isinstance(part, str) and part and "\0" not in part for part in parsed
        ):
            refusals.append({
                "code": "validation-command-invalid",
                "message": f"Command {index} must be a non-empty JSON array of strings",
            })
            continue
        commands.append(parsed)
    if not values:
        refusals.append({"code": "validation-required", "message": "At least one validation command is required"})
    return commands, refusals


def run_validation(root: Path, commands: list[list[str]], phase: str, timeout: int) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    for command in commands:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command, cwd=root, shell=False, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, errors="replace", timeout=timeout, check=False,
            )
            result = {
                "phase": phase, "command": command,
                "outcome": "passed" if completed.returncode == 0 else "failed",
                "exit_code": completed.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        except subprocess.TimeoutExpired:
            result = {
                "phase": phase, "command": command, "outcome": "timeout", "exit_code": None,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        except OSError as exc:
            result = {
                "phase": phase, "command": command, "outcome": "error", "exit_code": None,
                "duration_ms": round((time.monotonic() - started) * 1000), "detail": str(exc),
            }
        results.append(result)
        if result["outcome"] != "passed":
            return results, False
    return results, True


def recovery_identity(path: Path) -> tuple[int, int]:
    stat = path.stat(follow_symlinks=False)
    if path.is_symlink() or is_junction(path) or not path.is_dir():
        raise ValueError("Recovery root is not a plain directory")
    return stat.st_dev, stat.st_ino


def verify_recovery_root(path: Path, identity: tuple[int, int]) -> None:
    if recovery_identity(path) != identity:
        raise OSError("Recovery root identity changed during Apply")


def create_recovery_root(workspace: Path, run_key: str) -> tuple[Path, tuple[int, int]]:
    parent = workspace.parent.resolve(strict=True)
    if parent.is_symlink() or is_junction(parent):
        raise ValueError("Workspace parent cannot be a link or junction")
    created = Path(tempfile.mkdtemp(prefix=f".clean-up-{run_key}-", dir=str(parent)))
    try:
        if os.path.commonpath([str(workspace), str(created)]) == str(workspace):
            raise ValueError("Recovery directory resolved inside the workspace")
        if os.stat(workspace).st_dev != os.stat(created).st_dev:
            raise ValueError("Recovery directory is not on the workspace filesystem")
    except BaseException:
        created.rmdir()
        raise
    return created, recovery_identity(created)


def remove_tree_no_follow(path: Path) -> None:
    with os.scandir(path) as iterator:
        children = list(iterator)
    for entry in children:
        child = Path(entry.path)
        if entry.is_symlink() or is_junction(child):
            if child.is_dir() and not child.is_symlink():
                os.rmdir(child)
            else:
                child.unlink()
        elif entry.is_dir(follow_symlinks=False):
            remove_tree_no_follow(child)
        else:
            child.unlink()
    path.rmdir()


def discard_recovery(path: Path, identity: tuple[int, int]) -> tuple[bool, str | None]:
    try:
        verify_recovery_root(path, identity)
        remove_tree_no_follow(path)
        return True, None
    except OSError as exc:
        return False, str(exc)


def top_level_targets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(items, key=lambda item: len(PurePosixPath(item["path"]).parts))
    roots: list[dict[str, Any]] = []
    for item in ordered:
        if any(item["path"].startswith(root["path"] + "/") for root in roots):
            continue
        roots.append(item)
    return roots


def write_recovery_map(root: Path, identity: tuple[int, int], mappings: list[dict[str, Any]]) -> None:
    verify_recovery_root(root, identity)
    atomic_write_json(root / "recovery-map.json", [{
        "original": mapping["relative"], "backup": Path(mapping["backup"]).name,
        "state": mapping["state"], "fingerprint": mapping["fingerprint"],
    } for mapping in mappings])


def quarantine_targets(
    workspace: Path, recovery_root: Path, identity: tuple[int, int],
    roots: list[dict[str, Any]], mappings: list[dict[str, Any]],
) -> None:
    for index, item in enumerate(roots, start=1):
        original, error = lexical_path(workspace, item["path"])
        if error or original is None:
            raise OSError(error or f"Could not resolve {item['path']}")
        if has_link_ancestor(workspace, original) or target_outside_workspace(workspace, original):
            raise OSError(f"Link, junction, or escaping target refused: {item['path']}")
        backup = recovery_root / f"item-{index:04d}"
        mapping = {
            "relative": item["path"], "original": original, "backup": backup,
            "fingerprint": item["current"], "state": "planned",
        }
        mappings.append(mapping)
        write_recovery_map(recovery_root, identity, mappings)
        current = fingerprint_path(workspace, original)
        if fingerprint_token(current) != fingerprint_token(item["current"]):
            raise OSError(f"Approved state became stale before quarantine: {item['path']}")
        os.replace(original, backup)
        mapping["state"] = "quarantined"
        if fingerprint_token(fingerprint_path(workspace, backup)) != fingerprint_token(item["current"]):
            raise OSError(f"Recovery fingerprint mismatch for {item['path']}")
        write_recovery_map(recovery_root, identity, mappings)


def restore_targets(
    workspace: Path, recovery_root: Path, identity: tuple[int, int], mappings: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    try:
        verify_recovery_root(recovery_root, identity)
    except OSError as exc:
        return False, [str(exc)]
    for mapping in reversed(mappings):
        if mapping["state"] != "quarantined":
            continue
        backup, original = Path(mapping["backup"]), Path(mapping["original"])
        if not os.path.lexists(backup):
            errors.append(f"Recovery item missing for {mapping['relative']}")
            continue
        if os.path.lexists(original):
            errors.append(f"Original path reappeared during recovery: {mapping['relative']}")
            continue
        if has_link_ancestor(workspace, original.parent) or target_outside_workspace(workspace, original.parent):
            errors.append(f"Original parent became unsafe during recovery: {mapping['relative']}")
            continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, original)
            if fingerprint_token(fingerprint_path(workspace, original)) != fingerprint_token(mapping["fingerprint"]):
                errors.append(f"Restored fingerprint mismatch: {mapping['relative']}")
            else:
                mapping["state"] = "restored"
        except OSError as exc:
            errors.append(f"Could not restore {mapping['relative']}: {exc}")
    return not errors, errors


def preflight(inspection: dict[str, Any], approved_ids: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    refusals = list(inspection["refusals"])
    if not inspection.get("apply_supported"):
        refusals.append({"code": "inspection-not-applicable", "message": "Inspection is not eligible for Apply"})
    if len(approved_ids) != len(set(approved_ids)):
        refusals.append({"code": "duplicate-approval", "message": "Approved IDs must be unique"})
    for item_id in approved_ids:
        if not ID_PATTERN.fullmatch(item_id):
            refusals.append({"code": "approval-format-invalid", "message": f"Invalid candidate ID: {item_id}"})
    candidates = {
        item["id"]: item for item in inspection["items"]
        if item["classification"] == "candidate" and item["proposed_action"] == "remove-whole-path"
    }
    unknown = sorted(set(approved_ids) - set(candidates))
    if unknown:
        refusals.append({
            "code": "approval-not-current",
            "message": "Approved IDs are stale or not current whole-path candidates: " + ", ".join(unknown),
        })
    selected = [candidates[item_id] for item_id in approved_ids if item_id in candidates]
    for item in selected:
        if is_reserved_path(item["path"]):
            refusals.append({"code": "reserved-target", "message": f"Reserved path cannot be applied: {item['path']}"})
        if item["current"].get("type") in {"symlink", "junction", "link", "other"}:
            refusals.append({"code": "link-target-unsupported", "message": f"Unsupported target: {item['path']}"})
    return selected, refusals


def resolve_report_path(workspace: Path, value: str | None, selected: list[dict[str, Any]]) -> tuple[Path | None, list[dict[str, str]]]:
    if value is None:
        return None, []
    normalized, error = normalize_relative_path(value)
    if error or normalized is None:
        return None, [{"code": "report-path-invalid", "message": error or "Invalid report path"}]
    if not normalized.startswith(".clean-up/reports/") or not normalized.endswith(".json"):
        return None, [{
            "code": "report-path-invalid",
            "message": "Reports must be explicit .json paths under .clean-up/reports/",
        }]
    path, error = lexical_path(workspace, normalized)
    if error or path is None:
        return None, [{"code": "report-path-invalid", "message": error or "Invalid report path"}]
    if os.path.lexists(path):
        return None, [{"code": "report-exists", "message": f"Report path already exists: {normalized}"}]
    for item in selected:
        if normalized == item["path"] or normalized.startswith(item["path"] + "/"):
            return None, [{"code": "report-target-overlap", "message": "Report overlaps a cleanup target"}]
    cursor = path.parent
    while cursor != workspace and not cursor.exists():
        cursor = cursor.parent
    if cursor.is_symlink() or is_junction(cursor) or target_outside_workspace(workspace, cursor):
        return None, [{"code": "report-parent-unsafe", "message": "Report parent is a link, junction, or escape"}]
    return path, []


def initial_result(args: argparse.Namespace, run_key: str) -> dict[str, Any]:
    return {
        "schema": APPLY_SCHEMA, "mode": "apply", "run_key": run_key, "status": "starting",
        "started": utc_now(), "completed": None, "scope": {"paths": list(args.path), "git_base": args.git_base},
        "approved_ids": list(args.approve), "actions": [], "validation": [],
        "cleanup_mutations_performed": False, "report": args.report, "refusals": [],
        "recovery": {"status": "not-created", "location": None, "detail": None},
    }


def report_document(result: dict[str, Any]) -> dict[str, Any]:
    return {"schema": REPORT_SCHEMA, **{key: value for key, value in result.items() if key != "schema"}}


def try_write_report(report: Path | None, result: dict[str, Any]) -> bool:
    if report is None:
        return True
    try:
        atomic_write_json(report, report_document(result))
        return True
    except OSError as exc:
        result["refusals"].append({"code": "report-write-failed", "message": str(exc)})
        return False


def apply_cleanup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_key = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    result = initial_result(args, run_key)
    workspace = Path(args.workspace).resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("Workspace root must be a directory")
    if args.validation_timeout <= 0:
        raise ValueError("Validation timeout must be positive")

    commands, command_refusals = parse_validation_commands(args.validate_command)
    inspection = inspect(workspace, list(args.path), args.git_base)
    selected, target_refusals = preflight(inspection, list(args.approve))
    report, report_refusals = resolve_report_path(workspace, args.report, selected)
    result["refusals"].extend(command_refusals + target_refusals + report_refusals)
    if result["refusals"]:
        result["status"] = "refused"
        result["completed"] = utc_now()
        try_write_report(report, result)
        return result, 2

    baseline_results, baseline_ok = run_validation(workspace, commands, "baseline", args.validation_timeout)
    result["validation"].extend(baseline_results)
    if not baseline_ok:
        result["status"] = "refused"
        result["refusals"].append({"code": "baseline-validation-failed", "message": "Baseline validation did not pass"})
        result["completed"] = utc_now()
        try_write_report(report, result)
        return result, 2

    refreshed = inspect(workspace, list(args.path), args.git_base)
    refreshed_selected, refreshed_refusals = preflight(refreshed, list(args.approve))
    if refreshed_refusals or [item["id"] for item in refreshed_selected] != [item["id"] for item in selected]:
        result["status"] = "refused"
        result["refusals"].extend(refreshed_refusals or [{
            "code": "approval-not-current", "message": "Repository state changed during baseline validation",
        }])
        result["completed"] = utc_now()
        try_write_report(report, result)
        return result, 2
    selected = refreshed_selected

    recovery_root: Path | None = None
    recovery_identity_value: tuple[int, int] | None = None
    mappings: list[dict[str, Any]] = []
    try:
        recovery_root, recovery_identity_value = create_recovery_root(workspace, run_key)
        result["recovery"] = {"status": "available", "location": str(recovery_root), "detail": None}
        quarantine_targets(
            workspace, recovery_root, recovery_identity_value, top_level_targets(selected), mappings,
        )
        result["cleanup_mutations_performed"] = True
        result["actions"] = [{
            "id": item["id"], "path": item["path"], "outcome": "removed",
            "detail": "Moved to same-filesystem quarantine pending validation.",
        } for item in selected]
        post_results, post_ok = run_validation(workspace, commands, "after-cleanup", args.validation_timeout)
        result["validation"].extend(post_results)
        if not post_ok:
            raise RuntimeError("After-cleanup validation did not pass")
        reappeared = [
            mapping["relative"] for mapping in mappings
            if os.path.lexists(mapping["original"])
        ]
        if reappeared:
            raise RuntimeError(
                "Cleanup target reappeared during after-cleanup validation: " + ", ".join(reappeared)
            )
        post_state = inspect(workspace, list(args.path), args.git_base)
        if (
            post_state["git"].get("head") != refreshed["git"].get("head")
            or post_state["git"].get("base_commit") != refreshed["git"].get("base_commit")
        ):
            raise RuntimeError("HEAD or the explicit Git base changed during after-cleanup validation")
        result["status"] = "completed"
        result["completed"] = utc_now()
        if not try_write_report(report, result):
            raise RuntimeError("Requested cleanup report could not be written")
    except BaseException as exc:
        result["refusals"].append({"code": "apply-failed", "message": str(exc)})
        if recovery_root is not None and recovery_identity_value is not None:
            restored, errors = restore_targets(
                workspace, recovery_root, recovery_identity_value, mappings,
            )
            if restored:
                discarded, discard_error = discard_recovery(recovery_root, recovery_identity_value)
                result["status"] = "restored"
                result["recovery"] = {
                    "status": "discarded" if discarded else "retained",
                    "location": None if discarded else str(recovery_root), "detail": discard_error,
                }
                for action in result["actions"]:
                    action["outcome"] = "restored"
                exit_code = 2
            else:
                result["status"] = "recovery-required"
                result["recovery"] = {
                    "status": "retained", "location": str(recovery_root), "detail": "; ".join(errors),
                }
                exit_code = 3
        else:
            result["status"] = "refused"
            exit_code = 2
        result["completed"] = utc_now()
        if report is not None and not report.exists():
            try_write_report(report, result)
        return result, exit_code

    assert recovery_root is not None and recovery_identity_value is not None
    discarded, discard_error = discard_recovery(recovery_root, recovery_identity_value)
    if discarded:
        result["recovery"] = {
            "status": "discarded", "location": None,
            "detail": "Recovery snapshot removed after successful validation.",
        }
    else:
        result["status"] = "completed-recovery-retained"
        result["recovery"] = {"status": "retained", "location": str(recovery_root), "detail": discard_error}
    result["completed"] = utc_now()
    if report is not None:
        try:
            atomic_write_json(report, report_document(result))
        except OSError as exc:
            result["status"] = "completed-report-update-failed"
            result["refusals"].append({"code": "report-update-failed", "message": str(exc)})
            return result, 3
    return result, 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Workspace Git root")
    parser.add_argument("--path", action="append", required=True, help="Frozen inspected path; repeat as needed")
    parser.add_argument("--git-base", help="Same optional Git base used during inspection")
    parser.add_argument("--approve", action="append", required=True, help="Approved PC candidate ID")
    parser.add_argument("--validate-command", action="append", required=True, help="Validation command as a JSON argument array")
    parser.add_argument("--validation-timeout", type=int, default=600)
    parser.add_argument("--report", help="Optional non-existing .clean-up/reports/*.json path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result, exit_code = apply_cleanup(args)
    except (OSError, ValueError) as exc:
        result = {"schema": APPLY_SCHEMA, "mode": "apply", "status": "failed", "error": str(exc)}
        exit_code = 3
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
