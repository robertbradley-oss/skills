# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable, contains its own tests when applicable, and has
no plugin or marketplace packaging. Repository-wide automation lives under
`.github/` so the root remains focused on installable skill packages.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Create trustworthy project handoffs for fresh Codex tasks. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Clean Up | Resolve file, artifact, release, duplicate, branch, and worktree evidence into safe cleanup verdicts and approved recovery-backed removal. | [`clean-up/`](clean-up/) |
| Simplify | Explain technical reports in everyday language without changing their conclusions. | [`simplify-report/`](simplify-report/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path `clean-handoff`, `clean-up`, `gameplan`, or
`simplify-report`. Start a new Codex task after installation so the skill
catalog refreshes.

## Repository validation

The shared validation workflow under [`.github/workflows/`](.github/workflows/)
checks all four skill packages on Windows, macOS, and Linux, verifies Clean
Handoff against its locked canonical source, runs its syntax and test gates,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.
