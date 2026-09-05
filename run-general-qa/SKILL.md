---
name: run-general-qa
description: "Run a broad project QA audit and report verified coverage and gaps."
---


# Run General QA

Perform the broadest safe verification supported by the project. Treat "check
everything" as a coverage objective, not permission to run destructive, external,
state-changing, or production actions.

## Operating contract

- A QA-only request is audit and report only. A combined QA-and-fix request authorizes fixing in-scope defects and rechecking them. Do not otherwise fix source, update snapshots, rewrite formatting,
  install or update dependencies, commit, push, deploy, migrate, seed, publish, or
  release unless the user separately requests that action.
- Preserve pre-existing uncommitted work. Record Git state before and after checks;
  never revert changes that a check creates.
- Prefer project-declared commands and repository instructions over generic commands.
- Use the package manager and toolchain selected by lockfiles, manifests, wrappers,
  and CI configuration.
- Keep all generated test data in an isolated temporary directory when practical.
- Do not access paid services, production data, private accounts, or external systems
  merely because credentials or connectors are available.
- Do not call the result comprehensive unless every applicable discovered surface was
  exercised. List every limitation explicitly.

## 1. Establish the QA target

1. Resolve the repository root and requested scope. Default to the current repository
   when the user does not narrow the target.
2. Read applicable `AGENTS.md`, repository instructions, README files, manifests,
   lockfiles, workspace definitions, and CI workflows.
3. Capture the starting branch, revision, and `git status --short`. Do not assume a
   dirty tree was produced by QA.
4. Identify the project type and user-facing surfaces: library, CLI, API, web app,
   desktop/mobile app, extension, action/plugin, infrastructure, or documentation.
5. Identify required services, credentials, fixtures, browsers, databases, and build
   tools. Separate available surfaces from unavailable ones before running checks.

## 2. Build a coverage matrix

Create a working matrix with these categories. Mark each as applicable or not
applicable, available or unavailable, and release-critical or supplementary. Treat a
surface as release-critical only when it carries unique user risk that the other
checks do not substantially cover.

| Category | Typical evidence |
| --- | --- |
| Repository hygiene | clean conflict markers, valid manifests, Git diff checks |
| Static checks | format-check, lint, typecheck, compile checks |
| Automated tests | unit, integration, contract, end-to-end tests |
| Build and package | production build, bundle, package/dry-run validation |
| Product behavior | representative user journeys or isolated smoke workflows |
| UI and accessibility | responsive states, keyboard, console, visible semantics |
| Configuration | example config, environment validation, CI/action definitions |
| Documentation | commands and examples needed for primary use still work |
| Security and privacy | only lightweight relevant checks unless a security audit is requested |

Read [references/surface-checks.md](references/surface-checks.md) after identifying the
applicable product surfaces. Load only the sections relevant to the target.

## 3. Select commands conservatively

1. Inventory declared scripts and CI commands before choosing what to run.
2. Prefer non-writing checks such as `format:check`, lint, typecheck, test, build,
   package validation, and declared smoke or end-to-end commands.
3. Inspect script definitions for nested calls. Avoid running duplicate commands when
   one declared aggregate already provides the same evidence, unless independent
   execution materially improves failure diagnosis.
4. Reject commands whose names or bodies imply deploy, publish, release, migration,
   seed, install, update, fix, write-format, snapshot approval, data deletion, or
   external mutation.
5. Do not invent an unsupported test command. Missing coverage is a reportable gap.
6. Ask before a check requires a meaningful download, account login, external write,
   production-like mutation, or unusually long/expensive execution.

## 4. Run the pass in layers

Run independent checks even after another category fails when doing so is safe and
useful. Capture the exact command, exit status, duration when available, and concise
failure evidence.

1. **Fast hygiene:** manifest parsing, conflict-marker search, `git diff --check`, and
   cheap repository-native validation.
2. **Static checks:** formatting check, lint, typecheck, schema/config checks.
3. **Automated tests:** focused or aggregate unit, integration, contract, and e2e tests.
4. **Build/package:** production compilation, bundles, package metadata, and safe
   dry-run packaging when the project supports it.
5. **Product smoke:** exercise representative primary workflows using isolated data.
6. **Specialist checks:** route UI, accessibility, performance, or security depth to
   the relevant installed skill only when that surface exists and the requested QA
   scope supports it.

Do not diagnose solely from a final aggregate exit code. Read the failure output,
locate the failing component, and distinguish a product defect from a missing tool,
environment limitation, flaky test, or unavailable dependency. Apply fixes only when included in the user's request.

## 5. Verify QA did not alter the project

1. Capture final `git status --short` and compare it with the starting state.
2. Report new tracked changes and generated artifacts. Do not remove or revert them.
3. Confirm that locally started processes were stopped if the QA pass created them.
4. Keep useful screenshots or logs only when they support a reported finding; otherwise
   use temporary locations.

## 6. Report the result

Use one of these overall outcomes:

- **Passed:** every applicable, available check passed and any unavailable surfaces
  were supplementary or substantially covered by equivalent local evidence. List the
  limitations even though the result passed.
- **Needs attention:** a check failed, QA changed tracked files, or a release-critical
  surface with unique risk could not be verified. A missing live integration is not
  automatically release-critical when deterministic local contract tests cover it.
- **Blocked:** the project could not be resolved or no meaningful check could run.

Lead with the outcome, then report:

1. What passed.
2. What failed, with the smallest useful reproduction command and cause category.
3. What was skipped or unavailable and why.
4. Coverage by category and product surface.
5. Whether Git state changed during QA.
6. A useful next action when one remains; do not manufacture one after completion.

Never equate "tests passed" with "QA passed" when builds, runtime workflows, or other
applicable surfaces failed or were not exercised. Never bury a failure beneath a long
list of successes.
