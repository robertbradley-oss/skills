import assert from "node:assert/strict";
import { promises as fsp } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("skill uses a single-workflow fast path", async () => {
  const skill = await fsp.readFile(path.join(root, "SKILL.md"), "utf8");

  assert.match(skill, /Use conversation context/u);
  assert.match(skill, /Only create a task when the user explicitly requests one/u);
  assert.match(skill, /Discover the saved project/u);
  assert.match(skill, /current `create_thread` contract/u);
  assert.match(skill, /honoring an explicit user request/u);
  assert.match(skill, /Do not invent a branch/u);
  assert.match(skill, /Create one task/u);
  assert.match(skill, /do not retry an uncertain creation blindly/u);
  assert.match(skill, /or wait for the destination to finish/u);
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
description: "Prepare a concise handoff or create a new task when explicitly requested."
---`);

  const agents = await fsp.readFile(path.join(root, "agents", "openai.yaml"), "utf8");
  assert.match(agents, /short_description: "Fast handoff to a new task or copyable text"/u);
  assert.match(agents, /default_prompt: "Use \$clean-handoff /u);
});
