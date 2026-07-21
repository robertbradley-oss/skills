---
name: gameplan
description: Create, lock, recall, orient from, challenge, execute, validate, and update a durable workspace GAMEPLAN.md as the single authority for Outcome, Strategy, Guardrails, and at most one explicitly approved execution slice. Use when the user invokes `$gameplan`; asks to lock in, save, or remember an agreed plan; executes work under a locked plan; needs explicit approval before strategy changes or scope expansion; requires direct validation evidence and close-through-Update; prepares completed work for cleanup with non-authoritative Task Footprints; needs status or a next recommendation; or wants the current plan stress-tested.
---

# GamePlan

Preserve strategic continuity across tasks with one canonical `GAMEPLAN.md`. Treat it as durable operating context, not merely a checklist.

## Locate the canonical plan

1. Use a plan path explicitly named by the user.
2. Otherwise, look for `GAMEPLAN.md` at the workspace root.
3. If none exists and the user asks to lock or create a plan, create it from `assets/GAMEPLAN.template.md` at the workspace root.
4. If none exists for a read-only operation, say that no game plan is locked yet and offer to create one.
5. If multiple plausible plans exist and the intended plan cannot be inferred safely, ask which one governs the work.

Read the complete canonical plan before recalling it, reporting status, updating it, challenging it, or recommending work from it.

## Interpret the operation

Map explicit commands and natural-language equivalents to these operations:

- **Lock**: Convert an agreed direction into the canonical plan, locking the strategic core and optionally one explicitly approved execution slice.
- **Recall**: Restate the plan faithfully and concisely.
- **Orient**: Explain the destination, current position, important changes, and next move.
- **Status**: Report completed, active, blocked, and next work against the plan.
- **Recommend**: Refresh from the plan and current evidence, then recommend one next task.
- **Update**: Patch progress, evidence, decisions, or affected strategy sections.
- **Challenge**: Stress-test assumptions and recommend revisions without applying them silently.

If the request combines operations, perform them in dependency order: recall or inspect, update if explicitly requested, then orient or recommend.

When the user asks for write-based project work under a locked plan, apply the approved-slice preflight below before any task mutation.

## Preserve authority and intent

- Treat the user's current explicit instruction as authoritative.
- Treat locked Outcome, Strategy, and Guardrails as governing context until the user explicitly changes them.
- Treat the Approved Execution Slice, when present, as the only current implementation authority inside GamePlan. Its absence means GamePlan has approved no write-based execution slice.
- Treat Workstreams, Current State, and Next Move as operational state that may evolve as work progresses.
- Distinguish agreements from brainstorming, alternatives, and assistant suggestions.
- Do not convert an unresolved idea into a locked decision.
- Do not reopen a settled decision solely because another approach appears attractive.
- Surface conflicts between a proposed action and the locked plan before proceeding.
- Ask only when an ambiguity would materially change the outcome, strategy, guardrails, or irreversible work.
- Label material inferences and facts that may be stale.

## Model the approved execution slice

Keep all normative execution authority visible in the canonical `GAMEPLAN.md`. Never create an auxiliary active pointer, hidden contract, repository baseline, or parallel lifecycle to select or broaden a slice.

A strategic-only Lock is valid. In that case, set `Approved Execution Slice` to `None approved`. A Lock that authorizes immediate implementation may contain at most one slice with:

- Approval date and explicit user authority
- Objective
- Allowed files, expressed as exact workspace-relative files or directory prefixes
- Constraints, including explicit forbidden paths when needed
- Completion criteria
- Exact validation commands
- Validation authorization
- Concise evidence state or a pointer to detailed evidence

Apply these contract rules:

- Require a concrete objective and at least one allowed file or directory.
- Treat unlisted paths as outside the slice. The whole workspace rule `.` is valid only when the user explicitly approves it.
- Keep Outcome, Strategy, and Guardrails separate from the slice. A file-scope change must not silently revise strategy, and a strategy revision must not masquerade as a scope amendment.
- If the user explicitly supplies every material slice field, Lock may record the slice as approved without redundant confirmation.
- If GamePlan infers a material objective, path, constraint, completion criterion, validation command, or authorization boundary, present the complete proposed slice and wait for explicit approval before marking it approved.
- Never infer approval from repository contents, an existing task footprint, a work report, prior ScopeLock state, or assistant-authored prose.
- Listed validation commands are expectations unless `Validation authorization` explicitly grants standing authority. Standing authority applies only to the exact, project-local, non-destructive commands the user approved; risky or externally mutating commands still require contemporaneous approval.
- Any later expansion of allowed paths, relaxation of constraints or completion criteria, replacement of the objective, or change to validation authority requires explicit user approval.

