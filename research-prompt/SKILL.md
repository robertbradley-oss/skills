---
name: research-prompt
description: "Write a research brief for another researcher or research agent."
---

# Research Prompt

Use this skill to turn a vague research need into one self-contained assignment a
researcher can run without follow-up questions.

## Deliverable

By default, produce one tight paragraph. If the user asks for a structured brief,
use short sections instead.

## Rules

- Prompt the job, not just the topic.
- Assume the researcher has zero prior context.
- Start with the project/product/context in plain English.
- State the one question the research must answer and the decision it informs.
- Include all known constraints: timeframe, geography, source type, excluded
  topics, ranking criteria, audience, and end use.
- Include 3-6 numbered sub-questions inline.
- Prefer primary sources: official docs, filings, papers, changelogs, repos,
  datasets, standards, court/regulatory records, or direct statements.
- Treat forums, social posts, and marketing pages as weak signal unless the task
  is explicitly about sentiment or positioning.
- Require contradiction handling: separate confirmed fact, inference, and
  unresolved uncertainty.
- Require a gap pass before finishing: identify weak claims, then search again
  or label the gap.
- Demand citations for each material claim.
- Require the final output format the researcher should produce.

## Process

1. Pull available context from the conversation and relevant project files.
2. Ask one concise clarifying question only if the end use or core question is
   missing.
3. Identify the single decision the research supports.
4. Draft 3-6 sub-questions that cover the decision.
5. Add include/avoid constraints and source hierarchy.
6. Compress into the requested format.

## One-paragraph template

```text
For a reader with no prior context: <explain the project/product/situation in 1-2 sentences>. Research <topic with identifying facts> to answer one question: <question> - for <decision/end use>. Find: (1) <sub-question>; (2) <sub-question>; (3) <sub-question>; (4) <optional sub-question>. Include <constraints>; avoid <excluded sources/topics>. Prefer primary sources; treat forums/social/marketing as weak signal unless directly relevant. If sources conflict, separate confirmed facts from inference and unresolved uncertainty. Corroborate material claims where possible, label single-source claims, and do a final gap pass before finishing. For each finding, provide the source link, the specific claim it supports, confidence level, and why it matters. Output the results as <requested format>.
```
