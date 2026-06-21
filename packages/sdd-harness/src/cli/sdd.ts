import { HarnessInputError } from "../errors.js";
import { validateCatalogPayload } from "../contracts/catalog.js";
import { validateManifest } from "../manifest/validate.js";
import type { Actor, CommandResult } from "../types.js";
import { advanceStory, approveArtifact, recordCheck, registerArtifact, registerEvidence, resolveReview, reviseArtifact, updateStoryStatus, updateTask } from "../orchestrator/commands.js";
import { humanActor } from "../orchestrator/identity.js";
import { initializeStory } from "../orchestrator/init.js";
import { storyManifestPath } from "../orchestrator/paths.js";
import { storyStatus } from "../orchestrator/status.js";
import { recoverStaleLock, withLock } from "../orchestrator/lock.js";
import { storyDirectory } from "../orchestrator/paths.js";
import { recoverTransaction } from "../orchestrator/store.js";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { findRepoRoot } from "../repo.js";

interface Parsed { positionals: string[]; options: Map<string, string[]> }

async function main(): Promise<void> {
  const root = await findRepoRoot();
  const { result, format } = await executeCli(root, process.argv.slice(2));
  output(result, format);
  process.exitCode = result.ok ? 0 : 1;
}

export async function executeCli(root: string, args: string[]): Promise<{ result: CommandResult; format: string }> {
  const parsed = parse(args.filter((item) => item !== "--"));
  const command = parsed.positionals[0];
  if (!command) throw new HarnessInputError("SDD-ARGUMENT", usage());
  validatePublicInput(parsed);
  let result: CommandResult;
  switch (command) {
    case "init":
      result = await initializeStory(root, {
        title: required(parsed, "title"), changeType: required(parsed, "change-type"),
        components: many(parsed, "component"), affectedData: many(parsed, "affected-data"), affectedFlows: many(parsed, "affected-flow"),
        readPaths: many(parsed, "read-path"), writePaths: many(parsed, "write-path"), targetGaps: many(parsed, "target-gap"),
      });
      break;
    case "validate": {
      const story = required(parsed, "story");
      const report = await validateManifest(root, storyManifestPath(root, story));
      result = { ok: report.valid, command, story_id: story, changed: false, blockers: report.errors, next_actions: report.valid ? ["run sdd status"] : ["fix validation errors"], data: report };
      break;
    }
    case "status": result = await storyStatus(root, required(parsed, "story")); break;
    case "approve": result = await approveArtifact(root, required(parsed, "story"), required(parsed, "artifact"), required(parsed, "decision"), one(parsed, "identity"), one(parsed, "comment")); break;
    case "revise": result = await reviseArtifact(root, required(parsed, "story"), required(parsed, "artifact"), required(parsed, "reason"), one(parsed, "identity")); break;
    case "artifact": {
      if (parsed.positionals[1] !== "register") throw new HarnessInputError("SDD-ARGUMENT", "Usage: artifact register --story --type --path");
      result = await registerArtifact(root, required(parsed, "story"), required(parsed, "type"), required(parsed, "path"));
      break;
    }
    case "evidence": {
      if (parsed.positionals[1] !== "record") throw new HarnessInputError("SDD-ARGUMENT", "Usage: evidence record --story --condition --evidence");
      result = await registerEvidence(root, required(parsed, "story"), required(parsed, "condition"), manyRequired(parsed, "evidence"), await resolveActor(root, parsed));
      break;
    }
    case "next": result = await advanceStory(root, required(parsed, "story")); break;
    case "run": {
      const story = required(parsed, "story");
      if (one(parsed, "task")) result = await updateTask(root, story, required(parsed, "task"), required(parsed, "to"), one(parsed, "reason"), one(parsed, "identity"), await optionalExecutor(root, parsed), many(parsed, "evidence"));
      else if (one(parsed, "check")) result = await recordCheck(root, story, required(parsed, "check"), integer(parsed, "exit-code"), required(parsed, "evidence"));
      else throw new HarnessInputError("SDD-ARGUMENT", "run requires --task or --check");
      break;
    }
    case "review": result = await resolveReview(root, required(parsed, "story"), required(parsed, "decision"), one(parsed, "identity"), one(parsed, "cause"), one(parsed, "comment")); break;
    case "story": result = await updateStoryStatus(root, required(parsed, "story"), required(parsed, "to"), required(parsed, "reason"), one(parsed, "identity")); break;
    case "contract": {
      if (parsed.positionals[1] !== "validate") throw new HarnessInputError("SDD-ARGUMENT", "Usage: contract validate --schema --input");
      const report = await validateCatalogPayload(root, required(parsed, "schema"), required(parsed, "input"));
      result = { ok: report.valid, command: "contract validate", changed: false, blockers: report.errors, next_actions: report.valid ? [] : ["fix contract payload"], data: report };
      break;
    }
    case "recover": {
      const story = required(parsed, "story");
      const lock = path.join(storyDirectory(root, story), ".harness", "state.lock");
      const staleLock = await recoverStaleLock(lock);
      const transaction = await withLock(lock, () => recoverTransaction(root, story));
      result = { ok: true, command, story_id: story, changed: staleLock || transaction, blockers: [], next_actions: ["run sdd validate", "run sdd status"] };
      break;
    }
    default: throw new HarnessInputError("SDD-ARGUMENT", `Unknown command: ${command}\n${usage()}`);
  }
  return { result, format: one(parsed, "format") ?? "json" };
}

