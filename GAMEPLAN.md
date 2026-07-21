# Game Plan

## Outcome

Make GamePlan's "lock in this plan" command the single authority for strategic continuity and execution control by absorbing ScopeLock's beneficial approval-boundary and verification abilities.

GamePlan succeeds when one canonical `GAMEPLAN.md` locks Outcome, Strategy, and Guardrails; holds at most one explicitly approved execution slice; requires approval before strategy changes or scope expansion; records direct completion evidence; and closes the slice through a targeted Update without a second active pointer, Git baseline, lifecycle, or status authority.

The integration is complete only after fresh-context and real-project validation prove the replacement and every ScopeLock component is conservatively classified: safely removable local material is gone, while anything that could possibly support another skill or related product is retained.

## Strategy

Evolve the existing local, Markdown-backed GamePlan skill rather than merge ScopeLock source code or architecture. Absorb the useful behavior into GamePlan's Lock, Status, execution, and Update operations:

- an approved objective, exact allowed files or directories, constraints, completion criteria, and validation commands;
- explicit approval for inferred material scope and later scope expansion;
- default-deny behavior outside the approved slice;
- direct evidence with honest uncertainty and no invented authorship;
- close-through-Update using Current State, Decisions, and Next Move.

Keep the implementation deliberately small and preserve the existing artifact model:

```text
gameplan/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
`-- assets/
    |-- COMPILED_FOOTPRINT.template.md
    |-- GAMEPLAN.template.md
    `-- TASK_FOOTPRINT.template.md
```

`GAMEPLAN.md` is normative authority. The Approved Execution Slice is its current implementation boundary. Task Footprints and compiled footprints remain cleanup provenance, and work reports remain detailed evidence; none may authorize or broaden execution.

Implement the capability in six phases. The strategic direction is locked as a whole, but only one phase-sized execution slice is approved at a time. Close each phase with direct evidence and a canonical-plan update before approving the next slice.

## Guardrails

- Treat GamePlan as strategic operating context, not merely a checklist.
- Keep Outcome, Strategy, and Guardrails authoritative until explicitly revised by the user.
- Allow Current State and Next Move to evolve with evidence.
- Keep `GAMEPLAN.md` as the only normative authority; no footprint, report, helper output, installed cache, or hidden metadata may select or broaden the active slice.
- Allow at most one approved execution slice at a time.
- Require explicit approval before adding allowed files or directories, relaxing constraints or completion criteria, replacing the slice objective, or changing the strategic core.
- Use exact workspace-relative files and directory prefixes. Require explicit approval for `.` as the whole workspace.
- The one-time Phase F Slice 2 external-target exception expired on closure and grants no continuing external-write authority.
- Treat exact, project-local, non-destructive validation commands as standing authorization only when the approved slice says so. Risky or externally mutating commands require contemporaneous approval.
- Never treat brainstorming as agreement.
- Never overwrite the full plan when a targeted patch is sufficient.
- Never mark work complete without evidence.
- Never change strategy merely because another approach appears attractive.
- Never recommend a next task before reading the canonical plan.
- Clearly label inferences and facts that may be stale.
- Preserve user-authored content, meaningful constraints, rejected alternatives, and decision rationale whenever possible.
- Ask only when ambiguity would materially change the plan.
- Challenge mode may recommend revisions but must not silently apply them.
- Treat task footprints as provenance, never execution authority or proof of authorship.
- Never claim authorship from Git state; preserve pre-existing and concurrent work and label uncertainty.
- Never infer deletion safety from timestamps, Git status alone, missing footprint entries, or uncertain classification.
- Preserve pre-existing dirty paths and require later cleanup authorization even for explicit cleanup candidates.
- Compile only explicitly ordered task footprints into one materialized v1 artifact; never scan the footprint directory, infer chronology, or weaken plan-start protection.
- Keep the first execution-control implementation Markdown-only; add a helper only after repeated dogfooding proves a specific reliability failure.
- Defer multiple named plans, user-wide storage, snapshots and diffs, archival, external integrations, shared team plans, and a full plugin until the local skill proves useful.
- Clean Handoff is not part of this merger: it is not a target, dependency, workstream, validation surface, release gate, or execution-slice candidate; do not inspect, invoke, modify, or coordinate with it under this plan.
- Do not modify ScopeLock during Phases A through E.
- During Phase F, delete a ScopeLock component only when affirmative dependency evidence proves removal cannot break any other skill or related product. Missing, indirect, dynamic, contradictory, possible, or uncertain dependencies require retention.
- If proving a ScopeLock deletion safe would require inspecting, invoking, testing, or modifying an external product, retain the component as dependency-uncertain unless the user separately authorizes that external-product work.
- Never blanket-delete `.codex-scope/` or manually remove generated plugin caches. Enumerate exact targets, preserve useful history and possible dependencies, and use supported removal paths where available.
- Do not delete, archive, unpublish, or rewrite remote ScopeLock repositories or marketplace listings without separate explicit approval.
- After every phase completes, update this canonical plan from direct evidence before reporting completion or requesting approval for the next phase. Close or retain the slice, compact Current State, update the phase status and Next Move, preserve Decisions, and name the detailed evidence source.
- The agent may judge and mark a phase complete without separate confirmation only when every locked completion criterion is directly evidenced, every required validation passes, the work stayed inside the approved scope, the task footprint is finalized, and the canonical phase-close update passes. If any mark is missing, failed, uncertain, skipped, or out of scope, keep the phase incomplete and report the gap.
- Phase-completion authority does not authorize scope expansion, strategy or Guardrail changes, skipped validation, destructive cleanup, external mutations, or approval and start of the next phase.

