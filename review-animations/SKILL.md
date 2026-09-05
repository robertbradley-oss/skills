---
name: review-animations
description: "Review a selected motion change for observable usability and performance issues."
---


# Review motion changes

Review the selected motion code or diff for observable usability, accessibility, and performance problems. Do not default to finding faults or treat stylistic preferences as defects.

Consider purpose and frequency, response latency, origin and continuity, interruption, reduced motion, input devices, and consistency with the product. Frequent actions should stay responsive; keyboard initiation alone is not a defect. Easing, duration, pure fades, and layout animation require context rather than blanket bans.

Use [STANDARDS.md](STANDARDS.md) for timing examples and review details only when needed. Project conventions and measured interaction behavior govern the choice. Verify rapid retriggering and realistic device/load behavior when relevant.

Report confirmed findings with file/line, conditions, user impact, evidence, and a remedy. Omit empty tables and invented findings. Distinguish static concerns from reproduced defects. Give a verdict only when requested or useful, and state verification gaps.

For a review-only task, stop after findings. If fixes are requested, apply the authorized changes using the project's motion conventions and recheck the affected interaction.
