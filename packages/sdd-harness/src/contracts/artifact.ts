import { parseDocument } from "yaml";

import { HarnessInputError } from "../errors.js";
import { sha256File, sha256Text } from "../hash.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord, ValidationIssue } from "../types.js";
import { contractIssues, createCatalogValidator } from "./catalog.js";

export interface ParsedArtifact { metadata: AnyRecord; sections: Record<string, string> }

export function parseArtifactMarkdown(content: string): ParsedArtifact {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/.exec(content);
  if (!match) throw new HarnessInputError("SDD-ARTIFACT-FRONTMATTER", "Artifact requires YAML front matter delimited by ---");
  const document = parseDocument(match[1]!, { schema: "core", uniqueKeys: true });
  if (document.errors.length) throw new HarnessInputError("SDD-ARTIFACT-YAML", document.errors.map((item) => item.message).join("; "));
  const metadata = document.toJS({ maxAliasCount: 0 }) as AnyRecord;
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) throw new HarnessInputError("SDD-ARTIFACT-YAML", "Front matter must be an object");
  const sections: Record<string, string> = {};
  const lines = match[2]!.split(/\r?\n/);
  let heading: string | null = null;
  let buffer: string[] = [];
  const flush = (): void => { if (heading) sections[heading] = buffer.join("\n").trim(); };
  for (const line of lines) {
    const section = /^##\s+(.+?)\s*$/.exec(line);
    if (section) {
      flush();
      heading = section[1]!;
      if (Object.hasOwn(sections, heading)) throw new HarnessInputError("SDD-ARTIFACT-SECTION", `Duplicate section: ${heading}`);
      buffer = [];
    } else if (heading) buffer.push(line);
  }
  flush();
  return { metadata, sections };
}

export async function validateArtifactContent(root: string, content: string, expectedType: string, expectedVersion: string, expectedStory: string, checkDocumentHashes = true): Promise<{ parsed?: ParsedArtifact; issues: ValidationIssue[] }> {
  let parsed: ParsedArtifact;
  try { parsed = parseArtifactMarkdown(content); } catch (error) {
    const known = error as HarnessInputError;
    return { issues: [{ code: known.code ?? "SDD-ARTIFACT-PARSE", instance_path: "/", message: error instanceof Error ? error.message : String(error) }] };
  }
  const validator = await createCatalogValidator(root, `artifact/${expectedType}@${expectedVersion}`);
  const issues = validator(parsed) ? [] : contractIssues(validator.errors, "/artifact");
  if (parsed.metadata.artifact_type !== expectedType) issues.push({ code: "SDD-ARTIFACT-TYPE", instance_path: "/metadata/artifact_type", message: `Expected ${expectedType}` });
  if (parsed.metadata.artifact_schema_version !== expectedVersion) issues.push({ code: "SDD-ARTIFACT-VERSION", instance_path: "/metadata/artifact_schema_version", message: `Expected ${expectedVersion}` });
  if (parsed.metadata.story_id !== expectedStory) issues.push({ code: "SDD-ARTIFACT-STORY", instance_path: "/metadata/story_id", message: `Expected ${expectedStory}` });
  for (const [index, reference] of (parsed.metadata.documentation_consulted ?? []).entries()) {
    if (!checkDocumentHashes) break;
    try {
      const actual = await sha256File(resolveConcreteRepoPath(root, reference.path));
      if (actual !== reference.sha256) issues.push({ code: "SDD-DOC-STALE", instance_path: `/metadata/documentation_consulted/${index}/sha256`, message: `Documentation hash is stale: ${reference.path}` });
    } catch (error) {
      issues.push({ code: "SDD-DOC-MISSING", instance_path: `/metadata/documentation_consulted/${index}/path`, message: error instanceof Error ? error.message : String(error) });
    }
  }
  return { parsed, issues };
}

export function renderArtifactTemplate(template: string, values: Record<string, string>): string {
  return template.replace(/\{\{([A-Z0-9_]+)\}\}/g, (_match, key: string) => {
    if (!(key in values)) throw new HarnessInputError("SDD-TEMPLATE-VARIABLE", `Missing template variable: ${key}`);
    return values[key]!;
  });
}

export function hashInlineReference(content: string): string { return sha256Text(content); }
