# Finish the task

Use this workflow to leave the requested implementation and its affected area complete, understandable, organized, and verified. This is an editing workflow coordinated by the agent, not a new script mode or a relaxation of the removal contracts in [OPERATIONS.md](OPERATIONS.md).

## Establish the affected area

Recover the intended outcome and existing authorization from the conversation and applicable project instructions. Inspect current changes and the code, tests, configuration, and documentation needed to understand them. A finishing request authorizes relevant reversible edits; an audit-only request does not.

If invoked before implementation starts, capture the initial branch, HEAD, status, and relevant existing diff in the working context. Do not create a tracking file by default. When invoked afterward, use available conversation and Git evidence without inventing a starting baseline or attributing every changed or untracked file to this task. Do not guess a `--git-base` for cleanup scripts.

Keep unrelated or uncertain existing work intact. Expand beyond touched files only to complete the requested behavior, update affected references, or validate dependencies. A repository-wide restructuring or unrelated cleanup requires its own scope. If the task cannot be identified, continue read-only inspection and ask for the missing task context before editing.

## Complete and simplify the implementation

Compare the actual behavior with the requested outcome. Resolve unfinished integration, temporary stubs, task-related debug instrumentation, and obsolete paths introduced or superseded by the work.

Review the affected code in context for unnecessary branching, duplicate logic, unused additions, misleading names, and abstractions that add complexity without serving the task. Make concrete improvements when behavior and callers are understood. Preserve public contracts and intentional behavior unless the task authorizes changing them. Do not broaden this into a dependency upgrade, architectural rewrite, or cosmetic sweep.

The tracked-code analyzer in OPERATIONS.md is optional evidence, not a prerequisite or a proof of dead code. Before removing a declaration, check callers, exports, framework conventions, configuration, dynamic access, and relevant tests. Keep uncertain declarations and explain material uncertainty. A `DC-...` finding alone never authorizes removal.

Use normal editing tools for justified changes within source files, including removal of obsolete code. Whole-file or whole-directory disposal is governed by the existing path cleanup contract; do not turn a file deletion into an emptying edit to bypass it. If those scripts cannot accept the target, preserve it and report the limitation rather than manually deleting it.

## Organize the affected files

Place new or touched files in established project locations when their role and destination are clear. Update imports, package exports, build and test configuration, documentation links, and other affected references in the same change. Preserve file contents during moves and check for collisions and case-sensitive path issues.

The file-organization analyzer is optional and covers only loose root files. Its `FO-...` decisions are leads for this editing workflow, not Apply authorization. Review the actual role and references before moving a file. Resolve routine placement choices from project conventions; keep the current location when evidence is ambiguous.

A task-finishing request supplies the edit request required by the audit contract for relevant code changes and moves. Do not ask for a second approval for those already authorized reversible edits. Do not move unrelated files or replace occupied destinations. File moves must preserve content and update references; use the removal workflow for disposal.

## Remove verified leftovers

Identify task-related temporary files, generated output, abandoned artifacts, and eligible Git hygiene targets using current evidence. Prefer exact inspection of known targets; use Triage when a broader inventory is necessary. A broad scan does not expand the task's mutation scope.

Follow the applicable Inspect, reference-review, and Apply sections of OPERATIONS.md without modification. Preserve exact candidate IDs, fingerprints, recovery behavior, validation, and the separation between path and Git approval. Untracked status and generated-looking names do not prove disposability. Never promote a script review or preserve result.

Complete the independent code edits, file moves, and their validation before presenting removals for approval, so the user sees a concrete result. Inspect removal candidates against that resulting state. Reuse existing approval for the same current exact candidates; otherwise request only the exact removal approval still needed. Pending removal approval does not block unrelated authorized finishing work, and elapsed time does not supply approval.

## Validate and close

Run checks appropriate to the changed behavior and project requirements. Check the final diff for accidental behavior changes, unrelated edits, broken references, debug residue, and incomplete work. For moves, verify affected import or build paths. For simplification, use relevant tests, type checks, builds, or direct behavior checks; add tests when they protect meaningful behavior rather than mirror the implementation.

Where pre-existing failures are suspected, establish a baseline without resetting or discarding user work. Fix task-related failures and state any unresolved validation limits accurately. Apply's before/after validation and stale-evidence checks still run when approved removals are performed.

Stop when the requested outcome is met, affected files are coherent, justified cleanup is handled or explicitly pending, and relevant checks pass or their limitations are reported. Do not keep expanding the change because another improvement is possible.

Report the completed behavior, useful simplifications and organization changes, removal outcomes, validation, and any remaining blocker or exact approval request. Distinguish implementation completion from cleanup still awaiting approval. Do not label the entire repository clean based on a task-scoped review.