## Approved Execution Slice

None approved. Phase F closed on 2026-07-20 with direct evidence in `work/gameplan-execution-control-phase-f-slice-1-results.md`, `work/gameplan-execution-control-phase-f-slice-2-results.md`, and `work/scopelock-retirement-manifest.md`.

## Closed Execution Slice Record

**Phase F Slice 2 — Install, compile provenance, and close**

- **Approval:** Explicitly approved by the user on 2026-07-20 after all workspace writes, three external targets, ordered compiled sources, rollback rules, completion criteria, and eleven command strings were exposed.
- **Objective:** Install the three proven workspace GamePlan files into their exact installed targets, validate the complete installed package, finalize the conservative retention manifest, compile Phase A–F provenance, and close Phase F and the complete GamePlan.
- **Allowed workspace write files:**
  - `GAMEPLAN.md`
  - `work/gameplan-execution-control-phase-f-slice-2-results.md`
  - `work/scopelock-retirement-manifest.md`
  - `.gameplan/footprints/2026-07-20-execution-control-phase-f-slice-2.md`
  - `.gameplan/footprints/2026-07-20-execution-control-compiled.md`
- **One-time external write targets:**
  - `C:\Users\robby\.codex\skills\gameplan\SKILL.md`
  - `C:\Users\robby\.codex\skills\gameplan\agents\openai.yaml`
  - `C:\Users\robby\.codex\skills\gameplan\assets\GAMEPLAN.template.md`
- **Ordered compiled sources:**
  1. `.gameplan/footprints/2026-07-20-execution-control-phase-a.md`
  2. `.gameplan/footprints/2026-07-20-execution-control-phase-b.md`
  3. `.gameplan/footprints/2026-07-20-execution-control-phase-c.md`
  4. `.gameplan/footprints/2026-07-20-execution-control-phase-d.md`
  5. `.gameplan/footprints/2026-07-20-execution-control-phase-e-slice-1.md`
  6. `.gameplan/footprints/2026-07-20-execution-control-phase-e-slice-2.md`
  7. `.gameplan/footprints/2026-07-20-execution-control-phase-f-slice-1.md`
  8. `.gameplan/footprints/2026-07-20-execution-control-phase-f-slice-2.md`
