---
name: preferred-ui-libraries
description: "Consult Robert's UI-library preferences when selecting a new component dependency."
---

# Preferred UI Libraries

Consider these libraries first when their specialized interaction matches the product need. Treat them as preferred candidates, not automatic dependencies.

Before installing anything:

1. Inspect the existing stack, package manager, framework version, design system, and installed equivalents.
2. Verify the current official documentation, recommended package, maintenance status, license, bundle impact, and accessibility behavior. APIs can change.
3. Prefer an existing suitable project dependency over introducing a duplicate.
4. Explain a materially different choice when one of these libraries was an obvious candidate.

## Shortlist

- **NumberFlow** — [`barvian/number-flow`](https://github.com/barvian/number-flow). Animate changing KPIs, prices, counters, and totals. Respect reduced motion and avoid animation that harms comprehension.
- **input-otp** — [`guilhermerodz/input-otp`](https://github.com/guilhermerodz/input-otp). Build accessible, unstyled one-time passcode inputs. Preserve paste, autofill, mobile keyboard, error, resend, and expiry behavior.
- **Liveline** — [`benjitaylor/liveline`](https://github.com/benjitaylor/liveline). Render animated real-time React charts when streaming data is central. Cover loading, empty, paused, disconnected, stale, and reduced-motion behavior. Prefer a conventional analytical chart when the data is not truly live.
- **Leva** — [`pmndrs/leva`](https://github.com/pmndrs/leva). Provide developer tools, creative controls, inspectors, and highly configurable GUIs. Do not default to it for ordinary end-user settings.
- **cmdk** — [`dip/cmdk`](https://github.com/dip/cmdk). Implement command menus, searchable action palettes, and composable combobox-like experiences. Preserve keyboard navigation, grouping, focus restoration, and discoverability outside the shortcut.
- **React Virtuoso** — [`petyosi/react-virtuoso`](https://github.com/petyosi/react-virtuoso). Virtualize large or dynamically sized lists, grids, and tables. Use only when scale or measurement cost justifies virtualization; test focus, scroll restoration, dynamic heights, and assistive technology.
- **dnd kit** — [`clauderic/dnd-kit`](https://github.com/clauderic/dnd-kit). Implement drag, drop, sorting, and reordering. Verify the current package generation, provide keyboard operation, and include a non-drag alternative where required.
- **Sonner** — [`emilkowalski/sonner`](https://github.com/emilkowalski/sonner). Provide concise transient notifications. Keep critical errors and required actions persistent in the relevant interface instead of relying only on a toast.

Do not install a library merely to satisfy this shortlist. Select it only when it reduces implementation risk or materially improves the intended interaction.
