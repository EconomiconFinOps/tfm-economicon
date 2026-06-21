import { readFile } from "node:fs/promises";
import { beforeAll, describe, expect, it } from "vitest";
import { parse } from "yaml";

import { loadConfig, loadWorkflow } from "../src/config.js";
import { evaluateNext } from "../src/orchestrator/gates.js";
import { findRepoRoot } from "../src/repo.js";

let root: string;
let workflow: Awaited<ReturnType<typeof loadWorkflow>>;
let fixture: any;

beforeAll(async () => {
  root = await findRepoRoot();
  const config = await loadConfig(root);
  workflow = await loadWorkflow(root, config);
  fixture = parse(await readFile(`${root}/SPEC/examples/HU-000-fixture/manifest.yaml`, "utf8"));
});

describe("forward gates", () => {
  it.each([
    ["INTAKE", "TR-002", [artifact("user-story")], []],
    ["PRD", "TR-003", [artifact("user-story"), artifact("prd")], ["no_open_functional_questions"]],
    ["TDR", "TR-004", [artifact("prd"), artifact("tdr")], ["architecture_invariants_evaluated", "architecture_gaps_evaluated"]],
    ["PLAN", "TR-005", [artifact("tdr"), artifact("roadmap"), artifact("task")], []],
    ["EXECUTION", "TR-006", [artifact("roadmap"), artifact("task"), plainArtifact("execution-summary")], ["source_hashes_current"]],
    ["VERIFICATION", "TR-007", [plainArtifact("execution-summary"), plainArtifact("verification-evidence")], ["verification_matches_evaluated_commit"]],
    ["REVIEW", "TR-008", [plainArtifact("verification-evidence"), artifact("review")], ["architecture_gates_satisfied"]],
  ])("accepts satisfied %s gate as %s", async (stage, transitionId, artifacts, evidence) => {
    const manifest = structuredClone(fixture);
    manifest.story.change_type = "harness-docs";
    manifest.workflow.stage = stage;
    manifest.artifacts = artifacts;
    manifest.scope.write_paths = ["packages/sdd-harness/**"];
    manifest.tasks = stage === "EXECUTION" ? [{ status: "COMPLETED" }] : [];
    manifest.checks = stage === "VERIFICATION" ? [{ status: "COMPLETED", result: { exit_code: 0 } }] : [];
    manifest.gate_evidence = evidence.map((condition) => ({ condition, satisfied: true }));
    const result = await evaluateNext(root, manifest, workflow);
    expect(result.transition?.id).toBe(transitionId);
    expect(result.blockers).toEqual([]);
  });

  it("fails closed when nondeducible evidence is absent", async () => {
    const manifest = structuredClone(fixture);
    manifest.workflow.stage = "PRD";
    manifest.artifacts = [artifact("prd")];
    const result = await evaluateNext(root, manifest, workflow);
    expect(result.blockers).toContainEqual(expect.objectContaining({ code: "WF-OPEN-QUESTIONS" }));
  });
});

function artifact(type: string): any {
  return { type, path: `${type}.md`, version: 1, sha256: "a".repeat(64), status: "APPROVED", approvals: [{ decision: "APPROVED", artifact_version: 1, artifact_sha256: "a".repeat(64) }] };
}
function plainArtifact(type: string): any { return { ...artifact(type), status: "DRAFT", approvals: [] }; }
