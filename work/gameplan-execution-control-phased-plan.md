# Proposed GamePlan: absorb ScopeLock capabilities into Lock

**Status:** Proposed for user approval; not locked and not authorized for implementation.

**Prepared:** 2026-07-20

## Approval effect

Approval of this draft would:

- lock the Outcome, Strategy, and Guardrails below into the canonical `GAMEPLAN.md`;
- remove the prior Clean Handoff v0.8 timing gate because Clean Handoff is neither a dependency nor a target of this work;
- lock this as a behavioral absorption into GamePlan's "lock in this plan" command, not a source-level merge of either product;
- authorize only Phase A's initial execution slice, while locking later phases as sequencing rather than blanket implementation authority;
- leave Clean Handoff completely out of scope and leave ScopeLock unchanged during Phases A through E;
- make dependency-safe retirement part of Phase F: delete only ScopeLock material affirmatively proven unable to break any skill or related product, and retain everything with a known, possible, uncertain, or unverified dependency.

## Outcome

Make GamePlan's "lock in this plan" command the single authority for strategic continuity and execution control by absorbing ScopeLock's beneficial approval-boundary and verification abilities.

A completed integration must let one canonical `GAMEPLAN.md`:

- lock Outcome, Strategy, and Guardrails until the user explicitly revises them;
- hold at most one explicitly approved execution slice with an objective, allowed files, constraints, completion criteria, and validation commands;
- require approval before strategy changes, relaxed constraints, replacement objectives, or scope expansion;
- guide execution without a second active pointer, immutable Git baseline, or parallel lifecycle/status system;
- record direct validation evidence and close a completed slice through one targeted GamePlan Update;
- preserve task footprints as cleanup provenance and detailed reports as evidence without allowing either to override the canonical plan.

The integration is complete when fresh-context use reliably obeys the approved slice, stops at approval boundaries, closes with direct evidence, preserves strategic authority, no longer needs standalone ScopeLock to manage ordinary GamePlan execution, and every ScopeLock component has been conservatively classified: safely removable material is gone, while anything that could possibly support another skill or product is retained.

## Strategy

Evolve the existing local, Markdown-backed GamePlan Lock behavior rather than merge ScopeLock source code or architecture. This is a product-capability absorption: users continue to invoke GamePlan, and GamePlan owns the resulting plan authority and execution boundary.

Absorb only ScopeLock's useful product concepts:

- explicit user approval of a concrete work boundary;
- exact allowed files and directory prefixes;
- explicit approval for scope expansion;
- honest, evidence-backed verification with uncertainty preserved.

Keep GamePlan's existing authority model and artifacts:

- `GAMEPLAN.md` is normative authority;
- the Approved Execution Slice is the current authorization boundary;
- Task Footprints and compiled footprints are non-authoritative cleanup provenance;
- work reports contain detailed validation evidence;
- Current State and Next Move remain the only operational status model;
- Decisions preserve material approvals and strategic revisions.

Implement and validate the feature in phases. Lock the full strategic direction once approved, but authorize only one phase-sized execution slice at a time. Close each phase with evidence and a canonical-plan update before approving the next slice.

## Guardrails

