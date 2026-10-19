import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import os from 'node:os';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {appRoot,buildLanding,parseOrigin,digest,PUBLIC_INPUTS} from '../scripts/build.mjs';
async function fixture(t) { const root=await fs.mkdtemp(path.join(os.tmpdir(),'economicon-landing-build-')); const sourceDir=path.join(root,'src'); await fs.cp(path.join(appRoot,'src'),sourceDir,{recursive:true}); t.after(async()=>{if(path.dirname(root)!==os.tmpdir()||!path.basename(root).startsWith('economicon-landing-build-'))throw new Error('Unsafe fixture cleanup');await fs.rm(root,{recursive:true,force:true});});return {root,sourceDir,outDir:path.join(root,'dist')}; }
test('local build is non-indexable, closed and reproducible without exposing inputs or environment',async t=>{
 const options=await fixture(t);await fs.writeFile(path.join(options.sourceDir,'.env'),'SECRET_SENTINEL_JUP089');await fs.writeFile(path.join(options.root,'internal.txt'),'PRIVATE_SENTINEL_JUP089');
 const first=await buildLanding({...options,origin:''});const second=await buildLanding({...options,origin:''});assert.deepEqual(first,second);assert.equal(first.origin,null);
 const names=(await fs.readdir(options.outDir)).sort();assert.deepEqual(names,['404.html','_headers','app.js','assets','build-manifest.json','index.html','robots.txt','sitemap.xml','style.css']);
 assert.deepEqual(first.files.map(f=>f.file).sort(),[...PUBLIC_INPUTS,'robots.txt','sitemap.xml','_headers'].sort());
 for(const item of first.files){const bytes=await fs.readFile(path.join(options.outDir,item.file));assert.equal(digest(bytes),item.sha256);assert.equal(bytes.length,item.bytes);assert.doesNotMatch(bytes.toString('utf8'),/SECRET_SENTINEL_JUP089|PRIVATE_SENTINEL_JUP089/);}
 const html=await fs.readFile(path.join(options.outDir,'index.html'),'utf8');assert.match(html,/noindex,nofollow/);assert.doesNotMatch(html,/rel="canonical"|property="og:url"/);assert.equal(await fs.readFile(path.join(options.outDir,'robots.txt'),'utf8'),'User-agent: *\nDisallow: /\n');assert.doesNotMatch(await fs.readFile(path.join(options.outDir,'sitemap.xml'),'utf8'),/<loc>/);
 assert.ok(first.files.reduce((n,f)=>n+f.bytes,0)<350000,'public artifact budget');
 const cliOut=path.join(options.root,'cli','dist');const output=execFileSync(process.execPath,[path.join(appRoot,'scripts/build.mjs')],{cwd:options.root,env:{...process.env,LANDING_OUT_DIR:cliOut,SITE_ORIGIN:''},encoding:'utf8'});assert.equal(JSON.parse(output).mode,'local-noindex');assert.equal(JSON.parse(await fs.readFile(path.join(cliOut,'build-manifest.json'),'utf8')).version,1);
});
test('HTTPS origin produces consistent canonical, OG and sitemap; invalid forms fail',async t=>{
 const options=await fixture(t);await buildLanding({...options,origin:'https://landing.example.test/'});
 const html=await fs.readFile(path.join(options.outDir,'index.html'),'utf8');assert.match(html,/rel="canonical" href="https:\/\/landing\.example\.test\/"/);assert.match(html,/property="og:url" content="https:\/\/landing\.example\.test\/"/);assert.match(html,/property="og:image" content="https:\/\/landing\.example\.test\/assets\/economicon-primary\.png"/);assert.match(await fs.readFile(path.join(options.outDir,'sitemap.xml'),'utf8'),/<loc>https:\/\/landing\.example\.test\/<\/loc>/);
 for(const origin of ['http://site.test','https://user:pass@site.test','https://site.test/path','https://site.test/?q=x','https://site.test/#x','https://localhost','https://127.0.0.1','https://site.test:8443','not a URL'])assert.throws(()=>parseOrigin(origin));
});
test('invalid source/origin never replaces the last valid artifact',async t=>{
 const options=await fixture(t);const before=await buildLanding({...options,origin:''});await assert.rejects(buildLanding({...options,origin:'http://site.test'}));await fs.unlink(path.join(options.sourceDir,'assets/favicon.png'));await assert.rejects(buildLanding({...options,origin:''}));const after=JSON.parse(await fs.readFile(path.join(options.outDir,'build-manifest.json'),'utf8'));assert.deepEqual(before,after);
});
test('symbolic public asset directory is rejected before output publication',async t=>{
 const options=await fixture(t);const assets=path.join(options.sourceDir,'assets');const target=path.join(options.root,'assets-real');await fs.rename(assets,target);await fs.symlink(target,assets,process.platform==='win32'?'junction':'dir');await assert.rejects(buildLanding({...options,origin:''}),/Symbolic/);await assert.rejects(fs.access(options.outDir));
});
