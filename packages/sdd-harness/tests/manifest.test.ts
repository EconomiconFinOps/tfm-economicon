import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";

import { validateManifest } from "../src/manifest/validate.js";
import { HarnessInputError } from "../src/errors.js";
import { findRepoRoot } from "../src/repo.js";

let root: string;
const temporaryDirectories: string[] = [];

beforeAll(async () => {
  root = await findRepoRoot();
});

afterEach(async () => {
  await Promise.all(temporaryDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

describe("manifest validation", () => {
  it("accepts the isolated HU-000 fixture", async () => {
    const report = await validateManifest(root, "SPEC/examples/HU-000-fixture/manifest.yaml");
    expect(report).toMatchObject({ valid: true, story_id: "HU-000", errors: [] });
  });

  it("rejects unknown schema properties", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.unknown = true;
    });
    const report = await validateManifest(root, path);
    expect(report.valid).toBe(false);
    expect(report.errors.some((error) => error.code === "SDD-MANIFEST-SCHEMA")).toBe(true);
  });

  it("classifies unsupported manifest versions as input errors", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.schema_version = "1.1.0";
    });
    await expect(validateManifest(root, path)).rejects.toMatchObject({ code: "SDD-MANIFEST-VERSION" });
  });

  it("rejects unsafe repository paths", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.scope.read_paths = ["../outside"];
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-MANIFEST-SCHEMA" }));
  });

  it("rejects harness-docs with runtime changes", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.story.runtime_changes = true;
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-HARNESS-RUNTIME" }));
  });

  it("rejects remediation without target gaps", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.story.change_type = "remediation";
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-REMEDIATION-GAPS" }));
  });

  it("rejects an artifact with a stale hash", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.artifacts[0].sha256 = "a".repeat(64);
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-ARTIFACT-HASH" }));
  });

  it("rejects approvals created by an agent", async () => {
    const path = await mutatedManifest((manifest) => {
      const artifact = manifest.artifacts[0];
      artifact.status = "APPROVED";
      artifact.approvals = [
        {
          decision: "APPROVED",
          artifact_version: artifact.version,
          artifact_sha256: artifact.sha256,
          approver: { actor_type: "agent", identity: "review-agent" },
          decided_at: "2026-06-20T09:00:00Z",
          comment: null,
        },
      ];
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-MANIFEST-SCHEMA" }));
  });

  it("rejects checks whose status and result disagree", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.checks = [
        {
          id: "TEST-001",
          name: "invalid result",
          command: "test",
          cwd: ".",
          status: "COMPLETED",
          result: {
            id: "RESULT-001",
            exit_code: 1,
            started_at: "2026-06-20T09:00:00Z",
            completed_at: "2026-06-20T09:00:01Z",
            evidence_path: "SPEC/examples/HU-000-fixture/journal.ndjson",
          },
        },
      ];
      manifest.traceability.entities.push(
        { id: "TEST-001", type: "TEST", artifact_path: null },
        { id: "RESULT-001", type: "RESULT", artifact_path: "SPEC/examples/HU-000-fixture/journal.ndjson" },
      );
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-CHECK-EXIT" }));
  });

  it("rejects unknown architecture references", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.architecture.invariants.push("ARCH-99");
      manifest.traceability.entities.push({ id: "ARCH-99", type: "ARCH", artifact_path: "docs/ARCHITECTURE.md" });
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-ARCH-UNKNOWN" }));
  });

  it("rejects broken traceability", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.traceability.relations[0].to = "REQ-999";
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-TRACE-RELATION-BROKEN" }));
  });

  it("rejects unknown and cyclic task dependencies", async () => {
    const path = await mutatedManifest((manifest) => {
      manifest.tasks = [
        {
          id: "TASK-001",
          path: "SPEC/examples/HU-000-fixture/user-story.md",
          status: "PENDING",
          depends_on: ["TASK-002"],
          required_checks: [],
          attempts: [],
        },
        {
          id: "TASK-002",
          path: "SPEC/examples/HU-000-fixture/user-story.md",
          status: "PENDING",
          depends_on: ["TASK-001"],
          required_checks: [],
          attempts: [],
        },
      ];
      manifest.traceability.entities.push(
        { id: "TASK-001", type: "TASK", artifact_path: "SPEC/examples/HU-000-fixture/user-story.md" },
        { id: "TASK-002", type: "TASK", artifact_path: "SPEC/examples/HU-000-fixture/user-story.md" },
      );
    });
    const report = await validateManifest(root, path);
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-TASK-CYCLE" }));
  });

  it("accepts a finding with evidence and explicit architecture traceability", async () => {
    const path = await mutatedManifest((manifest) => addFinding(manifest));
    expect(await validateManifest(root, path)).toMatchObject({ valid: true });
  });

  it("rejects findings without evidence, resolution or traceability", async () => {
    const withoutEvidence = await mutatedManifest((manifest) => { addFinding(manifest); manifest.findings[0].evidence = []; manifest.traceability.relations = manifest.traceability.relations.filter((item: any) => item.from !== "FIND-001"); });
    const first = await validateManifest(root, withoutEvidence);
    expect(first.errors).toContainEqual(expect.objectContaining({ code: "SDD-MANIFEST-SCHEMA" }));
    const withoutResolution = await mutatedManifest((manifest) => { addFinding(manifest); manifest.findings[0].status = "RESOLVED"; });
    expect((await validateManifest(root, withoutResolution)).errors).toContainEqual(expect.objectContaining({ code: "SDD-MANIFEST-SCHEMA" }));
  });
});

function addFinding(manifest: any): void {
  manifest.findings.push({
    id: "FIND-001", summary: "Architecture evidence missing", severity: "BLOCKING", status: "OPEN",
    cause: "design_or_architecture", requirement_ids: [], task_ids: [], invariant_ids: ["ARCH-07"],
    evidence: [{ path: "SPEC/examples/HU-000-fixture/user-story.md", sha256: "b634acdd465d0d4b23576644aa65588bfe5e4df99fb32e2ada7d963dc9c4af08" }], resolution: null,
  });
  manifest.traceability.entities.push({ id: "FIND-001", type: "FIND", artifact_path: "SPEC/examples/HU-000-fixture/user-story.md" });
  manifest.traceability.relations.push({ from: "FIND-001", to: "ARCH-07", type: "finds" });
}

async function mutatedManifest(mutate: (manifest: any) => void): Promise<string> {
  const source = await readFile(path.join(root, "SPEC/examples/HU-000-fixture/manifest.yaml"), "utf8");
  const manifest = parse(source);
  mutate(manifest);
  const directory = await mkdtemp(path.join(root, "SPEC/examples/HU-000-test-"));
  temporaryDirectories.push(directory);
  const target = path.join(directory, "manifest.yaml");
  await writeFile(target, stringify(manifest), "utf8");
  return target;
}
