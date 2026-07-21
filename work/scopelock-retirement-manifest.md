# ScopeLock Retirement Manifest

Date: 2026-07-20
Status: Finalized for Phase F — retention dispositions executed; no removal candidates
Authority: Evidence only; this manifest cannot authorize installation, configuration changes, or deletion

## Disposition vocabulary

- `remove — dependency safety proven`: no component currently qualifies.
- `retain — live dependency`: direct local evidence shows an active registration or verified consumer.
- `retain — possible dependency`: a concrete reference exists but live consumption was not invoked or tested.
- `retain — dependency uncertain`: the exact component or its consumers could not be completely inspected.
- `retain — historical evidence`: preserve useful evidence even when runtime consumption is absent.
- `separate approval required`: the action is outside the current slice or requires external, configuration, remote, or destructive authority.

Static-search absence is supporting evidence only and never satisfies the no-break deletion rule.

## Exact discovered components and references

| Exact component or referenced target | Category | Disposition | Direct evidence and limitation |
|---|---|---|---|
| `C:\Users\robby\.codex\config.toml` | Configuration | retain — live dependency | Read-only search found active `[marketplaces.scopelock]` and `[plugins."scopelock@scopelock"]` registrations. Changing this file requires a later exact configuration slice. |
| `\\?\C:\Users\robby\Documents\Codex\2026-07-15\paste-this-into-a-new-empty\scopelock\dist\scopelock-marketplace-0.2.0+codex.20260719234815` | Configured marketplace source | retain — live dependency | Exact `source` value in active configuration. The target was not inside the approved read-only roots and was not inspected. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\` | Installed managed plugin package | retain — live dependency | The amended exact inventory succeeded. Active plugin configuration and skill discovery make manual cache removal unsafe; every descendant is retained under the category map below. |
| `scopelock/context/v2` | Compatibility interface | retain — live dependency | Existing canonical evidence records a verified external consumer. The consumer was not inspected or invoked in this slice. |
| `scopelock/reserved-sideband/v1` | Compatibility interface | retain — live dependency | Existing canonical evidence records a verified external consumer. The consumer was not inspected or invoked in this slice. |
| `C:\Users\robby\Documents\Codex\2026-07-16\scopelock-phase-5-test` | Registered project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\Codex\2026-07-16\scopelock-phase-5-fresh-retest` | Registered project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\Codex\2026-07-16\scopelock-phase-5-test\work\cli-fresh-pickup` | Registered project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\Codex\2026-07-16\scopelock-phase-5-test\work\cli-fresh-workflow` | Registered project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\Codex\2026-07-16\scopelock-phase-5-app-pickup` | Registered project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\Codex\2026-07-15\paste-this-into-a-new-empty\scopelock` | Registered source-project reference | retain — possible dependency | Exact project key found in configuration; the project was not inspected. |
| `C:\Users\robby\Documents\game plan\.codex-scope` | Enumerated workspace store | retain — dependency uncertain | The exact approved metadata command reported no enumerated store. Absence does not authorize deletion and says nothing about stores outside the approved roots. |
| `C:\Users\robby\.codex-scope` | Enumerated user store | retain — dependency uncertain | The exact approved metadata command reported no enumerated store. Absence does not authorize deletion and says nothing about stores outside the approved roots. |
| Remote repository or marketplace listing | Remote/public surface | separate approval required | No network or remote inspection was authorized. No remote action is included in Phase F Slice 1. |

## Installed package category map

Every path observed by amended command 5 is covered by one exact package path or directory prefix below. Directory rows include every observed descendant. No row is a deletion candidate.

| Exact installed path or prefix | Observed contents | Disposition | Reason |
|---|---|---|---|
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\.codex-plugin\` | `plugin.json` | retain — live dependency | Runtime plugin metadata inside the actively registered package. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\hooks\` | `hooks.json` | retain — possible dependency | Hook registration may participate in the installed product; contents were not invoked or dependency-tested. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\scripts\` | release builders, `scopelock.mjs`, and `scopelock-hook.mjs` | retain — possible dependency | Runtime, hook, build, or supported uninstall behavior may consume these scripts. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\skills\` | ScopeLock skill and UI metadata | retain — live dependency | The installed skill is currently discoverable. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\references\` | protocol, path rules, and Lock/Status/Verify workflow references | retain — possible dependency | The discovered skill or another package surface may load these references. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\marketplace\` | marketplace listing | retain — possible dependency | It is part of the configured marketplace package; remote/public action would require separate approval. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\assets\` | icons, logo, demo video, and social preview | retain — possible dependency | Marketplace, UI, documentation, or packaging may consume these assets. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\demo\` | demo render and runner scripts | retain — possible dependency | Installed package completeness and marketplace/demo workflows were not dependency-tested. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\examples\` | auth-demo source, configuration, tests, package metadata, and README | retain — possible dependency | Tests, documentation, or demonstrations may consume this subtree. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\docs\` | architecture, contracts, schemas, security, workflows, plans, and test summaries | retain — historical evidence | Useful historical/design evidence is explicitly preserved; some references may also be loaded by product workflows. |
| `C:\Users\robby\.codex\plugins\cache\scopelock\scopelock\0.2.0+codex.20260719234815\package.json` | Package entry point and metadata | retain — live dependency | Package registration and supported lifecycle behavior may depend on it. |

The following exact observed top-level files are retained as package metadata, legal/security material, release evidence, or historical evidence: `.gitignore`, `CHANGELOG.md`, `LICENSE`, `PHASE-1.md`, `PHASE-2.md`, `PHASE-3.md`, `PHASE-3.5.md`, `PHASE-4.md`, `PHASE-5.md`, `PRIVACY.md`, `README.md`, `RELEASE_NOTES.md`, `SECURITY.md`, `scopelock-threat-model.md`, and `security_best_practices_report.md`. Their disposition is `retain — historical evidence` plus `retain — possible dependency` while the managed plugin remains configured.

## Conservative conclusion

The exact cache inventory, active plugin/marketplace configuration, discoverable skill, known live compatibility interfaces, uninspected configured source, registered project references, and lack of file-level no-break testing leave no component eligible for `remove — dependency safety proven`. Phase F therefore executed a retain-only disposition with no ScopeLock deletion or mutation. A later retirement proposal may document retention or use a supported uninstall path only if it can preserve every live or possible dependency; this manifest itself authorizes neither action.

## GamePlan installation outcome

Phase F Slice 2 updated only the three explicitly approved installed GamePlan targets. The installed package validator passed and all five installed files hash-match their workspace sources. That one-time installation authority expired when the slice closed; this manifest grants no continuing installation, ScopeLock mutation, or deletion authority.
