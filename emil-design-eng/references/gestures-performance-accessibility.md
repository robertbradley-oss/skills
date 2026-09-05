# Gestures, Performance, and Accessibility

## Drag and dismissal

Use both distance and velocity when a quick flick should dismiss:

```js
const elapsed = performance.now() - dragStartedAt;
const velocity = Math.abs(distance) / elapsed;

if (Math.abs(distance) >= threshold || velocity > 0.11) {
  dismiss();
}
```

Tune the threshold in the real component. Apply increasing resistance beyond natural bounds instead of an abrupt hard stop. Capture the pointer after drag begins and ignore extra touch points so the interaction does not jump between fingers.

Always provide a non-drag path for the action when WCAG 2.5.7 applies.

## Performance

- Prefer transform and opacity because they are commonly compositor-friendly.
- Treat layout-affecting animation as an explicit tradeoff; keep its scope small and measure it.
- Avoid `transition: all` and large paint-heavy filters.
- Changing an inherited CSS variable can recalculate styles across descendants. For per-frame drag values, update the target transform directly unless profiling supports another approach.
- Do not flag Motion or Framer Motion shorthand properties by syntax alone. Profile dropped frames and main-thread work under realistic load.
- CSS does not automatically mean off-main-thread. Compositing depends on the property, browser, layer state, and surrounding work.
- Use CSS for predictable state transitions, WAAPI for programmatic browser-native control, and the project's motion library for dynamic orchestration when it earns the dependency.

```js
element.animate(
  [
    { transform: 'translateY(100%)', opacity: 0 },
    { transform: 'translateY(0)', opacity: 1 },
  ],
  { duration: 220, easing: 'cubic-bezier(0.23, 1, 0.32, 1)', fill: 'both' },
);
```

## Reduced motion

Reduced motion means removing or minimizing nonessential movement while preserving useful feedback. Prefer opacity, color, and instant state changes when translation, rotation, parallax, zoom, or spring motion would be uncomfortable.

```css
@media (prefers-reduced-motion: reduce) {
  .animated-element {
    transform: none;
    transition-duration: 0.01ms;
  }
}
```

Use the motion library's reduced-motion hook when animation values are produced in JavaScript.

## Hover and touch

Gate hover-only motion:

```css
@media (hover: hover) and (pointer: fine) {
  .item:hover {
    transform: translateY(-2px);
  }
}
```

Verify that tap does not leave a false hover state and that the interaction has a clear focus-visible equivalent.

## Debugging

1. Slow the animation to two to five times its duration.
2. Inspect whether easing, transform origin, opacity, color, and layout changes stay synchronized.
3. Retrigger and reverse it rapidly.
4. Step through frames in browser developer tools.
5. Test under page loading or CPU throttling.
6. Test gestures on physical touch hardware when practical.
7. Confirm reduced motion, focus visibility, and keyboard alternatives.

Treat a smooth desktop recording as partial evidence, not proof of robust interaction behavior.
