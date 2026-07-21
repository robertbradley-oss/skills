# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Add plan-wide compiled footprint capability`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-19`
Finalized: `2026-07-19`
Baseline: `git status --short --untracked-files=all returned the protected paths listed below before the first task write; the installed GamePlan skill matched the workspace source`
Coverage: `workspace paths only`

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `.gameplan/footprints/2026-07-19-task-footprint-capability.md` | `untracked` | Finalized footprint-capability provenance existed before this task. |
| `.gitignore` | `untracked` | User-owned repository configuration existed before this task. |
| `GAMEPLAN.md` | `untracked` | Canonical GamePlan product plan existed before this task. |
| `gameplan/SKILL.md` | `untracked` | Installed source instructions existed before this task. |
| `gameplan/agents/openai.yaml` | `untracked` | Skill UI metadata existed before this task. |
| `gameplan/assets/GAMEPLAN.template.md` | `untracked` | Canonical plan template existed before this task. |
| `gameplan/assets/TASK_FOOTPRINT.template.md` | `untracked` | Task footprint template existed before this task. |
| `work/gameplan-execution-control-proposal.md` | `untracked` | Parked proposal existed before this task and remains untouched. |
| `work/gameplan-v1-test-results.md` | `untracked` | Existing validation evidence existed before this task. |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `GAMEPLAN.md` | `pre-existing` | `deliverable` | `keep` | Record the compiled-footprint contract and evidence. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled-footprint-capability.md` | `created` | `deliverable` | `keep` | Preserve this capability task's provenance. |
| `.gameplan/footprints/2026-07-19-gameplan-compiled.md` | `created` | `deliverable` | `keep` | Dogfood plan-wide compiled provenance for GamePlan itself. |
| `gameplan/SKILL.md` | `pre-existing` | `deliverable` | `keep` | Define conservative compiled-footprint production and lifecycle. |
| `gameplan/assets/GAMEPLAN.template.md` | `pre-existing` | `deliverable` | `keep` | Point new plans at one active or compiled footprint. |
| `gameplan/assets/COMPILED_FOOTPRINT.template.md` | `created` | `deliverable` | `keep` | Provide the materialized v1 rollup shape. |
| `work/gameplan-compiled-footprint-results.md` | `created` | `deliverable` | `keep` | Preserve validation, dogfood, and installed-parity evidence. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