- **Constraints:** Update installed files only with `apply_patch`. Do not change the already matching installed compiled-footprint or task-footprint templates. Stop before installation if any pre-install hash differs from Slice 1 evidence. Capture the original installed contents before mutation; if installed validation fails, restore all three original installed files and leave the slice active. Retain every ScopeLock component. Perform no ScopeLock, configuration, hook, store, excluded-product, marketplace, repository, or remote mutation and no deletion. The external-target exception expires on closure.
- **Completion criteria:**
  - Pre-install workspace and installed hashes match the exact Slice 1 evidence, and workspace validation passes before installation.
  - Only the three authorized installed files are updated, using `apply_patch`, and all five installed GamePlan package files then hash-match their workspace sources.
  - The installed package validator and installed execution-control contract search pass; otherwise all three installed files are rolled back and the slice remains active.
  - The retirement manifest is finalized for Phase F, retains every ScopeLock component, and contains no component row marked `remove — dependency safety proven`.
  - The Phase F Slice 2 footprint is finalized, then the compiled footprint is finalized from the eight exact ordered sources using the earliest source baseline and conservative merge rules.
  - The evidence report records direct results and limitations, every command satisfies its expected outcome, the exact workspace and external boundaries are respected, and the canonical close marks all six phases complete with no active slice.
- **Exact commands:**
  1. `git status --short --untracked-files=all`
  2. `$expected=@{'gameplan\SKILL.md'='F329293298E6BB34E79BDF575B2AA21F48CC9DD160FC5F899FBB01224F011F23';'gameplan\agents\openai.yaml'='012EF70FE9C083B846C88795811840A3B1178E93E78E27369FD9A2E063F4A01E';'gameplan\assets\GAMEPLAN.template.md'='BAB4AA729081233CE10AEA9D523728DD7E253AE631281702F6C5E68568C60D58';'C:\Users\robby\.codex\skills\gameplan\SKILL.md'='D25504DCD48B50BF079CDD3BCAD938AC62F248DA0A5002BD285B6D9F44D8889E';'C:\Users\robby\.codex\skills\gameplan\agents\openai.yaml'='BF848D9AE2049FBED3D6738827EAD914E47091DAB290B18426D40DB205AC6B78';'C:\Users\robby\.codex\skills\gameplan\assets\GAMEPLAN.template.md'='6D2D410DE44B5A90FE835AE466BBCB8513CA52EEB121F3B204FA3E0DE061F04C'}; $bad=@(); foreach($path in $expected.Keys){ if(!(Test-Path -LiteralPath $path)){ $bad+="$path=MISSING"; continue }; $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash; if($actual -ne $expected[$path]){ $bad+="$path=$actual" } }; if($bad.Count){ $bad; exit 2 }; 'PREINSTALL_HASH_GATE_OK'`
  3. `$targets=@('C:\Users\robby\.codex\skills\gameplan\SKILL.md','C:\Users\robby\.codex\skills\gameplan\agents\openai.yaml','C:\Users\robby\.codex\skills\gameplan\assets\GAMEPLAN.template.md'); foreach($target in $targets){ "===BEGIN $target==="; Get-Content -Raw -LiteralPath $target; "===END $target===" }`
  4. `$env:PYTHONPATH='work/validator-deps'; python 'C:\Users\robby\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'gameplan'`
  5. `$env:PYTHONPATH='work/validator-deps'; python 'C:\Users\robby\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'C:\Users\robby\.codex\skills\gameplan'`
  6. `$pairs=@(@('gameplan\SKILL.md','C:\Users\robby\.codex\skills\gameplan\SKILL.md'),@('gameplan\agents\openai.yaml','C:\Users\robby\.codex\skills\gameplan\agents\openai.yaml'),@('gameplan\assets\COMPILED_FOOTPRINT.template.md','C:\Users\robby\.codex\skills\gameplan\assets\COMPILED_FOOTPRINT.template.md'),@('gameplan\assets\GAMEPLAN.template.md','C:\Users\robby\.codex\skills\gameplan\assets\GAMEPLAN.template.md'),@('gameplan\assets\TASK_FOOTPRINT.template.md','C:\Users\robby\.codex\skills\gameplan\assets\TASK_FOOTPRINT.template.md')); $bad=@(); foreach($pair in $pairs){ $left=(Get-FileHash -Algorithm SHA256 -LiteralPath $pair[0]).Hash; $right=(Get-FileHash -Algorithm SHA256 -LiteralPath $pair[1]).Hash; if($left -ne $right){ $bad+="$($pair[0]) != $($pair[1])" } }; if($bad.Count){ $bad; exit 2 }; 'ALL_FIVE_GAMEPLAN_FILES_MATCH'`
  7. `rg -n "Approved Execution Slice|scope expansion|Validate and close|cleanup" 'C:\Users\robby\.codex\skills\gameplan\SKILL.md' 'C:\Users\robby\.codex\skills\gameplan\assets\GAMEPLAN.template.md' 'C:\Users\robby\.codex\skills\gameplan\agents\openai.yaml'`
  8. `$path='.gameplan\footprints\2026-07-20-execution-control-compiled.md'; $text=Get-Content -Raw -LiteralPath $path; $required=@('Schema: `gameplan-task-footprint/v1`','State: `finalized`','2026-07-20-execution-control-phase-a.md','2026-07-20-execution-control-phase-b.md','2026-07-20-execution-control-phase-c.md','2026-07-20-execution-control-phase-d.md','2026-07-20-execution-control-phase-e-slice-1.md','2026-07-20-execution-control-phase-e-slice-2.md','2026-07-20-execution-control-phase-f-slice-1.md','2026-07-20-execution-control-phase-f-slice-2.md'); $missing=$required | Where-Object { !$text.Contains($_) }; if($missing){ $missing; exit 2 }; 'COMPILED_FOOTPRINT_CONTRACT_OK'`
  9. `$path='work\scopelock-retirement-manifest.md'; $text=Get-Content -Raw -LiteralPath $path; if(!$text.Contains('Status: Finalized for Phase F')){ 'FINAL_STATUS_MISSING'; exit 2 }; $removals=Select-String -LiteralPath $path -Pattern '^\|.*\|\s*remove — dependency safety proven\s*\|'; if($removals){ $removals; exit 3 }; 'RETENTION_MANIFEST_FINAL'`
  10. `git diff --check`
  11. `$path='GAMEPLAN.md'; $text=Get-Content -Raw -LiteralPath $path; $required=@('None approved. Phase F closed','**Phase F — Install and conservative ScopeLock retirement:** Complete.','All six phases are complete; no execution slice is active.','.gameplan/footprints/2026-07-20-execution-control-compiled.md'); $missing=$required | Where-Object { !$text.Contains($_) }; if($missing){ $missing; exit 2 }; 'CANONICAL_PHASE_F_CLOSE_OK'`
