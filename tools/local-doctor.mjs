import { execFile } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const README_LINK = "README.md#con-docker-compose";
const MIN_AUTH_SECRET_LENGTH = 32;

const ESCAPED_DOLLAR = "\u0000";

function interpolate(value, lookup) {
  const expanded = value.replace(
    /\$\$|\$\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?)([-?])([^}]*))?\}|\$([A-Za-z_][A-Za-z0-9_]*)/g,
    (match, braced, colon, operator, argument, bare) => {
      if (match === "$$") return "$";
      const current = lookup(braced ?? bare);
      if (operator === "-") {
        const missing = colon ? !current : current === undefined;
        return missing ? argument : current;
      }
      return current ?? "";
    },
  );
  return expanded.replaceAll(ESCAPED_DOLLAR, "$");
}

// Compose interpolates unquoted and double-quoted values, looking up the process environment first.
export function parseDotenv(text, env = {}) {
  const vars = new Map();
  const lookup = (name) => (env[name] !== undefined ? env[name] : vars.get(name));
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
          result += next === "n" ? "\n" : next === "$" ? ESCAPED_DOLLAR : next;
        } else if (char === '"') {
          break;
        } else {
          result += char;
        }
      }
      value = interpolate(result, lookup);
    } else {
      // Compose only treats # as a comment when whitespace precedes it.
      value = interpolate(value.replace(/\s+#.*$/, "").trim(), lookup);
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

export function resolveVariables(fileVars, env) {
  const vars = new Map(fileVars);
  for (const [key, value] of Object.entries(env)) {
    if (value !== undefined) vars.set(key, value);
  }
  return vars;
}

// Mirrors apps/{backend,processor}/app/core/runtime_secrets.py and the backend settings validators.
export const BACKEND_RULES = {
  placeholders: new Set(["secret", "password", "changeme", "change-me", "replace-me", "replace-me-auth-secret"]),
  databaseQueryOptions: new Set(["sslmode", "connect_timeout", "application_name"]),
  databaseSchemes: new Set(["cockroachdb", "cockroachdb+psycopg", "cockroachdb+psycopg2"]),
  vectorSchemes: new Set(["postgresql", "postgresql+psycopg", "postgresql+psycopg2"]),
  brokerSchemes: new Set(["amqp", "amqps"]),
  insecureDatabaseHosts: new Set(["localhost", "127.0.0.1", "::1", "cockroachdb"]),
};
// Values the backend settings parse as true for boolean flags such as DEMO_SEED_ENABLED.
export const TRUE_VALUES = new Set(["1", "on", "t", "true", "y", "yes"]);

const DSN_RULES = {
  DATABASE_URL: { schemes: BACKEND_RULES.databaseSchemes, database: true },
  RABBITMQ_URL: { schemes: BACKEND_RULES.brokerSchemes, database: false },
  VECTOR_DATABASE_URL: { schemes: BACKEND_RULES.vectorSchemes, database: true },
};

// Python's unquote decodes valid %XX escapes and leaves the rest literal; decodeURIComponent throws instead.
function unquote(text) {
  return text.replace(/(?:%[0-9A-Fa-f]{2})+/g, (run) => {
    try {
      return decodeURIComponent(run);
    } catch {
      return run;
    }
  });
}

function parseDsn(name, value) {
  if (/\s/.test(value)) return { error: `${name} no puede contener espacios ni saltos de linea.` };
  // Parsers disagree on which raw @ ends the credentials, so only an encoded @ is safe.
  const authority = value.split("://")[1]?.split(/[/?#]/)[0] ?? "";
  if (authority.split("@").length > 2) {
    return { error: `${name} tiene una @ sin codificar en el usuario o la password (escribela como %40).` };
  }
  let url;
  let user;
  let password;
  try {
    url = new URL(value);
    user = unquote(url.username);
    password = unquote(url.password);
  } catch {
    return { error: `${name} no es una URL valida (los caracteres especiales de la password van codificados).` };
  }
  const rules = DSN_RULES[name];
  // SQLAlchemy keeps the driver name as written, while urlsplit lowercases the broker scheme.
  const written = value.slice(0, value.indexOf(":"));
  const scheme = rules.database ? written : written.toLowerCase();
  if (!rules.schemes.has(scheme)) return { error: `${name} debe usar uno de estos esquemas: ${[...rules.schemes].join(", ")}.` };
  // SQLAlchemy rejects "host:" with no port, while WHATWG URL and urlsplit accept it.
  if (rules.database && authority.endsWith(":")) return { error: `${name} tiene un ":" sin numero de puerto.` };
  if (!url.hostname || url.port === "0") return { error: `${name} necesita un host y un puerto distinto de 0.` };
  if (rules.database) {
    if (!url.pathname.slice(1)) return { error: `${name} debe indicar la base de datos en la ruta.` };
    const keys = [...url.searchParams.keys()];
    if (keys.some((key) => !BACKEND_RULES.databaseQueryOptions.has(key)) || new Set(keys).size !== keys.length) {
      return { error: `${name} solo admite estas opciones, una vez cada una: ${[...BACKEND_RULES.databaseQueryOptions].join(", ")}.` };
    }
  }
  return { user, password, host: url.hostname.replace(/^\[|\]$/g, ""), sslmode: url.searchParams.get("sslmode") };
}

function checkConfiguration(vars, contract) {
  const errors = [];
  const present = (name) => (vars.get(name) ?? "") !== "";
  for (const name of contract.required) {
    if (!present(name)) errors.push(`Falta ${name}: docker-compose.yml la exige y no puede estar vacia.`);
  }
  const runtime = vars.get("RUNTIME_ENVIRONMENT") || "production";
  const relaxed = runtime === "test";
  const placeholder = (value) => BACKEND_RULES.placeholders.has(value.toLowerCase());
  const insecureOptIn = ["development", "test"].includes(runtime) && (vars.get("ALLOW_INSECURE_LOCAL_DATABASE") || "false") === "true";
  if (!insecureOptIn) {
    errors.push(
      "La CockroachDB local sin autenticacion exige RUNTIME_ENVIRONMENT=development o test y ALLOW_INSECURE_LOCAL_DATABASE=true, " +
        "solo tras confirmar que el proyecto, sus datos y sus puertos son locales y desechables.",
    );
  }

  const dsns = new Map();
  for (const name of Object.keys(DSN_RULES)) {
    if (!present(name)) continue;
    const parsed = parseDsn(name, vars.get(name));
    if (parsed.error) {
      errors.push(parsed.error);
      continue;
    }
    dsns.set(name, parsed);
    if (name === "DATABASE_URL") {
      const insecure = !parsed.password.trim() || parsed.sslmode === "disable";
      if (insecure && insecureOptIn && !BACKEND_RULES.insecureDatabaseHosts.has(parsed.host)) {
        errors.push(`DATABASE_URL sin password o con sslmode=disable solo se admite contra ${[...BACKEND_RULES.insecureDatabaseHosts].join(", ")}.`);
      }
    } else if (!parsed.user.trim() || !parsed.password.trim()) {
      errors.push(`${name} necesita usuario y password.`);
    }
    if (!relaxed && placeholder(parsed.password)) {
      errors.push(`${name} usa una password de ejemplo; el backend la rechaza.`);
    }
  }
  if (!relaxed && dsns.get("RABBITMQ_URL")?.user === "guest" && dsns.get("RABBITMQ_URL")?.password === "guest") {
    errors.push("RABBITMQ_URL usa las credenciales por defecto guest/guest; el backend las rechaza.");
  }
  if (!relaxed && dsns.get("VECTOR_DATABASE_URL")?.password === "postgres") {
    errors.push("VECTOR_DATABASE_URL usa la password por defecto postgres; el backend la rechaza.");
  }

  const pairs = [
    ["RABBITMQ_URL", "RABBITMQ_DEFAULT_USER", "user"],
    ["RABBITMQ_URL", "RABBITMQ_DEFAULT_PASS", "password"],
    ["VECTOR_DATABASE_URL", "POSTGRES_PASSWORD", "password"],
  ];
  for (const [urlName, name, part] of pairs) {
    const credentials = dsns.get(urlName);
    if (credentials && present(name) && credentials[part] !== vars.get(name)) {
      errors.push(`${urlName} y ${name} no coinciden (compara tras decodificar la URL; los caracteres especiales van codificados).`);
    }
  }

  const singleLine = (value) => value.trim() !== "" && !/[\r\n]/.test(value);
  if (present("AUTH_SECRET_KEY")) {
    const key = vars.get("AUTH_SECRET_KEY");
    if (!singleLine(key)) {
      errors.push("AUTH_SECRET_KEY no puede estar en blanco ni ocupar varias lineas.");
    } else if (!relaxed && ([...key].length < MIN_AUTH_SECRET_LENGTH || placeholder(key))) {
      errors.push(`AUTH_SECRET_KEY debe tener al menos ${MIN_AUTH_SECRET_LENGTH} caracteres y no ser un valor de ejemplo.`);
    }
  }
  if (TRUE_VALUES.has((vars.get("DEMO_SEED_ENABLED") ?? "").trim().toLowerCase())) {
    const demo = vars.get("DEMO_PASSWORD") ?? "";
    if (!singleLine(demo) || (!relaxed && placeholder(demo))) {
      errors.push("DEMO_PASSWORD es obligatoria con DEMO_SEED_ENABLED activo: en una linea, no en blanco y no un valor de ejemplo.");
    }
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
    // A wildcard bind also collides with loopback and dual-stack IPv6 listeners on some systems.
    const hosts = host === "0.0.0.0" ? ["0.0.0.0", "127.0.0.1", "::"] : [host];
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
    // Without IPv6 on the host, the IPv6 probe cannot be held by anyone.
    server.once("error", (error) => resolve(error.code === "EAFNOSUPPORT" || error.code === "EADDRNOTAVAIL"));
    server.listen({ port, host, exclusive: true, ipv6Only: false }, () => server.close(() => resolve(true)));
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
  const vars = resolveVariables(hasEnvFile ? parseDotenv(fs.readFileSync(envPath, "utf8"), env) : new Map(), env);
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
          "Los volumenes guardan las credenciales del primer arranque: conserva los valores ya usados de RABBITMQ_DEFAULT_USER, " +
          "RABBITMQ_DEFAULT_PASS, POSTGRES_PASSWORD y GRAFANA_ADMIN_PASSWORD, porque cambiarlos en .env no cambia los del servicio " +
          "(RABBITMQ_ERLANG_COOKIE si prevalece). `docker compose down -v` borra los datos.",
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
