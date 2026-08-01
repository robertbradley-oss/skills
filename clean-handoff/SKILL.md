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

1. Call `list_projects` once and select the saved project whose local path matches the current workspace. Ask one concise question only if there is no unique match.
2. Call `create_thread` once with the short handoff as its prompt. Follow the tool's environment rules and do not wait for the new task to run.
3. Report whether creation succeeded. Do not retry automatically or create local handoff files.

## Portable handoff

Return the short handoff in one copyable Markdown block. Do not call task tools or write files.