- **Validation authorization:** The user's exact approval grants standing authority only for these eleven local, non-destructive commands during Slice 2. Commands 1–4 are pre-install gates, commands 5–7 validate the installation, and commands 8–11 validate final provenance and canonical closure. The approved installed-file mutations and any required rollback use `apply_patch`, not shell copy commands.
- **Evidence target:** `work/gameplan-execution-control-phase-f-slice-2-results.md`

## Workstreams

- **Phase A — Canonical authority contract:** Complete. The optional slice contract and safe template default are validated.
- **Phase B — Approval-bound execution:** Complete. The approved slice now governs mutations, scope expansion, strategic conflicts, footprints, and slice-aware status.
- **Phase C — Evidence and close-through-Update:** Complete. Direct criterion evidence, failed-validation retention, and single-Update closure are validated.
- **Phase D — Adversarial validation:** Complete. The ten-scenario authority and failure matrix passes with exposed contract gaps corrected.
- **Phase E — Real-project dogfooding:** Complete. Two sequential real-project slices passed: dirty-worktree template/UI alignment and exact scope-expansion approval with discovery-surface alignment.
- **Phase F — Install and conservative ScopeLock retirement:** Complete. The three changed GamePlan files were installed and the five-file package was validated; all ScopeLock components were retained because no deletion candidate had affirmative no-break evidence; eight ordered footprints were compiled as final provenance.

## Current State

### Completed

