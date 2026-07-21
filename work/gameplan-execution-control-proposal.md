# Parked proposal: execution control inside GamePlan

**Status:** Historical design input, superseded by `work/gameplan-execution-control-phased-plan.md`; not authorized for implementation.

**2026-07-20 clarification:** Clean Handoff is completely outside this work. The earlier Clean Handoff timing gate and compatibility references in this historical proposal are superseded. The current proposal absorbs ScopeLock's beneficial abilities directly into GamePlan's "lock in this plan" command without modifying or depending on Clean Handoff, then removes only ScopeLock parts affirmatively proven unable to break any other skill or related product. Known, possible, uncertain, or unverified dependencies are retained. See the phased plan for the controlling absorption and retirement rules.

**Date:** 2026-07-19

## Recommendation

Make `GAMEPLAN.md` the single authority for both strategic continuity and the currently approved execution boundary. Extend GamePlan's existing Lock and Update behavior with one optional, explicitly approved execution slice. Do not embed ScopeLock as a second product, copy its repository-baseline engine, or introduce another lifecycle/status model.

The future design should absorb three ideas from ScopeLock:

1. A concrete, user-approved execution contract.
2. An explicit approval boundary for scope expansion.
3. Evidence-backed verification before work is folded back into the canonical plan.

It should not absorb ScopeLock's independent active pointer, immutable Git baseline, separate Lock lifecycle, or parallel health/report outcomes. Those mechanisms are coherent for ScopeLock's original forensic-drift product, but they compete with GamePlan when both try to govern the same work.

## Why this fits GamePlan

GamePlan already protects the strategic authority that ScopeLock does not model:

- Outcome, Strategy, and Guardrails remain authoritative until explicitly revised.
- Current State and Next Move carry operational state.
- Decisions preserve approved changes and rationale.
- Update already requires direct evidence and compacts detailed verification into durable milestones.

The missing layer is narrower: GamePlan can say where the project is going and what comes next, but it does not yet express exactly which implementation slice is approved now, what files that slice may touch, or what evidence closes it.

## ScopeLock evidence and critique

The analysis used the installed ScopeLock `0.1.1+codex.20260717130011` package as historical product evidence. No ScopeLock files were changed.

### Concepts worth preserving

- The contract requires an objective, allowed paths, constraints, definition of done, and validation requirements.
- Inferred material scope must be approved before activation.
- Active scope can expand only through an explicit amendment.
- Verification records observed changes and command results without inventing authorship or test success.
- Pre-existing or uncertain work is reported honestly rather than silently attributed to the current task.
- A successful verification does not itself decide the next strategic move.

### Concepts to leave behind

#### Separate lifecycle

ScopeLock has Proposed, Active, Closed, and Abandoned transitions in addition to GamePlan's Current State and Next Move. Verification is separate from closing. This creates an extra sequence the user and agent must maintain even when the canonical plan already knows whether work is active, complete, blocked, or next.

**Recommendation:** Do not add a second lifecycle. The presence of one approved slice means work is authorized. GamePlan Status reports its progress through Current State. Closing the slice is a targeted GamePlan Update.

#### Hidden metadata authority

ScopeLock stores authority across `.codex-scope/active.json`, `contract.md`, `baseline.json`, amendments, and reports. The active pointer determines which Lock governs execution even though `GAMEPLAN.md` may describe a different next move.

**Recommendation:** Keep all normative fields in the human-readable canonical plan. Supporting evidence may live in `work/` or another named artifact, but it must never select the active slice, broaden scope, or override the plan.

#### Baseline reconciliation

ScopeLock captures a Git baseline and reconciles later branch, HEAD, index, worktree, untracked-path, fingerprint, and ancestry changes. Branch changes or rewritten history can make a Lock stale and force creation of a new Lock. This is useful for ScopeLock's original promise of detecting repository drift, but it is too expensive and brittle as GamePlan's default authority mechanism.

**Recommendation:** Treat the execution slice as prospective authorization, not forensic attribution. At verification, inspect known edits and current repository evidence, label uncertainty, and avoid claiming who changed pre-existing files. If future use proves that stronger diff attribution is necessary, add a read-only evidence helper whose output is subordinate to `GAMEPLAN.md`; do not recreate an authoritative baseline store.

#### Parallel status model

