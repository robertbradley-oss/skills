import assert from "node:assert/strict";
import { promises as fsp } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  inspectOrdinaryDirectoryChain,
  isInside,
  readStableRegularFile,
  reparsePointState,
  resolveOrdinaryDirectory,
  sameFilesystemPath,
} from "../scripts/internal/fs-safety.mjs";

async function fixture(t) {
  const root = await fsp.realpath(await fsp.mkdtemp(path.join(tmpdir(), "clean-handoff-d1-fs-")));
  const tempRoot = await fsp.realpath(tmpdir());
  assert.equal(isInside(tempRoot, root), true);
  t.after(async () => {
    assert.equal(isInside(tempRoot, root), true);
    await fsp.rm(root, { recursive: true, force: true });
  });
  return root;
}

test("path comparison and containment are platform-correct", async (t) => {
  const root = await fixture(t);
  const child = path.join(root, "child");
  const sibling = path.join(path.dirname(root), `${path.basename(root)}-sibling`);
  assert.equal(isInside(root, root), true);
  assert.equal(isInside(root, child), true);
  assert.equal(isInside(root, sibling), false);
  assert.equal(sameFilesystemPath(root, path.join(root, ".")), true);
});

test("ordinary directory chains stop safely at the first missing segment", async (t) => {
  const root = await fixture(t);
  await fsp.mkdir(path.join(root, "existing"));
  assert.equal(await resolveOrdinaryDirectory(root), await fsp.realpath(root));
  const chain = await inspectOrdinaryDirectoryChain(root, ["existing", "missing", "later"]);
  assert.equal(chain.boundaryState, "missing");
  assert.equal(chain.existingDepth, 1);
  assert.equal(chain.lastExistingDirectory, await fsp.realpath(path.join(root, "existing")));
  assert.equal(chain.targetPath, path.join(await fsp.realpath(root), "existing", "missing", "later"));
});

test("stable reads enforce size, identity, and final-change checks", async (t) => {
  const root = await fixture(t);
  const file = path.join(root, "evidence.txt");
  await fsp.writeFile(file, "stable", "utf8");
  const read = await readStableRegularFile(file, { containingDirectory: root, maxBytes: 64 });
  assert.equal(read.bytes.toString("utf8"), "stable");
  assert.equal(typeof read.identity.size, "string");

  await assert.rejects(
    readStableRegularFile(file, { containingDirectory: root, maxBytes: 2 }),
    (error) => error.code === "file-too-large",
  );

  await assert.rejects(
    readStableRegularFile(file, {
      containingDirectory: root,
      maxBytes: 64,
      onBeforeFinalCheck: async () => fsp.writeFile(file, "changed-content", "utf8"),
    }),
    (error) => error.code === "concurrent-file-change",
  );
});

test("symbolic-link and junction boundaries are rejected when the platform supports them", async (t) => {
  const root = await fixture(t);
  const targetDirectory = path.join(root, "target-dir");
  const targetFile = path.join(root, "target.txt");
  await fsp.mkdir(targetDirectory);
  await fsp.writeFile(targetFile, "secret", "utf8");

  const fileLink = path.join(root, "file-link");
  try {
    await fsp.symlink(targetFile, fileLink, "file");
  } catch (error) {
    if (["EPERM", "EACCES", "UNKNOWN"].includes(error?.code)) {
      t.skip("File-link creation is unavailable on this platform.");
      return;
    }
    throw error;
  }
  assert.equal(await reparsePointState(fileLink), "name-surrogate");
  await assert.rejects(
    readStableRegularFile(fileLink, { containingDirectory: root }),
    (error) => error.code === "unsafe-file",
  );

  const directoryLink = path.join(root, "directory-link");
  await fsp.symlink(targetDirectory, directoryLink, process.platform === "win32" ? "junction" : "dir");
  await assert.rejects(resolveOrdinaryDirectory(directoryLink), (error) => error.code === "unsafe-directory");
});
