import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import vm from 'node:vm';
import {appRoot,buildLanding,digest} from '../scripts/build.mjs';
import {createLandingServer} from '../scripts/serve.mjs';

async function fixture(t, origin='') {
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'economicon-landing-llms-'));
  t.after(async()=>{
    assert.equal(path.dirname(root),os.tmpdir());
    assert.ok(path.basename(root).startsWith('economicon-landing-llms-'));
    await fs.rm(root,{recursive:true,force:true});
  });
  const directory=path.join(root,'dist');
  const manifest=await buildLanding({outDir:directory,origin});
  return {directory,manifest};
}
async function start(t, directory, runtimeConfig) {
  const server=await createLandingServer({directory,runtimeConfig});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(async()=>{if(server.listening)await new Promise(resolve=>server.close(resolve));});
  return {server,port:server.address().port};
}
function request(port, pathname, method='GET', headers={}) {
  return new Promise((resolve,reject)=>{
    const req=http.request({host:'127.0.0.1',port,path:pathname,method,headers},res=>{
      const chunks=[];res.on('data',chunk=>chunks.push(chunk));
      res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,body:Buffer.concat(chunks)}));
    });
    req.on('error',reject);req.end();
  });
}
function publicConfig(script) {
  const context=vm.createContext({});vm.runInContext(script,context);
  return JSON.parse(JSON.stringify(context.__LANDING_PUBLIC_CONFIG__));
}

