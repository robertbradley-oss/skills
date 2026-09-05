# Maintained skill sources

This repository maintains four skill packages: `clean-handoff`, `clean-up`, `gameplan`, and `simplify-report`. Installing a skill locally does not establish authorship or make this repository its maintained source. Review provenance and maintenance intent individually before adding another package. Vendor plugin caches and `.system` skills remain vendor-managed.

`clean-handoff` is junction-linked from the local Codex installation to this repository. Other installed packages are separate copies. Before copying or reinstalling, compare source and installed files and preserve intentional changes on both sides; synchronize complete changed resources, not just SKILL.md. Do not overwrite newer source scripts or tests with older installed copies.

The separate `robertbradley-oss/clean-handoff` repository and its former pinned revision record earlier history. This repository now maintains the local variant directly, with its contract tests; CI no longer requires byte equality with that historical pin.

The sibling `game plan/`, `post clean/`, `post-clean-pr/`, and `simplify/` directories are historical snapshots. Preserve them for history and do not reinstall them over current packages. This source index grants no execution or deletion authority.
