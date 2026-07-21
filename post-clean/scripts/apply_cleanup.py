#!/usr/bin/env python3
"""Apply explicitly approved whole-path Post Clean candidates."""

from __future__ import annotations

import argparse
import hashlib
import html
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

from inspect_footprint import (
    clean_cell,
    fingerprint_path,
    fingerprint_token,
    inspect,
    is_junction,
    is_reserved_path,
    lexical_path,
    target_outside_workspace,
)


REPORT_SCHEMA = "post-clean-report/v1"
APPLY_SCHEMA = "post-clean-apply/v1"
ID_PATTERN = re.compile(r"^PC-[A-F0-9]{12}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".post-clean-", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def markdown_cell(value: Any) -> str:
    return (
        html.escape(str(value), quote=False)
        .replace("`", "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "\\|")
    )


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Post Clean Report",
        "",
        f"Schema: `{REPORT_SCHEMA}`",
        f"Run: `{result['run_key']}`",
        f"Status: `{result['status']}`",
        f"Source footprint: `{result.get('source_footprint') or 'unavailable'}`",
        f"Source SHA-256 before: `{result.get('source_sha256_before') or 'unavailable'}`",
        f"Source SHA-256 after: `{result.get('source_sha256_after') or 'unchanged'}`",
        f"Started: `{result['started']}`",
        f"Completed: `{result.get('completed') or 'pending'}`",
        "",
        "## Authorization",
        "",
    ]
    if result["approved_ids"]:
        lines.extend(f"- `{item}`" for item in result["approved_ids"])
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Actions",
            "",
            "| ID | Path | Outcome | Detail |",
            "|---|---|---|---|",
        ]
    )
    for action in result["actions"]:
        lines.append(
            f"| `{markdown_cell(action.get('id', '-'))}` | "
            f"`{markdown_cell(action.get('path', '-'))}` | "
            f"`{markdown_cell(action.get('outcome', '-'))}` | "
            f"{markdown_cell(action.get('detail', ''))} |"
        )
    if not result["actions"]:
        lines.append("| - | - | - | No cleanup action was attempted. |")

    lines.extend(
        [
            "",
            "## Validation",
            "",
            "| Phase | Command | Outcome | Exit | Duration ms |",
            "|---|---|---|---|---|",
        ]
    )
    for validation in result["validation"]:
        command = json.dumps(validation["command"], ensure_ascii=False)
        lines.append(
            f"| `{markdown_cell(validation['phase'])}` | "
            f"`{markdown_cell(command)}` | "
            f"`{markdown_cell(validation['outcome'])}` | "
            f"`{markdown_cell(validation.get('exit_code', '-'))}` | "
            f"`{markdown_cell(validation['duration_ms'])}` |"
        )
    if not result["validation"]:
        lines.append("| - | - | - | - | No validation ran. |")

    lines.extend(
        [
            "",
            "## Recovery",
            "",
            f"- Status: `{result['recovery']['status']}`",
            f"- Location: `{markdown_cell(result['recovery'].get('location') or 'none')}`",
            f"- Detail: {markdown_cell(result['recovery'].get('detail') or 'None.')}",
            "",
            "## Footprint obligations",
            "",
            f"- Matching open removal obligations completed: `{result['obligations_updated']}`",
        ]
    )
    if result["refusals"]:
        lines.extend(["", "## Refusals", ""])
        lines.extend(
            f"- `{markdown_cell(item['code'])}`: {markdown_cell(item['message'])}"
            for item in result["refusals"]
        )
    return "\n".join(lines) + "\n"


def parse_validation_commands(values: list[str]) -> tuple[list[list[str]], list[dict[str, str]]]:
    commands: list[list[str]] = []
    refusals: list[dict[str, str]] = []
    for index, value in enumerate(values, start=1):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            refusals.append(
                {"code": "validation-command-invalid", "message": f"Command {index}: {exc}"}
            )
            continue
        if (
            not isinstance(parsed, list)
            or not parsed
            or not all(isinstance(part, str) and part and "\0" not in part for part in parsed)
        ):
            refusals.append(
                {
                    "code": "validation-command-invalid",
                    "message": f"Command {index} must be a non-empty JSON array of strings",
                }
            )
            continue
        commands.append(parsed)
    return commands, refusals


