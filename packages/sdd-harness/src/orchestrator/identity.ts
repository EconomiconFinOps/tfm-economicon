import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { HarnessInputError } from "../errors.js";
import type { Actor } from "../types.js";

const execFileAsync = promisify(execFile);

export async function humanActor(root: string, override?: string): Promise<Actor> {
  if (override?.trim()) return { type: "human", identity: override.trim() };
  try {
    const [{ stdout: name }, { stdout: email }] = await Promise.all([
      execFileAsync("git", ["config", "user.name"], { cwd: root }),
      execFileAsync("git", ["config", "user.email"], { cwd: root }),
    ]);
    if (!name.trim() || !email.trim()) throw new Error("missing Git identity");
    return { type: "human", identity: `${name.trim()} <${email.trim()}>` };
  } catch {
    throw new HarnessInputError("SDD-HUMAN-IDENTITY", "Set git user.name/user.email or pass --identity");
  }
}
