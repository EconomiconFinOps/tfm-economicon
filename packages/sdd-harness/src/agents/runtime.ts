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
export interface RuntimeResult { execution: CodexExecution; events: string; timed_out: boolean; malformed: boolean }

export async function executeCodexAgent(root: string, run: AnyRecord, definition: AgentDefinition, policy: AgentPolicy, catalog: AgentCatalog, permissionToml: string, profile: PermissionProfile): Promise<RuntimeResult> {
  const { command, version } = await resolveCodexCommand(root);
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
    events: parsed.events.map((event) => JSON.stringify(event)).join("\n") + (parsed.events.length ? "\n" : ""), timed_out: result.timedOut, malformed: parsed.malformed,
  };
}

export interface CodexCommand { file: string; prefix: string[]; label: string }
async function resolveCodexCommand(root: string): Promise<{ command: CodexCommand; version: { stdout: string } }> {
  const configured = process.env.SDD_CODEX_BIN;
  if (configured) {
    if (!path.isAbsolute(configured)) throw new HarnessInputError("SDD-CODEX-BIN", "SDD_CODEX_BIN must be absolute");
    if (configured.endsWith(".cmd") || configured.endsWith(".bat")) throw new HarnessInputError("SDD-CODEX-BIN", "Shell wrappers are forbidden; use codex.exe or codex.js");
    const command = commandFor(configured, "SDD_CODEX_BIN");
    const probe = await probeCommand(command, root);
    if (!probe.version) throw new HarnessInputError("SDD-CODEX-VERSION", `Configured Codex CLI is unusable: ${probe.reason}`);
    return { command, version: { stdout: probe.stdout } };
  }
  const candidates: CodexCommand[] = [];
  const names = process.platform === "win32" ? ["codex.exe"] : ["codex"];
  for (const directory of (process.env.PATH ?? "").split(path.delimiter).filter(Boolean)) for (const name of names) {
    const file = path.join(directory.replace(/^"|"$/g, ""), name); if (existsSync(file)) candidates.push(commandFor(file, `PATH:${path.basename(directory)}`));
  }
  if (process.platform === "win32" && process.env.APPDATA) {
    const script = path.join(process.env.APPDATA, "npm", "node_modules", "@openai", "codex", "bin", "codex.js");
    if (existsSync(script)) candidates.push(commandFor(script, "npm-global"));
  }
  const unique = [...new Map(candidates.map((item) => [`${item.file}\0${item.prefix.join("\0")}`, item])).values()];
  return selectCompatibleCodex(unique, root);
}

export async function selectCompatibleCodex(candidates: CodexCommand[], root: string): Promise<{ command: CodexCommand; version: { stdout: string } }> {
  const probes = await Promise.all(candidates.map(async (command) => ({ command, probe: await probeCommand(command, root) })));
  const compatible = probes.filter((item) => item.probe.version).sort((a, b) => compareVersion(b.probe.version!, a.probe.version!) || lexical(a.command.label, b.command.label));
  if (compatible[0]) return { command: compatible[0].command, version: { stdout: compatible[0].probe.stdout } };
  const details = probes.map((item) => `${item.command.label}: ${item.probe.reason}`).join("; ") || "no candidates discovered";
  throw new HarnessInputError("SDD-CODEX-VERSION", `Codex CLI >= 0.134.0 was not found (${details})`);
}

function commandFor(file: string, label: string): CodexCommand { return file.endsWith(".js") || file.endsWith(".mjs") ? { file: process.execPath, prefix: [file], label } : { file, prefix: [], label }; }
async function probeCommand(command: CodexCommand, root: string): Promise<{ version: [number, number, number] | null; stdout: string; reason: string }> {
  try {
    const result = await capture(command.file, [...command.prefix, "--version"], 10_000, 16_384, 16_384, root);
    const version = parsedVersion(result.stdout);
    if (result.code !== 0) return { version: null, stdout: result.stdout, reason: `exit ${result.code ?? "null"}` };
    if (result.timedOut) return { version: null, stdout: result.stdout, reason: "timeout" };
    if (!version || !compatibleVersionTuple(version)) return { version: null, stdout: result.stdout, reason: `incompatible ${result.stdout.trim() || "unknown"}` };
    return { version, stdout: result.stdout, reason: "compatible" };
  } catch (error) { return { version: null, stdout: "", reason: error instanceof Error ? error.message.slice(0, 200) : "probe failed" }; }
}

