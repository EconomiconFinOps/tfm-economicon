import path from "node:path";

import { loadConfig, loadWorkflow } from "../config.js";
import { HarnessInputError } from "../errors.js";
import { readYaml } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { JsonObject, ValidationReport } from "../types.js";
import type { HarnessConfig, WorkflowContract } from "../types.js";
import { validateWorkflowApproval } from "../workflow/validate-approval.js";
import { createManifestValidator, displayManifestPath, schemaIssues } from "./schema.js";
import { validateManifestSemantics } from "./semantics.js";

export async function validateManifest(root: string, inputPath: string): Promise<ValidationReport> {
  const config = await loadConfig(root);
  const workflow = await loadWorkflow(root, config);
  await validateWorkflowApproval(root, config, workflow);

  const manifestPath = path.isAbsolute(inputPath)
    ? assertAbsoluteManifestInsideRoot(root, inputPath)
    : resolveConcreteRepoPath(root, inputPath.replaceAll("\\", "/"));
  const rawManifest = await readYaml<unknown>(manifestPath);
  const manifest = rawManifest as JsonObject;
  const schemaVersion =
    rawManifest && typeof rawManifest === "object" && !Array.isArray(rawManifest)
      ? (rawManifest as JsonObject).schema_version
      : undefined;
  if (typeof schemaVersion === "string" && !config.schemas.supported_manifest_versions.includes(schemaVersion)) {
    throw new HarnessInputError("SDD-MANIFEST-VERSION", `Unsupported manifest schema version: ${String(schemaVersion)}`);
  }

  return validateManifestData(root, manifestPath, manifest, config, workflow);
}

export async function validateManifestData(
  root: string,
  manifestPath: string,
  manifest: JsonObject,
  config: HarnessConfig,
  workflow: WorkflowContract,
  overlay: Map<string, string> = new Map(),
): Promise<ValidationReport> {
  const schemaVersion = manifest.schema_version;
  const validateSchema = await createManifestValidator(root, config);
  if (!validateSchema(manifest)) {
    return { valid: false, path: displayManifestPath(root, manifestPath), ...(typeof schemaVersion === "string" ? { schema_version: schemaVersion } : {}), errors: schemaIssues(validateSchema.errors) };
  }
  const errors = await validateManifestSemantics(root, manifestPath, manifest, config, workflow, overlay);
  return { valid: errors.length === 0, path: displayManifestPath(root, manifestPath), schema_version: schemaVersion as string, story_id: (manifest.story as JsonObject).id as string, errors };
}

function assertAbsoluteManifestInsideRoot(root: string, inputPath: string): string {
  const resolved = path.resolve(inputPath);
  const relative = path.relative(root, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new HarnessInputError("SDD-MANIFEST-OUTSIDE-ROOT", "Manifest must be inside the repository");
  }
  return resolved;
}
