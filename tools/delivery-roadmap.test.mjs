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

const expectedP0 = [
  13, 14, 19, 20, 21, 22, 23, 24, 25, 26, 35, 36, 42, 43, 44, 47, 48, 49,
  50, 51, 52, 53, 54, 55, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
  72, 73, 74, 75, 76, 77, 78, 79, 80, 82, 83,
].map((value) => `JUP-${String(value).padStart(3, "0")}`);

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

test("assigns every current P0 task exactly once", () => {
  const assigned = roadmap.milestones.flatMap(({ task_ids }) => task_ids);
  assert.equal(new Set(assigned).size, assigned.length);
  assert.deepEqual([...assigned].sort(), [...expectedP0].sort());
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

test("does not authorize bulk Trello dates before team approval", () => {
  assert.equal(
    roadmap.calendar_status,
    "team-baseline-pending-institutional-confirmation",
  );
  assert.match(narrative, /no se aplican masivamente hasta que el\s+equipo apruebe/i);
});
