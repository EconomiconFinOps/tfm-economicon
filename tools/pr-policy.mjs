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

  const participants = [];
  for (const label of ROLE_LABELS) {
    const value = readRole(body, label);
    if (!value || PLACEHOLDER_PATTERN.test(value)) {
      errors.push(`Falta una persona concreta para el rol ${label}.`);
    } else {
      participants.push(value.toLocaleLowerCase("es").normalize("NFKC"));
    }
  }
  if (
    participants.length === ROLE_LABELS.length &&
    new Set(participants).size !== ROLE_LABELS.length
  ) {
    errors.push("Los cuatro roles deben asignarse a cuatro personas distintas.");
  }
  return errors;
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

function main() {
  const eventPath = parseArgs(process.argv.slice(2)) ?? process.env.GITHUB_EVENT_PATH;
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
