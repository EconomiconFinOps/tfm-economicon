import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { parse } from "yaml";

import { sha256File } from "../src/hash.js";
import { HarnessBlockedError } from "../src/errors.js";
import { createJournalEvent } from "../src/orchestrator/journal.js";
import { initializeStory } from "../src/orchestrator/init.js";
import { recoverStaleLock, withLock } from "../src/orchestrator/lock.js";
import { mutateStory, recoverTransaction } from "../src/orchestrator/store.js";
import { findRepoRoot } from "../src/repo.js";

const temporary: string[] = [];
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("transaction safety", () => {
  it("rejects a concurrent state lock", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-lock-"));
    temporary.push(root);
    const lock = path.join(root, "state.lock");
    let release!: () => void;
    const waiting = new Promise<void>((resolve) => { release = resolve; });
    const first = withLock(lock, () => waiting);
    await new Promise((resolve) => setTimeout(resolve, 20));
    await expect(withLock(lock, async () => undefined)).rejects.toMatchObject({ code: "SDD-LOCKED" });
    release();
    await first;
  });

  it("recovers only a proven stale local lock", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-lock-"));
    temporary.push(root);
    const stale = path.join(root, "stale.lock");
    await writeFile(stale, JSON.stringify({ pid: 2147483000, hostname: os.hostname(), created_at: "2000-01-01T00:00:00.000Z" }));
    expect(await recoverStaleLock(stale)).toBe(true);
    const live = path.join(root, "live.lock");
    await writeFile(live, JSON.stringify({ pid: process.pid, hostname: os.hostname(), created_at: "2000-01-01T00:00:00.000Z" }));
    await expect(recoverStaleLock(live)).rejects.toMatchObject({ code: "SDD-LOCK-LIVE" });
    expect(await readFile(live, "utf8")).toContain(String(process.pid));
  });

  it("rolls a persisted transaction forward after interruption", async () => {
    const repository = await findRepoRoot();
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-recovery-"));
    temporary.push(root);
    await cp(path.join(repository, ".sdd"), path.join(root, ".sdd"), { recursive: true });
    await mkdir(path.join(root, "docs"), { recursive: true });
    for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) {
      await cp(path.join(repository, "docs", name), path.join(root, "docs", name));
    }
    await initializeStory(root, {
      title: "Recovery", changeType: "harness-docs", components: ["sdd-harness"],
      affectedData: [], affectedFlows: ["workflow"], readPaths: ["docs/**"],
      writePaths: ["packages/sdd-harness/**"], targetGaps: [],
    });
    const storyDir = path.join(root, "SPEC/HU-001");
    const manifestPath = path.join(storyDir, "manifest.yaml");
    const manifest = parse(await readFile(manifestPath, "utf8"));
    const sourceManifestSha256 = await sha256File(manifestPath);
    const event = createJournalEvent(manifest, "story.blocked", { type: "system", identity: "test" }, { reason: "interrupted" });
    const targetManifest = structuredClone(manifest);
    targetManifest.workflow.status = "BLOCKED";
    targetManifest.journal.head_sequence = event.sequence;
    targetManifest.journal.head_hash = event.event_hash;
    await mkdir(path.join(storyDir, ".harness"), { recursive: true });
    const intentPath = path.join(storyDir, ".harness/transaction.json");
    const intent = {
      story_id: "HU-001", correlation_id: manifest.correlation_id,
      source_manifest_sha256: sourceManifestSha256, target_manifest: targetManifest,
      event, extra_writes: [],
    };
    await writeFile(intentPath, JSON.stringify({ ...intent, story_id: "HU-999" }), "utf8");
    await expect(recoverTransaction(root, "HU-001")).rejects.toMatchObject({ code: "SDD-TRANSACTION-CONTEXT" });
    await writeFile(intentPath, JSON.stringify({ ...intent, source_manifest_sha256: "0".repeat(64) }), "utf8");
    await expect(recoverTransaction(root, "HU-001")).rejects.toMatchObject({ code: "SDD-TRANSACTION-SOURCE" });
    await writeFile(intentPath, JSON.stringify({ ...intent, extra_writes: [{ path: "../outside", content: "x" }] }), "utf8");
    await expect(recoverTransaction(root, "HU-001")).rejects.toMatchObject({ code: "SDD-PATH-TRAVERSAL" });
    await writeFile(intentPath, JSON.stringify(intent), "utf8");
    expect(await recoverTransaction(root, "HU-001")).toBe(true);
    expect(parse(await readFile(manifestPath, "utf8")).workflow.status).toBe("BLOCKED");
    expect((await readFile(path.join(storyDir, "journal.ndjson"), "utf8")).trim().split(/\r?\n/)).toHaveLength(2);
  });

  it("rolls back a staged manifest that would not validate", async () => {
    const repository = await findRepoRoot();
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-rollback-"));
    temporary.push(root);
    await cp(path.join(repository, ".sdd"), path.join(root, ".sdd"), { recursive: true });
    await mkdir(path.join(root, "docs"), { recursive: true });
    for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) await cp(path.join(repository, "docs", name), path.join(root, "docs", name));
    await initializeStory(root, { title: "Rollback", changeType: "harness-docs", components: [], affectedData: [], affectedFlows: [], readPaths: [], writePaths: [], targetGaps: [] });
    const manifestPath = path.join(root, "SPEC/HU-001/manifest.yaml");
    const journalPath = path.join(root, "SPEC/HU-001/journal.ndjson");
    const before = [await readFile(manifestPath, "utf8"), await readFile(journalPath, "utf8")];
    await expect(mutateStory(root, "HU-001", async (manifest) => {
      manifest.workflow.stage = "INVALID";
      return { event_type: "invalid", event_data: {}, actor: { type: "system", identity: "test" }, result: { ok: true, command: "test", changed: true, blockers: [], next_actions: [] } };
    })).rejects.toBeInstanceOf(HarnessBlockedError);
    expect([await readFile(manifestPath, "utf8"), await readFile(journalPath, "utf8")]).toEqual(before);
  });
});