function prompt(run: AnyRecord, agentId: string, profile: PermissionProfile): string {
  return [
    `Execute the prepared SDD run ${run.run_id} as agent ${agentId}.`,
    `Read ${run.input_path} and invoke only the skill named in that input.`,
    `Write the contractual skill output to ${run.output_path} and candidates only below ${path.posix.dirname(run.output_path)}/artifacts/.`,
    `Allowed product write paths: ${profile.write_paths.filter((item) => !item.includes("/.harness/skill-runs/")).join(", ") || "none"}.`,
    "Do not approve, advance stages, run external checks, request permissions, use network access, or spawn subagents.",
    `Your final response must be the receipt JSON for run ${run.run_id}; status must match output.json and output_path must be ${run.output_path}.`,
    `The receipt must include input_sha256 ${run.input_sha256} and output_sha256 computed from the exact output.json bytes.`,
  ].join("\n");
}

async function capture(file: string, args: string[], timeoutMs: number, stdoutLimit: number, stderrLimit: number, cwd: string): Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, { shell: false, windowsHide: true, cwd, stdio: ["ignore", "pipe", "pipe"], detached: process.platform !== "win32" });
    const out: Buffer[] = []; const err: Buffer[] = []; let outBytes = 0; let errBytes = 0; let timedOut = false; let overflow: string | null = null; let settled = false;
    const terminate = (): void => terminateTree(child.pid);
    const append = (chunk: Buffer, target: Buffer[], current: number, limit: number, stream: string): number => {
      const remaining = Math.max(0, limit - current); if (remaining) target.push(chunk.subarray(0, remaining));
      if (chunk.length > remaining && !overflow) { overflow = stream; terminate(); }
      return current + Math.min(chunk.length, remaining);
    };
    const timer = setTimeout(() => { timedOut = true; terminate(); }, timeoutMs);
    child.stdout.on("data", (chunk: Buffer) => { outBytes = append(chunk, out, outBytes, stdoutLimit, "stdout"); });
    child.stderr.on("data", (chunk: Buffer) => { errBytes = append(chunk, err, errBytes, stderrLimit, "stderr"); });
    child.on("error", (error) => { if (settled) return; settled = true; clearTimeout(timer); reject(new HarnessInputError("SDD-CODEX-SPAWN", error.message)); });
    child.on("close", (code) => { if (settled) return; settled = true; clearTimeout(timer); const stdout = Buffer.concat(out).toString("utf8"); const stderr = Buffer.concat(err).toString("utf8"); if (overflow) reject(new HarnessInputError("SDD-CODEX-OUTPUT-LIMIT", `${overflow} exceeded configured limit`)); else resolve({ code, stdout, stderr, timedOut }); });
  });
}

function terminateTree(pid: number | undefined): void {
  if (!pid) return;
  if (process.platform === "win32") {
    const killer = spawn("taskkill.exe", ["/PID", String(pid), "/T", "/F"], { shell: false, windowsHide: true, stdio: "ignore" }); killer.unref();
    const force = setTimeout(() => { try { process.kill(pid, "SIGKILL"); } catch { /* already gone */ } }, 2_000); force.unref();
  } else {
    try { process.kill(-pid, "SIGTERM"); } catch { /* already gone */ }
    const force = setTimeout(() => { try { process.kill(-pid, "SIGKILL"); } catch { /* already gone */ } }, 2_000); force.unref();
  }
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
function parsedVersion(value: string): [number, number, number] | null { const match = value.match(/codex(?:-cli)?\s+(\d+)\.(\d+)\.(\d+)/i); return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : null; }
function compatibleVersionTuple(value: [number, number, number]): boolean { return value[0] > 0 || value[1] >= 134; }
function compareVersion(a: [number, number, number], b: [number, number, number]): number { return a[0] - b[0] || a[1] - b[1] || a[2] - b[2]; }
function lexical(a: string, b: string): number { return a < b ? -1 : a > b ? 1 : 0; }
