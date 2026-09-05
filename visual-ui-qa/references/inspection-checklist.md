# Inspection checklist

Use this as a disciplined scan, not as a report template.

## Geometry and responsiveness

- Check horizontal overflow, accidental page scroll, clipped content, overlapping layers, and obscured controls.
- Check intrinsic sizing, grid/flex minimums, wrapping, truncation, aspect ratios, sticky regions, safe areas, and viewport-height assumptions.
- Test intermediate widths and content extremes; a layout that works only at named breakpoints is not verified.
- Check that reading order and action priority remain sensible when columns collapse.

## Hierarchy and visual system

- Check that the primary task and action are visually unambiguous.
- Check spacing rhythm, alignment, density, typography hierarchy, line length, and scan paths.
- Check colors, radii, borders, shadows, icon treatment, and spacing against existing tokens and components.
- Flag generic repetition only when it weakens information priority or conflicts with the product direction.

## Content and states

- Check realistic short, long, missing, malformed, and localized-looking content.
- Check loading, empty, error, partial, stale, disabled, success, and destructive states when relevant.
- Check that errors explain what happened and how to recover without destroying entered work.
- Check that optimistic or asynchronous transitions do not jump, flash, duplicate, or lose context.

## Interaction and visible accessibility

- Check keyboard reachability, logical focus order, visible focus, escape behavior, and focus restoration.
- Check hover, focus, active, selected, disabled, drag, and touch feedback.
- Check labels, accessible names, semantic heading order, dialog behavior, status announcements, and error association using inspection tools when available.
- Check contrast, non-color cues, zoom/reflow, touch-target size, and reduced-motion behavior.
- Treat automated accessibility results as leads; verify important failures manually.

## Motion and perceived quality

- Check whether motion explains hierarchy or state change rather than merely decorating it.
- Check interruption, repeated triggers, exit behavior, transform origins, layout shift, and reduced-motion alternatives.
- Check font and image loading, skeleton stability, cumulative layout shift, and interaction latency visible to the user.

## Evidence standard

For every reported defect, retain:

- route or component
- viewport dimensions
- UI state and data conditions
- reproduction steps
- screenshot, recording, DOM observation, or console evidence
- user impact
- likely cause and confidence

Do not report a pass for an untested state. Do not call a subjective preference a defect without connecting it to usability, consistency, accessibility, or an explicit design direction.