- Do not merge ScopeLock wholesale or copy its helper, hooks, `.codex-scope/` storage, active pointer, contract/baseline store, amendments, report lifecycle, health states, or finding taxonomy.
- Do not modify ScopeLock during Phases A through E. Phase F may remove an exact component only after GamePlan passes all replacement gates, the concrete retirement inventory is approved, and affirmative dependency evidence shows its removal cannot break any other skill or related product.
- Keep Clean Handoff completely out of scope. It is not a dependency, compatibility workstream, implementation target, validation surface, or release gate for this plan.
- Preserve useful historical ScopeLock evidence in version-control history and one concise retirement report; do not retain redundant runtime copies merely as history.
- Define `unused` narrowly: a ScopeLock component is unused only when it is not absorbed into GamePlan and affirmative dependency analysis proves that no installed or source skill, plugin, workflow, hook, configuration, package, or related product could consume it. Lack of a discovered reference is not proof that removal is safe.
- Treat every known, possible, uncertain, dynamic, indirect, undocumented, or unverified dependency as a preservation requirement. When evidence is incomplete or contradictory, retain the component and classify it `retain — dependency uncertain`.
- Retain the minimal `scopelock/context/v2` and `scopelock/reserved-sideband/v1` provider while it has a verified external consumer. Its retention does not make it GamePlan authority and does not authorize Clean Handoff changes.
- Never perform a blanket recursive deletion of `.codex-scope/` directories. Phase F must enumerate exact stores, distinguish retained evidence from proven removable residue, verify each target and consumer, and use supported uninstall/removal paths only when they preserve every retained dependency.
- Do not delete, archive, unpublish, or rewrite a remote ScopeLock repository or marketplace listing without separate explicit approval; the locked retirement target is local standalone implementation and installation residue unless expanded later.
- Keep `GAMEPLAN.md` as the only normative authority. No footprint, report, helper output, installed cache, or hidden metadata may select or broaden the active slice.
- Keep Outcome, Strategy, and Guardrails locked until explicit user revision.
- Allow at most one approved execution slice at a time.
- Require explicit approval before adding allowed files or directories, relaxing a constraint or completion criterion, replacing the slice objective, or changing the strategic core.
- Use exact workspace-relative files and directory prefixes for the initial scope grammar. Require explicit approval for `.` as the whole workspace.
- Treat listed validation commands as standing authorization only when exact, project-local, and non-destructive. Networked, privileged, destructive, or externally mutating commands still require contemporaneous approval.
- Never claim authorship from Git state. Preserve pre-existing and concurrent changes and label attribution uncertainty.
- Keep detailed command output and repetitive evidence in named work reports; keep only concise outcomes and evidence pointers in `GAMEPLAN.md`.
- Maintain existing task-footprint and compiled-footprint cleanup protections, including earliest-baseline protection and no automatic deletion authorization.
- Keep the first implementation Markdown-only. Add a helper only after repeated dogfooding proves a specific reliability failure.
- Do not install or publish the revised skill until its workspace source passes structural and behavioral validation.

## Authority model

| Artifact | Role | May authorize or broaden work? |
|---|---|---|
| `GAMEPLAN.md` | Strategic and execution authority | Yes, only through explicit user-approved changes |
| Approved Execution Slice | One current implementation boundary inside `GAMEPLAN.md` | Yes, within its exact approved fields |
| Task Footprint | Per-task creation and cleanup provenance | No |
| Compiled Footprint | Plan-wide cleanup handoff | No |
| Work report | Detailed tests, inspections, and evidence | No |
| ScopeLock history | Retained historical evidence | No |
| Helper output, if added later | Read-only or evidence-producing support | No |

## Absorption and retirement decision rule

Each ScopeLock capability receives one of three dispositions:

- **Absorb:** Re-express the user benefit inside GamePlan's canonical Lock, Status, execution, or Update behavior.
- **Retain as compatibility:** Keep only a verified live interface required by another product; it remains non-authoritative for GamePlan.
- **Removal candidate:** Delete only after GamePlan proves the replacement and affirmative evidence shows the exact component cannot possibly break another skill or related product. Otherwise retain it.

A capability is absorbed only when it passes all of these tests:

- **Lock relevance:** It directly strengthens what the user means by "lock in this plan."
- **Single-authority fit:** It can live in or derive from `GAMEPLAN.md` without another active pointer, baseline, lifecycle, or status authority.
- **User-value test:** It protects an approval boundary, prevents silent scope drift, or makes completion evidence more trustworthy.
- **Minimality test:** It can be implemented through the Markdown-backed skill without importing a forensic subsystem merely for theoretical assurance.
- **Non-duplication test:** Existing Current State, Decisions, Task Footprints, compiled footprints, and work reports cannot already provide the benefit cleanly.
- **Evidence-honesty test:** It does not require invented authorship or certainty that repository evidence cannot prove.

Removal uses a separate, fail-safe test. A component is removable only when its absorbed replacement has passed Phase E, the exact dependency inventory affirmatively proves no direct, indirect, dynamic, configured, packaged, or related-product consumer remains, its historical value has a concise retained pointer, and its deletion target, validation method, and recovery path are known. Absence from search results, documentation, or the current installed catalog is insufficient. Any plausible breakage path changes the disposition to retain.