- Locked the version 1 product direction: one local, Markdown-backed canonical plan per workspace with seven intent-based operations and protected strategic authority.
- Implemented the complete `gameplan` skill package, including UI metadata and the reusable canonical plan template.
- Passed structural, installation, discovery, operation, natural-language, contradiction, and messy-plan validation. Evidence: `work/gameplan-v1-test-results.md`.
- Proved GamePlan's Lock, Recommend, plan-grounded execution, targeted Update, and milestone compaction through prior real-project dogfooding while preserving strategy, guardrails, decision history, and staging boundaries. Evidence: `work/gameplan-v1-test-results.md`.
- Captured a parked design recommendation for absorbing ScopeLock's approval-boundary, execution-slice, and verification concepts into GamePlan without adopting its independent lifecycle, hidden authority, Git baseline, or parallel status model. Evidence: `work/gameplan-execution-control-proposal.md`.
- Added and installed a versioned per-task footprint that records protected pre-existing work, created artifacts, temporary/scaffold intent, experiment disposition, cleanup obligations, and uncertainty without expanding Current State into a file log. Evidence: `work/gameplan-v1-test-results.md`.
- Added and installed a Markdown-only compiled footprint that gives Post Clean one conservative plan-wide v1 source without scanning or expanding component footprints. Evidence: `work/gameplan-compiled-footprint-results.md`.
- Approved and locked the phased ScopeLock-capability absorption strategy, conservative dependency-retention rule, and Phase A execution slice. Source: `work/gameplan-execution-control-phased-plan.md` and the 2026-07-20 user approval.
- Completed Phase A's single-authority Lock contract and safe `None approved` template default without importing ScopeLock lifecycle or metadata authority. Evidence: `work/gameplan-execution-control-phase-a-results.md`.
- Completed Phase B's approval-bound execution behavior, including default-deny paths, explicit expansion pauses, separate strategy approval, footprint gating, and slice-aware status without parallel lifecycle state. Evidence: `work/gameplan-execution-control-phase-b-results.md`.
- Completed Phase C's direct criterion evidence and close-through-Update behavior: incomplete validation preserves the active slice and blocker, while successful validation compacts canonical state, advances Next Move without approval, and finalizes provenance without duplicate lifecycle authority. Evidence: `work/gameplan-execution-control-phase-c-results.md`.
- Completed Phase D's adversarial matrix across dirty, protected, untracked, concurrent, missing-path, late-scope, risky-command, failed-test, stale-evidence, and interrupted-execution behavior; two contract ambiguities were corrected without importing ScopeLock authority or external-product work. Evidence: `work/gameplan-execution-control-phase-d-results.md`.
- Completed Phase E's two sequential real-project dogfooding slices while protecting dirty pre-existing paths and preserving one-slice authority: reusable template/UI alignment, then an exact scope-expansion decision and discovery-surface alignment. Evidence: `work/gameplan-execution-control-phase-e-slice-1-results.md` and `work/gameplan-execution-control-phase-e-slice-2-results.md`.
- Completed Phase F: installed and validated the five-file GamePlan package, finalized the conservative retain-only ScopeLock manifest with no deletions, and compiled all eight ordered execution-control footprints. Evidence: `work/gameplan-execution-control-phase-f-slice-1-results.md`, `work/gameplan-execution-control-phase-f-slice-2-results.md`, and `work/scopelock-retirement-manifest.md`.

### Active

- All six phases are complete; no execution slice is active.

### Blocked

- None.

## Task Footprint

Finalized: `.gameplan/footprints/2026-07-20-execution-control-compiled.md` (`gameplan-task-footprint/v1`). This is the single materialized cleanup-provenance input for the eight exact ordered execution-control footprints; it grants no cleanup or deletion authority.

## Next Move

Use the installed GamePlan for future locked work. Any later cleanup must consume the finalized compiled footprint, verify current state, and receive separate explicit cleanup approval; any future ScopeLock deprecation or remote action requires a new plan and exact approved slice.

## Open Questions

