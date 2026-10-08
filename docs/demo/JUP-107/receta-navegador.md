# Receta de navegador JUP-107

Guion que recorre la [demo](guion.md) en un navegador real y comprueba lo que muestra la interfaz contra las cifras de [esperados.json](esperados.json). Se ejecuta **fuera del repositorio**: Playwright no es dependencia del proyecto. Capturas, vídeo y resultados se guardan también fuera.

## Qué hace y qué no

- Entra por el formulario de acceso con la cuenta de demostración, recorre los pasos D1 a D10 (y D11 si no se desactiva) y, en cada uno, comprueba los textos y las cifras de la interfaz: totales por periodo, filas de desglose, filas de la tabla mensual (incluido el mes sin datos), comparaciones, aviso de registros sin fecha y el cambio de cliente.
- Guarda una captura por paso, un vídeo mudo de la sesión y `resultado.json` con `pass`, `fail` o `not_run` por paso. Si un paso falla, los siguientes quedan como `not_run`.
- **No carga ni retira datos**: `apply` y `remove` son comandos explícitos de [preparacion.md](preparacion.md).
- **No intercepta ni responde peticiones** y no escribe la sesión en el almacenamiento: solo observa lo que la interfaz recibe del backend. Falla ante un error de página o de origen cruzado.
- La contraseña de demostración se pasa por la variable de entorno `DEMO_PASSWORD` y no se imprime ni se guarda.
- Es una ejecución **automatizada**: comprueba valores y etiquetas, no el cronometraje de una persona presentando. Se anota en [registro-ensayo.md](registro-ensayo.md) como tal.

## Requisitos

- El stack de [preparacion.md](preparacion.md) levantado y con los datos cargados (`status` en `present`).
- Node.js 22 o superior. Verificado con Node `v24.15.0`, Playwright `1.63.0` y Chromium `153.0.8010.12` (revisión `1243` de Playwright).

## Preparación

En una carpeta propia fuera del repositorio:

```powershell
npm init -y
npm install playwright-core
npx playwright-core install chromium
```

Guardar el script de abajo como `demo107.js` en esa carpeta.

## Ejecución

```powershell
$env:DEMO_PASSWORD = '<contraseña de demostración>'
$env:OUT_DIR = 'C:\ruta\fuera\del\repo\jup107-run'
$env:CHROMIUM_PATH = '<ruta a chrome.exe de la revisión 1243 de Playwright>'
$env:EXPECTED_JSON = '<ruta al checkout>\docs\demo\JUP-107\esperados.json'
$env:COMMIT = '<commit del paquete de demo>'
node demo107.js
```

Variables opcionales: `BASE_URL` (por defecto `http://localhost:5173`) y `WITH_OPTIONAL=0` para omitir D11. La salida es una línea por paso; el código de salida es 1 si algún paso falla y 2 si faltan variables o hay un error de la propia receta.

## Control positivo

Para comprobar que la receta detecta un desajuste, apuntar `EXPECTED_JSON` a una copia de `esperados.json` con una cifra alterada (por ejemplo el `expected` de `F03` o el `percent` de `F17`): el paso correspondiente debe salir `fail` nombrando la cifra y los siguientes `not_run`.

## Script

