import { appendFile, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { parse, stringify } from "yaml";

import { HarnessInputError } from "./errors.js";

export async function readText(path: string): Promise<string> {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    throw new HarnessInputError("SDD-READ-ERROR", `Cannot read ${path}: ${messageOf(error)}`);
  }
}

export async function readYaml<T>(path: string): Promise<T> {
  const content = await readText(path);
  try {
    return parse(content) as T;
  } catch (error) {
    throw new HarnessInputError("SDD-YAML-ERROR", `Cannot parse ${path}: ${messageOf(error)}`);
  }
}

export async function writeTextAtomic(filePath: string, content: string): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  try {
    await writeFile(temporary, content, { encoding: "utf8", flag: "wx" });
    await rename(temporary, filePath);
  } finally {
    await rm(temporary, { force: true });
  }
}

export async function writeYamlAtomic(filePath: string, value: unknown): Promise<void> {
  await writeTextAtomic(filePath, stringify(value, { lineWidth: 0 }));
}

export async function appendLine(filePath: string, value: string): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  await appendFile(filePath, `${value}\n`, "utf8");
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
