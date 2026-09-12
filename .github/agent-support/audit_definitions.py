#!/usr/bin/env python3
"""Read-only structural checks for SKILL.md and *.agent.md. Requires PyYAML."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than silently accepting the last value."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.S)
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+\"[^\"]*\")?\s*\)")
AGENT_FIELDS = {
    "name", "description", "tools", "target", "model", "disable-model-invocation",
    "user-invocable", "infer", "mcp-servers", "metadata",
}
EXCLUDED = {".git", "node_modules", ".venv", "venv", "__pycache__"}


def prose_lines(text):
    """Ignore fenced examples and single-line inline code for link checks."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            yield number, re.sub(r"(`+).*?\1", "", line)


def audit_file(path, root):
    findings = []

    def add(code, message, line=1, severity="error"):
        findings.append(dict(file=path.relative_to(root).as_posix(), line=line,
                             severity=severity, code=code, message=message))

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        add("read", str(error))
        return findings
    match = FRONT.match(text)
    if not match:
        add("frontmatter", "Missing or malformed YAML frontmatter boundary")
        return findings
    try:
        meta = yaml.load(match.group(1), Loader=UniqueLoader)
    except (yaml.YAMLError, ValueError, TypeError) as error:
        add("yaml", str(error))
        return findings
    if not isinstance(meta, dict):
        add("mapping", "Frontmatter must be a mapping")
        return findings
    if not isinstance(meta.get("description"), str) or not meta["description"].strip():
        add("description", "Description must be a non-empty string")
    body = text[match.end():]
    if not body.strip():
        add("body", "Instruction body is empty")
    if path.name == "SKILL.md":
        name = meta.get("name")
        if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
            add("name", "Skill name must use lowercase hyphen-case, at most 64 characters")
        elif name != path.parent.name:
            add("name", "Skill name differs from its directory")
    else:
        if len(body) > 30000:
            add("body-length", "Agent prompt exceeds 30,000 characters")
        for field in meta:
            if field not in AGENT_FIELDS:
                add("host-field", f"Verify host support for property: {field}", severity="warning")
        for field in ("name", "model"):
            if field in meta and (not isinstance(meta[field], str) or not meta[field].strip()):
                add(field, f"{field} must be a non-empty string")
        if "target" in meta and meta["target"] not in ("vscode", "github-copilot"):
            add("target", "Target must be vscode or github-copilot")
        for field in ("disable-model-invocation", "user-invocable", "infer"):
            if field in meta and not isinstance(meta[field], bool):
                add(field, f"{field} must be boolean")
        if "tools" in meta:
            tools = meta["tools"]
            if not (isinstance(tools, str) or
                    isinstance(tools, list) and all(isinstance(t, str) and t.strip() for t in tools)):
                add("tools", "Tools must be a string or a list of non-empty strings")

    for number, line in prose_lines(text):
        for link in LINK.finditer(line):
            destination = link.group(1) or link.group(2)
            try:
                url = urlsplit(destination)
                if url.scheme or url.netloc or not url.path:
                    continue
                relative = unquote(url.path)
                target = (root / relative.lstrip("/") if relative.startswith("/")
                          else path.parent / relative).resolve()
                if not target.is_relative_to(root):
                    add("outside-root", f"Local link leaves audit root: {destination}", number, "warning")
                elif not target.exists():
                    add("broken-link", f"Missing local link: {destination}", number)
            except (ValueError, OSError) as error:
                add("link", f"Cannot resolve link: {error}", number)
    return findings


def audit(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Audit root is not a directory: {root}")
    files = sorted(p for p in root.rglob("*")
                   if (p.name == "SKILL.md" or p.name.endswith(".agent.md"))
                   and not any(part in EXCLUDED for part in p.relative_to(root).parts)
                   and p.is_file() and not p.is_symlink()
                   and p.resolve().is_relative_to(root))
    findings = [finding for path in files for finding in audit_file(path, root)]
    if not files:
        findings.append(dict(file=".", line=1, severity="error", code="empty",
                             message="No SKILL.md or *.agent.md definitions found"))
    return dict(files_checked=len(files), findings=findings,
                errors=sum(f["severity"] == "error" for f in findings),
                warnings=sum(f["severity"] == "warning" for f in findings))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.directory)
    except (OSError, ValueError) as error:
        parser.exit(2, f"audit failed: {error}\n")
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
