import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { promises as fsp } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const cli = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "scripts", "clean-handoff.mjs");

function handoff() {
  return {
    objective: "Prepare a minimal handoff.",
    completed: ["Inspected the workspace."],
    remaining: ["Continue in the destination."],
    decisions: ["Transfer context, never approval."],
    repository_state: "Working tree state was summarized.",
    validation_state: "Focused validation is current.",
    risks: [],
    next_action: "Read the live GamePlan.",
  };
}

async function workspace(t) {
  const root = await fsp.mkdtemp(path.join(os.tmpdir(), "clean-handoff-cli-"));
  t.after(() => fsp.rm(root, { recursive: true, force: true }));
  return root;
}

function run(root, input) {
  const result = spawnSync(process.execPath, [cli, "prepare", "--project-root", root], {
    encoding: "utf8",
    input: JSON.stringify(input),
    windowsHide: true,
    maxBuffer: 1024 * 1024,
  });
  assert.equal(result.stderr, "");
  return { ...result, output: JSON.parse(result.stdout) };
}

test("public CLI prepares Direct and Portable handoffs without workspace writes", async (t) => {
  const root = await workspace(t);
  const before = await fsp.readdir(root);
  const direct = run(root, {
    schema: "clean-handoff/context-input/v1",
    mode: "direct",
    projects: [{ projectId: "saved-project", projectKind: "local", path: root }],
    handoff: handoff(),
  });
  assert.equal(direct.status, 0);
  assert.equal(direct.output.ok, true);
  assert.equal(direct.output.command, "prepare");
  assert.equal(direct.output.result.project_selection.state, "exact");
  assert.equal(direct.output.result.task_tool.permitted_calls, 1);

  const portable = run(root, {
    schema: "clean-handoff/context-input/v1",
    mode: "portable",
    projects: null,
    handoff: handoff(),
  });
  assert.equal(portable.status, 0);
  assert.equal(portable.output.result.project_selection, null);
  assert.equal(portable.output.result.task_tool.permitted_calls, 0);
  assert.equal(portable.output.result.storage_written, false);
  assert.deepEqual(await fsp.readdir(root), before);
});

test("public CLI exposes only prepare and bounded help", () => {
  const help = spawnSync(process.execPath, [cli, "--help"], { encoding: "utf8", windowsHide: true });
  assert.equal(help.status, 0);
  assert.match(help.stdout, /\bprepare\b/u);
  for (const retired of ["checkpoint", "resume", "status", "transfer-preflight", "prepare-transfer", "finalize-transfer"]) {
    assert.doesNotMatch(help.stdout, new RegExp(`\\b${retired}\\b`, "u"));
  }
  const commandHelp = spawnSync(process.execPath, [cli, "prepare", "--help"], { encoding: "utf8", windowsHide: true });
  assert.equal(commandHelp.status, 0);
  assert.match(commandHelp.stdout, /clean-handoff\/context-input\/v1/u);
  assert.match(commandHelp.stdout, /one task-tool call/u);
  assert.match(commandHelp.stdout, /permits no task-tool call/u);
});

test("public CLI failures stay bounded and hide raw input", async (t) => {
  const root = await workspace(t);
  const failed = run(root, { password: "hunter2" });
  assert.equal(failed.status, 1);
  assert.equal(failed.output.ok, false);
  assert.equal(failed.output.error.code, "invalid-object-keys");
  assert.doesNotMatch(JSON.stringify(failed.output), /hunter2/u);
  assert.equal(failed.output.project_root, ".");
});
