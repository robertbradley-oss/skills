# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable and contains no plugin or marketplace packaging.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Create trustworthy project handoffs for fresh Codex tasks. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Post Clean | Review GamePlan task footprints and perform explicitly approved cleanup safely. | [`post-clean/`](post-clean/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path `clean-handoff`, `gameplan`, or `post-clean`. Start a new Codex
task after installation so the skill catalog refreshes.

## Canonical source

The `clean-handoff/` package is a byte-identical distribution of the canonical
[`robertbradley-oss/clean-handoff`](https://github.com/robertbradley-oss/clean-handoff)
standalone repository. This umbrella copy is installable, but it is not a
second implementation authority; Clean Handoff changes originate in the
canonical repository and are imported here only after validation.

## Retired products

ScopeLock remains preserved in its own archived repository. See
[`RETIRED.md`](RETIRED.md) for the historical pointer; its source is not copied
into this active-skills repository.

## Repository validation

The shared validation workflow checks all three skill packages on Windows,
macOS, and Linux, verifies Clean Handoff against its locked canonical source,
runs its syntax and test gates, compiles the Post Clean helpers, and runs the
Post Clean test suite.
