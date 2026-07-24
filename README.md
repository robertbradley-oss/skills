# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable and contains no plugin or marketplace packaging.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Create trustworthy project handoffs for fresh Codex tasks. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Post Clean | Review GamePlan task footprints and perform explicitly approved cleanup safely. | [`post-clean/`](post-clean/) |
| Simplify | Explain technical reports in everyday language without changing their conclusions. | [`simplify-report/`](simplify-report/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path `clean-handoff`, `gameplan`, `post-clean`, or
`simplify-report`. Start a new Codex task after installation so the skill
catalog refreshes.

## Repository validation

The shared validation workflow checks all four skill packages on Windows,
macOS, and Linux, verifies Clean Handoff against its locked canonical source,
runs its syntax and test gates, compiles the Post Clean helpers, and runs the
Post Clean and Simplify test suites.
