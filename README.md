# RobertOS Skills

Standalone Codex skills maintained by RobertOS. Each top-level skill directory
is independently installable, contains its own tests when applicable, and has
no plugin or marketplace packaging. Repository-wide automation lives under
`.github/` so the root remains focused on installable skill packages.

## Active skills

| Skill | Purpose | Package |
| --- | --- | --- |
| Clean Handoff | Prepare and resume context handoffs; use available tools for task delivery and supported migration. | [`clean-handoff/`](clean-handoff/) |
| GamePlan | Preserve strategic continuity and control approved execution slices. | [`gameplan/`](gameplan/) |
| Clean Up | Automatically resolve file, artifact, release, duplicate, organization, branch, worktree, and tracked-code evidence into safe keep, move, cleanup, or preservation decisions. | [`clean-up/`](clean-up/) |
| Simplify | Explain technical reports in everyday language without changing their conclusions. | [`simplify-report/`](simplify-report/) |

Install any package with Codex's `$skill-installer` using this repository and
the package path `clean-handoff`, `clean-up`, `gameplan`, or
`simplify-report`. Start a new Codex task after installation so the skill
catalog refreshes.

## Clean Handoff

Clean Handoff prepares enough context for another task to continue the work.
It is an instruction-based skill that uses the tools available in its current
environment; it does not provide its own transfer service or device connection.

| Capability | Behavior and requirements |
| --- | --- |
| Portable brief | Preserves the goal, completed and remaining work, validation evidence, materials, and next action in copyable Markdown. |
| Evidence and decisions | Keeps relevant source links and selection criteria; separates user decisions from assistant recommendations and unresolved ideas. |
| Context import | Reads a named, accessible source conversation when task-reading tools are available. |
| Task delivery | Sends context to an existing task, or creates a new Codex or ChatGPT Work cloud task when explicitly requested and supported by the tools. |
| Native migration | Prefers a supported move of the existing Codex task and Git state when migration is requested; accounts separately for required attachments and other files. |
| Deferred work | Carries an instruction to acknowledge receipt and wait until the user says to start. |
| Incoming handoff | Reconciles supplied context with current instructions and accessible materials, then resumes the next authorized action. |
| Transfer status | Distinguishes prepared, pending, delivered, acknowledged, completed migration, and failed outcomes; identifies missing materials or access. |

For requests to move the existing task and files, it checks native migration
support first. Phone-to-PC and PC-to-phone routing distinguishes control of the
same host from moving execution to a different host or cloud. It accounts for
required Git changes and attachments, checks migration status, and reports
missing materials. Feature flagged capabilities are used only when exposed;
a context summary is never reported as a completed task migration.

Research handoffs preserve the source brief's evidence standard, including
independent pain evidence, competitor checks, payment evidence, and minimal
customer effort when those criteria apply. Compatibility reports cover
only the operation and environment verified by the tools; a readable ChatGPT
conversation alone does not establish Work mode or cloud execution.

Example requests:

- "Use $clean-handoff to create a ChatGPT Work cloud task for this research."
- "Use $clean-handoff to continue this in my existing task named Release review."
- "Use $clean-handoff to prepare copyable context for Codex cloud."
- "Use $clean-handoff to resume from this handoff in the current workspace."
- "Move my task named Checkout fix to my home PC, including its files."
- "Continue the same PC-hosted task from my phone."
- "Send this to Codex so it's ready to be worked on when I get home."

The last request prepares a brief for later execution. It carries an explicit
instruction to acknowledge receipt and wait for the user to say "start". Current
task tools can trigger a receiving run, so this is an acknowledgment-only
instruction, not a scheduler-enforced pause. A request for no run or setup at all
keeps the brief in the source conversation when no draft facility is available.

On a phone, [Remote](https://learn.chatgpt.com/docs/remote-connections) can use
the connected desktop's skills and Codex tasks. The host must remain available.
Ordinary mobile ChatGPT needs the skill available to that account and a supported
delivery tool. If delivery is unavailable, Clean Handoff prepares the brief in
the source conversation and gives a pickup instruction for Codex at home;
it does not claim the work was sent or automatically queued.

Direct creation or delivery depends on the tools available in that environment.
The Codex app's current `create_thread` tool supports ChatGPT Work cloud creation;
its currently exposed `handoff_thread` tool does not migrate tasks to cloud.
The skill rechecks the active contract for newly available routes. Unsupported
routes get one self-contained, copyable prompt. Local skill installation does not establish
cloud installation or transfer access to files, credentials, or conversation history.

### Availability and verification

This repository distributes the standalone skill. A local experimental plugin
package was prepared during development, but is not included here, published,
or installed in mobile ChatGPT. Packaging the instructions as a plugin does not
add Codex task tools, a PC connection, automatic offline delivery, or cloud
migration support. The portable brief can be used without installing the skill
at the destination. See OpenAI's [skill availability](https://learn.chatgpt.com/docs/build-skills)
and [plugin packaging guidance](https://learn.chatgpt.com/docs/build-plugins)
for supported distribution routes.

Context retrieval from an accessible ChatGPT conversation into a Codex task was
demonstrated during development. That does not verify Work cloud execution,
reverse-direction delivery, file migration, or a phone-to-PC plugin. Package and
metadata checks validate structure; live cross-device transfer remains unverified.

## Clean Up

Clean Up is an evidence-based repository and workspace maintenance skill. It
scans broadly, makes technical retention decisions automatically, and asks the
user only for approval before an exact filesystem or Git mutation.

It covers:

- generated build output, temporary residue, caches, artifacts, and old local
  releases;
- exact duplicate files and loose root files that belong in an established
  project directory;
- stale local branches and linked worktrees;
- tracked dead-code signals in C# and PowerShell, including modified files;
- ordinary folders as well as Git repositories and multi-worktree workspaces.

### Decision workflow

| Stage | What it does | Mutates anything? |
| --- | --- | --- |
| Triage | Runs the broad audit, investigates promising leads, and decides remove, move, keep, or preserve. | No |
| Discover | Produces the raw lead inventory when explicitly requested or when diagnosing Triage. | No |
| Inspect | Freezes exact path or Git targets and binds candidates to their current state. | No |
| Apply | Re-inspects approved candidates, quarantines recoverable data, validates the result, and rejects stale evidence. | Yes, with explicit approval |

Uncertain evidence defaults to keeping the item. Discovery, dead-code, and
organization IDs never authorize deletion. Cleanup and Git candidates require
their exact current IDs and separate approval, so a broad scan cannot silently
remove or reorganize a workspace.

### Quick start

Install `clean-up`, restart Codex so the skill catalog refreshes, then use:

```text
Use $clean-up to audit this workspace and automatically decide what should be
removed, moved, kept, or preserved across files, organization, Git hygiene,
and tracked code. Do not ask me to make technical retention decisions; ask
only for exact mutation approval.
```

The default Triage report leads with a plain verdict such as `clean`,
`cleanup-recommended`, `organization-recommended`, or `incomplete`, followed
by the exact action and evidence that matter.

## Repository validation

The shared validation workflow under [`.github/workflows/`](.github/workflows/)
checks all four skill packages on Windows, macOS, and Linux, runs Clean Handoff package and metadata tests,
compiles the Clean Up helpers, and runs the package-local Clean Up and
Simplify test suites.

See [source maintenance](CANONICAL-SOURCES.md) for synchronization rules and package provenance boundaries.
