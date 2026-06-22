import { spawn } from "node:child_process";
import path from "node:path";
import { existsSync } from "node:fs";

import { loadConfig } from "../config.js";
import { HarnessInputError } from "../errors.js";
import { sha256Text } from "../hash.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord } from "../types.js";
import type { AgentCatalog, AgentDefinition, AgentPolicy } from "./catalog.js";
import type { PermissionProfile } from "./permissions.js";

export interface CodexExecution {
  provider: "codex-cli"; status: "COMPLETED" | "FAILED"; started_at: string; completed_at: string; duration_ms: number;
  exit_code: number | null; codex_version: string | null; model: string | null; thread_id: string | null; usage: AnyRecord | null;
  stdout_sha256: string; stderr_excerpt: string;
}
export interface RuntimeResult { execution: CodexExecution; events: string; timed_out: boolean }

export async function executeCodexAgent(root: string, run: AnyRecord, definition: AgentDefinition, policy: AgentPolicy, catalog: AgentCatalog, permissionToml: string, profile: PermissionProfile): Promise<RuntimeResult> {
  const command = resolveCodexCommand();
  const version = await capture(command.file, [...command.prefix, "--version"], 10_000, 16_384, 16_384, root);
  if (version.code !== 0 || version.timedOut || !compatibleVersion(version.stdout)) throw new HarnessInputError("SDD-CODEX-VERSION", `Codex CLI >= 0.134.0 is required; found: ${version.stdout.trim() || "unknown"}`);
  const config = await loadConfig(root);
  const receiptPath = `${path.posix.dirname(run.output_path)}/receipt.json`;
  const args = [...command.prefix, "exec", "--ephemeral", "--json", "--output-schema", resolveConcreteRepoPath(root, config.agents.receipt_schema), "-o", resolveConcreteRepoPath(root, receiptPath), "-C", root,
    "-c", 'approval_policy="never"', "-c", 'default_permissions="sdd-agent"', "-c", `permissions.sdd-agent.filesystem=${permissionToml}`,
    "-c", "permissions.sdd-agent.network.enabled=false", "-c", `developer_instructions=${JSON.stringify(definition.developer_instructions)}`,
    "-c", `model_reasoning_effort=${JSON.stringify(policy.reasoning_effort)}`, prompt(run, definition.name, profile)];
  const started = new Date();
  const result = await capture(command.file, args, policy.timeout_seconds * 1000, catalog.runtime.max_output_bytes, catalog.runtime.max_error_bytes, root);
  const completed = new Date();
  const parsed = normalizeEvents(result.stdout);
  return {
    execution: { provider: "codex-cli", status: result.code === 0 && !result.timedOut && !parsed.malformed ? "COMPLETED" : "FAILED", started_at: started.toISOString(), completed_at: completed.toISOString(), duration_ms: completed.getTime() - started.getTime(), exit_code: result.code, codex_version: version.stdout.trim() || null, model: parsed.model, thread_id: parsed.threadId, usage: parsed.usage, stdout_sha256: sha256Text(result.stdout), stderr_excerpt: sanitize(parsed.malformed ? `Malformed Codex JSONL event stream. ${result.stderr}` : result.stderr, catalog.runtime.max_error_bytes) },
    events: parsed.events.map((event) => JSON.stringify(event)).join("\n") + (parsed.events.length ? "\n" : ""), timed_out: result.timedOut,
  };
}

