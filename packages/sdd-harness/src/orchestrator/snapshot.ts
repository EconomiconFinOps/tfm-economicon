import path from "node:path";

import { readText } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord } from "../types.js";
import type { ExtraWrite } from "./store.js";

export async function snapshotArtifact(root: string, storyId: string, artifact: AnyRecord): Promise<{ path: string; write: ExtraWrite }> {
  const basename = path.posix.basename(artifact.path);
  const snapshotPath = `SPEC/${storyId}/history/${artifact.type}/v${String(artifact.version).padStart(4, "0")}/${basename}`;
  return {
    path: snapshotPath,
    write: { path: snapshotPath, content: await readText(resolveConcreteRepoPath(root, artifact.path)), immutable: true },
  };
}
