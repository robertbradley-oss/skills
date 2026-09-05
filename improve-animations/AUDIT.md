# Motion review reference

Apply only the sections relevant to the interaction. Values are starting points, not pass/fail thresholds.

## Purpose and frequency
Use feedback, state explanation, continuity, or deliberate atmosphere. Keep repeated actions responsive and avoid delaying input. Keyboard-driven interactions can use subtle motion when it helps orientation; no motion is also valid.

## Timing and easing
Try roughly 100–200 ms for small feedback, 150–250 ms for menus, and 200–500 ms for larger surfaces, then tune to distance, frequency, and context. Use existing project tokens. Ease-out often suits entrances; ease-in-out suits on-screen movement. Judge exits and other curves by the actual interaction rather than banning a keyword.

## Continuity and interruption
Anchor trigger-related surfaces where appropriate. Pure fades and centered dialogs can be intentional. Rapid retriggering should not jump, queue stale animations, or lose state. Use transitions, springs, CSS, or WAAPI according to the required behavior; test interruption rather than judging syntax alone.

## Performance
Prefer transform and opacity when they serve the interaction. Profile layout animation and blur under realistic load before assigning severity. Avoid unbounded `transition: all` when it animates unintended properties. Library transform shorthand alone is not evidence of a performance problem.

## Accessibility and input
Respect reduced-motion preferences using static feedback or gentle alternatives that retain meaning. Preserve focus and keyboard operation. Gate hover-only motion to suitable devices. Check touch cancellation and gesture behavior where applicable.

## Evidence
Record the location, trigger, observed effect, user impact, and tested conditions. Preserve deliberate product choices unless evidence shows a problem. Do not invent missed opportunities, rejected candidates, or findings to fill a quota.
