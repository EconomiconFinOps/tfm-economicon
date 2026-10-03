import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { TRUE_VALUES, parseDotenv, resolveVariables } from "./local-doctor.mjs";

const DEMO_EMAIL = "operator@example.com";
const TENANT = "tenant-core";
// Subscription of the simulator dataset; the default ingestion covers 2024-06-01..2024-06-20.
const SUBSCRIPTION = "64e355d7-997c-491d-b0c1-8414dccfcf42";
const PERIOD = { start_date: "2024-06-01", end_date: "2024-06-21" };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const REQUEST_TIMEOUT_MS = 10_000;

class StepError extends Error {}

function port(vars, name, fallback) {
  const value = vars.get(name);
  return value ? value : fallback;
}

export function composeRunner(root) {
  return (args) =>
    new Promise((resolve) => {
      execFile(
        "docker",
        ["compose", "--project-directory", root, ...args],
        { encoding: "utf8", timeout: 120_000, windowsHide: true },
        (error, stdout) => resolve({ code: error ? (typeof error.code === "number" ? error.code : 1) : 0, stdout: stdout ?? "" }),
      );
    });
}

export async function runSmoke({
  root,
  env = process.env,
  fetchImpl = fetch,
  compose = composeRunner(root),
  healthTimeoutMs = 60_000,
  jobTimeoutMs = 120_000,
  pollMs = 2_000,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
}) {
  const lines = [];
  const envPath = path.join(root, ".env");
  const vars = resolveVariables(fs.existsSync(envPath) ? parseDotenv(fs.readFileSync(envPath, "utf8"), env) : new Map(), env);

  if (!TRUE_VALUES.has((vars.get("DEMO_SEED_ENABLED") ?? "").trim().toLowerCase())) {
    lines.push("[FALLO] El smoke necesita el usuario demo: pon DEMO_SEED_ENABLED=true en .env y recrea el backend.");
    return { code: 1, lines };
  }
  if (!vars.get("DEMO_PASSWORD")) {
    lines.push("[FALLO] El smoke necesita DEMO_PASSWORD en .env o en el entorno.");
    return { code: 1, lines };
  }

  const database = databaseName(vars.get("DATABASE_URL"));
  const api = `http://127.0.0.1:${port(vars, "API_HOST_PORT", "8000")}`;
  const services = [
    ["backend", `${api}/health`],
    ["processor", `http://127.0.0.1:${port(vars, "PROCESSOR_HOST_PORT", "8001")}/health`],
    ["azure-cost-api", `http://127.0.0.1:${port(vars, "AZURE_COST_API_HOST_PORT", "8002")}/health`],
    ["frontend", `http://127.0.0.1:${port(vars, "FRONTEND_HOST_PORT", "5173")}/`],
  ];

  const request = (url, init = {}) => fetchImpl(url, { ...init, signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
  const until = async (timeoutMs, attempt) => {
    const deadline = Date.now() + timeoutMs;
    for (;;) {
      const result = await attempt();
      if (result !== undefined) return result;
      if (Date.now() >= deadline) return undefined;
      await sleep(pollMs);
    }
  };

  let token;
  let jobId;
  const steps = [
    ["Salud de backend, processor, Azure Cost API y frontend", async () => {
      for (const [name, url] of services) {
        const healthy = await until(healthTimeoutMs, async () => {
          try {
            return (await request(url)).ok ? true : undefined;
          } catch {
            return undefined;
          }
        });
        if (!healthy) throw new StepError(`${name} no responde en ${url}`);
      }
    }],
    ["Login del usuario demo", async () => {
      const response = await request(`${api}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: DEMO_EMAIL, password: vars.get("DEMO_PASSWORD") }),
      });
      if (!response.ok) throw new StepError(`login respondio ${response.status}`);
      token = (await response.json()).access_token;
      if (!token) throw new StepError("login no devolvio access_token");
    }],
    ["Ingesta de costes desde la Azure Cost API simulada", async () => {
      const result = await compose([
        "exec", "-T", "processor", "python", "-m", "app.run_azure_cost_ingestion",
        "--tenant-id", TENANT, "--subscription-id", SUBSCRIPTION,
      ]);
      if (result.code !== 0) throw new StepError(`ingesta de costes termino con codigo ${result.code}`);
    }],
    ["Resumen de costes con datos", async () => {
      const query = new URLSearchParams(PERIOD);
      const response = await request(`${api}/billing/summary?${query}`, { headers: authHeaders(token) });
      if (!response.ok) throw new StepError(`resumen de costes respondio ${response.status}`);
      const summary = await response.json();
      if (summary.data_status === "empty" || !summary.totals?.length) {
        throw new StepError("resumen de costes sin datos para el periodo ingerido");
      }
    }],
    ["Job de documento publicado en RabbitMQ y completado por el processor", async () => {
      const response = await request(`${api}/jobs/ingest`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: TENANT, source: "local-smoke", text_content: "Smoke del entorno local." }),
      });
      if (!response.ok) throw new StepError(`job de ingesta respondio ${response.status}`);
      jobId = (await response.json()).job_id;
      // The id goes into SQL text, so only a UUID is accepted.
      if (!UUID.test(String(jobId))) throw new StepError("job de ingesta sin un identificador UUID valido");
      const status = await until(jobTimeoutMs, async () => {
        const result = await compose([
          "exec", "-T", "cockroachdb", "/cockroach/cockroach", "sql", "--insecure", "--format=csv", `--database=${database}`,
          "-e", `SELECT status FROM jobs WHERE id = '${jobId}'`,
        ]);
        if (result.code !== 0) throw new StepError(`no se pudo leer el estado del job en la base ${database} de CockroachDB`);
        const value = result.stdout.trim().split(/\r?\n/).at(-1);
        return value === "completed" || value === "failed" ? value : undefined;
      });
      if (status !== "completed") {
        throw new StepError(status ? `el job ${jobId} termino en ${status}` : `el job ${jobId} no se completo a tiempo`);
      }
    }],
  ];

  for (const [index, [name, run]] of steps.entries()) {
    try {
      await run();
      lines.push(`[OK] ${index + 1}/${steps.length} ${name}`);
    } catch (error) {
      const reason = error instanceof StepError ? error.message : "error inesperado";
      lines.push(`[FALLO] ${index + 1}/${steps.length} ${name}: ${reason}`);
      return { code: 1, lines };
    }
  }
  lines.push("[OK] Recorrido minimo verificado.");
  return { code: 0, lines };
}

function databaseName(dsn) {
  try {
    const name = new URL(dsn).pathname.slice(1);
    return /^[A-Za-z0-9_]+$/.test(name) ? name : "defaultdb";
  } catch {
    return "defaultdb";
  }
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}`, "X-Tenant-Id": TENANT };
}

async function main(argv) {
  const index = argv.indexOf("--project-directory");
  const root = index >= 0 ? path.resolve(argv[index + 1]) : path.dirname(path.dirname(fileURLToPath(import.meta.url)));
  const { code, lines } = await runSmoke({ root });
  for (const line of lines) (line.startsWith("[FALLO]") ? console.error : console.log)(line);
  process.exitCode = code;
}

// argv[1] is not always a file (for example "-" when the module is read from standard input).
function isMainModule() {
  if (!process.argv[1]) return false;
  try {
    return fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
}

if (isMainModule()) {
  await main(process.argv.slice(2));
}
