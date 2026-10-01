import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parseDotenv, readComposeContract, runDoctor } from "./local-doctor.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const composeText = fs.readFileSync(path.join(root, "docker-compose.yml"), "utf8");
const exampleText = fs.readFileSync(path.join(root, ".env.example"), "utf8");

const SECRETS = {
  AUTH_SECRET_KEY: "SENTINEL-auth-0123456789abcdefghijklmnop",
  RABBITMQ_DEFAULT_USER: "sentinel-rabbit-user",
  RABBITMQ_DEFAULT_PASS: "SENTINEL-rabbit@pass:%x",
  RABBITMQ_ERLANG_COOKIE: "SENTINELCOOKIEVALUE",
  POSTGRES_PASSWORD: "SENTINEL-pg@pass:%y",
  GRAFANA_ADMIN_PASSWORD: "SENTINEL-grafana",
};
const enc = encodeURIComponent;
const VALID = {
  ...SECRETS,
  RABBITMQ_URL: `amqp://${enc(SECRETS.RABBITMQ_DEFAULT_USER)}:${enc(SECRETS.RABBITMQ_DEFAULT_PASS)}@rabbitmq:5672/`,
  VECTOR_DATABASE_URL: `postgresql+psycopg://postgres:${enc(SECRETS.POSTGRES_PASSWORD)}@postgres-pgvector:5432/embeddings`,
  DATABASE_URL: "cockroachdb+psycopg://root@cockroachdb:26257/defaultdb?sslmode=disable",
  RUNTIME_ENVIRONMENT: "development",
  ALLOW_INSECURE_LOCAL_DATABASE: "true",
};
const SENTINELS = [
  ...Object.values(SECRETS),
  ...Object.values(SECRETS).map(enc),
  VALID.RABBITMQ_URL,
  VALID.VECTOR_DATABASE_URL,
];

const dotenv = (vars) => Object.entries(vars).map(([key, value]) => `${key}=${value}`).join("\n") + "\n";

function project(envText) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup-doctor-"));
  fs.writeFileSync(path.join(dir, "docker-compose.yml"), composeText);
  if (envText !== undefined) fs.writeFileSync(path.join(dir, ".env"), envText);
  return dir;
}

const noDocker = { containerPorts: async () => [], volumes: async () => [] };
const allFree = async () => true;

