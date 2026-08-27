import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const compose = parse(fs.readFileSync(path.join(root, "docker-compose.yml"), "utf8"));

const applicationServices = ["azure-cost-api", "backend", "processor", "frontend"];
const infrastructureServices = ["cockroachdb", "rabbitmq", "postgres-pgvector"];

test("declares every MVP application and infrastructure service", () => {
  assert.deepEqual(
    Object.keys(compose.services).sort(),
    [...applicationServices, ...infrastructureServices].sort(),
  );
  assert.deepEqual(Object.keys(compose.volumes).sort(), ["cockroach-data", "pgvector-data"]);
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
  for (const serviceName of ["backend", "processor", "frontend"]) {
    for (const dependency of Object.values(compose.services[serviceName].depends_on)) {
      assert.equal(dependency.condition, "service_healthy");
    }
  }
});

test("binds infrastructure ports to loopback and permits isolated overrides", () => {
  const expectedVariables = {
    cockroachdb: ["COCKROACH_SQL_PORT", "COCKROACH_HTTP_PORT"],
    rabbitmq: ["RABBITMQ_PORT", "RABBITMQ_MANAGEMENT_PORT"],
    "postgres-pgvector": ["PGVECTOR_PORT"],
  };

  for (const [serviceName, variables] of Object.entries(expectedVariables)) {
    const ports = compose.services[serviceName].ports.map(String);
    assert.ok(ports.every((port) => port.startsWith("127.0.0.1:")));
    for (const variable of variables) {
      assert.ok(ports.some((port) => port.includes(`\${${variable}:-`)));
    }
  }
});

test("pins pnpm 9 and builds the frontend before running its preview server", () => {
  const source = fs.readFileSync(path.join(root, "apps", "frontend", "Dockerfile"), "utf8");
  assert.match(source, /corepack prepare pnpm@9\.0\.0 --activate/);
  assert.match(source, /pnpm install --frozen-lockfile/);
  assert.match(source, /pnpm --filter @finops\/frontend build/);
  assert.match(source, /cp vite\.config\.js \/tmp\/vite\.config\.js/);
  assert.match(source, /NODE_PATH=\/workspace\/apps\/frontend\/node_modules/);
  assert.match(source, /node .*node_modules\/vite\/bin\/vite\.js preview/);
});
