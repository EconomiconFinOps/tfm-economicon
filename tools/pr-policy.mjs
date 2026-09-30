import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

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

export function checkPullRequest({ title = "", body = "", head = "", base = "" }) {
  const errors = [];
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
      participants.set(label, value.toLocaleLowerCase("es").normalize("NFKC"));
    }
  }
  if (participants.size === ROLE_LABELS.length) {
    const reviewer = participants.get("Revision de PR");
    const validator = participants.get("Validacion, pruebas y documentacion");
    // Declared exception: one person may review and validate; leadership and pairing stay separate.
    const sameReviewer = reviewer === validator && declaresSamePersonException(body);
    const expected = sameReviewer ? ROLE_LABELS.length - 1 : ROLE_LABELS.length;
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
const REVIEW_KINDS = [
  { key: "revision", label: "Revision", pattern: /^revisi[oó]n\s+jup-(\d{3})\b/iu },
  { key: "validacion", label: "Validacion", pattern: /^validaci[oó]n\s+jup-(\d{3})\b/iu },
];
// A dismissed review leaves the reviewer without a current decision, so an older request must not come back.
const DECISIVE_STATES = new Set(["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]);

// Accents and case are ignored so that "Validación" and "validacion" match the same title.
const plain = (text) => text.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("es");

function declaresSamePersonException(body) {
  const expected = plain(SAME_PERSON_EXCEPTION);
  // Hidden or quoted text is not a declaration: drop HTML comments and fenced code blocks.
  const visible = body.replace(/<!--[\s\S]*?-->/g, "").replace(/^```[\s\S]*?^```/gm, "");
  return visible.split(/\r?\n/).some((line) => plain(line.trim()).replace(/\.$/, "") === expected);
}

export function checkReviews({ title = "", body = "", author = "", reviews = [] }) {
  const titleMatch = TITLE_PATTERN.exec(title);
  if (!titleMatch) return [`El titulo debe contener un identificador JUP-XXX. Ver ${REVIEW_FLOW_LINK}`];
  const id = titleMatch[1];
  const authorLogin = author.toLocaleLowerCase("en");
  const published = reviews
    .filter(({ state, user }) => state !== "PENDING" && user.toLocaleLowerCase("en") !== authorLogin)
    .sort((a, b) => Date.parse(a.submitted_at) - Date.parse(b.submitted_at));

  const errors = [];
  const authors = {};
  for (const kind of REVIEW_KINDS) {
    authors[kind.key] = new Set(
      published
        .filter(({ body: text = "" }) => kind.pattern.exec(text.normalize("NFC").trimStart())?.[1] === id)
        .map(({ user }) => user.toLocaleLowerCase("en")),
    );
    if (authors[kind.key].size === 0) {
      errors.push(
        `Falta la review "${kind.label} JUP-${id}" de alguien distinto del autor; la primera linea de la review debe ser ese titulo en texto plano. Ver ${REVIEW_FLOW_LINK}`,
      );
    }
  }

  const { revision, validacion } = authors;
  const onlySamePerson =
    revision.size > 0 &&
    validacion.size > 0 &&
    [...revision].every((user) => validacion.size === 1 && validacion.has(user));
  if (onlySamePerson && !declaresSamePersonException(body)) {
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
    title: pull.title ?? "",
    body: pull.body ?? "",
    author: pull.user?.login ?? "",
    base: pull.base?.ref ?? "",
    reviews,
  };
}

export function parseEvent(event) {
  const pullRequest = event.pull_request;
  if (!pullRequest) throw new Error("El evento no contiene pull_request.");
  return {
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

async function mainReviews(eventPath) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error(`[ERROR] Falta GITHUB_TOKEN para leer las reviews del pull request. Ver ${REVIEW_FLOW_LINK}`);
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
    console.error(`[ERROR] No se pudieron leer las reviews del pull request #${number}: ${error.message}. Ver ${REVIEW_FLOW_LINK}`);
    process.exitCode = 1;
    return;
  }
  const errors = checkReviews(input);
  if (errors.length) {
    for (const error of errors) console.error(`[ERROR] ${error}`);
    process.exitCode = 1;
    return;
  }
  console.log("[OK] Revision y validacion publicadas, sin cambios pendientes.");
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
