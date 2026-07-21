# Game Plan

## Outcome

Define the observable result that means the plan succeeded.

## Strategy

State the chosen approach and why it was selected.

## Guardrails

- List constraints, protected decisions, preferences, and non-goals.

## Approved Execution Slice

None approved. A Lock or Update may replace this safe default with at most one explicitly user-approved slice containing approval authority, objective, exact allowed files or directory prefixes, constraints, completion criteria, exact validation commands, validation authorization, and concise evidence state. This section is execution authority; Task Footprints and work reports are not.

Keep the approved slice active when any completion criterion or validation is failed, incomplete, stale, inferred, or uncertain. Record the exact blocker under Current State and keep Next Move on an in-scope repair or revalidation action.

Close only when every criterion has direct evidence and every required validation passes. Use one targeted Update to compact the durable outcome into Current State, advance Next Move without approving it, preserve the strategic core and Decisions, finalize the task footprint, and return this section to `None approved`. `None approved` means no write-based execution is authorized; it is not a parallel lifecycle state.

## Workstreams

1. Name the major bodies of work and describe their relationships.

## Current State

### Completed

- Record compact completed outcomes backed by direct evidence and point to detailed reports when needed.

### Active

- Record the approved slice's current in-scope work and evidence status.

### Blocked

- Record failed or incomplete completion criteria, the observed result, and what would clear each blocker.

## Task Footprint

None active. During write-based execution under an approved slice, point to one task artifact under `.gameplan/footprints/`. When multiple task footprints feed plan-wide cleanup, point only to one materialized compiled artifact without copying its file-level detail here. This is cleanup provenance and never execution authority.

## Next Move

State one concrete in-scope action, or one proposed slice when none is approved, plus why it comes next and its completion evidence. Next Move does not authorize execution.

## Open Questions

- Record unresolved decisions that could materially affect execution.

## Decisions

- YYYY-MM-DD — Record an agreed decision and its rationale.

## Refresh Triggers

- List conditions that require the strategy to be reviewed.

## Last Refreshed

YYYY-MM-DD — Identify the conversation, evidence, or event used for this refresh.
