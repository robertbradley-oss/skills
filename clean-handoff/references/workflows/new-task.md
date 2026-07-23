# Direct Handoff

Use this workflow only after the user explicitly requests a new Codex task.

1. Inspect the current workspace and read the live root `GAMEPLAN.md`. Gather only the objective, completed work, remaining work, important decisions, repository state, validation state, risks, and immediate next action.
2. List saved Codex projects and confirm that task creation is available.
3. Call `node scripts/clean-handoff.mjs prepare --project-root <root>` once with `mode: "direct"`, the saved-project list, and the compact context. Stop unless the result reports one exact match.
4. Use only the returned `handoff_text` as the destination prompt. It is context only and carries no approval.
5. Invoke `create_thread` exactly once for the saved project at the returned match index. Do not retry automatically.
6. Report the direct tool result honestly. A queued, failed, or unknown result is not a created task; do not create local recovery state.

The destination must inspect its live repository and live canonical `GAMEPLAN.md` before acting. If identity or live state is uncertain, stop for one clear confirmation.
