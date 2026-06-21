import path from "node:path";

import { HarnessInputError } from "../errors.js";

export function assertStoryId(storyId: string): void {
  if (!/^HU-[0-9]{3,}$/.test(storyId)) {
    throw new HarnessInputError("SDD-STORY-ID", `Invalid story ID: ${storyId}`);
  }
}

export function storyDirectory(root: string, storyId: string): string {
  assertStoryId(storyId);
  if (storyId === "HU-000") return path.join(root, "SPEC", "examples", "HU-000-fixture");
  return path.join(root, "SPEC", storyId);
}

export function storyManifestPath(root: string, storyId: string): string {
  return path.join(storyDirectory(root, storyId), "manifest.yaml");
}

export function relativeRepoPath(root: string, absolute: string): string {
  return path.relative(root, absolute).replaceAll("\\", "/");
}
