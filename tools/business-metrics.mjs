import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const nonempty = (v) => typeof v === "string" && v.trim().length > 0;
const integer = (v) => Number.isSafeInteger(v) && v >= 0;
const evidence = (v) => Array.isArray(v) && v.length > 0 && v.every(nonempty);
const sum = (values) => {
  const value = values.reduce((a, b) => a + b, 0);
  if (!Number.isSafeInteger(value)) throw new Error("Total fuera del rango entero seguro.");
  return value;
};
const pct = (a, b) => b === 0 ? null : a / b * 100;
const date = (v) => nonempty(v) && /^\d{4}-\d{2}-\d{2}$/.test(v)
  && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;

export function validateRun(run) {
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  const keys = (obj, allowed, label) => {
    for (const key of Object.keys(obj)) check(allowed.includes(key), `${label}: campo desconocido ${key}.`);
  };
  if (!run || typeof run !== "object" || Array.isArray(run)) return ["Registro inválido."];
  keys(run, ["schema_version", "jup", "run_id", "scope", "dataset_version", "configuration", "reviewer",
    "commit", "provenance", "period", "currency", "cost_basis", "minor_unit_digits", "evidence",
    "trials", "costs", "opportunities"], "Registro");
  check(run.schema_version === 1, "schema_version debe ser 1.");
  check(run.jup === "JUP-068", "JUP inválido.");
  for (const key of ["run_id", "scope", "dataset_version", "configuration", "reviewer"]) {
    check(nonempty(run[key]), `Falta ${key}.`);
  }
  check(/^[a-f0-9]{40}$/.test(run.commit ?? ""), "commit debe identificar la revisión completa.");
  check(["synthetic", "measured"].includes(run.provenance), "Procedencia inválida.");
  check(date(run.period?.start) && date(run.period?.end)
    && run.period.start <= run.period.end, "Periodo inválido.");
  if (run.period && typeof run.period === "object") keys(run.period, ["start", "end"], "Periodo");
  check(/^[A-Z]{3}$/.test(run.currency ?? ""), "Moneda inválida.");
  check(["actual", "amortized"].includes(run.cost_basis), "Base de coste inválida.");
  check(integer(run.minor_unit_digits) && run.minor_unit_digits <= 3, "Escala monetaria inválida.");
  check(evidence(run.evidence), "Falta evidencia del registro.");
  for (const section of ["trials", "costs", "opportunities"]) {
    if (!Array.isArray(run[section])) { errors.push(`${section} debe ser una lista.`); continue; }
    const ids = new Set();
    for (const row of run[section]) {
      if (!row || typeof row !== "object" || Array.isArray(row)) { errors.push(`${section}: fila inválida.`); continue; }
      check(nonempty(row.id) && !ids.has(row.id), `${section}: ID vacío o duplicado.`);
      ids.add(row.id);
      check(evidence(row.evidence), `${section}/${row.id}: falta evidencia.`);
    }
  }
  // Stop before interpreting malformed rows.
  if (errors.length) return errors;
  const trialKeys = new Set();
  for (const t of run.trials) {
    keys(t, ["id", "case_id", "participant", "repetition", "context_sha256", "result", "manual_ms", "assisted_ms", "evidence"], t.id);
    check(nonempty(t.case_id) && nonempty(t.participant) && nonempty(t.context_sha256)
      && /^[a-f0-9]{64}$/.test(t.context_sha256), `${t.id}: identidad/contexto inválido.`);
    check(Number.isSafeInteger(t.repetition) && t.repetition > 0, `${t.id}: repetición inválida.`);
    const key = JSON.stringify([t.case_id, t.participant, t.repetition]);
    check(!trialKeys.has(key), `${t.id}: pareja repetida.`); trialKeys.add(key);
    check(["pass", "fail", "blocked", "not_run"].includes(t.result), `${t.id}: resultado inválido.`);
    check(integer(t.manual_ms) && t.manual_ms > 0, `${t.id}: tiempo manual inválido.`);
    check(t.result === "pass" ? integer(t.assisted_ms) && t.assisted_ms > 0
      : t.assisted_ms === null || (integer(t.assisted_ms) && t.assisted_ms > 0), `${t.id}: tiempo asistido inválido.`);
  }
  for (const c of run.costs) {
    keys(c, ["id", "resource_id", "amount_minor", "allocation", "owner", "rule", "evidence"], c.id);
    check(nonempty(c.resource_id) && integer(c.amount_minor), `${c.id}: recurso/importe inválido.`);
    check(["allocated", "shared", "unallocated", "excluded"].includes(c.allocation), `${c.id}: allocation inválido.`);
    if (["allocated", "shared"].includes(c.allocation)) check(nonempty(c.owner), `${c.id}: falta owner.`);
    if (["shared", "excluded"].includes(c.allocation)) check(nonempty(c.rule), `${c.id}: falta regla documentada.`);
  }
  const eligibleByResource = new Map();
  for (const c of run.costs.filter((c) => c.allocation !== "excluded" && integer(c.amount_minor))) {
    eligibleByResource.set(c.resource_id, sum([eligibleByResource.get(c.resource_id) ?? 0, c.amount_minor]));
  }
  const estimatedResources = new Set();
  for (const o of run.opportunities) {
    keys(o, ["id", "resource_id", "status", "savings_minor", "reason", "owner", "risk", "method", "evidence"], o.id);
    check(["estimated", "candidate", "not_evaluable"].includes(o.status), `${o.id}: estado inválido.`);
    check(nonempty(o.resource_id) && nonempty(o.reason), `${o.id}: falta recurso/razón.`);
    if (o.status !== "estimated") {
      check(o.savings_minor === null, `${o.id}: candidato no puede cuantificar ahorro.`); continue;
    }
    check(nonempty(o.owner) && nonempty(o.risk) && nonempty(o.method), `${o.id}: falta owner/riesgo/método.`);
    check(integer(o.savings_minor) && o.savings_minor <= (eligibleByResource.get(o.resource_id) ?? -1),
      `${o.id}: ahorro inválido o superior al coste elegible del recurso.`);
    check(!estimatedResources.has(o.resource_id), `${o.id}: ahorro solapado; consolidar por recurso.`);
    estimatedResources.add(o.resource_id);
  }
  return errors;
}

