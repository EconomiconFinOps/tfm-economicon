import { readFile } from "node:fs/promises";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { beforeAll, describe, expect, it } from "vitest";

import { findRepoRoot } from "../src/repo.js";

let root: string;
beforeAll(async () => { root = await findRepoRoot(); });

describe("public command schemas", () => {
  it("compile as Draft 2020-12 and validate normalized envelopes", async () => {
    const ajv = new Ajv2020({ allErrors: true, strict: true });
    addFormats(ajv);
    const input = ajv.compile(JSON.parse(await readFile(path.join(root, ".sdd/schemas/command-input.schema.json"), "utf8")));
    const output = ajv.compile(JSON.parse(await readFile(path.join(root, ".sdd/schemas/command-output.schema.json"), "utf8")));
    expect(input({ command: "status", format: "json", story: "HU-001" })).toBe(true);
    expect(input({ command: "status", format: "json", story: "HU-001", unknown: true })).toBe(false);
    expect(output({ ok: false, changed: false, blockers: [{ code: "WF-X", instance_path: "/", message: "blocked" }], next_actions: [] })).toBe(true);
  });
});
