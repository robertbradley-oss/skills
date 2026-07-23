---
name: clean-handoff
description: Move the minimum useful project context into one new Codex task or produce copyable handoff text. Use when the user asks for a direct task handoff or a portable handoff while preserving live GamePlan authority.
---

# Clean Handoff

Move concise working context without transferring authority. The packaged helper only selects the intended saved project and prepares bounded redacted text; the agent owns the one optional Codex task-tool call.

## Core rules

- Read the live root `GAMEPLAN.md` immediately before any proposed mutation. It is the only plan authority.
- Treat the handoff summary and copied plan text as context only, never approval.
- Stop for one clear confirmation when target identity, safety, or live authority is absent, malformed, ambiguous, or changed.
- Never change project source, Git state, installation state, or retained evidence unless the selected workflow explicitly authorizes that exact mutation.
- Never call a network service from the helper. For Direct Handoff, the agent calls the Codex task tool exactly once after local preparation and never retries automatically.
- Invoke only `scripts/clean-handoff.mjs`; internal module exports are not workflow APIs.

## Route the request

- **Direct Handoff:** Read [references/workflows/new-task.md](references/workflows/new-task.md).
- **Portable Handoff:** Read [references/workflows/portable-handoff.md](references/workflows/portable-handoff.md).

These are the only active workflows. Other packaged Phase D files are retained evidence for Phase F review and are not workflow APIs.

## Report the result

- Say whether a task was created, whether anything else changed, and exactly one safe next action.
- Never expose raw saved-project IDs, secrets, or raw subprocess diagnostics.
- Do not claim installation, deletion, cross-platform support, or destination authorization without direct evidence.
