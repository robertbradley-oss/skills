# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable and contains no plugin or marketplace packaging.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Post Clean | Review GamePlan task footprints and perform explicitly approved cleanup safely. | [`post-clean/`](post-clean/) |

Install either package with Codex's `$skill-installer` using this repository and
the package path `gameplan` or `post-clean`. Start a new Codex task after
installation so the skill catalog refreshes.

## Planned migration

Clean Handoff will join this repository only after its standalone
`clean-handoff` rebuild passes migration, installation, and workflow validation.
The current Clean Handoff repositories remain authoritative until then.

## Retired products

ScopeLock remains preserved in its own archived repository. See
[`RETIRED.md`](RETIRED.md) for the historical pointer; its source is not copied
into this active-skills repository.

## Repository validation

The shared validation workflow checks both skill packages on Windows, macOS,
and Linux, compiles the Post Clean helpers, and runs the Post Clean test suite.
