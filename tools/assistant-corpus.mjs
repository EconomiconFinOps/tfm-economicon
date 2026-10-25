#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

export const CORPUS_ROOT = path.join("docs", "assistant-corpus");
export const MANIFEST_PATH = path.join(CORPUS_ROOT, "manifest.yaml");
export const EXPECTED_VERSION = 1;
export const EXPECTED_CORPUS = "assistant-document-corpus";
export const REQUIRED_FIELDS = [
  "id",
  "title",
  "path",
  "category",
  "tags",
  "language",
  "version",
  "scope",
  "tenant_id",
  "dataset_id",
  "source_type",
  "updated_at",
];
export const ALLOWED_CATEGORIES = new Set(["finops", "business-rules", "glossary", "product-architecture"]);
export const ALLOWED_SCOPES = new Set(["global", "dataset", "tenant"]);

function isMainModule() {
  return process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}

function addIssue(issues, message) {
  issues.push(message);
}

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function hasOwn(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function toManifestPath(filePath) {
  return filePath.split(path.sep).join("/");
}

function containsParentSegment(value) {
  return /(^|[\\/])\.\.([\\/]|$)/.test(value);
}

function isSubPath(childPath, parentPath) {
  const relative = path.relative(parentPath, childPath);
  return relative === "" || (!!relative && !relative.startsWith("..") && !path.isAbsolute(relative));
}

function walkMarkdownFiles(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walkMarkdownFiles(fullPath));
    } else if (entry.isFile() && path.extname(entry.name).toLowerCase() === ".md") {
      results.push(fullPath);
    }
  }
  return results;
}

function validateManifestShape(manifest, issues) {
  if (!isPlainObject(manifest)) {
    addIssue(issues, "manifest.yaml must contain a YAML object.");
    return false;
  }

  if (manifest.version !== EXPECTED_VERSION) {
    addIssue(issues, `manifest.version must be ${EXPECTED_VERSION}.`);
  }

  if (manifest.corpus !== EXPECTED_CORPUS) {
    addIssue(issues, `manifest.corpus must be ${EXPECTED_CORPUS}.`);
  }

  if (!Array.isArray(manifest.documents) || manifest.documents.length === 0) {
    addIssue(issues, "manifest.documents must be a non-empty array.");
    return false;
  }

  return true;
}

function validateRequiredFields(entry, label, issues) {
  for (const field of REQUIRED_FIELDS) {
    if (!hasOwn(entry, field)) {
      addIssue(issues, `${label} is missing required metadata field: ${field}.`);
    }
  }
}

function validateTextMetadata(entry, label, issues) {
  for (const field of ["id", "title", "path", "category", "language", "version", "scope", "source_type", "updated_at"]) {
    if (hasOwn(entry, field) && !isNonEmptyString(entry[field])) {
      addIssue(issues, `${label}.${field} must be a non-empty string.`);
    }
  }

  if (hasOwn(entry, "tags")) {
    if (!Array.isArray(entry.tags) || entry.tags.length === 0) {
      addIssue(issues, `${label}.tags must be a non-empty array.`);
    } else {
      entry.tags.forEach((tag, tagIndex) => {
        if (!isNonEmptyString(tag)) {
          addIssue(issues, `${label}.tags[${tagIndex}] must be a non-empty string.`);
        }
      });
    }
  }
}

function validateCategoryAndScope(entry, label, issues) {
  if (isNonEmptyString(entry.category) && !ALLOWED_CATEGORIES.has(entry.category)) {
    addIssue(issues, `${label}.category has invalid value: ${entry.category}.`);
  }

  if (isNonEmptyString(entry.scope) && !ALLOWED_SCOPES.has(entry.scope)) {
    addIssue(issues, `${label}.scope has invalid value: ${entry.scope}.`);
  }

  if (entry.scope === "global") {
    if (entry.tenant_id !== null) {
      addIssue(issues, `${label} with scope global must set tenant_id: null.`);
    }
    if (entry.dataset_id !== null) {
      addIssue(issues, `${label} with scope global must set dataset_id: null.`);
    }
  }

  if (entry.scope === "dataset") {
    if (entry.tenant_id !== null) {
      addIssue(issues, `${label} with scope dataset must set tenant_id: null.`);
    }
    if (!isNonEmptyString(entry.dataset_id)) {
      addIssue(issues, `${label} with scope dataset must set dataset_id to a non-empty string.`);
    }
  }

  if (entry.scope === "tenant") {
    if (!isNonEmptyString(entry.tenant_id)) {
      addIssue(issues, `${label} with scope tenant must set tenant_id to a non-empty string.`);
    }
    if (entry.dataset_id !== null && !isNonEmptyString(entry.dataset_id)) {
      addIssue(issues, `${label}.dataset_id must be null or a non-empty string.`);
    }
  }
}