function parse(args: string[]): Parsed {
  const positionals: string[] = [];
  const options = new Map<string, string[]>();
  for (let index = 0; index < args.length; index += 1) {
    const item = args[index]!;
    if (!item.startsWith("--")) { positionals.push(item); continue; }
    const key = item.slice(2);
    const value = args[index + 1];
    if (!value || value.startsWith("--")) throw new HarnessInputError("SDD-ARGUMENT", `Option --${key} requires a value`);
    options.set(key, [...(options.get(key) ?? []), value]);
    index += 1;
  }
  return { positionals, options };
}

const repeatable = new Set(["component", "affected-data", "affected-flow", "read-path", "write-path", "target-gap", "evidence"]);
const common = ["format"];
const specs: Record<string, string[]> = {
  init: ["title", "change-type", "component", "affected-data", "affected-flow", "read-path", "write-path", "target-gap"],
  validate: ["story"], status: ["story"], next: ["story"],
  approve: ["story", "artifact", "decision", "identity", "comment"],
  revise: ["story", "artifact", "reason", "identity"],
  "artifact register": ["story", "type", "path"],
  "evidence record": ["story", "condition", "evidence", "actor-type", "identity"],
  run: ["story", "task", "check", "to", "reason", "identity", "executor-type", "executor-id", "exit-code", "evidence"],
  review: ["story", "decision", "identity", "cause", "comment"],
  story: ["story", "to", "reason", "identity"],
  recover: ["story"],
  "contract validate": ["schema", "input"],
};

function validatePublicInput(parsed: Parsed): void {
  const key = ["artifact", "evidence", "contract"].includes(parsed.positionals[0] ?? "") ? parsed.positionals.slice(0, 2).join(" ") : parsed.positionals[0]!;
  const allowed = specs[key];
  if (!allowed) throw new HarnessInputError("SDD-ARGUMENT", `Unknown command: ${key}`);
  const expectedPositionals = key.includes(" ") ? 2 : 1;
  if (parsed.positionals.length !== expectedPositionals) throw new HarnessInputError("SDD-ARGUMENT", `Unexpected positional argument: ${parsed.positionals.at(expectedPositionals) ?? ""}`);
  for (const [option, values] of parsed.options) {
    if (![...common, ...allowed].includes(option)) throw new HarnessInputError("SDD-ARGUMENT", `Unknown option --${option}`);
    if (values.length > 1 && !repeatable.has(option)) throw new HarnessInputError("SDD-ARGUMENT", `Option --${option} cannot be repeated`);
  }
  enumValue(parsed, "format", ["json", "text"]);
  enumValue(parsed, "change-type", ["feature", "remediation", "harness-docs"]);
  enumValue(parsed, "decision", ["APPROVED", "CHANGES_REQUESTED", "REJECTED"]);
  enumValue(parsed, "actor-type", ["human", "agent", "system"]);
  enumValue(parsed, "executor-type", ["human", "agent", "system"]);
  enumValue(parsed, "to", key === "story" ? ["ACTIVE", "BLOCKED", "CANCELLED"] : ["PENDING", "RUNNING", "COMPLETED", "FAILED", "BLOCKED"]);
  if (one(parsed, "task") && one(parsed, "check")) throw new HarnessInputError("SDD-ARGUMENT", "run accepts either --task or --check, not both");
}

