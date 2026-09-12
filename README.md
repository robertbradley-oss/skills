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
| Practice Coach | Build understanding through adaptive exercises, feedback, and transfer checks. | [`practice-coach/`](practice-coach/) |
| Feedback to Findings | Synthesize existing feedback into traceable themes while preserving contradictions and sampling limits. | [`feedback-to-findings/`](feedback-to-findings/) |
| Check My Analysis | Review calculations, comparisons, and the evidence supporting analytical conclusions. | [`check-my-analysis/`](check-my-analysis/) |
| Measure Success | Define practical measures, baselines, justified targets, and guardrails for an initiative. | [`measure-success/`](measure-success/) |
| Research Brief | Create a self-contained research assignment with evidence standards and completion criteria. | [`research-brief/`](research-brief/) |
| UI Stress Test | Reproduce layout failures using content extremes, narrow containers, and relevant environment variations. | [`ui-stress-test/`](ui-stress-test/) |
| Form Flow Fixer | Diagnose and repair validation, submission, input preservation, and recovery behavior. | [`form-flow-fixer/`](form-flow-fixer/) |
| UI State Completeness | Find missing states and transition failures, including relevant async and lifecycle cases. | [`ui-state-completeness/`](ui-state-completeness/) |
| Design System Fit | Implement UI using evidence from the product's existing components and visual conventions. | [`design-system-fit/`](design-system-fit/) |
| Motion Resilience | Test animated interactions under interruption, reversal, repeated input, and reduced motion. | [`motion-resilience/`](motion-resilience/) |

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

## Learning, evidence, and measurement

These skills work from supplied context and use relevant tools or sources when
needed. They do not require a particular analytics platform or a learning workspace.

| Skill | Example request |
| --- | --- |
| Practice Coach | `Use $practice-coach to help me practice percentages and adapt the exercises to my answers.` |
| Feedback to Findings | `Use $feedback-to-findings to identify supported themes and conflicting experiences in these customer reviews.` |
| Check My Analysis | `Use $check-my-analysis to check whether this report's calculations and conclusions hold up.` |
| Measure Success | `Use $measure-success to define how we should evaluate this onboarding initiative.` |
| Research Brief | `Use $research-brief to write an assignment for comparing these options using consistent evidence.` |

Practice Coach checks demonstrated understanding rather than treating exposure
as learning. Feedback to Findings distinguishes repeated comments from independent
respondents. Check My Analysis assesses whether conclusions follow from evidence,
even when reported totals agree. Measure Success keeps targets grounded in a
baseline or an explicit requirement. Research Brief defines the investigation
without automatically starting it.

## UI implementation and robustness

These skills pair focused workflows with reusable content or event-sequence
fixtures, or a design-system comparison guide. Map the fixtures to an isolated
test environment and the project's existing browser tooling. Fixtures are test
inputs, not proof that the application passed.

| Skill | Example request |
| --- | --- |
| UI Stress Test | `Use $ui-stress-test to find and fix clipping in this dialog with long content and narrow widths.` |
| Form Flow Fixer | `Use $form-flow-fixer to fix this form's error handling and verify retry and keyboard completion.` |
| UI State Completeness | `Use $ui-state-completeness to check this search UI when responses arrive out of order.` |
| Design System Fit | `Use $design-system-fit to add this settings screen using our existing UI conventions.` |
| Motion Resilience | `Use $motion-resilience to test this drawer when it is rapidly opened, closed, and reopened.` |

Reviews report findings; requested fixes include scoped implementation and
reverification. Static inspection is kept distinct from browser evidence,
simulated request tests from real integration tests, and untested behavior
from passed checks.

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
checks all nineteen skill packages on Windows, macOS, and Linux, verifies Clean
Handoff against its locked canonical source, runs its syntax and test gates,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.
