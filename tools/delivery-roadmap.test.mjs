import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const roadmap = JSON.parse(
  fs.readFileSync(path.join(root, "docs", "planning", "JUP-080-milestones.json"), "utf8"),
);
const narrative = fs.readFileSync(
  path.join(root, "docs", "planning", "JUP-080-delivery-roadmap.md"),
  "utf8",
);
const snapshot = JSON.parse(fs.readFileSync(
  path.join(root, "docs", "planning", "JUP-080-p0-snapshot.json"), "utf8",
));

test("pins delivery, freeze and defense dates in chronological order", () => {
  assert.equal(roadmap.internal_code_freeze, "2026-10-09");
  assert.equal(roadmap.internal_document_freeze, "2026-10-16");
  assert.equal(roadmap.delivery_date, "2026-10-23");
  assert.equal(roadmap.defense_rehearsal, "2026-10-27");
  assert.equal(roadmap.defense_date, "2026-10-29");

  const dates = roadmap.milestones.map(({ date }) => date);
  assert.deepEqual(dates, [...dates].sort());
  assert.equal(new Set(dates).size, dates.length);
});

test("assigns every P0 task in the dated snapshot exactly once", () => {
  const assigned = roadmap.milestones.flatMap(({ task_ids }) => task_ids);
  const expectedP0 = roadmap.p0_snapshot.task_ids;

  assert.equal(roadmap.p0_snapshot.source, "https://trello.com/b/CawMVPoy/economicon");
  assert.equal(roadmap.p0_snapshot.captured_at, roadmap.as_of);
  assert.equal(roadmap.p0_snapshot.count, snapshot.cards.length);
  assert.equal(expectedP0.length, roadmap.p0_snapshot.count);
  assert.equal(new Set(expectedP0).size, expectedP0.length);
  assert.deepEqual(
    expectedP0.filter((id) => ["JUP-085", "JUP-086", "JUP-087"].includes(id)),
    ["JUP-085", "JUP-086", "JUP-087"],
  );
  assert.equal(new Set(assigned).size, assigned.length);
  assert.deepEqual([...assigned].sort(), [...expectedP0].sort());
  assert.deepEqual([...expectedP0].sort(), snapshot.cards.map(c => c.task_id).sort());
  assert.equal(roadmap.p0_snapshot.queried_at, snapshot.queried_at);
});

test("recovery covers open P0 only and never backdates completed cards", () => {
  const targets = roadmap.recovery_plan.targets;
  const open = snapshot.cards.filter(c => !c.state.startsWith("70"));
  assert.deepEqual(targets.map(t => t.task_id).sort(), open.map(c => c.task_id).sort());
  assert.equal(new Set(targets.map(t => t.task_id)).size, targets.length);
  for (const target of targets) {
    assert.match(target.date, /^\d{4}-\d{2}-\d{2}$/);
    assert.ok(target.date >= roadmap.as_of);
    assert.ok(target.date <= roadmap.defense_date);
  }
  const date = id => targets.find(t => t.task_id === id).date;
  assert.ok(date("JUP-035") < date("JUP-054"));
  assert.ok(date("JUP-036") < date("JUP-071"));
  assert.ok(date("JUP-071") < date("JUP-109"));
  assert.ok(date("JUP-110") < date("JUP-065"));
  assert.ok(date("JUP-065") < date("JUP-066"));
});

test("protects the official Jupiter deliverables and evaluation constraints", () => {
  for (const requirement of [
    /MVP funcional/i,
    /base vectorial/i,
    /API de modelo/i,
    /CI\/CD/i,
    /monitorizacion y logging/i,
    /maximo de 20 paginas/i,
    /10 a 20 minutos/i,
    /video demo de 5 a 10 minutos es\s+opcional/i,
    /entregables \(80 %\)/i,
    /presentacion \(20 %\)/i,
  ]) {
    assert.match(narrative, requirement);
  }
});

test("keeps scope and work in progress bounded", () => {
  assert.match(narrative, /Maximo: dos tarjetas de implementacion P0 y una/i);
  assert.match(narrative, /P1 solo entra si M4 termina en fecha/i);
  assert.match(narrative, /P2 permanece despues\s+del MVP/i);
  assert.match(narrative, /A partir del 09\/10 solo entran correcciones/i);
});

test("records approval and user confirmation before calendar activation", () => {
  assert.equal(
    roadmap.calendar_status,
    "confirmed-by-user",
  );
  assert.match(narrative, /no se aplican masivamente hasta que el\s+equipo apruebe/i);
  assert.equal(roadmap.roadmap_approval.status, "approved-by-authorized-subagents");
  assert.equal(roadmap.calendar_confirmation.delivery_date, roadmap.delivery_date);
  assert.equal(roadmap.calendar_confirmation.defense_date, roadmap.defense_date);
  assert.equal(roadmap.recovery_plan.status, "activated-and-verified");
  const receipt = JSON.parse(fs.readFileSync(path.join(root, roadmap.recovery_plan.activation_evidence), "utf8"));
  assert.deepEqual(receipt.results.map(r => r.task_id).sort(), roadmap.recovery_plan.targets.map(t => t.task_id).sort());
  for (const result of receipt.results) {
    const target = roadmap.recovery_plan.targets.find(t => t.task_id === result.task_id);
    const local = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(result.after_due));
    assert.equal(local, `${target.date} 18:00`);
    assert.equal(result.preserved_fields, true);
  }
});
