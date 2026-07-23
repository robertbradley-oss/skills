import fs from "node:fs";
import { promises as fsp } from "node:fs";
import path from "node:path";

import { SafeFailure } from "./errors.mjs";

const DEFAULT_MAXIMUM_BYTES = 512 * 1024;

export function isInside(parentPath, childPath) {
  const relative = path.relative(path.resolve(parentPath), path.resolve(childPath));
  return relative === ""
    || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

export function sameFilesystemPath(left, right) {
  const normalize = (value) => {
    const resolved = path.normalize(path.resolve(value));
    return process.platform === "win32" ? resolved.toLowerCase() : resolved;
  };
  return normalize(left) === normalize(right);
}

export function fileIdentity(stats) {
  if (!stats) return null;
  return Object.freeze({
    dev: String(stats.dev),
    ino: String(stats.ino),
    mode: String(stats.mode),
    size: String(stats.size),
    mtimeNs: String(stats.mtimeNs),
    birthtimeNs: String(stats.birthtimeNs),
  });
}

export function sameFileIdentity(left, right) {
  if (!left || !right) return false;
  const first = fileIdentity(left);
  const second = fileIdentity(right);
  const inodeKnown = first.ino !== "0" && second.ino !== "0";
  return first.dev === second.dev
    && (!inodeKnown || first.ino === second.ino)
    && first.mode === second.mode
    && first.size === second.size
    && first.mtimeNs === second.mtimeNs
    && first.birthtimeNs === second.birthtimeNs;
}

export async function reparsePointState(logicalPath, knownStats = null) {
  let stats = knownStats;
  try {
    stats ??= await fsp.lstat(logicalPath, { bigint: true });
  } catch {
    return "unknown";
  }
  if (stats.isSymbolicLink()) return "name-surrogate";
  return stats.isDirectory() || stats.isFile() ? "clear" : "reparse";
}

export async function resolveOrdinaryDirectory(logicalPath, options = {}) {
  if (typeof logicalPath !== "string" || !path.isAbsolute(logicalPath)) {
    throw new SafeFailure("unsafe-directory", "The directory path must be absolute.");
  }
  let entry;
  try {
    entry = await fsp.lstat(logicalPath, { bigint: true });
  } catch {
    throw new SafeFailure("directory-unavailable", "The directory boundary could not be inspected.");
  }
  if (!entry.isDirectory() || entry.isSymbolicLink() || await reparsePointState(logicalPath, entry) !== "clear") {
    throw new SafeFailure("unsafe-directory", "The directory boundary is redirected or is not an ordinary directory.");
  }
  let resolved;
  try {
    resolved = await fsp.realpath(logicalPath);
  } catch {
    throw new SafeFailure("directory-unavailable", "The directory boundary could not be resolved.");
  }
  if (options.requireSamePath !== false && !sameFilesystemPath(logicalPath, resolved)) {
    throw new SafeFailure("unsafe-directory", "The directory boundary resolves through another filesystem path.");
  }
  if (options.containmentRoot && !isInside(options.containmentRoot, resolved)) {
    throw new SafeFailure("path-escape", "The resolved directory escapes its containment boundary.");
  }
  return resolved;
}

function assertSafeSegment(segment) {
  if (typeof segment !== "string"
    || segment.length === 0
    || segment === "."
    || segment === ".."
    || segment.includes("/")
    || segment.includes("\\")
    || /[\u0000-\u001f\u007f]/u.test(segment)) {
    throw new SafeFailure("unsafe-path-segment", "A storage path segment is invalid.");
  }
}

export async function inspectOrdinaryDirectoryChain(rootPath, segments) {
  if (!Array.isArray(segments)) throw new SafeFailure("unsafe-path-segment", "Storage path segments are required.");
  const root = await resolveOrdinaryDirectory(rootPath);
  let current = root;
  let boundaryState = "existing";
  let existingDepth = 0;

  for (const segment of segments) {
    assertSafeSegment(segment);
    const candidate = path.join(current, segment);
    let entry;
    try {
      entry = await fsp.lstat(candidate, { bigint: true });
    } catch (error) {
      if (error?.code !== "ENOENT") {
        throw new SafeFailure("directory-unavailable", "A directory candidate could not be inspected.");
      }
      boundaryState = "missing";
      break;
    }
    if (!entry.isDirectory() || entry.isSymbolicLink() || await reparsePointState(candidate, entry) !== "clear") {
      throw new SafeFailure("unsafe-directory", "A directory candidate is redirected or is not an ordinary directory.");
    }
    const resolved = await fsp.realpath(candidate).catch(() => null);
    if (resolved === null || !sameFilesystemPath(candidate, resolved) || !isInside(root, resolved)) {
      throw new SafeFailure("unsafe-directory", "A directory candidate resolves through another filesystem path.");
    }
    current = resolved;
    existingDepth += 1;
  }

  return Object.freeze({
    root,
    targetPath: path.join(root, ...segments),
    lastExistingDirectory: current,
    existingDepth,
    boundaryState,
  });
}

export async function readStableRegularFile(filePath, options = {}) {
  const maximum = options.maxBytes ?? DEFAULT_MAXIMUM_BYTES;
  if (!Number.isSafeInteger(maximum) || maximum < 0) {
    throw new SafeFailure("invalid-read-limit", "The file read limit is invalid.");
  }
  const target = path.resolve(filePath);
  const containingDirectory = await resolveOrdinaryDirectory(
    options.containingDirectory ?? path.dirname(target),
  );
  if (!isInside(containingDirectory, target) || sameFilesystemPath(containingDirectory, target)) {
    throw new SafeFailure("path-escape", "The file escapes its containing directory.");
  }

  let before;
  try {
    before = await fsp.lstat(target, { bigint: true });
  } catch (error) {
    throw new SafeFailure(
      error?.code === "ENOENT" ? "file-missing" : "file-unavailable",
      error?.code === "ENOENT" ? "The file does not exist." : "The file could not be inspected.",
    );
  }
  if (!before.isFile() || before.isSymbolicLink() || await reparsePointState(target, before) !== "clear") {
    throw new SafeFailure("unsafe-file", "The file is redirected or is not an ordinary file.");
  }
  if (before.size > BigInt(maximum)) throw new SafeFailure("file-too-large", "The file exceeds the permitted size.");

  let beforeReal;
  try {
    beforeReal = await fsp.realpath(target);
  } catch {
    throw new SafeFailure("file-unavailable", "The file could not be resolved.");
  }
  if (!sameFilesystemPath(target, beforeReal) || !isInside(containingDirectory, beforeReal)) {
    throw new SafeFailure("unsafe-file", "The file resolves through another filesystem path.");
  }

  let handle;
  try {
    handle = await fsp.open(target, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0));
    const opened = await handle.stat({ bigint: true });
    if (!opened.isFile() || !sameFileIdentity(before, opened)) {
      throw new SafeFailure("concurrent-file-change", "The file changed while it was opened.");
    }

    const chunks = [];
    let total = 0;
    let position = 0;
    while (true) {
      const remaining = maximum + 1 - total;
      const buffer = Buffer.allocUnsafe(Math.max(1, Math.min(64 * 1024, remaining)));
      const { bytesRead } = await handle.read(buffer, 0, buffer.length, position);
      if (bytesRead === 0) break;
      chunks.push(buffer.subarray(0, bytesRead));
      total += bytesRead;
      position += bytesRead;
      if (total > maximum) throw new SafeFailure("file-too-large", "The file exceeds the permitted size.");
    }
    const afterOpen = await handle.stat({ bigint: true });
    if (!sameFileIdentity(opened, afterOpen) || BigInt(total) !== afterOpen.size) {
      throw new SafeFailure("concurrent-file-change", "The file changed while it was read.");
    }
    const bytes = Buffer.concat(chunks);
    await handle.close();
    handle = null;

    if (options.onBeforeFinalCheck !== undefined) {
      if (typeof options.onBeforeFinalCheck !== "function") {
        throw new SafeFailure("invalid-read-hook", "The final file-check hook is invalid.");
      }
      await options.onBeforeFinalCheck();
    }

    const after = await fsp.lstat(target, { bigint: true });
    const afterReal = await fsp.realpath(target);
    if (after.isSymbolicLink()
      || !sameFileIdentity(before, after)
      || !sameFilesystemPath(beforeReal, afterReal)
      || !isInside(containingDirectory, afterReal)) {
      throw new SafeFailure("concurrent-file-change", "The file changed before validation completed.");
    }
    return Object.freeze({ bytes, identity: fileIdentity(after) });
  } catch (error) {
    if (error instanceof SafeFailure) throw error;
    throw new SafeFailure("unsafe-file", "The file could not be read safely.");
  } finally {
    if (handle) {
      try { await handle.close(); } catch { /* read-only cleanup */ }
    }
  }
}
