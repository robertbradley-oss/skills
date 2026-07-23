# Portable Handoff

Portable Handoff is output-only and works for Git and non-Git workspaces.

1. Inspect the current workspace and read the live root `GAMEPLAN.md` when safely available.
2. Gather only the objective, completed work, remaining work, important decisions, repository state, validation state, risks, and immediate next action.
3. Call `node scripts/clean-handoff.mjs prepare --project-root <root>` once with `mode: "portable"`, `projects: null`, and the compact context.
4. Return only the bounded redacted `handoff_text` in one copyable Markdown block.
5. State that the receiver must inspect its own workspace and live canonical `GAMEPLAN.md` before acting and that the text carries no approval.

Do not call a task tool and do not create a file, checkpoint, packet, receipt, cache, sideband record, or Git change.
