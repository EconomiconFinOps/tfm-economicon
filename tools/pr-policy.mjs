import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pr161AgentEvidence } from "./pr161-agent-evidence.mjs";

const BRANCH_PATTERN = /^(feat|fix|docs|test|chore|refactor|ci|build)\/JUP-(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const TITLE_PATTERN = /\bJUP-(\d{3})\b/i;
const BODY_ID_PATTERN = /^-\s*ID:\s*JUP-(\d{3})\s*$/im;
const TRELLO_PATTERN = /https:\/\/trello\.com\/c\/[A-Za-z0-9]+/;
const ALLOWED_BASES = new Set(["main", "develop"]);
const ROLE_LABELS = [
  "Liderazgo",
  "Pairing/coautoria",
  "Revision de PR",
  "Validacion, pruebas y documentacion",
];
const PLACEHOLDER_PATTERN = /^(?:@?usuario|@?pendiente|por asignar|n\/a|-)$/i;

function readRole(body, label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = new RegExp(`^- ${escaped}:\\s*([^\\r\\n]+)$`, "im").exec(body);
  return match?.[1]?.trim();
}

export function checkPullRequest(input) {
  const { title = "", body = "", head = "", base = "" } = input;
  const errors = [];
  const specific = pr135Exception(input);
  if (specific.declared && !specific.active) errors.push(PR135_SCOPE_ERROR);
  const titleMatch = TITLE_PATTERN.exec(title);
  const bodyIdMatch = BODY_ID_PATTERN.exec(body);

  if (!ALLOWED_BASES.has(base)) {
    errors.push("La rama base debe ser main o develop.");
  }
  if (!titleMatch) {
    errors.push("El titulo debe contener un identificador JUP-XXX.");
  }
  if (!bodyIdMatch) {
    errors.push("El cuerpo debe identificar exactamente la tarjeta JUP-XXX.");
  } else if (titleMatch && bodyIdMatch[1] !== titleMatch[1]) {
    errors.push("El identificador JUP del cuerpo y el titulo debe coincidir.");
  }
  if (!TRELLO_PATTERN.test(body)) {
    errors.push("El cuerpo debe enlazar directamente la tarjeta de Trello.");
  }

  if (base === "main") {
    if (head !== "develop") {
      errors.push("Solo develop puede abrir un pull request hacia main.");
    }
  } else if (base === "develop") {
    const branchMatch = BRANCH_PATTERN.exec(head);
    if (!branchMatch) {
      errors.push("La rama debe seguir tipo/JUP-XXX-descripcion.");
    } else if (titleMatch && branchMatch[2] !== titleMatch[1]) {
      errors.push("El identificador JUP de la rama y el titulo debe coincidir.");
    }
  }

  const participants = new Map();
  for (const label of ROLE_LABELS) {
    const value = readRole(body, label);
    if (!value || PLACEHOLDER_PATTERN.test(value)) {
      errors.push(`Falta una persona concreta para el rol ${label}.`);
    } else {
      participants.set(label, plain(value.normalize("NFKC")).replace(/^@/, ""));
    }
  }
  if (participants.size === ROLE_LABELS.length) {
    const reviewer = participants.get("Revision de PR");
    const validator = participants.get("Validacion, pruebas y documentacion");
    // Declared exception: one person may review and validate; leadership and pairing stay separate.
    const declared = declaresSamePersonException(body);
    if (declared && reviewer !== validator) {
      errors.push(
        "La excepcion de misma persona esta declarada, pero Revision de PR y Validacion nombran a personas distintas.",
      );
    }
    const sameReviewer = reviewer === validator && declared;
    const expected = sameReviewer || specific.active ? ROLE_LABELS.length - 1 : ROLE_LABELS.length;
    if (new Set(participants.values()).size !== expected) {
      errors.push(
        sameReviewer
          ? "Con la excepcion declarada, liderazgo, pairing y la persona que revisa y valida deben ser tres personas distintas."
          : "Los cuatro roles deben asignarse a cuatro personas distintas.",
      );
    }
  }
  return errors;
}

export const REVIEW_FLOW_LINK =
  "https://github.com/EconomiconFinOps/tfm-economicon/blob/develop/CONTRIBUTING.md#review-and-validation-flow";
export const SAME_PERSON_EXCEPTION = "- Excepcion: revision y validacion por la misma persona, acordado en Trello";
export const PR135_PAIRING_REVIEW_EXCEPTION = "- Excepcion puntual PR135: pairing y revision por Lucia Mateo; validacion por Paris Arcos Martin; autorizada por Alejandro Aguado el 2026-10-18";
const PR135_SCOPE_ERROR = "La excepcion puntual PR135 solo es valida para PR135/JUP-126 en EconomiconFinOps/tfm-economicon, hacia develop, con autor, rama y roles autorizados. Ver " + REVIEW_FLOW_LINK;
const PR135_ROLE_LOGINS = { revision: "lmatsan", validacion: "parisarcos" };
const REVIEW_KINDS = [
  { key: "revision", label: "Revision", pattern: /^revisi[oó]n\s+jup-(\d{3})\b/iu },
  { key: "validacion", label: "Validacion", pattern: /^validaci[oó]n\s+jup-(\d{3})\b/iu },
];
// A dismissed review leaves the reviewer without a current decision, so an older request must not come back.
const DECISIVE_STATES = new Set(["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]);

// Accents and case are ignored so that "Validación" and "validacion" match the same title.
const plain = (text) => text.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("es");

// The one-off authorization must be plain visible Markdown, not an example or
// hidden declaration. Keep this stricter reader separate from the general rule.
function pr135VisibleLines(body) {
  const lines = body.replace(/\r\n?/g, "\n")
    .replace(/<!--[\s\S]*?(?:-->|$)/g, "")
    .replace(/<([a-z][a-z0-9-]*)(?:\s[^>]*)?>[\s\S]*?(?:<\/\1\s*>|$)/gi, "")
    .split("\n");
  const visible = [];
  let fence;
  for (const line of lines) {
    const match = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
    if (fence) {
      if (match && match[1][0] === fence[0] && match[1].length >= fence.length && !match[2].trim()) fence = undefined;
      continue;
    }
    if (match && !(match[1][0] === "`" && match[2].includes("`"))) {
      fence = match[1];
      continue;
    }
    if (!/^( {4,}|\t)/.test(line)) visible.push(line);
  }
  // CommonMark code spans may cross line breaks, so remove them before
  // considering a standalone-looking marker or role line within that span.
  return visible.join("\n").replace(/(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)/g, "").split("\n");
}

function pr135Exception({ number, repository = "", author = "", title = "", body = "", base = "", head = "" }) {
  const lines = pr135VisibleLines(body);
  const declarations = lines.filter((line) => line.trim() === PR135_PAIRING_REVIEW_EXCEPTION);
  const declared = declarations.length > 0;
  const roles = ["Alejandro Aguado", "Lucia Mateo", "Lucia Mateo", "Paris Arcos Martin"];
  const rolesMatch = ROLE_LABELS.every((label, index) => {
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(`^- ${escaped}:\\s*([^\\r\\n]+)$`, "i");
    const values = lines.map((line) => pattern.exec(line)?.[1]?.trim()).filter((value) => value !== undefined);
    return values.length === 1 && plain(values[0].normalize("NFKC")) === plain(roles[index]);
  });
  return {
    declared,
    active: declarations.length === 1 && number === 135
      && repository.toLowerCase() === "economiconfinops/tfm-economicon"
      && author.toLowerCase() === "iber1to"
      && TITLE_PATTERN.exec(title)?.[1] === "126"
      && lines.filter((line) => /^-\s*ID:\s*JUP-126\s*$/i.test(line)).length === 1
      && base === "develop" && head === "fix/JUP-126-dismissed-review-titles"
      && rolesMatch,
  };
}

function declaresSamePersonException(body) {
  const expected = plain(SAME_PERSON_EXCEPTION);
  // Only text GitHub renders as plain Markdown counts: no comments, code blocks or indented code, closed or not.
  const visible = body
    .replace(/<!--[\s\S]*?(?:-->|$)/g, "")
    .replace(/^ {0,3}(```|~~~)[\s\S]*?(?:^ {0,3}\1|$(?![\s\S]))/gm, "");
  return visible
    .split(/\r?\n/)
    .some((line) => !/^( {4,}|\t)/.test(line) && plain(line.trim()).replace(/\.$/, "") === expected);
}

export function checkReviews(input, { evidenceRoot = process.cwd() } = {}) {
  const { title = "", body = "", author = "", reviews = [] } = input;
  const titleMatch = TITLE_PATTERN.exec(title);
  if (!titleMatch) return [`El titulo debe contener un identificador JUP-XXX. Ver ${REVIEW_FLOW_LINK}`];
  const id = titleMatch[1];
  const authorLogin = author.toLocaleLowerCase("en");
  const published = reviews
    .filter(({ state, user }) => state !== "PENDING" && user.toLocaleLowerCase("en") !== authorLogin)
    .sort((a, b) => Date.parse(a.submitted_at) - Date.parse(b.submitted_at));

  const errors = [];
  const agents = pr161AgentEvidence(input, pr135VisibleLines(body), evidenceRoot);
  errors.push(...agents.errors);
  const specific = pr135Exception(input);
  if (specific.declared && !specific.active) errors.push(PR135_SCOPE_ERROR);
  const authors = {};
  for (const kind of REVIEW_KINDS) {
    // Preserve history for change-request resolution below; a dismissed title
    // cannot supply a role or revive an older title from the same person.
    const latestTitled = new Map();
    for (const item of published) {
      if (kind.pattern.exec((item.body ?? "").normalize("NFC").trimStart())?.[1] === id) {
        latestTitled.set(item.user.toLocaleLowerCase("en"), item);
      }
    }
    authors[kind.key] = new Set(
      [...latestTitled]
        .filter(([, item]) => item.state !== "DISMISSED")
        // Only for the explicitly authorized PR135 allocation: the assigned
        // review/validation supply titles. Other reviews remain in published
        // and still resolve/block change requests, without dismissing history.
        .filter(([user]) => !specific.active || user === PR135_ROLE_LOGINS[kind.key])
        .map(([user]) => user),
    );
    if (authors[kind.key].size === 0 && !agents.active) {
      errors.push(
        `Falta la review "${kind.label} JUP-${id}" de alguien distinto del autor; la primera linea de la review debe ser ese titulo en texto plano. Ver ${REVIEW_FLOW_LINK}`,
      );
    }
  }

  const { revision, validacion } = authors;
  const samePerson = [...revision].some((user) => validacion.has(user));
  if (samePerson && !declaresSamePersonException(body)) {
    errors.push(
      `Revision y validacion las ha publicado la misma persona sin declarar la excepcion en la descripcion del PR ("${SAME_PERSON_EXCEPTION}"). Ver ${REVIEW_FLOW_LINK}`,
    );
  }

  const latestDecision = new Map();
  for (const { user, state } of published) {
    if (DECISIVE_STATES.has(state)) latestDecision.set(user.toLocaleLowerCase("en"), { user, state });
  }
  for (const { user, state } of latestDecision.values()) {
    if (state === "CHANGES_REQUESTED") {
      errors.push(`Hay cambios pedidos pendientes de ${user}. Ver ${REVIEW_FLOW_LINK}`);
    }
  }
  return errors;
}

async function getJson(fetchImpl, url, token) {
  const response = await fetchImpl(url, {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (!response.ok) throw new Error(`GitHub API ${response.status} en ${url}`);
  return response.json();
}

export async function fetchReviewInput({
  repository,
  number,
  token,
  apiUrl = "https://api.github.com",
  fetchImpl = fetch,
}) {
  const base = `${apiUrl}/repos/${repository}/pulls/${number}`;
  const pull = await getJson(fetchImpl, base, token);
  const reviews = [];
  for (let page = 1; ; page += 1) {
    const batch = await getJson(fetchImpl, `${base}/reviews?per_page=100&page=${page}`, token);
    reviews.push(
      ...batch.map(({ user, state, body, submitted_at }) => ({ user: user?.login ?? "", state, body: body ?? "", submitted_at })),
    );
    if (batch.length < 100) break;
  }
  return {
    number: pull.number,
    repository,
    title: pull.title ?? "",
    body: pull.body ?? "",
    author: pull.user?.login ?? "",
    base: pull.base?.ref ?? "",
    head: pull.head?.ref ?? "",
    headSha: pull.head?.sha ?? "",
    reviews,
  };
}

export function parseEvent(event) {
  const pullRequest = event.pull_request;
  if (!pullRequest) throw new Error("El evento no contiene pull_request.");
  return {
    number: pullRequest.number,
    repository: event.repository?.full_name ?? "",
    author: pullRequest.user?.login ?? "",
    title: pullRequest.title ?? "",
    body: pullRequest.body ?? "",
    head: pullRequest.head?.ref ?? "",
    base: pullRequest.base?.ref ?? "",
  };
}

function parseArgs(argv) {
  const index = argv.indexOf("--event");
  return index >= 0 ? argv[index + 1] : undefined;
}

function reportReviewError(message) {
  console.error(`[ERROR] ${message}`);
  // Annotations show the reason in the checks panel without opening the job log.
  if (process.env.GITHUB_ACTIONS === "true") {
    const data = message.replaceAll("%", "%25").replaceAll("\r", "%0D").replaceAll("\n", "%0A");
    console.log(`::error title=JUP reviews::${data}`);
  }
}

async function mainReviews(eventPath) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    reportReviewError(`Falta GITHUB_TOKEN para leer las reviews del pull request. Ver ${REVIEW_FLOW_LINK}`);
    process.exitCode = 1;
    return;
  }
  const event = JSON.parse(fs.readFileSync(path.resolve(eventPath), "utf8"));
  const number = event.pull_request?.number;
  let input;
  try {
    // Reviews are read live: rerunning a job replays the original event payload.
    input = await fetchReviewInput({
      repository: process.env.GITHUB_REPOSITORY,
      number,
      token,
      apiUrl: process.env.GITHUB_API_URL ?? "https://api.github.com",
    });
  } catch (error) {
    reportReviewError(`No se pudieron leer las reviews del pull request #${number}: ${error.message}. Ver ${REVIEW_FLOW_LINK}`);
    process.exitCode = 1;
    return;
  }
  const errors = checkReviews(input);
  if (errors.length) {
    for (const error of errors) reportReviewError(error);
    process.exitCode = 1;
    return;
  }
  console.log("[OK] Revision y validacion verificadas conforme a la politica aplicable, sin cambios pendientes.");
}

function main() {
  const argv = process.argv.slice(2);
  const eventPath = parseArgs(argv) ?? process.env.GITHUB_EVENT_PATH;
  if (argv.includes("--reviews")) {
    if (!eventPath) {
      console.error("Uso: node tools/pr-policy.mjs --reviews --event <github-event.json>");
      process.exitCode = 2;
      return;
    }
    return mainReviews(eventPath);
  }
  if (!eventPath) {
    console.error("Uso: pnpm pr:check --event <github-event.json>");
    process.exitCode = 2;
    return;
  }
  const event = JSON.parse(fs.readFileSync(path.resolve(eventPath), "utf8"));
  const errors = checkPullRequest(parseEvent(event));
  if (errors.length) {
    for (const error of errors) console.error(`[ERROR] ${error}`);
    process.exitCode = 1;
    return;
  }
  console.log("[OK] Pull request enlazado a JUP y preparado para revision.");
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
