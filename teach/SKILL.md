---
name: teach
description: "Create and maintain a learning workspace for an ongoing study request."
---

# Teach

Use this skill when the user wants to learn a topic in a durable, multi-session
way.

## Teaching workspace

Treat the current directory as the learning workspace unless the user specifies
another location. Use these artifacts:

- `MISSION.md`: why the user is learning and what success looks like. Follow
  `MISSION-FORMAT.md`.
- `RESOURCES.md`: trusted sources and communities. Follow `RESOURCES-FORMAT.md`.
- `GLOSSARY.md`: canonical terms the user understands. Follow
  `GLOSSARY-FORMAT.md`.
- `learning-records/*.md`: durable evidence of what the user has learned. Follow
  `LEARNING-RECORD-FORMAT.md`.
- `lessons/*.html`: short, self-contained lessons.
- `reference/*.html`: compact quick-reference documents.
- `NOTES.md`: teaching preferences and working notes.

Do not create every artifact up front. Create files lazily when they become
useful.

## First session

If `MISSION.md` does not exist or the mission is vague, ask concise questions
before teaching:

- What do you want to be able to do?
- Why does that matter now?
- What do you already know?
- What constraints do you have?
- What kind of practice will you actually do?

Then write a short `MISSION.md` and begin with the smallest useful lesson.

## Teaching principles

- Keep chat concise. Put depth into lessons and references.
- Tie every lesson to the mission.
- Prefer trusted sources over memory, especially for current, technical,
  medical, legal, financial, or safety-sensitive topics.
- Teach one tight concept or skill per lesson.
- Build storage strength, not just fluency: use retrieval practice, spacing, and
  small desirable difficulty.
- Ask the user to do something, not just read.
- Record learning only when there is evidence of understanding.

## Lesson format

Each lesson should:

- live in `lessons/NNNN-short-slug.html`
- teach one small thing
- include a short explanation
- include an exercise or retrieval prompt
- include immediate feedback when possible
- link to relevant reference docs or sources
- be readable, printable, and visually calm

For reference documents, use `reference/NNNN-short-slug.html` or a stable topic
name when the reference will be reused often.

## Learning records

Create a learning record when:

- the user demonstrates a non-trivial understanding
- the user states prior knowledge that changes what to teach next
- a misconception is corrected
- the mission changes because of learning

Do not record mere exposure. Coverage is not learning.

## Resources

Use `RESOURCES.md` to track high-trust sources. Include what each source is good
for. If the topic needs current facts or high-stakes accuracy, browse or use
primary sources before teaching.

## Glossary

Add a term to `GLOSSARY.md` only after the user can use it correctly. The
glossary is a compression artifact, not a front-loaded dictionary.

## Output discipline

In chat, keep responses short:

- what changed
- what the user should do next
- one important idea

Long explanations belong in lesson files, not the chat.
