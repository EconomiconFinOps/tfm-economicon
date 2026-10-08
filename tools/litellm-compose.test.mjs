import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parse, stringify } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const gatewayImage = "ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd";
const testEnabled = process.env.JUP108_DOCKER_FAKE === "1";
const mockEnabled = process.env.JUP108_DOCKER_MOCK === "1";

test("JUP-108 AI consumers cannot start before a healthy gateway", {
  skip: process.env.JUP108_DOCKER_HEALTH !== "1",
}, () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "jup108-health-"));
  const project = `jup108-health-${randomBytes(5).toString("hex")}`;
  const ai = parse(fs.readFileSync(path.join(root, "infra/litellm/compose.ai.yml"), "utf8"));
  const file = path.join(directory, "compose.yaml");
  const environment = { ...process.env, COMPOSE_DISABLE_ENV_FILE: "1", COMPOSE_PROFILES: "" };
  const command = ["compose", "--env-file", path.join(directory, "empty.env"), "-p", project, "-f", file];
  fs.writeFileSync(path.join(directory, "empty.env"), "");
  function run(args) {
    const result = spawnSync("docker", args, { env: environment, encoding: "utf8", timeout: 60000 });
    assert.ifError(result.error);
    return result;
  }
  const receipt = { project, checks: {}, cleanup: false };
  try {
    for (const healthy of [false, true]) {
      const service = { image: gatewayImage, entrypoint: ["python", "-c", "import time; time.sleep(120)"],
        networks: ["isolated"] };
      fs.writeFileSync(file, stringify({ services: {
        litellm: { ...service, healthcheck: { test: ["CMD", "python", "-c", `exit(${healthy ? 0 : 1})`],
          interval: "1s", timeout: "2s", retries: 1 } },
        ...Object.fromEntries(["backend", "processor"].map((name) => [name,
          { ...service, depends_on: { litellm: ai.services[name].depends_on.litellm } }])),
      }, networks: { isolated: { internal: true } } }));
      const up = run([...command, "up", "-d", "--pull", "never", "--wait", "--wait-timeout", "20"]);
      const running = run([...command, "ps", "--services", "--status", "running"]);
      assert.equal(running.status, 0);
      const consumers = running.stdout.trim().split(/\r?\n/).filter((name) => ["backend", "processor"].includes(name));
      assert.equal(up.status === 0, healthy);
      assert.equal(consumers.length, healthy ? 2 : 0);
      receipt.checks[healthy ? "healthy_allows_both" : "unhealthy_blocks_both"] = true;
      assert.equal(run([...command, "down", "--timeout", "1"]).status, 0);
    }
  } finally {
    const down = run([...command, "down", "--volumes", "--remove-orphans", "--timeout", "1"]);
    const leftovers = ["container", "volume", "network"].map((kind) => {
      const result = run([kind, "ls", "-q", "--filter", `label=com.docker.compose.project=${project}`]);
      assert.equal(result.status, 0);
      return result.stdout.trim();
    });
    receipt.cleanup = down.status === 0 && leftovers.every((value) => value === "");
    fs.writeFileSync(path.join(directory, "receipt.json"), JSON.stringify(receipt, null, 2));
    console.log(`JUP108_HEALTH_RECEIPT=${directory}`);
    assert.ok(receipt.cleanup);
  }
});

