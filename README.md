# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable, contains its own tests when applicable, and has
no plugin or marketplace packaging. Repository-wide automation lives under
`.github/` so the root remains focused on installable skill packages.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Preserve evidence, decisions, and next actions for reliable context transfer between tasks. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Clean Up | Automatically resolve file, artifact, release, duplicate, organization, branch, worktree, and tracked-code evidence into safe keep, move, cleanup, or preservation decisions. | [`clean-up/`](clean-up/) |
| Simplify | Explain technical reports in everyday language without changing their conclusions. | [`simplify-report/`](simplify-report/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path `clean-handoff`, `clean-up`, `gameplan`, or
`simplify-report`. Start a new Codex task after installation so the skill
catalog refreshes.

## Clean Handoff

Clean Handoff preserves the context another task needs to continue accurately.
It prepares a copyable brief, uses available task tools for requested delivery,
and helps resume incoming work without repeating completed steps.

It carries:

- the goal, acceptance criteria, completed work, and remaining work;
- explicit user decisions, separately from assistant suggestions and unresolved ideas;
- decision-relevant source links, evidence, and validation results;
- required files, repository state, missing materials, and access limitations;
- the next authorized action and whether to start now or wait.

Research handoffs retain the source brief's evidence standard. This includes
independent pain evidence, competitor checks, payment evidence, and minimal
customer effort when those criteria apply. Copying a source link does not imply
that its claims were reverified.

Example requests:

- "Use $clean-handoff to prepare a copyable brief for this work."
- "Bring the context from my task named Research review into this task."
- "Use $clean-handoff to continue this in my existing task named Release review."
- "Create a new Codex task with this context."
- "Create a ChatGPT Work cloud task with this research brief."
- "Prepare this handoff for later; wait until I say start."
- "Use $clean-handoff to resume from this handoff in the current workspace."

Reading another conversation, delivering to an existing task, and creating a new
one depend on tools and access in the current environment. New tasks require an
explicit request. If delivery is unavailable, the skill returns a portable brief
and clearly reports that it has not been delivered.

Deferred handoffs carry an instruction to acknowledge receipt and wait for the
user to start. This is a recipient instruction, not an enforced scheduling
feature; delivery can trigger an acknowledgment run. If no run or setup is
allowed, the brief stays in the source unless a supported draft facility exists.

Native task migration is conditional on platform support and is distinct from
context delivery. Required files and local changes are accounted for separately;
a summary does not establish that they transferred. Cross-device delivery remains
unverified and is not a promised capability of this skill.

Context retrieval from an accessible ChatGPT conversation into a Codex task was
demonstrated during development. That result does not establish Work cloud mode,
file migration, or successful delivery in the opposite direction. The skill
reports prepared, pending, delivered, and acknowledged states separately.
Package and metadata checks validate structure, not end-to-end transfer behavior.

## Clean Up

Clean Up is an evidence-based repository and workspace maintenance skill. It
scans broadly, makes technical retention decisions automatically, and asks the
user only for approval before an exact filesystem or Git mutation.

It covers:

- generated build output, temporary residue, caches, artifacts, and old local
  releases;
- exact duplicate files and loose root files that belong in an established
  project directory;
- stale local branches and linked worktrees;
- tracked dead-code signals in C# and PowerShell, including modified files;
- ordinary folders as well as Git repositories and multi-worktree workspaces.

### Decision workflow

| Stage | What it does | Mutates anything? |
| --- | --- | --- |
| Triage | Runs the broad audit, investigates promising leads, and decides remove, move, keep, or preserve. | No |
| Discover | Produces the raw lead inventory when explicitly requested or when diagnosing Triage. | No |
| Inspect | Freezes exact path or Git targets and binds candidates to their current state. | No |
| Apply | Re-inspects approved candidates, quarantines recoverable data, validates the result, and rejects stale evidence. | Yes, with explicit approval |

Uncertain evidence defaults to keeping the item. Discovery, dead-code, and
organization IDs never authorize deletion. Cleanup and Git candidates require
their exact current IDs and separate approval, so a broad scan cannot silently
remove or reorganize a workspace.

### Quick start

Install `clean-up`, restart Codex so the skill catalog refreshes, then use:

```text
Use $clean-up to audit this workspace and automatically decide what should be
removed, moved, kept, or preserved across files, organization, Git hygiene,
and tracked code. Do not ask me to make technical retention decisions; ask
only for exact mutation approval.
```

The default Triage report leads with a plain verdict such as `clean`,
`cleanup-recommended`, `organization-recommended`, or `incomplete`, followed
by the exact action and evidence that matter.

## Repository validation

The shared validation workflow under [`.github/workflows/`](.github/workflows/)
checks all four skill packages on Windows, macOS, and Linux, runs Clean Handoff package and metadata tests,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.

See [source maintenance](CANONICAL-SOURCES.md) for synchronization rules and package provenance boundaries.
