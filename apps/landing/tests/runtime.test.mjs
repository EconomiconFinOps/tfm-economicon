import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {buildLanding,digest} from '../scripts/build.mjs';
import {createLandingServer} from '../scripts/serve.mjs';
import {publicDestination,readPublicConfig,serializePublicConfig} from '../scripts/runtime-config.mjs';

test('public destinations reject executable, local, credential-bearing or malformed URLs independently',()=>{
 for(const url of ['',undefined,'javascript:alert(1)','http://video.example.org/', 'https://user:pass@example.org/','https://localhost/','https://app.local/','https://127.0.0.1/','https://2130706433/','https://[::1]/','https://app.example.org:8443/','https://app.example.org/\nnext','https://app.example.org/?token=abc','https://app.example.org/?X-Amz-Signature=abc','https://app.example.org/?api_key=abc','https://app.example.org/'+ 'a'.repeat(4096)])assert.equal(publicDestination(url),null,String(url));
 const valid='https://drive.google.com/file/d/example/view?usp=drive_link';
 assert.equal(publicDestination(valid),valid);
 assert.deepEqual(readPublicConfig({LANDING_VIDEO_URL:'/media/presentation.mp4',LANDING_APP_URL:'/media/app.mp4'}),{videoUrl:'/media/presentation.mp4',appUrl:null});
 for(const videoUrl of ['/media/a.mp4?x=1','/media/../a.mp4','//media/a.mp4'])assert.equal(readPublicConfig({LANDING_VIDEO_URL:videoUrl}).videoUrl,null);
 assert.deepEqual(readPublicConfig({LANDING_VIDEO_URL:valid,LANDING_APP_URL:'javascript:alert(1)',AUTH_SECRET_KEY:'SENTINEL'}),{videoUrl:valid,appUrl:null});
 assert.deepEqual(readPublicConfig({LANDING_APP_URL:'https://app.example.org/'}),{videoUrl:null,appUrl:'https://app.example.org/'});
});

test('configuration is a frozen closed schema with safe executable serialization',()=>{
 const script=serializePublicConfig({videoUrl:'https://video.example.org/?q=</script>',appUrl:'https://app.example.org/#x',secret:'SENTINEL'});
 assert.doesNotMatch(script,/<|SENTINEL|secret/);
 const context=vm.createContext({});vm.runInContext(script,context);
 assert.deepEqual(Object.keys(context.__LANDING_PUBLIC_CONFIG__).sort(),['appUrl','videoUrl']);
 assert.equal(Object.isFrozen(context.__LANDING_PUBLIC_CONFIG__),true);
 assert.equal(context.__LANDING_PUBLIC_CONFIG__.videoUrl,'https://video.example.org/?q=%3C/script%3E');
});

test('startup-only public resource and health never cache, disclose environment or alter the static artifact',async t=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'economicon-landing-runtime-'));
 const directory=path.join(root,'dist');await buildLanding({outDir:directory,origin:''});
 const before=await fs.readFile(path.join(directory,'build-manifest.json'));
 const config={videoUrl:'https://video.example.org/a',appUrl:'https://app.example.org/a',secret:'SENTINEL'};
 const server=await createLandingServer({directory,runtimeConfig:config});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 t.after(async()=>{await new Promise(resolve=>server.close(resolve));assert.equal(path.dirname(root),os.tmpdir());assert.ok(path.basename(root).startsWith('economicon-landing-runtime-'));await fs.rm(root,{recursive:true,force:true});});
 const base='http://127.0.0.1:'+server.address().port;
 config.appUrl='https://changed.example.org/';
 for(const route of ['/runtime-config.js','/healthz']){
  const response=await fetch(base+route,{headers:{'If-None-Match':'*','If-Modified-Since':new Date().toUTCString()}});
  assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(response.headers.get('etag'),null);
  assert.equal(response.headers.get('x-content-type-options'),'nosniff');
  const body=await response.text();assert.doesNotMatch(body,/SENTINEL|changed.example|AUTH_SECRET|environment/);
  const head=await fetch(base+route,{method:'HEAD'});assert.equal(head.status,200);assert.equal(await head.text(),'');assert.equal(Number(head.headers.get('content-length')),Buffer.byteLength(body));
  assert.equal((await fetch(base+route,{method:'POST'})).status,405);
  if(route==='/healthz')assert.deepEqual(JSON.parse(body),{status:'ok'});
  else{assert.match(response.headers.get('content-type'),/javascript/);assert.match(body,/app.example.org\/a/);}
 }
 assert.equal(digest(await fs.readFile(path.join(directory,'build-manifest.json'))),digest(before));
 const page=await fetch(base);assert.match(page.headers.get('content-security-policy'),/frame-src https:\/\/drive.google.com;/);
 const html=await page.text();assert.ok(html.indexOf('runtime-config.js')<html.indexOf('app.js'));assert.doesNotMatch(html,/<iframe|drive.google.com|app.example.org/);
 for(const route of ['/.env','/scripts/runtime-config.mjs','/scripts/start.mjs','/build-manifest.json'])assert.equal((await fetch(base+route)).status,404);
});