test("JUP-108 root Compose keeps scoped gateway keys and state across recreation", { skip: !testEnabled }, () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "jup108-compose-"));
  const project = `jup108-fake-${randomBytes(5).toString("hex")}`;
  const upstream = `sk-${randomBytes(24).toString("hex")}`;
  const master = `sk-${randomBytes(24).toString("hex")}`;
  const password = randomBytes(24).toString("hex");
  const sensitive = [upstream, master, password];
  const safe = (value) => sensitive.reduce((text, secret) => text.replaceAll(secret, "[REDACTED]"), String(value));
  const environment = Object.fromEntries(Object.entries(process.env).filter(([name]) =>
    !/^(LITELLM_|OPENROUTER_|COMPOSE_|DATABASE_URL$|ECONOMICON_ENV_FILE$|OPENAI_API_KEY$)/i.test(name)));
  environment.COMPOSE_DISABLE_ENV_FILE = "1";

  const envPath = path.join(directory, "synthetic.env");
  fs.writeFileSync(envPath, [
    `OPENROUTER_API_KEY=${upstream}`,
    `LITELLM_MASTER_KEY=${master}`,
    `LITELLM_DATABASE_PASSWORD=${password}`,
    "DATABASE_URL=postgresql://synthetic@cockroachdb:26257/economicon",
    "RABBITMQ_URL=amqp://synthetic@rabbitmq:5672/",
    "VECTOR_DATABASE_URL=postgresql://synthetic@postgres-pgvector:5432/embeddings",
    "AUTH_SECRET_KEY=synthetic-test-only-not-a-production-secret",
    "RABBITMQ_DEFAULT_USER=synthetic",
    "RABBITMQ_DEFAULT_PASS=synthetic",
    "RABBITMQ_ERLANG_COOKIE=synthetic-test-only",
    "POSTGRES_PASSWORD=synthetic",
    "GRAFANA_ADMIN_PASSWORD=synthetic",
    "RUNTIME_ENVIRONMENT=development",
    "ALLOW_INSECURE_LOCAL_DATABASE=true",
  ].join("\n") + "\n");
  const missingEnvPath = path.join(directory, "missing-upstream.env");
  fs.writeFileSync(missingEnvPath, fs.readFileSync(envPath, "utf8")
    .replace(/^OPENROUTER_API_KEY=.*$/m, "OPENROUTER_API_KEY="));

  const gatewayConfig = parse(fs.readFileSync(path.join(root, "infra/litellm/config.example.yaml"), "utf8"));
  for (const model of gatewayConfig.model_list) {
    model.litellm_params.api_base = "http://fake-upstream:8080/v1";
  }
  const configPath = path.join(directory, "config.yaml");
  fs.writeFileSync(configPath, stringify(gatewayConfig));
  const responsePath = path.join(directory, "response.json");
  fs.writeFileSync(responsePath, JSON.stringify({ answer: "synthetic only" }));
  const fixturePath = path.join(root, "apps/processor/tests/fixtures/litellm_fake_upstream.py");
  const override = {
    services: {
      litellm: { volumes: [`${configPath.replaceAll("\\", "/")}:/app/economicon-config.yaml:ro`] },
      "fake-upstream": {
        image: gatewayImage,
        entrypoint: ["python", "/fixture/server.py"],
        environment: { EXPECTED_KEY: upstream },
        networks: ["gateway"],
        volumes: [
          `${fixturePath.replaceAll("\\", "/")}:/fixture/server.py:ro`,
          `${responsePath.replaceAll("\\", "/")}:/fixture/response.json:ro`,
        ],
      },
    },
    networks: { gateway: { internal: true }, default: { internal: true } },
  };
  const overridePath = path.join(directory, "override.yaml");
  fs.writeFileSync(overridePath, stringify(override));
  const probeOverridePath = path.join(directory, "probe-override.yaml");
  fs.writeFileSync(probeOverridePath, `services:
  backend:
    image: ${gatewayImage}
    build: !reset null
  processor:
    image: ${gatewayImage}
    build: !reset null
`);
  const compose = ["compose", "--env-file", envPath, "-p", project, "-f",
    path.join(root, "docker-compose.yml"), "-f", path.join(root, "infra/litellm/compose.ai.yml"),
    "-f", overridePath, "--profile", "ai"];
  const probeCompose = [...compose.slice(0, -2), "-f", probeOverridePath, ...compose.slice(-2)];
  const receipt = { project, mode: "synthetic-upstream-no-paid-calls", checks: {}, commands: [] };

  function run(args, { input, timeout = 30000, allowFailure = false } = {}) {
    const result = spawnSync("docker", args, {
      cwd: root, env: environment, input, timeout, encoding: "utf8", windowsHide: true,
    });
    receipt.commands.push({ operation: args[0] === "compose" ? args.at(-1) : args.slice(0, 2).join(" "),
      exit: result.status });
    if (result.error || (!allowFailure && result.status !== 0)) {
      throw new Error(`Docker operation failed: ${safe(result.error?.message ?? result.stderr).slice(0, 1200)}`);
    }
    return result;
  }

  const forward = `import json,sys,urllib.request,urllib.error
p=json.load(sys.stdin)
r=urllib.request.Request('http://127.0.0.1:4000'+p['path'],data=None if p['body'] is None else json.dumps(p['body']).encode(),headers={'Authorization':'Bearer '+p['key'],'Content-Type':'application/json'})
try:
    response=urllib.request.urlopen(r,timeout=15)
except urllib.error.HTTPError as exc:
    response=exc
with response:
    print(json.dumps({'status':response.status,'body':response.read().decode()}))`;
  function api(route, key = master, body = null) {
    const payload = JSON.stringify({ path: route, key, body });
    const result = run([...compose, "exec", "-T", "litellm", "python", "-c", forward], { input: payload });
    const response = JSON.parse(result.stdout);
    return { status: response.status, body: JSON.parse(response.body) };
  }

  const probe = `import json,os,urllib.request
url=os.environ['LITELLM_BASE_URL'].rstrip('/')+os.environ['PROBE_PATH']
body=json.loads(os.environ['PROBE_BODY'])
r=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['LITELLM_API_KEY'],'Content-Type':'application/json'})
with urllib.request.urlopen(r,timeout=15) as response:
    print(response.status)`;

  try {
    run([...compose, "config", "--quiet"]);
    const missingSecretCompose = [...compose];
    missingSecretCompose[missingSecretCompose.indexOf(envPath)] = missingEnvPath;
    const rejected = run([...missingSecretCompose, "run", "--rm", "--no-deps", "--pull", "never", "litellm"],
      { timeout: 30000, allowFailure: true });
    receipt.checks.missing_upstream_rejected = rejected.status !== 0;
    run([...compose, "up", "-d", "--pull", "never", "--wait", "--wait-timeout", "90",
      "litellm", "fake-upstream"], { timeout: 120000 });
    for (const name of ["default", "gateway"]) {
      const network = JSON.parse(run(["network", "inspect", `${project}_${name}`]).stdout)[0];
      assert.equal(network.Internal, true, `${name} must have no external egress`);
    }
    receipt.checks.gateway_health = api("/health/liveliness").status === 200;

    const backend = api("/key/generate", master, {
      models: ["economicon-embedding"], duration: "10m", max_budget: 1,
    });
    const processor = api("/key/generate", master, {
      models: ["economicon-chat", "economicon-chat-deepseek", "economicon-embedding"],
      duration: "10m", max_budget: 1,
    });
    assert.equal(backend.status, 200, "backend key generation failed");
    assert.equal(processor.status, 200, "processor key generation failed");
    assert.ok(backend.body.key && processor.body.key && backend.body.key !== processor.body.key,
      "independent virtual keys were not issued");
    sensitive.push(backend.body.key, processor.body.key);
    fs.appendFileSync(envPath, `BACKEND_LITELLM_API_KEY=${backend.body.key}\nLITELLM_API_KEY=${processor.body.key}\n`);
    const embedding = { model: "economicon-embedding", input: "synthetic question", dimensions: 1536 };
    const chat = { model: "economicon-chat", messages: [{ role: "user", content: "synthetic question" }] };
    receipt.checks.backend_embedding = api("/v1/embeddings", backend.body.key, embedding).status === 200;
    receipt.checks.backend_chat_denied = [401, 403].includes(api("/v1/chat/completions", backend.body.key, chat).status);
    receipt.checks.processor_chat = api("/v1/chat/completions", processor.body.key, chat).status === 200;
    receipt.checks.invalid_key_denied = [401, 403].includes(api("/v1/embeddings", "sk-invalid-synthetic", embedding).status);
    const backendProbe = run([...probeCompose, "run", "--rm", "--no-deps", "--pull", "never",
      "--entrypoint", "python", "-e", "PROBE_PATH=/embeddings",
      `-e`, `PROBE_BODY=${JSON.stringify(embedding)}`, "backend", "-c", probe], { timeout: 45000 });
    const processorProbe = run([...probeCompose, "run", "--rm", "--no-deps", "--pull", "never",
      "--entrypoint", "python", "-e", "PROBE_PATH=/chat/completions",
      `-e`, `PROBE_BODY=${JSON.stringify(chat)}`, "processor", "-c", probe], { timeout: 45000 });
    receipt.checks.backend_network_and_key = backendProbe.stdout.trim() === "200";
    receipt.checks.processor_network_and_key = processorProbe.stdout.trim() === "200";

    run([...compose, "up", "-d", "--pull", "never", "--force-recreate", "--wait",
      "--wait-timeout", "90", "litellm-db", "litellm"], { timeout: 120000 });
    const info = api("/key/info?key=" + encodeURIComponent(backend.body.key));
    receipt.checks.key_persisted = info.status === 200
      && info.body.info.models.join(",") === "economicon-embedding";
    receipt.checks.request_after_recreate = api("/v1/embeddings", backend.body.key, embedding).status === 200;
    const rows = run([...compose, "exec", "-T", "litellm-db", "psql", "-U", "litellm", "-d", "litellm",
      "-At", "-c", 'SELECT count(*) FROM "LiteLLM_SpendLogs";']);
    receipt.checks.spend_persisted = Number(rows.stdout.trim()) >= 2;
    assert.ok(Object.values(receipt.checks).every(Boolean), "Gateway acceptance checks failed");
  } finally {
    const down = run([...compose, "down", "--volumes", "--remove-orphans", "--timeout", "10"],
      { timeout: 60000, allowFailure: true });
    const leftovers = ["container", "volume", "network"].map((kind) =>
      run([kind, "ls", "-q", "--filter", `label=com.docker.compose.project=${project}`],
        { allowFailure: true }).stdout.trim());
    receipt.cleanup = down.status === 0 && leftovers.every((item) => item === "");
    fs.writeFileSync(path.join(directory, "receipt.json"), safe(JSON.stringify(receipt, null, 2)));
    fs.unlinkSync(envPath);
    fs.unlinkSync(missingEnvPath);
    fs.unlinkSync(overridePath);
    fs.unlinkSync(probeOverridePath);
    console.log(`JUP108_RECEIPT=${directory}`);
    assert.ok(receipt.cleanup, "Disposable Compose project was not fully removed");
  }
});

