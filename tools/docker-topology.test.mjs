import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

import { parse } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const compose = parse(fs.readFileSync(path.join(root, "docker-compose.yml"), "utf8"));

const applicationServices = ["azure-cost-api", "backend", "processor", "frontend"];
const infrastructureServices = ["cockroachdb", "rabbitmq", "postgres-pgvector"];
const monitoringServices = ["prometheus", "grafana"];

test("declares every MVP application, infrastructure and monitoring service", () => {
  assert.deepEqual(
    Object.keys(compose.services).sort(),
    [...applicationServices, ...infrastructureServices, ...monitoringServices].sort(),
  );
  assert.deepEqual(
    Object.keys(compose.volumes).sort(),
    ["cockroach-data", "pgvector-data", "prometheus-data", "grafana-data"].sort(),
  );
});

test("builds every application from a versioned Dockerfile", () => {
  for (const serviceName of applicationServices) {
    const service = compose.services[serviceName];
    assert.ok(service.build, `${serviceName} must define a build`);
    assert.ok(service.healthcheck, `${serviceName} must define a healthcheck`);
    assert.equal(service.init, true, `${serviceName} must use an init process`);
    assert.equal(service.read_only, true, `${serviceName} must use a read-only root filesystem`);
    assert.ok(service.tmpfs.includes("/tmp"), `${serviceName} must provide a writable /tmp`);
    assert.ok(
      service.security_opt.includes("no-new-privileges:true"),
      `${serviceName} must disable privilege escalation`,
    );

    const dockerfile = path.join(
      root,
      typeof service.build === "string"
        ? path.join(service.build, "Dockerfile")
        : service.build.dockerfile ?? path.join(service.build.context, "Dockerfile"),
    );
    const source = fs.readFileSync(dockerfile, "utf8");
    assert.match(source, /^FROM .+@sha256:[a-f0-9]{64}/m);
    assert.match(source, /^USER (?!root$).+/m);
    assert.match(source, /^HEALTHCHECK /m);
  }
});

test("pins infrastructure images by immutable digest and checks their health", () => {
  for (const serviceName of infrastructureServices) {
    const service = compose.services[serviceName];
    assert.match(service.image, /^[^\s]+:[^\s]+@sha256:[a-f0-9]{64}$/);
    assert.ok(service.healthcheck, `${serviceName} must define a healthcheck`);
  }
});

test("waits for healthy dependencies instead of container start only", () => {
  for (const serviceName of ["backend", "processor", "frontend", ...monitoringServices]) {
    for (const dependency of Object.values(compose.services[serviceName].depends_on)) {
      assert.equal(dependency.condition, "service_healthy");
    }
  }
});

test("binds infrastructure and monitoring ports to loopback and permits isolated overrides", () => {
  const expectedVariables = {
    cockroachdb: ["COCKROACH_SQL_PORT", "COCKROACH_HTTP_PORT"],
    rabbitmq: ["RABBITMQ_PORT", "RABBITMQ_MANAGEMENT_PORT"],
    "postgres-pgvector": ["PGVECTOR_PORT"],
    prometheus: ["PROMETHEUS_PORT"],
    grafana: ["GRAFANA_PORT"],
  };

  for (const [serviceName, variables] of Object.entries(expectedVariables)) {
    const ports = compose.services[serviceName].ports.map(String);
    assert.ok(ports.every((port) => port.startsWith("127.0.0.1:")));
    for (const variable of variables) {
      assert.ok(ports.some((port) => port.includes(`\${${variable}:-`)));
    }
  }
});

test("preserves monitoring configuration, persistence and health dependencies", () => {
  const expectedVolumes = {
    prometheus: [
      "./apps/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
      "prometheus-data:/prometheus",
    ],
    grafana: [
      "./apps/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro",
      "./apps/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro",
      "grafana-data:/var/lib/grafana",
    ],
  };

  for (const [serviceName, volumes] of Object.entries(expectedVolumes)) {
    assert.deepEqual([...compose.services[serviceName].volumes].sort(), [...volumes].sort());
    for (const volume of volumes.filter((volume) => volume.startsWith("./"))) {
      assert.ok(fs.existsSync(path.join(root, volume.split(":")[0])), `${serviceName} configuration must exist`);
    }
  }

  assert.ok(compose.services.prometheus.healthcheck);
  assert.deepEqual(Object.keys(compose.services.prometheus.depends_on).sort(), ["backend", "processor"]);
  assert.deepEqual(Object.keys(compose.services.grafana.depends_on), ["prometheus"]);
  assert.equal(compose.services.grafana.environment.GF_AUTH_ANONYMOUS_ENABLED, "false");
});

test("separates published application ports from fixed container ports", () => {
  const expected = {
    backend: ["API_HOST_PORT", "8000", "API_PORT"],
    processor: ["PROCESSOR_HOST_PORT", "8001", "PROCESSOR_PORT"],
    frontend: ["FRONTEND_HOST_PORT", "5173", null],
    "azure-cost-api": ["AZURE_COST_API_HOST_PORT", "8002", null],
  };

  for (const [serviceName, [hostVariable, containerPort, internalVariable]] of Object.entries(expected)) {
    const ports = compose.services[serviceName].ports.map(String);
    assert.ok(ports.some((port) => port.includes(`\${${hostVariable}:-`) && port.endsWith(`:${containerPort}`)));
    if (internalVariable) {
      assert.equal(String(compose.services[serviceName].environment[internalVariable]), containerPort);
    }
  }
});

