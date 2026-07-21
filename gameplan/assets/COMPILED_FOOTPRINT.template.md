# GamePlan Compiled Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Compiled provenance for <plan purpose>`
Plan: `GAMEPLAN.md`
State: `active`
Started: `YYYY-MM-DD`
Finalized: `—`
Baseline: `Materialized from the explicitly ordered finalized sources below`
Coverage: `workspace paths only`
Scope: `compiled`

## Compiled sources

| Order | Footprint |
|---|---|
| `1` | `.gameplan/footprints/<task-key>.md` |

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|
| `<workspace/relative/path>` | `<modified, staged, untracked, or uncertain>` | `<why it was protected before the plan's first write task>` |

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `<workspace/relative/path>` | `<created or pre-existing>` | `<deliverable, temporary, scaffold, experiment, or uncertain>` | `<keep, remove, adopted, abandoned, or review>` | `<latest consistent plan-level intent>` |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `<workspace/relative/path>` | `<remove, restore, inspect, transfer, or other>` | `<open, done, or waived>` | `<latest consistent obligation>` |

## Consumer contract

- Resolve only exact workspace-relative paths; use `/` separators and no globs.
- Treat `keep` and `adopted` as intentional deliverables.
- Treat `remove` and `abandoned` only as cleanup candidates, never as deletion authorization by themselves.
- Never automatically delete a protected path, an item marked `review`, an uncertain item, an absent entry, or an unlisted path.
- Verify current existence and state before acting; this footprint records intent, not proof of present filesystem state.
- Consume only `finalized` footprints for cleanup decisions. Treat `active` footprints as incomplete.
- Treat `Compiled sources` as provenance only; never expand them or infer unlisted sources.
