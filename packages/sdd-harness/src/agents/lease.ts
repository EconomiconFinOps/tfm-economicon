import { mkdir, open, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { HarnessInputError } from "../errors.js";
import { storyDirectory } from "../orchestrator/paths.js";

const OWNER_START_MS = Math.round(Date.now() - process.uptime() * 1000);
export interface AgentLease { run_id: string; agent_id: string; pid: number; process_start_ms: number; hostname: string; created_at: string }

export function agentLeasePath(root: string, storyId: string): string { return path.join(storyDirectory(root, storyId), ".harness", "agent.lease.json"); }

export async function acquireAgentLease(root: string, storyId: string, runId: string, agentId: string): Promise<AgentLease> {
  const file = agentLeasePath(root, storyId);
  await mkdir(path.dirname(file), { recursive: true });
  const lease: AgentLease = { run_id: runId, agent_id: agentId, pid: process.pid, process_start_ms: OWNER_START_MS, hostname: os.hostname(), created_at: new Date().toISOString() };
  try { const handle = await open(file, "wx"); await handle.writeFile(JSON.stringify(lease)); await handle.close(); return lease; }
  catch { throw new HarnessInputError("SDD-AGENT-ACTIVE", `An agent lease already exists for ${storyId}`); }
}

export async function releaseAgentLease(root: string, storyId: string, lease: AgentLease): Promise<void> {
  const current = await readLease(root, storyId);
  if (!current || current.pid !== lease.pid || current.process_start_ms !== lease.process_start_ms || current.run_id !== lease.run_id) throw new HarnessInputError("SDD-AGENT-LEASE", "Agent lease ownership changed");
  await rm(agentLeasePath(root, storyId));
}

export async function assertMutationAllowed(root: string, storyId: string): Promise<void> {
  const lease = await readLease(root, storyId);
  if (!lease) return;
  if (lease.pid === process.pid && lease.process_start_ms === OWNER_START_MS && lease.hostname === os.hostname()) return;
  throw new HarnessInputError(isAlive(lease.pid) ? "SDD-AGENT-ACTIVE" : "SDD-AGENT-LEASE-STALE", `Story is reserved by agent run ${lease.run_id}`);
}

export async function recoverAgentLease(root: string, storyId: string): Promise<AgentLease | null> {
  const lease = await readLease(root, storyId);
  if (!lease) return null;
  if (lease.hostname !== os.hostname() || isAlive(lease.pid)) throw new HarnessInputError("SDD-AGENT-ACTIVE", `Agent process ${lease.pid} is still live or cannot be verified`);
  await rm(agentLeasePath(root, storyId));
  return lease;
}

export async function readLease(root: string, storyId: string): Promise<AgentLease | null> {
  try {
    const value = JSON.parse(await readFile(agentLeasePath(root, storyId), "utf8")) as AgentLease;
    if (!value.run_id || !value.agent_id || !Number.isInteger(value.pid) || !Number.isFinite(value.process_start_ms) || !value.hostname || !value.created_at) throw new HarnessInputError("SDD-AGENT-LEASE", "Agent lease is invalid");
    return value;
  } catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return null; throw error; }
}
function isAlive(pid: number): boolean { try { process.kill(pid, 0); return true; } catch (error) { return (error as NodeJS.ErrnoException).code === "EPERM"; } }