ScopeLock distinguishes lifecycle (`active`, `closed`, `abandoned`), health (`clean`, `attention`, `stale`, `unavailable`), findings, and report outcomes (`pass`, `warning`, `fail`, `incomplete`). GamePlan already has Completed, Active, Blocked, Next Move, Open Questions, Decisions, and evidence requirements.

**Recommendation:** Reuse GamePlan's existing status vocabulary. Validation results are evidence attached to the slice, not a new project status. A failed check makes Current State blocked or active; it does not establish a second health authority.

## Proposed canonical model

Continue to require the existing ten canonical sections. In a future approved version, add one optional section after Guardrails:

```markdown
## Approved Execution Slice

Approval: User-approved on YYYY-MM-DD

- Objective: One concrete implementation result.
- Allowed files:
  - exact/path.ext
  - allowed/directory/
- Constraints:
  - Relevant implementation and safety boundaries.
- Completion criteria:
  - Observable result required before closure.
- Validation commands:
  - exact command to run
- Validation authorization: Granted with slice approval for the exact, project-local, non-destructive commands above.
- Evidence: Not yet recorded.
```

Rules:

- At most one execution slice is approved at a time.
- If no work is approved, the section says `None approved`.
- Every normative field is visible in `GAMEPLAN.md`.
- Allowed paths use exact files or directory prefixes initially; no glob language is needed for the first iteration.
- An explicitly allowed whole workspace must be written as `.` and approved as such.
- Listed commands are standing authorization only when the slice says so and the commands are exact, project-local, and non-destructive. Networked, destructive, privileged, or externally mutating commands still require contemporaneous approval.
- Supporting logs and detailed output are evidence, not authority.

## Approval boundaries

| Proposed change | Agent behavior |
|---|---|
| Work stays within the approved objective, files, constraints, criteria, and commands | Proceed and update operational evidence as needed |
| Add an allowed file or directory | Stop and request explicit scope-expansion approval |
| Relax a constraint or completion criterion | Stop and request explicit approval |
| Replace the slice objective | Treat as a new slice and request explicit approval |
| Change Outcome, Strategy, or Guardrails | Stop, explain the strategic conflict, and request explicit strategy approval |
| Narrow allowed files or add a protective constraint without invalidating work already done | May propose a targeted operational update; do not erase prior evidence |
| Discover unrelated or pre-existing changes | Preserve them, label attribution uncertain, and do not absorb them into the slice |
| Need a validation command not listed | Request approval before running it when it is materially different or carries side effects |

Scope expansion and strategy change are deliberately different approvals. Adding one implementation file should not reopen the product strategy; changing the strategy should not be disguised as a file-list amendment.

## Lock, execute, verify, and close

### Lock

When the user says to lock the game plan in:

1. Lock the agreed Outcome, Strategy, and Guardrails as GamePlan already does.
2. If immediate implementation is part of the agreement, draft one execution slice.
3. Activate the slice directly when every material field was explicitly supplied by the user.
4. If GamePlan inferred an objective, allowed path, constraint, criterion, or command, present the slice and obtain approval before treating it as active.
5. Do not create an auxiliary active pointer or baseline.

### Execute

Before editing, read the full canonical plan and the approved slice. Stay within both the strategic core and the slice. Unexpected file needs trigger an approval request; they do not silently broaden the slice.

### Verify

Verification should produce direct evidence for each completion criterion:

- exact command or inspection performed;
- timestamp;
- exit status or observed result;
- concise, sanitized summary;
- named evidence artifact when detailed output matters;
- explicit uncertainty where repository evidence cannot distinguish pre-existing or concurrent work.

GamePlan should verify the current slice, not reconcile the entire repository against an immutable starting snapshot. It must not infer authorship from Git state.

### Close through Update

Closing is not a separate product lifecycle. It is one atomic GamePlan Update:

1. Confirm every completion criterion has direct evidence or explicitly record what remains incomplete.
2. Add one durable, evidence-linked milestone to Current State.
3. Update Next Move from the result.
4. Record a Decision only when the close changed strategy, guardrails, or another decision-relevant commitment.
5. Set Approved Execution Slice to `None approved` or replace it with a newly approved slice.
6. Preserve detailed evidence at its named location and retain historical ScopeLock artifacts untouched.

If validation fails, do not close. Keep the slice approved, record the blocker in Current State, and recommend the smallest in-scope recovery action.

## Future implementation plan

Implementation remains unauthorized until the re-entry gate below is satisfied.

### Phase 0: re-entry and compatibility review

