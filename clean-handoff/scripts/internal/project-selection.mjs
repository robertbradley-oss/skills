import path from "node:path";

import { assertExactKeys } from "./context-safety.mjs";
import { SafeFailure } from "./errors.mjs";
import { resolveOrdinaryDirectory, sameFilesystemPath } from "./fs-safety.mjs";

export const PROJECT_SELECTION_SCHEMA = "clean-handoff/project-selection/v1";

export function normalizeProjectList(value) {
  if (Array.isArray(value)) return value;
  assertExactKeys(value, ["schemaVersion", "projects"], "Saved-project list");
  if (value.schemaVersion !== 1 || !Array.isArray(value.projects)) {
    throw new SafeFailure("invalid-project-list", "The saved-project list envelope is unsupported.");
  }
  return value.projects;
}

async function candidateDirectory(value) {
  if (typeof value !== "string" || !path.isAbsolute(value)) return null;
  try {
    return await resolveOrdinaryDirectory(value, { requireSamePath: false });
  } catch {
    return null;
  }
}

export async function selectExactProject(projectRoot, projects) {
  const root = await resolveOrdinaryDirectory(projectRoot, { requireSamePath: false });
  const list = normalizeProjectList(projects);
  if (list.length > 10_000) throw new SafeFailure("project-list-too-large", "The saved-project list exceeds the supported bound.");
  const matches = [];
  for (let index = 0; index < list.length; index += 1) {
    const project = list[index];
    if (project === null
      || typeof project !== "object"
      || Array.isArray(project)
      || project.projectKind !== "local"
      || typeof project.projectId !== "string") continue;
    const resolved = await candidateDirectory(project.path);
    if (resolved !== null && sameFilesystemPath(root, resolved)) matches.push(index);
  }
  return Object.freeze({
    schema: PROJECT_SELECTION_SCHEMA,
    state: matches.length === 1 ? "exact" : matches.length === 0 ? "unavailable" : "ambiguous",
    match_index: matches.length === 1 ? matches[0] : null,
  });
}
