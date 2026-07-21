# GamePlan Compiled Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Compiled provenance for the GamePlan product plan`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-19`
Finalized: `2026-07-19`
Baseline: `Materialized from the explicitly ordered source footprints below`
Coverage: `workspace paths only`
Scope: `compiled`

## Compiled sources

| Order | Footprint |
|---|---|
| `1` | `.gameplan/footprints/2026-07-19-task-footprint-capability.md` |
| `2` | `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` |

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `.gitignore` | `untracked` | Repository configuration predated the compiled-footprint work. |
| `GAMEPLAN.md` | `untracked` | Canonical plan predated the compiled-footprint work. |
| `gameplan/SKILL.md` | `untracked` | Skill source predated the compiled-footprint work. |
| `gameplan/agents/openai.yaml` | `untracked` | Skill UI metadata predated the compiled-footprint work. |
| `gameplan/assets/GAMEPLAN.template.md` | `untracked` | Plan template predated the compiled-footprint work. |
| `work/gameplan-execution-control-proposal.md` | `untracked` | Parked proposal remains protected and untouched. |
| `work/gameplan-v1-test-results.md` | `untracked` | Existing validation evidence remains protected. |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `.gameplan/footprint.md` | `created` | `experiment` | `abandoned` | Preserve the recorded rejection of the fixed-path prototype. |
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | `created` | `temporary` | `remove` | Retain until an authorized cleanup pass resolves its open obligation. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` | `created` | `deliverable` | `keep` | Preserve compiled-footprint capability provenance. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled.md` | `created` | `deliverable` | `keep` | Provide one plan-wide source for Post Clean. |
| `gameplan/assets/TASK_FOOTPRINT.template.md` | `created` | `deliverable` | `keep` | Preserve the task-level provenance template. |
| `gameplan/assets/COMPILED_FOOTPRINT.template.md` | `created` | `deliverable` | `keep` | Preserve the plan-wide materialization template. |
| `gameplan/SKILL.md` | `pre-existing` | `deliverable` | `keep` | Preserve task and compiled-footprint behavior. |
| `gameplan/assets/GAMEPLAN.template.md` | `pre-existing` | `deliverable` | `keep` | Preserve single-pointer guidance. |
| `gameplan/agents/openai.yaml` | `pre-existing` | `deliverable` | `keep` | Preserve skill UI metadata. |
| `GAMEPLAN.md` | `pre-existing` | `deliverable` | `keep` | Preserve the canonical plan and compiled pointer. |
| `work/gameplan-v1-test-results.md` | `pre-existing` | `deliverable` | `keep` | Preserve existing validation evidence. |
| `work/gameplan-compiled-footprint-results.md` | `created` | `deliverable` | `keep` | Preserve compiled-footprint validation evidence. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `.gameplan/footprint.md` | `remove` | `done` | Abandoned fixed-path prototype is absent. |
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | `remove` | `open` | Retain until Post Clean review and explicit authorization. |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
- Treat `Compiled sources` as provenance only; never expand them or infer unlisted sources.