export function calculateMetrics(run) {
  const errors = validateRun(run);
  if (errors.length) throw new Error(errors.join("\n"));
  const successful = run.trials.filter((t) => t.result === "pass");
  const manual = sum(successful.map((t) => t.manual_ms));
  const assisted = sum(successful.map((t) => t.assisted_ms));
  const buckets = Object.fromEntries(["allocated", "shared", "unallocated", "excluded"].map((bucket) =>
    [bucket, sum(run.costs.filter((c) => c.allocation === bucket).map((c) => c.amount_minor))]));
  const eligible = sum([buckets.allocated, buckets.shared, buckets.unallocated]);
  const estimates = run.opportunities.filter((o) => o.status === "estimated");
  const potential = sum(estimates.map((o) => o.savings_minor));
  return {
    schema_version: 1, jup: run.jup, run_id: run.run_id, provenance: run.provenance,
    input_sha256: createHash("sha256").update(JSON.stringify(run)).digest("hex"),
    scope: run.scope, period: run.period, currency: run.currency,
    cost_basis: run.cost_basis, minor_unit_digits: run.minor_unit_digits,
    commit: run.commit, dataset_version: run.dataset_version, configuration: run.configuration,
    reviewer: run.reviewer, evidence: run.evidence,
    time: {
      results: Object.fromEntries(["pass", "fail", "blocked", "not_run"].map((status) =>
        [status, run.trials.filter((t) => t.result === status).length])),
      eligible_pairs: successful.length, manual_ms: manual, assisted_ms: assisted,
      saved_ms: successful.length ? manual - assisted : null,
      saved_percent: pct(manual - assisted, manual),
      pairs: successful.map((t) => ({ id: t.id, saved_ms: t.manual_ms - t.assisted_ms,
        saved_percent: pct(t.manual_ms - t.assisted_ms, t.manual_ms), evidence: t.evidence })),
    },
    allocation: { ...buckets, total_minor: sum(Object.values(buckets)), eligible_minor: eligible,
      assigned_percent: pct(buckets.allocated, eligible),
      governed_percent: pct(sum([buckets.allocated, buckets.shared]), eligible),
      unallocated_percent: pct(buckets.unallocated, eligible) },
    savings: {
      estimated_count: estimates.length,
      candidate_count: run.opportunities.filter((o) => o.status === "candidate").length,
      not_evaluable_count: run.opportunities.filter((o) => o.status === "not_evaluable").length,
      potential_minor: estimates.length ? potential : null,
      potential_percent: estimates.length ? pct(potential, eligible) : null,
      realized_minor: null,
      estimates: estimates.map(({ id, resource_id, savings_minor, evidence }) => ({ id, resource_id, savings_minor, evidence })),
    },
  };
}

function main() {
  const [command, filename, ...rest] = process.argv.slice(2);
  if (!["validate", "report"].includes(command) || !filename || rest.length) {
    console.error("Uso: node tools/business-metrics.mjs [validate|report] registro.json");
    process.exitCode = 2; return;
  }
  try {
    const run = JSON.parse(fs.readFileSync(filename, "utf8"));
    // Calculate even for validation, to detect overflow in totals.
    const report = calculateMetrics(run);
    console.log(command === "report" ? JSON.stringify(report, null, 2) : `[OK] ${run.run_id} (${run.provenance})`);
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
