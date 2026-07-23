import assert from "node:assert/strict";
import test from "node:test";

import {
  SafeFailure,
  asSafeFailure,
  failureEnvelope,
  notice,
  successEnvelope,
} from "../scripts/internal/errors.mjs";

test("SafeFailure preserves only bounded static diagnostics", () => {
  const safe = new SafeFailure("invalid-input", "The input is invalid.");
  assert.equal(safe.code, "invalid-input");
  assert.equal(safe.message, "The input is invalid.");
  assert.equal(safe.kind, "failure");

  const unsafe = new SafeFailure("BAD CODE", "secret\nraw-path");
  assert.equal(unsafe.code, "internal-failure");
  assert.equal(unsafe.message, "The operation failed without exposing untrusted diagnostics.");
});

test("unexpected errors collapse to one non-leaking failure", () => {
  const raw = new Error("C:\\private\\token=abc");
  const safe = asSafeFailure(raw);
  assert.equal(safe.code, "internal-failure");
  assert.doesNotMatch(safe.message, /private|token/iu);

  assert.deepEqual(failureEnvelope(raw, {
    schema: "clean-handoff/test/v1",
    command: "test",
  }), {
    schema: "clean-handoff/test/v1",
    command: "test",
    ok: false,
    project_root: ".",
    error: {
      code: "internal-failure",
      message: "The operation failed without exposing untrusted diagnostics.",
    },
  });
});

test("success and notice shapes are deterministic", () => {
  assert.deepEqual(notice("safe-notice", "A safe notice."), {
    code: "safe-notice",
    message: "A safe notice.",
  });
  assert.deepEqual(successEnvelope({
    schema: "clean-handoff/test/v1",
    command: "test",
    result: { value: 1 },
  }), {
    schema: "clean-handoff/test/v1",
    command: "test",
    ok: true,
    project_root: ".",
    result: { value: 1 },
  });
});

test("checkpoint partial-state evidence is bounded and non-leaking", () => {
  const safe = new SafeFailure("checkpoint-pointer-failed", "The pointer failed safely.", {
    transaction: {
      state: "archive-published-pointer-failed",
      archive: "git-common-dir/clean-handoff/v2/projects/<project-key>/checkpoints/id.md",
      storage_written: true,
    },
  });
  assert.deepEqual(failureEnvelope(safe, {
    schema: "clean-handoff/helper-output/v2",
    command: "checkpoint",
  }).transaction, {
    archive: "git-common-dir/clean-handoff/v2/projects/<project-key>/checkpoints/id.md",
    state: "archive-published-pointer-failed",
    storage_written: true,
  });

  const unsafe = new SafeFailure("checkpoint-pointer-failed", "The pointer failed safely.", {
    transaction: { archive: "C:\\private\npath" },
  });
  assert.equal(failureEnvelope(unsafe, {
    schema: "clean-handoff/helper-output/v2",
    command: "checkpoint",
  }).transaction, undefined);
});
