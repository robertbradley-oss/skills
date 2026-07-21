# GamePlan Task Footprint

Schema: `gameplan-task-footprint/v1`
Task: `<short task name>`
Plan: `GAMEPLAN.md`
State: `active`
Started: `YYYY-MM-DD`
Finalized: `—`
Baseline: `<inspection performed before the first task write>`
Coverage: `workspace paths only`

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `<workspace/relative/path>` | `<modified, staged, untracked, or uncertain>` | `<why it must be preserved>` |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `<workspace/relative/path>` | `<created or pre-existing>` | `<deliverable, temporary, scaffold, experiment, or uncertain>` | `<keep, remove, adopted, abandoned, or review>` | `<brief intended role>` |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `<workspace/relative/path>` | `<remove, restore, inspect, transfer, or other>` | `<open, done, or waived>` | `<brief obligation>` |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
