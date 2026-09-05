# Maintained skill sources

As of September 5, 2026, this repository is the maintained source for all 54 user skills listed in README.md. It includes the audited installed packages and their supporting resources, licenses, and notices. Vendor plugin caches and `.system` skills remain vendor-managed.

`clean-handoff` is junction-linked from the local Codex installation to this repository. Other installed packages are separate copies. Before copying or reinstalling, compare source and installed files and preserve intentional changes on both sides; synchronize complete changed resources, not just SKILL.md. Do not overwrite newer source scripts or tests with older installed copies.

The separate `robertbradley-oss/clean-handoff` repository and its former pinned revision record earlier history. This repository now maintains the local variant directly, with its contract tests; CI no longer requires byte equality with that historical pin.

The sibling `game plan/`, `post clean/`, `post-clean-pr/`, and `simplify/` directories are historical snapshots. Preserve them for history and do not reinstall them over current packages. This source index grants no execution or deletion authority.
