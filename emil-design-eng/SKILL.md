---
name: emil-design-eng
description: "Implement or refine a specific web animation or interaction detail."
---

# Emil Design Engineering

Apply motion only when it improves feedback, spatial understanding, continuity, perceived responsiveness, or deliberate delight. Preserve the product's existing design language and validate the interaction in its real context.

This skill is adapted from [Emil Kowalski's design-engineering work](https://animations.dev/) and the public `emilkowalski/skills` collection.

## Routing boundary

- Use this skill to implement or refine a concrete motion or interaction detail.
- Use `frontend-skill` to establish composition, hierarchy, imagery, and aesthetic direction.
- Use `frontend-ui-engineering` for component architecture, state, responsiveness, accessibility, and production verification across the broader interface.
- Use `review-animations` for a verdict on existing motion code and `improve-animations` for a read-only motion roadmap.
- Use `find-animation-opportunities` when the question is where motion might help, without implementation.

## Workflow

1. Read repository instructions and inspect the component, its trigger, surrounding states, and existing motion conventions.
2. State the interaction's purpose internally: feedback, spatial continuity, state explanation, transition smoothing, or delight.
3. Estimate frequency and initiation method. Keep repeated and keyboard-driven actions nearly instant unless motion materially preserves orientation.
4. Select the smallest suitable mechanism: CSS transition, CSS animation, Web Animations API, or the project's existing motion library.
5. Load only the relevant reference below and implement one coherent interaction slice.
6. Add reduced-motion behavior and gate hover-only effects for devices that actually support hover.
7. Verify rapid retriggering, interruption, enter/exit symmetry, focus behavior, touch behavior, and realistic performance.
8. Run the project's checks and browser verification appropriate to the touched surface. Report what changed and what was verified.

## Reference routing

| Need | Read |
| --- | --- |
| Purpose, frequency, easing, timing, springs, and stagger | [references/motion-foundations.md](references/motion-foundations.md) |
| Buttons, popovers, tooltips, toasts, transforms, blur, and clip-path | [references/component-patterns.md](references/component-patterns.md) |
| Gestures, performance, reduced motion, touch, and debugging | [references/gestures-performance-accessibility.md](references/gestures-performance-accessibility.md) |

## Core defaults

- Prefer no motion to motion without a clear job.
- Prefer fast feedback and interruptible transitions for frequently repeated UI.
- Use ease-out for entrances, ease-in-out for on-screen movement, and linear only for constant-rate motion.
- Prefer transform and opacity, but allow measured layout animation when it is essential to the interaction.
- Avoid `transition: all`; name the properties being animated.
- Do not enter from `scale(0)`; begin near the final size and pair scale with opacity when appropriate.
- Anchor popovers and menus to their trigger; keep unanchored modals centered.
- Make exits at least as fast as entrances unless the interaction intentionally requires confirmation.
- Treat duration tables and curves as starting points, then tune in context.

## Verification checklist

- The interaction has a clear purpose and does not delay the user's next action.
- Rapid repeated input does not restart awkwardly, queue stale animation, or lose state.
- Focus remains visible and predictable throughout the transition.
- Reduced-motion users retain state feedback without unnecessary movement.
- Hover behavior is not accidentally triggered as a persistent state on touch devices.
- The animation remains smooth under realistic loading and device conditions.
- Build, lint, tests, and browser checks relevant to the change pass.

Do not force a review table or generic motion commentary onto implementation work. Explain only the decisions that help the user understand the result.
