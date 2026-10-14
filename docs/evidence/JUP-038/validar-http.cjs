// Uso: node validar-http.cjs <directorio privado con stack/jup038.env y capturas/>  (SOLO82=1 repite solo el recálculo 8.2).
// Tareas 8.2 y 8.3 de JUP-038 contra el stack aislado `jup038v`: recálculo independiente de una evidencia y
// comprobaciones por HTTP. NO importa nada del backend: reimplementa el cálculo con BigInt y el hash con crypto.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const SCR = process.argv[2];
const env = Object.fromEntries(fs.readFileSync(path.join(SCR, "stack/jup038.env"), "utf8").split(/\r?\n/)
  .filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.split("=")[0], l.slice(l.indexOf("=") + 1)]));
const API = "http://localhost:18741";
const out = { c: {}, notas: [] };
const ok = (k, v, extra) => { out.c[k] = !!v; console.log(v ? "  ✓" : "  ✗", k, v ? "" : `-> ${extra ?? ""}`); };

async function call(method, url, { token, tenant, body } = {}) {
  const r = await fetch(API + url, {
    method, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(tenant ? { "X-Tenant-Id": tenant } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await r.text();
  let json; try { json = JSON.parse(text); } catch { json = text; }
  return { status: r.status, json, text };
}

// ---- Oráculo independiente: decimales exactos con BigInt (escala 12) y redondeo HALF_UP a 2 decimales ----
const SC = 12n;
const parse = (s) => { const m = /^(-?)(\d+)(?:\.(\d+))?$/.exec(s); const f = (m[3] ?? "").padEnd(Number(SC), "0").slice(0, Number(SC)); return BigInt(m[1] + m[2] + f); };
const U = 10n ** SC;
// num/den (BigInt, escala SC en num) -> texto con 2 decimales, HALF_UP (valores positivos)
const fmt2 = (num, den) => { const scaled = (num * 100n * 2n + den * U) / (den * 2n * U); const s = scaled.toString().padStart(3, "0"); return `${s.slice(0, -2)}.${s.slice(-2)}`; };
function canonical(v) { // equivalente a json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)
  if (Array.isArray(v)) return `[${v.map(canonical).join(",")}]`;
  if (v && typeof v === "object") return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canonical(v[k])}`).join(",")}}`;
  return JSON.stringify(v);
}

(async () => {
  const login = await call("POST", "/auth/login", { body: { email: "operator@example.com", password: env.DEMO_PASSWORD } });
  const token = login.json.access_token;
  ok("login", login.status === 200 && token, login.text.slice(0, 80));
  const core = { token, tenant: "tenant-core" };
  const list = await call("GET", "/billing/anomalies/episodes?scope=all", core);
  const episodes = list.json.episodes;
  const by = Object.fromEntries(episodes.map((e) => [e.service, e]));
  ok("3 episodios en tenant-core", episodes.length === 3, String(episodes.length));

  // conversación con las tres explicaciones guardadas por el navegador
  const convs = await call("GET", "/assistant/conversations", core);
  let evidencias = [];
  for (const c of convs.json.items) {
    const d = await call("GET", `/assistant/conversations/${c.id}`, core);
    for (const m of d.json.messages) if (m.role === "assistant" && m.metadata?.anomaly_evidence) evidencias.push({ conv: c.id, msg: m });
  }
  ok("hay explicaciones guardadas por el navegador (3)", evidencias.length >= 3, String(evidencias.length));

  // ===== 8.2 Recálculo independiente de la evidencia de Compute =====
  console.log("== 8.2 recálculo independiente");
  const e = evidencias.map((x) => x.msg.metadata.anomaly_evidence).find((x) => x.episode.service === "Compute");
  const R = parse(e.operands.reference_seven_day_total), O = parse(e.operands.opening_observed_cost), I7 = parse(e.operands.accumulated_impact_times_seven);
  const refDaily = fmt2(R, 7n), abs = fmt2(O * 7n - R, 7n);
  const exceso = O * 7n - R;
  const rel = fmt2(exceso * 100n * U, R); // (O*7-R)*100/R: el cociente es adimensional (ambos con escala U)
  const impacto = fmt2(I7, 7n);
  const sev = I7 > 2000n * 7n * U ? "P1" : I7 >= 500n * 7n * U ? "P2" : "P3";
  console.log("  operandos:", e.operands, "->", { refDaily, abs, rel, impacto, sev });
  ok("referencia diaria recalculada", refDaily === e.opening.reference_daily_cost, `${refDaily} vs ${e.opening.reference_daily_cost}`);
  ok("subida absoluta recalculada", abs === e.opening.absolute_increase, `${abs} vs ${e.opening.absolute_increase}`);
  ok("subida relativa recalculada", rel === e.opening.relative_increase_percent, `${rel} vs ${e.opening.relative_increase_percent}`);
  ok("impacto acumulado recalculado", impacto === e.impact.accumulated_impact, `${impacto} vs ${e.impact.accumulated_impact}`);
  ok("criticidad recalculada", sev === e.impact.severity, `${sev} vs ${e.impact.severity}`);
  ok("regla estricta cumplida (>100 y >20 %)", exceso > 100n * 7n * U && exceso * 5n > R);
  const { id, explained_at, ...cuerpo } = e;
  const hash = crypto.createHash("sha256").update(canonical({ tenant: "tenant-core", ...cuerpo }), "utf8").digest("hex");
  ok("identificador recalculado desde el JSON canónico (sha256)", `anomaly-explanation:${hash}` === id, `${hash} vs ${id}`);
  out.notas.push({ operandos: e.operands, recalculado: { refDaily, abs, rel, impacto, sev }, id, hashRecalculado: `anomaly-explanation:${hash}` });

  if (process.env.SOLO82) { console.log(`
RESUMEN 8.2: ${Object.values(out.c).filter(Boolean).length}/${Object.keys(out.c).length} OK`); fs.writeFileSync(path.join(SCR, "capturas/informe-8.2.json"), JSON.stringify(out, null, 2)); return; }
  // ===== 8.3 Comprobaciones por HTTP =====
  console.log("== 8.3 HTTP");
  const compute = by.Compute, database = by.Database;
  // conversación propia en tenant-core (para pedir explicaciones por HTTP)
  const conv = (await call("POST", "/assistant/conversations", { ...core, body: { title: "validacion 8.3" } })).json;
  const ask = (id, ctx = core, convId = conv.id) => call("POST", `/assistant/conversations/${convId}/messages`, { ...ctx, body: { content: "¿Por qué?", anomaly_query: { episode_id: id } } });
  const msgs = async (ctx, convId) => (await call("GET", `/assistant/conversations/${convId}`, ctx)).json.messages.length;

  // a) aislamiento: otro cliente e inexistente dan la misma respuesta
  const growth = { token, tenant: "tenant-growth" };
  const convG = (await call("POST", "/assistant/conversations", { ...growth, body: { title: "validacion growth" } })).json;
  const ajeno = await ask(compute.id, growth, convG.id);
  const falso = await ask("anomaly-" + "0".repeat(64), growth, convG.id);
  ok("id de otro cliente -> 404", ajeno.status === 404, `${ajeno.status} ${ajeno.text}`);
  ok("id inexistente -> 404", falso.status === 404, `${falso.status} ${falso.text}`);
  ok("misma respuesta byte a byte (otro cliente = inexistente)", ajeno.text === falso.text, `${ajeno.text} | ${falso.text}`);
  ok("cuerpo exacto del 404", ajeno.text === '{"detail":{"code":"anomaly_episode_not_found"}}', ajeno.text);
  ok("la conversación del otro cliente sigue sin mensajes", (await msgs(growth, convG.id)) === 0);
  // id con formato inválido -> 422 sin tocar nada
  const inval = await ask("anomaly-ZZ", core);
  ok("formato inválido -> 422", inval.status === 422, String(inval.status));
  ok("ambas selecciones a la vez -> 422", (await call("POST", `/assistant/conversations/${conv.id}/messages`, { ...core, body: { content: "x", anomaly_query: { episode_id: compute.id }, ownership_query: { group_by: "project" } } })).status === 422);
  ok("nada guardado tras 404/422", (await msgs(core, conv.id)) === 0);

  // b) pgvector parado: la explicación responde
  console.log("  (parando pgvector)");
  spawnSync("docker", ["stop", "jup038v-postgres-pgvector-1"], { encoding: "utf8" });
  const sinVector = await ask(compute.id);
  ok("con pgvector PARADO la explicación responde 201", sinVector.status === 201, `${sinVector.status} ${sinVector.text.slice(0, 120)}`);
  const idSinVector = sinVector.json.assistant_message?.metadata?.anomaly_evidence?.id;
  const docSinVector = await call("POST", `/assistant/conversations/${conv.id}/messages`, { ...core, body: { content: "pregunta documental" } });
  ok("(control) una pregunta documental SÍ falla sin pgvector", docSinVector.status >= 500, String(docSinVector.status));
  spawnSync("docker", ["start", "jup038v-postgres-pgvector-1"], { encoding: "utf8" });
  console.log("  (pgvector reiniciado)");

  // c) cambio de estado: el id cambia y el mensaje anterior se conserva
  const antes = await ask(compute.id);
  const idAntes = antes.json.assistant_message.metadata.anomaly_evidence.id;
  ok("misma anomalía sin cambios -> mismo id (con y sin pgvector)", idAntes === idSinVector, `${idAntes} vs ${idSinVector}`);
  const patch = await call("PATCH", `/billing/anomalies/episodes/${compute.id}`, { ...core, body: { status: "investigating" } });
  ok("PATCH a investigating = 200", patch.status === 200, `${patch.status} ${patch.text.slice(0, 100)}`);
  const despues = await ask(compute.id);
  const evDespues = despues.json.assistant_message.metadata.anomaly_evidence;
  ok("tras cambiar el estado el id CAMBIA", evDespues.id !== idAntes);
  ok("el texto nuevo dice «Investigando»", despues.json.assistant_message.content.includes("Estado: Investigando."));
  const guardados = (await call("GET", `/assistant/conversations/${conv.id}`, core)).json.messages.filter((m) => m.role === "assistant");
  const vieja = guardados.find((m) => m.metadata?.anomaly_evidence?.id === idAntes);
  ok("el mensaje anterior se conserva con su id y «Nueva»", vieja && vieja.content.includes("Estado: Nueva."));
  ok("3 explicaciones guardadas en la conversación", guardados.length === 3, String(guardados.length));

  // d) episodio cerrado con motivo con comillas y acentos: fecha UTC y escape
  const motivo = 'Cierre "prueba" ñ Ünicode';
  const cierre = await call("PATCH", `/billing/anomalies/episodes/${database.id}`, { ...core, body: { status: "resolved", reason: motivo } });
  ok("cerrar Database con motivo = 200", cierre.status === 200, `${cierre.status} ${cierre.text.slice(0, 100)}`);
  const cerrada = await ask(database.id);
  const txt = cerrada.json.assistant_message?.content ?? "";
  const fechaUtc = new Date(cierre.json.closed_at).toISOString().slice(0, 10);
  ok("la explicación del cierre lleva la fecha UTC y el motivo escapado", txt.includes(`Cerrada el ${fechaUtc} (UTC) con el motivo ${JSON.stringify(motivo)}.`), txt.split("\n").find((l) => l.startsWith("Estado")));

  // e) registros del backend: ni nombres de servicio ni motivos
  const logs = spawnSync("docker", ["logs", "jup038v-backend-1"], { encoding: "utf8", maxBuffer: 1 << 26 });
  const texto = (logs.stdout || "") + (logs.stderr || "");
  const hallazgos = ["Compute", "Database", "Analytics", "Cierre \"prueba\"", "Cierre \\\"prueba\\\""].filter((s) => texto.includes(s));
  console.log("  líneas de registro del backend:", texto.split("\n").length, "| mensajes de explicación:", (texto.match(/messages/g) || []).length);
  ok("ningún nombre de servicio ni motivo en los registros del backend", hallazgos.length === 0, hallazgos.join(", "));
  out.notas.push({ lineasRegistro: texto.split("\n").length });

  fs.writeFileSync(path.join(SCR, "capturas/informe-8.2-8.3.json"), JSON.stringify(out, null, 2));
  const fallos = Object.entries(out.c).filter(([, v]) => !v).map(([k]) => k);
  console.log(`\nRESUMEN: ${Object.keys(out.c).length - fallos.length}/${Object.keys(out.c).length} OK${fallos.length ? " | fallan: " + fallos.join("; ") : ""}`);
})().catch((e) => { console.error("FALLO GENERAL", e); process.exit(1); });
