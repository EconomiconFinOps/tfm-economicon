import { mkdtemp, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { readYaml } from "../src/io.js";

describe("YAML input", () => {
  it("classifies malformed YAML as an input error", async () => {
    const directory = await mkdtemp(path.join(os.tmpdir(), "sdd-yaml-"));
    const target = path.join(directory, "invalid.yaml");
    await writeFile(target, "root: [broken", "utf8");

    await expect(readYaml(target)).rejects.toMatchObject({ code: "SDD-YAML-ERROR" });
  });
});
