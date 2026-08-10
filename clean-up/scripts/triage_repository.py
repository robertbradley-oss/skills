#!/usr/bin/env python3
"""Turn broad Clean Up discovery into a concise read-only decision report."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from discover_repository import discover, evidence_text, markdown_cell
from inspect_repository import fingerprint_summary, inspect


OUTPUT_SCHEMA = "clean-up-triage/v1"
AUTO_INSPECT_SIGNALS = {"generated-residue", "temporary-file"}
STRICT_CANDIDATE_KINDS = {
    "empty-directory", "ignored-generated", "remote-backed-release", "temporary-residue",
}
PC_ID_PATTERN = re.compile(r"^PC-[A-F0-9]{12}$")
ARTIFACT_BUNDLE = re.compile(
    r"^(?:phase-\d+|release-\d+(?:\.\d+){1,3}|config-[a-z0-9-]+)$",
    flags=re.IGNORECASE,
)
REFERENCE_SUFFIXES = {
    ".gif", ".jpeg", ".jpg", ".json", ".md", ".pdf", ".png", ".svg", ".webp",
}
EVIDENCE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".json", ".png", ".svg", ".webp"}


def bounded_regular_files(path: Path, max_entries: int = 500) -> list[Path] | None:
    if path.is_symlink():
        return None
    if path.is_file():
        return [path]
    if not path.is_dir():
        return None
    files: list[Path] = []
    scanned = 0
    stack = [path]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    scanned += 1
                    if scanned > max_entries:
                        return None
                    child = Path(entry.path)
                    if entry.is_symlink():
                        return None
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(child)
                    elif entry.is_file(follow_symlinks=False):
                        files.append(child)
                    else:
                        return None
        except OSError:
            return None
    return files


def current_bytes(current: dict[str, Any]) -> int:
    if current.get("type") == "file":
        size = current.get("size")
        return size if isinstance(size, int) and size >= 0 else 0
    if current.get("type") != "directory":
        return 0
    total = 0
    for entry in current.get("entries", []):
        if isinstance(entry, dict) and entry.get("type") == "file":
            size = entry.get("size")
            if isinstance(size, int) and size >= 0:
                total += size
    return total


def retained_reason(item: dict[str, Any]) -> str | None:
    evidence = item.get("evidence", {})
    retention = evidence.get("release_retention") or {}
    reason = str(retention.get("reason") or item.get("reason") or "")
    if "current or within the two newest stable releases" in reason.lower():
        return "Keep locally: this is one of the newest two published stable releases."
    if retention and retention.get("eligible") is False:
        return f"Keep locally: exact remote recovery is not proven ({reason})."
    references = evidence.get("references") or {}
    match_count = references.get("match_count")
    if isinstance(match_count, int) and match_count > 0:
        return f"Keep pending dependency changes: repository content has {match_count} exact path reference(s)."
    return None


def decision_for_inspection(lead: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    candidate_kind = item.get("candidate_kind")
    if (
        item.get("classification") == "candidate"
        and candidate_kind in STRICT_CANDIDATE_KINDS
        and item.get("proposed_action") == "remove-whole-path"
        and isinstance(item.get("id"), str)
        and PC_ID_PATTERN.fullmatch(item["id"])
    ):
        return {
            "decision": "safe-to-remove",
            "reason": item.get("reason") or "Exact Inspect established a strict whole-path candidate.",
        }
    keep_reason = retained_reason(item)
    if keep_reason:
        return {"decision": "keep", "reason": keep_reason}
    if item.get("classification") == "candidate" and candidate_kind == "git-new":
        return {
            "decision": "unresolved",
            "reason": "The path is new to Git, but broad triage cannot prove why it exists or that it is disposable.",
        }
    return {
        "decision": "unresolved",
        "reason": item.get("reason") or lead.get("reason") or "Current evidence is insufficient.",
    }


def triage_path_lead(root: Path, lead: dict[str, Any], git_base: str | None) -> dict[str, Any]:
    try:
        inspection = inspect(root, [lead["target"]], git_base)
    except (OSError, ValueError) as exc:
        return {
            "lead_id": lead["id"], "path": lead["target"], "decision": "unresolved",
            "reason": f"Exact Inspect failed: {exc}", "inspection": None,
        }
    items = inspection.get("items", [])
    if inspection.get("refusals") or len(items) != 1:
        messages = [str(item.get("message")) for item in inspection.get("refusals", [])]
        reason = "; ".join(message for message in messages if message) or "Exact Inspect did not return one item."
        return {
            "lead_id": lead["id"], "path": lead["target"], "decision": "unresolved",
            "reason": reason, "inspection": inspection,
        }
    item = items[0]
    decision = decision_for_inspection(lead, item)
    return {
        "lead_id": lead["id"],
        "path": lead["target"],
        **decision,
        "candidate_id": item.get("id") if decision["decision"] == "safe-to-remove" else None,
        "candidate_kind": item.get("candidate_kind"),
        "bytes": current_bytes(item.get("current", {})),
        "fingerprint": fingerprint_summary(item.get("current", {})),
        "inspection": inspection,
    }


def unresolved_lead(lead: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    evidence = lead.get("evidence", {})
    footprint = evidence.get("footprint", {}) if isinstance(evidence, dict) else {}
    size = footprint.get("bytes") if isinstance(footprint, dict) else 0
    if lead.get("surface") == "duplicate-set" and isinstance(evidence, dict):
        size = evidence.get("total_bytes", size)
    return {
        "lead_id": lead["id"],
        "surface": lead["surface"],
        "target": lead["target"],
        "signal": lead["signal"],
        "bytes": size if isinstance(size, int) and size >= 0 else 0,
        "reason": reason or lead.get("reason") or "Current evidence is insufficient.",
        "evidence_summary": evidence_text(lead),
    }


def keep_lead(lead: dict[str, Any], reason: str) -> dict[str, Any]:
    item = unresolved_lead(lead, reason)
    return {
        "lead_id": item["lead_id"], "path": item["target"],
        "surface": item["surface"], "signal": item["signal"],
        "bytes": item["bytes"], "decision": "keep", "reason": reason,
    }


def structured_artifact_archive(root: Path, lead: dict[str, Any]) -> bool:
    if lead.get("target") != "artifacts" or lead.get("evidence", {}).get("git") != "ignored":
        return False
    archive = root / "artifacts"
    children: list[Path] = []
    try:
        with os.scandir(archive) as iterator:
            for entry in iterator:
                if len(children) >= 100:
                    return False
                children.append(Path(entry.path))
    except OSError:
        return False
    children.sort(key=lambda item: item.name.lower())
    if len(children) < 2:
        return False
    if any(
        not child.is_dir() or child.is_symlink() or not ARTIFACT_BUNDLE.fullmatch(child.name)
        for child in children
    ):
        return False
    scanned = 0
    for child in children:
        marker = False
        stack = [child]
        while stack and scanned < 20_000 and not marker:
            directory = stack.pop()
            try:
                with os.scandir(directory) as iterator:
                    for entry in iterator:
                        scanned += 1
                        path = Path(entry.path)
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(path)
                        elif entry.is_file(follow_symlinks=False) and path.suffix.lower() in EVIDENCE_SUFFIXES:
                            marker = True
                        if scanned >= 20_000:
                            break
            except OSError:
                return False
        if not marker:
            return False
    return True


def structured_release_container(root: Path, target: str) -> bool:
    if target.lower() not in {"release", "releases"}:
        return False
    container = root / target
    children: list[Path] = []
    try:
        with os.scandir(container) as iterator:
            for entry in iterator:
                if len(children) >= 200:
                    return False
                children.append(Path(entry.path))
    except OSError:
        return False
    release_directories = 0
    for child in children:
        if not child.is_dir() or child.is_symlink():
            continue
        manifest = child / "release-manifest.json"
        if manifest.is_file() and not manifest.is_symlink() and version_in_path(child.name):
            release_directories += 1
    return release_directories >= 2


def version_in_path(name: str) -> bool:
    return re.search(r"(?<!\d)\d+(?:\.\d+){1,3}(?!\d)", name) is not None


def path_role_keep_reason(root: Path, lead: dict[str, Any]) -> str | None:
    target = str(lead.get("target", ""))
    parts = PurePosixPath(target).parts
    if structured_artifact_archive(root, lead):
        return (
            "Keep by default: this ignored root is a structured phase, release, and validation evidence archive. "
            "No expiry or remote-recovery policy authorizes discarding that evidence."
        )
    if structured_release_container(root, target):
        return (
            "Keep as a container: versioned child releases are triaged independently, "
            "so the shared release root is not itself a deletion target."
        )
    if parts and parts[0].lower() == "references":
        absolute = root.joinpath(*parts)
        regular = bounded_regular_files(absolute)
        if regular and all(item.suffix.lower() in REFERENCE_SUFFIXES for item in regular):
            return "Keep by role: this is intentionally named reference material, not generated residue."
    if parts and parts[0].lower() == "installer":
        absolute = root.joinpath(*parts)
        regular = bounded_regular_files(absolute)
        if regular and all(item.suffix.lower() == ".iss" for item in regular):
            return "Keep by role: this is installer source code, not generated installer output."
    return None


def duplicate_role_keep_reason(lead: dict[str, Any]) -> str | None:
    paths = lead.get("evidence", {}).get("paths", [])
    if not isinstance(paths, list) or len(paths) < 2:
        return None
    parsed = [PurePosixPath(str(path)) for path in paths]
    if all(
        len(path.parts) >= 4
        and path.parts[0].lower() == "docs"
        and re.fullmatch(r"phase-\d+", path.parts[1], flags=re.IGNORECASE)
        and path.parts[2].lower() == "evidence"
        and path.suffix.lower() in EVIDENCE_SUFFIXES
        for path in parsed
    ):
        return (
            "Keep by role: byte-identical files occupy distinct phase or UI-state evidence paths, "
            "so their locations carry documentation meaning."
        )
    return None


def verdict_for(result: dict[str, Any]) -> tuple[str, str]:
    summary = result["summary"]
    incomplete = bool(
        result["warnings"]
        or summary.get("discovery_truncated")
        or summary.get("filesystem_scan_truncated")
        or summary.get("duplicate_hash_budget_exhausted")
        or summary.get("auto_inspect_truncated")
    )
    candidates = summary["safe_to_remove_count"]
    recoverable = summary["recoverable_bytes"]
    unresolved = summary["unresolved_count"]
    hygiene = summary["git_hygiene_count"]
    if incomplete:
        return "incomplete", "The cleanup audit is incomplete; do not call the workspace clean from this run."
    if candidates:
        unresolved_note = (
            f" {unresolved} unresolved lead(s) still prevent a fully clean verdict."
            if unresolved else ""
        )
        return (
            "cleanup-recommended",
            f"Cleanup is recommended: {candidates} proven whole-path candidate(s) can recover "
            f"{format_bytes(recoverable)}.{unresolved_note}",
        )
    if unresolved:
        return (
            "review-remains",
            f"No deletion is proven safe, but {unresolved} unresolved lead(s) prevent a clean verdict.",
        )
    if hygiene:
        return (
            "generally-clean-git-hygiene",
            f"File cleanup is complete; {hygiene} branch or worktree hygiene item(s) remain separate.",
        )
    return "clean", "The workspace is clean based on the completed read-only audit."


def triage(
    workspace: Path, git_base: str | None, max_leads: int,
    max_files: int = 50000, max_hash_bytes: int = 1024 * 1024 * 1024,
    max_inspections: int = 50,
) -> dict[str, Any]:
    if max_inspections <= 0:
        raise ValueError("max-inspections must be positive")
    discovery = discover(workspace, git_base, max_leads, max_files, max_hash_bytes)
    root = Path(discovery["workspace"])
    warnings = [
        item for item in discovery["warnings"]
        if not (
            discovery["scope_type"] == "folder"
            and item.get("code") == "git-unavailable"
        )
    ]
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "mode": "triage",
        "mutations_performed": False,
        "workspace": discovery["workspace"],
        "scope_type": discovery["scope_type"],
        "verdict": None,
        "headline": None,
        "summary": {},
        "safe_to_remove": [],
        "keep": [],
        "unresolved": [],
        "git_hygiene": [],
        "repository_attention": [],
        "proposed_authorization_set": [],
        "warnings": warnings,
        "review_required": True,
        "discovery": discovery,
    }
    inspectable = [
        lead for lead in discovery["leads"]
        if discovery["scope_type"] == "git-repository"
        and lead["surface"] == "path"
        and lead["signal"] in AUTO_INSPECT_SIGNALS
    ]
    selected_ids = {lead["id"] for lead in inspectable[:max_inspections]}
    path_results: dict[str, dict[str, Any]] = {}
    for lead in inspectable[:max_inspections]:
        path_results[lead["id"]] = triage_path_lead(root, lead, git_base)

    for lead in discovery["leads"]:
        if lead["surface"] == "path":
            if lead["id"] in path_results:
                item = path_results[lead["id"]]
                if item["decision"] == "safe-to-remove":
                    result["safe_to_remove"].append(item)
                elif item["decision"] == "keep":
                    result["keep"].append(item)
                else:
                    keep_reason = path_role_keep_reason(root, lead)
                    if keep_reason:
                        result["keep"].append(keep_lead(lead, keep_reason))
                    else:
                        result["unresolved"].append({
                            "lead_id": item["lead_id"], "surface": "path",
                            "target": item["path"], "signal": lead["signal"],
                            "bytes": item.get("bytes", 0), "reason": item["reason"],
                            "evidence_summary": item.get("fingerprint", "unknown"),
                        })
            elif lead["id"] in selected_ids:
                raise AssertionError("Selected path was not inspected")
            else:
                keep_reason = path_role_keep_reason(root, lead)
                if keep_reason:
                    result["keep"].append(keep_lead(lead, keep_reason))
                else:
                    reason = None
                    if lead["signal"] == "untracked-content":
                        reason = "Generic untracked content is preserved unless provenance and intent establish that it is residue."
                    elif lead in inspectable:
                        reason = "Automatic exact inspection limit was reached before this path."
                    result["unresolved"].append(unresolved_lead(lead, reason))
        elif lead["surface"] in {"branch", "worktree"}:
            result["git_hygiene"].append(unresolved_lead(lead))
        elif lead["surface"] == "repository":
            result["repository_attention"].append(unresolved_lead(lead))
        else:
            keep_reason = duplicate_role_keep_reason(lead) if lead["surface"] == "duplicate-set" else None
            if keep_reason:
                result["keep"].append(keep_lead(lead, keep_reason))
            else:
                result["unresolved"].append(unresolved_lead(lead))

    result["safe_to_remove"].sort(key=lambda item: (-item.get("bytes", 0), item["path"]))
    result["keep"].sort(key=lambda item: item["path"])
    result["unresolved"].sort(key=lambda item: (-item.get("bytes", 0), item["target"]))
    result["git_hygiene"].sort(key=lambda item: (item["surface"], item["target"]))
    result["proposed_authorization_set"] = [
        item["candidate_id"] for item in result["safe_to_remove"] if item.get("candidate_id")
    ]
    result["apply_supported"] = bool(result["proposed_authorization_set"])
    result["summary"] = {
        "discovery_lead_count": discovery["summary"]["lead_count"],
        "discovery_truncated": discovery["summary"]["truncated"],
        "filesystem_scan_truncated": discovery["summary"].get("filesystem_scan_truncated", False),
        "duplicate_hash_budget_exhausted": discovery["summary"].get("duplicate_hash_budget_exhausted", False),
        "auto_inspect_count": len(path_results),
        "auto_inspect_truncated": len(inspectable) > len(path_results),
        "safe_to_remove_count": len(result["safe_to_remove"]),
        "recoverable_bytes": sum(item.get("bytes", 0) for item in result["safe_to_remove"]),
        "kept_count": len(result["keep"]),
        "retained_bytes": sum(item.get("bytes", 0) for item in result["keep"]),
        "unresolved_count": len(result["unresolved"]) + len(result["repository_attention"]),
        "git_hygiene_count": len(result["git_hygiene"]),
    }
    result["verdict"], result["headline"] = verdict_for(result)
    return result


def format_bytes(value: int) -> str:
    units = ["bytes", "KiB", "MiB", "GiB", "TiB"]
    amount = float(max(0, value))
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{int(amount)} {unit}" if unit == "bytes" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{value} bytes"


def render_markdown(result: dict[str, Any], details_limit: int = 10) -> str:
    lines = [
        "# Clean Up triage", "", "## Bottom line", "", result["headline"],
        "", f"Repository verdict: `{result['verdict']}`", "",
        "## Safe to remove", "",
    ]
    if result["safe_to_remove"]:
        lines.extend([
            "| Candidate ID | Exact path | Kind | Recoverable | Evidence |",
            "|---|---|---|---:|---|",
        ])
        for item in result["safe_to_remove"]:
            lines.append(
                f"| `{item['candidate_id']}` | `{markdown_cell(item['path'])}` | "
                f"`{markdown_cell(item['candidate_kind'])}` | {format_bytes(item['bytes'])} | "
                f"{markdown_cell(item['reason'])} |"
            )
        authorization = ", ".join(f"`{item}`" for item in result["proposed_authorization_set"])
        lines.extend(["", f"Proposed authorization set: {authorization}"])
    else:
        lines.append("No whole-path deletion is currently proven safe.")

    lines.extend(["", "## What remains unresolved", ""])
    unresolved = result["repository_attention"] + result["unresolved"]
    if unresolved:
        lines.extend([
            "| Surface | Target | Footprint | Missing decision evidence |",
            "|---|---|---:|---|",
        ])
        for item in unresolved[:details_limit]:
            lines.append(
                f"| `{markdown_cell(item['surface'])}` | `{markdown_cell(item['target'])}` | "
                f"{format_bytes(item.get('bytes', 0))} | {markdown_cell(item['reason'])} |"
            )
        hidden = len(unresolved) - min(len(unresolved), details_limit)
        if hidden:
            lines.extend(["", f"{hidden} additional unresolved lead(s) are retained in the JSON evidence."])
    else:
        lines.append("No unresolved file or repository leads remain.")

    lines.extend(["", "## Git hygiene", ""])
    if result["git_hygiene"]:
        lines.append(
            f"{len(result['git_hygiene'])} branch or worktree item(s) need a separate Git review; path Apply does not remove them."
        )
    else:
        lines.append("No separate branch or worktree hygiene items were found.")
    if result["keep"]:
        lines.extend(["", f"Kept automatically with concrete evidence: {len(result['keep'])} path(s)."])
    lines.extend([
        "", "Triage and its exact inspections made no filesystem or Git mutations.",
        "Discovery `PD-...` IDs never authorize removal.",
        "A `PC-...` candidate still requires separate explicit approval and fresh Apply verification.",
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
    parser.add_argument("--max-leads", type=int, default=200, help="Bound discovery leads")
    parser.add_argument("--max-files", type=int, default=50000, help="Bound filesystem files examined")
    parser.add_argument("--max-hash-bytes", type=int, default=1024 * 1024 * 1024, help="Bound duplicate hashing")
    parser.add_argument("--max-inspections", type=int, default=50, help="Bound automatic exact inspections")
    parser.add_argument("--details-limit", type=int, default=10, help="Bound unresolved rows in Markdown")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.details_limit <= 0:
        print(json.dumps({"schema": OUTPUT_SCHEMA, "error": "details-limit must be positive"}, indent=2))
        return 1
    try:
        result = triage(
            Path(args.workspace), args.git_base, args.max_leads,
            args.max_files, args.max_hash_bytes, args.max_inspections,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"schema": OUTPUT_SCHEMA, "error": str(exc)}, indent=2))
        return 1
    if args.format == "markdown":
        sys.stdout.write(render_markdown(result, args.details_limit))
    else:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