| ScopeLock capability | Disposition | Reason |
|---|---|---|
| Objective, exact allowed files/directories, locked constraints, completion criteria | Absorb | These are the core Approved Execution Slice inside GamePlan Lock |
| Approval of inferred material scope and later scope expansion | Absorb | This protects the user's authorization boundary without a second product |
| Default-deny behavior outside the approved slice | Absorb | An unlisted file need must pause for approval |
| Explicit forbidden paths | Absorb as Guardrails or slice constraints | GamePlan needs the protection, not a separate rule store |
| Exact project-relative file and directory-prefix grammar | Absorb | It is simple, inspectable, and sufficient for the first version |
| Direct validation results and honest `verified`, `inferred`, or `uncertain` language | Absorb | This improves closure evidence without importing report states |
| Preserve pre-existing dirty paths and avoid invented authorship | Absorb through existing Task Footprints and execution rules | GamePlan already has the right provenance surface |
| Late approval must not rewrite history | Absorb through Decisions and evidence | Preserve the principle without a `late-approved` outcome enum |
| Lock proposal, activation, inspection, verification, and closure as separate commands | Removal candidate after replacement | GamePlan owns these interactions, but files stay if any other consumer could depend on them |
| `.codex-scope/active.json`, immutable contracts, baselines, amendments, and reports | Removal candidate after exact evidence and dependency review | They are parallel authority for GamePlan, but retained evidence or consumers override cleanup |
| Git fingerprints, ancestry reconciliation, stale-baseline machinery, and Git-only activation | Removal candidate | They are not absorbed; retain them if another skill or product could consume their behavior or evidence |
| Separate lifecycle, health, finding, and report-outcome taxonomies | Removal candidate | GamePlan does not use them, but shared schemas or consumers require retention |
| PreToolUse, PostToolUse, SessionStart, and Stop hooks | Removal candidate after behavioral validation | Remove only when hook registration and every possible consumer are affirmatively cleared |
| Standalone ScopeLock Lock, Status, and Verify skills, demos, marketplace product surface, and redundant docs/tests | Removal candidate after cutover | Delete only exact parts proven consumer-free; uncertainty or related-product use requires retention |
| `scopelock/context/v2` plus reserved-sideband classification | Retain as minimal compatibility while consumed | A read-only dependency audit found an active external consumer; deleting it would break that consumer while Clean Handoff remains untouched |

## Phases

### Phase A: canonical authority contract

**Purpose:** Encode the single-authority model and the Approved Execution Slice contract in GamePlan's workspace source.

**Phase outcomes:**

- `gameplan/SKILL.md` defines one optional Approved Execution Slice and distinguishes it from Task Footprints, compiled footprints, validation evidence, Current State, and Next Move.
- `gameplan/assets/GAMEPLAN.template.md` contains a usable slice structure with `None approved` as the safe default.
- The explicit `$gameplan` Lock operation and ordinary-language "lock in this plan" request distinguish a strategic-only plan from a plan with an approved execution slice.
- The skill requires approval for inferred material slice fields and forbids auxiliary active pointers or repository baselines.
- Workspace structural validation passes and the canonical plan records evidence before Phase B is proposed.

**Phase gate:** The authority hierarchy is unambiguous in a fresh context, existing footprint behavior remains intact, and no implementation writes occur outside the approved Phase A slice.

### Phase B: approval-bound execution behavior

**Purpose:** Make the approved slice govern execution and scope changes.

**Phase outcomes:**

- GamePlan reads the complete plan and slice before the first authorized mutation.
- In-scope work proceeds without reopening strategy.
- Adding a file or directory, relaxing a constraint, changing completion criteria, or replacing the objective stops at an explicit approval boundary.
- Strategy changes remain separate from scope amendments and create preserved decision history when approved.
- The task footprint begins before the first phase mutation and records provenance without becoming execution authority.

**Phase gate:** Fresh-context exercises demonstrate both uninterrupted in-scope execution and reliable pauses for scope expansion or strategic conflict.

### Phase C: validation evidence and close-through-Update

**Purpose:** Connect completion criteria to direct evidence and return completed work cleanly to the canonical plan.

**Phase outcomes:**

- Every completion criterion receives an exact inspection or command result, timestamp, exit status or observed outcome, concise summary, and evidence pointer when detail matters.
- Failed or incomplete validation leaves the slice active and records the blocker in Current State.
- Successful closure is one targeted Update that compacts the durable outcome into Current State, advances Next Move, preserves decision history, and sets the slice to `None approved`.
- Closing does not create separate `closed`, `abandoned`, health, or report-outcome authority.

**Phase gate:** Both successful and failed closure scenarios preserve strategic sections, task-footprint provenance, and direct evidence without duplicate lifecycle state.