- After local usage proves the model, should GamePlan support multiple named plans or continue enforcing one canonical plan per workspace?
- What evidence threshold should trigger adding scripts, automatic snapshots, or cross-workspace storage?
- Should this capability remain an evolution of GamePlan v1 or receive a new product-version label at installation time?
- What is the smallest independently retainable package boundary for ScopeLock's live context/reserved-sideband provider without preserving broader standalone behavior?
- Should any remote ScopeLock repository or marketplace listing later be archived or unpublished? This remains outside local retirement authority.

## Decisions

- 2026-07-18 — Build GamePlan as a skill before considering a plugin; this tests the core workflow with less architecture.
- 2026-07-18 — Use `GAMEPLAN.md` at the workspace root as the durable memory surface for version 1.
- 2026-07-18 — Keep strategy and guardrails locked while allowing operational status to evolve from evidence.
- 2026-07-18 — Defer scripts and external integrations until real usage demonstrates a repeated need.
- 2026-07-18 — Lock the expanded build plan, including its product principle, operation contracts, realistic validation scenarios, acceptance criteria, and explicitly deferred ideas; these details clarify the existing strategy without changing it.
- 2026-07-18 — Strengthen Update with milestone compaction and external evidence pointers; three dogfooding cycles showed reliable strategy preservation but repeated accumulation of routine completion detail.
- 2026-07-19 — Historical only: park the execution-control proposal behind an unrelated product's v0.8 timing gate; if later approved, absorb only ScopeLock's approval-boundary, execution-slice, and verification concepts into GamePlan, keep `GAMEPLAN.md` authoritative, and defer any standalone ScopeLock deprecation decision. Superseded on 2026-07-20 by the direct phased plan below; this created no lasting dependency, scope, or validation obligation.
- 2026-07-19 — Add a lightweight, per-task `gameplan-task-footprint/v1` companion artifact for cleanup provenance; keep it non-authoritative, exact-path, conservative about deletion, and separate from validation reports and the parked execution-control proposal.
- 2026-07-19 — Materialize explicitly ordered task footprints into one plan-wide `gameplan-task-footprint/v1` artifact for Post Clean; preserve the single-source consumer boundary and keep compilation Markdown-only.
- 2026-07-20 — Make GamePlan the single normative authority for strategic continuity and one approved execution slice.
- 2026-07-20 — Absorb ScopeLock's approval-boundary, exact-scope, and verification benefits without merging its storage, baselines, hooks, lifecycle, health, or report architecture.
- 2026-07-20 — Treat Task Footprints as cleanup provenance and work reports as evidence; neither may authorize or broaden execution.
- 2026-07-20 — Lock the phased strategy while approving only one phase-sized execution slice at a time; authorize Phase A now and require a later approval for Phase B.
- 2026-07-20 — Exclude all external products from this merger's dependency graph and scope; a possible external consumer is a conservative ScopeLock-retention reason, not authority to inspect or change that consumer.
- 2026-07-20 — Make conservative local ScopeLock retirement part of completion: delete only exact components affirmatively proven unable to break another skill or related product; retain every known, possible, uncertain, indirect, or unverified dependency.
- 2026-07-20 — Require a canonical GamePlan update after every completed phase and before the next phase begins; phase completion must close or retain the slice, compact status, preserve decision history, update Next Move, and point to direct evidence.
- 2026-07-20 — Approve the complete Phase B execution slice exactly as proposed, including its four-file boundary and two local validation commands; no later phase or external product work is authorized.
- 2026-07-20 — Delegate evidence-backed phase-completion judgment to the agent when all locked completion criteria are directly satisfied, required validation passes, scope is respected, the footprint is finalized, and the canonical close update passes. This does not delegate approval for the next phase or any broader authority.
- 2026-07-20 — Approve the complete Phase C execution slice with its four-file boundary, preserved Phase A/B semantics, three local validation commands, and prohibition on external-product, ScopeLock, installed-copy, template, metadata, prior-evidence, compiled-footprint, and later-phase changes.
- 2026-07-20 — Tighten the merger boundary before Phase D: name the specifically excluded product only once in Guardrails, remove it from operational evidence and status, and treat possible external consumption only as a conservative ScopeLock-retention signal.
- 2026-07-20 — Approve the exact Phase D adversarial-validation slice with its four-file boundary, ten-scenario matrix, three local validation commands, and prohibition on ScopeLock authority, external-product interaction, installed-copy changes, fixtures, scripts, dependencies, and later-phase work.
- 2026-07-20 — Approve Phase E's overall real-project dogfooding outcome, but do not treat the request to approve all Phase E slices as concurrent or unseen execution authority. Preserve the locked one-exact-slice-at-a-time boundary because the user did not explicitly revise it and Phase E must prove that boundary in ordinary use.
- 2026-07-20 — Approve Phase E Slice 1 with its five-file dirty-worktree boundary, template and UI-prompt alignment objective, three exact local validation commands, and prohibition on workspace-skill, installed-copy, ScopeLock, external-product, later-slice, and Phase F changes.
- 2026-07-20 — Approve the exact Phase E Slice 2 only after its objective, five-file boundary, constraints, completion criteria, validation commands, and evidence target were presented; this sequential approval is the real scope-expansion boundary Phase E must evidence.
- 2026-07-20 — Approve Phase F's outcome and sequencing, but preserve one-exact-slice-at-a-time authority: read-only validation and inventory must finish before installation or any evidence-backed deletion is proposed, and no unseen installation or deletion target is authorized.
- 2026-07-20 — Approve the tightened exact Phase F Slice 1 after its four write paths, exact read-only roots, nine command strings, validation authorization, retention defaults, and prohibition on installation and deletion were all exposed.
- 2026-07-20 — Approve the exact Phase F Slice 1 root amendment: replace only the missing command 5 read-only root with the versioned nested package root; preserve every write path, constraint, criterion, other command, and prohibition on installation or deletion.
- 2026-07-20 — Retain every inventoried ScopeLock component. Active registration, discoverable runtime surfaces, known compatibility consumption, possible package/workflow dependencies, useful history, and incomplete no-break evidence leave no exact component eligible for deletion; this is a successful conservative classification, not cleanup failure.
- 2026-07-20 — Approve the exact Phase F Slice 2, including a one-time Guardrail exception for exactly three installed GamePlan files, in-place `apply_patch` installation with rollback, eight ordered provenance sources, final manifest retention, eleven validation commands, and complete six-phase closure; no ScopeLock or other external mutation is authorized.
- 2026-07-20 — Close Phase F and the six-phase GamePlan after the installed package validator and five-file equality check passed, retain every ScopeLock component because none had affirmative no-break deletion evidence, finalize the eight-source compiled footprint, and expire the one-time installed-file exception.