Keep artifact roles distinct:

| Artifact | Role | Authority |
|---|---|---|
| `GAMEPLAN.md` | Strategic and execution authority | Normative |
| Approved Execution Slice | One current implementation boundary inside `GAMEPLAN.md` | Normative within its approved fields |
| Task Footprint or compiled footprint | Cleanup provenance | Never execution authority |
| Work report | Detailed validation evidence | Never execution authority |
| Helper or external product evidence | Supporting context | Never selects or broadens the slice |

## Execute under an approved slice

Before write-based project execution, read the complete canonical plan and perform this preflight:

1. Confirm `Approved Execution Slice` contains exactly one explicitly approved slice rather than `None approved` or a proposal awaiting approval.
2. Confirm the requested work fits the approved objective and locked strategic core.
3. Enumerate every intended write path, including `GAMEPLAN.md`, the task footprint, and any evidence report needed during execution or phase closure. GamePlan administrative artifacts receive no implicit sideband exception; they must appear in Allowed files.
4. Normalize intended paths to workspace-relative `/` form. Reject empty paths, absolute paths, drive-qualified paths, traversal with `..`, and wildcard or regular-expression syntax. Match an exact file only to itself and a directory prefix ending in `/` to its descendants.
5. Apply explicit forbidden paths or constraints before allowed paths. Treat every unlisted path as outside the slice.
6. Confirm the intended actions preserve all slice constraints, completion criteria, and validation-authorization limits.
7. Only after the preflight passes, begin the task footprint before the first authorized task mutation and proceed.

A direct user-authorized Lock or Update may modify the canonical plan to propose, approve, narrow, close, or replace a slice without an already active slice. That administrative plan change authorizes no other file mutation and must preserve the strategic approval rules.

### Stay within the boundary

- Work inside the approved objective, paths, constraints, criteria, and validation authority without reopening settled strategy.
- Preserve unrelated and pre-existing changes. Do not attribute a repository change to the current task when concurrent or prior work makes authorship uncertain.
- Keep the footprint current as allowed artifacts are created, adopted, abandoned, or reclassified, but never treat footprint contents as permission.
- Before a phase is reported complete or the next phase is proposed, update the canonical plan from direct evidence as required by its Guardrails.

### Handle dirty, missing, concurrent, and interrupted state

- A dirty worktree or untracked path is context, not authorship evidence and not automatic failure. Capture the exact pre-write state in the footprint, protect every pre-existing dirty path, and do not inspect untracked contents merely to classify provenance.
- An allowed path grants permission to use that exact path; it does not prove the path exists or authorize a substitute. Create a missing allowed path only when the approved objective or criteria clearly require its creation. If an expected pre-existing input is missing or creation intent is ambiguous, stop, keep the slice active, record the blocker in Current State, and do not synthesize, redirect, or use another path.
- Preserve concurrent unrelated changes outside the slice. If an intended target changes after preflight or overlapping authorship becomes uncertain, re-read the current canonical plan and target state, pause before overwriting, and report the uncertainty. Obtain approval for any changed objective, path, constraint, criterion, or validation authority.
- If execution is interrupted, leave the Approved Execution Slice and footprint active. Record what is complete, incomplete, or uncertain without claiming closure. On resume, re-read the complete plan, repeat preflight for every remaining write, and treat earlier validation as stale when relevant implementation or target state changed.

### Stop for scope expansion

Before touching an unlisted path, relaxing a constraint or completion criterion, replacing the objective, or changing validation authority:

1. Stop before the mutation or command.
2. State the exact proposed change, why it is needed, and which completion criterion it affects.
3. Keep strategy unchanged and request explicit approval for the complete revised slice.
4. If approved, patch the canonical slice before proceeding and preserve a dated Decision when the change is decision-relevant.
5. If work already occurred outside the slice, report it honestly; later approval does not rewrite its history as originally authorized.

Never infer expansion approval from code changes, a dependency installation, a footprint, validation output, prior ScopeLock state, or a user's approval of a different phase.

### Separate strategy conflicts

If execution conflicts with Outcome, Strategy, or Guardrails, stop and explain the strategic conflict separately from file scope. Require explicit strategy approval, record the dated revision and rationale, and only then align or replace the execution slice. A scope amendment alone cannot change strategic authority.

### Surface the slice without parallel status

