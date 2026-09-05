---
name: clean-handoff
description: "Prepare a concise handoff or create a new task when explicitly requested."
---


# Clean handoff

Use conversation context to prepare a short destination prompt: objective, completed and remaining work, important decisions, relevant files and validation state, and the next action. Omit secrets and raw tool output. Tell the destination to inspect live workspace state before edits.

Do not inspect the whole repository or run tests solely to prepare a handoff. Include a relevant GamePlan when the user is working from it; current user direction controls scope.

## Create a new task

Only create a task when the user explicitly requests one. Discover the saved project and select the unambiguous match. Follow the current `create_thread` contract for environment and starting-state selection, honoring an explicit user request for the saved checkout or an isolated worktree. Do not invent a branch or require a starting branch when the tool permits its default.

Create one task with the concise prompt. Report the returned outcome and do not retry an uncertain creation blindly or wait for the destination to finish.

## Portable handoff

If the user requests copyable context, return one Markdown block. Do not create a task or write a local handoff file unless requested.
