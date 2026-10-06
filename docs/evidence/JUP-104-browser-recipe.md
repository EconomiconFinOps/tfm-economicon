# Receta de navegador JUP-104 — recorrido del operador

Guion que conduce el recorrido de [JUP-104](https://trello.com/c/lVvZa7P5/96-jup-104) en un
navegador real, siguiendo las decisiones 4 y 5 del
[`design.md`](../../openspec/changes/archive/2026-10-06-jup-104-e2e-validation/design.md). Se ejecuta **fuera del
repositorio**: Playwright no es dependencia del proyecto. Resultados y capturas se guardan también
fuera. Los resultados de su ejecución están en [JUP-104-validation.md](JUP-104-validation.md).

## Qué hace

Entra por el formulario de acceso con la cuenta de demostración, recorre el selector de ámbito, los
costes, las pantallas, la ingesta de un documento, el asistente, la recarga del historial y el cierre
de sesión, y comprueba además por consulta de solo lectura que el trabajo queda completado y que el
documento, sus fragmentos y sus vectores constan en el ámbito correcto.

- **No intercepta ni responde peticiones** (no usa `page.route`): solo observa las respuestas que la
  propia interfaz recibe del backend.
- **No escribe la sesión** en el almacenamiento: la crea la aplicación al enviar el formulario.
- **Falla** si hay un error de página, un error de CORS en la consola o un paso que no se cumple, y
  entonces los pasos que dependen de él quedan como `not_run`.
- **Modifica datos** (pasos 5.1 y 6.x): ingiere un documento en Growth Ops y crea dos conversaciones
  con mensajes. Úsese solo en un stack desechable, con volúmenes nuevos y `local:smoke` ejecutado una
  vez antes. Repetirlo sobre el mismo stack añade documentos y conversaciones.

## Requisitos

- El stack de Docker Compose levantado y sano, en el proyecto que indique `COMPOSE_PROJECT_NAME`
  (ver la sección «Stack local aislado» de la evidencia), con `DEMO_SEED_ENABLED=true` y la cuenta
  `operator@example.com`.
- Node.js 22 o superior. Verificado con Node `v24.15.0`, Playwright `1.63.0` y Chromium
  `153.0.8010.12` (revisión `1243` de Playwright).
- Docker en el `PATH`: el guion ejecuta `docker compose exec` y `docker compose logs`.

## Preparación

Fuera del repositorio, en una carpeta propia:

```powershell
New-Item -ItemType Directory C:\ruta\fuera\del\repo\jup104-e2e-runner
Set-Location C:\ruta\fuera\del\repo\jup104-e2e-runner
npm init -y
npm install playwright@1.63.0
npx playwright install chromium
```

Guardar el guion de abajo como `journey.cjs` en esa carpeta.

## Ejecución

La contraseña se pasa por entorno y no se imprime. No escribirla en el guion ni en un historial de
consola compartido.

```powershell
$env:COMPOSE_PROJECT_NAME = "jup104-e2e"
$env:E2E_REPO_ROOT = "C:\ruta\al\repositorio"            # raiz del clon, en el commit validado
$env:E2E_OUT = "C:\ruta\fuera\del\repo\salida-jup104"    # resultados y capturas
$env:E2E_PASSWORD = "<valor de DEMO_PASSWORD>"           # en la evidencia consta solo el nombre
node journey.cjs
```

- `E2E_PHASE=read` ejecuta solo los pasos que no modifican datos (`0.1` y el grupo 4): sirve para
  ensayar selectores sin ensuciar el stack.
- `E2E_BASE_URL` (por defecto `http://localhost:5173`) y `E2E_API_URL` (`http://localhost:8000`).
- Código de salida `0` si todos los pasos pasan, sin errores de página ni de CORS; `1` si no.
- Salida: `results.json` (pasos, observaciones, navegador, commit), capturas numeradas y
  `processor-log.txt`.

## Límites del guion

- Playwright lanza Chromium con sus opciones estándar de automatización (el paso `0.1` las lista a
  partir de la línea de comandos real del proceso, entre ellas `--no-sandbox` y
  `--disable-popup-blocking`). Ninguna relaja CORS ni la política de mismo origen, y el paso falla si
  aparece `--disable-web-security`, `--allow-running-insecure-content`,
  `--disable-site-isolation-trials` o `--ignore-certificate-errors`. La pasada manual en un navegador
  habitual (tarea 7.1) cubre lo que este navegador de pruebas no puede.
- Una petición `GET /billing/summary` con `net::ERR_ABORTED` es normal: la aplicación cancela la
  consulta en curso cuando cambia la selección de periodo o de agrupación.
- La lectura de la línea de comandos del navegador usa PowerShell en Windows y `ps` en otros
  sistemas; en un sistema sin ninguno de los dos el paso `0.1` falla y hay que acreditarlo de otra
  forma.

## Guion

```javascript
// JUP-104 -- recorrido del operador en un navegador real.
// Se ejecuta FUERA del repositorio. No intercepta ni responde peticiones (sin page.route), no escribe la
// sesion en el almacenamiento (entra por el formulario) y no relaja ninguna proteccion del navegador.
// Las consultas a CockroachDB y pgvector son de solo lectura (docker compose exec).
//
// Variables de entorno:
//   E2E_PASSWORD      contrasena del operador de demostracion (obligatoria; nunca se imprime)
//   E2E_REPO_ROOT     raiz del repositorio (obligatoria): de ella salen el documento y la pregunta
//   E2E_OUT           carpeta de salida fuera del repositorio (obligatoria)
//   E2E_BASE_URL      por defecto http://localhost:5173
//   E2E_API_URL       por defecto http://localhost:8000
//   COMPOSE_PROJECT_NAME  proyecto de Compose del stack validado (heredado por docker compose)
//   E2E_PHASE         "read" ejecuta solo los pasos que no modifican datos (0.1 y grupo 4); por defecto, todos
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execFileSync, spawnSync } = require("child_process");

const BASE = process.env.E2E_BASE_URL || "http://localhost:5173";
const API = process.env.E2E_API_URL || "http://localhost:8000";
const ROOT = process.env.E2E_REPO_ROOT;
const OUT = process.env.E2E_OUT;
const PASSWORD = process.env.E2E_PASSWORD;
for (const [name, value] of [["E2E_PASSWORD", PASSWORD], ["E2E_REPO_ROOT", ROOT], ["E2E_OUT", OUT]]) {
  if (!value) { console.error(`Falta ${name}`); process.exit(2); }
}
fs.mkdirSync(OUT, { recursive: true });

const PERIOD = { start: "2024-06-01", end: "2024-06-21" };
const DOC_PATH = "docs/assistant-corpus/finops/azure-finops-mvp.md";
const DOC = fs.readFileSync(path.join(ROOT, DOC_PATH), "utf8");
const QUESTIONS = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/validation/JUP-069-questions.json"), "utf8"));
const QUESTION = QUESTIONS.cases.find((c) => c.id === "JUP-069-004").question;
const DOC_SHA = crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT, DOC_PATH))).digest("hex");
const FORBIDDEN_FLAGS = ["disable-web-security", "allow-running-insecure-content", "disable-site-isolation-trials", "ignore-certificate-errors"];

const results = { started: new Date().toISOString(), base: BASE, api: API, steps: [], pageErrors: [], consoleErrors: [], failedRequests: [], notes: {} };
const state = {};
const failed = new Set();
let shot = 0;

function sh(cmd, args, input) {
  const r = spawnSync(cmd, args, { encoding: "utf8", input, timeout: 60000, windowsHide: true });
  if (r.status !== 0) throw new Error(`${cmd} ${args.slice(0, 4).join(" ")} -> ${r.status}: ${(r.stderr || "").slice(0, 300)}`);
  return r.stdout;
}
const compose = (...a) => sh("docker", ["compose", ...a]);
const cockroach = (sql) => compose("exec", "-T", "cockroachdb", "/cockroach/cockroach", "sql", "--insecure", "--format=csv", "--database=defaultdb", "-e", sql).trim();
const pg = (sql) => compose("exec", "-T", "postgres-pgvector", "psql", "-U", "postgres", "-d", "embeddings", "-tA", "-F", "|", "-c", sql).trim();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const READ_ONLY = ["0.1", "4.1", "4.2", "4.3", "4.4"];
async function step(id, title, needs, fn) {
  if (process.env.E2E_PHASE === "read" && !READ_ONLY.includes(id)) return;
  const rec = { id, title, status: "not_run", observations: [] };
  results.steps.push(rec);
  const blocked = needs.filter((n) => failed.has(n));
  if (blocked.length) { rec.reason = `depende de ${blocked.join(", ")}, que no se acredito`; failed.add(id); return; }
  const obs = (text) => { rec.observations.push(text); console.log(`  . ${text}`); };
  console.log(`[${id}] ${title}`);
  try {
    await fn(obs);
    rec.status = "pass";
  } catch (error) {
    rec.status = "fail"; rec.reason = String(error.message || error).slice(0, 600); failed.add(id);
    console.log(`  ! FALLO: ${rec.reason}`);
    try { await state.page.screenshot({ path: path.join(OUT, `${String(++shot).padStart(2, "0")}-${id}-FALLO.png`), fullPage: true }); } catch {}
  }
}
async function snap(name) { await state.page.screenshot({ path: path.join(OUT, `${String(++shot).padStart(2, "0")}-${name}.png`), fullPage: true }); }
const must = (cond, msg) => { if (!cond) throw new Error(msg); };

// Respuestas que la propia interfaz recibe del backend (solo se observan, no se tocan).
const seen = [];
function watch(page) {
  page.on("pageerror", (e) => results.pageErrors.push(String(e).slice(0, 300)));
  page.on("console", (m) => { if (m.type() === "error") results.consoleErrors.push(m.text().slice(0, 300)); });
  page.on("requestfailed", (r) => results.failedRequests.push(`${r.method()} ${new URL(r.url()).pathname} ${r.failure()?.errorText}`));
  page.on("response", async (r) => {
    const u = new URL(r.url());
    if (!r.url().startsWith(API)) return;
    const entry = { t: Date.now(), method: r.request().method(), path: u.pathname, search: u.search, status: r.status(), tenant: r.request().headers()["x-tenant-id"] || null };
    try { const ct = r.headers()["content-type"] || ""; if (ct.includes("json") && u.pathname !== "/auth/login") entry.body = await r.json(); } catch {}
    seen.push(entry);
  });
}
const apiSince = (t, filter = () => true) => seen.filter((e) => e.t >= t && filter(e));
async function waitApi(pred, ms = 15000) {
  const end = Date.now() + ms;
  for (;;) { const hit = seen.find(pred); if (hit) return hit; if (Date.now() > end) throw new Error("no llego la respuesta esperada del backend"); await sleep(150); }
}

async function selectTenant(page, name) {
  const sel = page.getByLabel("Ambito de cliente");
  await sel.selectOption({ label: name });
  must((await sel.locator("option:checked").innerText()) === name, `el selector no quedo en ${name}`);
}
async function setPeriod(page) {
  await page.getByLabel("Inicio (UTC)").fill(PERIOD.start);
  await page.getByLabel("Fin exclusivo (UTC)").fill(PERIOD.end);
}
async function costView(page) {
  const t0 = Date.now();
  const empty = page.getByText("Sin datos de costes para este periodo.");
  const total = page.getByRole("heading", { name: "Coste total del periodo" });
  await Promise.race([empty.waitFor({ timeout: 20000 }), total.waitFor({ timeout: 20000 })]);
  if (await empty.count()) return { empty: true, t0 };
  const totals = await page.locator("section[aria-label='Costes reales de Azure'] p.font-bold").allInnerTexts();
  const rows = await page.locator("section[aria-label='Costes reales de Azure'] tbody tr").count();
  return { empty: false, totals, rows, t0 };
}
// Espera a que no llegue ninguna respuesta del backend durante ms: un refetch en segundo plano de la pantalla anterior
// (TanStack Query muestra datos en cache y refresca al montar) no debe atribuirse a la pantalla siguiente.
async function quiet(ms = 2000) {
  for (;;) { const last = seen.length ? seen[seen.length - 1].t : 0; if (Date.now() - last >= ms) return; await sleep(200); }
}
async function nav(page, label) { await page.getByRole("link", { name: label, exact: true }).click(); }
async function demoMarks(page) {
  return page.evaluate(() => ({
    h2: [...document.querySelectorAll("main h2, h2")].map((e) => e.textContent.trim()).slice(0, 2),
    demoRegions: [...document.querySelectorAll("[aria-label]")].filter((e) => /demostraci/i.test(e.getAttribute("aria-label"))).length,
    demoText: (document.body.innerText.match(/demostraci[oó]n|datos de prueba/gi) || []).length
  }));
}
async function askAssistant(page, question) {
  await nav(page, "Assistant");
  await page.getByPlaceholder("New conversation title").waitFor();
  const tNew = Date.now();
  await page.getByRole("button", { name: "New", exact: true }).click();
  const created = await waitApi((e) => e.t >= tNew && e.method === "POST" && e.path === "/assistant/conversations" && e.body, 15000);
  const box = page.getByPlaceholder("Ask the assistant about the ingested tenant documents.");
  await box.waitFor();
  const t0 = Date.now();
  await box.fill(question);
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const reply = await waitApi((e) => e.t >= t0 && e.method === "POST" && /\/messages$/.test(e.path), 30000);
  must(reply.status === 201, `POST mensaje respondio ${reply.status}`);
  const text = reply.body.assistant_message.content;
  await page.locator("article", { hasText: "assistant" }).last().waitFor();
  return { reply, text, convId: reply.path.split("/")[3], createdId: created.body.id };
}
// El chunker del processor normaliza los espacios ("a b<salto>c" -> "a b c"): se compara con esa misma normalizacion.
const norm = (t) => t.replace(/\s+/g, " ").trim();
const NORM_DOC = norm(DOC);
function fragments(text) {
  // La plantilla del backend: "- <origen>: <primeros 140 caracteres del fragmento>"
  return text.split("\n").filter((l) => l.startsWith("- ")).map((l) => l.replace(/^- [^:]+: /, ""));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "es-ES", timezoneId: "UTC" });
  const page = await context.newPage();
  state.page = page;
  watch(page);
  results.browser = { name: "chromium", version: browser.version(), playwright: require("playwright/package.json").version };
  results.commit = execFileSync("git", ["-C", ROOT, "rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim();

  await step("0.1", "Chromium sin opciones que relajen la seguridad", [], async (obs) => {
    // Linea de comandos REAL del proceso principal del navegador (el que no lleva --type=).
    const cmd = process.platform === "win32"
      ? sh("powershell", ["-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"Name LIKE 'chrome%'\" | Where-Object { $_.CommandLine -match 'ms-playwright' -and $_.CommandLine -notmatch '--type=' } | ForEach-Object { $_.CommandLine }"])
      : sh("sh", ["-c", "ps -eo args | grep -E 'ms-playwright.*(chrome|chromium)' | grep -v -e '--type=' -e grep"]);
    const line = cmd.replace(/\s+/g, " ").trim();
    must(line.length > 0, "no se pudo leer la linea de comandos del navegador");
    const bad = FORBIDDEN_FLAGS.filter((f) => line.includes(f));
    results.notes.chromiumCommandLineFlags = (line.match(/--[a-z0-9-]+(=[^ ]*)?/gi) || []).map((f) => f.replace(/(--user-data-dir|--remote-debugging-pipe).*/, "$1")).filter((f) => !/user-data-dir/.test(f));
    must(bad.length === 0, `opciones prohibidas en la linea de comandos: ${bad.join(", ")}`);
    obs(`version ${browser.version()}; linea de comandos leida del proceso, ${results.notes.chromiumCommandLineFlags.length} opciones, ninguna de: ${FORBIDDEN_FLAGS.join(", ")}`);
    obs(`opciones: ${results.notes.chromiumCommandLineFlags.join(" ")}`);
  });

  await step("4.1", "Acceso por el formulario", [], async (obs) => {
    await page.goto(`${BASE}/login`);
    await page.getByRole("heading", { name: "Access the tenant control tower" }).waitFor();
    obs(`correo precargado: ${await page.locator("#login-email").inputValue()}`);
    await page.locator("#login-password").fill(PASSWORD);
    const t0 = Date.now();
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.getByLabel("Ambito de cliente").waitFor({ timeout: 20000 });
    const login = apiSince(t0, (e) => e.path === "/auth/login")[0];
    must(login && login.status === 200, `login respondio ${login && login.status}`);
    const hasSession = await page.evaluate(() => Boolean(localStorage.getItem("finops.session")));
    must(hasSession, "la aplicacion no creo la sesion");
    obs("POST /auth/login 200 desde el navegador; sesion creada por la aplicacion (solo se comprueba que existe)");
    obs(`respuestas de /me y /tenants: ${apiSince(t0).filter((e) => ["/me", "/tenants"].includes(e.path)).map((e) => `${e.path} ${e.status}`).join(", ")}`);
    obs(`ambitos del selector: ${(await page.getByLabel("Ambito de cliente").locator("option").allInnerTexts()).join(" | ")}`);
    obs(`identidad en la cabecera: ${(await page.locator("header p.text-xs").first().innerText())}`);
    await snap("acceso");
  });

  await step("4.2", "Costes de Core Finance, 2024-06-01 a 2024-06-21", ["4.1"], async (obs) => {
    await selectTenant(page, "Core Finance");
    await page.getByRole("link", { name: "Coste Global", exact: true }).click();
    await setPeriod(page);
    const v = await costView(page);
    must(!v.empty, "Core Finance no muestra costes");
    state.coreTotals = v.totals;
    obs(`totales en pantalla: ${v.totals.join(" ; ")}; filas del desglose: ${v.rows}`);
    const api = await waitApi((e) => e.path === "/billing/summary" && e.search.includes(PERIOD.start) && e.search.includes(PERIOD.end) && e.tenant === "tenant-core" && e.body);
    const apiTotals = api.body.totals.map((t) => `${t.cost} ${t.currency}`);
    obs(`GET /billing/summary${api.search} (X-Tenant-Id tenant-core) ${api.status}: totals ${apiTotals.join(" ; ")}, data_status ${api.body.data_status}, grupos ${api.body.groups.length}, registros sin dimension ${api.body.missing_dimension_count}, sin fecha excluidos ${api.body.excluded_undated_count}`);
    const partial = await page.getByText(/Datos parciales/).count();
    obs(`aviso 'Datos parciales' visible: ${partial ? "si" : "no"}`);
    must(JSON.stringify(apiTotals) === JSON.stringify(v.totals), "el total de pantalla no coincide con el de la respuesta");
    obs(`ahorro potencial: ${(await page.getByText(/Ahorro potencial/).first().innerText())}`);
    await snap("costes-core");
    // El agrupado por defecto (Servicio) deja los 38 registros sin dimension; se anota tambien un reparto con sentido.
    const t1 = Date.now();
    await page.getByLabel("Agrupar por").selectOption("resource_group");
    const rg = await waitApi((e) => e.t >= t1 && e.path === "/billing/summary" && e.search.includes("group_by=resource_group") && e.body, 20000);
    await page.locator("section[aria-label='Costes reales de Azure'] tbody tr").first().waitFor();
    const rgRows = await page.locator("section[aria-label='Costes reales de Azure'] tbody tr").count();
    obs(`agrupado por Grupo de recursos: ${rgRows} filas en pantalla, grupos en la respuesta ${rg.body.groups.length}, data_status ${rg.body.data_status}, totals ${rg.body.totals.map((t) => `${t.cost} ${t.currency}`).join(" ; ")}, registros sin dimension ${rg.body.missing_dimension_count}`);
    await snap("costes-core-grupo-recursos");
  });

  await step("4.3", "Cambio de ambito a Growth Ops y vuelta", ["4.2"], async (obs) => {
    await selectTenant(page, "Growth Ops");
    await setPeriod(page);
    const g = await costView(page);
    must(g.empty, "Growth Ops muestra costes");
    obs("Growth Ops: la seccion de costes reales muestra 'Sin datos de costes para este periodo.'");
    obs(`el periodo sigue en ${await page.getByLabel("Inicio (UTC)").inputValue()} a ${await page.getByLabel("Fin exclusivo (UTC)").inputValue()}`);
    await snap("costes-growth");
    await selectTenant(page, "Core Finance");
    await setPeriod(page);
    const c = await costView(page);
    must(!c.empty && JSON.stringify(c.totals) === JSON.stringify(state.coreTotals), "Core Finance no recupera los mismos valores");
    obs(`Core Finance recupera ${c.totals.join(" ; ")}`);
  });

  await step("4.4", "Pantallas: origen de los datos", ["4.1"], async (obs) => {
    const screens = [["Coste Detallado", "/operational"], ["Corte Global", "/cuts"], ["Anomalías", "/anomalies"], ["Recomendaciones", "/recommendations"], ["Overview", "/overview-legacy"], ["Coste Global", "/"]];
    results.notes.screens = [];
    for (const [label, route] of screens) {
      await quiet();
      const t0 = Date.now();
      await nav(page, label);
      await page.waitForURL(`**${route}`);
      await sleep(2500);
      const calls = [...new Set(apiSince(t0).map((e) => `${e.method} ${e.path} ${e.status}`))];
      const marks = await demoMarks(page);
      results.notes.screens.push({ label, route, apiCalls: calls, ...marks });
      obs(`${route} "${marks.h2.join(" / ")}": peticiones al backend en esta visita [${calls.join(", ") || "ninguna"}]; regiones aria-label con 'demostracion': ${marks.demoRegions}; apariciones del rotulo de demostracion/datos de prueba: ${marks.demoText}`);
      await snap(`pantalla-${route.replace(/\W+/g, "") || "raiz"}`);
    }
  });

  await step("5.1", "Ingesta desde la interfaz (Growth Ops)", ["4.1"], async (obs) => {
    await selectTenant(page, "Growth Ops");
    await nav(page, "Ingestions");
    await page.locator("#ingest-source").fill("assistant-corpus");
    await page.locator("#ingest-artifact-uri").fill(DOC_PATH);
    await page.locator("#ingest-text-content").fill(DOC);
    obs(`documento ${DOC_PATH}: ${Buffer.byteLength(DOC)} bytes, SHA-256 ${DOC_SHA}`);
    state.ingestStart = new Date().toISOString();
    const t0 = Date.now();
    await page.getByRole("button", { name: "Queue ingestion" }).click();
    await page.getByText("Job accepted").waitFor({ timeout: 20000 });
    const post = apiSince(t0, (e) => e.path === "/jobs/ingest")[0];
    must(post && post.status === 202, `POST /jobs/ingest respondio ${post && post.status}`);
    const vals = await page.locator("strong").allInnerTexts();
    state.jobId = post.body.job_id;
    obs(`la interfaz muestra Job ID ${vals[0]}, Status ${vals[1]}, Queue ${vals[2]}; X-Tenant-Id de la peticion: ${post.tenant}`);
    must(vals[0] === state.jobId, "el Job ID mostrado no coincide con la respuesta");
    await snap("ingesta-aceptada");
  });

  await step("5.2", "Trabajo completado en CockroachDB", ["5.1"], async (obs) => {
    const end = Date.now() + 120000; let status = "";
    const q = `SELECT status FROM jobs WHERE id = '${state.jobId}'`;
    while (Date.now() < end) { status = cockroach(q).split(/\r?\n/).at(-1); if (["completed", "failed"].includes(status)) break; await sleep(2000); }
    obs(`consulta: ${q} -> ${status || "(sin fila)"}`);
    must(status === "completed", `el trabajo termino en '${status}'`);
  });

  await step("5.3", "Documento, fragmentos y vectores en pgvector", ["5.2"], async (obs) => {
    const doc = pg(`SELECT id, tenant_id, source, artifact_uri, chunk_count FROM knowledge_documents WHERE job_id = '${state.jobId}'`);
    obs(`knowledge_documents (job_id = ${state.jobId}): ${doc}`);
    const [docId, tenant] = doc.split("|");
    must(tenant === "tenant-growth", `el documento consta en '${tenant}'`);
    state.docId = docId;
    const chunks = pg(`SELECT count(*) FROM document_chunks WHERE document_id = '${docId}'`);
    const emb = pg(`SELECT count(*), min(dimension), max(dimension), string_agg(DISTINCT provider, ',') FROM chunk_embeddings e JOIN document_chunks c ON c.id = e.chunk_id WHERE c.document_id = '${docId}'`);
    obs(`document_chunks: ${chunks}; chunk_embeddings (cuenta|dim min|dim max|proveedor): ${emb}`);
    const other = pg(`SELECT count(*) FROM knowledge_documents WHERE job_id = '${state.jobId}' AND tenant_id <> 'tenant-growth'`);
    const core = pg(`SELECT count(*) FROM document_chunks c JOIN knowledge_documents d ON d.id = c.document_id WHERE d.tenant_id = 'tenant-core' AND d.job_id = '${state.jobId}'`);
    obs(`fragmentos de este trabajo en tenant-core: ${core}; documentos de este trabajo fuera de tenant-growth: ${other}`);
    must(Number(chunks) > 0 && Number(chunks) === Number(emb.split("|")[0]), "fragmentos y vectores no cuadran");
    must(core === "0" && other === "0", "el documento consta en otro ambito");
    const same = pg(`SELECT id FROM knowledge_documents WHERE tenant_id = 'tenant-growth' AND source = 'assistant-corpus' AND artifact_uri = '${DOC_PATH}' ORDER BY created_at`).split(/\r?\n/).filter(Boolean);
    state.docIds = same;
    obs(`documentos de tenant-growth con este mismo origen y URI: ${same.length} (${same.map((i) => (i === docId ? `${i} <- este recorrido` : i)).join(", ")})`);
    const dim = pg("SELECT format_type(atttypid, atttypmod) FROM pg_attribute WHERE attrelid = 'chunk_embeddings'::regclass AND attname = 'embedding'");
    obs(`tipo de la columna de vectores: ${dim}`);
  });

  await step("5.4", "Registro del processor para el trabajo", ["5.2"], async (obs) => {
    const log = compose("logs", "--no-log-prefix", "processor");
    const lines = log.split(/\r?\n/).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter((d) => d && d.timestamp >= state.ingestStart);
    fs.writeFileSync(path.join(OUT, "processor-log.txt"), lines.map((d) => JSON.stringify({ timestamp: d.timestamp, level: d.level, event: d.event, logger: d.logger })).join("\n"));
    const errors = lines.filter((d) => ["error", "critical"].includes(d.level));
    obs(`${lines.length} eventos del processor desde ${state.ingestStart}: ${[...new Set(lines.map((d) => `${d.event}(${d.level})`))].join(", ")}; de nivel error: ${errors.length}`);
  });

  await step("6.1", "Pregunta JUP-069-004 en Growth Ops", ["5.3"], async (obs) => {
    obs(`pregunta: ${QUESTION}`);
    const r = await askAssistant(page, QUESTION);
    state.growth = r;
    obs(`conversacion creada con New: ${r.createdId}; conversacion que recibio el mensaje: ${r.convId}${r.createdId === r.convId ? "" : " (NO coinciden)"}`);
    obs(`respuesta (${r.text.length} caracteres): ${r.text.replace(/\n/g, " / ").slice(0, 600)}`);
    const frags = fragments(r.text);
    obs(`fragmentos mostrados: ${frags.length}`);
    must(frags.length > 0, "la respuesta no contiene fragmentos");
    // Exacta: cada fragmento mostrado es el prefijo de 140 caracteres de un fragmento guardado de un documento de esta ingesta.
    const ids = state.docIds.map((i) => `'${i}'`).join(",");
    const stored = new Set(pg(`SELECT left(content, 140) FROM document_chunks WHERE document_id IN (${ids})`).split(/\r?\n/).map((l) => l.trimEnd()));
    const notStored = frags.filter((f) => !stored.has(f.trimEnd()));
    must(notStored.length === 0, `fragmentos mostrados que no son el prefijo de ningun fragmento guardado: ${notStored.length}`);
    obs("cada fragmento mostrado coincide exactamente con los primeros 140 caracteres de un fragmento guardado en pgvector del documento ingerido");
    const notInDoc = frags.filter((f) => !NORM_DOC.includes(norm(f)));
    must(notInDoc.length === 0, `fragmentos que no son subcadena del documento normalizado: ${notInDoc.length}`);
    obs("y cada uno es subcadena del documento original con los espacios normalizados");
    obs(`retrieved_context de la respuesta: ${r.reply.body.retrieved_context.length} fragmentos, distancias ${r.reply.body.retrieved_context.map((c) => c.distance.toFixed(4)).join(", ")}`);
    await snap("asistente-growth");
  });

  await step("6.2", "Evento retrieval del backend", ["6.1"], async (obs) => {
    const id = state.growth.reply.body.user_message.id;
    const log = compose("logs", "--no-log-prefix", "backend");
    const ev = log.split(/\r?\n/).filter((l) => l.includes(id) && l.includes('"retrieval"')).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean).at(-1);
    must(ev, `no hay evento retrieval para el mensaje ${id}`);
    obs(`evento: provider ${ev.provider}, alias ${ev.alias}, top_k ${ev.top_k}, max_distance ${ev.max_distance}, resultados ${ev.results}, document_ids ${JSON.stringify([...new Set(ev.document_ids)])}, distancias ${JSON.stringify(ev.distances)}`);
    state.provider = ev.provider;
    results.notes.embeddingProvider = ev.provider;
    must(ev.document_ids.length > 0 && ev.document_ids.every((d) => state.docIds.includes(d)), "los document_ids no son los de los documentos ingeridos");
    obs(`document_ids dentro de los ${state.docIds.length} documentos de tenant-growth con este origen: ${ev.document_ids.every((d) => state.docIds.includes(d))}; incluye el de este recorrido: ${ev.document_ids.includes(state.docId)}`);
  });

  await step("6.3", "Recarga del historial (RF-087-002)", ["6.1"], async (obs) => {
    const t0 = Date.now();
    await page.reload();
    await page.getByLabel("Ambito de cliente").waitFor({ timeout: 20000 });
    await page.getByLabel("Ambito de cliente").selectOption({ label: "Growth Ops" });
    await nav(page, "Assistant");
    const isMine = (e) => e.t >= t0 && e.method === "GET" && e.path === `/assistant/conversations/${state.growth.convId}`;
    await page.getByText("Assistant chat").waitFor();
    await sleep(3000);
    if (!seen.some(isMine)) {
      // La aplicacion selecciona la primera conversacion de la lista; si no es la de este recorrido, se abre pulsandola.
      const titles = page.locator("button", { hasText: "Ops review" });
      const n = await titles.count();
      obs(`la conversacion de este recorrido no es la primera de la lista (${n} con el mismo titulo): se abre pulsando cada una hasta dar con ella`);
      for (let i = 0; i < n && !seen.some(isMine); i++) { await titles.nth(i).click(); await sleep(1500); }
    }
    const detail = await waitApi(isMine, 20000);
    obs(`GET ${detail.path} -> ${detail.status}`);
    must(detail.status === 200, `el historial respondio ${detail.status}`);
    await page.getByText(QUESTION).first().waitFor({ timeout: 10000 });
    await page.getByText("He encontrado contexto relacionado").first().waitFor({ timeout: 10000 });
    obs(`tras recargar se muestran la pregunta y la respuesta; mensajes en el historial: ${detail.body.messages.length}`);
    await snap("historial-recargado");
  });

  await step("6.3b", "Segunda conversacion en el mismo ambito: el mensaje va a la conversacion nueva", ["6.1"], async (obs) => {
    await selectTenant(page, "Growth Ops");
    await nav(page, "Assistant");
    const list = await page.locator("button", { hasText: "Ops review" }).count();
    await page.getByPlaceholder("New conversation title").fill("Segunda conversacion");
    const t0 = Date.now();
    await page.getByRole("button", { name: "New", exact: true }).click();
    const created = await waitApi((e) => e.t >= t0 && e.method === "POST" && e.path === "/assistant/conversations" && e.body, 15000);
    const box = page.getByPlaceholder("Ask the assistant about the ingested tenant documents.");
    await box.waitFor();
    await box.fill("Comprobacion: a que conversacion va este mensaje?");
    await page.getByRole("button", { name: "Send", exact: true }).click();
    const sent = await waitApi((e) => e.t >= t0 && e.method === "POST" && e.path.endsWith("/messages"), 30000);
    const usedId = sent.path.split("/")[3];
    obs(`conversaciones previas en Growth Ops con titulo 'Ops review': ${list}; conversacion creada: ${created.body.id}; el mensaje se envio a: ${usedId}`);
    await snap("segunda-conversacion");
    must(usedId === created.body.id, `el mensaje se envio a la conversacion ${usedId} y no a la recien creada ${created.body.id}`);
  });

  await step("6.4", "La misma pregunta en Core Finance", ["6.1"], async (obs) => {
    await selectTenant(page, "Core Finance");
    const r = await askAssistant(page, QUESTION);
    obs(`respuesta (${r.text.length} caracteres): ${r.text.replace(/\n/g, " / ").slice(0, 400)}`);
    const frags = fragments(r.text);
    obs(`fragmentos mostrados: ${frags.length}; retrieved_context: ${r.reply.body.retrieved_context.length}`);
    const fromDoc = frags.filter((f) => NORM_DOC.includes(norm(f)));
    must(fromDoc.length === 0, `${fromDoc.length} fragmentos del documento de Growth Ops aparecen en Core Finance`);
    obs("ningun fragmento mostrado en Core Finance es del documento ingestado en Growth Ops");
    const ids = r.reply.body.retrieved_context.map((c) => c.chunk_id);
    if (ids.length) {
      const inGrowth = pg(`SELECT count(*) FROM document_chunks WHERE document_id IN (${state.docIds.map((i) => `'${i}'`).join(",")}) AND id IN (${ids.map((i) => `'${i}'`).join(",")})`);
      obs(`de esos ${ids.length} chunk_id, pertenecen al documento de Growth Ops: ${inGrowth}`);
      must(inGrowth === "0", "chunk_id del documento de Growth Ops devueltos a Core Finance");
    }
    await snap("asistente-core");
  });

  await step("6.5", "Cierre de sesion y ruta protegida", ["4.1"], async (obs) => {
    await page.getByRole("button", { name: "Cerrar sesion" }).click();
    await page.getByRole("heading", { name: "Access the tenant control tower" }).waitFor({ timeout: 10000 });
    obs(`tras cerrar sesion se presenta el acceso (${new URL(page.url()).pathname})`);
    await page.goto(`${BASE}/assistant`);
    await page.getByRole("heading", { name: "Access the tenant control tower" }).waitFor({ timeout: 10000 });
    obs(`abrir /assistant directamente termina en ${new URL(page.url()).pathname}`);
    const left = await page.evaluate(() => Boolean(localStorage.getItem("finops.session")));
    must(!left, "queda sesion guardada");
    await snap("cierre-sesion");
  });

  results.finished = new Date().toISOString();
  const bad = results.consoleErrors.filter((m) => /CORS|Access-Control/i.test(m));
  results.summary = { pass: results.steps.filter((s) => s.status === "pass").length, fail: results.steps.filter((s) => s.status === "fail").length, notRun: results.steps.filter((s) => s.status === "not_run").length, pageErrors: results.pageErrors.length, corsConsoleErrors: bad.length, consoleErrors: results.consoleErrors.length, failedRequests: results.failedRequests.length };
  const byCode = {};
  for (const e of seen) { const k = `${e.method} ${e.path} ${e.status}`; byCode[k] = (byCode[k] || 0) + 1; }
  results.notes.apiResponses = byCode;
  results.notes.apiServerErrors = seen.filter((e) => e.status >= 500).length;
  results.notes.apiClientErrors = seen.filter((e) => e.status >= 400 && e.status < 500).length;
  fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 2));
  console.log("\nRESUMEN", JSON.stringify(results.summary));
  await browser.close();
  process.exit(results.summary.fail || results.pageErrors.length || bad.length ? 1 : 0);
})().catch((e) => { console.error("ERROR NO PREVISTO", e); process.exit(3); });
```
