import { spawn } from "node:child_process";
import { mkdir, readFile, rm } from "node:fs/promises";
import path from "node:path";

import { sha256Text } from "../hash.js";
import { findRepoRoot } from "../repo.js";

const root = await findRepoRoot();
const smoke = ".sdd/.codex-smoke";
const marker = `${smoke}/allowed.txt`;
const protectedFile = "docs/ARCHITECTURE.md";
const before = sha256Text(await readFile(path.join(root, protectedFile), "utf8"));
await mkdir(path.join(root, smoke), { recursive: true });
try {
  const executable = process.env.SDD_CODEX_BIN ?? (process.platform === "win32" ? "codex.exe" : "codex");
  const command = executable.endsWith(".js") || executable.endsWith(".mjs") ? process.execPath : executable;
  const prefix = command === process.execPath ? [executable] : [];
  const filesystem = `{":minimal"="read",":workspace_roots"={"."="read",${JSON.stringify(marker)}="write",${JSON.stringify(protectedFile)}="read"}}`;
  const args = [...prefix, "exec", "--ephemeral", "--json", "-C", root, "-c", 'approval_policy="never"', "-c", 'default_permissions="sdd-smoke"', "-c", `permissions.sdd-smoke.filesystem=${filesystem}`, "-c", "permissions.sdd-smoke.network.enabled=false", `Write exactly 'allowed' to ${marker}. Then attempt to append text to ${protectedFile}; the second operation must be denied by the sandbox. Do not request permissions. Finish after both attempts.`];
  const result = await run(command, args, root, 120_000);
  let allowed = ""; try { allowed = await readFile(path.join(root, marker), "utf8"); } catch { /* reported below */ }
  const after = sha256Text(await readFile(path.join(root, protectedFile), "utf8"));
  if (result.code !== 0 || allowed.trim() !== "allowed" || before !== after) throw new Error(`Codex sandbox smoke failed (exit=${result.code}, allowed=${allowed.trim()}, protected_unchanged=${before === after})\n${result.stderr.slice(0, 2000)}`);
  process.stdout.write(`${JSON.stringify({ ok: true, allowed_write: marker, denied_write: protectedFile, protected_unchanged: true }, null, 2)}\n`);
} finally {
  await rm(path.join(root, smoke), { recursive: true, force: true });
}

function run(file: string, args: string[], cwd: string, timeoutMs: number): Promise<{ code: number | null; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, { cwd, shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] }); let stderr = "";
    const timer = setTimeout(() => child.kill(), timeoutMs);
    child.stderr.on("data", (chunk) => { stderr += String(chunk); }); child.stdout.resume();
    child.on("error", reject); child.on("close", (code) => { clearTimeout(timer); resolve({ code, stderr }); });
  });
}
