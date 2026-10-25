# JUP-057 — Reproducción de navegador

Instalar Playwright/Chromium en un entorno de pruebas externo. Compilar el frontend y ejecutar `corepack pnpm --filter @finops/frontend preview` (4173). Guardar el siguiente código como archivo .cjs fuera del repositorio, ajustar TARGET_URL y OUTPUT y ejecutarlo con Node desde el entorno que contiene Playwright. La sesión y los endpoints están simulados; no requiere credenciales reales.

```javascript
const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
const TARGET_URL = 'http://localhost:4173';
const OUTPUT = './jup057-browser-results';

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({viewport: {width:1440,height:1100}, locale:'es-ES', timezoneId:'Europe/Paris'});
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror', error=> errors.push(String(error)));
  const user={id:'demo-user',full_name:'Revisión demo',email:'demo@example.test',role:'operator'};
  await page.addInitScript(user=>localStorage.setItem('finops.session',JSON.stringify({accessToken:'fixture-only-not-a-credential',user})),user);
  await page.route('http://localhost:8000/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    const body=path==='/me'?user:path==='/tenants'?{items:[{id:'demo',name:'Cliente demo',slug:'demo',plan:'pro'}]}:null;
    if(body===null)throw new Error(`Unexpected API request ${path}`);
    await route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(body)});
  });
  try {
    await page.goto(TARGET_URL+'/anomalies');
    await page.getByRole('heading',{name:'Panel de Anomalías y Alertas'}).waitFor();
    await page.getByRole('table').waitFor();
    const rows=()=>page.locator('tbody tr');
    assert.equal(await rows().count(),3);
    assert.match(await rows().nth(0).innerText(),/EC2/);
    assert.match(await rows().nth(1).innerText(),/CloudFront/);
    assert.match(await page.getByRole('region',{name:'Resumen del conjunto de muestra'}).innerText(),/30\.700/);
    await page.screenshot({path:OUTPUT+'/desktop.png',fullPage:true});
    await page.getByLabel('Estado',{exact:true}).selectOption('Resuelto');
    await page.getByLabel('Criticidad',{exact:true}).selectOption('Media');
    assert.equal(await rows().count(),2);
    const downloadEvent=page.waitForEvent('download');
    await page.getByRole('button',{name:'Exportar Resultados',exact:true}).click();
    await page.getByRole('button',{name:'Exportar CSV',exact:true}).click();
    const download=await downloadEvent;
    assert.match(download.suggestedFilename(),/demo/);
    const csvPath=OUTPUT+'/filtered-demo.csv';
    await download.saveAs(csvPath);
    const csv=fs.readFileSync(csvPath,'utf8');
    assert.match(csv,/RDS Database/); assert.match(csv,/Azure Storage/); assert.doesNotMatch(csv,/EC2/); assert.match(csv,/demostración/);
    await page.getByLabel('Criticidad',{exact:true}).selectOption('Alta');
    await page.getByRole('heading',{name:'No hay alertas con estos filtros'}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Exportar Resultados',exact:true}).isDisabled(),true);
    await page.screenshot({path:OUTPUT+'/empty.png',fullPage:true});
    await page.getByRole('button',{name:'Ver anomalías abiertas',exact:true}).click();
    assert.equal(await rows().count(),3);
    await page.getByLabel('Estado',{exact:true}).selectOption('Todos');
    assert.equal(await page.getByRole('combobox',{name:'Ordenar por'}).count(),0);
    assert.equal(await rows().count(),5);
    assert.match(await rows().nth(2).innerText(),/RDS Database/);
    await page.getByRole('button',{name:'Restablecer filtros',exact:true}).click();
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:OUTPUT+'/mobile.png',fullPage:true});
    const panelDimensions=await page.locator('main > div').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth,viewport:innerWidth,document:document.documentElement.scrollWidth}));
    assert.ok(panelDimensions.scroll<=panelDimensions.client+1,JSON.stringify(panelDimensions));
    await page.getByLabel('Criticidad',{exact:true}).selectOption('Baja');
    assert.equal(await rows().count(),1);
    const table=page.getByRole('region',{name:'Lista de anomalías; desplazamiento horizontal disponible'});
    const tableDimensions=await table.evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}));
    assert.ok(tableDimensions.scroll>tableDimensions.client);
    await table.focus(); await page.keyboard.press('End');
    await page.getByRole('button',{name:'Restablecer filtros',exact:true}).click();
    assert.deepEqual(errors,[]);
    const result={status:'PASS',checks:['default open ordering and metrics','combined status/severity','filtered real CSV download','empty and disabled export','reset','fixed priority and removed ordering selector','mobile controls and panel containment'],panelDimensions,tableDimensions,pageErrors:errors};
    fs.writeFileSync(OUTPUT+'/browser-results.json',JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  } finally {await browser.close();}
})();

```
