import { execFile } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

import { captureBaseline, validateScope } from "../src/orchestrator/scope.js";

const exec = promisify(execFile);
const temporary: string[] = [];
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("execution scope", () => {
  it("allows declared paths and blocks other changes relative to the baseline", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-scope-"));
    temporary.push(root);
    await exec("git", ["init"], { cwd: root });
    await mkdir(path.join(root, "apps"), { recursive: true });
    await writeFile(path.join(root, "apps/allowed.ts"), "before", "utf8");
    await writeFile(path.join(root, "blocked.txt"), "before", "utf8");
    const captured = await captureBaseline(root, "HU-001");
    await mkdir(path.join(root, "SPEC/HU-001/.harness"), { recursive: true });
    await writeFile(path.join(root, captured.path), captured.content, "utf8");
    await writeFile(path.join(root, "apps/allowed.ts"), "after", "utf8");
    await writeFile(path.join(root, "blocked.txt"), "after", "utf8");
    const issues = await validateScope(root, { story: { id: "HU-001" }, scope: { write_paths: ["apps/**"] }, execution: { baseline: { path: captured.path, sha256: captured.sha256 } } });
    expect(issues).toEqual([{ code: "WF-OUT-OF-SCOPE", instance_path: "/scope/write_paths", message: "Changed path is outside approved scope: blocked.txt" }]);
  });
});
