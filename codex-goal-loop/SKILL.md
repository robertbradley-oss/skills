---
name: codex-goal-loop
description: "Draft and manage explicitly requested Codex goal runs and their completion conditions."
---


# Codex goal runs

Use for explicitly requested autonomous goal runs or goal prompts. Drafting a prompt does not authorize creating a goal.

Define one verifiable outcome, relevant constraints, validation evidence, and a completion or escalation condition. Point to documents only when they supply necessary context. Use `define-goal` if shaping the objective is the primary task.

Follow the live goal-tool contract for creation and status changes. In particular, complete only when the objective is achieved; mark blocked only after the tool's required repeated-blocker threshold. Do not infer goals, budgets, or authority for external actions from a long-running task.

Work until the scoped outcome and appropriate verification are complete. Fix failures caused by the work and rerun affected checks; don't rerun a whole suite after every minor edit. Preserve tests and meaningful acceptance criteria. Ask when a missing product decision or unauthorized external action blocks further useful work, while continuing independent in-scope tasks.

For a goal prompt, include the outcome, scope, essential constraints, evidence of completion, and stopping boundary. Match the user's format; do not force checkpoints, ADRs, read-all-docs instructions, or new artifacts.
