import assert from "node:assert/strict";
import { promises as fsp } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

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
  const frontmatter = skill.match(/^---\n([\s\S]*?)\n---(?:\n|$)/u)?.[1];
  assert.ok(frontmatter, "SKILL.md must have YAML frontmatter");
  assert.match(frontmatter, /^name: clean-handoff$/mu);
  const description = frontmatter.match(/^description: "(.+)"$/mu)?.[1];
  assert.ok(description?.trim(), "skill discovery needs a description");
  assert.ok(description.length <= 1024);

  const agents = await fsp.readFile(path.join(root, "agents", "openai.yaml"), "utf8");
  const shortDescription = agents.match(/short_description: "(.+)"/u)?.[1];
  assert.ok(shortDescription?.trim(), "skill UI needs a short description");
  assert.ok(shortDescription.length >= 25 && shortDescription.length <= 64);
  assert.match(agents, /default_prompt: "Use \$clean-handoff /u);
});
