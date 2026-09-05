---
name: delegating-to-agents
description: "Plan and coordinate authorized subagent work with distinct ownership."
---

# Delegating to Agents

Use this skill to decide whether to delegate work and to write clean, bounded
subagent prompts when delegation is appropriate.

## First principle

Do not delegate by reflex. Delegate only when it materially improves the work and
does not make coordination harder than doing the task locally.

In this Codex environment, only spawn subagents when the user explicitly asks for
subagents, delegation, parallel agent work, or similar. A request for depth,
thoroughness, or investigation is not enough by itself.

## Delegation decision

Before delegating, make a short local plan:

1. Identify the immediate critical-path task.
2. Identify sidecar tasks that can run independently.
3. Decide what to do locally right now.
4. Delegate only independent work that can proceed without blocking the next
   local action.

Keep work local when:
- The next step depends on the answer.
- The task is tightly coupled to edits you are about to make.
- The scope is vague or likely to change.
- The subagent would need sensitive credentials or risky production access.
- The coordination cost is higher than the work itself.

Delegate when:
- The user explicitly asked for agents/subagents/parallel work.
- The task can be described with a clear output.
- The subagent can work on a disjoint file set or a bounded research question.
- The result can be reviewed and integrated quickly.

## Good delegated tasks

Good delegation prompts are concrete, bounded, and self-contained.

Use subagents for:
- Independent codebase questions with exact files or concepts to inspect.
- Bounded implementation slices with disjoint file ownership.
- Parallel test or verification passes while local work continues elsewhere.
- Independent artifact review, such as checking a migration plan or generated
  skill for edge cases.

Avoid delegating:
- Broad "understand the repo" tasks.
- The same question multiple agents are already answering.
- Urgent blocking work.
- Work that requires live secrets, destructive operations, or unclear approval.

## Prompt template

Use this structure for delegated work:

```markdown
Task: <one concrete task>
Context: <minimum necessary background>
Ownership: <files/modules/questions this agent owns>
Do not touch: <files/modules/scope exclusions>
Expected output: <exact final answer or changed files>
Validation: <commands/checks to run, if relevant>
Coordination: You are not alone in the codebase. Do not revert or overwrite work
from others. If you encounter unrelated changes, work with them or report the
conflict.
```

For code-editing workers, always specify file or module ownership. Prefer
disjoint write sets across agents.

For explorer/research agents, ask a specific question and request file/line
references or evidence. Do not ask for a generic tour.

## While agents run

- Continue meaningful local work that does not duplicate the delegated task.
- Do not keep polling if the result is not yet needed.
- Wait only when the next critical-path action depends on the result.
- Do not redo the delegated task locally; integrate or verify the result when it
  returns.

## Integrating results

When a subagent returns:

1. Read the final answer and any changed files.
2. Check whether the output matches the delegated scope.
3. Review diffs before accepting edits.
4. Run relevant validation if code changed.
5. Merge the useful parts into the main work.
6. Close the agent when it is no longer needed.

If a subagent returns an unsafe or off-scope result, do not apply it blindly.
Extract any useful findings, then continue locally or delegate a tighter task if
the user still wants parallel work.

## Anti-patterns

- Delegating the immediate blocker and then waiting idle.
- Giving multiple agents overlapping ownership of the same files.
- Asking a subagent to decide product scope without user context.
- Letting a subagent weaken tests, remove validation, or broaden scope.
- Treating a subagent final answer as verified truth without checking evidence.
- Leaving completed agents open after their result has been integrated.

## Relationship to goals

Use `codex-goal-loop` for long-running autonomous work with a verifiable stop
condition. Use this skill when splitting work across agents or deciding whether
parallelism is worthwhile. The two can combine, but delegation still requires
clear ownership and explicit user intent.