- Recall names whether a slice is approved but does not reinterpret it.
- Orient includes the approved objective and boundary between current position and next move.
- Status reports the slice under the existing active or blocked categories, including any approval needed; do not invent lifecycle, health, or report-outcome enums.
- Recommend either names one next task that fits the approved slice or, when no slice is approved, recommends one concrete slice for approval. A recommendation alone grants no authority.

## Validate and close an approved execution slice

Treat completion evidence as support for a targeted GamePlan Update, never as new authority or a parallel closure system. A changed file, a passing command, or an assistant summary does not establish completion by itself.

### Build direct evidence for every criterion

Before closing a slice, enumerate every completion criterion and record one evidence entry for each criterion in the canonical plan or, when detail matters, in the slice's allowed work report. Each entry must contain:

- the completion criterion being evaluated;
- the exact inspection target or exact approved validation command used;
- the observation timestamp, including timezone when available;
- the command exit status, or the observed outcome for an inspection;
- a concise result summary; and
- an exact evidence pointer when supporting detail lives outside `GAMEPLAN.md`.

Apply these evidence rules:

- Mark a criterion verified only from a directly observed result that actually tests the criterion. Label interpretations as `inferred` and missing, ambiguous, or contradictory results as `uncertain`; neither label satisfies completion.
- Run only the exact commands covered by the slice's validation authorization. A changed command, new dependency, risky action, or externally mutating check requires approval before use.
- Preserve failed output and limitations honestly. Do not turn a partial pass, missing command, unreadable artifact, or absent reference into success.
- Treat evidence as stale when relevant implementation changed after it was observed. Re-run the approved validation or keep the criterion incomplete.
- Confirm that every task write stayed within Allowed files and preserved the objective, constraints, strategic core, and protected pre-existing work. A later approval does not retroactively cure an out-of-scope write.
- Require all criteria to be directly verified and every required validation command to pass before closure. One failed, incomplete, stale, inferred, or uncertain item keeps the slice active.

### Keep failed or incomplete validation active

When any completion mark is missing:

1. Preserve the Approved Execution Slice unchanged; do not set it to `None approved`.
2. Keep the task footprint active and retain all provenance recorded so far.
3. Update Current State under Active or Blocked with the exact failed criterion, observed result, and what would clear it.
4. Set Next Move to the smallest in-scope repair or approved revalidation action. Do not advance to the next phase or imply its approval.
5. Preserve Outcome, Strategy, Guardrails, and Decisions unless the user separately approves a strategic revision.
6. Put detailed output in the allowed evidence report and keep only a concise evidence pointer in the canonical plan.

Failure is ordinary operational evidence, not a new lifecycle state. Do not add `failed`, `closed`, `abandoned`, health, finding, or report-outcome authority alongside Current State and the Approved Execution Slice.

### Close through one targeted Update

Close only after the complete evidence set, scope review, and footprint review all pass. Prepare one bounded closure change that:

1. compacts the durable outcome into Current State and removes superseded active or blocked narration;
2. advances Next Move to one concrete proposal or task without approving a new slice;
3. preserves Outcome, Strategy, Guardrails, Open Questions, Refresh Triggers, and the complete Decisions history;
4. replaces the approved slice with `None approved` plus a concise closure date and evidence pointer;
5. finalizes the task footprint in the same bounded change and updates the canonical Task Footprint pointer; and
6. applies the Update compaction gate before completion is reported.

Inspect the prepared change before applying it. If the canonical close, footprint finalization, or compaction gate cannot be completed together, leave the slice active and record the blocker instead. After applying the closure, inspect the canonical sections directly; if they do not match the proven evidence, treat the phase as incomplete and correct the administrative Update before reporting.

`None approved` means no write-based execution is authorized. It is not a `closed` lifecycle value. Preserve historical completion through the compact Current State milestone, Decisions when decision-relevant, the finalized footprint, and the evidence pointer rather than through another active pointer or status taxonomy.

## Maintain a task footprint during execution

Use one companion artifact per write-based task at `.gameplan/footprints/<task-key>.md`, created from `assets/TASK_FOOTPRINT.template.md`. Treat it as provenance for later cleanup, never as execution authority, validation evidence, or proof of authorship.

### Begin

- Do not create a footprint for Lock, Recall, Orient, Status, Recommend, Challenge, or another read-only task merely because a plan exists.
- Do not create a footprint for write-based execution until the canonical plan contains one approved slice and the intended footprint path itself is allowed.
- Before the first authorized project mutation that executes a locked plan, create the footprint and add a concise `Task Footprint` pointer to `GAMEPLAN.md`. Use a stable date-and-purpose task key; never overwrite another footprint.
- Before that first mutation, capture pre-existing dirty paths with `git status --short --untracked-files=all` when Git is available. Record exact paths and observed states under Protected pre-existing items; do not read untracked file contents merely to classify them.
- When Git is unavailable, inspect intended target paths before writing. Mark any unresolved origin as `uncertain` with disposition `review`.
- Record dates as context only. Base provenance on explicit paths, observed state, and stated intent rather than timestamps.

