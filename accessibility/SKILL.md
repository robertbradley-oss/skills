---
name: accessibility
description: "Audit or fix web accessibility when accessibility is the primary task."
---

# Accessibility

Treat accessibility as observable product behavior, not a checklist inferred from source code. Prefer native HTML, preserve existing project conventions, and distinguish automated coverage from manual verification.

## Scope boundary

- Use this skill for a dedicated accessibility audit, remediation pass, or accessibility-specific implementation question.
- Use `frontend-ui-engineering` for routine component construction where accessibility is one engineering requirement among several.
- Pair with `visual-ui-qa` when a running interface needs browser evidence across viewports and interaction states.
- Do not claim legal compliance or complete WCAG conformance from automated checks alone.

## Workflow

1. Read repository instructions and identify the requested pages, components, states, and conformance target.
2. Determine authority:
   - For review, diagnosis, or reporting, inspect and report without editing.
   - For implementation requests, make the smallest fixes that address verified problems.
3. Inspect semantic structure, keyboard behavior, focus, accessible names, forms, status messages, contrast, reflow, target size, media alternatives, motion, and authentication where relevant.
4. Run the project's existing accessibility checks. Add or install tooling only when it is within scope.
5. Manually exercise the affected flows. Automated tools cannot prove keyboard order, usable focus, screen-reader meaning, cognitive clarity, or complete conformance.
6. Report each finding with evidence: location, behavior, affected users, WCAG criterion when known, severity, and a concrete remedy.
7. When fixes are authorized, implement them, rerun the affected checks, and repeat the manual interaction.
8. End with passed, failed, skipped, and unavailable coverage. Preserve uncertainty.

## Reference routing

Load only the detail needed for the task:

| Need | Read |
| --- | --- |
| WCAG 2.2 criteria, levels, and changed requirements | [references/WCAG.md](references/WCAG.md) |
| Modal focus, skip links, errors, labels, dragging alternatives, tabs, live regions, and screen-reader commands | [references/A11Y-PATTERNS.md](references/A11Y-PATTERNS.md) |

## Baseline checks

### Structure and names

- Use one descriptive page title and a logical heading hierarchy.
- Give images appropriate alternatives; use empty `alt` for decorative images.
- Give every control an accessible name that agrees with its visible label.
- Prefer native buttons, links, inputs, dialogs, lists, tables, and landmarks before adding ARIA.
- Set page and inline language where it changes.

### Keyboard and focus

- Make every action available without a pointer.
- Preserve a logical focus order and visible focus indicator.
- Prevent keyboard traps and restore focus after dismissing transient UI.
- Keep focused elements visible around sticky headers, footers, and overlays.
- Provide skip navigation and non-drag alternatives where applicable.

### Forms and dynamic state

- Associate labels and instructions programmatically with inputs.
- Identify errors in text, set the relevant state, and focus or summarize errors appropriately.
- Announce meaningful asynchronous status changes without moving focus unnecessarily.
- Support autofill, paste, password managers, and accessible authentication alternatives.

### Visual and motion

- Meet contrast requirements for text, controls, graphics, and focus indicators.
- Do not use color as the only signal.
- Verify reflow and usability at 200% zoom and narrow widths.
- Meet WCAG 2.2 target-size requirements or document an applicable exception.
- Respect `prefers-reduced-motion`; remove nonessential movement while retaining useful state feedback.

## Evidence and severity

Use severity to communicate user impact, not stylistic preference:

- **Critical:** blocks a core flow for keyboard or assistive-technology users, creates a trap, or makes essential content unavailable.
- **Serious:** makes an important flow difficult or ambiguous, including missing labels, unusable focus, or insufficient contrast.
- **Moderate:** degrades clarity or efficiency without blocking the flow.

For every finding include:

```text
Location:
Observed behavior:
Affected users:
Criterion:
Severity:
Recommended change:
Verification:
```

## Verification

Use the repository's own commands first. Representative checks may include:

```bash
npx lighthouse <url> --only-categories=accessibility
npx axe <url>
```

Also verify, as relevant:

- keyboard-only completion with Tab, Shift+Tab, Enter, Space, Escape, and arrow keys
- focus entry, containment, restoration, and visibility
- accessible names and reading order with a screen reader
- 200% zoom, narrow-width reflow, high contrast, and reduced motion
- loading, empty, error, success, disabled, expanded, and modal states

Never report an untested surface as passed.
