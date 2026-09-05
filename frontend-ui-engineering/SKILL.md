---
name: frontend-ui-engineering
description: "Implement web UI in the project's component and design conventions."
---


# Frontend implementation

Implement the requested UI using the project's existing component, styling, state, and accessibility conventions. Inspect the affected flow and nearby code; avoid introducing a parallel design system or arbitrary file-size rules.

- Preserve the established visual direction. Use `frontend-skill` only when substantial art direction is unresolved.
- Use the simplest state ownership that serves the flow. Preserve loading, error, empty, and recovery behavior where applicable.
- Prefer native controls and established accessible primitives. Check keyboard operation, accessible names, focus entry/restoration, and modal behavior for the touched interaction.
- Use semantic tokens and content-driven layout; check realistic content lengths, a narrow viewport, and relevant layout boundaries.
- Choose animation mechanisms already supported by the project. Use `emil-design-eng` for a focused motion problem and `accessibility` for a dedicated audit.
- Verify the affected user journey in the browser when available, then run the relevant project checks. Code inspection alone does not verify visual behavior.

Complete the requested implementation and fix regressions caused by it. Report observed results and any untested surface. Do not add new test infrastructure, full viewport matrices, or broad audits for an isolated low-risk styling change.