function resolveCodexCommand(): { file: string; prefix: string[] } {
  const configured = process.env.SDD_CODEX_BIN;
  if (configured) {
    if (!path.isAbsolute(configured)) throw new HarnessInputError("SDD-CODEX-BIN", "SDD_CODEX_BIN must be absolute");
    if (configured.endsWith(".cmd") || configured.endsWith(".bat")) throw new HarnessInputError("SDD-CODEX-BIN", "Shell wrappers are forbidden; use codex.exe or codex.js");
    return configured.endsWith(".js") || configured.endsWith(".mjs") ? { file: process.execPath, prefix: [configured] } : { file: configured, prefix: [] };
  }
  if (process.platform === "win32" && process.env.APPDATA) {
    const script = path.join(process.env.APPDATA, "npm", "node_modules", "@openai", "codex", "bin", "codex.js");
    if (existsSync(script)) return { file: process.execPath, prefix: [script] };
  }
  return { file: process.platform === "win32" ? "codex.exe" : "codex", prefix: [] };
}

function prompt(run: AnyRecord, agentId: string, profile: PermissionProfile): string {
  return [
    `Execute the prepared SDD run ${run.run_id} as agent ${agentId}.`,
    `Read ${run.input_path} and invoke only the skill named in that input.`,
    `Write the contractual skill output to ${run.output_path} and candidates only below ${path.posix.dirname(run.output_path)}/artifacts/.`,
    `Allowed product write paths: ${profile.write_paths.filter((item) => !item.includes("/.harness/skill-runs/")).join(", ") || "none"}.`,
    "Do not approve, advance stages, run external checks, request permissions, use network access, or spawn subagents.",
    `Your final response must be the receipt JSON for run ${run.run_id}; status must match output.json and output_path must be ${run.output_path}.`,
  ].join("\n");
}

async function capture(file: string, args: string[], timeoutMs: number, stdoutLimit: number, stderrLimit: number, cwd: string): Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, { shell: false, windowsHide: true, cwd, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = ""; let stderr = ""; let timedOut = false; let overflow: string | null = null;
    const timer = setTimeout(() => { timedOut = true; child.kill(); }, timeoutMs);
    child.stdout.on("data", (chunk) => { if (Buffer.byteLength(stdout) < stdoutLimit) stdout += String(chunk); else { overflow = "stdout"; child.kill(); } });
    child.stderr.on("data", (chunk) => { if (Buffer.byteLength(stderr) < stderrLimit) stderr += String(chunk); else { overflow = "stderr"; child.kill(); } });
    child.on("error", (error) => { clearTimeout(timer); reject(new HarnessInputError("SDD-CODEX-SPAWN", error.message)); });
    child.on("close", (code) => { clearTimeout(timer); if (overflow) reject(new HarnessInputError("SDD-CODEX-OUTPUT-LIMIT", `${overflow} exceeded configured limit`)); else resolve({ code, stdout, stderr, timedOut }); });
  });
}

function normalizeEvents(raw: string): { events: AnyRecord[]; threadId: string | null; model: string | null; usage: AnyRecord | null; malformed: boolean } {
  const events: AnyRecord[] = []; let threadId: string | null = null; let model: string | null = null; let usage: AnyRecord | null = null; let malformed = false;
  for (const line of raw.split(/\r?\n/).filter(Boolean)) {
    let event: AnyRecord; try { event = JSON.parse(line); } catch { malformed = true; continue; }
    if (event.type === "thread.started") { threadId = event.thread_id ?? null; model = event.model ?? model; events.push({ type: event.type, thread_id: threadId, model }); }
    else if (["turn.started", "turn.completed", "turn.failed", "error"].includes(event.type)) { if (event.usage) usage = event.usage; events.push({ type: event.type, usage: event.usage ?? undefined, code: event.code ?? undefined }); }
  }
  return { events, threadId, model, usage, malformed };
}
function sanitize(value: string, limit: number): string { return value.replace(/(api[_-]?key|token|secret|password)\s*[=:]\s*\S+/gi, "$1=[REDACTED]").slice(0, limit); }
function compatibleVersion(value: string): boolean {
  const match = value.match(/codex(?:-cli)?\s+(\d+)\.(\d+)\.(\d+)/i); if (!match) return false;
  const [major, minor] = [Number(match[1]), Number(match[2])]; return major > 0 || minor >= 134;
}
