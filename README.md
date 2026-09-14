# RobertOS Skills and Agents

Reusable Codex skills and GitHub Copilot agents maintained by RobertOS.
Each top-level skill directory is independently installable and contains its
own tests when applicable. Copilot agent profiles and their supporting tools
live under `.github/`, alongside repository-wide automation.

## GitHub Copilot agents

| Agent | Job | Example request |
| --- | --- | --- |
| [Bug Reproducer](.github/agents/bug-reproducer.agent.md) | Demonstrate a reported bug with an executed regression test, or explain why reproduction is blocked. | `Reproduce issue 123 with a regression test. Do not fix production code.` |
| [Docs Verifier](.github/agents/docs-verifier.agent.md) | Check documented setup and examples in a fresh environment, then correct supported documentation errors. | `Verify the README quick start in a fresh environment and fix documentation errors.` |
| [Skill Auditor](.github/agents/skill-auditor.agent.md) | Check definitions for structural defects, broken local references, and conflicting instructions. | `Audit these skill definitions. Separate structural errors from instruction concerns.` |
| [Release Evidence](.github/agents/release-evidence.agent.md) | Connect release changes to exact commits, CI, deployment, and live verification evidence. | `Report what shipped between these two SHAs to staging and identify verification gaps.` |

### Use an agent

1. Open [GitHub Agents](https://github.com/copilot/agents) and select
   `robertbradley-oss/skills` as the repository.
2. Select a custom agent and submit a task, such as one of the examples above.
   Availability depends on your Copilot account and repository configuration.
3. To use an agent on your own code, copy its `.agent.md` file into your target
   repository's `.github/agents/` directory and commit it to the default branch.
   Profiles here do not automatically apply to other repositories.

In Copilot CLI, use `/agent` to choose an available profile. Skill Auditor's
optional Python checker can be copied with the supporting directory; see the
setup guide for its dependency and command.

See [setup, examples, and validation](.github/agent-support/README.md) to use them
here or copy them into another repository. These are Copilot agent profiles;
the Codex skill packages below remain independently installable.

Structural validation and helper tests run in CI. Hosted Copilot behavior
evaluations have not been run; [evaluation cases](.github/agent-support/EVALUATION.md)
define the evidence needed to assess each agent.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Preserve evidence, decisions, and next actions for reliable context transfer between tasks. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Keep a project plan current and track which work is approved. | [`gameplan/`](gameplan/) |
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

Clean Handoff is maintained directly in this repository; its earlier external
snapshot is historical rather than a required byte-for-byte source.

Context retrieval from an accessible ChatGPT conversation into a Codex task was
demonstrated during development. That result does not establish Work cloud mode,
file migration, or successful delivery in the opposite direction. The skill
reports prepared, pending, delivered, and acknowledged states separately.
Package and metadata checks validate structure, not end-to-end transfer behavior.

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
checks all nineteen skill packages on Windows, macOS, and Linux, runs Clean
Handoff package and metadata tests,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites. It also validates all four Copilot agent profiles and runs
the definition auditor's tests. These automated checks do not establish agent
reasoning quality or successful execution in a hosted Copilot session.
