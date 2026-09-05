# Component Motion Patterns

## Pressable controls

Use subtle press feedback without changing layout:

```css
.button {
  transition: transform 140ms var(--ease-out-ui);
}

.button:active {
  transform: scale(0.97);
}
```

Keep the scale between roughly 0.95 and 0.99 and test text and icon legibility.

## Entrances

Avoid `scale(0)`. Start close to the final size and combine with opacity:

```css
.entering {
  opacity: 0;
  transform: scale(0.96);
}
```

Use `@starting-style` when the project's browser support allows it:

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 200ms ease-out, transform 200ms ease-out;

  @starting-style {
    opacity: 0;
    transform: translateY(100%);
  }
}
```

## Popovers, menus, and tooltips

Anchor motion to the trigger with the component library's transform-origin variable. Keep modals centered because they are not spatially attached to one trigger.

```css
.popover {
  transform-origin: var(--radix-popover-content-transform-origin);
  transition: opacity 150ms ease-out, transform 150ms ease-out;
}
```

Delay the first tooltip enough to avoid accidental activation. Once a tooltip group is active, show adjacent tooltips immediately and skip their entrance animation.

## Transitions and interruption

Prefer transitions for rapidly retargeted UI because they continue from the current computed state. Use keyframes for predetermined sequences that should play as authored. Verify quick reversal instead of assuming either mechanism is always interruptible.

## Blur and crossfades

When two distinct states visibly overlap during a crossfade, a small blur can soften the seam. Keep it subtle and measure on Safari and lower-end devices because filters can be expensive.

```css
.content {
  transition: filter 180ms ease, opacity 180ms ease;
}

.content[data-transitioning="true"] {
  filter: blur(2px);
  opacity: 0.7;
}
```

## Transforms

- Percentage translation is relative to the element's own size, making `translateY(100%)` useful for drawers and toasts.
- `scale()` also scales children; verify icon strokes and text rendering.
- Set `transform-origin` to the spatial source of an anchored interaction.
- Use 3D transforms only when depth communicates something or materially improves the experience.

## Clip-path

Use `clip-path: inset()` for reveals, comparisons, progress fills, and hold interactions without adding wrapper elements.

```css
.overlay {
  clip-path: inset(0 100% 0 0);
  transition: clip-path 180ms ease-out;
}

.control:active .overlay {
  clip-path: inset(0 0 0 0);
  transition: clip-path 2s linear;
}
```

For deliberate hold actions, make the hold slow and the release fast. Preserve an alternative for keyboard and assistive-technology users.

## Component craft

- Ship strong defaults before adding many options.
- Keep setup friction low and naming clear.
- Handle pauses, interruptions, hidden tabs, pointer capture, and stacked hit areas invisibly.
- Match motion personality to the component: crisp for dense tools, softer for expressive consumer surfaces.
- Review the interaction again with fresh eyes after the first implementation pass.
