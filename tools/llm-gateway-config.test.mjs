import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const configText = fs.readFileSync(
  path.join(root, "infra", "litellm", "config.example.yaml"),
  "utf8",
);
const config = parse(configText);

test("maps exactly one approved OpenRouter upstream to each logical alias", () => {
  assert.deepEqual(
    config.model_list.map(({ model_name, litellm_params }) => [
      model_name,
      litellm_params.model,
    ]),
    [
      ["economicon-chat", "openrouter/z-ai/glm-5.2"],
      ["economicon-chat-deepseek", "openrouter/deepseek/deepseek-v4-pro"],
      ["economicon-embedding", "openrouter/openai/text-embedding-3-small"],
    ],
  );
  assert.equal(new Set(config.model_list.map(({ model_name }) => model_name)).size, 3);
});

test("keeps upstream credentials isolated from the gateway master key", () => {
  for (const { litellm_params } of config.model_list) {
    assert.equal(litellm_params.api_key, "os.environ/OPENROUTER_API_KEY");
  }
  assert.equal(config.general_settings.master_key, "os.environ/LITELLM_MASTER_KEY");
  assert.equal(config.litellm_settings.master_key, undefined);
  assert.doesNotMatch(configText, /sk-or-v1-[A-Za-z0-9_-]+/);
});

test("restricts only primary chat to DeepInfra through OpenRouter without relaxing privacy", () => {
  for (const { model_name, litellm_params } of config.model_list) {
    assert.deepEqual(litellm_params.extra_body.provider, {
      zdr: true,
      data_collection: "deny",
      allow_fallbacks: false,
      ...(model_name === "economicon-chat"
        ? { only: ["deepinfra/fp4"], require_parameters: true }
        : {}),
      ...(model_name === "economicon-embedding"
        ? { max_price: { prompt: 0.02 } }
        : {}),
    });
    assert.equal(litellm_params.api_base, undefined);
  }
});

test("disables optional high-effort reasoning only for baseline chat aliases", () => {
  const chatModels = config.model_list.filter(({ model_name }) =>
    model_name.startsWith("economicon-chat"),
  );
  const embedding = config.model_list.find(
    ({ model_name }) => model_name === "economicon-embedding",
  );

  assert.equal(chatModels.length, 2);
  for (const { litellm_params } of chatModels) {
    assert.deepEqual(litellm_params.extra_body.reasoning, { enabled: false });
  }
  assert.equal(embedding.litellm_params.extra_body.reasoning, undefined);
});

test("preserves the approved embedding dimensions and operational limits", () => {
  const embedding = config.model_list.find(
    ({ model_name }) => model_name === "economicon-embedding",
  );

  assert.equal(embedding.litellm_params.dimensions, 1536);
  assert.deepEqual(embedding.model_info, {
    input_cost_per_token: 2e-8,
    output_cost_per_token: 0,
  });
  assert.equal(config.litellm_settings.request_timeout, 30);
  assert.equal(config.litellm_settings.set_verbose, false);
  for (const item of config.model_list.slice(0, 2)) {
    assert.equal(item.litellm_params.max_tokens, 800);
    assert.equal(item.model_info, undefined);
  }
});

test("JUP-023 disables both gateway and router retries to bound processor attempts", () => {
  assert.equal(config.litellm_settings.num_retries, 0);
  assert.equal(config.router_settings?.num_retries, 0);
});

test("contains only public synthetic benchmark cases with unique identifiers", () => {
  const cases = fs
    .readFileSync(path.join(root, "fixtures", "llm-benchmark", "cases.jsonl"), "utf8")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));

  assert.equal(cases.length, 5);
  assert.equal(new Set(cases.map(({ id }) => id)).size, cases.length);
  for (const item of cases) {
    assert.equal(typeof item.prompt, "string");
    assert.ok(item.prompt.length > 0);
    assert.ok(item.expected_terms.length > 0);
  }
});
