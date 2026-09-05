---
name: visual-ui-qa
description: "Inspect or verify a running web interface's visual and interaction behavior."
---

# Visual UI QA

Produce evidence-backed interface findings and, when authorized, a verified fix. Treat screenshots as evidence, not decoration.

## Establish the test surface

1. Identify the URL, route, or startup command from the repository and user request.
2. Inspect existing design-system tokens, component conventions, and product vocabulary before judging stylistic consistency.
3. Choose the smallest representative viewport matrix:
   - narrow mobile: about 375 px
   - wide mobile or tablet when the layout changes materially
   - desktop: about 1440 px
   - one boundary width near each observed layout transition
4. Identify states that matter: default, loading, empty, error, populated, selected, expanded, disabled, destructive confirmation, long content, and reduced motion. Test only states reachable safely and relevant to the request.
5. State any important surface or state that cannot be reached. Do not invent evidence.

## Capture a baseline

Use the available browser-control or browser-automation capability. Prefer deterministic viewport sizes and stable seeded data. Wait for fonts, images, animation, and network-dependent content to settle before capture.

For each tested surface:

1. Capture the full page or relevant region.
2. Exercise primary interaction paths with keyboard as well as pointer when interaction is in scope.
3. Inspect the browser console for errors that affect presentation or behavior.
4. Record the route, viewport, state, reproduction steps, and evidence for each defect.

Read [references/inspection-checklist.md](references/inspection-checklist.md) for the detailed inspection pass. Do not mechanically report every checklist item; report only defects supported by evidence.

## Diagnose before editing

Trace each visible defect to the smallest plausible cause. Distinguish among:

- component-local styling
- intrinsic sizing or content wrapping
- container or grid behavior
- typography or asset loading
- state logic or missing state coverage
- design-token inconsistency
- browser/runtime failure

Prefer intrinsic layout fixes (`min-width: 0`, flexible tracks, wrapping, clamping, containment, correct source order) before adding breakpoints. Prefer existing tokens and primitives before creating new values or components.

Rank findings:

- **P0 — blocking:** prevents task completion or makes essential content unusable
- **P1 — major:** broken layout, inaccessible primary interaction, severe hierarchy or state failure
- **P2 — moderate:** noticeable inconsistency, awkward responsive behavior, or incomplete secondary state
- **P3 — polish:** small alignment, typography, or motion refinement

Include the exact location, conditions, user impact, evidence, and recommended correction. Avoid taste-only criticism unless the project has an explicit visual direction that the UI violates.

## Apply fixes only when authorized

If the user asked only for an audit, stop after findings. If the user asked to build, fix, or polish:

1. Make the smallest coherent change that addresses the cause.
2. Preserve the project design system and unrelated user changes.
3. Cover content extremes and intermediate widths, not only the captured screenshot.
4. Add or update automated coverage when the defect is behaviorally important or likely to regress.

## Re-verify

Re-run the exact failing viewport, state, and interaction. Then check adjacent widths and affected shared components. Compare before and after evidence and confirm:

- the original defect is gone
- no new overflow, clipping, wrapping, focus, or state regression appeared
- console behavior did not worsen
- relevant tests and checks pass

Never claim a visual fix is verified from code inspection alone. If a runnable interface is unavailable, label the result as a static review and give the command or missing condition needed for visual verification.

## Report the outcome

Lead with the overall result. For an audit, list findings in priority order and include tested surfaces plus untested limitations. For an implementation, summarize what changed, cite the affected files, and report the verification matrix and any remaining risks. Keep screenshots or paths attached to the finding they support.