### Phase D: adversarial behavioral validation

**Purpose:** Prove the model under the failure cases that made ScopeLock valuable without importing ScopeLock's architecture.

**Phase outcomes:**

- Validation covers dirty worktrees, protected pre-existing paths, untracked files, concurrent unrelated changes, missing allowed files, late scope requests, risky validation commands, failed tests, stale evidence, and interrupted execution.
- GamePlan never invents authorship, silently expands scope, treats footprint provenance as proof, or rewrites strategy from operational evidence.
- ScopeLock v0.2 historical records and reserved-sideband behavior remain untouched.
- Tests demonstrate that the beneficial ScopeLock behaviors now belong to GamePlan Lock, Status, execution, and Update semantics without invoking ScopeLock.

**Phase gate:** The complete behavioral matrix passes in fresh tasks and no unresolved high-severity authority conflict remains.

### Phase E: real-project dogfooding

**Purpose:** Validate usefulness and friction across ordinary work rather than only constructed tests.

**Phase outcomes:**

- At least two real multi-file execution slices complete, including one dirty-worktree case and one scope-expansion decision.
- Each slice produces a finalized task footprint, direct validation evidence, a compact Current State milestone, and the correct Next Move.
- Repeated failures, friction, or ambiguity are captured as evidence; implementation does not grow scripts or new state merely as a precaution.
- The product can distinguish strategy approval, slice approval, validation authorization, and cleanup approval in normal conversation.

**Phase gate:** Dogfooding shows reliable strategic continuity and execution control with less workflow duplication than standalone ScopeLock.

### Phase F: install, cut over, and retire unused ScopeLock parts

**Purpose:** Finish the GamePlan capability, cut ordinary execution control over to GamePlan, and conservatively remove only ScopeLock components proven safe to delete.

**Phase outcomes:**

- Workspace and installed GamePlan copies match after final validation.
- UI metadata and examples describe strategic Lock, approved execution slices, phase closure, and provenance accurately.
- A durable results report records structural validation, behavioral validation, dogfooding evidence, limitations, and remaining open questions.
- An exact retirement manifest maps every ScopeLock source, installed, configuration, hook, storage, documentation, test, asset, and marketplace-related component to `remove — dependency safety proven`, `retain — live dependency`, `retain — possible dependency`, `retain — dependency uncertain`, `retain — historical evidence`, or `separate approval required`.
- The dependency audit covers installed and source skills, plugins, router skills, hooks, scripts, package entry points, configuration, generated registrations, workflow documentation, versioned schemas, sideband providers, and related products. Static search is supporting evidence, not sufficient proof by itself.
- Standalone ScopeLock surfaces are removed through supported uninstall or exact-path cleanup only when the manifest records affirmative no-break evidence. Any surface with a possible or unverified consumer remains intact.
- Only verified live compatibility residue remains, including the minimal context/reserved-sideband provider while externally consumed; it has no GamePlan authority.
- Exact local ScopeLock evidence stores are reviewed individually. Only proven redundant residue is removed; useful history, uncertain data, externally owned data, and anything another product could inspect are preserved.
- Removal validation proves GamePlan still passes its complete matrix and every retained dependency still works without any related-product modification. Remaining ScopeLock surfaces are documented as retained dependencies or uncertainty, not mislabeled as cleanup failures.

**Phase gate:** GamePlan execution control is installed and proven, the approved local ScopeLock retirement manifest has been executed and verified, every deletion has affirmative no-break evidence, all known or possible dependencies are retained and documented, and remote/public actions remain untouched unless separately approved.

## Initial approved execution slice proposed with this plan

Plan approval would authorize Phase A only.

- **Objective:** Encode the Approved Execution Slice authority contract and safe template default without implementing later-phase execution, closure, installation, or ScopeLock disposition work.
- **Allowed files:**
  - `GAMEPLAN.md`
  - `gameplan/SKILL.md`
  - `gameplan/assets/GAMEPLAN.template.md`
  - `gameplan/agents/openai.yaml`
  - `work/gameplan-execution-control-phase-a-results.md`
  - `.gameplan/footprints/2026-07-20-execution-control-phase-a.md`
- **Constraints:**
  - Preserve all unrelated and pre-existing workspace content.
  - Do not modify or invoke Clean Handoff or ScopeLock, and do not modify installed skill copies, compiled footprints, or prior evidence reports.
  - Do not add scripts or hidden state.
  - Keep later phases unimplemented and unauthorized.
