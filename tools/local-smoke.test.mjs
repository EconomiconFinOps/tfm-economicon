import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { runSmoke } from "./local-smoke.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const PASSWORD = "SENTINEL-demo-password";
const TOKEN = "SENTINEL-access-token";
const JOB_ID = "3f2c8a1e-6b4d-4e8f-9a0b-1c2d3e4f5a6b";
const ENV = { DEMO_SEED_ENABLED: "true", DEMO_PASSWORD: PASSWORD };

function project(envText = "") {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup-smoke-"));
  fs.writeFileSync(path.join(dir, ".env"), envText);
  return dir;
}

const json = (status, body) => ({ status, ok: status >= 200 && status < 300, json: async () => body });

function fakeStack(overrides = {}) {
  const calls = [];
  const state = { jobPolls: 0 };
  const responses = {
    "GET 8000 /health": () => json(200, { status: "ok" }),
    "GET 8001 /health": () => json(200, { status: "ok" }),
    "GET 8002 /health": () => json(200, { status: "ok" }),
    "GET 5173 /": () => json(200, {}),
    "POST 8000 /auth/login": () => json(200, { access_token: TOKEN, token_type: "bearer" }),
    "GET 8000 /billing/summary": () => json(200, { data_status: "available", totals: [{ amount: "12.50", currency: "USD" }] }),
    "POST 8000 /jobs/ingest": () => json(202, { job_id: JOB_ID, status: "queued" }),
    ...overrides.http,
  };
  const fetchImpl = async (url, init = {}) => {
    const parsed = new URL(url);
    const key = `${init.method ?? "GET"} ${parsed.port} ${parsed.pathname}`;
    calls.push({ kind: "http", key, url, init });
    const handler = responses[key];
    if (!handler) throw new Error(`unexpected ${key}`);
    return handler({ url: parsed, init });
  };
  const compose = async (args) => {
    calls.push({ kind: "compose", args });
    if (args.includes("app.run_azure_cost_ingestion")) {
      return overrides.ingestion?.(args) ?? { code: 0, stdout: '{"status": "completed", "row_count": 20}' };
    }
    if (args.includes("cockroachdb")) {
      state.jobPolls += 1;
      return overrides.jobStatus?.(state.jobPolls, args) ?? { code: 0, stdout: "status\ncompleted\n" };
    }
    throw new Error(`unexpected compose ${args.join(" ")}`);
  };
  return { calls, state, fetchImpl, compose };
}

const fast = { healthTimeoutMs: 50, jobTimeoutMs: 50, pollMs: 1, sleep: async () => {} };

