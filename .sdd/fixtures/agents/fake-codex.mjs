import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

if (process.argv.includes("--version")) {
  console.log("codex-cli 0.140.0");
  process.exit(0);
}
const prompt = process.argv.at(-1);
const run = prompt.match(/run ([0-9a-f-]{36})/i)[1];
const inputPath = prompt.match(/Read ([^ ]+) and/)[1];
const outputPath = prompt.match(/to ([^ ]+\/output\.json)/)[1];
const inputRaw = await readFile(inputPath, "utf8");
const input = JSON.parse(inputRaw);
const output = {
  schema_version: "2.0.0", run_id: run, input_sha256: createHash("sha256").update(inputRaw).digest("hex"),
  correlation_id: input.correlation_id, skill: input.skill, status: "BLOCKED", artifacts: [],
  docs_consulted: input.docs_context.applicable, doc_conflicts: [], traceability: [],
  errors: [{ code: "FIXTURE-BLOCKED", message: "fixture", path: null }],
  result: { acceptance_criteria: ["AC-001"], gaps: ["fixture"] },
};
await writeFile(outputPath, JSON.stringify(output));
const receiptPath = process.argv[process.argv.indexOf("-o") + 1];
await writeFile(receiptPath, JSON.stringify({ run_id: run, status: "BLOCKED", output_path: outputPath }));
console.log(JSON.stringify({ type: "thread.started", thread_id: "thread-fixture", model: "fixture" }));
console.log(JSON.stringify({ type: "turn.completed", usage: { input_tokens: 1, output_tokens: 1 } }));