### Record as work happens

- Add or update a Task items row in the same change that creates, adopts, abandons, or reclassifies an artifact whenever practical; otherwise update it immediately afterward.
- Use workspace-relative `/` paths without globs. Use `created` or `pre-existing` for Origin.
- Use Kind values `deliverable`, `temporary`, `scaffold`, `experiment`, or `uncertain`.
- Use Disposition values `keep`, `remove`, `adopted`, `abandoned`, or `review`.
- Mark experiments `adopted` when promoted to an intentional deliverable and `abandoned` when rejected. Do not leave a completed experiment ambiguous.
- Record planned removal, restoration, inspection, or transfer under Cleanup obligations with status `open`, `done`, or `waived`.
- Keep intent notes short. Point to an existing work report for detailed validation; do not duplicate command output, test totals, or step-by-step evidence.
- Keep every pre-existing dirty path protected even if the task later modifies it. A protected path is never an automatic deletion candidate.

### Finalize and retain

1. Review created artifacts, experiments, uncertain items, and cleanup obligations before reporting task completion.
2. Resolve every experiment to `adopted` or `abandoned`; keep unresolved provenance as `uncertain` and `review`.
3. Set State to `finalized` and record Finalized only after the task's authorized mutations are complete. If work stops unexpectedly, leave State `active`.
4. Update the `GAMEPLAN.md` pointer to say `Finalized` without copying file details into Current State.
5. Retain the footprint while any cleanup obligation is open or until a later cleanup consumer has finished. Remove it only when obligations are done, waived, or explicitly transferred and the user or an authorized cleanup workflow approves removal; then remove or replace the plan pointer.

### Compile for plan-wide cleanup

When more than one write-task footprint contributes to a completed plan, or the user asks to prepare the plan for Post Clean, materialize one `.gameplan/footprints/<plan-key>-compiled.md` artifact from `assets/COMPILED_FOOTPRINT.template.md`. Keep schema `gameplan-task-footprint/v1` so cleanup consumers read it as one frozen source rather than expanding a manifest.

1. List source footprints explicitly and in execution order under `Compiled sources`. Append only the footprint governing the work as it happens; never discover sources by scanning the directory or comparing timestamps.
2. Set the compiled artifact to `active` while any included task is active. Finalize each task footprint first, then rebuild and finalize the compiled artifact. Missing, active, malformed, unknown-schema, duplicated-path, or unordered sources keep the compiled artifact active and conservative.
3. Carry only plan-start protected paths into `Protected pre-existing items`. Derive them from the earliest included task baseline; never let a later task's dirty baseline reclassify an earlier task-created path as protected or pre-existing.
4. Emit one `Task items` row per exact path. Preserve plan-level `created` origin once established. Use the latest consistent explicit kind, disposition, and intent; resolve unclear or conflicting history to `uncertain` and `review`.
5. Merge cleanup obligations by exact path and action. Preserve `open` when status conflicts or a later explicit closure is unavailable. Include the compiled artifact itself as a created `keep` deliverable.
6. Point the `Task Footprint` section of `GAMEPLAN.md` to only the compiled artifact and retain every listed source footprint. Rebuilding the compiled artifact invalidates earlier Post Clean IDs and approvals by design.

### Stable cleanup-consumer contract

- Consume only schema `gameplan-task-footprint/v1`, including a materialized compiled artifact; treat unknown schemas conservatively.
- Treat only `remove` and `abandoned` rows as cleanup candidates. These labels do not themselves authorize deletion.
- Preserve `keep`, `adopted`, protected, `review`, uncertain, unlisted, and absent paths.
- Verify the current path and state before acting. Never infer cleanup intent from timestamps or from Git status alone.
- Treat an `active` footprint as incomplete and never use it for automatic deletion decisions.

## Lock a plan

1. Inspect the relevant conversation, artifacts, and any existing `GAMEPLAN.md`.
2. Extract the agreed outcome, chosen strategy, guardrails, optional approved execution slice, workstreams, current state, next move, open questions, decisions, and refresh triggers.
3. Resolve information into three classes:
   - **Locked**: explicitly agreed decisions and constraints.
   - **Operational**: status, sequencing, blockers, and next actions.
   - **Unresolved**: questions or alternatives that remain open.
