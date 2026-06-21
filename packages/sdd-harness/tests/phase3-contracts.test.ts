import { readFile } from "node:fs/promises";
import path from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { parse } from "yaml";

import { renderArtifactTemplate, validateArtifactContent } from "../src/contracts/artifact.js";
import { createCatalogValidator } from "../src/contracts/catalog.js";
import { loadSchemaCatalog } from "../src/contracts/catalog.js";
import { sha256Text } from "../src/hash.js";
import { findRepoRoot } from "../src/repo.js";

let root: string;
let matrix: { artifact_schemas: string[]; skill_schemas: string[]; directions: string[] };
beforeAll(async () => {
  root = await findRepoRoot();
  matrix = parse(await readFile(path.join(root, ".sdd/fixtures/contracts/cases.yaml"), "utf8"));
});

describe("Phase 3 artifact contracts", () => {
  it.each(["user-story", "prd", "tdr", "roadmap", "task", "execution-summary", "verification-evidence", "review"])("renders and validates %s", async (type) => {
    const content = await rendered(type);
    expect((await validateArtifactContent(root, content, type, "1.0.0", "HU-001")).issues).toEqual([]);
  });

  it("rejects missing front matter, unknown properties, wrong type and missing sections", async () => {
    const valid = await rendered("review");
    expect((await validateArtifactContent(root, valid.replace(/^---[\s\S]*?---\r?\n/, ""), "review", "1.0.0", "HU-001")).issues[0]?.code).toBe("SDD-ARTIFACT-FRONTMATTER");
    expect((await validateArtifactContent(root, valid.replace("story_id: HU-001", "story_id: HU-001\nunknown: true"), "review", "1.0.0", "HU-001")).issues).toContainEqual(expect.objectContaining({ code: "SDD-CONTRACT-SCHEMA" }));
    expect((await validateArtifactContent(root, valid.replace("artifact_type: review", "artifact_type: prd"), "review", "1.0.0", "HU-001")).issues).toContainEqual(expect.objectContaining({ code: "SDD-ARTIFACT-TYPE" }));
    expect((await validateArtifactContent(root, valid.replace(/## Veredicto[\s\S]*?(?=## Hallazgos)/, ""), "review", "1.0.0", "HU-001")).issues).toContainEqual(expect.objectContaining({ code: "SDD-CONTRACT-SCHEMA" }));
  });

  it("rejects unsafe aliases and stale documentation", async () => {
    const valid = await rendered("prd");
    const alias = valid.replace("architecture_invariants: [ARCH-01]", "architecture_invariants: &a [ARCH-01]\ntraceability: *a").replace("traceability: [HU-001]\n", "");
    expect((await validateArtifactContent(root, alias, "prd", "1.0.0", "HU-001")).issues.length).toBeGreaterThan(0);
    const stale = valid.replace(/[a-f0-9]{64}/, "0".repeat(64));
    expect((await validateArtifactContent(root, stale, "prd", "1.0.0", "HU-001")).issues).toContainEqual(expect.objectContaining({ code: "SDD-DOC-STALE" }));
  });

  it("lists a valid and invalid strategy for every artifact schema", () => {
    expect(matrix.artifact_schemas).toHaveLength(8);
  });
});

describe("Phase 3 skill contracts", () => {
  it("catalogs versioned contracts with stable unique IDs", async () => {
    const catalog = await loadSchemaCatalog(root);
    const ids = Object.keys(catalog.schemas);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids.every((id) => /@\d+\.\d+\.\d+$/.test(id))).toBe(true);
    for (const id of ids) expect(await createCatalogValidator(root, id)).toBeTypeOf("function");
  });

  it("validates positive and negative fixtures for every specific skill schema", async () => {
    for (const skill of matrix.skill_schemas) {
      for (const direction of matrix.directions) {
        const schemaId = `skill/${skill}/${direction}@1.0.0`;
        const validator = await createCatalogValidator(root, schemaId);
        const payload = direction === "input" ? inputFixture(skill) : outputFixture(skill);
        expect(validator(payload), `${schemaId}: ${JSON.stringify(validator.errors)}`).toBe(true);
        expect(validator({ ...payload, unexpected: true }), `${schemaId} must reject additional properties`).toBe(false);
        expect(validator({ ...payload, skill: "reviewer" === skill ? "verifier" : "reviewer" }), `${schemaId} must bind skill`).toBe(false);
      }
    }
  });

  it("rejects unknown schema IDs", async () => {
    await expect(createCatalogValidator(root, "skill/unknown/input@1.0.0")).rejects.toMatchObject({ code: "SDD-SCHEMA-ID" });
  });
});

async function rendered(type: string): Promise<string> {
  const template = await readFile(path.join(root, ".sdd/templates", `${type}.md`), "utf8");
  const architecture = await readFile(path.join(root, "docs/ARCHITECTURE.md"), "utf8");
  return renderArtifactTemplate(template, { STORY_ID: "HU-001", TITLE: "Contract fixture", ARCHITECTURE_SHA256: sha256Text(architecture) });
}

function inputFixture(skill: string): any {
  const parameters: Record<string, any> = {
    "spec-intake": { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: ["complete"] },
    "prd-generator": { acceptance_criteria: ["AC-001"], input_approval_sha256: "a".repeat(64) },
    "tdr-generator": { repository_context: ["docs/ARCHITECTURE.md"], technical_constraints: ["ARCH-01"] },
    "task-planner": { decisions: ["DEC-001"], delivery_constraints: ["sequential"] },
    "plan-executor": { task_ids: ["TASK-001"], required_checks: ["TEST-001"] },
    verifier: { baseline_sha256: "a".repeat(64), required_checks: ["TEST-001"] },
    reviewer: { evaluated_commit: "abcdef1", target_gaps: [] },
  };
  return { schema_version: "1.0.0", correlation_id: "00000000-0000-4000-8000-000000000010", skill, story_id: "HU-001", artifact_versions: [], docs_context: { inventory: [], applicable: [], excluded: [] }, requested_scope: { components: [], affected_data: [], affected_flows: [], read_paths: [], write_paths: [] }, parameters: parameters[skill] };
}

function outputFixture(skill: string): any {
  const result: Record<string, any> = {
    "spec-intake": { normalized_story: "SPEC/HU-001/user-story.md", acceptance_criteria: ["AC-001"], gaps: [] },
    "prd-generator": { prd_path: "SPEC/HU-001/prd.md", requirements: ["REQ-001"], assumptions: [], exclusions: [] },
    "tdr-generator": { tdr_path: "SPEC/HU-001/tdr.md", decisions: ["DEC-001"], components: ["backend"], risks: [] },
    "task-planner": { roadmap_path: "SPEC/HU-001/roadmap.md", tasks: ["TASK-001"], execution_order: ["TASK-001"], parallelism_allowed: false },
    "plan-executor": { task_results: [], modified_files: [], executed_checks: [], execution_summary_path: "SPEC/HU-001/execution-summary.md" },
    verifier: { verification_path: "SPEC/HU-001/verification-evidence.md", check_results: ["RESULT-001"], verdict: "PASSED" },
    reviewer: { review_path: "SPEC/HU-001/review.md", verdict: "APPROVED", findings: [] },
  };
  return { schema_version: "1.0.0", correlation_id: "00000000-0000-4000-8000-000000000010", skill, status: "COMPLETED", artifacts: [], docs_consulted: [], doc_conflicts: [], traceability: [], errors: [], result: result[skill] };
}
