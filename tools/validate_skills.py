#!/usr/bin/env python3
"""Validate every active skill package in this repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("clean-handoff", "gameplan", "post-clean", "simplify-report")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)


def fail(message: str) -> None:
    raise ValueError(message)


def validate_skill(directory_name: str) -> None:
    skill_dir = ROOT / directory_name
    skill_file = skill_dir / "SKILL.md"
    agent_file = skill_dir / "agents" / "openai.yaml"

    if not skill_file.is_file():
        fail(f"{directory_name}: SKILL.md is missing")
    if not agent_file.is_file():
        fail(f"{directory_name}: agents/openai.yaml is missing")

    content = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)
    if match is None:
        fail(f"{directory_name}: invalid YAML frontmatter boundary")

    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        fail(f"{directory_name}: frontmatter must be a mapping")
    if set(frontmatter) != {"name", "description"}:
        fail(f"{directory_name}: frontmatter must contain only name and description")

    name = frontmatter["name"]
    description = frontmatter["description"]
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        fail(f"{directory_name}: name must use lowercase hyphen-case")
    if name != directory_name:
        fail(f"{directory_name}: folder and frontmatter names differ")
    if len(name) > 64:
        fail(f"{directory_name}: name exceeds 64 characters")
    if not isinstance(description, str) or not description.strip():
        fail(f"{directory_name}: description must be a non-empty string")
    if len(description) > 1024 or "<" in description or ">" in description:
        fail(f"{directory_name}: description violates length or character rules")
    if len(content.splitlines()) > 500:
        fail(f"{directory_name}: SKILL.md exceeds the 500-line context guideline")

    agent_metadata = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
    if not isinstance(agent_metadata, dict) or not isinstance(agent_metadata.get("interface"), dict):
        fail(f"{directory_name}: agents/openai.yaml lacks interface metadata")
    interface = agent_metadata["interface"]
    for field in ("display_name", "short_description", "default_prompt"):
        if not isinstance(interface.get(field), str) or not interface[field].strip():
            fail(f"{directory_name}: interface.{field} must be a non-empty string")


def main() -> int:
    try:
        for skill in SKILLS:
            validate_skill(skill)
            print(f"validated {skill}")
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
