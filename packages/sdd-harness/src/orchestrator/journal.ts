import { randomUUID } from "node:crypto";

import { canonicalJson, sha256Text } from "../hash.js";
import type { Actor, AnyRecord, JournalEvent, ValidationIssue } from "../types.js";

export function createJournalEvent(manifest: AnyRecord, eventType: string, actor: Actor, data: AnyRecord): JournalEvent {
  const unsigned = {
    event_id: randomUUID(),
    event_type: eventType,
    sequence: manifest.journal.head_sequence + 1,
    previous_event_hash: manifest.journal.head_hash,
    occurred_at: new Date().toISOString(),
    actor,
    story_id: manifest.story.id,
    correlation_id: manifest.correlation_id,
    data,
  };
  return { ...unsigned, event_hash: sha256Text(canonicalJson(unsigned)) } as JournalEvent;
}

export function validateJournalEvents(lines: string[], manifest: AnyRecord): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  let previous: string | null = null;
  let sequence = 0;
  for (const [index, line] of lines.entries()) {
    try {
      const event = JSON.parse(line) as AnyRecord;
      const { event_hash: eventHash, ...unsigned } = event;
      sequence += 1;
      if (event.sequence !== sequence || event.previous_event_hash !== previous) {
        issues.push({ code: "SDD-JOURNAL-CHAIN", instance_path: `/journal/${index}`, message: "Journal sequence or previous hash is invalid" });
      }
      if (sha256Text(canonicalJson(unsigned)) !== eventHash) {
        issues.push({ code: "SDD-JOURNAL-HASH", instance_path: `/journal/${index}/event_hash`, message: "Journal event hash is invalid" });
      }
      if (event.story_id !== manifest.story.id || event.correlation_id !== manifest.correlation_id) {
        issues.push({ code: "SDD-JOURNAL-CONTEXT", instance_path: `/journal/${index}`, message: "Journal event context does not match manifest" });
      }
      previous = eventHash;
    } catch {
      issues.push({ code: "SDD-JOURNAL-JSON", instance_path: `/journal/${index}`, message: "Journal line is not valid JSON" });
    }
  }
  if (sequence !== manifest.journal.head_sequence || previous !== manifest.journal.head_hash) {
    issues.push({ code: "SDD-JOURNAL-HEAD", instance_path: "/journal", message: "Manifest journal head does not match journal contents" });
  }
  return issues;
}
