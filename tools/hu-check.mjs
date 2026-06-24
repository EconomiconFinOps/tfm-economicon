#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const REQUIRED_BACKLOG_COLUMNS = [
  "ID",
  "Fecha",
  "Origen",
  "Tipo",
  "Severidad",
  "Scope",
  "Estado",
  "Owner",
  "Accion",
  "Change/Fix",
];

export const VALID_FINDING_STATES = new Set([
  "Open",
  "Planned",
  "In progress",
  "Fixed",
  "Accepted risk",
  "Won't fix",
]);

const OLD_HARNESS_PATHS = [".sdd", path.join("packages", "sdd-harness"), "SPEC"];
const OLD_HARNESS_GIT_PATTERN = /^(?:\.sdd\/|packages\/sdd-harness\/|SPEC\/)/;
const APPROVAL_SCAN_ROOTS = ["docs", "openspec", "tools"];
const TEXT_EXTENSIONS = new Set([".md", ".mjs", ".js", ".json", ".yaml", ".yml", ".txt"]);

function isMainModule() {
  return process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}

export function parseArgs(argv) {
  const args = { command: argv[2] ?? "help", change: undefined };
  for (let index = 3; index < argv.length; index += 1) {
    if (argv[index] === "--") {
      continue;
    }
    if (argv[index] === "--change") {
      args.change = argv[index + 1];
      index += 1;
    }
  }
  return args;
}

export function findSpecFiles(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findSpecFiles(fullPath));
    } else if (entry.name === "spec.md") {
      results.push(fullPath);
    }
  }
  return results;
}

export function hasOpenTasks(markdown) {
  return markdown
    .split(/\r?\n/)
    .some((line) => /^\s*-\s+\[\s\]\s+/.test(line));
}

export function hasAnyTask(markdown) {
  return markdown
    .split(/\r?\n/)
    .some((line) => /^\s*-\s+\[[ xX]\]\s+/.test(line));
}

export function hasStructuredApproval(markdown, approvalType) {
  return approvalBlocks(markdown).some((block) => {
    const typePattern = new RegExp(`^\\s*-\\s+Approval type:\\s*${escapeRegExp(approvalType)}\\s*$`, "im");
    const decisionPattern = /^\s*-\s+Decision:\s*approved\s*$/im;
    return typePattern.test(block) && decisionPattern.test(block);
  });
}