- **Completion criteria:**
  - The workspace skill and template express the single-authority model and one optional slice.
  - Strategic-only Lock and Lock-with-slice behavior are distinguishable.
  - Inferred material slice fields require approval.
  - Task Footprints remain provenance and do not gain execution authority.
  - The official skill validator passes.
  - A fresh-context contract review finds no duplicate authority or lifecycle.
- **Validation commands:**
  - `$env:PYTHONPATH='work/validator-deps'; python 'C:\Users\robby\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'gameplan'`
  - `git diff --check`
- **Validation authorization:** Granted with plan approval for these exact local, non-destructive commands.
- **Evidence target:** `work/gameplan-execution-control-phase-a-results.md`

Any new file or command needed during Phase A requires approval before use.

## Current evidence

- GamePlan v1, milestone compaction, task footprints, and compiled footprints are installed and validated in the current canonical plan.
- ScopeLock `0.2.0+codex.20260719234815` is locally installed. Its v0.2 contract adds authoritative reserved-sideband classification while retaining the separate Lock, Status, Verify, baseline, and lifecycle architecture that this plan intentionally does not absorb.
- Clean Handoff is explicitly excluded. Its source, installed version, release state, workflows, compatibility contracts, and future work do not gate or participate in this plan.
- A read-only dependency audit found that Clean Handoff currently consumes `scopelock/context/v2` and `scopelock/reserved-sideband/v1`. Therefore that minimal provider is currently used compatibility residue, not an unused deletion target; no Clean Handoff change is included.
- No GamePlan execution-control implementation has begun.

## Open questions deferred beyond plan approval

- Does repeated dogfooding justify a subordinate read-only changed-path helper, or is Markdown plus direct inspection sufficient?
- Should this capability remain an evolution of GamePlan v1 or receive a new product-version label at installation time?
- What is the smallest independently retainable package boundary for the live ScopeLock context/reserved-sideband provider without preserving the standalone Lock product?
- Should any remote ScopeLock repository or marketplace listing later be archived or unpublished? That action is intentionally outside the local retirement authorization.

## Decisions proposed for locking

- 2026-07-20 — Make GamePlan the single normative authority for strategic continuity and one approved execution slice.
- 2026-07-20 — Absorb ScopeLock's approval-boundary, exact-scope, and verification concepts without merging its storage, baseline, hooks, lifecycle, health, or report architecture.
- 2026-07-20 — Treat Task Footprints as cleanup provenance and work reports as evidence; neither may authorize or broaden execution.
- 2026-07-20 — Lock the phased strategy while approving only one phase-sized execution slice at a time.
- 2026-07-20 — Remove Clean Handoff from the dependency graph and scope entirely; absorb ScopeLock's beneficial abilities directly into GamePlan's "lock in this plan" behavior.
- 2026-07-20 — Make conservative local ScopeLock retirement part of GamePlan completion: delete only exact components affirmatively proven unable to break another skill or related product; retain useful history plus every known, possible, uncertain, indirect, or unverified dependency.

## Refresh triggers

- A phase exposes competing authority between the canonical plan, slice, footprint, report, or retained ScopeLock evidence.
- Fresh-context execution silently expands scope or changes strategy.
- Direct validation cannot close a slice without reintroducing a parallel lifecycle.
- Task-footprint cleanup provenance becomes confused with execution authorization.
- ScopeLock changes materially beyond the inspected v0.2 contract.
- The live dependency inventory shows a proposed ScopeLock deletion target is still consumed.
- Dependency evidence for a proposed deletion is missing, indirect, dynamic, contradictory, or uncertain.
- The retained context/reserved-sideband provider cannot be isolated without preserving broader standalone ScopeLock behavior.
- Repeated dogfooding proves Markdown-only execution control unreliable or excessively repetitive.
- The user changes the desired outcome, strategy, guardrails, phase order, or initial execution slice.

## Recommended model

Use **gpt-5.6-sol with xhigh reasoning** for the locked implementation phases. This is the strongest available agentic coding option for a task that combines product-contract design, multi-file skill changes, approval semantics, adversarial validation, and preservation of existing dirty-worktree evidence.

Use gpt-5.6-terra only for bounded follow-up work where lower latency matters more than maximum reasoning depth, such as rerunning validators or making a narrowly specified documentation correction.
