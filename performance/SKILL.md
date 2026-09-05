---
name: performance
description: "Diagnose and improve measured web loading or runtime performance."
license: MIT
metadata:
  author: web-quality-skills
  version: "1.0"
---


# Web performance

Start from the reported symptom and available measurements. Identify the affected route, device/network conditions, and relevant loading or runtime metric. Prefer the project's existing performance tooling.

Use [OPTIMIZATION.md](OPTIMIZATION.md) only for the relevant bottleneck: resource loading, images/fonts, caching, runtime, or third-party code. Treat budgets and browser-support claims as illustrative; verify current APIs and target support before changes. Avoid applying the whole cookbook.

For LCP, INP, or CLS work, use the relevant `core-web-vitals` reference. Implement requested improvements, compare under consistent conditions, and report measured results and limits. Do not claim field improvement from a single lab run.
