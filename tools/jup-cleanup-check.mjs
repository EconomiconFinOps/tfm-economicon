import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const FORBIDDEN_PREFIXES = [
  ".claude/",
  ".codex/",
  ".engram/",
  "tools/engram/",
  "docs/templates/hu/",
];
const FORBIDDEN_FILES = new Set([
  "docs/hu-release-notes.md",
  "docs/manuals/sdd-user-manual.md",
  "docs/spikes/open-spec-engram.md",
  "docs/spikes/openspec-hu-adaptation-plan.md",
  "tools/hu-check.mjs",
  "tools/hu-check.test.mjs",
]);
const PARALLEL_CHANGE =
  /^openspec\/changes\/(?:archive\/)?(?:\d{4}-\d{2}-\d{2}-)?hu-\d{3}(?:[-/]|$)/i;
const WINDOWS_BINARY = /\.(?:exe|dll|msi)$/i;

export function validateTrackedFiles(files) {
  const errors = [];

  for (const original of files) {
    const file = original.replaceAll("\\", "/");

    if (FORBIDDEN_PREFIXES.some((prefix) => file.startsWith(prefix))) {
      errors.push("Configuración o herramienta ajena al proyecto: " + file);
      continue;
    }

    if (FORBIDDEN_FILES.has(file)) {
      errors.push("Artefacto obsoleto del flujo paralelo: " + file);
      continue;
    }

    if (PARALLEL_CHANGE.test(file)) {
      errors.push("Propuesta con numeración paralela: " + file);
      continue;
    }

    if (WINDOWS_BINARY.test(file)) {
      errors.push("Binario específico de Windows: " + file);
    }
  }

  return errors;
}

export function getTrackedFiles(cwd = process.cwd()) {
  const output = execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard", "-z"],
    { cwd, encoding: "utf8" },
  );

  return output.split("\0").filter(Boolean);
}

function main() {
  const files = getTrackedFiles();
  const errors = validateTrackedFiles(files);
  if (errors.length > 0) {
    for (const error of errors) console.error("[ERROR] " + error);
    process.exitCode = 1;
    return;
  }

  console.log(
    "[OK] " + files.length + " archivos sin agentes personales, binarios ni tareas paralelas.",
  );
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main();
}