4. Check for contradictions. Ask about only those that would materially alter the plan; otherwise record the uncertainty under Open Questions.
5. Resolve the execution boundary:
   - Record `None approved` when the agreement is strategic-only or immediate implementation was not approved.
   - Record one approved slice when the user explicitly supplied every material field.
   - When any material field was inferred, keep the slice proposed and obtain approval before treating it as active.
6. Create or patch `GAMEPLAN.md`. Preserve useful user-authored wording and unaffected sections.
7. Record meaningful decisions with an ISO date and brief rationale.
8. Set `Last Refreshed` to the current date and identify the evidence used.
9. Confirm the locked strategic core, whether an execution slice is approved, any unresolved issue, and the next move.

## Update without erasing history

Read the full plan, inspect current evidence when available, and patch only affected sections.

- Update Current State and Next Move freely when evidence supports the change.
- Change Outcome, Strategy, or Guardrails only when the user explicitly revises them.
- Record a dated Decisions entry for a meaningful strategic revision.
- Mark superseded decisions as superseded; do not delete their rationale.
- Do not mark work complete without evidence.
- Treat Current State as a concise milestone summary, not an append-only activity log.
- Before adding routine progress, merge related Completed items for the same workstream or milestone into one summary that states the outcome and names the strongest evidence source.
- Move detailed test counts, file lists, command output, and step-by-step history to an existing work report or named evidence artifact; keep only the durable result and evidence pointer in `GAMEPLAN.md`. Do not create a new evidence file during a read-only operation or without write authorization.
- Preserve a standalone status item when it still affects a blocker, next action, open question, guardrail, or decision rationale.
- Never compact Decisions by deleting history. Mark superseded decisions explicitly and preserve their rationale.
- After patching, apply this compaction gate before reporting completion:
  1. Make each Completed bullet represent a distinct decision-relevant milestone or workstream outcome, not an individual helper, command, test run, implementation slice, or Lock lifecycle event.
  2. Remove exact test totals, file counts, command output, and repeated verification narration from Current State when a durable evidence source exists.
  3. Name the existing report or evidence artifact supporting each compacted milestone that depends on detailed verification.
  4. Preserve every blocker, open question, guardrail, and decision rationale.
- If any gate check fails, revise the patch before reporting completion. If no durable evidence source can be identified, keep only the minimum evidence needed and state that compaction is incomplete; never invent a pointer.

## Recall, orient, and report status

For **Recall**, summarize the plan without adding new strategy.

For **Orient**, return:

1. Where we are going
2. Where we are now
3. What execution slice is approved, or that none is approved
4. What changed
5. What to do next

For **Status**, organize the response as completed, active, blocked, and next. Include the approved slice under active or its required approval under blocked without creating a parallel status model. Distinguish file-backed facts from inference.

Do not modify the plan during Recall, Orient, or Status unless the user also asks for an update.

## Recommend the next task

1. Read the complete plan.
2. Inspect relevant current workspace evidence when possible.
3. Check dependencies, blockers, sequencing, guardrails, and refresh triggers.
4. Recommend one concrete next task that fits the approved slice. If none is approved, recommend one complete slice for approval instead of implying execution authority.
5. Explain briefly why it is next and what completion evidence should exist.

Do not edit the plan merely because a recommendation was made. Update it only when requested or when completing an explicitly authorized GamePlan update operation.

## Challenge the plan

Evaluate assumptions, missing evidence, changed conditions, internal contradictions, sequencing risks, and opportunity cost. Separate findings into:

- execution changes that preserve strategy;
- possible strategy changes requiring user approval;
- facts requiring verification;
- unresolved questions.

Recommend revisions, but never apply them silently in Challenge mode.

## Maintain the canonical structure

Keep these sections in `GAMEPLAN.md`:

- Outcome
- Strategy
- Guardrails
- Approved Execution Slice, optional after Guardrails; use `None approved` as the safe default
- Workstreams
- Current State
- Next Move
- Open Questions
- Decisions
- Refresh Triggers
- Last Refreshed

Use `assets/GAMEPLAN.template.md` as the starting structure for a new plan. `Approved Execution Slice` is optional execution authority, while `Task Footprint` is an optional single-pointer provenance section; never confuse their roles. Point to the active task artifact until a compiled artifact is needed, then point only to the compiled artifact. The absence of a footprint in an older plan means no footprint is declared, not that cleanup is safe. Adapt the content to the work; do not leave placeholder instructions in the locked file.
