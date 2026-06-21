import { spawn } from "node:child_process";
import { cp, mkdir, mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeAll, describe, expect, it } from "vitest";

import { findRepoRoot } from "../src/repo.js";

let repositoryRoot: string;
const temporary: string[] = [];
beforeAll(async () => { repositoryRoot = await findRepoRoot(); });
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("public CLI process", () => {
  it("supports JSON/text and stable exit codes 0/1/2", async () => {
    const valid = await invoke(repositoryRoot, ["validate", "--story", "HU-000"]);
    expect(valid.code).toBe(0);
    expect(JSON.parse(valid.stdout)).toMatchObject({ ok: true, story_id: "HU-000" });
    const text = await invoke(repositoryRoot, ["validate", "--story", "HU-000", "--format", "text"]);
    expect(text.code).toBe(0);
    expect(text.stdout).toMatch(/^OK HU-000/);
    const usage = await invoke(repositoryRoot, ["status", "--story", "HU-000", "--unknown", "x"]);
    expect(usage.code).toBe(2);
    expect(JSON.parse(usage.stderr).blockers[0].code).toBe("SDD-ARGUMENT");

    const root = await temporaryRepository();
    expect((await invoke(root, ["init", "--title", "Blocked", "--change-type", "harness-docs"])).code).toBe(0);
    const blocked = await invoke(root, ["next", "--story", "HU-001"]);
    expect(blocked.code).toBe(1);
    expect(JSON.parse(blocked.stdout).ok).toBe(false);
  });

  it("validates catalog contracts through the public process", async () => {
    const valid = await invoke(repositoryRoot, ["contract", "validate", "--schema", "skill/common-input@1.0.0", "--input", ".sdd/fixtures/contracts/common-input.valid.yaml"]);
    expect(valid.code).toBe(0);
    expect(JSON.parse(valid.stdout)).toMatchObject({ ok: true, command: "contract validate" });
    const invalid = await invoke(repositoryRoot, ["contract", "validate", "--schema", "skill/common-input@1.0.0", "--input", ".sdd/fixtures/contracts/common-input.invalid.yaml", "--format", "text"]);
    expect(invalid.code).toBe(1);
    expect(invalid.stdout).toContain("SDD-CONTRACT-SCHEMA");
    const unknown = await invoke(repositoryRoot, ["contract", "validate", "--schema", "unknown@1.0.0", "--input", ".sdd/fixtures/contracts/common-input.valid.yaml"]);
    expect(unknown.code).toBe(2);
  });
});

async function invoke(cwd: string, args: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
  const cli = path.resolve(fileURLToPath(new URL("../src/cli/sdd.ts", import.meta.url)));
  const tsx = path.resolve(fileURLToPath(new URL("../node_modules/tsx/dist/cli.mjs", import.meta.url)));
  const { VITEST: ignored, ...env } = process.env;
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [tsx, cli, ...args], { cwd, env });
    let stdout = ""; let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code: code ?? -1, stdout, stderr }));
  });
}

async function temporaryRepository(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), "sdd-process-"));
  temporary.push(root);
  await cp(path.join(repositoryRoot, ".sdd"), path.join(root, ".sdd"), { recursive: true });
  await mkdir(path.join(root, "docs"), { recursive: true });
  for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) {
    await cp(path.join(repositoryRoot, "docs", name), path.join(root, "docs", name));
  }
  return root;
}
