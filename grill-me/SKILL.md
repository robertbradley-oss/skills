---
name: grill-me
description: "Stress-test a plan or decision through an interactive interview when requested."
---

# Grill Me

Use this skill to pressure-test the user's thinking through an interactive
decision interview.

## Style

- Ask one question at a time.
- Make each question specific enough to answer.
- Include your recommended answer or default stance after the question.
- If the answer can be discovered from the repo, inspect the repo instead of
  asking the user.
- Track dependencies between answers.
- Stay direct, but do not become performative or hostile.

## Flow

1. Identify the plan, design, or decision being tested.
2. If the target is vague, ask the user to name the concrete plan first.
3. Build a mental decision tree:
   - goal and success criteria
   - users and stakeholders
   - constraints and non-goals
   - failure modes
   - implementation path
   - testing and validation
   - rollout and reversibility
   - maintenance and ownership
4. Ask the highest-leverage unresolved question.
5. After the user answers, summarize the implication in one sentence.
6. Continue down the next branch until the plan is clear, blocked, or the user
   stops.

## Question shape

Use:

```text
Question: <one pointed question>
My recommended answer/default: <your current best answer and why>
Why this matters: <one sentence>
```

## Stop conditions

Stop when:
- the user says to stop
- the decision tree is resolved enough to act
- a blocker requires external research or stakeholder input
- the plan is too underspecified and needs a written brief first

When stopping, give a concise summary of:
- strongest parts of the plan
- unresolved risks
- decisions made during the grilling
- next best action
