# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable, contains its own tests when applicable, and has
no plugin or marketplace packaging. Repository-wide automation lives under
`.github/` so the root remains focused on installable skill packages.

## Active skills

This repository maintains all 54 user skill packages. System skills and vendor plugin caches are excluded. Existing package licenses and notices are retained.

| Package | Purpose |
| --- | --- |
| [accessibility](accessibility/SKILL.md) | Audit or fix web accessibility when accessibility is the primary task. |
| [animation-vocabulary](animation-vocabulary/SKILL.md) | Name a web animation effect from its visual description. |
| [apple-design](apple-design/SKILL.md) | Design Apple-style web interactions, gestures, and materials when requested. |
| [better-colors](better-colors/SKILL.md) | Create or review color palettes, tokens, contrast, and gamut behavior. |
| [better-layout](better-layout/SKILL.md) | Design or review web layout, grouping, spacing, and responsive structure. |
| [better-typography](better-typography/SKILL.md) | Choose or review web typography, text wrapping, and font behavior. |
| [better-writing](better-writing/SKILL.md) | Write or review interface labels, instructions, errors, and empty states. |
| [brain-to-docs](brain-to-docs/SKILL.md) | Interview the user to capture project vision and decisions in maintained documentation. |
| [claimguardagent](claimguardagent/SKILL.md) | Handle explicit ClaimGuard agent requests using current repository instructions. |
| [clean-handoff](clean-handoff/SKILL.md) | Prepare a concise handoff or create a new task when explicitly requested. |
| [clean-up](clean-up/SKILL.md) | Audit workspace cleanup candidates and apply specifically authorized cleanup. |
| [codex-goal-loop](codex-goal-loop/SKILL.md) | Draft and manage explicitly requested Codex goal runs and their completion conditions. |
| [core-web-vitals](core-web-vitals/SKILL.md) | Diagnose and improve measured LCP, INP, or CLS problems. |
| [daily-gmail-cleanup](daily-gmail-cleanup/SKILL.md) | Run or review Robert's established Gmail inbox cleanup policy. |
| [define-goal](define-goal/SKILL.md) | Define or refine a goal and create it only when explicitly requested. |
| [delegating-to-agents](delegating-to-agents/SKILL.md) | Plan and coordinate authorized subagent work with distinct ownership. |
| [effective-agent-skills](effective-agent-skills/SKILL.md) | Audit skill routing, instruction scope, and progressive disclosure. |
| [emil-design-eng](emil-design-eng/SKILL.md) | Implement or refine a specific web animation or interaction detail. |
| [find-animation-opportunities](find-animation-opportunities/SKILL.md) | Find useful motion opportunities in an interface without editing during an audit. |
| [frontend-skill](frontend-skill/SKILL.md) | Establish visual direction for a new or substantially redesigned web experience. |
| [frontend-ui-engineering](frontend-ui-engineering/SKILL.md) | Implement web UI in the project's component and design conventions. |
| [gameplan](gameplan/SKILL.md) | Create, recall, or revise a durable GamePlan when requested. |
| [grill-me](grill-me/SKILL.md) | Stress-test a plan or decision through an interactive interview when requested. |
| [improve-animations](improve-animations/SKILL.md) | Audit motion across a codebase or prepare implementation plans when requested. |
| [ispring-handoff](ispring-handoff/SKILL.md) | Preserve weekly iSpring KPI candidates across project-chat continuations. |
| [jupyter-notebook](jupyter-notebook/SKILL.md) | Create or edit reproducible Jupyter notebooks. |
| [layers-conceptual-model](layers-conceptual-model/SKILL.md) | Define product objects, relationships, states, and vocabulary. |
| [layers-domain](layers-domain/SKILL.md) | Map domain concepts, processes, and terminology conflicts. |
| [layers-interaction-flow](layers-interaction-flow/SKILL.md) | Design task flows, interaction destinations, and failure paths. |
| [layers-intro](layers-intro/SKILL.md) | Explain the Layers of Product Design framework when needed. |
| [layers-observed-behaviour](layers-observed-behaviour/SKILL.md) | Plan user research or synthesize behavioral evidence. |
| [layers-orient](layers-orient/SKILL.md) | Identify the unresolved design decision causing a product problem. |
| [layers-product-strategy](layers-product-strategy/SKILL.md) | Connect user opportunities to product bets and experiments. |
| [layers-surface](layers-surface/SKILL.md) | Review whether interface details match the product model and task flow. |
| [layers-user-needs](layers-user-needs/SKILL.md) | Identify and prioritize user needs from available evidence. |
| [no-ai-slop](no-ai-slop/SKILL.md) | Edit a draft for clarity and voice, or flag writing patterns without rewriting. |
| [performance](performance/SKILL.md) | Diagnose and improve measured web loading or runtime performance. |
| [playwright](playwright/SKILL.md) | Automate a browser through Playwright CLI when that tool is appropriate. |
| [preferred-ui-libraries](preferred-ui-libraries/SKILL.md) | Consult Robert's UI-library preferences when selecting a new component dependency. |
| [read-all-adrs](read-all-adrs/SKILL.md) | Read every ADR when the user explicitly requests complete decision-history intake. |
| [repreportagent](repreportagent/SKILL.md) | Handle explicit RepReport agent requests using current repository instructions. |
| [research-prompt](research-prompt/SKILL.md) | Write a research brief for another researcher or research agent. |
| [review-animations](review-animations/SKILL.md) | Review a selected motion change for observable usability and performance issues. |
| [robert-workflow](robert-workflow/SKILL.md) | Coordinate workflow choices when Robert asks how to approach a task. |
| [run-general-qa](run-general-qa/SKILL.md) | Run a broad project QA audit and report verified coverage and gaps. |
| [screenshot](screenshot/SKILL.md) | Capture a desktop screenshot when requested or no suitable app capture exists. |
| [security-best-practices](security-best-practices/SKILL.md) | Review security practices or implement requested secure defaults for supported stacks. |
| [security-ownership-map](security-ownership-map/SKILL.md) | Analyze security ownership and bus-factor risk from Git history. |
| [security-threat-model](security-threat-model/SKILL.md) | Produce a repository-grounded threat model when requested. |
| [simplify-report](simplify-report/SKILL.md) | Explain a supplied technical report without rerunning its checks. |
| [teach](teach/SKILL.md) | Create and maintain a learning workspace for an ongoing study request. |
| [transcribe](transcribe/SKILL.md) | Transcribe audio or video with optional speaker labels. |
| [vercel-deploy](vercel-deploy/SKILL.md) | Deploy to Vercel when requested, respecting the specified target environment. |
| [visual-ui-qa](visual-ui-qa/SKILL.md) | Inspect or verify a running web interface's visual and interaction behavior. |

Install a package with Codex's skill installer using this repository and its directory name. Start a new task afterward to refresh the catalog. See [source maintenance](CANONICAL-SOURCES.md) before synchronizing an existing installation.

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
checks every skill package on Windows, macOS, and Linux, runs Clean
Handoff contract tests,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.