- Confirm Clean Handoff v0.8 is finished.
- Review its final transfer, evidence, and task-continuation contracts for overlap.
- Re-read current GamePlan and ScopeLock behavior; do not assume the 2026-07-19 artifacts are still current.
- Obtain explicit user approval for the final GamePlan change.

### Phase 1: contract and template prototype

- Add the optional Approved Execution Slice section to the GamePlan contract and template.
- Specify exact approval semantics, scope grammar, validation authorization, and close-through-Update behavior.
- Keep the implementation Markdown-only; add no script or hidden state.
- Add examples for strategic-only Lock, Lock with a slice, scope expansion, failed validation, and successful close.

### Phase 2: skill behavior

- Extend Lock to distinguish the strategic core from one operational slice.
- Extend Status and Orient to show the approved slice without adding new status enums.
- Extend Update to record validation evidence and close the slice atomically.
- Extend Challenge to detect slice/strategy conflicts and proposed scope expansion.

### Phase 3: validation

- Test fresh-context adherence to allowed files.
- Test that inferred scope requires approval.
- Test that an added file pauses execution without reopening strategy.
- Test that Outcome, Strategy, or Guardrail changes require explicit approval.
- Test exact command authorization and rejection of unapproved risky commands.
- Test failed validation, incomplete evidence, dirty worktrees, and concurrent unrelated changes without invented attribution.
- Test closure compaction into Current State and Next Move with no duplicate lifecycle state.

### Phase 4: dogfood and compare

- Use the model on at least two real execution slices, including one dirty worktree.
- Compare friction and missed detections with historical ScopeLock evidence.
- Add a helper only if repeated evidence shows Markdown inspection is unreliable; any helper must be read-only or evidence-producing and subordinate to the canonical plan.

### Phase 5: later ScopeLock disposition decision

- Decide separately whether standalone ScopeLock remains useful for high-assurance repository drift inspection.
- Consider deprecation only after GamePlan execution control is proven and historical ScopeLock evidence is retained.
- Do not make deprecation a prerequisite for the GamePlan experiment.

## Acceptance criteria for a future implementation

- `GAMEPLAN.md` is the only normative authority for strategy and the active execution slice.
- Outcome, Strategy, and Guardrails cannot change without explicit user approval.
- Only one execution slice can be approved at a time.
- The slice always contains an objective, allowed files, constraints, completion criteria, validation commands, and approval state.
- Scope expansion pauses execution and requires explicit approval.
- Verification records direct evidence and uncertainty without claiming authorship it cannot prove.
- Closing updates Current State and Next Move in one operation and removes the active slice.
- No `.codex-scope` directory, active pointer, immutable repository baseline, or parallel lifecycle/health model is required.
- Existing ScopeLock records remain untouched and readable.
- Clean Handoff integration remains unchanged unless separately approved.

## Non-goals

- Implementing this proposal now.
- Modifying Clean Handoff or ScopeLock.
- Importing ScopeLock wholesale.
- Providing operating-system enforcement or guaranteed write prevention.
- Proving who authored repository changes.
- Automatically deprecating or deleting standalone ScopeLock.
- Adding multiple concurrent execution slices.

## Open design questions for re-entry

- Should validation evidence live inline until closure, or always point to an existing work report once output exceeds a small threshold?
- Should a newly approved slice replace `Next Move`, or should `Next Move` remain the strategic sequencing statement that the slice instantiates?
- Is exact file/directory-prefix scope sufficient after dogfooding, or is a narrowly defined pattern grammar needed?
- Which Clean Handoff v0.8 evidence fields should GamePlan reference rather than duplicate?
- Does repeated dirty-worktree use justify a non-authoritative changed-path helper?

## Re-entry gate

Reopen this proposal only when both conditions are true:

1. Clean Handoff v0.8 is finished and its final behavior can be inspected.
2. The user explicitly approves revisiting or implementing GamePlan execution control.

Until then, GamePlan v1 remains frozen in observation-only dogfooding and this document is advisory evidence, not active strategy.

## Evidence sources inspected

- GamePlan canonical plan and skill behavior in this workspace.
- `work/gameplan-v1-test-results.md`, including the proven mandatory compaction gate.
- Installed Clean Handoff package metadata showing version `0.7.0` at the time of review.
- Installed ScopeLock `0.1.1+codex.20260717130011` product contract, conceptual model, workflows, schemas/path rules, changelog, and test evidence.
