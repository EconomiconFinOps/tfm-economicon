import { access } from "node:fs/promises";
import path from "node:path";

import { HarnessInputError } from "./errors.js";

export async function findRepoRoot(start = process.cwd()): Promise<string> {
  let current = path.resolve(start);
  while (true) {
    try {
      await access(path.join(current, ".sdd", "config.yaml"));
      return current;
    } catch {
      const parent = path.dirname(current);
      if (parent === current) {
        throw new HarnessInputError("SDD-ROOT-NOT-FOUND", "Cannot locate repository root containing .sdd/config.yaml");
      }
      current = parent;
    }
  }
}

export function resolveConcreteRepoPath(root: string, value: string): string {
  assertRepoPath(value);
  const resolved = path.resolve(root, ...value.split("/"));
  const relative = path.relative(root, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new HarnessInputError("SDD-PATH-OUTSIDE-ROOT", `Path escapes repository: ${value}`);
  }
  return resolved;
}

export function assertRepoPath(value: string): void {
  if (!value || value.includes("\\") || path.isAbsolute(value) || /^[A-Za-z]:/.test(value)) {
    throw new HarnessInputError("SDD-PATH-INVALID", `Path must be repository-relative with forward slashes: ${value}`);
  }
  if (value.split("/").includes("..")) {
    throw new HarnessInputError("SDD-PATH-TRAVERSAL", `Path traversal is forbidden: ${value}`);
  }
}

