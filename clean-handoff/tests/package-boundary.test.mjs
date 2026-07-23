import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { promises as fsp } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const scriptsRoot = path.join(skillRoot, "scripts");

async function filesUnder(root, relativeTo = root) {
  const names = [];
  async function visit(directory) {
    for (const entry of await fsp.readdir(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) await visit(absolute);
      else names.push(path.relative(relativeTo, absolute).replace(/\\/gu, "/"));
    }
  }
  await visit(root);
  return names.sort();
}

function imports(source) {
  return [...source.matchAll(/\bfrom\s+"([^"]+)"/gu)].map((match) => match[1]);
}

async function runtimeGraph() {
  const files = await filesUnder(scriptsRoot, skillRoot);
  const graph = new Map();
  for (const file of files) {
    const source = await fsp.readFile(path.join(skillRoot, file), "utf8");
    const edges = [];
    for (const specifier of imports(source)) {
      if (specifier.startsWith("node:")) continue;
      const resolved = path.resolve(path.dirname(path.join(skillRoot, file)), specifier);
      assert.equal(resolved.startsWith(`${skillRoot}${path.sep}`), true);
      edges.push(path.relative(skillRoot, resolved).replace(/\\/gu, "/"));
    }
    graph.set(file, edges);
  }
  return graph;
}

function reachable(graph, entry) {
  const seen = new Set();
  const visit = (file) => {
    if (seen.has(file)) return;
    seen.add(file);
    for (const dependency of graph.get(file) ?? []) visit(dependency);
  };
  visit(entry);
  return seen;
}

test("metadata describes only Direct and Portable Handoff", async () => {
  const skill = await fsp.readFile(path.join(skillRoot, "SKILL.md"), "utf8");
  const frontmatter = skill.slice(0, skill.indexOf("\n---", 4) + 4);
  assert.equal(frontmatter, `---
name: clean-handoff
description: Move the minimum useful project context into one new Codex task or produce copyable handoff text. Use when the user asks for a direct task handoff or a portable handoff while preserving live GamePlan authority.
---`);
  const activeLinks = [...skill.matchAll(/\]\(references\/workflows\/([a-z-]+)\.md\)/gu)].map((match) => match[1]);
  assert.deepEqual(activeLinks, ["new-task", "portable-handoff"]);
  for (const retired of ["Checkpoint", "Resume", "Status", "Incoming Handoff"]) {
    assert.doesNotMatch(skill, new RegExp(`\\*\\*${retired}`, "u"));
  }
  assert.match(skill, /live root `GAMEPLAN\.md`/u);

  const agents = await fsp.readFile(path.join(skillRoot, "agents", "openai.yaml"), "utf8");
  assert.equal(agents, `interface:
  display_name: "Clean Handoff"
  short_description: "Hand work to a new task or portable text"
  default_prompt: "Use $clean-handoff to create one direct handoff or produce portable handoff text."
policy:
  allow_implicit_invocation: true
`);
});

test("the package contains only the two active workflow guides", async () => {
  assert.deepEqual(await filesUnder(path.join(skillRoot, "references"), path.join(skillRoot, "references")), [
    "workflows/new-task.md",
    "workflows/portable-handoff.md",
  ]);
  const direct = await fsp.readFile(path.join(skillRoot, "references", "workflows", "new-task.md"), "utf8");
  assert.equal((direct.match(/`create_thread`/gu) ?? []).length, 1);
  assert.match(direct, /exactly once/u);
  assert.match(direct, /Do not retry automatically/u);
  assert.match(direct, /creates no persistent transfer state|do not create local recovery state/iu);
  const portable = await fsp.readFile(path.join(skillRoot, "references", "workflows", "portable-handoff.md"), "utf8");
  assert.match(portable, /output-only/u);
  assert.match(portable, /Do not call a task tool/u);
  assert.match(portable, /carries no approval/u);
});

test("the runtime graph contains only the six active modules", async () => {
  const files = await filesUnder(scriptsRoot, skillRoot);
  assert.deepEqual(files, [
    "scripts/clean-handoff.mjs",
    "scripts/internal/context-safety.mjs",
    "scripts/internal/errors.mjs",
    "scripts/internal/fs-safety.mjs",
    "scripts/internal/minimal-handoff.mjs",
    "scripts/internal/project-selection.mjs",
  ]);
  const graph = await runtimeGraph();
  assert.deepEqual(reachable(graph, "scripts/clean-handoff.mjs"), new Set([
    "scripts/clean-handoff.mjs",
    "scripts/internal/errors.mjs",
    "scripts/internal/context-safety.mjs",
    "scripts/internal/minimal-handoff.mjs",
    "scripts/internal/project-selection.mjs",
    "scripts/internal/fs-safety.mjs",
  ]));
});

test("runtime remains self-contained and free of active external-product authority", async () => {
  const graph = await runtimeGraph();
  for (const file of ["SKILL.md", "agents/openai.yaml", ...graph.keys()]) {
    const source = await fsp.readFile(path.join(skillRoot, file), "utf8");
    assert.equal(/\.codex-plugin|plugins[\\/]cache/iu.test(source), false);
    assert.equal(/(?:^|["'])\.\.\/[.]{0,2}(?:scripts|references|tests)\//mu.test(source), false);
    assert.equal(/scope.?lock/iu.test(source), false);
  }
});

test("standalone helper exposes only one deterministic preparation command", () => {
  const cli = path.join(scriptsRoot, "clean-handoff.mjs");
  const help = spawnSync(process.execPath, [cli, "--help"], { encoding: "utf8", windowsHide: true });
  assert.equal(help.status, 0);
  assert.match(help.stdout, /\bprepare\b/u);
  for (const retired of [
    "select-project", "gameplan-status", "snapshot", "analyze", "checkpoint", "storage-preflight",
    "build-preflight", "transfer-preflight", "prepare-transfer", "render-transfer", "verify-transfer",
    "resolve-transfer", "finalize-transfer", "route-task-result",
  ]) assert.doesNotMatch(help.stdout, new RegExp(`\\b${retired}\\b`, "u"));
  const commandHelp = spawnSync(process.execPath, [cli, "prepare", "--help"], { encoding: "utf8", windowsHide: true });
  assert.equal(commandHelp.status, 0);
  assert.match(commandHelp.stdout, /clean-handoff\/helper-output\/v2/u);
  const unknown = spawnSync(process.execPath, [cli, "not-a-command"], { encoding: "utf8", windowsHide: true });
  assert.equal(unknown.status, 1);
  assert.equal(JSON.parse(unknown.stdout).error.code, "unknown-command");
  assert.equal(unknown.stderr, "");
});
