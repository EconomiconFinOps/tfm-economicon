import { HarnessInputError } from "../errors.js";
import { canonicalJson, sha256Text } from "../hash.js";
import { assertRepoPath } from "../repo.js";
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

export function compilePermissions(storyId: string, runPrefix: string, skill: string, policy: AgentPolicy, scope: AnyRecord): { profile: PermissionProfile; sha256: string; toml: string } {
  const writePaths = [`${runPrefix}/output.json`, `${runPrefix}/receipt.json`, `${runPrefix}/artifacts`];
  if (policy.may_modify_product_code) for (const item of scope.write_paths ?? []) writePaths.push(permissionPath(item));
  const storyRoot = storyId === "HU-000" ? `SPEC/examples/${storyId}-fixture` : `SPEC/${storyId}`;
  const readOnly = [".git", ".codex", ".agents", `.agents/skills/${skill}`, ".sdd", "docs/ARCHITECTURE.md", "docs/SDD-WORKFLOW.md", "docs/architecture-status.md", `${storyRoot}/manifest.yaml`, `${storyRoot}/journal.ndjson`, `${storyRoot}/history`];
  const profile: PermissionProfile = { schema_version: "1.0.0", profile: "sdd-agent", read_root: true, write_paths: unique(writePaths), read_only_paths: unique(readOnly), deny_paths: [".agents/skills", ".env", "**/.env", "**/*.env", "**/credentials*", "**/*secret*"], network: false };
  const entries = ['"."="read"', ...profile.write_paths.map((item) => `${quote(item)}="write"`), ...profile.read_only_paths.map((item) => `${quote(item)}="read"`), ...profile.deny_paths.map((item) => `${quote(item)}="deny"`)];
  return { profile, sha256: sha256Text(canonicalJson(profile)), toml: `{":minimal"="read",":workspace_roots"={${entries.join(",")}}}` };
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
function unique(values: string[]): string[] { return [...new Set(values)].sort((a, b) => a < b ? -1 : a > b ? 1 : 0); }
function quote(value: string): string { return JSON.stringify(value); }
