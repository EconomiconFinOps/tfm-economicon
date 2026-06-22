import { HarnessInputError } from "../errors.js";
import { canonicalJson, sha256Text } from "../hash.js";
import { assertRepoPath } from "../repo.js";
import { lstat, realpath } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import type { AnyRecord } from "../types.js";
import type { AgentPolicy } from "./catalog.js";

export interface PermissionProfile extends AnyRecord {
  schema_version: "1.0.0";
  profile: "sdd-agent";
  read_root: true;
  write_paths: string[];
  read_only_paths: string[];
  deny_paths: string[];
  network: false;
}
export interface PermissionAnchor { path: string; realpath: string; dev: number; ino: number }
export interface CompiledPermissions { profile: PermissionProfile; sha256: string; toml: string; anchors: PermissionAnchor[] }

export async function compilePermissions(root: string, storyId: string, runPrefix: string, skill: string, policy: AgentPolicy, scope: AnyRecord): Promise<CompiledPermissions> {
  const writePaths = [`${runPrefix}/output.json`, `${runPrefix}/receipt.json`, `${runPrefix}/artifacts`];
  const anchors: PermissionAnchor[] = [];
  if (existsSync(path.join(root, ...`${runPrefix}/artifacts`.split("/")))) anchors.push(await inspectPermissionRoot(root, `${runPrefix}/artifacts`, true));
  if (policy.may_modify_product_code) for (const item of scope.write_paths ?? []) {
    const normalized = permissionPath(item); writePaths.push(normalized);
    anchors.push(await inspectPermissionRoot(root, normalized, item.endsWith("/**")));
  }
  const storyRoot = storyId === "HU-000" ? `SPEC/examples/${storyId}-fixture` : `SPEC/${storyId}`;
  const readOnly = [".git", ".codex", ".agents", `.agents/skills/${skill}`, ".sdd", "docs/ARCHITECTURE.md", "docs/SDD-WORKFLOW.md", "docs/architecture-status.md", `${storyRoot}/manifest.yaml`, `${storyRoot}/journal.ndjson`, `${storyRoot}/history`];
  const profile: PermissionProfile = { schema_version: "1.0.0", profile: "sdd-agent", read_root: true, write_paths: unique(writePaths), read_only_paths: unique(readOnly), deny_paths: [".agents/skills", ".env", "**/.env", "**/*.env", "**/credentials*", "**/*secret*"], network: false };
  const entries = ['"."="read"', ...profile.write_paths.map((item) => `${quote(item)}="write"`), ...profile.read_only_paths.map((item) => `${quote(item)}="read"`), ...profile.deny_paths.map((item) => `${quote(item)}="deny"`)];
  return { profile, sha256: sha256Text(canonicalJson(profile)), toml: `{":minimal"="read",":workspace_roots"={${entries.join(",")}}}`, anchors };
}

export async function verifyPermissionAnchors(root: string, anchors: PermissionAnchor[]): Promise<void> {
  for (const expected of anchors) {
    const absolute = path.join(root, ...expected.path.split("/"));
    const value = await lstat(absolute);
    if (value.isSymbolicLink() || await realpath(absolute) !== expected.realpath || value.dev !== expected.dev || value.ino !== expected.ino) throw new HarnessInputError("SDD-AGENT-SCOPE-CHANGED", `Permission root changed during execution: ${expected.path}`);
  }
}

function permissionPath(value: string): string {
  assertRepoPath(value);
  if (/[?\[\]]/.test(value) || (value.includes("*") && !value.endsWith("/**")) || value.slice(0, -3).includes("*")) throw new HarnessInputError("SDD-AGENT-SCOPE-UNENFORCEABLE", `Scope cannot be represented by filesystem permissions: ${value}`);
  const normalized = value.endsWith("/**") ? value.slice(0, -3) : value;
  const protectedRoots = ["SPEC", ".sdd", ".codex", ".agents", ".git"];
  const protectedFiles = ["docs/ARCHITECTURE.md", "docs/SDD-WORKFLOW.md", "docs/architecture-status.md"];
  if (!normalized || normalized === "." || protectedRoots.some((item) => normalized === item || normalized.startsWith(`${item}/`)) || protectedFiles.includes(normalized)) throw new HarnessInputError("SDD-AGENT-SCOPE-UNENFORCEABLE", `Protected or broad scope: ${value}`);
  return normalized.replace(/\/$/, "");
}
async function inspectPermissionRoot(root: string, normalized: string, directoryPattern: boolean): Promise<PermissionAnchor> {
  const parts = normalized.split("/"); let nearest = root; let nearestRelative = ".";
  for (let index = 0; index < parts.length; index += 1) {
    const candidate = path.join(root, ...parts.slice(0, index + 1));
    try {
      const value = await lstat(candidate);
      if (value.isSymbolicLink()) throw new HarnessInputError("SDD-AGENT-SCOPE-SYMLINK", `Symlink scope component is forbidden: ${parts.slice(0, index + 1).join("/")}`);
      nearest = candidate; nearestRelative = parts.slice(0, index + 1).join("/");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
      if (index < parts.length - 1 || directoryPattern) throw new HarnessInputError("SDD-AGENT-SCOPE-MISSING", `Permission root does not exist: ${normalized}`);
      break;
    }
  }
  const resolvedRoot = await realpath(root); const resolved = await realpath(nearest);
  if (resolved !== resolvedRoot && !resolved.startsWith(`${resolvedRoot}${path.sep}`)) throw new HarnessInputError("SDD-AGENT-SCOPE-ESCAPE", `Permission root escapes the repository: ${normalized}`);
  const value = await lstat(nearest);
  return { path: nearestRelative, realpath: resolved, dev: value.dev, ino: value.ino };
}
function unique(values: string[]): string[] { return [...new Set(values)].sort((a, b) => a < b ? -1 : a > b ? 1 : 0); }
function quote(value: string): string { return JSON.stringify(value); }
