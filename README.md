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
| Clean Up | Finish implementation tasks with scoped simplification, organization, cleanup, and validation, or audit workspace cleanup candidates. | [`clean-up/`](clean-up/) |
| Simplify | Explain technical reports in everyday language without changing their conclusions. | [`simplify-report/`](simplify-report/) |
| Knowledge Interview | Turn practical expertise into usable guides, procedures, or onboarding material through a focused interview. | [`knowledge-interview/`](knowledge-interview/) |
| Proposal Reviewer | Test consequential proposal claims against evidence and identify questions that could change the decision. | [`proposal-reviewer/`](proposal-reviewer/) |
| Meeting Brief | Prepare focused meeting briefs and capture supported decisions and actions from meeting notes. | [`meeting-brief/`](meeting-brief/) |
| Decision Coach | Clarify priorities, compare alternatives, and identify evidence that would change a choice. | [`decision-coach/`](decision-coach/) |
| Reconcile Reports | Explain conflicting report totals by aligning definitions and quantifying adjustments and unresolved gaps. | [`reconcile-reports/`](reconcile-reports/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path from the table above. For example:

```text
Use $skill-installer to install knowledge-interview from
https://github.com/robertbradley-oss/skills.
```

Start a new Codex task after installation so the skill catalog refreshes.

## Interviews, reviews, and decisions

The five skills below work from conversation, supplied files, or relevant
available sources without requiring a particular app or connector.

| Skill | Example request |
| --- | --- |
| Knowledge Interview | `Use $knowledge-interview to interview me about this process and write a guide a new teammate can follow.` |
| Proposal Reviewer | `Use $proposal-reviewer to assess this vendor proposal and identify the evidence we need before deciding.` |
| Meeting Brief | `Use $meeting-brief to prepare for this meeting using these notes and the decisions we need to make.` |
| Decision Coach | `Use $decision-coach to help me compare these options against my priorities.` |
| Reconcile Reports | `Use $reconcile-reports to explain why these spreadsheets show different totals and quantify any remaining gap.` |

Knowledge Interview elicits examples and exceptions instead of assuming the
reader has the expert's background. Proposal Reviewer separates claims from
proof. Meeting Brief distinguishes suggestions from confirmed commitments.
Decision Coach elicits priorities before suggesting answers when those
priorities affect the choice. Reconcile Reports preserves source data and
shows how much of the difference is explained.

## Clean Up

Clean Up supports two workflows: finishing an implementation task and auditing
a workspace. Task finishing carries out relevant authorized code edits and file
moves, updates references, investigates leftovers, and validates the result.
Broad audit questions remain read-only until exact removals are approved.

### Task finishing

The [task-finishing workflow](clean-up/TASK_FINISHING.md) reviews the requested
outcome and affected files, completes unfinished integration, simplifies code
where behavior is understood, and places files according to project conventions.
It preserves unrelated work and does not expand into a repository-wide rewrite.
Unused-code signals require context review before editing.

Routine reversible edits within the authorized task proceed without repeated
approval. Whole-file, directory, branch, and worktree removals retain the existing
exact-target inspection, approval, stale-evidence, and recovery checks. The agent
finishes independent edits and validation before requesting any remaining removal
approval. A task-scoped review does not establish that the whole repository is clean.

### Workspace audit

It covers:

- generated build output, temporary residue, caches, artifacts, and old local
  releases;
- exact duplicate files and loose root files that belong in an established
  project directory;
- stale local branches and linked worktrees;
- tracked dead-code signals in C#, PowerShell, JavaScript/JSX, and TypeScript/TSX,
  including modified files;
- ordinary folders as well as Git repositories and multi-worktree workspaces.

### Decision workflow

| Stage | What it does | Mutates anything? |
| --- | --- | --- |
| Task finishing | Completes scoped implementation, simplifies code, organizes affected files, and validates behavior. | Authorized edits and moves; removals use Inspect and Apply |
| Triage | Runs the broad audit, investigates promising leads, and decides remove, move, keep, or preserve. | No |
| Discover | Produces the raw lead inventory when explicitly requested or when diagnosing Triage. | No |
| Inspect | Freezes exact path or Git targets and binds candidates to their current state. | No |
| Apply | Re-inspects approved candidates, quarantines recoverable data, validates the result, and rejects stale evidence. | Yes, with explicit approval |

Uncertain evidence defaults to keeping the item. Discovery, dead-code, and
organization IDs never authorize deletion. Cleanup and Git candidates require
their exact current IDs and separate approval, so a broad scan cannot silently
remove or reorganize a workspace.

The [audit and removal operations](clean-up/OPERATIONS.md) document the scripts
and evidence requirements. Duplicate findings remain report-only; audit code and
organization findings require the editing workflow to implement justified changes.

### Quick start

Install `clean-up`, restart Codex so the skill catalog refreshes, then use:

```text
Use $clean-up to finish this implementation task: complete remaining work,
simplify the affected code, organize files and update references, inspect
leftovers, and run relevant validation. Keep unrelated work intact.
```

For a read-only workspace audit:

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
checks all nine skill packages on Windows, macOS, and Linux, verifies Clean
Handoff against its locked canonical source, runs its syntax and test gates,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.
