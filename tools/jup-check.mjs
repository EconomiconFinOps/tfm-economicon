import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const CHANGE_PATTERN = /^jup-(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const REQUIRED_FILES = ["proposal.md", "design.md", "tasks.md"];

export function parseChange(argv) {
  const index = argv.indexOf("--change");
  return index >= 0 ? argv[index + 1] : undefined;
}

function findSpecFiles(root) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const target = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...findSpecFiles(target));
    if (entry.isFile() && entry.name.endsWith(".md")) files.push(target);
  }
  return files;
}

export function checkChange(root, change) {
  const errors = [];
  const match = CHANGE_PATTERN.exec(change ?? "");
  if (!match) return ["El change debe usar jup-NNN-descripcion-en-kebab-case."];

  const jupId = `JUP-${match[1]}`;
  const changeDir = path.join(root, "openspec", "changes", change);
  if (!fs.existsSync(changeDir)) return [`No existe ${path.relative(root, changeDir)}.`];

  const metadata = path.join(changeDir, ".openspec.yaml");
  if (!fs.existsSync(metadata)) errors.push("Falta .openspec.yaml.");
  for (const file of REQUIRED_FILES) {
    if (!fs.existsSync(path.join(changeDir, file))) errors.push(`Falta ${file}.`);
  }

  const specs = findSpecFiles(path.join(changeDir, "specs"));
  if (specs.length === 0) errors.push("Falta al menos un delta spec en specs/.");

  const textFiles = [metadata, ...REQUIRED_FILES.map((file) => path.join(changeDir, file)), ...specs]
    .filter((file) => fs.existsSync(file));
  const combined = textFiles.map((file) => fs.readFileSync(file, "utf8")).join("\n");
  const proposalPath = path.join(changeDir, "proposal.md");
  const proposal = fs.existsSync(proposalPath) ? fs.readFileSync(proposalPath, "utf8") : "";

  if (!combined.includes(jupId)) errors.push(`Los artefactos no contienen ${jupId}.`);
  if (!/^Trello:\s+https:\/\/trello\.com\/c\/[A-Za-z0-9]+/m.test(proposal)) {
    errors.push("proposal.md no contiene una URL directa de Trello.");
  }
  if (/\bHU-\d{3}\b/i.test(combined)) errors.push("Se detecto una numeracion paralela.");
  return errors;
}

function main() {
  const change = parseChange(process.argv.slice(2));
  if (!change) {
    console.error("Uso: pnpm jup:check --change jup-NNN-descripcion");
    process.exitCode = 2;
    return;
  }
  const errors = checkChange(process.cwd(), change);
  if (errors.length > 0) {
    for (const error of errors) console.error(`[ERROR] ${error}`);
    process.exitCode = 1;
    return;
  }
  console.log(`[OK] ${change} esta enlazado y completo.`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
