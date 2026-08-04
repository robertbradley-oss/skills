---
name: clean-handoff
description: Create one new Codex task with the minimum useful context, or return that context as copyable text. Use when the user asks to hand off, continue in a new task, or make a portable handoff.
---

# Clean Handoff

Keep this fast. Use context already present in the conversation; do not inspect the repository, run tests, or invoke a helper script just to prepare a handoff.

## Build the handoff

Write a short destination prompt containing only:

- the objective;
- completed and remaining work;
- important decisions or constraints;
- relevant files and validation state, when known;
- the immediate next action.

Do not include secrets, raw tool output, or speculative details. State that the destination must inspect live workspace state before changing anything. If a root `GAMEPLAN.md` exists, read it once immediately before handoff and treat it as the authority for plan status; do not search for it or stop when it is absent.

## Direct handoff

Use this route only when the user explicitly asks for a new Codex task.

1. Call `list_projects` once. Select the saved project explicitly named by the user; otherwise select the project whose local path matches the current workspace. Ask one concise question only if there is no unique match.
2. Continue in the selected saved project's existing workspace with `environment: { type: "local" }`. A new task is not an implicit request for a new Git worktree, and Git projects must not be switched to worktree mode merely because `isGitRepository` is true.
3. Use `environment: { type: "worktree" }` only when the user explicitly requests an isolated worktree. Require the user to name an existing starting branch or explicitly request the selected project's current working-tree state; pass that choice as `startingState`. Never rely on an inferred `main`, `master`, or default branch.
4. Call `create_thread` once with the short handoff as its prompt and do not wait for the new task to run.
5. Report whether creation succeeded. Do not retry automatically or create local handoff files.

## Portable handoff

Return the short handoff in one copyable Markdown block. Do not call task tools or write files.
