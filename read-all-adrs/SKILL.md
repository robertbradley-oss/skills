---
name: read-all-adrs
description: "Read every ADR when the user explicitly requests complete decision-history intake."
---


# Read all ADRs

Use only when the user requests complete ADR intake or a review explicitly needs the whole decision history. Ordinary implementation should search relevant accepted decisions instead.

Discover ADR directories such as `docs/adr`, `docs/adrs`, `docs/decisions`, or `adr`. Read the discovered records in order and distinguish accepted, proposed, deprecated, and superseded decisions. If none exist, state that and continue with available context.

Report the number read, active decisions relevant to the task, and material contradictions with file links. Do not apply superseded decisions. Ask only if an unresolved conflict changes the requested work.
