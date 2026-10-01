import { execFile } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const README_LINK = "README.md#con-docker-compose";
const MIN_AUTH_SECRET_LENGTH = 32;

export function parseDotenv(text) {
  const vars = new Map();
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim().replace(/^export\s+/, "");
    if (!line || line.startsWith("#")) continue;
    const equals = line.indexOf("=");
    if (equals <= 0) continue;
    const key = line.slice(0, equals).trim();
    let value = line.slice(equals + 1).trim();
    if (value.startsWith("'")) {
      const end = value.indexOf("'", 1);
      value = end > 0 ? value.slice(1, end) : value.slice(1);
    } else if (value.startsWith('"')) {
      let result = "";
      for (let index = 1; index < value.length; index += 1) {
        const char = value[index];
        if (char === "\\" && index + 1 < value.length) {
          const next = value[++index];
          result += next === "n" ? "\n" : next;
        } else if (char === '"') {
          break;
        } else {
          result += char;
        }
      }
      value = result;
    } else {
      // Compose only treats # as a comment when whitespace precedes it.
      value = value.replace(/\s+#.*$/, "").trim();
    }
    vars.set(key, value);
  }
  return vars;
}

export function readComposeContract(composeText) {
  const required = [...new Set([...composeText.matchAll(/\$\{([A-Z0-9_]+):\?[^}]*\}/g)].map((match) => match[1]))].sort();
  const ports = [];
  for (const service of Object.values(parse(composeText).services ?? {})) {
    for (const mapping of service.ports ?? []) {
      const match = /^(?:(\d+\.\d+\.\d+\.\d+):)?\$\{([A-Z0-9_]+):-(\d+)\}:\d+$/.exec(String(mapping));
      if (match) ports.push({ variable: match[2], default: match[3], host: match[1] ?? "0.0.0.0" });
    }
  }
  return { required, ports };
}

function resolveVariables(fileVars, env) {
  const vars = new Map(fileVars);
  for (const [key, value] of Object.entries(env)) {
    if (value !== undefined) vars.set(key, value);
  }
  return vars;
}

function urlCredentials(value) {
  try {
    const url = new URL(value);
    return { user: decodeURIComponent(url.username), password: decodeURIComponent(url.password) };
  } catch {
    return undefined;
  }
}

function checkConfiguration(vars, contract) {
  const errors = [];
  const present = (name) => (vars.get(name) ?? "") !== "";
  for (const name of contract.required) {
    if (!present(name)) errors.push(`Falta ${name}: docker-compose.yml la exige y no puede estar vacia.`);
  }

  const pairs = [
    ["RABBITMQ_URL", "RABBITMQ_DEFAULT_USER", "user"],
    ["RABBITMQ_URL", "RABBITMQ_DEFAULT_PASS", "password"],
    ["VECTOR_DATABASE_URL", "POSTGRES_PASSWORD", "password"],
  ];
  const parsed = new Map();
  for (const name of new Set(pairs.map(([url]) => url))) {
    if (!present(name)) continue;
    const credentials = urlCredentials(vars.get(name));
    if (credentials) parsed.set(name, credentials);
    else errors.push(`${name} no es una URL valida (las passwords con caracteres especiales van codificadas, p. ej. @ como %40).`);
  }
  for (const [urlName, name, part] of pairs) {
    const credentials = parsed.get(urlName);
    if (credentials && present(name) && credentials[part] !== vars.get(name)) {
      errors.push(`${urlName} y ${name} no coinciden (compara tras decodificar la URL; los caracteres especiales van codificados).`);
    }
  }

  if (present("AUTH_SECRET_KEY") && vars.get("AUTH_SECRET_KEY").length < MIN_AUTH_SECRET_LENGTH) {
    errors.push(`AUTH_SECRET_KEY debe tener al menos ${MIN_AUTH_SECRET_LENGTH} caracteres.`);
  }

  const runtime = vars.get("RUNTIME_ENVIRONMENT") || "production";
  const insecure = vars.get("ALLOW_INSECURE_LOCAL_DATABASE") || "false";
  if (!["development", "test"].includes(runtime) || insecure !== "true") {
    errors.push(
      "La CockroachDB local sin autenticacion exige RUNTIME_ENVIRONMENT=development o test y ALLOW_INSECURE_LOCAL_DATABASE=true, " +
        "solo tras confirmar que el proyecto, sus datos y sus puertos son locales y desechables.",
    );
  }
  return errors;
}

