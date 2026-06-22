import Ajv2020Module, { type ErrorObject, type ValidateFunction } from "ajv/dist/2020.js";
import addFormatsModule from "ajv-formats";
import { parseDocument } from "yaml";

import { loadConfig } from "../config.js";
import { HarnessInputError } from "../errors.js";
import { readText, readYaml } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { JsonObject, ValidationIssue } from "../types.js";

interface SchemaCatalog { catalog_version: string; schemas: Record<string, string> }

export async function loadSchemaCatalog(root: string): Promise<SchemaCatalog> {
  const config = await loadConfig(root);
  const catalog = await readYaml<SchemaCatalog>(resolveConcreteRepoPath(root, config.schemas.catalog));
  if (catalog.catalog_version !== "1.0.0" || !catalog.schemas || Array.isArray(catalog.schemas)) throw new HarnessInputError("SDD-SCHEMA-CATALOG", "Schema catalog is invalid");
  return catalog;
}

export async function createCatalogValidator(root: string, schemaId: string): Promise<ValidateFunction> {
  const catalog = await loadSchemaCatalog(root);
  const selected = catalog.schemas[schemaId];
  if (!selected) throw new HarnessInputError("SDD-SCHEMA-ID", `Unknown schema ID: ${schemaId}`);
  const Ajv2020 = (Ajv2020Module as any).default ?? Ajv2020Module;
  const addFormats = (addFormatsModule as any).default ?? addFormatsModule;
  const ajv = new Ajv2020({ allErrors: true, strict: true, strictRequired: false, strictTypes: false });
  addFormats(ajv);
  const schemas: JsonObject[] = [];
  for (const schemaPath of new Set(Object.values(catalog.schemas))) {
    schemas.push(JSON.parse(await readText(resolveConcreteRepoPath(root, schemaPath))) as JsonObject);
  }
  const supporting = [".sdd/schemas/artifacts/artifact-contract.schema.json", ".sdd/schemas/skills/skill-contract.schema.json", ".sdd/schemas/skills/v2/skill-contract.schema.json"];
  for (const schemaPath of supporting) {
    try { schemas.push(JSON.parse(await readText(resolveConcreteRepoPath(root, schemaPath))) as JsonObject); } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  for (const schema of schemas) ajv.addSchema(schema);
  const schema = JSON.parse(await readText(resolveConcreteRepoPath(root, selected))) as JsonObject;
  return ajv.getSchema(schema.$id as string) ?? ajv.compile(schema);
}

export function contractIssues(errors: ErrorObject[] | null | undefined, prefix = ""): ValidationIssue[] {
  return (errors ?? []).map((error) => ({ code: "SDD-CONTRACT-SCHEMA", instance_path: `${prefix}${error.instancePath || "/"}`, message: error.message ?? "Contract validation failed" }));
}

export async function validateCatalogPayload(root: string, schemaId: string, inputPath: string): Promise<{ valid: boolean; schema_id: string; path: string; errors: ValidationIssue[] }> {
  const content = await readText(resolveConcreteRepoPath(root, inputPath));
  const document = parseDocument(content, { schema: "core", uniqueKeys: true });
  if (document.errors.length) {
    const errors = document.errors.map((error) => ({ code: "SDD-CONTRACT-PARSE", instance_path: "/", message: error.message }));
    return { valid: false, schema_id: schemaId, path: inputPath, errors };
  }
  const payload = document.toJS({ maxAliasCount: 0 });
  const validator = await createCatalogValidator(root, schemaId);
  const errors = validator(payload) ? [] : contractIssues(validator.errors);
  return { valid: errors.length === 0, schema_id: schemaId, path: inputPath, errors };
}