def run_validation(
    root: Path, commands: list[list[str]], phase: str, timeout: int
) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    passed = True
    for command in commands:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                shell=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
                check=False,
            )
            outcome = "passed" if completed.returncode == 0 else "failed"
            result = {
                "phase": phase,
                "command": command,
                "outcome": outcome,
                "exit_code": completed.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
            if completed.returncode != 0:
                passed = False
        except subprocess.TimeoutExpired:
            result = {
                "phase": phase,
                "command": command,
                "outcome": "timeout",
                "exit_code": None,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
            passed = False
        except OSError as exc:
            result = {
                "phase": phase,
                "command": command,
                "outcome": "error",
                "exit_code": None,
                "duration_ms": round((time.monotonic() - started) * 1000),
                "detail": str(exc),
            }
            passed = False
        results.append(result)
        if not passed:
            break
    return results, passed


def report_path(root: Path, source_footprint: str, run_key: str) -> Path:
    source_key = re.sub(r"[^A-Za-z0-9-]+", "-", Path(source_footprint).stem).strip("-")
    source_key = source_key or "footprint"
    directory = root / ".gameplan" / "cleanups"
    candidate = directory / f"{source_key}-{run_key}.md"
    if candidate.exists():
        raise FileExistsError(f"Cleanup report already exists: {candidate}")
    return candidate


def recovery_identity(path: Path) -> tuple[int, int]:
    stat = path.stat(follow_symlinks=False)
    if path.is_symlink() or is_junction(path) or not path.is_dir():
        raise ValueError("Recovery root is not a plain directory")
    return stat.st_dev, stat.st_ino


def verify_recovery_root(path: Path, identity: tuple[int, int]) -> None:
    if recovery_identity(path) != identity:
        raise OSError("Recovery root identity changed during Apply")


def create_recovery_root(workspace: Path, run_key: str) -> tuple[Path, tuple[int, int]]:
    created = Path(tempfile.mkdtemp(prefix=f"post-clean-{run_key}-"))
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
        if path.exists():
            verify_recovery_root(path, identity)
            remove_tree_no_follow(path)
        return True, None
    except OSError as exc:
        return False, str(exc)


def top_level_targets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(items, key=lambda item: len(PurePosixPath(item["path"]).parts))
    roots: list[dict[str, Any]] = []
    for item in ordered:
        if any(
            item["path"].startswith(root["path"] + "/")
            and root["current"].get("type") == "directory"
            for root in roots
        ):
            continue
        roots.append(item)
    return roots


def write_recovery_map(
    recovery_root: Path,
    identity: tuple[int, int],
    mappings: list[dict[str, Any]],
) -> None:
    verify_recovery_root(recovery_root, identity)
    serialized = []
    for mapping in mappings:
        serialized.append(
            {
                "original": mapping["relative"],
                "backup": Path(mapping["backup"]).name,
                "state": mapping["state"],
                "fingerprint": mapping["fingerprint"],
            }
        )
    atomic_write_json(recovery_root / "recovery-map.json", serialized)


def quarantine_targets(
    workspace: Path,
    recovery_root: Path,
    recovery_identity_value: tuple[int, int],
    roots: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> None:
    for index, item in enumerate(roots, start=1):
        original, error = lexical_path(workspace, item["path"])
        if error or original is None:
            raise OSError(error or f"Could not resolve {item['path']}")
        backup = recovery_root / f"item-{index:04d}"
        mapping = {
            "relative": item["path"],
            "original": original,
            "backup": backup,
            "fingerprint": item["current"],
            "state": "planned",
        }
        mappings.append(mapping)
        write_recovery_map(recovery_root, recovery_identity_value, mappings)
        current = fingerprint_path(workspace, original)
        if fingerprint_token(current) != fingerprint_token(item["current"]):
            raise OSError(f"Approved state became stale before quarantine: {item['path']}")
        os.replace(original, backup)
        mapping["state"] = "quarantined"
        backup_fingerprint = fingerprint_path(workspace, backup)
        if fingerprint_token(backup_fingerprint) != fingerprint_token(item["current"]):
            raise OSError(f"Recovery fingerprint mismatch for {item['path']}")
        write_recovery_map(recovery_root, recovery_identity_value, mappings)


def restore_targets(
    workspace: Path,
    recovery_root: Path,
    recovery_identity_value: tuple[int, int],
    mappings: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    try:
        verify_recovery_root(recovery_root, recovery_identity_value)
    except OSError as exc:
        return False, [str(exc)]
    for mapping in reversed(mappings):
        backup = Path(mapping["backup"])
        original = Path(mapping["original"])
        if mapping["state"] != "quarantined":
            continue
        if not os.path.lexists(backup):
            errors.append(f"Recovery item missing for {mapping['relative']}")
            continue
        if os.path.lexists(original):
            errors.append(f"Original path reappeared during recovery: {mapping['relative']}")
            continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, original)
            restored = fingerprint_path(workspace, original)
            if fingerprint_token(restored) != fingerprint_token(mapping["fingerprint"]):
                errors.append(f"Restored fingerprint mismatch: {mapping['relative']}")
            else:
                mapping["state"] = "restored"
        except OSError as exc:
            errors.append(f"Could not restore {mapping['relative']}: {exc}")
    return not errors, errors


def mark_cleanup_obligations(text: str, successful_paths: set[str]) -> tuple[str, int]:
    lines = text.splitlines()
    in_section = False
    updated = 0
    for index, line in enumerate(lines):
        if line.strip() == "## Cleanup obligations":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.strip().startswith("|"):
            continue
        raw_cells = line.strip().strip("|").split("|")
        if len(raw_cells) != 4:
            continue
        cells = [clean_cell(cell) for cell in raw_cells]
        if cells[0] in successful_paths and cells[1] == "remove" and cells[2] == "open":
            raw_cells[2] = " `done` "
            lines[index] = "|" + "|".join(raw_cells) + "|"
            updated += 1
    suffix = "\n" if text.endswith(("\n", "\r")) else ""
    return "\n".join(lines) + suffix, updated


def preflight(
    inspection: dict[str, Any], approved_ids: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    refusals: list[dict[str, str]] = []
    if inspection["refusals"]:
        refusals.extend(inspection["refusals"])
    if len(approved_ids) != len(set(approved_ids)):
        refusals.append({"code": "duplicate-approval", "message": "Approved IDs must be unique"})
    for item_id in approved_ids:
        if not ID_PATTERN.fullmatch(item_id):
            refusals.append(
                {"code": "approval-format-invalid", "message": f"Invalid candidate ID: {item_id}"}
            )

    candidates = {
        item["id"]: item
        for item in inspection["items"]
        if item["classification"] == "candidate"
        and item["proposed_action"] == "remove-whole-path"
        and item["source"] == "task-item"
    }
    unknown = sorted(set(approved_ids) - set(candidates))
    if unknown:
        refusals.append(
            {
                "code": "approval-not-current",
                "message": "Approved IDs are stale or not current whole-path candidates: "
                + ", ".join(unknown),
            }
        )

    selected = [candidates[item_id] for item_id in approved_ids if item_id in candidates]
    selected_ids = {item["id"] for item in selected}
    candidate_by_path = {item["path"]: item for item in candidates.values()}

    for item in selected:
        path = item["path"]
        if is_reserved_path(path) or path == inspection["source"].get("path"):
            refusals.append(
                {"code": "reserved-target", "message": f"Reserved path cannot be applied: {path}"}
            )
        if item["current"].get("type") in {"symlink", "junction"}:
            refusals.append(
                {"code": "link-target-unsupported", "message": f"Link cleanup is unsupported: {path}"}
            )
        if item["current"].get("type") == "directory":
            missing = []
            for entry in item["current"].get("entries", []):
                descendant = path + "/" + entry.get("path", "")
                child = candidate_by_path.get(descendant)
                if child is None or child["id"] not in selected_ids:
                    missing.append(descendant)
            if missing:
                refusals.append(
                    {
                        "code": "directory-authorization-incomplete",
                        "message": f"Directory {path} lacks approved candidate IDs for: "
                        + ", ".join(sorted(missing)),
                    }
                )
    return selected, refusals


def initial_result(run_key: str, approved_ids: list[str]) -> dict[str, Any]:
    return {
        "schema": APPLY_SCHEMA,
        "mode": "apply",
        "run_key": run_key,
        "status": "starting",
        "started": utc_now(),
        "completed": None,
        "source_footprint": None,
        "source_sha256_before": None,
        "source_sha256_after": None,
        "approved_ids": approved_ids,
        "actions": [],
        "validation": [],
        "obligations_updated": 0,
        "cleanup_mutations_performed": False,
        "report": None,
        "refusals": [],
        "recovery": {"status": "not-created", "location": None, "detail": None},
    }


def apply_cleanup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_key = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    approved_ids = list(args.approve)
    result = initial_result(run_key, approved_ids)
    workspace = Path(args.workspace).resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("Workspace root must be a directory")
    if args.validation_timeout <= 0:
        raise ValueError("Validation timeout must be positive")

    commands, command_refusals = parse_validation_commands(args.validate_command)
    inspection = inspect(workspace, args.footprint)
    result["source_footprint"] = inspection["source"].get("path")
    result["source_sha256_before"] = inspection["source"].get("sha256")
    selected, target_refusals = preflight(inspection, approved_ids)
    result["refusals"].extend(command_refusals + target_refusals)

    source_path: Path | None = None
    source_original: str | None = None
    if result["source_footprint"]:
        resolved_source, source_error = lexical_path(workspace, result["source_footprint"])
        if source_error or resolved_source is None or target_outside_workspace(workspace, resolved_source):
            result["refusals"].append(
                {
                    "code": "source-path-invalid",
                    "message": source_error or "Source footprint resolves outside the workspace",
                }
            )
        else:
            source_path = resolved_source
            try:
                source_original = source_path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                result["refusals"].append(
                    {"code": "source-read-failed", "message": str(exc)}
                )

    report: Path | None = None
    if result["source_footprint"]:
        try:
            report = report_path(workspace, result["source_footprint"], run_key)
            result["report"] = report.relative_to(workspace).as_posix()
        except (OSError, ValueError) as exc:
            result["refusals"].append({"code": "report-path-failed", "message": str(exc)})
    if report and target_outside_workspace(workspace, report):
        result["refusals"].append(
            {"code": "report-path-escape", "message": "Cleanup report resolves outside workspace"}
        )
        report = None
        result["report"] = None

    if result["refusals"]:
        result["status"] = "refused"
        result["completed"] = utc_now()
        if report:
            try:
                atomic_write_text(report, render_report(result))
            except OSError as exc:
                result["report"] = None
                result["refusals"].append({"code": "report-write-failed", "message": str(exc)})
        return result, 2

    try:
        recovery_root, recovery_identity_value = create_recovery_root(workspace, run_key)
    except (OSError, ValueError) as exc:
        result["status"] = "failed"
        result["completed"] = utc_now()
        result["recovery"] = {
            "status": "not-created",
            "location": None,
            "detail": str(exc),
        }
        result["refusals"].append(
            {"code": "recovery-create-failed", "message": str(exc)}
        )
        if report:
            try:
                atomic_write_text(report, render_report(result))
            except OSError as report_exc:
                result["report"] = None
                result["refusals"].append(
                    {"code": "report-write-failed", "message": str(report_exc)}
                )
        return result, 3
    result["recovery"] = {
        "status": "available",
        "location": str(recovery_root),
        "detail": "Recovery map is written before each quarantine move.",
    }
    if report is None:
        discard_recovery(recovery_root, recovery_identity_value)
        result["status"] = "failed"
        result["completed"] = utc_now()
        result["refusals"].append(
            {"code": "report-required", "message": "A durable report path is required before Apply"}
        )
        return result, 3

    result["status"] = "running"
    try:
        atomic_write_text(report, render_report(result))
    except OSError as exc:
        discarded, discard_error = discard_recovery(
            recovery_root, recovery_identity_value
        )
        result["status"] = "failed"
        result["completed"] = utc_now()
        result["report"] = None
        result["recovery"] = {
            "status": "discarded" if discarded else "retained",
            "location": None if discarded else str(recovery_root),
            "detail": discard_error or "Report creation failed before cleanup mutation.",
        }
        result["refusals"].append({"code": "report-write-failed", "message": str(exc)})
        return result, 3

    baseline, baseline_passed = run_validation(
        workspace, commands, "baseline", args.validation_timeout
    )
    result["validation"].extend(baseline)
    if not baseline_passed:
        discarded, discard_error = discard_recovery(recovery_root, recovery_identity_value)
        result["status"] = "refused"
        result["completed"] = utc_now()
        result["recovery"] = {
            "status": "discarded" if discarded else "retained",
            "location": None if discarded else str(recovery_root),
            "detail": discard_error or "Baseline validation failed before cleanup mutation.",
        }
        result["refusals"].append(
            {"code": "baseline-validation-failed", "message": "Cleanup was not attempted"}
        )
        atomic_write_text(report, render_report(result))
        return result, 2

    fresh_inspection = inspect(workspace, args.footprint)
    fresh_selected, fresh_refusals = preflight(fresh_inspection, approved_ids)
    if fresh_refusals:
        discarded, discard_error = discard_recovery(recovery_root, recovery_identity_value)
        result["status"] = "refused"
        result["completed"] = utc_now()
        result["recovery"] = {
            "status": "discarded" if discarded else "retained",
            "location": None if discarded else str(recovery_root),
            "detail": discard_error or "Approved state changed during baseline validation.",
        }
        result["refusals"].extend(fresh_refusals)
        atomic_write_text(report, render_report(result))
        return result, 2
    selected = fresh_selected

    roots = top_level_targets(selected)
    mappings: list[dict[str, Any]] = []
    if source_path is None or source_original is None:
        raise ValueError("Source footprint became unavailable after preflight")
    source_changed = False

    for item in selected:
        result["actions"].append(
            {
                "id": item["id"],
                "path": item["path"],
                "outcome": "approved",
                "detail": "Awaiting verified quarantine.",
            }
        )

    try:
        quarantine_targets(
            workspace, recovery_root, recovery_identity_value, roots, mappings
        )
        result["cleanup_mutations_performed"] = True
        for action in result["actions"]:
            action["outcome"] = "quarantined"
            action["detail"] = "Exact approved whole path is absent from the workspace."

        after, after_passed = run_validation(
            workspace, commands, "post-clean", args.validation_timeout
        )
        result["validation"].extend(after)
        if not after_passed:
            raise RuntimeError("post-clean validation failed")

        for item in selected:
            current_path, current_error = lexical_path(workspace, item["path"])
            if current_error or current_path is None or os.path.lexists(current_path):
                raise RuntimeError(f"Approved path reappeared after validation: {item['path']}")

        current_source = source_path.read_text(encoding="utf-8-sig")
        if current_source != source_original:
            result["source_sha256_after"] = hashlib.sha256(
                current_source.encode("utf-8")
            ).hexdigest()
            raise RuntimeError("Source footprint changed during Apply")

        successful_paths = {item["path"] for item in selected}
        updated_source, obligations_updated = mark_cleanup_obligations(
            source_original, successful_paths
        )
        if obligations_updated:
            atomic_write_text(source_path, updated_source)
            source_changed = True
            result["obligations_updated"] = obligations_updated
            result["source_sha256_after"] = hashlib.sha256(updated_source.encode("utf-8")).hexdigest()

        result["status"] = "completed"
        result["completed"] = utc_now()
        result["recovery"]["detail"] = "Post-clean validation passed; recovery will be discarded."
        for action in result["actions"]:
            action["outcome"] = "removed"
            action["detail"] = "Approved path removed after successful validation."
        atomic_write_text(report, render_report(result))

    except Exception as exc:
        restored, restore_errors = restore_targets(
            workspace, recovery_root, recovery_identity_value, mappings
        )
        if source_changed:
            try:
                atomic_write_text(source_path, source_original)
                source_changed = False
                result["source_sha256_after"] = None
                result["obligations_updated"] = 0
            except OSError as source_exc:
                restored = False
                restore_errors.append(f"Could not restore source footprint: {source_exc}")

        if restored:
            recovery_validation, recovery_passed = run_validation(
                workspace, commands, "restored", args.validation_timeout
            )
            result["validation"].extend(recovery_validation)
            discarded, discard_error = discard_recovery(
                recovery_root, recovery_identity_value
            )
            result["status"] = "restored" if recovery_passed else "restored-validation-failed"
            result["recovery"] = {
                "status": "discarded" if discarded else "retained",
                "location": None if discarded else str(recovery_root),
                "detail": discard_error or str(exc),
            }
            for action in result["actions"]:
                action["outcome"] = "restored"
                action["detail"] = "Original fingerprint restored after Apply failure."
            exit_code = 2 if recovery_passed else 3
        else:
            result["status"] = "recovery-required"
            result["recovery"] = {
                "status": "retained",
                "location": str(recovery_root),
                "detail": "; ".join(restore_errors) or str(exc),
            }
            for action in result["actions"]:
                action["outcome"] = "recovery-required"
                action["detail"] = "Use the retained recovery map before further mutation."
            exit_code = 3
        result["completed"] = utc_now()
        result["refusals"].append({"code": "apply-failed", "message": str(exc)})
        try:
            atomic_write_text(report, render_report(result))
        except OSError as report_exc:
            result["refusals"].append(
                {"code": "report-update-failed", "message": str(report_exc)}
            )
        return result, exit_code

    discarded, discard_error = discard_recovery(recovery_root, recovery_identity_value)
    if discarded:
        result["recovery"] = {
            "status": "discarded",
            "location": None,
            "detail": "Recovery snapshot removed after successful validation and reporting.",
        }
    else:
        result["status"] = "completed-recovery-retained"
        result["recovery"] = {
            "status": "retained",
            "location": str(recovery_root),
            "detail": discard_error,
        }
    result["completed"] = utc_now()
    try:
        atomic_write_text(report, render_report(result))
        return result, 0
    except OSError as exc:
        result["status"] = "completed-report-update-failed"
        result["refusals"].append({"code": "report-update-failed", "message": str(exc)})
        return result, 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Workspace root")
    parser.add_argument(
        "--footprint", required=True, help="Explicit workspace-relative source footprint"
    )
    parser.add_argument("--approve", action="append", required=True, help="Approved PC candidate ID")
    parser.add_argument(
        "--validate-command",
        action="append",
        required=True,
        help="Validation command as a JSON argument array; repeat as needed",
    )
    parser.add_argument("--validation-timeout", type=int, default=600)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result, exit_code = apply_cleanup(args)
    except (OSError, ValueError) as exc:
        result = {
            "schema": APPLY_SCHEMA,
            "mode": "apply",
            "status": "failed",
            "error": str(exc),
        }
        exit_code = 3
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
