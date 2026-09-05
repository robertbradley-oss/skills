---
name: brain-to-docs
description: "Interview the user to capture project vision and decisions in maintained documentation."
---


# brain-to-docs

Use this skill to turn the user's implicit project knowledge into clear project
documentation through repeated question -> answer -> doc update cycles.

## Core loop

1. Inspect existing docs before asking anything.
   - Read `README.md` if present.
   - Inspect the existing documentation index and read only files relevant to the interview topic.
   - Use fast file discovery such as `rg --files` before choosing files.
2. Ask a small set of useful questions, using context to avoid questions already answered.
   - Honor the user's preferred interview format and adapt the question count to the topic.
   - Mix angles: product, audience, constraints, taste, workflow, architecture,
     risks, non-goals, naming, business model, launch path, maintenance.
   - If the user gives a focus area, make the questions diverse within that area.
3. After each user answer, immediately update docs.
   - Combine closely related answers into a coherent update when that improves clarity.
   - Preserve existing docs and style where possible.
   - Create missing directories/files only when they are the right home for the
     information.
4. Briefly report what changed, then ask the next useful question set.
5. Repeat until the user says they are done, pauses, or redirects.

## Artifact rules

- `README.md`: project vision, purpose, audience, current shape, high-level usage,
  and durable project narrative.
- `docs/adr/NNNN-slug.md`: confirmed decisions with meaningful tradeoffs or
  architectural/product consequences.
- `docs/project-context.md`: preferences, taste, working assumptions, glossary,
  open questions, constraints, and useful background that does not belong in
  README or an ADR.

If the repo already uses a different documentation structure, follow it instead
of forcing these paths.

## ADR format

Use ADRs only for decisions the user has actually confirmed. Do not invent
decisions from vague preferences.

```markdown
# NNNN Short Decision Title

Status: Accepted

## Context

What made the decision necessary.

## Decision

The decision in plain language.

## Consequences

What this enables, what it rules out, and known tradeoffs.
```

Number ADRs by scanning existing ADR filenames and choosing the next four-digit
number. If no ADRs exist, start at `0001-...`.

## Question quality

Good questions should uncover decisions that future contributors or agents would
otherwise have to rediscover.

Prefer questions like:
- "What should this project refuse to become, even if users ask for it?"
- "What taste or quality bar should future UI/code/docs changes preserve?"
- "Which decision feels obvious to you but would surprise a new contributor?"
- "What tradeoff have you already made that should not be reopened casually?"
- "What would make this project feel like it has lost the plot?"

Avoid five questions that all live in the same lane, such as only tech stack or
only monetization.

## Writing rules

- Keep chat responses concise and plain.
- Use short sentences.
- Write docs in calm, direct English.
- Do not challenge the user's thinking unless asked, or unless there is a severe
  factual, safety, security, legal, or architectural risk.
- Do not overwrite unrelated documentation.
- Do not create ADRs for routine implementation details.
- If an answer is ambiguous, write the stable part and capture uncertainty under
  open questions rather than pretending it is resolved.

## Update protocol

After each answer:

1. Decide the target artifact: README, ADR, project context, or existing doc.
2. Make the smallest useful edit.
3. Re-read the edited section or file.
4. Verify the documented claim still matches the user's answer.
5. Tell the user the file changed in one sentence.
6. Ask the next question or question set.

If no project files are available, ask where the docs should live before creating
anything.
