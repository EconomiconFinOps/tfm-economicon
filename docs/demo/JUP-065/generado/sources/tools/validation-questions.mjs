import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const suitePath = "docs/validation/JUP-069-questions.json";
export const categories = ["costs", "allocation", "tagging", "budgets", "anomalies", "recommendations", "scope"];
const behaviors = ["answer", "clarify", "abstain"];
const nonempty = (value) => typeof value === "string" && value.trim().length > 0;
const strings = (value) => Array.isArray(value) && value.length > 0 && value.every(nonempty);
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
export const digest = (text) => createHash("sha256").update(text.replaceAll("\r\n", "\n")).digest("hex");

export function validateSuite(suite, repoRoot = root) {
  const errors = [];
  const check = (condition, message) => { if (!condition) errors.push(message); };
  if (!object(suite)) return ["La batería debe ser un objeto JSON."];
  check(suite.schema_version === 1, "schema_version debe ser 1.");
  check(/^\d+\.\d+\.\d+$/.test(suite.suite_version ?? ""), "Falta suite_version semántica.");
  check(suite.jup === "JUP-069" && suite.trello === "https://trello.com/c/Qi5uwxgW", "Trazabilidad JUP/Trello inválida.");
  check(suite.language === "es" && nonempty(suite.provenance), "Falta idioma o procedencia.");
  const sources = object(suite.sources) ? suite.sources : {};
  check(Object.keys(sources).length > 0, "Faltan fuentes.");
  for (const [id, source] of Object.entries(sources)) {
    if (!object(source) || !nonempty(source.path) || !/^[a-f0-9]{64}$/.test(source.sha256 ?? "")) {
      errors.push(`Fuente ${id}: ruta o SHA-256 inválido.`);
      continue;
    }
    const relative = path.relative(repoRoot, path.resolve(repoRoot, source.path));
    if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
      errors.push(`Fuente ${id}: ruta fuera del repositorio.`);
      continue;
    }
    try {
      check(digest(fs.readFileSync(path.join(repoRoot, relative), "utf8")) === source.sha256,
        `Fuente ${id}: contenido cambiado; revisar expectativas y versión antes de actualizar el hash.`);
    } catch {
      errors.push(`Fuente ${id}: fichero no disponible.`);
    }
  }
  if (!Array.isArray(suite.cases)) return [...errors, "cases debe ser una lista."];
  check(suite.cases.length >= 21, "Se requieren al menos 21 consultas.");
  const ids = new Set();
  const questions = new Set();
  const coverage = new Set();
  const behaviorCoverage = new Set();
  for (const [index, item] of suite.cases.entries()) {
    const label = item?.id ?? `caso ${index}`;
    if (!object(item)) { errors.push(`${label}: caso inválido.`); continue; }
    check(/^JUP-069-\d{3}$/.test(item.id ?? "") && !ids.has(item.id), `${label}: ID inválido o duplicado.`);
    ids.add(item.id);
    check(categories.includes(item.category), `${label}: categoría inválida.`);
    check(behaviors.includes(item.behavior), `${label}: comportamiento inválido.`);
    coverage.add(item.category);
    behaviorCoverage.add(item.behavior);
    check(nonempty(item.question) && nonempty(item.context), `${label}: falta pregunta o contexto.`);
    const normalized = typeof item.question === "string" ? item.question.trim().toLocaleLowerCase("es") : "";
    check(!questions.has(normalized), `${label}: pregunta duplicada.`);
    questions.add(normalized);
    check(strings(item.sources) && item.sources.every((id) => Object.hasOwn(sources, id)), `${label}: referencias desconocidas o vacías.`);
    const expected = object(item.expected) ? item.expected : {};
    check(strings(expected.required) && strings(expected.forbidden), `${label}: faltan criterios positivos o negativos.`);
    check(Array.isArray(expected.numbers), `${label}: numbers debe ser una lista.`);
    for (const number of Array.isArray(expected.numbers) ? expected.numbers : []) {
      check(object(number) && nonempty(number.label) && nonempty(number.unit)
        && Number.isFinite(number.value) && Number.isFinite(number.tolerance) && number.tolerance >= 0,
      `${label}: expectativa numérica inválida.`);
    }
  }
  for (const category of categories) check(coverage.has(category), `Sin cobertura: ${category}.`);
  for (const behavior of behaviors) check(behaviorCoverage.has(behavior), `Sin comportamiento: ${behavior}.`);
  return errors;
}

// Deliberately whitelist fields: answer keys and evaluation rubrics never enter prompts.
export function prepareInputs(suite) {
  return {
    jup: suite.jup,
    suite_version: suite.suite_version,
    suite_sha256: digest(JSON.stringify(suite)),
    cases: suite.cases.map(({ id, question, context }) => ({
      id,
      prompt: `Contexto de prueba (datos sintéticos):\n${context}\n\nPregunta:\n${question}`,
    })),
  };
}

function main() {
  const command = process.argv[2] ?? "validate";
  if (!["validate", "prepare"].includes(command) || process.argv.length > 3) {
    console.error("Uso: node tools/validation-questions.mjs [validate|prepare]");
    process.exitCode = 2;
    return;
  }
  try {
    const suite = JSON.parse(fs.readFileSync(path.join(root, suitePath), "utf8"));
    const errors = validateSuite(suite);
    if (errors.length) throw new Error(errors.join("\n"));
    if (command === "prepare") console.log(JSON.stringify(prepareInputs(suite), null, 2));
    else console.log(`[OK] ${suite.cases.length} consultas, ${categories.length} categorías, fuentes y rúbricas verificadas (sin evaluar respuestas del asistente).`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
