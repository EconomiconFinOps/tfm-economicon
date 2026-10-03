import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { digest, root, suitePath } from "./validation-questions.mjs";

export { root };
export const labelsPath = "docs/validation/JUP-022-retrieval-labels.json";
const COVERAGE = ["direct", "partial", "none"];
const nonempty = (value) => typeof value === "string" && value.trim().length > 0;
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

// ATX headings outside fenced code, counted by their exact text; the same text twice is ambiguous.
export function headingsOf(text) {
  const counts = new Map();
  let fence = null;
  for (const line of text.replaceAll("\r\n", "\n").split("\n")) {
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (marker) {
      if (!fence) fence = marker[1][0];
      else if (marker[1][0] === fence) fence = null;
      continue;
    }
    if (fence) continue;
    const heading = /^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$/.exec(line);
    if (heading) counts.set(heading[1].trim(), (counts.get(heading[1].trim()) ?? 0) + 1);
  }
  return counts;
}

function readSources(sources, repoRoot, errors) {
  const headings = {};
  for (const [id, source] of Object.entries(sources)) {
    const relative = path.relative(repoRoot, path.resolve(repoRoot, source.path));
    if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
      errors.push(`fuente ${id}: ruta fuera del repositorio.`);
      continue;
    }
    let text;
    try {
      text = fs.readFileSync(path.join(repoRoot, relative), "utf8");
    } catch {
      errors.push(`fuente ${id}: fichero no disponible.`);
      continue;
    }
    if (digest(text) !== source.sha256) {
      errors.push(`fuente ${id}: contenido cambiado; revisar las etiquetas y el banco antes de actualizar el hash.`);
      continue;
    }
    headings[id] = headingsOf(text);
  }
  return headings;
}

export function validateLabels(labels, { repoRoot = root, suite } = {}) {
  const errors = [];
  const check = (condition, message) => { if (!condition) errors.push(message); };
  const bank = suite ?? JSON.parse(fs.readFileSync(path.join(repoRoot, suitePath), "utf8"));
  if (!object(labels)) return ["El fichero de etiquetas debe ser un objeto JSON."];
  check(labels.schema_version === 1, "schema_version debe ser 1.");
  check(labels.jup === "JUP-022" && labels.trello === "https://trello.com/c/DPZpQ09b", "Trazabilidad JUP/Trello invalida.");
  check(labels.bank?.path === suitePath && labels.bank?.suite_version === bank.suite_version,
    "banco cambiado: la version o la ruta del banco no coincide; revisar las etiquetas.");

  const sources = object(bank.sources) ? bank.sources : {};
  for (const [id, source] of Object.entries(sources)) {
    const declared = labels.sources?.[id];
    check(declared?.path === source.path && declared?.sha256 === source.sha256,
      `fuente ${id}: la ruta o el hash de las etiquetas no coincide con el banco.`);
  }
  const headings = readSources(sources, repoRoot, errors);

  const cases = new Map((Array.isArray(bank.cases) ? bank.cases : []).map((item) => [item.id, item]));
  if (!Array.isArray(labels.labels)) return [...errors, "labels debe ser una lista."];
  const seen = new Set();
  for (const entry of labels.labels) {
    const id = entry?.case;
    if (!object(entry) || !cases.has(id)) { errors.push(`${id ?? "etiqueta"}: caso inexistente en el banco.`); continue; }
    check(!seen.has(id), `${id}: etiqueta duplicada.`);
    seen.add(id);
    const coverage = entry.coverage;
    check(COVERAGE.includes(coverage), `${id}: cobertura invalida.`);
    if (entry.expect !== undefined && !Array.isArray(entry.expect)) errors.push(`${id}: expect debe ser una lista.`);
    const expect = Array.isArray(entry.expect) ? entry.expect : [];
    if (coverage === "none") {
      check(expect.length === 0, `${id}: cobertura none no admite secciones.`);
      check(nonempty(entry.note), `${id}: cobertura none exige una nota que explique el hueco.`);
    } else if (COVERAGE.includes(coverage)) {
      check(expect.length > 0, `${id}: cobertura direct o partial exige al menos una seccion.`);
    }
    const declared = new Set(cases.get(id).sources ?? []);
    const used = new Set();
    for (const item of expect) {
      const key = `${item?.source}\u0000${item?.heading}`;
      check(nonempty(item?.heading) && nonempty(item?.source), `${id}: seccion sin fuente o sin encabezado.`);
      check(!used.has(key), `${id}: seccion repetida (${item?.source}, ${item?.heading}).`);
      used.add(key);
      if (!declared.has(item?.source)) { errors.push(`${id}: fuente ${item?.source} no declarada por el caso.`); continue; }
      const known = headings[item.source];
      if (!known) continue;
      const count = known.get(item.heading) ?? 0;
      check(count > 0, `${id}: el encabezado "${item.heading}" no existe en la fuente ${item.source}.`);
      check(count < 2, `${id}: el encabezado "${item.heading}" es ambiguo en la fuente ${item.source}; usar uno que aparezca una sola vez.`);
    }
  }
  for (const id of cases.keys()) check(seen.has(id), `${id}: caso sin etiqueta.`);
  return errors;
}

function isMainModule() {
  if (!process.argv[1]) return false;
  try {
    return fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
}

function main() {
  const command = process.argv[2] ?? "validate";
  if (command !== "validate" || process.argv.length > 3) {
    console.error("Uso: node tools/retrieval-labels.mjs [validate]");
    process.exitCode = 2;
    return;
  }
  try {
    const labels = JSON.parse(fs.readFileSync(path.join(root, labelsPath), "utf8"));
    const errors = validateLabels(labels);
    if (errors.length) throw new Error(errors.join("\n"));
    const count = (value) => labels.labels.filter((entry) => entry.coverage === value).length;
    console.log(`[OK] ${labels.labels.length} etiquetas (${count("direct")} directas, ${count("partial")} parciales, ${count("none")} sin cobertura) coherentes con el banco y con la version de los documentos.`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

if (isMainModule()) main();
