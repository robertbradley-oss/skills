# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Phase E Slice 1 template and UI-prompt dogfooding`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-20`
Finalized: `2026-07-20`
Baseline: `git status --short --untracked-files=all` captured after authorized slice activation and before the first Slice 1 execution write; 22 exact untracked paths were observed
Coverage: workspace paths only; the workspace skill, installed copies, ScopeLock, external products, other templates, prior evidence, compiled footprints, later Phase E slices, scripts, dependencies, and Phase F are outside the approved boundary

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled.md` | untracked | Pre-existing compiled footprint; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-20-execution-control-phase-a.md` | untracked | Finalized Phase A provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-20-execution-control-phase-b.md` | untracked | Finalized Phase B provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-20-execution-control-phase-c.md` | untracked | Finalized Phase C provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-20-execution-control-phase-d.md` | untracked | Finalized Phase D provenance; preserve unchanged. |
| `.gitignore` | untracked | Pre-existing workspace configuration; preserve unchanged. |
| `GAMEPLAN.md` | untracked | Existing canonical plan; protected even while narrowly activated and later closed for Slice 1. |
| `gameplan/SKILL.md` | untracked | Existing workspace skill source; outside Slice 1 and unchanged. |
| `gameplan/agents/openai.yaml` | untracked | Existing UI metadata; protected even while aligned in place. |
| `gameplan/assets/COMPILED_FOOTPRINT.template.md` | untracked | Existing compiled-footprint contract; outside Slice 1 and unchanged. |
| `gameplan/assets/GAMEPLAN.template.md` | untracked | Existing canonical template; protected even while aligned in place. |
| `gameplan/assets/TASK_FOOTPRINT.template.md` | untracked | Existing task-footprint contract; outside Slice 1 and unchanged. |
| `work/gameplan-compiled-footprint-results.md` | untracked | Existing evidence; outside Slice 1 and unchanged. |
| `work/gameplan-execution-control-phase-a-results.md` | untracked | Existing Phase A evidence; preserve unchanged. |
| `work/gameplan-execution-control-phase-b-results.md` | untracked | Existing Phase B evidence; preserve unchanged. |
| `work/gameplan-execution-control-phase-c-results.md` | untracked | Existing Phase C evidence; preserve unchanged. |
| `work/gameplan-execution-control-phase-d-results.md` | untracked | Existing Phase D evidence; preserve unchanged. |
| `work/gameplan-execution-control-phased-plan.md` | untracked | Approved source plan; preserve unchanged. |
| `work/gameplan-execution-control-proposal.md` | untracked | Historical superseded proposal; preserve unchanged. |
| `work/gameplan-v1-test-results.md` | untracked | Existing evidence; outside Slice 1 and unchanged. |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-e-slice-1.md` | created | temporary | remove | Retain as Slice 1 provenance until the footprint lifecycle permits removal. |
| `GAMEPLAN.md` | pre-existing | deliverable | keep | Activate and close Slice 1, then advance Phase E from direct evidence. |
| `gameplan/assets/GAMEPLAN.template.md` | pre-existing | deliverable | keep | Align the reusable canonical template with the proven execution-control contract. |
| `gameplan/agents/openai.yaml` | pre-existing | deliverable | keep | Align the UI prompt with strategic Lock, one exact slice, evidence, and closure. |
| `work/gameplan-execution-control-phase-e-slice-1-results.md` | created | deliverable | keep | Preserve direct Slice 1 validation and dogfooding evidence. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-e-slice-1.md` | remove | open | Remove only after finalization and a later authorized cleanup workflow approves removal. |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