async function doctor(envText, options = {}) {
  const dir = project(envText);
  try {
    const result = await runDoctor({
      root: dir,
      env: options.env ?? {},
      docker: options.docker ?? noDocker,
      isPortFree: "isPortFree" in options ? options.isPortFree : allFree,
    });
    return { ...result, text: result.lines.map(({ text }) => text).join("\n"), dir };
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function assertNoSecrets(text) {
  for (const sentinel of SENTINELS) assert.ok(!text.includes(sentinel), "secret leaked");
  assert.doesNotMatch(text, /SENTINEL/i);
}

test("parses dotenv lines the way Compose does", () => {
  const vars = parseDotenv([
    "# comment",
    "",
    "A=plain",
    "B=with spaces  # inline comment",
    "C='single # kept'",
    'D="double \\"quoted\\" # kept"',
    "export E=exported",
    "F=a=b=c",
    "G=",
    "  H = trimmed  ",
    "I=value#nocomment",
  ].join("\r\n"));
  assert.equal(vars.get("A"), "plain");
  assert.equal(vars.get("B"), "with spaces");
  assert.equal(vars.get("C"), "single # kept");
  assert.equal(vars.get("D"), 'double "quoted" # kept');
  assert.equal(vars.get("E"), "exported");
  assert.equal(vars.get("F"), "a=b=c");
  assert.equal(vars.get("G"), "");
  assert.equal(vars.get("H"), "trimmed");
  assert.equal(vars.get("I"), "value#nocomment");
});

test("reads required variables and published ports from the Compose file", () => {
  const contract = readComposeContract(composeText);
  assert.deepEqual(contract.required, [
    "AUTH_SECRET_KEY", "DATABASE_URL", "GRAFANA_ADMIN_PASSWORD", "POSTGRES_PASSWORD",
    "RABBITMQ_DEFAULT_PASS", "RABBITMQ_DEFAULT_USER", "RABBITMQ_ERLANG_COOKIE",
    "RABBITMQ_URL", "VECTOR_DATABASE_URL",
  ]);
  const ports = Object.fromEntries(contract.ports.map((port) => [port.variable, port]));
  assert.deepEqual(Object.keys(ports).sort(), [
    "API_HOST_PORT", "AZURE_COST_API_HOST_PORT", "COCKROACH_HTTP_PORT", "COCKROACH_SQL_PORT",
    "FRONTEND_HOST_PORT", "GRAFANA_PORT", "PGVECTOR_PORT", "PROCESSOR_HOST_PORT",
    "PROMETHEUS_PORT", "RABBITMQ_MANAGEMENT_PORT", "RABBITMQ_PORT",
  ]);
  assert.deepEqual(ports.COCKROACH_SQL_PORT, { variable: "COCKROACH_SQL_PORT", default: "26257", host: "127.0.0.1" });
  assert.deepEqual(ports.API_HOST_PORT, { variable: "API_HOST_PORT", default: "8000", host: "0.0.0.0" });
});

test("a valid local configuration passes", async () => {
  const result = await doctor(dotenv(VALID));
  assert.equal(result.code, 0, result.text);
  assert.match(result.text, /\[OK\]/);
  assert.match(result.text, /instalacion nueva/i);
  assertNoSecrets(result.text);
});

test("a plain copy of .env.example lists every missing secret and the opt-in", async () => {
  const result = await doctor(exampleText);
  assert.equal(result.code, 1);
  for (const name of readComposeContract(composeText).required) {
    assert.match(result.text, new RegExp(`\\b${name}\\b`), name);
  }
  assert.match(result.text, /RUNTIME_ENVIRONMENT/);
  assert.match(result.text, /ALLOW_INSECURE_LOCAL_DATABASE/);
});

test("a missing .env is reported and never created", async () => {
  const dir = project(undefined);
  try {
    const result = await runDoctor({ root: dir, env: {}, docker: noDocker, isPortFree: allFree });
    const text = result.lines.map(({ text }) => text).join("\n");
    assert.equal(result.code, 1);
    assert.match(text, /\.env/);
    assert.match(text, /README/);
    assert.equal(fs.existsSync(path.join(dir, ".env")), false);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("names both variables when the RabbitMQ or pgvector credentials disagree, without values", async () => {
  const rabbit = await doctor(dotenv({ ...VALID, RABBITMQ_DEFAULT_PASS: "SENTINEL-other" }));
  assert.equal(rabbit.code, 1);
  assert.match(rabbit.text, /RABBITMQ_URL.*RABBITMQ_DEFAULT_PASS|RABBITMQ_DEFAULT_PASS.*RABBITMQ_URL/);
  assertNoSecrets(rabbit.text);

  const user = await doctor(dotenv({ ...VALID, RABBITMQ_DEFAULT_USER: "sentinel-other-user" }));
  assert.equal(user.code, 1);
  assert.match(user.text, /RABBITMQ_DEFAULT_USER/);

  const vector = await doctor(dotenv({ ...VALID, POSTGRES_PASSWORD: "SENTINEL-other" }));
  assert.equal(vector.code, 1);
  assert.match(vector.text, /VECTOR_DATABASE_URL.*POSTGRES_PASSWORD|POSTGRES_PASSWORD.*VECTOR_DATABASE_URL/);
  assertNoSecrets(vector.text);
});

test("an unencoded special character in the URL password is a mismatch, not a crash", async () => {
  const raw = `amqp://${SECRETS.RABBITMQ_DEFAULT_USER}:${SECRETS.RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/`;
  const result = await doctor(dotenv({ ...VALID, RABBITMQ_URL: raw }));
  assert.equal(result.code, 1);
  assert.match(result.text, /RABBITMQ_URL/);
  assertNoSecrets(result.text);
});

test("a malformed URL is reported by name only", async () => {
  const result = await doctor(dotenv({ ...VALID, VECTOR_DATABASE_URL: "not a url SENTINEL-pg" }));
  assert.equal(result.code, 1);
  assert.match(result.text, /VECTOR_DATABASE_URL/);
  assertNoSecrets(result.text);
});

test("a short AUTH_SECRET_KEY is rejected without printing it", async () => {
  const result = await doctor(dotenv({ ...VALID, AUTH_SECRET_KEY: "SENTINEL-short" }));
  assert.equal(result.code, 1);
  assert.match(result.text, /AUTH_SECRET_KEY/);
  assert.match(result.text, /32/);
  assertNoSecrets(result.text);
});

test("the insecure local database needs both development/test and the explicit opt-in", async () => {
  for (const vars of [
    { RUNTIME_ENVIRONMENT: "production", ALLOW_INSECURE_LOCAL_DATABASE: "true" },
    { RUNTIME_ENVIRONMENT: "development", ALLOW_INSECURE_LOCAL_DATABASE: "false" },
    { RUNTIME_ENVIRONMENT: "Development", ALLOW_INSECURE_LOCAL_DATABASE: "true" },
    { RUNTIME_ENVIRONMENT: "development", ALLOW_INSECURE_LOCAL_DATABASE: "TRUE" },
  ]) {
    const result = await doctor(dotenv({ ...VALID, ...vars }));
    assert.equal(result.code, 1, JSON.stringify(vars));
    assert.match(result.text, /ALLOW_INSECURE_LOCAL_DATABASE/);
  }
  const test_ = await doctor(dotenv({ ...VALID, RUNTIME_ENVIRONMENT: "test" }));
  assert.equal(test_.code, 0, test_.text);
});

test("the process environment wins over .env, also when it is empty", async () => {
  const fromEnv = await doctor(dotenv({ ...VALID, AUTH_SECRET_KEY: "" }), {
    env: { AUTH_SECRET_KEY: SECRETS.AUTH_SECRET_KEY },
  });
  assert.equal(fromEnv.code, 0, fromEnv.text);

  const emptied = await doctor(dotenv(VALID), { env: { GRAFANA_ADMIN_PASSWORD: "" } });
  assert.equal(emptied.code, 1);
  assert.match(emptied.text, /GRAFANA_ADMIN_PASSWORD/);
});

function listen(host) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, host, () => resolve(server));
  });
}

test("reports a busy loopback port by variable and number", async () => {
  const server = await listen("127.0.0.1");
  const port = server.address().port;
  try {
    const result = await doctor(dotenv({ ...VALID, PGVECTOR_PORT: String(port) }), { isPortFree: undefined });
    assert.equal(result.code, 1, result.text);
    assert.match(result.text, new RegExp(`PGVECTOR_PORT.*${port}`));
  } finally {
    server.close();
  }
});

test("a port published on all interfaces is busy when only loopback is taken", async () => {
  const server = await listen("127.0.0.1");
  const port = server.address().port;
  try {
    const result = await doctor(dotenv({ ...VALID, API_HOST_PORT: String(port) }), { isPortFree: undefined });
    assert.equal(result.code, 1, result.text);
    assert.match(result.text, new RegExp(`API_HOST_PORT.*${port}`));
  } finally {
    server.close();
  }
});

test("ports already published by this Compose project are not busy", async () => {
  const server = await listen("127.0.0.1");
  const port = server.address().port;
  try {
    const result = await doctor(dotenv({ ...VALID, PGVECTOR_PORT: String(port) }), {
      isPortFree: undefined,
      docker: { containerPorts: async () => [port], volumes: async () => [] },
    });
    assert.equal(result.code, 0, result.text);
  } finally {
    server.close();
  }
});

test("rejects invalid and duplicated host ports", async () => {
  const invalid = await doctor(dotenv({ ...VALID, API_HOST_PORT: "abc", PGVECTOR_PORT: "70000" }));
  assert.equal(invalid.code, 1);
  assert.match(invalid.text, /API_HOST_PORT/);
  assert.match(invalid.text, /PGVECTOR_PORT/);

  const duplicated = await doctor(dotenv({ ...VALID, API_HOST_PORT: "9999", GRAFANA_PORT: "9999" }));
  assert.equal(duplicated.code, 1);
  assert.match(duplicated.text, /API_HOST_PORT/);
  assert.match(duplicated.text, /GRAFANA_PORT/);
});

test("an existing installation asks to keep the existing cookie and Grafana password", async () => {
  const result = await doctor(dotenv(VALID), {
    docker: { containerPorts: async () => [], volumes: async () => ["tfm_cockroach-data", "tfm_rabbitmq-data"] },
  });
  assert.equal(result.code, 0, result.text);
  assert.match(result.text, /instalacion existente/i);
  assert.match(result.text, /RABBITMQ_ERLANG_COOKIE/);
  assert.match(result.text, /GRAFANA_ADMIN_PASSWORD/);
});

test("still reports .env problems when Docker does not answer", async () => {
  const down = {
    containerPorts: async () => { throw new Error("daemon down SENTINEL"); },
    volumes: async () => { throw new Error("daemon down SENTINEL"); },
  };
  const result = await doctor(exampleText, { docker: down });
  assert.equal(result.code, 1);
  assert.match(result.text, /Docker/);
  assert.match(result.text, /AUTH_SECRET_KEY/);
  assertNoSecrets(result.text);
});

test("never prints a secret in any combination of present, missing and wrong values", async () => {
  const cases = [
    VALID,
    { ...VALID, RABBITMQ_DEFAULT_PASS: "" },
    { ...VALID, RABBITMQ_URL: "" },
    { ...VALID, POSTGRES_PASSWORD: "SENTINEL-x", RABBITMQ_DEFAULT_USER: "sentinel-y" },
    { ...VALID, VECTOR_DATABASE_URL: "postgresql://postgres:SENTINEL%ZZ@h/db" },
    { ...VALID, AUTH_SECRET_KEY: "SENTINEL" },
  ];
  for (const vars of cases) {
    const result = await doctor(dotenv(vars));
    assertNoSecrets(result.text);
  }
});

test("the command line reads the project directory and never prints secrets", () => {
  const dir = project(dotenv({ ...VALID, RABBITMQ_DEFAULT_PASS: "SENTINEL-other" }));
  try {
    const env = { ...process.env };
    for (const name of Object.keys(VALID)) delete env[name];
    const result = spawnSync(process.execPath, [path.join(root, "tools", "local-doctor.mjs"), "--project-directory", dir], {
      encoding: "utf8",
      env,
      timeout: 60_000,
    });
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stdout + result.stderr, /RABBITMQ_DEFAULT_PASS/);
    assertNoSecrets(result.stdout + result.stderr);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