async function smoke(stack, { env = ENV, envText = "", options = {} } = {}) {
  const dir = project(envText);
  try {
    const result = await runSmoke({ root: dir, env, fetchImpl: stack.fetchImpl, compose: stack.compose, ...fast, ...options });
    return { ...result, text: result.lines.join("\n") };
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function assertNoSecrets(text) {
  assert.ok(!text.includes(PASSWORD), "password leaked");
  assert.ok(!text.includes(TOKEN), "token leaked");
}

test("a healthy stack passes the five steps in order", async () => {
  const stack = fakeStack();
  const result = await smoke(stack);
  assert.equal(result.code, 0, result.text);
  const passed = result.lines.filter((line) => line.startsWith("[OK]"));
  assert.equal(passed.length, 6);
  const order = stack.calls.map((call) => (call.kind === "http" ? call.key : `compose ${call.args.includes("cockroachdb") ? "sql" : "ingest"}`));
  const first = (key) => order.indexOf(key);
  assert.ok(first("POST 8000 /auth/login") > Math.max(first("GET 8000 /health"), first("GET 8001 /health"), first("GET 8002 /health"), first("GET 5173 /")));
  assert.ok(first("compose ingest") > first("POST 8000 /auth/login"));
  assert.ok(first("GET 8000 /billing/summary") > first("compose ingest"));
  assert.ok(first("POST 8000 /jobs/ingest") > first("GET 8000 /billing/summary"));
  assert.ok(first("compose sql") > first("POST 8000 /jobs/ingest"));
  assertNoSecrets(result.text);
});

test("sends the demo credentials, the bearer token and the demo tenant", async () => {
  const stack = fakeStack();
  await smoke(stack);
  const login = stack.calls.find((call) => call.key === "POST 8000 /auth/login");
  assert.deepEqual(JSON.parse(login.init.body), { email: "operator@example.com", password: PASSWORD });
  for (const key of ["GET 8000 /billing/summary", "POST 8000 /jobs/ingest"]) {
    const call = stack.calls.find((item) => item.key === key);
    assert.equal(call.init.headers.Authorization, `Bearer ${TOKEN}`);
    assert.equal(call.init.headers["X-Tenant-Id"], "tenant-core");
  }
  const summary = new URL(stack.calls.find((call) => call.key === "GET 8000 /billing/summary").url);
  assert.equal(summary.searchParams.get("start_date"), "2024-06-01");
  assert.equal(summary.searchParams.get("end_date"), "2024-06-21");
  const job = JSON.parse(stack.calls.find((call) => call.key === "POST 8000 /jobs/ingest").init.body);
  assert.equal(job.tenant_id, "tenant-core");
  const ingest = stack.calls.find((call) => call.kind === "compose" && call.args.includes("app.run_azure_cost_ingestion"));
  assert.deepEqual(ingest.args.slice(0, 3), ["exec", "-T", "processor"]);
  assert.ok(ingest.args.includes("tenant-core"));
});

test("stops before calling the backend when the demo seed is not enabled", async () => {
  for (const [env, variable] of [
    [{ DEMO_PASSWORD: PASSWORD }, "DEMO_SEED_ENABLED"],
    [{ DEMO_SEED_ENABLED: "false", DEMO_PASSWORD: PASSWORD }, "DEMO_SEED_ENABLED"],
    [{ DEMO_SEED_ENABLED: "true", DEMO_PASSWORD: "" }, "DEMO_PASSWORD"],
  ]) {
    const stack = fakeStack();
    const result = await smoke(stack, { env });
    assert.equal(result.code, 1);
    assert.match(result.text, new RegExp(variable));
    assert.equal(stack.calls.length, 0);
    assertNoSecrets(result.text);
  }
});

test("reads the demo settings and ports from .env, with the environment winning", async () => {
  const stack = fakeStack({
    http: {
      "GET 18000 /health": () => json(200, {}),
      "POST 18000 /auth/login": () => json(200, { access_token: TOKEN }),
      "GET 18000 /billing/summary": () => json(200, { data_status: "partial", totals: [{ amount: "1" }] }),
      "POST 18000 /jobs/ingest": () => json(202, { job_id: JOB_ID }),
    },
  });
  const result = await smoke(stack, {
    env: { API_HOST_PORT: "18000" },
    envText: `DEMO_SEED_ENABLED=true\nDEMO_PASSWORD=${PASSWORD}\nAPI_HOST_PORT=9999\n`,
  });
  assert.equal(result.code, 0, result.text);
  assert.ok(stack.calls.some((call) => call.kind === "http" && call.url.includes(":18000")));
  assert.ok(stack.calls.every((call) => call.kind !== "http" || !call.url.includes(":9999")));
});

test("names the processor when its health check never answers, within the bounded wait", async () => {
  const stack = fakeStack({ http: { "GET 8001 /health": () => { throw new Error("ECONNREFUSED"); } } });
  const started = Date.now();
  const result = await smoke(stack, { options: { sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)), pollMs: 5 } });
  assert.equal(result.code, 1);
  assert.match(result.text, /\[FALLO\].*processor/i);
  assert.ok(Date.now() - started < 2_000);
  assert.ok(!stack.calls.some((call) => call.key === "POST 8000 /auth/login"));
});