function enumValue(parsed: Parsed, key: string, allowed: string[]): void {
  const value = one(parsed, key);
  if (value !== undefined && !allowed.includes(value)) throw new HarnessInputError("SDD-ARGUMENT", `Invalid --${key}: ${value}`);
}

function integer(parsed: Parsed, key: string): number {
  const value = required(parsed, key);
  if (!/^-?\d+$/.test(value)) throw new HarnessInputError("SDD-ARGUMENT", `--${key} must be an integer`);
  const parsedValue = Number(value);
  if (!Number.isSafeInteger(parsedValue)) throw new HarnessInputError("SDD-ARGUMENT", `--${key} must be a safe integer`);
  return parsedValue;
}

function one(parsed: Parsed, key: string): string | undefined { return parsed.options.get(key)?.at(-1); }
function many(parsed: Parsed, key: string): string[] { return parsed.options.get(key) ?? []; }
function required(parsed: Parsed, key: string): string { const value = one(parsed, key); if (!value) throw new HarnessInputError("SDD-ARGUMENT", `Missing --${key}`); return value; }
function manyRequired(parsed: Parsed, key: string): string[] { const value = many(parsed, key); if (!value.length) throw new HarnessInputError("SDD-ARGUMENT", `Missing --${key}`); return value; }

async function resolveActor(root: string, parsed: Parsed): Promise<Actor> {
  const type = one(parsed, "actor-type") ?? "human";
  if (type === "human") return humanActor(root, one(parsed, "identity"));
  if (!new Set(["agent", "system"]).has(type)) throw new HarnessInputError("SDD-ACTOR", `Invalid actor type: ${type}`);
  const identity = type === "system" ? one(parsed, "identity") ?? "sdd-cli" : required(parsed, "identity");
  return { type: type as "agent" | "system", identity };
}

async function optionalExecutor(root: string, parsed: Parsed): Promise<Actor | undefined> {
  const type = one(parsed, "executor-type");
  const identity = one(parsed, "executor-id");
  if (!type && !identity) return undefined;
  if (!type || !identity) throw new HarnessInputError("SDD-EXECUTOR", "Executor requires --executor-type and --executor-id");
  if (type === "human") return humanActor(root, identity);
  return { type: type as "agent" | "system", identity };
}

function output(result: CommandResult, format: string): void {
  if (format === "json") process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  else if (format === "text") process.stdout.write(`${result.ok ? "OK" : "BLOCKED"} ${result.story_id ?? ""} ${result.stage ?? ""} ${result.status ?? ""}\n${result.blockers.map((item) => `${item.code}: ${item.message}`).join("\n")}\n`);
  else throw new HarnessInputError("SDD-FORMAT", `Unsupported format: ${format}`);
}

function usage(): string { return "Usage: sdd <init|validate|status|approve|revise|artifact|evidence|next|run|review|story|contract|recover> [options]"; }

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then(() => process.stdout.end(() => process.exit(process.exitCode ?? 0))).catch((error: unknown) => {
    const known = error instanceof HarnessInputError;
    process.stderr.write(`${JSON.stringify({ ok: false, changed: false, blockers: [{ code: known ? error.code : "SDD-UNEXPECTED", instance_path: "/", message: error instanceof Error ? error.message : String(error) }], next_actions: ["correct command input and retry"] }, null, 2)}\n`);
    process.stderr.end(() => process.exit(2));
  });
}