test("pins pnpm 9 and builds the frontend before running its preview server", () => {
  const source = fs.readFileSync(path.join(root, "apps", "frontend", "Dockerfile"), "utf8");
  assert.match(source, /corepack prepare pnpm@9\.0\.0 --activate/);
  assert.match(source, /pnpm install --frozen-lockfile/);
  assert.match(source, /pnpm --filter @finops\/frontend build/);
  assert.ok(fs.existsSync(path.join(root, "apps", "frontend", "vite.config.ts")));
  assert.match(source, /cp vite\.config\.ts \/tmp\/vite\.config\.ts/);
  assert.match(source, /preview --config \/tmp\/vite\.config\.ts/);
  assert.match(source, /NODE_PATH=\/workspace\/apps\/frontend\/node_modules/);
  assert.match(source, /node .*node_modules\/vite\/bin\/vite\.js preview/);
});

// JUP-053 declarative checks. Actual context/image-layer and browser-bundle
// sentinel exclusion, scanner controls, and credential relocation require QA.
for (const [service, field, variable] of [
  ["backend", "AUTH_SECRET_KEY", "AUTH_SECRET_KEY"],
  ...["backend", "processor"].flatMap((service) =>
    ["DATABASE_URL", "RABBITMQ_URL", "VECTOR_DATABASE_URL"].map((field) => [service, field, field]),
  ),
  ["rabbitmq", "RABBITMQ_DEFAULT_USER", "RABBITMQ_DEFAULT_USER"],
  ["rabbitmq", "RABBITMQ_DEFAULT_PASS", "RABBITMQ_DEFAULT_PASS"],
  ["rabbitmq", "RABBITMQ_ERLANG_COOKIE", "RABBITMQ_ERLANG_COOKIE"],
  ["postgres-pgvector", "POSTGRES_PASSWORD", "POSTGRES_PASSWORD"],
  ["grafana", "GF_SECURITY_ADMIN_PASSWORD", "GRAFANA_ADMIN_PASSWORD"],
]) {
  test(`JUP-053 ${service}.${field} requires an external nonempty input`, () => {
    const value = compose.services[service].environment?.[field];
    assert.equal(typeof value, "string", "Required Compose input is absent");
    assert.ok(value.startsWith("${" + variable + ":?") && value.endsWith("}"),
      "Required Compose input must reject both unset and empty values");
  });
}

test("JUP-053 mock providers do not require a gateway key or receive upstream credentials", () => {
  const environment = compose.services.processor.environment;
  assert.equal(environment.LITELLM_API_KEY, "${LITELLM_API_KEY:-}");
  for (const name of ["backend", "processor", "frontend"]) {
    for (const field of ["OPENROUTER_API_KEY", "LITELLM_MASTER_KEY"]) {
      assert.equal(compose.services[name].environment?.[field], undefined);
      assert.equal(compose.services[name].build.args?.[field], undefined);
    }
  }
});

for (const serviceName of applicationServices) {
  test(`JUP-053 ${serviceName} context declares root and nested dotenv exclusions`, () => {
    const build = compose.services[serviceName].build;
    const context = typeof build === "string" ? build : build.context;
    const ignore = fs.readFileSync(path.join(root, context, ".dockerignore"), "utf8");
    const rules = ignore.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith("#"));
    assert.ok(rules.includes(".env") || rules.includes(".env*") || rules.includes("**/.env*"));
    assert.ok(rules.includes(".env.*") || rules.includes(".env*") || rules.includes("**/.env*"),
      "Root dotenv variants must be excluded");
    assert.ok(rules.includes("**/.env") || rules.includes("**/.env*"), "Nested dotenv files must be excluded");
    assert.ok(rules.includes("**/.env.*") || rules.includes("**/.env*"), "Nested dotenv variants must be excluded");
    assert.ok(!rules.some((rule) => rule.startsWith("!") && rule.includes(".env") && !rule.includes("example")),
      "A later inclusion must not restore secret dotenv variants");
  });
}

test("JUP-053 credential examples leave real secret fields empty", () => {
  const source = fs.readFileSync(path.join(root, ".env.example"), "utf8");
  const fields = new Map(source.split(/\r?\n/).filter((line) => /^[A-Z][A-Z0-9_]*=/.test(line))
    .map((line) => { const split = line.indexOf("="); return [line.slice(0, split), line.slice(split + 1).trim()]; }));
  for (const field of ["AUTH_SECRET_KEY", "DATABASE_URL", "RABBITMQ_URL", "VECTOR_DATABASE_URL",
    "POSTGRES_PASSWORD", "RABBITMQ_DEFAULT_PASS", "RABBITMQ_ERLANG_COOKIE", "DEMO_PASSWORD", "GRAFANA_ADMIN_PASSWORD",
    "OPENROUTER_API_KEY", "LITELLM_MASTER_KEY"]) {
    assert.ok(fields.has(field), `Missing inventory field: ${field}`);
    assert.ok(["", '""', "''"].includes(fields.get(field)), `Example field must be empty: ${field}`);
  }
});

test("JUP-053 login form initializes with the unchanged email and a blank password", () => {
  const source = fs.readFileSync(path.join(root, "apps/frontend/src/pages/LoginPage.tsx"), "utf8");
  const initializer = source.match(/useState\((\{[\s\S]*?\})\)/);
  assert.ok(initializer, "Locate the existing login form state initializer");
  const form = vm.runInNewContext("(" + initializer[1] + ")", {}, { timeout: 1000 });
  assert.equal(form.email, "operator@example.com");
  assert.equal(form.password, "");
});
