// Validación de JUP-038 en un Chrome real contra el stack aislado `jup038v` (tarea 8.1).
// Uso: node validar-navegador.cjs <directorio privado con stack/jup038.env y capturas/>. Requiere `npm i playwright-core`
// y Chrome. Las capturas y el informe JSON se escriben en <directorio>/capturas. El archivo de entorno NO se versiona.
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const SCR = process.argv[2];
const REPO = path.resolve(__dirname, "../../..");
const env = Object.fromEntries(fs.readFileSync(path.join(SCR, "stack/jup038.env"), "utf8").split(/\r?\n/)
  .filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.split("=")[0], l.slice(l.indexOf("=") + 1)]));
const esperados = JSON.parse(fs.readFileSync(path.join(REPO, "docs/demo/JUP-107/esperados-anomalias.json"), "utf8"));
const BASE = "http://localhost:18742";
const SEV = { P1: "Alta (P1)", P2: "Media (P2)", P3: "Baja (P3)" };
const CAP = path.join(SCR, "capturas");
const report = { servicios: {}, consola: [], peticionesFallidas: [], generales: {} };
const log = (...a) => console.log(...a);

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const requests = [];
  page.on("request", (r) => requests.push({ method: r.method(), url: r.url(), t: Date.now() }));
  page.on("console", (m) => { if (["error", "warning"].includes(m.type())) report.consola.push(`${m.type()}: ${m.text().slice(0, 200)}`); });
  page.on("pageerror", (e) => report.consola.push(`pageerror: ${String(e).slice(0, 200)}`));
  page.on("requestfailed", (r) => report.peticionesFallidas.push(`${r.method()} ${r.url()} ${r.failure()?.errorText}`));
  const posts = () => requests.filter((r) => r.method === "POST" && /\/assistant\/conversations\/[^/]+\/messages/.test(r.url)).length;

  // 1. Acceso y cliente
  await page.goto(`${BASE}/login`);
  await page.fill("#login-email", "operator@example.com");
  await page.fill("#login-password", env.DEMO_PASSWORD);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 20000 });
  const tenantSelect = page.locator("select").first();
  await tenantSelect.waitFor({ timeout: 20000 });
  report.generales.clientes = await tenantSelect.locator("option").allInnerTexts();
  await tenantSelect.selectOption({ label: "Core Finance" });
  log("clientes:", report.generales.clientes, "| activo:", await tenantSelect.inputValue());

  // 2. Panel sin detectar y detección
  await page.goto(`${BASE}/anomalies`);
  await page.getByRole("button", { name: /Detectar ahora/ }).waitFor({ timeout: 20000 });
  const antes = await page.locator("main").innerText();
  report.generales.antesDeDetectar = /Todavía no se han buscado anomalías/.test(antes);
  report.generales.avisoSintetico = /Datos sintéticos de demostración/.test(antes);
  await page.getByRole("button", { name: /Detectar ahora/ }).click();
  await page.getByRole("status", { name: "Resultado de la detección" }).waitFor({ timeout: 30000 });
  report.generales.resultadoDeteccion = (await page.getByRole("status", { name: "Resultado de la detección" }).innerText()).replace(/\s+/g, " ").slice(0, 300);
  await page.waitForSelector("table tbody tr", { timeout: 20000 });
  report.generales.filas = (await page.locator("table tbody tr").allInnerTexts()).map((t) => t.replace(/\s+/g, " "));
  log("detección:", report.generales.resultadoDeteccion);
  log("filas:", report.generales.filas);
  await page.screenshot({ path: path.join(CAP, "01-panel-1280.png"), fullPage: true });

  // 3. Por cada anomalía esperada: detalle -> enlace -> asistente -> enviar -> verificar
  let primera = true;
  // JUP-119 agrupó los episodios por fecha de referencia: los tres de JUP-107 son los de 2026-09-21 (la versión 2 del
  // archivo los tenía en `episodes`). El stack debe arrancar con COST_REFERENCE_DATE=2026-09-21.
  const esperadosEpisodios = esperados.episodes ?? esperados.episodes_by_reference["2026-09-21"].episodes;
  for (const esp of esperadosEpisodios) {
    const svc = esp.service;
    const r = (report.servicios[svc] = { esperado: esp, comprobaciones: {} });
    const ok = (k, v, extra) => { r.comprobaciones[k] = v; if (!v) log("  ✗", svc, k, extra ?? ""); };
    try {
      await page.goto(`${BASE}/anomalies`);
      await page.waitForSelector("table tbody tr", { timeout: 20000 });
      await page.getByRole("button", { name: new RegExp(`^Detalle de ${svc}`) }).first().click();
      const dialog = page.getByRole("dialog");
      await dialog.waitFor();
      const link = dialog.getByRole("link", { name: "Explicar en el asistente" });
      await link.waitFor();
      const href = await link.getAttribute("href");
      r.href = href;
      ok("enlace con formato", /^\/assistant\?episode=anomaly-[0-9a-f]{64}$/.test(href ?? ""), href);
      const episodeId = (href ?? "").split("episode=")[1];
      if (primera) await page.screenshot({ path: path.join(CAP, "02-detalle-con-enlace-1280.png") });
      const postsAntes = posts();
      await link.click();
      await page.waitForURL(/\/assistant\?episode=/, { timeout: 15000 });
      ok("navega a /assistant con el parametro", page.url().endsWith(`/assistant?episode=${episodeId}`), page.url());
      // sin conversación seleccionada el redactor no existe: se crea una desde la pantalla, como haría una persona
      await page.waitForLoadState("networkidle");
      const nueva = page.getByRole("button", { name: /^Nueva$/ });
      const haySelector = await page.getByRole("checkbox", { name: "Explicar una anomalía" }).count();
      if (!haySelector) { await nueva.click(); }
      const casilla = page.getByRole("checkbox", { name: "Explicar una anomalía" });
      await casilla.waitFor({ timeout: 20000 });
      ok("modo activado por el enlace", await casilla.isChecked());
      const select = page.getByRole("combobox", { name: "Anomalía", exact: true });
      await select.waitFor({ timeout: 20000 });
      await page.waitForFunction((id) => document.querySelector("select")?.value !== "" || [...document.querySelectorAll("select")].some((s) => s.value === id), episodeId, { timeout: 15000 });
      ok("anomalía preseleccionada = la del enlace", (await select.inputValue()) === episodeId, await select.inputValue());
      ok("pregunta propuesta", (await page.getByRole("textbox", { name: "Pregunta" }).inputValue()) === "¿Por qué se ha marcado esta anomalía?");
      ok("CERO POST antes de pulsar Enviar", posts() === postsAntes, `posts=${posts()} antes=${postsAntes}`);
      const aviso = await page.getByRole("status").filter({ hasText: "no está entre las de este cliente" }).count();
      ok("sin aviso de anomalía ajena", aviso === 0);
      const articulosAntes = await page.locator("article").count();
      const respuesta = page.waitForResponse((resp) => /\/messages$/.test(resp.url()) && resp.request().method() === "POST", { timeout: 20000 });
      await page.getByRole("button", { name: "Enviar" }).click();
      const resp = await respuesta;
      r.status = resp.status();
      ok("POST 201", resp.status() === 201, String(resp.status()));
      ok("exactamente 1 POST de mensajes", posts() === postsAntes + 1);
      const cuerpo = JSON.parse(resp.request().postData() ?? "{}");
      ok("cuerpo del POST = {content, anomaly_query}", JSON.stringify(Object.keys(cuerpo).sort()) === JSON.stringify(["anomaly_query", "content"]) && cuerpo.anomaly_query?.episode_id === episodeId, JSON.stringify(Object.keys(cuerpo)));
      await page.waitForFunction((n) => document.querySelectorAll("article").length >= n + 2, articulosAntes, { timeout: 20000 });
      ok("el parámetro episode desaparece de la dirección", !page.url().includes("episode="), page.url());
      const ultimo = page.locator("article").last();
      const texto = await ultimo.innerText();
      r.texto = texto;
      // Valores esperados (documento de JUP-107, calculados con aritmética exacta sin el backend)
      ok("referencia diaria", texto.includes(`frente a una referencia de ${esp.reference_daily_cost} EUR al día`), esp.reference_daily_cost);
      ok("impacto y días", texto.includes(`Impacto acumulado: ${esp.accumulated_impact} EUR en ${esp.impact_day_count} días`), `${esp.accumulated_impact}/${esp.impact_day_count}`);
      ok("criticidad", texto.includes(`Criticidad: ${SEV[esp.severity]}`), SEV[esp.severity]);
      ok("servicio entrecomillado", texto.includes(`Anomalía candidata en el servicio "${svc}" (EUR).`));
      ok("causa no establecida", texto.includes("Causa no establecida: es un candidato para investigar"));
      ok("aviso de datos sintéticos", texto.includes("incluyen datos sintéticos de demostración"));
      ok("estado y seguimiento", esp.observation === "observed"
        ? texto.includes("Estado: Nueva. Se sigue observando.")
        : texto.includes(`Ya no se observa desde ${esp.no_longer_observed_on}; sigue abierta hasta que una persona la cierre.`));
      ok("día de apertura", texto.includes(`el ${esp.start_date} el coste observado fue`));
      const resumen = ultimo.getByText(/^Evidencia de la anomalía — /);
      ok("bloque de evidencia visible", (await resumen.count()) === 1);
      ok("resumen con la criticidad", (await resumen.innerText()).includes(SEV[esp.severity]));
      await resumen.click();
      await ultimo.getByText("Operandos exactos").click();
      const operandos = await ultimo.locator("details details").innerText();
      r.operandos = operandos.replace(/\s+/g, " ");
      ok("operandos exactos con 12 decimales", /\d+\.\d{12}/.test(operandos), operandos);
      ok("limitaciones listadas", (await ultimo.getByLabel("Limitaciones").locator("li").count()) === 5);
      await ultimo.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(CAP, `03-explicacion-${svc.toLowerCase()}-1280.png`), fullPage: true });
      if (svc === "Compute") {
        await page.setViewportSize({ width: 390, height: 844 });
        await ultimo.scrollIntoViewIfNeeded();
        const desbordaX = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
        ok("sin desbordamiento horizontal a 390 px", !desbordaX);
        await page.screenshot({ path: path.join(CAP, "04-explicacion-compute-390.png"), fullPage: true });
        await page.setViewportSize({ width: 1280, height: 900 });
      }
      primera = false;
    } catch (e) {
      r.error = String(e).slice(0, 400);
      log("  ERROR en", svc, r.error);
      await page.screenshot({ path: path.join(CAP, `error-${svc}.png`), fullPage: true }).catch(() => {});
    }
    const fallos = Object.entries(r.comprobaciones).filter(([, v]) => !v).map(([k]) => k);
    log(`${svc}: ${Object.keys(r.comprobaciones).length - fallos.length}/${Object.keys(r.comprobaciones).length} comprobaciones OK${fallos.length ? " | fallan: " + fallos.join("; ") : ""}`);
  }
  report.generales.postsTotales = posts();
  fs.writeFileSync(path.join(SCR, "capturas/informe-8.1.json"), JSON.stringify(report, null, 2));
  log("consola (errores/avisos):", report.consola.length, "| peticiones fallidas:", report.peticionesFallidas.length);
  await browser.close();
})().catch((e) => { console.error("FALLO GENERAL", e); process.exit(1); });
