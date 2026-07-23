#!/usr/bin/env node

import path from "node:path";

import { SafeFailure, failureEnvelope, successEnvelope } from "./internal/errors.mjs";
import {
  CONTEXT_HELPER_OUTPUT_SCHEMA,
  CONTEXT_LIMITS,
  parseStrictJson,
} from "./internal/context-safety.mjs";
import { prepareMinimalHandoff } from "./internal/minimal-handoff.mjs";

const COMMAND = "prepare";

function generalHelp() {
  return [
    "Clean Handoff standalone helper",
    "",
    "Usage:",
    "  node clean-handoff.mjs prepare --project-root <absolute-path>",
    "  node clean-handoff.mjs prepare --help",
    "",
    "Commands:",
    "  prepare  Build one bounded redacted Direct or Portable handoff without writing state.",
    "",
    "The helper never creates a task, writes transfer state, or calls a network service.",
  ].join("\n");
}

function commandHelp() {
  return [
    "Clean Handoff prepare",
    "",
    "Usage:",
    "  node clean-handoff.mjs prepare --project-root <absolute-path>",
    "",
    "Input: one clean-handoff/context-input/v1 JSON object on standard input.",
    "Output: one sanitized clean-handoff/helper-output/v2 JSON envelope.",
    "Direct mode requires one exact saved local project match and permits one task-tool call.",
    "Portable mode permits no task-tool call. Neither mode writes persistent transfer state.",
  ].join("\n");
}

function emit(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

async function readStdin(maximum, label) {
  const chunks = [];
  let total = 0;
  for await (const chunk of process.stdin) {
    total += chunk.length;
    if (total > maximum) throw new SafeFailure("input-too-large", `${label} exceeds the permitted size.`);
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

function projectRootArgument(args) {
  if (args.length !== 2 || args[0] !== "--project-root" || !path.isAbsolute(args[1])) {
    throw new SafeFailure("project-root-required", "prepare requires one absolute project root.");
  }
  return args[1];
}

async function main(argv) {
  if (argv.length === 1 && ["--help", "-h"].includes(argv[0])) {
    process.stdout.write(`${generalHelp()}\n`);
    return;
  }
  if (argv[0] !== COMMAND) {
    throw new SafeFailure("unknown-command", "Use --help to view the Clean Handoff command.");
  }
  if (argv.length === 2 && ["--help", "-h"].includes(argv[1])) {
    process.stdout.write(`${commandHelp()}\n`);
    return;
  }
  const projectRoot = projectRootArgument(argv.slice(1));
  const input = parseStrictJson(
    await readStdin(CONTEXT_LIMITS.handoffInputBytes, "Prepare input"),
    { label: "Prepare input", maxBytes: CONTEXT_LIMITS.handoffInputBytes },
  );
  emit(successEnvelope({
    schema: CONTEXT_HELPER_OUTPUT_SCHEMA,
    command: COMMAND,
    result: await prepareMinimalHandoff(projectRoot, input),
  }));
}

const argv = process.argv.slice(2);
try {
  await main(argv);
} catch (error) {
  emit(failureEnvelope(error, {
    schema: CONTEXT_HELPER_OUTPUT_SCHEMA,
    command: argv[0] === COMMAND ? COMMAND : "unknown",
  }));
  process.exitCode = 1;
}