async function checkPorts(vars, contract, ownPorts, isPortFree) {
  const errors = [];
  const byPort = new Map();
  for (const { variable, default: fallback, host } of contract.ports) {
    const raw = vars.has(variable) && vars.get(variable) !== "" ? vars.get(variable) : fallback;
    const port = Number(raw);
    if (!/^\d+$/.test(raw) || port < 1 || port > 65535) {
      errors.push(`${variable} no es un puerto valido (1-65535).`);
      continue;
    }
    byPort.set(port, [...(byPort.get(port) ?? []), { variable, host }]);
  }
  for (const [port, users] of byPort) {
    if (users.length > 1) {
      errors.push(`${users.map(({ variable }) => variable).join(" y ")} usan el mismo puerto ${port}.`);
      continue;
    }
    if (ownPorts.has(port)) continue;
    const [{ variable, host }] = users;
    // A wildcard bind also collides with a loopback listener on some systems.
    const hosts = host === "0.0.0.0" ? ["0.0.0.0", "127.0.0.1"] : [host];
    for (const candidate of hosts) {
      if (!(await isPortFree(port, candidate))) {
        errors.push(`${variable}: el puerto ${port} esta ocupado o reservado en ${candidate}; liberalo o cambia ${variable} en .env.`);
        break;
      }
    }
  }
  return errors;
}

export function isPortFree(port, host) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.listen({ port, host, exclusive: true }, () => server.close(() => resolve(true)));
  });
}

export function composeProjectName(root, vars) {
  const explicit = vars.get("COMPOSE_PROJECT_NAME");
  const name = explicit || path.basename(path.resolve(root));
  return name.toLowerCase().replace(/[^a-z0-9_-]/g, "").replace(/^[^a-z0-9]+/, "");
}

function docker(args) {
  return new Promise((resolve, reject) => {
    execFile("docker", args, { encoding: "utf8", timeout: 20_000, windowsHide: true }, (error, stdout) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });
}

export const realDocker = {
  async containerPorts(project) {
    const output = await docker(["ps", "--filter", `label=com.docker.compose.project=${project}`, "--format", "{{.Ports}}"]);
    return [...output.matchAll(/:(\d+)->/g)].map((match) => Number(match[1]));
  },
  async volumes(project) {
    const output = await docker(["volume", "ls", "--filter", `label=com.docker.compose.project=${project}`, "--format", "{{.Name}}"]);
    return output.split(/\r?\n/).filter(Boolean);
  },
};

export async function runDoctor({ root, env = process.env, docker: dockerClient = realDocker, isPortFree: portCheck = isPortFree }) {
  const lines = [];
  const error = (text) => lines.push({ level: "error", text: `[ERROR] ${text}` });
  const info = (text) => lines.push({ level: "info", text: `[INFO] ${text}` });

  const envPath = path.join(root, ".env");
  const contract = readComposeContract(fs.readFileSync(path.join(root, "docker-compose.yml"), "utf8"));
  const hasEnvFile = fs.existsSync(envPath);
  if (!hasEnvFile) {
    error(`No existe .env junto a docker-compose.yml. Copia .env.example a .env y completa los secretos (ver ${README_LINK}).`);
  }
  const vars = resolveVariables(hasEnvFile ? parseDotenv(fs.readFileSync(envPath, "utf8")) : new Map(), env);
  if (hasEnvFile) checkConfiguration(vars, contract).forEach(error);

  const project = composeProjectName(root, vars);
  let ownPorts = new Set();
  let volumes;
  try {
    ownPorts = new Set(await dockerClient.containerPorts(project));
    volumes = await dockerClient.volumes(project);
  } catch {
    error("Docker no responde: arranca Docker Desktop (o el demonio de Docker) y vuelve a ejecutar el diagnostico.");
  }
  (await checkPorts(vars, contract, ownPorts, portCheck)).forEach(error);

  if (volumes) {
    if (volumes.length) {
      info(
        `Instalacion existente del proyecto "${project}" (${volumes.length} volumenes). ` +
          "Conserva los valores ya usados de RABBITMQ_ERLANG_COOKIE y GRAFANA_ADMIN_PASSWORD; `docker compose down -v` borra los datos.",
      );
    } else {
      info(`Instalacion nueva del proyecto "${project}": no hay volumenes previos.`);
    }
  }

  const failed = lines.some(({ level }) => level === "error");
  if (!failed) lines.push({ level: "info", text: "[OK] El entorno local esta listo para `docker compose up --build --wait`." });
  return { code: failed ? 1 : 0, lines };
}

async function main(argv) {
  const index = argv.indexOf("--project-directory");
  const root = index >= 0 ? path.resolve(argv[index + 1]) : path.dirname(path.dirname(fileURLToPath(import.meta.url)));
  const { code, lines } = await runDoctor({ root });
  for (const { level, text } of lines) (level === "error" ? console.error : console.log)(text);
  process.exitCode = code;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main(process.argv.slice(2));
}
