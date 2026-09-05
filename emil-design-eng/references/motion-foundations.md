# Motion Foundations

## Purpose and frequency

Every animation should serve feedback, spatial continuity, explanation, transition smoothing, or deliberate delight.

| Frequency | Default treatment |
| --- | --- |
| Constant or keyboard-driven | Instant or extremely short; retain motion only when it preserves orientation |
| Frequent navigation or hover | Subtle and short |
| Occasional modal, drawer, popover, or toast | Standard UI motion |
| Rare onboarding, success, or celebration | More expressive motion is acceptable |

Do not apply a blanket ban to keyboard-triggered motion. The important constraint is that animation must not make a practiced action feel delayed.

## Easing

- Entrances and direct responses: ease-out.
- Movement or morphing already on screen: ease-in-out.
- Hover and color changes: ease or a restrained project curve.
- Constant-rate motion: linear.
- Avoid ease-in for ordinary UI entrances because it delays visible response.

Useful starting curves:

```css
--ease-out-ui: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out-ui: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

Reuse the project's established curves when they exist. Tune with [easing.dev](https://easing.dev/) or [easings.co](https://easings.co/) instead of inventing many near-duplicates.

## Timing

| Interaction | Starting range |
| --- | --- |
| Press feedback | 100-160ms |
| Tooltip or small popover | 125-200ms |
| Dropdown or select | 150-250ms |
| Modal or drawer | 200-400ms |
| Explanatory or marketing sequence | Longer only when comprehension benefits |

Keep routine UI under roughly 300ms when possible. Let distance, size, and complexity justify exceptions. Make exits faster than entrances when the system is clearing the user's path.

## Springs

Use springs for interruptible gestures, drag momentum, reversible interactions, and decorative elements that should retain velocity.

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

Or use physical parameters when the library and interaction benefit from them:

```js
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

Keep bounce subtle, usually between 0.1 and 0.3. Avoid bounce in restrained product UI unless it matches the product's personality.

## Stagger

Use stagger only when a group should be perceived as a sequence. Keep delays around 30-80ms and never block interaction while the sequence completes.

```css
.item {
  opacity: 0;
  transform: translateY(8px);
  animation: enter 240ms var(--ease-out-ui) forwards;
  animation-delay: calc(var(--index) * 50ms);
}
```

## Perceived responsiveness

Immediate visible response matters more than decorative duration. A fast initial change, prompt press state, and skipped tooltip delay after the first tooltip can make an interface feel faster without disguising real latency. Never use motion to conceal a stalled or failed operation.
