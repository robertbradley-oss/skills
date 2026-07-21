# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Execution-control Phase B approval-bound execution`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-20`
Finalized: `2026-07-20`
Baseline: `git status --short --untracked-files=all` captured before Phase B activation and the first Phase B write; 16 exact untracked paths were observed
Coverage: workspace paths only; installed skill copies, templates, UI metadata, ScopeLock, and Clean Handoff are outside the approved Phase B boundary

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled.md` | untracked | Pre-existing compiled footprint; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-20-execution-control-phase-a.md` | untracked | Finalized Phase A provenance; preserve unchanged. |
| `.gitignore` | untracked | Pre-existing workspace configuration; preserve unchanged. |
| `GAMEPLAN.md` | untracked | Existing canonical plan; protected even while narrowly updated for Phase B. |
| `gameplan/SKILL.md` | untracked | Existing workspace skill source; protected even while modified in place. |
| `gameplan/agents/openai.yaml` | untracked | Existing UI metadata; outside Phase B and unchanged. |
| `gameplan/assets/COMPILED_FOOTPRINT.template.md` | untracked | Existing compiled-footprint contract; outside Phase B and unchanged. |
| `gameplan/assets/GAMEPLAN.template.md` | untracked | Existing canonical template; outside Phase B and unchanged. |
| `gameplan/assets/TASK_FOOTPRINT.template.md` | untracked | Existing task-footprint contract; outside Phase B and unchanged. |
| `work/gameplan-compiled-footprint-results.md` | untracked | Existing evidence; outside Phase B and unchanged. |
| `work/gameplan-execution-control-phase-a-results.md` | untracked | Existing Phase A evidence; preserve unchanged. |
| `work/gameplan-execution-control-phased-plan.md` | untracked | Approved source plan; preserve unchanged. |
| `work/gameplan-execution-control-proposal.md` | untracked | Historical superseded proposal; preserve unchanged. |
| `work/gameplan-v1-test-results.md` | untracked | Existing evidence; outside Phase B and unchanged. |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-b.md` | created | temporary | remove | Retain as Phase B provenance until the footprint lifecycle permits removal. |
| `GAMEPLAN.md` | pre-existing | deliverable | keep | Activate and close the Phase B slice, then advance the locked plan from evidence. |
| `gameplan/SKILL.md` | pre-existing | deliverable | keep | Implement approval-bound execution, scope-expansion pauses, and slice-aware status behavior. |
| `work/gameplan-execution-control-phase-b-results.md` | created | deliverable | keep | Preserve direct Phase B validation and scenario-review evidence. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-b.md` | remove | open | Remove only after finalization and a later authorized cleanup workflow approves removal. |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
