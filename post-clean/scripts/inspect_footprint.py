#!/usr/bin/env python3
"""Read-only inspector for gameplan-task-footprint/v1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SUPPORTED_SCHEMA = "gameplan-task-footprint/v1"
OUTPUT_SCHEMA = "post-clean-inspection/v1"
REMOVABLE_KINDS = {"temporary", "scaffold", "experiment"}
REMOVABLE_DISPOSITIONS = {"remove", "abandoned"}
PRESERVED_DISPOSITIONS = {"keep", "adopted"}
KNOWN_ORIGINS = {"created", "pre-existing"}
KNOWN_KINDS = {"deliverable", "temporary", "scaffold", "experiment", "uncertain"}
KNOWN_DISPOSITIONS = {"keep", "remove", "adopted", "abandoned", "review"}
RESERVED_EXACT_PATHS = {".git", ".gameplan", "GAMEPLAN.md"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_utf8(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except (OSError, UnicodeError) as exc:
        return None, f"Could not read {path}: {exc}"


def metadata_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?mi)^{re.escape(key)}:\s*`([^`]*)`\s*$", text)
    return match.group(1).strip() if match else None


def section_text(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*\r?\n(.*?)(?=^##\s+|\Z)", text
    )
    return match.group(1) if match else None


def clean_cell(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1]
    return value.strip()


def parse_table(
    text: str, heading: str, expected_headers: list[str]
) -> tuple[list[dict[str, str]], list[str]]:
    body = section_text(text, heading)
    if body is None:
        return [], [f"Missing section: {heading}"]

    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return [], [f"Missing table in section: {heading}"]

    errors: list[str] = []
    rows: list[dict[str, str]] = []

    def split(line: str) -> list[str]:
        if "\\|" in line:
            raise ValueError("escaped pipes are unsupported")
        return [clean_cell(cell) for cell in line.strip().strip("|").split("|")]

    try:
        headers = split(lines[0])
    except ValueError as exc:
        return [], [f"Invalid {heading} header: {exc}"]
    if headers != expected_headers:
        return [], [f"Unexpected {heading} columns: {headers}"]

    for number, line in enumerate(lines[2:], start=1):
        try:
            cells = split(line)
        except ValueError as exc:
            errors.append(f"Invalid {heading} row {number}: {exc}")
            continue
        if len(cells) != len(headers):
            errors.append(f"Invalid {heading} row {number}: wrong column count")
            continue
        if not any(cells):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows, errors


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
        return {"type": "file", "size": path.stat().st_size, "sha256": sha256_file(path)}
    if path.is_dir():
        entries: list[dict[str, Any]] = []

        def scan(directory: Path) -> None:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda entry: entry.name)
            for entry in children:
                child = Path(entry.path)
                relative = child.relative_to(path).as_posix()
                if entry.is_symlink() or is_junction(child):
                    detail = fingerprint_path(root, child)
                    entries.append({"path": relative, **detail})
                elif entry.is_dir(follow_symlinks=False):
                    entries.append({"path": relative, "type": "directory"})
                    scan(child)
                elif entry.is_file(follow_symlinks=False):
                    entries.append(
                        {
                            "path": relative,
                            "type": "file",
                            "size": child.stat().st_size,
                            "sha256": sha256_file(child),
                        }
                    )
                else:
                    entries.append({"path": relative, "type": "other"})

        scan(path)
        manifest = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
        return {
            "type": "directory",
            "entries": entries,
            "entry_count": len(entries),
            "sha256": sha256_bytes(manifest),
        }
    return {"type": "other"}


def fingerprint_token(fingerprint: dict[str, Any]) -> str:
    encoded = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(encoded)


def stable_id(
    source_digest: str, source_kind: str, path: str, action: str, state_token: str
) -> str:
    material = "\0".join([source_digest, source_kind, path, action, state_token]).encode()
    return "PC-" + sha256_bytes(material)[:12].upper()


def paths_overlap(first: str, second: str) -> bool:
    return first == second or first.startswith(second + "/") or second.startswith(first + "/")


def is_reserved_path(path: str) -> bool:
    return any(path == reserved or path.startswith(reserved + "/") for reserved in RESERVED_EXACT_PATHS)


def select_footprint(root: Path, requested: str | None) -> tuple[Path | None, str, list[str]]:
    if requested:
        normalized, error = normalize_relative_path(requested)
        if error:
            return None, "invalid", [error]
        selected, error = lexical_path(root, normalized)
        return selected, "explicit", [error] if error else []

    gameplan = root / "GAMEPLAN.md"
    text, error = read_utf8(gameplan)
    if error or text is None:
        return None, "missing", [error or "GAMEPLAN.md is unavailable"]
    body = section_text(text, "Task Footprint")
    if body is None:
        return None, "missing", ["GAMEPLAN.md has no Task Footprint section"]
    matches = re.findall(r"`(\.gameplan/footprints/[^`]+\.md)`", body)
    unique = list(dict.fromkeys(matches))
    if not unique:
        return None, "missing", ["No footprint is referenced by GAMEPLAN.md"]
    if len(unique) != 1:
        return None, "ambiguous", ["GAMEPLAN.md references multiple task footprints"]
    normalized, error = normalize_relative_path(unique[0])
    if error or normalized is None:
        return None, "invalid", [error or "Footprint pointer is invalid"]
    selected, error = lexical_path(root, normalized)
    return selected, "gameplan", [error] if error else []


def is_removable_row(row: dict[str, str]) -> bool:
    return (
        row.get("Origin") == "created"
        and row.get("Kind") in REMOVABLE_KINDS
        and row.get("Disposition") in REMOVABLE_DISPOSITIONS
    )


def inspect(workspace: Path, requested: str | None) -> dict[str, Any]:
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Workspace root must be a directory")
    selected, selection, selection_issues = select_footprint(root, requested)
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "mode": "inspect",
        "mutations_performed": False,
        "apply_supported": True,
        "workspace": str(root),
        "source": {"selection": selection, "path": None, "schema": None, "state": None},
        "items": [],
        "provisional_authorization_set": [],
        "refusals": [],
    }
    if selection_issues or selected is None:
        result["refusals"] = [
            {"code": f"source-{selection}", "message": issue}
            for issue in selection_issues
            if issue
        ]
        return result

    try:
        selected_relative = selected.relative_to(root).as_posix()
    except ValueError:
        result["refusals"].append(
            {"code": "source-outside-workspace", "message": "Footprint is outside the workspace"}
        )
        return result
    result["source"]["path"] = selected_relative

    if not selected_relative.startswith(".gameplan/footprints/") or not selected_relative.endswith(".md"):
        result["refusals"].append(
            {
                "code": "source-location-invalid",
                "message": "Footprint must be a Markdown file under .gameplan/footprints/",
            }
        )
        return result
    if target_outside_workspace(root, selected):
        result["refusals"].append(
            {
                "code": "source-link-escape",
                "message": "Footprint link or junction resolves outside the workspace",
            }
        )
        return result

    text, read_error = read_utf8(selected)
    if read_error or text is None:
        result["refusals"].append(
            {"code": "source-unreadable", "message": read_error or "Footprint is unreadable"}
        )
        return result

    source_digest = sha256_bytes(text.encode("utf-8"))
    source_token = sha256_bytes((selected_relative + "\0" + source_digest).encode())
    schema = metadata_value(text, "Schema")
    state = metadata_value(text, "State")
    result["source"].update({"schema": schema, "state": state, "sha256": source_digest})

    protected_rows, protected_errors = parse_table(
        text,
        "Protected pre-existing items",
        ["Path", "Observed state", "Protection reason"],
    )
    task_rows, task_errors = parse_table(
        text,
        "Task items",
        ["Path", "Origin", "Kind", "Disposition", "Intent"],
    )
    obligation_rows, obligation_errors = parse_table(
        text,
        "Cleanup obligations",
        ["Path", "Action", "Status", "Reason"],
    )
    parse_errors = protected_errors + task_errors + obligation_errors

    protected: list[str] = []
    for row in protected_rows:
        normalized, error = normalize_relative_path(row.get("Path", ""))
        if error:
            parse_errors.append(f"Invalid protected path {row.get('Path', '')!r}: {error}")
        elif normalized:
            protected.append(normalized)

    normalized_rows: list[tuple[dict[str, str], str | None, str | None]] = []
    path_counts: dict[str, int] = {}
    for row in task_rows:
        normalized, error = normalize_relative_path(row.get("Path", ""))
        normalized_rows.append((row, normalized, error))
        if normalized:
            path_counts[normalized] = path_counts.get(normalized, 0) + 1
    duplicates = sorted(path for path, count in path_counts.items() if count > 1)
    if duplicates:
        parse_errors.append("Duplicate task paths: " + ", ".join(duplicates))

    source_blockers: list[dict[str, str]] = []
    if schema != SUPPORTED_SCHEMA:
        source_blockers.append(
            {"code": "unsupported-schema", "message": f"Unsupported schema: {schema or 'missing'}"}
        )
    if state != "finalized":
        source_blockers.append(
            {"code": "source-not-finalized", "message": f"Footprint state is {state or 'missing'}"}
        )
    source_blockers.extend(
        {"code": "malformed-footprint", "message": error} for error in parse_errors
    )
    result["refusals"].extend(source_blockers)
    source_ready = not source_blockers

    removable_paths = {
        normalized
        for row, normalized, error in normalized_rows
        if normalized and not error and is_removable_row(row)
    }

    for row, normalized, path_error in normalized_rows:
        raw_path = row.get("Path", "")
        display_path = normalized or raw_path
        classification = "review"
        action = "none"
        reason = path_error or "Footprint row requires review"
        current: dict[str, Any] = {"type": "unresolved"}

        if normalized and not path_error:
            absolute, resolution_error = lexical_path(root, normalized)
            if resolution_error or absolute is None:
                reason = resolution_error or "Path could not be resolved"
            else:
                if target_outside_workspace(root, absolute):
                    current = {"type": "link-escape", "external_target": True}
                else:
                    try:
                        current = fingerprint_path(root, absolute)
                    except OSError as exc:
                        current = {"type": "unreadable", "error": str(exc)}

                protected_match = next(
                    (item for item in protected if paths_overlap(normalized, item)), None
                )
                values_known = (
                    row.get("Origin") in KNOWN_ORIGINS
                    and row.get("Kind") in KNOWN_KINDS
                    and row.get("Disposition") in KNOWN_DISPOSITIONS
                )

                if not source_ready:
                    classification = "preserve"
                    reason = "Source footprint is not eligible for cleanup classification"
                elif is_reserved_path(normalized) or normalized == selected_relative:
                    classification = "preserve"
                    reason = "Post Clean control and evidence paths are reserved"
                elif protected_match:
                    classification = "preserve"
                    reason = f"Path overlaps protected item {protected_match}"
                elif not values_known:
                    classification = "review"
                    reason = "Footprint row contains an unknown enum value"
                elif row.get("Disposition") in PRESERVED_DISPOSITIONS:
                    classification = "preserve"
                    reason = f"Disposition {row.get('Disposition')} is intentional"
                elif row.get("Kind") == "uncertain" or row.get("Disposition") == "review":
                    classification = "preserve"
                    reason = "Uncertain or review items must be preserved"
                elif row.get("Kind") == "deliverable" and row.get("Disposition") in REMOVABLE_DISPOSITIONS:
                    classification = "review"
                    reason = "Conflicting deliverable and removal intent"
                elif row.get("Origin") != "created":
                    classification = "review"
                    reason = "Pre-existing paths are ineligible for whole-path removal"
                elif not is_removable_row(row):
                    classification = "review"
                    reason = "Row does not satisfy the whole-path candidate contract"
                elif current.get("type") == "absent":
                    classification = "preserve"
                    reason = "Absent paths require no cleanup"
                elif current.get("type") in {"unreadable", "other"} or current.get("error"):
                    classification = "review"
                    reason = "Current path state cannot be fingerprinted reliably"
                elif current.get("external_target"):
                    classification = "review"
                    reason = "Link or junction resolves outside the workspace"
                elif current.get("type") in {"symlink", "junction"}:
                    classification = "review"
                    reason = "Link and junction cleanup is not supported by whole-path Apply"
                elif current.get("type") == "directory":
                    unlisted = []
                    external = []
                    for entry in current.get("entries", []):
                        if entry.get("external_target"):
                            external.append(entry.get("path", ""))
                        descendant = normalized + "/" + entry.get("path", "")
                        if descendant not in removable_paths:
                            unlisted.append(descendant)
                    if external:
                        classification = "review"
                        reason = "Directory contains an external link or junction"
                    elif unlisted:
                        classification = "review"
                        reason = "Directory contains unlisted or preserved descendants"
                        current["unlisted_descendants"] = sorted(unlisted)
                    else:
                        classification = "candidate"
                        action = "remove-whole-path"
                        reason = "Task-created removable directory with fully listed descendants"
                else:
                    classification = "candidate"
                    action = "remove-whole-path"
                    reason = "Task-created removable item with a current fingerprint"

        state_token = fingerprint_token(current)
        item_id = stable_id(source_token, "task-item", display_path, action, state_token)
        item = {
            "id": item_id,
            "path": display_path,
            "source": "task-item",
            "classification": classification,
            "proposed_action": action,
            "reason": reason,
            "footprint": {
                "origin": row.get("Origin"),
                "kind": row.get("Kind"),
                "disposition": row.get("Disposition"),
                "intent": row.get("Intent"),
            },
            "current": current,
        }
        result["items"].append(item)
        if classification == "candidate":
            result["provisional_authorization_set"].append(item_id)

    task_items_by_path = {
        item["path"]: item for item in result["items"] if item["source"] == "task-item"
    }
    for item in result["items"]:
        if item["classification"] != "candidate" or item["current"].get("type") != "directory":
            continue
        blocked_descendants = []
        for entry in item["current"].get("entries", []):
            descendant = item["path"] + "/" + entry.get("path", "")
            child = task_items_by_path.get(descendant)
            if child is None or child.get("classification") != "candidate":
                blocked_descendants.append(descendant)
        if blocked_descendants:
            result["provisional_authorization_set"].remove(item["id"])
            item["classification"] = "review"
            item["proposed_action"] = "none"
            item["reason"] = "Directory contains descendants that are not cleanup candidates"
            item["current"]["blocked_descendants"] = sorted(blocked_descendants)
            item["id"] = stable_id(
                source_token,
                "task-item",
                item["path"],
                "none",
                fingerprint_token(item["current"]),
            )

    for row in obligation_rows:
        if row.get("Status") != "open":
            continue
        normalized, path_error = normalize_relative_path(row.get("Path", ""))
        display_path = normalized or row.get("Path", "")
        current: dict[str, Any] = {"type": "unresolved"}
        if normalized and not path_error:
            absolute, resolution_error = lexical_path(root, normalized)
            if (
                not resolution_error
                and absolute is not None
                and not target_outside_workspace(root, absolute)
            ):
                try:
                    current = fingerprint_path(root, absolute)
                except OSError as exc:
                    current = {"type": "unreadable", "error": str(exc)}
        item_id = stable_id(
            source_token,
            "cleanup-obligation",
            display_path,
            "targeted-review",
            fingerprint_token(current),
        )
        result["items"].append(
            {
                "id": item_id,
                "path": display_path,
                "source": "cleanup-obligation",
                "classification": "review",
                "proposed_action": "targeted-review",
                "reason": path_error or "Open obligation requires exact-scope review",
                "footprint": {
                    "action": row.get("Action"),
                    "status": row.get("Status"),
                    "reason": row.get("Reason"),
                },
                "current": current,
            }
        )

    result["provisional_authorization_set"].sort()
    return result


def fingerprint_summary(current: dict[str, Any]) -> str:
    kind = current.get("type", "unknown")
    digest = current.get("sha256")
    if digest:
        return f"{kind}:{digest[:12]}"
    if kind in {"symlink", "junction"}:
        return f"{kind}:{current.get('target', 'unknown')}"
    return kind


def render_markdown(result: dict[str, Any]) -> str:
    source = result["source"]
    lines = [
        "# Post Clean inspection",
        "",
        f"Source: `{source.get('path') or source.get('selection')}`",
        f"Schema: `{source.get('schema') or 'unavailable'}`",
        f"State: `{source.get('state') or 'unavailable'}`",
        "Mutations: `none`",
        "Apply support: `available with explicit approval`",
        "",
        "| ID | Path | Decision | Action | Fingerprint | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for item in result["items"]:
        reason = str(item["reason"]).replace("|", "\\|")
        path = str(item["path"]).replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{path}` | `{item['classification']}` | "
            f"`{item['proposed_action']}` | `{fingerprint_summary(item['current'])}` | {reason} |"
        )
    if not result["items"]:
        lines.append("| - | - | - | - | - | No inspectable items. |")
    lines.extend(["", "Provisional authorization set: " + (
        ", ".join(f"`{item}`" for item in result["provisional_authorization_set"])
        if result["provisional_authorization_set"] else "empty"
    )])
    if result["refusals"]:
        lines.extend(["", "Refusals:"])
        lines.extend(f"- {item['code']}: {item['message']}" for item in result["refusals"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Workspace root")
    parser.add_argument(
        "--footprint", help="Explicit workspace-relative footprint path; otherwise use GAMEPLAN.md"
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect(Path(args.workspace), args.footprint)
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
