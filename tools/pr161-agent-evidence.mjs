// One-off human authorization, not a general alternative to GitHub reviews.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

export const PR161_AGENT_EXCEPTION = "- Excepcion puntual PR161: revision y validacion por agentes independientes, autorizada por el usuario el 2026-10-24";
const DIRECTORY = "docs/evidence/JUP-131-pr161-reconciliation";
const PUBLICATION_FILES = new Set([
  ...["manifest.json", "revision.json", "validacion.json", "revision.md", "validacion.md", "README.md"].map((name) => `${DIRECTORY}/${name}`),
  "docs/continuidad/README.md", "docs/continuidad/cloud-aws.md",
  "docs/evidence/JUP-131-pr161-agent-exception.md",
  "docs/planning/2026-10-25-jup131-reconcile-master.md",
]);
const ROLES = [
  "- Liderazgo: Alejandro Aguado",
  "- Pairing/coautoria: Victor Mendez",
  "- Revision de PR: Agente pr161_code_review (excepcion PR161)",
  "- Validacion, pruebas y documentacion: Agente pr161_validation (excepcion PR161)",
];
const REPORTS = [
  { kind: "revision", title: "Revision JUP-131", agent: "/root/pr161_code_review", verdict: "APPROVE" },
  { kind: "validacion", title: "Validacion JUP-131", agent: "/root/pr161_validation", verdict: "PASS" },
];
const digest = (value) => createHash("sha256").update(value.replaceAll("\r\n", "\n")).digest("hex");
const require = (condition, message) => { if (!condition) throw new Error(message); };

export function pr161AgentEvidence(input, visibleLines, root) {
  const lines = visibleLines.map((line) => line.trim());
  const declarations = lines.filter((line) => line === PR161_AGENT_EXCEPTION);
  if (!declarations.length) return { active: false, errors: [] };
  try {
    require(declarations.length === 1 && input.number === 161
      && input.repository?.toLowerCase() === "economiconfinops/tfm-economicon"
      && input.author?.toLowerCase() === "iber1to"
      && /(?:^|[^A-Za-z0-9])JUP-131\b/i.test(input.title)
      && lines.filter((line) => /^- ID: JUP-\d+$/i.test(line)).length === 1
      && lines.includes("- ID: JUP-131")
      && input.base === "develop" && input.head === "feat/JUP-131-atlas-ecs"
      && ROLES.every((role) => lines.filter((line) => line.startsWith(role.split(":")[0] + ":")).length === 1 && lines.includes(role)),
    "alcance o roles distintos de la autorizacion PR161");
    const git = (...args) => execFileSync("git", args, { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], maxBuffer: 4 * 1024 * 1024 });
    require(/^[a-f0-9]{40}$/.test(input.headSha ?? "") && git("rev-parse", "HEAD").trim() === input.headSha,
      "checkout distinto del head vigente; repetir el check actualizado");
    const read = (file) => git("show", `${input.headSha}:${file}`);
    const manifest = JSON.parse(read(`${DIRECTORY}/manifest.json`));
    const candidate = manifest.candidate_sha;
    require(/^[a-f0-9]{40}$/.test(candidate ?? ""), "candidato invalido");
    git("merge-base", "--is-ancestor", candidate, input.headSha);
    const delta = git("diff", "--name-only", "--no-renames", candidate, input.headSha, "--").trim().split("\n").filter(Boolean);
    require(delta.every((file) => PUBLICATION_FILES.has(file)), "delta de codigo posterior al candidato revisado; revalidar");
    require(Array.isArray(manifest.reports) && manifest.reports.length === 2, "faltan dos informes independientes");
    for (const expected of REPORTS) {
      const entries = manifest.reports.filter((entry) => entry.kind === expected.kind);
      require(entries.length === 1, "rol de informe duplicado o ausente");
      const entry = entries[0];
      require(entry.path === `${DIRECTORY}/${expected.kind}.json`, "ruta de informe inesperada");
      const raw = read(entry.path);
      require(digest(raw) === entry.sha256, "integridad del dictamen incorrecta");
      const record = JSON.parse(raw);
      require(record.candidate_sha === candidate && record.title === expected.title
        && record.agent === expected.agent && record.verdict === expected.verdict,
      "dictamen negativo, atribucion o candidato incorrectos");
      require(record.report === `${DIRECTORY}/${expected.kind}.md`, "ruta de evidencia inesperada");
      require(digest(read(record.report)) === record.report_sha256, "integridad de la evidencia incorrecta");
    }
    return { active: true, errors: [] };
  } catch (error) {
    // Do not expose subprocess output; it can contain arbitrary repository data.
    const detail = error.status !== undefined ? "evidencia/candidato Git inaccesible" : error.message;
    return { active: false, errors: [`Excepcion PR161 rechazada: ${detail}.`] };
  }
}