function approvalBlocks(markdown) {
  const blocks = [];
  const matches = [...markdown.matchAll(/^## Human Approval\s*$/gim)];

  for (const match of matches) {
    const start = match.index ?? 0;
    const rest = markdown.slice(start);
    const afterHeading = rest.slice(match[0].length);
    const nextHeading = afterHeading.search(/^##\s+/gm);
    blocks.push(nextHeading === -1 ? rest : rest.slice(0, match[0].length + nextHeading));
  }

  return blocks;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function parseMarkdownTable(markdown, requiredColumns = []) {
  const lines = markdown.split(/\r?\n/);
  const tables = [];

  for (let index = 0; index < lines.length - 1; index += 1) {
    const headerLine = lines[index].trim();
    const separatorLine = lines[index + 1].trim();

    if (!headerLine.startsWith("|") || !separatorLine.startsWith("|")) {
      continue;
    }

    const headers = splitTableRow(headerLine);
    const isSeparator = splitTableRow(separatorLine).every((cell) => /^:?-{3,}:?$/.test(cell));
    if (!isSeparator) {
      continue;
    }

    if (requiredColumns.length > 0 && !requiredColumns.every((column) => headers.includes(column))) {
      continue;
    }

    const rows = [];
    for (let rowIndex = index + 2; rowIndex < lines.length; rowIndex += 1) {
      const rowLine = lines[rowIndex].trim();
      if (!rowLine.startsWith("|")) {
        break;
      }

      const values = splitTableRow(rowLine);
      const row = {};
      headers.forEach((header, cellIndex) => {
        row[header] = values[cellIndex] ?? "";
      });
      rows.push(row);
    }

    tables.push({ headers, rows });
  }

  return tables;
}

function splitTableRow(line) {
  return line
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

export function validateBacklogMarkdown(markdown) {
  const issues = [];
  const tables = parseMarkdownTable(markdown, REQUIRED_BACKLOG_COLUMNS);
  if (tables.length === 0) {
    return ["Missing findings backlog table with required columns."];
  }

  const table = tables[0];
  for (const row of table.rows) {
    if (!/^RF-\d{3}-\d{3}$/.test(row.ID ?? "")) {
      issues.push(`Invalid finding ID: ${row.ID || "<empty>"}`);
    }
    if (!VALID_FINDING_STATES.has(row.Estado ?? "")) {
      issues.push(`Invalid finding state for ${row.ID || "<unknown>"}: ${row.Estado || "<empty>"}`);
    }
  }

  return issues;
}

export function parseReviewFindings(markdown) {
  if (!/^## Review Findings\s*$/im.test(markdown)) {
    return { missingSection: true, findings: [] };
  }

  const tables = parseMarkdownTable(markdown, ["ID", "Scope", "Backlog"]);
  if (tables.length === 0) {
    return { missingSection: false, findings: [] };
  }

  return { missingSection: false, findings: tables[0].rows };
}

export function reviewFindingNeedsBacklog(row) {
  const scope = (row.Scope ?? "").toLowerCase();
  const action = (row.Accion ?? row.Action ?? "").toLowerCase();
  const backlog = (row.Backlog ?? "").toLowerCase();

  return (
    scope.includes("out of scope") ||
    backlog.includes("added") ||
    /\b(defer|deferred|follow-up|create hu|later|tbd|accept)\b/.test(action)
  );
}

export function hasProductChanges(statusText) {
  return productChangePaths(statusText).length > 0;
}

export function productChangePaths(statusText) {
  return statusText
    .split(/\r?\n/)
    .flatMap((line) => statusLinePaths(line))
    .filter((changedPath) => {
      const normalized = changedPath.replace(/\\/g, "/");
      return normalized.startsWith("apps/") || normalized.startsWith("packages/");
    });
}

function statusLinePaths(line) {
  if (!line.trim()) {
    return [];
  }

  const value = line.slice(3).trim();
  if (!value) {
    return [];
  }

  if (value.includes(" -> ")) {
    return value.split(" -> ").map((item) => item.trim());
  }

  return [value];
}

function legacyApprovalLabels() {
  return ["Pre-code", "Post-review"].map((prefix) => `${prefix}${" approval"}${": approved"}`);
}

export function legacyApprovalMatchesInText(text, filePath = "<inline>") {
  const matches = [];
  const lines = text.split(/\r?\n/);

  lines.forEach((line, lineIndex) => {
    for (const label of legacyApprovalLabels()) {
      if (line.includes(label)) {
        matches.push({ filePath, line: lineIndex + 1 });
      }
    }
  });

  return matches;
}

export function findLegacyApprovalMatches(rootDir = process.cwd()) {
  const files = [
    ...APPROVAL_SCAN_ROOTS.flatMap((scanRoot) => walkTextFiles(path.join(rootDir, scanRoot))),
    path.join(rootDir, "package.json"),
  ];

  return files.flatMap((filePath) => {
    if (!fs.existsSync(filePath)) {
      return [];
    }
    return legacyApprovalMatchesInText(readText(filePath), path.relative(rootDir, filePath));
  });
}

function walkTextFiles(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkTextFiles(fullPath));
    } else if (TEXT_EXTENSIONS.has(path.extname(entry.name))) {
      files.push(fullPath);
    }
  }
  return files;
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function ok(message) {
  return { ok: true, message };
}

function fail(message) {
  return { ok: false, message };
}

function printResults(results) {
  for (const result of results) {
    const prefix = result.ok ? "OK" : "FAIL";
    console.log(`${prefix} ${result.message}`);
  }
}

function exitCode(results) {
  return results.every((result) => result.ok) ? 0 : 1;
}

function runCommand(name, args, rootDir) {
  if (process.platform === "win32" && name === "pnpm") {
    return spawnSync([name, ...args].join(" "), { cwd: rootDir, encoding: "utf8", shell: true });
  }
  return spawnSync(name, args, { cwd: rootDir, encoding: "utf8" });
}

function commandOutput(result) {
  if (result.error) {
    return result.error.message;
  }
  return (result.stderr || result.stdout || "").trim();
}

export function checkAntiHarness(rootDir = process.cwd()) {
  const results = [];

  for (const oldPath of OLD_HARNESS_PATHS) {
    const exists = fs.existsSync(path.join(rootDir, oldPath));
    results.push(exists ? fail(`Old harness path exists: ${oldPath}`) : ok(`Old harness path absent: ${oldPath}`));
  }

  const gitResult = runCommand("git", ["ls-files"], rootDir);
  if (gitResult.status !== 0) {
    results.push(fail(`git ls-files failed: ${commandOutput(gitResult)}`));
    return results;
  }

  const matches = gitResult.stdout
    .split(/\r?\n/)
    .filter((line) => OLD_HARNESS_GIT_PATTERN.test(line));

  results.push(matches.length === 0 ? ok("No old harness files are tracked.") : fail(`Old harness files are tracked: ${matches.join(", ")}`));

  return results;
}

export function checkFindings(rootDir = process.cwd()) {
  const backlogPath = path.join(rootDir, "openspec", "findings", "backlog.md");
  if (!fs.existsSync(backlogPath)) {
    return [fail("Missing openspec/findings/backlog.md")];
  }

  const issues = validateBacklogMarkdown(readText(backlogPath));
  return issues.length === 0 ? [ok("Findings backlog is valid.")] : issues.map(fail);
}

export function checkApprovalFormat(rootDir = process.cwd()) {
  const matches = findLegacyApprovalMatches(rootDir);
  if (matches.length === 0) {
    return [ok("Structured HiTL approval format is the only approval format present.")];
  }

  return matches.map((match) => fail(`Legacy HiTL approval wording found at ${match.filePath}:${match.line}`));
}

export function checkPreCode(changeName, rootDir = process.cwd()) {
  const results = [];
  if (!changeName) {
    return [fail("Missing --change <change-name>.")];
  }

  const changeDir = path.join(rootDir, "openspec", "changes", changeName);
  if (!fs.existsSync(changeDir)) {
    return [fail(`Missing OpenSpec change: ${changeName}`)];
  }
  results.push(ok(`OpenSpec change exists: ${changeName}`));

  const requiredFiles = ["proposal.md", "design.md", "tasks.md"];
  for (const fileName of requiredFiles) {
    const filePath = path.join(changeDir, fileName);
    results.push(fs.existsSync(filePath) ? ok(`Found ${fileName}.`) : fail(`Missing ${fileName}.`));
  }

  const specFiles = findSpecFiles(path.join(changeDir, "specs"));
  results.push(specFiles.length > 0 ? ok(`Found ${specFiles.length} spec file(s).`) : fail("Missing specs/*/spec.md."));

  const markdownFiles = requiredFiles
    .map((fileName) => path.join(changeDir, fileName))
    .filter((filePath) => fs.existsSync(filePath))
    .map(readText)
    .join("\n");

  results.push(hasStructuredApproval(markdownFiles, "pre-code") ? ok("Pre-code HiTL approval recorded.") : fail("Missing structured pre-code HiTL approval."));

  const tasksPath = path.join(changeDir, "tasks.md");
  if (fs.existsSync(tasksPath)) {
    results.push(hasAnyTask(readText(tasksPath)) ? ok("tasks.md contains at least one task.") : fail("tasks.md contains no tasks."));
  }

  const openspecResult = runCommand("pnpm", ["openspec:validate"], rootDir);
  results.push(openspecResult.status === 0 ? ok("pnpm openspec:validate passed.") : fail(`pnpm openspec:validate failed: ${commandOutput(openspecResult)}`));

  results.push(...checkApprovalFormat(rootDir));
  results.push(...checkAntiHarness(rootDir));

  const gitStatus = runCommand("git", ["status", "--porcelain"], rootDir);
  if (gitStatus.status !== 0) {
    results.push(fail(`git status --porcelain failed: ${commandOutput(gitStatus)}`));
  } else {
    const productPaths = productChangePaths(gitStatus.stdout);
    results.push(productPaths.length === 0 ? ok("No product changes are present before execution.") : fail(`Product changes are present before execution: ${productPaths.join(", ")}`));
  }

  return results;
}

export function checkChange(changeName, rootDir = process.cwd()) {
  const results = [];
  if (!changeName) {
    return [fail("Missing --change <change-name>.")];
  }

  const changeDir = path.join(rootDir, "openspec", "changes", changeName);
  if (!fs.existsSync(changeDir)) {
    return [fail(`Missing OpenSpec change: ${changeName}`)];
  }
  results.push(ok(`OpenSpec change exists: ${changeName}`));

  const requiredFiles = ["proposal.md", "design.md", "tasks.md", "review.md"];
  for (const fileName of requiredFiles) {
    const filePath = path.join(changeDir, fileName);
    results.push(fs.existsSync(filePath) ? ok(`Found ${fileName}.`) : fail(`Missing ${fileName}.`));
  }

  const specFiles = findSpecFiles(path.join(changeDir, "specs"));
  results.push(specFiles.length > 0 ? ok(`Found ${specFiles.length} spec file(s).`) : fail("Missing specs/*/spec.md."));

  const markdownFiles = requiredFiles
    .map((fileName) => path.join(changeDir, fileName))
    .filter((filePath) => fs.existsSync(filePath))
    .map(readText)
    .join("\n");

  results.push(hasStructuredApproval(markdownFiles, "pre-code") ? ok("Pre-code HiTL approval recorded.") : fail("Missing structured pre-code HiTL approval."));
  results.push(hasStructuredApproval(markdownFiles, "post-review") ? ok("Post-review HiTL approval recorded.") : fail("Missing structured post-review HiTL approval."));

  const tasksPath = path.join(changeDir, "tasks.md");
  if (fs.existsSync(tasksPath)) {
    results.push(hasOpenTasks(readText(tasksPath)) ? fail("tasks.md contains open tasks.") : ok("tasks.md has no open tasks."));
  }

  const reviewPath = path.join(changeDir, "review.md");
  if (fs.existsSync(reviewPath)) {
    results.push(...checkReviewFindingsAgainstBacklog(reviewPath, rootDir));
  }

  const openspecResult = runCommand("pnpm", ["openspec:validate"], rootDir);
  results.push(openspecResult.status === 0 ? ok("pnpm openspec:validate passed.") : fail(`pnpm openspec:validate failed: ${commandOutput(openspecResult)}`));

  results.push(...checkApprovalFormat(rootDir));
  results.push(...checkAntiHarness(rootDir));

  return results;
}

function checkReviewFindingsAgainstBacklog(reviewPath, rootDir) {
  const results = [];
  const review = readText(reviewPath);
  const parsed = parseReviewFindings(review);
  if (parsed.missingSection) {
    return [fail("review.md is missing ## Review Findings.")];
  }

  results.push(ok("review.md contains ## Review Findings."));

  const backlogPath = path.join(rootDir, "openspec", "findings", "backlog.md");
  const backlog = fs.existsSync(backlogPath) ? readText(backlogPath) : "";
  if (!fs.existsSync(backlogPath)) {
    results.push(fail("Missing openspec/findings/backlog.md."));
    return results;
  }

  const missing = parsed.findings
    .filter(reviewFindingNeedsBacklog)
    .map((row) => row.ID)
    .filter((id) => id && !backlog.includes(id));

  results.push(missing.length === 0 ? ok("Review findings are linked to backlog when required.") : fail(`Findings missing from backlog: ${missing.join(", ")}`));

  return results;
}

function printHelp() {
  console.log(`Usage:
  node tools/hu-check.mjs check --change <change-name>
  node tools/hu-check.mjs pre-code --change <change-name>
  node tools/hu-check.mjs approval-format
  node tools/hu-check.mjs findings
  node tools/hu-check.mjs anti-harness`);
}

export function runCli(argv = process.argv, rootDir = process.cwd()) {
  const { command, change } = parseArgs(argv);
  let results;

  if (command === "check") {
    results = checkChange(change, rootDir);
  } else if (command === "pre-code") {
    results = checkPreCode(change, rootDir);
  } else if (command === "approval-format") {
    results = checkApprovalFormat(rootDir);
  } else if (command === "findings") {
    results = checkFindings(rootDir);
  } else if (command === "anti-harness") {
    results = checkAntiHarness(rootDir);
  } else {
    printHelp();
    return 1;
  }

  printResults(results);
  return exitCode(results);
}

if (isMainModule()) {
  process.exitCode = runCli();
}
