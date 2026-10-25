#!/usr/bin/env node
// Huella y datos declarados de la entrada del gateway que resuelve un alias de chat (JUP-133).
//
// Solo lectura: lee un fichero de configuración de LiteLLM y escribe en la salida estándar un JSON con el alias,
// el modelo, el proveedor y la cuantización que la configuración declara, y el sha256 de la entrada. Sirve para
// rellenar `model_identity` en `docs/validation/evaluation-runs.json` (`generation_model_id`, `generation_provider`,
// `generation_quantization`, `gateway_config_sha256`). Lo que sale es lo que la configuración DECLARA: no prueba
// qué modelo respondió en una ejecución concreta.
//
// Uso: node tools/gateway-config-hash.mjs [--config RUTA] [--alias ALIAS]
//   --config  por defecto infra/litellm/config.example.yaml
//   --alias   por defecto economicon-chat
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const DEFAULT_CONFIG = path.join(root, "infra", "litellm", "config.example.yaml");
const DEFAULT_ALIAS = "economicon-chat";

// JSON canónico: claves ordenadas a cualquier profundidad, para que el orden y el formato del YAML no cambien la huella.
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
  }
  return value;
}

export function describeAlias(configText, alias) {
  const config = parse(configText);
  if (config === null || typeof config !== "object" || !Array.isArray(config.model_list)) {
    throw new Error("la configuración no tiene una lista model_list");
  }
  const entries = config.model_list.filter((entry) => entry && entry.model_name === alias);
  if (entries.length === 0) throw new Error(`no hay ninguna entrada para el alias ${alias}`);
  if (entries.length > 1) throw new Error(`el alias ${alias} está repetido en model_list`);
  const entry = entries[0];
  const params = entry.litellm_params ?? {};
  // La referencia a la credencial no condiciona la generación: se excluye para que rotar la variable no parta series.
  const { api_key: _credential, ...generation } = params;
  const allowed = params.extra_body?.provider?.only;
  let provider = null;
  let quantization = null;
  if (allowed !== undefined) {
    if (!Array.isArray(allowed) || allowed.length !== 1 || typeof allowed[0] !== "string") {
      throw new Error(`el alias ${alias} debe fijar un solo proveedor en provider.only para declarar su identidad`);
    }
    const parts = allowed[0].split("/");
    if (parts.length > 2 || parts.some((part) => part === "")) {
      throw new Error(`el alias ${alias} debe declarar provider.only como proveedor o proveedor/cuantización, sin trozos vacíos ni de más`);
    }
    [provider, quantization = null] = parts;
  }
  const payload = canonical({ model_name: alias, litellm_params: generation });
  return {
    alias,
    generation_model_id: typeof params.model === "string" ? params.model : null,
    generation_provider: provider,
    generation_quantization: quantization,
    gateway_config_sha256: createHash("sha256").update(JSON.stringify(payload)).digest("hex"),
  };
}

function main(argv) {
  let config = DEFAULT_CONFIG;
  let alias = DEFAULT_ALIAS;
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if ((flag !== "--config" && flag !== "--alias") || !value) {
      process.stderr.write("uso: node tools/gateway-config-hash.mjs [--config RUTA] [--alias ALIAS]\n");
      return 2;
    }
    if (flag === "--config") config = path.resolve(value);
    else alias = value;
  }
  try {
    process.stdout.write(`${JSON.stringify(describeAlias(fs.readFileSync(config, "utf8"), alias), null, 2)}\n`);
    return 0;
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
