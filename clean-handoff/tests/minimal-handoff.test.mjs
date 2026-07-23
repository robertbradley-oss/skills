import assert from "node:assert/strict";
import { promises as fsp } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { SafeFailure } from "../scripts/internal/errors.mjs";
import {
  HANDOFF_OUTPUT_SCHEMA,
  HANDOFF_PROMPT_BYTES,
  prepareMinimalHandoff,
} from "../scripts/internal/minimal-handoff.mjs";

function context(overrides = {}) {
  return {
    objective: "Move the minimum useful context.",
    completed: ["Phase D produced a working baseline."],
    remaining: ["Validate the two minimal flows."],
    decisions: ["Use built-in task creation exactly once."],
    repository_state: "The workspace has protected untracked evidence.",
    validation_state: "Focused tests are pending.",
    risks: ["Live platform validation remains Phase G."],
    next_action: "Inspect the live repository and GamePlan.",
    ...overrides,
  };
}

async function workspace(t) {
  const root = await fsp.mkdtemp(path.join(os.tmpdir(), "clean-handoff-minimal-"));
  t.after(() => fsp.rm(root, { recursive: true, force: true }));
  return root;
}

test("Direct Handoff selects exactly one project and permits one call without state", async (t) => {
  const root = await workspace(t);
  const before = await fsp.readdir(root);
  const output = await prepareMinimalHandoff(root, {
    schema: "clean-handoff/context-input/v1",
    mode: "direct",
    projects: [{ projectId: "saved-project", projectKind: "local", path: root }],
    handoff: context({ repository_state: "token=super-secret-value remains local." }),
  });
  assert.equal(output.schema, HANDOFF_OUTPUT_SCHEMA);
  assert.equal(output.mode, "direct");
  assert.equal(output.project_selection.state, "exact");
  assert.equal(output.project_selection.match_index, 0);
  assert.deepEqual(output.task_tool, { permitted_calls: 1, automatic_retry: false });
  assert.equal(output.storage_written, false);
  assert.equal(output.authority, "context-only");
  assert.match(output.handoff_text, /Inspect the live repository/u);
  assert.match(output.handoff_text, /live canonical `GAMEPLAN\.md`/u);
  assert.match(output.handoff_text, /context only; it carries no approval/u);
  assert.match(output.handoff_text, /token=\[REDACTED\]/u);
  assert.doesNotMatch(output.handoff_text, /super-secret-value/u);
  assert.ok(Buffer.byteLength(output.handoff_text, "utf8") <= HANDOFF_PROMPT_BYTES);
  assert.deepEqual(await fsp.readdir(root), before);
});

test("Direct Handoff fails closed for unavailable or ambiguous project identity", async (t) => {
  const root = await workspace(t);
  await assert.rejects(
    prepareMinimalHandoff(root, {
      schema: "clean-handoff/context-input/v1",
      mode: "direct",
      projects: [],
      handoff: context(),
    }),
    (error) => error instanceof SafeFailure && error.code === "project-unavailable",
  );
  await assert.rejects(
    prepareMinimalHandoff(root, {
      schema: "clean-handoff/context-input/v1",
      mode: "direct",
      projects: [
        { projectId: "one", projectKind: "local", path: root },
        { projectId: "two", projectKind: "local", path: root },
      ],
      handoff: context(),
    }),
    (error) => error instanceof SafeFailure && error.code === "project-ambiguous",
  );
});

test("Portable Handoff returns copyable text and permits no task call or state", async (t) => {
  const root = await workspace(t);
  const before = await fsp.readdir(root);
  const output = await prepareMinimalHandoff(root, {
    schema: "clean-handoff/context-input/v1",
    mode: "portable",
    projects: null,
    handoff: context(),
  });
  assert.equal(output.mode, "portable");
  assert.equal(output.project_selection, null);
  assert.deepEqual(output.task_tool, { permitted_calls: 0, automatic_retry: false });
  assert.equal(output.storage_written, false);
  for (const heading of [
    "Objective",
    "Completed work",
    "Remaining work",
    "Important decisions",
    "Repository state",
    "Validation state",
    "Risks",
    "Immediate next action",
    "Destination requirements",
  ]) assert.match(output.handoff_text, new RegExp(`## ${heading}`, "u"));
  assert.deepEqual(await fsp.readdir(root), before);
});

test("Portable Handoff rejects project lists and oversized compact fields", async (t) => {
  const root = await workspace(t);
  await assert.rejects(
    prepareMinimalHandoff(root, {
      schema: "clean-handoff/context-input/v1",
      mode: "portable",
      projects: [],
      handoff: context(),
    }),
    (error) => error instanceof SafeFailure && error.code === "invalid-input",
  );
  await assert.rejects(
    prepareMinimalHandoff(root, {
      schema: "clean-handoff/context-input/v1",
      mode: "portable",
      projects: null,
      handoff: context({ objective: "x".repeat(601) }),
    }),
    (error) => error instanceof SafeFailure && error.code === "invalid-text",
  );
});
