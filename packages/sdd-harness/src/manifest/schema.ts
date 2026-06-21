import path from "node:path";
import Ajv2020Module, { type ErrorObject, type ValidateFunction } from "ajv/dist/2020.js";
import addFormatsModule from "ajv-formats";

import { readText } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { HarnessConfig, JsonObject, ValidationIssue } from "../types.js";

export async function createManifestValidator(root: string, config: HarnessConfig): Promise<ValidateFunction<JsonObject>> {
  const schemaPath = resolveConcreteRepoPath(root, config.schemas.manifest);
  const schema = JSON.parse(await readText(schemaPath)) as JsonObject;
  const Ajv2020 = (Ajv2020Module as any).default ?? Ajv2020Module;
  const addFormats = (addFormatsModule as any).default ?? addFormatsModule;
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  return ajv.compile(schema) as ValidateFunction<JsonObject>;
}

export function schemaIssues(errors: ErrorObject[] | null | undefined): ValidationIssue[] {
  return (errors ?? []).map((error) => ({
    code: "SDD-MANIFEST-SCHEMA",
    instance_path: error.instancePath || "/",
    message: error.message ?? "Schema validation failed",
  }));
}

export function displayManifestPath(root: string, manifestPath: string): string {
  return path.relative(root, manifestPath).replaceAll("\\", "/");
}