test("reports a rejected login without printing the password", async () => {
  const stack = fakeStack({ http: { "POST 8000 /auth/login": () => json(401, { detail: `bad ${PASSWORD}` }) } });
  const result = await smoke(stack);
  assert.equal(result.code, 1);
  assert.match(result.text, /\[FALLO\].*login.*401/i);
  assertNoSecrets(result.text);
});

test("reports a failed cost ingestion and does not continue", async () => {
  const stack = fakeStack({ ingestion: () => ({ code: 1, stdout: '{"error_code": "AzureCostHttpError"}' }) });
  const result = await smoke(stack);
  assert.equal(result.code, 1);
  assert.match(result.text, /\[FALLO\].*ingesta de costes/i);
  assert.ok(!stack.calls.some((call) => call.key === "GET 8000 /billing/summary"));
});

test("an empty cost summary is a failure", async () => {
  for (const body of [{ data_status: "empty", totals: [] }, { data_status: "available", totals: [] }]) {
    const stack = fakeStack({ http: { "GET 8000 /billing/summary": () => json(200, body) } });
    const result = await smoke(stack);
    assert.equal(result.code, 1, JSON.stringify(body));
    assert.match(result.text, /\[FALLO\].*resumen/i);
  }
});

test("a job that never completes fails within the bounded wait, and a failed job fails at once", async () => {
  const pending = fakeStack({ jobStatus: () => ({ code: 0, stdout: "status\nqueued\n" }) });
  const waited = await smoke(pending, { options: { sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)), pollMs: 5 } });
  assert.equal(waited.code, 1);
  assert.match(waited.text, /\[FALLO\].*job/i);
  assert.ok(pending.state.jobPolls >= 2);

  const failed = fakeStack({ jobStatus: () => ({ code: 0, stdout: "status\nfailed\n" }) });
  const result = await smoke(failed);
  assert.equal(result.code, 1);
  assert.match(result.text, /failed/);
  assert.equal(failed.state.jobPolls, 1);
});

test("never puts an unexpected job id into the SQL query", async () => {
  const stack = fakeStack({ http: { "POST 8000 /jobs/ingest": () => json(202, { job_id: "x'; DROP TABLE jobs; --" }) } });
  const result = await smoke(stack);
  assert.equal(result.code, 1);
  assert.equal(stack.state.jobPolls, 0);
});

test("can run twice against the same stack", async () => {
  const stack = fakeStack();
  assert.equal((await smoke(stack)).code, 0);
  assert.equal((await smoke(stack)).code, 0);
  assert.equal(stack.calls.filter((call) => call.key === "POST 8000 /jobs/ingest").length, 2);
});

test("the command line stops on a disabled demo seed without network calls", () => {
  const dir = project("DEMO_SEED_ENABLED=false\n");
  try {
    const env = { ...process.env };
    delete env.DEMO_SEED_ENABLED;
    delete env.DEMO_PASSWORD;
    const result = spawnSync(process.execPath, [path.join(root, "tools", "local-smoke.mjs"), "--project-directory", dir], {
      encoding: "utf8",
      env,
      timeout: 30_000,
    });
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stdout + result.stderr, /DEMO_SEED_ENABLED/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("an unexpected error never prints its message, which may carry response text", async () => {
  const stack = fakeStack({
    http: {
      "POST 8000 /auth/login": () => ({ status: 200, ok: true, json: async () => { throw new SyntaxError(`Unexpected token in ${TOKEN}`); } }),
    },
  });
  const result = await smoke(stack);
  assert.equal(result.code, 1);
  assert.match(result.text, /\[FALLO\].*login/i);
  assertNoSecrets(result.text);
});

test("a job that RabbitMQ could not accept fails the job step", async () => {
  const stack = fakeStack({ http: { "POST 8000 /jobs/ingest": () => json(503, { code: "publish_not_sent" }) } });
  const result = await smoke(stack);
  assert.equal(result.code, 1);
  assert.match(result.text, /\[FALLO\].*503/);
  assert.equal(stack.state.jobPolls, 0);
});
