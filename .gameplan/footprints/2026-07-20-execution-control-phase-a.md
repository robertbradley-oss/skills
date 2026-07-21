# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Execution-control Phase A canonical authority contract`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-20`
Finalized: `2026-07-20`
Baseline: `git status --short --untracked-files=all` captured before the GamePlan Lock and first Phase A write; 14 exact untracked paths were observed
Coverage: workspace paths only; installed skill copies, ScopeLock, and Clean Handoff are outside the authorized Phase A boundary

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled.md` | untracked | Pre-existing compiled footprint; preserve unchanged. |
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | untracked | Pre-existing finalized provenance; preserve unchanged. |
| `.gitignore` | untracked | Pre-existing workspace configuration; preserve unchanged. |
| `GAMEPLAN.md` | untracked | Existing canonical plan; protected even while narrowly updated for the approved Lock and Phase A. |
| `gameplan/SKILL.md` | untracked | Existing skill source; protected even while modified in place. |
| `gameplan/agents/openai.yaml` | untracked | Existing UI metadata; protected even while modified in place. |
| `gameplan/assets/COMPILED_FOOTPRINT.template.md` | untracked | Existing compiled-footprint contract; outside Phase A and unchanged. |
| `gameplan/assets/GAMEPLAN.template.md` | untracked | Existing canonical template; protected even while modified in place. |
| `gameplan/assets/TASK_FOOTPRINT.template.md` | untracked | Existing task-footprint contract; outside Phase A and unchanged. |
| `work/gameplan-compiled-footprint-results.md` | untracked | Existing evidence; outside Phase A and unchanged. |
| `work/gameplan-execution-control-phased-plan.md` | untracked | Approved source plan; retained unchanged during implementation. |
| `work/gameplan-execution-control-proposal.md` | untracked | Historical superseded proposal; retained unchanged. |
| `work/gameplan-v1-test-results.md` | untracked | Existing evidence; outside Phase A and unchanged. |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-a.md` | created | temporary | remove | Retain as Phase A provenance until the footprint lifecycle permits removal. |
| `GAMEPLAN.md` | pre-existing | deliverable | keep | Lock the approved phased strategy, point to this footprint, and close Phase A from evidence. |
| `gameplan/SKILL.md` | pre-existing | deliverable | keep | Define the canonical Approved Execution Slice contract and Lock semantics. |
| `gameplan/assets/GAMEPLAN.template.md` | pre-existing | deliverable | keep | Add the safe `None approved` slice default and authority guidance. |
| `gameplan/agents/openai.yaml` | pre-existing | deliverable | keep | Make execution-control behavior discoverable in GamePlan UI metadata. |
| `work/gameplan-execution-control-phase-a-results.md` | created | deliverable | keep | Preserve direct Phase A validation and contract-review evidence. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `.gameplan/footprints/2026-07-20-execution-control-phase-a.md` | remove | open | Remove only after finalization and a later authorized cleanup workflow approves removal. |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
