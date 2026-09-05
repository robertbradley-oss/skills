# Product-surface checks

Use only the sections that match the detected project. Repository documentation and
declared test workflows remain authoritative.

## Library or SDK

- Run type/compile checks and unit or contract tests.
- Build the distributable form and inspect package exports and included files.
- Exercise one minimal consumer import in an isolated temporary project when possible
  without installing new dependencies.
- Check supported runtime/module variants only when declared by the project.

## Command-line application

- Exercise `--help`, invalid arguments, and one representative successful workflow.
- Run file-writing or Git-writing journeys only inside an isolated temporary directory
  or temporary repository.
- Inspect exit codes, stdout/stderr separation, error clarity, and output format.
- Avoid commands that authenticate, publish, delete, or contact production services.

## API or service

- Start only a local development/test server with isolated configuration.
- Check health/startup, one representative successful request, validation failure, and
  safe error handling.
- Do not send writes to shared or production databases, queues, storage, or APIs.
- Stop every server or service process created by the pass.

## Web application

- Use the installed visual UI QA or browser verification skill when available.
- Check a representative desktop and mobile viewport, console/runtime errors, overflow,
  broken assets, keyboard access, and primary non-destructive journeys.
- Exercise loading, empty, error, and populated states when safely reachable.
- Do not approve or replace screenshot baselines without explicit authorization.

## Desktop or mobile application

- Prefer project-native test runners, emulators, or simulators already configured.
- Check launch, one primary journey, error handling, window/viewport resizing, and
  platform-specific packaging when available.
- State clearly when GUI automation, signing, devices, or platform toolchains are absent.

## GitHub Action, plugin, extension, or integration

- Validate its manifest and build/bundle output.
- Run fixture-driven or local harness tests for inputs, outputs, and failure behavior.
- Verify committed distributable artifacts match source only when the project defines a
  deterministic comparison method.
- Do not publish, install globally, or invoke live third-party mutations.

## Data, schema, or migration project

- Validate schemas and representative valid/invalid fixtures.
- Run migrations only against an isolated disposable database and only when their test
  workflow is already declared safe.
- Check backward/forward compatibility only to the degree the repository specifies.
- Never run seed or migration commands against an unknown or shared environment.

## Documentation or examples

- Verify primary setup and usage commands against the current interface when safe.
- Check executable snippets, links, generated references, and example fixtures using
  repository-declared tooling.
- Treat stale instructions that block primary use as QA failures; cosmetic prose issues
  are findings only when documentation quality is in scope.

## Security, privacy, accessibility, and performance

- General QA may report obvious exposed secrets, unsafe fixture data, privacy-contract
  regressions, inaccessible primary controls, or severe performance failures supported
  by direct evidence.
- Do not claim a security, accessibility, privacy, or performance audit from this pass.
- Use the relevant specialist skill for deep or compliance-oriented coverage, and name
  that separate scope in the final report.
