import { SafeFailure } from "./errors.mjs";
import { assertExactKeys, boundedText, boundedTextList, redactText } from "./context-safety.mjs";
import { selectExactProject } from "./project-selection.mjs";

export const HANDOFF_INPUT_SCHEMA = "clean-handoff/context-input/v1";
export const HANDOFF_OUTPUT_SCHEMA = "clean-handoff/context/v1";
export const HANDOFF_PROMPT_BYTES = 8 * 1024;

const MODES = new Set(["direct", "portable"]);
const SCALAR_LIMIT = 600;
const LIST_ITEM_LIMIT = 160;
const LIST_ITEM_COUNT = 6;

function compactText(value, label) {
  return redactText(boundedText(value, label, SCALAR_LIMIT), SCALAR_LIMIT);
}

function compactList(value, label) {
  return boundedTextList(value, label, {
    maximumItems: LIST_ITEM_COUNT,
    maximumCharacters: LIST_ITEM_LIMIT,
  }).map((item) => redactText(item, LIST_ITEM_LIMIT));
}

function normalizeContext(value) {
  assertExactKeys(value, [
    "objective",
    "completed",
    "remaining",
    "decisions",
    "repository_state",
    "validation_state",
    "risks",
    "next_action",
  ], "Handoff context");
  return Object.freeze({
    objective: compactText(value.objective, "Objective"),
    completed: compactList(value.completed, "Completed work"),
    remaining: compactList(value.remaining, "Remaining work"),
    decisions: compactList(value.decisions, "Important decisions"),
    repository_state: compactText(value.repository_state, "Repository state"),
    validation_state: compactText(value.validation_state, "Validation state"),
    risks: compactList(value.risks, "Risks"),
    next_action: compactText(value.next_action, "Immediate next action"),
  });
}

function listSection(title, values) {
  return [`## ${title}`, "", ...(values.length === 0 ? ["- None reported."] : values.map((value) => `- ${value}`))];
}

export function renderHandoffText(context) {
  const lines = [
    "# Clean Handoff",
    "",
    "## Objective",
    "",
    context.objective,
    "",
    ...listSection("Completed work", context.completed),
    "",
    ...listSection("Remaining work", context.remaining),
    "",
    ...listSection("Important decisions", context.decisions),
    "",
    "## Repository state",
    "",
    context.repository_state,
    "",
    "## Validation state",
    "",
    context.validation_state,
    "",
    ...listSection("Risks", context.risks),
    "",
    "## Immediate next action",
    "",
    context.next_action,
    "",
    "## Destination requirements",
    "",
    "- Inspect the live repository before continuing.",
    "- Read the live canonical `GAMEPLAN.md` before any mutation.",
    "- Treat this handoff as context only; it carries no approval.",
    "- If identity, authority, or live state is uncertain, stop for confirmation.",
  ];
  const text = `${lines.join("\n")}\n`;
  if (Buffer.byteLength(text, "utf8") > HANDOFF_PROMPT_BYTES) {
    throw new SafeFailure("handoff-too-large", "The compact handoff exceeds the permitted output size.");
  }
  return text;
}

export async function prepareMinimalHandoff(projectRoot, input) {
  assertExactKeys(input, ["schema", "mode", "projects", "handoff"], "Prepare input");
  if (input.schema !== HANDOFF_INPUT_SCHEMA || !MODES.has(input.mode)) {
    throw new SafeFailure("invalid-input", "The handoff input schema or mode is unsupported.");
  }
  const context = normalizeContext(input.handoff);
  let projectSelection = null;
  if (input.mode === "direct") {
    projectSelection = await selectExactProject(projectRoot, input.projects);
    if (projectSelection.state !== "exact") {
      throw new SafeFailure(
        projectSelection.state === "ambiguous" ? "project-ambiguous" : "project-unavailable",
        "Direct Handoff requires exactly one matching saved local project.",
      );
    }
  } else if (input.projects !== null) {
    throw new SafeFailure("invalid-input", "Portable Handoff requires projects to be null.");
  }

  return Object.freeze({
    schema: HANDOFF_OUTPUT_SCHEMA,
    mode: input.mode,
    project_selection: projectSelection,
    handoff_text: renderHandoffText(context),
    task_tool: Object.freeze({
      permitted_calls: input.mode === "direct" ? 1 : 0,
      automatic_retry: false,
    }),
    storage_written: false,
    authority: "context-only",
  });
}