```js
// Recorre la demo de JUP-107 en un navegador real y comprueba lo que muestra la interfaz.
// Se ejecuta fuera del repositorio. No carga ni retira datos, no intercepta peticiones y no imprime la contraseña.
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const OUT = process.env.OUT_DIR;
const PASSWORD = process.env.DEMO_PASSWORD;
const CHROMIUM = process.env.CHROMIUM_PATH;
const EXPECTED = process.env.EXPECTED_JSON;
const WITH_OPTIONAL = process.env.WITH_OPTIONAL !== '0';
if (!OUT || !PASSWORD || !CHROMIUM || !EXPECTED) {
  console.error('Faltan OUT_DIR, DEMO_PASSWORD, CHROMIUM_PATH o EXPECTED_JSON.');
  process.exit(2);
}
fs.mkdirSync(OUT, { recursive: true });

const pack = JSON.parse(fs.readFileSync(EXPECTED, 'utf8'));
const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const label = (ym) => `${MONTHS[Number(ym.slice(5, 7)) - 1]} de ${ym.slice(0, 4)}`;
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const signed = (v) => (v.startsWith('-') ? v : `+${v}`);
// Un importe cuenta solo si no es parte de otro mayor (190.00 no vale por 90.00).
const standalone = (s) => new RegExp(`(?<![\\d.])${escape(s)}(?![\\d])`);

function checkFigure(text, f) {
  const out = [];
  if (f.kind === 'period_total') {
    if (!standalone(`${f.expected} ${f.currency}`).test(text)) out.push('falta el total ' + f.expected + ' ' + f.currency);
    if (!text.includes(`${label(f.from)} – ${label(f.to)} · ${f.records} registros`)) out.push('falta el recuento ' + f.records);
  } else if (f.kind === 'group_total') {
    const name = f.key === null ? 'Sin dimensión' : f.key;
    const row = new RegExp(`^${escape(name)}\\t[^\\t]*\\t${f.currency}\\t${escape(f.expected)}\\t${f.records}$`, 'm');
    if (!row.test(text)) out.push(`falta la fila ${name} ${f.currency} ${f.expected} (${f.records})`);
  } else if (f.kind === 'month_total') {
    const row = f.expected === null
      ? new RegExp(`^${label(f.month)}\\t${f.currency}\\t—\\t—\\tSin datos de esta moneda\\.`, 'm')
      : new RegExp(`^${label(f.month)}\\t${f.currency}\\t${escape(f.expected)}\\t${f.records}\\t`, 'm');
    if (!row.test(text)) out.push(`falta la fila mensual ${f.month} ${f.currency} ${f.expected === null ? 'sin datos' : f.expected}`);
  } else if (f.kind === 'comparison') {
    if (!text.includes(`Comparación: ${label(f.last_month)} frente a ${label(f.first_month)} · ${f.currency}`)) out.push('falta el título de la comparación');
    if (!standalone(`${signed(f.difference)} ${f.currency}`).test(text)) out.push('falta la variación absoluta ' + signed(f.difference));
    if (!standalone(`${signed(f.percent)} %`).test(text)) out.push('falta la variación porcentual ' + signed(f.percent));
  } else if (f.kind === 'undated') {
    if (!new RegExp(`(?<![\\d])${f.records} registros sin fecha excluidos`).test(text)) out.push('falta el aviso de registros sin fecha');
  }
  return out.map((m) => `${f.id}: ${m}`);
}

async function main() {
  const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: path.join(OUT, 'video'), size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();
  const problems = [];
  let watching = false;
  const tenant = () => page.getByLabel('Ambito de cliente');
  page.on('pageerror', (e) => problems.push('error de página: ' + e.message));
  page.on('console', (m) => {
    if (m.type() === 'error' && /CORS|Access-Control/i.test(m.text())) problems.push('error de origen cruzado: ' + m.text().slice(0, 120));
  });
  // La interfaz cancela la consulta anterior al cambiar de periodo o de cliente: eso no es un fallo.
  page.on('requestfailed', (r) => {
    const reason = r.failure()?.errorText;
    if (watching && reason !== 'net::ERR_ABORTED') problems.push(`petición fallida: ${new URL(r.url()).pathname} (${reason})`);
  });
  page.on('response', (r) => { if (watching && r.status() >= 400) problems.push(`respuesta ${r.status()}: ${new URL(r.url()).pathname}`); });

  const settle = async () => { await page.waitForLoadState('networkidle').catch(() => {}); await page.waitForTimeout(1500); };
  const main = () => page.innerText('main');
  const setPeriod = async (from, to) => { await page.getByLabel('Mes inicial').fill(from); await page.getByLabel('Mes final').fill(to); };
  const actions = {
    D1: async () => {},
    D2: async () => { await tenant().selectOption('tenant-growth'); await settle(); await setPeriod('2026-01', '2026-06'); },
    D3: async () => { await page.getByLabel('Agrupar por').selectOption('service'); },
    D4: async () => { await page.getByLabel('Moneda').selectOption('EUR'); },
    D5: async () => {},
    D6: async () => { await page.getByLabel('Moneda').selectOption('USD'); },
    D7: async () => { await page.getByLabel('Agrupar por').selectOption('tag'); await page.getByLabel('Clave de etiqueta').fill('cost_center'); },
    D8: async () => {},
    D9: async () => { await tenant().selectOption('tenant-core'); },
    D10: async () => {},
    D11: async () => { await tenant().selectOption('tenant-growth'); await settle(); await setPeriod('2026-07', '2026-07'); await settle(); await page.getByLabel('Moneda').selectOption('USD'); },
  };

  await page.goto(BASE_URL);
  await page.fill('#login-password', PASSWORD);
  await page.click('button[type=submit]');
  try {
    await tenant().waitFor({ timeout: 20000 });
  } catch (e) {
    console.error('No se pudo iniciar sesión: no aparece el selector de cliente.');
    await context.close(); await browser.close();
    process.exit(2);
  }
  await settle();
  watching = true;

  const results = [];
  let blocked = false;
  for (const step of pack.steps) {
    if (step.optional && !WITH_OPTIONAL) continue;
    if (blocked) { results.push({ id: step.id, result: 'not_run', seconds: 0, notes: ['un paso anterior falló'], info: [] }); continue; }
    const started = Date.now();
    const notes = [];
    const info = [];
    try {
      await actions[step.id]();
      await settle();
      const text = await main();
      for (const needle of step.ui_contains || []) if (!text.includes(needle)) notes.push(`no aparece «${needle}»`);
      for (const f of pack.figures.filter((x) => x.step === step.id)) notes.push(...checkFigure(text, f));
      if (step.screen === 'none') info.push('paso hablado: sin comprobación de interfaz');
      if (step.id === 'D9') {
        await tenant().selectOption('tenant-growth');
        await settle();
        const back = await main();
        if (!standalone('90.00 EUR').test(back)) notes.push('al volver a Growth Ops no reaparece el total 90.00 EUR');
      }
      await page.screenshot({ path: path.join(OUT, `${step.id}.png`), fullPage: true });
    } catch (e) {
      notes.push('excepción: ' + e.message.split('\n')[0]);
    }
    notes.push(...problems.splice(0));
    const result = notes.length ? 'fail' : 'pass';
    if (result === 'fail') blocked = true;
    results.push({ id: step.id, result, seconds: Math.round((Date.now() - started) / 1000), notes, info });
  }
  await settle();
  if (problems.length) results.push({ id: 'fin', result: 'fail', seconds: 0, notes: problems.splice(0), info: [] });
  await context.close();
  await browser.close();
  const report = { mode: 'automatizada', date: new Date().toISOString(), commit: process.env.COMMIT || null, steps: results };
  fs.writeFileSync(path.join(OUT, 'resultado.json'), JSON.stringify(report, null, 2));
  for (const r of results) console.log(`${r.id.padEnd(4)} ${r.result.padEnd(8)} ${String(r.seconds).padStart(3)} s ${r.notes.concat(r.info).join(' | ')}`);
  process.exit(results.some((r) => r.result === 'fail') ? 1 : 0);
}

main().catch((e) => { console.error('ERR', e.message); process.exit(2); });
```