test("JUP-108 root Compose starts in mock mode without the AI profile", { skip: !mockEnabled }, async () => {
  const images = {
    backend: process.env.JUP108_MOCK_BACKEND_IMAGE,
    processor: process.env.JUP108_MOCK_PROCESSOR_IMAGE,
    frontend: process.env.JUP108_MOCK_FRONTEND_IMAGE,
    "azure-cost-api": process.env.JUP108_MOCK_AZURE_IMAGE,
  };
  assert.ok(Object.values(images).every(Boolean), "Set four JUP108_MOCK_*_IMAGE values for the isolated smoke");
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "jup108-mock-"));
  const project = `jup108-mock-${randomBytes(5).toString("hex")}`;
  const secret = randomBytes(24).toString("hex");
  const cookie = randomBytes(24).toString("hex");
  const authSecret = randomBytes(32).toString("hex");
  const safe = (value) => [secret, cookie, authSecret]
    .reduce((text, valueToHide) => text.replaceAll(valueToHide, "[REDACTED]"), String(value));
  const environment = Object.fromEntries(Object.entries(process.env).filter(([name]) =>
    !/^(LITELLM_|OPENROUTER_|COMPOSE_|AUTH_SECRET_KEY$|DATABASE_URL$|RABBITMQ_|VECTOR_DATABASE_URL$|POSTGRES_PASSWORD$|GRAFANA_ADMIN_PASSWORD$)/i.test(name)));
  environment.COMPOSE_DISABLE_ENV_FILE = "1";

  const listeners = await Promise.all(Array.from({ length: 11 }, () => new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server));
  })));
  const ports = listeners.map((server) => server.address().port);
  await Promise.all(listeners.map((server) => new Promise((resolve) => server.close(resolve))));
  const [api, processor, frontend, azure, cockroachSql, cockroachHttp, rabbit,
    rabbitAdmin, vector, prometheus, grafana] = ports;
  const envPath = path.join(directory, "synthetic.env");
  fs.writeFileSync(envPath, [
    "RUNTIME_ENVIRONMENT=development",
    "ALLOW_INSECURE_LOCAL_DATABASE=true",
    "DATABASE_URL=cockroachdb+psycopg://root@cockroachdb:26257/defaultdb?sslmode=disable",
    `RABBITMQ_DEFAULT_USER=jup108`,
    `RABBITMQ_DEFAULT_PASS=${secret}`,
    `RABBITMQ_ERLANG_COOKIE=${cookie}`,
    `RABBITMQ_URL=amqp://jup108:${secret}@rabbitmq:5672/`,
    `POSTGRES_PASSWORD=${secret}`,
    `VECTOR_DATABASE_URL=postgresql+psycopg://postgres:${secret}@postgres-pgvector:5432/embeddings`,
    `AUTH_SECRET_KEY=${authSecret}`,
    `GRAFANA_ADMIN_PASSWORD=${secret}`,
    "EMBEDDING_PROVIDER=mock",
    "EMBEDDING_DIMENSION=8",
    "LLM_PROVIDER=mock",
    "DEMO_SEED_ENABLED=false",
    `COCKROACH_SQL_PORT=${cockroachSql}`,
    `COCKROACH_HTTP_PORT=${cockroachHttp}`,
    `RABBITMQ_PORT=${rabbit}`,
    `RABBITMQ_MANAGEMENT_PORT=${rabbitAdmin}`,
    `PGVECTOR_PORT=${vector}`,
    `PROMETHEUS_PORT=${prometheus}`,
    `GRAFANA_PORT=${grafana}`,
  ].join("\n") + "\n");
  const overridePath = path.join(directory, "override.yaml");
  fs.writeFileSync(overridePath, `services:
  backend:
    image: ${images.backend}
    build: !reset null
    ports: !override ["127.0.0.1:${api}:8000"]
  processor:
    image: ${images.processor}
    build: !reset null
    ports: !override ["127.0.0.1:${processor}:8001"]
  frontend:
    image: ${images.frontend}
    build: !reset null
    ports: !override ["127.0.0.1:${frontend}:5173"]
  azure-cost-api:
    image: ${images["azure-cost-api"]}
    build: !reset null
    ports: !override ["127.0.0.1:${azure}:8002"]
`);
  const compose = ["compose", "--env-file", envPath, "-p", project, "-f",
    path.join(root, "docker-compose.yml"), "-f", overridePath];
  const receipt = { project, mode: "mock-no-openrouter", images, checks: {}, cleanup: false };
  function run(args, { timeout = 30000, allowFailure = false } = {}) {
    const result = spawnSync("docker", args, {
      cwd: root, env: environment, timeout, encoding: "utf8", windowsHide: true,
    });
    if (result.error || (!allowFailure && result.status !== 0)) {
      throw new Error(`Docker operation failed: ${result.error?.message ?? result.stderr.slice(-1600)}`);
    }
    return result;
  }
  try {
    const configured = run([...compose, "config", "--services"]).stdout.trim().split(/\r?\n/);
    receipt.checks.nine_services_without_ai = configured.length === 9
      && !configured.includes("litellm") && !configured.includes("litellm-db");
    assert.ok(receipt.checks.nine_services_without_ai);
    run([...compose, "up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "420"],
      { timeout: 450000 });
    const running = run([...compose, "ps", "--services", "--status", "running"]).stdout.trim().split(/\r?\n/);
    receipt.checks.all_services_running = running.length === 9;
    receipt.checks.no_gateway_container = run(["container", "ls", "-q", "--filter",
      `label=com.docker.compose.project=${project}`, "--filter", "label=com.docker.compose.service=litellm"])
      .stdout.trim() === "";
    const backendHealth = await fetch(`http://127.0.0.1:${api}/health`, { signal: AbortSignal.timeout(10000) });
    receipt.checks.backend_healthy = backendHealth.ok;
    assert.ok(Object.values(receipt.checks).every(Boolean), "Mock startup checks failed");
  } catch (error) {
    const logs = run([...compose, "logs", "--no-color", "--tail", "60", "backend"],
      { timeout: 30000, allowFailure: true });
    const diagnostic = safe(logs.stdout);
    receipt.backend_diagnostic = diagnostic.slice(0, 5000) + diagnostic.slice(-3000);
    throw error;
  } finally {
    const down = run([...compose, "down", "--volumes", "--remove-orphans", "--timeout", "10"],
      { timeout: 90000, allowFailure: true });
    const leftovers = ["container", "volume", "network"].map((kind) =>
      run([kind, "ls", "-q", "--filter", `label=com.docker.compose.project=${project}`],
        { allowFailure: true }).stdout.trim());
    receipt.cleanup = down.status === 0 && leftovers.every((item) => item === "");
    fs.writeFileSync(path.join(directory, "receipt.json"), JSON.stringify(receipt, null, 2));
    fs.unlinkSync(envPath);
    fs.unlinkSync(overridePath);
    console.log(`JUP108_MOCK_RECEIPT=${directory}`);
    assert.ok(receipt.cleanup, "Disposable mock project was not fully removed");
  }
});
