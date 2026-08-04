import assert from "node:assert/strict";
import { promises as fsp } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("skill uses a single-workflow fast path", async () => {
  const skill = await fsp.readFile(path.join(root, "SKILL.md"), "utf8");

  assert.match(skill, /Keep this fast\./u);
  assert.match(skill, /context already present in the conversation/u);
  assert.match(skill, /Call `list_projects` once/u);
  assert.match(skill, /Call `create_thread` once/u);
  assert.match(skill, /environment: \{ type: "local" \}/u);
  assert.match(skill, /new task is not an implicit request for a new Git worktree/u);
  assert.match(skill, /only when the user explicitly requests an isolated worktree/u);
  assert.match(skill, /Never rely on an inferred `main`, `master`, or default branch/u);
  assert.match(skill, /do not wait for the new task to run/u);
  assert.match(skill, /Do not retry automatically/u);
  assert.match(skill, /Portable handoff/u);
  assert.doesNotMatch(skill, /references\/|scripts\//u);
});

test("runtime package has no helper or workflow-reference latency", async () => {
  async function filesUnder(directory) {
    const files = [];
    let entries;
    try {
      entries = await fsp.readdir(directory, { withFileTypes: true });
    } catch (error) {
      if (error?.code === "ENOENT") return files;
      throw error;
    }
    for (const entry of entries) {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) files.push(...await filesUnder(target));
      else files.push(target);
    }
    return files;
  }

  for (const directory of ["scripts", "references"]) {
    assert.deepEqual(await filesUnder(path.join(root, directory)), []);
  }
});

test("metadata remains concise and routable", async () => {
  const skill = (await fsp.readFile(path.join(root, "SKILL.md"), "utf8")).replace(/\r\n/gu, "\n");
  const frontmatter = skill.slice(0, skill.indexOf("\n---", 4) + 4);
  assert.equal(frontmatter, `---
name: clean-handoff
description: Create one new Codex task with the minimum useful context, or return that context as copyable text. Use when the user asks to hand off, continue in a new task, or make a portable handoff.
---`);

  const agents = await fsp.readFile(path.join(root, "agents", "openai.yaml"), "utf8");
  assert.match(agents, /short_description: "Fast handoff to a new task or copyable text"/u);
  assert.match(agents, /default_prompt: "Use \$clean-handoff /u);
});