test('authored llms description is factual, discoverable and has no compiled operational destination',async t=>{
  const {directory,manifest}=await fixture(t);
  const description=await fs.readFile(path.join(directory,'llms.txt'),'utf8');
  assert.match(description,/^# Economicon\n\n> MVP académico de FinOps/m);
  assert.match(description,/datos públicos y sintéticos/);
  assert.match(description,/señales candidatas de anomalías/);
  assert.match(description,/fuentes documentales/);
  assert.match(description,/no conecta a una cuenta Azure real ni ejecuta acciones autónomas/);
  assert.match(description,/no son resultados medidos ni beneficios comerciales acreditados/);
  assert.match(description,/github\.com\/EconomiconFinOps\/tfm-economicon/);
  assert.doesNotMatch(description,/JUP-\d|BM-0|harness|LANDING_|demo-jupiter|landing-demo-jupiter|ignora.*instrucciones/i);
  assert.ok(manifest.files.some(item=>item.file==='llms.txt'));
  assert.equal(digest(await fs.readFile(path.join(appRoot,'src/llms.txt'))),digest(Buffer.from(description)));
  const html=await fs.readFile(path.join(directory,'index.html'),'utf8');
  assert.match(html,/<link rel="describedby" href="\/llms\.txt" type="text\/plain">/);
  assert.match(html,/noindex,nofollow/);
});

test('llms GET/HEAD is UTF8 text, startup-only, no-store and never conditional304 or secret-bearing',async t=>{
  const {directory}=await fixture(t);
  const config={appUrl:'https://app.example.org/a_(b)?view=costs#x',videoUrl:'https://video.example.org/private',AUTH_SECRET_KEY:'SECRET_SENTINEL'};
  const {port}=await start(t,directory,config);
  config.appUrl='https://changed.example.org/';
  const result=await request(port,'/llms.txt','GET',{'if-none-match':'*','if-modified-since':new Date().toUTCString(),'range':'bytes=0-3'});
  assert.equal(result.status,200);
  assert.equal(result.headers['content-type'],'text/plain; charset=utf-8');
  assert.equal(result.headers['cache-control'],'no-store');
  assert.equal(result.headers.etag,undefined);
  assert.equal(result.headers['x-content-type-options'],'nosniff');
  assert.equal(result.headers['x-robots-tag'],'noindex, nofollow');
  assert.match(result.headers['content-security-policy'],/connect-src 'none'/);
  assert.match(result.body.toString(),/\[Abrir la aplicación\]\(<https:\/\/app\.example\.org\/a_\(b\)\?view=costs#x>\)/);
  assert.doesNotMatch(result.body.toString(),/SECRET_SENTINEL|AUTH_SECRET|changed\.example|video\.example/);
  const head=await request(port,'/llms.txt','HEAD');
  assert.equal(head.status,200);assert.equal(head.body.length,0);
  assert.equal(Number(head.headers['content-length']),result.body.length);
  assert.equal(head.headers['cache-control'],'no-store');assert.equal(head.headers.etag,undefined);
  assert.equal((await request(port,'/llms.txt','POST')).status,405);
});

test('app A to B to A changes llms with runtime config while every compiled artifact remains identical',async t=>{
  const {directory,manifest}=await fixture(t);
  const raw=await fs.readFile(path.join(directory,'build-manifest.json'));
  const bodies=[];
  for(const appUrl of ['https://app.example.org/a','https://other.example.org/b','https://app.example.org/a']) {
    const {server,port}=await start(t,directory,{appUrl,videoUrl:null,secret:'SECRET_SENTINEL'});
    const response=await request(port,'/llms.txt');bodies.push(response.body.toString());
    const runtime=publicConfig((await request(port,'/runtime-config.js')).body.toString());
    assert.deepEqual(runtime,{appUrl,videoUrl:null});
    assert.ok(response.body.toString().includes('](<'+runtime.appUrl+'>)'));
    for(const item of manifest.files)assert.equal(digest(await fs.readFile(path.join(directory,item.file))),item.sha256);
    assert.deepEqual(await fs.readFile(path.join(directory,'build-manifest.json')),raw);
    await new Promise(resolve=>server.close(resolve));
  }
  assert.equal(bodies[0],bodies[2]);assert.notEqual(bodies[0],bodies[1]);
  assert.doesNotMatch(await fs.readFile(path.join(directory,'llms.txt'),'utf8'),/app\.example|other\.example|SECRET_SENTINEL/);
});

test('missing/unsafe app links are omitted independently; aliases, private paths and queries remain closed',async t=>{
  const {directory}=await fixture(t);
  for(const appUrl of [undefined,'','javascript:alert(1)','https://user:SECRET_SENTINEL@app.example.org/','https://app.example.org/?token=SECRET_SENTINEL','/media/app.mp4']) {
    const {server,port}=await start(t,directory,{appUrl,videoUrl:'/media/presentation.mp4',secret:'SECRET_SENTINEL'});
    const result=await request(port,'/llms.txt');
    assert.equal(result.status,200);assert.match(result.body.toString(),/^# Economicon/);
    assert.doesNotMatch(result.body.toString(),/## Aplicación|Abrir la aplicación|SECRET_SENTINEL|javascript:|presentation\.mp4/);
    assert.equal(publicConfig((await request(port,'/runtime-config.js')).body.toString()).appUrl,null);
    assert.equal((await request(port,'/healthz')).status,200);
    for(const route of ['/llms.txt?x=1','/%6clms.txt','/llms%2etxt','/llms.txt/','/src/llms.txt','/scripts/runtime-config.mjs','/.env','/build-manifest.json','/../llms.txt'])assert.equal((await request(port,route)).status,404,route);
    await new Promise(resolve=>server.close(resolve));
  }
});

test('public origin and local-noindex remain separate from the runtime application destination',async t=>{
  for(const origin of ['', 'https://landing.example.org']) {
    const {directory}=await fixture(t,origin);
    const {port}=await start(t,directory,{appUrl:'https://app.example.org/',videoUrl:null});
    const description=await request(port,'/llms.txt');
    const robots=(await request(port,'/robots.txt')).body.toString();
    const html=(await request(port,'/')).body.toString();
    const sitemap=(await request(port,'/sitemap.xml')).body.toString();
    assert.match(description.body.toString(),/<https:\/\/app\.example\.org\/>/);
    assert.doesNotMatch(html,/app\.example\.org/);assert.doesNotMatch(sitemap,/app\.example\.org/);
    if(origin) {
      assert.match(html,/rel="canonical" href="https:\/\/landing\.example\.org\/"/);
      assert.match(html,/content="index,follow"/);assert.match(robots,/Allow: \/\n/);
      assert.match(sitemap,/<loc>https:\/\/landing\.example\.org\/<\/loc>/);
      assert.equal(description.headers['x-robots-tag'],undefined);
    } else {
      assert.match(html,/noindex,nofollow/);assert.doesNotMatch(html,/rel="canonical"/);
      assert.equal(robots,'User-agent: *\nDisallow: /\n');assert.doesNotMatch(sitemap,/<loc>/);
      assert.equal(description.headers['x-robots-tag'],'noindex, nofollow');
    }
  }
});

test('missing or changed llms template fails the verified artifact boundary at startup',async t=>{
  const {directory}=await fixture(t);
  await fs.appendFile(path.join(directory,'llms.txt'),'\nUnexpected change');
  await assert.rejects(createLandingServer({directory}),/integrity mismatch/);
  const other=await fixture(t);
  const manifestPath=path.join(other.directory,'build-manifest.json');
  const manifest=JSON.parse(await fs.readFile(manifestPath,'utf8'));
  manifest.files=manifest.files.filter(item=>item.file!=='llms.txt');
  await fs.writeFile(manifestPath,JSON.stringify(manifest));
  await assert.rejects(createLandingServer({directory:other.directory}),/Public index\/404\/description missing/);
});
