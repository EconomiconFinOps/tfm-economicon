import { mkdir, open, readFile, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";

import { HarnessInputError } from "../errors.js";

export async function withLock<T>(lockPath: string, action: () => Promise<T>): Promise<T> {
  await mkdir(path.dirname(lockPath), { recursive: true });
  let handle;
  try {
    handle = await open(lockPath, "wx");
    await handle.writeFile(JSON.stringify({ pid: process.pid, hostname: os.hostname(), created_at: new Date().toISOString() }));
  } catch {
    let owner = "unknown";
    try { owner = await readFile(lockPath, "utf8"); } catch { /* no-op */ }
    throw new HarnessInputError("SDD-LOCKED", `Harness state is locked: ${lockPath} (${owner})`);
  }
  try {
    return await action();
  } finally {
    await handle.close();
    await rm(lockPath, { force: true });
  }
}

export async function recoverStaleLock(lockPath: string, minimumAgeMs = 30_000): Promise<boolean> {
  let raw: string;
  try { raw = await readFile(lockPath, "utf8"); } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return false;
    throw error;
  }
  let owner: { pid?: number; hostname?: string; created_at?: string };
  try { owner = JSON.parse(raw); } catch { throw new HarnessInputError("SDD-LOCK-INVALID", "Lock metadata is not valid JSON"); }
  if (!Number.isInteger(owner.pid) || owner.hostname !== os.hostname() || !owner.created_at) throw new HarnessInputError("SDD-LOCK-OWNER", "Lock owner cannot be proven stale on this host");
  const age = Date.now() - Date.parse(owner.created_at);
  if (!Number.isFinite(age) || age < minimumAgeMs) throw new HarnessInputError("SDD-LOCK-LIVE", "Lock is too recent to recover");
  if (isProcessAlive(owner.pid!)) throw new HarnessInputError("SDD-LOCK-LIVE", `Lock belongs to live process ${owner.pid}`);
  await rm(lockPath);
  return true;
}

function isProcessAlive(pid: number): boolean {
  try { process.kill(pid, 0); return true; } catch (error) { return (error as NodeJS.ErrnoException).code === "EPERM"; }
}