function validatePath(entry, label, rootDir, manifestPathSet, issues) {
  if (!isNonEmptyString(entry.path)) {
    return;
  }

  if (path.isAbsolute(entry.path)) {
    addIssue(issues, `${label}.path must be repository-relative, not absolute.`);
    return;
  }

  if (containsParentSegment(entry.path)) {
    addIssue(issues, `${label}.path must not contain parent directory segments.`);
    return;
  }

  const rootPath = path.resolve(rootDir);
  const corpusRootPath = path.resolve(rootDir, CORPUS_ROOT);
  const resolvedPath = path.resolve(rootPath, entry.path);
  if (!isSubPath(resolvedPath, corpusRootPath)) {
    addIssue(issues, `${label}.path must resolve under ${toManifestPath(CORPUS_ROOT)}.`);
    return;
  }

  const normalizedManifestPath = toManifestPath(path.relative(rootPath, resolvedPath));
  manifestPathSet.add(normalizedManifestPath);

  if (!fs.existsSync(resolvedPath)) {
    addIssue(issues, `${label}.path does not exist: ${entry.path}.`);
    return;
  }

  const stat = fs.statSync(resolvedPath);
  if (!stat.isFile()) {
    addIssue(issues, `${label}.path must reference a file: ${entry.path}.`);
    return;
  }

  const content = fs.readFileSync(resolvedPath, "utf8");
  if (content.trim().length === 0) {
    addIssue(issues, `${label}.path references an empty document: ${entry.path}.`);
  }
}

function validateUndeclaredMarkdown(rootDir, declaredPaths, issues) {
  const rootPath = path.resolve(rootDir);
  const corpusRootPath = path.resolve(rootDir, CORPUS_ROOT);

  for (const category of ALLOWED_CATEGORIES) {
    const categoryPath = path.join(corpusRootPath, category);
    for (const markdownPath of walkMarkdownFiles(categoryPath)) {
      const manifestPath = toManifestPath(path.relative(rootPath, markdownPath));
      if (!declaredPaths.has(manifestPath)) {
        addIssue(issues, `Indexable markdown document is not declared in manifest: ${manifestPath}.`);
      }
    }
  }
}

export function validateAssistantCorpus(rootDir = process.cwd()) {
  const issues = [];
  const manifestPath = path.join(rootDir, MANIFEST_PATH);

  if (!fs.existsSync(manifestPath)) {
    return [`Missing assistant corpus manifest: ${toManifestPath(MANIFEST_PATH)}.`];
  }

  let manifest;
  try {
    manifest = parse(fs.readFileSync(manifestPath, "utf8"));
  } catch (error) {
    return [`manifest.yaml failed to parse: ${error.message}`];
  }

  if (!validateManifestShape(manifest, issues)) {
    return issues;
  }

  const ids = new Set();
  const paths = new Set();
  const categories = new Set();
  const declaredPaths = new Set();

  manifest.documents.forEach((entry, index) => {
    const label = `documents[${index}]`;
    if (!isPlainObject(entry)) {
      addIssue(issues, `${label} must be an object.`);
      return;
    }

    validateRequiredFields(entry, label, issues);
    validateTextMetadata(entry, label, issues);
    validateCategoryAndScope(entry, label, issues);

    if (isNonEmptyString(entry.id)) {
      if (ids.has(entry.id)) {
        addIssue(issues, `Duplicate document id: ${entry.id}.`);
      }
      ids.add(entry.id);
    }

    if (isNonEmptyString(entry.path)) {
      if (paths.has(entry.path)) {
        addIssue(issues, `Duplicate document path: ${entry.path}.`);
      }
      paths.add(entry.path);
    }

    if (isNonEmptyString(entry.category) && ALLOWED_CATEGORIES.has(entry.category)) {
      categories.add(entry.category);
    }

    validatePath(entry, label, rootDir, declaredPaths, issues);
  });

  for (const category of ALLOWED_CATEGORIES) {
    if (!categories.has(category)) {
      addIssue(issues, `Missing required corpus category in manifest: ${category}.`);
    }
  }

  validateUndeclaredMarkdown(rootDir, declaredPaths, issues);

  return issues;
}

function printValidation(issues) {
  if (issues.length === 0) {
    console.log("OK Assistant corpus manifest is valid.");
    return;
  }

  for (const issue of issues) {
    console.error(`FAIL ${issue}`);
  }
}

export function runCli(argv = process.argv, rootDir = process.cwd()) {
  const command = argv[2] ?? "validate";
  if (command !== "validate") {
    console.error("Usage: node tools/assistant-corpus.mjs validate");
    return 1;
  }

  const issues = validateAssistantCorpus(rootDir);
  printValidation(issues);
  return issues.length === 0 ? 0 : 1;
}

if (isMainModule()) {
  process.exitCode = runCli();
}
