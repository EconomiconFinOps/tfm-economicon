import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { describeAlias } from "./gateway-config-hash.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const tool = path.join(root, "tools", "gateway-config-hash.mjs");

const BASE = `
model_list:
  - model_name: economicon-chat
    litellm_params:
      model: openrouter/vendor/model-a
      api_key: os.environ/OPENROUTER_API_KEY
      max_tokens: 800
      extra_body:
        provider:
          zdr: true
          data_collection: deny
          allow_fallbacks: false
          only: [someprovider/fp8]
  - model_name: economicon-embedding
    litellm_params:
      model: openrouter/openai/text-embedding-3-small
      api_key: os.environ/OPENROUTER_API_KEY
`;

const describe = (text, alias = "economicon-chat") => describeAlias(text, alias);

test("hashes the alias entry as a sha256 in lowercase hexadecimal", () => {
  assert.match(describe(BASE).gateway_config_sha256, /^[0-9a-f]{64}$/);
});

test("is deterministic and independent of key order and formatting", () => {
  const reordered = `
model_list:
  - litellm_params:
      extra_body:
        provider:
          only:
            - someprovider/fp8
          allow_fallbacks: false
          data_collection: deny
          zdr: true
      max_tokens: 800
      model: openrouter/vendor/model-a
      api_key: os.environ/OPENROUTER_API_KEY
    model_name: economicon-chat
`;
  assert.equal(describe(reordered).gateway_config_sha256, describe(BASE).gateway_config_sha256);
});

test("changes when the model, the provider restriction or a generation parameter changes", () => {
  const reference = describe(BASE).gateway_config_sha256;
  for (const [from, to] of [
    ["openrouter/vendor/model-a", "openrouter/vendor/model-b"],
    ["only: [someprovider/fp8]", "only: [otherprovider/fp8]"],
    ["only: [someprovider/fp8]", "only: [someprovider/fp4]"],
    ["max_tokens: 800", "max_tokens: 900"],
    ["allow_fallbacks: false", "allow_fallbacks: true"],
  ]) {
    assert.notEqual(describe(BASE.replace(from, to)).gateway_config_sha256, reference, `${from} -> ${to}`);
  }
});

test("ignores other aliases, the credential reference and the order of the entries", () => {
  const reference = describe(BASE).gateway_config_sha256;
  assert.equal(describe(BASE.replace("text-embedding-3-small", "other-embedding")).gateway_config_sha256, reference);
  assert.equal(
    describe(BASE.replace("api_key: os.environ/OPENROUTER_API_KEY", "api_key: os.environ/OTHER_KEY")).gateway_config_sha256,
    reference,
  );
});

test("declares model, provider and quantization from the configuration, and null when it does not say", () => {
  const described = describe(BASE);
  assert.equal(described.generation_model_id, "openrouter/vendor/model-a");
  assert.equal(described.generation_provider, "someprovider");
  assert.equal(described.generation_quantization, "fp8");
  const free = describe(BASE.replace("          only: [someprovider/fp8]\n", ""));
  assert.equal(free.generation_provider, null);
  assert.equal(free.generation_quantization, null);
  const noQuantization = describe(BASE.replace("someprovider/fp8", "someprovider"));
  assert.equal(noQuantization.generation_provider, "someprovider");
  assert.equal(noQuantization.generation_quantization, null);
});

test("refuses an alias that is missing, repeated or has several allowed providers", () => {
  assert.throws(() => describe(BASE, "no-existe"), /no-existe/);
  assert.throws(() => describe(BASE + BASE.split("model_list:")[1].split("  - model_name: economicon-embedding")[0]), /repetido/);
  assert.throws(() => describe(BASE.replace("[someprovider/fp8]", "[a/fp8, b/fp8]")), /un solo proveedor/);
});

test("refuses a file that is not a gateway configuration", () => {
  assert.throws(() => describe("general_settings: {}"), /model_list/);
  assert.throws(() => describe("- 1\n- 2"), /model_list/);
});

test("command line prints JSON without secrets and fails with a readable error", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gwhash-"));
  const file = path.join(dir, "config.yaml");
  fs.writeFileSync(file, BASE);
  const ok = spawnSync(process.execPath, [tool, "--config", file, "--alias", "economicon-chat"], { encoding: "utf8" });
  assert.equal(ok.status, 0, ok.stderr);
  const parsed = JSON.parse(ok.stdout);
  assert.deepEqual(Object.keys(parsed), [
    "alias", "generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256",
  ]);
  assert.doesNotMatch(ok.stdout, /OPENROUTER_API_KEY/);
  const missing = spawnSync(process.execPath, [tool, "--config", file, "--alias", "nope"], { encoding: "utf8" });
  assert.equal(missing.status, 1);
  assert.match(missing.stderr, /nope/);
  const bad = spawnSync(process.execPath, [tool, "--config", path.join(dir, "no-existe.yaml")], { encoding: "utf8" });
  assert.equal(bad.status, 1);
  const usage = spawnSync(process.execPath, [tool, "--desconocido"], { encoding: "utf8" });
  assert.equal(usage.status, 2);
});

test("describes the alias of the repository example without hardcoding which model it serves", () => {
  const described = describeAlias(
    fs.readFileSync(path.join(root, "infra", "litellm", "config.example.yaml"), "utf8"),
    "economicon-chat",
  );
  assert.match(described.gateway_config_sha256, /^[0-9a-f]{64}$/);
  assert.equal(typeof described.generation_model_id, "string");
});
