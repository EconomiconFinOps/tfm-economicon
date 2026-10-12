import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

// Frases en inglés ya traducidas. Se amplía con cada hallazgo; los términos que
// se conservan en inglés están en GLOSARIO.md y no deben aparecer aquí.
const ENGLISH_UI_TEXT = [
  "Operator login", "Access the tenant control tower", "This demo build", "Your session has expired",
  "Signing in", "Sign in", "Password", "Email",
  "Tenant bootstrap", "Reset session", "Select a tenant",
  "Choose a tenant", "No active tenant", "No tenant is active", "Visible Tenants", "Tenants",
  "Conversations", "Assistant chat", "New conversation title", "Loading conversation", "Create a conversation",
  "Ask the assistant", "Sending...", "Each conversation",
  "Source", "Artifact URI", "Text content", "Queueing job", "Queue ingestion", "Job accepted", "Job ID",
  "Create ingestion job", "Ingestions", "Assistant", "Overview",
  "Bootstrapping", "Connecting to", "Backend unavailable", "Possible overlapping", "Monthly Spend",
  "Savings Identified", "Service Health", "Active operator", "Billing period", "Unavailable", "No cost data"
];

const SEGMENTS = /"((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\]|\\.)*)`|>([^<>{}\n]+)</g;

function stripComments(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, (block) => block.replace(/[^\n]/g, " "))
    .replace(/(^|[^:"'`\\])\/\/[^\n]*/g, "$1");
}

export function findEnglishUiText(source: string): string[] {
  const code = stripComments(source).replace(/^\s*(import|export)\b[^\n]*\bfrom\s+["'][^"']*["'];?/gm, "");
  const found: string[] = [];
  for (const match of code.matchAll(SEGMENTS)) {
    const text = match[1] ?? match[2] ?? match[3] ?? match[4] ?? "";
    for (const phrase of ENGLISH_UI_TEXT) {
      if (new RegExp(`(^|[^\\p{L}\\p{N}_])${phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}($|[^\\p{L}\\p{N}_])`, "u").test(text)) {
        found.push(phrase);
      }
    }
  }
  return found;
}

function interfaceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === "test" ? [] : interfaceFiles(path);
    return /\.(ts|tsx)$/.test(name) && !/\.(test|d)\.(ts|tsx)$/.test(name) ? [path] : [];
  });
}

describe("interfaz en español", () => {
  it("no muestra textos en inglés ya traducidos", () => {
    const root = join(process.cwd(), "src");
    const offenders = interfaceFiles(root).flatMap((file) => {
      const found = findEnglishUiText(readFileSync(file, "utf8"));
      return found.map((phrase) => `${relative(process.cwd(), file)}: ${phrase}`);
    });
    expect(offenders).toEqual([]);
  });

  it("detecta un botón con texto en inglés", () => {
    expect(findEnglishUiText('<button type="submit">Sign in</button>')).toEqual(["Sign in"]);
    expect(findEnglishUiText('const label = "Sign in";')).toEqual(["Sign in"]);
    expect(findEnglishUiText('<input placeholder="Ask the assistant about it" />')).toEqual(["Ask the assistant"]);
  });

  it("ignora comentarios, identificadores, rutas y claves", () => {
    const source = [
      "// Sign in the operator and reset session",
      "/* Tenants and Assistant notes */",
      'import { Assistant } from "../Assistant";',
      "const Tenants = fetchTenants(assistantPath);",
      'const route = { path: "/assistant", key: "tenants" };'
    ].join("\n");
    expect(findEnglishUiText(source)).toEqual([]);
  });

  it("no confunde una palabra en español con una frase en inglés", () => {
    expect(findEnglishUiText("<p>Contraseña y Asistente de Passwords</p>")).toEqual([]);
    expect(findEnglishUiText("<p>Fuentes y SourceMap</p>")).toEqual([]);
  });

  it("no marca un término que el glosario conserva en inglés", () => {
    expect(findEnglishUiText("<p>Gestión FinOps en Azure con UTC</p>")).toEqual([]);
  });
});
