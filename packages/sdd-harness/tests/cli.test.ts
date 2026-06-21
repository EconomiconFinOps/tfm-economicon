import { cp, mkdir, mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeAll, describe, expect, it } from "vitest";

import { executeCli } from "../src/cli/sdd.js";
import { findRepoRoot } from "../src/repo.js";

const temporary: string[] = [];
let repositoryRoot: string;
beforeAll(async () => { repositoryRoot = await findRepoRoot(); });
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("CLI contract", () => {
  it("returns a stable command envelope and honors text format", async () => {
    const root = await temporaryRepository();
    const execution = await executeCli(root, ["init", "--title", "CLI story", "--change-type", "harness-docs", "--format", "text"]);
    expect(execution.format).toBe("text");
    expect(execution.result).toMatchObject({ ok: true, command: "init", story_id: "HU-001", changed: true, stage: "INTAKE", status: "ACTIVE", blockers: [] });
  });

  it("classifies missing required options as input errors", async () => {
    const root = await temporaryRepository();
    await expect(executeCli(root, ["init", "--title", "Incomplete"])).rejects.toMatchObject({ code: "SDD-ARGUMENT" });
  });

  it.each([
    [["status", "--story", "HU-001", "--unknown", "x"], "SDD-ARGUMENT"],
    [["status", "--story", "HU-001", "--story", "HU-002"], "SDD-ARGUMENT"],
    [["init", "--title", "x", "--change-type", "invalid"], "SDD-ARGUMENT"],
    [["run", "--story", "HU-001", "--check", "TEST-001", "--exit-code", "1.5", "--evidence", "result.txt"], "SDD-ARGUMENT"],
  ])("rejects malformed public input %#", async (args, code) => {
    await expect(executeCli(process.cwd(), args)).rejects.toMatchObject({ code });
  });
});

async function temporaryRepository(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), "sdd-cli-"));
  temporary.push(root);
  await cp(path.join(repositoryRoot, ".sdd"), path.join(root, ".sdd"), { recursive: true });
  await mkdir(path.join(root, "docs"), { recursive: true });
  for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) await cp(path.join(repositoryRoot, "docs", name), path.join(root, "docs", name));
  return root;
}