## Refresh Triggers

- The skill cannot reliably distinguish agreement from brainstorming.
- Updates damage locked strategy or erase decision history.
- Recommendations ignore the canonical plan or current workspace evidence.
- One-plan-per-workspace becomes restrictive in repeated use.
- Manual Markdown maintenance becomes unreliable or excessively repetitive.
- Command and natural-language invocations produce materially inconsistent behavior.
- Contradictory instructions bypass locked decisions instead of surfacing the conflict.
- The user explicitly changes the desired outcome, strategy, or guardrails.
- Footprints are skipped during write-based execution, updated only at task end, overwrite retained footprints, lose pre-existing dirty-path protection, or make cleanup candidates appear automatically deletable.
- A compiled footprint drops an explicit source, contains duplicate task paths, weakens the earliest baseline, or cannot remain conservative when source history conflicts.
- Execution silently expands the approved slice or changes strategy.
- Validation cannot close a slice without creating parallel lifecycle authority.
- A proposed ScopeLock deletion target has any known, possible, dynamic, indirect, undocumented, contradictory, or uncertain consumer.
- Repeated dogfooding proves Markdown-only execution control unreliable or excessively repetitive.
- A phase is marked complete without direct evidence for every locked completion criterion, passing every required validation, respected scope, a finalized footprint, and a successful canonical close update; or the next phase begins without explicit approval.

## Last Refreshed

2026-07-20 — Completed Phase F and the full six-phase plan from direct installation, retention, provenance, and canonical-close evidence. No execution slice or continuing external-write exception remains active.
