---
name: vercel-deploy
description: "Deploy to Vercel when requested, respecting the specified target environment."
---


# Vercel Deploy

Deploy any project to Vercel instantly. **Always deploy as preview** (not production) unless the user explicitly asks for production.

## Prerequisites

- Check whether the Vercel CLI is installed (for example, `command -v vercel` on POSIX shells or `where.exe vercel` on Windows).
- In this Codex desktop environment, do not request sandbox escalation. Run deploy commands normally; if network or authentication fails, report the error and the next user action.
- The deployment might take a few minutes. Use appropriate timeout values.

## Quick Start

1. Check whether the Vercel CLI is installed (no escalation for this check):

```bash
command -v vercel
```

2. If `vercel` is installed, run this using the current execution tool's supported timeout/session settings:
```bash
vercel deploy [path] -y
```

Builds can take several minutes. Use the returned process session for follow-up and keep the user informed; do not assume a long blocking timeout is supported.

3. If `vercel` is not installed, or if the CLI fails with "No existing credentials found", use the fallback method below.

## Fallback (No Auth)

If CLI fails with auth error, use the deploy script:

```bash
skill_dir="<path-to-skill>"

# Deploy current directory
bash "$skill_dir/scripts/deploy.sh"

# Deploy specific project
bash "$skill_dir/scripts/deploy.sh" /path/to/project

# Deploy existing tarball
bash "$skill_dir/scripts/deploy.sh" /path/to/project.tgz
```

The script handles framework detection, packaging, and deployment. It waits for the build to complete and returns JSON with `previewUrl` and `claimUrl`.

On Windows, use this fallback only when Bash is available. If Bash is unavailable, prefer the Vercel CLI path and report that the bundled shell fallback cannot run in the current shell.

**Tell the user:** "Your deployment is ready at [previewUrl]. Claim it at [claimUrl] to manage your deployment."

## Production Deploys

Only if user explicitly asks:
```bash
vercel deploy [path] --prod -y
```

## Output

Show the user the deployment URL. For fallback deployments, also show the claim URL.

Verify the authorized deployment with an appropriate read-only status or page check. Report separately whether deployment completed and whether the relevant page or flow was verified.

## Troubleshooting

### Network Access

If deployment fails due to network issues (timeouts, DNS errors, connection resets), report the exact failure and whether it came from CLI auth, packaging, upload, or build status. Do not request sandbox escalation in this environment.
