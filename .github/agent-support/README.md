# Useful agents

Four GitHub Copilot custom agent profiles live in [`.github/agents`](../agents/).
They are reusable instructions executed by your agent host, not standalone apps
or a background service. Running them requires a compatible Copilot environment
and its normal access/usage allowance. No model or paid external service is pinned.

| Agent | Example request | Expected result |
| --- | --- | --- |
| Bug Reproducer | Reproduce issue 123 with a regression test. Do not fix production code. | Observed failure, exact command, revision, and reproduction limits. |
| Docs Verifier | Verify the README quick start in a fresh environment and fix supported documentation errors. | Command results and corrections with retest evidence. |
| Skill Auditor | Audit these skill definitions and report structural and instruction issues. | Structural check results plus separate semantic findings. |
| Release Evidence | Report what shipped between these two SHAs to staging and what was verified. | Claims tied to commits, CI, deployment, and live evidence or explicit gaps. |

## Use in this repository

After the profiles reach the default branch, open the
[GitHub Agents page](https://github.com/copilot/agents), select this repository,
and select a custom agent. Agent availability also depends on your account and
repository configuration. In Copilot CLI, select a profile with `/agent`.

## Use in another repository

Copy the desired `.agent.md` files from `.github/agents/` into the destination's
`.github/agents/`. Preserve existing files and resolve filename collisions before
copying. Commit them to the destination's default branch for GitHub use.
Profiles in this repository do not automatically become available in your other
repositories. These files are not Codex `SKILL.md` packages.

The four profiles are self-contained. For Skill Auditor's optional structural
checker, also copy this `agent-support` directory into `.github/agent-support/`.
Inspect the helper, then install the pinned dependency in an isolated Python
environment: `python -m pip install PyYAML==6.0.3`. Python 3.12 or newer is supported.
Run from the destination repository root:

```sh
python .github/agent-support/audit_definitions.py .
```

The helper reads definitions and prints JSON; it does not modify them or execute
their contents. Exit 0 means no structural errors, 1 means errors were found,
and 2 means the requested audit could not start. Warnings still require review.
It checks `SKILL.md` and `*.agent.md`, not arbitrary `.md` agent filenames.
It ignores common dependency directories and file symlinks. Local inline Markdown
links are checked relative to each document (leading `/` means the audit root);
fenced examples, inline code, external URLs, and anchors are not validated.
Reference-style links, complex nested Markdown, full skill schemas, tool
availability, and MCP configuration schemas need separate review. Audit only
trusted local directory trees; this utility is not a filesystem sandbox.

## Validation and evaluation

```sh
python .github/agent-support/audit_definitions.py .github/agents
python -B -m unittest discover -s .github/agent-support/tests -p "test_*.py" -v
```

CI runs these checks on Windows, macOS, and Linux. Automated tests exercise the
checker using valid and malformed temporary definitions. They do not establish
the four agents' reasoning quality. The [evaluation cases](EVALUATION.md) provide
repeatable tasks and rejection criteria for testing that separately. No hosted
Copilot evaluation or success-rate claim is bundled with this initial release.

Shell tools can modify files even when an agent is instructed to be read-only.
Use host permissions and an isolated environment appropriate to the target code.
The Release Evidence profile intentionally omits the edit tool and instructs
read-only inspection; this is not a guarantee enforced by its prompt.

Configuration reference: [GitHub custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration).
